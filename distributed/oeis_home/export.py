"""OEIS-ready exports: b-files, the draft entries, discoveries.csv and evidence.json.

Rules applied here.  Project policy (spec D12), stricter than the OEIS Style Sheet, which permits
probable-prime terms if labelled: DATA holds only proven terms and stays under 260 characters;
b-file lines are ``n a(n)`` with LF endings and no line over 1000 characters; probable-prime terms
are never called prime; a term whose position is not yet determined goes into a COMMENT (the
A001606 convention), never into DATA or the b-file.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import date
from pathlib import Path

from .families import Family, value

BFILE_N_MAX = 6000
DATA_MAX_CHARS = 260


def bfile(terms: list[tuple[int, int]], header_lines: list[str]) -> str:
    lines = [f"# {h}" for h in header_lines]
    for n, a in terms:
        line = f"{n} {a}"
        if len(line) > 1000:
            break
        lines.append(line)
    return "\n".join(lines) + "\n"


def _data_line(values: list[int]) -> str:
    out = []
    for v in values:
        cand = ",".join(map(str, out + [v]))
        if len(cand) > DATA_MAX_CHARS:
            break
        out.append(v)
    return ",".join(map(str, out))


def prime_index_terms(ledger: dict, variant: str) -> list[dict]:
    """All confirmed prime / prp indices for a sign variant (even indices come from the shared variant)."""
    out = []
    for uid, u in ledger["units"].items():
        if u["state"] not in ("verified", "double_checked"):
            continue
        for rec in u.get("verdicts", []):
            if rec["v"] not in ("prime", "prp"):
                continue
            if rec["variant"] == variant or (rec["variant"] == "even"):
                pc = next((pc for pc in ledger.get("positive_claims", []) if pc["unit_id"] == uid and pc["n"] == rec["n"]
                           and pc["variant"] == rec["variant"]), {})
                pari = pc.get("maintainer_pari", "none")
                proven = rec["v"] == "prime" or pari == "isprime"
                out.append({"n": rec["n"], "variant": rec["variant"], "status": "proven" if proven else "prp", "digits": rec["digits"],
                            "unit_id": uid, "discoverer": pc.get("discoverer_login", ""), "verifier": pc.get("verifier_login", ""),
                            "maintainer_pari": pari, "cert_sha256": pc.get("cert_sha256", "")})
    out.sort(key=lambda t: t["n"])
    for k, t in enumerate(out, start=1):
        t["k"] = k
    return out


def extension_lines(terms: list[dict], contributors: dict[str, dict], submitter: str) -> list[str]:
    today = date.today().strftime("%b %d %Y")
    lines = []
    run_start, run_owner, prev_k = None, None, 0
    for t in terms:
        owner = t["discoverer"] or submitter
        if owner != run_owner:
            if run_owner is not None:
                lines.append(_ext_line(run_start, prev_k, run_owner, contributors, submitter, today))
            run_start, run_owner = t["k"], owner
        prev_k = t["k"]
        if t["status"] == "prp":
            lines.append(f"a({t['k']}) corresponds to a probable prime (BPSW test and strong probable-prime tests to bases 2, 3 and the worker base; "
                         f"no prime factor q = 2*k*{t['n']} +- 1 with k <= 20000, and every prime factor of this term has that form). - _{submitter}_, {today}")
    if run_owner is not None:
        lines.append(_ext_line(run_start, prev_k, run_owner, contributors, submitter, today))
    return lines


def _ext_line(k0: int, k1: int, owner: str, contributors: dict[str, dict], submitter: str, today: str) -> str:
    rng = f"a({k0})" if k0 == k1 else f"a({k0})-a({k1})"
    c = contributors.get(owner, {})
    name = c.get("oeis_credit_name") or ""
    if not name:
        return f"{rng} found by an OEIS@home volunteer ({c.get('display_name', owner)}), contributed by _{submitter}_, {today}"
    return f"{rng} from _{name}_, {today}"


def oeis_ready(ledger: dict, fam: Family, contributors: dict[str, dict], submitter: str = "Andy Triboletti") -> dict:
    vt = ledger["verified_through"]
    seqs = {}
    for key, variant in (("A3", "m1"), ("A4", "p1")):
        terms = [t for t in prime_index_terms(ledger, variant) if t["n"] < vt]
        pending = [{"n": t["n"], "variant": t["variant"], "reason": "position_undetermined"} for t in prime_index_terms(ledger, variant) if t["n"] >= vt]
        proven_prefix = []
        for t in terms:
            if t["status"] != "proven":
                break
            proven_prefix.append(t["n"])
        for pt in pending:
            rec = next((r for uu in ledger["units"].values() for r in uu.get("verdicts", []) if r["n"] == pt["n"] and r["variant"] == pt["variant"]), {})
            pt["digits"] = rec.get("digits", 0)
        seqs[key] = {"anumber": "", "name": f"Numbers k such that |{'A1' if variant == 'm1' else 'A2'}(k)| is prime", "offset": [1, 2],
                     "data": _data_line(proven_prefix), "bfile": f"exports/lehmer-q2/{key}.bfile.txt", "terms": terms,
                     "pending_terms": pending, "extensions_lines": extension_lines(terms, contributors, submitter)}
    for key, variant in (("A1", "m1"), ("A2", "p1")):
        vals = [int(value(variant, n)) for n in range(0, 45)]
        seqs[key] = {"anumber": "", "name": f"Lehmer companion sequence Vbar_n(sqrt({5 if variant == 'm1' else 3}), 2)", "offset": [0, 1],
                     "data": _data_line(vals), "bfile": f"exports/lehmer-q2/{key}.bfile.txt", "terms": []}
    return {"family": fam.id, "family_hash": fam.hash, "verified_through": vt, "sequences": seqs,
            "tree_sha": _tree_sha(), "release": ledger.get("release", ""),
            "contributors": [{"login": login, **c} for login, c in ledger.get("contributors", {}).items()]}


def _tree_sha() -> str:
    import subprocess  # noqa: PLC0415

    r = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], capture_output=True, text=True, check=False)
    return r.stdout.strip() if r.returncode == 0 else ""


def write_exports(ledger: dict, fam: Family, contributors: dict[str, dict], out: Path, submitter: str = "Andy Triboletti") -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    ready = oeis_ready(ledger, fam, contributors, submitter)
    stamp = date.today().isoformat()
    for key, variant in (("A1", "m1"), ("A2", "p1")):
        terms = [(n, int(value(variant, n))) for n in range(0, BFILE_N_MAX + 1)]
        b = -1 if variant == "m1" else 1
        (out / f"{key}.bfile.txt").write_text(bfile(terms, [f"{key} b-file, n = 0..{BFILE_N_MAX}, generated {stamp} by oeis_home 0.1.0 (family {fam.hash}, tree {ready['tree_sha'][:12]})",
                                                           f"a(n) = Psi(2,{b},n): Psi(0)=2, Psi(1)=1, Psi(n+1) = {4 - b}^(n mod 2)*Psi(n) - 2*Psi(n-1)",
                                                           f"(PARI) a(n) = if(n==0, 2, my(p=2, q=1); for(k=1, n-1, [p, q] = [q, if(k%2, {4 - b}, 1)*q - 2*p]); q)"]), encoding="utf-8")
    for key in ("A3", "A4"):
        s = ready["sequences"][key]
        (out / f"{key}.bfile.txt").write_text(bfile([(t["k"], t["n"]) for t in s["terms"]],
                                                    [f"{key} b-file, k = 1..{len(s['terms'])}, generated {stamp}; verified_through = {ready['verified_through']}; tree {ready['tree_sha'][:12]}",
                                                     "status per term in evidence.json (proven = PARI isprime / deterministic; prp = BPSW + strong PRP tests)"]),
                                              encoding="utf-8")
    (out / "oeis_draft.txt").write_text(draft_entries(ready, submitter, stamp), encoding="utf-8")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["variant", "n", "digits", "status", "position_final", "discoverer", "verifier", "maintainer_pari", "unit_id"])
    for key, variant in (("A3", "m1"), ("A4", "p1")):
        for t in prime_index_terms(ledger, variant):
            w.writerow([t["variant"], t["n"], t["digits"], t["status"], t["n"] < ready["verified_through"], t["discoverer"], t["verifier"], t["maintainer_pari"], t["unit_id"]])
    (out / "discoveries.csv").write_text(buf.getvalue(), encoding="utf-8")
    (out / "evidence.json").write_text(json.dumps(ready, indent=1, ensure_ascii=False), encoding="utf-8")
    return ready


def _data_or_banner(seq: dict, key: str, ready: dict) -> str:
    terms = seq["data"].split(",") if seq["data"] else []
    if len(terms) >= 4:
        return seq["data"]
    n_pending = len(seq.get("pending_terms", []))
    return (f"[EMPTY — verified_through = {ready['verified_through']}; {n_pending} confirmed index(es) await a second account "
            f"and/or a maintainer gp check; DO NOT SUBMIT {key} yet]")


def _pending_comment_lines(seq: dict, key: str, submitter: str, today: str) -> str:
    out = []
    for pt in seq.get("pending_terms", []):
        out.append(f"%C {key} {pt['n']} is a term, but its position is not yet determined; the corresponding {pt.get('digits', '?')}-digit "
                   f"value is a probable prime (BPSW and strong probable-prime tests to bases 2, 3 and the worker base). - _{submitter}_, {today}")
    return "\n".join(out)


def draft_entries(ready: dict, submitter: str, stamp: str) -> str:
    s = ready["sequences"]
    today = date.today().strftime("%b %d %Y")
    a3_data, a4_data = _data_or_banner(s["A3"], "A3", ready), _data_or_banner(s["A4"], "A4", ready)
    a3_comment = "%C A3 Terms in DATA are proven primes; further probable-prime indices are listed in the b-file and marked in the extensions." if s["A3"]["data"] else ""
    a4_comment = "%C A4 Terms in DATA are proven primes; further probable-prime indices are listed in the b-file and marked in the extensions." if s["A4"]["data"] else ""
    text = f"""OEIS draft entries generated {stamp} from the OEIS@home ledger (A-numbers are placeholders; submit manually,
run every PARI line in gp first; DATA lines contain proven terms only).

