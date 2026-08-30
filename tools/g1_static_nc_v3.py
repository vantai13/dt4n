#!/usr/bin/env python3
"""NC-G1-static v3: separate packetization from measurement-path residuals."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from tools.summarize_infra import summarize as summarize_infra

LINKS = ("uA", "uB", "ac", "ad", "bc", "bd", "vC", "vD")
TX_NODE = {
    "uA": "sSRC", "uB": "sSRC", "ac": "sA", "ad": "sA",
    "bc": "sB", "bd": "sB", "vC": "sC", "vD": "sD",
}
RX_NODE = {
    "uA": "sA", "uB": "sB", "ac": "sC", "ad": "sD",
    "bc": "sC", "bd": "sD", "vC": "sDST", "vD": "sDST",
}
TELEMETRY_SIDE = {
    "uA": "src", "uB": "src", "vC": "dst", "vD": "dst",
    "ac": "core", "ad": "core", "bc": "core", "bd": "core",
}
BURN_S = 20.0
EXPECTED_WIRE_BYTES = 1442.0
PREREG_TAG = "phase-G-g1-static-nc-v3-prereg"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def measured_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {
        "sample_index", "link", "rho", "tx_bytes_delta", "dt_s",
        "monotonic_s", "read_duration_us",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("%s lacks v3 columns %s" % (path, sorted(missing)))
    return frame


def acf1(values: np.ndarray) -> float:
    if len(values) < 3 or np.std(values[:-1]) == 0 or np.std(values[1:]) == 0:
        return float("nan")
    return float(np.corrcoef(values[:-1], values[1:])[0, 1])


def path_residual(
    measured: pd.DataFrame,
    ledger_path: Path,
    cap_bps: float,
    rate_pps: float,
    ledger_tick_s: float,
) -> tuple[dict[str, object], np.ndarray]:
    """Fit counter bytes to paired packet counts on one monotonic-time grid."""
    frame = measured.sort_values("monotonic_s")
    start = float(frame["monotonic_s"].iloc[0]) + BURN_S
    frame = frame[frame["monotonic_s"] >= start].reset_index(drop=True)
    if len(frame) < 30:
        raise ValueError("insufficient post-burn measured rows")

    ledger = pd.read_csv(ledger_path)
    time_column = "t_mono" if "t_mono" in ledger.columns else "monotonic_s"
    required = {time_column, "cum_packets", "lag_s"}
    missing = required - set(ledger.columns)
    if missing:
        raise ValueError("%s lacks %s" % (ledger_path, sorted(missing)))
    duplicate_fraction = float(1.0 - ledger[time_column].nunique() / len(ledger))
    ledger = ledger.groupby(time_column, as_index=False, sort=True).last()
    ledger_t = ledger[time_column].to_numpy(dtype=float)
    ledger_n = ledger["cum_packets"].to_numpy(dtype=float)
    if len(ledger_t) < 2 or np.any(np.diff(ledger_t) <= 0.0):
        raise ValueError("invalid ledger timestamps in %s" % ledger_path)
    if np.any(np.diff(ledger_n) < 0.0):
        raise ValueError("non-monotone packet ledger in %s" % ledger_path)

    sample_t = frame["monotonic_s"].to_numpy(dtype=float)
    indices = np.searchsorted(ledger_t, sample_t, side="right") - 1
    if np.min(indices) < 0:
        raise ValueError("ledger starts after post-burn measurement grid")
    if sample_t[-1] > ledger_t[-1]:
        raise ValueError("measurement grid extends beyond packet ledger")

    d_packets = np.diff(ledger_n[indices])
    measured_bytes = frame["tx_bytes_delta"].to_numpy(dtype=float)[1:]
    interval_s = frame["dt_s"].to_numpy(dtype=float)[1:]
    if len(d_packets) != len(measured_bytes) or len(d_packets) < 29:
        raise ValueError("paired window length mismatch")
    design = np.column_stack((d_packets, np.ones_like(d_packets)))
    (bytes_per_packet, background), *_ = np.linalg.lstsq(
        design, measured_bytes, rcond=None
    )
    fitted = bytes_per_packet * d_packets + background
    residual_bytes = measured_bytes - fitted
    residual_rho = residual_bytes / (cap_bps * interval_s / 8.0)

    mean_packets = float(np.mean(d_packets))
    mean_dt = float(np.mean(interval_s))
    denom_bytes = cap_bps * mean_dt / 8.0
    # This is in rho^2 and can therefore be added to v_path.  The relative
    # packet-count expression 1/(6*n^2) is retained separately for audit.
    v_pack_rho = float((bytes_per_packet / denom_bytes) ** 2 / 6.0)
    v_pack_relative = float(1.0 / (6.0 * mean_packets**2))
    v_path = float(np.var(residual_rho, ddof=1))
    residual_sd_pkts = (
        float(np.std(residual_bytes, ddof=1) / abs(bytes_per_packet))
        if bytes_per_packet != 0.0
        else float("inf")
    )
    max_gap = float(np.max(np.diff(ledger_t)))
    result = {
        "status": "OK",
        "n_windows": int(len(d_packets)),
        "mean_packets_per_window": mean_packets,
        "bytes_per_packet_fitted": float(bytes_per_packet),
        "background_bytes_per_window": float(background),
        "residual_sd_pkts": residual_sd_pkts,
        "acf1_residual": acf1(residual_rho),
        "v_path": v_path,
        "v_pack_rho_units": v_pack_rho,
        "v_pack_relative_units": v_pack_relative,
        "path_to_pack_ratio": float(v_path / v_pack_rho) if v_pack_rho > 0 else float("nan"),
        "v_measured": float(np.var(frame["rho"].to_numpy(dtype=float)[1:], ddof=1)),
        "ledger": {
            "tick_s": float(ledger_tick_s),
            "max_gap_s": max_gap,
            "align_error_pkts_design": float(rate_pps * ledger_tick_s),
            "align_error_pkts_observed_max": float(rate_pps * max_gap),
            "lag_p95_s": float(np.percentile(ledger["lag_s"], 95)),
            "lag_max_s": float(np.max(ledger["lag_s"])),
            "duplicate_ts_frac": duplicate_fraction,
        },
    }
    result["gates"] = {
        "G1S3-1_bytes_per_packet": bool(abs(bytes_per_packet - EXPECTED_WIRE_BYTES) <= 4.0),
        "G1S3-2_background": bool(
            abs(background) <= 0.01 * abs(bytes_per_packet) * mean_packets
        ),
        "G1S3-3_residual_sd": bool(residual_sd_pkts <= 1.5),
        "G1S3-4_residual_acf": bool(
            np.isfinite(result["acf1_residual"])
            and -0.60 <= float(result["acf1_residual"]) <= 0.15
        ),
        "G1S3-7_alignment_design": bool(rate_pps * ledger_tick_s <= 1.2),
        "G1S3-7b_alignment_observed": bool(rate_pps * max_gap <= 1.2),
        "G1S3-8_no_stall": bool(
            result["ledger"]["lag_p95_s"] <= 0.02
            and result["ledger"]["lag_max_s"] <= 0.05
        ),
    }
    return result, residual_rho


def rho_path_pairs(residuals: dict[str, np.ndarray]) -> list[dict[str, object]]:
    rows = []
    for left, right in itertools.combinations(LINKS, 2):
        n = min(len(residuals[left]), len(residuals[right]))
        correlation = float(np.corrcoef(residuals[left][:n], residuals[right][:n])[0, 1])
        rows.append(
            {
                "pair": "%s-%s" % (left, right),
                "rho_path": correlation,
                "same_tx_node": int(TX_NODE[left] == TX_NODE[right]),
                "same_rx_node": int(RX_NODE[left] == RX_NODE[right]),
                "same_telemetry_side": int(
                    TELEMETRY_SIDE[left] == TELEMETRY_SIDE[right]
                ),
            }
        )
    return rows


def prereg_check(run_git_hash: str) -> dict[str, object]:
    tag = subprocess.run(
        ["git", "rev-list", "-n", "1", PREREG_TAG],
        capture_output=True, text=True, check=False,
    )
    tag_hash = tag.stdout.strip()
    passed = bool(
        tag_hash
        and run_git_hash
        and subprocess.run(
            ["git", "merge-base", "--is-ancestor", tag_hash, run_git_hash],
            check=False,
        ).returncode
        == 0
    )
    return {
        "pass": passed,
        "tag": PREREG_TAG,
        "tag_hash": tag_hash or None,
        "run_git_hash": run_git_hash or None,
    }


def analyse_cell(run_dir: Path, cell: str, rep: int) -> dict[str, object]:
    measured_path = run_dir / "rho_measured.csv"
    sampler1_path = run_dir / "rho_measured_s1.csv"
    meta_path = run_dir / "rho_trace_meta.json"
    infra_path = run_dir / "infra.jsonl"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("engine") != "static":
        raise ValueError("%s is not a static control" % run_dir)
    measured = measured_frame(measured_path)
    per_link: dict[str, dict[str, object]] = {}
    residuals: dict[str, np.ndarray] = {}
    ledger_tick = float(meta.get("offered_dt_s", 0.0))
    for link in LINKS:
        profile = meta["profile"][link]
        result, residual = path_residual(
            measured[measured["link"] == link],
            run_dir / "flow_logs" / ("rho_offered_%s.csv" % link),
            float(profile["cap_mbps"]) * 1e6,
            float(profile["rate_pps"]),
            ledger_tick,
        )
        result["emitter"] = {
            key: meta["flow_engine"].get(link, {}).get(key)
            for key in (
                "packet_shortfall_ratio", "max_lag_s", "max_backlog",
                "n_send_errors", "packets_sent", "max_ledger_gap_s",
                "align_error_pkts_observed_max",
            )
        }
        per_link[link] = result
        residuals[link] = residual

    infra = summarize_infra(infra_path)
    emitters = [per_link[link]["emitter"] for link in LINKS]
    infra_checks = {
        "cpu_p95_lt_40": float(infra["cpu_p95"]) < 40.0,
        "net_drops_zero": int(infra["net_drops"]) == 0,
        "swap_zero": float(infra["swap_max_pct"]) == 0.0,
        "packet_shortfall_le_0p01": all(
            item["packet_shortfall_ratio"] is not None
            and float(item["packet_shortfall_ratio"]) <= 0.01
            for item in emitters
        ),
        "max_lag_le_0p05": all(
            item["max_lag_s"] is not None and float(item["max_lag_s"]) <= 0.05
            for item in emitters
        ),
        "send_errors_zero": all(item["n_send_errors"] == 0 for item in emitters),
    }
    sampler_files_ok = bool(int(meta.get("rho_samplers", 0)) >= 2 and sampler1_path.exists())
    frames = [measured]
    if sampler_files_ok:
        frames.append(measured_frame(sampler1_path))
    read_us = np.concatenate(
        [frame["read_duration_us"].to_numpy(dtype=float) for frame in frames]
    )
    measured_dt = float(meta["measured_window_s"])
    read_p95 = float(np.percentile(read_us, 95))
    implied_error = read_p95 * 1e-6 / measured_dt
    prereg = prereg_check(str(meta.get("git_hash", "")))
    link_gates = {
        gate: all(bool(per_link[link]["gates"][gate]) for link in LINKS)
        for gate in next(iter(per_link.values()))["gates"]
    }
    validity = {
        "G1S3-0_engine_and_two_samplers": sampler_files_ok,
        **link_gates,
        "G1S3-5_infrastructure_clean": all(infra_checks.values()),
        "G1S3-6_preregistered_before_run": bool(prereg["pass"]),
        "G1S3-9_read_error_lt_0p005": implied_error < 0.005,
    }
    pairs = rho_path_pairs(residuals)
    pair_u = next(row for row in pairs if row["pair"] == "uA-uB")
    return {
        "cell": cell,
        "rep": rep,
        "run_dir": str(run_dir),
        "engine": "static",
        "measured_window_s": measured_dt,
        "telemetry_config": {
            "ditto": meta.get("ditto"),
            "aoi_probe": meta.get("aoi_probe_out") is not None,
            "reconcile_every": meta.get("reconcile_every"),
            "measurement_mode": meta.get("measurement_mode"),
        },
        "per_link": per_link,
        "rho_path_pairs": pairs,
        "rho_path_uA_uB": pair_u["rho_path"],
        "rho_path_uA_uB_outcome": (
            "SHARED_PATH_NOISE"
            if pair_u["rho_path"] >= 0.5
            else "CLEAN_PATH"
            if pair_u["rho_path"] <= 0.15
            else "INCONCLUSIVE"
        ),
        "infra": infra,
        "infrastructure_checks": infra_checks,
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
            "rho_measured_s0": sha256(measured_path),
            "rho_measured_s1": sha256(sampler1_path) if sampler1_path.exists() else None,
            "meta": sha256(meta_path),
            "infra": sha256(infra_path),
        },
    }


def dt_control(cells: list[dict[str, object]]) -> dict[str, object]:
    selected = {
        float(cell["measured_window_s"]): cell
        for cell in cells
        if str(cell["cell"]).startswith("D_dt_")
    }
    expected = (0.2, 0.5, 1.0)
    if any(dt not in selected for dt in expected):
        return {"status": "NOT_RUN", "available_dt_s": sorted(selected)}
    rows = {}
    all_pass = True
    for link in LINKS:
        variances = {
            dt: float(selected[dt]["per_link"][link]["v_measured"])
            for dt in expected
        }
        ratio_0p2_0p5 = variances[0.2] / variances[0.5]
        ratio_0p5_1p0 = variances[0.5] / variances[1.0]
        passed = 3.125 <= ratio_0p2_0p5 <= 12.5 and 2.0 <= ratio_0p5_1p0 <= 8.0
        all_pass = all_pass and passed
        rows[link] = {
            "v_measured": {str(key): value for key, value in variances.items()},
            "ratio_0p2_over_0p5": ratio_0p2_0p5,
            "ratio_0p5_over_1p0": ratio_0p5_1p0,
            "expected": {"ratio_0p2_over_0p5": 6.25, "ratio_0p5_over_1p0": 4.0},
            "pass_factor_two_band": passed,
        }
    return {"status": "PASS" if all_pass else "FAIL", "per_link": rows}


def certify(cells: list[dict[str, object]], sigma_grid: list[float]) -> dict[str, object]:
    certificate = {}
    for cell in cells:
        key = str(cell["cell"])
        valid = cell["status"] == "VALID"
        v_by_link = {
            link: float(
                cell["per_link"][link]["v_pack_rho_units"]
                + cell["per_link"][link]["v_path"]
            )
            for link in LINKS
        }
        worst = max(v_by_link.values())
        certificate[key] = {
            "status": "VALID" if valid else "INVALID",
            "failed_validity": [
                gate for gate, passed in cell["validity"].items() if not passed
            ],
            "v_pack_plus_v_path_by_link": v_by_link,
            "v_worst_link": worst,
            "sigma_min_feasible": float(np.sqrt(0.85 * worst / 0.15)),
            "sigma_allowed": [
                sigma for sigma in sigma_grid
                if sigma**2 / (sigma**2 + worst) >= 0.85
            ],
        }
    return certificate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--sigma-grid", default="0.01,0.02,0.03,0.05,0.10")
    parser.add_argument(
        "--out", type=Path,
        default=Path("results/LIVE/phase-G/measurement_path_cert_v3.json"),
    )
    parser.add_argument(
        "--detail-out", type=Path,
        default=Path("results/SMOKE/phase-G/g1_static_nc_v3_detail.json"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sigma_grid = [float(value) for value in args.sigma_grid.split(",")]
    cells = []
    for cell_dir in sorted(path for path in args.campaign.iterdir() if path.is_dir()):
        for rep_dir in sorted(path for path in cell_dir.iterdir() if path.is_dir()):
            cells.append(
                analyse_cell(
                    rep_dir, cell_dir.name,
                    int(rep_dir.name.removeprefix("rep")),
                )
            )
    if not cells:
        raise SystemExit("no campaign cells found under %s" % args.campaign)
    cert = certify(cells, sigma_grid)
    dt_result = dt_control(cells)
    print("\n=== NC-G1-static v3: PAIRED RESIDUAL ===\n")
    print("%-10s %-5s %9s %10s %9s %8s %8s" % (
        "cell", "link", "B_hat", "c_bytes", "sd_pkts", "acf1_R", "vR/vP",
    ))
    for cell in cells:
        for link in LINKS:
            row = cell["per_link"][link]
            print("%-10s %-5s %9.2f %10.1f %9.3f %8.3f %8.3f" % (
                cell["cell"], link, row["bytes_per_packet_fitted"],
                row["background_bytes_per_window"], row["residual_sd_pkts"],
                row["acf1_residual"], row["path_to_pack_ratio"],
            ))
    print("\n=== RUN VALIDITY ===\n")
    for cell in cells:
        failed = [gate for gate, passed in cell["validity"].items() if not passed]
        print("%-10s %-7s cpu_p95=%6.2f rho_path(uA,uB)=%7.3f failed=%s" % (
            cell["cell"], cell["status"], cell["infra"]["cpu_p95"],
            cell["rho_path_uA_uB"], failed,
        ))
    print("\nDT CONTROL: %s" % dt_result["status"])

    git_hash = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    common = {
        "schema": "dt4n.phase_g.g1_static_nc.v3",
        "status": "NEGATIVE_CONTROL_PAIRED_RESIDUAL",
        "constants": {
            "burn_s": BURN_S,
            "expected_wire_bytes": EXPECTED_WIRE_BYTES,
            "sigma_grid": sigma_grid,
            "threshold_sf": 0.85,
        },
        "provenance": {
            "git_hash": git_hash,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/g1_static_nc_v3.py",
            "campaign": str(args.campaign),
            "prereg_tag": PREREG_TAG,
        },
    }
    args.detail_out.parent.mkdir(parents=True, exist_ok=True)
    args.detail_out.write_text(
        json.dumps({**common, "cells": cells, "dt_control": dt_result}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                **common,
                "certificate": cert,
                "dt_control": dt_result,
                "expires_when": "generator, sampler, telemetry, dt, topology, host, or 30-day age changes",
                "detail_artifact": str(args.detail_out),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("\ncert   : %s\ndetail : %s" % (args.out, args.detail_out))


if __name__ == "__main__":
    main()
