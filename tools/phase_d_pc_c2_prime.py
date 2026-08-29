#!/usr/bin/env python3
"""D-A001 PC-C2': audit generator tau on offered traces, not counters.

No Mininet is run.  The signed design is
``docs/phase-D/A001-amendment-pc-c2.md``.
"""
from __future__ import annotations

import glob
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from measurements import acf_nugget as N
from measurements import link_corr_matrix as L


EDGE = ("uA", "uB", "vC", "vD")
CELL_A_OFFERED = "results/RAW/phase-23/aoi_v7_campaign/rho_offered_clean_rho0.925_rep*.csv"
CELL_C_OFFERED = "results/RAW/phase-D/cellC/rho_offered_rep*.csv"
CELL_A_MEASURED = "results/RAW/phase-23/aoi_v7_campaign/rho_measured_clean_rho0.925_rep*.csv"
CELL_C_MEASURED = "results/RAW/phase-D/cellC/rho_measured_rep*.csv"
A080 = Path("results/LIVE/phase-23/acf_nugget.json")
CELL_C_ANALYSIS = Path("results/SMOKE/phase-D/cellC_analysis.json")
OUT = Path("results/SMOKE/phase-D/pc_c2_prime.json")
NLAG_DIVISOR = 4
NLAG_CAP = 3000
TAU_RATIO_MIN = 5.0
SIGNAL_FRACTION_C_MIN = 0.75


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def acf_prefix(values: np.ndarray, nlag: int) -> np.ndarray:
    """Biased ACF numerator normalized by lag-zero, evaluated by FFT."""
    values = np.asarray(values, dtype=float)
    centered = values - float(values.mean())
    denominator = float(centered @ centered)
    if denominator <= 0:
        return np.concatenate(([1.0], np.zeros(nlag)))
    fft_len = 1 << (2 * len(centered) - 1).bit_length()
    spectrum = np.fft.rfft(centered, fft_len)
    autocov = np.fft.irfft(spectrum * np.conjugate(spectrum), fft_len)[: nlag + 1]
    return np.asarray(autocov / denominator, dtype=float)


