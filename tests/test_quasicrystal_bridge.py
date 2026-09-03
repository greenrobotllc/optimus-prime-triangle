"""Tests for research.quasicrystal_bridge — Landau's theorem and the Fibonacci Bragg module, numerically."""
from __future__ import annotations

import math

import numpy as np
import pytest

import config as cfg
from research import quasicrystal_bridge as qb


@pytest.fixture(scope="module")
def gammas():
    path = cfg.OUTPUT_DIR / "odlyzko_zeros1.txt"
    if path.exists():
        return qb.load_odlyzko_zeros(path, download=False)[:20000]
    return qb.compute_zeros_mpmath(400)


def test_von_mangoldt():
    assert [round(qb.von_mangoldt(n), 6) for n in (1, 2, 3, 4, 6, 8, 9, 12, 25)] == \
           [0.0, round(math.log(2), 6), round(math.log(3), 6), round(math.log(2), 6), 0.0, round(math.log(2), 6), round(math.log(3), 6), 0.0, round(math.log(5), 6)]


def test_landau_spikes_at_log_prime_powers(gammas):
    T = gammas[-1]
    for n in (2, 3, 4, 5, 7):
        u0 = math.log(n)
        window = np.linspace(u0 - 0.05, u0 + 0.05, 201)
        F = qb.zero_diffraction(gammas, window)
        assert abs(window[np.argmin(F)] - u0) < 0.006, n         # the minimum sits at log n
        assert F.min() < 0.55 * qb.landau_prediction(n, T)        # and is roughly the predicted depth
    # no spike where Λ vanishes: F stays noise-level around u = log 6
    window = np.linspace(math.log(6) - 0.01, math.log(6) + 0.01, 41)
    assert qb.zero_diffraction(gammas, window).min() > 0.3 * qb.landau_prediction(2, T)


def test_zeta_peak_table_relative_errors(gammas):
    rows = qb.zeta_peak_table(gammas, n_max=16)
    assert [r.n for r in rows] == [2, 3, 4, 5, 7, 8, 9, 11, 13, 16]
    assert np.median([r.relative_error for r in rows]) < 0.25


def test_fibonacci_chain_positions_lie_in_Z_phi():
    x = qb.fibonacci_chain(60)
    word = qb.fibonacci_word(60)
    assert word.startswith("LSLLSLSL") and "SS" not in word and "LLL" not in word
    for j, pos in enumerate(x):
        nL, nS = word[:j].count("L"), word[:j].count("S")
        assert math.isclose(pos, nL * cfg.PHI + nS)


def test_bragg_peaks_on_the_dual_module():
    x = qb.fibonacci_chain(3000)
    peaks = {(b.m, b.n): b for b in qb.bragg_intensities(x, index_max=8, k_max=40.0)}
    # Fibonacci-indexed peaks (F_k, F_{k+1}) have conjugate |φ̄|^k and are the bright ones
    for mn in ((1, 1), (2, 3), (3, 5), (1, 2)):
        assert peaks[mn].amplitude2 > 0.05, (mn, peaks[mn])
    assert peaks[(2, 3)].amplitude2 > peaks[(1, 1)].amplitude2 > peaks[(1, 0)].amplitude2 > peaks[(-1, 1)].amplitude2   # ordered by |m + nφ̄|
    # off the module the intensity is at the noise level 1/N
    k_off = qb.bragg_position(1, 1) + 0.37
    assert qb.chain_diffraction(x, np.array([k_off]))[0] / len(x) ** 2 < 5e-3
    assert math.isclose(qb.bragg_position(1, 1), 2 * math.pi * (1 + cfg.PHI) / math.sqrt(5))


def test_build_bridge_small(gammas):
    data = qb.build_bridge(gammas[:2000], u_points=300, n_tiles=500, k_points=400)
    assert set(data) >= {"u", "F_normalised", "zeta_peaks", "k", "background", "bragg_peaks"}
    assert len(data["u"]) >= 300 and len(data["k"]) == 400            # the grid gains the exact log n abscissae
    assert all(any(abs(v - math.log(n)) < 1e-5 for v in data["u"]) for n in (2, 3, 5))   # exact abscissae present (grid rounded to 1e-6)


def test_page_generator_embeds_data(tmp_path, gammas):
    from visualization.zeta_page import write_page

    data = qb.build_bridge(gammas[:1500], u_points=200, n_tiles=300, k_points=300)
    out = write_page(data, tmp_path / "zeta.html")
    text = out.read_text(encoding="utf-8")
    assert "<title>Diffraction of the Zeta Zeros</title>" in text and "zeta-chart" in text and "fib-chart" in text
    assert '"zeta_peaks"' in text and "__DATA__" not in text
