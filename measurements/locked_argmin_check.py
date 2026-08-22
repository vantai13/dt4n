#!/usr/bin/env python3
"""Phase 20R.8 -- prove exact-zero decision error is a locked-argmin regime.

Criterion:

    lock_ratio = min_t(cost_second - cost_best) / max_t|cost_twin - cost_true|

If ``lock_ratio > 1``, the twin error is never large enough to close the cost
gap to the runner-up path.  In that cell, ``err = 0`` is mechanically forced
rather than suspiciously lucky.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from measurements import decision_error_v2 as D
from measurements import sla_calib_v2 as SLA
from twin import cost_v2 as C
from twin import topology_v7 as T7


SIGMA = 0.0096
TAU = 1.0
DT = 0.005
N = 200_000
SEEDS = (101, 102, 103, 104, 105)
OUT = "results/SUPERSEDED/phase-20R/locked_argmin_check.json"


def check_cell(tt, cv2, mode: str, rho_bar: float, seed: int, n: int) -> Dict[str, Any]:
    cell = SLA.calibrate_cell(cv2, mode, float(rho_bar), seed=100, n=n, dt=DT, tau=TAU)
    if not cell.get("feasible"):
        return {
            "mode": mode,
            "rho_bar": float(rho_bar),
            "seed": int(seed),
            "feasible": False,
            "reason": cell.get("reason"),
        }

    w_loss = float(cell["w_loss"])
    rho = SLA.ar1_matrix(mode, float(rho_bar), SIGMA, tau=TAU, dt=DT, n=n, seed=int(seed))

    _delay_true, _loss_true, cost_true = tt.path_tables(mode, rho, w_loss)
    _delay_twin, _loss_twin, cost_twin = cv2.tables_batch(rho, mode, w_loss)

    opt = cost_true.argmin(axis=1)
    sorted_cost = np.sort(cost_true, axis=1)
    gap_min = float((sorted_cost[:, 1] - sorted_cost[:, 0]).min())
    twin_err_max = float(np.abs(cost_twin - cost_true).max())
    ratio = gap_min / max(twin_err_max, 1e-12)

    return {
        "mode": mode,
        "rho_bar": float(rho_bar),
        "seed": int(seed),
        "feasible": True,
        "w_loss": w_loss,
        "opt_path_share": {
            T7.PATH_NAMES[k]: float((opt == k).mean()) for k in range(T7.K)
        },
        "n_distinct_optimal_paths": int(len(set(opt.tolist()))),
        "min_cost_gap_ms": gap_min,
        "max_abs_twin_error_ms": twin_err_max,
        "lock_ratio": ratio,
        "argmin_locked": bool(ratio > 1.0),
    }


def run(
    rho_bars: Sequence[float],
    modes: Sequence[str],
    seeds: Sequence[int],
    n: int,
) -> Dict[str, Any]:
    tt = D.TruthTable()
    cv2 = C.CostV2(strict_reliable=False)
    rows: List[Dict[str, Any]] = []
    for mode in modes:
        for rho_bar in rho_bars:
            for seed in seeds:
                rows.append(check_cell(tt, cv2, str(mode), float(rho_bar), int(seed), int(n)))

    feasible = [r for r in rows if r.get("feasible")]
    locked = [r for r in feasible if r["argmin_locked"]]
    unlocked = [r for r in feasible if not r["argmin_locked"]]
    return {
        "phase": "20R.8",
        "schema": "phase20r8/locked_argmin/v1",
        "criterion": (
            "lock_ratio = min_t(cost_second - cost_best) / "
            "max_t|cost_twin - cost_true|"
        ),
        "interpretation": "lock_ratio > 1 => argmin cannot flip => err = 0 is forced",
        "config": {
            "sigma_rho": SIGMA,
            "tau": TAU,
            "dt": DT,
            "n": int(n),
            "seeds": [int(seed) for seed in seeds],
        },
        "summary": {
            "n_cells": len(feasible),
            "n_locked": len(locked),
            "n_unlocked": len(unlocked),
            "locked_cells": sorted(
                {"%s@%.3f" % (r["mode"], r["rho_bar"]) for r in locked}
            ),
        },
        "rows": rows,
    }


def _parse_csv_floats(text: str) -> List[float]:
    return [float(x) for x in str(text).split(",") if x.strip()]


def _parse_csv_ints(text: str) -> List[int]:
    return [int(x) for x in str(text).split(",") if x.strip()]


def _parse_csv_text(text: str) -> List[str]:
    return [x.strip() for x in str(text).split(",") if x.strip()]


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--rho-bars",
        default="0.595,0.625,0.635,0.655,0.685,0.700,0.850,0.925,0.960",
    )
    ap.add_argument("--modes", default="poisson,h2")
    ap.add_argument("--seeds", default=",".join(str(seed) for seed in SEEDS))
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)

    report = run(
        _parse_csv_floats(args.rho_bars),
        _parse_csv_text(args.modes),
        _parse_csv_ints(args.seeds),
        int(args.n),
    )
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")

    print("mode     rho_bar seed | n_opt | min_gap_ms | twin_err_ms | lock_ratio | locked")
    for row in report["rows"]:
        if not row.get("feasible"):
            continue
        print(
            "%-8s %.3f  %3d  |  %d    | %10.4f | %11.4f | %10.2f | %s"
            % (
                row["mode"],
                row["rho_bar"],
                row["seed"],
                row["n_distinct_optimal_paths"],
                row["min_cost_gap_ms"],
                row["max_abs_twin_error_ms"],
                row["lock_ratio"],
                "yes" if row["argmin_locked"] else "no",
            )
        )
    print(
        "\nlocked: %d/%d cells -> %s"
        % (
            report["summary"]["n_locked"],
            report["summary"]["n_cells"],
            report["summary"]["locked_cells"],
        )
    )
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
