#!/usr/bin/env python3
"""Phase 20R.7 -- the four final figures listed in docs/phase-20R/08-mechanism.md sec.7.

  1. mechanism_gap_clipped        gap_ab(x) under the clipped common-mode shift
  2. mechanism_channel_split_d2   |w_loss d2 loss| vs |d2 delay|  (prediction P3)
  3. mechanism_d2_cost            d2(cost)/d(rho)2 across rho
  4. mechanism_radius_vs_err      median r(s) vs err at the operating z  (P1)

Plus one clearly separated exploratory figure. It is kept in its own file with
its own prefix so no reader can mistake a post-hoc observation for one of the
three predictions signed in Amendment 15 sec.7.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from measurements import margin_radius as MR
from measurements import mechanism_map as MM
from twin import topology_v7 as T7


K4 = "results/phase-20R/mechanism_k4_closed_form.json"
MAPS = "results/phase-20R/mechanism_maps.json"
RADIUS = "results/phase-20R/margin_radius.json"
FIGDIR = "docs/phase-20R/figures"
MODES = ("poisson", "h2")


def ensure_dir(path: str) -> None:
    if path:
        os.makedirs(path, exist_ok=True)


def load(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def mode_block(report: Mapping[str, Any], mode: str) -> Mapping[str, Any]:
    for block in report["modes"]:
        if str(block["mode"]) == str(mode):
            return block
    raise KeyError(mode)


def fig1_gap_clipped(k4: Mapping[str, Any], out: str, x_max: float = 0.006) -> str:
    fig, axes = plt.subplots(1, len(MODES), figsize=(11, 4.2))
    for ax, mode in zip(axes, MODES):
        block = mode_block(k4, mode)
        delay = block["link_delay_ms"]
        loss = block["link_loss"]
        w_loss = float(block["w_loss"])
        x = np.linspace(0.0, x_max, 601)

        # x is the per-link magnitude of the negative common-mode shift, so the
        # shift handed to path_costs is -x. r_path = 3 * x_link.
        curves = {
            path: np.array([MM.path_costs(delay, loss, w_loss, shift=-float(xi))[path] for xi in x])
            for path in T7.PATH_NAMES
        }

        pairs = sorted(
            block["clipped_negative_loss_shift"],
            key=lambda row: float("inf") if row["first_r_star_path"] is None else float(row["first_r_star_path"]),
        )
        for row in pairs[:3]:
            a, b = row["pair"]
            ax.plot(3.0 * x, curves[a] - curves[b], lw=1.6, label="%s - %s" % (a, b))
            if row["first_r_star_path"] is not None:
                ax.axvline(float(row["first_r_star_path"]), color="black", ls=":", lw=1)

        scan = block["scan_cascade_loss_common_mode"].get("r_star_bracket")
        if scan:
            ax.axvspan(float(scan["r_star_lo"]), float(scan["r_star_hi"]), color="tab:red", alpha=0.25, label="scan bracket")
        ax.axhline(0.0, color="black", lw=0.9)
        ax.set_xlabel(r"$r_{\mathrm{path}} = 3\,x_{\mathrm{link}}$")
        ax.set_title(mode)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    axes[0].set_ylabel("cost gap [ms]")
    fig.suptitle("20R.7 fig 1 - clipped common-mode landscape; a zero crossing is a ranking flip")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def fig2_channel_split_d2(maps: Mapping[str, Any], out: str) -> str:
    rows = [r for r in maps["rows"] if r["significant_d2_loss"]]
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    for mode, marker in zip(MODES, ("o", "s")):
        cell = [r for r in rows if r["mode"] == mode]
        ax.scatter(
            [abs(r["d2_delay_ms"]) for r in cell],
            [abs(r["w_d2_loss_ms"]) for r in cell],
            marker=marker,
            s=45,
            alpha=0.85,
            label=mode,
        )
    lim = [1.0, 1e5]
    ax.plot(lim, lim, color="black", lw=1, ls="--", label="equal contribution")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$|d^2(\mathrm{delay})/d\rho^2|$  [ms]")
    ax.set_ylabel(r"$|w_{\mathrm{loss}}\, d^2(\mathrm{loss})/d\rho^2|$  [ms]")
    ax.set_title("20R.7 fig 2 - P3: every relevant cell sits above the diagonal")
    ax.grid(alpha=0.3, which="both")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def fig3_d2_cost(maps: Mapping[str, Any], out: str) -> str:
    rows = maps["rows"]
    fig, axes = plt.subplots(1, len(MODES), figsize=(11, 4.2), sharex=True)
    for ax, mode in zip(axes, MODES):
        cells = sorted({(r["bw"], r["q"]) for r in rows if r["mode"] == mode})
        for bw, q in cells:
            s = sorted((r for r in rows if r["mode"] == mode and r["bw"] == bw and r["q"] == q), key=lambda r: r["rho"])
            line, = ax.plot(
                [r["rho"] for r in s],
                [r["d2_cost_ms"] for r in s],
                marker="o",
                ms=3,
                alpha=0.6,
                label="bw=%.0f q=%d" % (bw, q),
            )
            sig = [r for r in s if r["significant_d2_loss"]]
            ax.plot(
                [r["rho"] for r in sig],
                [r["d2_cost_ms"] for r in sig],
                linestyle="none",
                marker="o",
                ms=7,
                mfc="none",
                mec=line.get_color(),
                mew=1.6,
            )
        ax.axhline(0.0, color="black", lw=0.9)
        ax.set_yscale("symlog", linthresh=100.0)
        ax.set_xlabel(r"$\rho$")
        ax.set_title(mode)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel(r"$d^2(\mathrm{cost})/d\rho^2$  [ms]")
    axes[0].legend(fontsize=8)
    fig.suptitle("20R.7 fig 3 - cost curvature; rings pass the Amendment 16 significance gate")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def _radius_points(radius: Mapping[str, Any], key: str) -> List[Dict[str, Any]]:
    err = MR.load_err(z=float(radius["z"]))
    out = []
    for cell in radius["cells"]:
        k = (cell["mode"], cell["rho_bar"])
        if k in err:
            out.append(
                {
                    "mode": cell["mode"],
                    "rho_bar": cell["rho_bar"],
                    "x": float(cell[key]["mean"]),
                    "y": float(err[k]["err_total"]),
                    "lo": float(err[k]["err_total_ci95_lo"]),
                    "hi": float(err[k]["err_total_ci95_hi"]),
                }
            )
    return out


def _scatter_cells(ax, points, xlabel):
    for mode, marker in zip(MODES, ("o", "s")):
        cell = [p for p in points if p["mode"] == mode]
        ax.errorbar(
            [p["x"] for p in cell],
            [p["y"] for p in cell],
            yerr=[[p["y"] - p["lo"] for p in cell], [p["hi"] - p["y"] for p in cell]],
            linestyle="none",
            marker=marker,
            ms=8,
            capsize=3,
            label=mode,
        )
        for p in cell:
            ax.annotate(r"$\bar\rho$=%.3f" % p["rho_bar"], (p["x"], p["y"]), textcoords="offset points", xytext=(6, 5), fontsize=7)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(r"$\mathrm{err}_{\mathrm{total}}$")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)


def fig4_radius_vs_err(radius: Mapping[str, Any], out: str) -> str:
    points = _radius_points(radius, "median_r_bound")
    h1 = radius["h1_bound"]
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    _scatter_cells(ax, points, r"median $r(s)$  [units of $\rho$]")
    ax.set_title(
        "20R.7 fig 4 - P1 NOT SUPPORTED\n"
        r"Spearman $\rho=%+.3f$, one-sided $p=%.4f$ (alpha=0.05), $z=%.2f$"
        % (h1["pooled"]["rho"], h1["pooled"]["p_one_sided_negative"], float(radius["z"]))
    )
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def fig_exploratory_exceedance(radius: Mapping[str, Any], out: str) -> str:
    points = _radius_points(radius, "frac_r_bound_below_sigma")
    stat = MR.spearman_negative([-p["x"] for p in points], [p["y"] for p in points])
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    _scatter_cells(ax, points, r"$P[\,r(s) < \sigma_\rho\,]$")
    ax.set_title(
        "EXPLORATORY - NOT a Phase 20R result\n"
        r"post-hoc, generated after P1 failed; Spearman $\rho=%+.3f$, $p=%.2e$"
        % (-stat["rho"], stat["p_one_sided_negative"])
    )
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--k4", default=K4)
    ap.add_argument("--maps", default=MAPS)
    ap.add_argument("--radius", default=RADIUS)
    ap.add_argument("--figdir", default=FIGDIR)
    args = ap.parse_args(argv)

    ensure_dir(args.figdir)
    k4, maps, radius = load(args.k4), load(args.maps), load(args.radius)
    made = [
        fig1_gap_clipped(k4, os.path.join(args.figdir, "mechanism_gap_clipped.png")),
        fig2_channel_split_d2(maps, os.path.join(args.figdir, "mechanism_channel_split_d2.png")),
        fig3_d2_cost(maps, os.path.join(args.figdir, "mechanism_d2_cost.png")),
        fig4_radius_vs_err(radius, os.path.join(args.figdir, "mechanism_radius_vs_err.png")),
        fig_exploratory_exceedance(radius, os.path.join(args.figdir, "exploratory_margin_exceedance.png")),
    ]
    for path in made:
        print("-> %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
