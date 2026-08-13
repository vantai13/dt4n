#!/usr/bin/env python3
"""Phase 22 / Lesson 22.4 -- validity AFTER the acceptance decision.

21R guarantees ``P(s > q_hat) <= alpha`` marginally.  It says nothing about
``P(s > q_hat | accept)``, and the two differ because the acceptance rule keys
on ``m_hat``, which is positively correlated with the score.

Three repair procedures, all of which reduce to 21R at ``kappa = 0`` where it
matters:

* ``fcr``       -- Benjamini-Yekutieli style: calibrate at
                   ``alpha * P(accept)``.  This is self-referential, so it is
                   solved as a fixed point.
* ``mondrian``  -- absorb ``m_hat`` into the Mondrian taxonomy.
* ``selective`` -- calibrate on the selected calibration rows only.  This is a
                   fixed point over a set, and can enter a finite limit cycle.

Every acceptance probability used inside a fixed point is measured on
calibration rows.  Using test rows would leak the evaluation set into the
calibration rule.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

from cert.conformal_v2 import conformal_level, empirical_qhat
from cert.simultaneous_score import ALPHA


MAX_ITER = 50
TOL = 1e-9
KAPPA_GRID = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0)
PROCEDURES = ("none", "fcr", "mondrian", "selective")


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
    if isinstance(value, np.ndarray):
        return [_json_clean(x) for x in value.tolist()]
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
    match = re.match(r"calib_set_v3_(.+)_([0-9]+\.[0-9]+)(?:_V[0-9]+)?\.parquet$", name)
    if not match:
        return "unknown"
    suffix = "_V3" if "_V3.parquet" in name else ""
    return "%s@%.3f%s" % (match.group(1), float(match.group(2)), suffix)


def _norm_key(key: Any, single: bool) -> Any:
    if single and isinstance(key, tuple):
        return key[0]
    if not single and not isinstance(key, tuple):
        return (key,)
    return key


def _plain_key(key: Any) -> Any:
    if isinstance(key, tuple):
        return tuple(int(x) if isinstance(x, (np.integer, int)) else x for x in key)
    if isinstance(key, (np.integer, int)):
        return int(key)
    return key


def _qhat_by_group(
    calib: pd.DataFrame,
    score: str,
    keys: Sequence[str],
    alpha_by_key: Mapping[Any, float],
) -> Dict[Any, float]:
    """One conformal quantile per group key, each at its own alpha."""
    keys = list(keys)
    out: Dict[Any, float] = {}
    single = len(keys) == 1
    for key, sub in calib.groupby(keys, sort=True):
        key = _norm_key(key, single)
        n_eff = int(sub["block_id"].nunique())
        alpha = float(alpha_by_key[key])
        lvl = conformal_level(n_eff, alpha)
        out[key] = float("inf") if lvl is None else empirical_qhat(sub[score].to_numpy(np.float64), lvl)
    return out


def _map_qhat(df: pd.DataFrame, keys: Sequence[str], qhat: Mapping[Any, float]) -> np.ndarray:
    keys = list(keys)
    if len(keys) == 1:
        mapping = {int(k): float(v) for k, v in qhat.items()}
        return df[keys[0]].map(mapping).to_numpy(np.float64)
    idx = pd.MultiIndex.from_frame(df[keys])
    return pd.Series(qhat).reindex(idx).to_numpy(np.float64)


def _accept(df: pd.DataFrame, q: np.ndarray, kappa: float) -> np.ndarray:
    return df["m_hat"].to_numpy(np.float64) >= float(kappa) * np.asarray(q, dtype=np.float64)


def fit_none(
    calib: pd.DataFrame,
    kappa: float,
    score: str = "s_margin",
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
) -> Dict[str, Any]:
    """The 21R marginal conformal baseline."""
    groups = sorted(calib[bin_col].unique())
    alpha_g = {g: float(alpha) for g in groups}
    q = _qhat_by_group(calib, score, [bin_col], alpha_g)
    return {
        "procedure": "none",
        "qhat": {int(g): float(q[g]) for g in groups},
        "keys": [bin_col],
        "converged": True,
        "degenerate": False,
        "cycle_len": 1,
        "n_iter": 1,
        "trace": [],
    }


def fit_fcr(
    calib: pd.DataFrame,
    kappa: float,
    score: str = "s_margin",
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
    m_family: int = 1,
    p_scope: str = "global",
    max_iter: int = MAX_ITER,
) -> Dict[str, Any]:
    """Iterate ``alpha' = alpha * P(accept) / m`` until qhat stops moving."""
    if p_scope not in ("global", "per_bin"):
        raise ValueError("p_scope phai la 'global' hoac 'per_bin'")
    groups = sorted(calib[bin_col].unique())
    alpha_g = {g: float(alpha) for g in groups}
    q_prev = None
    trace: List[Dict[str, Any]] = []

    for it in range(int(max_iter)):
        q = _qhat_by_group(calib, score, [bin_col], alpha_g)
        acc = _accept(calib, _map_qhat(calib, [bin_col], q), kappa)
        zb = calib[bin_col].to_numpy()
        p_bin = {int(g): float(acc[zb == g].mean()) for g in groups}
        p_all = float(acc.mean())
        trace.append(
            {
                "iter": int(it),
                "qhat": {int(g): float(q[g]) for g in groups},
                "alpha_prime": {int(g): float(alpha_g[g]) for g in groups},
                "p_accept_calib": p_bin,
                "p_accept_global": p_all,
            }
        )

        collapsed = [int(g) for g in groups if not np.isfinite(q[g])]
        if collapsed:
            return {
                "procedure": "fcr",
                "qhat": {int(g): float(q[g]) for g in groups},
                "keys": [bin_col],
                "converged": False,
                "degenerate": True,
                "collapsed_bins": collapsed,
                "n_iter": int(it) + 1,
                "p_scope": p_scope,
                "trace": trace,
            }

        if q_prev is not None:
            rel = max(abs(q[g] - q_prev[g]) / max(q_prev[g], 1e-12) for g in groups)
            if rel < TOL:
                return {
                    "procedure": "fcr",
                    "qhat": {int(g): float(q[g]) for g in groups},
                    "keys": [bin_col],
                    "converged": True,
                    "degenerate": False,
                    "collapsed_bins": [],
                    "cycle_len": 1,
                    "n_iter": int(it) + 1,
                    "p_scope": p_scope,
                    "trace": trace,
                }
        q_prev = q

        if p_scope == "global":
            alpha_g = {g: max(float(alpha) * p_all / int(m_family), 1e-12) for g in groups}
        else:
            alpha_g = {g: max(float(alpha) * p_bin[int(g)] / int(m_family), 1e-12) for g in groups}

    return {
        "procedure": "fcr",
        "qhat": {int(g): float(max(t["qhat"][int(g)] for t in trace)) for g in groups},
        "keys": [bin_col],
        "converged": False,
        "degenerate": False,
        "collapsed_bins": [],
        "cycle_len": 0,
        "n_iter": int(max_iter),
        "p_scope": p_scope,
        "trace": trace,
    }


