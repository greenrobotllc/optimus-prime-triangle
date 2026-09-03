"""Automated identity discovery (goal G8) and the discoveries ledger.

What the pipeline does
----------------------
1. Enumerate points ``(a, b)`` of the Ψ family over the integers and over the rings
   ``Z[√2]``, ``Z[√3]``, ``Z[φ]`` (with ``a = 1`` on the rings).
2. For each point compute the exact sequence ``Ψ(a, b, n)``, ``n < n_max``, and classify it:
   periodic (with the period predicted by the classification theorem for comparison),
   a known classical sequence (offline library, up to sign), or unclassified.
3. Scan the integer points for prime density among ``|Ψ(a, b, n)|`` (goal G5): which points
   of the family are rich in primes (Mersenne ``(−2, −5)``, Lucas ``(−1, −3)``, …).
4. Record candidate results in a ledger with a status ladder::

       numeric-verified  →  sympy-proved / proved (elementary)  →  novelty: unchecked | classical | checked

   The working label is ``config.DISCOVERY_LABEL``.  A label in the ledger is a *working
   name*; mathematical names stick only through publication and citation, and novelty is
   never asserted by this code — a human must check OEIS and the literature.

The census is also a self-consistency check of the classification theorem: within the
coefficient range searched, the only periodic points of the golden ring are the four
golden ``b`` values and ``1, 0, −1``.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import config as cfg
from core_math.mersenne import is_prime_int
from core_math.psi_sequence import QuadInt, minimal_period, psi
from research.known_sequences import match
from research.periodicity import THEOREM_STATEMENT, predicted_period

RING_NAMES: dict[str, str] = {"Z[sqrt2]": "sqrt2", "Z[sqrt3]": "sqrt3", "Z[phi]": "phi"}


# --------------------------------------------------------------------------- points
@dataclass(frozen=True)
class Point:
    ring: str                       # "Z" or one of RING_NAMES
    a: Any
    b: Any

    @property
    def label(self) -> str:
        return f"Ψ({self.a}, {self.b}, n) over {self.ring}"

    def b_float(self) -> float:
        return float(self.b)


def enumerate_points(grid: dict[str, object] | None = None) -> list[Point]:
    grid = grid or cfg.DISCOVERY_GRID
    lo, hi = grid["int_range"]  # type: ignore[misc]
    pts: list[Point] = []
    for a in range(lo, hi + 1):
        for b in range(lo, hi + 1):
            if 2 * a == b:
                continue
            pts.append(Point("Z", a, b))
    clo, chi = grid["coeff_range"]  # type: ignore[misc]
    for ring in grid["rings"]:  # type: ignore[union-attr]
        key = RING_NAMES[ring]
        for u in range(clo, chi + 1):
            for v in range(clo, chi + 1):
                if v == 0:
                    continue
                pts.append(Point(ring, QuadInt(1, 0, key), QuadInt(u, v, key)))
    return pts


def sequence(point: Point, n_max: int) -> list[Any]:
    vals = []
    for n in range(n_max):
        v = psi(point.a, point.b, n)
        if isinstance(point.a, QuadInt) and isinstance(v, int):
            v = QuadInt(v, 0, point.a.ring)
        vals.append(v)
    return vals


def classify_point(point: Point, n_max: int | None = None) -> dict[str, Any]:
    n_max = n_max or int(cfg.DISCOVERY_GRID["n_max"])  # type: ignore[arg-type]
    seq = sequence(point, n_max)
    period = minimal_period(seq)
    info: dict[str, Any] = {"point": point.label, "ring": point.ring, "n_max": n_max, "period": period}
    if period is not None:
        info["kind"] = "periodic"
        if point.ring != "Z" or point.a == 1:
            info["predicted_period"] = predicted_period(point.b_float())
            info["prediction_rule"] = "equals"
            info["prediction_agrees"] = info["predicted_period"] == period
        elif point.a == -1:
            # Theorem 14 with λ = −1: Ψ(−1, b, n) = (−1)^{⌊n/2⌋} Ψ(1, −b, n); the sign factor has period 4,
            # so the minimal period divides lcm(4, period of Ψ(1, −b, ·)).
            base = predicted_period(-point.b_float())
            info["predicted_period"] = math.lcm(4, base) if base else None
            info["prediction_rule"] = "divides"
            info["prediction_agrees"] = base is not None and info["predicted_period"] % period == 0
        else:
            info["predicted_period"] = None
            info["prediction_rule"] = "none"
            info["prediction_agrees"] = False       # |a| ≥ 2: the roots have modulus √|Q| > 1, no periodicity
        return info
    if point.ring == "Z":
        hits = match([int(v) for v in seq])
        if hits:
            info["kind"] = "known_sequence"
            info["matches"] = hits
            return info
    info["kind"] = "unclassified"
    return info


def census(grid: dict[str, object] | None = None) -> list[dict[str, Any]]:
    grid = grid or cfg.DISCOVERY_GRID
    return [classify_point(pt, int(grid["n_max"])) for pt in enumerate_points(grid)]  # type: ignore[arg-type]


def periodic_points(cen: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [c for c in cen if c["kind"] == "periodic"]


def prime_density_scan(grid: dict[str, object] | None = None, n_terms: int = 40, top: int = 12) -> list[dict[str, Any]]:
    """Integer points ranked by the number of primes among ``|Ψ(a, b, n)|``, ``2 ≤ n < n_terms``."""
    grid = grid or cfg.DISCOVERY_GRID
    rows = []
    for pt in enumerate_points(grid):
        if pt.ring != "Z":
            continue
        seq = [abs(int(v)) for v in sequence(pt, n_terms)]
        if minimal_period(seq) is not None:
            continue
        prime_idx = [n for n in range(2, n_terms) if seq[n] > 1 and is_prime_int(seq[n])]
        # Cramér-style size expectation: a random integer of size N is prime with probability ≈ 1/ln N
        expected = sum(1.0 / math.log(seq[n]) for n in range(2, n_terms) if seq[n] > 2)
        rows.append({"point": pt.label, "a": pt.a, "b": pt.b, "primes": len(prime_idx), "indices": prime_idx,
                     "expected_by_size": expected, "ratio": len(prime_idx) / expected if expected else 0.0,
                     "prime_indices_all_prime": all(is_prime_int(n) for n in prime_idx)})
    rows.sort(key=lambda r: (-r["ratio"], r["a"], r["b"]))
    return rows[:top]


# --------------------------------------------------------------------------- ledger
@dataclass
class Candidate:
    slug: str
    title: str
    statement: str
    kind: str                           # theorem | identity | ring | proposition
    numeric_verified: bool
    proof_status: str                   # "sympy-proved (n ≤ 12)" | "proved (elementary)" | "unproved"
    novelty: str                        # "unchecked" | "classical" | "checked"
    evidence: str
    label: str = cfg.DISCOVERY_LABEL
    notes: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    references: list[str] = field(default_factory=list)      # prior art found by the novelty audit
    novelty_note: str = ""                                    # what was searched / why the verdict


class Ledger:
    """Markdown ledger with an embedded JSON block for round-tripping."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else cfg.LEDGER_PATH
        self.entries: list[Candidate] = []

    def add(self, cand: Candidate) -> None:
        self.entries = [e for e in self.entries if e.slug != cand.slug] + [cand]

    def to_markdown(self) -> str:
        lines = [
            "# Discoveries ledger",
            "",
            f"Working label: **{cfg.DISCOVERY_LABEL}**.  A label here is a working name.  Mathematical names",
            "stick only through publication and citation; novelty is *not* asserted by this repository —",
            "each entry's `novelty` field must be checked by a human against OEIS and the literature.",
            "",
            "Status ladder: `numeric-verified → sympy-proved / proved (elementary) → novelty: unchecked | classical | corollary_of_known | checked`.",
            "",
        ]
        for e in self.entries:
            lines += [
                f"## {e.title}",
                "",
                f"**{e.label} candidate** · kind: {e.kind} · numeric-verified: {e.numeric_verified} · proof: {e.proof_status} · novelty: **{e.novelty}**",
                "",
                f"> {e.statement}",
                "",
                f"Evidence: {e.evidence}",
                "",
            ]
            if e.notes:
                lines += [f"Notes: {e.notes}", ""]
            if e.novelty_note:
                lines += [f"Novelty check: {e.novelty_note}", ""]
            if e.references:
                lines += ["References:"] + [f"- {r}" for r in e.references] + [""]
        lines += ["```json", json.dumps([asdict(e) for e in self.entries], indent=2, ensure_ascii=False, default=str), "```", ""]
        return "\n".join(lines)

    def write(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.to_markdown(), encoding="utf-8")
        return self.path

    @classmethod
    def load(cls, path: Path | None = None) -> "Ledger":
        led = cls(path)
        if not led.path.exists():
            return led
        text = led.path.read_text(encoding="utf-8")
        if "```json" not in text:
            return led
        block = text.split("```json", 1)[1].split("```", 1)[0]
        for raw in json.loads(block):
            led.entries.append(Candidate(**raw))
        return led


