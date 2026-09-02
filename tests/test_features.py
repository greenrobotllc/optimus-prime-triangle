"""Tests for ml_models.features and ml_models.dataset — including leakage guards."""
from __future__ import annotations

import pathlib

import numpy as np
import pytest

from core_math import mersenne as m
from ml_models import features as f
from ml_models.dataset import build_dataset


def test_feature_vector_length_matches_names_and_is_finite():
    for p in (2, 3, 5, 7, 11, 13, 127, 4423, 136279841):
        for arith in (True, False):
            v = f.extract_features(p, arith)
            assert v.shape == (len(f.feature_names(arith)),)
            assert np.all(np.isfinite(v))
    assert len(f.FEATURE_NAMES) == len(f.GEOMETRY_ONLY_FEATURE_NAMES) + 4


def test_features_never_call_lucas_lehmer(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("lucas_lehmer must not be called during feature extraction")

    monkeypatch.setattr(m, "lucas_lehmer", boom)
    monkeypatch.setattr(m, "lucas_lehmer_residue", boom)
    f.feature_matrix([5, 7, 11, 13, 31], True)


def test_features_source_does_not_reference_label_sources():
    src = pathlib.Path(f.__file__).read_text()
    assert "KNOWN_MERSENNE_EXPONENTS" not in src
    assert "is_known_mersenne_exponent" not in src
    assert "lucas_lehmer" not in src


def test_pow2_ring_features_are_constant_for_p_ge_5():
    ps = m.prime_exponents(5, 3000)
    X = f.feature_matrix(ps, False)
    names = f.feature_names(False)
    for i, name in enumerate(names):
        if name.endswith("_at_pow2"):
            assert np.ptp(X[:, i]) < 1e-12, name
    j = names.index("golden_phi-1_at_pow2")
    assert np.allclose(X[:, j], -(1 + 5 ** 0.5) / 2)


def test_arithmetic_features_are_sane():
    names = f.FEATURE_NAMES
    v = f.extract_features(11)
    assert v[names.index("sophie_germain_factor")] == 1.0
    assert v[names.index("trial_factor_found")] == 1.0
    assert v[names.index("trial_factor_log10_k")] == 0.0          # 23 = 2·1·11 + 1 → k = 1
    v13 = f.extract_features(13)
    assert v13[names.index("trial_factor_found")] == 0.0
    assert 0.0 <= v13[names.index("wagstaff_prior")] <= 1.0


def test_labels_from_table_equal_lucas_lehmer_below_600():
    X, y, ps = build_dataset(2, 600)
    assert X.shape == (len(ps), len(f.FEATURE_NAMES))
    assert list(y) == [int(m.lucas_lehmer(p)) for p in ps]
    assert y.sum() == 13


def test_wagstaff_prior_recoverable_from_log2_column():
    X, _, ps = build_dataset(2, 300, use_arithmetic=False)
    prior = f.wagstaff_prior_from_features(X)
    assert np.allclose(prior, [m.wagstaff_probability(p) for p in ps])


def test_scale_feature_indices():
    assert f.scale_feature_indices(True) == [0, 1, 2, 3]
    with pytest.raises(ValueError):
        f.extract_features(1)
