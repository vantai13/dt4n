#!/usr/bin/env python3
"""Lesson 23.22 Task B-3 -- hinh ba panel cua ket qua tai hieu chuan.

(a) heatmap 8x8 `viol|accept` cua C3-R @ `n` = 250, hang/cot sap theo `kappa_A`
    GIAM DAN. Thong diep: KHONG mot o nao vuot `alpha`; bon o duoi san
    acceptance duoc danh dau rieng.
(b) scatter |log(kappa_A/kappa_B)| vs |acceptance - a*| @ `n` = 500, 56 o ngoai
    duong cheo, kem duong hoi quy. Thong diep: gia cua `kappa` sai CO DAU va
    DU DOAN DUOC.
(c) bon cot sd -- menh de bao toan. Thong diep: KHONG ai giu duoc CA HAI.

Moi con so trong hinh duoc TINH LAI tu `rows` cua artifact, khong doc lai
khoi `predictions`. Neu hai ben lech, hinh se lech va test se bat.

Chay:
    python -m tools.fig4_recalibrate_transfer
"""
from __future__ import annotations

import argparse
import json
import math
import os
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Sequence, Tuple

INPUT = "results/LIVE/phase-23/recalibrate_transfer.json"
OUTPUT = "results/LIVE/phase-23/fig4_recalibrate_transfer.png"
ALPHA = 0.10
FLOOR = 0.20
N_HEAT = 250
N_SLOPE = 500


def _mean(xs: Sequence[Any]) -> float:
    vals = [float(x) for x in xs if x is not None and math.isfinite(float(x))]
    return float("nan") if not vals else sum(vals) / len(vals)


def cells_by_kappa(report: Mapping[str, Any]) -> List[Tuple[str, float]]:
    """8 cell song, sap theo `kappa_A` GIAM DAN (tuc do kho TANG DAN)."""
    kap = report["config"]["kappa_A"]
    live = list(report["cells_live"])
    return sorted(((c, float(kap[c])) for c in live), key=lambda t: -t[1])


def aggregate(report: Mapping[str, Any], n: int) -> Dict[Tuple[str, str], Dict[str, float]]:
    """o(A,B) = TRUNG BINH tren draw, chi gia tri huu han (`A068` muc 3.1b)."""
    bucket: Dict[Tuple[str, str], List[Mapping[str, Any]]] = defaultdict(list)
    for row in report["rows"]:
        if int(row["n"]) == int(n):
            bucket[(row["A"], row["B"])].append(row)
    fields = (
        "C3_viol_given_accept", "C3_acceptance_test", "C3_err_given_accept",
        "B2_acceptance_test", "B2_err_given_accept", "anchor_err",
    )
    return {
        key: {f: _mean([r[f] for r in rows]) for f in fields}
        for key, rows in bucket.items()
    }


def panel_a_matrix(report: Mapping[str, Any]) -> Dict[str, Any]:
    order = cells_by_kappa(report)
    agg = aggregate(report, N_HEAT)
    names = [c for c, _ in order]
    viol = [[agg[(a, b)]["C3_viol_given_accept"] for b in names] for a in names]
    below = [(i, j) for i, a in enumerate(names) for j, b in enumerate(names)
             if agg[(a, b)]["C3_acceptance_test"] < FLOOR]
    flat = [v for row in viol for v in row]
    return {
        "names": names, "kappa": [k for _, k in order], "viol": viol,
        "below_floor": below, "max_viol": max(flat), "n_cells": len(flat),
        "n_over_alpha": sum(1 for v in flat if v > ALPHA),
    }


