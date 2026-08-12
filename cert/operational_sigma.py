#!/usr/bin/env python3
"""Phase 21R / Lesson 21R.8 -- operational-sigma robustness analysis.

The fixed-sigma path from Lessons 21R.1-21R.7 is a controlled design: it keeps
``sigma_rho = 0.0096`` so rho_bar can be studied without the sigma-rho_bar
confound.  This module runs the naturalistic path where each operating cell uses
its calibrated operational sigma, then checks whether the Phase 21R conclusions
survive without changing the original gates.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from cert.build_calib_set_v2 import SEEDS, SIGMA as SIGMA_FIXED, build_one
from cert.conformal_v2 import ALPHA, conformal_level, empirical_qhat, split_blocks
from measurements.decision_error_v2 import CALIBRATION, TRUTH_TABLE, TruthTable, feasible_cells
from twin import cost_v2 as C


DEGENERATE_ERR = 0.01
KAPPAS = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0)
COV_TOL_MARGINAL = 0.02
COV_TOL_PER_BIN = 0.05
H7_MIN_ACCEPTANCE = 0.10
H7_MAX_RISK_RATIO = 0.50
NEAR_ZERO_PC_MAX_ERR = 0.001
NEAR_ZERO_PC_MIN_ACCEPTANCE = 0.95
SHAPE_INVARIANCE_MODES = ("poisson", "h2")


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


def _cell_key(cell: Mapping[str, Any]) -> str:
    return "%s@%.3f" % (str(cell["mode"]), float(cell["rho_bar"]))


def _curve_row(curve: Sequence[Mapping[str, Any]], kappa: float) -> Dict[str, Any]:
    for row in curve:
        if np.isclose(float(row["kappa"]), float(kappa)):
            return dict(row)
    return {}


def run_cell(
    cell: Mapping[str, Any],
    tt: TruthTable,
    cv: C.CostV2,
    sigma: Optional[float],
    alpha: float = ALPHA,
    seeds: Sequence[int] = SEEDS,
) -> Dict[str, Any]:
    """Run one cell.

    ``sigma=None`` uses the cell's operational sigma from ``sla_calibration``.
    ``sigma=SIGMA_FIXED`` reproduces the controlled fixed-sigma path.
    """
    parts = []
    metas = []
    for seed in seeds:
        frame, meta = build_one(cell, int(seed), tt, cv, sigma=sigma)
        parts.append(frame)
        metas.append(meta)
    df = pd.concat(parts, ignore_index=True)

    is_calib = split_blocks(df["block_id"].to_numpy())
    qhat: Dict[int, float] = {}
    levels: Dict[int, Optional[float]] = {}
    n_calib_blocks: Dict[int, int] = {}
    for group, sub in df.assign(_calib=is_calib).groupby("z_bin", sort=True):
        g = int(group)
        calib = sub[sub["_calib"]]
        n_eff = int(calib["block_id"].nunique())
        level = conformal_level(n_eff, alpha)
        levels[g] = None if level is None else float(level)
        n_calib_blocks[g] = n_eff
        qhat[g] = (
            float("inf")
            if level is None
            else empirical_qhat(calib["s_margin"].to_numpy(np.float64), level)
        )

    test = df.loc[~is_calib].copy()
    q_row = test["z_bin"].map(qhat).to_numpy(np.float64)
    m_hat = test["m_hat"].to_numpy(np.float64)
    wrong = test["wrong"].to_numpy(bool)
    score = test["s_margin"].to_numpy(np.float64)
    anchor = float(wrong.mean())
    q_first = float(qhat[min(qhat)])
    q_last = float(qhat[max(qhat)])

    coverage_by_bin = {
        int(group): float((sub["s_margin"].to_numpy(np.float64) <= qhat[int(group)]).mean())
        for group, sub in test.groupby("z_bin", sort=True)
    }
    curve = []
    for kappa in KAPPAS:
        acc = m_hat >= float(kappa) * q_row
        n_accept = int(acc.sum())
        err_accept = float(wrong[acc].mean()) if n_accept else float("nan")
        curve.append(
            {
                "kappa": float(kappa),
                "acceptance_rate": float(acc.mean()),
                "n_accept": n_accept,
                "err_given_accept": err_accept,
                "err_given_reject": float(wrong[~acc].mean()) if (~acc).any() else float("nan"),
                "risk_ratio": float(err_accept / anchor) if n_accept and anchor > 0.0 else float("nan"),
            }
        )

    degenerate = bool(anchor < DEGENERATE_ERR)
    if degenerate:
        k1 = _curve_row(curve, 1.0)
        h7 = {
            "pass": None,
            "reason": "degenerate cell (anchor_err < %.3f)" % DEGENERATE_ERR,
            "near_zero_control": {
                "acceptance_at_kappa1": k1.get("acceptance_rate"),
                "err_at_kappa1": k1.get("err_given_accept"),
                "pass": bool(
                    k1
                    and float(k1["acceptance_rate"]) >= NEAR_ZERO_PC_MIN_ACCEPTANCE
                    and float(k1["err_given_accept"]) <= NEAR_ZERO_PC_MAX_ERR
                ),
            },
        }
    else:
        ok = [
            row
            for row in curve
            if float(row["acceptance_rate"]) >= H7_MIN_ACCEPTANCE
            and float(row["err_given_accept"]) <= H7_MAX_RISK_RATIO * anchor
        ]
        h7 = {
            "pass": bool(ok),
            "kappas_satisfying": [float(row["kappa"]) for row in ok],
            "best": max(ok, key=lambda row: row["acceptance_rate"]) if ok else None,
            "threshold_risk": float(H7_MAX_RISK_RATIO * anchor),
            "min_acceptance_rate": float(H7_MIN_ACCEPTANCE),
        }

    sigma_used = float(metas[0]["sigma_rho"])
    out: Dict[str, Any] = {
        "mode": str(cell["mode"]),
        "rho_bar": float(cell["rho_bar"]),
        "role": str(cell.get("role", "")),
        "sigma_mode": "fixed" if sigma is not None else "operational",
        "sigma_used": sigma_used,
        "anchor_err": anchor,
        "degenerate": degenerate,
        "qhat": qhat,
        "qhat_ratio_last_over_first": (
            float(q_last / q_first) if np.isfinite(q_first) and q_first > 0.0 else float("nan")
        ),
        "coverage_marginal": float((score <= q_row).mean()),
        "coverage_by_bin": coverage_by_bin,
        "n_rows": int(len(df)),
        "n_test": int(len(test)),
        "n_calib_blocks": n_calib_blocks,
        "level": levels,
        "curve": curve,
        "H7": h7,
        "pass_G3": bool(abs(float((score <= q_row).mean()) - (1.0 - alpha)) <= COV_TOL_MARGINAL),
        "pass_G4": bool(
            all(abs(v - (1.0 - alpha)) <= COV_TOL_PER_BIN for v in coverage_by_bin.values())
        ),
    }
    return out


def compare_paths(fixed: Mapping[str, Any], operational: Mapping[str, Any]) -> Dict[str, Any]:
    """Compare the controlled fixed-sigma path against the operational path."""
    fixed_k1 = _curve_row(fixed["curve"], 1.0)
    oper_k1 = _curve_row(operational["curve"], 1.0)
    sigma_fixed = float(fixed["sigma_used"])
    sigma_oper = float(operational["sigma_used"])
    return {
        "sigma_fixed": sigma_fixed,
        "sigma_operational": sigma_oper,
        "sigma_ratio": float(sigma_oper / sigma_fixed) if sigma_fixed else float("nan"),
        "anchor_fixed": float(fixed["anchor_err"]),
        "anchor_operational": float(operational["anchor_err"]),
        "degenerate_fixed": bool(fixed["degenerate"]),
        "degenerate_operational": bool(operational["degenerate"]),
        "rescued_by_operational": bool(fixed["degenerate"] and not operational["degenerate"]),
        "qhat_first_fixed": float(fixed["qhat"][min(fixed["qhat"])]),
        "qhat_first_operational": float(operational["qhat"][min(operational["qhat"])]),
        "qhat_ratio_fixed": float(fixed["qhat_ratio_last_over_first"]),
        "qhat_ratio_operational": float(operational["qhat_ratio_last_over_first"]),
        "acceptance_k1_fixed": fixed_k1.get("acceptance_rate"),
        "acceptance_k1_operational": oper_k1.get("acceptance_rate"),
        "err_k1_fixed": fixed_k1.get("err_given_accept"),
        "err_k1_operational": oper_k1.get("err_given_accept"),
        "coverage_fixed": float(fixed["coverage_marginal"]),
        "coverage_operational": float(operational["coverage_marginal"]),
    }


def _shape_invariance_eligible(key: str, result: Mapping[str, Any]) -> bool:
    mode = str(result.get("mode") or key.split("@", 1)[0])
    if mode not in SHAPE_INVARIANCE_MODES:
        return False
    qhat = result["qhat"]
    first = float(qhat[min(qhat)])
    last = float(qhat[max(qhat)])
    return bool(np.isfinite(first) and np.isfinite(last) and first > 0.0 and last > 0.0)


def invariance_report(results: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    """Report shape invariance of q_hat(last age bin) / q_hat(first age bin)."""
    rows = []
    for key, result in sorted(results.items()):
        if not _shape_invariance_eligible(key, result):
            continue
        qhat = result["qhat"]
        first = float(qhat[min(qhat)])
        last = float(qhat[max(qhat)])
        rows.append(
            {
                "cell": key,
                "qhat_first": first,
                "qhat_last": last,
                "ratio": float(last / first),
                "anchor_err": float(result["anchor_err"]),
                "h7_degenerate": bool(result["degenerate"]),
            }
        )
    if not rows:
        return {}
    ratios = np.array([row["ratio"] for row in rows], dtype=np.float64)
    firsts = np.array([row["qhat_first"] for row in rows], dtype=np.float64)
    return {
        "per_cell": rows,
        "n_cells": int(len(rows)),
        "ratio_mean": float(ratios.mean()),
        "ratio_sd": float(ratios.std(ddof=1)) if len(ratios) > 1 else 0.0,
        "ratio_min": float(ratios.min()),
        "ratio_max": float(ratios.max()),
        "ratio_rel_spread": float((ratios.max() - ratios.min()) / ratios.mean()),
        "qhat_scale_spread_factor": float(firsts.max() / firsts.min()),
        "note": (
            "q_hat(first bin) varies strongly across traffic regimes, but the age "
            "shape ratio stays narrow. This is observed on synthetic AR(1), tau=1.0; "
            "it is a Phase 23 hypothesis for real telemetry, not a proven law."
        ),
    }


def monotonicity_in_rho(results: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    """Check whether operational difficulty is monotone in rho_bar."""
    out: Dict[str, Any] = {}
    for mode in ("cbr", "poisson", "h2"):
        points = sorted(
            (
                (float(result["rho_bar"]), float(result["anchor_err"]), float(result["sigma_used"]))
                for key, result in results.items()
                if str(result.get("mode") or key.split("@", 1)[0]) == mode
            ),
            key=lambda item: item[0],
        )
        if len(points) < 3:
            continue
        err = np.array([point[1] for point in points], dtype=np.float64)
        out[mode] = {
            "rho_bar": [float(point[0]) for point in points],
            "anchor_err": [float(point[1]) for point in points],
            "sigma": [float(point[2]) for point in points],
            "monotone_increasing": bool(np.all(np.diff(err) >= 0.0)),
            "monotone_decreasing": bool(np.all(np.diff(err) <= 0.0)),
            "argmax_rho_bar": float(points[int(np.argmax(err))][0]),
        }
    out["note"] = (
        "Operational difficulty combines rho_bar and available sigma. Because "
        "sigma_max(rho_bar) peaks in the middle, the product need not be monotone."
    )
    return out


def summary_table(results: Mapping[str, Mapping[str, Any]]) -> list[Dict[str, Any]]:
    rows = []
    for key, result in sorted(results.items()):
        k1 = _curve_row(result["curve"], 1.0)
        rows.append(
            {
                "cell": key,
                "sigma": float(result["sigma_used"]),
                "anchor_err": float(result["anchor_err"]),
                "coverage_marginal": float(result["coverage_marginal"]),
                "qhat_first": float(result["qhat"][min(result["qhat"])]),
                "qhat_last": float(result["qhat"][max(result["qhat"])]),
                "qhat_ratio": float(result["qhat_ratio_last_over_first"]),
                "acceptance_k1": k1.get("acceptance_rate"),
                "err_k1": k1.get("err_given_accept"),
                "err_reject_k1": k1.get("err_given_reject"),
                "degenerate": bool(result["degenerate"]),
                "H7": result["H7"],
                "pass_G3": bool(result["pass_G3"]),
                "pass_G4": bool(result["pass_G4"]),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="results/phase-21R/operational_sigma.json")
    parser.add_argument("--alpha", type=float, default=ALPHA)
    parser.add_argument("--also-fixed", action="store_true")
    args = parser.parse_args()

    tt = TruthTable(TRUTH_TABLE)
    cv = C.CostV2(strict_reliable=False)
    cells = list(feasible_cells(CALIBRATION, include_pc1=True))

    operational: Dict[str, Dict[str, Any]] = {}
    fixed: Dict[str, Dict[str, Any]] = {}
    for cell in cells:
        key = _cell_key(cell)
        print("  %s (operational) ..." % key, flush=True)
        operational[key] = run_cell(cell, tt, cv, sigma=None, alpha=float(args.alpha))
        if args.also_fixed:
            print("  %s (fixed) ..." % key, flush=True)
            fixed[key] = run_cell(cell, tt, cv, sigma=SIGMA_FIXED, alpha=float(args.alpha))

    summary = {
        "n_cells": int(len(operational)),
        "n_degenerate": int(sum(bool(row["degenerate"]) for row in operational.values())),
        "n_nondegenerate": int(sum(not bool(row["degenerate"]) for row in operational.values())),
        "all_pass_G3": bool(all(row["pass_G3"] for row in operational.values())),
        "all_pass_G4": bool(all(row["pass_G4"] for row in operational.values())),
        "all_nondegenerate_pass_H7": bool(
            all(row["H7"]["pass"] for row in operational.values() if not row["degenerate"])
        ),
        "n_degenerate_near_zero_control_pass": int(
            sum(
                bool(row["H7"]["near_zero_control"]["pass"])
                for row in operational.values()
                if row["degenerate"]
            )
        ),
        "coverage_range": [
            float(min(row["coverage_marginal"] for row in operational.values())),
            float(max(row["coverage_marginal"] for row in operational.values())),
        ],
        "sigma_range": [
            float(min(row["sigma_used"] for row in operational.values())),
            float(max(row["sigma_used"] for row in operational.values())),
        ],
    }
    out: Dict[str, Any] = {
        "operational": operational,
        "operational_table": summary_table(operational),
        "invariance_qhat_ratio": invariance_report(operational),
        "monotonicity_in_rho_bar": monotonicity_in_rho(operational),
        "summary": summary,
        "provenance": {
            "script": "cert/operational_sigma.py",
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "alpha": float(args.alpha),
            "seeds": [int(seed) for seed in SEEDS],
            "sigma_fixed": float(SIGMA_FIXED),
            "truth_table": TRUTH_TABLE,
            "calibration": CALIBRATION,
        },
    }
    if args.also_fixed:
        comparison = {key: compare_paths(fixed[key], operational[key]) for key in operational}
        out["fixed"] = fixed
        out["fixed_table"] = summary_table(fixed)
        out["comparison"] = comparison
        out["summary"]["n_rescued_by_operational"] = int(
            sum(bool(row["rescued_by_operational"]) for row in comparison.values())
        )

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(_json_clean(out), f, indent=1, sort_keys=True)
        f.write("\n")

    print(
        json.dumps(
            _json_clean(
                {
                    "summary": out["summary"],
                    "invariance_qhat_ratio": out["invariance_qhat_ratio"],
                    "monotonicity_in_rho_bar": out["monotonicity_in_rho_bar"],
                }
            ),
            indent=1,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
