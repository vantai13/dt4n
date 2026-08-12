#!/usr/bin/env python3
"""Phase 21R / Lesson 21R.7 -- freshness requirements.

Lessons 21R.1-21R.6 describe the system:

    z -> q_hat(z), acceptance(z), error(z)

This module inverts that view into an engineering specification:

    quality target -> required z* -> synchronization frequency

For sawtooth AoI, the distinction between peak AoI and average AoI matters:

    z_max  = d_sync + T
    z_mean = d_sync + T / 2

The same numeric AoI requirement therefore implies a 2x synchronization-rate
difference depending on which interpretation is intended.
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

from cert import margin_score as MS
from cert.conformal_v2 import conformal_level, empirical_qhat, split_blocks
from measurements.decision_error import sawtooth_age_steps
from measurements.decision_error_v2 import (
    CALIBRATION,
    DT,
    N,
    TRUTH_TABLE,
    TruthTable,
    _cell_arrays,
    feasible_cells,
)
from twin import cost_v2 as C


BLOCK_S = 5.0
COMMON_K = 800
SIGMA = 0.0096
SEEDS = (101, 102, 103, 104, 105)
ALPHA = 0.10
D_SYNC = 0.051
TARGET_ERR = 0.01
Z_GRID = (
    0.0,
    0.005,
    0.010,
    0.020,
    0.030,
    0.040,
    0.055,
    0.075,
    0.100,
    0.150,
    0.200,
    0.300,
    0.400,
    0.550,
)
Z_FRONTIER = (0.055, 0.100, 0.150, 0.200, 0.300, 0.400, 0.550)


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


def block_len(dt: float = DT, block_s: float = BLOCK_S) -> int:
    return int(round(float(block_s) / float(dt)))


def _load_cell(mode: str, rho_bar: float) -> Mapping[str, Any]:
    cells = {
        (str(c["mode"]), float(c["rho_bar"])): c
        for c in feasible_cells(CALIBRATION, include_pc1=True)
    }
    key = (str(mode), float(rho_bar))
    if key not in cells:
        raise SystemExit("cell %s is not feasible in %s" % (key, CALIBRATION))
    return cells[key]


def _fixed_z_frame_from_arrays(
    arrays: Mapping[str, Any],
    seed: int,
    z: float,
    common_k: int = COMMON_K,
    dt: float = DT,
) -> pd.DataFrame:
    k = int(round(float(z) / float(dt)))
    cur = np.arange(int(common_k), int(arrays["n"]))
    old = cur - k
    if old.min() < 0:
        raise ValueError("common_k=%d is too small for z=%.6f" % (int(common_k), float(z)))

    y_true = arrays["c_true"][cur]
    y_hat = arrays["c_fresh"][old]
    _a1, _a2, m_hat, m_true = MS.margins(y_true, y_hat)
    rows = np.arange(len(cur))
    a_twin = arrays["a_fresh"][old]
    a_star = arrays["a_true"][cur]
    cost_true = arrays["c_true"][cur]
    viol = arrays["viol"]

    return pd.DataFrame(
        {
            "block_id": (int(seed) * 100_000 + cur // block_len(dt)).astype(np.int32),
            "m_hat": m_hat.astype(np.float32),
            "m_true": m_true.astype(np.float32),
            "s_margin": np.abs(m_hat - m_true).astype(np.float32),
            "wrong": (a_twin != a_star),
            "regret": (cost_true[rows, a_twin] - cost_true[rows, a_star]).astype(np.float32),
            "d_sla": (viol[cur, a_twin].astype(float) - viol[cur, a_star].astype(float)).astype(
                np.float32
            ),
        }
    )


def build_fixed_z(
    cell: Mapping[str, Any],
    tt: TruthTable,
    cv: C.CostV2,
    z: float,
    seeds: Sequence[int] = SEEDS,
    n: int = N,
    dt: float = DT,
    sigma: float = SIGMA,
) -> pd.DataFrame:
    """Build one fixed-z table, evaluated on the common Phase 20R window."""
    parts = []
    for seed in seeds:
        arrays = _cell_arrays(tt, cv, cell, seed=int(seed), n=int(n), dt=float(dt), sigma_override=sigma)
        parts.append(_fixed_z_frame_from_arrays(arrays, int(seed), float(z), dt=float(dt)))
    return pd.concat(parts, ignore_index=True)


def build_fixed_z_tables(
    cell: Mapping[str, Any],
    tt: TruthTable,
    cv: C.CostV2,
    z_grid: Sequence[float] = Z_GRID,
    seeds: Sequence[int] = SEEDS,
    n: int = N,
    dt: float = DT,
    sigma: float = SIGMA,
) -> Dict[float, pd.DataFrame]:
    """Build all fixed-z tables while reusing each seed's physical arrays."""
    tables: Dict[float, list[pd.DataFrame]] = {float(z): [] for z in z_grid}
    for seed in seeds:
        arrays = _cell_arrays(tt, cv, cell, seed=int(seed), n=int(n), dt=float(dt), sigma_override=sigma)
        for z in z_grid:
            tables[float(z)].append(_fixed_z_frame_from_arrays(arrays, int(seed), float(z), dt=float(dt)))
    return {z: pd.concat(parts, ignore_index=True) for z, parts in tables.items()}


