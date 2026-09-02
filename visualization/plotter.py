"""Interactive Plotly map of the Mersenne Star, and a static period-20 wheel.

Only ``plotly.graph_objects`` is used (no ``plotly.express``, no kaleido).  Trace names are
stable so that tests and the README can refer to them:

``star_vertices``, ``star_edges``, ``ring_<period>``, ``golden_ring_<name>``,
``golden_triangles``, ``pentagram_intersections``, ``golden_spiral``, ``candidates``,
``known_mersenne_primes``.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import numpy as np
import plotly.graph_objects as go

import config as cfg
from core_math.geometry import ExponentPoint, StarGeometry

GOLD = "#f5c518"
_HOVER = ("p = %{customdata[0]}<br>plausibility = %{customdata[3]:.3f}<br>Lucas–Lehmer: %{customdata[4]}"
          "<br>Eight-Levels value Ψ(1,0,p) = %{customdata[1]}<br>golden level Ψ(1,φ−1,p) = %{customdata[2]:.3f}"
          "<br>θ₂₀ = %{customdata[5]}°<br>trial factor: %{customdata[6]}<extra></extra>")


def _segments(pairs: Iterable[tuple[np.ndarray, np.ndarray]]) -> tuple[list, list, list]:
    xs: list = []
    ys: list = []
    zs: list = []
    for p0, p1 in pairs:
        xs += [p0[0], p1[0], None]
        ys += [p0[1], p1[1], None]
        zs += [p0[2], p1[2], None]
    return xs, ys, zs


def _closed_polygon(pts: np.ndarray) -> tuple[list, list, list]:
    closed = np.vstack([pts, pts[:1]])
    return closed[:, 0].tolist(), closed[:, 1].tolist(), closed[:, 2].tolist()


def build_star_figure(star: StarGeometry, points: list[ExponentPoint], plausibility: np.ndarray,
                      ll_result: dict[int, bool | None], known: set[int], trial_factors: dict[int, int | None] | None = None,
                      title: str | None = None) -> go.Figure:
    """Assemble the 3-D figure.  ``plausibility[i]`` belongs to ``points[i]``."""
    trial_factors = trial_factors or {}
    fig = go.Figure()

    # the star (interpretation — see core_math.geometry)
    V = star.vertices
    fig.add_trace(go.Scatter3d(
        name="star_vertices", x=V[:, 0], y=V[:, 1], z=V[:, 2], mode="markers+text",
        text=[f"L={int(l)}" for l in star.vertex_levels], textposition="top center",
        marker=dict(size=7, color="#ff7f0e", symbol="circle"),
        hovertemplate="vertex %{text}<extra>Eight Levels</extra>",
    ))
    xs, ys, zs = _segments((V[i], V[j]) for i, j in star.edges)
    fig.add_trace(go.Scatter3d(name="star_edges", x=xs, y=ys, z=zs, mode="lines", line=dict(color="#ff7f0e", width=4), hoverinfo="skip"))

    # satellite rings
    for period, nodes in sorted(star.rings.items()):
        x, y, z = _closed_polygon(nodes)
        fig.add_trace(go.Scatter3d(name=f"ring_{period}", x=x, y=y, z=z, mode="lines+markers",
                                   marker=dict(size=3), line=dict(width=2), opacity=0.8,
                                   hovertemplate=f"period-{period} ring, θ = {cfg.RING_THETA_DEG[period]}°<extra></extra>"))
    for name, nodes in star.golden_rings.items():
        x, y, z = _closed_polygon(nodes)
        b, theta, period = cfg.GOLDEN_RINGS[name]
        fig.add_trace(go.Scatter3d(name=f"golden_ring_{name}", x=x, y=y, z=z, mode="lines+markers",
                                   marker=dict(size=2, color=GOLD), line=dict(width=1, color=GOLD, dash="dot"), opacity=0.6,
                                   hovertemplate=f"golden ring b = {name}, θ = {theta}°, period {period}<extra></extra>"))

    # golden triangles, intersections and spiral
    if star.golden_triangles is not None:
        xs, ys, zs = [], [], []
        for tri in star.golden_triangles:
            x, y, z = _closed_polygon(tri)
            xs += x + [None]
            ys += y + [None]
            zs += z + [None]
        fig.add_trace(go.Scatter3d(name="golden_triangles", x=xs, y=ys, z=zs, mode="lines",
                                   line=dict(color=GOLD, width=5), hovertemplate="golden triangle 36°–72°–72°<extra></extra>"))
    if star.intersections is not None:
        I = star.intersections
        fig.add_trace(go.Scatter3d(name="pentagram_intersections", x=I[:, 0], y=I[:, 1], z=I[:, 2], mode="markers",
                                   marker=dict(size=6, color=GOLD, symbol="diamond"),
                                   hovertemplate="golden-triangle intersection (radius R/φ²)<extra></extra>"))
    if star.spiral is not None:
        S = star.spiral
        fig.add_trace(go.Scatter3d(name="golden_spiral", x=S[:, 0], y=S[:, 1], z=S[:, 2], mode="lines",
                                   line=dict(color=GOLD, width=1), opacity=0.5, hoverinfo="skip"))

    # candidates
    if points:
        P = np.array([[pt.x, pt.y, pt.z] for pt in points])
        custom = [[pt.p, pt.level8, pt.level20, float(plausibility[i]),
                   {True: "prime", False: "composite", None: "not tested"}[ll_result.get(pt.p)],
                   int(pt.theta20_deg), trial_factors.get(pt.p) or "none (k ≤ %d)" % cfg.TRIAL_FACTOR_K_MAX]
                  for i, pt in enumerate(points)]
        fig.add_trace(go.Scatter3d(
            name="candidates", x=P[:, 0], y=P[:, 1], z=P[:, 2], mode="markers",
            marker=dict(size=[3 + 1.2 * math.log2(pt.p) / 4 for pt in points], color=plausibility, colorscale="Viridis",
                        cmin=0.0, cmax=1.0, colorbar=dict(title="plausibility", x=1.02), opacity=0.85),
            customdata=custom, hovertemplate=_HOVER,
        ))
        idx = [i for i, pt in enumerate(points) if pt.p in known]
        if idx:
            fig.add_trace(go.Scatter3d(
                name="known_mersenne_primes", x=P[idx, 0], y=P[idx, 1], z=P[idx, 2], mode="markers+text",
                text=[str(points[i].p) for i in idx], textposition="top center", textfont=dict(color=GOLD, size=10),
                marker=dict(size=9, color=GOLD, symbol="diamond", line=dict(color="white", width=1)),
                customdata=[custom[i] for i in idx], hovertemplate=_HOVER,
            ))

    fig.update_layout(
        template="plotly_dark",
        title=title or (f"Mersenne Star (interpretation, layout '{star.layout}') — Ψ rotation rings, golden triangles, "
                        "candidate exponents coloured by siever plausibility"),
        scene=dict(aspectmode="data", xaxis_title="x", yaxis_title="y", zaxis_title="z ∝ log₂ p / ring height"),
        legend=dict(itemsizing="constant"),
        margin=dict(l=0, r=0, t=60, b=0),
    )
    return fig


def write_html(fig: go.Figure, path: Path, include_plotlyjs: bool | str = cfg.INCLUDE_PLOTLYJS) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(path), include_plotlyjs=include_plotlyjs, full_html=True)
    return path


def plot_period20_wheel_png(points: list[ExponentPoint], plausibility: np.ndarray, ll_result: dict[int, bool | None],
                            known: set[int], path: Path) -> Path:
    """Polar scatter: angle = 54°·p (period-20 node), radius = 1 + frac(log_φ p)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, projection="polar")
    for k in range(20):
        ax.plot([math.radians(18 * k)] * 2, [0, 2.05], color="#888", lw=0.4, alpha=0.6)
    th = [math.radians(pt.theta20_deg) for pt in points]
    r = [1.0 + pt.r_octave for pt in points]
    sc = ax.scatter(th, r, c=plausibility, cmap="viridis", vmin=0, vmax=1, s=14, alpha=0.85)
    kn = [i for i, pt in enumerate(points) if pt.p in known]
    if kn:
        ax.scatter([th[i] for i in kn], [r[i] for i in kn], marker="*", s=140, c=GOLD, edgecolors="k", zorder=5,
                   label="known Mersenne prime exponents")
        for i in kn:
            ax.annotate(str(points[i].p), (th[i], r[i]), fontsize=7, xytext=(3, 3), textcoords="offset points")
    ax.set_rlim(0, 2.1)
    ax.set_title("Period-20 golden ring: angle 54°·p, radius 1 + frac(log_φ p)\n(coordinates, not a primality signal)", fontsize=10)
    fig.colorbar(sc, ax=ax, shrink=0.6, label="siever plausibility")
    if kn:
        ax.legend(loc="lower left", fontsize=8)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return path
