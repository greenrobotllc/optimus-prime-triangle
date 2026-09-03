"""The computational bridge to Dyson's quasicrystal picture (the "moonshot", as a demonstration).

Two aperiodic point sets, two diffraction patterns
---------------------------------------------------
* **The Fibonacci chain.**  Lay tiles of length ``φ`` and ``1`` in the order of the Fibonacci
  word (``L → LS, S → L``).  Every position is an element of ``Z[φ] = Z + Zφ``, the set is a
  cut-and-project (model) set, and its diffraction is *pure point*: Bragg peaks at
  ``k = 2π (m + nφ) / √5`` (the dual module of ``Z[φ]`` under the trace form), with intensity
  governed by the conjugate ``m + nφ̄`` (peaks with small ``|m + nφ̄|`` are bright).  This is a
  one-dimensional quasicrystal, and it belongs to the class that Kurasov–Sarnak construct and
  that Olevskii–Ulanovskii and Alon–Cohen–Vinzant proved is *all* of the one-dimensional
  Fourier quasicrystals with integer weights.
* **The zeta zeros.**  Write the non-trivial zeros as ``ρ = 1/2 + iγ`` (RH is verified for
  every zero used here).  Landau's theorem (1911), the explicit formula seen as diffraction::

      Σ_{0<γ≤T} x^{ρ} = −(T/2π) Λ(x) + O(log T)      (x > 1),

  so ``F(u) = Σ_{γ≤T} cos(γu)`` has a negative spike of height ``(T/2π)·Λ(n)/√n`` exactly at
  ``u = log n`` for every prime power ``n = p^k`` (``Λ`` is the von Mangoldt function) and is
  ``O(√T)``-noise elsewhere.  The "diffraction pattern" of the zeros is the logarithmic
  prime-power lattice, and the zeros are, in Dyson's phrase, a quasicrystal — but not a
  uniformly discrete one: their density grows like ``log T``, which puts them outside the
  classified class.  Whether they form a crystalline measure at all is equivalent to RH.

What this module does is exactly measurable: build both patterns from real data (Odlyzko's
table of the first 100 000 zeros, or ``mpmath`` for a few hundred), locate the peaks, and check
them against the two theories — ``2π(m + nφ)/√5`` and ``Λ(n)/√n``.  Nothing here is new
mathematics; it is Landau 1911 and Elser 1985 made visible side by side.
"""
from __future__ import annotations

import math
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import config as cfg
from core_math.mersenne import sieve_primes

PHI = cfg.PHI
ODLYZKO_URL = "https://www-users.cse.umn.edu/~odlyzko/zeta_tables/zeros1"     # first 100 000 zeros, 9 decimals