def fit_mondrian(
    calib: pd.DataFrame,
    kappa: float,
    score: str = "s_margin",
    keys: Sequence[str] = ("z_bin", "m_hat_bin"),
    alpha: float = ALPHA,
) -> Dict[str, Any]:
    """Condition on the variable that drives selection: ``m_hat_bin``."""
    keys = list(keys)
    alpha_g = {
        _norm_key(k, len(keys) == 1): float(alpha)
        for k, _sub in calib.groupby(keys, sort=True)
    }
    q = _qhat_by_group(calib, score, keys, alpha_g)
    q = {_plain_key(_norm_key(k, len(keys) == 1)): float(v) for k, v in q.items()}
    n_blk = {
        str(_plain_key(_norm_key(k, len(keys) == 1))): int(sub["block_id"].nunique())
        for k, sub in calib.groupby(keys, sort=True)
    }
    return {
        "procedure": "mondrian",
        "qhat": {str(k): float(v) for k, v in q.items()},
        "_qhat_raw": q,
        "keys": keys,
        "converged": True,
        "degenerate": False,
        "cycle_len": 1,
        "n_iter": 1,
        "n_calib_blocks": n_blk,
        "trace": [],
    }


def fit_selective(
    calib: pd.DataFrame,
    kappa: float,
    score: str = "s_margin",
    bin_col: str = "z_bin",
    alpha: float = ALPHA,
    max_iter: int = MAX_ITER,
    min_blocks: int = 9,
) -> Dict[str, Any]:
    """Calibrate on ``{m_hat >= kappa * qhat}``, the set the procedure acts on."""
    groups = sorted(calib[bin_col].unique())
    alpha_g = {g: float(alpha) for g in groups}
    q = _qhat_by_group(calib, score, [bin_col], alpha_g)
    trace: List[Dict[str, Any]] = []
    seen: Dict[Tuple[float, ...], int] = {}

    for it in range(int(max_iter)):
        sel = _accept(calib, _map_qhat(calib, [bin_col], q), kappa)
        sub = calib[sel]
        n_blk = {int(g): int(sub[sub[bin_col] == g]["block_id"].nunique()) for g in groups}
        if min(n_blk.values()) < int(min_blocks):
            return {
                "procedure": "selective",
                "qhat": {int(g): float(q[g]) for g in groups},
                "keys": [bin_col],
                "converged": False,
                "n_iter": int(it),
                "degenerate": True,
                "cycle_len": 0,
                "n_calib_blocks": n_blk,
                "trace": trace,
            }

        q_new = _qhat_by_group(sub, score, [bin_col], alpha_g)
        sig = tuple(round(float(q_new[g]), 12) for g in groups)
        trace.append(
            {
                "iter": int(it),
                "qhat": {int(g): float(q_new[g]) for g in groups},
                "n_selected_blocks": n_blk,
                "frac_selected": float(sel.mean()),
            }
        )

        rel = max(abs(q_new[g] - q[g]) / max(q[g], 1e-12) for g in groups)
        if rel < TOL:
            return {
                "procedure": "selective",
                "qhat": {int(g): float(q_new[g]) for g in groups},
                "keys": [bin_col],
                "converged": True,
                "cycle_len": 1,
                "n_iter": int(it) + 1,
                "degenerate": False,
                "n_calib_blocks": n_blk,
                "trace": trace,
            }

        if sig in seen:
            first = seen[sig]
            cycle_states = [t["qhat"] for t in trace[first:-1]]
            if not cycle_states:
                cycle_states = [trace[-1]["qhat"]]
            return {
                "procedure": "selective",
                "qhat": {int(g): float(max(c[int(g)] for c in cycle_states)) for g in groups},
                "keys": [bin_col],
                "converged": True,
                "cycle_len": len(cycle_states),
                "n_iter": int(it) + 1,
                "degenerate": False,
                "n_calib_blocks": n_blk,
                "trace": trace,
            }

        seen[sig] = len(trace) - 1
        q = q_new

    return {
        "procedure": "selective",
        "qhat": {int(g): float(q[g]) for g in groups},
        "keys": [bin_col],
        "converged": False,
        "cycle_len": 0,
        "n_iter": int(max_iter),
        "degenerate": False,
        "trace": trace,
    }


