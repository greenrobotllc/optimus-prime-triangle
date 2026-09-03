"""Tests for core_math.psi_sequence — exact identities from Ibrahim's papers plus the
normalisation identity and the periodicity classification derived in this repo."""
from __future__ import annotations

import math
from fractions import Fraction

import pytest

from core_math import mersenne as m
from core_math import psi_sequence as ps
from core_math.psi_sequence import PHI_EXACT, SQRT2_EXACT, SQRT3_EXACT, QuadInt

PSI_1_4 = [2, 1, -4, -5, 14, 19, -52, -71, 194, 265, -724, -989, 2702, 3691, -10084, -13775, 37634]


def _symmetric(period: int, half: dict[int, object]) -> tuple:
    """Build a table from ``{residue: value}`` given for 0..period/2 (paper's ±r notation)."""
    return tuple(half[min(r, period - r)] for r in range(period))


def _float_period(seq: list[float], tol: float = 1e-6) -> int | None:
    for P in range(1, len(seq) // 2 + 1):
        if all(abs(seq[i] - seq[i + P]) < tol for i in range(len(seq) - P)):
            return P
    return None


# --------------------------------------------------------------------------- basic values
def test_psi_1_4_first_17_values():
    assert [ps.psi(1, 4, n) for n in range(17)] == PSI_1_4


def test_first_psi_polynomials_match_paper_at_a2_b3():
    # Ψ(a,b,n) for n=0..7 from the paper, evaluated at a=2, b=3
    a, b = 2, 3
    expected = [2, 1, -b, -b - a, -2 * a**2 + b**2, -a**2 + a * b + b**2, 3 * a**2 * b - b**3,
                a**3 + 2 * a**2 * b - a * b**2 - b**3]
    assert [ps.psi(a, b, n) for n in range(8)] == expected


def test_negative_index_convention():
    assert ps.psi(1, 4, -5) == ps.psi(1, 4, 5)


# --------------------------------------------------------------------------- equivalent forms
def test_recurrence_equals_explicit_and_lucas_v():
    for a in range(-4, 5):
        for b in range(-6, 7):
            for n in range(0, 14):
                r = ps.psi(a, b, n)
                assert ps.psi_explicit(a, b, n) == r
                if 2 * a != b:
                    assert ps.psi_via_lucas_v(a, b, n) == r


def test_explicit_form_with_fractions():
    assert ps.psi_explicit(Fraction(1, 2), Fraction(1, 3), 7) == ps.psi(Fraction(1, 2), Fraction(1, 3), 7)


def test_closed_form_eq36_matches():
    for a in (1, 2, -1):
        for b in (0, 1, 3, 4, -5):
            if b == 2 * a:
                continue
            for n in range(0, 12):
                assert math.isclose(ps.psi_closed_form(a, b, n), ps.psi(a, b, n), rel_tol=1e-9, abs_tol=1e-9)


def test_trig_form_for_abs_b_below_2():
    for b in (-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, ps._RINGS["phi"][3] - 1, 1 - ps._RINGS["phi"][3]):
        for n in range(0, 30):
            assert math.isclose(ps.psi_trig(b, n), ps.psi(1.0, b, n), abs_tol=1e-9)


def test_doubling_identity():
    for a in range(-3, 4):
        for b in range(-4, 5):
            for n in range(0, 10):
                assert ps.psi_double(a, b, ps.psi(a, b, n), n) == ps.psi(a, b, 2 * n)


def test_product_identity_theorem22():
    for a in range(-2, 3):
        for b in range(-3, 4):
            for n in range(0, 9):
                for k in range(0, n + 1):
                    lhs = (2 * a - b) ** (ps.delta(n) * ps.delta(k)) * ps.psi(a, b, n) * ps.psi(a, b, k)
                    rhs = ps.psi(a, b, n + k) + a ** min(n, k) * ps.psi(a, b, n - k)
                    assert lhs == rhs


def test_psi_mod_matches_direct_mod():
    for a in range(-2, 3):
        for b in range(-3, 5):
            for n in range(0, 41):
                for mod in (7, 97, 10007):
                    assert ps.psi_mod(a, b, n, mod) == ps.psi(a, b, n) % mod


def test_psi_pow2_mod_matches():
    for a, b in ((1, 4), (2, 3), (-2, -5)):
        for k in range(0, 7):
            assert ps.psi_pow2_mod(a, b, k, 10007) == ps.psi(a, b, 2 ** k) % 10007


# --------------------------------------------------------------------------- Lucas–Lehmer link
def test_psi_1_4_pow2_equals_lucas_lehmer_terms():
    seq = m.lucas_lehmer_sequence(13, s0=4, reduce=False)   # s_0 .. s_11
    for k in range(2, 7):
        assert ps.psi(1, 4, 2 ** k) == seq[k - 1]


def test_theorem26_equals_lucas_lehmer():
    for p in m.prime_exponents(3, 61):
        assert ps.theorem26_is_prime(p) == m.lucas_lehmer(p)


def test_theorem27_mod4_pattern():
    for p in (5, 7, 13):
        assert [ps.theorem27_residue(p, mu) for mu in range(1, 9)] == [0, -2, 0, 2, 0, -2, 0, 2]


def test_theorem30_neighbours_not_divisible_when_prime():
    for p in (5, 7, 13, 17):
        assert not ps.theorem30_neighbour_divides(p)


# --------------------------------------------------------------------------- sequence links
def test_lucas_numbers_psi_m1_m3():
    assert all(ps.psi(-1, -3, n) == ps.lucas(n) for n in range(40))


def test_fibonacci_lucas_alternation_psi_1_m3():
    assert all(ps.psi(1, -3, n) == (ps.fibonacci(n) if n % 2 else ps.lucas(n)) for n in range(40))


def test_mersenne_and_wagstaff_family():
    for n in range(40):
        assert ps.psi(-2, -5, n) == 2 ** n + (-1) ** n
        assert ps.psi(2, -5, n) == (2 ** n + 1) // 3 ** (n % 2)
    for p in (3, 5, 7, 11, 13):
        assert ps.psi(-2, -5, p) == m.mersenne_number(p)
        assert ps.psi(2, -5, p) == m.wagstaff_number(p)


def test_psi_1_3_is_signed_lucas_and_lucas_at_powers_of_two():
    for n in range(40):
        assert ps.psi(1, 3, n) == (-1) ** (n // 2) * ps.lucas(n)
    for lg in (2, 3, 4, 5):
        assert ps.psi(1, 3, 2 ** lg) == ps.lucas(2 ** lg)


def test_chebyshev_link():
    for x in (1, 2, 3):
        T = [1, x]
        for _ in range(12):
            T.append(2 * x * T[-1] - T[-2])
        for n in range(12):
            val = Fraction(x ** ps.delta(n), 2 ** ps.delta(n + 1)) * ps.psi(1, 2 - 4 * x * x, n)
            assert val == T[n]


def test_dickson_link():
    for x in (1, 2, 3):
        for alpha in (-2, 1, 3):
            D = [2, x]
            for _ in range(12):
                D.append(x * D[-1] - alpha * D[-2])
            for n in range(12):
                assert x ** ps.delta(n) * ps.psi(alpha, 2 * alpha - x * x, n) == D[n]


# --------------------------------------------------------------------------- periodic rings
def test_periodic_tables_match_paper():
    r2, r3, phi = SQRT2_EXACT, SQRT3_EXACT, PHI_EXACT
    assert ps.PERIODIC_TABLES[6] == (2, 1, -1, -2, -1, 1)
    assert ps.PERIODIC_TABLES[8] == (2, 1, 0, -1, -2, -1, 0, 1)
    assert ps.PERIODIC_TABLES[12] == (2, 1, 1, 0, -1, -1, -2, -1, -1, 0, 1, 1)
    assert ps.PERIODIC_TABLES[16] == _symmetric(16, {0: 2, 1: 1, 2: -r2, 3: -1 - r2, 4: 0, 5: 1 + r2, 6: r2, 7: -1, 8: -2})
    assert ps.PERIODIC_TABLES[24] == _symmetric(24, {0: 2, 1: 1, 2: -r3, 3: -1 - r3, 4: 1, 5: 2 + r3, 6: 0,
                                                     7: -2 - r3, 8: -1, 9: 1 + r3, 10: r3, 11: -1, 12: -2})
    assert ps.PERIODIC_TABLES[20] == _symmetric(20, {0: 2, 1: 1, 2: 1 - phi, 3: -phi, 4: -phi, 5: 0, 6: phi,
                                                     7: phi, 8: phi - 1, 9: -1, 10: -2})


def test_tables_are_genuinely_periodic():
    one = {6: 1, 8: 1, 12: 1, 16: QuadInt(1, 0, "sqrt2"), 20: QuadInt(1, 0, "phi"), 24: QuadInt(1, 0, "sqrt3")}
    b = {6: 1, 8: 0, 12: -1, 16: SQRT2_EXACT, 20: PHI_EXACT - 1, 24: SQRT3_EXACT}
    for period, table in ps.PERIODIC_TABLES.items():
        seq = [ps.psi(one[period], b[period], n) for n in range(3 * period + 1)]
        assert ps.minimal_period(seq) == period
        assert all(seq[n] == table[n % period] for n in range(len(seq)))


def test_eight_levels_and_golden_level_helpers():
    assert [ps.eight_level(n) for n in range(9)] == [2, 1, 0, -1, -2, -1, 0, 1, 2]
    assert ps.golden_level_exact(3) == -PHI_EXACT
    assert math.isclose(ps.golden_level(6), (1 + math.sqrt(5)) / 2)
    assert math.isclose(ps.psi_periodic(16, 5), 1 + math.sqrt(2))


def test_golden_rings_periods_and_angles_exact():
    expected = {"phi": (72.0, 10), "1-phi": (36.0, 10), "-phi": (18.0, 20), "phi-1": (54.0, 20)}
    one = QuadInt(1, 0, "phi")
    for name, (b, theta, period, table) in ps.GOLDEN_TABLES.items():
        assert (theta, period) == expected[name]
        seq = [ps.psi(one, b, n) for n in range(3 * period + 1)]
        assert ps.minimal_period(seq) == period
        assert all(seq[n] == table[n % period] for n in range(len(seq)))
        assert math.isclose(math.degrees(ps.rotation_angle_rad(float(b))), theta, abs_tol=1e-9)


def test_periodicity_rule_m_or_2m():
    """Ψ(1, −2cos2θ, n) with θ = 2πk/m has period m (m even) or 2m (m odd)."""
    for mm in range(3, 31):
        for k in range(1, mm):
            if math.gcd(k, mm) != 1:
                continue
            theta = 2 * math.pi * k / mm
            b = -2 * math.cos(2 * theta)
            if abs(b - 2) < 1e-12:      # degenerate b = 2a
                continue
            predicted = mm if mm % 2 == 0 else 2 * mm
            seq = [ps.psi(1.0, b, n) for n in range(3 * predicted + 2)]
            assert _float_period(seq) == predicted, (mm, k, b)


def test_golden_level_of_pow2_is_minus_phi_for_all_odd_primes():
    for p in m.prime_exponents(5, 2000):
        assert pow(2, p - 1, 20) in (4, 16)
        assert ps.golden_level_exact(pow(2, p - 1, 20)) == -PHI_EXACT


def test_pisano_period_20_mod_5():
    seq = [ps.fibonacci(n) % 5 for n in range(100)]
    assert ps.minimal_period(seq) == 20


def test_fibonacci_mod_fast_doubling():
    for mod in (7, 1000, 10007):
        for n in range(0, 200):
            assert ps.fibonacci_mod(n, mod) == ps.fibonacci(n) % mod


# --------------------------------------------------------------------------- QuadInt
def test_quadint_arithmetic():
    phi = PHI_EXACT
    assert phi * phi == phi + 1
    assert SQRT2_EXACT * SQRT2_EXACT == 2
    assert SQRT3_EXACT ** 2 == 3
    assert phi * phi.conjugate() == -1 and phi.norm() == -1
    assert (1 + SQRT2_EXACT) * (1 - SQRT2_EXACT) == -1
    assert math.isclose(float(phi), (1 + math.sqrt(5)) / 2)
    assert repr(phi - 1) == "-1+φ" and repr(-phi) == "-φ" and repr(QuadInt(2, 0)) == "2"
    assert phi ** 5 == 5 * phi + 3
    with pytest.raises(TypeError):
        _ = phi + SQRT2_EXACT
    assert phi.to_sympy() is not None


def test_psi_is_lehmer_companion_sequence():
    for a in range(-4, 5):
        for b in range(-6, 7):
            if 2 * a == b:
                continue
            for n in range(0, 16):
                assert ps.psi_via_lehmer(a, b, n) == ps.psi(a, b, n)
    # Lehmer numbers Ū_n(√5, −1) with Q = −1, R = 5: U_n = F_n·(√5)^{...}: the odd terms are Lucas U at (P,Q)=(1,-1)?
    # sanity: R=1, Q=-1 is the Fibonacci/Lucas pair itself
    assert [ps.lehmer_bar(1, -1, n) for n in range(10)] == [ps.fibonacci(n) for n in range(10)]
    assert [ps.lehmer_companion_bar(1, -1, n) for n in range(10)] == [ps.lucas(n) for n in range(10)]
    # R = 12, Q = 1: Lucas–Lehmer numbers 4, 14, 194 at n = 2, 4, 8 — but as companion of √12: V_2 = R − 2Q = 10?  use R=4,Q=1
    assert ps.lehmer_companion_bar(4, 1, 2) == 2 and ps.lehmer_companion_bar(16, 1, 2) == 14


def test_fibonacci_mod_iterative_handles_huge_indices():
    M = (1 << 127) - 1
    assert ps.fibonacci_mod(1 << 127, M) == 0            # α(M_127) = 2^127
    assert ps.fibonacci_mod(1 << 126, M) != 0
    assert ps.lucas_number_mod(1 << 126, M) == 0
    assert all(ps.lucas_number_mod(n, 1009) == ps.lucas(n) % 1009 for n in range(60))
