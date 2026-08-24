#!/usr/bin/env python3
"""Render the post-hoc M-180 live-region pattern grouped by process family."""
from __future__ import annotations

import argparse
import json
import os
from typing import Any, Mapping, Sequence


INPUT = "results/LIVE/phase-23/live_region_sweep_slaB.json"
OUTPUT = "results/LIVE/phase-23/fig3_live_region_by_family.png"


def family_rows(report: Mapping[str, Any], mode: str) -> list[dict[str, Any]]:
    rows = []
    for cell, payload in report["cells"].items():
        if not cell.startswith(mode + "@"):
            continue
        delta = float(payload["F2"]["delta_system_vs_neo"])
        rows.append(
            {
                "cell": cell,
                "rho_bar": float(cell.split("@")[1]),
                "delta": delta,
                "regime": str(payload["live_definitions"]["regime"]),
                "direction": (
                    "helpful" if delta < 0.0 else ("harmful" if delta > 0.0 else "neutral")
                ),
            }
        )
    return sorted(rows, key=lambda row: row["rho_bar"])


def plot(report: Mapping[str, Any], out: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"helpful": "#15803d", "harmful": "#b91c1c", "neutral": "#64748b"}
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.7), sharey=True)
    for ax, mode in zip(axes, ("poisson", "h2")):
        rows = family_rows(report, mode)
        live = [row for row in rows if row["regime"] == "LIVE"]
        if live:
            ax.axvspan(
                min(row["rho_bar"] for row in live),
                max(row["rho_bar"] for row in live),
                color="#fbbf24",
                alpha=0.18,
                label="authoritative LIVE span",
            )
        ax.plot(
            [row["rho_bar"] for row in rows],
            [row["delta"] for row in rows],
            color="#334155",
            linewidth=1.4,
            zorder=2,
        )
        for row in rows:
            ax.scatter(
                [row["rho_bar"]],
                [row["delta"]],
                color=colors[row["direction"]],
                edgecolor="white",
                linewidth=0.7,
                s=62,
                zorder=3,
            )
            ax.annotate(
                row["regime"],
                (row["rho_bar"], row["delta"]),
                xytext=(0, 7),
                textcoords="offset points",
                ha="center",
                fontsize=7,
                rotation=28,
            )
        ax.axhline(0.0, color="black", linestyle="--", linewidth=0.9)
        ax.set_title(mode)
        ax.set_xlabel(r"mean load $\bar{\rho}$")
        ax.grid(alpha=0.2)
        ax.legend(loc="best", fontsize=8)
    axes[0].set_ylabel("fallback vs twin weighted delta (F2)")
    fig.suptitle("M-180 (exploratory/post-hoc): direction differs by process family")
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
