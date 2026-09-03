"""Golden-triangle geometry, the Ψ rotation rings, and the Mersenne Star coordinate map.

Rigorous part
-------------
Each periodic Ψ ring ``Ψ(1, b, n)`` with ``b = −2·cos 2θ`` is literally a rotation by ``θ``
(see :mod:`core_math.psi_sequence`), so the natural coordinate of an exponent ``p`` on a
ring of period ``k`` is the angle ``θ_k · p`` on a regular ``k``-gon.  The period-20 golden
ring rotates by ``54° = 3·18°``; its nodes are the vertices of a regular 20-gon, whose
vertex angles ``36°, 72°, 108°`` are exactly the pentagram / golden-triangle angles.  Prime
exponents other than 2 and 5 land on the eight *odd* multiples of 18° that are coprime to
20 (``3p mod 20`` is a unit when ``gcd(p, 20) = 1``).

The Mersenne Star of the source paper (now read in full)
------------------------------------------------------
Ibrahim, "The emergence of the Mersenne Star" (HAL hal-05035758v2, DOI
10.1080/25765299.2025.2569155) defines everything in the ``(ζ, ξ)`` parameter plane of the
Quanta Prime Sequence ``Ω_r(k | ζ, ξ | n)``:

* the **Mersenne Triangle** is the three points ``A = (0, −1)``, ``B = (−2, −5)``, ``C = (1, 4)``
  (Theorem 7.1: ``M_p`` prime iff ``Ω_0(n/2|0,−1|n)·Ω_0(⌊p/2⌋|−2,−5|p)`` divides
  ``Ω_0(n/2|1,4|n)·Ω_0(⌊p/2⌋|0,−1|p)``, ``n = 2^{p−1}`` — which is the Lucas–Lehmer test);
* the **Mersenne Star** is the eight points ``A(0,−1), B(−2,−5), C(1,4), F(−1,4), G(1,−4),
  H(2,5), I(−1,−4), J(0,1)`` (Tables 1 and 3); its twelve edges, drawn in Figure 1 but never
  listed in the text, join each of the six off-axis points to both axis points ``A`` and ``J``
  (the complete bipartite graph ``K_{2,6}``); the "32 relationships" are Theorem 7.6, the
  sign-symmetric variants of Theorem 7.1, all equivalent to Lucas–Lehmer;
* the **neighbours** (Table 1) are the parameter points ``(1,3)``, ``(−1,−3)`` (Lucas),
  ``(1,−3)`` (Fibonacci/Lucas mix) and the periodic points ``(1,1), (1,0), (1,−1), (1,√2),
  (1,φ−1), (1,√3)`` with periods 6, 8, 12, 16, 20, 24.

The Mersenne Triangle is not a golden triangle (its angles are ≈ 2.7°, 3.1°, 174.2°), and the
paper contains no pentagram or golden triangle.  Layout ``"paper_parameter_plane"`` reproduces
the paper exactly (points in the plane ``z = 0``); the two earlier layouts ``"octagon_crown"``
and ``"stella_octangula"`` are kept as labelled interpretations from before the text was
available.  The golden decorations requested by the project brief (rotation rings, pentagram,
golden triangles, spiral) are drawn on a separate plane ``z = DECORATION_Z`` and are *not*
part of the paper's construction.

Candidate exponents are placed on the period-20 ring at angle ``54°·p`` (their own period-20
node), radius ``R₂₀·(1 + frac(log_φ p))`` (numbers close to a power of φ — Lucas numbers — sit
on the inner edge: the "φ-convergence zone") and height ``∝ log₂ p``.  All proximity metrics
are dimensionless numbers in ``[0, 1]``; they are *coordinates*, not evidence of primality.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

import config as cfg
from core_math.psi_sequence import EIGHT_LEVELS, rotation_angle_rad

PHI = cfg.PHI
_LOG_PHI = math.log(PHI)


# --------------------------------------------------------------------------- dataclasses
@dataclass(frozen=True)
class ExponentPoint:
    """3-D placement of a candidate exponent plus its ring coordinates."""

    p: int
    x: float
    y: float
    z: float
    theta20_deg: float
    theta8_deg: float
    theta_golden_deg: float
    level8: int
    level20: float
    r_octave: float


#: The paper's Mersenne Star: label -> (ζ, ξ) in the QPS parameter plane (Tables 1 and 3).
PAPER_STAR_VERTICES: dict[str, tuple[int, int]] = {
    "A": (0, -1), "B": (-2, -5), "C": (1, 4), "F": (-1, 4), "G": (1, -4), "H": (2, 5), "I": (-1, -4), "J": (0, 1),
}
PAPER_STAR_ORDER: tuple[str, ...] = tuple(PAPER_STAR_VERTICES)
#: Twelve edges decoded from Figure 1: both axis points A, J joined to every off-axis point (K_{2,6}).
PAPER_STAR_EDGES: tuple[tuple[str, str], ...] = tuple((axis, other) for axis in ("A", "J") for other in ("B", "H", "C", "F", "G", "I"))
#: The Mersenne Triangle (Theorem 7.1, Figure 4).
PAPER_TRIANGLE: dict[str, tuple[int, int]] = {"A": (0, -1), "B": (-2, -5), "C": (1, 4)}
#: Neighbour points of Table 1: label -> ((ζ, ξ), description).
PAPER_NEIGHBOURS: dict[str, tuple[tuple[float, float], str]] = {
    "L1": ((1, 3), "Lucas numbers"),
    "L2": ((-1, -3), "Lucas numbers"),
    "Mix": ((1, -3), "Fibonacci / Lucas mix"),
    "P6": ((1, 1), "period 6"),
    "P8": ((1, 0), "period 8 (Eight Levels)"),
    "P12": ((1, -1), "period 12"),
    "P16": ((1, math.sqrt(2)), "period 16"),
    "P20": ((1, PHI - 1), "period 20 (golden ratio)"),
    "P24": ((1, math.sqrt(3)), "period 24"),
}


@dataclass
class StarGeometry:
    layout: str
    vertices: np.ndarray                      # (8, 3)
    edges: list[tuple[int, int]]              # 12 pairs
    vertex_levels: np.ndarray                 # (8,)
    vertex_labels: list[str] = field(default_factory=list)
    triangle: np.ndarray | None = None                                 # (3, 3) the Mersenne Triangle (paper layout)
    neighbours: dict[str, tuple[np.ndarray, str]] = field(default_factory=dict)   # label -> (point, description)
    rings: dict[int, np.ndarray] = field(default_factory=dict)         # period -> (k, 3)
    golden_rings: dict[str, np.ndarray] = field(default_factory=dict)  # name -> (k, 3)
    pentagram_outer: np.ndarray | None = None                          # (5, 3)
    intersections: np.ndarray | None = None                            # (5, 3) inner pentagon
    golden_triangles: np.ndarray | None = None                         # (5, 3, 3)
    spiral: np.ndarray | None = None                                   # (N, 3)


# --------------------------------------------------------------------------- golden triangle
def golden_triangle(base: float = 1.0, apex: tuple[float, float] = (0.0, 0.0), rotation_deg: float = 90.0) -> np.ndarray:
    """Vertices of a 36°–72°–72° golden triangle (apex first), leg = φ·base.

    The legs leave the apex at ``rotation ± 18°``; since ``2·sin 18° = 1/φ`` the base has
    the requested length.
    """
    leg = PHI * base
    ax, ay = apex
    pts = [(ax, ay)]
    for sign in (+1, -1):
        ang = math.radians(rotation_deg + sign * 18.0)
        pts.append((ax + leg * math.cos(ang), ay + leg * math.sin(ang)))
    return np.array(pts, dtype=float)


def triangle_angles_deg(tri: np.ndarray) -> tuple[float, float, float]:
    """Interior angles (degrees) of a triangle given as three 2-D or 3-D points."""
    P = np.asarray(tri, dtype=float)
    out = []
    for i in range(3):
        u = P[(i + 1) % 3] - P[i]
        v = P[(i + 2) % 3] - P[i]
        c = float(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v)))
        out.append(math.degrees(math.acos(max(-1.0, min(1.0, c)))))
    return tuple(out)  # type: ignore[return-value]


def pentagram(R: float, z: float = 0.0, rotation_deg: float = 90.0) -> tuple[np.ndarray, np.ndarray]:
    """Outer vertices (radius ``R``) and inner vertices (radius ``R/φ²``) of a pentagram."""
    outer = np.array([[R * math.cos(math.radians(rotation_deg + 72 * k)),
                       R * math.sin(math.radians(rotation_deg + 72 * k)), z] for k in range(5)])
    r_in = R / PHI**2
    inner = np.array([[r_in * math.cos(math.radians(rotation_deg + 36 + 72 * k)),
                       r_in * math.sin(math.radians(rotation_deg + 36 + 72 * k)), z] for k in range(5)])
    return outer, inner


def golden_triangles_in_pentagram(R: float, z: float = 0.0, rotation_deg: float = 90.0) -> np.ndarray:
    """The five star-point triangles (apex = outer vertex, base = two adjacent inner vertices).

    Each is a golden triangle: leg/base = φ.
    """
    outer, inner = pentagram(R, z, rotation_deg)
    tris = []
    for k in range(5):
        tris.append(np.array([outer[k], inner[k], inner[(k - 1) % 5]]))
    return np.array(tris)


def golden_spiral(turns: float = 2.0, n: int = 400, scale: float = 0.25, z: float = 0.0) -> np.ndarray:
    """Points on the golden spiral ``r = scale·φ^{2θ/π}`` (quarter-turn growth by φ)."""
    t = np.linspace(0.0, 2 * math.pi * turns, n)
    r = scale * PHI ** (2 * t / math.pi)
    return np.column_stack([r * np.cos(t), r * np.sin(t), np.full_like(t, z)])


# --------------------------------------------------------------------------- rings
def ring_theta_deg(b: float) -> float:
    """Rotation angle ``θ`` (degrees) of the ring ``Ψ(1, b, ·)``, ``b = −2cos 2θ``."""
    return math.degrees(rotation_angle_rad(b))


def ring_node_angle_deg(period: int, n: int) -> float:
    """Angle of index ``n`` on the ring of the given period: ``θ_period · n (mod 360)``."""
    theta = cfg.RING_THETA_DEG[period]
    return (theta * n) % 360.0


def ring_nodes(period: int, radius: float, z: float = 0.0, phase_deg: float = 0.0) -> np.ndarray:
    """``period`` equally spaced nodes on a circle (the regular ``k``-gon of a ring)."""
    ang = np.radians(phase_deg + 360.0 * np.arange(period) / period)
    return np.column_stack([radius * np.cos(ang), radius * np.sin(ang), np.full(period, z)])


# --------------------------------------------------------------------------- the star
def star_vertices(layout: str = cfg.STAR_LAYOUT, height_scale: float = 0.5) -> np.ndarray:
    if layout == "paper_parameter_plane":
        return np.array([[*PAPER_STAR_VERTICES[k], 0.0] for k in PAPER_STAR_ORDER], dtype=float)
    if layout == "octagon_crown":
        ang = np.radians(45.0 * np.arange(8))
        return np.column_stack([np.cos(ang), np.sin(ang), height_scale * np.array(EIGHT_LEVELS, dtype=float)])
    if layout == "stella_octangula":
        return np.array([[(k >> 0 & 1) * 2 - 1, (k >> 1 & 1) * 2 - 1, (k >> 2 & 1) * 2 - 1] for k in range(8)], dtype=float)
    raise ValueError(f"unknown star layout {layout!r}")


def star_edges(layout: str = cfg.STAR_LAYOUT) -> list[tuple[int, int]]:
    if layout == "paper_parameter_plane":
        idx = {k: i for i, k in enumerate(PAPER_STAR_ORDER)}
        return [(idx[a], idx[b]) for a, b in PAPER_STAR_EDGES]
    if layout == "octagon_crown":
        rim = [(k, (k + 1) % 8) for k in range(8)]
        diameters = [(k, k + 4) for k in range(4)]
        return rim + diameters
    if layout == "stella_octangula":
        even = [k for k in range(8) if bin(k).count("1") % 2 == 0]
        odd = [k for k in range(8) if bin(k).count("1") % 2 == 1]
        edges = []
        for tet in (even, odd):
            for i in range(4):
                for j in range(i + 1, 4):
                    edges.append((tet[i], tet[j]))
        return edges
    raise ValueError(f"unknown star layout {layout!r}")


def build_star(layout: str = cfg.STAR_LAYOUT) -> StarGeometry:
    """Assemble the star, its satellite rings, the pentagram and the golden triangles."""
    paper = layout == "paper_parameter_plane"
    star = StarGeometry(
        layout=layout,
        vertices=star_vertices(layout),
        edges=star_edges(layout),
        vertex_levels=np.zeros(8) if paper else np.array(EIGHT_LEVELS, dtype=float),
        vertex_labels=list(PAPER_STAR_ORDER) if paper else [f"L={lvl}" for lvl in EIGHT_LEVELS],
    )
    if paper:
        star.triangle = np.array([[*PAPER_TRIANGLE[k], 0.0] for k in ("A", "B", "C")], dtype=float)
        star.neighbours = {name: (np.array([pt[0], pt[1], 0.0]), desc) for name, (pt, desc) in PAPER_NEIGHBOURS.items()}
    z0 = cfg.DECORATION_Z if paper else 0.0
    for period, radius in cfg.RING_RADII.items():
        star.rings[period] = ring_nodes(period, radius, z0 + cfg.RING_Z[period])
    for i, (name, (_, _, period)) in enumerate(cfg.GOLDEN_RINGS.items()):
        star.golden_rings[name] = ring_nodes(period, cfg.GOLDEN_RING_RADIUS * (1 + 0.06 * i),
                                             z0 + cfg.GOLDEN_RING_Z + 0.1 * (i + 1))
    outer, inner = pentagram(cfg.GOLDEN_RING_RADIUS, z0 + cfg.GOLDEN_RING_Z)
    star.pentagram_outer = outer
    star.intersections = inner
    star.golden_triangles = golden_triangles_in_pentagram(cfg.GOLDEN_RING_RADIUS, z0 + cfg.GOLDEN_RING_Z)
    star.spiral = golden_spiral(cfg.SPIRAL_TURNS, z=z0 + cfg.GOLDEN_RING_Z)
    return star


def mersenne_triangle_angles_deg() -> tuple[float, float, float]:
    """Interior angles of the paper's Mersenne Triangle A(0,−1), B(−2,−5), C(1,4) — not golden."""
    return triangle_angles_deg(np.array([[*PAPER_TRIANGLE[k]] for k in ("A", "B", "C")], dtype=float))


