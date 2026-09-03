from oeis_home import ledger as L
from oeis_home.export import bfile, extension_lines, oeis_ready


def _unit(results, filtered_ok=True, disputed=False, claims=()):
    return {"unit_id": "u", "results": results, "filtered_checked": {"ok": filtered_ok, "count": 1}, "disputed": disputed, "claims": list(claims)}


def test_unit_state_machine():
    assert L.unit_state(_unit([])) == "open"
    assert L.unit_state(_unit([], claims=["alice"])) == "claimed"
    a = {"login": "alice", "status": "valid", "github_id": 1}
    b = {"login": "bob", "status": "valid", "github_id": 2}
    a2 = {"login": "alice2", "status": "valid", "github_id": 1}
    assert L.unit_state(_unit([a], filtered_ok=False)) == "pending"
    assert L.unit_state(_unit([a])) == "verified"
    assert L.unit_state(_unit([a, a2])) == "verified"                 # same GitHub id counts once
    assert L.unit_state(_unit([a, b])) == "double_checked"
    assert L.unit_state(_unit([a, dict(b, role="verifier", github_id=0)])) == "double_checked"
    assert L.unit_state(_unit([dict(b, role="verifier", github_id=0)])) == "verified"          # one verifier result is one result
    assert L.unit_state(_unit([a, {"login": "alice-verifier", "status": "valid", "github_id": 1, "role": "verifier"}])) == "verified"   # same account
    assert L.unit_state(_unit([a, b], disputed=True)) == "disputed"
    assert L.unit_state(_unit([dict(a, status="invalid")])) == "invalid"
    assert L.unit_state(_unit([dict(a, status="withdrawn")])) == "invalid"


def test_next_units_prefers_fresh_then_double(fam):
    units = {"lehmer-q2-00000000-00005000": {"state": "verified", "results": [{"login": "bob", "github_id": 2}]},
             "lehmer-q2-00005000-00010000": {"state": "open", "results": []},
             "lehmer-q2-00010000-00015000": {"state": "verified", "results": [{"login": "alice", "github_id": 1}]}}
    ledger = {"units": units, "contributors": {"alice": {"github_id": 1}}}
    assert L.next_units(ledger, "alice", "any", 3) == ["lehmer-q2-00005000-00010000", "lehmer-q2-00000000-00005000"]
    assert L.next_units(ledger, "alice", "double", 5) == ["lehmer-q2-00000000-00005000"]


def test_bfile_and_extension_lines():
    text = bfile([(1, 4), (2, 5), (3, 6)], ["header"])
    assert text == "# header\n1 4\n2 5\n3 6\n" and text.endswith("\n")
    terms = [{"k": 1, "n": 4, "status": "proven", "discoverer": "alice"}, {"k": 2, "n": 5, "status": "proven", "discoverer": "alice"},
             {"k": 3, "n": 1019, "status": "prp", "discoverer": "bob"}]
    contributors = {"alice": {"oeis_credit_name": "Alice Example", "display_name": "Alice"}, "bob": {"oeis_credit_name": "", "display_name": "Bob"}}
    lines = extension_lines(terms, contributors, "Andy Triboletti")
    assert lines[0].startswith("a(1)-a(2) from _Alice Example_")
    assert any("probable prime" in line for line in lines) and any("OEIS@home volunteer (Bob)" in line for line in lines)


def test_oeis_ready_data_line_proven_only_and_under_260(fam):
    units = {"lehmer-q2-00000000-00005000": {"state": "verified", "n_hi": 5000, "results": [],
             "verdicts": [{"n": 4, "variant": "even", "v": "prime", "method": "small", "digits": 1},
                          {"n": 5, "variant": "m1", "v": "prime", "method": "small", "digits": 1},
                          {"n": 1019, "variant": "m1", "v": "prp", "method": "bpsw", "digits": 154},
                          {"n": 1039, "variant": "m1", "v": "prp", "method": "bpsw", "digits": 157}],
             "positive_claims": []}}
    positive = [{"unit_id": "lehmer-q2-00000000-00005000", "n": 1019, "variant": "m1", "discoverer_login": "alice", "verifier_login": "bob", "maintainer_pari": "isprime", "ci_confirmed": True},
                {"unit_id": "lehmer-q2-00000000-00005000", "n": 1039, "variant": "m1", "discoverer_login": "alice", "verifier_login": "", "maintainer_pari": "none", "ci_confirmed": True}]
    ledger = {"units": units, "verified_through": 1030, "contributors": {}, "positive_claims": positive}
    ready = oeis_ready(ledger, fam, {})
    a3 = ready["sequences"]["A3"]
    assert a3["data"] == "4,5,1019" and len(a3["data"]) <= 260
    assert [t["n"] for t in a3["terms"]] == [4, 5, 1019]
    assert [(t["n"], t["variant"], t["reason"]) for t in a3["pending_terms"]] == [(1039, "m1", "position_undetermined")]
    from oeis_home.export import draft_entries
    draft = draft_entries(ready, "Andy Triboletti", "2026-09-03")
    assert "%C A3 1039 is a term, but its position is not yet determined" in draft
    assert "[EMPTY" in draft.split("%S A4 ")[1].split("\n")[0]                                # no A4 terms -> banner, not a bare line
    assert ready["sequences"]["A1"]["data"].startswith("2,1,1,-1,-7,-5,-11")
