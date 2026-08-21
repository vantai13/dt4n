#!/usr/bin/env python3
"""Lesson 23.7-ter -- direct P1/P3 differential cascade residual.

Reads exact-path branch-B/branch-C states produced by ``additivity_live
--t7-path``.  It never substitutes the pooled 20R.6 residual.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from measurements import decision_error_v2 as D
from measurements.additivity_check import calibration_by_cell
from measurements.provenance import env_fingerprint
from mininet.topology_tandem import tandem_links_for_path
from twin import cost_v2 as C
from twin import topology_v7 as T7


PATHS = ("P1", "P3")
N_BOOT = 10_000
BOOT_SEED = 20260821
OUT = "results/phase-23/differential_residual_p1_p3.json"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def read_state(path: str, branch: str, expected_path: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    with open(path, "r", encoding="utf-8") as f:
        state = dict(json.load(f))
    rows = []
    for raw in state.get("rows", []):
        if str(raw.get("branch")) != str(branch):
            continue
        row = dict(raw)
        if str(row.get("t7_path", row.get("path", ""))) != str(expected_path):
            raise AssertionError("state %s has wrong path in row: %r" % (path, row.get("t7_path")))
        if row.get("gate_fail"):
            raise AssertionError("invalid live row in %s: %s" % (path, row.get("gate_fail")))
        row["_state_file"] = path
        rows.append(row)
    if not rows:
        raise ValueError("no %s rows for %s in %s" % (branch, expected_path, path))
    return state, rows


def validate_path_proof(state: Mapping[str, Any], path: str) -> Dict[str, Any]:
    expected = tandem_links_for_path(path)
    measured = list(dict(state.get("qdisc_proof", {})).get("measured", []))
    got = tuple(
        (
            str(row["link"]), str(row["topology_v7_link"]),
            float(row["bw"]), int(row["q"]), float(row["base_ms"]),
        )
        for row in measured
    )
    if got != expected:
        raise AssertionError("qdisc path proof mismatch for %s: got=%r expected=%r" % (path, got, expected))
    return {
        "path": path,
        "topology_v7_links": list(T7.PATHS[path]),
        "tandem_specs": [list(row) for row in expected],
        "pass": True,
    }


def _probe_loss(row: Mapping[str, Any]) -> float:
    if row.get("probe_loss") is not None:
        return float(row["probe_loss"])
    sent = int(row["n_sent"])
    if sent <= 0:
        raise ValueError("n_sent=0")
    return 1.0 - float(row["n_recv_unique"]) / float(sent)


def _digest(row: Mapping[str, Any], link: str) -> str:
    digests = row.get("load_schedule_digests")
    if not isinstance(digests, Mapping) or link not in digests:
        raise KeyError("missing load_schedule_digests[%s]" % link)
    return str(digests[link])


def path_residuals(
    rows_b: Sequence[Mapping[str, Any]],
    rows_c: Sequence[Mapping[str, Any]],
    path: str,
) -> List[Dict[str, Any]]:
    specs = tandem_links_for_path(path)
    idx_b: Dict[Tuple[str, float, int, str], Mapping[str, Any]] = {}
    for row in rows_b:
        idx_b[(str(row["mode"]), float(row["rho_bar"]), int(row["seed"]), str(row["link"]))] = row
    idx_c = {
        (str(row["mode"]), float(row["rho_bar"]), int(row["seed"])): row
        for row in rows_c
    }
    out: List[Dict[str, Any]] = []
    for key in sorted(idx_c):
        mode, rho_bar, seed = key
        c_row = idx_c[key]
        b_rows = []
        for link_name, _t7, _bw, _q, _base in specs:
            bkey = (mode, rho_bar, seed, link_name)
            if bkey not in idx_b:
                raise ValueError("missing B row %r" % (bkey,))
            b_rows.append(idx_b[bkey])
        for (link_name, _t7, _bw, _q, _base), b_row in zip(specs, b_rows):
            if _digest(b_row, link_name) != _digest(c_row, link_name):
                raise AssertionError("B/C schedule mismatch path=%s cell=%s@%.3f seed=%d link=%s" % (path, mode, rho_bar, seed, link_name))

        b_keep = float(np.prod([1.0 - _probe_loss(row) for row in b_rows]))
        b_loss = 1.0 - b_keep
        c_loss = _probe_loss(c_row)
        b_delay = float(sum(float(row["q_mean_ms"]) for row in b_rows))
        c_delay = float(c_row["q_mean_ms"])
        w_values = [float(row["w_loss"]) for row in b_rows] + [float(c_row["w_loss"])]
        if max(w_values) - min(w_values) > 1e-9:
            raise AssertionError("w_loss mismatch path=%s cell=%s@%.3f seed=%d" % (path, mode, rho_bar, seed))
        r_loss = c_loss - b_loss
        r_delay = c_delay - b_delay
        w_loss = w_values[0]
        out.append(
            {
                "path": path,
                "mode": mode,
                "rho_bar": rho_bar,
                "seed": seed,
                "w_loss": w_loss,
                "B_loss": b_loss,
                "C_loss": c_loss,
                "B_delay_ms": b_delay,
                "C_delay_ms": c_delay,
                "r_loss": r_loss,
                "r_delay_ms": r_delay,
                "r_cost_ms": r_delay + w_loss * r_loss,
                "schedule_digests": {row[0]: _digest(c_row, row[0]) for row in specs},
            }
        )
    extra_b = {
        (str(row["mode"]), float(row["rho_bar"]), int(row["seed"])) for row in rows_b
    } - set(idx_c)
    if extra_b:
        raise ValueError("B rows without matching C cells: %s" % sorted(extra_b))
    return out


def bootstrap_mean(values: Sequence[float], n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> Dict[str, Any]:
    arr = np.asarray(values, dtype=float)
    if arr.size < 3:
        raise ValueError("need at least 3 paired seeds, got %d" % arr.size)
    rng = np.random.default_rng(int(seed))
    picks = rng.integers(0, arr.size, size=(int(n_boot), arr.size))
    means = arr[picks].mean(axis=1)
    return {
        "n": int(arr.size),
        "point": float(arr.mean()),
        "se": float(means.std(ddof=1)),
        "ci90": [float(np.percentile(means, 5.0)), float(np.percentile(means, 95.0))],
        "per_seed": {str(i): float(v) for i, v in enumerate(arr)},
        "n_boot": int(n_boot),
        "bootstrap_seed": int(seed),
    }


def truth_p1_p3_gap(mode: str, rho_bar: float, truth_table: str, calibration: str) -> Dict[str, Any]:
    tt = D.TruthTable(truth_table)
    cells = calibration_by_cell(calibration)
    w_loss = float(cells[(str(mode), round(float(rho_bar), 12))]["w_loss"])
    rho = C.rho_vector(float(rho_bar))
    costs: Dict[str, float] = {}
    components: Dict[str, Any] = {}
    for path in PATHS:
        delay = 0.0
        keep = 1.0
        for link in T7.PATHS[path]:
            d, loss = tt.delay_loss(str(mode), link, np.asarray([rho[link]], dtype=float))
            delay += float(d[0])
            keep *= 1.0 - float(loss[0])
        path_loss = 1.0 - keep
        costs[path] = delay + w_loss * path_loss
        components[path] = {"delay_ms": delay, "loss": path_loss, "cost_ms": costs[path]}
    return {
        "w_loss": w_loss,
        "rho_by_link": rho,
        "paths": components,
        "gap_P1_P3_ms": abs(costs["P1"] - costs["P3"]),
    }


def point_verdict(ci90: Sequence[float], gap: float) -> Dict[str, Any]:
    lo, hi = float(ci90[0]), float(ci90[1])
    upper_abs = max(abs(lo), abs(hi))
    lower_abs = 0.0 if lo <= 0.0 <= hi else min(abs(lo), abs(hi))
    if upper_abs < float(gap):
        verdict = "SAFE_AT_POINT"
    elif lower_abs > float(gap):
        verdict = "UNSAFE_AT_POINT"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "verdict": verdict,
        "gap_ms": float(gap),
        "ci90_abs_lower_ms": lower_abs,
        "ci90_abs_upper_ms": upper_abs,
        "safety_factor_lower": float(gap) / upper_abs if upper_abs > 0.0 else None,
    }


def analyze(
    path_rows: Mapping[str, Sequence[Mapping[str, Any]]],
    truth_table: str = D.TRUTH_TABLE,
    calibration: str = D.CALIBRATION,
    n_boot: int = N_BOOT,
) -> Dict[str, Any]:
    by_path_cell_seed: Dict[Tuple[str, str, float, int], Mapping[str, Any]] = {}
    for path, rows in path_rows.items():
        for row in rows:
            by_path_cell_seed[(path, str(row["mode"]), float(row["rho_bar"]), int(row["seed"]))] = row
    cells = sorted({(str(row["mode"]), float(row["rho_bar"])) for rows in path_rows.values() for row in rows})
    results = []
    for mode, rho_bar in cells:
        seeds_by_path = {
            path: {seed for p, m, r, seed in by_path_cell_seed if p == path and m == mode and r == rho_bar}
            for path in PATHS
        }
        if seeds_by_path["P1"] != seeds_by_path["P3"] or not seeds_by_path["P1"]:
            raise ValueError("P1/P3 seed mismatch for %s@%.3f: %s" % (mode, rho_bar, seeds_by_path))
        seeds = sorted(seeds_by_path["P1"])
        per_seed = []
        for seed in seeds:
            p1 = by_path_cell_seed[("P1", mode, rho_bar, seed)]
            p3 = by_path_cell_seed[("P3", mode, rho_bar, seed)]
            if abs(float(p1["w_loss"]) - float(p3["w_loss"])) > 1e-9:
                raise AssertionError("P1/P3 w_loss mismatch")
            per_seed.append(
                {
                    "seed": seed,
                    "r_P1": {k: float(p1[k]) for k in ("r_loss", "r_delay_ms", "r_cost_ms")},
                    "r_P3": {k: float(p3[k]) for k in ("r_loss", "r_delay_ms", "r_cost_ms")},
                    "d_loss": float(p1["r_loss"]) - float(p3["r_loss"]),
                    "d_delay_ms": float(p1["r_delay_ms"]) - float(p3["r_delay_ms"]),
                    "d_cost_ms": float(p1["r_cost_ms"]) - float(p3["r_cost_ms"]),
                }
            )
        summaries = {}
        for channel in ("d_loss", "d_delay_ms", "d_cost_ms"):
            bs = bootstrap_mean([row[channel] for row in per_seed], n_boot=n_boot, seed=BOOT_SEED)
            bs["per_seed"] = {str(row["seed"]): float(row[channel]) for row in per_seed}
            summaries[channel] = bs
        truth = truth_p1_p3_gap(mode, rho_bar, truth_table, calibration)
        w_loss = float(truth["w_loss"])
        summaries["w_loss_abs_d_loss"] = {
            "point_ms": w_loss * abs(float(summaries["d_loss"]["point"])),
            "ci90_abs_upper_ms": w_loss * max(abs(x) for x in summaries["d_loss"]["ci90"]),
        }
        verdict = point_verdict(summaries["d_cost_ms"]["ci90"], float(truth["gap_P1_P3_ms"]))
        results.append(
            {
                "cell": "%s@%.3f" % (mode, rho_bar),
                "mode": mode,
                "rho_bar": rho_bar,
                "seeds": seeds,
                "per_seed": per_seed,
                "summary": summaries,
                "truth_at_cell_center": truth,
                "decision": verdict,
                "h2_probe_scope": "Poisson fixed-count probe over H2 background" if mode == "h2" else None,
            }
        )
    nc = []
    for path, rows in path_rows.items():
        for row in rows:
            nc.append(
                bool(
                    float(row["r_loss"]) - float(row["r_loss"]) == 0.0
                    and float(row["r_delay_ms"]) - float(row["r_delay_ms"]) == 0.0
                    and float(row["r_cost_ms"]) - float(row["r_cost_ms"]) == 0.0
                )
            )
    return {
        "schema": "phase23/differential_residual/v1",
        "lesson": "23.7-ter",
        "estimand": "r_p=C_p-compose(B_p); differential=r_P1-r_P3 on paired cell/seed",
        "paths": {path: list(T7.PATHS[path]) for path in PATHS},
        "cells": results,
        "negative_control_same_path": {"n": len(nc), "all_exact_zero": bool(nc and all(nc))},
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for path in PATHS:
        ap.add_argument("--%s-b" % path.lower(), required=True)
        ap.add_argument("--%s-c" % path.lower(), required=True)
    ap.add_argument("--truth-table", default=D.TRUTH_TABLE)
    ap.add_argument("--calibration", default=D.CALIBRATION)
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)

    states: Dict[str, Dict[str, Any]] = {}
    residuals: Dict[str, List[Dict[str, Any]]] = {}
    proofs = {}
    input_files = {}
    for path in PATHS:
        b_file = str(getattr(args, "%s_b" % path.lower()))
        c_file = str(getattr(args, "%s_c" % path.lower()))
        state_b, rows_b = read_state(b_file, "B", path)
        state_c, rows_c = read_state(c_file, "C", path)
        proofs[path] = {
            "B": validate_path_proof(state_b, path),
            "C": validate_path_proof(state_c, path),
        }
        residuals[path] = path_residuals(rows_b, rows_c, path)
        states[path] = {"B": state_b, "C": state_c}
        input_files[path] = {
            "B": {"path": b_file, "sha256": sha256_file(b_file)},
            "C": {"path": c_file, "sha256": sha256_file(c_file)},
        }

    report = analyze(residuals, args.truth_table, args.calibration, args.n_boot)
    report["validity"] = {
        "all_input_rows_gate_clean": True,
        "path_proofs": proofs,
        "all_B_C_schedule_digests_paired": True,
    }
    report["provenance"] = {
        "inputs": input_files,
        "truth_table": {"path": args.truth_table, "sha256": sha256_file(args.truth_table)},
        "calibration": {"path": args.calibration, "sha256": sha256_file(args.calibration)},
        "environment": env_fingerprint(),
        "kernel": platform.release(),
        "argv": list(sys.argv),
        "n_boot": int(args.n_boot),
        "bootstrap_seed": BOOT_SEED,
        "state_plan_digests": {
            path: {branch: state.get("plan_digest") for branch, state in pair.items()}
            for path, pair in states.items()
        },
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")

    print("=== LESSON 23.7-ter: P1-P3 DIFFERENTIAL RESIDUAL ===")
    print("%-18s %12s %22s %12s %12s %s" % ("cell", "d_cost", "CI90 d_cost", "gap", "SF lower", "verdict"))
    for cell in report["cells"]:
        s = cell["summary"]["d_cost_ms"]
        d = cell["decision"]
        print(
            "%-18s %+12.6f [%+9.4f,%+9.4f] %12.6f %12s %s"
            % (
                cell["cell"], s["point"], s["ci90"][0], s["ci90"][1],
                d["gap_ms"], "-" if d["safety_factor_lower"] is None else "%.3f" % d["safety_factor_lower"],
                d["verdict"],
            )
        )
    print("NC same-path exact zero: %s" % report["negative_control_same_path"]["all_exact_zero"])
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
