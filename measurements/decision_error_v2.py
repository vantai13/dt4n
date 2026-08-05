#!/usr/bin/env python3
"""Phase 20R -- decision error with measured ground truth (Lesson 20R.5).

Compared with Phase 20, the true cost comes from the measured truth table while
the twin still uses ``link_model_v2``. Therefore ``err(z=0)`` is model error,
not a bug. Only the perfect-twin control is required to be exactly zero.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from measurements import sla_calib_v2 as SLA
from measurements.decision_error import check_z_grid
from mininet.rho_spec import ou_trajectory
from twin import cost_v2 as C
from twin import topology_v7 as T7


DT = 0.005
TAU = 1.0
N = 200_000
CONTROL_N = 50_000
BLOCK_S = 5.0
N_BOOT = 2000
Z_GRID = (0.0, 0.05, 0.10, 0.20, 0.30, 0.55)
Z_EXTRAP = (1.0, 2.0, 4.0)
Z_ALL = Z_GRID + Z_EXTRAP

TRUTH_TABLE = "results/phase-20R/truth_table.parquet"
CALIBRATION = "results/phase-20R/sla_calibration.json"
CONTROLS_OUT = "results/phase-20R/controls.json"
FIXED_OUT = "results/phase-20R/decision_error_by_age_by_regime.parquet"
RHO_SOURCE = "calibration_ar1"


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_json(path: str, data: object) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def z_key(z_s: float) -> str:
    return "%.3f" % float(z_s)


def load_calibration(path: str = CALIBRATION) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        report = json.load(f)
    return [dict(row) for row in report["cells"]]


def feasible_cells(path: str = CALIBRATION, include_pc1: bool = True) -> List[Dict[str, Any]]:
    rows = []
    for cell in load_calibration(path):
        if not cell.get("feasible"):
            continue
        role = str(cell.get("role", ""))
        if role == "gate" or (include_pc1 and role.startswith("pc1")):
            rows.append(cell)
    return rows


class TruthTable:
    """Measured lookup table. Linear interpolation, explicit clipping log."""

    def __init__(self, parquet_path: str = TRUTH_TABLE):
        table = pd.read_parquet(parquet_path)
        self.field = table.attrs.get("truth_field", "q_mean_ms")
        self.curves: Dict[Tuple[str, float, int], Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}
        for key, group in table.groupby(["mode", "bw", "q"], sort=True):
            group = group.sort_values("rho")
            self.curves[(str(key[0]), float(key[1]), int(key[2]))] = (
                group["rho"].to_numpy(float),
                group["delay_mean_ms"].to_numpy(float),
                group["loss"].to_numpy(float),
                group["se_mean_ms"].to_numpy(float),
            )
        self.clip_log: Dict[str, float] = {}

    def reset_clip_log(self) -> None:
        self.clip_log = {}

    def domain(self, mode: str, bw: float, q: int) -> Tuple[float, float]:
        rho = self.curves[(str(mode), float(bw), int(q))][0]
        return float(rho.min()), float(rho.max())

    def queue_delay_loss(self, mode: str, bw: float, q: int, rho: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        grid, delay, loss, _se = self.curves[(str(mode), float(bw), int(q))]
        rq = np.clip(np.asarray(rho, dtype=float), float(grid.min()), float(grid.max()))
        return np.interp(rq, grid, delay), np.interp(rq, grid, loss)

    def delay_loss(self, mode: str, link: str, rho: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        bw, base, q = T7.LINKS[link]
        grid, delay, loss, _se = self.curves[(str(mode), float(bw), int(q))]
        rho_arr = np.asarray(rho, dtype=float)
        lo, hi = float(grid.min()), float(grid.max())
        n_out = int(((rho_arr < lo) | (rho_arr > hi)).sum())
        self.clip_log["%s|%s" % (mode, link)] = n_out / max(int(rho_arr.size), 1)
        rq = np.clip(rho_arr, lo, hi)
        total_delay = float(base) + C.serialization_ms(bw) + np.interp(rq, grid, delay)
        return total_delay, np.interp(rq, grid, loss)

    def path_tables(self, mode: str, rho_mat: np.ndarray, w_loss: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        rho_mat = np.asarray(rho_mat, dtype=float)
        n = int(rho_mat.shape[0])
        delay = np.zeros((n, T7.K), dtype=float)
        keep = np.ones((n, T7.K), dtype=float)
        idx = {link: i for i, link in enumerate(T7.LINK_NAMES)}
        for action, path in enumerate(T7.PATH_NAMES):
            for link in T7.PATHS[path]:
                d, loss = self.delay_loss(mode, link, rho_mat[:, idx[link]])
                delay[:, action] += d
                keep[:, action] *= 1.0 - loss
        loss = 1.0 - keep
        return delay, loss, delay + float(w_loss) * loss


def rho_matrix_from_cell(
    mode: str,
    rho_bar: float,
    sigma: float,
    seed: int,
    tau: float = TAU,
    n: int = N,
    dt: float = DT,
    source: str = RHO_SOURCE,
) -> np.ndarray:
    """Return ``rho[t, link]`` for a Phase 20R operating cell.

    ``calibration_ar1`` matches ``sla_calib_v2`` and ``predict_err_quick``:
    independent AR(1) streams per link around the Q7 offset means. The
    ``scalar_ou`` source is kept only as a diagnostic because Q7 warns that
    common-mode rho can lock the path ranking and create artificial err ~= 0.
    """
    if source == "calibration_ar1":
        return SLA.ar1_matrix(mode, rho_bar, sigma, tau=tau, dt=dt, n=n, seed=seed)
    if source != "scalar_ou":
        raise ValueError("unknown rho source %r" % source)
    traj = ou_trajectory(
        rho_bar=float(rho_bar),
        sigma_rho=float(sigma),
        tau_rho=float(tau),
        n_steps=int(n),
        seed=int(seed),
        dt=float(dt),
    )
    rho_t = np.asarray(traj.rho, dtype=float)
    return np.stack(
        [np.clip(rho_t + C.LINK_OFFSET[link], C.RHO_MIN, C.RHO_MAX) for link in T7.LINK_NAMES],
        axis=1,
    )


def _viol(delay: np.ndarray, loss: np.ndarray, t_delay_ms: float, t_loss: float) -> np.ndarray:
    return (delay > float(t_delay_ms)) | (loss > float(t_loss))


def _decomposition(
    d_true: np.ndarray,
    d_fresh: np.ndarray,
    k: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    m = slice(k, len(d_true))
    d_twin = d_fresh[: len(d_true) - k] if k else d_fresh
    e_model = d_true[m] - d_fresh[m]
    e_stale = d_fresh[m] - d_twin
    total = d_true[m] - d_twin
    if not np.allclose(e_model + e_stale, total, atol=1e-9):
        raise AssertionError("phan ra khong khop")
    return e_model, e_stale, total


def run_cell(
    tt: TruthTable,
    cv2: C.CostV2,
    cal_cell: Mapping[str, Any],
    seed: int,
    tau: float = TAU,
    n: int = N,
    dt: float = DT,
    z_values: Sequence[float] = Z_ALL,
    rho_source: str = RHO_SOURCE,
) -> Dict[str, Any]:
    check_z_grid(z_values, dt)
    mode = str(cal_cell["mode"])
    rho_bar = float(cal_cell["rho_bar"])
    sigma = float(cal_cell["sigma_rho"])
    w_loss = float(cal_cell["w_loss"])
    t_delay = float(cal_cell["t_delay_ms"])
    t_loss = float(cal_cell["t_loss"])

    tt.reset_clip_log()
    rho_mat = rho_matrix_from_cell(mode, rho_bar, sigma, seed, tau=tau, n=n, dt=dt, source=rho_source)
    d_true, l_true, c_true = tt.path_tables(mode, rho_mat, w_loss)
    d_fresh, l_fresh, c_fresh = cv2.tables_batch(rho_mat, mode, w_loss)
    a_true = c_true.argmin(axis=1)
    a_fresh = c_fresh.argmin(axis=1)
    viol = _viol(d_true, l_true, t_delay, t_loss)
    err_model_const = float((a_fresh != a_true).mean())

    out: Dict[str, Any] = {
        "mode": mode,
        "rho_bar": rho_bar,
        "seed": int(seed),
        "tau_rho": float(tau),
        "sigma_rho": sigma,
        "n": int(n),
        "dt": float(dt),
        "rho_source": str(rho_source),
        "clip_fraction": dict(tt.clip_log),
        "per_z": {},
    }
    rows = np.arange(int(n))
    for z_s in z_values:
        k = int(round(float(z_s) / float(dt)))
        if k >= int(n):
            raise ValueError("z %.3f exceeds trace length" % float(z_s))
        current = slice(k, int(n))
        lag_rows = rows[: int(n) - k]
        a_twin = a_fresh[: int(n) - k] if k else a_fresh
        a_now = a_fresh[current]
        a_truth = a_true[current]
        e_model, e_stale, _total = _decomposition(d_true, d_fresh, k)
        out["per_z"][z_key(z_s)] = {
            "z_s": float(z_s),
            "z_steps": int(k),
            "err_total": float((a_twin != a_truth).mean()),
            "err_model": err_model_const,
            "err_stale": float((a_twin != a_now).mean()),
            "d_sla": float(viol[current][lag_rows, a_twin].mean() - viol[current][lag_rows, a_truth].mean()),
            "rms_e_model": float(np.sqrt((e_model**2).mean())),
            "rms_e_stale": float(np.sqrt((e_stale**2).mean())),
            "cov_e": float(np.mean(e_model * e_stale)),
            "extrapolated": bool(float(z_s) in Z_EXTRAP),
        }
    return out


def block_bootstrap_paired(
    indicators: Mapping[str, np.ndarray],
    block_len: int,
    n_boot: int = N_BOOT,
    seed: int = 7,
) -> Dict[str, Tuple[float, float]]:
    n = len(next(iter(indicators.values())))
    n_blocks = n // int(block_len)
    if n_blocks <= 0:
        raise ValueError("block_len too large for n")
    rng = np.random.default_rng(int(seed))
    acc = {key: np.empty(int(n_boot), dtype=float) for key in indicators}
    offsets = np.arange(int(block_len))[None, :]
    for b in range(int(n_boot)):
        pick = rng.integers(0, n_blocks, size=n_blocks)
        idx = (pick[:, None] * int(block_len) + offsets).ravel()
        for key, values in indicators.items():
            acc[key][b] = np.asarray(values)[idx].mean()
    return {
        key: (float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5)))
        for key, values in acc.items()
    }


def _control_one(
    tt: TruthTable,
    cv2: C.CostV2,
    cal_cell: Mapping[str, Any],
    n: int,
    seed: int,
    rho_source: str,
) -> Dict[str, Any]:
    mode = str(cal_cell["mode"])
    rho_mat = rho_matrix_from_cell(
        mode,
        float(cal_cell["rho_bar"]),
        float(cal_cell["sigma_rho"]),
        int(seed),
        tau=TAU,
        n=int(n),
        dt=DT,
        source=rho_source,
    )
    tt.reset_clip_log()
    _d_true, _l_true, c_true = tt.path_tables(mode, rho_mat, float(cal_cell["w_loss"]))
    a_true = c_true.argmin(axis=1)

    nc1b = float((c_true.argmin(axis=1) != a_true).mean())
    rng = np.random.default_rng(99)
    nc2 = float((rng.integers(0, T7.K, size=int(n)) != a_true).mean())
    nc3 = float((a_true[:-1] != a_true[1:]).mean()) if int(n) > 1 else 0.0
    return {
        "mode": mode,
        "rho_bar": float(cal_cell["rho_bar"]),
        "seed": int(seed),
        "n": int(n),
        "rho_source": str(rho_source),
        "NC1b_perfect_twin": nc1b,
        "NC2_random_twin": nc2,
        "NC3_one_step_churn": nc3,
        "clip_fraction": dict(tt.clip_log),
    }


def controls(
    tt: TruthTable,
    cv2: C.CostV2,
    calibration_path: str = CALIBRATION,
    n: int = CONTROL_N,
    seed: int = 100,
    rho_source: str = RHO_SOURCE,
) -> Dict[str, Any]:
    check = check_z_grid(list(Z_ALL), DT)
    cells = feasible_cells(calibration_path, include_pc1=True)
    rows = [_control_one(tt, cv2, cell, n=n, seed=seed, rho_source=rho_source) for cell in cells]
    pc1 = [row for row in rows if row["mode"] == "cbr"]
    return {
        "phase": "20R.5",
        "script": "measurements.decision_error_v2",
        "n_cells": len(rows),
        "n": int(n),
        "seed": int(seed),
        "rho_source": str(rho_source),
        "z_grid_check": check,
        "summary": {
            "NC1b_max_abs": float(max(abs(row["NC1b_perfect_twin"]) for row in rows)) if rows else math.nan,
            "NC2_min": float(min(row["NC2_random_twin"] for row in rows)) if rows else math.nan,
            "NC2_max": float(max(row["NC2_random_twin"] for row in rows)) if rows else math.nan,
            "NC2_pass_0p72_0p78": bool(rows and all(0.72 <= row["NC2_random_twin"] <= 0.78 for row in rows)),
            "PC1_cbr_one_step_churn_max": float(max((row["NC3_one_step_churn"] for row in pc1), default=0.0)),
        },
        "rows": rows,
    }


def flatten_cell_result(result: Mapping[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for z, metrics in result["per_z"].items():
        rows.append(
            {
                "mode": result["mode"],
                "rho_bar": result["rho_bar"],
                "seed": result["seed"],
                "tau_rho": result["tau_rho"],
                "sigma_rho": result["sigma_rho"],
                "n": result["n"],
                "dt": result["dt"],
                "z_key": z,
                **metrics,
                "clip_fraction_max": max(result["clip_fraction"].values()) if result["clip_fraction"] else 0.0,
            }
        )
    return rows


def run_fixed_grid(
    truth_path: str = TRUTH_TABLE,
    calibration_path: str = CALIBRATION,
    out_path: str = FIXED_OUT,
    n: int = N,
    seeds: Sequence[int] = (101, 102, 103, 104, 105),
    rho_source: str = RHO_SOURCE,
) -> pd.DataFrame:
    tt = TruthTable(truth_path)
    cv2 = C.CostV2(strict_reliable=False)
    rows = []
    for cell in feasible_cells(calibration_path, include_pc1=True):
        for seed in seeds:
            rows.extend(flatten_cell_result(run_cell(tt, cv2, cell, seed=seed, n=n, rho_source=rho_source)))
    table = pd.DataFrame(rows)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(out, index=False)
    return table


def parse_int_list(text: str) -> Tuple[int, ...]:
    vals = [int(part.strip()) for part in str(text).split(",") if part.strip()]
    if not vals:
        raise ValueError("expected at least one seed")
    return tuple(vals)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--truth-table", default=TRUTH_TABLE)
    ap.add_argument("--calibration", default=CALIBRATION)
    ap.add_argument("--control", action="store_true", help="run mandatory controls first")
    ap.add_argument("--control-out", default=CONTROLS_OUT)
    ap.add_argument("--run-fixed", action="store_true", help="run fixed-z grid artifact")
    ap.add_argument("--out", default=FIXED_OUT)
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--control-n", type=int, default=CONTROL_N)
    ap.add_argument("--seeds", default="101,102,103,104,105")
    ap.add_argument("--rho-source", choices=("calibration_ar1", "scalar_ou"), default=RHO_SOURCE)
    args = ap.parse_args(argv)

    tt = TruthTable(args.truth_table)
    cv2 = C.CostV2(strict_reliable=False)
    if args.control:
        report = controls(tt, cv2, args.calibration, n=args.control_n, rho_source=args.rho_source)
        write_json(args.control_out, report)
        print(json.dumps(report["summary"], indent=2, sort_keys=True))
        print("controls -> %s" % args.control_out)
    if args.run_fixed:
        table = run_fixed_grid(
            args.truth_table,
            args.calibration,
            args.out,
            n=args.n,
            seeds=parse_int_list(args.seeds),
            rho_source=args.rho_source,
        )
        print("fixed rows=%d -> %s" % (len(table), args.out))
    if not args.control and not args.run_fixed:
        ap.print_help()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