def panel_b_points(report: Mapping[str, Any]) -> Dict[str, Any]:
    kap = report["config"]["kappa_A"]
    a_star = float(report["config"]["a_star"])
    agg = aggregate(report, N_SLOPE)
    xs: List[float] = []
    ys: List[float] = []
    for (a, b), val in agg.items():
        if a == b:
            continue
        xs.append(abs(math.log(float(kap[a]) / float(kap[b]))))
        ys.append(abs(val["C3_acceptance_test"] - a_star))
    # CUNG uoc luong voi `cert/recalibrate_transfer.py:661` (`np.polyfit` bac 1,
    # CO he so tu do). Dung mot uoc luong khac se cho hinh va gate lech nhau.
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    intercept = my - slope * mx
    return {"x": xs, "y": ys, "slope": slope, "intercept": intercept,
            "n": n, "a_star": a_star}


def panel_c_bars(report: Mapping[str, Any]) -> Dict[str, float]:
    """sd tinh LAI: C3-R tren o(A,B) TREN SAN; B2-R tren 8 cell B (trung vi truc A)."""
    agg = aggregate(report, N_HEAT)
    above = [v for v in agg.values() if v["C3_acceptance_test"] >= FLOOR]

    def sd(xs: Sequence[float]) -> float:
        n = len(xs)
        mu = sum(xs) / n
        return math.sqrt(sum((x - mu) ** 2 for x in xs) / (n - 1))

    by_b: Dict[str, List[Dict[str, float]]] = defaultdict(list)
    for (_a, b), v in agg.items():
        by_b[b].append(v)

    def med(xs: Sequence[float]) -> float:
        s = sorted(xs)
        m = len(s) // 2
        return s[m] if len(s) % 2 else 0.5 * (s[m - 1] + s[m])

    return {
        "C3_sd_viol": sd([v["C3_viol_given_accept"] for v in above]),
        "C3_sd_acceptance": sd([v["C3_acceptance_test"] for v in above]),
        "B2_sd_acceptance": sd([med([x["B2_acceptance_test"] for x in v]) for v in by_b.values()]),
        "B2_sd_err": sd([med([x["B2_err_given_accept"] for x in v]) for v in by_b.values()]),
    }


