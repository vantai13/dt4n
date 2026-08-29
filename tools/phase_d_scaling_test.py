#!/usr/bin/env python3
"""Phase D' correlation scaling test with burn-in and effective sample size.

Input files use the long-form Phase-23 schema
``sample_index,timestamp_s,link,rho,...``.  The tool never silently treats row
count as independent sample count: each reported Fisher interval carries the
sum of per-run ``T/(2*tau_pair)`` across independent runs.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
from pathlib import Path

import numpy as np


DEFAULT_PAIRS = (("uA", "uB"), ("ac", "ad"), ("vC", "vD"), ("uA", "vD"))


def autocorrelation_fft(values: np.ndarray, max_lag: int) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if x.size < 4:
        raise ValueError("series is too short")
    x = x - x.mean()
    variance = float(np.dot(x, x))
    if variance <= 0:
        return np.concatenate(([1.0], np.zeros(max_lag, dtype=float)))
    fft_len = 1 << (2 * x.size - 1).bit_length()
    spectrum = np.fft.rfft(x, n=fft_len)
    covariance = np.fft.irfft(spectrum * np.conjugate(spectrum), n=fft_len)[: x.size]
    covariance /= np.arange(x.size, 0, -1, dtype=float)
    return covariance[: max_lag + 1] / covariance[0]


def tau_integral(values: np.ndarray, dt_s: float) -> tuple[float, int]:
    max_lag = min(max(1, len(values) // 4), 200_000)
    acf = autocorrelation_fft(values, max_lag)
    nonpositive = np.flatnonzero(acf[1:] <= 0.0)
    cut = int(nonpositive[0]) if nonpositive.size else len(acf) - 1
    tau_s = float(dt_s * (0.5 + acf[1 : cut + 1].sum()))
    return max(tau_s, 0.5 * dt_s), cut


def load_long_csv(path: Path) -> tuple[dict[str, np.ndarray], float, float]:
    per_link: dict[str, list[tuple[int, float, float]]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            link = row["link"]
            value_key = "rho_offered" if row.get("rho_offered", "") else "rho"
            per_link.setdefault(link, []).append(
                (int(row["sample_index"]), float(row["timestamp_s"]), float(row[value_key]))
            )
    arrays: dict[str, np.ndarray] = {}
    timestamps: list[np.ndarray] = []
    for link, rows in per_link.items():
        rows.sort(key=lambda item: item[0])
        arrays[link] = np.asarray([row[2] for row in rows], dtype=float)
        timestamps.append(np.asarray([row[1] for row in rows], dtype=float))
    if not timestamps:
        raise ValueError(f"no rows in {path}")
    diffs = np.concatenate([np.diff(ts) for ts in timestamps if len(ts) > 1])
    dt_s = float(np.median(diffs[diffs > 0]))
    duration_s = float(min(ts[-1] - ts[0] for ts in timestamps))
    return arrays, dt_s, duration_s


def fisher_ci(r_value: float, n_eff: float) -> tuple[float | None, float | None]:
    if n_eff <= 4.0:
        return None, None
    z_value = float(np.arctanh(np.clip(r_value, -0.999999, 0.999999)))
    half_width = 1.96 / np.sqrt(n_eff - 3.0)
    bounds = np.tanh([z_value - half_width, z_value + half_width])
    return float(bounds[0]), float(bounds[1])


def audit(paths: list[Path], windows_s: list[float], burn_tau: float) -> dict[str, object]:
    runs = []
    for path in paths:
        arrays, dt_s, duration_s = load_long_csv(path)
        tau = {link: tau_integral(values, dt_s)[0] for link, values in arrays.items()}
        runs.append({"path": str(path), "arrays": arrays, "dt_s": dt_s, "duration_s": duration_s, "tau": tau})

    rows = []
    for first, second in DEFAULT_PAIRS:
        for window_s in windows_s:
            per_run = []
            for run in runs:
                if first not in run["arrays"] or second not in run["arrays"]:
                    continue
                tau_pair = max(run["tau"][first], run["tau"][second])
                burn_s = burn_tau * tau_pair
                dt_s = run["dt_s"]
                start = int(np.ceil(burn_s / dt_s))
                count = int(np.floor(window_s / dt_s))
                xa = run["arrays"][first]
                xb = run["arrays"][second]
                if count < 4 or start + count > min(len(xa), len(xb)):
                    continue
                r_value = float(np.corrcoef(xa[start : start + count], xb[start : start + count])[0, 1])
                if np.isfinite(r_value):
                    per_run.append({"r": r_value, "tau_pair_s": tau_pair, "n_eff": window_s / (2.0 * tau_pair)})
            if not per_run:
                continue
            z_mean = float(np.mean([np.arctanh(np.clip(item["r"], -0.999999, 0.999999)) for item in per_run]))
            pooled_r = float(np.tanh(z_mean))
            n_eff_total = float(sum(item["n_eff"] for item in per_run))
            ci_low, ci_high = fisher_ci(pooled_r, n_eff_total)
            rows.append(
                {
                    "pair": f"{first}-{second}",
                    "window_s": window_s,
                    "n_runs": len(per_run),
                    "r_pooled_fisher": pooled_r,
                    "r_per_run": [item["r"] for item in per_run],
                    "tau_pair_mean_s": float(np.mean([item["tau_pair_s"] for item in per_run])),
                    "n_eff_total": n_eff_total,
                    "ci95": [ci_low, ci_high],
                    "sampling_adequate": bool(n_eff_total >= 25.0),
                }
            )

    return {
        "schema": "dt4n.phase_d.scaling_test.v1",
        "n_input_runs": len(runs),
        "burn_in_rule": f"{burn_tau:g} * tau_pair",
        "windows_requested_s": windows_s,
        "run_diagnostics": [
            {
                "path": run["path"],
                "dt_s": run["dt_s"],
                "duration_s": run["duration_s"],
                "tau_s": run["tau"],
            }
            for run in runs
        ],
        "rows": rows,
        "status": "OK" if rows else "INSUFFICIENT_DURATION_AFTER_5TAU_BURN_IN",
        "note": "A scaling verdict requires at least two adequate windows for the same pair.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glob", dest="pattern", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--windows", type=float, nargs="+", default=[60, 120, 240, 480, 960, 1800])
    parser.add_argument("--burn-tau", type=float, default=5.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = [Path(path) for path in sorted(glob.glob(args.pattern))]
    if not paths:
        raise SystemExit(f"no files matched: {args.pattern}")
    result = audit(paths, args.windows, args.burn_tau)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "n_input_runs": len(paths), "n_rows": len(result["rows"]), "out": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()
