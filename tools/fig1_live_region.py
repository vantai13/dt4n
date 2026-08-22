#!/usr/bin/env python3
"""Render the preregistered live-region boundary figure."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Mapping, Sequence


INPUT = "results/SUPERSEDED/phase-23/live_region_sweep.json"
OUTPUT = "results/SUPERSEDED/phase-23/fig1_live_region.png"


def plot(report: Mapping[str, Any], out: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(8.6, 7.2), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    colors = {"poisson": "#1f77b4", "h2": "#d62728"}
    for mode in ("poisson", "h2"):
        rows = []
        for cell, payload in report["cells"].items():
            if not cell.startswith(mode + "@"):
                continue
            rho = float(cell.split("@")[1])
            d = payload["lift_swing_F2"]
            rows.append((rho, float(d["lift"] - d["swing"]), float(d["err_neo"])))
        rows.sort()
        if not rows:
            continue
        x, y, err = zip(*rows)
        ax.plot(x, y, color=colors[mode], marker="o", linewidth=1.8, label=mode)
        ax2.plot(x, err, color=colors[mode], marker="o", linewidth=1.8, label=mode)
        for rho, value, e in rows:
            if e < float(report["live_threshold"]):
                ax.scatter([rho], [value], color="#9ca3af", edgecolor="black", s=65, zorder=5)
                ax2.scatter([rho], [e], color="#9ca3af", edgecolor="black", s=65, zorder=5)
    bracket = report["metrics"].get("M_53_boundary_bracket")
    if bracket:
        ax.axvspan(bracket[0], bracket[1], color="#f59e0b", alpha=0.18, label="boundary bracket")
    ax.axhline(0.0, color="black", linestyle="--", linewidth=1)
    ax.set_ylabel("lift - swing")
    ax.set_title("Live decision region and observed benefit boundary")
    ax.grid(alpha=0.25)
    ax.legend()
    threshold = float(report["live_threshold"])
    ax2.axhspan(0.0, threshold, color="#9ca3af", alpha=0.18, label="dead: err_neo < %.2f" % threshold)
    ax2.axhline(threshold, color="#555555", linestyle=":", linewidth=1)
    ax2.set_xlabel(r"mean load $\bar{\rho}$")
    ax2.set_ylabel("err_neo")
    ax2.grid(alpha=0.25)
    ax2.legend(loc="best")
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