%I A1
%S A1 {s['A1']['data']}
%N A1 Lehmer companion sequence Vbar_n(sqrt(5), 2): a(n) = (alpha^n + beta^n)/sqrt(5)^(n mod 2), where alpha and beta are the roots of x^2 - sqrt(5)*x + 2.
%C A1 D. H. Lehmer's companion sequence Vbar_n for R = 5, Q = 2: Vbar_n = V_n for even n and V_n/sqrt(R) for odd n, where V_n = alpha^n + beta^n, alpha + beta = sqrt(R), alpha*beta = Q.
%C A1 Equivalently a(n) = Psi(2,-1,n) in the notation of the arXiv link: Psi(0) = 2, Psi(1) = 1, Psi(n+1) = 5^(n mod 2)*Psi(n) - 2*Psi(n-1).
%C A1 a(n) is odd for n >= 1. a(m) divides a(n) whenever m divides n and n/m is odd.
%C A1 |a(n)| = 1 only for n = 1, 2, 3, 7 (for n >= 16 by the primitive-divisor theorem for Lehmer numbers, Bilu-Hanrot-Voutier 2001; checked directly for n < 16).
%C A1 The bisection a(2n) = A272931(n) = V_n(1,4). Indices n with |a(n)| prime: A3.
%F A1 a(n) = a(n-2) - 4*a(n-4) for n >= 4.
%F A1 G.f.: (2 + x - x^2 - 2*x^3)/(1 - x^2 + 4*x^4).
%F A1 a(2n) = V_n(1,4) = A272931(n); 2*a(2n+1) = V_n(1,4) - 3*U_n(1,4).
%F A1 a(n) = 5^floor(n/2) * V_n(1, 2/5), V the Lucas sequence with V_0 = 2, V_1 = P.
%F A1 a(2n) = V_n(1,4) = A272931(n); U_n(1,4) = A106853(n-1) for n >= 1.
%e A1 a(2) = 5*a(1) - 2*a(0) = 1; a(3) = a(2) - 2*a(1) = -1; a(4) = 5*a(3) - 2*a(2) = -7.
%t A1 LinearRecurrence[{{0, 1, 0, -4}}, {{2, 1, 1, -1}}, 45]
%o A1 (PARI) a(n) = if(n==0, 2, my(p=2, q=1); for(k=1, n-1, [p, q] = [q, if(k%2, 5, 1)*q - 2*p]); q)
%o A1 (PARI) Vec((2 + x - x^2 - 2*x^3)/(1 - x^2 + 4*x^4) + O(x^45))
%o A1 (Python)
%o A1 def a(n):
%o A1     if n == 0: return 2
%o A1     p, q = 2, 1
%o A1     for k in range(1, n): p, q = q, (5 if k % 2 else 1)*q - 2*p
%o A1     return q
%Y A1 Cf. A272931 (bisection), A106853, A2, A3, A000032, A001606.
%K A1 sign,easy
%O A1 0,1
%A A1 _{submitter}_, {today}
%D A1 D. H. Lehmer, An extended theory of Lucas' functions, Ann. of Math. (2) 31 (1930), 419-448.
%H A1 M. Ibrahim, <a href="https://arxiv.org/abs/2404.05772">Generalizing the Eight Levels Theorem</a>, arXiv:2404.05772 [math.GM], 2024.
%H A1 <a href="/index/Rec#order_04">Index entries for linear recurrences with constant coefficients</a>, signature (0,1,0,-4).

