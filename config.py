"""Default parameters for the Geometric Prime Explorer.

Everything here is a plain module constant so that ``main.py`` can override values
from the command line and tests can monkeypatch them.

Mathematical notes
------------------
* ``RING_B`` lists the parameter ``b`` of the Ψ-sequence ``Ψ(1, b, n)`` (Ibrahim,
  arXiv:2404.05772, Def. 4.1) for which the sequence is periodic in ``n``.  With
  ``b = -2·cos(2θ)`` one has ``Ψ(1, b, n) = 2·cos(nθ)`` for even ``n``, so each ring is a
  rotation by ``θ`` (``RING_THETA_DEG``).  The period is ``m`` when ``θ = 2π·k/m`` with
  ``m`` even and ``2m`` when ``m`` is odd.
* ``GOLDEN_RINGS`` are the four golden-ratio parameters.  Only ``b = φ − 1`` (period 20)
  appears in the source paper; the other three are predictions of the classification
  above, verified exactly in ``Z[φ]`` by the test-suite.
* ``EIGHT_LEVELS`` is ``Ψ(1, 0, n)`` for ``n mod 8`` — the "Eight Levels" of the theorem's
  name — and is the vertex height used for the Mersenne Star interpretation.
"""
from __future__ import annotations

import math
from pathlib import Path

# --------------------------------------------------------------------------- constants
PHI: float = (1.0 + math.sqrt(5.0)) / 2.0          # golden ratio φ
PSI_CONJ: float = 1.0 - PHI                         # ψ = −1/φ, the conjugate root
GOLDEN_ANGLE_DEG: float = 360.0 / PHI ** 2          # ≈ 137.5077°
SQRT2: float = math.sqrt(2.0)
SQRT3: float = math.sqrt(3.0)
EULER_GAMMA: float = 0.5772156649015329

# --------------------------------------------------------------------------- candidates
P_MIN: int = 5                  # p = 2, 3 are trivial Mersenne primes and are reported separately
P_MAX_DEFAULT: int = 2500       # 367 prime exponents, 17 known Mersenne primes, LL sweep ≈ 1 s
P_MAX_FULL: int = 5000          # 669 prime exponents, 20 known Mersenne primes, LL sweep ≈ 13 s
LL_TIME_BUDGET_S: float = 25.0

# --------------------------------------------------------------------------- Ψ rings (a = 1)
RING_B: dict[int, float] = {6: 1.0, 8: 0.0, 12: -1.0, 16: SQRT2, 20: PHI - 1.0, 24: SQRT3}
RING_THETA_DEG: dict[int, float] = {6: 60.0, 8: 45.0, 12: 30.0, 16: 67.5, 20: 54.0, 24: 75.0}
GOLDEN_PERIOD: int = 20
# name -> (b, rotation angle in degrees, period)
GOLDEN_RINGS: dict[str, tuple[float, float, int]] = {
    "phi": (PHI, 72.0, 10),
    "1-phi": (1.0 - PHI, 36.0, 10),
    "-phi": (-PHI, 18.0, 20),
    "phi-1": (PHI - 1.0, 54.0, 20),
}
EIGHT_LEVELS: tuple[int, ...] = (2, 1, 0, -1, -2, -1, 0, 1)

# --------------------------------------------------------------------------- star geometry
STAR_LAYOUTS: tuple[str, ...] = ("paper_parameter_plane", "octagon_crown", "stella_octangula")
STAR_LAYOUT: str = "paper_parameter_plane"   # the paper's definition; the other two are earlier interpretations
DECORATION_Z: float = -2.5                   # z-plane of the golden decorations under the paper star
RING_RADII: dict[int, float] = {8: 1.0, 6: 1.6, 12: 2.2, 16: 2.8, 20: 3.4, 24: 4.0}
RING_Z: dict[int, float] = {8: 0.0, 6: 0.3, 12: 0.6, 16: 0.9, 20: 1.2, 24: 1.5}
GOLDEN_RING_RADIUS: float = RING_RADII[20]
GOLDEN_RING_Z: float = RING_Z[20]
N_GOLDEN_TRIANGLES: int = 5
CANDIDATE_Z_SCALE: float = 0.25
SPIRAL_TURNS: float = 2.0

# --------------------------------------------------------------------------- siever
SEED: int = 20
CV_FOLDS: int = 5
CV_REPEATS: int = 10
USE_ARITHMETIC_FEATURES: bool = True
TRIAL_FACTOR_K_MAX: int = 64
LOGISTIC_C: float = 0.3
MLP_HIDDEN: tuple[int, ...] = (32, 16)
MLP_EPOCHS: int = 300
MLP_LR: float = 1e-2
MLP_WEIGHT_DECAY: float = 1e-3
MLP_DROPOUT: float = 0.2

# --------------------------------------------------------------------------- research
NMC_P_MAX: int = 1000
WIEFERICH_LIMIT: int = 100_000
WSS_LIMIT: int = 20_000
SQUAREFREE_P_MAX: int = 200
STATS_N_REP: int = 2000            # Monte-Carlo replications for research/exponent_statistics
RANK_P_MAX_FACTOR: int = 127       # factor M_p − 1 for the rank-of-apparition cofactors up to this p
RANK_P_MAX_CHECK: int = 4423       # verify α(M_p) = 2^p for p ≡ 3 (mod 4) up to this p
SQUAREFREE_Q_MAX: int = 100_000
DISCOVERY_GRID: dict[str, object] = {
    "int_range": (-5, 5),          # includes the Mersenne point (−2, −5) and the Wagstaff point (2, −5)
    "rings": ("Z[sqrt2]", "Z[sqrt3]", "Z[phi]"),
    "coeff_range": (-2, 2),
    "n_max": 40,
}
DISCOVERY_LABEL: str = "Triboletti–Fable"
LEDGER_PATH: Path = Path("discoveries") / "candidates.md"

# --------------------------------------------------------------------------- output
OUTPUT_DIR: Path = Path("output")
HTML_NAME: str = "mersenne_star.html"
WHEEL_PNG_NAME: str = "period20_wheel.png"
GROWTH_PNG_NAME: str = "growth_law.png"
SUMMARY_CSV_NAME: str = "summary.csv"
RESEARCH_REPORT_NAME: str = "research_report.md"
INCLUDE_PLOTLYJS: bool | str = True


def as_dict() -> dict[str, object]:
    """Return every public constant as a dictionary (handy for logging a run)."""
    return {k: v for k, v in globals().items() if k.isupper()}
