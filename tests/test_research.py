"""Tests for the research package (goals G1–G4, G7)."""
from __future__ import annotations

import math

import pytest

from core_math import mersenne as m
from core_math.psi_sequence import PHI_EXACT, fibonacci, lucas
from research import conjectures as cj
from research import growth_laws as gl
from research import known_sequences as ks
from research import periodicity as pr


# --------------------------------------------------------------------------- G1 growth laws
def test_growth_factor_of_known_exponents():
    assert 1.40 <= gl.growth_factor() <= 1.46
    assert 1.42 <= gl.least_squares_growth_factor() <= 1.46
    assert 1.42 <= gl.root_growth_factor() <= 1.45


def test_hypothesis_table_orders_phi_last():
    rows = gl.hypothesis_table(n_boot=500)
    z = {r["hypothesis"]: abs(r["z"]) for r in rows}
    assert z["golden ratio phi"] > z["Eberhart (3/2)^n"] > z["Lenstra-Pomerance-Wagstaff 2^(1/e^gamma)"]
    inside = {r["hypothesis"]: r["inside_ci"] for r in rows}
    assert inside["Lenstra-Pomerance-Wagstaff 2^(1/e^gamma)"] and not inside["golden ratio phi"]
    assert "phi" in gl.format_table(rows)


def test_lpw_expected_count_order_of_magnitude():
    assert 35 < gl.lpw_expected_count(136279841) < 65
    assert gl.lpw_expected_vs_observed()[-1][2] == 52


def test_plot_growth_law(tmp_path):
    out = gl.plot_growth_law(tmp_path / "growth.png")
    assert out.exists() and out.stat().st_size > 1000


# --------------------------------------------------------------------------- G2 NMC
def test_nmc_condition1_examples():
    assert all(cj.nmc_condition1(p) for p in (3, 5, 7, 13, 17, 19, 31, 61, 127))
    assert not cj.nmc_condition1(11) and not cj.nmc_condition1(23)


def test_nmc_dashboard_below_300():
    d = cj.nmc_dashboard(300)
    assert d["all_three"] == [3, 5, 7, 13, 17, 19, 31, 61, 127]
    assert d["counterexamples"] == []
    assert d["wagstaff_primes"] == [3, 5, 7, 11, 13, 17, 19, 23, 31, 43, 61, 79, 101, 127, 167, 191, 199]
    assert d["mersenne_primes"] == [p for p in m.KNOWN_MERSENNE_EXPONENTS if 3 <= p <= 300]


# --------------------------------------------------------------------------- G3 Wieferich / squarefree
def test_wieferich_primes_below_1e5():
    assert cj.wieferich_search(100_000) == [1093, 3511]


def test_no_square_factor_of_small_mersenne_numbers():
    res = cj.mersenne_square_factor_check(100, 50_000)
    assert res["hits"] == [] and res["checked"] > 50


# --------------------------------------------------------------------------- G4 Wall–Sun–Sun
def test_no_wall_sun_sun_prime_below_2e4():
    assert cj.wall_sun_sun_search(20_000) == []


def test_fibonacci_entry_point_of_mersenne_primes():
    res = cj.fibonacci_entry_point_check([5, 7, 13, 17, 19, 31])
    assert all(res.values())


# --------------------------------------------------------------------------- G7 periodicity
def test_periodicity_predictions_match_all_reduced_rotations_up_to_30():
    rows = pr.prediction_table(30)
    assert rows and all(r["verified"] for r in rows), [r for r in rows if not r["verified"]]


def test_golden_and_paper_rings_verified_exactly():
    g = {r["name"]: r for r in pr.golden_rings()}
    assert {n: r["predicted_period"] for n, r in g.items()} == {"phi": 10, "1-phi": 10, "-phi": 20, "phi-1": 20}
    assert all(r["verified_exact"] for r in g.values())
    assert [r["in_source_paper"] for r in pr.golden_rings()] == [False, False, False, True]
    assert [r["predicted_period"] for r in pr.paper_rings()] == [6, 8, 12, 16, 20, 24]
    assert all(r["verified_exact"] for r in pr.paper_rings())


