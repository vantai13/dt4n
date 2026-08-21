#!/usr/bin/env python3
"""Render Lesson 23.15 Figure 1 from the committed eight-cell artifact."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Mapping, Sequence


INPUT = "results/phase-23/eight_cell_sweep.json"
OUTPUT = "results/phase-23/fig1_lift_vs_swing_8cells.png"


def plot(report: Mapping[str, Any], out: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.2, 5.8))
    label_offsets = {
        "poisson@0.700": (8, 58),
        "h2@0.850": (8, 43),
        "h2@0.925": (8, 28),
        "h2@0.960": (8, 13),
    }
    for cell, row in report["cells"].items():
        d = row["lift_swing_F2"]
        seen = row["status"] == "seen"
        ax.scatter(d["swing"], d["lift"], marker="o" if seen else "s", s=75,
                   color="#1f77b4" if seen else "#d62728", edgecolor="black", linewidth=0.5)
        offset = label_offsets.get(cell, (5, 4))
        ax.annotate(
            cell,
            (d["swing"], d["lift"]),
            xytext=offset,
            textcoords="offset points",
            fontsize=8,
            arrowprops={"arrowstyle": "-", "color": "#777777", "linewidth": 0.6}
            if cell in label_offsets else None,
        )
    vals = [0.0] + [float(row["lift_swing_F2"][k]) for row in report["cells"].values() for k in ("lift", "swing")]
    lo, hi = min(vals), max(vals)
    pad = max((hi - lo) * 0.08, 0.002)
    ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], "k--", linewidth=1, label="lift = swing")
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_ylim(lo - pad, hi + pad)
    ax.set_xlabel("fallback swing (F2)")
    ax.set_ylabel("certificate lift (F2 decomposition)")
    ax.set_title("Lift versus fallback swing across eight operating cells")
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
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