def evaluate_at_z(
    df: pd.DataFrame,
    kappas: Sequence[float] = (0.5, 1.0),
    alpha: float = ALPHA,
) -> Dict[str, Any]:
    """Fit q_hat on calibration blocks and evaluate a single fixed-z test set."""
    is_calib = split_blocks(df["block_id"].to_numpy())
    calib = df.loc[is_calib]
    level = conformal_level(int(calib["block_id"].nunique()), alpha)
    qhat = (
        float("inf")
        if level is None
        else empirical_qhat(calib["s_margin"].to_numpy(np.float64), level)
    )
    test = df.loc[~is_calib]
    m_hat = test["m_hat"].to_numpy(np.float64)
    wrong = test["wrong"].to_numpy(bool)
    regret = test["regret"].to_numpy(np.float64)
    d_sla = test["d_sla"].to_numpy(np.float64)

    out: Dict[str, Any] = {
        "qhat": float(qhat),
        "err_anchor_all": float(df["wrong"].mean()),
        "err_anchor": float(wrong.mean()),
        "rms_s_margin_all": float(np.sqrt(np.mean(df["s_margin"].to_numpy(np.float64) ** 2))),
        "rms_s_margin": float(np.sqrt(np.mean(test["s_margin"].to_numpy(np.float64) ** 2))),
        "n_test": int(len(test)),
        "n_calib_blocks": int(calib["block_id"].nunique()),
        "n_test_blocks": int(test["block_id"].nunique()),
        "level": None if level is None else float(level),
    }
    for kappa in kappas:
        acc = m_hat >= float(kappa) * qhat
        prefix = "k%g_" % float(kappa)
        out[prefix + "acceptance"] = float(acc.mean())
        out[prefix + "err"] = float(wrong[acc].mean()) if acc.any() else float("nan")
        out[prefix + "regret"] = float(regret[acc].mean()) if acc.any() else float("nan")
        out[prefix + "d_sla"] = float(d_sla[acc].mean()) if acc.any() else float("nan")
        out[prefix + "n_accept"] = int(acc.sum())
    return out


def invert_for_z(
    table: pd.DataFrame,
    column: str,
    target: float,
    decreasing_is_good: bool = True,
    d_sync: float = D_SYNC,
) -> Dict[str, Any]:
    """Linearly interpolate z* such that a metric meets the requested target."""
    d = table.sort_values("z").reset_index(drop=True)
    z = d["z"].to_numpy(np.float64)
    y = d[column].to_numpy(np.float64)
    bad = np.where(y > target)[0] if decreasing_is_good else np.where(y < target)[0]
    if len(bad) == 0:
        return {
            "z_star": float(z[-1]),
            "status": "target_met_on_whole_grid",
            "feasible_vs_d_sync": bool(float(z[-1]) >= float(d_sync)),
            "d_sync": float(d_sync),
        }
    j = int(bad[0])
    if j == 0:
        return {
            "z_star": None,
            "status": "infeasible_even_at_z0",
            "feasible_vs_d_sync": False,
            "d_sync": float(d_sync),
            "note": "target is not met even at instantaneous synchronization",
        }

    y0 = float(y[j - 1])
    y1 = float(y[j])
    if y1 == y0:
        z_star = float(z[j])
    else:
        z_star = float(z[j - 1] + (z[j] - z[j - 1]) * (target - y0) / (y1 - y0))
    return {
        "z_star": z_star,
        "status": "interpolated",
        "feasible_vs_d_sync": bool(z_star >= float(d_sync)),
        "d_sync": float(d_sync),
    }