def test_classify_ring_regimes():
    assert pr.classify_ring(4.0)["regime"] == "hyperbolic" and pr.predicted_period(4.0) is None
    assert pr.classify_ring(2.0)["regime"] == "degenerate"
    assert pr.predicted_period(-2.0) == 2
    assert pr.predicted_period(0.0) == 8 and math.isclose(pr.rotation_angle_deg(0.0), 45.0)
    assert pr.predicted_period(0.3) is None          # irrational turn
    assert "iff" in pr.THEOREM_STATEMENT


# --------------------------------------------------------------------------- known sequences
def test_known_sequence_matches():
    assert "fibonacci" in ks.match([fibonacci(n) for n in range(20)])
    assert "lucas" in ks.match([lucas(n) for n in range(20)])
    assert "-(lucas)" in ks.match([-lucas(n) for n in range(20)])
    assert "2^n+(-1)^n" in ks.match([2**n + (-1) ** n for n in range(20)])
    assert ks.match([1, 2, 3]) == []


# --------------------------------------------------------------------------- G8 discovery / ledger / lean / report
from research import discovery as dc          # noqa: E402
from research import lean_export as le        # noqa: E402
from research.report import research_report   # noqa: E402
from core_math.psi_sequence import QuadInt    # noqa: E402


def test_enumerate_points_excludes_degenerate_and_zero_ring_coefficients():
    pts = dc.enumerate_points()
    assert all(not (pt.ring == "Z" and 2 * pt.a == pt.b) for pt in pts)
    assert all(pt.b.v != 0 for pt in pts if pt.ring != "Z")
    assert {pt.ring for pt in pts} == {"Z", "Z[sqrt2]", "Z[sqrt3]", "Z[phi]"}


def test_classify_point_periodic_known_and_unclassified():
    c = dc.classify_point(dc.Point("Z", 1, 0))
    assert c["kind"] == "periodic" and c["period"] == 8 and c["prediction_agrees"]
    c = dc.classify_point(dc.Point("Z", -1, -3))
    assert c["kind"] == "known_sequence" and "lucas" in c["matches"]
    c = dc.classify_point(dc.Point("Z[phi]", QuadInt(1, 0, "phi"), PHI_EXACT - 1))
    assert c["kind"] == "periodic" and c["period"] == 20 and c["prediction_agrees"]
    c = dc.classify_point(dc.Point("Z", 3, -4))
    assert c["kind"] in ("known_sequence", "unclassified")


def test_census_golden_ring_periodic_points_are_exactly_the_four_golden_values():
    cen = dc.census()
    golden = {c["point"] for c in cen if c["kind"] == "periodic" and c["ring"] == "Z[phi]"}
    expected = {f"Ψ(1, {b}, n) over Z[phi]" for b in (PHI_EXACT, 1 - PHI_EXACT, -PHI_EXACT, PHI_EXACT - 1)}
    assert golden == expected
    assert all(c["prediction_agrees"] for c in cen if c["kind"] == "periodic"), [c for c in cen if c["kind"] == "periodic" and not c["prediction_agrees"]]


def test_prime_density_scan_finds_the_classical_points():
    rows = dc.prime_density_scan(top=500)
    by_point = {r["point"]: r for r in rows}
    mers = by_point["Ψ(-2, -5, n) over Z"]
    assert mers["primes"] >= 8                                      # odd n: Mersenne primes; even n: 2^n + 1 (Fermat primes 5, 17, 257, 65537)
    assert all(m.is_prime_int(n) for n in mers["indices"] if n % 2 == 1)
    assert {n for n in mers["indices"] if n % 2 == 0} == {2, 4, 8, 16}
    assert mers["ratio"] > 1.0 and mers["expected_by_size"] > 0
    assert rows == sorted(rows, key=lambda r: -r["ratio"])
    assert by_point["Ψ(-1, -3, n) over Z"]["primes"] >= 8          # Lucas primes