def plot(report: Mapping[str, Any], out: str) -> Dict[str, Any]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    A = panel_a_matrix(report)
    B = panel_b_points(report)
    C = panel_c_bars(report)

    fig = plt.figure(figsize=(15.4, 5.0))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1.0, 0.85], wspace=0.36)

    # ---- (a) heatmap ------------------------------------------------------
    ax = fig.add_subplot(gs[0, 0])
    # Thang mau PHAI dat tam o `alpha`, khong dat tran o `alpha`. Neu dat tran,
    # moi o ~0.07 se roi vao vung DO/CAM cua `RdYlGn_r` va hinh se NOI NGUOC
    # voi so: tat ca deu DUOI nguong ma trong nhu sap vo.
    norm = matplotlib.colors.TwoSlopeNorm(vmin=0.0, vcenter=ALPHA, vmax=2.0 * ALPHA)
    im = ax.imshow(A["viol"], cmap="RdYlGn_r", norm=norm, aspect="auto")
    short = [c.replace("poisson@", "P").replace("h2@", "H") for c in A["names"]]
    ax.set_xticks(range(len(short)))
    ax.set_xticklabels(short, rotation=45, ha="right", fontsize=7.5)
    ax.set_yticks(range(len(short)))
    ax.set_yticklabels(short, fontsize=7.5)
    for i in range(len(short)):
        for j in range(len(short)):
            ax.text(j, i, "%.3f" % A["viol"][i][j], ha="center", va="center",
                    fontsize=6.2, color="#1f2937")
    for (i, j) in A["below_floor"]:
        ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                               edgecolor="#1d4ed8", linewidth=2.4))
    ax.set_xlabel(r"deploy on B  $\longrightarrow$ harder ($\kappa_B$ smaller)", fontsize=8.5)
    ax.set_ylabel(r"calibrate on A  $\longrightarrow$ harder", fontsize=8.5)
    ax.set_title("(a) $viol\\,|\\,accept$ after recalibration, $n=250$\n"
                 "%d/%d cells below $\\alpha=0.10$ (max %.4f); blue = acceptance < %.2f"
                 % (A["n_cells"] - A["n_over_alpha"], A["n_cells"], A["max_viol"], FLOOR),
                 fontsize=9)
    cb = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.02)
    cb.set_label(r"$viol\,|\,accept$   ($\alpha=0.10$ = centre of scale)", fontsize=7.5)
    cb.ax.axhline(ALPHA, color="black", linewidth=1.4)

    # ---- (b) slope --------------------------------------------------------
    ax = fig.add_subplot(gs[0, 1])
    ax.scatter(B["x"], B["y"], s=34, color="#0f766e", edgecolor="white",
               linewidth=0.6, zorder=3)
    lo, hi = 0.0, max(B["x"]) * 1.06
    ax.plot([lo, hi],
            [B["intercept"] + B["slope"] * lo, B["intercept"] + B["slope"] * hi],
            color="#b91c1c", linewidth=1.6, zorder=2,
            label="slope = %.4f  (signed [0.40, 0.62])" % B["slope"])
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xlabel(r"$|\log(\kappa_A/\kappa_B)|$   (how wrong the carried $\kappa$ is)",
                  fontsize=8.5)
    ax.set_ylabel(r"$|acceptance_B - a^*|$", fontsize=8.5)
    ax.set_title("(b) the price of a wrong $\\kappa$ is signed and predictable\n"
                 "$n=500$, %d off-diagonal cells" % B["n"], fontsize=9)
    ax.grid(alpha=0.22)
    ax.legend(loc="upper left", fontsize=8)

    # ---- (c) conservation -------------------------------------------------
    ax = fig.add_subplot(gs[0, 2])
    labels = ["C3-R\n$viol$", "C3-R\nacceptance", "B2-R\nacceptance", "B2-R\n$err|accept$"]
    vals = [C["C3_sd_viol"], C["C3_sd_acceptance"], C["B2_sd_acceptance"], C["B2_sd_err"]]
    cols = ["#15803d", "#94a3b8", "#15803d", "#94a3b8"]
    bars = ax.bar(range(4), vals, color=cols, edgecolor="#334155", linewidth=0.8)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v * 1.15, "%.4f" % v,
                ha="center", fontsize=8)
    ax.set_yscale("log")
    ax.set_xticks(range(4))
    ax.set_xticklabels(labels, fontsize=7.6)
    ax.set_ylabel("sd across regimes (log scale)", fontsize=8.5)
    ax.set_title("(c) neither procedure holds both\n"
                 "green = HELD    grey = LET FLOAT", fontsize=9)
    ax.grid(alpha=0.22, axis="y")

    fig.suptitle("Lesson 23.22 Task B-3 -- recalibration restores coverage; "
                 "what is lost is acceptance, not validity   "
                 "[aoi=measured_v7_uniform, sla=exogenous_g114_S-B, $a^*$=%.5f]"
                 % B["a_star"], fontsize=10.5)
    # KHONG dung `tight_layout`: colorbar cua panel (a) khong tuong thich va
    # matplotlib se canh bao + co the bo cuc sai. Dat le tay.
    fig.subplots_adjust(left=0.055, right=0.985, top=0.80, bottom=0.17)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return {"panel_a": A, "panel_b": B, "panel_c": C}


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default=INPUT)
    ap.add_argument("--out", default=OUTPUT)
    args = ap.parse_args(argv)
    with open(args.input, "r", encoding="utf-8") as fh:
        summary = plot(json.load(fh), args.out)
    print("figure -> %s" % args.out)
    print("  (a) %d/%d o duoi alpha, max %.4f, %d o duoi san acceptance"
          % (summary["panel_a"]["n_cells"] - summary["panel_a"]["n_over_alpha"],
             summary["panel_a"]["n_cells"], summary["panel_a"]["max_viol"],
             len(summary["panel_a"]["below_floor"])))
    print("  (b) do doc = %.4f tren %d o" % (summary["panel_b"]["slope"],
                                             summary["panel_b"]["n"]))
    print("  (c) %s" % {k: round(v, 5) for k, v in summary["panel_c"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
