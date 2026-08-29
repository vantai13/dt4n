#!/usr/bin/env python3
"""D-A002 PC-C2'': generator control on a baseline branch long enough to measure tau.

Signed design: ``docs/phase-D/00b-prereg-pc-c2-second.md``.
Diagnosis that motivated it: ``docs/phase-D/A002-amendment-pc-c2-prime.md``.

Two locked repairs relative to PC-C2' (A001):

* branch A is a NEW 1505 s run so ``T/tau >= 50`` holds on both branches, and
  ``NLAG_CAP`` is raised symmetrically so the ACF window is no longer the
  binding constraint;
* the signal-fraction estimator is given its physical ``[0,1]`` range plus a
  per-cell ``tau``-normalised fit-lag grid.

Thresholds are unchanged from A001.  Nothing here reads Cell C frozen outcomes.
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

CELL_A_LONG_OFFERED = "results/RAW/phase-D/cellA_long/rho_offered_rep*.csv"
CELL_A_LONG_MEASURED = "results/RAW/phase-D/cellA_long/rho_measured_rep*.csv"
CELL_C_OFFERED = "results/RAW/phase-D/cellC/rho_offered_rep*.csv"
CELL_C_MEASURED = "results/RAW/phase-D/cellC/rho_measured_rep*.csv"
INFRA = Path("results/PENDING/phase-D/infra_cellA_long.jsonl")
A080 = Path("results/LIVE/phase-23/acf_nugget.json")
PC_C2_PRIME = Path("results/SMOKE/phase-D/pc_c2_prime.json")
OUT = Path("results/SMOKE/phase-D/pc_c2_second.json")

# --- constants locked in 00b-prereg-pc-c2-second.md.  Not command-line flags.
NLAG_DIVISOR = 4
NLAG_CAP = 50_000            # A001 used 3_000 and it was BINDING (D-L21)
TAU_RATIO_MIN = 5.0          # unchanged from A001
SIGNAL_FRACTION_A_MAX = 0.50
SIGNAL_FRACTION_C_MIN = 0.75
CEILING_SE_MULT = 3.0        # intercept must not sit significantly above log(1)
A_FIT_LAGS = (30, 40, 50, 65, 80, 100, 125, 155, 190, 240, 300)
C_FIT_LAGS = (3, 4, 5, 6, 8, 10, 13, 16, 21, 26)
TAU_OVER_T_FLOOR = 50.0      # the project's own 55*tau budget floor (D-L15)


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


# ----------------------------------------------------------- PC-C2''a, offered
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
        "cut_at_ceiling": bool(cut == nlag),
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


def offered_cell(paths: list[str], expect_reps: int) -> dict[str, object]:
    if len(paths) != expect_reps:
        raise ValueError(f"expected {expect_reps} offered traces, got {len(paths)}")
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
                "n_samples": int(len(wide)),
                "duration_s": float(len(wide) * dt),
                "edge": estimates,
            }
        )
    median_tau = {link: float(np.median(values)) for link, values in per_link.items()}
    duration = float(np.median([run["duration_s"] for run in per_run]))
    return {
        "per_run": per_run,
        "median_tau_s": median_tau,
        "duration_s": duration,
        "T_over_tau": {link: float(duration / tau) for link, tau in median_tau.items()},
        "min_T_over_tau": float(min(duration / tau for tau in median_tau.values())),
        "any_cut_at_ceiling": bool(
            any(run["edge"][link]["cut_at_ceiling"] for run in per_run for link in EDGE)
        ),
    }


# ------------------------------------------------------- PC-C2''b, bounded sf
def fit_nugget_bounded(acf_values: np.ndarray, lags) -> dict[str, object]:
    """A080 log-linear fit with the estimator's physical ``[0,1]`` range restored.

    ``signal_fraction`` is clamped to the ceiling and the fit is rejected only
    when the intercept sits *significantly* above ``log(1)=0``, judged by the
    least-squares standard error rather than by a hand-picked margin.
    """
    lags_arr = np.asarray(lags, dtype=float)
    values = np.asarray(acf_values, dtype=float)
    ok = np.isfinite(values) & (values > N.ACF_FIT_MIN)
    if int(ok.sum()) < 3:
        return {
            "valid": False,
            "reason": "fewer_than_3_positive_fit_lags",
            "n_fit_lags": int(ok.sum()),
        }
    times = lags_arr[ok] * L.DT_MEASURED_S
    logs = np.log(values[ok])
    coeffs, cov = np.polyfit(times, logs, 1, cov=True)
    slope, intercept = float(coeffs[0]), float(coeffs[1])
    se_intercept = float(np.sqrt(cov[1, 1]))
    raw = float(np.exp(intercept))
    at_ceiling = bool(raw > 1.0)
    significantly_above = bool(intercept > CEILING_SE_MULT * se_intercept)
    valid = bool(slope < 0.0 and raw > 0.0 and not significantly_above)
    return {
        "valid": valid,
        "reason": (
            "ok" if valid
            else "nonnegative_slope" if slope >= 0.0
            else "intercept_significantly_above_ceiling"
        ),
        "n_fit_lags": int(ok.sum()),
        "fit_lags_used": [int(x) for x in lags_arr[ok]],
        "fit_lag_span_s": [float(times.min()), float(times.max())],
        "slope_per_s": slope,
        "log_intercept": intercept,
        "se_log_intercept": se_intercept,
        "intercept_over_se": float(intercept / se_intercept) if se_intercept > 0 else None,
        "signal_fraction_raw": raw,
        "signal_fraction": (min(1.0, raw) if valid else None),
        "at_ceiling": at_ceiling,
        "lambda_nugget": (float(1.0 - min(1.0, raw)) if valid else None),
        "tau_measured_s": (float(-1.0 / slope) if slope < 0.0 else None),
    }


def measured_signal(paths: list[str], fit_lags, expect_reps: int) -> dict[str, object]:
    if len(paths) != expect_reps:
        raise ValueError(f"expected {expect_reps} measured traces, got {len(paths)}")
    matrices = [L.load_run(path) for path in paths]
    n_samples = [int(matrix.shape[0]) for matrix in matrices]
    if min(n_samples) <= max(fit_lags):
        raise ValueError(f"trace too short for fit lags {max(fit_lags)}: {n_samples}")
    per_link: dict[str, object] = {}
    for link in EDGE:
        index = L.IDX[link]
        curve = N._mean_acf(matrices, index, fit_lags)
        fit = fit_nugget_bounded(curve, fit_lags)
        fit["acf_fit_values"] = {
            str(lag): float(value) for lag, value in zip(fit_lags, curve)
        }
        per_link[link] = fit
    valid = all(bool(per_link[link]["valid"]) for link in EDGE)
    fractions = [
        float(per_link[link]["signal_fraction"])
        for link in EDGE
        if per_link[link]["valid"]
    ]
    return {
        "paths": paths,
        "n_samples_per_rep": n_samples,
        "fit_lags": [int(lag) for lag in fit_lags],
        "per_link": per_link,
        "all_edge_fits_valid": valid,
        "any_at_ceiling": bool(any(per_link[link]["at_ceiling"] for link in EDGE)),
        "median_edge_signal_fraction": float(np.median(fractions)) if fractions else None,
    }


# ------------------------------------------------------------------- infra gate
def infra_block() -> dict[str, object]:
    if not INFRA.exists():
        return {"present": False, "all_flags_false": False, "reason": "missing_jsonl"}
    from tools.summarize_infra import summarize

    summary = summarize(INFRA)
    flags = {key: bool(value) for key, value in summary.items() if key.startswith("flag_")}
    return {
        "present": True,
        "summary": summary,
        "flags": flags,
        "all_flags_false": bool(not any(flags.values())),
    }


def main() -> None:
    paths = {
        "cell_A_long_offered": sorted(glob.glob(CELL_A_LONG_OFFERED)),
        "cell_C_offered": sorted(glob.glob(CELL_C_OFFERED)),
        "cell_A_long_measured": sorted(glob.glob(CELL_A_LONG_MEASURED)),
        "cell_C_measured": sorted(glob.glob(CELL_C_MEASURED)),
    }
    expected = {
        "cell_A_long_offered": 1,
        "cell_C_offered": 3,
        "cell_A_long_measured": 1,
        "cell_C_measured": 3,
    }
    shortfall = {k: len(v) for k, v in paths.items() if len(v) != expected[k]}
    if shortfall:
        raise ValueError(f"input count mismatch, expected {expected}, got {shortfall}")

    infra = infra_block()

    offered_a = offered_cell(paths["cell_A_long_offered"], 1)
    offered_c = offered_cell(paths["cell_C_offered"], 3)
    ratios = {
        link: float(offered_a["median_tau_s"][link] / offered_c["median_tau_s"][link])
        for link in EDGE
    }
    median_ratio = float(np.median(list(ratios.values())))
    budget_ok = bool(
        offered_a["min_T_over_tau"] >= TAU_OVER_T_FLOOR
        and offered_c["min_T_over_tau"] >= TAU_OVER_T_FLOOR
    )
    pc_a_pass = bool(np.isfinite(median_ratio) and median_ratio >= TAU_RATIO_MIN)

    signal_a = measured_signal(paths["cell_A_long_measured"], A_FIT_LAGS, 1)
    signal_c = measured_signal(paths["cell_C_measured"], C_FIT_LAGS, 3)
    sf_a = signal_a["median_edge_signal_fraction"]
    sf_c = signal_c["median_edge_signal_fraction"]
    pc_b_pass = bool(
        signal_a["all_edge_fits_valid"]
        and signal_c["all_edge_fits_valid"]
        and sf_a is not None
        and sf_c is not None
        and float(sf_a) <= SIGNAL_FRACTION_A_MAX
        and float(sf_c) >= SIGNAL_FRACTION_C_MIN
    )

    data_complete = bool(
        infra["all_flags_false"]
        and signal_a["all_edge_fits_valid"]
        and signal_c["all_edge_fits_valid"]
    )
    if not infra["all_flags_false"]:
        label = "REANALYSIS_INVALID_OR_INCOMPLETE"
    elif not pc_a_pass:
        label = "GENERATOR_CONTROL_FAIL_CELL_C_REMAINS_INVALID"
    elif not (signal_a["all_edge_fits_valid"] and signal_c["all_edge_fits_valid"]):
        label = "REANALYSIS_INVALID_OR_INCOMPLETE"
    elif not pc_b_pass:
        label = "NUGGET_MODEL_MISS_CELL_C_REMAINS_INVALID_FOR_THIS_AMENDMENT"
    else:
        label = "CONTROL_REDESIGN_SUPPORTED_CELL_C_REANALYSIS_VALID"

    a080 = json.loads(A080.read_text(encoding="utf-8"))
    prime = json.loads(PC_C2_PRIME.read_text(encoding="utf-8"))
    all_inputs = [p for group in paths.values() for p in group] + [str(A080), str(PC_C2_PRIME)]
    if infra["present"]:
        all_inputs.append(str(INFRA))

    artifact = {
        "schema": "dt4n.phase_d.pc_c2_second.v1",
        "status": "SIGNED_CONTROL_ON_NEW_BASELINE_RUN",
        "preregistration": "docs/phase-D/00b-prereg-pc-c2-second.md",
        "diagnosis": "docs/phase-D/A002-amendment-pc-c2-prime.md",
        "signed_tag": "phase-D-pc-c2-second-start",
        "new_mininet_runs": 1,
        "locked_constants": {
            "offered_nlag": f"min(n//{NLAG_DIVISOR}, {NLAG_CAP})",
            "nlag_cap_A001": 3000,
            "tau_ratio_min": TAU_RATIO_MIN,
            "signal_fraction_A_max": SIGNAL_FRACTION_A_MAX,
            "signal_fraction_C_min": SIGNAL_FRACTION_C_MIN,
            "ceiling_se_mult": CEILING_SE_MULT,
            "A_fit_lags": list(A_FIT_LAGS),
            "C_fit_lags": list(C_FIT_LAGS),
            "acf_fit_min": N.ACF_FIT_MIN,
            "measured_dt_s": L.DT_MEASURED_S,
            "T_over_tau_floor": TAU_OVER_T_FLOOR,
        },
        "infra": infra,
        "PC_C2_second_a": {
            "cell_A_long": offered_a,
            "cell_C": offered_c,
            "ratio_A_over_C": ratios,
            "median_ratio_A_over_C": median_ratio,
            "budget_T_over_tau_ok": budget_ok,
            "signed_prediction_ratio": 10.9,
            "pass": pc_a_pass,
        },
        "PC_C2_second_b": {
            "cell_A_long": signal_a,
            "cell_C": signal_c,
            "median_signal_fraction_A": sf_a,
            "median_signal_fraction_C": sf_c,
            "A080_15_run_reference": {
                "median_edge_signal_fraction": a080["adjudication"]["median_edge_signal_fraction"],
                "all_fits_valid": a080["adjudication"]["all_fits_valid"],
                "branch": a080["adjudication"]["branch"],
            },
            "signed_prediction_sf_A": 0.37,
            "signed_prediction_sf_C": [0.87, 1.00],
            "pass": pc_b_pass,
        },
        "comparison_to_A001": {
            "PC_C2_prime_median_ratio": prime["PC_C2_prime"]["median_ratio_A_over_C"],
            "PC_C2_prime_pass": prime["PC_C2_prime"]["pass"],
            "PC_C2_prime_b_pass": prime["PC_C2_prime_b"]["pass"],
            "PC_C2_prime_label": prime["adjudication"]["label"],
        },
        "adjudication": {
            "label": label,
            "data_complete": data_complete,
            "cell_C_readjudicated_valid": bool(
                label == "CONTROL_REDESIGN_SUPPORTED_CELL_C_REANALYSIS_VALID"
            ),
            "may_read_frozen_outcomes_under_A002": bool(
                label == "CONTROL_REDESIGN_SUPPORTED_CELL_C_REANALYSIS_VALID"
            ),
            "S19_tau_scales_as_inverse_sigma_squared_refuted": bool(
                infra["all_flags_false"] and budget_ok and not pc_a_pass
            ),
        },
        "provenance": {
            "git_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
            ).stdout.strip(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/phase_d_pc_c2_second.py",
            "inputs_sha256": {path: sha256(path) for path in all_inputs},
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "PC_C2_second_a": {
                    "tau_A_long": offered_a["median_tau_s"],
                    "tau_C": offered_c["median_tau_s"],
                    "ratios": ratios,
                    "median_ratio": median_ratio,
                    "T_over_tau_A": offered_a["min_T_over_tau"],
                    "T_over_tau_C": offered_c["min_T_over_tau"],
                    "budget_ok": budget_ok,
                    "pass": pc_a_pass,
                },
                "PC_C2_second_b": {
                    "sf_A": sf_a,
                    "sf_C": sf_c,
                    "A_valid": signal_a["all_edge_fits_valid"],
                    "C_valid": signal_c["all_edge_fits_valid"],
                    "any_at_ceiling": bool(signal_a["any_at_ceiling"] or signal_c["any_at_ceiling"]),
                    "pass": pc_b_pass,
                },
                "infra_all_flags_false": infra["all_flags_false"],
                "adjudication": artifact["adjudication"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
