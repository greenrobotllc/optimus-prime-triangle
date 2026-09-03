"""``oeis-home`` command line: keygen · register · claim · unit · run · check · status · verify-pr · rebuild."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__, canon, families, keys, units
from .compute import run_unit
from .ledger import build as build_ledger, next_units
from .verify import filtered_check, load_contributors, verify_claim_file, verify_pr, verify_result_file

REPO_ENV = "OEIS_HOME_REPO"
RAW_LEDGER = "https://raw.githubusercontent.com/greenrobotllc/optimus-prime-triangle/main/distributed/ledger/lehmer-q2.json"


def repo_root(args) -> Path:
    if getattr(args, "repo", None):
        return Path(args.repo).resolve()
    if os.environ.get(REPO_ENV):
        return Path(os.environ[REPO_ENV]).resolve()
    here = Path.cwd().resolve()
    for p in (here, *here.parents):
        if (p / "distributed" / "families" / "lehmer-q2.json").exists():
            return p
    raise SystemExit("run inside the repository checkout or set OEIS_HOME_REPO")


def load_family(root: Path):
    return families.load(root / "distributed" / "families" / "lehmer-q2.json")


def load_releases(root: Path) -> dict:
    return json.loads((root / "distributed" / "RELEASES.json").read_text(encoding="utf-8"))


def write_signed(path: Path, env: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canon.file_bytes(env))


def my_login(root: Path, sk, override: str | None) -> str:
    fp = keys.fingerprint(keys.public_raw(sk))
    if override:
        return override
    for login, c in load_contributors(root).items():
        if c["fingerprint"] == fp:
            return login
    raise SystemExit("this key is not registered yet; run `oeis-home register` (or pass --login)")


# --------------------------------------------------------------------------- commands
def cmd_keygen(args) -> int:
    sk = keys.generate(Path(args.path))
    print(f"wrote {args.path}\nfingerprint {keys.fingerprint(keys.public_raw(sk))}")
    return 0


def cmd_register(args) -> int:
    root = repo_root(args)
    sk = keys.load(Path(args.key))
    login = args.login.lower()
    gid = args.github_id
    if gid is None:
        if login.startswith("ext-"):
            gid = 0
        else:
            from .github import user_id  # noqa: PLC0415

            gid = user_id(login)
    pub = keys.public_raw(sk)
    payload = {"login": login, "github_id": gid, "fingerprint": keys.fingerprint(pub), "pubkey": pub.hex(),
               "display_name": args.display_name, "oeis_credit_name": args.oeis_credit_name or "", "role": args.role}
    path = root / "distributed" / "contributors" / f"{login}.json"
    existing = load_contributors(root).get(login)
    if existing and existing["fingerprint"] != payload["fingerprint"]:
        if not args.old_key:
            raise SystemExit(f"{login} is registered with another key; pass --old-key to rotate")
        old = keys.load(Path(args.old_key))
        payload["supersedes"] = existing["fingerprint"]
        payload["rotation_sig"] = keys.rotation_signature(old, pub)
    write_signed(path, keys.sign_envelope("contributor", payload, sk))
    print(f"wrote {path.relative_to(root)} (github_id {gid})")
    return 0


def cmd_unit(args) -> int:
    fam = load_family(repo_root(args))
    cands = units.candidates(fam, args.unit_id)
    lo, hi = units.parse_unit_id(args.unit_id, fam.bands)
    print(json.dumps({"unit_id": args.unit_id, "family": fam.id, "family_hash": fam.hash, "n_lo": lo, "n_hi": hi,
                      "candidates": cands[:8] + (["…"] if len(cands) > 8 else []), "n_candidates": len(cands)}, indent=1))
    return 0


def cmd_claim(args) -> int:
    root = repo_root(args)
    fam = load_family(root)
    sk = keys.load(Path(args.key))
    login = my_login(root, sk, args.login)
    try:
        from .github import fetch_ledger  # noqa: PLC0415

        ledger = fetch_ledger(args.ledger_url)
    except Exception:  # noqa: BLE001 - offline: fall back to the local ledger
        path = root / "distributed" / "ledger" / "lehmer-q2.json"
        ledger = json.loads(path.read_text()) if path.exists() else build_ledger(root, fam, load_contributors(root))
    picked = next_units(ledger, login, args.need, args.count)
    fp = keys.fingerprint(keys.public_raw(sk))
    for uid in picked:
        payload = {"unit_id": uid, "login": login, "worker": fp, "family_hash": fam.hash, "nonce": os.urandom(32).hex()}
        write_signed(root / "distributed" / "claims" / "lehmer-q2" / f"{uid}--{login}.json", keys.sign_envelope("claim", payload, sk))
        print(uid)
    if not picked:
        print("no unit available for you right now")
    return 0


def cmd_run(args) -> int:
    root = repo_root(args)
    fam = load_family(root)
    sk = keys.load(Path(args.key))
    login = my_login(root, sk, args.login)
    fp = keys.fingerprint(keys.public_raw(sk))
    out = root / "distributed" / "results" / "lehmer-q2" / args.unit_id / f"{login}.json"
    if out.exists() and not args.force:
        raise SystemExit(f"{out} exists; results are add-only (use --force to recompute locally)")
    partial = root / "distributed" / "results" / "lehmer-q2" / args.unit_id / f".{login}.partial.json"
    payload = run_unit(fam, args.unit_id, fp, login, progress=(None if args.quiet else print), partial_path=partial)
    write_signed(out, keys.sign_envelope("result", payload, sk))
    s = payload["summary"]
    print(f"wrote {out.relative_to(root)}: {len(payload['verdicts'])} lines, {s['prp']} prp, {s['prime']} prime, {s['composite']} composite, "
          f"{payload['wall_ms'] / 1000:.0f} s")
    return 0


def cmd_check(args) -> int:
    root = repo_root(args)
    fam = load_family(root)
    contributors = load_contributors(root)
    releases = load_releases(root)
    rc = 0
    for f in args.files:
        path = Path(f)
        if "/results/" in str(path.resolve()):
            rep = verify_result_file(path, fam, contributors, releases, full=not args.quick)
        elif "/claims/" in str(path.resolve()):
            rep = verify_claim_file(path, fam, contributors)
        else:
            from .verify import verify_contributor_file  # noqa: PLC0415

            rep = verify_contributor_file(path, None, contributors, maintainer=True)
        print(f"{'OK  ' if rep.ok else 'FAIL'} {path}  lines={rep.lines_checked} recomputed={rep.recomputed} prp={rep.prp_confirmed}")
        for e in rep.errors:
            print("   ", e)
        rc |= 0 if rep.ok else 1
    return rc


def cmd_status(args) -> int:
    root = repo_root(args)
    fam = load_family(root)
    ledger = build_ledger(root, fam, load_contributors(root))
    print(json.dumps({"counts": ledger["counts"], "verified_through": ledger["verified_through"],
                      "positive_claims": [(p["n"], p["variant"], p.get("discoverer_login", "")) for p in ledger["positive_claims"]]}, indent=1))
    return 0


def cmd_verify_pr(args) -> int:
    root = repo_root(args)
    fam = load_family(root)
    from .github import changed_files  # noqa: PLC0415

    changed = changed_files(root, args.base, args.head)
    rep = verify_pr(root, changed, args.author_id, fam, load_releases(root), maintainer=args.maintainer, full=True, time_budget_s=args.time_budget)
    summary = {"ok": rep.ok, "files": len(changed), "lines_checked": rep.lines_checked, "recomputed": rep.recomputed,
               "prp_confirmed": rep.prp_confirmed, "errors": rep.errors}
    print(json.dumps(summary, indent=1))
    if args.summary_file:
        Path(args.summary_file).write_text(json.dumps(summary, indent=1))
    return 0 if rep.ok else 1


def cmd_rebuild(args) -> int:
    root = repo_root(args)
    fam = load_family(root)
    contributors = load_contributors(root)
    releases = load_releases(root)
    vdir = root / "distributed" / "verified" / "lehmer-q2"
    vdir.mkdir(parents=True, exist_ok=True)
    bot = keys.load(Path(args.bot_key)) if args.bot_key else None
    if args.set_pari:
        uid, n, variant, result = args.set_pari
        notes_path = vdir / f"{uid}.pari.json"
        notes = json.loads(notes_path.read_text()) if notes_path.exists() else []
        notes = [x for x in notes if not (x["n"] == int(n) and x["variant"] == variant)]
        notes.append({"unit_id": uid, "n": int(n), "variant": variant, "result": result, "recorded_at": datetime.now(timezone.utc).isoformat()})
        notes_path.write_text(json.dumps(notes, indent=1))
        print(f"recorded gp {result} for {uid} n={n} {variant}")
    withdrawn = {r["worker_sha256"] for r in releases.get("withdrawn", [])}
    from .github import file_first_merge  # noqa: PLC0415

    rdir = root / "distributed" / "results" / "lehmer-q2"
    for unit_dir in sorted(p for p in rdir.iterdir() if p.is_dir()) if rdir.exists() else []:
        uid = unit_dir.name
        vpath = vdir / f"{uid}.json"
        existing = json.loads(vpath.read_text()).get("payload") if vpath.exists() else None
        known = {r["path"]: r for r in (existing or {}).get("results", [])}
        result_files = sorted(p for p in unit_dir.glob("*.json") if not p.name.startswith("."))
        need = [p for p in result_files if str(p.relative_to(root)) not in known
                or known[str(p.relative_to(root))].get("worker_sha256") in withdrawn or args.full]
        if not need and existing:
            continue
        results = list((existing or {}).get("results", []))
        verdict_rows = list((existing or {}).get("verdicts", []))
        canonical = (existing or {}).get("canonical", "")
        for path in need:
            rel = str(path.relative_to(root))
            rep = verify_result_file(path, fam, contributors, releases, full=True)
            payload = rep.payload or {}
            sw = payload.get("software", {}).get("worker_sha256", "")
            status = "withdrawn" if sw in withdrawn else ("valid" if rep.ok else "invalid")
            merge = file_first_merge(root, rel)
            entry = {"path": rel, "login": payload.get("login", path.stem), "worker": payload.get("worker", ""), "worker_sha256": sw,
                     "status": status, "merge_sha": merge["sha"], "merged_at": merge["committed_at"], "pr_number": 0,
                     "pr_created_at": merge["committed_at"], "ci_run_id": os.environ.get("GITHUB_RUN_ID", "local"),
                     "lines_recomputed": rep.recomputed, "lines_total": rep.lines_checked, "errors": rep.errors[:5]}
            results = [r for r in results if r["path"] != rel] + [entry]
            if status == "valid" and not canonical:
                canonical = rel
                verdict_rows = [{k: v for k, v in rec.items() if k in ("n", "variant", "v", "method", "digits", "factor")} for rec in payload["verdicts"]]
            print(f"{uid} {rel}: {status} ({rep.recomputed} lines recomputed){'; ' + '; '.join(rep.errors[:2]) if rep.errors else ''}")
        valid = [r for r in results if r["status"] == "valid"]
        disputed = False
        if len(valid) >= 2:
            vecs = {}
            for r in valid:
                env = canon.check_file_bytes((root / r["path"]).read_bytes())
                vecs[r["path"]] = [(x["n"], x["variant"], x["v"]) for x in env["payload"]["verdicts"]]
            disputed = len({tuple(v) for v in vecs.values()}) > 1
        fchk = filtered_check(fam, uid)
        positive = []
        for rec in verdict_rows:
            if rec["v"] != "prp":
                continue
            holders = sorted((r for r in valid if _has_prp(root, r["path"], rec["n"], rec["variant"])), key=lambda r: r["pr_created_at"] or "9")
            first = holders[0] if holders else None
            second = next((r for r in holders[1:] if contributors.get(r["login"], {}).get("github_id") != contributors.get(first["login"], {}).get("github_id")
                           or contributors.get(r["login"], {}).get("role") == "verifier"), None) if first else None
            positive.append({"n": rec["n"], "variant": rec["variant"], "digits": rec["digits"],
                             "discoverer_login": first["login"] if first else "", "discovered_at": first["pr_created_at"] if first else "",
                             "verifier_login": second["login"] if second else "", "ci_confirmed": bool(first), "maintainer_pari": "none", "cert_sha256": ""})
        credits = []
        seen_ids = set()
        for r in sorted(valid, key=lambda r: r["pr_created_at"] or "9"):
            gid = contributors.get(r["login"], {}).get("github_id")
            credits.append({"login": r["login"], "display_name": contributors.get(r["login"], {}).get("display_name", r["login"]),
                            "role": "first" if not seen_ids else "double"})
            seen_ids.add(gid)
        lo, hi = units.parse_unit_id(uid, fam.bands)
        payload_v = {"unit_id": uid, "family_hash": fam.hash, "n_lo": lo, "n_hi": hi, "results": results, "canonical": canonical,
                     "filtered_checked": {"count": fchk["count"], "ok": fchk["ok"], "run_id": os.environ.get("GITHUB_RUN_ID", "local")},
                     "verdicts": verdict_rows, "positive_claims": positive, "credits": credits, "disputed": disputed,
                     "decided_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        if bot:
            write_signed(vpath, keys.sign_envelope("verified", payload_v, bot))
        else:
            vpath.write_bytes(canon.canon({"kind": "verified", "payload": payload_v, "signature": None}) + b"\n")
    ledger = build_ledger(root, fam, contributors, _claims(root))
    (root / "distributed" / "ledger").mkdir(exist_ok=True)
    (root / "distributed" / "ledger" / "lehmer-q2.json").write_text(json.dumps(ledger, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    from .export import write_exports  # noqa: PLC0415
    from .report import render_site  # noqa: PLC0415

    write_exports(ledger, fam, contributors, root / "distributed" / "exports" / "lehmer-q2")
    render_site(ledger, contributors, fam, root / "distributed" / "docs", built_from=os.environ.get("GITHUB_SHA", "")[:12])
    print(json.dumps({"counts": ledger["counts"], "verified_through": ledger["verified_through"], "positive": len(ledger["positive_claims"])}))
    return 0


def _has_prp(root: Path, rel: str, n: int, variant: str) -> bool:
    env = canon.check_file_bytes((root / rel).read_bytes())
    return any(x["n"] == n and x["variant"] == variant and x["v"] == "prp" for x in env["payload"]["verdicts"])


def _claims(root: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    cdir = root / "distributed" / "claims" / "lehmer-q2"
    for path in sorted(cdir.glob("*.json")) if cdir.exists() else []:
        try:
            env = canon.check_file_bytes(path.read_bytes())
            out.setdefault(env["payload"]["unit_id"], []).append(env["payload"]["login"])
        except Exception:  # noqa: BLE001
            continue
    return out


# --------------------------------------------------------------------------- parser
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="oeis-home", description=__doc__)
    ap.add_argument("--version", action="version", version=f"oeis-home {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    key_default = str(keys.DEFAULT_KEY_PATH)

    p = sub.add_parser("keygen", help="create your Ed25519 identity key")
    p.add_argument("--path", default=key_default)
    p.set_defaults(fn=cmd_keygen)
    p = sub.add_parser("register", help="write distributed/contributors/<login>.json")
    p.add_argument("--login", required=True)
    p.add_argument("--display-name", required=True)
    p.add_argument("--oeis-credit-name", default="")
    p.add_argument("--github-id", type=int)
    p.add_argument("--role", default="worker", choices=("worker", "verifier", "bot"))
    p.add_argument("--key", default=key_default)
    p.add_argument("--old-key")
    p.add_argument("--repo")
    p.set_defaults(fn=cmd_register)
    p = sub.add_parser("unit", help="print a work unit")
    p.add_argument("unit_id")
    p.add_argument("--repo")
    p.set_defaults(fn=cmd_unit)
    p = sub.add_parser("claim", help="pick units and write advisory claim files")
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--need", default="any", choices=("any", "first", "double", "tiebreak"))
    p.add_argument("--login")
    p.add_argument("--key", default=key_default)
    p.add_argument("--ledger-url", default=RAW_LEDGER)
    p.add_argument("--repo")
    p.set_defaults(fn=cmd_claim)
    p = sub.add_parser("run", help="compute and sign a unit")
    p.add_argument("--unit", dest="unit_id", required=True)
    p.add_argument("--login")
    p.add_argument("--key", default=key_default)
    p.add_argument("--force", action="store_true")
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--repo")
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("check", help="verify signed files locally")
    p.add_argument("files", nargs="+")
    p.add_argument("--quick", action="store_true")
    p.add_argument("--repo")
    p.set_defaults(fn=cmd_check)
    p = sub.add_parser("status", help="unit states from the local checkout")
    p.add_argument("--repo")
    p.set_defaults(fn=cmd_status)
    p = sub.add_parser("verify-pr", help="CI: verify the files changed between two commits")
    p.add_argument("--base", required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--author-id", type=int)
    p.add_argument("--maintainer", action="store_true")
    p.add_argument("--time-budget", type=float)
    p.add_argument("--summary-file")
    p.add_argument("--repo")
    p.set_defaults(fn=cmd_verify_pr)
    p = sub.add_parser("rebuild", help="maintainer/CI: verify results, write verified/, ledger/, exports/, docs/")
    p.add_argument("--bot-key")
    p.add_argument("--full", action="store_true", help="re-verify everything")
    p.add_argument("--set-pari", nargs=4, metavar=("UNIT", "N", "VARIANT", "RESULT"))
    p.add_argument("--repo")
    p.set_defaults(fn=cmd_rebuild)
    return ap




def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
