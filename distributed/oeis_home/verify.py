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
    prp_confirmed: list[str] = field(default_factory=list)
    wall_ms: int = 0
    payload: dict | None = None
    reference_checked: int = 0
    notes: list[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)


def _read_envelope(path: Path, kind: str, rep: Report) -> tuple[dict | None, str]:
    try:
        if Path(path).name.startswith("."):
            raise CanonError("checkpoint or hidden file committed; delete it (results/**/.*.partial.json)")
        env = check_file_bytes(Path(path).read_bytes())
        fp = verify_envelope(env, kind)
        return env, fp
    except (CanonError, SignatureError, OSError) as exc:
        rep.fail(f"{path.name}: {exc}")
        return None, ""
    except Exception as exc:  # noqa: BLE001 - a crafted file must never crash the verifier
        rep.fail(f"{path.name}: malformed ({type(exc).__name__})")
        return None, ""


def _is_str(x) -> bool:
    return isinstance(x, str)


def _is_int(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


# --------------------------------------------------------------------------- contributors
def verify_contributor_file(path: Path, pr_author_id: int | None, existing: dict[str, dict], maintainer: bool = False,
                            pr_author_login: str | None = None, pending: dict[str, dict] | None = None) -> Report:
    """``existing`` must be the registry of the BASE commit (never the overlaid working tree)."""
    rep = Report()
    env, fp = _read_envelope(path, "contributor", rep)
    if env is None:
        return rep
    p = env["payload"]
    required = {"login", "github_id", "fingerprint", "pubkey", "display_name", "oeis_credit_name", "role"}
    if not isinstance(p, dict) or not required <= set(p):
        rep.fail(f"{path.name}: missing fields")
        return rep
    login = p["login"]
    if not _is_str(login) or not LOGIN_RE.match(login) or Path(path).stem != login:
        rep.fail(f"{path.name}: login must match the file name and ^[a-z0-9-]+$ / ext-")
        return rep
    if not _is_int(p["github_id"]) or p["github_id"] < 0 or (login.startswith("ext-") != (p["github_id"] == 0)):
        rep.fail(f"{path.name}: github_id must be the numeric id (0 only for ext- logins)")
    if not all(_is_str(p[k]) for k in ("fingerprint", "pubkey", "display_name", "oeis_credit_name", "role")):
        rep.fail(f"{path.name}: string fields have the wrong type")
        return rep
    if p["fingerprint"] != fp or p["fingerprint"] != env["signature"]["key"] or p["pubkey"] != env["signature"]["pubkey"]:
        rep.fail(f"{path.name}: fingerprint/pubkey do not match the signing key")
    if not 1 <= len(p["display_name"]) <= 64 or len(p["oeis_credit_name"]) > 64:
        rep.fail(f"{path.name}: display_name must be 1–64 and oeis_credit_name ≤ 64 characters")
    if p["role"] not in ("worker", "verifier", "bot") or (p["role"] != "worker" and not maintainer):
        rep.fail(f"{path.name}: role {p['role']!r} not allowed here")
    prev = p.get("previous_fingerprints", [])
    if not isinstance(prev, list) or not all(_is_str(x) and FP_RE.match(x) for x in prev):
        rep.fail(f"{path.name}: previous_fingerprints must be a list of fingerprints")
    is_ext = login.startswith("ext-")
    if pr_author_id is not None and not is_ext and pr_author_id != p["github_id"]:
        rep.fail(f"{path.name}: PR author id {pr_author_id} does not match github_id {p['github_id']}")
    if pr_author_login is not None and not is_ext and not maintainer and login != pr_author_login.lower():
        rep.fail(f"{path.name}: login must be your own GitHub login ({pr_author_login.lower()})")
    if is_ext and pr_author_id is not None and not maintainer:
        rep.fail(f"{path.name}: ext- registrations must come from a maintainer")
    # one key, one login (base registry and the other files of the same PR)
    for other_login, other in list(existing.items()) + list((pending or {}).items()):
        if other_login != login and (other.get("fingerprint") == p["fingerprint"] or other.get("pubkey") == p["pubkey"]
                                     or p["fingerprint"] in other.get("previous_fingerprints", [])):
            rep.fail(f"{path.name}: this key is already registered under {other_login!r}")
    old = existing.get(login)
    if old is not None:
        if old["github_id"] != p["github_id"] and not maintainer:
            rep.fail(f"{path.name}: github_id may not change on an existing login")
        if old["fingerprint"] != p["fingerprint"]:
            if p.get("supersedes") != old["fingerprint"] or not _is_str(p.get("rotation_sig")):
                rep.fail(f"{path.name}: replacing a registered key needs supersedes + rotation_sig")
            elif not verify_rotation(bytes.fromhex(old["pubkey"]), bytes.fromhex(p["pubkey"]), p["rotation_sig"]):
                rep.fail(f"{path.name}: rotation_sig does not verify under the old key")
            elif old["fingerprint"] not in prev or not set(old.get("previous_fingerprints", [])) <= set(prev):
                rep.fail(f"{path.name}: previous_fingerprints must keep the whole key history")
    rep.payload = p
    return rep


def accepted_fingerprints(contributor: dict) -> set[str]:
    """The current key plus every superseded key of a login (old results stay valid after rotation)."""
    return {contributor["fingerprint"], *contributor.get("previous_fingerprints", [])}


def load_contributors(repo: Path) -> dict[str, dict]:
    """All registered contributors on this checkout (verified envelopes only; bad files are skipped)."""
    out: dict[str, dict] = {}
    cdir = Path(repo) / "distributed" / "contributors"
    for path in sorted(cdir.glob("*.json")) if cdir.exists() else []:
        try:
            rep = verify_contributor_file(path, None, {}, maintainer=True)
        except Exception:  # noqa: BLE001
            continue
        if rep.ok and rep.payload:
            out[rep.payload["login"]] = rep.payload
    return out


def load_contributors_at(repo: Path, ref: str) -> dict[str, dict]:
    """The registry as committed at git ``ref`` (what CI must trust, not the overlaid working tree)."""
    import subprocess  # noqa: PLC0415
    import tempfile  # noqa: PLC0415

    names = subprocess.run(["git", "-C", str(repo), "ls-tree", "--name-only", ref, "distributed/contributors/"],
                           capture_output=True, text=True, check=False).stdout.split()
    out: dict[str, dict] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for rel in names:
            if not rel.endswith(".json"):
                continue
            blob = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{rel}"], capture_output=True, check=False).stdout
            path = Path(tmp) / Path(rel).name
            path.write_bytes(blob)
            try:
                rep = verify_contributor_file(path, None, {}, maintainer=True)
            except Exception:  # noqa: BLE001
                continue
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
    if rec["v"] not in ("prime", "prp", "composite", "unit") or rec["method"] not in ("small", "factor", "fermat", "bpsw", "mr13", "cert"):
        errors.append(f"n={n} {v}: bad v/method {rec['v']}/{rec['method']}")
    if rec["method"] == "factor":
        if rec["v"] != "composite" or not isinstance(rec.get("factor"), str) or not rec["factor"].isdigit():
            errors.append(f"n={n} {v}: factor verdict malformed")
    if rec["method"] in ("fermat", "bpsw", "mr13") and not (isinstance(rec.get("res64"), str) and HEX16_RE.match(rec["res64"])):
        errors.append(f"n={n} {v}: res64 missing or malformed")
    if rec["v"] == "prp" and (rec["method"] not in ("bpsw", "mr13") or not isinstance(rec.get("sprp"), list)):
        errors.append(f"n={n} {v}: prp must carry method bpsw and sprp bases")
    if rec["v"] == "prime" and rec["method"] == "cert" and not isinstance(rec.get("cert"), dict):
        errors.append(f"n={n} {v}: cert verdict without certificate")


def recompute_line(fam: Family, rec: dict, base: int) -> dict:
    return verdict(fam, rec["variant"], rec["n"], base)


def _same_verdict(mine: dict, theirs: dict) -> bool:
    same_method = mine["method"] == theirs["method"] or {mine["method"], theirs["method"]} == {"bpsw", "mr13"}
    if mine["v"] != theirs["v"] or not same_method or mine["digits"] != theirs["digits"]:
        return False
    for k in ("factor", "res64", "sprp"):
        if mine.get(k) != theirs.get(k):
            return False
    return True


def result_stem_ok(stem: str, login: str) -> bool:
    """``<login>.json`` or ``<login>-<k>.json`` with ``k ≥ 2`` (logins may themselves contain digits and dashes)."""
    return stem == login or re.fullmatch(re.escape(login) + r"-(?:[2-9]|[1-9][0-9]+)", stem) is not None


def verify_result_file(path: Path, fam: Family, contributors: dict[str, dict], releases: dict, full: bool = True,
                       time_budget_s: float | None = None, reference_check: str = "optional") -> Report:
    """``reference_check``: ``"require"`` (CI: the independent core_math evaluator must be present),
    ``"optional"`` (skip with a note when absent) or ``"off"``."""
    t0 = time.perf_counter()
    rep = Report()
    env, fp = _read_envelope(path, "result", rep)
    if env is None:
        return rep
    p = env["payload"]
    required = {"schema", "family", "family_hash", "unit_id", "n_lo", "n_hi", "login", "worker", "software", "base",
                "verdicts", "summary", "nonce"}
    if not isinstance(p, dict) or not required <= set(p):
        rep.fail(f"{path.name}: missing fields")
        return rep
    if not (all(_is_str(p[k]) for k in ("schema", "family", "family_hash", "unit_id", "login", "worker", "nonce"))
            and all(_is_int(p[k]) for k in ("n_lo", "n_hi", "base")) and isinstance(p["software"], dict)
            and isinstance(p["verdicts"], list) and isinstance(p["summary"], dict)):
        rep.fail(f"{path.name}: payload fields have the wrong types")
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
    if not result_stem_ok(Path(path).stem, p["login"]):
        rep.fail(f"{path.name}: file name must be <login>.json or <login>-<k>.json")
    if c is None:
        rep.fail(f"{path.name}: login {p['login']!r} is not registered")
    elif fp not in accepted_fingerprints(c) or p["worker"] != fp:
        rep.fail(f"{path.name}: signing key is not a registered key of {p['login']}")
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
        if not isinstance(rec, dict):
            errors.append(f"n={n} {v}: verdict is not an object")
            continue
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
            if reference_check != "off":
                try:
                    from .families import reference_value  # noqa: PLC0415

                    if abs(reference_value(rec["variant"], rec["n"])) != N:
                        rep.fail(f"{path.name}: n={rec['n']}: value cross-check against core_math failed")
                        continue
                    rep.reference_checked += 1
                except ImportError:
                    if reference_check == "require":
                        rep.fail(f"{path.name}: n={rec['n']}: independent core_math evaluator unavailable (set PYTHONPATH to the repository root)")
                        continue
                    rep.notes.append(f"n={rec['n']} {rec['variant']}: core_math cross-check skipped (not importable here)")
                if rec["digits"] <= 5000 and pow(3, int(N) - 1, int(N)) != 1:
                    rep.fail(f"{path.name}: n={rec['n']}: pure-Python Fermat check failed")
                    continue
            rep.prp_confirmed.append(f"{rec['n']}/{rec['variant']}")
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
              maintainer: bool = False, full: bool = True, time_budget_s: float | None = None,
              base_contributors: dict[str, dict] | None = None, pr_author_login: str | None = None,
              reference_check: str = "require") -> Report:
    """Path policy plus every file check.

    ``changed`` is ``[(status, path)]`` relative to the repo root (merge-base diff).  ``base_contributors``
    is the registry of the base commit; when ``None`` it is read from the working tree, which is only
    safe outside CI (the workflow overlays the PR's data directories before running this).
    """
    rep = Report()
    existing = base_contributors if base_contributors is not None else load_contributors(repo)
    contributors = dict(existing)
    pending: dict[str, dict] = {}
    contributor_paths, claim_paths, result_paths = [], [], []
    for status, rel in changed:
        if not rel.startswith(ALLOWED_DIRS):
            rep.fail(f"{rel}: outside the volunteer-writable directories")
            continue
        if status in ("D", "R", "C", "T"):
            rep.fail(f"{rel}: deleting, renaming or retyping files is not allowed")
            continue
        if Path(rel).name.startswith("."):
            rep.fail(f"{rel}: hidden/checkpoint files must not be committed (delete results/**/.*.partial.json)")
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
                rep.fail(f"{rel}: results are add-only; a wrong merged file is withdrawn by a maintainer (open an issue), "
                         "and a fresh run goes to <login>-2.json")
            result_paths.append(rel)
    for rel in contributor_paths:
        try:
            r = verify_contributor_file(Path(repo) / rel, pr_author_id, existing, maintainer=maintainer,
                                        pr_author_login=pr_author_login, pending=pending)
        except Exception as exc:  # noqa: BLE001
            r = Report(ok=False, errors=[f"{rel}: malformed ({type(exc).__name__})"])
        rep.errors += r.errors
        rep.ok &= r.ok
        if r.ok and r.payload:
            pending[r.payload["login"]] = r.payload
            contributors[r.payload["login"]] = r.payload
    for rel in claim_paths:
        try:
            r = verify_claim_file(Path(repo) / rel, fam, contributors)
        except Exception as exc:  # noqa: BLE001
            r = Report(ok=False, errors=[f"{rel}: malformed ({type(exc).__name__})"])
        rep.errors += r.errors
        rep.ok &= r.ok
    for rel in result_paths:
        try:
            r = verify_result_file(Path(repo) / rel, fam, contributors, releases, full=full, time_budget_s=time_budget_s,
                                   reference_check=reference_check)
        except Exception as exc:  # noqa: BLE001
            r = Report(ok=False, errors=[f"{rel}: malformed ({type(exc).__name__})"])
        rep.errors += r.errors
        rep.notes += r.notes
        rep.ok &= r.ok
        rep.lines_checked += r.lines_checked
        rep.recomputed += r.recomputed
        rep.reference_checked += r.reference_checked
        rep.prp_confirmed += r.prp_confirmed
        if r.ok and r.payload and pr_author_id is not None:
            c = contributors.get(r.payload["login"], {})
            if not r.payload["login"].startswith("ext-") and c.get("github_id") != pr_author_id and not maintainer:
                rep.fail(f"{rel}: PR author is not the registered owner of {r.payload['login']}")
    return rep
