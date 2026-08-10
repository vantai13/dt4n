#!/usr/bin/env python3
"""Plot the Lesson 20R.7 mechanism maps from ``mechanism_maps.json``.

Four figures, in the order fixed by Amendment 15 sec.3:

  1. d(loss)/d(rho)                          per family and link class
  2. d2(loss)/d(rho)2 with error bars        significance-gated markers
  3. d(cost)/d(rho) split into contributions delay vs w_loss*loss
  4. |w_loss*d1_loss| / |d1_delay|           dimensionless channel ratio

Every published number comes from a grid node. Lines only connect nodes; they
are a visual guide, not an interpolation claim.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


MAPS = "results/phase-20R/mechanism_maps.json"
FIGDIR = "docs/phase-20R/figures"
MODES = ("poisson", "h2")


def ensure_dir(path: str) -> None:
    if path:
        os.makedirs(path, exist_ok=True)


def load(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cells(rows: Sequence[Mapping[str, Any]], mode: str) -> List[Tuple[float, int]]:
    return sorted({(float(r["bw"]), int(r["q"])) for r in rows if str(r["mode"]) == mode})


def series(rows: Sequence[Mapping[str, Any]], mode: str, bw: float, q: int) -> List[Mapping[str, Any]]:
    return sorted(
        (r for r in rows if str(r["mode"]) == mode and float(r["bw"]) == bw and int(r["q"]) == q),
        key=lambda r: float(r["rho"]),
    )


def label(bw: float, q: int) -> str:
    return "bw=%.0f Mbps, q=%d" % (bw, q)


def fig1_d1_loss(report: Mapping[str, Any], out: str) -> str:
    rows = report["rows"]
    fig, axes = plt.subplots(1, len(MODES), figsize=(11, 4), sharex=True)
    for ax, mode in zip(axes, MODES):
        for bw, q in cells(rows, mode):
            s = series(rows, mode, bw, q)
            ax.plot([r["rho"] for r in s], [r["d1_loss"] for r in s], marker="o", ms=3, label=label(bw, q))
        ax.set_title("%s" % mode)
        ax.set_xlabel(r"$\rho$")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel(r"$d(\mathrm{loss})/d\rho$  [1/$\rho$]")
    axes[0].legend(fontsize=8)
    fig.suptitle("Lesson 20R.7 map 1 - loss slope (nodes only, h = %.2f)" % report["estimator"]["h_primary"])
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def fig2_d2_loss(report: Mapping[str, Any], out: str) -> str:
    rows = report["rows"]
    k = float(report["estimator"]["sig_k"])
    fig, axes = plt.subplots(1, len(MODES), figsize=(11, 4), sharex=True)
    for ax, mode in zip(axes, MODES):
        for bw, q in cells(rows, mode):
            s = series(rows, mode, bw, q)
            x = [r["rho"] for r in s]
            y = [r["d2_loss"] for r in s]
            e = [k * r["se_d2_loss"] for r in s]
            line = ax.errorbar(x, y, yerr=e, marker="o", ms=3, lw=1, elinewidth=0.8,
                               capsize=2, alpha=0.55, label=label(bw, q))
            colour = line.lines[0].get_color()
            sig = [r for r in s if r["significant_d2_loss"]]
            ax.plot([r["rho"] for r in sig], [r["d2_loss"] for r in sig],
                    linestyle="none", marker="o", ms=7, mfc="none", mec=colour, mew=1.6)
        ax.axhline(0.0, color="black", lw=0.8)
        ax.set_title(mode)
        ax.set_xlabel(r"$\rho$")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel(r"$d^2(\mathrm{loss})/d\rho^2$  [1/$\rho^2$]")
    axes[0].legend(fontsize=8)
    fig.suptitle(r"Lesson 20R.7 map 2 - loss curvature; bars are $\pm%.0f\,$SE, rings pass the gate" % k)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def fig3_cost_split(report: Mapping[str, Any], out: str) -> str:
    rows = report["rows"]
    fig, axes = plt.subplots(1, len(MODES), figsize=(11, 4), sharex=True)
    for ax, mode in zip(axes, MODES):
        bw, q = cells(rows, mode)[-1]
        s = series(rows, mode, bw, q)
        x = [r["rho"] for r in s]
        ax.plot(x, [r["d1_delay_ms"] for r in s], marker="o", ms=3, label=r"$d(\mathrm{delay})/d\rho$")
        ax.plot(x, [r["w_d1_loss_ms"] for r in s], marker="s", ms=3,
                label=r"$w_{\mathrm{loss}}\, d(\mathrm{loss})/d\rho$")
        ax.plot(x, [r["d1_cost_ms"] for r in s], marker="^", ms=3, lw=2, label=r"$d(\mathrm{cost})/d\rho$")
        ax.set_yscale("symlog", linthresh=1.0)
        ax.set_title("%s, %s  ($w_{loss}$=%.0f)" % (mode, label(bw, q), s[0]["w_loss"]))
        ax.set_xlabel(r"$\rho$")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    axes[0].set_ylabel("ms per unit " + r"$\rho$")
    fig.suptitle("Lesson 20R.7 map 3 - cost gradient split by channel")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def fig4_channel_ratio(report: Mapping[str, Any], out: str) -> str:
    rows = report["rows"]
    crossing = {(str(c["mode"]), float(c["bw"]), int(c["q"])): c["rho_channel_crossing"]
                for c in report["channel_crossing"]}
    fig, axes = plt.subplots(1, len(MODES), figsize=(11, 4), sharex=True)
    for ax, mode in zip(axes, MODES):
        for bw, q in cells(rows, mode):
            s = series(rows, mode, bw, q)
            x = [r["rho"] for r in s]
            y = [min(float(r["ratio_channel_d1"]), 1e4) for r in s]
            line, = ax.plot(x, y, marker="o", ms=3, label=label(bw, q))
            cross = crossing.get((mode, bw, q))
            if cross is not None:
                ax.axvline(float(cross), color=line.get_color(), ls="--", lw=1, alpha=0.7)
        ax.axhline(1.0, color="black", lw=0.9)
        ax.set_yscale("log")
        ax.set_title(mode)
        ax.set_xlabel(r"$\rho$")
        ax.grid(alpha=0.3, which="both")
    axes[0].set_ylabel(r"$|w_{\mathrm{loss}} d_\rho \mathrm{loss}| \, / \, |d_\rho \mathrm{delay}|$")
    axes[0].legend(fontsize=8)
    fig.suptitle("Lesson 20R.7 map 4 - channel dominance; dashed line is the crossing")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--maps", default=MAPS)
    ap.add_argument("--figdir", default=FIGDIR)
    args = ap.parse_args(argv)

    report = load(args.maps)
    ensure_dir(args.figdir)
    made = [
        fig1_d1_loss(report, os.path.join(args.figdir, "mechanism_d1_loss.png")),
        fig2_d2_loss(report, os.path.join(args.figdir, "mechanism_d2_loss.png")),
        fig3_cost_split(report, os.path.join(args.figdir, "mechanism_cost_split.png")),
        fig4_channel_ratio(report, os.path.join(args.figdir, "mechanism_channel_ratio.png")),
    ]
    for path in made:
        print("-> %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