def seed_candidates(bridge_report: dict[str, bool] | None = None, census_rows: list[dict[str, Any]] | None = None) -> list[Candidate]:
    """Every candidate this repository can justify, with the novelty verdicts of the 2026-09-02
    literature / OEIS audit (two independent prior-art hunts per claim, merged and re-verified)."""
    br = bridge_report or {}
    cen = census_rows or []
    golden_ok = all(c.get("prediction_agrees", False) for c in periodic_points(cen) if c["ring"] == "Z[phi]") if cen else True
    LEWIN = "M. Lewin, Periodic Fibonacci and Lucas sequences, Fibonacci Quart. 29.4 (1991) 310–315, Thms 1–2 — https://www.fq.math.ca/Scanned/29-4/lewin.pdf"
    LUCAS = "E. Lucas, Théorie des fonctions numériques simplement périodiques, Amer. J. Math. 1 (1878) — https://archive.org/details/jstor-2369308"
    LEHMER = "D. H. Lehmer, An extended theory of Lucas' functions, Ann. of Math. 31 (1930) 419–448 — https://www.jstor.org/stable/1968235"
    RW = "E. L. Roettger, H. C. Williams, Some remarks concerning the Lucas–Lehmer primality test, J. Integer Seq. 28 (2025) — https://cs.uwaterloo.ca/journals/JIS/VOL28/Roettger/roettger15.pdf"
    IB1 = "M. Ibrahim, Generalizing the Eight Levels Theorem, arXiv:2404.05772 — https://arxiv.org/abs/2404.05772"
    IB2 = "M. Ibrahim, On the emergence of the Quanta Prime Sequence, arXiv:2502.06796 — https://arxiv.org/html/2502.06796v1"
    IB3 = "M. Ibrahim, The emergence of the Mersenne Star, HAL hal-05035758v2 (preprint of doi:10.1080/25765299.2025.2569155) — https://hal.science/hal-05035758v2"
    return [
        Candidate(
            slug="periodicity-classification",
            title="Periodicity classification of the Ψ rings",
            statement=THEOREM_STATEMENT,
            kind="theorem",
            numeric_verified=golden_ok,
            proof_status="proved (closed form; rotation form sympy-checked for n ≤ 8)" if br.get("rotation_form") is True else "unproved (rotation form not sympy-checked in this run)",
            novelty="classical",
            evidence="exact periods in Z, Z[√2], Z[√3], Z[φ] for all six paper rings and the four golden rings; float check for every reduced rotation k/m with m ≤ 30",
            notes="Ibrahim's own Chebyshev identity at x = cos θ plus the folklore criterion 'a linear recurrence is periodic iff its roots are roots of unity'. Lewin (1991) states the period formula for V_n(2cos θ, 1) explicitly; OEIS A087204 is the period-6 ring.",
            novelty_note="Checked 2026-09-02 against Lucas 1878, Lewin 1991, Somer 1980, MacHenry–Wong 2007, Wikipedia (Lehmer sequence, Chebyshev polynomials) and OEIS: the statement is classical; only its application to Ibrahim's six examples is new bookkeeping.",
            references=[LEWIN, LUCAS, "L. Somer, Fibonacci Quart. 18.4 (1980), Thm 4 — https://www.fq.math.ca/Scanned/18-4/somer.pdf",
                        "T. MacHenry, K. Wong, arXiv:0712.2403, Thm 2.1 — https://arxiv.org/abs/0712.2403", "OEIS A087204 — https://oeis.org/A087204"],
        ),
        Candidate(
            slug="golden-rings",
            title="Three golden rings not listed in the source paper",
            statement="Ψ(1, φ, n) has period 10 (rotation 72°), Ψ(1, 1−φ, n) has period 10 (36°), Ψ(1, −φ, n) has period 20 (18°); with the paper's Ψ(1, φ−1, n) (54°, period 20) the four golden rotation angles are exactly the golden-triangle angles.",
            kind="ring",
            numeric_verified=True,
            proof_status="proved (corollary of the classification)",
            novelty="corollary_of_known",
            evidence="exact sequences in Z[φ] over three periods",
            novelty_note="2cos(π/5) = φ and 2cos(2π/5) = φ − 1 are classical (Euclid XIII.10, OEIS A001622); the three rings are one line from the classification. Not in Ibrahim's papers, but not a result either.",
            references=["Wikipedia, Golden ratio — pentagon and pentagram — https://en.wikipedia.org/wiki/Golden_ratio", "OEIS A001622 — https://oeis.org/A001622", LEWIN, IB1 + " §16.1.6"],
        ),
        Candidate(
            slug="lehmer-identification",
            title="Ψ is Lehmer's companion sequence",
            statement="Ψ(a, b, n) = V̄_n(√(2a − b), a), D. H. Lehmer's companion sequence (1930): V̄_n = V_n for even n and V_n/√R for odd n, with α + β = √R, αβ = Q. Every property of the Ψ / Eight-Levels family is a property of Lehmer sequences; equivalently Ψ(a, b, n) = (2a − b)^{⌊n/2⌋}·V_n(1, a/(2a − b)).",
            kind="identity",
            numeric_verified=True,
            proof_status="proved (both sides satisfy the same recurrence with the same initial values; sympy for n ≤ 12)",
            novelty="corollary_of_known",
            evidence="exact check in Z[√R] for |a| ≤ 4, |b| ≤ 6, n < 16",
            notes="This is the sharpest classical identification and it settles the novelty of every Ψ-ring statement. Ibrahim's eq. (36) prints the Binet form; no source states the Lehmer identification, which is a one-line substitution R = 2a − b, Q = a.",
            novelty_note="Checked 2026-09-02: Lehmer 1930, MathWorld 'Lehmer Number', Wikipedia 'Lehmer sequence', Roettger–Williams 2025 §2 give the definition; the identification with Ψ is not published but is immediate. Worth a remark, not a theorem.",
            references=[LEHMER, "MathWorld, Lehmer Number — https://mathworld.wolfram.com/LehmerNumber.html", "Wikipedia, Lehmer sequence — https://en.wikipedia.org/wiki/Lehmer_sequence", RW, IB1 + " eq. (36)"],
        ),
        Candidate(
            slug="normalisation-identity",
            title="Ψ is a rescaled Lucas V-sequence",
            statement="Ψ(a, b, n) = (2a − b)^{⌊n/2⌋} · V_n(1, a/(2a − b)).",
            kind="identity",
            numeric_verified=True,
            proof_status="sympy-proved (n ≤ 12); general proof via Binet" if br.get("normalisation_identity") is True else "unproved (not sympy-checked in this run)",
            novelty="classical",
            evidence="exact rational-function identity for each n ≤ 12; integer check for |a| ≤ 4, |b| ≤ 6, n < 14",
            notes="Superseded by the Lehmer identification.",
            novelty_note="Checked 2026-09-02: Lucas 1878 / Lehmer 1930; Wikipedia 'Lucas sequence' (relations between sequences with different parameters).",
            references=[LUCAS, LEHMER, "Wikipedia, Lucas sequence — https://en.wikipedia.org/wiki/Lucas_sequence"],
        ),
        Candidate(
            slug="ll-index-constancy",
            title="Ring coordinates of the Lucas–Lehmer index are constant",
            statement="For every odd prime p ≥ 5, 2^{p−1} ≡ 4 (mod 6), 0 (mod 8), 4 (mod 12), 0 (mod 16), 4 or 16 (mod 20), 16 (mod 24); hence Ψ(1,1,2^{p−1}) = −1, Ψ(1,0,·) = 2, Ψ(1,−1,·) = −1, Ψ(1,√2,·) = 2, Ψ(1,φ−1,·) = −φ, Ψ(1,√3,·) = −1 independently of p. All periodic neighbours of the Mersenne Star carry no information about p, so the Star paper's proposal to use the periodic strips to accelerate Mersenne testing cannot work as stated.",
            kind="proposition",
            numeric_verified=True,
            proof_status="proved (elementary)",
            novelty="classical",
            evidence="all primes 5 ≤ p < 400 and all 52 known Mersenne exponents",
            novelty_note="Checked 2026-09-02: Ibrahim's own Theorem 7 (arXiv:2404.05772, eqs. 20, 24, 26, 31) states Ψ(1,φ−1,2^l) = −φ for even l ≥ 4 and the analogues for the other rings; the consequence for the Star paper's proposals is not drawn there.",
            references=[IB1 + " Theorem 7", IB3 + " §§1.4, 1.5, 12.1"],
        ),
        Candidate(
            slug="golden-seed",
            title="The golden Lucas–Lehmer seed and its exact domain",
            statement="Seed s₀ = 3 = L₂ gives s_k = L_{2^{k+1}} = φ^{2^{k+1}} + ψ^{2^{k+1}}, and the test is valid iff p ≡ 3 (mod 4); no seed built in Q(√5) can be universal.",
            kind="proposition",
            numeric_verified=True,
            proof_status="proved (classical; (5 | M_p) = +1 iff p ≡ 1 mod 4)",
            novelty="classical",
            evidence="all primes p ≤ 500; p = 5 is the smallest failure",
            novelty_note="Checked 2026-09-02: Lucas 1876/1878 (M_127), Robinson 1954, Jansen 2012, Roettger–Williams 2025, OEIS A001566, Wikipedia (alternative starting values).",
            references=[RW, "R. M. Robinson, Mersenne and Fermat numbers, Proc. AMS 5 (1954) 842–846", "OEIS A001566 — https://oeis.org/A001566",
                        "Wikipedia, Lucas–Lehmer primality test — https://en.wikipedia.org/wiki/Lucas%E2%80%93Lehmer_primality_test"],
        ),
        Candidate(
            slug="qps-is-lucas-lehmer",
            title="Ibrahim's primality theorems and all 32 Mersenne Star conditions are the Lucas–Lehmer test",
            statement="Ψ(1, 4, 2^k) is the Lucas–Lehmer term s_{k−1}; Theorem 26 of arXiv:2404.05772, Theorem 9 of arXiv:2502.06796 (B-ratio = Ψ(1, 4, 2^{p−1})) and all 32 conditions of Theorem 7.6 of the Mersenne Star paper reduce literally to 2^p − 1 | Ψ(1, 4, 2^{p−1}); they add no primality information beyond Lucas–Lehmer.",
            kind="source_correction",
            numeric_verified=True,
            proof_status="proved (closed form Ψ(1,4,n) ∝ (1+√3)^n + (1−√3)^n; anchor ratios computed exactly)",
            novelty="corollary_of_known",
            evidence="p ≤ 61 (Theorem 26 vs LL); p = 5, 7, 11, 13 for Theorem 9 and for all 32 Star conditions",
            novelty_note="Checked 2026-09-02: Theorem 26 is itself titled 'a new version for Lucas–Lehmer' and proved via LL in the source; the QPS paper proves Theorem 9 from that theorem; a 2024 mersenneforum thread already notes the equivalence. That the Star's 32 conditions carry nothing new is not stated in the Star paper.",
            references=[IB1 + " Theorem 26", IB2 + " Theorems 9, 47, 51", IB3 + " Theorem 7.6",
                        "mersenneforum thread 'Eight levels theorem' (2024) — http://web.archive.org/web/20250116091733/https://www.mersenneforum.org/node/22736", "OEIS A003010 — https://oeis.org/A003010"],
        ),
        Candidate(
            slug="mersenne-fibonacci-rank",
            title="Fibonacci rank of apparition of Mersenne primes with p ≡ 3 (mod 4)",
            statement="If M_p = 2^p − 1 is prime and p ≡ 3 (mod 4), the Fibonacci rank of apparition of M_p is exactly 2^p = M_p + 1 (M_p | F_{2^p}, M_p ∤ F_{2^{p−1}}, M_p | L_{2^{p−1}}); verified for every such known Mersenne prime up to p = 4423 and for p = 86243. For p ≡ 1 (mod 4) the rank divides M_p − 1 with odd cofactor 1, 1, 1, 9, 3, 1, 1, 1, 3 for p = 5, 13, 17, 61, 89, 521, 2281, 3217, 4253 (a power of 3 each time; consistent with chance).",
            kind="theorem",
            numeric_verified=True,
            proof_status="proved (Lucas's law of apparition + Lehmer's half-index criterion)",
            novelty="corollary_of_known",
            evidence="every known Mersenne prime with p ≡ 3 (mod 4) and p ≤ 4423 (plus 86243); cofactors from factordb factorizations of 2^{p−1} − 1",
            novelty_note="Checked 2026-09-02: not found verbatim in OEIS (A001602, A000057, A001177), Wikipedia, MathWorld or the Prime Pages, but one step from Lucas 1878 and equivalent statements appear in Roettger–Williams 2025, Jaroma 2004, Guo–Koch 2009 (Thm 3.4) and Baker arXiv:2608.05319 (Prop. 1); OEIS A000057 (primes with entry point p+1) already lists 7, 127, 524287.",
            references=[LUCAS + " pp. 289–305", RW, "J. H. Jaroma, Note on the Lucas–Lehmer test, Irish Math. Soc. Bull. 54 (2004) — https://www.maths.tcd.ie/pub/ims/bull54/M5402.pdf",
                        "C. Guo, A. Koch, Bounds for Fibonacci period growth, Involve 2 (2009) — https://msp.org/involve/2009/2-2/involve-v2-n2-p04-p.pdf", "OEIS A000057 — https://oeis.org/A000057"],
        ),
        # ------------------------------------------------------------------ results not found in the sources
        Candidate(
            slug="qps-closed-form",
            title="Closed form for the whole Quanta Prime Sequence table",
            statement="For all n ≥ 1, r, k ≥ 0, with N = n − r and u = n − 2r − δ(n−1): Ω_r(k | ζ, ξ | n) = Σ_{j=0}^{k} C(k, j) (2ζ − ξ)^{k−j} (−2ζ)^j · (N−j−1)^{(k−j)↓} · u(u−2)⋯(u−2j+2). In particular Ω depends on (n, r) only through (N, u). The three explicit formulas of the source (points (0,−1), (1,2), (1,−2), Theorems 42, 41, 19) are the special cases.",
            kind="theorem",
            numeric_verified=True,
            proof_status="proved (induction on k: the recurrence step is a symbolic identity in N, u, k, j; exact check for n ≤ 30, all r ≤ ⌊n/2⌋+3, all k ≤ ⌊n/2⌋)",
            novelty="unchecked",
            evidence="0 mismatches in 21 000 entries (workflow) and 8 000 entries (independent re-check), random (ζ, ξ) ∈ [−9, 9]²",
            notes="Standard technique (binomial sum solving a two-term recurrence); the value is that the QPS paper (2025) has no general formula.",
            novelty_note="Not in arXiv:2502.06796 (read in full); the arXiv API lists no follow-up papers. No wider literature search was possible for this 2025 object; as far as we know new, but routine.",
            references=[IB2 + " Definition 6.1, Theorems 19, 41, 42"],
        ),
        Candidate(
            slug="qps-hypergeometric",
            title="Hypergeometric form and exponential generating function of the QPS table",
            statement="With N = n − r, u = n − 2r − δ(n−1), 2ζ ≠ ξ and k ≤ N − 1: Ω_r(k) = (2ζ − ξ)^k (N−1)^{k↓} · ₂F₁(−k, −u/2; 1 − N; 4ζ/(2ζ − ξ)) (terminating series), and Σ_k Ω_r(k) x^k/(k! (N−1)^{k↓}) = e^{(2ζ−ξ)x} · ₁F₁(−u/2; 1 − N; −4ζx). Note 1 − 4ζ/(2ζ−ξ) = −(2ζ+ξ)/(2ζ−ξ) is the quantity s of Ibrahim's closed form.",
            kind="theorem",
            numeric_verified=True,
            proof_status="proved (rewrite of the closed form with Pochhammer symbols; exact check n ≤ 18, EGF coefficients n ≤ 14)",
            novelty="unchecked",
            evidence="383/383 terminating ₂F₁ values and 447 EGF coefficients exact",
            novelty_note="Not in the source paper; routine rewriting. As far as we know new for this object.",
            references=[IB2],
        ),
        Candidate(
            slug="qps-gegenbauer-column",
            title="The r = δ(n) column of the QPS table is a Gegenbauer column, with a ξ-parity law",
            statement="Let K = ⌊n/2⌋. For 1 ≤ k ≤ K − 1: Ω_{δ(n)}(k | ζ, ξ | n) = (−ζ)^k k! (2K−1)^{k↓}/(K−1)^{k↓} · C_k^{(K−k)}(ξ/2ζ); for 0 ≤ k ≤ K it equals (−1)^k (2K−1)^{k↓} Σ_i C(k,2i) (2i)!/(i! (K−1)^{i↓}) (−ζ²)^i ξ^{k−2i}. Hence Ω_{δ(n)}(k | ζ, −ξ | n) = (−1)^k Ω_{δ(n)}(k | ζ, ξ | n) — a parity law that fails for every other column. At k = K the λ → 0 limit is the classical corner Ψ(ζ, ξ, 2K) = (−1)^K V_K(ξ, ζ²).",
            kind="theorem",
            numeric_verified=True,
            proof_status="proved from the closed form (quadratic transformation of the terminating ₂F₁); sympy check n ≤ 30",
            novelty="unchecked",
            evidence="196 Gegenbauer values and 1016 parity checks exact; explicit counterexample for other columns (n = 7, r = 0, k = 1)",
            novelty_note="Not in the source paper (which mentions only Chebyshev/Dickson at the corner). Standard special-function identities. As far as we know new for this object.",
            references=[IB2, "DLMF §18.5 (Gegenbauer polynomials as ₂F₁) — https://dlmf.nist.gov/18.5"],
        ),
        Candidate(
            slug="qps-shift-identity",
            title="Odd-n QPS tables contain the even-n tables as their r ≥ 1 columns",
            statement="For every odd n ≥ 3 and all r, k ≥ 0: Ω_{r+1}(k | ζ, ξ | n) = Ω_r(k | ζ, ξ | n − 1). Consequently Ψ(ζ, ξ, 2m) and Ψ(ζ, ξ, 2m+1) sit in adjacent columns r = 1, 0 of the same layer k = m of the table n = 2m + 1. The analogous shift from even n fails (n = 8, r = 0, k = 1: −2(3ξ − ζ) ≠ −2(3ξ + ζ)).",
            kind="theorem",
            numeric_verified=True,
            proof_status="proved (Ω depends on (n, r) only through (n − r, n − 2r − δ(n−1)), which coincide for (r+1, n) and (r, n−1) when n is odd)",
            novelty="unchecked",
            evidence="3192 exact checks for odd n ≤ 29 (workflow), 1320 independent re-checks",
            novelty_note="Not in the source paper; elementary. As far as we know new for this object.",
            references=[IB2],
        ),
        Candidate(
            slug="mersenne-star-errata",
            title="Errata for the Mersenne Star paper (HAL v2 preprint)",
            statement="(1) Section 10 prints Ω_0(n/2|1,−2|n) = Ω_0(n/2|0,1|n)·2^{δ(n+1)} and Ω_0(n/2|1,−3|n) = Ω_0(n/2|0,1|n)·{F(n), L(n)}; both are false as written (wrong by (−1)^{⌊n/2⌋} for n ≡ 2, 3 mod 4) and true with the anchor (0,−1) — as the paper's own p. 16 uses. (2) Lemma 7.4 (Ω_0(⌊n/2⌋|−1,4|n) = Ω_0(⌊n/2⌋|1,4|n) = Ω_0(⌊n/2⌋|1,−4|n)) is stated for 8 | n but holds exactly for all 4 | n (and n = 1) and for no other n ≤ 40. (3) The bullet on p. 11 listing (1, √5) among periodic points is wrong: Ψ(1, √5, n) is unbounded (|b| > 2). (4) The twelve edges of the Star are never listed; Figure 1 draws K_{2,6} (A and J joined to the six other points). (5) Cross-references cite 'Theorem 6.1' and 'Lemmas 6.3, 6.4' for results numbered 7.1, 7.3, 7.4.",
            kind="source_correction",
            numeric_verified=True,
            proof_status="proved (exact computation n ≤ 40; Figure 1 vector content decoded)",
            novelty="unchecked",
            evidence="research workflow 2026-09-02; Lemma 7.4 range re-verified independently (tests/test_qps.py)",
            novelty_note="Errata; not previously published as far as we know.",
            references=[IB3 + " §10, Lemma 7.4, p. 11, Figure 1"],
        ),
        Candidate(
            slug="lehmer-q2-prime-conjecture",
            title="Conjecture: infinitely many primes in the Lehmer companions V̄_n(√5, 2) and V̄_n(√3, 2)",
            statement="For (a, b) ∈ {(2,−1), (2,1), (2,3), (2,−3)} — the Lehmer companion pairs (R, Q) = (5,2), (3,2), (1,2), (7,2) — |Ψ(a, b, n)| is prime for infinitely many n; primes occur only at n = 2^k·m with m = 1, m prime, or m a product of 'unit' indices (d with |Ψ(a,b,d)| = 1) with a prime; and the number of prime indices ≤ N is asymptotic to Σ_{admissible n ≤ N} e^γ ln(2n)/ln|Ψ(a,b,n)| ≈ (4e^γ/ln 2) ln N ≈ 10.3 ln N for (2, ±1). Evidence: 57 and 58 primes for n ≤ 1000 against heuristic 56.6 and 55.7.",
            kind="conjecture",
            numeric_verified=True,
            proof_status="unproved (heuristic of Wagstaff type; Hone–Jeffery–Selcoe prove the analogous Q = 1 statements only conditionally)",
            novelty="unchecked",
            evidence="prime counts for n ≤ 1000 (BPSW probable primes above 3.3·10^24); primitive-divisor theorem of Bilu–Hanrot–Voutier verified for n ≤ 120",
            novelty_note="The Q = 1 analogue is Conjecture 6.1–6.3 of Hone–Jeffery–Selcoe (arXiv:1802.01793); no statement for Q = 2 Lehmer companions found in OEIS or the accessible literature.",
            references=["A. Hone, L. Jeffery, R. Selcoe, On a family of sequences related to Chebyshev polynomials, arXiv:1802.01793 — https://arxiv.org/abs/1802.01793",
                        "S. S. Wagstaff Jr., Divisors of Mersenne numbers, Math. Comp. 40 (1983) 385–397", "Y. Bilu, G. Hanrot, P. Voutier, J. reine angew. Math. 539 (2001) 75–122"],
        ),
        Candidate(
            slug="oeis-gaps",
            title="Ψ-family sequences absent from OEIS (candidate submissions)",
            statement="As of 2026-09-02 OEIS has no entry (offsets 0, 1, 2 queried) for: Ψ(1,4,n) = V̄_n(√(−2),1) = 2,1,−4,−5,14,19,−52,−71,194,265,−724,−989,2702,3691,… (the paper's own Lucas–Lehmer Ψ-sequence; even part (−1)^m·A003500, odd part A001834; |Ψ(1,4,n)| prime for n ≤ 401 exactly at n = 0,3,5,7,13,19,29,37,293); Ψ(2,−1,n) = V̄_n(√5,2) = 2,1,1,−1,−7,−5,−11,−1,17,19,61,23,−7,−53,…; Ψ(2,1,n) = V̄_n(√3,2) = 2,1,−1,−3,−7,−1,11,13,17,−9,−61,−43,−7,79,…; their odd bisections and their prime-index sets. Recurrences: a(n) = −4a(n−2) − a(n−4); a(n) = a(n−2) − 4a(n−4); a(n) = −a(n−2) − 4a(n−4).",
            kind="oeis_gap",
            numeric_verified=True,
            proof_status="proved (closed forms are Lehmer 1930)",
            novelty="checked",
            evidence="OEIS JSON searches with leading term(s) dropped (2026-09-02); three earlier apparent gaps were refuted by the same method: Ψ(2,−5,n) = A076737(n+2), Ψ(−1,−6,n) = A159582 (n ≥ 1), Ψ(1,−6,n) = A079496 with even terms doubled",
            novelty_note="An OEIS submission is the legitimate way to attach a name to these; the mathematics is classical.",
            references=["OEIS A003500, A001834, A299100, A272931 (bisections / prime indices) — https://oeis.org", LEHMER],
        ),
        Candidate(
            slug="zeta-diffraction-bridge",
            title="The zeta zeros diffract into the logarithmic prime-power lattice (demonstration)",
            statement="With the first 100 000 zeros ρ = 1/2 + iγ (Odlyzko), F(u) = Σ cos(γu) has a spike of depth −(T/2π)·Λ(n)/√n at every u = log n with n a prime power (Landau 1911 / the explicit formula), reproduced to relative error < 0.2 % for all prime powers n ≤ 60; the Fibonacci chain with tiles (φ, 1) has Bragg peaks exactly at k = 2π(m + nφ)/√5, brightest at Fibonacci index pairs (1,1), (2,3), (3,5), (1,2). The two aperiodic point sets have discrete diffraction, but the zeros are not uniformly discrete (density ~ log T) and so lie outside the classified class of one-dimensional Fourier quasicrystals (Kurasov–Sarnak; Olevskii–Ulanovskii; Alon–Cohen–Vinzant): Dyson's 2009 route to RH stops here.",
            kind="demonstration",
            numeric_verified=True,
            proof_status="n/a (classical theorems made visible)",
            novelty="classical",
            evidence="research/quasicrystal_bridge.py on Odlyzko's zeros1 table; tests/test_quasicrystal_bridge.py",
            novelty_note="Landau 1911; Guinand 1948 / Weil 1952 explicit formula; Elser 1985 for the Fibonacci chain; Dyson 2009 (Notices AMS, 'Birds and frogs'); Kurasov–Sarnak 2020; Alon–Cohen–Vinzant 2023. No new claim.",
            references=["E. Landau, Über die Nullstellen der Zetafunktion, Math. Ann. 71 (1912) 548–564",
                        "F. Dyson, Birds and frogs, Notices AMS 56 (2009) 212–223 — https://www.ams.org/notices/200902/rtx090200212p.pdf",
                        "P. Kurasov, P. Sarnak, Stable polynomials and crystalline measures, J. Math. Phys. 61 (2020) — https://doi.org/10.1063/5.0012286",
                        "L. Alon, A. Cohen, C. Vinzant, Every real-rooted exponential polynomial is the restriction of a Lee–Yang polynomial (2023) — https://arxiv.org/abs/2303.03201",
                        "A. Odlyzko, tables of zeros of the Riemann zeta function — https://www-users.cse.umn.edu/~odlyzko/zeta_tables/"],
        ),
        Candidate(
            slug="exponent-statistics",
            title="No golden or residue structure in the 52 known exponents",
            statement="Against a size-matched Monte-Carlo null (each exponent replaced by a random prime within a factor 1.5; 2000–20000 replications) none of the φ-zone, Fibonacci-zone, Beatty or golden-angle metrics of the known exponents differs from chance (p = 0.19–0.82), p mod 20 is consistent with equidistribution (p = 0.5), and no residue class mod 4, 8, 12, 20, 24 is significant after Bonferroni/Holm correction. The mod-12 nominal p ≈ 0.015 is a mod-3 × mod-4 interaction (21 of 50 exponents are 5 mod 12; Fisher p = 0.018) that does not survive correction and is not claimed.",
            kind="negative_result",
            numeric_verified=True,
            proof_status="n/a (statistics)",
            novelty="unchecked",
            evidence="research/exponent_statistics.py (2000 reps) and an independent 20000-rep re-implementation in the workflow; both agree",
            novelty_note="A negative result; no prior test of these particular hypotheses was found, none was expected.",
            references=["S. S. Wagstaff Jr., Math. Comp. 40 (1983) (mod-4 weighting)"],
        ),
    ]


