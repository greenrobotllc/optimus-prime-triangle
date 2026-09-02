"""Tests for core_math.symbolic_bridge (sympy identities)."""
from __future__ import annotations

import sympy as sp

from core_math import symbolic_bridge as sb
from core_math.psi_sequence import PHI_EXACT, golden_level_exact


def test_psi_poly_homogeneous_degree_floor_n_half():
    for n in range(1, 11):
        P = sb.psi_poly(n)
        assert P.total_degree() == n // 2
        assert sb.verify_homogeneity(n)


def test_explicit_and_closed_form():
    assert all(sb.verify_explicit(n) for n in range(0, 12))
    assert all(sb.verify_closed_form(n) for n in range(1, 10))


def test_normalisation_identity_symbolic():
    assert all(sb.normalisation_identity(n) for n in range(0, 13))
    assert "V_n" in sb.normalisation_proof_sketch()


def test_directional_operator_c4_gives_psi_1_4_n():
    assert all(sb.verify_operator_gives_lucas_lehmer(n) for n in range(1, 11))
    assert sb.directional_operator(8, 4) == 194


def test_directional_operator_c3_gives_lucas_at_powers_of_two():
    for n in (4, 8, 16):
        assert sb.directional_operator(n, 3) == sp.Integer([7, 47, 2207][[4, 8, 16].index(n)])
    assert all(sb.verify_operator_gives_lucas_numbers(n) for n in range(1, 11))


def test_directional_operator_golden_gives_minus_phi():
    assert sb.verify_operator_golden(4) and sb.verify_operator_golden(16)
    assert sb.verify_directional_identity(6, sp.GoldenRatio - 1)


def test_ring_parameters_are_roots_of_psi_b_poly_2_to_6():
    roots = sb.ring_parameter_roots()
    assert roots[2] == [0] and roots[3] == [-1]
    assert [sb.is_zero(r - e) for r, e in zip(roots[4], [-sp.sqrt(2), sp.sqrt(2)])] == [True, True]
    assert [sb.is_zero(r - e) for r, e in zip(roots[5], [-sp.GoldenRatio, sp.GoldenRatio - 1])] == [True, True]
    assert [sb.is_zero(r - e) for r, e in zip(roots[6], [-sp.sqrt(3), 0, sp.sqrt(3)])] == [True, True, True]
    assert sb.psi_b_poly(5).as_expr() == sp.expand(sp.Symbol("b") ** 2 + sp.Symbol("b") - 1)


def test_chebyshev_and_dickson_links():
    assert all(sb.verify_chebyshev(n) for n in range(0, 11))
    assert all(sb.verify_dickson(n) for n in range(0, 11))


def test_golden_period_table_symbolic_matches_exact_ring():
    table = sb.golden_period_table_symbolic()
    for n in range(20):
        assert sb.is_zero(table[n] - golden_level_exact(n).to_sympy())


def test_rotation_form_symbolic():
    assert all(sb.verify_trig_form(n) for n in range(1, 9))


def test_no_universal_golden_seed():
    assert sb.no_universal_golden_seed(300)


def test_is_zero_handles_symbols():
    assert not sb.is_zero(sp.Symbol("a") + 1)
    assert sb.is_zero(sp.GoldenRatio ** 2 - sp.GoldenRatio - 1)


def test_bridge_report_all_true():
    report = sb.bridge_report(8)
    assert report and all(report.values()), report