def test_ledger_round_trip_and_label(tmp_path):
    path = tmp_path / "ledger.md"
    ledger, cen, density = dc.run_discovery(path, {"rotation_form": True, "normalisation_identity": True})
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Triboletti" in text and "novelty" in text and "```json" in text
    reloaded = dc.Ledger.load(path)
    assert [e.slug for e in reloaded.entries] == [e.slug for e in ledger.entries]
    assert {e.slug for e in ledger.entries} >= {"periodicity-classification", "golden-rings", "normalisation-identity", "ll-index-constancy",
                                                "golden-seed", "lehmer-identification", "qps-is-lucas-lehmer", "mersenne-fibonacci-rank"}
    assert all(isinstance(e.references, list) for e in reloaded.entries)
    assert not any(e.kind == "anomaly" for e in ledger.entries)
    assert {e.novelty for e in ledger.entries} <= {"unchecked", "classical"}


def test_lean_export_produces_skeletons():
    cands = dc.seed_candidates()
    text = le.export(cands)
    assert text.startswith("import Mathlib")
    assert text.count("theorem ") == len(cands) and "sorry" in text
    assert "LucasLehmer" in text and "goldenRatio" in text and "Nat.fib" in text and "LehmerVbar" in text
    assert "triboletti_fable_golden_rings" in text


def test_research_report_small(tmp_path):
    md, results = research_report(nmc_p_max=60, wieferich_limit=5000, wss_limit=2000, ledger_path=tmp_path / "l.md",
                                  growth_png=tmp_path / "g.png", stats_n_rep=20, rank_p_max_factor=17, rank_p_max_check=127)
    assert results["rank_of_apparition"] and "G4b" in md and "G1b" in md
    for tag in ("G1", "G2", "G3", "G4", "G7", "G8"):
        assert f"## {tag}" in md
    assert results["nmc"]["counterexamples"] == [] and results["wieferich"] == [1093, 3511]
    assert (tmp_path / "g.png").exists() and (tmp_path / "l.md").exists()


# --------------------------------------------------------------------------- rank of apparition theorem
def test_fibonacci_rank_of_apparition_small_primes():
    # classical values: α(2)=3 excluded; α(3)=4, α(7)=8, α(11)=10, α(13)=7, α(31)=30, α(89)=11
    assert [cj.fibonacci_rank_of_apparition(q) for q in (3, 7, 11, 13, 31, 89)] == [4, 8, 10, 7, 30, 11]


def test_mersenne_fibonacci_rank_theorem_p_3_mod_4():
    for p in (7, 19, 31, 107, 127, 607, 1279, 2203):
        assert cj.mersenne_fibonacci_rank_is_2p(p)
    with pytest.raises(ValueError):
        cj.mersenne_fibonacci_rank_is_2p(13)


def test_mersenne_fibonacci_rank_table():
    rows = {r["p"]: r for r in cj.mersenne_fibonacci_rank_table(p_max_factor=89, p_max_check=607)}
    assert all(rows[p]["alpha_is_2p"] for p in (7, 19, 31, 107, 127, 607))
    assert rows[5]["alpha_is_maximal"] and rows[13]["alpha_is_maximal"] and rows[17]["alpha_is_maximal"]
    assert rows[61]["cofactor"] == 9 and rows[89]["cofactor"] == 3


# --------------------------------------------------------------------------- exponent statistics
from research import exponent_statistics as es   # noqa: E402


def test_residue_counts_and_chi_square():
    counts = es.residue_counts(m.KNOWN_MERSENNE_EXPONENTS, 4)
    assert counts == {1: 32, 3: 18}
    c20 = es.residue_counts(m.KNOWN_MERSENNE_EXPONENTS, 20)
    assert 5 not in c20 and sum(c20.values()) == 49          # p = 5 is not a unit mod 20
    assert es.chi_square_uniform({1: 25, 3: 25}) == 0.0


def test_monte_carlo_tests_run_and_give_valid_pvalues():
    r = es.residue_test(20, n_rep=30, seed=1)
    assert 0.0 <= r["p_value"] <= 1.0 and r["k"] == 20
    z = es.phi_zone_test("phi_zone_distance", n_rep=30, seed=1)
    assert 0.0 <= z["p_value"] <= 1.0 and 0.0 <= z["observed"] <= 1.0
    b = es.mod4_binomial_test()
    assert b["n_3mod4"] == 18 and 0.0 <= b["p_uniform"] <= 1.0 and 0.4 < b["wagstaff_expected_fraction"] < 0.5
    rep = es.format_report(es.run_all(n_rep=20, seed=2))
    assert "residues mod 20" in rep and "Wagstaff" in rep
