"""Periodicity classification of the Ψ rings — the repo's first labelled candidate result.

Theorem (periodicity classification; derived in this repository)
-----------------------------------------------------------------
Let ``a = 1`` and ``|b| < 2``, and write ``b = −2·cos(2θ)`` with ``0 < θ < π/2``.  Then::

    Ψ(1, b, n) = 2·cos(nθ)          for even n,
    Ψ(1, b, n) = cos(nθ) / cos(θ)   for odd n,

so ``n ↦ Ψ(1, b, n)`` is periodic **iff** ``θ/(2π)`` is rational.  Writing ``θ = 2π·k/m`` in
lowest terms, the minimal period is ``m`` when ``m`` is even and ``2m`` when ``m`` is odd.
For ``|b| > 2`` the sequence is unbounded (``2·cosh``); ``b = 2`` is degenerate (linear
growth) and ``b = −2`` has period 2.

Proof.  Equation 36 of Ibrahim's paper with ``a = 1``: ``s = (b + 2)/(b − 2) = −tan²θ``, so
``√s = i·tan θ`` and ``(1 ± i tan θ)^n = sec^n θ · e^{±inθ}``; the prefactor
``(2 − b)^{⌊n/2⌋}/2^n = cos^{2⌊n/2⌋}θ · 2^{2⌊n/2⌋ − n}`` cancels the secants except for one
factor when ``n`` is odd.  Periodicity of ``cos(nθ)`` in ``n`` requires ``θ/2π ∈ Q``; the
even and odd branches differ, so the period of the interleaved sequence is the least
common multiple of ``2`` and the order ``m`` of the rotation. ∎

Consequences
------------
* The six rings reported by Ibrahim (periods 6, 8, 12, 16, 20, 24 at ``b = 1, 0, −1, √2,
  φ−1, √3``) are the rotations ``θ = 60°, 45°, 30°, 67.5°, 54°, 75°``.
* The golden ratio gives four rings — ``b = φ`` (θ = 72°, period 10), ``b = 1 − φ`` (36°, 10),
  ``b = −φ`` (18°, 20) and ``b = φ − 1`` (54°, 20) — whose angles are exactly the
  golden-triangle / pentagram angles.  Only the last appears in the paper.
* Because ``2^{p−1}`` stabilises modulo every one of these periods, the ring coordinate of
  the Lucas–Lehmer index is the same for every odd prime ``p``; the rings are coordinates,
  not primality tests.

Novelty status: the ingredients (Chebyshev / Lucas-sequence normalisation) are classical;
the *statement* unifying Ibrahim's six isolated observations and the three unlisted golden
rings is what the ledger records, with novelty flagged as unchecked.
"""
from __future__ import annotations

import math
from fractions import Fraction

from core_math.psi_sequence import PHI_EXACT, QuadInt, SQRT2_EXACT, SQRT3_EXACT, minimal_period, psi, rotation_angle_rad

THEOREM_STATEMENT = (
    "Ψ(1, −2cos 2θ, n) is periodic in n iff θ/2π = k/m is rational; the minimal period is m for even m "
    "and 2m for odd m.  Golden rings: b=φ (72°, 10), b=1−φ (36°, 10), b=−φ (18°, 20), b=φ−1 (54°, 20)."
)


def rotation_angle_deg(b: float) -> float:
    """``θ`` in degrees with ``b = −2cos 2θ``."""
    return math.degrees(rotation_angle_rad(b))


def rational_turn(b: float, max_denominator: int = 2000, tol: float = 1e-9) -> Fraction | None:
    """``θ/2π`` as a reduced fraction when it is (numerically) rational, else ``None``."""
    if abs(b) > 2:
        return None
    r = rotation_angle_rad(b) / (2 * math.pi)
    frac = Fraction(r).limit_denominator(max_denominator)
    return frac if abs(float(frac) - r) < tol else None


def regime(b: float) -> str:
    if abs(b) < 2:
        return "elliptic"
    if b == 2:
        return "degenerate"
    if b == -2:
        return "elliptic"
    return "hyperbolic"


