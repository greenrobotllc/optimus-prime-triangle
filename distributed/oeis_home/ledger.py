"""Unit states, credits and the ledger built from ``verified/`` records."""
from __future__ import annotations

from pathlib import Path

from .families import Family
from .units import all_units

STATES = ("open", "claimed", "pending", "verified", "double_checked", "disputed", "invalid")


def identity(result: dict) -> str:
    """One identity per GitHub account, whatever the role; keys without an account (ext-, verifier
    keys registered by the maintainer with github_id 0) are identified by their login."""
    gid = result.get("github_id", 0)
    return f"gh:{gid}" if gid else f"login:{result['login']}"


def unit_state(unit_rec: dict) -> str:
    results = unit_rec.get("results", [])
    valid = [r for r in results if r.get("status") == "valid"]
    if unit_rec.get("disputed"):
        return "disputed"
    if results and not valid:
        return "invalid" if any(r.get("status") in ("invalid", "withdrawn") for r in results) else "pending"
    if not results:
        return "claimed" if unit_rec.get("claims") else "open"
    if not unit_rec.get("filtered_checked", {}).get("ok"):
        return "pending"
    ids = {identity(r) for r in valid}
    return "double_checked" if len(valid) >= 2 and len(ids) >= 2 else "verified"


def trusted_signers(contributors: dict[str, dict], roles: tuple[str, ...]) -> set[str]:
    return {c["fingerprint"] for c in contributors.values() if c.get("role") in roles}


def load_verified(repo: Path, contributors: dict[str, dict], allow_unsigned: bool = False) -> dict[str, dict]:
    """Verified records signed by a registered ``bot`` key.  Unsigned records are accepted only when
    ``allow_unsigned`` (local runs) and are marked ``unsigned``; anything else is ignored."""
    from .canon import CanonError, check_file_bytes  # noqa: PLC0415
    from .keys import SignatureError, verify_envelope  # noqa: PLC0415

    bots = trusted_signers(contributors, ("bot",))
    out = {}
    vdir = repo / "distributed" / "verified" / "lehmer-q2"
    for path in sorted(vdir.glob("*.json")) if vdir.exists() else []:
        if path.name.endswith(".pari.json"):
            continue
        try:
            data = path.read_bytes()
            env = check_file_bytes(data)
            if env.get("signature") is None:
                if not allow_unsigned:
                    continue
                payload = dict(env["payload"])
                payload["unsigned"] = True
            else:
                fp = verify_envelope(env, "verified")
                if fp not in bots:
                    continue
                payload = dict(env["payload"])
                payload["unsigned"] = False
        except (CanonError, SignatureError, OSError, KeyError, TypeError, ValueError):
            continue
        out[payload["unit_id"]] = payload
    return out


def load_pari_notes(repo: Path, contributors: dict[str, dict]) -> dict[tuple[str, int, str], str]:
    """Maintainer ``gp`` checks: envelopes of kind ``note`` signed by a registered verifier/bot key."""
    from .canon import CanonError, check_file_bytes  # noqa: PLC0415
    from .keys import SignatureError, verify_envelope  # noqa: PLC0415

    signers = trusted_signers(contributors, ("verifier", "bot"))
    out = {}
    vdir = repo / "distributed" / "verified" / "lehmer-q2"
    for path in sorted(vdir.glob("*.pari.json")) if vdir.exists() else []:
        try:
            env = check_file_bytes(path.read_bytes())
            if verify_envelope(env, "note") not in signers:
                continue
            for note in env["payload"]["notes"]:
                if note.get("result") in ("isprime", "ispseudoprime", "composite"):
                    out[(note["unit_id"], int(note["n"]), note["variant"])] = note["result"]
        except (CanonError, SignatureError, OSError, KeyError, TypeError, ValueError):
            continue
    return out


