#!/usr/bin/env python3
"""Phase 21R / Lesson 21R.3 -- decompose model error vs staleness error.

The Phase 21R target decomposition is at decision-margin level on the cost
scale.  Delay/path decompositions are reported only to label and cross-check
older Phase 20R quantities.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

from cert import margin_score as MS
from measurements.decision_error_v2 import DT, N, TruthTable, _cell_arrays, feasible_cells
from twin import cost_v2 as C


SIGMA = 0.0096
SEEDS = (101, 102, 103, 104, 105)
COMMON_K = 800
Z_FINE = (
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


def decompose_margin(
    y_true: np.ndarray,
    y_mid: np.ndarray,
    y_hat: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(e_model, e_stale, total)`` at decision-margin level.

    The pair ``(a1,a2)`` is selected from stale ``y_hat`` and held fixed for all
    three worlds.  Re-selecting it on ``y_mid`` keeps the telescoping total true
    but changes the scientific meaning of the split.
    """
    y_mid_arr = np.asarray(y_mid, dtype=np.float64)
    a1, a2, m_hat, m_true = MS.margins(y_true, y_hat)
    rows = np.arange(len(y_mid_arr))
    m_mid = y_mid_arr[rows, a2] - y_mid_arr[rows, a1]
    e_model = m_true - m_mid
    e_stale = m_mid - m_hat
    total = m_true - m_hat
    if not np.allclose(e_model + e_stale, total, atol=1e-9):
        raise AssertionError("dong nhat thuc phan ra bien khong khop")
    return e_model, e_stale, total