def sync_rate_from_z(
    z: Optional[float],
    d_sync: float = D_SYNC,
    interpretation: str = "mean",
) -> Optional[float]:
    """Convert an AoI requirement into a synchronization rate in Hz."""
    if interpretation not in ("max", "mean"):
        raise ValueError("interpretation must be 'max' or 'mean'")
    if z is None or float(z) <= float(d_sync):
        return None
    period = float(z) - float(d_sync)
    if interpretation == "mean":
        period *= 2.0
    return float(1.0 / period)


def aoi_averaging_check(
    table: pd.DataFrame,
    z_levels: Sequence[float],
    measured_sawtooth_err: Optional[float] = None,
    column: str = "err_anchor",
) -> Dict[str, Any]:
    """Compare E[f(z)], f(E[z]), and f(max z) over the sawtooth AoI grid."""
    d = table.sort_values("z")
    z = d["z"].to_numpy(np.float64)
    y = d[column].to_numpy(np.float64)
    levels = np.asarray(z_levels, dtype=np.float64)
    out = {
        "E_of_f": float(np.interp(levels, z, y).mean()),
        "f_of_E": float(np.interp(float(levels.mean()), z, y)),
        "f_of_max": float(np.interp(float(levels.max()), z, y)),
        "z_mean": float(levels.mean()),
        "z_max": float(levels.max()),
    }
    out["jensen_order_holds"] = bool(out["E_of_f"] <= out["f_of_E"] <= out["f_of_max"])
    if measured_sawtooth_err is not None:
        measured = float(measured_sawtooth_err)
        out["measured_sawtooth"] = measured
        out["closest_to"] = min(
            (
                ("E_of_f", abs(out["E_of_f"] - measured)),
                ("f_of_E", abs(out["f_of_E"] - measured)),
                ("f_of_max", abs(out["f_of_max"] - measured)),
            ),
            key=lambda item: item[1],
        )[0]
    return out


def iso_quality_frontier(
    tables: Mapping[float, pd.DataFrame],
    target_err: float = TARGET_ERR,
    alpha: float = ALPHA,
    d_sync: float = D_SYNC,
    kappa_hi: float = 12.0,
    n_bisect: int = 60,
    min_accept_rows: int = 50,
) -> pd.DataFrame:
    """For each z, find kappa* such that err|accept is at most target_err."""
    rows = []
    for z in sorted(float(x) for x in tables):
        df = tables[z]
        is_calib = split_blocks(df["block_id"].to_numpy())
        calib = df.loc[is_calib]
        level = conformal_level(int(calib["block_id"].nunique()), alpha)
        if level is None:
            continue
        qhat = empirical_qhat(calib["s_margin"].to_numpy(np.float64), level)
        test = df.loc[~is_calib]
        m_hat = test["m_hat"].to_numpy(np.float64)
        wrong = test["wrong"].to_numpy(bool)

        lo = 0.0
        hi = float(kappa_hi)
        for _ in range(int(n_bisect)):
            mid = 0.5 * (lo + hi)
            acc = m_hat >= mid * qhat
            err = float(wrong[acc].mean()) if int(acc.sum()) > int(min_accept_rows) else 0.0
            if err > float(target_err):
                lo = mid
            else:
                hi = mid

        acc = m_hat >= hi * qhat
        rows.append(
            {
                "z": float(z),
                "qhat": float(qhat),
                "kappa_star": float(hi),
                "acceptance_rate": float(acc.mean()),
                "n_accept": int(acc.sum()),
                "err_check": float(wrong[acc].mean()) if acc.any() else float("nan"),
                "sync_hz_mean_interp": sync_rate_from_z(z, d_sync, "mean"),
                "sync_hz_max_interp": sync_rate_from_z(z, d_sync, "max"),
            }
        )
    return pd.DataFrame(rows)


def knee_of_frontier(frontier: pd.DataFrame) -> Dict[str, Any]:
    """Estimate the knee using acceptance slope over log10 sync rate."""
    d = frontier.dropna(subset=["sync_hz_mean_interp"]).sort_values("sync_hz_mean_interp")
    if len(d) < 3:
        return {}
    freq = np.log10(d["sync_hz_mean_interp"].to_numpy(np.float64))
    acc = d["acceptance_rate"].to_numpy(np.float64)
    slope = np.diff(acc) / np.diff(freq)
    if len(slope) <= 1:
        idx = 0
    else:
        idx = int(np.argmax(-np.diff(slope))) + 1
    return {
        "knee_sync_hz": float(d["sync_hz_mean_interp"].iloc[idx]),
        "knee_z": float(d["z"].iloc[idx]),
        "knee_acceptance": float(d["acceptance_rate"].iloc[idx]),
        "slope_per_decade": [float(x) for x in slope],
        "note": "Slope is measured as acceptance gained per decade of sync frequency.",
    }


