import pytest

from oeis_home import units as U
from oeis_home.families import is_candidate


def test_band_grid_and_ids():
    assert U.unit_bounds(0) == (0, 5000) and U.unit_bounds(20000) == (20000, 21000)
    assert U.unit_bounds(60000) == (60000, 60400) and U.unit_bounds(120000) == (120000, 120200)
    assert U.unit_bounds(199800) == (199800, 200000)
    for bad in (2500, 200000, -5, 20500):
        with pytest.raises(ValueError):
            U.unit_bounds(bad)
    uid = U.unit_id(20000)
    assert uid == "lehmer-q2-00020000-00021000" and U.parse_unit_id(uid) == (20000, 21000)
    with pytest.raises(ValueError):
        U.parse_unit_id("lehmer-q2-00020000-00025000")
    assert len(U.all_units(200000)) == 4 + 40 + 150 + 400


def test_candidates_are_sorted_and_filtered(tiny_fam):
    c = U.candidates(tiny_fam, "lehmer-q2-00000000-00000200")
    assert c == sorted(c) and c[0] == (0, "even") and (200, "even") not in c
    assert all(is_candidate(tiny_fam, v, n) for n, v in c)
    assert (21, "m1") in c and (21, "p1") not in c and (25, "p1") in c


def test_worker_base():
    from oeis_home.compute import small_prime_decision

    b = U.worker_base("k1:" + "ab" * 32, "lehmer-q2-00000000-00005000")
    assert 7 <= b <= 100003 and small_prime_decision(b) == "prime"
    assert b == U.worker_base("k1:" + "ab" * 32, "lehmer-q2-00000000-00005000")
    assert b != U.worker_base("k1:" + "cd" * 32, "lehmer-q2-00000000-00005000")
