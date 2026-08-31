#!/usr/bin/env python3
"""G.1 closed-form signal-fraction validation and existing-RAW replay.

``validate`` exercises the preregistered independent per-window ``round()``
pipeline.  It must pass before ``measure`` is allowed to inspect retained RAW.
The cumulative MA(1) estimator is deliberately not used here because G.0 has
no carry accumulator.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

from tools.g1_quant_model import (
    WIRE_BYTES_DEFAULT,
    acf,
    estimate_white_round,
    packet_rho_quantum,
    quant_var_rho_independent_round,
    quant_var_rho_static,
    sigma_min_for_sf,
)


WIRE_BYTES = WIRE_BYTES_DEFAULT
QUANT_MODE = "independent_round"
SIGMA_GRID = (0.01, 0.015, 0.02, 0.03, 0.05, 0.10)
SF_TARGET = 0.85
BURN_IN_S = 20.0

VALIDATION_RECEIPT = Path(
    "results/SMOKE/phase-G/g1_closed_form_validation.json"
)
VALIDATE_SIGMA = (0.01, 0.02, 0.03, 0.05)
VALIDATE_TAU = (3.0, 10.0, 30.0)
VALIDATE_SEEDS = 16
VALIDATE_N = 6000
GATE_SF_ABS_ERR = 0.03
GATE_ACF3_CONTROL = 0.03


def git_hash() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() or "unknown"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _synth(
    sigma: float,
    tau: float,
    dt: float,
    n: int,
    rng: np.random.Generator,
    rho_bar: float = 0.857,
    cap_bps: float = 8e6,
) -> np.ndarray:
    """AR(1) -> independent window round -> wire-rate measurement."""
    phi = float(np.exp(-dt / tau))
    signal = np.empty(n)
    signal[0] = rng.standard_normal()
    innovations = rng.standard_normal(n)
    scale = float(np.sqrt(1.0 - phi * phi))
    for index in range(1, n):
        signal[index] = phi * signal[index - 1] + scale * innovations[index]
    offered = rho_bar + sigma * signal
    wanted = offered * cap_bps * dt / (WIRE_BYTES * 8.0)
    counts = np.round(wanted)
    return counts * WIRE_BYTES * 8.0 / (dt * cap_bps)


def stage_validate(out_path: Path) -> bool:
    rng = np.random.default_rng(20260901)
    cells: list[dict[str, object]] = []
    for sigma in VALIDATE_SIGMA:
        for tau in VALIDATE_TAU:
            v_pack = quant_var_rho_independent_round(WIRE_BYTES, 0.2, 8e6)
            sf_true = sigma**2 / (sigma**2 + v_pack)
            sf_estimates = []
            control_errors = []
            reasons = []
            for _ in range(VALIDATE_SEEDS):
                result = estimate_white_round(
                    _synth(sigma, tau, 0.2, VALIDATE_N, rng)
                )
                if result["valid"]:
                    sf_estimates.append(float(result["sf_hat"]))
                    control_errors.append(float(result["acf3_control_error"]))
                else:
                    reasons.append(str(result["reason"]))
            if sf_estimates:
                sf_median = float(np.median(sf_estimates))
                control_median = float(np.median(control_errors))
                sf_error = abs(sf_median - sf_true)
            else:
                sf_median = control_median = sf_error = float("nan")
            passed = bool(
                len(sf_estimates) == VALIDATE_SEEDS
                and sf_error <= GATE_SF_ABS_ERR
                and control_median <= GATE_ACF3_CONTROL
            )
            cells.append(
                {
                    "dt_s": 0.2,
                    "sigma": sigma,
                    "tau_s": tau,
                    "sf_true": sf_true,
                    "sf_hat_median": sf_median,
                    "sf_abs_error": sf_error,
                    "acf3_control_error_median": control_median,
                    "valid_seeds": len(sf_estimates),
                    "invalid_reasons": reasons,
                    "verdict": "PASS" if passed else "FAIL",
                }
            )
    n_pass = sum(cell["verdict"] == "PASS" for cell in cells)
    artifact = {
        "schema": "dt4n.phase_g.g1_closed_form_validation.v2",
        "stage": "validate",
        "status": "SYNTHETIC_NO_NETWORK",
        "git_hash": git_hash(),
        "quantization_mode": QUANT_MODE,
        "wire_bytes": WIRE_BYTES,
        "n_per_cell": VALIDATE_N,
        "gates": {
            "sf_abs_error_max": GATE_SF_ABS_ERR,
            "acf3_control_error_max": GATE_ACF3_CONTROL,
            "valid_seeds_required": VALIDATE_SEEDS,
        },
        "n_cells": len(cells),
        "n_pass": n_pass,
        "overall": "PASS" if n_pass == len(cells) else "FAIL",
        "cells": cells,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print(
        "%7s %6s | %9s %9s %9s | %14s | %s"
        % ("sigma", "tau", "sf_true", "sf_hat", "abs_err", "lag3_control", "verdict")
    )
    for cell in cells:
        print(
            "%7.3f %6.1f | %9.4f %9.4f %9.4f | %14.4f | %s"
            % (
                cell["sigma"],
                cell["tau_s"],
                cell["sf_true"],
                cell["sf_hat_median"],
                cell["sf_abs_error"],
                cell["acf3_control_error_median"],
                cell["verdict"],
            )
        )
    print("\nVALIDATE: %d/%d -> %s" % (n_pass, len(cells), artifact["overall"]))
    return artifact["overall"] == "PASS"


def _load_run(run: Path) -> tuple[dict[str, list[tuple[float, float, float]]], dict]:
    rows: dict[str, list[tuple[float, float, float]]] = collections.defaultdict(list)
    with (run / "rho_measured.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if int(row["sampler_id"]) == 0:
                rows[row["link"]].append(
                    (
                        float(row["monotonic_s"]),
                        float(row["rho"]),
                        float(row["dt_s"]),
                    )
                )
    meta = json.loads((run / "rho_trace_meta.json").read_text(encoding="utf-8"))
    return rows, meta


def _validation_is_current() -> tuple[dict, str]:
    if not VALIDATION_RECEIPT.exists():
        raise SystemExit("REFUSED: validation receipt is missing (NT 53).")
    receipt = json.loads(VALIDATION_RECEIPT.read_text(encoding="utf-8"))
    if receipt.get("overall") != "PASS":
        raise SystemExit("REFUSED: stage validate has not passed (NT 53).")
    if receipt.get("quantization_mode") != QUANT_MODE:
        raise SystemExit("REFUSED: validation used a different quantization mode.")
    return receipt, sha256(VALIDATION_RECEIPT)


def stage_measure(runs: list[Path], out_path: Path) -> None:
    receipt, receipt_sha = _validation_is_current()
    if not runs:
        raise SystemExit("REFUSED: --runs must contain at least one RAW run.")
    results = []
    for run in runs:
        rows, meta = _load_run(run)
        if meta.get("engine") != "static":
            raise SystemExit("REFUSED: existing-RAW decomposition expects static runs")
        links = []
        for link, series in sorted(rows.items()):
            engine = meta["flow_engine"][link]
            cap_bps = float(engine["cap_mbps"]) * 1e6
            rate_pps = float(engine["rate_pps"])
            time_values = np.asarray([item[0] for item in series])
            rho_values = np.asarray([item[1] for item in series])
            dt_values = np.asarray([item[2] for item in series])
            keep = time_values > time_values[0] + BURN_IN_S
            rho_values = rho_values[keep]
            dt_s = float(np.median(dt_values[keep]))
            var_total = float(np.var(rho_values, ddof=1))
            v_static = quant_var_rho_static(
                rate_pps, WIRE_BYTES, dt_s, cap_bps
            )
            v_nonquantized = max(var_total - v_static, 0.0)
            v_round_future = quant_var_rho_independent_round(
                WIRE_BYTES, dt_s, cap_bps
            )
            instrument_var = v_round_future + v_nonquantized
            links.append(
                {
                    "link": link,
                    "cap_mbps": float(engine["cap_mbps"]),
                    "rate_pps": rate_pps,
                    "dt_s": dt_s,
                    "n_samples": int(rho_values.size),
                    "f_frac": float((rate_pps * dt_s) % 1.0),
                    "packet_rho_quantum": packet_rho_quantum(
                        WIRE_BYTES, dt_s, cap_bps
                    ),
                    "var_total_static_raw": var_total,
                    "v_pack_static": v_static,
                    "v_nonquantized_raw": v_nonquantized,
                    "sigma_nonquantized_raw": float(np.sqrt(v_nonquantized)),
                    "v_pack_future_independent_round": v_round_future,
                    "instrument_var_conservative": instrument_var,
                    "sf_by_sigma": {
                        str(sigma): sigma**2 / (sigma**2 + instrument_var)
                        for sigma in SIGMA_GRID
                    },
                    "sigma_min_conservative_sf85": sigma_min_for_sf(
                        WIRE_BYTES,
                        dt_s,
                        cap_bps,
                        sf_target=SF_TARGET,
                        v_path=v_nonquantized,
                        mode=QUANT_MODE,
                    ),
                    "acf1_static_observed": acf(rho_values, 1),
                    "interpretation": (
                        "raw non-quantized residual; event-equivalent, not a "
                        "stationary v_path certificate"
                    ),
                }
            )
        results.append(
            {"run": str(run), "engine": meta["engine"], "n_links": len(links), "links": links}
        )

    binding = max(
        link["sigma_min_conservative_sf85"]
        for result in results
        for link in result["links"]
    )
    artifact = {
        "schema": "dt4n.phase_g.g1_closed_form_measure.v2",
        "stage": "measure",
        "status": "REANALYSIS_EXISTING_RAW_NO_NETWORK",
        "git_hash": git_hash(),
        "wire_bytes": WIRE_BYTES,
        "future_quantization_mode": QUANT_MODE,
        "burn_in_s": BURN_IN_S,
        "sf_target": SF_TARGET,
        "sigma_min_binding_all_runs": binding,
        "validation": {
            "path": str(VALIDATION_RECEIPT),
            "sha256": receipt_sha,
            "overall": receipt["overall"],
        },
        "inputs": [
            {
                "path": str(run / "rho_measured.csv"),
                "sha256": sha256(run / "rho_measured.csv"),
            }
            for run in runs
        ],
        "runs": results,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    for result in results:
        print("\n" + "=" * 111)
        print("RUN %s engine=%s" % (result["run"], result["engine"]))
        print(
            "%5s %4s %7s | %10s %10s %10s %9s | %7s %7s | %8s"
            % (
                "link", "C", "f", "v_total", "v_static", "v_nonq", "sig_nonq",
                "sf@.02", "sf@.03", "sig_min",
            )
        )
        for link in result["links"]:
            print(
                "%5s %4.0f %7.4f | %10.3e %10.3e %10.3e %9.5f | %7.3f %7.3f | %8.4f"
                % (
                    link["link"],
                    link["cap_mbps"],
                    link["f_frac"],
                    link["var_total_static_raw"],
                    link["v_pack_static"],
                    link["v_nonquantized_raw"],
                    link["sigma_nonquantized_raw"],
                    link["sf_by_sigma"]["0.02"],
                    link["sf_by_sigma"]["0.03"],
                    link["sigma_min_conservative_sf85"],
                )
            )
    print("\nBinding conservative sigma_min(sf>=%.2f): %.4f" % (SF_TARGET, binding))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("validate", "measure"), required=True)
    parser.add_argument("--runs", nargs="*", default=[])
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.stage == "validate":
        raise SystemExit(0 if stage_validate(Path(args.out)) else 1)
    stage_measure([Path(value) for value in args.runs], Path(args.out))


if __name__ == "__main__":
    main()
