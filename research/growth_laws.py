"""Growth laws for the exponents of Mersenne primes (goal G1).

Named hypotheses for the ``n``-th Mersenne-prime exponent ``q_n``:

* **Lenstra–Pomerance–Wagstaff**: the number of Mersenne primes with ``p ≤ x`` is about
  ``e^γ·log₂ x``, equivalently successive exponents grow by the factor ``2^{1/e^γ} ≈ 1.4758``.
* **Eberhart's conjecture** (1964): ``q_n ~ (3/2)^n``.
* the **golden-ratio hypothesis** implicit in the project brief: ``q_{n+1}/q_n → φ ≈ 1.618``.

Under the LPW model the gaps ``ln q_{n+1} − ln q_n`` behave like independent exponential
variables with mean ``ln 2 / e^γ``, so the natural statistic is the mean log-gap; the
ranking of hypotheses uses the empirical standard error of that mean and a bootstrap
confidence interval.  With 52 exponents the evidence is limited; the module reports
z-scores rather than declaring anything "proved".
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

import config as cfg
from core_math.mersenne import EULER_GAMMA, KNOWN_MERSENNE_EXPONENTS

HYPOTHESES: dict[str, float] = {
    "Lenstra-Pomerance-Wagstaff 2^(1/e^gamma)": 2.0 ** (1.0 / math.exp(EULER_GAMMA)),
    "Eberhart (3/2)^n": 1.5,
    "golden ratio phi": cfg.PHI,
}


def log_gaps(exponents: tuple[int, ...] | list[int] = KNOWN_MERSENNE_EXPONENTS, start_rank: int = 1) -> np.ndarray:
    q = np.asarray(exponents[start_rank - 1:], dtype=float)
    return np.diff(np.log(q))


def growth_factor(exponents: tuple[int, ...] | list[int] = KNOWN_MERSENNE_EXPONENTS, start_rank: int = 1) -> float:
    """Geometric-mean successive ratio ``exp(mean log-gap)``."""
    return float(math.exp(log_gaps(exponents, start_rank).mean()))


def least_squares_growth_factor(exponents: tuple[int, ...] | list[int] = KNOWN_MERSENNE_EXPONENTS) -> float:
    """``exp(slope)`` of the least-squares line ``ln q_n ~ n``."""
    q = np.asarray(exponents, dtype=float)
    n = np.arange(1, len(q) + 1)
    slope = np.polyfit(n, np.log(q), 1)[0]
    return float(math.exp(slope))


def root_growth_factor(exponents: tuple[int, ...] | list[int] = KNOWN_MERSENNE_EXPONENTS) -> float:
    """``q_N^{1/N}`` for the last known exponent."""
    return float(exponents[-1] ** (1.0 / len(exponents)))


def bootstrap_ci(exponents: tuple[int, ...] | list[int] = KNOWN_MERSENNE_EXPONENTS, n_boot: int = 4000,
                 seed: int = cfg.SEED, level: float = 0.95, start_rank: int = 1) -> tuple[float, float]:
    """Bootstrap CI for the growth factor by resampling the log-gaps."""
    gaps = log_gaps(exponents, start_rank)
    rng = np.random.default_rng(seed)
    means = np.array([rng.choice(gaps, size=len(gaps), replace=True).mean() for _ in range(n_boot)])
    lo, hi = np.quantile(np.exp(means), [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi)


def hypothesis_table(exponents: tuple[int, ...] | list[int] = KNOWN_MERSENNE_EXPONENTS, n_boot: int = 4000,
                     seed: int = cfg.SEED, start_rank: int = 1) -> list[dict[str, object]]:
    """Observed factor, bootstrap CI and z-score for each named hypothesis."""
    gaps = log_gaps(exponents, start_rank)
    mean_gap = float(gaps.mean())
    se = float(gaps.std(ddof=1) / math.sqrt(len(gaps)))
    lo, hi = bootstrap_ci(exponents, n_boot, seed, start_rank=start_rank)
    rows = []
    for name, factor in HYPOTHESES.items():
        z = (math.log(factor) - mean_gap) / se
        rows.append({"hypothesis": name, "factor": factor, "observed": math.exp(mean_gap),
                     "ci95": (lo, hi), "z": z, "inside_ci": lo <= factor <= hi})
    return rows


def lpw_expected_count(x: float) -> float:
    """Expected number of Mersenne primes with exponent ``≤ x`` under LPW: ``e^γ·log₂ x``."""
    return math.exp(EULER_GAMMA) * math.log2(x)


def lpw_expected_vs_observed(exponents: tuple[int, ...] | list[int] = KNOWN_MERSENNE_EXPONENTS) -> list[tuple[int, float, int]]:
    return [(q, lpw_expected_count(q), i + 1) for i, q in enumerate(exponents)]


def format_table(rows: list[dict[str, object]]) -> str:
    lines = [f"{'hypothesis':<44}{'factor':>8}{'observed':>10}{'95% CI':>18}{'z':>7}"]
    for r in rows:
        lo, hi = r["ci95"]  # type: ignore[misc]
        lines.append(f"{r['hypothesis']:<44}{r['factor']:>8.4f}{r['observed']:>10.4f}{'[' + f'{lo:.3f}, {hi:.3f}' + ']':>18}{r['z']:>7.2f}")
    return "\n".join(lines)


def plot_growth_law(path: Path, exponents: tuple[int, ...] | list[int] = KNOWN_MERSENNE_EXPONENTS) -> Path:
    """``log₂ q_n`` against rank with the least-squares line and the hypothesis slopes."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    q = np.asarray(exponents, dtype=float)
    n = np.arange(1, len(q) + 1)
    y = np.log2(q)
    slope, intercept = np.polyfit(n, y, 1)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(n, y, "o", label="known exponents (log₂ q_n)")
    ax.plot(n, slope * n + intercept, "-", label=f"least squares, factor {2**slope:.3f}")
    for name, factor in HYPOTHESES.items():
        ax.plot(n, y[0] + np.log2(factor) * (n - 1), "--", alpha=0.7, label=f"{name}: {factor:.3f}")
    ax.set_xlabel("rank n")
    ax.set_ylabel("log₂ q_n")
    ax.set_title("Growth of Mersenne-prime exponents vs named hypotheses")
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
