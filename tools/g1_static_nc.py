#!/usr/bin/env python3
"""NC-G1-static v2: direct variance with mechanism-matched validity gates."""
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
BURN_S = 20.0
DRIFT_WINDOWS_S = (25.0, 50.0, 100.0, 200.0)
PREREG_TAG = "phase-G-g1-static-nc-v2-prereg"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def measured_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"sample_index", "link", "rho", "rho_rx", "monotonic_s", "read_duration_us"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("%s lacks v2 columns %s" % (path, sorted(missing)))
    return frame


def load_measured(path: Path, column: str = "rho") -> pd.DataFrame:
    frame = measured_frame(path)
    wide = frame.pivot(index="sample_index", columns="link", values=column)
    return wide[list(LINKS)].dropna()


def measurement_grid(path: Path) -> np.ndarray:
    frame = measured_frame(path)
    grid = frame.sort_values("sample_index").drop_duplicates("sample_index")["monotonic_s"].to_numpy(dtype=float)
    if len(grid) < 2 or np.any(np.diff(grid) <= 0.0):
        raise ValueError("invalid independent measurement grid in %s" % path)
    return grid


def load_static_ledger_on_grid(flow_log_dir: Path, link: str, grid_monotonic_s: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    """Project cumulative bytes onto the independent counter-sampler clock."""
    raw = pd.read_csv(flow_log_dir / ("rho_offered_%s.csv" % link))
    required = {"monotonic_s", "cum_bytes", "lag_s"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError("v2 ledger for %s lacks %s" % (link, sorted(missing)))
    duplicate_fraction = float(1.0 - raw["monotonic_s"].nunique() / len(raw))
    frame = raw.groupby("monotonic_s", as_index=False, sort=True).last()
    times = frame["monotonic_s"].to_numpy(dtype=float)
    cumulative = frame["cum_bytes"].to_numpy(dtype=float)
    if len(times) < 2 or np.any(np.diff(times) <= 0.0) or np.any(np.diff(cumulative) < 0.0):
        raise ValueError("invalid cumulative ledger for %s" % link)
    if grid_monotonic_s[0] < times[0] or grid_monotonic_s[-1] > times[-1]:
        raise ValueError("measurement grid falls outside ledger for %s" % link)
    cumulative_on_grid = np.interp(grid_monotonic_s, times, cumulative)
    lag = raw["lag_s"].to_numpy(dtype=float)
    stall = {
        "lag_p95_s": float(np.percentile(lag, 95)),
        "lag_max_s": float(np.max(lag)),
        "duplicate_ts_frac": duplicate_fraction,
        "max_ledger_gap_s": float(np.max(np.diff(times))),
    }
    return np.diff(cumulative_on_grid) * 8.0, np.diff(grid_monotonic_s), stall


def nugget_direct(values: np.ndarray, n_pkt_window: float, pace_tick_s: float, rate_pps: float) -> dict[str, object]:
    """Measure variance and classify it against the deterministic-pacer null."""
    v_total = float(np.var(values, ddof=1))
    v_white = float(np.var(np.diff(values), ddof=1) / 2.0)
    white_ratio = float(v_white / v_total) if v_total > 0.0 else float("nan")
    acf1 = float(1.0 - white_ratio)
    backlog_packets = max(1.0, rate_pps * pace_tick_s)
    v_floor_eff = float(2.0 * (backlog_packets**2 / 12.0) / (n_pkt_window**2))
    v_ratio = float(v_total / v_floor_eff) if v_floor_eff > 0.0 else float("nan")
    if v_ratio <= 3.0 and -0.80 <= acf1 <= 0.05:
        noise_class = "QUANT_LIMITED"
    elif abs(acf1) < 0.10:
        noise_class = "WHITE"
    elif acf1 > 0.15:
        noise_class = "SLOW"
    else:
        noise_class = "MIXED"
    return {
        "mean": float(np.mean(values)), "v_total": v_total, "v_white": v_white,
        "white_ratio": white_ratio, "acf1": acf1, "v_floor_eff": v_floor_eff,
        "v_ratio": v_ratio, "noise_class": noise_class,
        "sd_total": float(np.sqrt(v_total)), "n": int(len(values)),
        "g1s_2a_no_slow_component": bool(acf1 <= 0.15),
        "g1s_2b_near_physical_floor": bool(v_ratio <= 5.0),
    }


def drift_curve(values: np.ndarray, dt_s: float, windows_s: Iterable[float]) -> dict[str, object]:
    result = {}
    for window_s in windows_s:
        width = int(round(window_s / dt_s))
        n_windows = len(values) // max(width, 1)
        if width < 30 or n_windows < 2:
            result[str(window_s)] = {"status": "NOT_IDENTIFIABLE", "n_windows": n_windows}
            continue
        variances = np.asarray([np.var(values[i * width:(i + 1) * width], ddof=1) for i in range(n_windows)])
        cv_null = float(np.sqrt(2.0 / (width - 1)))
        cv_observed = float(np.std(variances, ddof=1) / np.mean(variances))
        result[str(window_s)] = {"status": "OK", "n_windows": int(n_windows), "cv_observed": cv_observed, "cv_null_analytic": cv_null, "ratio": float(cv_observed / cv_null), "stationary": bool(cv_observed <= 2.0 * cv_null)}
    return result


def pair_table(wide: pd.DataFrame) -> list[dict[str, object]]:
    rows = []
    for left, right in itertools.combinations(LINKS, 2):
        x, y = wide[left].to_numpy(dtype=float), wide[right].to_numpy(dtype=float)
        level = float(np.corrcoef(x, y)[0, 1])
        differenced = float(np.corrcoef(np.diff(x), np.diff(y))[0, 1])
        rows.append({"pair": "%s-%s" % (left, right), "rho_eps_level": level, "rho_eps_diff": differenced, "band_agreement": float(abs(level - differenced)), "same_tx_node": int(TX_NODE[left] == TX_NODE[right]), "same_rx_node": int(RX_NODE[left] == RX_NODE[right]), "same_telemetry_side": int(TELEMETRY_SIDE[left] == TELEMETRY_SIDE[right])})
    return rows


def discriminate(rows: list[dict[str, object]], key: str = "rho_eps_level") -> dict[str, object]:
    result = {}
    for label in ("same_tx_node", "same_rx_node", "same_telemetry_side"):
        inside = [float(row[key]) for row in rows if row[label] == 1]
        outside = [float(row[key]) for row in rows if row[label] == 0]
        result[label] = {"n_in": len(inside), "n_out": len(outside), "median_in": float(np.median(inside)), "median_out": float(np.median(outside)), "separation": float(np.median(inside) - np.median(outside)), "fully_separated": bool(min(inside) > max(outside))}
    return result


def same_link_sampler_correlations(path_a: Path, path_b: Path, burn_s: float) -> list[dict[str, object]]:
    a, b = measured_frame(path_a), measured_frame(path_b)
    rows = []
    for link in LINKS:
        xa = a[a["link"] == link].sort_values("monotonic_s")
        xb = b[b["link"] == link].sort_values("monotonic_s")
        start = max(float(xa["monotonic_s"].iloc[0]), float(xb["monotonic_s"].iloc[0])) + burn_s
        xa, xb = xa[xa["monotonic_s"] >= start], xb[xb["monotonic_s"] >= start]
        ta, tb = xa["monotonic_s"].to_numpy(dtype=float), xb["monotonic_s"].to_numpy(dtype=float)
        keep = (ta >= tb[0]) & (ta <= tb[-1])
        observed = xa["rho"].to_numpy(dtype=float)[keep]
        interpolated = np.interp(ta[keep], tb, xb["rho"].to_numpy(dtype=float))
        rows.append({"link": link, "rho_same_link_s0_s1": float(np.corrcoef(observed, interpolated)[0, 1]), "n": int(len(observed))})
    return rows


def prereg_check(run_git_hash: str) -> dict[str, object]:
    tag = subprocess.run(["git", "rev-list", "-n", "1", PREREG_TAG], capture_output=True, text=True, check=False)
    tag_hash = tag.stdout.strip()
    passed = bool(tag_hash and run_git_hash and subprocess.run(["git", "merge-base", "--is-ancestor", tag_hash, run_git_hash], check=False).returncode == 0)
    return {"pass": passed, "tag": PREREG_TAG, "tag_hash": tag_hash or None, "run_git_hash": run_git_hash or None}


def analyse_cell(run_dir: Path, cell: str, rep: int) -> dict[str, object]:
    measured_csv, sampler1_csv = run_dir / "rho_measured.csv", run_dir / "rho_measured_s1.csv"
    meta_path, infra_path, flow_log_dir = run_dir / "rho_trace_meta.json", run_dir / "infra.jsonl", run_dir / "flow_logs"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("engine") != "static":
        raise ValueError("%s is not a static control" % run_dir)
    if int(meta.get("rho_samplers", 0)) < 2 or not sampler1_csv.exists():
        raise ValueError("%s lacks the locked independent sampler" % run_dir)
    measured_dt = float(meta["measured_window_s"])
    burn = int(round(BURN_S / measured_dt))
    wide_tx, wide_rx = load_measured(measured_csv, "rho").iloc[burn:], load_measured(measured_csv, "rho_rx").iloc[burn:]
    grid = measurement_grid(measured_csv)
    # Row ``burn`` measures the interval ending at grid[burn], whose left
    # endpoint is grid[burn-1]. Startup coverage before burn is irrelevant and
    # may precede the last child process opening its ledger by a few ms.
    analysis_grid = grid[max(0, burn - 1):]
    if len(wide_tx) < 30:
        raise ValueError("%s has insufficient post-burn samples" % run_dir)
    per_link = {}
    for link in LINKS:
        profile = meta["profile"][link]
        values = wide_tx[link].to_numpy(dtype=float)
        direct = nugget_direct(values, float(profile["rate_pps"]) * measured_dt, float(meta["pace_tick_s"]), float(profile["rate_pps"]))
        direct["drift"] = drift_curve(values, measured_dt, DRIFT_WINDOWS_S)
        bits, dts, stall = load_static_ledger_on_grid(flow_log_dir, link, analysis_grid)
        offered = bits / (float(profile["cap_mbps"]) * 1e6 * dts)
        v_offered = float(np.var(offered, ddof=1))
        direct["v_offered"] = v_offered
        direct["offered_share"] = float(v_offered / direct["v_total"]) if direct["v_total"] > 0 else float("nan")
        direct["stall"] = stall
        direct["g1s_1a_generator_flat"] = bool(np.isfinite(direct["offered_share"]) and direct["offered_share"] <= 0.10)
        direct["g1s_1b_no_stall"] = bool(stall["lag_p95_s"] <= 0.02 and stall["max_ledger_gap_s"] <= 0.05)
        summary = meta["flow_engine"].get(link, {})
        direct["emitter"] = {key: summary.get(key) for key in ("max_lag_s", "max_backlog", "n_catchup", "packet_shortfall_ratio", "packets_sent", "n_send_errors")}
        per_link[link] = direct
    infra = summarize_infra(infra_path)
    emitters = [per_link[link]["emitter"] for link in LINKS]
    infra_checks = {"cpu_p95_lt_40": float(infra["cpu_p95"]) < 40.0, "net_drops_zero": int(infra["net_drops"]) == 0, "swap_zero": float(infra["swap_max_pct"]) == 0.0, "packet_shortfall_le_0p01": all(item["packet_shortfall_ratio"] is not None and float(item["packet_shortfall_ratio"]) <= 0.01 for item in emitters), "max_lag_le_0p05": all(item["max_lag_s"] is not None and float(item["max_lag_s"]) <= 0.05 for item in emitters), "send_errors_zero": all(item["n_send_errors"] == 0 for item in emitters)}
    frames = [measured_frame(measured_csv), measured_frame(sampler1_csv)]
    read_us = np.concatenate([frame["read_duration_us"].to_numpy(dtype=float) for frame in frames])
    read_p95, implied_error = float(np.percentile(read_us, 95)), float(np.percentile(read_us, 95)) * 1e-6 / measured_dt
    prereg = prereg_check(str(meta.get("git_hash", "")))
    quant_count = sum(per_link[link]["noise_class"] == "QUANT_LIMITED" for link in LINKS)
    validity = {"G1S2-0_engine_and_two_samplers": True, "G1S2-1_independent_grid_flat_all_links": all(per_link[link]["g1s_1a_generator_flat"] and per_link[link]["g1s_1b_no_stall"] for link in LINKS), "G1S2-2a_no_slow_all_links": all(per_link[link]["g1s_2a_no_slow_component"] for link in LINKS), "G1S2-2b_at_least_6_quant_limited": quant_count >= 6, "G1S2-3_infrastructure_clean": all(infra_checks.values()), "G1S2-4_preregistered_before_run": bool(prereg["pass"]), "G1S2-5_read_error_lt_0p005": implied_error < 0.005}
    pairs_tx, pairs_rx = pair_table(wide_tx), pair_table(wide_rx)
    return {"cell": cell, "rep": rep, "run_dir": str(run_dir), "engine": "static", "measured_window_s": measured_dt, "n_samples_after_burn": int(len(wide_tx)), "telemetry_config": {"ditto": meta.get("ditto"), "aoi_probe": meta.get("aoi_probe_out") is not None, "reconcile_every": meta.get("reconcile_every"), "measurement_mode": meta.get("measurement_mode")}, "per_link": per_link, "quant_limited_links": quant_count, "pairs_tx": pairs_tx, "pairs_rx": pairs_rx, "discrimination_tx": discriminate(pairs_tx), "discrimination_rx": discriminate(pairs_rx), "independent_sampler": same_link_sampler_correlations(measured_csv, sampler1_csv, BURN_S), "infra": infra, "infrastructure_checks": infra_checks, "preregistration": prereg, "read_duration_us": {"p50": float(np.percentile(read_us, 50)), "p95": read_p95, "p99": float(np.percentile(read_us, 99)), "max": float(np.max(read_us)), "implied_rate_error_p95": implied_error}, "validity": validity, "status": "VALID" if all(validity.values()) else "INVALID", "input_sha256": {"rho_measured_s0": sha256(measured_csv), "rho_measured_s1": sha256(sampler1_csv), "meta": sha256(meta_path), "infra": sha256(infra_path)}}


def certify(cells: list[dict[str, object]], sigma_grid: list[float], threshold_sf: float = 0.85) -> dict[str, object]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for cell in cells:
        grouped.setdefault(str(cell["cell"]), []).append(cell)
    result = {}
    for key, reps in grouped.items():
        valid = all(rep["status"] == "VALID" for rep in reps)
        base = {"status": "VALID" if valid else "INVALID", "n_reps": len(reps), "n_valid_reps": sum(rep["status"] == "VALID" for rep in reps), "telemetry_config": reps[0]["telemetry_config"], "failed_validity": sorted({gate for rep in reps for gate, passed in rep["validity"].items() if not passed})}
        if not valid:
            result[key] = base
            continue
        v_by_link = {link: float(np.median([rep["per_link"][link]["v_total"] for rep in reps])) for link in LINKS}
        v_worst = float(max(v_by_link.values()))
        result[key] = {**base, "v_by_link": v_by_link, "v_worst_link": v_worst, "sigma_min_feasible": float(np.sqrt(threshold_sf * v_worst / (1.0 - threshold_sf))), "sf_at_sigma": {str(s): float(s**2 / (s**2 + v_worst)) for s in sigma_grid}, "sigma_allowed": [s for s in sigma_grid if s**2 / (s**2 + v_worst) >= threshold_sf]}
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--sigma-grid", default="0.01,0.02,0.03,0.05,0.10")
    parser.add_argument("--out", type=Path, default=Path("results/LIVE/phase-G/measurement_path_cert_v2.json"))
    parser.add_argument("--detail-out", type=Path, default=Path("results/SMOKE/phase-G/g1_static_nc_v2_detail.json"))
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
    print("\n=== NC-G1-static v2: DIRECT MEASUREMENT ===\n")
    print("%-5s %-4s %-5s %11s %7s %8s %-13s %5s %5s" % ("cell", "rep", "link", "v_total", "acf1", "v/floor", "class", "V1", "V2"))
    for cell in cells:
        for link in LINKS:
            row = cell["per_link"][link]
            print("%-5s %-4d %-5s %11.4e %7.3f %8.3f %-13s %5s %5s" % (cell["cell"], cell["rep"], link, row["v_total"], row["acf1"], row["v_ratio"], row["noise_class"], "PASS" if row["g1s_1a_generator_flat"] and row["g1s_1b_no_stall"] else "FAIL", "PASS" if row["g1s_2a_no_slow_component"] and row["g1s_2b_near_physical_floor"] else "FAIL"))
    print("\n=== RUN VALIDITY ===\n")
    for cell in cells:
        print("%-5s rep%-2d %-7s quant=%d/8 cpu_p95=%6.2f read_p95=%7.1fus implied=%7.5f" % (cell["cell"], cell["rep"], cell["status"], cell["quant_limited_links"], cell["infra"]["cpu_p95"], cell["read_duration_us"]["p95"], cell["read_duration_us"]["implied_rate_error_p95"]))
    print("\n=== CERTIFICATE ===\n")
    for key, row in cert.items():
        suffix = " failed=%s" % row["failed_validity"] if row["status"] != "VALID" else " sigma_min=%.4f allowed=%s" % (row["sigma_min_feasible"], row["sigma_allowed"])
        print("%-5s %s%s" % (key, row["status"], suffix))
    git_hash = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip()
    common = {"schema": "dt4n.phase_g.g1_static_nc.v2", "status": "NEGATIVE_CONTROL_DIRECT_MEASUREMENT", "estimators_used": "NONE (sample variance/correlation and mechanism-matched diagnostics)", "constants": {"BURN_S": BURN_S, "DRIFT_WINDOWS_S": list(DRIFT_WINDOWS_S), "sigma_grid": sigma_grid, "threshold_sf": 0.85}, "provenance": {"git_hash": git_hash, "timestamp_utc": datetime.now(timezone.utc).isoformat(), "script": "tools/g1_static_nc.py", "campaign": str(args.campaign), "prereg_tag": PREREG_TAG}}
    args.detail_out.parent.mkdir(parents=True, exist_ok=True)
    args.detail_out.write_text(json.dumps({**common, "cells": cells}, indent=2) + "\n", encoding="utf-8")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({**common, "certificate": cert, "expires_when": "any generator, sampler, telemetry, dt, topology, or 30-day age change", "detail_artifact": str(args.detail_out)}, indent=2) + "\n", encoding="utf-8")
    print("\ncert   : %s\ndetail : %s" % (args.out, args.detail_out))


if __name__ == "__main__":
    main()
