import json

import pytest

from oeis_home import families as F


def test_values_match_reference_and_test_vectors(fam):
    tv = fam.test_vectors
    assert [int(F.value("m1", n)) for n in range(len(tv["m1_first"]))] == tv["m1_first"]
    assert [int(F.value("p1", n)) for n in range(len(tv["p1_first"]))] == tv["p1_first"]
    assert [int(F.value("even", 2 * m)) for m in range(len(tv["V14_first"]))] == tv["V14_first"]
    for n in list(range(0, 300)) + [2000, 2001, 4095, 4096, 4097]:
        for v in F.variants_for(n):
            assert int(F.value(v, n)) == F.reference_value(v, n)
    with pytest.raises(ValueError):
        F.value("even", 3)


def test_unit_indices(fam):
    for v, expected in (("m1", {1, 2, 3, 7}), ("p1", {1, 2, 5})):
        assert {n for n in range(400) if F.abs_value(v, n) == 1} == expected == set(fam.units[v])


def test_candidate_closed_form_equals_divisor_rule(fam):
    for v in ("m1", "p1", "even"):
        units = fam.units[v]
        for n in range(16, 3001):
            if v == "even" and n % 2:
                continue
            rule = not any(n % d == 0 and (n // d) % 2 == 1 and d not in units for d in range(1, n))
            assert F.is_candidate(fam, v, n) == rule, (v, n)
    for n in (12, 21, 49, 2446, 4096):
        assert F.is_candidate(fam, "m1", n)
    assert F.is_candidate(fam, "p1", 25) and not F.is_candidate(fam, "p1", 21) and not F.is_candidate(fam, "m1", 27)


def test_filter_witness_is_exact(fam):
    for v in ("m1", "p1"):
        for n in range(16, 1501):
            if F.is_candidate(fam, v, n):
                assert F.filter_witness(fam, v, n) is None
            else:
                d = F.filter_witness(fam, v, n)
                assert d is not None and F.check_filter_witness(v, n, d), (v, n, d)
    assert not F.check_filter_witness("m1", 12, 4)          # |Psi(4)| == |Psi(12)| == 7: not a valid witness


def test_family_hash_ignores_prose_fields(tmp_path):
    raw = json.loads(F.DEFAULT_PATH.read_text())
    h = F.family_hash(raw)
    raw["definition"] = "edited"
    raw["references"] = []
    raw["bands"] = [[0, 10, 5]]
    raw["n_max_open"] = 10
    assert F.family_hash(raw) == h
    raw["filter"]["units"]["m1"] = [1, 2, 3]
    assert F.family_hash(raw) != h