def evaluate(
    test: pd.DataFrame,
    fit: Mapping[str, Any],
    kappa: float,
    score: str = "s_margin",
    alpha: float = ALPHA,
) -> Dict[str, Any]:
    """Evaluate post-selection coverage and operational decision failure."""
    keys = list(fit["keys"])
    raw = fit.get("_qhat_raw", fit["qhat"])
    if len(keys) == 1:
        q = test[keys[0]].map({int(k): float(v) for k, v in raw.items()}).to_numpy(np.float64)
    else:
        q = _map_qhat(test, keys, raw)
    s = test[score].to_numpy(np.float64)
    mh = test["m_hat"].to_numpy(np.float64)
    mt = test["m_true"].to_numpy(np.float64)
    acc = mh >= float(kappa) * q
    viol = s > q
    n_acc = int(acc.sum())
    viol_acc = float(viol[acc].mean()) if n_acc else float("nan")
    viol_marg = float(viol.mean())
    return {
        "kappa": float(kappa),
        "qhat": {str(k): float(v) for k, v in raw.items()},
        "acceptance": float(acc.mean()),
        "violation_marginal": viol_marg,
        "violation_given_accept": viol_acc,
        "inflation": float(viol_acc / viol_marg) if n_acc and viol_marg > 0.0 else float("nan"),
        "decision_failure_given_accept": float((mt[acc] < 0.0).mean()) if n_acc else float("nan"),
        "decision_failure_marginal": float((mt < 0.0).mean()),
        "median_slack_given_accept": float(np.median((mh - q)[acc])) if n_acc else float("nan"),
        "n_accept": n_acc,
        "converged": bool(fit.get("converged", True)),
        "n_iter": int(fit.get("n_iter", 1)),
        "degenerate": bool(fit.get("degenerate", False)),
        "cycle_len": int(fit.get("cycle_len", 1)),
        "collapsed_bins": list(fit.get("collapsed_bins", [])),
        "pass_post_selection": bool(n_acc and viol_acc <= float(alpha) + 1e-12),
        "scale": "cost_ms",
        "level": "margin",
        "rowset": "test rows",
    }


