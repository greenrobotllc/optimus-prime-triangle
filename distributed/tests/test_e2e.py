"""End-to-end on the tiny-band family: two keys run one unit, everything verifies, rebuild double-checks it."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from oeis_home import canon, cli, keys
from oeis_home.compute import run_unit, worker_sha256
from oeis_home.families import abs_value
from oeis_home.verify import filtered_check, load_contributors, verify_pr, verify_result_file

UID = "lehmer-q2-00000000-00000200"


@pytest.fixture(scope="module")
def payloads(tiny_fam, fixture_keys):
    out = {}
    for login in ("alice", "bob"):
        fp = keys.fingerprint(keys.public_raw(fixture_keys[login]))
        out[login] = run_unit(tiny_fam, UID, fp, login, progress=None)
    return out


def _write(root: Path, login: str, payload: dict, sk, name: str | None = None) -> Path:
    path = root / "distributed" / "results" / "lehmer-q2" / UID / f"{name or login}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canon.file_bytes(keys.sign_envelope("result", payload, sk)))
    return path


def test_run_unit_payload_shape(tiny_fam, payloads):
    p = payloads["alice"]
    assert p["unit_id"] == UID and p["family_hash"] == tiny_fam.hash and len(p["verdicts"]) > 60
    assert p["summary"]["prp"] >= 2 and p["software"]["worker_sha256"] == worker_sha256()
    assert [v["v"] for v in payloads["alice"]["verdicts"]] == [v["v"] for v in payloads["bob"]["verdicts"]]   # same verdicts, different residues
    assert payloads["alice"]["base"] != payloads["bob"]["base"]


def test_resume_from_partial(tiny_fam, fixture_keys, tmp_path):
    fp = keys.fingerprint(keys.public_raw(fixture_keys["alice"]))
    partial = tmp_path / "p.json"
    full = run_unit(tiny_fam, UID, fp, "alice", progress=None)
    partial.write_text(json.dumps({"unit_id": UID, "base": full["base"], "worker": fp, "verdicts": full["verdicts"][:10]}))
    resumed = run_unit(tiny_fam, UID, fp, "alice", progress=None, partial_path=partial)
    assert resumed["verdicts"] == full["verdicts"] and not partial.exists()


def test_valid_results_and_named_rejections(tiny_repo, tiny_fam, fixture_keys, payloads):
    root = tiny_repo
    releases = json.loads((root / "distributed" / "RELEASES.json").read_text())
    contributors = load_contributors(root)
    ok = _write(root, "alice", payloads["alice"], fixture_keys["alice"])
    rep = verify_result_file(ok, tiny_fam, contributors, releases)
    assert rep.ok and rep.recomputed == len(payloads["alice"]["verdicts"]) and rep.prp_confirmed, rep.errors

    def expect_fail(label, path, needle):
        r = verify_result_file(path, tiny_fam, contributors, releases)
        assert not r.ok and any(needle in e for e in r.errors), (label, r.errors)
        path.unlink()

    # copied file under another login (bob signs alice's payload)
    expect_fail("copied", _write(root, "bob", payloads["alice"], fixture_keys["bob"]), "file name must be <login>.json")
    p = copy.deepcopy(payloads["bob"])
    p["login"] = "bob"
    p2 = copy.deepcopy(payloads["alice"])
    p2["login"] = "bob"
    p2["worker"] = payloads["bob"]["worker"]
    expect_fail("copied residues", _write(root, "bob", p2, fixture_keys["bob"]), "base")
    # altered verdict
    p = copy.deepcopy(payloads["bob"])
    idx = next(i for i, v in enumerate(p["verdicts"]) if v["v"] == "prp")
    p["verdicts"][idx]["v"] = "composite"
    expect_fail("altered", _write(root, "bob", p, fixture_keys["bob"]), "summary")
    p["summary"]["prp"] -= 1
    p["summary"]["composite"] += 1
    expect_fail("altered2", _write(root, "bob", p, fixture_keys["bob"]), "recomputed")
    # wrong base
    p = copy.deepcopy(payloads["bob"])
    p["base"] = 7
    expect_fail("base", _write(root, "bob", p, fixture_keys["bob"]), "worker base")
    # factor == N
    p = copy.deepcopy(payloads["bob"])
    idx = next(i for i, v in enumerate(p["verdicts"]) if v["method"] == "factor")
    p["verdicts"][idx]["factor"] = str(abs_value(p["verdicts"][idx]["variant"], p["verdicts"][idx]["n"]))
    expect_fail("factor==N", _write(root, "bob", p, fixture_keys["bob"]), "recomputed")
    # missing / extra candidate
    p = copy.deepcopy(payloads["bob"])
    p["verdicts"].pop(3)
    expect_fail("missing", _write(root, "bob", p, fixture_keys["bob"]), "verdicts, expected")
    p = copy.deepcopy(payloads["bob"])
    p["verdicts"].append(p["verdicts"][-1])
    expect_fail("extra", _write(root, "bob", p, fixture_keys["bob"]), "verdicts, expected")
    # CRLF file, wrong family hash, withdrawn version, unknown kind, duplicate key
    path = _write(root, "bob", payloads["bob"], fixture_keys["bob"])
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    expect_fail("crlf", path, "canonical")
    p = copy.deepcopy(payloads["bob"])
    p["family_hash"] = "sha256:" + "0" * 64
    expect_fail("hash", _write(root, "bob", p, fixture_keys["bob"]), "family_hash")
    p = copy.deepcopy(payloads["bob"])
    p["software"]["worker_sha256"] = "1" * 64
    expect_fail("version", _write(root, "bob", p, fixture_keys["bob"]), "accepted release")
    env = keys.sign_envelope("claim", payloads["bob"], fixture_keys["bob"])
    path = root / "distributed" / "results" / "lehmer-q2" / UID / "bob.json"
    path.write_bytes(canon.file_bytes(env))
    expect_fail("kind", path, "unexpected kind")
    path.write_bytes(b'{"kind":"result","kind":"result"}\n')
    expect_fail("dup", path, "duplicate key")
    # the honest second result passes
    assert verify_result_file(_write(root, "bob", payloads["bob"], fixture_keys["bob"]), tiny_fam, contributors, releases).ok


def test_verify_pr_policy_and_rebuild(tiny_repo, tiny_fam, fixture_keys, payloads, monkeypatch):
    root = tiny_repo
    releases = json.loads((root / "distributed" / "RELEASES.json").read_text())
    rel_a = f"distributed/results/lehmer-q2/{UID}/alice.json"
    rep = verify_pr(root, [("A", rel_a)], 1001, tiny_fam, releases)
    assert rep.ok, rep.errors
    assert not verify_pr(root, [("A", rel_a)], 1002, tiny_fam, releases).ok                 # bob cannot submit alice's file
    assert not verify_pr(root, [("M", rel_a)], 1001, tiny_fam, releases).ok                 # results are add-only
    assert not verify_pr(root, [("A", "distributed/oeis_home/compute.py")], 1001, tiny_fam, releases).ok
    assert not verify_pr(root, [("A", "distributed/contributors/mallory.json")], 1001, tiny_fam, releases).ok
    assert filtered_check(tiny_fam, UID)["ok"]
    # rebuild through the CLI on the temp repo (no git history -> merge metadata empty)
    monkeypatch.setenv("OEIS_HOME_REPO", str(root))
    assert cli.main(["rebuild", "--repo", str(root)]) == 0
    verified = json.loads((root / "distributed" / "verified" / "lehmer-q2" / f"{UID}.json").read_text())["payload"]
    assert [r["status"] for r in verified["results"]] == ["valid", "valid"] and verified["filtered_checked"]["ok"]
    ledger = json.loads((root / "distributed" / "ledger" / "lehmer-q2.json").read_text())
    assert ledger["units"][UID]["state"] == "double_checked"
    assert (root / "distributed" / "docs" / "index.html").exists() and (root / "distributed" / "exports" / "lehmer-q2" / "oeis_draft.txt").exists()
    positives = [p for p in ledger["positive_claims"] if p["unit_id"] == UID]
    assert positives and all(p["verifier_login"] for p in positives)
    assert ledger["verified_through"] == 0                                                    # gp checks not yet recorded
    for p in positives:
        assert cli.main(["rebuild", "--repo", str(root), "--set-pari", UID, str(p["n"]), p["variant"], "isprime"]) == 0
    ledger = json.loads((root / "distributed" / "ledger" / "lehmer-q2.json").read_text())
    assert ledger["verified_through"] == 200
    ready = json.loads((root / "distributed" / "exports" / "lehmer-q2" / "evidence.json").read_text())
    assert ready["sequences"]["A3"]["data"].startswith("0,4,5,6,8,9,10,11,12,13,14,16,17,19,21,22,26,29,31,32,34,43,46,47,58,59,61,67,73,82,86,94,101,109,113")
    snippet = (root / "distributed" / "docs" / "index.html").read_text()
    assert "psi_mod(2," in snippet


def test_cli_check_and_status(tiny_repo, monkeypatch, capsys):
    root = tiny_repo
    monkeypatch.setenv("OEIS_HOME_REPO", str(root))
    assert cli.main(["check", "--repo", str(root), str(root / "distributed" / "results" / "lehmer-q2" / UID / "alice.json")]) == 0
    assert cli.main(["status", "--repo", str(root)]) == 0
    out = capsys.readouterr().out
    assert "double_checked" in out and "OK" in out
