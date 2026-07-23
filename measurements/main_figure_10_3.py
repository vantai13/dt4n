#!/usr/bin/env python3
"""Phase 10.3 main figure with paired CI95.

This script is deliberately external to ``rl.routing_2path.metrics_r``: the core
measurement helpers return means, while the thesis figure needs per-seed rows
to compute paired confidence intervals.

Outputs:
  measurements/out/main_figure_10_3.csv
  measurements/out/main_figure_10_3_cost_ci.md
  measurements/out/main_figure_10_3_summary.txt
  measurements/out/main_figure_10_3.png
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

from rl.routing_2path.baselines import ospf_calibrated
from rl.routing_2path.metrics_r import make_env, run_episode
from rl.routing_2path.oracles import blind_dijkstra, clairvoyant_dijkstra, posthoc_dijkstra
from rl.routing_2path.topology_r import LOAD_CFG_SWEEP


Z_VALUES = (0, 1, 2, 3, 5, 8, 12, 20)
N_SEEDS_CONFIRMATORY = 500
N_SEEDS_QUICK = 60
DITTO_MAX_AOI_S = 0.55
R2_ACCEPT = 0.95
OUT_DIR = Path("measurements/out")


POLICIES = (
    ("clair", clairvoyant_dijkstra),
    ("blind", blind_dijkstra),
    ("ospf", ospf_calibrated),
)


def saturating(aoi, A, tau):
    """Return A * (1 - exp(-AoI / tau))."""
    return A * (1.0 - np.exp(-aoi / tau))


def ci95(values):
    """Return 95% CI half-width for a mean."""
    values = np.asarray(values, dtype=float)
    if len(values) <= 1:
        return 0.0
    return float(1.96 * values.std(ddof=1) / np.sqrt(len(values)))


def fit_curve(aoi, wrong_excess):
    """Fit wrong_excess(AoI) and return A, tau, R2, and predictions."""
    aoi = np.asarray(aoi, dtype=float)
    wrong_excess = np.asarray(wrong_excess, dtype=float)
    p0 = [max(float(wrong_excess.max()), 1e-3), 2.0]
    popt, _pcov = curve_fit(
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
    }


def run_policy_once(policy_fn, z, seed):
    """Run one policy on one seed and return an EpisodeStats dict."""
    env = make_env(z, seed=seed, load_cfg=LOAD_CFG_SWEEP)
    return run_episode(
        env,
        policy_fn,
        seed=seed,
        target_fn=posthoc_dijkstra,
    ).as_dict()


def collect_z(z, seeds):
    """Collect per-seed paired rows for one z."""
    per_policy = {name: [] for name, _policy in POLICIES}
    for seed in seeds:
        for name, policy_fn in POLICIES:
            per_policy[name].append(run_policy_once(policy_fn, z, seed))
    return per_policy


def summarize_z(z, per_policy):
    """Summarize one z, keeping paired CI for difference metrics."""
    returns = {
        name: np.array([row["total_reward"] for row in rows], dtype=float)
        for name, rows in per_policy.items()
    }
    wrong = {
        name: np.array([row["wrong_rate"] for row in rows], dtype=float)
        for name, rows in per_policy.items()
    }
    aoi_samples = np.array(
        [row["aoi_mean_s"] for row in per_policy["blind"]],
        dtype=float,
    )

    cob = returns["clair"] - returns["blind"]
    wrong_excess = wrong["blind"] - wrong["clair"]
    blind_minus_ospf = returns["blind"] - returns["ospf"]

    row = {
        "z_steps": int(z),
        "aoi_mean_s": float(aoi_samples.mean()),
        "n": int(len(aoi_samples)),
        "clair_return": float(returns["clair"].mean()),
        "clair_return_ci95": ci95(returns["clair"]),
        "blind_return": float(returns["blind"].mean()),
        "blind_return_ci95": ci95(returns["blind"]),
        "ospf_return": float(returns["ospf"].mean()),
        "ospf_return_ci95": ci95(returns["ospf"]),
        "cost_of_blindness": float(cob.mean()),
        "cost_of_blindness_ci95_paired": ci95(cob),
        "blind_minus_ospf": float(blind_minus_ospf.mean()),
        "blind_minus_ospf_ci95_paired": ci95(blind_minus_ospf),
        "clair_wrong_rate": float(wrong["clair"].mean()),
        "blind_wrong_rate": float(wrong["blind"].mean()),
        "wrong_excess": float(wrong_excess.mean()),
        "wrong_excess_ci95_paired": ci95(wrong_excess),
    }
    return row


def collect_curve(z_values, seeds):
    """Collect all z rows for the main figure."""
    rows = []
    for z in z_values:
        print(f"[COLLECT] z={z:2d} seeds={len(seeds)}")
        per_policy = collect_z(z, seeds)
        row = summarize_z(z, per_policy)
        print(
            f"  AoI={row['aoi_mean_s']:5.2f}s "
            f"CoB={row['cost_of_blindness']:.4f} "
            f"+/-{row['cost_of_blindness_ci95_paired']:.4f} "
            f"wrong_excess={row['wrong_excess']:.4f} "
            f"+/-{row['wrong_excess_ci95_paired']:.4f}"
        )
        rows.append(row)
    return rows


def sanity_checks(rows):
    """Return sanity checks for the 10.3 figure."""
    clair_returns = np.array([row["clair_return"] for row in rows], dtype=float)
    clair_wrong = np.array([row["clair_wrong_rate"] for row in rows], dtype=float)
    wrong_excess = np.array([row["wrong_excess"] for row in rows], dtype=float)
    return {
        "clair_return_spread": float(clair_returns.max() - clair_returns.min()),
        "clair_return_mean_ci": float(
            np.mean([row["clair_return_ci95"] for row in rows])
        ),
        "clair_wrong_spread": float(clair_wrong.max() - clair_wrong.min()),
        "z0_wrong_excess": float(wrong_excess[0]),
        "wrong_excess_monotone": bool(np.all(np.diff(wrong_excess) >= -1e-12)),
    }


def write_csv(rows, path):
    """Write the summarized rows to CSV."""
    fields = [
        "z_steps",
        "aoi_mean_s",
        "n",
        "clair_return",
        "clair_return_ci95",
        "blind_return",
        "blind_return_ci95",
        "ospf_return",
        "ospf_return_ci95",
        "cost_of_blindness",
        "cost_of_blindness_ci95_paired",
        "blind_minus_ospf",
        "blind_minus_ospf_ci95_paired",
        "clair_wrong_rate",
        "blind_wrong_rate",
        "wrong_excess",
        "wrong_excess_ci95_paired",
    ]
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"[CSV] wrote {path}")


def write_cost_table(rows, path):
    """Write the paired cost-of-blindness table."""
    lines = [
        "# Phase 10.3 paired CI table",
        "",
        "| z | AoI(s) | cost_of_blindness | paired CI95 | wrong_excess | paired CI95 |",
        "|--:|-------:|------------------:|------------:|-------------:|------------:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['z_steps']} | {row['aoi_mean_s']:.2f} | "
            f"{row['cost_of_blindness']:.4f} | "
            f"{row['cost_of_blindness_ci95_paired']:.4f} | "
            f"{row['wrong_excess']:.4f} | "
            f"{row['wrong_excess_ci95_paired']:.4f} |"
        )
    with open(path, "w") as handle:
        handle.write("\n".join(lines) + "\n")
    print(f"[TABLE] wrote {path}")


def make_figure(rows, fit, path):
    """Create the main 10.3 figure."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    aoi = np.array([row["aoi_mean_s"] for row in rows], dtype=float)
    aoi_smooth = np.linspace(0.0, float(aoi.max()), 250)

    wrong = np.array([row["wrong_excess"] for row in rows], dtype=float)
    wrong_ci = np.array(
        [row["wrong_excess_ci95_paired"] for row in rows],
        dtype=float,
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.6))

    ax1.scatter(aoi, wrong, color="crimson", zorder=4, label="wrong_excess")
    ax1.fill_between(
        aoi,
        wrong - wrong_ci,
        wrong + wrong_ci,
        color="crimson",
        alpha=0.16,
        label="paired CI95",
    )
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
    ax1.set_title("Mechanism axis: stale state causes wrong decisions")
    ax1.grid(alpha=0.3)
    ax1.legend(fontsize=8)

    for key, color, label in [
        ("clair", "green", "fresh Dijkstra reference"),
        ("blind", "crimson", "blind stale Dijkstra"),
        ("ospf", "gray", "static OSPF baseline"),
    ]:
        mean = np.array([row[f"{key}_return"] for row in rows], dtype=float)
        ci = np.array([row[f"{key}_return_ci95"] for row in rows], dtype=float)
        ax2.plot(aoi, mean, color=color, label=label, zorder=3)
        ax2.fill_between(aoi, mean - ci, mean + ci, color=color, alpha=0.15)

    ax2.axvline(fit["tau_s"], color="navy", ls=":", label="tau knee")
    ax2.axvline(
        DITTO_MAX_AOI_S,
        color="green",
        ls=":",
        alpha=0.75,
        label="Ditto max 0.55s",
    )
    ax2.set_xlabel("AoI (s)")
    ax2.set_ylabel("return")
    ax2.set_title("Consequence axis: return curves with CI95")
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print(f"[FIG] wrote {path}")