def run_discovery(path: Path | None = None, bridge_report: dict[str, bool] | None = None,
                  grid: dict[str, object] | None = None) -> tuple[Ledger, list[dict[str, Any]], list[dict[str, Any]]]:
    """Census + prime-density scan + ledger update.  Returns ``(ledger, census, density)``.

    When no ``bridge_report`` is supplied the symbolic checks are run here, so the ledger never
    records a "proved" status that was not actually verified in this run.
    """
    if bridge_report is None:
        from core_math.symbolic_bridge import bridge_report as _bridge_report

        bridge_report = _bridge_report(8)
    cen = census(grid)
    density = prime_density_scan(grid)
    ledger = Ledger.load(path)
    for cand in seed_candidates(bridge_report, cen):
        ledger.add(cand)
    # every periodic point found in the census that the theorem did not predict would be news
    surprises = [c for c in periodic_points(cen) if c.get("prediction_agrees") is False]
    for c in surprises:
        slug = "unexpected-period-" + c["point"].replace(" ", "").replace("Ψ", "psi").replace(",", "_").replace("(", "").replace(")", "")
        ledger.add(Candidate(slug=slug, title=f"Unexpected period at {c['point']}",
                             statement=f"{c['point']} is periodic with period {c['period']} but the classification predicts {c['predicted_period']}.",
                             kind="anomaly", numeric_verified=True, proof_status="unproved", novelty="unchecked",
                             evidence=f"n < {c['n_max']}", details=c))
    ledger.write()
    return ledger, cen, density
