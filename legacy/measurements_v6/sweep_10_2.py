#!/usr/bin/env python3
"""Phase 10.2 confirmatory AoI sweep.

This is the official post-registration sweep, not a pilot:

* primary mechanism axis: wrong_excess(AoI)
* fitted model: A * (1 - exp(-AoI / tau))
* consequence axis: cost_of_blindness
* GO/NO-GO gate: max(cost_of_blindness) / std_agent

Outputs:
  measurements/out/sweep_10_2.csv
  measurements/out/sweep_10_2_mechanism.md
  measurements/out/sweep_10_2_summary.txt
  measurements/out/sweep_10_2.png
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

from rl.routing_2path.metrics_r import evaluate_z_range
from rl.routing_2path.topology_r import LOAD_CFG_SWEEP


Z_VALUES = (0, 1, 2, 3, 5, 8, 12, 20)
N_SEEDS_CONFIRMATORY = 500
N_SEEDS_QUICK = 60
R2_ACCEPT = 0.95
STD_AGENT = 0.0450
SNR_GO = 3.0
SNR_MAYBE = 2.0
DITTO_MAX_AOI_S = 0.55
OUT_DIR = Path("measurements/out")


def saturating(aoi, A, tau):
    """Return A * (1 - exp(-AoI / tau))."""
    return A * (1.0 - np.exp(-aoi / tau))


def fit_curve(aoi, wrong_excess):
    """Fit the saturating curve and return a result dictionary."""
    aoi = np.asarray(aoi, dtype=float)
    wrong_excess = np.asarray(wrong_excess, dtype=float)
    p0 = [max(float(np.max(wrong_excess)), 1e-3), 2.0]
    popt, pcov = curve_fit(
        saturating,
        aoi,
        wrong_excess,
        p0=p0,
        bounds=([0.0, 1e-6], [1.0, 100.0]),
        maxfev=10000,
    )
    pred = saturating(aoi, *popt)
    ss_res = float(np.sum((wrong_excess - pred) ** 2))
    ss_tot = float(np.sum((wrong_excess - wrong_excess.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else float("nan")

    return {
        "A": float(popt[0]),
        "tau_s": float(popt[1]),
        "r2": float(r2),
        "pred": pred,
        "pcov": pcov,
    }


def run_sweep(n_seeds):
    """Run evaluate_z over the registered z grid."""
    print(f"[SWEEP] z={Z_VALUES} seeds={n_seeds} load_cfg=LOAD_CFG_SWEEP")
    rows = evaluate_z_range(
        z_values=Z_VALUES,
        seeds=range(int(n_seeds)),
        load_cfg=LOAD_CFG_SWEEP,
    )
    for row in rows:
        print(
            f"  z={row['z_steps']:2d} "
            f"AoI={row['aoi_mean_s']:5.2f}s "
            f"wrong_excess={row['wrong_excess']:.4f} "
            f"CoB={row['cost_of_blindness']:.4f} "
            f"blind_wrong={row['blind_wrong_rate']:.4f} "
            f"clair_wrong={row['clair_wrong_rate']:.4f}"
        )
    return rows


def sanity_checks(rows):
    """Compute simple checks that should be inspected before trusting the fit."""
    wrong_excess = np.array([row["wrong_excess"] for row in rows], dtype=float)
    cost = np.array([row["cost_of_blindness"] for row in rows], dtype=float)
    clair_wrong = np.array([row["clair_wrong_rate"] for row in rows], dtype=float)

    return {
        "z0_wrong_excess": float(wrong_excess[0]),
        "clair_wrong_range": float(clair_wrong.max() - clair_wrong.min()),
        "wrong_excess_monotone": bool(np.all(np.diff(wrong_excess) >= -1e-12)),
        "cost_monotone": bool(np.all(np.diff(cost) >= -1e-12)),
    }


def compute_gate(rows):
    """Compute the return-unit SNR gate from cost_of_blindness."""
    cost = np.array([row["cost_of_blindness"] for row in rows], dtype=float)
    cost_max = float(np.max(cost))
    snr = cost_max / max(STD_AGENT, 1e-12)

    if snr >= SNR_GO:
        decision = "GO"
        reason = f"SNR={snr:.2f} >= {SNR_GO:.1f}"
    elif snr >= SNR_MAYBE:
        decision = "GO_WITH_MORE_SEEDS"
        reason = f"{SNR_MAYBE:.1f} <= SNR={snr:.2f} < {SNR_GO:.1f}"
    else:
        decision = "NO_GO"
        reason = f"SNR={snr:.2f} < {SNR_MAYBE:.1f}"

    return {
        "cost_of_blindness_max": cost_max,
        "std_agent": float(STD_AGENT),
        "snr": float(snr),
        "decision": decision,
        "reason": reason,
    }


def write_csv(rows, path):
    """Write raw sweep rows for reproducibility."""
    fields = [
        "z_steps",
        "aoi_mean_s",
        "wrong_excess",
        "cost_of_blindness",
        "blind_wrong_rate",
        "clair_wrong_rate",
        "blind_return",
        "clair_return",
        "ospf_return",
        "ospf_reactive_return",
        "blind_safe_path_freq",
        "clair_safe_path_freq",
    ]
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"[CSV] wrote {path}")


def make_figure(rows, fit, path):
    """Write the two-panel thesis figure."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    aoi = np.array([row["aoi_mean_s"] for row in rows], dtype=float)
    wrong_excess = np.array([row["wrong_excess"] for row in rows], dtype=float)
    cost = np.array([row["cost_of_blindness"] for row in rows], dtype=float)
    aoi_smooth = np.linspace(0.0, float(aoi.max()), 250)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.scatter(aoi, wrong_excess, color="crimson", zorder=3, label="measured")
    ax1.plot(
        aoi_smooth,
        saturating(aoi_smooth, fit["A"], fit["tau_s"]),
        "k--",
        label=(
            f"fit: A={fit['A']:.3f}, "
            f"tau={fit['tau_s']:.2f}s, R2={fit['r2']:.4f}"
        ),
    )
    ax1.axvline(fit["tau_s"], color="navy", ls=":", label="tau knee")
    ax1.axvline(
        DITTO_MAX_AOI_S,
        color="green",
        ls=":",
        alpha=0.75,
        label="Ditto max 0.55s",
    )
    ax1.set_xlabel("AoI (s)")
    ax1.set_ylabel("wrong_excess")
    ax1.set_title("Mechanism axis: stale information causes wrong decisions")
    ax1.grid(alpha=0.3)
    ax1.legend(fontsize=8)

    ax2.scatter(aoi, cost, color="darkorange", zorder=3)
    ax2.plot(aoi, cost, color="darkorange", alpha=0.55)
    ax2.set_xlabel("AoI (s)")
    ax2.set_ylabel("cost_of_blindness (return)")
    ax2.set_title("Consequence axis: return lost to stale state")
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print(f"[FIG] wrote {path}")


