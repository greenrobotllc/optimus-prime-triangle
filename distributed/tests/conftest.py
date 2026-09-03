"""Fixtures for the OEIS@home tests: a tiny-band family (fast units) and two fixture keys."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from oeis_home import canon, families, keys
from oeis_home.compute import worker_sha256

DIST = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def fam():
    return families.load(DIST / "families" / "lehmer-q2.json")


@pytest.fixture(scope="session")
def tiny_family_path(tmp_path_factory) -> Path:
    """Same family (same hash) with 200-wide units below 400, so a unit takes seconds."""
    raw = json.loads((DIST / "families" / "lehmer-q2.json").read_text())
    raw["bands"] = [[0, 400, 200]]
    raw["n_max_open"] = 400
    path = tmp_path_factory.mktemp("fam") / "lehmer-q2.json"
    path.write_text(json.dumps(raw))
    return path


@pytest.fixture(scope="session")
def tiny_fam(tiny_family_path):
    f = families.load(tiny_family_path)
    assert f.hash == families.load(DIST / "families" / "lehmer-q2.json").hash
    return f


@pytest.fixture(scope="session")
def fixture_keys():
    return {"alice": Ed25519PrivateKey.generate(), "bob": Ed25519PrivateKey.generate(), "bot": Ed25519PrivateKey.generate()}


def contributor_payload(login: str, sk, github_id: int, role: str = "worker") -> dict:
    pub = keys.public_raw(sk)
    return {"login": login, "github_id": github_id, "fingerprint": keys.fingerprint(pub), "pubkey": pub.hex(),
            "display_name": login.title(), "oeis_credit_name": "", "role": role, "previous_fingerprints": []}


@pytest.fixture(scope="session")
def make_contributor():
    return contributor_payload


@pytest.fixture(scope="session")
def tiny_repo(tmp_path_factory, tiny_family_path, fixture_keys) -> Path:
    """A throw-away repository layout with the tiny family, RELEASES and two registered contributors."""
    root = tmp_path_factory.mktemp("repo")
    d = root / "distributed"
    (d / "families").mkdir(parents=True)
    shutil.copy(tiny_family_path, d / "families" / "lehmer-q2.json")
    (d / "RELEASES.json").write_text(json.dumps({"accepted": [{"version": "0.1.0", "worker_sha256": worker_sha256(), "git_tag": "t"}], "withdrawn": []}))
    for sub in ("contributors", "claims/lehmer-q2", "results/lehmer-q2", "verified/lehmer-q2", "ledger", "exports", "docs"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    for login, gid in (("alice", 1001), ("bob", 1002)):
        env = keys.sign_envelope("contributor", contributor_payload(login, fixture_keys[login], gid), fixture_keys[login])
        (d / "contributors" / f"{login}.json").write_bytes(canon.file_bytes(env))
    env = keys.sign_envelope("contributor", contributor_payload("ext-bot", fixture_keys["bot"], 0, role="bot"), fixture_keys["bot"])
    (d / "contributors" / "ext-bot.json").write_bytes(canon.file_bytes(env))
    return root
