#!/usr/bin/env python3
"""Phase 20R.7 -- mechanism maps for d(loss)/d(rho), d2(loss)/d(rho)2, d(cost)/d(rho).

Amendment 15 sec.3 asks for three maps. Amendment 16 fixes the estimator:
the truth table is a piecewise-linear interpolant, so a second difference with
``h`` smaller than the grid step measures knot placement, not physics. All
derivatives here are evaluated AT GRID NODES with ``h = stride * grid step``.

This module is deliberately separate from ``mechanism_map`` (singular), which
holds the closed-form K4 result. That result differentiates with respect to the
common-mode shift ``delta`` (a smooth polynomial) and is unaffected by this fix.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from measurements import decision_error_v2 as D
from measurements import mechanism_map as MM
from measurements import residual_spec as RS


# Amd 15 sec.6: cbr is out of scope for Lesson 20R.7.
MODES: Tuple[str, ...] = ("poisson", "h2")

# Amd 16 sec.4: significance threshold, signed before looking at any map.
SIG_K = 2.0

# Agresti-Coull z for the loss proportion interval.
Z_AC = 1.959963984540054

# Amd 16 sec.4: below this expected packet count the loss point is a counting
# artifact rather than a measurement.
LOW_COUNT_MIN = 10.0

DEFAULT_OUT = "results/SUPERSEDED/phase-20R/mechanism_maps.json"


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def load_curves(
    parquet_path: str = D.TRUTH_TABLE,
    modes: Sequence[str] = MODES,
) -> Dict[Tuple[str, float, int], Dict[str, np.ndarray]]:
    """Return one curve per ``(mode, bw, q)``, sorted by rho, with packet counts.

    ``TruthTable`` drops ``n_pkt``; the loss error bar needs it, so this reads
    the parquet directly. Values at nodes are identical to ``TruthTable`` by
    construction because ``np.interp`` is exact at its own knots -- see
    ``crosscheck_truth_table``.
    """
    table = pd.read_parquet(parquet_path)
    allowed = {str(m) for m in modes}
    out: Dict[Tuple[str, float, int], Dict[str, np.ndarray]] = {}
    for key, group in table.groupby(["mode", "bw", "q"], sort=True):
        mode = str(key[0])
        if mode not in allowed:
            continue
        group = group.sort_values("rho")
        out[(mode, float(key[1]), int(key[2]))] = {
            "rho": group["rho"].to_numpy(float),
            "qdelay_ms": group["delay_mean_ms"].to_numpy(float),
            "loss": group["loss"].to_numpy(float),
            "se_qdelay_ms": group["se_mean_ms"].to_numpy(float),
            "n_pkt": group["n_pkt"].to_numpy(float),
        }
    if not out:
        raise ValueError("no curve matched modes=%s in %s" % (list(modes), parquet_path))
    return out


def excluded_modes(parquet_path: str = D.TRUTH_TABLE, modes: Sequence[str] = MODES) -> List[str]:
    table = pd.read_parquet(parquet_path)
    return sorted(set(table["mode"].astype(str)) - {str(m) for m in modes})


def grid_step(rho: np.ndarray, tol: float = 1e-9) -> Optional[float]:
    """Return the uniform step, or ``None`` when the grid is not uniform."""
    steps = np.diff(np.asarray(rho, dtype=float))
    if steps.size == 0:
        return None
    if float(np.max(np.abs(steps - steps[0]))) > tol:
        return None
    return float(steps[0])


def d1_weights(h_minus: float, h_plus: float) -> Tuple[float, float, float]:
    """Three-point first-derivative weights on a possibly non-uniform grid.

    Reduces to ``(-1/2h, 0, +1/2h)`` when ``h_minus == h_plus == h``.
    """
    hm, hp = float(h_minus), float(h_plus)
    return (
        -hp / (hm * (hm + hp)),
        (hp - hm) / (hm * hp),
        hm / (hp * (hm + hp)),
    )


def d2_weights(h_minus: float, h_plus: float) -> Tuple[float, float, float]:
    """Three-point second-derivative weights on a possibly non-uniform grid.

    Reduces to ``(1/h2, -2/h2, 1/h2)`` when ``h_minus == h_plus == h``.
    """
    hm, hp = float(h_minus), float(h_plus)
    return (
        2.0 / (hm * (hm + hp)),
        -2.0 / (hm * hp),
        2.0 / (hp * (hm + hp)),
    )


def apply_weights(weights: Sequence[float], values: Sequence[float]) -> float:
    return float(sum(float(w) * float(v) for w, v in zip(weights, values)))


def propagate_se(weights: Sequence[float], se: Sequence[float]) -> float:
    """Independent-point error propagation for a weighted sum.

    Scope: the three rho points come from different measured cells, so they are
    treated as independent. Shared seeds would induce positive correlation and
    make this an upper bound on the true SE of the difference.
    """
    return float(math.sqrt(sum((float(w) * float(s)) ** 2 for w, s in zip(weights, se))))


def loss_uncertainty(p: float, n_pkt: float) -> Dict[str, float]:
    """Binomial uncertainty for a measured loss ratio.

    ``se_wald`` collapses to 0 when no packet was dropped, which would claim
    infinite precision. ``se_ac`` (Agresti-Coull) stays positive and is the
    value propagated into the derivative error bars.
    """
    p = float(p)
    n = float(n_pkt)
    if n <= 0.0:
        return {"x_drop": 0.0, "se_wald": float("nan"), "se_ac": float("nan"), "p_tilde": float("nan")}
    x = round(p * n)
    se_wald = math.sqrt(max(p * (1.0 - p), 0.0) / n)
    n_t = n + Z_AC * Z_AC
    p_t = (x + 0.5 * Z_AC * Z_AC) / n_t
    se_ac = math.sqrt(max(p_t * (1.0 - p_t), 0.0) / n_t)
    return {"x_drop": float(x), "se_wald": float(se_wald), "se_ac": float(se_ac), "p_tilde": float(p_t)}


def build_rows(
    curves: Mapping[Tuple[str, float, int], Mapping[str, np.ndarray]],
    stride: int = 1,
    w_loss_by_mode: Mapping[str, float] = MM.DEFAULT_W_LOSS,
) -> List[Dict[str, Any]]:
    """One row per interior node. ``h = stride * grid step``.

    Nodes closer than ``stride`` to either edge are skipped, so the truth table
    is never queried outside its measured domain and never clipped.
    """
    stride = int(stride)
    if stride < 1:
        raise ValueError("stride must be >= 1")

    rows: List[Dict[str, Any]] = []
    for (mode, bw, q), curve in sorted(curves.items()):
        rho = np.asarray(curve["rho"], dtype=float)
        qdelay = np.asarray(curve["qdelay_ms"], dtype=float)
        loss = np.asarray(curve["loss"], dtype=float)
        se_qdelay = np.asarray(curve["se_qdelay_ms"], dtype=float)
        n_pkt = np.asarray(curve["n_pkt"], dtype=float)
        w_loss = float(w_loss_by_mode[str(mode)])
        n = int(rho.size)

        unc = [loss_uncertainty(float(loss[i]), float(n_pkt[i])) for i in range(n)]
        se_loss = np.asarray([u["se_ac"] for u in unc], dtype=float)

        for k in range(stride, n - stride):
            lo, hi = k - stride, k + stride
            h_minus = float(rho[k] - rho[lo])
            h_plus = float(rho[hi] - rho[k])
            idx = (lo, k, hi)

            w1 = d1_weights(h_minus, h_plus)
            w2 = d2_weights(h_minus, h_plus)

            d1_loss = apply_weights(w1, [loss[i] for i in idx])
            d2_loss = apply_weights(w2, [loss[i] for i in idx])
            d1_delay = apply_weights(w1, [qdelay[i] for i in idx])
            d2_delay = apply_weights(w2, [qdelay[i] for i in idx])

            se_d1_loss = propagate_se(w1, [se_loss[i] for i in idx])
            se_d2_loss = propagate_se(w2, [se_loss[i] for i in idx])
            se_d1_delay = propagate_se(w1, [se_qdelay[i] for i in idx])
            se_d2_delay = propagate_se(w2, [se_qdelay[i] for i in idx])

            w_d1_loss = w_loss * d1_loss
            w_d2_loss = w_loss * d2_loss
            d1_cost = d1_delay + w_d1_loss
            d2_cost = d2_delay + w_d2_loss

            expected_drops = float(loss[k]) * float(n_pkt[k])
            rows.append(
                {
                    "mode": str(mode),
                    "bw": float(bw),
                    "q": int(q),
                    "rho": float(rho[k]),
                    "stride": stride,
                    "h_minus": h_minus,
                    "h_plus": h_plus,
                    "loss": float(loss[k]),
                    "qdelay_ms": float(qdelay[k]),
                    "n_pkt": float(n_pkt[k]),
                    "expected_drops": expected_drops,
                    "low_count": bool(expected_drops < LOW_COUNT_MIN),
                    "w_loss": w_loss,
                    "d1_loss": d1_loss,
                    "d2_loss": d2_loss,
                    "se_d1_loss": se_d1_loss,
                    "se_d2_loss": se_d2_loss,
                    "d1_delay_ms": d1_delay,
                    "d2_delay_ms": d2_delay,
                    "se_d1_delay_ms": se_d1_delay,
                    "se_d2_delay_ms": se_d2_delay,
                    "w_d1_loss_ms": w_d1_loss,
                    "w_d2_loss_ms": w_d2_loss,
                    "d1_cost_ms": d1_cost,
                    "d2_cost_ms": d2_cost,
                    "ratio_channel_d1": (
                        abs(w_d1_loss) / abs(d1_delay) if abs(d1_delay) > 0.0 else float("inf")
                    ),
                    "ratio_channel_d2": (
                        abs(w_d2_loss) / abs(d2_delay) if abs(d2_delay) > 0.0 else float("inf")
                    ),
                    "significant_d2_loss": bool(abs(d2_loss) > SIG_K * se_d2_loss),
                }
            )
    return rows


def _argmax_row(rows: Sequence[Mapping[str, Any]], key: str) -> Optional[Mapping[str, Any]]:
    if not rows:
        return None
    return max(rows, key=lambda r: abs(float(r[key])))


def curvature_argmax(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Per ``(mode, bw, q)``: argmax of ``|d2_loss|``, raw and significance-gated."""
    out: List[Dict[str, Any]] = []
    keys = sorted({(str(r["mode"]), float(r["bw"]), int(r["q"])) for r in rows})
    for mode, bw, q in keys:
        cell = [r for r in rows if str(r["mode"]) == mode and float(r["bw"]) == bw and int(r["q"]) == q]
        gated = [r for r in cell if bool(r["significant_d2_loss"])]
        raw = _argmax_row(cell, "d2_loss")
        sig = _argmax_row(gated, "d2_loss")
        out.append(
            {
                "mode": mode,
                "bw": bw,
                "q": q,
                "n_nodes": len(cell),
                "n_significant": len(gated),
                "argmax_rho_raw": None if raw is None else float(raw["rho"]),
                "argmax_d2_loss_raw": None if raw is None else float(raw["d2_loss"]),
                "argmax_rho_significant": None if sig is None else float(sig["rho"]),
                "argmax_d2_loss_significant": None if sig is None else float(sig["d2_loss"]),
                "publishable": sig is not None,
            }
        )
    return out


