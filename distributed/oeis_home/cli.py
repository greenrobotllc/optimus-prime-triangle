"""``oeis-home`` command line: keygen · register · claim · unit · run · check · status · verify-pr · rebuild."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from . import __version__, canon, families, keys, units
from .compute import run_unit
from .ledger import build as build_ledger
from .ledger import identity, next_units, trusted_signers
from .verify import LOGIN_RE, filtered_check, load_contributors, load_contributors_at, verify_claim_file, verify_pr, verify_result_file

REPO_ENV = "OEIS_HOME_REPO"
RAW_LEDGER = "https://raw.githubusercontent.com/greenrobotllc/optimus-prime-triangle/main/distributed/ledger/lehmer-q2.json"
KEY_DEFAULT = str(keys.DEFAULT_KEY_PATH)


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


def load_key(path: str):
    try:
        return keys.load(Path(path))
    except (OSError, keys.SignatureError) as exc:
        raise SystemExit(f"cannot load the key at {path}: {exc}; run `oeis-home keygen` first") from exc


def my_login(root: Path, sk, override: str | None) -> str:
    fp = keys.fingerprint(keys.public_raw(sk))
    if override:
        return override
    for login, c in load_contributors(root).items():
        if fp == c["fingerprint"] or fp in c.get("previous_fingerprints", []):
            return login
    raise SystemExit("this key is not registered yet; run `oeis-home register` (or pass --login)")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- commands
def cmd_keygen(args) -> int:
    try:
        sk = keys.generate(Path(args.path))
    except FileExistsError:
        raise SystemExit(f"{args.path} already exists; keep it (one key per account) or pass --path for a second key") from None
    print(f"wrote {args.path}\nfingerprint {keys.fingerprint(keys.public_raw(sk))}")
    return 0


def cmd_register(args) -> int:
    root = repo_root(args)
    sk = load_key(args.key)
    login = args.login.lower()
    if not LOGIN_RE.match(login):
        raise SystemExit(f"login {login!r} must match ^[a-z0-9-]{{1,39}}$ (your GitHub login) or ext-<name>")
    gid = args.github_id
    if gid is None:
        if login.startswith("ext-"):
            gid = 0
        else:
            from .github import user_id  # noqa: PLC0415

            try:
                gid = user_id(login)
            except (urllib.error.URLError, OSError, KeyError, ValueError) as exc:
                raise SystemExit(f"could not look up the GitHub id for {login} ({exc}); pass --github-id N "
                                 f"(see https://api.github.com/users/{login})") from exc
    pub = keys.public_raw(sk)
    fp = keys.fingerprint(pub)
    registry = load_contributors(root)
    for other_login, other in registry.items():
        if other_login != login and (other["fingerprint"] == fp or fp in other.get("previous_fingerprints", [])):
            raise SystemExit(f"this key is already registered under {other_login!r}; one key per account")
    payload = {"login": login, "github_id": gid, "fingerprint": fp, "pubkey": pub.hex(),
               "display_name": args.display_name, "oeis_credit_name": args.oeis_credit_name or "", "role": args.role,
               "previous_fingerprints": []}
    existing = registry.get(login)
    if existing and existing["fingerprint"] != fp:
        if not args.old_key:
            raise SystemExit(f"{login} is registered with another key; pass --old-key <old key file> to rotate")
        old = load_key(args.old_key)
        if keys.fingerprint(keys.public_raw(old)) != existing["fingerprint"]:
            raise SystemExit("--old-key is not the currently registered key")
        payload["supersedes"] = existing["fingerprint"]
        payload["rotation_sig"] = keys.rotation_signature(old, pub)
        payload["previous_fingerprints"] = [*existing.get("previous_fingerprints", []), existing["fingerprint"]]
        payload["github_id"] = existing["github_id"]
    path = root / "distributed" / "contributors" / f"{login}.json"
    write_signed(path, keys.sign_envelope("contributor", payload, sk))
    print(f"wrote {path.relative_to(root)} (github_id {payload['github_id']}, role {args.role})")
    return 0


def cmd_unit(args) -> int:
    fam = load_family(repo_root(args))
    try:
        cands = units.candidates(fam, args.unit_id)
        lo, hi = units.parse_unit_id(args.unit_id, fam.bands)
    except ValueError as exc:
        raise SystemExit(f"{exc}; valid ids look like lehmer-q2-00020000-00021000 (see `oeis-home claim`)") from None
    print(json.dumps({"unit_id": args.unit_id, "family": fam.id, "family_hash": fam.hash, "n_lo": lo, "n_hi": hi,
                      "candidates": cands[:8] + (["…"] if len(cands) > 8 else []), "n_candidates": len(cands)}, indent=1))
    return 0


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


def cmd_claim(args) -> int:
    root = repo_root(args)
    fam = load_family(root)
    sk = load_key(args.key)
    login = my_login(root, sk, args.login)
    contributors = load_contributors(root)
    try:
        from .github import fetch_ledger  # noqa: PLC0415

        ledger = fetch_ledger(args.ledger_url)
    except Exception as exc:  # noqa: BLE001
        print(f"upstream ledger unavailable ({type(exc).__name__}); using the local checkout, which may be stale", file=sys.stderr)
        ledger = build_ledger(root, fam, contributors, _claims(root), allow_unsigned=True)
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
    sk = load_key(args.key)
    login = my_login(root, sk, args.login)
    fp = keys.fingerprint(keys.public_raw(sk))
    udir = root / "distributed" / "results" / "lehmer-q2" / args.unit_id
    out = udir / f"{login}.json"
    if out.exists():
        if not args.force:
            raise SystemExit(f"{out.relative_to(root)} exists; merged results are add-only. Use --force to write a fresh run as {login}-2.json")
        k = 2
        while (udir / f"{login}-{k}.json").exists():
            k += 1
        out = udir / f"{login}-{k}.json"
    partial = udir / f".{login}.partial.json"
    progress = None if args.quiet else (lambda msg: print(msg, flush=True))
    try:
        payload = run_unit(fam, args.unit_id, fp, login, progress=progress, partial_path=partial)
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    except KeyboardInterrupt:
        raise SystemExit("interrupted; progress saved — rerun the same command to resume") from None
    write_signed(out, keys.sign_envelope("result", payload, sk))
    s = payload["summary"]
    print(f"wrote {out.relative_to(root)}: {len(payload['verdicts'])} lines, {s['prp']} prp, {s['prime']} prime, {s['composite']} composite, "
          f"{payload['wall_ms'] / 1000:.0f} s", flush=True)
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
            rep = verify_result_file(path, fam, contributors, releases, full=not args.quick, reference_check="optional")
        elif "/claims/" in str(path.resolve()):
            rep = verify_claim_file(path, fam, contributors)
        else:
            from .verify import verify_contributor_file  # noqa: PLC0415

            rep = verify_contributor_file(path, None, contributors, maintainer=True)
        print(f"{'OK  ' if rep.ok else 'FAIL'} {path}  lines={rep.lines_checked} recomputed={rep.recomputed} prp={rep.prp_confirmed}")
        for e in rep.errors:
            print("   ", e)
        for note in rep.notes[:3]:
            print("    note:", note)
        rc |= 0 if rep.ok else 1
    return rc


def cmd_status(args) -> int:
    root = repo_root(args)
    fam = load_family(root)
    ledger = build_ledger(root, fam, load_contributors(root), _claims(root), allow_unsigned=True)
    print(json.dumps({"counts": ledger["counts"], "verified_through": ledger["verified_through"],
                      "positive_claims": [(p["n"], p["variant"], p.get("discoverer_login", "")) for p in ledger["positive_claims"]]}, indent=1))
    return 0


def cmd_verify_pr(args) -> int:
    root = repo_root(args)
    fam = load_family(root)
    from .github import changed_files  # noqa: PLC0415

    summary: dict = {"ok": False, "errors": ["verification did not complete"]}
    try:
        changed = changed_files(root, args.base, args.head)
        base_registry = load_contributors_at(root, args.base)
        rep = verify_pr(root, changed, args.author_id, fam, load_releases(root), maintainer=args.maintainer, full=True,
                        time_budget_s=args.time_budget, base_contributors=base_registry, pr_author_login=args.author_login,
                        reference_check="require" if args.require_reference else "optional")
        summary = {"ok": rep.ok, "files": len(changed), "lines_checked": rep.lines_checked, "recomputed": rep.recomputed,
                   "reference_checked": rep.reference_checked, "prp_confirmed": rep.prp_confirmed, "errors": rep.errors, "notes": rep.notes}
    finally:
        print(json.dumps(summary, indent=1))
        if args.summary_file:
            Path(args.summary_file).write_text(json.dumps(summary, indent=1))
    return 0 if summary["ok"] else 1


def _write_pari_notes(root: Path, sk, notes: list[dict]) -> None:
    vdir = root / "distributed" / "verified" / "lehmer-q2"
    by_unit: dict[str, list[dict]] = {}
    for n in notes:
        by_unit.setdefault(n["unit_id"], []).append(n)
    for uid, new_notes in by_unit.items():
        path = vdir / f"{uid}.pari.json"
        old: list[dict] = []
        if path.exists():
            try:
                old = canon.check_file_bytes(path.read_bytes())["payload"]["notes"]
            except Exception:  # noqa: BLE001
                old = []
        keep = [x for x in old if not any(x["n"] == y["n"] and x["variant"] == y["variant"] for y in new_notes)]
        payload = {"unit_id": uid, "notes": sorted(keep + new_notes, key=lambda x: (x["n"], x["variant"])), "recorded_at": now_iso()}
        write_signed(path, keys.sign_envelope("note", payload, sk))


def _copied_results(root: Path, valid: list[dict]) -> set[str]:
    """Results under different logins with identical residue vectors did not do independent work."""
    vectors: dict[tuple, list[str]] = {}
    for r in valid:
        try:
            env = canon.check_file_bytes((root / r["path"]).read_bytes())
        except Exception:  # noqa: BLE001
            continue
        key = tuple((x["n"], x["variant"], x["v"], x.get("res64", ""), x.get("factor", "")) for x in env["payload"]["verdicts"] if x.get("res64"))
        vectors.setdefault(key, []).append(r["path"])
    return {p for paths in vectors.values() if len(paths) > 1 for p in paths}


def cmd_rebuild(args) -> int:
    root = repo_root(args)
    fam = load_family(root)
    contributors = load_contributors(root)
    releases = load_releases(root)
    vdir = root / "distributed" / "verified" / "lehmer-q2"
    vdir.mkdir(parents=True, exist_ok=True)
    bot = load_key(args.bot_key) if args.bot_key else None
    if bot is None and not args.allow_unsigned:
        raise SystemExit("rebuild needs --bot-key (a registered role:bot key) or --allow-unsigned for a local, untrusted rebuild")
    if bot is not None and keys.fingerprint(keys.public_raw(bot)) not in trusted_signers(contributors, ("bot",)):
        raise SystemExit("the --bot-key is not registered as a role:bot contributor")
    signer = load_key(args.key) if args.key else None
    if args.set_pari or args.set_pari_file:
        if signer is None or keys.fingerprint(keys.public_raw(signer)) not in trusted_signers(contributors, ("verifier", "bot")):
            raise SystemExit("--set-pari needs --key pointing at a registered verifier or bot key (maintainer-signed notes)")
        notes: list[dict] = []
        if args.set_pari:
            uid, n, variant, result = args.set_pari
            notes.append({"unit_id": uid, "n": int(n), "variant": variant, "result": result})
        if args.set_pari_file:
            with open(args.set_pari_file, newline="") as fh:
                for row in csv.DictReader(fh):
                    notes.append({"unit_id": row["unit_id"], "n": int(row["n"]), "variant": row["variant"], "result": row["result"]})
        for note in notes:
            if note["result"] not in ("isprime", "ispseudoprime", "composite"):
                raise SystemExit(f"bad gp result {note['result']!r}")
        _write_pari_notes(root, signer, notes)
        print(f"recorded {len(notes)} signed gp note(s)")
    withdrawn = {r["worker_sha256"] for r in releases.get("withdrawn", [])}
    from .github import file_first_merge, pr_for_commit  # noqa: PLC0415

    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    rdir = root / "distributed" / "results" / "lehmer-q2"
    unit_dirs = sorted(p for p in rdir.iterdir() if p.is_dir()) if rdir.exists() else []
    for unit_dir in unit_dirs:
        uid = unit_dir.name
        try:
            lo, hi = units.parse_unit_id(uid, fam.bands)
        except ValueError as exc:
            print(f"{uid}: skipped ({exc})", flush=True)
            continue
        results = []
        canonical = ""
        verdict_rows: list[dict] = []
        for path in sorted(p for p in unit_dir.glob("*.json") if not p.name.startswith(".")):
            rel = str(path.relative_to(root))
            try:
                rep = verify_result_file(path, fam, contributors, releases, full=True,
                                         reference_check="require" if args.require_reference else "optional")
            except Exception as exc:  # noqa: BLE001
                rep = verify_result_file.__globals__["Report"](ok=False, errors=[f"malformed ({type(exc).__name__})"])
            payload = rep.payload or {}
            sw = payload.get("software", {}).get("worker_sha256", "")
            status = "withdrawn" if sw in withdrawn else ("valid" if rep.ok else "invalid")
            merge = file_first_merge(root, rel)
            meta = pr_for_commit(args.github_repo, merge["sha"], os.environ.get("GITHUB_TOKEN")) if args.github_repo and merge["sha"] else {}
            entry = {"path": rel, "login": payload.get("login", path.stem.split("-")[0]), "worker": payload.get("worker", ""),
                     "worker_sha256": sw, "status": status, "merge_sha": merge["sha"], "merged_at": merge["committed_at"],
                     "pr_number": meta.get("pr_number", 0), "pr_created_at": meta.get("pr_created_at") or merge["committed_at"],
                     "ci_run_id": run_id, "lines_recomputed": rep.recomputed, "lines_total": rep.lines_checked, "errors": rep.errors[:5]}
            results.append(entry)
            print(f"{uid} {rel}: {status} ({rep.recomputed} lines recomputed){'; ' + '; '.join(rep.errors[:2]) if rep.errors else ''}", flush=True)
        valid = [r for r in results if r["status"] == "valid"]
        for r in results:
            c = contributors.get(r["login"], {})
            r["github_id"], r["role"] = c.get("github_id", 0), c.get("role", "worker")
        copied = _copied_results(root, valid)
        for r in results:
            if r["path"] in copied:
                r["status"] = "invalid"
                r["errors"] = ["copied: identical residues under another login"]
        valid = [r for r in results if r["status"] == "valid"]
        vecs = {}
        for r in valid:
            env = canon.check_file_bytes((root / r["path"]).read_bytes())
            vecs[r["path"]] = tuple((x["n"], x["variant"], x["v"]) for x in env["payload"]["verdicts"])
        disputed = len(set(vecs.values())) > 1
        if valid:
            canonical = min(valid, key=lambda r: (r["pr_created_at"] or "9", r["path"]))["path"]
            env = canon.check_file_bytes((root / canonical).read_bytes())
            verdict_rows = [{k: v for k, v in rec.items() if k in ("n", "variant", "v", "method", "digits", "factor")} for rec in env["payload"]["verdicts"]]
        fchk = filtered_check(fam, uid)
        positive = []
        for rec in verdict_rows:
            if rec["v"] != "prp":
                continue
            holders = sorted((r for r in valid if (rec["n"], rec["variant"], "prp") in vecs[r["path"]]), key=lambda r: (r["pr_created_at"] or "9", r["path"]))
            first = holders[0] if holders else None
            second = next((r for r in holders[1:] if identity(r) != identity(first)), None) if first else None
            positive.append({"n": rec["n"], "variant": rec["variant"], "digits": rec["digits"],
                             "discoverer_login": first["login"] if first else "", "discovered_at": first["pr_created_at"] if first else "",
                             "verifier_login": second["login"] if second else "", "ci_confirmed": bool(first) and run_id != "local",
                             "ci_run_id": run_id, "maintainer_pari": "none", "cert_sha256": ""})
        credits = []
        seen: set[str] = set()
        for r in sorted(valid, key=lambda r: (r["pr_created_at"] or "9", r["path"])):
            ident = identity(r)
            credits.append({"login": r["login"], "display_name": contributors.get(r["login"], {}).get("display_name", r["login"]),
                            "role": "first" if not seen else ("double" if ident not in seen else "repeat")})
            seen.add(ident)
        payload_v = {"unit_id": uid, "family_hash": fam.hash, "n_lo": lo, "n_hi": hi, "results": results, "canonical": canonical,
                     "filtered_checked": {"count": fchk["count"], "ok": fchk["ok"], "run_id": run_id},
                     "verdicts": verdict_rows, "positive_claims": positive, "credits": credits, "disputed": disputed, "decided_at": now_iso()}
        vpath = vdir / f"{uid}.json"
        if bot is not None:
            write_signed(vpath, keys.sign_envelope("verified", payload_v, bot))
        else:
            vpath.write_bytes(canon.canon({"kind": "verified", "payload": payload_v, "signature": None}) + b"\n")
    ledger = build_ledger(root, fam, contributors, _claims(root), allow_unsigned=bot is None)
    (root / "distributed" / "ledger").mkdir(exist_ok=True)
    (root / "distributed" / "ledger" / "lehmer-q2.json").write_text(json.dumps(ledger, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    from .export import write_exports  # noqa: PLC0415
    from .report import render_site  # noqa: PLC0415

    write_exports(ledger, fam, contributors, root / "distributed" / "exports" / "lehmer-q2")
    render_site(ledger, contributors, fam, root / "distributed" / "docs", built_from=os.environ.get("GITHUB_SHA", "")[:12])
    print(json.dumps({"counts": ledger["counts"], "verified_through": ledger["verified_through"], "positive": len(ledger["positive_claims"])}), flush=True)
    return 0


# --------------------------------------------------------------------------- parser
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="oeis-home", description=__doc__)
    ap.add_argument("--version", action="version", version=f"oeis-home {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("keygen", help="create your Ed25519 identity key")
    p.add_argument("--path", default=KEY_DEFAULT)
    p.set_defaults(fn=cmd_keygen)

    p = sub.add_parser("register", help="write distributed/contributors/<login>.json")
    p.add_argument("--login", required=True)
    p.add_argument("--display-name", required=True)
    p.add_argument("--oeis-credit-name", default="")
    p.add_argument("--github-id", type=int)
    p.add_argument("--role", default="worker", choices=("worker", "verifier", "bot"))
    p.add_argument("--key", default=KEY_DEFAULT)
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
    p.add_argument("--key", default=KEY_DEFAULT)
    p.add_argument("--ledger-url", default=RAW_LEDGER)
    p.add_argument("--repo")
    p.set_defaults(fn=cmd_claim)

    p = sub.add_parser("run", help="compute and sign a unit")
    p.add_argument("--unit", dest="unit_id", required=True)
    p.add_argument("--login")
    p.add_argument("--key", default=KEY_DEFAULT)
    p.add_argument("--force", action="store_true", help="write a fresh run as <login>-<k>.json when one exists")
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
    p.add_argument("--author-login")
    p.add_argument("--maintainer", action="store_true")
    p.add_argument("--require-reference", action="store_true", help="fail if the independent core_math evaluator is unavailable")
    p.add_argument("--time-budget", type=float)
    p.add_argument("--summary-file")
    p.add_argument("--repo")
    p.set_defaults(fn=cmd_verify_pr)

    p = sub.add_parser("rebuild", help="maintainer/CI: re-derive verified/, ledger/, exports/, docs/ from the signed results")
    p.add_argument("--bot-key", help="registered role:bot key that signs verified records")
    p.add_argument("--allow-unsigned", action="store_true", help="local rebuild without a bot key (records are marked unsigned)")
    p.add_argument("--key", help="registered verifier/bot key for --set-pari notes")
    p.add_argument("--set-pari", nargs=4, metavar=("UNIT", "N", "VARIANT", "RESULT"))
    p.add_argument("--set-pari-file", help="CSV with columns unit_id,n,variant,result")
    p.add_argument("--github-repo", help="owner/name; enables PR metadata lookups (GITHUB_TOKEN)")
    p.add_argument("--require-reference", action="store_true")
    p.add_argument("--repo")
    p.set_defaults(fn=cmd_rebuild)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
