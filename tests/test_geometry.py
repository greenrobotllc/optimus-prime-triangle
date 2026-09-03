"""Tests for core_math.geometry."""
from __future__ import annotations

import math

import numpy as np

import config as cfg
from core_math import geometry as g
from core_math import mersenne as m
from core_math.psi_sequence import lucas


def test_golden_triangle_angles_and_leg_base_ratio():
    tri = g.golden_triangle(base=2.0)
    angles = sorted(g.triangle_angles_deg(tri))
    assert np.allclose(angles, [36.0, 72.0, 72.0])
    leg = np.linalg.norm(tri[1] - tri[0])
    base = np.linalg.norm(tri[2] - tri[1])
    assert math.isclose(leg / base, cfg.PHI, rel_tol=1e-12)
    assert math.isclose(base, 2.0, rel_tol=1e-12)


def test_golden_angle_137_5077():
    assert math.isclose(cfg.GOLDEN_ANGLE_DEG, 137.50776405, abs_tol=1e-7)


def test_ring_theta_values():
    for period, b in cfg.RING_B.items():
        assert math.isclose(g.ring_theta_deg(b), cfg.RING_THETA_DEG[period], abs_tol=1e-9)
    for name, (b, theta, _) in cfg.GOLDEN_RINGS.items():
        assert math.isclose(g.ring_theta_deg(b), theta, abs_tol=1e-9)


def test_period20_node_angles_are_multiples_of_18():
    for n in range(40):
        ang = g.ring_node_angle_deg(20, n)
        assert math.isclose(ang / 18.0, round(ang / 18.0), abs_tol=1e-9)


def test_prime_exponents_land_on_odd_multiples_of_18():
    assert round(g.ring_node_angle_deg(20, 5) / 18.0) == 15          # p = 5 is the exception
    for p in m.prime_exponents(7, 500):
        k = round(g.ring_node_angle_deg(20, p) / 18.0)
        assert k % 2 == 1 and math.gcd(k, 20) == 1


def test_pentagram_inner_radius_is_R_over_phi_squared_and_triangles_are_golden():
    outer, inner = g.pentagram(3.4)
    assert np.allclose(np.linalg.norm(outer[:, :2], axis=1), 3.4)
    assert np.allclose(np.linalg.norm(inner[:, :2], axis=1), 3.4 / cfg.PHI**2)
    tris = g.golden_triangles_in_pentagram(3.4)
    assert tris.shape == (5, 3, 3)
    for tri in tris:
        assert np.allclose(sorted(g.triangle_angles_deg(tri)), [36.0, 72.0, 72.0])


def test_paper_star_matches_the_source():
    star = g.build_star("paper_parameter_plane")
    assert star.vertex_labels == ["A", "B", "C", "F", "G", "H", "I", "J"]
    assert star.vertices[:, 2].tolist() == [0.0] * 8
    assert [tuple(int(v) for v in row[:2]) for row in star.vertices] == [(0, -1), (-2, -5), (1, 4), (-1, 4), (1, -4), (2, 5), (-1, -4), (0, 1)]
    # K_{2,6}: A and J each joined to the six off-axis points, no other edges
    a, j = 0, 7
    assert all(i in (a, j) for i, _ in star.edges) and len(star.edges) == 12
    assert set(k for _, k in star.edges) == {1, 2, 3, 4, 5, 6}
    assert star.triangle is not None and star.triangle.shape == (3, 3)
    assert set(star.neighbours) == {"L1", "L2", "Mix", "P6", "P8", "P12", "P16", "P20", "P24"}
    assert math.isclose(star.neighbours["P20"][0][1], cfg.PHI - 1)
    angles = sorted(g.mersenne_triangle_angles_deg())
    assert angles[2] > 160.0 and angles[0] < 10.0    # nearly degenerate (≈ 5°, 10°, 165°), not 36°–72°–72°
    # decorations sit on the separate plane
    assert all(star.rings[k][0, 2] < 0 for k in star.rings)


def test_star_has_8_vertices_12_edges_all_layouts():
    for layout in cfg.STAR_LAYOUTS:
        star = g.build_star(layout)
        assert star.vertices.shape == (8, 3)
        assert len(star.edges) == 12 and len(set(map(frozenset, star.edges))) == 12
        assert all(0 <= i < 8 and 0 <= j < 8 and i != j for i, j in star.edges)
        assert set(star.rings) == set(cfg.RING_RADII)
        assert set(star.golden_rings) == set(cfg.GOLDEN_RINGS)
        assert star.intersections.shape == (5, 3) and star.golden_triangles.shape == (5, 3, 3)
        assert star.spiral.shape[1] == 3


def test_stella_octangula_edges_are_two_tetrahedra():
    edges = g.star_edges("stella_octangula")
    def parity(k: int) -> int:
        return bin(k).count("1") % 2

    assert all(parity(i) == parity(j) for i, j in edges)


def test_exponent_coordinates_finite_for_largest_known_exponent():
    pt = g.exponent_coordinates(136279841)
    assert all(math.isfinite(v) for v in (pt.x, pt.y, pt.z, pt.theta_golden_deg, pt.r_octave))
    assert pt.theta20_deg == (54 * 136279841) % 360
    assert 0.0 <= pt.r_octave < 1.0


def test_proximity_metrics_in_unit_interval():
    for p in m.prime_exponents(2, 2000) + [136279841]:
        met = g.proximity_metrics(p)
        assert set(met) == {"phi_zone_distance", "fibonacci_zone_distance", "golden_node_angular_distance",
                            "pentagram_intersection_distance", "beatty_distance"}
        assert all(0.0 <= v <= 1.0 for v in met.values()), (p, met)


def test_phi_zone_distance_near_zero_at_lucas_numbers():
    # L_n = φ^n + ψ^n, so frac(log_φ L_n) → 0 geometrically fast (|ψ/φ|^n)
    for n in range(8, 30):
        assert g.proximity_metrics(lucas(n))["phi_zone_distance"] < 0.01
    assert g.proximity_metrics(lucas(5))["phi_zone_distance"] < 0.05


def test_golden_spiral_grows_by_phi_per_quarter_turn():
    pts = g.golden_spiral(turns=1.0, n=401)
    r = np.hypot(pts[:, 0], pts[:, 1])
    assert math.isclose(r[100] / r[0], cfg.PHI, rel_tol=1e-9)