def _add_sync_rates(inversions: Mapping[str, Dict[str, Any]], d_sync: float) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for key, value in inversions.items():
        row = dict(value)
        z_star = row.get("z_star")
        row["sync_hz_mean_interp"] = sync_rate_from_z(z_star, d_sync, "mean")
        row["sync_hz_max_interp"] = sync_rate_from_z(z_star, d_sync, "max")
        out[key] = row
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True)
    parser.add_argument("--rho-bar", type=float, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--target-err", type=float, default=TARGET_ERR)
    parser.add_argument("--measured-sawtooth-err", type=float, default=None)
    parser.add_argument("--d-sync", type=float, default=D_SYNC)
    parser.add_argument("--n", type=int, default=N)
    args = parser.parse_args()

    tt = TruthTable(TRUTH_TABLE)
    cv = C.CostV2(strict_reliable=False)
    cell = _load_cell(args.mode, float(args.rho_bar))

    tables = build_fixed_z_tables(cell, tt, cv, n=int(args.n))
    table = pd.DataFrame(
        [dict(z=float(z), **evaluate_at_z(df)) for z, df in tables.items()]
    ).sort_values("z")

    z_levels = np.unique(sawtooth_age_steps(int(args.n), DT) * DT)
    inversions = _add_sync_rates(
        {
            "err_anchor<=0.10_no_gate": invert_for_z(
                table, "err_anchor", 0.10, d_sync=float(args.d_sync)
            ),
            "err_gated<=0.01_kappa1": invert_for_z(
                table, "k1_err", 0.01, d_sync=float(args.d_sync)
            ),
            "acceptance>=0.50_kappa1": invert_for_z(
                table,
                "k1_acceptance",
                0.50,
                decreasing_is_good=False,
                d_sync=float(args.d_sync),
            ),
        },
        float(args.d_sync),
    )

    frontier = iso_quality_frontier(
        {z: tables[z] for z in Z_FRONTIER if float(z) >= float(args.d_sync)},
        target_err=float(args.target_err),
        d_sync=float(args.d_sync),
    )

    z0 = table.loc[np.isclose(table["z"], 0.0)].iloc[0]
    out: Dict[str, Any] = {
        "cell": "%s@%.3f" % (str(args.mode), float(args.rho_bar)),
        "d_sync": float(args.d_sync),
        "target_err": float(args.target_err),
        "z_grid": [float(z) for z in Z_GRID],
        "table": table.to_dict(orient="records"),
        "model_floor": {
            "err_at_z0_all_rows": float(z0["err_anchor_all"]),
            "err_at_z0_test_rows": float(z0["err_anchor"]),
            "rms_s_margin_at_z0_all_rows": float(z0["rms_s_margin_all"]),
            "rms_s_margin_at_z0_test_rows": float(z0["rms_s_margin"]),
            "qhat_at_z0": float(z0["qhat"]),
            "acceptance_at_z0_kappa1": float(z0["k1_acceptance"]),
            "err_gated_at_z0_kappa1": float(z0["k1_err"]),
            "note": (
                "The model floor applies to forced decisions; abstention can "
                "drive accepted-set error far below it."
            ),
        },
        "aoi_averaging": aoi_averaging_check(
            table, z_levels, measured_sawtooth_err=args.measured_sawtooth_err
        ),
        "inversions": inversions,
        "iso_quality_frontier": frontier.to_dict(orient="records"),
        "knee": knee_of_frontier(frontier),
        "provenance": {
            "script": "cert/freshness_requirement.py",
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "mode": str(args.mode),
            "rho_bar": float(args.rho_bar),
            "n": int(args.n),
            "dt": float(DT),
            "sigma": float(SIGMA),
            "seeds": [int(s) for s in SEEDS],
            "alpha": float(ALPHA),
            "d_sync": float(args.d_sync),
        },
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(_json_clean(out), f, indent=1, sort_keys=True)
        f.write("\n")

    cols = [
        "z",
        "err_anchor",
        "qhat",
        "k1_acceptance",
        "k1_err",
        "k1_regret",
        "k0.5_acceptance",
        "k0.5_err",
    ]
    print(table[cols].to_string(index=False))
    print()
    print(frontier.to_string(index=False))
    print()
    print(
        json.dumps(
            _json_clean(
                {
                    "model_floor": out["model_floor"],
                    "aoi_averaging": out["aoi_averaging"],
                    "inversions": out["inversions"],
                    "knee": out["knee"],
                }
            ),
            indent=1,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
