"""GitHub metadata (PR author id and timestamps) and git history lookups.  Timestamps are never
taken from the signed files themselves."""
from __future__ import annotations

import json
import subprocess
import urllib.request
from pathlib import Path


def _get_json(url: str, token: str | None = None) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "oeis-home"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def user_id(login: str, token: str | None = None) -> int:
    """Numeric GitHub user id for a login (public endpoint)."""
    return int(_get_json(f"https://api.github.com/users/{login}", token)["id"])


def pr_meta(repo: str, pr_number: int, token: str | None = None) -> dict:
    d = _get_json(f"https://api.github.com/repos/{repo}/pulls/{pr_number}", token)
    return {"author_id": int(d["user"]["id"]), "author_login": d["user"]["login"].lower(), "created_at": d["created_at"],
            "merged_at": d.get("merged_at") or "", "merge_commit_sha": d.get("merge_commit_sha") or ""}


def file_first_merge(repo_path: Path, rel_path: str) -> dict:
    """Commit that first added ``rel_path`` on the current branch: ``{"sha", "committed_at"}``."""
    out = subprocess.run(["git", "-C", str(repo_path), "log", "--diff-filter=A", "--follow", "--format=%H%x09%cI", "--", rel_path],
                         capture_output=True, text=True, check=False).stdout.strip().splitlines()
    if not out:
        return {"sha": "", "committed_at": ""}
    sha, when = out[-1].split("\t")
    return {"sha": sha, "committed_at": when}


def changed_files(repo_path: Path, base: str, head: str) -> list[tuple[str, str]]:
    """``[(status, path)]`` between two commits (``A`` added, ``M`` modified, ``D`` deleted, ``R`` renamed)."""
    out = subprocess.run(["git", "-C", str(repo_path), "diff", "--name-status", f"{base}...{head}"],   # merge-base diff
                         capture_output=True, text=True, check=True).stdout.strip().splitlines()
    rows = []
    for line in out:
        parts = line.split("\t")
        rows.append((parts[0][0], parts[-1]))
    return rows


def pr_for_commit(repo: str, sha: str, token: str | None = None) -> dict:
    """The pull request that introduced ``sha`` on the default branch (``{}`` if none / offline)."""
    if not sha:
        return {}
    try:
        rows = _get_json(f"https://api.github.com/repos/{repo}/commits/{sha}/pulls", token)
    except Exception:  # noqa: BLE001 - offline or no token: caller falls back to commit time
        return {}
    merged = [r for r in rows if r.get("merged_at")] or rows
    if not merged:
        return {}
    r = merged[0]
    return {"pr_number": int(r["number"]), "pr_created_at": r["created_at"], "author_login": r["user"]["login"].lower(),
            "author_id": int(r["user"]["id"])}


LEDGER_HOSTS = ("raw.githubusercontent.com",)


def fetch_ledger(raw_url: str) -> dict:
    """Fetch the upstream ledger; only https URLs on the GitHub raw host are accepted."""
    from urllib.parse import urlsplit  # noqa: PLC0415

    u = urlsplit(raw_url)
    if u.scheme != "https" or u.hostname not in LEDGER_HOSTS:
        raise ValueError(f"ledger URL must be https on {LEDGER_HOSTS}, got {raw_url!r}")
    with urllib.request.urlopen(urllib.request.Request(raw_url, headers={"User-Agent": "oeis-home"}), timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))
