"""The geometric siever: baselines, a logistic-regression model and a small torch MLP that
map an exponent's Mersenne-Star features to a "primality plausibility index" in [0, 1].

Honesty by construction
-----------------------
* There are only 52 known Mersenne primes; below ``p = 2500`` there are 17 positives among
  367 prime exponents.  Every model is therefore evaluated with *repeated stratified
  K-fold cross-validation*, metrics are pooled over the out-of-fold predictions of each
  repeat, and mean ± SD across repeats is reported.
* Every model is compared with three baselines: the constant base rate, **Wagstaff's
  heuristic prior** (the number-theoretic expectation ``e^γ·ln(a·p)/(p·ln 2)``) and a
  scale-only logistic model that sees ``log₂ p`` and ``p mod 4`` only.  The report prints
  an explicit line stating whether the geometric features give a lift over the Wagstaff
  prior that exceeds one standard deviation.
* The Lucas–Lehmer result is never a feature (see :mod:`ml_models.features`); it is the
  label, and it is recomputed downstream of scoring as the *confirmation* step.
"""
from __future__ import annotations

import math
from typing import Callable, Protocol

import numpy as np
from sklearn.feature_selection import VarianceThreshold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import config as cfg
from ml_models.features import scale_feature_indices, wagstaff_prior_from_features

METRICS: tuple[str, ...] = ("roc_auc", "average_precision", "brier", "log_loss", "ll_tests_to_full_recall")


class SieverBase(Protocol):
    def fit(self, X: np.ndarray, y: np.ndarray) -> "SieverBase": ...

    def predict_proba(self, X: np.ndarray) -> np.ndarray: ...   # shape (n,), P(M_p prime)


# --------------------------------------------------------------------------- baselines
class ConstantBaseline:
    """Predicts the training base rate for everyone."""

    rate: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> "ConstantBaseline":
        self.rate = float(np.mean(y))
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return np.full(len(X), self.rate)


class WagstaffBaseline:
    """The number-theoretic prior; needs no fitting."""

    def fit(self, X: np.ndarray, y: np.ndarray) -> "WagstaffBaseline":
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return wagstaff_prior_from_features(X)