def tau_int(values: np.ndarray, dt: float) -> dict[str, object]:
    nlag = min(len(values) // NLAG_DIVISOR, NLAG_CAP)
    curve = acf_prefix(values, nlag)
    cut = nlag
    for lag in range(1, len(curve)):
        if curve[lag] <= 0:
            cut = lag - 1
            break
    tau = float(dt * (0.5 + curve[1 : cut + 1].sum()))
    return {
        "tau_s": tau,
        "cut_lag": int(cut),
        "nlag": int(nlag),
        "max_lag_s": float(nlag * dt),
        "cut_s": float(cut * dt),
    }


def load_offered(path: str) -> tuple[pd.DataFrame, float]:
    frame = pd.read_csv(path)
    value_col = "rho_offered" if "rho_offered" in frame else "rho"
    wide = frame.pivot(index="sample_index", columns="link", values=value_col).dropna()
    missing = sorted(set(EDGE) - set(wide.columns))
    if missing:
        raise ValueError(f"{path}: missing edge links {missing}")
    per_sample_time = frame.groupby("sample_index")["timestamp_s"].first().loc[wide.index]
    dt = float(np.median(np.diff(per_sample_time.to_numpy())))
    if not (0.009 <= dt <= 0.011):
        raise ValueError(f"{path}: offered dt {dt} outside [0.009,0.011]")
    return wide, dt


def offered_cell(paths: list[str]) -> dict[str, object]:
    if len(paths) != 3:
        raise ValueError(f"expected three offered traces, got {len(paths)}")
    per_run: list[dict[str, object]] = []
    per_link: dict[str, list[float]] = {link: [] for link in EDGE}
    for rep, path in enumerate(paths, 1):
        wide, dt = load_offered(path)
        estimates = {link: tau_int(wide[link].to_numpy(), dt) for link in EDGE}
        for link in EDGE:
            per_link[link].append(float(estimates[link]["tau_s"]))
        per_run.append(
            {
                "rep": rep,
                "path": path,
                "dt_s": dt,
                "n_samples": len(wide),
                "edge": estimates,
            }
        )
    return {
        "per_run": per_run,
        "median_tau_s": {link: float(np.median(values)) for link, values in per_link.items()},
    }


def measured_signal(paths: list[str]) -> dict[str, object]:
    if len(paths) != 3:
        raise ValueError(f"expected three measured traces, got {len(paths)}")
    matrices = [L.load_run(path) for path in paths]
    per_link: dict[str, object] = {}
    for link in EDGE:
        index = L.IDX[link]
        curve = N._mean_acf(matrices, index, N.FIT_LAGS)
        fit = N.fit_nugget(curve, N.FIT_LAGS)
        fit["acf_fit_values"] = {
            str(lag): float(value) for lag, value in zip(N.FIT_LAGS, curve)
        }
        per_link[link] = fit
    valid = all(bool(per_link[link]["valid"]) for link in EDGE)
    fractions = [float(per_link[link]["signal_fraction"]) for link in EDGE if per_link[link]["valid"]]
    return {
        "paths": paths,
        "per_link": per_link,
        "all_edge_fits_valid": valid,
        "median_edge_signal_fraction": float(np.median(fractions)) if fractions else None,
    }


def main() -> None:
    paths = {
        "cell_A_offered": sorted(glob.glob(CELL_A_OFFERED)),
        "cell_C_offered": sorted(glob.glob(CELL_C_OFFERED)),
        "cell_A_measured": sorted(glob.glob(CELL_A_MEASURED)),
        "cell_C_measured": sorted(glob.glob(CELL_C_MEASURED)),
    }
    if any(len(value) != 3 for value in paths.values()):
        raise ValueError({key: len(value) for key, value in paths.items()})

    offered_a = offered_cell(paths["cell_A_offered"])
    offered_c = offered_cell(paths["cell_C_offered"])
    ratios = {
        link: float(offered_a["median_tau_s"][link] / offered_c["median_tau_s"][link])
        for link in EDGE
    }
    median_ratio = float(np.median(list(ratios.values())))
    pc_c2_prime_pass = bool(np.isfinite(median_ratio) and median_ratio >= TAU_RATIO_MIN)

    signal_a = measured_signal(paths["cell_A_measured"])
    signal_c = measured_signal(paths["cell_C_measured"])
    signal_c_median = signal_c["median_edge_signal_fraction"]
    pc_c2_prime_b_pass = bool(
        signal_c["all_edge_fits_valid"]
        and signal_c_median is not None
        and float(signal_c_median) >= SIGNAL_FRACTION_C_MIN
    )

    if not pc_c2_prime_pass:
        label = "GENERATOR_CONTROL_FAIL_CELL_C_REMAINS_INVALID"
    elif not signal_c["all_edge_fits_valid"]:
        label = "REANALYSIS_INVALID_OR_INCOMPLETE"
    elif not pc_c2_prime_b_pass:
        label = "NUGGET_MODEL_MISS_CELL_C_REMAINS_INVALID_FOR_THIS_AMENDMENT"
    else:
        label = "CONTROL_REDESIGN_SUPPORTED_CELL_C_REANALYSIS_VALID"

    a080 = json.loads(A080.read_text(encoding="utf-8"))
    frozen = json.loads(CELL_C_ANALYSIS.read_text(encoding="utf-8"))
    all_inputs = [path for group in paths.values() for path in group] + [str(A080), str(CELL_C_ANALYSIS)]
    artifact = {
        "schema": "dt4n.phase_d.pc_c2_prime.v1",
        "status": "SIGNED_REANALYSIS",
        "preregistration": "docs/phase-D/A001-amendment-pc-c2.md",
        "signed_tag": "phase-D-pc-c2-prime-start",
        "no_new_mininet": True,
        "locked_constants": {
            "offered_nlag": "min(n//4, 3000)",
            "tau_ratio_min": TAU_RATIO_MIN,
            "signal_fraction_C_min": SIGNAL_FRACTION_C_MIN,
            "nugget_fit_lags": list(N.FIT_LAGS),
            "nugget_acf_fit_min": N.ACF_FIT_MIN,
            "measured_dt_s": N.DT_MEASURED_S,
        },
        "PC_C2_prime": {
            "cell_A": offered_a,
            "cell_C": offered_c,
            "ratio_A_over_C": ratios,
            "median_ratio_A_over_C": median_ratio,
            "pass": pc_c2_prime_pass,
        },
        "PC_C2_prime_b": {
            "cell_A_rho0.925": signal_a,
            "cell_C": signal_c,
            "A080_15_run_reference": {
                "median_edge_signal_fraction": a080["adjudication"]["median_edge_signal_fraction"],
                "all_fits_valid": a080["adjudication"]["all_fits_valid"],
                "branch": a080["adjudication"]["branch"],
            },
            "pass": pc_c2_prime_b_pass,
        },
        "adjudication": {
            "label": label,
            "original_cell_C_verdict_preserved": frozen["status"],
            "frozen_cell_C_pooled_fisher_r": frozen["pooled_fisher_r"],
            "may_read_frozen_outcomes_under_A001": bool(
                label == "CONTROL_REDESIGN_SUPPORTED_CELL_C_REANALYSIS_VALID"
            ),
        },
        "provenance": {
            "git_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
            ).stdout.strip(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/phase_d_pc_c2_prime.py",
            "inputs_sha256": {path: sha256(path) for path in all_inputs},
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "PC_C2_prime": {
            "tau_A": offered_a["median_tau_s"],
            "tau_C": offered_c["median_tau_s"],
            "ratios": ratios,
            "median_ratio": median_ratio,
            "pass": pc_c2_prime_pass,
        },
        "PC_C2_prime_b": {
            "signal_A": signal_a["median_edge_signal_fraction"],
            "signal_C": signal_c_median,
            "all_C_valid": signal_c["all_edge_fits_valid"],
            "pass": pc_c2_prime_b_pass,
        },
        "adjudication": artifact["adjudication"],
    }, indent=2))


if __name__ == "__main__":
    main()