def write_mechanism_table(rows, path):
    """Write a markdown table of the mechanism metrics."""
    lines = [
        "# Phase 10.2 mechanism table",
        "",
        "| z | AoI(s) | blind_wrong | clair_wrong | wrong_excess | cost_of_blindness |",
        "|--:|-------:|------------:|------------:|-------------:|------------------:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['z_steps']} | {row['aoi_mean_s']:.2f} | "
            f"{row['blind_wrong_rate']:.4f} | {row['clair_wrong_rate']:.4f} | "
            f"{row['wrong_excess']:.4f} | {row['cost_of_blindness']:.4f} |"
        )
    with open(path, "w") as handle:
        handle.write("\n".join(lines) + "\n")
    print(f"[TABLE] wrote {path}")


def write_summary(rows, fit, fit_drop_tail, checks, gate, path):
    """Write a plain-text summary for copy/paste into notes."""
    we_at_ditto = float(saturating(DITTO_MAX_AOI_S, fit["A"], fit["tau_s"]))
    pct_at_ditto = 100.0 * we_at_ditto / max(fit["A"], 1e-12)
    knee_90 = float(np.log(10.0) * fit["tau_s"])

    lines = [
        "Phase 10.2 confirmatory sweep summary",
        "",
        f"Z_VALUES = {Z_VALUES}",
        f"STD_AGENT = {STD_AGENT:.4f}",
        "",
        "Sanity checks:",
        f"  z=0 wrong_excess        = {checks['z0_wrong_excess']:.6f}",
        f"  clair_wrong range       = {checks['clair_wrong_range']:.6f}",
        f"  wrong_excess monotone   = {checks['wrong_excess_monotone']}",
        f"  cost_of_blindness mono  = {checks['cost_monotone']}",
        "",
        "Fit on wrong_excess:",
        f"  A       = {fit['A']:.4f}",
        f"  tau     = {fit['tau_s']:.4f} s",
        f"  knee90  = {knee_90:.4f} s",
        f"  R2      = {fit['r2']:.4f}",
        "",
        "Robustness fit (drop tail z=20):",
        f"  A       = {fit_drop_tail['A']:.4f}",
        f"  tau     = {fit_drop_tail['tau_s']:.4f} s",
        f"  R2      = {fit_drop_tail['r2']:.4f}",
        "",
        "Ditto operating region:",
        f"  wrong_excess@0.55s = {we_at_ditto:.4f}",
        f"  pct_of_A           = {pct_at_ditto:.1f}%",
        f"  relation           = {'BEFORE' if DITTO_MAX_AOI_S < fit['tau_s'] else 'AFTER'} tau",
        "",
        "SNR gate on cost_of_blindness:",
        f"  cost_of_blindness_max = {gate['cost_of_blindness_max']:.4f}",
        f"  std_agent             = {gate['std_agent']:.4f}",
        f"  SNR                   = {gate['snr']:.2f}",
        f"  decision              = {gate['decision']}",
        f"  reason                = {gate['reason']}",
        "",
        "Rows:",
    ]
    for row in rows:
        lines.append(
            f"  z={row['z_steps']:2d} AoI={row['aoi_mean_s']:5.2f}s "
            f"wrong_excess={row['wrong_excess']:.4f} "
            f"CoB={row['cost_of_blindness']:.4f}"
        )

    with open(path, "w") as handle:
        handle.write("\n".join(lines) + "\n")
    print(f"[SUMMARY] wrote {path}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seeds",
        type=int,
        default=N_SEEDS_CONFIRMATORY,
        help="number of deterministic eval seeds per z",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help=f"smoke-test mode: use {N_SEEDS_QUICK} seeds",
    )
    parser.add_argument(
        "--out-dir",
        default=str(OUT_DIR),
        help="directory for CSV, figure, and summary outputs",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    n_seeds = N_SEEDS_QUICK if args.quick else int(args.seeds)
    out_dir = Path(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    if args.quick:
        print("[MODE] quick smoke test, not confirmatory")
    elif n_seeds != N_SEEDS_CONFIRMATORY:
        print(
            f"[MODE] custom seeds={n_seeds}; confirmatory default is "
            f"{N_SEEDS_CONFIRMATORY}"
        )
    else:
        print("[MODE] confirmatory")

    rows = run_sweep(n_seeds)
    checks = sanity_checks(rows)

    aoi = np.array([row["aoi_mean_s"] for row in rows], dtype=float)
    wrong_excess = np.array([row["wrong_excess"] for row in rows], dtype=float)
    fit = fit_curve(aoi, wrong_excess)
    fit_drop_tail = fit_curve(aoi[:-1], wrong_excess[:-1])
    gate = compute_gate(rows)

    print("\n[SANITY]")
    print(f"  z=0 wrong_excess       = {checks['z0_wrong_excess']:.6f}")
    print(f"  clair_wrong range      = {checks['clair_wrong_range']:.6f}")
    print(f"  wrong_excess monotone  = {checks['wrong_excess_monotone']}")
    print(f"  cost monotone          = {checks['cost_monotone']}")

    print("\n[FIT wrong_excess]")
    print(
        f"  A={fit['A']:.4f} tau={fit['tau_s']:.4f}s "
        f"R2={fit['r2']:.4f} knee90={np.log(10.0) * fit['tau_s']:.4f}s"
    )
    if fit["r2"] < R2_ACCEPT:
        print(f"  WARNING: R2 < {R2_ACCEPT}; do not treat tau as accepted.")
    else:
        print(f"  PASS: R2 >= {R2_ACCEPT}; tau is the registered knee.")

    print("\n[ROBUSTNESS drop z=20]")
    print(
        f"  A={fit_drop_tail['A']:.4f} "
        f"tau={fit_drop_tail['tau_s']:.4f}s "
        f"R2={fit_drop_tail['r2']:.4f}"
    )

    we_at_ditto = float(saturating(DITTO_MAX_AOI_S, fit["A"], fit["tau_s"]))
    print("\n[DITTO]")
    print(
        f"  wrong_excess@0.55s={we_at_ditto:.4f} "
        f"({100.0 * we_at_ditto / max(fit['A'], 1e-12):.1f}% of A)"
    )
    print(
        f"  0.55s is "
        f"{'BEFORE' if DITTO_MAX_AOI_S < fit['tau_s'] else 'AFTER'} "
        f"tau={fit['tau_s']:.4f}s"
    )

    print("\n[GATE cost_of_blindness]")
    print(
        f"  CoB_max={gate['cost_of_blindness_max']:.4f} "
        f"std_agent={gate['std_agent']:.4f} "
        f"SNR={gate['snr']:.2f} decision={gate['decision']}"
    )
    print(f"  {gate['reason']}")

    write_csv(rows, out_dir / "sweep_10_2.csv")
    write_mechanism_table(rows, out_dir / "sweep_10_2_mechanism.md")
    write_summary(
        rows,
        fit,
        fit_drop_tail,
        checks,
        gate,
        out_dir / "sweep_10_2_summary.txt",
    )
    make_figure(rows, fit, out_dir / "sweep_10_2.png")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