def build(repo: Path, fam: Family, contributors: dict[str, dict], claims: dict[str, list[str]] | None = None,
          allow_unsigned: bool = False) -> dict:
    """Assemble ``ledger/lehmer-q2.json`` from the verified records and contributors."""
    repo = Path(repo)
    verified = load_verified(repo, contributors, allow_unsigned=allow_unsigned)
    pari = load_pari_notes(repo, contributors)
    claims = claims or {}
    units: dict[str, dict] = {}
    positive: list[dict] = []
    for uid in all_units(fam.n_max_open, fam.bands):
        rec = verified.get(uid, {"unit_id": uid, "results": [], "verdicts": [], "positive_claims": [], "filtered_checked": {"ok": False, "count": 0}})
        rec = dict(rec)
        rec["claims"] = claims.get(uid, [])
        for r in rec["results"]:
            c = contributors.get(r["login"], {})
            r.setdefault("github_id", c.get("github_id", 0))
            r.setdefault("role", c.get("role", "worker"))
        rec["state"] = unit_state(rec)
        enriched = []
        for pc in rec.get("positive_claims", []):
            pc = dict(pc)
            pc["maintainer_pari"] = pari.get((uid, pc["n"], pc["variant"]), "none")
            pc["unit_id"] = uid
            enriched.append(pc)
        rec["positive_claims"] = enriched
        positive.extend(enriched)
        units[uid] = rec
    # verified_through by index: every verdict below it is final (composite / unit / deterministic prime,
    # or a prp that has a second identity and a maintainer gp check) inside a verified unit
    verified_through = 0
    for uid in all_units(fam.n_max_open, fam.bands):
        u = units[uid]
        if u["state"] not in ("verified", "double_checked") or not u.get("filtered_checked", {}).get("ok") or u.get("unsigned"):
            break
        claims_by_key = {(pc["n"], pc["variant"]): pc for pc in u["positive_claims"]}
        stop = None
        for rec in sorted(u.get("verdicts", []), key=lambda r: (r["n"], r["variant"])):
            if rec["v"] != "prp":
                continue
            pc = claims_by_key.get((rec["n"], rec["variant"]), {})
            if not (pc.get("verifier_login") and pc.get("ci_confirmed") and pc.get("maintainer_pari", "none") in ("isprime", "ispseudoprime")):
                stop = rec["n"]
                break
        if stop is not None:
            verified_through = max(verified_through, stop)
            break
        verified_through = u.get("n_hi", verified_through)
    stats: dict[str, dict] = {}
    for u in units.values():
        for r in u["results"]:
            s = stats.setdefault(r["login"], {"units_verified": 0, "first_finds": 0, "double_checks": 0, "invalid": 0})
            if r.get("status") == "valid":
                s["units_verified"] += 1
            elif r.get("status") == "invalid":
                s["invalid"] += 1
        for cr in u.get("credits", []):
            s = stats.setdefault(cr["login"], {"units_verified": 0, "first_finds": 0, "double_checks": 0, "invalid": 0})
            if cr["role"] == "first":
                s["first_finds"] += 1
            elif cr["role"] == "double":
                s["double_checks"] += 1
    return {
        "family": fam.id, "family_hash": fam.hash, "n_max_open": fam.n_max_open,
        "units": units, "positive_claims": sorted(positive, key=lambda p: (p["n"], p["variant"])),
        "verified_through": verified_through,
        "contributors": {login: {"display_name": c.get("display_name", login), "role": c.get("role", "worker"), "github_id": c.get("github_id", 0),
                                 **stats.get(login, {"units_verified": 0, "first_finds": 0, "double_checks": 0, "invalid": 0})}
                         for login, c in contributors.items()},
        "counts": {s: sum(1 for u in units.values() if u["state"] == s) for s in STATES},
    }


def next_units(ledger: dict, login: str, need: str = "any", count: int = 1) -> list[str]:
    """Units to work on: fresh ones first, then double-checks by a different account, then tie-breaks."""
    units = ledger["units"]
    me = ledger.get("contributors", {}).get(login, {})
    my_id = me.get("github_id")

    def eligible(u: dict, want: str) -> bool:
        st = u["state"]
        logins = {r["login"] for r in u["results"]}
        if login in logins or (my_id and any(r.get("github_id") == my_id for r in u["results"])):
            return False
        if want == "first":
            return st in ("open", "claimed")
        if want == "double":
            return st == "verified"
        if want == "tiebreak":
            return st == "disputed"
        return st in ("open", "claimed", "verified", "disputed")

    order = ["first", "double", "tiebreak"] if need == "any" else [need]
    picked: list[str] = []
    for want in order:
        for uid, u in units.items():
            if len(picked) >= count:
                break
            if eligible(u, want):
                picked.append(uid)
    return picked
