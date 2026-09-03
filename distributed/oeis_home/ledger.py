"""Unit states, credits and the ledger built from ``verified/`` records."""
from __future__ import annotations

import json
from pathlib import Path

from .families import Family
from .units import all_units

STATES = ("open", "claimed", "pending", "verified", "double_checked", "disputed", "invalid")


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
    ids = {r.get("github_id") for r in valid if r.get("github_id", 0) != 0} | {r["login"] for r in valid if r.get("role") == "verifier"}
    return "double_checked" if len(ids) >= 2 else "verified"


def _load_verified(repo: Path) -> dict[str, dict]:
    out = {}
    for path in sorted((repo / "distributed" / "verified" / "lehmer-q2").glob("*.json")):
        if path.name.endswith(".pari.json"):
            continue
        env = json.loads(path.read_text(encoding="utf-8"))
        payload = env.get("payload", env)
        out[payload["unit_id"]] = payload
    return out


def _load_pari_notes(repo: Path) -> dict[tuple[str, int, str], str]:
    out = {}
    for path in sorted((repo / "distributed" / "verified" / "lehmer-q2").glob("*.pari.json")):
        for note in json.loads(path.read_text(encoding="utf-8")):
            out[(note["unit_id"], note["n"], note["variant"])] = note["result"]
    return out


def build(repo: Path, fam: Family, contributors: dict[str, dict], claims: dict[str, list[str]] | None = None) -> dict:
    """Assemble ``ledger/lehmer-q2.json`` from the verified records and contributors."""
    repo = Path(repo)
    verified = _load_verified(repo)
    pari = _load_pari_notes(repo)
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
        for pc in rec.get("positive_claims", []):
            pc = dict(pc)
            pc["maintainer_pari"] = pari.get((uid, pc["n"], pc["variant"]), pc.get("maintainer_pari", "none"))
            pc["unit_id"] = uid
            positive.append(pc)
        units[uid] = rec
    verified_through = 0
    for uid in all_units(fam.n_max_open, fam.bands):
        u = units[uid]
        ok = u["state"] in ("verified", "double_checked") and u.get("filtered_checked", {}).get("ok")
        ok = ok and all(pc.get("verifier_login") and pc.get("ci_confirmed") and pc.get("maintainer_pari", "none") != "none"
                        for pc in positive if pc["unit_id"] == uid)
        if not ok:
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
        "contributors": {login: {"display_name": c.get("display_name", login), "role": c.get("role", "worker"),
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
