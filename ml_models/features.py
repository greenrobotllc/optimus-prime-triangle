"""Exponent → float feature vector for the geometric siever.

Leakage policy (enforced by tests)
----------------------------------
This module never imports the Lucas–Lehmer test and never references the table of known
Mersenne exponents.  Labels are attached in :mod:`ml_models.dataset`.  ``2^p`` is never
materialised: only ``log₂ p``, residues ``p mod k`` and ``pow(2, p − 1, k)`` are used, so
every feature is finite for ``p`` up to the largest known exponent and beyond.

Feature groups (see ``FEATURE_NAMES`` for the exact order)
-----------------------------------------------------------
A. scale — ``log2_p``, ``inv_ln_p``.  Wagstaff's heuristic density is ``∝ ln(a·p)/p``; these
   are the only magnitude encodings that are safe as floats.
B. residue harmonics — one-hot ``p ≡ 1, 3 (mod 4)`` and ``(cos, sin)`` of ``2π·(p mod k)/k``
   for ``k ∈ {3, 5, 8, 12, 16, 20, 24}``.  Every periodic Ψ ring is a function of these
   residues; the angle encoding keeps neighbouring residues close.
C. ring levels at ``p`` — ``Ψ(1, b, p)`` for the six paper rings and the four golden rings:
   ``p``'s exact coordinates on the "Mersenne Star" rings.
D. ring levels at the Lucas–Lehmer index ``n = 2^{p−1}`` (reduced mod the period).  These
   are *deliberately* included to document a fact: because the ring periods are of the
   form ``2^a·3^b·5^c`` and ``2^{p−1}`` stabilises modulo each of them, **every** group-D
   feature is constant for ``p ≥ 5`` (the golden one is ``−φ``).  ``VarianceThreshold``
   removes them; the CV report counts how many were dropped.
E. golden geometry — ``(cos, sin)`` of the golden-angle position ``p·137.5°`` and the five
   proximity metrics of :func:`core_math.geometry.proximity_metrics`.
F. arithmetic pre-sieve (toggleable) — Sophie-Germain factor flag, trial-factor flag,
   ``log10 k`` of the factor ``2kp + 1`` found (0 otherwise), Wagstaff prior.  Kept as a
   separate group so the ablation "geometry only vs geometry + arithmetic" is honest.
"""
from __future__ import annotations

import math

import numpy as np

import config as cfg
from core_math.geometry import proximity_metrics
from core_math.mersenne import sophie_germain_factor, trial_factor, wagstaff_probability
from core_math.psi_sequence import GOLDEN_TABLES, PERIODIC_TABLES, golden_ring_level, psi_periodic

RESIDUE_MODULI: tuple[int, ...] = (3, 5, 8, 12, 16, 20, 24)
RING_PERIODS: tuple[int, ...] = tuple(sorted(PERIODIC_TABLES))
GOLDEN_RING_NAMES: tuple[str, ...] = tuple(GOLDEN_TABLES)
PROXIMITY_KEYS: tuple[str, ...] = (
    "phi_zone_distance",
    "fibonacci_zone_distance",
    "golden_node_angular_distance",
    "pentagram_intersection_distance",
    "beatty_distance",
)
ARITHMETIC_FEATURES: tuple[str, ...] = ("sophie_germain_factor", "trial_factor_found", "trial_factor_log10_k", "wagstaff_prior")


def _names(use_arithmetic: bool) -> list[str]:
    names = ["log2_p", "inv_ln_p", "p_mod4_eq1", "p_mod4_eq3"]
    for k in RESIDUE_MODULI:
        names += [f"cos_p_mod{k}", f"sin_p_mod{k}"]
    names += [f"psi_ring{k}_at_p" for k in RING_PERIODS]
    names += [f"golden_{n}_at_p" for n in GOLDEN_RING_NAMES]
    names += [f"psi_ring{k}_at_pow2" for k in RING_PERIODS]
    names += [f"golden_{n}_at_pow2" for n in GOLDEN_RING_NAMES]
    names += ["cos_golden_angle", "sin_golden_angle"]
    names += list(PROXIMITY_KEYS)
    if use_arithmetic:
        names += list(ARITHMETIC_FEATURES)
    return names


FEATURE_NAMES: list[str] = _names(True)
GEOMETRY_ONLY_FEATURE_NAMES: list[str] = _names(False)
SCALE_FEATURE_NAMES: list[str] = ["log2_p", "inv_ln_p", "p_mod4_eq1", "p_mod4_eq3"]


def feature_names(use_arithmetic: bool = True) -> list[str]:
    return FEATURE_NAMES if use_arithmetic else GEOMETRY_ONLY_FEATURE_NAMES


def extract_features(p: int, use_arithmetic: bool = True) -> np.ndarray:
    """Float64 feature vector for exponent ``p`` (``len == len(feature_names(use_arithmetic))``)."""
    if p < 2:
        raise ValueError("p must be >= 2")
    row: list[float] = [math.log2(p), 1.0 / math.log(p) if p > 1 else 0.0, float(p % 4 == 1), float(p % 4 == 3)]
    for k in RESIDUE_MODULI:
        ang = 2.0 * math.pi * (p % k) / k
        row += [math.cos(ang), math.sin(ang)]
    row += [psi_periodic(k, p) for k in RING_PERIODS]
    row += [golden_ring_level(name, p) for name in GOLDEN_RING_NAMES]
    row += [psi_periodic(k, pow(2, p - 1, k)) for k in RING_PERIODS]
    row += [golden_ring_level(name, pow(2, p - 1, GOLDEN_TABLES[name][2])) for name in GOLDEN_RING_NAMES]
    ga = math.radians((p * cfg.GOLDEN_ANGLE_DEG) % 360.0)
    row += [math.cos(ga), math.sin(ga)]
    met = proximity_metrics(p)
    row += [met[k] for k in PROXIMITY_KEYS]
    if use_arithmetic:
        q = trial_factor(p, cfg.TRIAL_FACTOR_K_MAX)
        row += [
            float(sophie_germain_factor(p)),
            float(q is not None),
            math.log10((q - 1) // (2 * p)) if q is not None else 0.0,
            wagstaff_probability(p),
        ]
    return np.asarray(row, dtype=np.float64)


def feature_matrix(ps: list[int], use_arithmetic: bool = True) -> np.ndarray:
    """Stack :func:`extract_features` over a list of exponents."""
    return np.vstack([extract_features(p, use_arithmetic) for p in ps])


def scale_feature_indices(use_arithmetic: bool = True) -> list[int]:
    names = feature_names(use_arithmetic)
    return [names.index(n) for n in SCALE_FEATURE_NAMES]


def wagstaff_prior_from_features(X: np.ndarray) -> np.ndarray:
    """Recover the Wagstaff prior from the ``log2_p`` column (works without group F)."""
    ps = np.rint(2.0 ** X[:, 0]).astype(np.int64)
    return np.array([wagstaff_probability(int(p)) for p in ps])
