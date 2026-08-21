#!/usr/bin/env python3
"""Lesson 23.8[A] -- preregistered sensitivity of the bracket to ``d_sync``."""

from __future__ import annotations

import argparse
import gc
from datetime import datetime, timezone
import json
import os
import time
from typing import Any, Dict, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cert import config_matrix as CM
from cert import eight_cell_sweep as E
from cert import fallback_sweep as F
from cert.build_calib_set_v3 import build_cell
from cert.cell_matrices import git, json_clean, pin


AMENDMENT = "docs/phase-23/00zs-amendment-42.md"
PILOT = "results/phase-23/dsync_bridge_micro_pilot.json"
SLA_ARTIFACT = "results/phase-23/sla_calibration_lesson23_16.json"
LIVE_ARTIFACT = "results/phase-23/live_region_sweep.json"
EIGHT_CELL_ARTIFACT = "results/phase-23/eight_cell_sweep.json"
OUTPUT = "results/phase-23/dsync_sensitivity.json"
FIGURE = "results/phase-23/fig7_dsync_sensitivity.png"

D_SYNC_VALUES = (0.051, 0.175, 0.205, 0.230, 0.260)
TIER_1 = ("poisson@0.900", "poisson@0.925")
TIER_2 = ("poisson@0.850", "poisson@0.960", "h2@0.700")
CELL_SPECS: Dict[str, Dict[str, Any]] = {
    "poisson@0.850": {"mode": "poisson", "rho_bar": 0.850},
    "poisson@0.900": {"mode": "poisson", "rho_bar": 0.900},
    "poisson@0.925": {"mode": "poisson", "rho_bar": 0.925},
    "poisson@0.960": {"mode": "poisson", "rho_bar": 0.960},
    "h2@0.700": {"mode": "h2", "rho_bar": 0.700},
}

BASELINE_TOL = 1e-12
BIN_SHARE_TOL = 1e-4
ERR_AMPLITUDE_MAX = 0.060
A_0925_MAX = 0.018


def labelled_payload() -> Dict[str, Any]:
    """The enforced public label for every artifact from this lesson."""
    return {
        "status": "SENSITIVITY_ONLY",
        "closes_P23A": False,
        "limitation": "This sensitivity analysis does not measure AoI on topology_v7.",
    }


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _baseline(cell: str) -> Dict[str, float]:
    source = LIVE_ARTIFACT if cell == "poisson@0.900" else EIGHT_CELL_ARTIFACT
    row = _load_json(source)["cells"][cell]["lift_swing_F2"]
    return {
        "source": source,
        "err_neo": float(row["err_neo"]),
        "lift": float(row["lift"]),
        "swing": float(row["swing"]),
        "delta": float(row["delta_vs_anchor"]),
    }


def _sign(value: float) -> int:
    return 1 if value > 0.0 else (-1 if value < 0.0 else 0)


def _nondecreasing(values: Sequence[float], atol: float = 1e-15) -> bool:
    return bool(all(float(b) >= float(a) - float(atol) for a, b in zip(values, values[1:])))


