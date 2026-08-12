#!/usr/bin/env python3
"""Phase 21R / Lesson 21R.1 -- decision-margin nonconformity scores.

This module is the foundation for Phase 21R.  All action-pair choices are made
from ``y_hat`` only.  ``y_true`` is used only after the pair is fixed, so the
score rule cannot leak truth into the decision-time choice.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np


def _as_float64_2d(name: str, value: np.ndarray) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError(f"{name} phai co shape (n, K); nhan duoc ndim={arr.ndim}")
    if not np.isfinite(arr).all():
        raise ValueError(f"{name} chua NaN/inf")
    return arr


def _paired(y_true: np.ndarray, y_hat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    y_true_arr = _as_float64_2d("y_true", y_true)
    y_hat_arr = _as_float64_2d("y_hat", y_hat)
    if y_true_arr.shape != y_hat_arr.shape:
        raise ValueError(f"y_true {y_true_arr.shape} va y_hat {y_hat_arr.shape} phai cung shape")
    return y_true_arr, y_hat_arr


def top_two_by_twin(y_hat: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Return ``(a1, a2)``: the two best actions according to the twin only.

    The single-argument signature is intentional and tested.  It prevents truth
    leakage when selecting the action pair.  Stable sorting fixes the tie
    convention: lower action indices win ties.
    """
    y_hat_arr = _as_float64_2d("y_hat", y_hat)
    n, k = y_hat_arr.shape
    if k < 2:
        raise ValueError(f"can K >= 2 hanh dong de co bien quyet dinh; K={k}")

    order = np.argsort(y_hat_arr, axis=1, kind="stable")
    return order[:, 0].astype(np.int64), order[:, 1].astype(np.int64)


def margins(
    y_true: np.ndarray,
    y_hat: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(a1, a2, m_hat, m_true)`` for the twin-selected top-2 pair."""
    y_true_arr, y_hat_arr = _paired(y_true, y_hat)
    a1, a2 = top_two_by_twin(y_hat_arr)
    rows = np.arange(y_hat_arr.shape[0])
    m_hat = y_hat_arr[rows, a2] - y_hat_arr[rows, a1]
    m_true = y_true_arr[rows, a2] - y_true_arr[rows, a1]
    return a1, a2, m_hat, m_true


def s_margin_signed(y_true: np.ndarray, y_hat: np.ndarray) -> np.ndarray:
    """One-sided score: ``m_hat - m_true``.

    Positive values mean the twin is optimistic about the margin.  Negative
    values mean the true margin is wider than the twin believed.
    """
    _a1, _a2, m_hat, m_true = margins(y_true, y_hat)
    return m_hat - m_true


def s_margin(y_true: np.ndarray, y_hat: np.ndarray) -> np.ndarray:
    """Main two-sided score: ``abs(m_true - m_hat)``."""
    return np.abs(s_margin_signed(y_true, y_hat))


def s_margin_via_errors(y_true: np.ndarray, y_hat: np.ndarray) -> np.ndarray:
    """Equivalent calculation: ``abs(e(a2) - e(a1))`` with ``e=y_true-y_hat``."""
    y_true_arr, y_hat_arr = _paired(y_true, y_hat)
    a1, a2 = top_two_by_twin(y_hat_arr)
    rows = np.arange(y_hat_arr.shape[0])
    err = y_true_arr - y_hat_arr
    return np.abs(err[rows, a2] - err[rows, a1])


def s_vs_a1(y_true: np.ndarray, y_hat: np.ndarray) -> np.ndarray:
    """Phase 21 v7 score: ``max_a abs(e(a) - e(a1))``."""
    y_true_arr, y_hat_arr = _paired(y_true, y_hat)
    a1, _a2 = top_two_by_twin(y_hat_arr)
    rows = np.arange(y_hat_arr.shape[0])
    err = y_true_arr - y_hat_arr
    return np.abs(err - err[rows, a1][:, None]).max(axis=1)


def s_maxabs(y_true: np.ndarray, y_hat: np.ndarray) -> np.ndarray:
    """Absolute score: ``max_a abs(e(a))``.  For comparison only."""
    y_true_arr, y_hat_arr = _paired(y_true, y_hat)
    return np.abs(y_true_arr - y_hat_arr).max(axis=1)


def accept_certified(m_hat: np.ndarray, qhat: np.ndarray) -> np.ndarray:
    """C1 certificate: ``m_hat >= qhat``.  The factor is 1, not 2."""
    return np.asarray(m_hat, dtype=np.float64) >= np.asarray(qhat, dtype=np.float64)


def regret_upper_bound(m_hat: np.ndarray, qhat: np.ndarray) -> np.ndarray:
    """Pairwise regret upper bound: ``max(0, qhat - m_hat)``."""
    return np.maximum(
        0.0,
        np.asarray(qhat, dtype=np.float64) - np.asarray(m_hat, dtype=np.float64),
    )


def accept_kappa(m_hat: np.ndarray, qhat: np.ndarray, kappa: float) -> np.ndarray:
    """Dimensionless risk-coverage family: ``m_hat >= kappa*qhat``."""
    return np.asarray(m_hat, dtype=np.float64) >= float(kappa) * np.asarray(qhat, dtype=np.float64)


def kappa_of_eps_regret(qhat: np.ndarray, eps_regret: float) -> np.ndarray:
    """Map C2 to kappa: ``max(0, 1 - eps_regret/qhat)``."""
    qhat_arr = np.asarray(qhat, dtype=np.float64)
    return np.maximum(0.0, 1.0 - float(eps_regret) / np.maximum(qhat_arr, 1e-12))


def pair_is_true_contender(y_true: np.ndarray, y_hat: np.ndarray) -> np.ndarray:
    """Whether the true best action lies in the twin-selected pair ``{a1,a2}``."""
    y_true_arr, y_hat_arr = _paired(y_true, y_hat)
    a1, a2 = top_two_by_twin(y_hat_arr)
    a_star = np.argmin(y_true_arr, axis=1)
    return (a_star == a1) | (a_star == a2)