# --------------------------------------------------------------------------- zeros
def load_odlyzko_zeros(path: Path | None = None, download: bool = True) -> np.ndarray:
    """Imaginary parts of the first 100 000 zeros (Odlyzko), cached under ``output/``."""
    path = Path(path) if path else cfg.OUTPUT_DIR / "odlyzko_zeros1.txt"
    if not path.exists():
        if not download:
            raise FileNotFoundError(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(ODLYZKO_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            path.write_bytes(resp.read())
    return np.loadtxt(path, dtype=float)


def compute_zeros_mpmath(n: int) -> np.ndarray:
    """First ``n`` zeros via ``mpmath.zetazero`` (slow beyond a few hundred; for tests)."""
    import mpmath

    mpmath.mp.dps = 15
    return np.array([float(mpmath.zetazero(k).imag) for k in range(1, n + 1)])


# --------------------------------------------------------------------------- zeta diffraction
def von_mangoldt(n: int) -> float:
    """``Λ(n) = log p`` if ``n = p^k``, else 0."""
    if n < 2:
        return 0.0
    for p in sieve_primes(int(math.isqrt(n)) + 1):
        if n % p == 0:
            while n % p == 0:
                n //= p
            return math.log(p) if n == 1 else 0.0
    return math.log(n)


def zero_diffraction(gammas: np.ndarray, u: np.ndarray, chunk: int = 5000) -> np.ndarray:
    """``F(u) = Σ_γ cos(γ u)`` evaluated on the grid ``u`` (vectorised in chunks of zeros)."""
    out = np.zeros_like(u, dtype=float)
    for i in range(0, len(gammas), chunk):
        g = gammas[i:i + chunk]
        out += np.cos(np.outer(u, g)).sum(axis=1)
    return out


def landau_prediction(n: int, T: float) -> float:
    """Landau: ``Σ_{γ≤T} cos(γ log n) ≈ −(T/2π) Λ(n)/√n``."""
    return -(T / (2 * math.pi)) * von_mangoldt(n) / math.sqrt(n)


@dataclass(frozen=True)
class ZetaPeak:
    n: int
    u: float               # log n
    predicted: float       # Landau
    measured: float        # min of F on a window around log n
    relative_error: float


def zeta_peak_table(gammas: np.ndarray, n_max: int = 60, half_window: float = 0.004, points: int = 41) -> list[ZetaPeak]:
    """Measured vs predicted spike depth at ``u = log n`` for prime powers ``n ≤ n_max``."""
    T = float(gammas[-1])
    rows = []
    for n in range(2, n_max + 1):
        lam = von_mangoldt(n)
        if lam == 0.0:
            continue
        u0 = math.log(n)
        grid = np.linspace(u0 - half_window, u0 + half_window, points)
        measured = float(zero_diffraction(gammas, grid).min())
        pred = landau_prediction(n, T)
        rows.append(ZetaPeak(n, u0, pred, measured, abs(measured - pred) / abs(pred)))
    return rows


# --------------------------------------------------------------------------- Fibonacci chain
def fibonacci_word(n_tiles: int) -> str:
    """Prefix of the Fibonacci word over ``{L, S}`` with ``L → LS``, ``S → L``."""
    w = "L"
    while len(w) < n_tiles:
        w = "".join("LS" if c == "L" else "L" for c in w)
    return w[:n_tiles]


def fibonacci_chain(n_tiles: int, long: float = PHI, short: float = 1.0) -> np.ndarray:
    """Vertex positions of the Fibonacci chain (all in ``Z + Zφ``), starting at 0."""
    lengths = np.array([long if c == "L" else short for c in fibonacci_word(n_tiles)])
    return np.concatenate([[0.0], np.cumsum(lengths)])


def chain_diffraction(x: np.ndarray, k: np.ndarray, chunk: int = 4000) -> np.ndarray:
    """Normalised diffraction intensity ``I(k) = |Σ_j e^{i k x_j}|² / N``."""
    out = np.zeros_like(k, dtype=complex)
    for i in range(0, len(x), chunk):
        out += np.exp(1j * np.outer(k, x[i:i + chunk])).sum(axis=1)
    return (np.abs(out) ** 2) / len(x)


def bragg_position(m: int, n: int) -> float:
    """Bragg peak of the Fibonacci chain with tiles ``(φ, 1)``: ``k = 2π (m + nφ)/√5``."""
    return 2 * math.pi * (m + n * PHI) / math.sqrt(5.0)


@dataclass(frozen=True)
class BraggPeak:
    m: int
    n: int
    k: float               # 2π (m + nφ)/√5
    amplitude2: float      # |Σ_j e^{ikx_j}|² / N², in (0, 1]; the Bragg intensity per point
    conjugate: float       # |m + n·φ̄|, small for bright peaks


def bragg_intensities(x: np.ndarray, index_max: int = 8, k_max: float = 12.0) -> list[BraggPeak]:
    """Exact diffraction amplitude at every dual-module position ``2π(m + nφ)/√5`` in ``(0, k_max]``.

    A model set's Bragg peaks are narrower than any practical ``k``-grid (width ``≈ 2π/(N·ℓ̄)``),
    so the pure-point part must be sampled *at* the module, not near it.
    """
    peaks = []
    for m in range(-index_max, index_max + 1):
        for n in range(-index_max, index_max + 1):
            k = bragg_position(m, n)
            if 0.0 < k <= k_max:
                amp = abs(np.exp(1j * k * x).sum()) ** 2 / len(x) ** 2
                peaks.append(BraggPeak(m, n, float(k), float(amp), abs(m + n * (1 - PHI))))
    return sorted(peaks, key=lambda b: b.k)


# --------------------------------------------------------------------------- assembled bridge
def build_bridge(gammas: np.ndarray, u_max: float = 4.5, u_points: int = 2600, n_tiles: int = 4000,
                 k_max: float = 12.0, k_points: int = 3000) -> dict:
    """Everything the page needs, as plain lists."""
    T = float(gammas[-1])
    # Landau spikes are ~2π/T wide (≈ 5·10⁻⁵ for 10⁵ zeros): a uniform grid misses them entirely,
    # so the grid is the union of a uniform background and exact log n abscissae with a few
    # points on each flank.
    uniform = np.linspace(0.02, u_max, u_points)
    spikes = [math.log(n) for n in range(2, int(math.exp(u_max)) + 1) if von_mangoldt(n) > 0]
    flank = np.array([-6e-4, -2e-4, -6e-5, -2e-5, 0.0, 2e-5, 6e-5, 2e-4, 6e-4])
    u = np.unique(np.concatenate([uniform] + [u0 + flank for u0 in spikes]))
    F = zero_diffraction(gammas, u) / (T / (2 * math.pi))          # Landau-normalised: spikes at −Λ(n)/√n
    zeta_rows = zeta_peak_table(gammas, n_max=min(60, int(math.exp(u_max))))   # only lines inside the displayed domain
    x = fibonacci_chain(n_tiles)
    k = np.linspace(0.0, k_max, k_points)
    background = chain_diffraction(x, k) / len(x)               # chain_diffraction is |Σ|²/N; this makes it |Σ|²/N² like amplitude2
    bragg = [b for b in bragg_intensities(x, k_max=k_max) if b.amplitude2 >= 2e-4]
    return {
        "n_zeros": int(len(gammas)), "T": T,
        "spike_n": [n for n in range(2, int(math.exp(u_max)) + 1) if von_mangoldt(n) > 0],
        "u": u.round(6).tolist(), "F_normalised": F.round(5).tolist(),
        "zeta_peaks": [{"n": r.n, "u": round(r.u, 5), "predicted": round(r.predicted / (T / (2 * math.pi)), 5),
                        "measured": round(r.measured / (T / (2 * math.pi)), 5), "rel_err": round(r.relative_error, 4)} for r in zeta_rows],
        "n_tiles": n_tiles, "k": k.round(5).tolist(), "background": background.round(7).tolist(),
        "bragg_peaks": [{"m": b.m, "n": b.n, "k": round(b.k, 4), "amplitude2": round(b.amplitude2, 6), "conjugate": round(b.conjugate, 4)} for b in bragg],
    }
