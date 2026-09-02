"""Tests for core_math.mersenne — every assertion is an exact classical fact."""
from __future__ import annotations

import pytest

from core_math import mersenne as m


def _lucas(n: int) -> int:
    a, b = 2, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def test_mersenne_number_small_values():
    assert [m.mersenne_number(p) for p in (2, 3, 5, 7, 11, 13)] == [3, 7, 31, 127, 2047, 8191]
    with pytest.raises(ValueError):
        m.mersenne_number(0)


def test_known_exponents_sorted_prime_and_52():
    ks = m.KNOWN_MERSENNE_EXPONENTS
    assert len(ks) == 52
    assert list(ks) == sorted(ks)
    assert all(m.is_prime_int(p) for p in ks)
    assert ks[-1] == 136279841


def test_lucas_lehmer_matches_known_table_below_1000():
    found = [p for p in m.prime_exponents(2, 1000) if m.lucas_lehmer(p)]
    assert found == [p for p in m.KNOWN_MERSENNE_EXPONENTS if p <= 1000]
    assert len(found) == 14


def test_lucas_lehmer_rejects_composite_exponent():
    with pytest.raises(ValueError):
        m.lucas_lehmer(9)
    with pytest.raises(ValueError):
        m.lucas_lehmer(1)


def test_mod_mersenne_equals_percent():
    for p in (3, 5, 7, 13, 17):
        M = (1 << p) - 1
        for x in list(range(0, 3 * M + 5)) + [M * M - 1, M * M, M * M + 7, -5]:
            assert m.mod_mersenne(x, p) == x % M


def test_ll_s0_4_unreduced_sequence_is_4_14_194_37634():
    assert m.lucas_lehmer_sequence(7, s0=4, reduce=False)[:4] == [4, 14, 194, 37634]


def test_ll_s0_3_unreduced_sequence_equals_lucas_of_powers_of_two():
    seq = m.lucas_lehmer_sequence(7, s0=3, reduce=False)
    assert seq == [3, 7, 47, 2207, 4870847, 23725150497407]
    assert seq == [_lucas(2 ** (k + 1)) for k in range(len(seq))]


def test_ll_s0_3_agrees_with_s0_4_for_p_3_mod_4():
    for p in m.prime_exponents(3, 500):
        if p % 4 == 3:
            assert m.lucas_lehmer(p, s0=3) == m.lucas_lehmer(p, s0=4)


def test_ll_s0_3_raises_for_p_1_mod_4():
    with pytest.raises(ValueError):
        m.lucas_lehmer(5, s0=3)
    with pytest.raises(ValueError):
        m.lucas_lehmer_sequence(13, s0=3)


def test_universal_seeds_agree():
    for p in m.prime_exponents(3, 200):
        results = {m.lucas_lehmer(p, s0=s) for s in m.UNIVERSAL_LL_SEEDS}
        assert len(results) == 1


def test_sophie_germain_factor_divides():
    assert m.sophie_germain_factor(11) and (1 << 11) - 1 == 23 * 89
    assert m.sophie_germain_factor(23) and ((1 << 23) - 1) % 47 == 0
    for p in (83, 131, 179, 191, 239, 251):
        assert m.sophie_germain_factor(p)
        assert ((1 << p) - 1) % (2 * p + 1) == 0
    assert not m.sophie_germain_factor(3)      # 7 = M_3 itself
    assert not m.sophie_germain_factor(5)      # p ≡ 1 (mod 4)
    assert not m.sophie_germain_factor(7)      # 15 is not prime


def test_trial_factor_finds_23_for_p11_and_none_for_p13():
    assert m.trial_factor(11) == 23
    assert m.trial_factor(13) is None
    assert m.trial_factor(23) == 47
    assert m.trial_factor(3) is None           # never returns M_p itself
    q = m.trial_factor(29)
    assert q == 233 and ((1 << 29) - 1) % q == 0


def test_wagstaff_number_primes_below_300():
    expected = {3, 5, 7, 11, 13, 17, 19, 23, 31, 43, 61, 79, 101, 127, 167, 191, 199}
    got = {p for p in m.prime_exponents(3, 300) if m.is_prime_int(m.wagstaff_number(p))}
    assert got == expected
    with pytest.raises(ValueError):
        m.wagstaff_number(4)


def test_wagstaff_probability_in_unit_interval_and_decreasing():
    ps = m.prime_exponents(5, 5000)
    vals = [m.wagstaff_probability(p) for p in ps]
    assert all(0.0 <= v <= 1.0 for v in vals)
    same_class = [v for p, v in zip(ps, vals) if p % 4 == 3]
    assert all(a >= b for a, b in zip(same_class, same_class[1:]))
    assert m.wagstaff_probability(1) == 0.0


def test_is_prime_int_agrees_with_sieve():
    sieve = set(m.sieve_primes(5000))
    assert all(m.is_prime_int(n) == (n in sieve) for n in range(5001))
    assert m.is_prime_int(2 ** 61 - 1) and not m.is_prime_int(2 ** 67 - 1)


def test_iter_mersenne_numbers():
    assert list(m.iter_mersenne_numbers(7)) == [(2, 3), (3, 7), (5, 31), (7, 127)]
