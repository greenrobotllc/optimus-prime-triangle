"""Verification of contributor, claim and result files — the trust anchor of the pilot.

CI runs these with the base branch's code: byte-canonical form, signature, identity binding,
family hash, worker-version allow-list, candidate-set equality, and a full recomputation of every
verdict with the worker's own Fermat base.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from .canon import CanonError, check_file_bytes
from .compute import summarize, verdict
from .families import Family, abs_value, check_filter_witness, filter_witness, is_candidate, variants_for
from .keys import SignatureError, verify_envelope, verify_rotation
from .units import candidates, parse_unit_id, worker_base

LOGIN_RE = re.compile(r"^(?:[a-z0-9-]{1,39}|ext-[a-z0-9-]{1,32})$")
FP_RE = re.compile(r"^k1:[0-9a-f]{64}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
HEX16_RE = re.compile(r"^[0-9a-f]{16}$")
ALLOWED_DIRS = ("distributed/contributors/", "distributed/claims/", "distributed/results/")
RESULT_SCHEMA = "oeis-home/v1/result"


@dataclass
class Report:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    lines_checked: int = 0
    recomputed: int = 0
    prp_confirmed: list[int] = field(default_factory=list)
    wall_ms: int = 0
    payload: dict | None = None

    def fail(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)


def _read_envelope(path: Path, kind: str, rep: Report) -> tuple[dict | None, str]:
    try:
        env = check_file_bytes(Path(path).read_bytes())
        fp = verify_envelope(env, kind)
        return env, fp
    except (CanonError, SignatureError, OSError) as exc:
        rep.fail(f"{path.name}: {exc}")
        return None, ""


# --------------------------------------------------------------------------- contributors
def verify_contributor_file(path: Path, pr_author_id: int | None, existing: dict[str, dict], maintainer: bool = False) -> Report:
    rep = Report()
    env, fp = _read_envelope(path, "contributor", rep)
    if env is None:
        return rep
    p = env["payload"]
    required = {"login", "github_id", "fingerprint", "pubkey", "display_name", "oeis_credit_name", "role"}
    if not required <= set(p):
        rep.fail(f"{path.name}: missing fields {sorted(required - set(p))}")
        return rep
    login = p["login"]
    if not isinstance(login, str) or not LOGIN_RE.match(login) or Path(path).stem != login:
        rep.fail(f"{path.name}: login must match the file name and ^[a-z0-9-]+$ / ext-")
    if not isinstance(p["github_id"], int) or p["github_id"] < 0 or (login.startswith("ext-") != (p["github_id"] == 0)):
        rep.fail(f"{path.name}: github_id must be the numeric id (0 only for ext- logins)")
    if p["fingerprint"] != fp or p["fingerprint"] != env["signature"]["key"] or p["pubkey"] != env["signature"]["pubkey"]:
        rep.fail(f"{path.name}: fingerprint/pubkey do not match the signing key")
    if not isinstance(p["display_name"], str) or not 1 <= len(p["display_name"]) <= 64:
        rep.fail(f"{path.name}: display_name must be 1–64 characters")
    if not isinstance(p["oeis_credit_name"], str) or len(p["oeis_credit_name"]) > 64:
        rep.fail(f"{path.name}: oeis_credit_name must be ≤ 64 characters")
    if p["role"] not in ("worker", "verifier", "bot") or (p["role"] != "worker" and not maintainer):
        rep.fail(f"{path.name}: role {p['role']!r} not allowed here")
    if pr_author_id is not None and not login.startswith("ext-") and pr_author_id != p["github_id"]:
        rep.fail(f"{path.name}: PR author id {pr_author_id} does not match github_id {p['github_id']}")
    if login.startswith("ext-") and pr_author_id is not None and not maintainer:
        rep.fail(f"{path.name}: ext- registrations must come from a maintainer")
    old = existing.get(login)
    if old is not None and old["fingerprint"] != p["fingerprint"]:
        if p.get("supersedes") != old["fingerprint"] or not isinstance(p.get("rotation_sig"), str):
            rep.fail(f"{path.name}: replacing a registered key needs supersedes + rotation_sig")
        elif not verify_rotation(bytes.fromhex(old["pubkey"]), bytes.fromhex(p["pubkey"]), p["rotation_sig"]):
            rep.fail(f"{path.name}: rotation_sig does not verify under the old key")
    rep.payload = p
    return rep


def load_contributors(repo: Path) -> dict[str, dict]:
    """All registered contributors on this checkout (verified envelopes only)."""
    out: dict[str, dict] = {}
    for path in sorted((Path(repo) / "distributed" / "contributors").glob("*.json")):
        rep = verify_contributor_file(path, None, {}, maintainer=True)
        if rep.ok and rep.payload:
            out[rep.payload["login"]] = rep.payload
    return out


# --------------------------------------------------------------------------- claims
def verify_claim_file(path: Path, fam: Family, contributors: dict[str, dict]) -> Report:
    rep = Report()
    env, fp = _read_envelope(path, "claim", rep)
    if env is None:
        return rep
    p = env["payload"]
    if set(p) != {"unit_id", "login", "worker", "family_hash", "nonce"}:
        rep.fail(f"{path.name}: claim payload fields")
        return rep
    try:
        parse_unit_id(p["unit_id"], fam.bands)
    except ValueError as exc:
        rep.fail(f"{path.name}: {exc}")
    c = contributors.get(p["login"])
    if c is None or c["fingerprint"] != fp or p["worker"] != fp:
        rep.fail(f"{path.name}: login/worker not registered or key mismatch")
    if p["family_hash"] != fam.hash:
        rep.fail(f"{path.name}: family_hash mismatch")
    if Path(path).name != f"{p['unit_id']}--{p['login']}.json":
        rep.fail(f"{path.name}: file name must be <unit_id>--<login>.json")
    rep.payload = p
    return rep


# --------------------------------------------------------------------------- results
def _check_verdict_shape(rec: dict, n: int, v: str, fam: Family, errors: list[str]) -> None:
    keys = set(rec)
    if not {"n", "variant", "v", "digits", "method"} <= keys:
        errors.append(f"n={n} {v}: missing verdict fields")
        return
    if rec["n"] != n or rec["variant"] != v:
        errors.append(f"n={n} {v}: candidate order mismatch (got n={rec['n']} {rec['variant']})")
    if rec["v"] not in ("prime", "prp", "composite", "unit") or rec["method"] not in ("small", "factor", "fermat", "bpsw", "cert"):
        errors.append(f"n={n} {v}: bad v/method {rec['v']}/{rec['method']}")
    if rec["method"] == "factor":
        if rec["v"] != "composite" or not isinstance(rec.get("factor"), str) or not rec["factor"].isdigit():
            errors.append(f"n={n} {v}: factor verdict malformed")
    if rec["method"] in ("fermat", "bpsw") and not (isinstance(rec.get("res64"), str) and HEX16_RE.match(rec["res64"])):
        errors.append(f"n={n} {v}: res64 missing or malformed")
    if rec["v"] == "prp" and (rec["method"] != "bpsw" or not isinstance(rec.get("sprp"), list)):
        errors.append(f"n={n} {v}: prp must carry method bpsw and sprp bases")
    if rec["v"] == "prime" and rec["method"] == "cert" and not isinstance(rec.get("cert"), dict):
        errors.append(f"n={n} {v}: cert verdict without certificate")


def recompute_line(fam: Family, rec: dict, base: int) -> dict:
    return verdict(fam, rec["variant"], rec["n"], base)


def _same_verdict(mine: dict, theirs: dict) -> bool:
    if mine["v"] != theirs["v"] or mine["method"] != theirs["method"] or mine["digits"] != theirs["digits"]:
        return False
    for k in ("factor", "res64", "sprp"):
        if mine.get(k) != theirs.get(k):
            return False
    return True


def verify_result_file(path: Path, fam: Family, contributors: dict[str, dict], releases: dict, full: bool = True,
                       time_budget_s: float | None = None, reference_check: bool = True) -> Report:
    t0 = time.perf_counter()
    rep = Report()
    env, fp = _read_envelope(path, "result", rep)
    if env is None:
        return rep
    p = env["payload"]
    required = {"schema", "family", "family_hash", "unit_id", "n_lo", "n_hi", "login", "worker", "software", "base",
                "verdicts", "summary", "nonce"}
    if not required <= set(p):
        rep.fail(f"{path.name}: missing fields {sorted(required - set(p))}")
        return rep
    if p["schema"] != RESULT_SCHEMA or p["family"] != fam.id:
        rep.fail(f"{path.name}: schema/family mismatch")
    if p["family_hash"] != fam.hash:
        rep.fail(f"{path.name}: family_hash {p['family_hash']} != {fam.hash}")
    try:
        lo, hi = parse_unit_id(p["unit_id"], fam.bands)
        if (lo, hi) != (p["n_lo"], p["n_hi"]):
            rep.fail(f"{path.name}: n_lo/n_hi inconsistent with unit id")
        if Path(path).parent.name != p["unit_id"]:
            rep.fail(f"{path.name}: file must live in results/lehmer-q2/{p['unit_id']}/")
    except ValueError as exc:
        rep.fail(f"{path.name}: {exc}")
        return rep
    c = contributors.get(p["login"])
    if Path(path).stem != p["login"]:
        rep.fail(f"{path.name}: file name must be <login>.json")
    if c is None:
        rep.fail(f"{path.name}: login {p['login']!r} is not registered")
    elif c["fingerprint"] != fp or p["worker"] != fp:
        rep.fail(f"{path.name}: signing key is not the registered key of {p['login']}")
    sw = p["software"]
    accepted = {r["worker_sha256"] for r in releases.get("accepted", [])}
    withdrawn = {r["worker_sha256"] for r in releases.get("withdrawn", [])}
    if not isinstance(sw, dict) or sw.get("worker_sha256") not in accepted or sw.get("worker_sha256") in withdrawn:
        rep.fail(f"{path.name}: worker version {sw.get('worker_sha256', '?')[:12]} is not an accepted release")
    if not (isinstance(p["nonce"], str) and HEX64_RE.match(p["nonce"])):
        rep.fail(f"{path.name}: nonce must be 64 hex characters")
    if p["base"] != worker_base(fp, p["unit_id"]):
        rep.fail(f"{path.name}: base {p['base']} is not the worker base for this key and unit")
    if not rep.ok:
        return rep
    cands = candidates(fam, p["unit_id"])
    verdicts = p["verdicts"]
    if not isinstance(verdicts, list) or len(verdicts) != len(cands):
        rep.fail(f"{path.name}: {len(verdicts) if isinstance(verdicts, list) else '?'} verdicts, expected {len(cands)}")
        return rep
    errors: list[str] = []
    for rec, (n, v) in zip(verdicts, cands, strict=True):
        _check_verdict_shape(rec, n, v, fam, errors)
    if errors:
        for e in errors[:20]:
            rep.fail(f"{path.name}: {e}")
        return rep
    if summarize(verdicts) != p["summary"]:
        rep.fail(f"{path.name}: summary does not match the verdicts")
    for rec in verdicts:
        rep.lines_checked += 1
        if time_budget_s is not None and time.perf_counter() - t0 > time_budget_s:
            rep.fail(f"{path.name}: time budget exhausted after {rep.recomputed} recomputed lines")
            break
        if not full and rec["method"] in ("fermat", "bpsw") and rec["v"] != "prp":
            continue
        mine = recompute_line(fam, rec, p["base"])
        rep.recomputed += 1
        if not _same_verdict(mine, rec):
            rep.fail(f"{path.name}: n={rec['n']} {rec['variant']}: recomputed {mine['v']}/{mine['method']} != claimed {rec['v']}/{rec['method']}")
            continue
        if rec["v"] == "prp":
            N = abs_value(rec["variant"], rec["n"])
            if reference_check:
                try:
                    from .families import reference_value  # noqa: PLC0415

                    if abs(reference_value(rec["variant"], rec["n"])) != N:
                        rep.fail(f"{path.name}: n={rec['n']}: value cross-check against core_math failed")
                        continue
                except ImportError:
                    pass
                if rec["digits"] <= 5000 and pow(3, int(N) - 1, int(N)) != 1:
                    rep.fail(f"{path.name}: n={rec['n']}: pure-Python Fermat check failed")
                    continue
            rep.prp_confirmed.append(rec["n"])
    rep.payload = p
    rep.wall_ms = int((time.perf_counter() - t0) * 1000)
    return rep


def filtered_check(fam: Family, uid: str) -> dict:
    """CI's own witness check for every non-candidate ``(n, variant)`` of a unit."""
    lo, hi = parse_unit_id(uid, fam.bands)
    count, bad = 0, []
    for n in range(lo, hi):
        for v in variants_for(n):
            if is_candidate(fam, v, n):
                continue
            count += 1
            d = filter_witness(fam, v, n)
            if d is None or not check_filter_witness(v, n, d):
                bad.append([n, v])
    return {"count": count, "ok": not bad, "bad": bad[:20]}


