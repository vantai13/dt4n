#!/usr/bin/env python3
"""Phase 22 / Lesson 22.5 -- C0/C1/C2/C3 matrix and risk-coverage curves.

Two independent axes, four corners:

                 post-selection: NO        post-selection: YES
    pair only        C0 (= 21R)                  C2
    simultaneous     C1                          C3   <- full claim

The headline of Phase 22 is not a number; it is the curve of
``err | accept`` against ``acceptance`` as ``kappa`` sweeps.  Both violation
quantities are carried side by side everywhere:

* coverage violation: ``P(s > q_hat | accept)`` -- the formal claim
* decision failure:   ``P(a_twin != a_star | accept)`` -- the operational claim
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from cert.conformal_v2 import conformal_level, empirical_qhat
from cert.selective_conformal import KAPPA_GRID, MAX_ITER, TOL
from cert.simultaneous_score import ALPHA, alpha_bonferroni, alpha_sidak


PAIR_COLS = ("s_margin",)
SIM_COLS = ("s_pair_1", "s_pair_2", "s_pair_3")
MHAT_COLS = ("m_hat_1", "m_hat_2", "m_hat_3")

CONFIGS: Dict[str, Dict[str, Any]] = {
    "C0": {"simultaneous": False, "post": "none", "label": "21R baseline"},
    "C1": {"simultaneous": True, "post": "none", "label": "simultaneous only"},
    "C2": {"simultaneous": False, "post": "mondrian", "label": "post-selection only"},
    "C3": {"simultaneous": True, "post": "mondrian", "label": "both (full claim)"},
}
POST_VARIANTS = ("none", "fcr", "mondrian", "selective")
H7_MIN_ACCEPT = 0.10
H7_MAX_RATIO = 0.50
DEGENERATE_ERR = 0.02
MATCHED_ACCEPTANCE = (0.70, 0.50, 0.30, 0.15)


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


def _plain_scalar(x: Any) -> Any:
    if isinstance(x, (np.integer, int)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        return float(x)
    return x


def _norm(key: Any) -> tuple[Any, ...]:
    if isinstance(key, tuple):
        return tuple(_plain_scalar(x) for x in key)
    return (_plain_scalar(key),)


def _score_cols(simultaneous: bool) -> tuple[str, ...]:
    return SIM_COLS if bool(simultaneous) else PAIR_COLS


def _mhat_cols(simultaneous: bool) -> tuple[str, ...]:
    return MHAT_COLS if bool(simultaneous) else ("m_hat",)


def _keys(post: str) -> list[str]:
    return ["z_bin", "m_hat_bin"] if post == "mondrian" else ["z_bin"]


def _qhat(
    calib: pd.DataFrame,
    cols: Sequence[str],
    keys: Sequence[str],
    alpha_by_key: Mapping[tuple[Any, ...], float],
) -> Dict[tuple[Any, ...], np.ndarray]:
    """One qhat vector, one entry per score column, per taxonomy cell."""
    keys = list(keys)
    out: Dict[tuple[Any, ...], np.ndarray] = {}
    for key, sub in calib.groupby(keys, sort=True):
        k = _norm(key)
        n_eff = int(sub["block_id"].nunique())
        lvl = conformal_level(n_eff, float(alpha_by_key[k]))
        if lvl is None:
            out[k] = np.full(len(cols), np.inf, dtype=np.float64)
        else:
            out[k] = np.asarray(
                [empirical_qhat(sub[c].to_numpy(np.float64), lvl) for c in cols],
                dtype=np.float64,
            )
    return out


def _row_keys(df: pd.DataFrame, keys: Sequence[str]) -> list[tuple[Any, ...]]:
    return [tuple(_plain_scalar(x) for x in row) for row in zip(*[df[k].to_numpy() for k in keys])]


def _q_rows(
    df: pd.DataFrame,
    keys: Sequence[str],
    q: Mapping[tuple[Any, ...], np.ndarray],
    n_cols: int,
) -> np.ndarray:
    miss = np.full(int(n_cols), np.inf, dtype=np.float64)
    return np.vstack([q.get(k, miss) for k in _row_keys(df, keys)])


def _accept(df: pd.DataFrame, mcols: Sequence[str], qrows: np.ndarray, kappa: float) -> np.ndarray:
    mh = df[list(mcols)].to_numpy(np.float64)
    return (mh >= float(kappa) * np.asarray(qrows, dtype=np.float64)).all(axis=1)


def _alpha_each(alpha: float, m: int, simultaneous: bool, multiplicity: str) -> float:
    if not simultaneous:
        return float(alpha)
    if multiplicity == "bonferroni":
        return alpha_bonferroni(alpha, m)
    if multiplicity == "sidak":
        return alpha_sidak(alpha, m)
    raise ValueError("multiplicity phai la 'bonferroni' hoac 'sidak'")


def fit_config(
    calib: pd.DataFrame,
    config: str,
    kappa: float,
    alpha: float = ALPHA,
    post_variant: Optional[str] = None,
    multiplicity: str = "bonferroni",
    max_iter: int = MAX_ITER,
) -> Dict[str, Any]:
    """Calibrate one corner of the matrix at one kappa."""
    if config not in CONFIGS:
        raise ValueError("config phai thuoc %s; nhan %r" % (sorted(CONFIGS), config))
    cfg = CONFIGS[config]
    sim = bool(cfg["simultaneous"])
    post = post_variant or str(cfg["post"])
    if post not in POST_VARIANTS:
        raise ValueError("post phai thuoc %s; nhan %r" % (POST_VARIANTS, post))

    cols = _score_cols(sim)
    mcols = _mhat_cols(sim)
    m = len(cols)
    keys = _keys(post)
    a_each = _alpha_each(alpha, m, sim, multiplicity)
    cells = [_norm(k) for k, _sub in calib.groupby(keys, sort=True)]
    a_by = {k: float(a_each) for k in cells}
    info: Dict[str, Any] = {
        "config": config,
        "label": str(cfg["label"]),
        "simultaneous": sim,
        "post": post,
        "multiplicity": multiplicity if sim else None,
        "alpha_family": float(alpha),
        "alpha_each_base": float(a_each),
        "keys": list(keys),
        "score_cols": list(cols),
        "mhat_cols": list(mcols),
        "kappa": float(kappa),
    }

    if post in ("none", "mondrian"):
        q = _qhat(calib, cols, keys, a_by)
        info.update(converged=True, n_iter=1, degenerate=False, cycle_len=1)

    elif post == "fcr":
        q_prev = None
        trace = []
        q = _qhat(calib, cols, keys, a_by)
        for it in range(int(max_iter)):
            q = _qhat(calib, cols, keys, a_by)
            acc = _accept(calib, mcols, _q_rows(calib, keys, q, m), kappa)
            p = float(acc.mean())
            trace.append(
                {
                    "iter": int(it),
                    "alpha_each": float(a_by[cells[0]]),
                    "p_accept_calib": p,
                    "qhat_first_cell": [float(x) for x in q[cells[0]]],
                }
            )
            if not all(np.isfinite(v).all() for v in q.values()):
                info.update(converged=False, degenerate=True, n_iter=int(it) + 1, cycle_len=0)
                break
            if q_prev is not None:
                rel = max(
                    float(np.max(np.abs(q[k] - q_prev[k]) / np.maximum(q_prev[k], 1e-12)))
                    for k in cells
                )
                if rel < TOL:
                    info.update(converged=True, degenerate=False, n_iter=int(it) + 1, cycle_len=1)
                    break
            q_prev = q
            a_by = {k: max(float(alpha) * p / int(m), 1e-12) for k in cells}
        else:
            info.update(converged=False, degenerate=False, n_iter=int(max_iter), cycle_len=0)
        info["trace"] = trace

    elif post == "selective":
        q = _qhat(calib, cols, keys, a_by)
        seen: Dict[tuple[float, ...], int] = {}
        hist: list[Dict[tuple[Any, ...], np.ndarray]] = []
        info.update(converged=False, degenerate=False, n_iter=int(max_iter), cycle_len=0)
        for it in range(int(max_iter)):
            sel = _accept(calib, mcols, _q_rows(calib, keys, q, m), kappa)
            sub = calib[sel]
            nb_raw = sub.groupby(keys, sort=True)["block_id"].nunique()
            nb = {_norm(k): int(v) for k, v in nb_raw.items()}
            if min(nb.get(k, 0) for k in cells) < 9:
                info.update(converged=False, degenerate=True, n_iter=int(it), cycle_len=0)
                break
            q_new = _qhat(sub, cols, keys, a_by)
            hist.append(q_new)
            sig = tuple(round(float(x), 12) for k in cells for x in q_new[k])
            rel = max(
                float(np.max(np.abs(q_new[k] - q[k]) / np.maximum(q[k], 1e-12)))
                for k in cells
            )
            if rel < TOL:
                q = q_new
                info.update(converged=True, degenerate=False, n_iter=int(it) + 1, cycle_len=1)
                break
            if sig in seen:
                cycle = hist[seen[sig]:]
                q = {k: np.max(np.vstack([h[k] for h in cycle]), axis=0) for k in cells}
                info.update(converged=True, degenerate=False, n_iter=int(it) + 1, cycle_len=len(cycle))
                break
            seen[sig] = len(hist) - 1
            q = q_new
        info["trace"] = [
            {"iter": i, "qhat_first_cell": [float(x) for x in h[cells[0]]]}
            for i, h in enumerate(hist)
        ]

    info["qhat"] = {str(k): [float(x) for x in v] for k, v in q.items()}
    info["_q"] = q
    return info


def evaluate_config(
    test: pd.DataFrame,
    fit: Mapping[str, Any],
    anchor_err: float,
    alpha: float = ALPHA,
) -> Dict[str, Any]:
    sim = bool(fit["simultaneous"])
    cols = _score_cols(sim)
    mcols = _mhat_cols(sim)
    keys = list(fit["keys"])
    kappa = float(fit["kappa"])
    qrows = _q_rows(test, keys, fit["_q"], len(cols))
    scores = test[list(cols)].to_numpy(np.float64)
    acc = _accept(test, mcols, qrows, kappa)
    viol = (scores > qrows).any(axis=1)
    wrong = test["wrong"].to_numpy(bool)
    mtrue = test[["m_true_1", "m_true_2", "m_true_3"]].to_numpy(np.float64)
    lose_any = mtrue.min(axis=1) < 0.0
    n = int(acc.sum())
    err_acc = float(wrong[acc].mean()) if n else float("nan")
    viol_acc = float(viol[acc].mean()) if n else float("nan")
    return {
        "config": str(fit["config"]),
        "post": str(fit["post"]),
        "kappa": kappa,
        "acceptance": float(acc.mean()),
        "err_given_accept": err_acc,
        "err_given_reject": float(wrong[~acc].mean()) if (~acc).any() else float("nan"),
        "risk_ratio": float(err_acc / anchor_err) if anchor_err > 0.0 and np.isfinite(err_acc) else float("nan"),
        "violation_marginal": float(viol.mean()),
        "violation_given_accept": viol_acc,
        "lose_any_given_accept": float(lose_any[acc].mean()) if n else float("nan"),
        "lose_any_marginal": float(lose_any.mean()),
        "n_accept": n,
        "converged": bool(fit["converged"]),
        "degenerate": bool(fit["degenerate"]),
        "n_iter": int(fit["n_iter"]),
        "cycle_len": int(fit["cycle_len"]),
        "pass_coverage": bool(n and viol_acc <= float(alpha) + 1e-12),
        "scale": "cost_ms",
        "level": "simultaneous" if sim else "margin",
        "rowset": "test rows",
    }


def evaluate_H7(
    rows: Sequence[Mapping[str, Any]],
    anchor_err: float,
    min_accept: float = H7_MIN_ACCEPT,
    max_ratio: float = H7_MAX_RATIO,
    require_coverage: bool = True,
) -> Dict[str, Any]:
    """H22-7: enough acceptance, low risk, and optionally valid coverage."""
    if anchor_err < DEGENERATE_ERR:
        return {"pass": None, "reason": "o suy bien (anchor %.4f)" % anchor_err}
    ok = [
        r for r in rows
        if float(r["acceptance"]) >= float(min_accept)
        and np.isfinite(float(r["err_given_accept"]))
        and float(r["err_given_accept"]) <= float(max_ratio) * float(anchor_err)
        and (bool(r["pass_coverage"]) or not require_coverage)
    ]
    if not ok:
        best_effort = max(
            rows,
            key=lambda r: (
                float(r["acceptance"])
                if np.isfinite(float(r["err_given_accept"]))
                and float(r["err_given_accept"]) <= float(max_ratio) * float(anchor_err)
                else -1.0
            ),
        )
        return {
            "pass": False,
            "anchor_err": float(anchor_err),
            "threshold_risk": float(max_ratio) * float(anchor_err),
            "min_accept": float(min_accept),
            "require_coverage": bool(require_coverage),
            "best_effort": dict(best_effort),
        }
    best = max(ok, key=lambda r: float(r["acceptance"]))
    return {
        "pass": True,
        "anchor_err": float(anchor_err),
        "threshold_risk": float(max_ratio) * float(anchor_err),
        "min_accept": float(min_accept),
        "require_coverage": bool(require_coverage),
        "kappa": float(best["kappa"]),
        "acceptance": float(best["acceptance"]),
        "err_given_accept": float(best["err_given_accept"]),
        "risk_ratio": float(best["risk_ratio"]),
        "n_feasible_points": int(len(ok)),
    }


def aurc(rows: Sequence[Mapping[str, Any]]) -> float:
    """Area under the risk-coverage curve. Lower is better."""
    pts = sorted(
        (float(r["acceptance"]), float(r["err_given_accept"]))
        for r in rows
        if np.isfinite(float(r["err_given_accept"]))
    )
    if len(pts) < 2:
        return float("nan")
    x = np.asarray([p[0] for p in pts], dtype=np.float64)
    y = np.asarray([p[1] for p in pts], dtype=np.float64)
    if float(x.max() - x.min()) <= 0.0:
        return float("nan")
    return float(np.trapezoid(y, x) / (x.max() - x.min()))


def risk_at_acceptance(rows: Sequence[Mapping[str, Any]], target: float) -> float:
    pts = sorted(
        (float(r["acceptance"]), float(r["err_given_accept"]))
        for r in rows
        if np.isfinite(float(r["err_given_accept"]))
    )
    if not pts:
        return float("nan")
    x = np.asarray([p[0] for p in pts], dtype=np.float64)
    y = np.asarray([p[1] for p in pts], dtype=np.float64)
    keep_x = []
    keep_y = []
    for val in sorted(set(float(v) for v in x)):
        mask = x == val
        keep_x.append(val)
        keep_y.append(float(y[mask].min()))
    x = np.asarray(keep_x, dtype=np.float64)
    y = np.asarray(keep_y, dtype=np.float64)
    if target < float(x.min()) or target > float(x.max()):
        return float("nan")
    return float(np.interp(float(target), x, y))


def _monotone(rows: Sequence[Mapping[str, Any]]) -> Dict[str, bool]:
    ordered = sorted(rows, key=lambda r: float(r["kappa"]))
    accepts = [float(r["acceptance"]) for r in ordered]
    risks = [float(r["err_given_accept"]) for r in ordered if np.isfinite(float(r["err_given_accept"]))]
    acc_ok = all(b <= a + 1e-12 for a, b in zip(accepts, accepts[1:]))
    risk_ok = all(b <= a + 1e-12 for a, b in zip(risks, risks[1:]))
    return {"acceptance_nonincreasing": bool(acc_ok), "risk_nonincreasing": bool(risk_ok)}


def _positive_finite(x: float) -> bool:
    return bool(np.isfinite(float(x)) and float(x) > 0.0)


def run_matrix(
    df: pd.DataFrame,
    kappas: Sequence[float] = KAPPA_GRID,
    alpha: float = ALPHA,
    multiplicity: str = "bonferroni",
) -> Dict[str, Any]:
    if "is_calib" not in df.columns:
        raise ValueError("can cot is_calib")
    calib = df[df["is_calib"]]
    test = df[~df["is_calib"]]
    anchor_err = float(test["wrong"].mean())
    out: Dict[str, Any] = {
        "anchor_err_on_test": anchor_err,
        "threshold_risk_H22_7": float(H7_MAX_RATIO * anchor_err),
        "configs": {},
    }

    for cfg in CONFIGS:
        rows = []
        fits: Dict[str, Any] = {}
        for kappa in kappas:
            fit = fit_config(calib, cfg, float(kappa), alpha=alpha, multiplicity=multiplicity)
            rows.append(evaluate_config(test, fit, anchor_err, alpha=alpha))
            fits["%.3g" % float(kappa)] = fit
        out["configs"][cfg] = {
            "label": CONFIGS[cfg]["label"],
            "simultaneous": bool(CONFIGS[cfg]["simultaneous"]),
            "post": CONFIGS[cfg]["post"],
            "rows": rows,
            "fits": fits,
            "H22_7": evaluate_H7(rows, anchor_err, require_coverage=True),
            "H22_7_without_coverage": evaluate_H7(rows, anchor_err, require_coverage=False),
            "aurc": aurc(rows),
            "monotone": _monotone(rows),
        }

    variants = {}
    for post in POST_VARIANTS:
        rows = []
        fits = {}
        for kappa in kappas:
            fit = fit_config(
                calib,
                "C3",
                float(kappa),
                alpha=alpha,
                post_variant=post,
                multiplicity=multiplicity,
            )
            rows.append(evaluate_config(test, fit, anchor_err, alpha=alpha))
            fits["%.3g" % float(kappa)] = fit
        variants[post] = {
            "rows": rows,
            "fits": fits,
            "H22_7": evaluate_H7(rows, anchor_err, require_coverage=True),
            "aurc": aurc(rows),
            "monotone": _monotone(rows),
        }
    out["C3_post_variants"] = variants

    base_rows = out["configs"]["C0"]["rows"]
    matched = {}
    for cfg in CONFIGS:
        rows = out["configs"][cfg]["rows"]
        matched[cfg] = {
            "%.2f" % float(t): risk_at_acceptance(rows, float(t))
            for t in MATCHED_ACCEPTANCE
        }
    out["matched_risk_at_acceptance"] = matched
    out["matched_risk_ratio_vs_C0"] = {
        cfg: {
            "%.2f" % float(t): (
                float(matched[cfg]["%.2f" % float(t)] / matched["C0"]["%.2f" % float(t)])
                if np.isfinite(matched[cfg]["%.2f" % float(t)])
                and np.isfinite(matched["C0"]["%.2f" % float(t)])
                and matched["C0"]["%.2f" % float(t)] > 0.0
                else float("nan")
            )
            for t in MATCHED_ACCEPTANCE
        }
        for cfg in CONFIGS
    }

    base_aurc = float(out["configs"]["C0"]["aurc"])
    fcr_only_degrades = (
        _positive_finite(base_aurc)
        and variants["fcr"]["aurc"] / base_aurc > 1.10
        and all(variants[p]["aurc"] / base_aurc < 1.02 for p in ("none", "mondrian", "selective"))
    )
    out["gates"] = {
        "G22_8_H22_7_C3_full_claim": bool(out["configs"]["C3"]["H22_7"]["pass"] is True),
        "G22_9_acceptance_and_risk_monotone": bool(
            all(v["monotone"]["acceptance_nonincreasing"] and v["monotone"]["risk_nonincreasing"] for v in out["configs"].values())
        ),
        "G22_13_two_violation_quantities_reported": bool(
            all(
                "violation_given_accept" in row and "err_given_accept" in row and "lose_any_given_accept" in row
                for cfg in out["configs"].values()
                for row in cfg["rows"]
            )
        ),
        "C0_fails_H22_7_with_coverage": bool(out["configs"]["C0"]["H22_7"]["pass"] is False),
        "frontier_unchanged_C3_vs_C0_within_8pct": bool(
            all(
                abs(out["matched_risk_ratio_vs_C0"]["C3"]["%.2f" % float(t)] - 1.0) < 0.08
                for t in (0.70, 0.50, 0.30)
            )
        ),
        "frontier_not_degraded_C3_vs_C0_within_8pct": bool(
            all(
                out["matched_risk_ratio_vs_C0"]["C3"]["%.2f" % float(t)] <= 1.08
                for t in (0.70, 0.50, 0.30)
                if np.isfinite(out["matched_risk_ratio_vs_C0"]["C3"]["%.2f" % float(t)])
            )
        ),
        "FCR_only_variant_degrades_frontier": bool(fcr_only_degrades),
    }
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calib", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--alpha", type=float, default=ALPHA)
    parser.add_argument("--multiplicity", default="bonferroni", choices=("bonferroni", "sidak"))
    args = parser.parse_args()

    df = pd.read_parquet(args.calib)
    result = run_matrix(df, alpha=float(args.alpha), multiplicity=str(args.multiplicity))
    out = {
        "cell": _infer_cell(args.calib),
        "n_rows": int(len(df)),
        "n_blocks": int(df["block_id"].nunique()),
        "n_calib_blocks": int(df.loc[df["is_calib"], "block_id"].nunique()),
        "n_test_blocks": int(df.loc[~df["is_calib"], "block_id"].nunique()),
        "alpha": float(args.alpha),
        "multiplicity": str(args.multiplicity),
        "kappas": [float(k) for k in KAPPA_GRID],
        **result,
        "provenance": {
            "script": "cert/config_matrix.py",
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