def channel_crossing(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Per cell: the rho where ``|w_loss*d1_loss| / |d1_delay|`` reaches 1.

    Below it the cost gradient is delay-dominated, above it loss-dominated.
    Linear interpolation between the bracketing nodes; the grid step is the
    resolution, so the value is reported with that step attached.
    """
    out: List[Dict[str, Any]] = []
    keys = sorted({(str(r["mode"]), float(r["bw"]), int(r["q"])) for r in rows})
    for mode, bw, q in keys:
        cell = sorted(
            [r for r in rows if str(r["mode"]) == mode and float(r["bw"]) == bw and int(r["q"]) == q],
            key=lambda r: float(r["rho"]),
        )
        crossings: List[float] = []
        for a, b in zip(cell, cell[1:]):
            ra, rb = float(a["ratio_channel_d1"]), float(b["ratio_channel_d1"])
            if not math.isfinite(ra) or not math.isfinite(rb):
                continue
            if (ra - 1.0) <= 0.0 <= (rb - 1.0) and rb != ra:
                t = (1.0 - ra) / (rb - ra)
                crossings.append(float(a["rho"]) + t * (float(b["rho"]) - float(a["rho"])))
        out.append(
            {
                "mode": mode,
                "bw": bw,
                "q": q,
                "rho_channel_crossing": crossings[-1] if crossings else None,
                "rho_channel_crossing_first": crossings[0] if crossings else None,
                "n_upward_crossings": len(crossings),
                "resolution_rho": None if len(cell) < 2 else float(cell[1]["rho"] - cell[0]["rho"]),
                "max_ratio_channel_d1": max(
                    (float(r["ratio_channel_d1"]) for r in cell if math.isfinite(float(r["ratio_channel_d1"]))),
                    default=None,
                ),
            }
        )
    return out


def argmax_robustness(
    summary_a: Sequence[Mapping[str, Any]],
    summary_b: Sequence[Mapping[str, Any]],
    step: float,
    max_grid_steps: float = 1.0,
) -> Dict[str, Any]:
    """Amd 16 sec.5: argmax must not move more than one grid step across strides."""
    index_b = {(str(r["mode"]), float(r["bw"]), int(r["q"])): r for r in summary_b}
    rows: List[Dict[str, Any]] = []
    for a in summary_a:
        key = (str(a["mode"]), float(a["bw"]), int(a["q"]))
        b = index_b.get(key)
        ra = a.get("argmax_rho_significant")
        rb = None if b is None else b.get("argmax_rho_significant")
        if ra is None or rb is None:
            rows.append({"mode": key[0], "bw": key[1], "q": key[2], "stable": None, "reason": "no significant node"})
            continue
        shift = abs(float(ra) - float(rb))
        rows.append(
            {
                "mode": key[0],
                "bw": key[1],
                "q": key[2],
                "argmax_rho_stride_a": float(ra),
                "argmax_rho_stride_b": float(rb),
                "shift_rho": shift,
                "shift_grid_steps": shift / float(step),
                "stable": bool(shift <= max_grid_steps * float(step) + 1e-12),
            }
        )
    decided = [r for r in rows if r.get("stable") is not None]
    # The verdict is reported per family as well as pooled: w_loss and the loss
    # noise floor differ by family, so a pooled failure can hide a family that
    # is perfectly resolved. This split is structural, not a data-driven subgroup.
    by_mode: Dict[str, Any] = {}
    for mode in sorted({str(r["mode"]) for r in rows}):
        cell = [r for r in decided if str(r["mode"]) == mode]
        by_mode[mode] = {
            "n_decided": len(cell),
            "n_stable": sum(1 for r in cell if r["stable"]),
            "argmax_publishable": bool(cell) and all(r["stable"] for r in cell),
        }
    return {
        "grid_step": float(step),
        "max_grid_steps": float(max_grid_steps),
        "n_cells": len(rows),
        "n_decided": len(decided),
        "n_stable": sum(1 for r in decided if r["stable"]),
        "argmax_publishable": bool(decided) and all(r["stable"] for r in decided),
        "by_mode": by_mode,
        "cells": rows,
    }


def crosscheck_truth_table(
    curves: Mapping[Tuple[str, float, int], Mapping[str, np.ndarray]],
    tol: float = 1e-12,
) -> Dict[str, Any]:
    """Node values here must equal ``TruthTable`` values, or the maps drift."""
    tt = D.TruthTable()
    worst = 0.0
    n = 0
    for (mode, bw, q), curve in curves.items():
        rho = np.asarray(curve["rho"], dtype=float)
        delay, loss = tt.queue_delay_loss(mode, bw, q, rho)
        worst = max(
            worst,
            float(np.max(np.abs(delay - curve["qdelay_ms"]))),
            float(np.max(np.abs(loss - curve["loss"]))),
        )
        n += int(rho.size)
    if worst > tol:
        raise ValueError("node values disagree with TruthTable: max abs diff %g" % worst)
    return {"n_nodes_checked": n, "max_abs_diff": worst, "tol": tol}


def grid_report(curves: Mapping[Tuple[str, float, int], Mapping[str, np.ndarray]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for (mode, bw, q), curve in sorted(curves.items()):
        rho = np.asarray(curve["rho"], dtype=float)
        step = grid_step(rho)
        out.append(
            {
                "mode": mode,
                "bw": bw,
                "q": q,
                "n_nodes": int(rho.size),
                "rho_min": float(rho.min()),
                "rho_max": float(rho.max()),
                "uniform_step": step,
                "steps_seen": sorted({round(float(s), 6) for s in np.diff(rho)}),
            }
        )
    return out


def common_grid_step(curves: Mapping[Tuple[str, float, int], Mapping[str, np.ndarray]]) -> float:
    steps = {grid_step(np.asarray(c["rho"], dtype=float)) for c in curves.values()}
    if None in steps or len(steps) != 1:
        raise ValueError("grid is not uniform across curves: %s" % sorted(str(s) for s in steps))
    return float(next(iter(steps)))


def build_report(
    parquet_path: str = D.TRUTH_TABLE,
    modes: Sequence[str] = MODES,
    stride: int = 1,
    robust_stride: int = 2,
) -> Dict[str, Any]:
    curves = load_curves(parquet_path, modes=modes)
    grids = grid_report(curves)
    step = common_grid_step(curves)
    crosscheck = crosscheck_truth_table(curves)

    rows = build_rows(curves, stride=stride)
    rows_robust = build_rows(curves, stride=robust_stride)
    summary = curvature_argmax(rows)
    summary_robust = curvature_argmax(rows_robust)

    return {
        "schema": "phase20r7/mechanism_maps/v1",
        "phase": "20R.7",
        "amendment": "00q-amendment-16",
        "truth_table": parquet_path,
        "modes": list(modes),
        "modes_excluded": excluded_modes(parquet_path, modes),
        "estimator": {
            "evaluation": "grid nodes only",
            "h_primary": stride * step,
            "h_robustness": robust_stride * step,
            "stride_primary": int(stride),
            "stride_robustness": int(robust_stride),
            "stencil": "three-point, non-uniform-capable",
            "loss_se": "Agresti-Coull, z=%.6f" % Z_AC,
            "delay_se": "se_mean_ms column (batch)",
            "sig_k": SIG_K,
            "low_count_min": LOW_COUNT_MIN,
        },
        "grid": grids,
        "grid_step": step,
        "truth_table_crosscheck": crosscheck,
        "curvature_argmax": summary,
        "curvature_argmax_robustness_stride": summary_robust,
        "argmax_robustness": argmax_robustness(summary, summary_robust, step=step),
        "channel_crossing": channel_crossing(rows),
        "rows": rows,
        **RS.git_commit(),
    }


def print_summary(report: Mapping[str, Any]) -> None:
    step = float(report["grid_step"])
    est = report["estimator"]
    print("grid step = %.4f   h_primary = %.4f   h_robust = %.4f" % (step, est["h_primary"], est["h_robustness"]))
    print("modes excluded: %s" % (report["modes_excluded"] or "none"))
    print(
        "truth-table crosscheck: %d nodes, max abs diff %.3g"
        % (report["truth_table_crosscheck"]["n_nodes_checked"], report["truth_table_crosscheck"]["max_abs_diff"])
    )
    print()

    print("=== channel crossing |w_loss*d1_loss| / |d1_delay| = 1 ===")
    for row in report["channel_crossing"]:
        cross = row["rho_channel_crossing"]
        print(
            "  %-8s bw=%.1f q=%-3d  crossing=%s  max_ratio=%.2f"
            % (
                row["mode"],
                row["bw"],
                row["q"],
                "none" if cross is None else "%.4f" % cross,
                float(row["max_ratio_channel_d1"] or float("nan")),
            )
        )
    print()

    print("=== argmax |d2(loss)/d(rho)2| ===")
    for row in report["curvature_argmax"]:
        print(
            "  %-8s bw=%.1f q=%-3d  nodes=%2d sig=%2d  argmax_sig=%s  d2=%s"
            % (
                row["mode"],
                row["bw"],
                row["q"],
                row["n_nodes"],
                row["n_significant"],
                "none" if row["argmax_rho_significant"] is None else "%.3f" % row["argmax_rho_significant"],
                "n/a" if row["argmax_d2_loss_significant"] is None else "%.4f" % row["argmax_d2_loss_significant"],
            )
        )
    rob = report["argmax_robustness"]
    print()
    print(
        "argmax robustness pooled: %d/%d cells stable, publishable=%s"
        % (rob["n_stable"], rob["n_decided"], rob["argmax_publishable"])
    )
    for mode, row in sorted(rob["by_mode"].items()):
        print("  %-8s %d/%d stable, publishable=%s" % (mode, row["n_stable"], row["n_decided"], row["argmax_publishable"]))


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--truth-table", default=D.TRUTH_TABLE)
    ap.add_argument("--modes", default=",".join(MODES))
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--robust-stride", type=int, default=2)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    modes = tuple(part.strip() for part in args.modes.split(",") if part.strip())
    unknown = sorted(set(modes) - set(MM.DEFAULT_W_LOSS))
    if unknown:
        raise ValueError("no calibrated w_loss for modes: %s" % unknown)

    report = build_report(
        parquet_path=args.truth_table,
        modes=modes,
        stride=int(args.stride),
        robust_stride=int(args.robust_stride),
    )
    print_summary(report)
    ensure_parent(args.out)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