FITTERS: Dict[str, Callable[..., Dict[str, Any]]] = {
    "none": fit_none,
    "fcr": fit_fcr,
    "mondrian": fit_mondrian,
    "selective": fit_selective,
}


def run_grid(
    df: pd.DataFrame,
    procedures: Sequence[str] = PROCEDURES,
    kappas: Sequence[float] = KAPPA_GRID,
    score: str = "s_margin",
    alpha: float = ALPHA,
) -> Dict[str, Any]:
    """Fit every procedure on calibration rows and evaluate on test rows."""
    if "is_calib" not in df.columns:
        raise ValueError("can cot is_calib")
    calib = df[df["is_calib"]]
    test = df[~df["is_calib"]]
    out: Dict[str, Any] = {p: [] for p in procedures}
    fits: Dict[str, Dict[str, Any]] = {p: {} for p in procedures}
    for proc in procedures:
        if proc not in FITTERS:
            raise ValueError("procedure phai thuoc %s; nhan %r" % (PROCEDURES, proc))
        for kappa in kappas:
            fit = FITTERS[proc](calib, float(kappa), score=score, alpha=alpha)
            ev = evaluate(test, fit, float(kappa), score=score, alpha=alpha)
            out[proc].append(ev)
            fits[proc]["%.3g" % float(kappa)] = fit

    gates = {}
    k1 = {p: next(r for r in out[p] if abs(float(r["kappa"]) - 1.0) < 1e-12) for p in procedures}
    if {"fcr", "mondrian", "selective"} <= set(procedures):
        gates["G22_6_post_selection_valid_at_kappa1"] = bool(
            all(k1[p]["violation_given_accept"] <= float(alpha) for p in ("fcr", "mondrian", "selective"))
        )
        gates["G22_7_fixed_points_terminate"] = bool(
            fits["fcr"]["1"]["converged"] and fits["selective"]["1"]["converged"]
        )
    if "none" in procedures:
        gates["NC22_2_kappa0_reduces_to_21R"] = bool(
            out["none"][0]["acceptance"] == 1.0
            and out["none"][0]["violation_given_accept"] == out["none"][0]["violation_marginal"]
        )
    if "fcr" in procedures:
        gates["FCR_per_bin_collapse_reported"] = bool(fit_fcr(calib, 1.0, score=score, alpha=alpha, p_scope="per_bin")["degenerate"])
    if "mondrian" in procedures:
        vals = {r["kappa"]: r["violation_given_accept"] for r in out["mondrian"]}
        gates["Mondrian_boundary_kappa2_fails"] = bool(
            0.5 in vals and 1.0 in vals and 2.0 in vals
            and vals[0.5] <= float(alpha)
            and vals[1.0] <= float(alpha)
            and vals[2.0] > float(alpha)
        )

    return {
        "results": out,
        "fits": fits,
        "gates": gates,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calib", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--alpha", type=float, default=ALPHA)
    parser.add_argument("--score", default="s_margin")
    args = parser.parse_args()

    df = pd.read_parquet(args.calib)
    grid = run_grid(df, score=str(args.score), alpha=float(args.alpha))
    out = {
        "cell": _infer_cell(args.calib),
        "n_rows": int(len(df)),
        "n_blocks": int(df["block_id"].nunique()),
        "n_calib_blocks": int(df.loc[df["is_calib"], "block_id"].nunique()),
        "n_test_blocks": int(df.loc[~df["is_calib"], "block_id"].nunique()),
        "alpha": float(args.alpha),
        "score": str(args.score),
        "kappas": [float(x) for x in KAPPA_GRID],
        **grid,
        "provenance": {
            "script": "cert/selective_conformal.py",
            "calib": args.calib,
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(_json_clean(out), f, indent=1, sort_keys=True)
        f.write("\n")
    print(json.dumps(_json_clean(out), indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