def write_summary(rows, fit, fit_drop_tail, checks, path):
    """Write a text summary of the main figure."""
    we_at_ditto = float(saturating(DITTO_MAX_AOI_S, fit["A"], fit["tau_s"]))
    pct_at_ditto = 100.0 * we_at_ditto / max(fit["A"], 1e-12)

    lines = [
        "Phase 10.3 main figure summary",
        "",
        f"Z_VALUES = {Z_VALUES}",
        "",
        "Sanity checks:",
        f"  z=0 wrong_excess      = {checks['z0_wrong_excess']:.6f}",
        f"  clair return spread   = {checks['clair_return_spread']:.6f}",
        f"  mean clair CI95       = {checks['clair_return_mean_ci']:.6f}",
        f"  clair wrong spread    = {checks['clair_wrong_spread']:.6f}",
        f"  wrong_excess monotone = {checks['wrong_excess_monotone']}",
        "",
        "Fit on wrong_excess:",
        f"  A       = {fit['A']:.4f}",
        f"  tau     = {fit['tau_s']:.4f} s",
        f"  knee90  = {np.log(10.0) * fit['tau_s']:.4f} s",
        f"  R2      = {fit['r2']:.4f}",
        "",
        "Robustness fit (drop z=20):",
        f"  A       = {fit_drop_tail['A']:.4f}",
        f"  tau     = {fit_drop_tail['tau_s']:.4f} s",
        f"  R2      = {fit_drop_tail['r2']:.4f}",
        "",
        "Ditto operating region:",
        f"  wrong_excess@0.55s = {we_at_ditto:.4f}",
        f"  pct_of_A           = {pct_at_ditto:.1f}%",
        f"  relation           = {'BEFORE' if DITTO_MAX_AOI_S < fit['tau_s'] else 'AFTER'} tau",
        "",
        "Rows:",
    ]
    for row in rows:
        lines.append(
            f"  z={row['z_steps']:2d} AoI={row['aoi_mean_s']:5.2f}s "
            f"CoB={row['cost_of_blindness']:.4f} "
            f"+/-{row['cost_of_blindness_ci95_paired']:.4f} "
            f"wrong_excess={row['wrong_excess']:.4f} "
            f"+/-{row['wrong_excess_ci95_paired']:.4f}"
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
    seeds = list(range(n_seeds))
    out_dir = Path(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    if args.quick:
        print("[MODE] quick smoke test, not confirmatory")
    elif n_seeds == N_SEEDS_CONFIRMATORY:
        print("[MODE] confirmatory")
    else:
        print(
            f"[MODE] custom seeds={n_seeds}; confirmatory default is "
            f"{N_SEEDS_CONFIRMATORY}"
        )

    rows = collect_curve(Z_VALUES, seeds)
    aoi = np.array([row["aoi_mean_s"] for row in rows], dtype=float)
    wrong = np.array([row["wrong_excess"] for row in rows], dtype=float)
    fit = fit_curve(aoi, wrong)
    fit_drop_tail = fit_curve(aoi[:-1], wrong[:-1])
    checks = sanity_checks(rows)

    print("\n[SANITY]")
    print(f"  z=0 wrong_excess      = {checks['z0_wrong_excess']:.6f}")
    print(f"  clair return spread   = {checks['clair_return_spread']:.6f}")
    print(f"  mean clair CI95       = {checks['clair_return_mean_ci']:.6f}")
    print(f"  clair wrong spread    = {checks['clair_wrong_spread']:.6f}")
    print(f"  wrong_excess monotone = {checks['wrong_excess_monotone']}")
    if checks["clair_return_spread"] <= 3.0 * checks["clair_return_mean_ci"]:
        print("  PASS: clair return is flat within CI")
    else:
        print("  WARNING: clair return is not flat within CI")

    print("\n[FIT wrong_excess]")
    print(
        f"  A={fit['A']:.4f} tau={fit['tau_s']:.4f}s "
        f"R2={fit['r2']:.4f} knee90={np.log(10.0) * fit['tau_s']:.4f}s"
    )
    if fit["r2"] < R2_ACCEPT:
        print(f"  WARNING: R2 < {R2_ACCEPT}; inspect fit before using tau.")
    else:
        print(f"  PASS: R2 >= {R2_ACCEPT}; tau is accepted.")

    print("\n[ROBUSTNESS drop z=20]")
    print(
        f"  A={fit_drop_tail['A']:.4f} "
        f"tau={fit_drop_tail['tau_s']:.4f}s "
        f"R2={fit_drop_tail['r2']:.4f}"
    )

    print("\n[PAIRED CI TABLE]")
    print(" z | AoI(s) | cost_of_blindness +/- CI95 | wrong_excess +/- CI95")
    for row in rows:
        print(
            f"{row['z_steps']:2d} | {row['aoi_mean_s']:5.2f} | "
            f"{row['cost_of_blindness']:.4f} +/- "
            f"{row['cost_of_blindness_ci95_paired']:.4f} | "
            f"{row['wrong_excess']:.4f} +/- "
            f"{row['wrong_excess_ci95_paired']:.4f}"
        )

    write_csv(rows, out_dir / "main_figure_10_3.csv")
    write_cost_table(rows, out_dir / "main_figure_10_3_cost_ci.md")
    write_summary(rows, fit, fit_drop_tail, checks, out_dir / "main_figure_10_3_summary.txt")
    make_figure(rows, fit, out_dir / "main_figure_10_3.png")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
