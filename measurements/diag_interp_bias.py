#!/usr/bin/env python3
"""Phase 20R.6 -- what the truth-table interpolation actually costs, and where
each interpolated point comes from.

Two separate quantities kept apart on purpose:

``bias_curv``   estimator bias of ``np.interp`` on the REAL grid: the gap between
                the piecewise-linear reading the twin uses and a curvature-aware
                (monotone cubic) reading of the same measured points. This is the
                honest interpolation error.
``loo_h``       leave-out sensitivity: re-interpolate after thinning the grid to a
                coarser spacing. This answers "what if the grid were k times
                sparser" and is NOT the bias of the estimator in use.

Also stratifies each target by the ``source`` of its two bracketing grid points,
because the truth table merges a Phase L campaign with a later 20R campaign.

No scipy: the monotone cubic is Fritsch-Carlson, matching the repo convention of
keeping analysis dependencies to numpy/pandas.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from measurements import decision_error_v2 as D
from mininet.topology_tandem import TANDEM_LINKS
from twin import cost_v2 as C
from twin import topology_v7 as T7


OUT = "results/phase-20R/diag_interp_bias.json"
RHO_BAR = 0.925
MODES = ("poisson", "h2")
LOO_SPACING = 0.10


def pchip_slopes(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Fritsch-Carlson monotone cubic slopes (shape preserving, no overshoot)."""
    n = len(x)
    if n < 3:
        return np.gradient(y, x)
    h = np.diff(x)
    delta = np.diff(y) / h
    d = np.zeros(n, dtype=float)
    for k in range(1, n - 1):
        if delta[k - 1] * delta[k] > 0.0:
            w1 = 2.0 * h[k] + h[k - 1]
            w2 = h[k] + 2.0 * h[k - 1]
            d[k] = (w1 + w2) / (w1 / delta[k - 1] + w2 / delta[k])
    d[0] = _edge_slope(h[0], h[1], delta[0], delta[1])
    d[-1] = _edge_slope(h[-1], h[-2], delta[-1], delta[-2])
    return d


