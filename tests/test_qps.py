"""Tests for core_math.qps — Theorems 25, 11 and 9 of arXiv:2502.06796."""
from __future__ import annotations

import pytest

from core_math import psi_sequence as ps
from core_math import qps


def test_theorem25_ratio_equals_psi():
    for zeta in range(-2, 3):
        for xi in range(-4, 5):
            for n in range(1, 12):
                assert qps.psi_via_qps(zeta, xi, n) == ps.psi(zeta, xi, n)


def test_a_and_b_are_omega_special_cases():
    p = 11
    for r in range(0, 4):
        for k in range(0, 4):
            assert qps.a_sequence_value(r, k, p) == qps.omega(r, k, -2, -5, p)
            assert qps.b_sequence_value(r, k, 5) == qps.omega(r, k, 1, 4, 16)
    # hand-checked first step of A: A_0(1) = (p-1)·1 + 4p·1
    assert qps.a_sequence_value(0, 1, p) == (p - 1) + 4 * p


def test_theorem11_mersenne_numbers():
    for p in (3, 5, 7, 11, 13, 17, 19, 23, 29, 31):
        assert qps.mersenne_via_qps(p) == 2 ** p - 1


def test_b_ratio_equals_psi_1_4():
    for p in (5, 7):
        assert qps.b_ratio(p) == ps.psi(1, 4, 2 ** (p - 1))


def test_theorem9_primality_p5_p7():
    assert qps.qps_primality(5) is True
    assert qps.qps_primality(7) is True


@pytest.mark.slow
def test_theorem9_p11_composite():
    assert qps.qps_primality(11) is False


def test_guards():
    with pytest.raises(ValueError):
        qps.b_ratio(17)
    with pytest.raises(ValueError):
        qps.psi_via_qps(1, 1, 0)
    assert qps.falling_denominator(10, 0) == 1 and qps.falling_denominator(10, 3) == 9 * 8 * 7


# --------------------------------------------------------------------------- identities found in this repository
import random  # noqa: E402


def test_closed_form_matches_recurrence_everywhere():
    rng = random.Random(3)
    checked = 0
    for n in range(1, 22):
        K = n // 2
        for _ in range(3):
            z, x = rng.randint(-9, 9), rng.randint(-9, 9)
            for r in range(0, K + 3):
                for k in range(0, K + 1):
                    assert qps.omega_closed_form(r, k, z, x, n) == qps.omega(r, k, z, x, n)
                    checked += 1
    assert checked > 3000


def test_closed_form_recovers_paper_special_points():
    for n in range(2, 16):
        K = n // 2
        for r in range(0, K + 1):
            for k in range(0, K - r + 1):
                # (0, −1): falling factorial (paper Thm 42)
                assert qps.omega(r, k, 0, -1, n) == qps.falling(n - r - 1, k)
                # (1, 2): only j = k survives (paper Thm 41)
                assert qps.omega(r, k, 1, 2, n) == (-2) ** k * qps.double_falling(n - 2 * r - (n - 1) % 2, k)


def test_hypergeometric_form():
    rng = random.Random(5)
    for n in range(2, 18):
        K = n // 2
        for _ in range(3):
            z, x = rng.randint(-7, 7), rng.randint(-7, 7)
            if 2 * z == x:
                continue
            for r in range(0, K + 1):
                for k in range(0, min(K, n - r - 1) + 1):
                    assert qps.omega_hypergeometric(r, k, z, x, n) == qps.omega(r, k, z, x, n)


def test_delta_column_explicit_form_and_parity_law():
    rng = random.Random(7)
    for n in range(2, 26):
        rs = n % 2
        for _ in range(3):
            z, x = rng.randint(-7, 7), rng.randint(-7, 7)
            for k in range(0, n // 2 + 1):
                val = qps.omega_column_delta_explicit(k, z, x, n)
                assert val.denominator == 1 and int(val) == qps.omega(rs, k, z, x, n)
                assert qps.omega(rs, k, z, -x, n) == (-1) ** k * qps.omega(rs, k, z, x, n)
    # the parity law is special to the column r = δ(n)
    assert qps.omega(0, 1, 1, 1, 7) != -qps.omega(0, 1, 1, -1, 7)


def test_gegenbauer_column():
    for n in (6, 8, 9, 12, 13):
        K = n // 2
        for k in range(1, K):
            assert qps.omega_gegenbauer(k, 2, 3, n) == qps.omega(n % 2, k, 2, 3, n)


def test_shift_identity_odd_n_only():
    for n in range(3, 22, 2):
        assert qps.omega_shift_holds(n, 2, -3) and qps.omega_shift_holds(n, -1, 5)
    assert qps.omega(1, 1, 1, 1, 8) != qps.omega(0, 1, 1, 1, 7)


def test_star_even_symmetry_lemma_holds_for_all_multiples_of_4():
    holds = [n for n in range(1, 41) if qps.star_even_symmetry_holds(n)]
    assert holds == [1] + list(range(4, 41, 4))
