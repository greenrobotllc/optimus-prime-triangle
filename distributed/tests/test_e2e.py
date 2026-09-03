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
    assert all("/" in x for x in rep.prp_confirmed) and rep.reference_checked == len(rep.prp_confirmed)

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


def test_verify_pr_policy_and_rebuild(tiny_repo, tiny_fam, fixture_keys, payloads, monkeypatch, tmp_path):
    root = tiny_repo
    releases = json.loads((root / "distributed" / "RELEASES.json").read_text())
    rel_a = f"distributed/results/lehmer-q2/{UID}/alice.json"
    base_reg = load_contributors(root)
    rep = verify_pr(root, [("A", rel_a)], 1001, tiny_fam, releases, base_contributors=base_reg, pr_author_login="alice", reference_check="require")
    assert rep.ok, rep.errors
    assert not verify_pr(root, [("A", rel_a)], 1002, tiny_fam, releases, base_contributors=base_reg).ok       # bob cannot submit alice's file
    assert not verify_pr(root, [("M", rel_a)], 1001, tiny_fam, releases, base_contributors=base_reg).ok       # results are add-only
    assert not verify_pr(root, [("A", "distributed/oeis_home/compute.py")], 1001, tiny_fam, releases, base_contributors=base_reg).ok
    assert not verify_pr(root, [("A", "distributed/verified/lehmer-q2/x.json")], 1001, tiny_fam, releases, base_contributors=base_reg).ok
    assert not verify_pr(root, [("A", f"distributed/results/lehmer-q2/{UID}/.alice.partial.json")], 1001, tiny_fam, releases, base_contributors=base_reg).ok
    assert filtered_check(tiny_fam, UID)["ok"]
    # rebuild needs a registered bot key (or an explicit unsigned local mode)
    monkeypatch.setenv("OEIS_HOME_REPO", str(root))
    bot_path = tmp_path / "bot.key"
    bot_path.write_bytes(fixture_keys["bot"].private_bytes_raw())
    with pytest.raises(SystemExit):
        cli.main(["rebuild", "--repo", str(root)])
    assert cli.main(["rebuild", "--repo", str(root), "--bot-key", str(bot_path)]) == 0
    verified = json.loads((root / "distributed" / "verified" / "lehmer-q2" / f"{UID}.json").read_text())["payload"]
    assert [r["status"] for r in verified["results"]] == ["valid", "valid"] and verified["filtered_checked"]["ok"]
    ledger = json.loads((root / "distributed" / "ledger" / "lehmer-q2.json").read_text())
    assert ledger["units"][UID]["state"] == "double_checked" and not ledger["units"][UID].get("unsigned")
    assert (root / "distributed" / "docs" / "index.html").exists() and (root / "distributed" / "exports" / "lehmer-q2" / "oeis_draft.txt").exists()
    positives = [p for p in ledger["positive_claims"] if p["unit_id"] == UID]
    assert positives and all(p["verifier_login"] for p in positives)
    assert all(p["ci_confirmed"] is False for p in positives)                                 # local rebuild is not CI
    assert ledger["verified_through"] == 131                    # index-based: final up to the first prp without a gp check (n = 131)
    draft = (root / "distributed" / "exports" / "lehmer-q2" / "oeis_draft.txt").read_text()
    assert "%S A3 0,4,5,6,8,9,10,11,12,13,14,16,17,19,21,22,26,29,31,32,34,43,46,47,58,59,61,67,73,82,86,94,101,109,113" in draft
    assert "position is not yet determined" in draft and "[EMPTY" not in draft
    # gp notes must be signed by a verifier/bot key; then verified_through advances by index, and CI confirmation is simulated
    with pytest.raises(SystemExit):
        cli.main(["rebuild", "--repo", str(root), "--bot-key", str(bot_path), "--set-pari", UID, str(positives[0]["n"]), positives[0]["variant"], "isprime"])
    csv_path = root / "pari.csv"
    csv_path.write_text("unit_id,n,variant,result\n" + "".join(f"{UID},{p['n']},{p['variant']},isprime\n" for p in positives))
    monkeypatch.setenv("GITHUB_RUN_ID", "424242")
    assert cli.main(["rebuild", "--repo", str(root), "--bot-key", str(bot_path), "--key", str(bot_path), "--set-pari-file", str(csv_path)]) == 0
    ledger = json.loads((root / "distributed" / "ledger" / "lehmer-q2.json").read_text())
    assert ledger["verified_through"] == 200
    monkeypatch.delenv("GITHUB_RUN_ID")
    ready = json.loads((root / "distributed" / "exports" / "lehmer-q2" / "evidence.json").read_text())
    assert ready["sequences"]["A3"]["data"].startswith("0,4,5,6,8,9,10,11,12,13,14,16,17,19,21,22,26,29,31,32,34,43,46,47,58,59,61,67,73,82,86,94,101,109,113")
    assert all(t["status"] == "proven" for t in ready["sequences"]["A3"]["terms"])         # gp isprime reached the export
    snippet = (root / "distributed" / "docs" / "index.html").read_text()
    assert "psi_mod(2," in snippet


