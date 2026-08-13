#!/usr/bin/env python3
"""Phase 22 / Lesson 22.1 -- simultaneous nonconformity scores over K actions.

Phase 21R certified one pair ``{a1, a2}``. This module certifies all ``K``
actions at once. Every claim here is a statement about a difference against
``a1``, so the family has ``K - 1`` members, not ``K``.

Two layers on purpose:

* kernel layer   -- plain numpy in, plain numpy out. Easy to test and compose.
* labelled layer -- thin wrappers returning ``Labelled`` with the three tags
  ``scale`` / ``level`` / ``rowset`` required by the Phase 22 three-label rule.

All action choices are made from ``y_hat`` only. ``y_true`` never touches the
selection step, so the score rule cannot leak truth into the decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import numpy as np

from cert.margin_score import _as_float64_2d, _paired


# ---------------------------------------------------------------------------
# 0. Locked constants (mirror docs/phase-22/00-preregistration.md)
# ---------------------------------------------------------------------------

ALPHA = 0.10
SCALE_COST = "cost_ms"


def n_comparisons(k_actions: int) -> int:
    """Family size: every claim is a difference against ``a1``."""
    k_actions = int(k_actions)
    if k_actions < 2:
        raise ValueError("can K >= 2 hanh dong; K=%d" % k_actions)
    return k_actions - 1


def alpha_bonferroni(alpha: float, m: int) -> float:
    """Boole/union bound: split the budget evenly over ``m`` claims."""
    return float(alpha) / int(m)


def alpha_sidak(alpha: float, m: int) -> float:
    """Exact under independence: ``1 - (1-alpha)**(1/m)``."""
    return 1.0 - (1.0 - float(alpha)) ** (1.0 / int(m))


# ---------------------------------------------------------------------------
# 1. Kernel layer -- scores
# ---------------------------------------------------------------------------

def top_k_by_twin(y_hat: np.ndarray, k: Optional[int] = None) -> np.ndarray:
    """Return the twin ranking, shape ``(n, k)``. Column 0 is ``a1``.

    Single-substantive-argument signature is intentional and tested (GS-1):
    the ranking must not see ``y_true``. Stable sort fixes the tie rule, so
    lower action index wins.
    """
    y_hat_arr = _as_float64_2d("y_hat", y_hat)
    _n, k_actions = y_hat_arr.shape
    if k_actions < 2:
        raise ValueError("can K >= 2 hanh dong de co bien quyet dinh; K=%d" % k_actions)
    k = k_actions if k is None else int(k)
    if not 1 <= k <= k_actions:
        raise ValueError("k=%d ngoai [1, %d]" % (k, k_actions))
    order = np.argsort(y_hat_arr, axis=1, kind="stable")
    return order[:, :k].astype(np.int64)


def errors(y_true: np.ndarray, y_hat: np.ndarray) -> np.ndarray:
    """Signed twin error per action: ``e(a) = y_true(a) - y_hat(a)``."""
    y_true_arr, y_hat_arr = _paired(y_true, y_hat)
    return y_true_arr - y_hat_arr


def pair_scores(y_true: np.ndarray, y_hat: np.ndarray) -> np.ndarray:
    """Return ``(n, K-1)`` scores ``|e(a_j) - e(a_1)|`` by twin rank.

    Column ``j`` is the comparison ``a1`` versus the twin's ``(j+2)``-th best
    action. The column index is a rank slot, never a path identity, so the slot
    is exchangeable across rows.
    """
    err = errors(y_true, y_hat)
    order = top_k_by_twin(y_hat)
    rows = np.arange(err.shape[0])[:, None]
    err_ranked = err[rows, order]
    return np.abs(err_ranked[:, 1:] - err_ranked[:, [0]])


def pair_margins_hat(y_hat: np.ndarray) -> np.ndarray:
    """Return ``(n, K-1)`` twin gaps ``y_hat(a_j) - y_hat(a_1)``, all >= 0."""
    y_hat_arr = _as_float64_2d("y_hat", y_hat)
    order = top_k_by_twin(y_hat_arr)
    rows = np.arange(y_hat_arr.shape[0])[:, None]
    ranked = y_hat_arr[rows, order]
    return ranked[:, 1:] - ranked[:, [0]]


def pair_margins_true(y_true: np.ndarray, y_hat: np.ndarray) -> np.ndarray:
    """Return ``(n, K-1)`` true gaps ``y_true(a_j) - y_true(a_1)``; may be < 0."""
    y_true_arr, y_hat_arr = _paired(y_true, y_hat)
    order = top_k_by_twin(y_hat_arr)
    rows = np.arange(y_true_arr.shape[0])[:, None]
    ranked = y_true_arr[rows, order]
    return ranked[:, 1:] - ranked[:, [0]]


def s_simultaneous(y_true: np.ndarray, y_hat: np.ndarray) -> np.ndarray:
    """Max-score: ``max_{a != a1} |e(a) - e(a1)|``. Same as v7 ``s_vs_a1``."""
    return pair_scores(y_true, y_hat).max(axis=1)


def s_margin(y_true: np.ndarray, y_hat: np.ndarray) -> np.ndarray:
    """21R pair score. Equals ``pair_scores[:, 0]`` by construction."""
    return pair_scores(y_true, y_hat)[:, 0]


def s_maxabs(y_true: np.ndarray, y_hat: np.ndarray) -> np.ndarray:
    """Absolute score ``max_a |e(a)|``. Upper reference only, never certified."""
    return np.abs(errors(y_true, y_hat)).max(axis=1)


def a_star_rank_by_twin(y_true: np.ndarray, y_hat: np.ndarray) -> np.ndarray:
    """Rank (1-based) that the twin gave to the truly best action."""
    y_true_arr, y_hat_arr = _paired(y_true, y_hat)
    order = top_k_by_twin(y_hat_arr)
    a_star = np.argmin(y_true_arr, axis=1)
    hit = order == a_star[:, None]
    return (np.argmax(hit, axis=1) + 1).astype(np.int64)


# ---------------------------------------------------------------------------
# 2. Kernel layer -- conformal quantiles
# ---------------------------------------------------------------------------

def conformal_level(n_eff: int, alpha: float) -> Optional[float]:
    """Conservative split-conformal level, or ``None`` when n is too small.

    ``None`` means ``q_hat = +inf``: coverage still holds, but the interval is
    useless. This happens when ``n_eff < ceil(1/alpha) - 1``.
    """
    n_eff = int(n_eff)
    if n_eff <= 0:
        return None
    k = int(np.ceil((n_eff + 1) * (1.0 - float(alpha))))
    return None if k > n_eff else k / n_eff


def empirical_qhat(values: np.ndarray, level: Optional[float]) -> float:
    """Quantile with ``method='higher'`` so ``q_hat`` is a real sample point."""
    if level is None:
        return float("inf")
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return float("inf")
    return float(np.quantile(arr, float(level), method="higher"))


def qhat_maxscore(s_sim: np.ndarray, alpha: float = ALPHA, n_eff: Optional[int] = None) -> float:
    """One quantile of the max-score at level alpha; simultaneous for free."""
    arr = np.asarray(s_sim, dtype=np.float64)
    n_eff = int(arr.size) if n_eff is None else int(n_eff)
    return empirical_qhat(arr, conformal_level(n_eff, alpha))


def qhat_per_slot(
    pair_s: np.ndarray,
    alpha_each: float,
    n_eff: Optional[int] = None,
) -> np.ndarray:
    """One quantile per rank slot, each at level ``alpha_each``.

    Slots are calibrated separately, never pooled: the ``K-1`` scores inside a
    row are dependent, so pooling them would inflate ``n`` by ``K-1`` and make
    the ``(n+1)`` finite-sample correction wrong.
    """
    arr = np.asarray(pair_s, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError("pair_s phai co shape (n, K-1); ndim=%d" % arr.ndim)
    n_eff = int(arr.shape[0]) if n_eff is None else int(n_eff)
    level = conformal_level(n_eff, alpha_each)
    return np.array([empirical_qhat(arr[:, j], level) for j in range(arr.shape[1])], dtype=np.float64)


def qhat_bonferroni(pair_s: np.ndarray, alpha: float = ALPHA, n_eff: Optional[int] = None) -> np.ndarray:
    """Per-slot qhat with Bonferroni correction over ``K-1`` rank slots."""
    m = np.asarray(pair_s).shape[1]
    return qhat_per_slot(pair_s, alpha_bonferroni(alpha, m), n_eff=n_eff)


def qhat_sidak(pair_s: np.ndarray, alpha: float = ALPHA, n_eff: Optional[int] = None) -> np.ndarray:
    """Per-slot qhat with Sidak correction over ``K-1`` rank slots."""
    m = np.asarray(pair_s).shape[1]
    return qhat_per_slot(pair_s, alpha_sidak(alpha, m), n_eff=n_eff)


def qhat_uncorrected(pair_s: np.ndarray, alpha: float = ALPHA, n_eff: Optional[int] = None) -> np.ndarray:
    """Negative control only (PC22-2). No multiplicity correction."""
    return qhat_per_slot(pair_s, float(alpha), n_eff=n_eff)


# ---------------------------------------------------------------------------
# 3. Kernel layer -- coverage and acceptance
# ---------------------------------------------------------------------------

def coverage_simultaneous(pair_s: np.ndarray, qhat: np.ndarray | float) -> float:
    """``P(for all j: s_j <= qhat_j)`` -- the family-wise statement."""
    arr = np.asarray(pair_s, dtype=np.float64)
    q = np.broadcast_to(np.asarray(qhat, dtype=np.float64), arr.shape)
    return float((arr <= q).all(axis=1).mean())


def coverage_pointwise(pair_s: np.ndarray, qhat: np.ndarray | float) -> np.ndarray:
    """Per-slot coverage, shape ``(K-1,)``. Report next to the family one."""
    arr = np.asarray(pair_s, dtype=np.float64)
    q = np.broadcast_to(np.asarray(qhat, dtype=np.float64), arr.shape)
    return (arr <= q).mean(axis=0)


def accept_simultaneous(m_hat_pairs: np.ndarray, qhat: np.ndarray | float, kappa: float = 1.0) -> np.ndarray:
    """Accept iff every rival is beaten by ``kappa * qhat`` of its own slot."""
    mh = np.asarray(m_hat_pairs, dtype=np.float64)
    q = np.broadcast_to(np.asarray(qhat, dtype=np.float64), mh.shape)
    return (mh >= float(kappa) * q).all(axis=1)


def certified_argmin(
    y_hat: np.ndarray,
    qhat: np.ndarray | float,
    kappa: float = 1.0,
    fill: int = -1,
) -> np.ndarray:
    """Return ``a1`` where the simultaneous certificate holds, else ``fill``."""
    order = top_k_by_twin(y_hat)
    ok = accept_simultaneous(pair_margins_hat(y_hat), qhat, kappa=kappa)
    out = np.full(order.shape[0], int(fill), dtype=np.int64)
    out[ok] = order[ok, 0]
    return out


def decision_failure(m_true_pairs: np.ndarray) -> np.ndarray:
    """True when some rival is actually better: ``min_j m_true_j < 0``."""
    return np.asarray(m_true_pairs, dtype=np.float64).min(axis=1) < 0.0


# ---------------------------------------------------------------------------
# 4. Labelled layer -- three-label rule (G22-14)
# ---------------------------------------------------------------------------

LEVELS = ("per-link", "per-path", "margin", "simultaneous")
SCALES = ("delay_ms", "cost_ms", "dimensionless")


@dataclass(frozen=True)
class Labelled:
    """A number or array that cannot be read without its three tags."""

    value: Any
    scale: str
    level: str
    rowset: str
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.scale not in SCALES:
            raise ValueError("scale khong hop le: %r; phai thuoc %s" % (self.scale, SCALES))
        if self.level not in LEVELS:
            raise ValueError("level khong hop le: %r; phai thuoc %s" % (self.level, LEVELS))
        if not isinstance(self.rowset, str) or not self.rowset.strip():
            raise ValueError("rowset phai la chuoi mo ta tap hang, khong duoc rong")

    def as_dict(self) -> Dict[str, Any]:
        value = self.value
        if isinstance(value, np.ndarray):
            value = value.tolist()
        elif isinstance(value, (np.floating, np.integer)):
            value = value.item()
        out = {"value": value, "scale": self.scale, "level": self.level, "rowset": self.rowset}
        if self.extra:
            out["extra"] = dict(self.extra)
        return out


def labelled_scores(
    y_true: np.ndarray,
    y_hat: np.ndarray,
    rowset: str,
    scale: str = SCALE_COST,
) -> Dict[str, Labelled]:
    """All Phase 22 scores for one row set, each carrying its three tags."""
    pair_s = pair_scores(y_true, y_hat)
    return {
        "s_margin": Labelled(pair_s[:, 0], scale, "margin", rowset),
        "s_pair": Labelled(pair_s, scale, "margin", rowset, {"axis1": "twin rank slot 2..K"}),
        "s_sim": Labelled(pair_s.max(axis=1), scale, "simultaneous", rowset),
        "s_maxabs": Labelled(s_maxabs(y_true, y_hat), scale, "per-path", rowset),
    }


def labelled_qhat(
    pair_s: np.ndarray,
    procedure: str,
    alpha: float = ALPHA,
    n_eff: Optional[int] = None,
    rowset: str = "calib",
    scale: str = SCALE_COST,
) -> Labelled:
    """Calibrate with one of the four FWER procedures and tag the result."""
    arr = np.asarray(pair_s, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError("pair_s phai co shape (n, K-1); ndim=%d" % arr.ndim)
    m = int(arr.shape[1])
    table = {
        "maxscore": (lambda: qhat_maxscore(arr.max(axis=1), alpha, n_eff), "simultaneous", alpha),
        "bonferroni": (lambda: qhat_bonferroni(arr, alpha, n_eff), "simultaneous", alpha_bonferroni(alpha, m)),
        "sidak": (lambda: qhat_sidak(arr, alpha, n_eff), "simultaneous", alpha_sidak(alpha, m)),
        "uncorrected": (lambda: qhat_uncorrected(arr, alpha, n_eff), "margin", float(alpha)),
    }
    if procedure not in table:
        raise ValueError("procedure phai thuoc %s; nhan %r" % (sorted(table), procedure))
    fn, level, alpha_each = table[procedure]
    return Labelled(
        fn(),
        scale,
        level,
        rowset,
        {
            "procedure": procedure,
            "alpha_family": float(alpha),
            "alpha_each": float(alpha_each),
            "m_comparisons": m,
            "n_eff": int(arr.shape[0]) if n_eff is None else int(n_eff),
            "negative_control": procedure == "uncorrected",
        },
    )
