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
