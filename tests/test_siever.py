"""Tests for ml_models.siever."""
from __future__ import annotations

import numpy as np
import pytest

from ml_models import siever as sv
from ml_models.dataset import build_dataset
from ml_models.features import FEATURE_NAMES


@pytest.fixture(scope="module")
def data():
    X, y, ps = build_dataset(5, 1500)
    return X, y, ps


def test_logistic_outputs_in_unit_interval_and_drops_constant_block(data):
    X, y, _ = data
    model = sv.LogisticSiever().fit(X, y)
    s = sv.score_candidates(model, X)
    assert s.shape == (len(y),) and np.all((s >= 0) & (s <= 1))
    assert model.n_dropped_constant >= 10          # the whole *_at_pow2 block is constant for p >= 5
    top = model.coefficients(FEATURE_NAMES)[:5]
    assert all(isinstance(n, str) for n, _ in top)


def test_mlp_trains_deterministically_with_seed(data):
    X, y, _ = data
    a = sv.TorchMLPSiever(epochs=40, seed=7).fit(X, y).predict_proba(X)
    b = sv.TorchMLPSiever(epochs=40, seed=7).fit(X, y).predict_proba(X)
    assert np.allclose(a, b)
    assert np.all((a >= 0) & (a <= 1))


def test_wagstaff_and_constant_baselines(data):
    X, y, _ = data
    w = sv.WagstaffBaseline().predict_proba(X)
    assert np.all((w >= 0) & (w <= 1)) and w[0] >= w[-1]
    c = sv.ConstantBaseline().fit(X, y).predict_proba(X)
    assert np.allclose(c, y.mean())


def test_evaluate_cv_reports_all_models_and_valid_metrics(data):
    X, y, _ = data
    models = sv.default_model_factories(include_mlp=True, mlp_epochs=30)
    report = sv.evaluate_cv(models, X, y, folds=3, repeats=2, seed=1)
    assert set(report) == {"constant", "wagstaff", "scale_only", "logistic", "mlp"}
    for name, metrics in report.items():
        assert set(metrics) == set(sv.METRICS)
        assert 0.0 <= metrics["roc_auc"][0] <= 1.0
        assert 0.0 <= metrics["average_precision"][0] <= 1.0
        assert 1 <= metrics["ll_tests_to_full_recall"][0] <= len(y)
    table = sv.format_cv_table(report)
    assert "logistic" in table and "wagstaff" in table
    line = sv.honesty_line(report)
    assert "Wagstaff" in line


def test_train_default_and_unknown_kind(data):
    X, y, _ = data
    model = sv.train_default("logistic", X, y)
    assert sv.score_candidates(model, X[:3]).shape == (3,)
    with pytest.raises(ValueError):
        sv.train_default("svm", X, y)


def test_honesty_line_with_single_repeat(data):
    X, y, _ = data
    report = sv.evaluate_cv(sv.default_model_factories(include_mlp=False), X, y, folds=3, repeats=1, seed=1)
    assert "no spread estimate" in sv.honesty_line(report)