%I A2
%S A2 {s['A2']['data']}
%N A2 Lehmer companion sequence Vbar_n(sqrt(3), 2): a(n) = (alpha^n + beta^n)/sqrt(3)^(n mod 2), where alpha and beta are the roots of x^2 - sqrt(3)*x + 2.
%C A2 Lehmer companion sequence with R = 3, Q = 2 (see A1). Equivalently a(n) = Psi(2,1,n): Psi(0) = 2, Psi(1) = 1, Psi(n+1) = 3^(n mod 2)*Psi(n) - 2*Psi(n-1).
%C A2 a(n) is odd for n >= 1. a(m) divides a(n) whenever m divides n and n/m is odd. |a(n)| = 1 only for n = 1, 2, 5.
%C A2 a(2n) = (-1)^n*A272931(n) = (-1)^n*A1(2n), so the even terms of A3 and A4 coincide.
%F A2 a(n) = -a(n-2) - 4*a(n-4) for n >= 4.
%F A2 G.f.: (2 + x + x^2 - 2*x^3)/(1 + x^2 + 4*x^4).
%F A2 a(2n) = (-1)^n*V_n(1,4); 2*a(2n+1) = (-1)^n*(V_n(1,4) + 5*U_n(1,4)).
%F A2 a(n) = 3^floor(n/2) * V_n(1, 2/3).
%e A2 a(2) = 3*a(1) - 2*a(0) = -1; a(3) = a(2) - 2*a(1) = -3; a(4) = 3*a(3) - 2*a(2) = -7.
%t A2 LinearRecurrence[{{0, -1, 0, -4}}, {{2, 1, -1, -3}}, 45]
%o A2 (PARI) a(n) = if(n==0, 2, my(p=2, q=1); for(k=1, n-1, [p, q] = [q, if(k%2, 3, 1)*q - 2*p]); q)
%o A2 (PARI) Vec((2 + x + x^2 - 2*x^3)/(1 + x^2 + 4*x^4) + O(x^45))
%Y A2 Cf. A272931, A1, A4.
%K A2 sign,easy
%O A2 0,1
%A A2 _{submitter}_, {today}
%D A2 D. H. Lehmer, An extended theory of Lucas' functions, Ann. of Math. (2) 31 (1930), 419-448.
%H A2 M. Ibrahim, <a href="https://arxiv.org/abs/2404.05772">Generalizing the Eight Levels Theorem</a>, arXiv:2404.05772 [math.GM], 2024.
%H A2 <a href="/index/Rec#order_04">Index entries for linear recurrences with constant coefficients</a>, signature (0,-1,0,-4).

