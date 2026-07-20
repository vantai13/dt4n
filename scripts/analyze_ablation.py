#!/usr/bin/env python3
"""Phase 11.3 - paired tests for the AoI/noAoI ablation."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np
from scipy import stats


BRANCHES = ("aoi", "mask")
Z_VALUES = (0, 1, 3, 5, 8, 12)
METRICS = ("return", "wrong_rate", "safe_path_freq")


def load_rows(path: Path) -> list[dict]:
    """Load z-sweep CSV rows."""
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def values_by_z_branch(rows: list[dict], metric: str) -> dict:
    """Return data[z][branch] as seed-sorted arrays."""
    data = {}
    for z in Z_VALUES:
        data[z] = {}
        for branch in BRANCHES:
            pairs = [
                (int(row["seed"]), float(row[metric]))
                for row in rows
                if row["branch"] == branch and int(row["z"]) == z
            ]
            pairs.sort()
            seeds = [seed for seed, _value in pairs]
            if seeds != [0, 1, 2, 3, 4]:
                raise RuntimeError(
                    f"{metric} z={z} branch={branch}: expected seeds 0..4, got {seeds}"
                )
            data[z][branch] = np.array([value for _seed, value in pairs], dtype=float)
    return data


def aoi_by_z(rows: list[dict]) -> dict[int, float]:
    """Return mean AoI per z."""
    out = {}
    for z in Z_VALUES:
        values = [float(row["aoi_mean_s"]) for row in rows if int(row["z"]) == z]
        if not values:
            raise RuntimeError(f"missing z={z}")
        out[z] = float(np.mean(values))
    return out


def paired_stats(aoi_values: np.ndarray, mask_values: np.ndarray) -> dict:
    """Paired t-test and paired Cohen d for AoI minus mask."""
    diff = np.asarray(aoi_values, dtype=float) - np.asarray(mask_values, dtype=float)
    mean_diff = float(diff.mean())
    sd = float(diff.std(ddof=1)) if len(diff) > 1 else 0.0
    if sd <= 1e-12:
        if abs(mean_diff) <= 1e-12:
            t_stat = 0.0
            p_value = 1.0
            cohens_d = 0.0
        else:
            t_stat = math.copysign(float("inf"), mean_diff)
            p_value = 0.0
            cohens_d = math.copysign(float("inf"), mean_diff)
    else:
        t_stat, p_value = stats.ttest_rel(aoi_values, mask_values)
        cohens_d = mean_diff / sd
    return {
        "mean_aoi": float(np.mean(aoi_values)),
        "mean_mask": float(np.mean(mask_values)),
        "mean_diff": mean_diff,
        "diff_sd": sd,
        "t": float(t_stat),
        "p": float(p_value),
        "cohens_d_paired": float(cohens_d),
    }


def metric_table(rows: list[dict], metric: str) -> list[dict]:
    """Build paired stats rows for one metric."""
    data = values_by_z_branch(rows, metric)
    aoi_s = aoi_by_z(rows)
    out = []
    for z in Z_VALUES:
        stats_row = paired_stats(data[z]["aoi"], data[z]["mask"])
        stats_row.update({"metric": metric, "z": z, "aoi_mean_s": aoi_s[z]})
        out.append(stats_row)
    return out


def print_return_table(table: list[dict], lines: list[str]) -> None:
    """Append formatted return table to lines."""
    lines.append("=" * 88)
    lines.append("PRIMARY CHANNEL - return: agent-AoI vs agent-noAoI")
    lines.append("=" * 88)
    lines.append(
        f"{'z':>3} {'AoI(s)':>7} {'ret_aoi':>9} {'ret_mask':>9} "
        f"{'diff':>10} {'p':>9} {'d':>8} {'verdict':>14}"
    )
    for row in table:
        verdict = "different" if row["p"] < 0.05 else "tie"
        lines.append(
            f"{row['z']:>3} {row['aoi_mean_s']:>7.2f} "
            f"{row['mean_aoi']:>9.3f} {row['mean_mask']:>9.3f} "
            f"{row['mean_diff']:>+10.4f} {row['p']:>9.4f} "
            f"{row['cohens_d_paired']:>+8.2f} {verdict:>14}"
        )


def print_metric_table(table: list[dict], title: str, lines: list[str]) -> None:
    """Append formatted secondary metric table."""
    lines.append("")
    lines.append("=" * 88)
    lines.append(title)
    lines.append("=" * 88)
    lines.append(
        f"{'z':>3} {'AoI(s)':>7} {'aoi':>9} {'mask':>9} "
        f"{'diff':>10} {'p':>9} {'d':>8}"
    )
    for row in table:
        lines.append(
            f"{row['z']:>3} {row['aoi_mean_s']:>7.2f} "
            f"{row['mean_aoi']:>9.4f} {row['mean_mask']:>9.4f} "
            f"{row['mean_diff']:>+10.4f} {row['p']:>9.4f} "
            f"{row['cohens_d_paired']:>+8.2f}"
        )


def localized_verdict(return_table: list[dict], lines: list[str]) -> None:
    """Append H1/H2 localized-effect verdict."""
    by_z = {int(row["z"]): row for row in return_table}
    z0 = by_z[0]
    z_hi = by_z[max(Z_VALUES)]
    lines.append("")
    lines.append("=" * 88)
    lines.append("LOCALIZATION CHECK")
    lines.append("=" * 88)
    lines.append(
        f"z=0  fresh: diff={z0['mean_diff']:+.4f} p={z0['p']:.4f} "
        "(expected tie)"
    )
    lines.append(
        f"z={max(Z_VALUES)} stale: diff={z_hi['mean_diff']:+.4f} "
        f"p={z_hi['p']:.4f} (expected AoI > mask)"
    )
    if z0["p"] > 0.05 and z_hi["p"] < 0.05 and z_hi["mean_diff"] > 0:
        lines.append(
            "VERDICT: localized effect found - H1 and H2 are supported."
        )
    elif z0["p"] < 0.05:
        lines.append(
            "VERDICT: confounder warning - branches differ already at z=0."
        )
    else:
        lines.append(
            "VERDICT: not conclusive - inspect trend/effect sizes before claiming."
        )


def write_stats_csv(tables: list[list[dict]], path: Path) -> None:
    """Write long-form stats CSV."""
    fields = [
        "metric",
        "z",
        "aoi_mean_s",
        "mean_aoi",
        "mean_mask",
        "mean_diff",
        "diff_sd",
        "t",
        "p",
        "cohens_d_paired",
    ]
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for table in tables:
            for row in table:
                writer.writerow({field: row[field] for field in fields})
    print(f"[CSV] wrote {path}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="results/ablation/zsweep.csv")
    parser.add_argument("--out", default="results/ablation/analysis_summary.txt")
    parser.add_argument("--stats-csv", default="results/ablation/analysis_by_z.csv")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    rows = load_rows(Path(args.csv))
    return_table = metric_table(rows, "return")
    wrong_table = metric_table(rows, "wrong_rate")
    safe_table = metric_table(rows, "safe_path_freq")

    lines = []
    print_return_table(return_table, lines)
    print_metric_table(
        wrong_table,
        "MECHANISM CHANNEL - wrong_rate (lower is better)",
        lines,
    )
    print_metric_table(
        safe_table,
        "SECONDARY CHANNEL - safe_path_freq (interpret cautiously)",
        lines,
    )
    localized_verdict(return_table, lines)

    text = "\n".join(lines)
    print(text)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text + "\n")
    print(f"[TXT] wrote {out_path}")
    write_stats_csv([return_table, wrong_table, safe_table], Path(args.stats_csv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
