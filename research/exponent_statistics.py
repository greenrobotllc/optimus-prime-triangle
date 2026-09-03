"""Statistical tests of the geometric hypotheses on the 52 known Mersenne-prime exponents.

The brief asserts that Mersenne-prime exponents cluster on golden-ratio "harmonic nodes".
Two families of hypotheses can be tested against the data we actually have:

* **Residue hypotheses** — the exponents ``p > 3`` are not equidistributed among the units
  modulo ``k`` for ``k ∈ {4, 8, 12, 20, 24}`` (the ring periods).  Statistic: chi-square of
  the residue counts against uniformity on the units.
* **φ-zone hypotheses** — the exponents lie unusually close to powers of φ (Lucas numbers),
  to Fibonacci numbers, or have ``p·φ`` unusually close to an integer (Beatty distance).
  Statistic: mean distance.

Null model.  Because the exponents span 3 to 1.4·10⁸, a plain uniform null is wrong; the
null used here keeps the *sizes*: each known exponent ``q_i`` is replaced by a random prime
drawn from ``[q_i / 1.5, 1.5·q_i]``, and the statistic is recomputed.  Monte-Carlo
p-values are the fraction of replications at least as extreme as the observation.

For the mod-4 split, Wagstaff's heuristic itself predicts fewer exponents ``p ≡ 3 (mod 4)``
(they are more often killed by the Sophie-Germain factor ``2p + 1``); the exact binomial
test is reported under both the uniform null and the Wagstaff-weighted null.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Callable

import numpy as np

import config as cfg
from core_math.geometry import proximity_metrics
from core_math.mersenne import KNOWN_MERSENNE_EXPONENTS, is_prime_int

RESIDUE_MODULI: tuple[int, ...] = (4, 8, 12, 20, 24)


def units_mod(k: int) -> list[int]:
    return [r for r in range(1, k) if math.gcd(r, k) == 1]


def residue_counts(exponents, k: int) -> dict[int, int]:
    c = Counter(p % k for p in exponents if p > 3)
    return {r: c.get(r, 0) for r in units_mod(k)}


def chi_square_uniform(counts: dict[int, int]) -> float:
    n = sum(counts.values())
    e = n / len(counts)
    return float(sum((c - e) ** 2 / e for c in counts.values()))


def random_prime_near(q: int, rng: np.random.Generator, spread: float = 1.5) -> int:
    """A random prime in ``[q/spread, q·spread]`` (rejection sampling on odd integers)."""
    lo, hi = max(5, int(q / spread)), int(q * spread)
    while True:
        x = int(rng.integers(lo, hi + 1)) | 1
        if is_prime_int(x):
            return x


def monte_carlo(statistic: Callable[[list[int]], float], exponents=KNOWN_MERSENNE_EXPONENTS, n_rep: int = 2000,
                seed: int = cfg.SEED, two_sided: bool = False) -> dict[str, float]:
    """Monte-Carlo p-value of ``statistic`` under the size-matched random-prime null."""
    rng = np.random.default_rng(seed)
    base = [p for p in exponents if p > 3]
    observed = statistic(base)
    null = np.array([statistic([random_prime_near(q, rng) for q in base]) for _ in range(n_rep)])
    if two_sided:
        centre = float(np.median(null))
        p_value = float((np.count_nonzero(np.abs(null - centre) >= abs(observed - centre)) + 1) / (n_rep + 1))
    else:
        p_value = float((np.count_nonzero(null >= observed) + 1) / (n_rep + 1))
    return {"observed": float(observed), "null_mean": float(null.mean()), "null_sd": float(null.std(ddof=1)),
            "p_value": p_value, "n_rep": n_rep}


def residue_test(k: int, exponents=KNOWN_MERSENNE_EXPONENTS, n_rep: int = 2000, seed: int = cfg.SEED) -> dict[str, object]:
    res = monte_carlo(lambda ps: chi_square_uniform(residue_counts(ps, k)), exponents, n_rep, seed)
    res["k"] = k
    res["counts"] = residue_counts(exponents, k)
    return res


def phi_zone_test(metric: str = "phi_zone_distance", exponents=KNOWN_MERSENNE_EXPONENTS, n_rep: int = 2000,
                  seed: int = cfg.SEED) -> dict[str, object]:
    """Mean proximity metric of the exponents vs the size-matched null (two-sided)."""
    def stat(ps: list[int]) -> float:
        return float(np.mean([proximity_metrics(p)[metric] for p in ps]))
    res = monte_carlo(stat, exponents, n_rep, seed, two_sided=True)
    res["metric"] = metric
    return res


def mod4_binomial_test(exponents=KNOWN_MERSENNE_EXPONENTS) -> dict[str, float]:
    """Exact two-sided binomial tests of the count of ``p ≡ 3 (mod 4)`` among ``p > 3``."""
    from scipy.stats import binomtest

    ps = [p for p in exponents if p > 3]
    n3 = sum(p % 4 == 3 for p in ps)
    # Wagstaff-weighted expectation: relative weight ln(2p)/ln(6p) for p ≡ 3 vs p ≡ 1 (mod 4)
    w3 = np.mean([math.log(2 * p) for p in ps])
    w1 = np.mean([math.log(6 * p) for p in ps])
    q_w = w3 / (w3 + w1)
    return {
        "n": len(ps), "n_3mod4": n3,
        "p_uniform": float(binomtest(n3, len(ps), 0.5).pvalue),
        "wagstaff_expected_fraction": float(q_w),
        "p_wagstaff": float(binomtest(n3, len(ps), q_w).pvalue),
    }


def run_all(n_rep: int = 2000, seed: int = cfg.SEED) -> dict[str, object]:
    return {
        "residues": {k: residue_test(k, n_rep=n_rep, seed=seed) for k in RESIDUE_MODULI},
        "phi_zone": {m: phi_zone_test(m, n_rep=n_rep, seed=seed) for m in ("phi_zone_distance", "fibonacci_zone_distance", "beatty_distance", "golden_node_angular_distance")},
        "mod4": mod4_binomial_test(),
    }


def format_report(res: dict[str, object]) -> str:
    lines = ["| test | observed | null mean ± sd | p-value |", "|---|---|---|---|"]
    for k, r in res["residues"].items():  # type: ignore[union-attr]
        lines.append(f"| residues mod {k}: χ² vs uniform on units | {r['observed']:.2f} | {r['null_mean']:.2f} ± {r['null_sd']:.2f} | {r['p_value']:.3f} |")
    for m, r in res["phi_zone"].items():  # type: ignore[union-attr]
        lines.append(f"| mean {m} | {r['observed']:.3f} | {r['null_mean']:.3f} ± {r['null_sd']:.3f} | {r['p_value']:.3f} (two-sided) |")
    b = res["mod4"]  # type: ignore[index]
    lines.append(f"| count p ≡ 3 (mod 4): {b['n_3mod4']} of {b['n']} | binomial vs ½: p = {b['p_uniform']:.3f} | Wagstaff-weighted expectation {b['wagstaff_expected_fraction']:.3f} | p = {b['p_wagstaff']:.3f} |")
    return "\n".join(lines)