%I A3
%S A3 {a3_data}
%N A3 Numbers k such that |A1(k)| is prime, where A1(k) = Vbar_k(sqrt(5), 2) is the Lehmer companion sequence with R = 5, Q = 2.
%C A3 Since A1(m) divides A1(k) whenever k/m is odd and |A1(m)| = 1 only for m = 1, 2, 3, 7, a term k >= 16 is prime, twice a prime, a power of 2, or one of 21, 49; 21 is a term.
%C A3 The even terms are 2*j with |A272931(j)| prime and coincide with the even terms of A4.
{a3_comment}
{_pending_comment_lines(s['A3'], 'A3', submitter, today)}
%e A3 4 is a term because |A1(4)| = 7 is prime; 7 is not a term because |A1(7)| = 1.
%o A3 (PARI) A1(n) = if(n==0, 2, my(p=2, q=1); for(k=1, n-1, [p, q] = [q, if(k%2, 5, 1)*q - 2*p]); q);
%o A3 (PARI) select(n->isprime(abs(A1(n))), [0..1500]) \\ ispseudoprime for a fast search
%o A3 (Python)
%o A3 from sympy import isprime
%o A3 def A1(n):
%o A3     if n == 0: return 2
%o A3     p, q = 2, 1
%o A3     for k in range(1, n): p, q = q, (5 if k % 2 else 1)*q - 2*p
%o A3     return q
%o A3 print([n for n in range(1501) if isprime(abs(A1(n)))])
%Y A3 Cf. A1, A4, A272931, A001606.
%K A3 nonn,more
%O A3 1,2
%A A3 _{submitter}_, {today}
{chr(10).join('%E A3 ' + line for line in s['A3']['extensions_lines'])}

%I A4
%S A4 {a4_data}
%N A4 Numbers k such that |A2(k)| is prime, where A2(k) = Vbar_k(sqrt(3), 2) is the Lehmer companion sequence with R = 3, Q = 2.
%C A4 Since A2(m) divides A2(k) whenever k/m is odd and |A2(m)| = 1 only for m = 1, 2, 5, a term k >= 16 is prime, twice a prime, a power of 2, or 25; 25 is a term.
%C A4 The even terms coincide with those of A3.
{a4_comment}
{_pending_comment_lines(s['A4'], 'A4', submitter, today)}
%e A4 3 is a term because |A2(3)| = 3 is prime; 5 is not a term because |A2(5)| = 1.
%o A4 (PARI) A2(n) = if(n==0, 2, my(p=2, q=1); for(k=1, n-1, [p, q] = [q, if(k%2, 3, 1)*q - 2*p]); q);
%o A4 (PARI) select(n->isprime(abs(A2(n))), [0..1500])
%Y A4 Cf. A2, A3, A272931, A001606.
%K A4 nonn,more
%O A4 1,2
%A A4 _{submitter}_, {today}
{chr(10).join('%E A4 ' + line for line in s['A4']['extensions_lines'])}
"""
    return text