def test_cli_check_and_status(tiny_repo, monkeypatch, capsys):
    root = tiny_repo
    monkeypatch.setenv("OEIS_HOME_REPO", str(root))
    assert cli.main(["check", "--repo", str(root), str(root / "distributed" / "results" / "lehmer-q2" / UID / "alice.json")]) == 0
    assert cli.main(["status", "--repo", str(root)]) == 0
    out = capsys.readouterr().out
    assert "double_checked" in out and "OK" in out


def test_identity_attacks_are_rejected(tiny_repo, tiny_fam, fixture_keys, payloads, tmp_path, make_contributor):
    """Registry semantics: base-commit registry, login = PR author, one key per login, rotation keeps history."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    contributor_payload = make_contributor

    root = tiny_repo
    releases = json.loads((root / "distributed" / "RELEASES.json").read_text())
    base_reg = load_contributors(root)
    cdir = root / "distributed" / "contributors"
    mallory = Ed25519PrivateKey.generate()
    # 1. Mallory (id 5555) replaces alice.json with her own key: rejected even though the working tree now holds her file
    alice_path = cdir / "alice.json"
    original = alice_path.read_bytes()
    alice_path.write_bytes(canon.file_bytes(keys.sign_envelope("contributor", contributor_payload("alice", mallory, 5555), mallory)))
    rep = verify_pr(root, [("M", "distributed/contributors/alice.json")], 5555, tiny_fam, releases, base_contributors=base_reg, pr_author_login="alice")
    assert not rep.ok and any("github_id may not change" in e or "rotation_sig" in e for e in rep.errors), rep.errors
    # 2. same id, new key, but no rotation signature: rejected
    alice_path.write_bytes(canon.file_bytes(keys.sign_envelope("contributor", contributor_payload("alice", mallory, 1001), mallory)))
    rep = verify_pr(root, [("M", "distributed/contributors/alice.json")], 1001, tiny_fam, releases, base_contributors=base_reg, pr_author_login="alice")
    assert not rep.ok and any("rotation_sig" in e for e in rep.errors)
    # 3. proper rotation: accepted, and alice's OLD result still verifies under the new registry
    new_payload = contributor_payload("alice", mallory, 1001)
    new_payload["supersedes"] = base_reg["alice"]["fingerprint"]
    new_payload["rotation_sig"] = keys.rotation_signature(fixture_keys["alice"], keys.public_raw(mallory))
    new_payload["previous_fingerprints"] = [base_reg["alice"]["fingerprint"]]
    alice_path.write_bytes(canon.file_bytes(keys.sign_envelope("contributor", new_payload, mallory)))
    rep = verify_pr(root, [("M", "distributed/contributors/alice.json")], 1001, tiny_fam, releases, base_contributors=base_reg, pr_author_login="alice")
    assert rep.ok, rep.errors
    old_result = root / "distributed" / "results" / "lehmer-q2" / UID / "alice.json"
    assert verify_result_file(old_result, tiny_fam, load_contributors(root), releases, full=False).ok
    alice_path.write_bytes(original)
    # 4. login squatting: author 'carol' (id 7777) registering 'dave': rejected
    carol = Ed25519PrivateKey.generate()
    dave_path = cdir / "dave.json"
    dave_path.write_bytes(canon.file_bytes(keys.sign_envelope("contributor", contributor_payload("dave", carol, 7777), carol)))
    rep = verify_pr(root, [("A", "distributed/contributors/dave.json")], 7777, tiny_fam, releases, base_contributors=base_reg, pr_author_login="carol")
    assert not rep.ok and any("must be your own GitHub login" in e for e in rep.errors)
    dave_path.unlink()
    # 5. one key under two logins: rejected (bob's key registered as 'bob2', id 1003)
    bob2 = cdir / "bob2.json"
    bob2.write_bytes(canon.file_bytes(keys.sign_envelope("contributor", contributor_payload("bob2", fixture_keys["bob"], 1003), fixture_keys["bob"])))
    rep = verify_pr(root, [("A", "distributed/contributors/bob2.json")], 1003, tiny_fam, releases, base_contributors=base_reg, pr_author_login="bob2")
    assert not rep.ok and any("already registered under 'bob'" in e for e in rep.errors)
    bob2.unlink()


def test_unsigned_or_foreign_verified_records_are_not_trusted(tiny_repo, tiny_fam, fixture_keys):
    from oeis_home.ledger import load_verified

    root = tiny_repo
    contributors = load_contributors(root)
    vdir = root / "distributed" / "verified" / "lehmer-q2"
    payload = {"unit_id": UID, "results": [], "verdicts": [], "positive_claims": [], "filtered_checked": {"ok": True, "count": 1}}
    (vdir / f"{UID}.json").write_bytes(canon.canon({"kind": "verified", "payload": payload, "signature": None}) + b"\n")
    assert load_verified(root, contributors) == {}                                           # unsigned: ignored
    assert load_verified(root, contributors, allow_unsigned=True)[UID]["unsigned"] is True
    (vdir / f"{UID}.json").write_bytes(canon.file_bytes(keys.sign_envelope("verified", payload, fixture_keys["alice"])))
    assert load_verified(root, contributors) == {}                                           # signed by a non-bot key: ignored
    (vdir / f"{UID}.json").write_bytes(canon.file_bytes(keys.sign_envelope("verified", payload, fixture_keys["bot"])))
    assert load_verified(root, contributors)[UID]["unsigned"] is False


def test_force_rerun_uses_versioned_name(tiny_repo, tiny_fam, fixture_keys, monkeypatch, tmp_path):
    root = tiny_repo
    key_path = tmp_path / "bob.key"
    key_path.write_bytes(fixture_keys["bob"].private_bytes_raw())
    monkeypatch.setenv("OEIS_HOME_REPO", str(root))
    assert cli.main(["run", "--unit", UID, "--quiet", "--force", "--key", str(key_path), "--repo", str(root)]) == 0
    versioned = root / "distributed" / "results" / "lehmer-q2" / UID / "bob-2.json"
    assert versioned.exists()
    releases = json.loads((root / "distributed" / "RELEASES.json").read_text())
    assert verify_result_file(versioned, tiny_fam, load_contributors(root), releases, full=False).ok
    versioned.unlink()


def test_checkpoint_is_rejected_when_it_does_not_match_the_candidates(tiny_fam, fixture_keys, tmp_path):
    fp = keys.fingerprint(keys.public_raw(fixture_keys["alice"]))
    full = run_unit(tiny_fam, UID, fp, "alice", progress=None)
    partial = tmp_path / "p.json"
    # stale checkpoint: same unit/base/worker but a different family hash -> discarded, recomputed identically
    partial.write_text(json.dumps({"unit_id": UID, "base": full["base"], "worker": fp, "family_hash": "sha256:" + "0" * 64,
                                   "verdicts": [dict(full["verdicts"][0], n=999)]}))
    resumed = run_unit(tiny_fam, UID, fp, "alice", progress=None, partial_path=partial)
    assert resumed["verdicts"] == full["verdicts"]
    # shifted checkpoint (wrong candidate at position 0) is discarded as well
    partial.write_text(json.dumps({"unit_id": UID, "base": full["base"], "worker": fp, "family_hash": tiny_fam.hash,
                                   "verdicts": full["verdicts"][1:5]}))
    assert run_unit(tiny_fam, UID, fp, "alice", progress=None, partial_path=partial)["verdicts"] == full["verdicts"]


def test_non_integer_digits_is_a_named_error(tiny_repo, tiny_fam, fixture_keys, payloads):
    root = tiny_repo
    releases = json.loads((root / "distributed" / "RELEASES.json").read_text())
    p = copy.deepcopy(payloads["bob"])
    p["verdicts"][0]["digits"] = "5"
    path = _write(root, "bob", p, fixture_keys["bob"])
    rep = verify_result_file(path, tiny_fam, load_contributors(root), releases)
    assert not rep.ok and any("digits must be a positive integer" in e for e in rep.errors)
    path.unlink()


def test_key_history_overlap_is_rejected(tiny_repo, tiny_fam, fixture_keys, make_contributor):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    root = tiny_repo
    releases = json.loads((root / "distributed" / "RELEASES.json").read_text())
    base_reg = load_contributors(root)
    newcomer = Ed25519PrivateKey.generate()
    payload = make_contributor("erin", newcomer, 9001)
    payload["previous_fingerprints"] = [base_reg["alice"]["fingerprint"]]          # claims alice's current key as history
    path = root / "distributed" / "contributors" / "erin.json"
    path.write_bytes(canon.file_bytes(keys.sign_envelope("contributor", payload, newcomer)))
    rep = verify_pr(root, [("A", "distributed/contributors/erin.json")], 9001, tiny_fam, releases, base_contributors=base_reg, pr_author_login="erin")
    assert not rep.ok and any("already registered under 'alice'" in e for e in rep.errors)
    path.unlink()