# --------------------------------------------------------------------------- exponent placement
def frac_log_phi(v: float) -> float:
    """Fractional part of ``log_φ v``."""
    return (math.log(v) / _LOG_PHI) % 1.0


def exponent_coordinates(p: int, radius: float = cfg.GOLDEN_RING_RADIUS) -> ExponentPoint:
    """Place exponent ``p`` on the period-20 golden ring (angle ``54°·p``)."""
    theta20 = (54 * p) % 360
    theta8 = (45 * p) % 360
    theta_golden = (p * cfg.GOLDEN_ANGLE_DEG) % 360.0
    r_oct = frac_log_phi(p)
    r = radius * (1.0 + r_oct)
    ang = math.radians(theta20)
    from core_math.psi_sequence import golden_level  # local import avoids a cycle at import time

    return ExponentPoint(
        p=p,
        x=r * math.cos(ang),
        y=r * math.sin(ang),
        z=cfg.CANDIDATE_Z_SCALE * math.log2(p),
        theta20_deg=float(theta20),
        theta8_deg=float(theta8),
        theta_golden_deg=theta_golden,
        level8=EIGHT_LEVELS[p % 8],
        level20=golden_level(p),
        r_octave=r_oct,
    )


def angular_distance_deg(a_deg: float, b_deg: float) -> float:
    d = abs((a_deg - b_deg) % 360.0)
    return min(d, 360.0 - d)


