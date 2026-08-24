#!/usr/bin/env python3
"""Extend M-125a/b from 8 to 12 cells using the four Wave-4 pairs."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from typing import Any, Dict

import numpy as np
import pandas as pd

from cert.conformal_v2 import ALPHA, conformal_level, empirical_qhat
from cert.cell_matrices import git, json_clean
from measurements.validity import measurement_validity_block
from tools import run_23_20_matrix as runner


BETA = 0.431
M125A_BAND = (0.05, 0.13)
M125B_MAX_ABS = 0.25
LIVE_THRESHOLD = 0.05
BASE = "results/LIVE/phase-23/axis_remeasure_impact_wave1.json"
LEDGER = "results/RUN_LEDGER_wave4.json"
DIGEST = "results/RAW/phase-21R/WAVE4_DIGESTS.json"
OUTPUT = "results/LIVE/phase-23/axis_remeasure_impact_wave4.json"
CELLS = tuple(runner.CELLS_REGION)
COLS = ["z_s", "z_bin", "s_margin", "is_calib", "block_id", "a_twin", "a_star"]


def input_path(cell: str, axis: str) -> str:
    mode, rho = cell.split("@")
    tier = "LIVE" if axis == runner.AX_MEA else "SUPERSEDED"
    return (
        "results/%s/phase-21R/calib_set_%s_%.3f_U0_%s.parquet"
        % (tier, mode, float(rho), axis)
    )


def summarize(path: str) -> Dict[str, Any]:
    df = pd.read_parquet(path, columns=COLS)
    calibration = df[df["is_calib"].astype(bool)]
    test = df[~df["is_calib"].astype(bool)]
    bins: Dict[int, Dict[str, Any]] = {}
    qhat: Dict[int, float] = {}
    for group, rows in calibration.groupby("z_bin", sort=True):
        group = int(group)
        n_blocks = int(rows["block_id"].nunique())
        level = conformal_level(n_blocks, ALPHA)
        if level is None:
            raise AssertionError("khong du block conformal: %s B%d" % (path, group))
        qhat[group] = empirical_qhat(rows["s_margin"].to_numpy(float), level)
        bins[group] = {
            "qhat": qhat[group],
            "z_mean_ms": float(rows["z_s"].mean() * 1000.0),
            "n_calib_blocks": n_blocks,
            "conformal_level": float(level),
        }
    if set(bins) != {0, 1, 2, 3}:
        raise AssertionError("phai co dung bon z_bin: %s" % path)
    return {
        "path": path,
        "q_marginal": float(test["z_bin"].map(qhat).mean()),
        "z_mean_ms": float(calibration["z_s"].mean() * 1000.0),
        "err_neo_test": float((test["a_twin"] != test["a_star"]).mean()),
        "bins": bins,
    }


def analyze_cell(cell: str) -> Dict[str, Any]:
    old = summarize(input_path(cell, runner.AX_LEG))
    new = summarize(input_path(cell, runner.AX_MEA))
    marginal_delta = new["q_marginal"] / old["q_marginal"] - 1.0
    marginal_prediction = (new["z_mean_ms"] / old["z_mean_ms"]) ** BETA - 1.0
    counted = old["err_neo_test"] >= LIVE_THRESHOLD
    bins = []
    for group in range(4):
        qo, qn = old["bins"][group]["qhat"], new["bins"][group]["qhat"]
        zo = old["bins"][group]["z_mean_ms"]
        zn = new["bins"][group]["z_mean_ms"]
        prediction = (zn / zo) ** BETA
        ratio = qn / qo
        deviation = ratio / prediction - 1.0
        bins.append(
            {
                "bin": group,
                "q_old": qo,
                "q_new": qn,
                "z_old_ms": zo,
                "z_new_ms": zn,
                "ratio": ratio,
                "predicted": prediction,
                "deviation": deviation,
                "hit": abs(deviation) <= M125B_MAX_ABS,
            }
        )
    return {
        "M125a": {
            "q_marginal_old": old["q_marginal"],
            "q_marginal_new": new["q_marginal"],
            "delta": marginal_delta,
            "predicted": marginal_prediction,
            "deviation": (1.0 + marginal_delta) / (1.0 + marginal_prediction) - 1.0,
            "hit": M125A_BAND[0] <= marginal_delta <= M125A_BAND[1],
        },
        "M125b_bins": bins,
        "counted_M125b": counted,
        "err_neo_old": old["err_neo_test"],
        "inputs": {"legacy": old["path"], "measured": new["path"]},
    }


def build() -> Dict[str, Any]:
    with open(BASE, "r", encoding="utf-8") as handle:
        base = json.load(handle)
    extension = {cell: analyze_cell(cell) for cell in CELLS}
    all_cells = dict(base["cells"])
    all_cells.update(extension)
    all_bins = [row for cell in all_cells.values() for row in cell["M125b_bins"]]
    counted_bins = [
        row
        for cell in all_cells.values()
        if cell["counted_M125b"]
        for row in cell["M125b_bins"]
    ]
    a_deltas = [cell["M125a"]["delta"] for cell in all_cells.values()]
    counted_cells = [cell for cell, row in all_cells.items() if row["counted_M125b"]]
    ledger = json.load(open(LEDGER, encoding="utf-8"))
    wave4_pass = len(ledger) == 12 and all(row.get("pass") for row in ledger.values())
    m125a_pass = len(all_cells) == 12 and all(
        M125A_BAND[0] <= value <= M125A_BAND[1] for value in a_deltas
    )
    m125b_pass = bool(
        counted_bins
        and sum(row["hit"] for row in counted_bins) / len(counted_bins) >= 0.90
    )
    inputs = [BASE, LEDGER, DIGEST]
    inputs.extend(
        input_path(cell, axis)
        for cell in CELLS
        for axis in (runner.AX_LEG, runner.AX_MEA)
    )
    return json_clean(
        {
            "schema": "dt4n.axis_remeasure_impact_wave4.v1",
            "lesson": "23.21h",
            "prereg": "docs/phase-23/00zzk-amendment-49e.md",
            "beta": BETA,
            "cells": all_cells,
            "wave4_extension_cells": list(CELLS),
            "M125a": {
                "band": list(M125A_BAND),
                "n_cells": len(all_cells),
                "n_hit": sum(row["M125a"]["hit"] for row in all_cells.values()),
                "range_pct": [min(a_deltas) * 100.0, max(a_deltas) * 100.0],
                "pass": m125a_pass,
            },
            "M125b": {
                "max_abs_deviation": M125B_MAX_ABS,
                "n_all": len(all_bins),
                "n_hit_all": sum(row["hit"] for row in all_bins),
                "max_abs_dev_all": max(abs(row["deviation"]) for row in all_bins),
                "counted_cells": counted_cells,
                "n_counted": len(counted_bins),
                "n_hit_counted": sum(row["hit"] for row in counted_bins),
                "share_counted": sum(row["hit"] for row in counted_bins) / len(counted_bins),
                "max_abs_dev_counted": max(abs(row["deviation"]) for row in counted_bins),
                "pass": m125b_pass,
            },
            "gates": {
                "G23_141_wave4_12_builds": wave4_pass,
                "G23_142_expand_12_cells_48_bins": bool(m125a_pass and m125b_pass),
            },
            "validity": measurement_validity_block(
                instrument_module=__import__(__name__, fromlist=["_"]),
                inputs=inputs,
                note=(
                    "Paired U0 legacy/measured comparison on identical Wave-4 "
                    "load realisations; extends the frozen Wave-1 result."
                ),
            ),
            "provenance": {
                "script": "tools/wave4_axis_remeasure_impact.py",
                "git_hash": git("git", "rev-parse", "HEAD"),
                "git_dirty": bool(git("git", "status", "--porcelain")),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            },
        }
    )


def main() -> int:
    report = build()
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("M-125a %d/%d, range %.3f%%..%.3f%%" % (
        report["M125a"]["n_hit"], report["M125a"]["n_cells"],
        report["M125a"]["range_pct"][0], report["M125a"]["range_pct"][1]))
    print("M-125b all %d/%d, counted %d/%d, max counted %.3f%%" % (
        report["M125b"]["n_hit_all"], report["M125b"]["n_all"],
        report["M125b"]["n_hit_counted"], report["M125b"]["n_counted"],
        report["M125b"]["max_abs_dev_counted"] * 100.0))
    print("gates=%s" % json.dumps(report["gates"], sort_keys=True))
    print("artifact -> %s" % OUTPUT)
    return 0 if all(report["gates"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
