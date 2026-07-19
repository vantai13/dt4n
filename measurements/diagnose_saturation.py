#!/usr/bin/env python3
"""Diagnose wrong_excess saturation and tail behavior.

This is a follow-up diagnostic for Phase 10.2/10.3. It does not replace the
registered sweep. Its job is to answer:

1. Is the far-tail z=20 point noisy across independent seed blocks?
2. Does wrong_excess plateau when z is extended beyond the registered range?
3. Is a two-timescale fit materially better than the registered one-tau fit?
4. Are fitted time constants stable across independent seed blocks?

Outputs:
  measurements/out/diagnose_saturation.txt
  measurements/out/diagnose_saturation_test1.csv
  measurements/out/diagnose_saturation_test2.csv
  measurements/out/diagnose_saturation_test4.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import os
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

from rl.routing.metrics_r import evaluate_z
from rl.routing.topology_r import LOAD_CFG_SWEEP


OUT_DIR = Path("measurements/out")
DEFAULT_Z_EXTENDED = (0, 1, 2, 3, 5, 8, 12, 20, 30, 40, 60)


_LINES = []


def log(message=""):
    """Print and record one output line."""
    print(message, flush=True)
    _LINES.append(str(message))


def sat1(aoi, A, tau):
    """One-timescale saturation."""
    return A * (1.0 - np.exp(-aoi / tau))


def sat2(aoi, A1, tau1, A2, tau2):
    """Two-timescale saturation."""
    return (
        A1 * (1.0 - np.exp(-aoi / tau1))
        + A2 * (1.0 - np.exp(-aoi / tau2))
    )


def r2_score(y, y_pred):
    """Return R2 for fitted values."""
    y = np.asarray(y, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0.0 else float("nan")


def information_criteria(y, y_pred, n_params):
    """Return RSS, AIC, and BIC for a least-squares fit."""
    y = np.asarray(y, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    n = len(y)
    rss = max(float(np.sum((y - y_pred) ** 2)), 1e-15)
    # Gaussian least-squares IC up to an additive constant.
    aic = n * math.log(rss / n) + 2 * int(n_params)
    bic = n * math.log(rss / n) + int(n_params) * math.log(n)
    return rss, aic, bic


def fit_one_tau(aoi, wrong_excess):
    """Fit one-timescale saturation with positive bounds."""
    aoi = np.asarray(aoi, dtype=float)
    wrong_excess = np.asarray(wrong_excess, dtype=float)
    p0 = [max(float(wrong_excess.max()), 1e-3), 2.0]
    popt, _pcov = curve_fit(
        sat1,
        aoi,
        wrong_excess,
        p0=p0,
        bounds=([0.0, 1e-6], [1.0, 100.0]),
        maxfev=20000,
    )
    pred = sat1(aoi, *popt)
    rss, aic, bic = information_criteria(wrong_excess, pred, n_params=2)
    return {
        "A": float(popt[0]),
        "tau": float(popt[1]),
        "r2": float(r2_score(wrong_excess, pred)),
        "rss": rss,
        "aic": aic,
        "bic": bic,
        "pred": pred,
    }


def _sorted_two_tau_params(popt):
    pairs = sorted(
        [(float(popt[0]), float(popt[1])), (float(popt[2]), float(popt[3]))],
        key=lambda item: item[1],
    )
    return pairs[0][0], pairs[0][1], pairs[1][0], pairs[1][1]


def fit_two_tau(aoi, wrong_excess):
    """Fit two-timescale saturation and sort components by tau."""
    aoi = np.asarray(aoi, dtype=float)
    wrong_excess = np.asarray(wrong_excess, dtype=float)
    p0 = [0.15, 1.0, 0.08, 10.0]
    popt, _pcov = curve_fit(
        sat2,
        aoi,
        wrong_excess,
        p0=p0,
        bounds=([0.0, 1e-6, 0.0, 1e-6], [1.0, 100.0, 1.0, 100.0]),
        maxfev=50000,
    )
    A1, tau1, A2, tau2 = _sorted_two_tau_params(popt)
    pred = sat2(aoi, A1, tau1, A2, tau2)
    rss, aic, bic = information_criteria(wrong_excess, pred, n_params=4)
    return {
        "A1": A1,
        "tau1": tau1,
        "A2": A2,
        "tau2": tau2,
        "A_total": A1 + A2,
        "tau_ratio": tau2 / max(tau1, 1e-12),
        "r2": float(r2_score(wrong_excess, pred)),
        "rss": rss,
        "aic": aic,
        "bic": bic,
        "pred": pred,
    }


def evaluate_wrong_excess(z, seed_start, n_seeds):
    """Evaluate one z on an independent contiguous seed block."""
    return evaluate_z(
        z,
        seeds=range(int(seed_start), int(seed_start) + int(n_seeds)),
        load_cfg=LOAD_CFG_SWEEP,
    )


def write_csv(path, fieldnames, rows):
    """Write dictionaries to CSV."""
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    log(f"[CSV] wrote {path}")


def test1_noise(out_dir, z, blocks, block_size):
    """Run the same far-tail z over independent seed blocks."""
    log("=" * 72)
    log(f"TEST 1 - tail noise at z={z} ({blocks} blocks x {block_size} seeds)")
    log("=" * 72)

    rows = []
    values = []
    for block in range(blocks):
        seed_start = block * block_size
        result = evaluate_wrong_excess(z, seed_start, block_size)
        value = float(result["wrong_excess"])
        values.append(value)
        row = {
            "block": block + 1,
            "seed_start": seed_start,
            "seed_end": seed_start + block_size - 1,
            "z_steps": z,
            "aoi_mean_s": result["aoi_mean_s"],
            "wrong_excess": value,
            "cost_of_blindness": result["cost_of_blindness"],
        }
        rows.append(row)
        log(
            f"  block {block + 1}: seeds={row['seed_start']}-{row['seed_end']} "
            f"wrong_excess={value:.4f} CoB={row['cost_of_blindness']:.4f}"
        )

    values = np.array(values, dtype=float)
    spread = float(values.max() - values.min()) if len(values) else 0.0
    sd = float(values.std(ddof=1)) if len(values) > 1 else 0.0
    log(f"  mean={values.mean():.4f} sd_between_blocks={sd:.4f}")
    log(f"  max-min={spread:.4f}")
    if sd > 0.0:
        log(f"  spread/sd={spread / sd:.2f}")
    log("  Read: tail up/down of this size is sampling noise unless it repeats.")
    log("")

    write_csv(
        out_dir / "diagnose_saturation_test1.csv",
        [
            "block",
            "seed_start",
            "seed_end",
            "z_steps",
            "aoi_mean_s",
            "wrong_excess",
            "cost_of_blindness",
        ],
        rows,
    )
    return rows


def test2_saturation(out_dir, z_values, n_seeds):
    """Extend z well beyond the registered range and inspect the tail."""
    log("=" * 72)
    log(f"TEST 2 - extended z sweep for plateau (N={n_seeds})")
    log("=" * 72)

    rows = []
    for z in z_values:
        result = evaluate_wrong_excess(z, 0, n_seeds)
        row = {
            "z_steps": int(z),
            "aoi_mean_s": float(result["aoi_mean_s"]),
            "wrong_excess": float(result["wrong_excess"]),
            "cost_of_blindness": float(result["cost_of_blindness"]),
            "blind_wrong_rate": float(result["blind_wrong_rate"]),
            "clair_wrong_rate": float(result["clair_wrong_rate"]),
        }
        rows.append(row)
        log(
            f"  z={row['z_steps']:2d} AoI={row['aoi_mean_s']:5.1f}s "
            f"wrong_excess={row['wrong_excess']:.4f} "
            f"CoB={row['cost_of_blindness']:.4f}"
        )

    tail_delta = abs(rows[-1]["wrong_excess"] - rows[-2]["wrong_excess"])
    log(f"  |last - previous| = {tail_delta:.4f}")
    if tail_delta < 0.01:
        log("  Tail verdict: flat enough by the 0.01 wrong_excess heuristic.")
    else:
        log("  Tail verdict: not flat by the 0.01 heuristic; inspect with blocks.")
    log("")

    write_csv(
        out_dir / "diagnose_saturation_test2.csv",
        [
            "z_steps",
            "aoi_mean_s",
            "wrong_excess",
            "cost_of_blindness",
            "blind_wrong_rate",
            "clair_wrong_rate",
        ],
        rows,
    )
    return rows


def test3_phases(rows):
    """Compare one-tau and two-tau fits on the extended curve."""
    log("=" * 72)
    log("TEST 3 - one-timescale vs two-timescale fit")
    log("=" * 72)

    aoi = np.array([row["aoi_mean_s"] for row in rows], dtype=float)
    wrong_excess = np.array([row["wrong_excess"] for row in rows], dtype=float)
    one = fit_one_tau(aoi, wrong_excess)
    log(
        f"  [1-tau] A={one['A']:.4f} tau={one['tau']:.4f}s "
        f"R2={one['r2']:.5f} AIC={one['aic']:.2f} BIC={one['bic']:.2f}"
    )

    two = None
    try:
        two = fit_two_tau(aoi, wrong_excess)
        log(
            f"  [2-tau] fast: A1={two['A1']:.4f} tau1={two['tau1']:.4f}s"
        )
        log(
            f"          slow: A2={two['A2']:.4f} tau2={two['tau2']:.4f}s"
        )
        log(
            f"          A_total={two['A_total']:.4f} "
            f"tau_ratio={two['tau_ratio']:.2f}x "
            f"R2={two['r2']:.5f} AIC={two['aic']:.2f} BIC={two['bic']:.2f}"
        )
        log(f"  delta_R2  = {two['r2'] - one['r2']:+.5f}")
        log(f"  delta_AIC = {two['aic'] - one['aic']:+.2f} (negative favors 2-tau)")
        log(f"  delta_BIC = {two['bic'] - one['bic']:+.2f} (negative favors 2-tau)")

        if (
            two["tau_ratio"] > 3.0
            and two["bic"] < one["bic"] - 2.0
            and two["A1"] > 0.01
            and two["A2"] > 0.01
        ):
            log("  Verdict: two-timescale structure is worth investigating.")
        else:
            log("  Verdict: do not claim two mechanisms yet; evidence is weak/unstable.")
    except Exception as exc:
        log(f"  [2-tau] fit failed: {exc}")

    log("")
    return one, two


def test4_robustness(out_dir, z_values, trials, block_size):
    """Fit independent seed blocks and check whether tau estimates are stable."""
    log("=" * 72)
    log(f"TEST 4 - fit stability across {trials} independent seed blocks")
    log("=" * 72)

    rows_out = []
    for trial in range(trials):
        seed_start = trial * block_size
        curve_rows = []
        for z in z_values:
            result = evaluate_wrong_excess(z, seed_start, block_size)
            curve_rows.append(
                {
                    "z_steps": int(z),
                    "aoi_mean_s": float(result["aoi_mean_s"]),
                    "wrong_excess": float(result["wrong_excess"]),
                }
            )

        aoi = np.array([row["aoi_mean_s"] for row in curve_rows], dtype=float)
        wrong_excess = np.array(
            [row["wrong_excess"] for row in curve_rows],
            dtype=float,
        )
        one = fit_one_tau(aoi, wrong_excess)

        row_out = {
            "trial": trial + 1,
            "seed_start": seed_start,
            "seed_end": seed_start + block_size - 1,
            "one_A": one["A"],
            "one_tau": one["tau"],
            "one_r2": one["r2"],
            "two_A1": "",
            "two_tau1": "",
            "two_A2": "",
            "two_tau2": "",
            "two_r2": "",
            "two_bic_minus_one_bic": "",
        }
        text = (
            f"  block {trial + 1}: seeds={seed_start}-{seed_start + block_size - 1} "
            f"1tau_tau={one['tau']:.3f}s R2={one['r2']:.4f}"
        )

        try:
            two = fit_two_tau(aoi, wrong_excess)
            row_out.update(
                {
                    "two_A1": two["A1"],
                    "two_tau1": two["tau1"],
                    "two_A2": two["A2"],
                    "two_tau2": two["tau2"],
                    "two_r2": two["r2"],
                    "two_bic_minus_one_bic": two["bic"] - one["bic"],
                }
            )
            text += (
                f" | 2tau_tau1={two['tau1']:.3f}s "
                f"tau2={two['tau2']:.3f}s "
                f"dBIC={two['bic'] - one['bic']:+.2f}"
            )
        except Exception as exc:
            text += f" | 2tau failed: {exc}"

        rows_out.append(row_out)
        log(text)

    one_taus = np.array([row["one_tau"] for row in rows_out], dtype=float)
    log(
        f"  1tau tau mean={one_taus.mean():.3f}s "
        f"sd={one_taus.std(ddof=1) if len(one_taus) > 1 else 0.0:.3f}s"
    )
    log("  Read: stable tau across blocks is stronger than a single pretty fit.")
    log("")

    write_csv(
        out_dir / "diagnose_saturation_test4.csv",
        [
            "trial",
            "seed_start",
            "seed_end",
            "one_A",
            "one_tau",
            "one_r2",
            "two_A1",
            "two_tau1",
            "two_A2",
            "two_tau2",
            "two_r2",
            "two_bic_minus_one_bic",
        ],
        rows_out,
    )
    return rows_out


def parse_z_values(text):
    """Parse comma-separated z values."""
    return tuple(int(part.strip()) for part in text.split(",") if part.strip())


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--quick",
        action="store_true",
        help="use small seed counts for smoke testing",
    )
    parser.add_argument(
        "--z-values",
        default=",".join(str(z) for z in DEFAULT_Z_EXTENDED),
        help="comma-separated z values for extended saturation tests",
    )
    parser.add_argument("--tail-z", type=int, default=20)
    parser.add_argument("--tail-blocks", type=int, default=5)
    parser.add_argument("--tail-block-size", type=int, default=500)
    parser.add_argument("--extended-seeds", type=int, default=800)
    parser.add_argument("--robust-trials", type=int, default=3)
    parser.add_argument("--robust-block-size", type=int, default=400)
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    out_dir = Path(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    if args.quick:
        args.tail_blocks = min(args.tail_blocks, 2)
        args.tail_block_size = min(args.tail_block_size, 80)
        args.extended_seeds = min(args.extended_seeds, 120)
        args.robust_trials = min(args.robust_trials, 2)
        args.robust_block_size = min(args.robust_block_size, 100)
        log("[MODE] quick smoke test, not confirmatory")
    else:
        log("[MODE] full saturation diagnostic")

    z_values = parse_z_values(args.z_values)
    log("### Diagnose wrong_excess saturation ###")
    log(f"z_values={z_values}")
    log(f"load_cfg=LOAD_CFG_SWEEP")
    log("")

    test1_noise(out_dir, args.tail_z, args.tail_blocks, args.tail_block_size)
    extended_rows = test2_saturation(out_dir, z_values, args.extended_seeds)
    test3_phases(extended_rows)
    test4_robustness(out_dir, z_values, args.robust_trials, args.robust_block_size)

    summary_path = out_dir / "diagnose_saturation.txt"
    with open(summary_path, "w") as handle:
        handle.write("\n".join(_LINES) + "\n")
    print(f"\n[SUMMARY] wrote {summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