class ScaleOnlyLogistic:
    """Ablation: logistic regression on ``log₂ p``, ``1/ln p`` and ``p mod 4`` only."""

    def __init__(self, use_arithmetic: bool = True, C: float = cfg.LOGISTIC_C) -> None:
        self.idx = scale_feature_indices(use_arithmetic)
        self.pipe = Pipeline([("scale", StandardScaler()),
                              ("clf", LogisticRegression(class_weight="balanced", C=C, max_iter=5000))])

    def fit(self, X: np.ndarray, y: np.ndarray) -> "ScaleOnlyLogistic":
        self.pipe.fit(X[:, self.idx], y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.pipe.predict_proba(X[:, self.idx])[:, 1]


# --------------------------------------------------------------------------- models
class LogisticSiever:
    """VarianceThreshold → StandardScaler → balanced logistic regression."""

    def __init__(self, C: float = cfg.LOGISTIC_C) -> None:
        self.pipe = Pipeline([
            ("var", VarianceThreshold(1e-12)),
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(class_weight="balanced", C=C, max_iter=5000)),
        ])

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LogisticSiever":
        self.pipe.fit(X, y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.pipe.predict_proba(X)[:, 1]

    @property
    def n_dropped_constant(self) -> int:
        """How many features VarianceThreshold removed (the group-D ``_at_pow2`` block)."""
        return int((~self.pipe["var"].get_support()).sum())

    def coefficients(self, names: list[str]) -> list[tuple[str, float]]:
        support = self.pipe["var"].get_support()
        kept = [n for n, s in zip(names, support) if s]
        coefs = self.pipe["clf"].coef_[0]
        return sorted(zip(kept, coefs), key=lambda t: -abs(t[1]))


class TorchMLPSiever:
    """Small fully-connected network trained full-batch on CPU with a class-weighted loss."""

    def __init__(self, hidden: tuple[int, ...] = cfg.MLP_HIDDEN, epochs: int = cfg.MLP_EPOCHS, lr: float = cfg.MLP_LR,
                 weight_decay: float = cfg.MLP_WEIGHT_DECAY, dropout: float = cfg.MLP_DROPOUT, seed: int = cfg.SEED) -> None:
        self.hidden, self.epochs, self.lr = hidden, epochs, lr
        self.weight_decay, self.dropout, self.seed = weight_decay, dropout, seed
        self.model = None
        self.mean: np.ndarray | None = None
        self.std: np.ndarray | None = None

    def _build(self, n_in: int):
        import torch.nn as nn

        layers: list = []
        prev = n_in
        for h in self.hidden:
            layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(self.dropout)]
            prev = h
        layers.append(nn.Linear(prev, 1))
        return nn.Sequential(*layers)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "TorchMLPSiever":
        import torch

        torch.manual_seed(self.seed)
        self.mean = X.mean(axis=0)
        self.std = X.std(axis=0)
        self.std[self.std < 1e-12] = 1.0
        Xt = torch.tensor((X - self.mean) / self.std, dtype=torch.float32)
        yt = torch.tensor(y, dtype=torch.float32).unsqueeze(1)
        pos = float(y.sum())
        neg = float(len(y) - pos)
        pos_weight = torch.tensor([neg / max(pos, 1.0)], dtype=torch.float32)
        self.model = self._build(X.shape[1])
        loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
        opt = torch.optim.Adam(self.model.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        self.model.train()
        for _ in range(self.epochs):
            opt.zero_grad()
            loss = loss_fn(self.model(Xt), yt)
            loss.backward()
            opt.step()
        self.model.eval()
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        import torch

        assert self.model is not None and self.mean is not None and self.std is not None
        Xt = torch.tensor((X - self.mean) / self.std, dtype=torch.float32)
        with torch.no_grad():
            return torch.sigmoid(self.model(Xt)).squeeze(1).numpy().astype(np.float64)


# --------------------------------------------------------------------------- evaluation
def _metrics(y: np.ndarray, s: np.ndarray) -> dict[str, float]:
    s_clipped = np.clip(s, 1e-6, 1 - 1e-6)
    order = np.argsort(-s, kind="stable")
    ranks_of_positives = np.nonzero(y[order] == 1)[0]
    tests_to_recall = int(ranks_of_positives.max()) + 1 if len(ranks_of_positives) else 0
    return {
        "roc_auc": float(roc_auc_score(y, s)),
        "average_precision": float(average_precision_score(y, s)),
        "brier": float(brier_score_loss(y, s_clipped)),
        "log_loss": float(log_loss(y, s_clipped, labels=[0, 1])),
        "ll_tests_to_full_recall": float(tests_to_recall),
    }


def default_model_factories(use_arithmetic: bool = True, include_mlp: bool = True, mlp_epochs: int | None = None) -> dict[str, Callable[[], SieverBase]]:
    factories: dict[str, Callable[[], SieverBase]] = {
        "constant": ConstantBaseline,
        "wagstaff": WagstaffBaseline,
        "scale_only": lambda: ScaleOnlyLogistic(use_arithmetic),
        "logistic": LogisticSiever,
    }
    if include_mlp:
        factories["mlp"] = lambda: TorchMLPSiever(epochs=mlp_epochs or cfg.MLP_EPOCHS)
    return factories


def evaluate_cv(models: dict[str, Callable[[], SieverBase]], X: np.ndarray, y: np.ndarray, folds: int = cfg.CV_FOLDS,
                repeats: int = cfg.CV_REPEATS, seed: int = cfg.SEED) -> dict[str, dict[str, tuple[float, float]]]:
    """Repeated stratified K-fold; per repeat the out-of-fold scores are pooled before
    computing metrics (folds contain only 3–4 positives).  Returns mean ± SD per metric."""
    per_model: dict[str, list[dict[str, float]]] = {name: [] for name in models}
    for r in range(repeats):
        skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed + r)
        oof = {name: np.zeros(len(y)) for name in models}
        for train_idx, test_idx in skf.split(X, y):
            for name, factory in models.items():
                model = factory().fit(X[train_idx], y[train_idx])
                oof[name][test_idx] = model.predict_proba(X[test_idx])
        for name in models:
            per_model[name].append(_metrics(y, oof[name]))
    report: dict[str, dict[str, tuple[float, float]]] = {}
    for name, rows in per_model.items():
        report[name] = {}
        for metric in METRICS:
            vals = np.array([row[metric] for row in rows])
            report[name][metric] = (float(vals.mean()), float(vals.std(ddof=1)) if len(vals) > 1 else 0.0)
    return report


def format_cv_table(report: dict[str, dict[str, tuple[float, float]]]) -> str:
    header = f"{'model':<12}" + "".join(f"{m:>24}" for m in METRICS)
    lines = [header, "-" * len(header)]
    for name, metrics in report.items():
        cells = "".join(f"{metrics[m][0]:>15.3f} ± {metrics[m][1]:<6.3f}" for m in METRICS)
        lines.append(f"{name:<12}{cells}")
    return "\n".join(lines)


def honesty_line(report: dict[str, dict[str, tuple[float, float]]], model: str = "logistic", baseline: str = "wagstaff",
                 metric: str = "average_precision") -> str:
    """One sentence stating whether ``model`` beats ``baseline`` by more than one SD."""
    m_mean, m_sd = report[model][metric]
    b_mean, b_sd = report[baseline][metric]
    lift = m_mean - b_mean
    sd = math.sqrt(m_sd**2 + b_sd**2)
    if lift < sd:
        return (f"Lift of '{model}' over the Wagstaff prior on {metric} is {lift:+.3f} (< 1 SD = {sd:.3f}): "
                "no evidence of a geometric signal beyond the number-theoretic prior.")
    return (f"Lift of '{model}' over the Wagstaff prior on {metric} is {lift:+.3f} (≥ 1 SD = {sd:.3f}); "
            "treat as suggestive only — the sample has very few positives.")


# --------------------------------------------------------------------------- training / scoring
def train_default(kind: str, X: np.ndarray, y: np.ndarray, use_arithmetic: bool = True) -> SieverBase:
    factories = default_model_factories(use_arithmetic)
    if kind not in factories:
        raise ValueError(f"unknown model kind {kind!r}; choose from {sorted(factories)}")
    return factories[kind]().fit(X, y)


def score_candidates(model: SieverBase, X: np.ndarray) -> np.ndarray:
    """Plausibility index in ``[0, 1]`` for each row of ``X``."""
    return np.clip(model.predict_proba(X), 0.0, 1.0)