def predicted_period(b: float) -> int | None:
    """Period predicted by the classification, or ``None`` when not periodic."""
    if regime(b) != "elliptic":
        return None
    turn = rational_turn(b)
    if turn is None:
        return None
    m = turn.denominator
    return m if m % 2 == 0 else 2 * m


def is_periodic(b: float) -> bool:
    return predicted_period(b) is not None


def classify_ring(b: float) -> dict[str, object]:
    """Regime, rotation angle, rational turn and predicted period of ``Ψ(1, b, ·)``."""
    reg = regime(b)
    info: dict[str, object] = {"b": b, "regime": reg}
    if reg in ("elliptic", "degenerate") and abs(b) <= 2:
        info["theta_deg"] = rotation_angle_deg(b)
        turn = rational_turn(b)
        info["turn"] = turn
    info["period"] = predicted_period(b)
    return info


def float_period(seq: list[float], tol: float = 1e-6) -> int | None:
    for P in range(1, len(seq) // 2 + 1):
        if all(abs(seq[i] - seq[i + P]) < tol for i in range(len(seq) - P)):
            return P
    return None


def verify_prediction_float(b: float, n_extra: int = 2) -> bool:
    """Compute ``Ψ(1, b, n)`` in floating point and compare its period with the prediction."""
    pred = predicted_period(b)
    if pred is None:
        return False
    seq = [psi(1.0, b, n) for n in range(3 * pred + n_extra)]
    return float_period(seq) == pred


def verify_prediction_exact(one: QuadInt | int, b_exact: QuadInt | int, b_float: float) -> bool:
    """Exact check in a quadratic ring (or ``Z``) of the predicted period."""
    pred = predicted_period(b_float)
    if pred is None:
        return False
    seq = [psi(one, b_exact, n) for n in range(3 * pred + 2)]
    return minimal_period(seq) == pred


def golden_rings() -> list[dict[str, object]]:
    """The four golden rings with exact verification."""
    phi_f = float(PHI_EXACT)
    one = QuadInt(1, 0, "phi")
    rows = []
    for name, b_exact, b_float in (
        ("phi", PHI_EXACT, phi_f),
        ("1-phi", 1 - PHI_EXACT, 1 - phi_f),
        ("-phi", -PHI_EXACT, -phi_f),
        ("phi-1", PHI_EXACT - 1, phi_f - 1),
    ):
        pred = predicted_period(b_float)
        rows.append({
            "name": name,
            "b": b_exact,
            "theta_deg": rotation_angle_deg(b_float),
            "predicted_period": pred,
            "verified_exact": verify_prediction_exact(one, b_exact, b_float),
            "in_source_paper": name == "phi-1",
        })
    return rows


def paper_rings() -> list[dict[str, object]]:
    """Ibrahim's six rings with exact verification."""
    specs = [
        (1, 1, 1.0), (1, 0, 0.0), (1, -1, -1.0),
        (QuadInt(1, 0, "sqrt2"), SQRT2_EXACT, math.sqrt(2)),
        (QuadInt(1, 0, "phi"), PHI_EXACT - 1, float(PHI_EXACT) - 1),
        (QuadInt(1, 0, "sqrt3"), SQRT3_EXACT, math.sqrt(3)),
    ]
    return [{
        "b": b_exact, "theta_deg": rotation_angle_deg(b_float),
        "predicted_period": predicted_period(b_float),
        "verified_exact": verify_prediction_exact(one, b_exact, b_float),
    } for one, b_exact, b_float in specs]


def prediction_table(max_m: int = 30) -> list[dict[str, object]]:
    """Every reduced rotation ``k/m`` with ``m ≤ max_m``: predicted vs observed period."""
    rows = []
    for m in range(1, max_m + 1):
        for k in range(0 if m == 1 else 1, (m + 1) // 2 + (1 if m == 1 else 0)):
            if m > 1 and math.gcd(k, m) != 1:
                continue
            theta = 2 * math.pi * k / m
            b = -2 * math.cos(2 * theta)
            if abs(b - 2) < 1e-12:
                continue
            pred = predicted_period(b)
            rows.append({"k": k, "m": m, "theta_deg": math.degrees(theta) % 180, "b": b,
                         "predicted": pred, "verified": verify_prediction_float(b)})
    return rows
