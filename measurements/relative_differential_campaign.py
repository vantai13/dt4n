#!/usr/bin/env python3
"""Analyze the Amendment-36 relative residual Mininet campaign."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from cert.cell_matrices import RESIDUAL, TRUTH_TABLE, cell_matrices, prepare
from measurements import cascade_residual as CR
from measurements import differential_residual as DR
from measurements import decision_error_v2 as D
from measurements import residual_spec as RS
from measurements.additivity_check import calibration_by_cell
from measurements.provenance import env_fingerprint
from mininet.topology_tandem import TANDEM_LINKS, tandem_links_for_path


PATHS = ("P1", "P3")
RHOS = (0.850, 0.925)
SEEDS = tuple(range(101, 109))
N_BOOT = 10_000
BOOT_SEED = 20260821
OUT = "results/phase-23/relative_differential_campaign.json"
ORIGINAL_CI90 = (-0.0101350817936804, -0.008908490679519442)


def split_files(text: str) -> List[str]:
    out = [part.strip() for part in str(text).split(",") if part.strip()]
    if not out:
        raise ValueError("empty state-file list")
    return out


def load_path_states(
    path: str, b_files: Sequence[str], c_files: Sequence[str]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows: Dict[str, List[Dict[str, Any]]] = {"B": [], "C": []}
    proof: Dict[str, List[Dict[str, Any]]] = {"B": [], "C": []}
    inputs: Dict[str, List[Dict[str, str]]] = {"B": [], "C": []}
    for branch, files in (("B", b_files), ("C", c_files)):
        for state_file in files:
            state, selected = DR.read_state(state_file, branch, path)
            rows[branch].extend(selected)
            proof[branch].append(DR.validate_path_proof(state, path))
            inputs[branch].append({"path": state_file, "sha256": DR.sha256_file(state_file)})
    residuals = DR.path_residuals(rows["B"], rows["C"], path)
    expected = {(rho, seed) for rho in RHOS for seed in SEEDS}
    got = {(float(row["rho_bar"]), int(row["seed"])) for row in residuals}
    if got != expected:
        raise ValueError("grid mismatch for %s: missing=%s extra=%s" % (path, sorted(expected - got), sorted(got - expected)))
    return residuals, {"path_proofs": proof, "inputs": inputs}


def paired_bootstrap_ratio(
    low: Sequence[float], high: Sequence[float], n_boot: int = N_BOOT, seed: int = BOOT_SEED
) -> Dict[str, Any]:
    lo = np.asarray(low, dtype=float)
    hi = np.asarray(high, dtype=float)
    if lo.shape != hi.shape or lo.size < 3:
        raise ValueError("paired ratio needs same-shape arrays with n>=3")
    rng = np.random.default_rng(int(seed))
    picks = rng.integers(0, lo.size, size=(int(n_boot), lo.size))
    lo_means = lo[picks].mean(axis=1)
    hi_means = hi[picks].mean(axis=1)
    if np.any(np.isclose(hi_means, 0.0, atol=1e-15)):
        raise ValueError("bootstrap denominator r_rel@0.925 contains zero")
    ratios = lo_means / hi_means
    return {
        "point": float(lo.mean() / hi.mean()),
        "ci90": [float(np.percentile(ratios, 5.0)), float(np.percentile(ratios, 95.0))],
        "n": int(lo.size),
        "n_boot": int(n_boot),
        "bootstrap_seed": int(seed),
    }


def _by_rho_seed(rows: Sequence[Mapping[str, Any]]) -> Dict[float, Dict[int, float]]:
    out: Dict[float, Dict[int, float]] = {}
    for row in rows:
        rho, seed = float(row["rho_bar"]), int(row["seed"])
        if seed in out.setdefault(rho, {}):
            raise ValueError("duplicate relative residual rho=%.3f seed=%d" % (rho, seed))
        out[rho][seed] = float(row["r_relative_loss"])
    return out


def m31(path_rows: Mapping[str, Sequence[Mapping[str, Any]]], n_boot: int) -> Dict[str, Any]:
    out = {}
    for path in PATHS:
        indexed = _by_rho_seed(path_rows[path])
        low = [indexed[0.850][seed] for seed in SEEDS]
        high = [indexed[0.925][seed] for seed in SEEDS]
        result = paired_bootstrap_ratio(low, high, n_boot=n_boot)
        result["r_rel_by_rho_seed"] = {
            "0.850": {str(seed): float(indexed[0.850][seed]) for seed in SEEDS},
            "0.925": {str(seed): float(indexed[0.925][seed]) for seed in SEEDS},
        }
        result["pass"] = bool(0.7 <= result["point"] <= 1.4)
        out[path] = result
    return {"paths": out, "pass": bool(all(row["pass"] for row in out.values()))}


def m32(
    path_rows: Mapping[str, Sequence[Mapping[str, Any]]], n_boot: int
) -> Dict[str, Any]:
    indexed = {path: _by_rho_seed(path_rows[path])[0.925] for path in PATHS}
    base = cell_matrices(D.TruthTable(TRUTH_TABLE), mode="poisson", rho_bar=0.925)
    test = ~prepare(base)["is_calib"]
    loss = np.asarray(base["loss_true"], dtype=float)[test]
    cost = np.asarray(base["y_true"], dtype=float)[test]
    p1, p3 = 0, 2
    gap = np.abs(cost[:, p1] - cost[:, p3])
    denominator = float(np.quantile(gap, 0.05))
    if denominator <= 0.0:
        return {"pass": False, "reason": "q05_gap_is_zero", "q05_gap_ms": denominator}
    cells = calibration_by_cell(D.CALIBRATION)
    w_loss = float(cells[("poisson", 0.925)]["w_loss"])

    rng = np.random.default_rng(BOOT_SEED)
    picks = rng.integers(0, len(SEEDS), size=(int(n_boot), len(SEEDS)))
    p1_values = np.asarray([indexed["P1"][seed] for seed in SEEDS], dtype=float)
    p3_values = np.asarray([indexed["P3"][seed] for seed in SEEDS], dtype=float)
    p1_means = p1_values[picks].mean(axis=1)
    p3_means = p3_values[picks].mean(axis=1)
    safety = np.empty(int(n_boot), dtype=float)
    for i, (r1, r3) in enumerate(zip(p1_means, p3_means)):
        numerator = w_loss * np.abs(loss[:, p1] * r1 - loss[:, p3] * r3)
        safety[i] = float(np.quantile(numerator, 0.95)) / denominator
    point_num = w_loss * np.abs(loss[:, p1] * p1_values.mean() - loss[:, p3] * p3_values.mean())
    point = float(np.quantile(point_num, 0.95)) / denominator
    ci90 = [float(np.percentile(safety, 5.0)), float(np.percentile(safety, 95.0))]
    return {
        "definition": "q95_row(w*abs(loss_P1*rrel_P1-loss_P3*rrel_P3))/q05_row(abs(cost_P1-cost_P3))",
        "point": point,
        "ci90": ci90,
        "upper_ci90": ci90[1],
        "q05_gap_ms": denominator,
        "q95_differential_ms_point": point * denominator,
        "w_loss": w_loss,
        "n_test_rows": int(test.sum()),
        "n_boot": int(n_boot),
        "bootstrap_seed": BOOT_SEED,
        "pass": bool(ci90[1] < 1.0),
    }


def _legacy_state_rows(files: Sequence[str], branch: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    rows = CR.load_rows(files, branch)
    for row in rows:
        if row.get("gate_fail"):
            raise AssertionError("legacy control has invalid row: %s" % row.get("gate_fail"))
    return rows, [{"path": path, "sha256": DR.sha256_file(path)} for path in files]


def m33(legacy_b: Sequence[Mapping[str, Any]], legacy_c: Sequence[Mapping[str, Any]], n_boot: int) -> Dict[str, Any]:
    CR.assert_structural_invariant(legacy_b, legacy_c)
    diffs, baselines, seeds = CR.paired_residuals_with_baseline(
        legacy_b, legacy_c, "poisson", 0.925, "loss"
    )
    if tuple(seeds) != SEEDS:
        raise ValueError("legacy Q3 seeds mismatch: %s" % seeds)
    bs = CR.bootstrap_seed_mean(diffs, n_boot=n_boot, seed=BOOT_SEED)
    original = RS.records_by_mode_channel(RS.load(RESIDUAL))[("poisson", "loss")]
    lo, hi = ORIGINAL_CI90
    return {
        "point": float(bs["point"]),
        "ci90": [float(bs["ci90_lo"]), float(bs["ci90_hi"])],
        "relative_point": float(bs["point"] / np.mean(baselines)),
        "baseline_magnitude": float(np.mean(baselines)),
        "per_seed": {str(seed): float(value) for seed, value in zip(seeds, diffs)},
        "original_point": float(original.point),
        "original_ci90_locked": [lo, hi],
        "pass": bool(lo <= float(bs["point"]) <= hi),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for path in PATHS:
        ap.add_argument("--%s-b" % path.lower(), required=True)
        ap.add_argument("--%s-c" % path.lower(), required=True)
    ap.add_argument("--legacy-b", required=True)
    ap.add_argument("--legacy-c", required=True)
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)

    path_rows: Dict[str, List[Dict[str, Any]]] = {}
    provenance_inputs = {}
    for path in PATHS:
        rows, meta = load_path_states(
            path,
            split_files(getattr(args, "%s_b" % path.lower())),
            split_files(getattr(args, "%s_c" % path.lower())),
        )
        path_rows[path] = rows
        provenance_inputs[path] = meta
    legacy_b_files, legacy_c_files = split_files(args.legacy_b), split_files(args.legacy_c)
    legacy_b, legacy_b_meta = _legacy_state_rows(legacy_b_files, "B")
    legacy_c, legacy_c_meta = _legacy_state_rows(legacy_c_files, "C")

    report = {
        "schema": "phase23/relative_differential_campaign/v1",
        "lesson": "23.7-ter",
        "grid": {"paths": list(PATHS), "rho_bars": list(RHOS), "seeds": list(SEEDS), "mode": "poisson"},
        "M_31_relative_stability": m31(path_rows, args.n_boot),
        "M_32_differential_safety": m32(path_rows, args.n_boot),
        "M_33_legacy_reproduction": m33(legacy_b, legacy_c, args.n_boot),
        "path_residuals": path_rows,
        "provenance": {
            "environment": env_fingerprint(),
            "argv": list(sys.argv),
            "inputs": provenance_inputs,
            "legacy_inputs": {"B": legacy_b_meta, "C": legacy_c_meta},
            "truth_table": {"path": TRUTH_TABLE, "sha256": DR.sha256_file(TRUTH_TABLE)},
            "residual": {"path": RESIDUAL, "sha256": DR.sha256_file(RESIDUAL)},
            "amendment_36": {"path": "docs/phase-23/00zl-amendment-36.md", "sha256": DR.sha256_file("docs/phase-23/00zl-amendment-36.md")},
        },
    }
    report["summary"] = {
        "M_31": bool(report["M_31_relative_stability"]["pass"]),
        "M_32": bool(report["M_32_differential_safety"]["pass"]),
        "M_33": bool(report["M_33_legacy_reproduction"]["pass"]),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print("=== LESSON 23.7-ter: RELATIVE P1/P3 CAMPAIGN ===")
    for path, row in report["M_31_relative_stability"]["paths"].items():
        print("M-31 %s ratio=%+.6f CI90=[%+.6f,%+.6f] -> %s" % (
            path, row["point"], row["ci90"][0], row["ci90"][1], "PASS" if row["pass"] else "FAIL",
        ))
    row = report["M_32_differential_safety"]
    print("M-32 safety=%.6f CI90=[%.6f,%.6f] -> %s" % (
        row["point"], row["ci90"][0], row["ci90"][1], "PASS" if row["pass"] else "FAIL",
    ))
    row = report["M_33_legacy_reproduction"]
    print("M-33 legacy r=%+.9f original_CI90=[%+.9f,%+.9f] -> %s" % (
        row["point"], row["original_ci90_locked"][0], row["original_ci90_locked"][1],
        "PASS" if row["pass"] else "FAIL",
    ))
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
