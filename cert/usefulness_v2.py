#!/usr/bin/env python3
"""Phase 21R / Lesson 21R.6 -- risk-acceptance usefulness curve.

Lesson 21R.5 establishes a marginal conformal coverage contract.  This module
asks whether that contract is useful for selective routing decisions:

    accept <=> m_hat >= kappa * q_hat(age_bin)

Use "coverage" only for conformal coverage.  The selective-prediction x-axis is
an acceptance rate.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Sequence

import numpy as np
import pandas as pd

from cert.conformal_v2 import conformal_level, empirical_qhat, split_blocks


ALPHA = 0.10
KAPPA_GRID = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0)
MIN_ACCEPT_ROWS = 100
H7_MIN_ACCEPT = 0.10
H7_MAX_RISK_RATIO = 0.50
G12_MAX_ACCEPT = 0.90
DEGENERATE_ERR = 0.01
N_BOOT = 1000


def _git(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def _json_clean(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _json_clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_clean(v) for v in value]
    if isinstance(value, tuple):
        return [_json_clean(v) for v in value]
    if isinstance(value, np.generic):
        return _json_clean(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        if np.isposinf(value):
            return "inf"
        if np.isneginf(value):
            return "-inf"
        return None
    return value


def _infer_cell(path: str) -> str:
    name = os.path.basename(path)
    match = re.match(r"calib_set_(.+)_([0-9]+\.[0-9]+)(?:_V[0-9]+)?\.parquet$", name)
    if not match:
        return "unknown"
    return "%s@%.3f" % (match.group(1), float(match.group(2)))


def fit_qhat(
    df: pd.DataFrame,
    is_calib: np.ndarray,
    score: str = "s_margin",
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
) -> Dict[int, float]:
    """Fit Variant-B q_hat per age bin using calibration blocks only."""
    d = df.assign(_calib=np.asarray(is_calib, dtype=bool))
    qhat: Dict[int, float] = {}
    for group, sub in d.groupby(bin_col, sort=True):
        c = sub[sub["_calib"]]
        level = conformal_level(int(c["block_id"].nunique()), alpha)
        qhat[int(group)] = (
            float("inf")
            if level is None
            else empirical_qhat(c[score].to_numpy(np.float64), level)
        )
    return qhat


def _thresholds(test: pd.DataFrame, qhat: Mapping[int, float], bin_col: str, kappa: float) -> np.ndarray:
    qh = test[bin_col].map(qhat).to_numpy(np.float64)
    if float(kappa) == 0.0:
        return np.full(len(test), -np.inf, dtype=np.float64)
    return float(kappa) * qh


def risk_coverage(
    test: pd.DataFrame,
    qhat: Mapping[int, float],
    bin_col: str = "z_bin",
    kappas: Sequence[float] = KAPPA_GRID,
) -> pd.DataFrame:
    """Return one row per kappa, evaluated on test blocks only."""
    mh = test["m_hat"].to_numpy(np.float64)
    wrong = test["wrong"].to_numpy(bool)
    regret = test["regret"].to_numpy(np.float64)
    d_sla = (test["viol_twin"].astype(float) - test["viol_star"].astype(float)).to_numpy(np.float64)
    m_true = test["m_true"].to_numpy(np.float64)
    s_margin = test["s_margin"].to_numpy(np.float64)
    qh = test[bin_col].map(qhat).to_numpy(np.float64)

    rows = []
    for kappa in kappas:
        acc = mh >= _thresholds(test, qhat, bin_col, float(kappa))
        n_acc = int(acc.sum())
        rec: Dict[str, Any] = {
            "kappa": float(kappa),
            "acceptance_rate": float(acc.mean()),
            "n_accept": n_acc,
        }
        if n_acc >= MIN_ACCEPT_ROWS:
            rec.update(
                {
                    "err_given_accept": float(wrong[acc].mean()),
                    "d_sla_given_accept": float(d_sla[acc].mean()),
                    "regret_given_accept": float(regret[acc].mean()),
                    "p_mtrue_neg_given_accept": float((m_true[acc] < 0.0).mean()),
                    "coverage_violation_given_accept": float((s_margin[acc] > qh[acc]).mean()),
                }
            )
        else:
            rec.update(
                {
                    "err_given_accept": float("nan"),
                    "d_sla_given_accept": float("nan"),
                    "regret_given_accept": float("nan"),
                    "p_mtrue_neg_given_accept": float("nan"),
                    "coverage_violation_given_accept": float("nan"),
                }
            )
        rec["err_given_reject"] = float(wrong[~acc].mean()) if (~acc).any() else float("nan")
        rows.append(rec)
    return pd.DataFrame(rows)


def post_selection_diagnostics(
    test: pd.DataFrame,
    qhat: Mapping[int, float],
    bin_col: str = "z_bin",
    kappa: float = 1.0,
    alpha: float = ALPHA,
) -> Dict[str, Any]:
    """Report conformal coverage after selection and operational certification."""
    mh = test["m_hat"].to_numpy(np.float64)
    qh = test[bin_col].map(qhat).to_numpy(np.float64)
    s_margin = test["s_margin"].to_numpy(np.float64)
    s_signed = test["s_signed"].to_numpy(np.float64) if "s_signed" in test else test["m_hat"].to_numpy(np.float64) - test["m_true"].to_numpy(np.float64)
    m_true = test["m_true"].to_numpy(np.float64)
    acc = mh >= _thresholds(test, qhat, bin_col, float(kappa))
    if not acc.any():
        return {
            "kappa": float(kappa),
            "alpha": float(alpha),
            "n_accept": 0,
            "violation_marginal": float((s_margin > qh).mean()),
            "violation_given_accept": float("nan"),
            "coverage_holds_after_selection": None,
            "certification_holds_after_selection": None,
        }
    v_marg = float((s_margin > qh).mean())
    v_acc = float((s_margin[acc] > qh[acc]).mean())
    p_neg_marg = float((m_true < 0.0).mean())
    p_neg_acc = float((m_true[acc] < 0.0).mean())
    return {
        "kappa": float(kappa),
        "alpha": float(alpha),
        "n_accept": int(acc.sum()),
        "violation_marginal": v_marg,
        "violation_given_accept": v_acc,
        "violation_inflation": float(v_acc / max(v_marg, 1e-12)),
        "coverage_holds_after_selection": bool(v_acc <= alpha),
        "p_mtrue_neg_marginal": p_neg_marg,
        "p_mtrue_neg_given_accept": p_neg_acc,
        "certification_holds_after_selection": bool(p_neg_acc <= alpha),
        "p_signed_failure_given_accept": float((s_signed[acc] > mh[acc]).mean()),
        "median_slack_given_accept": float(np.median(mh[acc] - qh[acc])),
        "corr_score_vs_gap": float(np.corrcoef(s_margin, mh)[0, 1]),
        "note": (
            "Conformal marginal coverage does not automatically hold after "
            "selection. The operational certificate can still hold because "
            "accepted rows have m_hat >= q_hat and failure requires s_signed > m_hat."
        ),
    }


def evaluate_H7(
    curve: pd.DataFrame,
    anchor_err: float,
    min_accept: float = H7_MIN_ACCEPT,
    max_ratio: float = H7_MAX_RISK_RATIO,
) -> Dict[str, Any]:
    """H7: some point has acceptance >= min_accept and risk <= max_ratio*anchor."""
    if float(anchor_err) < DEGENERATE_ERR:
        return {
            "pass": None,
            "reason": "o suy bien (anchor_err < %.3f): H7 khong ap dung" % DEGENERATE_ERR,
            "anchor_err": float(anchor_err),
        }
    ok = curve[
        (curve["acceptance_rate"] >= float(min_accept))
        & (curve["err_given_accept"] <= float(max_ratio) * float(anchor_err))
    ]
    out: Dict[str, Any] = {
        "anchor_err": float(anchor_err),
        "threshold_risk": float(max_ratio) * float(anchor_err),
        "min_acceptance_rate": float(min_accept),
        "max_risk_ratio": float(max_ratio),
        "n_points": int(len(ok)),
        "pass": bool(len(ok) > 0),
    }
    if len(ok):
        best = ok.loc[ok["acceptance_rate"].idxmax()]
        out["best_point"] = {
            "kappa": float(best["kappa"]),
            "acceptance_rate": float(best["acceptance_rate"]),
            "err_given_accept": float(best["err_given_accept"]),
            "risk_ratio": float(best["err_given_accept"] / float(anchor_err)),
        }
    return out


def evaluate_G12(curve: pd.DataFrame, kappa: float = 1.0, max_accept: float = G12_MAX_ACCEPT) -> Dict[str, Any]:
    row = curve[np.isclose(curve["kappa"], float(kappa))]
    if not len(row):
        return {"pass": None, "reason": "missing kappa", "kappa": float(kappa)}
    acceptance = float(row["acceptance_rate"].iloc[0])
    return {"kappa": float(kappa), "acceptance_rate": acceptance, "pass": bool(acceptance <= max_accept)}


def evaluate_PC1(curve: pd.DataFrame, anchor_err: float, kappa: float = 1.0) -> Dict[str, Any]:
    """Positive-control gate for degenerate cells."""
    row = curve[np.isclose(curve["kappa"], float(kappa))]
    if float(anchor_err) >= DEGENERATE_ERR:
        return {"pass": None, "reason": "khong phai o suy bien", "anchor_err": float(anchor_err)}
    if not len(row):
        return {"pass": False, "reason": "missing kappa", "anchor_err": float(anchor_err)}
    acceptance = float(row["acceptance_rate"].iloc[0])
    err = float(row["err_given_accept"].iloc[0])
    return {
        "kappa": float(kappa),
        "anchor_err": float(anchor_err),
        "acceptance_rate": acceptance,
        "err_given_accept": err,
        "pass": bool(acceptance >= 0.99 and err == 0.0),
    }


def discrimination(curve: pd.DataFrame, kappa: float = 1.0) -> Dict[str, Any]:
    row = curve[np.isclose(curve["kappa"], float(kappa))]
    if not len(row):
        return {}
    err_accept = float(row["err_given_accept"].iloc[0])
    err_reject = float(row["err_given_reject"].iloc[0])
    return {
        "kappa": float(kappa),
        "err_given_accept": err_accept,
        "err_given_reject": err_reject,
        "ratio_reject_over_accept": float(err_reject / err_accept) if err_accept > 0.0 else float("inf"),
    }


def aurc(curve: pd.DataFrame) -> float:
    """Area under risk-acceptance curve. Lower is better."""
    d = curve.dropna(subset=["err_given_accept"]).sort_values("acceptance_rate")
    if len(d) < 2:
        return float("nan")
    return float(np.trapezoid(d["err_given_accept"], d["acceptance_rate"]))


def bootstrap_point(
    test: pd.DataFrame,
    qhat: Mapping[int, float],
    kappa: float,
    bin_col: str = "z_bin",
    n_boot: int = N_BOOT,
    seed: int = 6106,
) -> Dict[str, Any]:
    """Block bootstrap CI for acceptance rate and err|accept at one kappa."""
    threshold = _thresholds(test, qhat, bin_col, float(kappa))
    acc = test["m_hat"].to_numpy(np.float64) >= threshold
    tmp = pd.DataFrame(
        {
            "block_id": test["block_id"].to_numpy(),
            "n": np.ones(len(test), dtype=np.float64),
            "n_acc": acc.astype(np.float64),
            "n_wrong_acc": (acc & test["wrong"].to_numpy(bool)).astype(np.float64),
        }
    )
    by_block = tmp.groupby("block_id", sort=True)[["n", "n_acc", "n_wrong_acc"]].sum().to_numpy(np.float64)
    rng = np.random.default_rng(int(seed))
    acceptance = np.empty(int(n_boot), dtype=np.float64)
    risk = np.empty(int(n_boot), dtype=np.float64)
    for i in range(int(n_boot)):
        sample = by_block[rng.integers(0, len(by_block), len(by_block))].sum(axis=0)
        acceptance[i] = sample[1] / sample[0]
        risk[i] = sample[2] / sample[1] if sample[1] > 0.0 else np.nan
    return {
        "kappa": float(kappa),
        "n_boot": int(n_boot),
        "acceptance_ci95": [float(x) for x in np.nanpercentile(acceptance, [2.5, 97.5])],
        "err_given_accept_ci95": [float(x) for x in np.nanpercentile(risk, [2.5, 97.5])],
    }


def c2_mapping(qhat: Mapping[int, float], eps_regret: float, curve: pd.DataFrame) -> Dict[str, Any]:
    """Map C2 regret tolerance to kappa and report whether it binds at kappa=1."""
    kappas = {
        int(g): max(0.0, 1.0 - float(eps_regret) / float(q))
        if np.isfinite(float(q)) and float(q) > 0.0
        else 0.0
        for g, q in qhat.items()
    }
    row = curve[np.isclose(curve["kappa"], 1.0)]
    regret_k1 = float(row["regret_given_accept"].iloc[0]) if len(row) else float("nan")
    return {
        "eps_regret_ms": float(eps_regret),
        "kappa_C2_by_bin": kappas,
        "all_zero": bool(all(v == 0.0 for v in kappas.values())),
        "regret_given_accept_at_kappa1": regret_k1,
        "nonbinding_at_kappa1": bool(np.isfinite(regret_k1) and regret_k1 <= float(eps_regret)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calib", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--anchor-err", type=float, required=True)
    parser.add_argument("--eps-regret", type=float, default=None)
    parser.add_argument("--alpha", type=float, default=ALPHA)
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    args = parser.parse_args()

    df = pd.read_parquet(args.calib)
    is_calib = split_blocks(df["block_id"].to_numpy())
    qhat = fit_qhat(df, is_calib, alpha=float(args.alpha))
    test = df[~is_calib].copy()
    curve = risk_coverage(test, qhat)
    anchor_test = float(test["wrong"].mean())
    if anchor_test > 0.0:
        curve["err_ratio_to_test_anchor"] = curve["err_given_accept"] / anchor_test
    else:
        curve["err_ratio_to_test_anchor"] = np.nan

    out: Dict[str, Any] = {
        "cell": _infer_cell(args.calib),
        "qhat": qhat,
        "n_test_rows": int(len(test)),
        "anchor_err_declared": float(args.anchor_err),
        "anchor_err_on_test": anchor_test,
        "curve": curve.to_dict(orient="records"),
        "H7": evaluate_H7(curve, anchor_test),
        "G12": evaluate_G12(curve),
        "PC1": evaluate_PC1(curve, anchor_test),
        "discrimination_at_kappa_0.25": discrimination(curve, 0.25),
        "discrimination_at_kappa_1.0": discrimination(curve, 1.0),
        "discrimination_at_kappa_2.0": discrimination(curve, 2.0),
        "aurc": aurc(curve),
        "post_selection": post_selection_diagnostics(test, qhat, alpha=float(args.alpha)),
        "bootstrap_kappa_1.0": bootstrap_point(test, qhat, 1.0, n_boot=int(args.n_boot)),
        "bootstrap_kappa_0.5": bootstrap_point(test, qhat, 0.5, n_boot=int(args.n_boot)),
        "degenerate_cell": bool(anchor_test < DEGENERATE_ERR),
        "provenance": {
            "script": "cert/usefulness_v2.py",
            "calib": args.calib,
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "alpha": float(args.alpha),
            "n_boot": int(args.n_boot),
        },
    }
    if args.eps_regret is not None:
        out["C2_mapping"] = c2_mapping(qhat, float(args.eps_regret), curve)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(_json_clean(out), f, indent=1, sort_keys=True)
        f.write("\n")

    print(curve.to_string(index=False))
    print(
        json.dumps(
            _json_clean(
                {
                    "cell": out["cell"],
                    "H7": out["H7"],
                    "G12": out["G12"],
                    "PC1": out["PC1"],
                    "discrimination_at_kappa_1.0": out["discrimination_at_kappa_1.0"],
                    "aurc": out["aurc"],
                    "post_selection": out["post_selection"],
                    "bootstrap_kappa_1.0": out["bootstrap_kappa_1.0"],
                    "bootstrap_kappa_0.5": out["bootstrap_kappa_0.5"],
                    "C2_mapping": out.get("C2_mapping"),
                }
            ),
            indent=1,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
