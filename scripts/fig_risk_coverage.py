#!/usr/bin/env python3
"""Draw the Phase 22 risk-coverage headline figure."""

from __future__ import annotations

import argparse
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/phase-22/config_matrix_poisson_0.925.json")
    parser.add_argument("--out", default="results/phase-22/fig_risk_coverage.pdf")
    args = parser.parse_args()

    res = json.load(open(args.input, encoding="utf-8"))
    anchor = float(res["anchor_err_on_test"])
    style = {
        "C0": ("k", "o", "-"),
        "C1": ("tab:blue", "s", "--"),
        "C2": ("tab:orange", "^", "-."),
        "C3": ("tab:red", "D", "-"),
    }

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    for cfg, (color, marker, line) in style.items():
        rows = [
            r for r in res["configs"][cfg]["rows"]
            if r["err_given_accept"] is not None
        ]
        x = [float(r["acceptance"]) for r in rows]
        y = [float(r["err_given_accept"]) for r in rows]
        ok = [bool(r["pass_coverage"]) for r in rows]
        label = "%s %s (AURC %.4f)" % (
            cfg,
            res["configs"][cfg]["label"],
            float(res["configs"][cfg]["aurc"]),
        )
        ax[0].plot(x, y, line, color=color, lw=1.6, label=label, zorder=2)
        ax[0].scatter(
            [xi for xi, good in zip(x, ok) if good],
            [yi for yi, good in zip(y, ok) if good],
            marker=marker,
            s=34,
            color=color,
            zorder=3,
        )
        ax[0].scatter(
            [xi for xi, good in zip(x, ok) if not good],
            [yi for yi, good in zip(y, ok) if not good],
            marker=marker,
            s=34,
            facecolors="none",
            edgecolors=color,
            zorder=3,
        )

    ax[0].axhline(0.5 * anchor, color="gray", ls=":", lw=1)
    ax[0].axvline(0.10, color="gray", ls=":", lw=1)
    ax[0].set_xlabel("coverage = acceptance rate")
    ax[0].set_ylabel("risk = P(wrong | accept)")
    ax[0].set_title("Risk-coverage frontier\nfilled = coverage valid, hollow = violated")
    ax[0].legend(fontsize=7, loc="upper left")
    ax[0].grid(alpha=0.25)

    for cfg, (color, marker, line) in style.items():
        rows = [
            r for r in res["configs"][cfg]["rows"]
            if r["violation_given_accept"] is not None
        ]
        ax[1].plot(
            [float(r["kappa"]) for r in rows],
            [float(r["violation_given_accept"]) for r in rows],
            line,
            color=color,
            marker=marker,
            ms=4,
            lw=1.6,
            label=cfg,
        )
    ax[1].axhline(0.10, color="k", ls="--", lw=1.2, label="alpha=0.10")
    ax[1].set_xlabel("kappa")
    ax[1].set_ylabel("P(s > qhat | accept)")
    ax[1].set_title("Post-selection coverage violation")
    ax[1].set_xlim(0, 3.1)
    ax[1].legend(fontsize=8)
    ax[1].grid(alpha=0.25)

    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    fig.savefig(args.out, dpi=200)
    print(args.out)


if __name__ == "__main__":
    main()