def analyze_frame(df: pd.DataFrame) -> Dict[str, Any]:
    """Run the frozen C3/F2 analysis and expose its controls and qhat cell."""
    score, accept = F.c3_accept_set(df)
    crossfit = F.build_crossfit_predictions(df, score, accept)
    test_idx = np.asarray(crossfit["test_idx"], dtype=np.int64)
    f2 = F._risk_summary(crossfit["family_probs"]["F2"], df, accept, test_idx)
    decomposition = E._decomposition_f2(df, accept, test_idx, f2)

    fit = CM.fit_config(
        df[df["is_calib"]],
        "C3",
        1.0,
        alpha=F.ALPHA_FAMILY,
        multiplicity="bonferroni",
    )
    qhat_00 = np.asarray(fit["_q"][(0, 0)], dtype=np.float64)
    return json_clean(
        {
            "n_rows": int(len(df)),
            "n_test": int(len(test_idx)),
            "err_neo": float(decomposition["err_neo"]),
            "lift": float(decomposition["lift"]),
            "swing": float(decomposition["swing"]),
            "lift_minus_swing": float(decomposition["lift"] - decomposition["swing"]),
            "reject_share": float(decomposition["reject_share"]),
            "delta": float(decomposition["delta_vs_anchor"]),
            "identity_residual": float(decomposition["identity_residual"]),
            "qhat_z0_mhat0": [float(x) for x in qhat_00],
            "qhat_z0_mhat0_slot1": float(qhat_00[0]),
            "controls": {
                "row_disjoint": bool(all(row["row_disjoint"] for row in crossfit["folds"])),
                "seed_disjoint": bool(all(row["seed_disjoint"] for row in crossfit["folds"])),
                "identity_residual_le_1e_12": bool(decomposition["identity_residual"] <= 1e-12),
                "families_by_fold": {
                    str(row["scoring_seed"]): row["selected_family"]
                    for row in crossfit["folds"]
                },
            },
        }
    )


def build_and_analyze(cell: str, d_sync: float, n: int) -> Dict[str, Any]:
    spec = CELL_SPECS[cell]
    started = time.perf_counter()
    df, meta = build_cell(
        str(spec["mode"]),
        float(spec["rho_bar"]),
        n=int(n),
        calibration_path=SLA_ARTIFACT,
        d_sync=float(d_sync),
    )
    built = time.perf_counter()
    outcome = analyze_frame(df)
    finished = time.perf_counter()
    row = {
        **labelled_payload(),
        "cell": cell,
        "d_sync_s": float(d_sync),
        "d_sync_source": str(meta["d_sync_source"]),
        "w_loss": float(meta["w_loss"]),
        "sync_period_s": float(meta["sync_period_s"]),
        "z_edges_nominal": {
            "primary": [float(x) for x in meta["z_edges_primary"]],
            "secondary": [float(x) for x in meta["z_edges_secondary"]],
        },
        "z_edges_realised": {
            "min_s": float(meta["z_min_realised_s"]),
            "max_s": float(meta["z_max_realised_s"]),
        },
        "k_min": int(meta["z_step_k_min"]),
        "k_max": int(meta["z_step_k_max"]),
        "bin_shares": [float(x) for x in meta["bin_shares"]],
        "n_valid_rows_per_seed": int(meta["n_valid_rows"]),
        "build_seconds": float(built - started),
        "analysis_seconds": float(finished - built),
        **outcome,
    }
    del df
    gc.collect()
    return json_clean(row)