# --------------------------------------------------------------------------- pull requests
def verify_pr(repo: Path, changed: list[tuple[str, str]], pr_author_id: int | None, fam: Family, releases: dict,
              maintainer: bool = False, full: bool = True, time_budget_s: float | None = None) -> Report:
    """Path policy plus every file check; ``changed`` is ``[(status, path)]`` relative to the repo root."""
    rep = Report()
    existing = load_contributors(repo)
    contributors = dict(existing)
    contributor_paths, claim_paths, result_paths = [], [], []
    for status, rel in changed:
        if not rel.startswith(ALLOWED_DIRS):
            rep.fail(f"{rel}: outside the volunteer-writable directories")
            continue
        if status == "D" or status == "R":
            rep.fail(f"{rel}: deleting or renaming files is not allowed")
            continue
        if rel.startswith("distributed/contributors/"):
            if status == "M" and Path(rel).stem not in existing:
                rep.fail(f"{rel}: modification of an unregistered contributor file")
            contributor_paths.append(rel)
        elif rel.startswith("distributed/claims/"):
            if status != "A":
                rep.fail(f"{rel}: claims are add-only")
            claim_paths.append(rel)
        else:
            if status != "A":
                rep.fail(f"{rel}: results are add-only (rerun the unit instead of editing)")
            result_paths.append(rel)
    for rel in contributor_paths:
        r = verify_contributor_file(Path(repo) / rel, pr_author_id, existing, maintainer=maintainer)
        rep.errors += r.errors
        rep.ok &= r.ok
        if r.ok and r.payload:
            contributors[r.payload["login"]] = r.payload
    for rel in claim_paths:
        r = verify_claim_file(Path(repo) / rel, fam, contributors)
        rep.errors += r.errors
        rep.ok &= r.ok
    for rel in result_paths:
        r = verify_result_file(Path(repo) / rel, fam, contributors, releases, full=full, time_budget_s=time_budget_s)
        rep.errors += r.errors
        rep.ok &= r.ok
        rep.lines_checked += r.lines_checked
        rep.recomputed += r.recomputed
        rep.prp_confirmed += r.prp_confirmed
        if r.ok and r.payload and pr_author_id is not None:
            c = contributors.get(r.payload["login"], {})
            if not r.payload["login"].startswith("ext-") and c.get("github_id") != pr_author_id and not maintainer:
                rep.fail(f"{rel}: PR author is not the registered owner of {r.payload['login']}")
    return rep