def decompose_path(
    y_true: np.ndarray,
    y_mid: np.ndarray,
    y_hat: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return path-level ``(e_model, e_stale, total)`` for all K actions."""
    y_true_arr = np.asarray(y_true, dtype=np.float64)
    y_mid_arr = np.asarray(y_mid, dtype=np.float64)
    y_hat_arr = np.asarray(y_hat, dtype=np.float64)
    e_model = y_true_arr - y_mid_arr
    e_stale = y_mid_arr - y_hat_arr
    total = y_true_arr - y_hat_arr
    if not np.allclose(e_model + e_stale, total, atol=1e-9):
        raise AssertionError("dong nhat thuc phan ra duong khong khop")
    return e_model, e_stale, total


def moments(e_model: np.ndarray, e_stale: np.ndarray) -> Dict[str, float]:
    """Second moments and the required covariance identity."""
    em = np.asarray(e_model, dtype=np.float64).ravel()
    es = np.asarray(e_stale, dtype=np.float64).ravel()
    ms_m = float(np.mean(em * em))
    ms_s = float(np.mean(es * es))
    cov = float(np.mean(em * es))
    ms_t = float(np.mean((em + es) ** 2))
    if not np.isclose(ms_t, ms_m + ms_s + 2.0 * cov, rtol=1e-9, atol=1e-12):
        raise AssertionError("dong nhat thuc phuong sai khong khop")
    denom = np.sqrt(ms_m * ms_s)
    return {
        "rms_e_model": float(np.sqrt(ms_m)),
        "rms_e_stale": float(np.sqrt(ms_s)),
        "cov_e": cov,
        "corr_e": float(cov / denom) if denom > 0 else float("nan"),
        "rms_total": float(np.sqrt(ms_t)),
        "share_model": float(ms_m / ms_t) if ms_t > 0 else float("nan"),
        "share_stale": float(ms_s / ms_t) if ms_t > 0 else float("nan"),
        "share_cov": float(2.0 * cov / ms_t) if ms_t > 0 else float("nan"),
        "mean_e_model": float(em.mean()),
        "mean_e_stale": float(es.mean()),
        "n": int(em.size),
    }


def _arrays_for_sweep(
    cell: Mapping[str, Any],
    tt: TruthTable,
    cv: C.CostV2,
    seeds: Sequence[int],
    n: int,
    dt: float,
    sigma: float,
) -> list[Mapping[str, Any]]:
    return [_cell_arrays(tt, cv, cell, seed=int(seed), n=int(n), dt=float(dt), sigma_override=float(sigma)) for seed in seeds]


def sweep_z(
    cell: Mapping[str, Any],
    tt: TruthTable,
    cv: C.CostV2,
    level: str = "margin",
    channel: str = "cost",
    z_list: Sequence[float] = Z_FINE,
    seeds: Sequence[int] = SEEDS,
    n: int = N,
    dt: float = DT,
    sigma: float = SIGMA,
    arrays: Sequence[Mapping[str, Any]] | None = None,
) -> pd.DataFrame:
    """Sweep z and return one row per age for one level/channel pair."""
    if level not in ("margin", "path"):
        raise ValueError("level phai la 'margin' hoac 'path'")
    if channel not in ("cost", "delay"):
        raise ValueError("channel phai la 'cost' hoac 'delay'")

    key_true = "c_true" if channel == "cost" else "d_true"
    key_hat = "c_fresh" if channel == "cost" else "d_fresh"
    arrs = list(arrays) if arrays is not None else _arrays_for_sweep(cell, tt, cv, seeds, n, dt, sigma)
    rows = []
    cur = np.arange(COMMON_K, int(n))
    for z in z_list:
        k = int(round(float(z) / float(dt)))
        acc = []
        for arr in arrs:
            y_true = arr[key_true][cur]
            y_mid = arr[key_hat][cur]
            y_hat = arr[key_hat][cur - k]
            if level == "margin":
                if channel == "delay":
                    a1, a2 = MS.top_two_by_twin(arr["c_fresh"][cur - k])
                    rr = np.arange(len(cur))
                    m_true = y_true[rr, a2] - y_true[rr, a1]
                    m_mid = y_mid[rr, a2] - y_mid[rr, a1]
                    m_hat = y_hat[rr, a2] - y_hat[rr, a1]
                    em, es = m_true - m_mid, m_mid - m_hat
                    total = m_true - m_hat
                    if not np.allclose(em + es, total, atol=1e-9):
                        raise AssertionError("dong nhat thuc phan ra margin-delay khong khop")
                else:
                    em, es, _total = decompose_margin(y_true, y_mid, y_hat)
            else:
                em, es, _total = decompose_path(y_true, y_mid, y_hat)
            acc.append(moments(em, es))
        row = {"z_s": float(z), "level": level, "channel": channel}
        for key in acc[0]:
            row[key] = float(np.mean([m[key] for m in acc]))
        rows.append(row)
    return pd.DataFrame(rows)


def find_z_cross(df: pd.DataFrame) -> Dict[str, Any]:
    """Find where ``rms_e_stale`` crosses ``rms_e_model``."""
    d = df.sort_values("z_s")
    z = d["z_s"].to_numpy(float)
    diff = (d["rms_e_stale"] - d["rms_e_model"]).to_numpy(float)
    pos = np.where(diff > 0)[0]
    if len(pos) == 0:
        return {"z_cross_s": None, "status": "above_grid"}
    j = int(pos[0])
    if j == 0:
        z0 = float(z[0])
        s0 = float(d["rms_e_stale"].iloc[0])
        m0 = float(d["rms_e_model"].iloc[0])
        return {
            "z_cross_s": float(z0 * (m0 / s0) ** 2),
            "status": "below_grid_extrapolated_sqrt",
        }
    zc = z[j - 1] + (z[j] - z[j - 1]) * (-diff[j - 1]) / (diff[j] - diff[j - 1])
    return {"z_cross_s": float(zc), "status": "interpolated"}


def control_NC1_z0(cell: Mapping[str, Any], tt: TruthTable, cv: C.CostV2, seed: int = 101, n: int = 50_000) -> Dict[str, float]:
    """At z=0, staleness must be exactly zero."""
    arr = _cell_arrays(tt, cv, cell, seed=int(seed), n=int(n), sigma_override=SIGMA)
    em, es, _total = decompose_margin(arr["c_true"], arr["c_fresh"], arr["c_fresh"])
    return {
        "max_abs_e_stale": float(np.abs(es).max()),
        "rms_e_model": float(np.sqrt(np.mean(em * em))),
    }


def control_NC2_perfect_model(
    cell: Mapping[str, Any],
    tt: TruthTable,
    cv: C.CostV2,
    seed: int = 101,
    z: float = 0.20,
    n: int = 50_000,
) -> Dict[str, float]:
    """If cost_v2 is truth, model error is exactly zero."""
    arr = _cell_arrays(tt, cv, cell, seed=int(seed), n=int(n), sigma_override=SIGMA)
    k = int(round(float(z) / DT))
    cur = np.arange(k, int(n))
    em, es, total = decompose_margin(arr["c_fresh"][cur], arr["c_fresh"][cur], arr["c_fresh"][cur - k])
    return {
        "max_abs_e_model": float(np.abs(em).max()),
        "max_abs_diff_stale_total": float(np.abs(es - total).max()),
    }


def control_flatness(df: pd.DataFrame) -> Dict[str, float | bool]:
    """``rms_e_model`` should not depend on z."""
    values = df["rms_e_model"].to_numpy(float)
    rel = float((values.max() - values.min()) / values.mean())
    return {"rms_e_model_rel_spread": rel, "pass": bool(rel < 0.01)}


def _git(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def _load_cell(mode: str, rho_bar: float) -> Mapping[str, Any]:
    cells = {(str(c["mode"]), float(c["rho_bar"])): c for c in feasible_cells(include_pc1=True)}
    key = (str(mode), float(rho_bar))
    if key not in cells:
        raise SystemExit("o %s khong kha thi trong sla_calibration.json" % (key,))
    return cells[key]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True)
    parser.add_argument("--rho-bar", type=float, required=True)
    parser.add_argument("--out", default="results/SUPERSEDED/phase-21R/decomposition.json")
    parser.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    parser.add_argument("--n", type=int, default=N)
    parser.add_argument("--noise-floor-ms", type=float, default=1.4851)
    args = parser.parse_args()

    tt = TruthTable()
    cv = C.CostV2(strict_reliable=False)
    cell = _load_cell(args.mode, args.rho_bar)
    arrays = _arrays_for_sweep(cell, tt, cv, args.seeds, int(args.n), DT, SIGMA)

    out: Dict[str, Any] = {
        "cell": "%s@%.3f" % (str(args.mode), float(args.rho_bar)),
        "sweeps": {},
        "z_cross": {},
    }
    for level in ("margin", "path"):
        for channel in ("cost", "delay"):
            tag = "%s_%s" % (level, channel)
            df = sweep_z(cell, tt, cv, level=level, channel=channel, seeds=args.seeds, n=int(args.n), arrays=arrays)
            out["sweeps"][tag] = df.to_dict(orient="records")
            out["z_cross"][tag] = find_z_cross(df)
            if level == "margin" and channel == "cost":
                out["flatness"] = control_flatness(df)
                em = float(df["rms_e_model"].mean())
                floor = float(args.noise_floor_ms)
                out["model_error_net_of_measurement_noise"] = {
                    "rms_e_model_observed_ms": em,
                    "measurement_noise_floor_ms": floor,
                    "rms_model_true_ms": float(np.sqrt(max(em * em - floor * floor, 0.0))),
                    "variance_share_from_measurement_noise": float(min((floor * floor) / (em * em), 1.0)),
                }
    out["NC1_z0"] = control_NC1_z0(cell, tt, cv)
    out["NC2_perfect_model"] = control_NC2_perfect_model(cell, tt, cv)
    out["provenance"] = {
        "script": "cert/decomposition.py",
        "git_hash": _git("git", "rev-parse", "HEAD"),
        "git_dirty": bool(_git("git", "status", "--porcelain")),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "seeds": [int(s) for s in args.seeds],
        "n": int(args.n),
        "dt": float(DT),
        "sigma_rho": float(SIGMA),
        "common_k": int(COMMON_K),
        "z_grid": [float(z) for z in Z_FINE],
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print(
        json.dumps(
            {
                "cell": out["cell"],
                "z_cross": out["z_cross"],
                "flatness": out["flatness"],
                "model_error_net_of_measurement_noise": out["model_error_net_of_measurement_noise"],
                "NC1_z0": out["NC1_z0"],
                "NC2_perfect_model": out["NC2_perfect_model"],
            },
            indent=1,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
