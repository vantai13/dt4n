#!/usr/bin/env python3
"""Phase 11.3 - plot return, wrong_rate, and safe_path_freq curves."""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

import numpy as np


Z_VALUES = (0, 1, 3, 5, 8, 12)
BREAKING_POINT_S = 1.997


def load_metric(path: Path, metric: str):
    """Load metric arrays by z and branch."""
    with open(path, newline="") as handle:
        rows = list(csv.DictReader(handle))

    data = {}
    aoi_s = {}
    for z in Z_VALUES:
        z_rows = [row for row in rows if int(row["z"]) == z]
        if not z_rows:
            raise RuntimeError(f"missing z={z}")
        aoi_s[z] = float(np.mean([float(row["aoi_mean_s"]) for row in z_rows]))
        data[z] = {}
        for branch in ("aoi", "mask"):
            values = [
                float(row[metric])
                for row in z_rows
                if row["branch"] == branch
            ]
            if len(values) != 5:
                raise RuntimeError(
                    f"{metric} z={z} branch={branch}: expected 5, got {len(values)}"
                )
            data[z][branch] = np.array(values, dtype=float)
    return data, aoi_s


def ci95(values: np.ndarray) -> float:
    """Return seed-level 95% CI half-width."""
    values = np.asarray(values, dtype=float)
    if len(values) <= 1:
        return 0.0
    return float(1.96 * values.std(ddof=1) / np.sqrt(len(values)))


def plot_metric(csv_path: Path, out_dir: Path, metric: str, ylabel: str, filename: str,
                mark_breaking_point: bool = False) -> None:
    """Plot one metric with seed-level CI bands."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data, aoi_s = load_metric(csv_path, metric)
    xs = np.array([aoi_s[z] for z in Z_VALUES], dtype=float)

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for branch, color, label in [
        ("aoi", "#2a78d6", "agent-AoI"),
        ("mask", "#eb6834", "agent-noAoI"),
    ]:
        means = np.array([data[z][branch].mean() for z in Z_VALUES], dtype=float)
        cis = np.array([ci95(data[z][branch]) for z in Z_VALUES], dtype=float)
        ax.plot(xs, means, "-o", color=color, label=label)
        ax.fill_between(xs, means - cis, means + cis, color=color, alpha=0.16)

    if mark_breaking_point:
        ax.axvline(BREAKING_POINT_S, ls="--", color="0.45", alpha=0.8)
        ymin, ymax = ax.get_ylim()
        ax.text(
            BREAKING_POINT_S,
            ymin + 0.03 * (ymax - ymin),
            f" tau={BREAKING_POINT_S:.1f}s",
            color="0.35",
            fontsize=9,
        )

    ax.set_xlabel("AoI (s)")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    path = out_dir / filename
    fig.savefig(path, dpi=150)
    print(f"[FIG] wrote {path}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="results/ablation/zsweep.csv")
    parser.add_argument("--out-dir", default="results/ablation")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    csv_path = Path(args.csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(out_dir / "mplconfig"))
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

    plot_metric(
        csv_path,
        out_dir,
        "return",
        "return (mean over eval seeds)",
        "fig_return.png",
        mark_breaking_point=True,
    )
    plot_metric(
        csv_path,
        out_dir,
        "wrong_rate",
        "wrong_rate (lower is better)",
        "fig_wrong.png",
    )
    plot_metric(
        csv_path,
        out_dir,
        "safe_path_freq",
        "safe_path_freq",
        "fig_safe.png",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