def proximity_metrics(p: int, radius: float = cfg.GOLDEN_RING_RADIUS) -> dict[str, float]:
    """Dimensionless distances in ``[0, 1]`` from ``p`` to the golden-ratio structures.

    * ``phi_zone_distance``: ``2·min(f, 1−f)`` with ``f = frac(log_φ p)``; 0 at powers of φ
      (Lucas numbers ``L_n ≈ φ^n``).
    * ``fibonacci_zone_distance``: same with ``log_φ(p·√5)``; 0 near Fibonacci numbers.
    * ``golden_node_angular_distance``: angle of the golden-angle spiral position ``p·137.5°``
      to the nearest period-20 node (multiple of 18°), divided by 9°.
    * ``pentagram_intersection_distance``: planar distance to the nearest inner pentagon
      vertex, normalised by ``2.4·R``.
    * ``beatty_distance``: ``1 − 2·|frac(p·φ) − ½|``; 0 when ``p·φ`` is nearly an integer.
    """
    f1 = frac_log_phi(p)
    f2 = frac_log_phi(p * math.sqrt(5.0))
    golden_angle = (p * cfg.GOLDEN_ANGLE_DEG) % 360.0
    nearest = round(golden_angle / 18.0) * 18.0
    ang_dist = angular_distance_deg(golden_angle, nearest) / 9.0
    pt = exponent_coordinates(p, radius)
    _, inner = pentagram(radius, 0.0)
    d = float(np.min(np.hypot(inner[:, 0] - pt.x, inner[:, 1] - pt.y)))
    frac_phi = (p * PHI) % 1.0
    return {
        "phi_zone_distance": 2.0 * min(f1, 1.0 - f1),
        "fibonacci_zone_distance": 2.0 * min(f2, 1.0 - f2),
        "golden_node_angular_distance": min(1.0, ang_dist),
        "pentagram_intersection_distance": min(1.0, d / (2.4 * radius)),
        "beatty_distance": 1.0 - 2.0 * abs(frac_phi - 0.5),
    }
