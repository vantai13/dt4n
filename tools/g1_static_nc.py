#!/usr/bin/env python3
"""Directly measure v(config) and rho_epsilon for NC-G1-static.

There is no fitted measurement model in this analysis: the primary quantities
are sample variance and sample correlation of a deterministic-load control.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from tools.summarize_infra import summarize as summarize_infra


LINKS = ("uA", "uB", "ac", "ad", "bc", "bd", "vC", "vD")
TX_NODE = {"uA": "sSRC", "uB": "sSRC", "ac": "sA", "ad": "sA", "bc": "sB", "bd": "sB", "vC": "sC", "vD": "sD"}
RX_NODE = {"uA": "sA", "uB": "sB", "ac": "sC", "ad": "sD", "bc": "sC", "bd": "sD", "vC": "sDST", "vD": "sDST"}
TELEMETRY_SIDE = {"uA": "src", "uB": "src", "vC": "dst", "vD": "dst", "ac": "core", "ad": "core", "bc": "core", "bd": "core"}

DT_MEASURED_S = 0.20
BURN_S = 20.0
DRIFT_WINDOWS_S = (25.0, 50.0, 100.0, 200.0)
PREREG_TAG = "phase-G-g1-static-nc-prereg"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_measured(path: Path, column: str = "rho") -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"sample_index", "link", column}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("%s lacks columns %s" % (path, sorted(missing)))
    wide = frame.pivot(index="sample_index", columns="link", values=column)
    return wide[list(LINKS)].dropna()


def load_static_ledger(flow_log_dir: Path, link: str, dt_target: float) -> tuple[np.ndarray, np.ndarray]:
    frame = pd.read_csv(flow_log_dir / ("rho_offered_%s.csv" % link))
    # A delayed emitter can service more than one 10-ms logging deadline in a
    # single loop. Those rows observe the same cumulative state and their
    # timestamps can also collapse after six-decimal CSV formatting. Retain
    # the last cumulative state at each observed instant; no packet evidence
    # is discarded and no interpolation is introduced.
    frame = frame.groupby("timestamp_s", as_index=False, sort=True).last()
    times = frame["timestamp_s"].to_numpy(dtype=float)
    cumulative_bytes = frame["cum_bytes"].to_numpy(dtype=float)
    if len(times) < 2 or np.any(np.diff(times) <= 0.0):
        raise ValueError("invalid cumulative ledger for %s" % link)
    edges = np.arange(times[0], times[-1], dt_target)
    indices = np.searchsorted(times, edges)
    indices = indices[indices < len(times)]
    return np.diff(cumulative_bytes[indices]) * 8.0, np.diff(times[indices])


def nugget_direct(values: np.ndarray) -> dict[str, object]:
    v_total = float(np.var(values, ddof=1))
    v_white = float(np.var(np.diff(values), ddof=1) / 2.0)
    return {
        "mean": float(np.mean(values)),
        "v_total": v_total,
        "v_white": v_white,
        "white_ratio": float(v_white / v_total) if v_total > 0.0 else float("nan"),
        "sd_total": float(np.sqrt(v_total)),
        "n": int(len(values)),
    }


def drift_curve(values: np.ndarray, dt_s: float, windows_s: Iterable[float]) -> dict[str, object]:
    result = {}
    for window_s in windows_s:
        width = int(round(window_s / dt_s))
        n_windows = len(values) // max(width, 1)
        if width < 30 or n_windows < 2:
            result[str(window_s)] = {"status": "NOT_IDENTIFIABLE", "n_windows": n_windows}
            continue
        variances = np.asarray(
            [np.var(values[i * width:(i + 1) * width], ddof=1) for i in range(n_windows)]
        )
        cv_null = float(np.sqrt(2.0 / (width - 1)))
        cv_observed = float(np.std(variances, ddof=1) / np.mean(variances))
        result[str(window_s)] = {
            "status": "OK",
            "n_windows": int(n_windows),
            "cv_observed": cv_observed,
            "cv_null_analytic": cv_null,
            "ratio": float(cv_observed / cv_null),
            "stationary": bool(cv_observed <= 2.0 * cv_null),
        }
    return result


def pair_table(wide: pd.DataFrame) -> list[dict[str, object]]:
    rows = []
    for left, right in itertools.combinations(LINKS, 2):
        x = wide[left].to_numpy(dtype=float)
        y = wide[right].to_numpy(dtype=float)
        level = float(np.corrcoef(x, y)[0, 1])
        differenced = float(np.corrcoef(np.diff(x), np.diff(y))[0, 1])
        rows.append(
            {
                "pair": "%s-%s" % (left, right),
                "rho_eps_level": level,
                "rho_eps_diff": differenced,
                "band_agreement": float(abs(level - differenced)),
                "same_tx_node": int(TX_NODE[left] == TX_NODE[right]),
                "same_rx_node": int(RX_NODE[left] == RX_NODE[right]),
                "same_telemetry_side": int(TELEMETRY_SIDE[left] == TELEMETRY_SIDE[right]),
            }
        )
    return rows


def discriminate(rows: list[dict[str, object]], key: str = "rho_eps_level") -> dict[str, object]:
    result = {}
    for label in ("same_tx_node", "same_rx_node", "same_telemetry_side"):
        inside = [float(row[key]) for row in rows if row[label] == 1]
        outside = [float(row[key]) for row in rows if row[label] == 0]
        if not inside or not outside:
            result[label] = {"status": "NO_CONTRAST"}
            continue
        result[label] = {
            "n_in": len(inside),
            "n_out": len(outside),
            "median_in": float(np.median(inside)),
            "median_out": float(np.median(outside)),
            "separation": float(np.median(inside) - np.median(outside)),
            "fully_separated": bool(min(inside) > max(outside)),
        }
    return result


def prereg_check(run_git_hash: str) -> dict[str, object]:
    tag = subprocess.run(
        ["git", "rev-list", "-n", "1", PREREG_TAG], capture_output=True, text=True, check=False
    )
    tag_hash = tag.stdout.strip()
    if not tag_hash or not run_git_hash:
        return {"pass": False, "tag": PREREG_TAG, "tag_hash": tag_hash or None, "run_git_hash": run_git_hash or None}
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", tag_hash, run_git_hash], check=False
    )
    return {
        "pass": ancestry.returncode == 0,
        "tag": PREREG_TAG,
        "tag_hash": tag_hash,
        "run_git_hash": run_git_hash,
    }


def analyse_cell(run_dir: Path, cell: str, rep: int) -> dict[str, object]:
    measured_csv = run_dir / "rho_measured.csv"
    flow_log_dir = run_dir / "flow_logs"
    meta_path = run_dir / "rho_trace_meta.json"
    infra_path = run_dir / "infra.jsonl"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    engine_valid = meta.get("engine") == "static"
    if not engine_valid:
        raise ValueError("%s has engine=%r, expected 'static'" % (run_dir, meta.get("engine")))
    measured_dt = float(meta.get("measured_window_s", DT_MEASURED_S))
    if not np.isclose(measured_dt, DT_MEASURED_S):
        raise ValueError("%s measured window %.6f does not match locked %.6f" % (run_dir, measured_dt, DT_MEASURED_S))

    burn = int(round(BURN_S / measured_dt))
    wide_tx = load_measured(measured_csv, "rho").iloc[burn:]
    wide_rx = load_measured(measured_csv, "rho_rx").iloc[burn:]
    if len(wide_tx) < 30 or len(wide_rx) != len(wide_tx):
        raise ValueError("%s has insufficient post-burn samples" % run_dir)

    per_link = {}
    for link in LINKS:
        values = wide_tx[link].to_numpy(dtype=float)
        direct = nugget_direct(values)
        direct["drift"] = drift_curve(values, measured_dt, DRIFT_WINDOWS_S)
        bits, dts = load_static_ledger(flow_log_dir, link, measured_dt)
        cap_bps = float(meta["profile"][link]["cap_mbps"]) * 1e6
        offered = bits / (cap_bps * dts)
        offered = offered[burn:]
        if len(offered) < 2:
            raise ValueError("%s has insufficient offered samples for %s" % (run_dir, link))
        v_offered = float(np.var(offered, ddof=1))
        offered_share = float(v_offered / direct["v_total"]) if direct["v_total"] > 0.0 else float("nan")
        direct["v_offered"] = v_offered
        direct["offered_share"] = offered_share
        direct["nc_valid_1_generator_flat"] = bool(np.isfinite(offered_share) and offered_share <= 0.10)
        direct["nc_valid_2_white"] = bool(abs(float(direct["white_ratio"]) - 1.0) <= 0.25)
        quant_floor = float(meta["profile"][link]["sigma_quant_floor_0p2s"])
        direct["sigma_quant_floor"] = quant_floor
        direct["v_quant_floor"] = quant_floor**2
        direct["v_above_quant_floor_ratio"] = float(direct["v_total"] / (quant_floor**2))
        summary = meta["flow_engine"].get(link, {})
        direct["emitter"] = {
            key: summary.get(key)
            for key in ("max_lag_s", "n_catchup", "packet_shortfall_ratio", "packets_sent", "n_send_errors")
        }
        per_link[link] = direct

    infra = summarize_infra(infra_path)
    emitter_summaries = [per_link[link]["emitter"] for link in LINKS]
    nc3_checks = {
        "cpu_p95_lt_80": float(infra["cpu_p95"]) < 80.0,
        "net_drops_zero": int(infra["net_drops"]) == 0,
        "swap_zero": float(infra["swap_max_pct"]) == 0.0,
        "packet_shortfall_le_0p01": all(
            item["packet_shortfall_ratio"] is not None and float(item["packet_shortfall_ratio"]) <= 0.01
            for item in emitter_summaries
        ),
        "max_lag_le_0p05": all(
            item["max_lag_s"] is not None and float(item["max_lag_s"]) <= 0.05
            for item in emitter_summaries
        ),
        "send_errors_zero": all(item["n_send_errors"] == 0 for item in emitter_summaries),
    }
    read_us = pd.read_csv(measured_csv)["read_duration_us"].to_numpy(dtype=float)
    read_p95 = float(np.percentile(read_us, 95))
    implied_error = read_p95 * 1e-6 / measured_dt
    read_gate = implied_error < 0.005
    prereg = prereg_check(str(meta.get("git_hash", "")))
    valid_1 = all(bool(per_link[link]["nc_valid_1_generator_flat"]) for link in LINKS)
    valid_2 = all(bool(per_link[link]["nc_valid_2_white"]) for link in LINKS)
    valid_3 = all(nc3_checks.values())
    validity = {
        "G1S-0_engine_static": engine_valid,
        "G1S-1_generator_flat_all_links": valid_1,
        "G1S-2_white_all_links": valid_2,
        "G1S-3_infrastructure_clean": valid_3,
        "G1S-4_preregistered_before_run": bool(prereg["pass"]),
        "G1S-5_read_error_lt_0p005": read_gate,
    }
    return {
        "cell": cell,
        "rep": rep,
        "run_dir": str(run_dir),
        "engine": "static",
        "n_samples_after_burn": int(len(wide_tx)),
        "telemetry_config": {
            "ditto": meta.get("ditto"),
            "aoi_probe": meta.get("aoi_probe_out") is not None,
            "reconcile_every": meta.get("reconcile_every"),
            "measurement_mode": meta.get("measurement_mode"),
        },
        "per_link": per_link,
        "pairs_tx": pair_table(wide_tx),
        "pairs_rx": pair_table(wide_rx),
        "discrimination_tx": discriminate(pair_table(wide_tx)),
        "discrimination_rx": discriminate(pair_table(wide_rx)),
        "infra": infra,
        "nc_valid_3_checks": nc3_checks,
        "preregistration": prereg,
        "read_duration_us": {
            "p50": float(np.percentile(read_us, 50)),
            "p95": read_p95,
            "p99": float(np.percentile(read_us, 99)),
            "max": float(np.max(read_us)),
            "implied_rate_error_p95": implied_error,
        },
        "validity": validity,
        "status": "VALID" if all(validity.values()) else "INVALID",
        "input_sha256": {
            "rho_measured": sha256(measured_csv),
            "meta": sha256(meta_path),
            "infra": sha256(infra_path),
        },
    }


def certify(cells: list[dict[str, object]], sigma_grid: list[float], threshold_sf: float = 0.85) -> dict[str, object]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for cell in cells:
        grouped.setdefault(str(cell["cell"]), []).append(cell)
    certificate = {}
    for key, reps in grouped.items():
        valid = all(rep["status"] == "VALID" for rep in reps)
        base = {
            "status": "VALID" if valid else "INVALID",
            "n_reps": len(reps),
            "n_valid_reps": sum(rep["status"] == "VALID" for rep in reps),
            "telemetry_config": reps[0]["telemetry_config"],
            "failed_validity": sorted(
                {gate for rep in reps for gate, passed in rep["validity"].items() if not passed}
            ),
        }
        if not valid:
            certificate[key] = base
            continue
        v_by_link = {
            link: float(np.median([rep["per_link"][link]["v_total"] for rep in reps]))
            for link in LINKS
        }
        v_worst = float(max(v_by_link.values()))
        sigma_min = float(np.sqrt(threshold_sf * v_worst / (1.0 - threshold_sf)))
        certificate[key] = {
            **base,
            "v_by_link": v_by_link,
            "v_worst_link": v_worst,
            "sigma_min_feasible": sigma_min,
            "sf_at_sigma": {str(sigma): float(sigma**2 / (sigma**2 + v_worst)) for sigma in sigma_grid},
            "sigma_allowed": [sigma for sigma in sigma_grid if sigma**2 / (sigma**2 + v_worst) >= threshold_sf],
            "rho_eps_max_abs": float(max(abs(pair["rho_eps_level"]) for rep in reps for pair in rep["pairs_tx"])),
        }
    return certificate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--sigma-grid", default="0.01,0.02,0.03,0.05,0.10")
    parser.add_argument("--out", type=Path, default=Path("results/LIVE/phase-G/measurement_path_cert.json"))
    parser.add_argument("--detail-out", type=Path, default=Path("results/SMOKE/phase-G/g1_static_nc_detail.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sigma_grid = [float(value) for value in args.sigma_grid.split(",")]
    cells = []
    for cell_dir in sorted(path for path in args.campaign.iterdir() if path.is_dir()):
        for rep_dir in sorted(path for path in cell_dir.iterdir() if path.is_dir()):
            cells.append(analyse_cell(rep_dir, cell_dir.name, int(rep_dir.name.removeprefix("rep"))))
    if not cells:
        raise SystemExit("no campaign cells found under %s" % args.campaign)
    cert = certify(cells, sigma_grid)

    print("\n=== NC-G1-static: DIRECT v AND rho_eps ===\n")
    print("%-5s %-4s %-5s %11s %11s %8s %8s %5s %5s" % ("cell", "rep", "link", "v_total", "v_white", "white%", "off%", "V1", "V2"))
    for cell in cells:
        for link in LINKS:
            row = cell["per_link"][link]
            print(
                "%-5s %-4d %-5s %11.4e %11.4e %8.3f %8.3f %5s %5s"
                % (cell["cell"], cell["rep"], link, row["v_total"], row["v_white"], row["white_ratio"], row["offered_share"], "PASS" if row["nc_valid_1_generator_flat"] else "FAIL", "PASS" if row["nc_valid_2_white"] else "FAIL")
            )
    print("\n=== RUN VALIDITY ===\n")
    for cell in cells:
        print("%-5s rep%-2d %-7s cpu_p95=%6.2f drops=%d read_p95=%7.1fus implied=%7.5f" % (cell["cell"], cell["rep"], cell["status"], cell["infra"]["cpu_p95"], cell["infra"]["net_drops"], cell["read_duration_us"]["p95"], cell["read_duration_us"]["implied_rate_error_p95"]))
    print("\n=== DISCRIMINATION ===\n")
    for cell in cells:
        for counter, block in (("TX", cell["discrimination_tx"]), ("RX", cell["discrimination_rx"])):
            for label, row in block.items():
                print("%-5s rep%-2d %-2s %-22s in=% .4f out=% .4f sep=% .4f full=%s" % (cell["cell"], cell["rep"], counter, label, row["median_in"], row["median_out"], row["separation"], row["fully_separated"]))
    print("\n=== CERTIFICATE ===\n")
    for key, row in cert.items():
        if row["status"] == "VALID":
            print("%-5s VALID v_worst=%.4e sigma_min=%.4f allowed=%s" % (key, row["v_worst_link"], row["sigma_min_feasible"], row["sigma_allowed"]))
        else:
            print("%-5s INVALID failed=%s" % (key, row["failed_validity"]))

    git_hash = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip()
    common = {
        "schema": "dt4n.phase_g.g1_static_nc.v1",
        "status": "NEGATIVE_CONTROL_DIRECT_MEASUREMENT",
        "estimators_used": "NONE (sample variance and correlation only)",
        "constants": {"DT_MEASURED_S": DT_MEASURED_S, "BURN_S": BURN_S, "DRIFT_WINDOWS_S": list(DRIFT_WINDOWS_S), "sigma_grid": sigma_grid, "threshold_sf": 0.85},
        "provenance": {"git_hash": git_hash, "timestamp_utc": datetime.now(timezone.utc).isoformat(), "script": "tools/g1_static_nc.py", "campaign": str(args.campaign), "prereg_tag": PREREG_TAG},
    }
    args.detail_out.parent.mkdir(parents=True, exist_ok=True)
    args.detail_out.write_text(json.dumps({**common, "cells": cells}, indent=2) + "\n", encoding="utf-8")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                **common,
                "certificate": cert,
                "expires_when": "any telemetry configuration, sampling interval, topology, or 30-day age changes",
                "detail_artifact": str(args.detail_out),
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print("\ncert   : %s" % args.out)
    print("detail : %s" % args.detail_out)


if __name__ == "__main__":
    main()
