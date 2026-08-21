#!/usr/bin/env python3
"""Lesson 23.14 -- robustness of system Delta to objective misspecification."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from typing import Any, Dict, Mapping, Sequence

import numpy as np
import pandas as pd

from cert import fallback_sweep as F
from cert.build_calib_set_v3 import _load_cell
from cert.cell_matrices import TRUTH_TABLE, cell_matrices, git, json_clean, pin
from measurements.decision_error_v2 import TruthTable


AMENDMENT = "docs/phase-23/00zo-amendment-38.md"
FALLBACK_ARTIFACT = F.OUTPUT
OUTPUT = "results/phase-23/objective_misspecification_sweep.json"
FIGURE = "results/phase-23/fig2_objective_misspecification.png"
RATIOS = tuple(float(x) for x in np.linspace(0.5, 1.5, 11))
CELL_META = {
    "poisson@0.925": {"mode": "poisson", "rho_bar": 0.925, "slug": "poisson_0.925"},
    "poisson@0.850": {"mode": "poisson", "rho_bar": 0.850, "slug": "poisson_0.850"},
    "h2@0.700": {"mode": "h2", "rho_bar": 0.700, "slug": "h2_0.700"},
}


def _relative_artifact(cell: str) -> str:
    return "results/phase-23/residual_relative_audit_%s.json" % CELL_META[cell]["slug"]


def _measured_ratio(cell: str) -> float:
    with open(_relative_artifact(cell), "r", encoding="utf-8") as handle:
        rel = float(json.load(handle)["relative_residual"]["relative_point"])
    return 1.0 + rel


def _risk_at_truth(
    a_star: np.ndarray,
    a_twin: np.ndarray,
    accept: np.ndarray,
    test_idx: np.ndarray,
    fallback_probs: np.ndarray,
) -> Dict[str, float]:
    test_accept = accept[test_idx]
    reject_idx = test_idx[~test_accept]
    twin_wrong = (a_twin[test_idx] != a_star[test_idx]).astype(np.float64)
    fb_err = F.expected_error(fallback_probs[reject_idx], a_star[reject_idx])
    c_star = float((a_twin[reject_idx] != a_star[reject_idx]).mean())
    system = twin_wrong.copy()
    system[~test_accept] = fb_err
    gap = float(fb_err.mean() - c_star)
    reject_share = float((~test_accept).mean())
    delta = float(system.mean() - twin_wrong.mean())
    return {
        "err_neo": float(twin_wrong.mean()),
        "c_star_err_twin_given_reject": c_star,
        "err_F_given_reject": float(fb_err.mean()),
        "gap_err_F_reject_minus_c_star": gap,
        "reject_share": reject_share,
        "delta_system_vs_neo": delta,
        "identity_residual": float(abs(delta - reject_share * gap)),
    }


def analyze_cell(cell: str, fallback_report: Mapping[str, Any]) -> Dict[str, Any]:
    meta = CELL_META[cell]
    df = pd.read_parquet(F.CELL_SPECS[cell]["parquet"])
    score, accept = F.c3_accept_set(df)
    crossfit = F.build_crossfit_predictions(df, score, accept)
    test_idx = crossfit["test_idx"]
    selected_probs = crossfit["selected_probs"]
    a_twin = df["a_twin"].to_numpy(np.int64)

    calibration_cell = _load_cell(str(meta["mode"]), float(meta["rho_bar"]))
    w_loss = float(calibration_cell["w_loss"])

    def evaluate(ratio: float) -> Dict[str, Any]:
        mats = cell_matrices(
            TruthTable(TRUTH_TABLE),
            mode=str(meta["mode"]),
            rho_bar=float(meta["rho_bar"]),
            w_loss_override=w_loss * float(ratio),
        )
        a_star = np.asarray(mats["y_true"]).argmin(axis=1)
        if len(a_star) != len(df):
            raise AssertionError("truth/parquet length mismatch")
        row = _risk_at_truth(a_star, a_twin, accept, test_idx, selected_probs)
        row.update(
            {
                "w_eff_over_w_loss": float(ratio),
                "w_loss": w_loss,
                "w_eff": float(w_loss * ratio),
            }
        )
        return row

    curve = [evaluate(ratio) for ratio in RATIOS]
    measured_ratio = _measured_ratio(cell)
    measured = evaluate(measured_ratio)
    at_one = next(row for row in curve if abs(row["w_eff_over_w_loss"] - 1.0) < 1e-12)
    expected = float(
        fallback_report["cells"][cell]["calibration_selected"]["delta_system_vs_neo"]
    )
    gap = abs(float(at_one["delta_system_vs_neo"]) - expected)
    max_identity = max(
        row["identity_residual"] for row in [*curve, measured]
    )
    if gap > 1e-12 or max_identity > 1e-12:
        raise AssertionError(
            "objective controls failed for %s: ratio1_gap=%r identity=%r"
            % (cell, gap, max_identity)
        )
    return json_clean(
        {
            "cell": cell,
            "mode": meta["mode"],
            "rho_bar": meta["rho_bar"],
            "w_loss": w_loss,
            "frozen_families_by_fold": fallback_report["cells"][cell][
                "calibration_selected"
            ]["families_by_fold"],
            "curve": curve,
            "measured_relative_point": {
                "ratio": measured_ratio,
                "result": measured,
                "source": _relative_artifact(cell),
            },
            "controls": {
                "gate_frozen": True,
                "y_hat_frozen": True,
                "fallback_frozen": True,
                "ratio_1_delta_expected": expected,
                "ratio_1_delta_absolute_gap": gap,
                "ratio_1_reproduced_at_1e_12": bool(gap <= 1e-12),
                "max_identity_residual": max_identity,
            },
        }
    )


def run() -> Dict[str, Any]:
    with open(FALLBACK_ARTIFACT, "r", encoding="utf-8") as handle:
        fallback_report = json.load(handle)
    cells = {cell: analyze_cell(cell, fallback_report) for cell in CELL_META}
    return json_clean(
        {
            "schema": "objective_misspecification_sweep/v1",
            "lesson": "23.14",
            "estimand": "Delta under frozen twin, C3 gate, and calibration-selected fallback",
            "ratios": list(RATIOS),
            "cells": cells,
            "provenance": {
                "script": "cert/objective_misspecification.py",
                "git_hash": git("git", "rev-parse", "HEAD"),
                "git_dirty": bool(git("git", "status", "--porcelain", "--untracked-files=no")),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "inputs": [pin(AMENDMENT), pin(FALLBACK_ARTIFACT), pin(TRUTH_TABLE)]
                + [pin(_relative_artifact(cell)) for cell in CELL_META]
                + [pin(F.CELL_SPECS[cell]["parquet"]) for cell in CELL_META],
            },
        }
    )


def plot(report: Mapping[str, Any], out_path: str = FIGURE) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    for cell, payload in report["cells"].items():
        x = [row["w_eff_over_w_loss"] for row in payload["curve"]]
        y = [row["delta_system_vs_neo"] for row in payload["curve"]]
        line = ax.plot(x, y, marker="o", linewidth=2, label=cell)[0]
        measured = payload["measured_relative_point"]["result"]
        ax.scatter(
            [measured["w_eff_over_w_loss"]],
            [measured["delta_system_vs_neo"]],
            marker="*",
            s=150,
            color=line.get_color(),
            edgecolor="black",
            linewidth=0.6,
            zorder=5,
        )
    ax.axhline(0.0, color="black", linestyle="--", linewidth=1)
    ax.axvline(1.0, color="gray", linestyle=":", linewidth=1)
    ax.set_xlabel(r"objective ratio $w_{eff}/w_{loss}$")
    ax.set_ylabel(r"$\Delta = R_{system}-R_{neo}$")
    ax.set_title("Objective misspecification with frozen gate and fallback")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def print_report(report: Mapping[str, Any]) -> None:
    print("=== OBJECTIVE MISSPECIFICATION SWEEP ===")
    for cell, payload in report["cells"].items():
        values = [row["delta_system_vs_neo"] for row in payload["curve"]]
        measured = payload["measured_relative_point"]["result"]
        print(
            "%-16s Delta[min,max]=[%+.6f,%+.6f] measured(r=%.6f)=%+.6f"
            % (
                cell,
                min(values),
                max(values),
                measured["w_eff_over_w_loss"],
                measured["delta_system_vs_neo"],
            )
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=OUTPUT)
    parser.add_argument("--figure", default=FIGURE)
    args = parser.parse_args(argv)
    report = run()
    print_report(report)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    plot(report, args.figure)
    print("artifact -> %s" % args.out)
    print("figure   -> %s" % args.figure)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
