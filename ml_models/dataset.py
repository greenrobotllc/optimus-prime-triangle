"""Candidate pools with labels.  This is the only ML module allowed to see the label source."""
from __future__ import annotations

import numpy as np

from core_math.mersenne import is_known_mersenne_exponent, prime_exponents
from ml_models.features import feature_matrix


def build_dataset(p_min: int = 5, p_max: int = 2500, use_arithmetic: bool = True) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """``(X, y, ps)`` for all prime exponents in ``[p_min, p_max]``.

    ``y`` comes from the table of known Mersenne exponents, which the test-suite checks
    against Lucas–Lehmer.  The features never see the label.
    """
    ps = prime_exponents(p_min, p_max)
    if not ps:
        raise ValueError(f"no prime exponents in [{p_min}, {p_max}]")
    X = feature_matrix(ps, use_arithmetic)
    y = np.array([int(is_known_mersenne_exponent(p)) for p in ps], dtype=np.int64)
    return X, y, ps
