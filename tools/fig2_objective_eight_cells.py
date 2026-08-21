#!/usr/bin/env python3
"""Render Lesson 23.15 Figure 2 from the committed eight-cell artifact."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Mapping, Sequence


INPUT = "results/phase-23/eight_cell_sweep.json"
OUTPUT = "results/phase-23/fig2_objective_eight_cells.png"


def plot(report: Mapping[str, Any], out: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9.0, 6.0))
    for cell, row in report["cells"].items():
        curve = row["objective"]["curve"]
        ax.plot(
            [point["w_eff_over_w_loss"] for point in curve],
            [point["delta_system_vs_neo"] for point in curve],
            marker="o" if row["status"] == "seen" else None,
            markersize=3.5,
            linestyle="-" if row["status"] == "seen" else "--",
            linewidth=1.7,
            label=cell,
        )
    ratio = float(report["metrics"]["M_47_confirm_ratio"])
    ax.axhline(0.0, color="black", linestyle="--", linewidth=1)
    ax.axvline(ratio, color="#555555", linestyle=":", linewidth=1.3, label="confirm ratio")
    ax.set_xlabel(r"objective ratio $w_{eff}/w_{loss}$")
    ax.set_ylabel(r"$\Delta = R_{system}-R_{neo}$")
    ax.set_title("Frozen-system objective curves across eight operating cells")
    ax.grid(alpha=0.25)
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    fig.savefig(out, dpi=180)
    plt.close(fig)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=INPUT)
    parser.add_argument("--out", default=OUTPUT)
    args = parser.parse_args(argv)
    with open(args.input, "r", encoding="utf-8") as handle:
        plot(json.load(handle), args.out)
    print("figure -> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