def _edge_slope(h0: float, h1: float, d0: float, d1: float) -> float:
    slope = ((2.0 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
    if slope * d0 <= 0.0:
        return 0.0
    if d0 * d1 <= 0.0 and abs(slope) > abs(3.0 * d0):
        return 3.0 * d0
    return float(slope)


def pchip_eval(x: np.ndarray, y: np.ndarray, xq: float) -> float:
    """Evaluate the monotone cubic Hermite interpolant at a single point."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    xq = float(np.clip(xq, x[0], x[-1]))
    d = pchip_slopes(x, y)
    k = int(np.clip(np.searchsorted(x, xq) - 1, 0, len(x) - 2))
    h = x[k + 1] - x[k]
    t = (xq - x[k]) / h
    h00 = 2 * t ** 3 - 3 * t ** 2 + 1
    h10 = t ** 3 - 2 * t ** 2 + t
    h01 = -2 * t ** 3 + 3 * t ** 2
    h11 = t ** 3 - t ** 2
    return float(h00 * y[k] + h10 * h * d[k] + h01 * y[k + 1] + h11 * h * d[k + 1])


def leave_out_linear(x: np.ndarray, y: np.ndarray, xq: float, spacing: float) -> Dict[str, Any]:
    """Linear interpolation after thinning the grid to ~``spacing``.

    A sensitivity probe, not a bias estimate: it reports how much the reading
    would move if the campaign had sampled rho more coarsely.
    """
    gap = float(np.median(np.diff(x)))
    stride = max(int(round(float(spacing) / gap)), 1)
    best: Optional[Dict[str, Any]] = None
    for offset in range(stride):
        idx = np.arange(offset, len(x), stride)
        if len(idx) < 2:
            continue
        xs, ys = x[idx], y[idx]
        if not (xs[0] <= xq <= xs[-1]):
            continue
        lo = int(np.searchsorted(xs, xq) - 1)
        width = float(xs[min(lo + 1, len(xs) - 1)] - xs[max(lo, 0)])
        cand = {
            "value": float(np.interp(xq, xs, ys)),
            "bracket": [float(xs[max(lo, 0)]), float(xs[min(lo + 1, len(xs) - 1)])],
            "bracket_width": width,
            "n_points": int(len(xs)),
        }
        if best is None or abs(width - float(spacing)) < abs(best["bracket_width"] - float(spacing)):
            best = cand
    return best or {"value": float("nan"), "bracket": None, "bracket_width": float("nan"), "n_points": 0}


def grid_report(truth_table: str = D.TRUTH_TABLE) -> List[Dict[str, Any]]:
    table = pd.read_parquet(truth_table)
    rows: List[Dict[str, Any]] = []
    for key, group in table.groupby(["mode", "bw", "q"], sort=True):
        rho = np.sort(group["rho"].unique())
        gaps = np.diff(rho)
        rows.append(
            {
                "mode": str(key[0]),
                "bw": float(key[1]),
                "q": int(key[2]),
                "n_points": int(len(rho)),
                "rho_min": float(rho.min()),
                "rho_max": float(rho.max()),
                "gap_min": float(gaps.min()),
                "gap_max": float(gaps.max()),
                "uniform": bool(np.allclose(gaps, gaps[0])),
            }
        )
    return rows


def _curve(table: pd.DataFrame, mode: str, t7_link: str) -> pd.DataFrame:
    bw, _base, q = T7.LINKS[t7_link]
    sel = table[(table["mode"] == mode) & (table["bw"] == float(bw)) & (table["q"] == int(q))]
    return sel.sort_values("rho")


def link_report(
    truth_table: str = D.TRUTH_TABLE,
    rho_bar: float = RHO_BAR,
    modes: Sequence[str] = MODES,
    loo_spacing: float = LOO_SPACING,
) -> List[Dict[str, Any]]:
    table = pd.read_parquet(truth_table)
    rows: List[Dict[str, Any]] = []
    for mode in modes:
        for link, t7_link, _bw, _q, _base in TANDEM_LINKS:
            rho = float(C.rho_vector(float(rho_bar))[t7_link])
            curve = _curve(table, mode, t7_link)
            x = curve["rho"].to_numpy(float)
            y = curve["loss"].to_numpy(float)
            src = curve["source"].astype(str).to_numpy()
            lin = float(np.interp(rho, x, y))
            cur = pchip_eval(x, y, rho)
            k = int(np.clip(np.searchsorted(x, rho) - 1, 0, len(x) - 2))
            loo = leave_out_linear(x, y, rho, loo_spacing)
            bracket_sources = [str(src[k]), str(src[k + 1])]
            rows.append(
                {
                    "mode": str(mode),
                    "link": link,
                    "topology_v7_link": t7_link,
                    "rho": rho,
                    "grid_gap": float(np.median(np.diff(x))),
                    "loss_linear": lin,
                    "loss_curvature": cur,
                    "bias_curv": float(cur - lin),
                    "bracket_rho": [float(x[k]), float(x[k + 1])],
                    "bracket_source": bracket_sources,
                    "provenance": "pure_%s" % bracket_sources[0]
                    if bracket_sources[0] == bracket_sources[1]
                    else "mixed",
                    "loo_spacing": float(loo_spacing),
                    "loo_value": loo["value"],
                    "loo_bracket": loo["bracket"],
                    "loo_bracket_width": loo["bracket_width"],
                    "loo_shift": float(loo["value"] - lin),
                }
            )
    return rows


def path_report(link_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Compose link bias into path bias through 1 - prod(1 - l_i)."""
    out: List[Dict[str, Any]] = []
    frame = pd.DataFrame(list(link_rows))
    for mode, group in frame.groupby("mode", sort=True):
        lin = group["loss_linear"].to_numpy(float)
        cur = group["loss_curvature"].to_numpy(float)
        loo = group["loo_value"].to_numpy(float)
        path_lin = 1.0 - float(np.prod(1.0 - lin))
        path_cur = 1.0 - float(np.prod(1.0 - cur))
        path_loo = 1.0 - float(np.prod(1.0 - loo))
        partial = np.array([float(np.prod(np.delete(1.0 - lin, i))) for i in range(len(lin))])
        out.append(
            {
                "mode": str(mode),
                "path_loss_linear": path_lin,
                "path_loss_curvature": path_cur,
                "bias_path": float(path_cur - path_lin),
                "bias_path_via_partials": float(np.sum(partial * (cur - lin))),
                "path_loss_loo": path_loo,
                "loo_shift_path": float(path_loo - path_lin),
            }
        )
    return out


def attach_deficit(path_rows: List[Dict[str, Any]], check_report: str) -> None:
    """Express each bias as a share of the measured A' - A path deficit."""
    if not os.path.exists(check_report):
        return
    with open(check_report, "r", encoding="utf-8") as f:
        checks = json.load(f).get("checks", [])
    deficit = {
        str(row["mode"]): float(row["mean_ms"])
        for row in checks
        if row.get("contrast") == "Aprime_minus_A_path_loss"
    }
    for row in path_rows:
        obs = deficit.get(row["mode"])
        row["deficit_observed"] = obs
        row["bias_share_of_deficit"] = (
            None if not obs else float(row["bias_path"] / obs)
        )
        row["loo_share_of_deficit"] = (
            None if not obs else float(row["loo_shift_path"] / obs)
        )


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--truth-table", default=D.TRUTH_TABLE)
    ap.add_argument("--rho-bar", type=float, default=RHO_BAR)
    ap.add_argument("--loo-spacing", type=float, default=LOO_SPACING)
    ap.add_argument("--check-report", default="results/phase-20R/additivity_check_budgetfix_bg.json")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)

    grid = grid_report(args.truth_table)
    links = link_report(args.truth_table, args.rho_bar, loo_spacing=args.loo_spacing)
    paths = path_report(links)
    attach_deficit(paths, args.check_report)

    print("=== GRID cua truth table ===")
    print("%-8s %4s %3s %4s  %-14s %8s %8s  %s" % ("mode", "bw", "q", "n", "rho range", "gap_min", "gap_max", "deu?"))
    for row in grid:
        print(
            "%-8s %4.1f %3d %4d  %.2f .. %.2f  %8.4f %8.4f  %s"
            % (row["mode"], row["bw"], row["q"], row["n_points"], row["rho_min"], row["rho_max"],
               row["gap_min"], row["gap_max"], "yes" if row["uniform"] else "NO")
        )

    print()
    print("=== BIAS NOI SUY per-link (loss) ===")
    print(
        "%-8s %-4s %7s %10s %10s %11s | %-15s %-22s | %11s"
        % ("mode", "link", "rho", "linear", "curvature", "bias_curv", "bracket", "source", "loo_shift")
    )
    for row in links:
        print(
            "%-8s %-4s %7.4f %10.6f %10.6f %+11.6f | %-15s %-22s | %+11.6f"
            % (
                row["mode"], row["link"], row["rho"], row["loss_linear"], row["loss_curvature"],
                row["bias_curv"],
                "%.2f-%.2f" % (row["bracket_rho"][0], row["bracket_rho"][1]),
                "%s+%s" % (row["bracket_source"][0], row["bracket_source"][1]),
                row["loo_shift"],
            )
        )

    print()
    print("=== BIAS NOI SUY o muc PATH (dai luong di vao gate) ===")
    print("%-8s %14s %14s %12s %12s | %12s %10s" % (
        "mode", "path_linear", "path_curv", "bias_path", "loo_shift", "deficit_obs", "bias/def"))
    for row in paths:
        share = row.get("bias_share_of_deficit")
        print(
            "%-8s %14.6f %14.6f %+12.6f %+12.6f | %12s %10s"
            % (
                row["mode"], row["path_loss_linear"], row["path_loss_curvature"],
                row["bias_path"], row["loo_shift_path"],
                "n/a" if row.get("deficit_observed") is None else "%.6f" % row["deficit_observed"],
                "n/a" if share is None else "%.1f%%" % (100.0 * share),
            )
        )

    report = {
        "phase": "20R.6",
        "kind": "interpolation_bias_and_provenance",
        "rho_bar": float(args.rho_bar),
        "loo_spacing": float(args.loo_spacing),
        "note": "bias_curv = estimator bias on the real grid; loo_* = sensitivity to a coarser grid, NOT a bias",
        "grid": grid,
        "links": links,
        "paths": paths,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True, default=str)
        f.write("\n")
    print()
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