def summarize_cell(cell: str, rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    ordered = sorted(rows, key=lambda row: float(row["d_sync_s"]))
    nc = next(row for row in ordered if float(row["d_sync_s"]) == 0.051)
    baseline = _baseline(cell)
    gaps = {
        metric: abs(float(nc[metric]) - float(baseline[metric]))
        for metric in ("err_neo", "lift", "swing", "delta")
    }
    err = [float(row["err_neo"]) for row in ordered]
    ls = [float(row["lift_minus_swing"]) for row in ordered]
    delta = [float(row["delta"]) for row in ordered]
    qhat = [float(row["qhat_z0_mhat0_slot1"]) for row in ordered]
    base_shares = np.asarray(nc["bin_shares"], dtype=np.float64)
    bin_gap = max(
        float(np.max(np.abs(np.asarray(row["bin_shares"], dtype=np.float64) - base_shares)))
        for row in ordered
    )
    delta_nc = float(nc["delta"])
    return json_clean(
        {
            "baseline": baseline,
            "M_58_gaps": gaps,
            "M_58_max_abs_gap": max(gaps.values()),
            "M_59_max_bin_share_gap": bin_gap,
            "M_60_w_loss_bitwise_identical": bool(
                len({float(row["w_loss"]).hex() for row in ordered}) == 1
            ),
            "M_61_err_neo_nondecreasing": _nondecreasing(err),
            "M_61_err_neo_amplitude": float(max(err) - min(err)),
            "M_62_LS_sign_invariant": bool(
                all(_sign(value) == _sign(float(nc["lift_minus_swing"])) for value in ls)
            ),
            "M_63_delta_sign_invariant": bool(
                all(_sign(value) == _sign(delta_nc) for value in delta)
            ),
            "M_64_A": float(max(abs(value - delta_nc) for value in delta)),
            "M_65_qhat_slot1_nondecreasing": _nondecreasing(qhat),
            "d_sync_s": [float(row["d_sync_s"]) for row in ordered],
            "err_neo": err,
            "lift_minus_swing": ls,
            "delta": delta,
            "qhat_z0_mhat0_slot1": qhat,
        }
    )


def _tier_pass(summaries: Mapping[str, Mapping[str, Any]], cells: Sequence[str]) -> bool:
    return bool(
        all(
            summaries[cell]["M_62_LS_sign_invariant"]
            and summaries[cell]["M_63_delta_sign_invariant"]
            for cell in cells
        )
    )


def run(n: int = 200_000) -> Dict[str, Any]:
    rows: list[Dict[str, Any]] = []
    print("TIER 1", flush=True)
    for cell in TIER_1:
        for d_sync in D_SYNC_VALUES:
            print(f"  build {cell} d_sync={d_sync:.3f}", flush=True)
            row = build_and_analyze(cell, d_sync, n)
            rows.append(row)
            print(
                "    err=%.6f LS=%+.6f Delta=%+.6f build=%.2fs analyze=%.2fs"
                % (
                    row["err_neo"],
                    row["lift_minus_swing"],
                    row["delta"],
                    row["build_seconds"],
                    row["analysis_seconds"],
                ),
                flush=True,
            )

    summaries = {
        cell: summarize_cell(cell, [row for row in rows if row["cell"] == cell])
        for cell in TIER_1
    }
    tier_1_hit = _tier_pass(summaries, TIER_1)
    tier_2_triggered = not tier_1_hit
    if tier_2_triggered:
        print("TIER 1 MISS -> opening preregistered TIER 2", flush=True)
        for cell in TIER_2:
            for d_sync in D_SYNC_VALUES:
                print(f"  build {cell} d_sync={d_sync:.3f}", flush=True)
                row = build_and_analyze(cell, d_sync, n)
                rows.append(row)
                print(
                    "    err=%.6f LS=%+.6f Delta=%+.6f build=%.2fs analyze=%.2fs"
                    % (
                        row["err_neo"],
                        row["lift_minus_swing"],
                        row["delta"],
                        row["build_seconds"],
                        row["analysis_seconds"],
                    ),
                    flush=True,
                )
        summaries.update(
            {
                cell: summarize_cell(cell, [row for row in rows if row["cell"] == cell])
                for cell in TIER_2
            }
        )

    m58 = bool(all(summary["M_58_max_abs_gap"] <= BASELINE_TOL for summary in summaries.values()))
    m59 = bool(all(summary["M_59_max_bin_share_gap"] <= BIN_SHARE_TOL for summary in summaries.values()))
    m60 = bool(all(summary["M_60_w_loss_bitwise_identical"] for summary in summaries.values()))
    m61 = bool(
        all(
            summary["M_61_err_neo_nondecreasing"]
            and summary["M_61_err_neo_amplitude"] <= ERR_AMPLITUDE_MAX
            for summary in summaries.values()
        )
    )
    m62 = bool(all(summaries[cell]["M_62_LS_sign_invariant"] for cell in TIER_1))
    m63 = bool(all(summaries[cell]["M_63_delta_sign_invariant"] for cell in TIER_1))
    m64 = bool(summaries["poisson@0.925"]["M_64_A"] <= A_0925_MAX)
    m65 = bool(all(summary["M_65_qhat_slot1_nondecreasing"] for summary in summaries.values()))
    controls = {
        "NC_L_w_loss_bitwise": m60,
        "NC_M_baseline_reproduction": m58,
        "NC_N_bin_shares": m59,
        "NC_O_identity": bool(all(row["identity_residual"] <= 1e-12 for row in rows)),
        "NC_P_row_disjoint": bool(all(row["controls"]["row_disjoint"] for row in rows)),
        "NC_P_seed_disjoint": bool(all(row["controls"]["seed_disjoint"] for row in rows)),
        "NC_Q_n_valid_rows_reported": bool(all(row["n_valid_rows_per_seed"] > 0 for row in rows)),
    }
    if not all(controls.values()):
        raise AssertionError("mandatory sensitivity control failed: %s" % controls)

    return json_clean(
        {
            "schema": "dt4n.phase23.dsync_sensitivity.v1",
            "lesson": "23.8A",
            **labelled_payload(),
            "d_sync_s": list(D_SYNC_VALUES),
            "n": int(n),
            "tier_1_cells": list(TIER_1),
            "tier_2_cells": list(TIER_2),
            "tier_2_triggered": tier_2_triggered,
            "stop_rule": (
                "TIER_1_HIT_STOP" if not tier_2_triggered else "TIER_1_MISS_RUN_TIER_2_THEN_STOP"
            ),
            "rows": rows,
            "cells": summaries,
            "metrics": {
                "M_58": m58,
                "M_59": m59,
                "M_60": m60,
                "M_61": m61,
                "M_62": m62,
                "M_63": m63,
                "M_64": m64,
                "M_65": m65,
            },
            "headline": (
                "BRACKET_SIGN_INVARIANT" if m62 else "BRACKET_SIGN_NOT_INVARIANT"
            ),
            "controls": controls,
            "provenance": {
                "script": "cert/dsync_sensitivity.py",
                "git_hash": git("git", "rev-parse", "HEAD"),
                "git_dirty": bool(git("git", "status", "--porcelain", "--untracked-files=no")),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "inputs": [
                    pin(AMENDMENT),
                    pin(PILOT),
                    pin(SLA_ARTIFACT),
                    pin(LIVE_ARTIFACT),
                    pin(EIGHT_CELL_ARTIFACT),
                ],
            },
        }
    )


def plot_report(report: Mapping[str, Any], path: str = FIGURE) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.2))
    colors = plt.get_cmap("tab10")
    for index, (cell, summary) in enumerate(report["cells"].items()):
        x = np.asarray(summary["d_sync_s"], dtype=float) * 1000.0
        color = colors(index)
        axes[0].plot(x, summary["err_neo"], marker="o", label=cell, color=color)
        axes[1].plot(x, summary["lift_minus_swing"], marker="o", label=cell, color=color)
        axes[2].plot(x, summary["delta"], marker="o", label=cell, color=color)
    axes[0].set_ylabel("err_neo")
    axes[1].set_ylabel("lift - swing")
    axes[2].set_ylabel("Delta F2")
    for axis in axes:
        axis.set_xlabel("d_sync (ms)")
        axis.grid(alpha=0.25)
    axes[1].axhline(0.0, color="black", linewidth=0.9)
    axes[2].axhline(0.0, color="black", linewidth=0.9)
    axes[0].legend(fontsize=8)
    fig.suptitle("Lesson 23.8A — d_sync sensitivity (SENSITIVITY_ONLY)")
    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=200_000)
    parser.add_argument("--out", default=OUTPUT)
    parser.add_argument("--figure", default=FIGURE)
    args = parser.parse_args()
    report = run(n=int(args.n))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    plot_report(report, args.figure)
    print(json.dumps({
        "headline": report["headline"],
        "metrics": report["metrics"],
        "controls": report["controls"],
        "stop_rule": report["stop_rule"],
        "tier_2_triggered": report["tier_2_triggered"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
