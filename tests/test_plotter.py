"""Tests for visualization.plotter."""
from __future__ import annotations

import numpy as np

import config as cfg
from core_math.geometry import build_star, exponent_coordinates
from core_math.mersenne import KNOWN_MERSENNE_EXPONENTS, prime_exponents
from visualization import plotter as pl


def _sample():
    ps = prime_exponents(5, 200)
    points = [exponent_coordinates(p) for p in ps]
    plaus = np.linspace(0.1, 0.9, len(ps))
    ll = {p: (p in KNOWN_MERSENNE_EXPONENTS) for p in ps}
    ll[ps[-1]] = None
    return ps, points, plaus, ll


def test_figure_has_expected_trace_names():
    ps, points, plaus, ll = _sample()
    fig = pl.build_star_figure(build_star(), points, plaus, ll, set(KNOWN_MERSENNE_EXPONENTS), {11: 23})
    names = {tr.name for tr in fig.data}
    expected = {"star_vertices", "star_edges", "golden_triangles", "pentagram_intersections", "golden_spiral",
                "candidates", "known_mersenne_primes"}
    expected |= {f"ring_{k}" for k in cfg.RING_RADII} | {f"golden_ring_{n}" for n in cfg.GOLDEN_RINGS}
    assert expected <= names
    cand = next(tr for tr in fig.data if tr.name == "candidates")
    assert len(cand.x) == len(ps)
    known = next(tr for tr in fig.data if tr.name == "known_mersenne_primes")
    assert len(known.x) == sum(p in KNOWN_MERSENNE_EXPONENTS for p in ps)


def test_write_html_creates_file(tmp_path):
    ps, points, plaus, ll = _sample()
    fig = pl.build_star_figure(build_star("stella_octangula"), points, plaus, ll, set(KNOWN_MERSENNE_EXPONENTS))
    out = pl.write_html(fig, tmp_path / "star.html", include_plotlyjs="cdn")
    assert out.exists() and out.stat().st_size > 10_000
    assert "candidates" in out.read_text(encoding="utf-8")


def test_period20_wheel_png(tmp_path):
    ps, points, plaus, ll = _sample()
    out = pl.plot_period20_wheel_png(points, plaus, ll, set(KNOWN_MERSENNE_EXPONENTS), tmp_path / "wheel.png")
    assert out.exists() and out.stat().st_size > 5_000
