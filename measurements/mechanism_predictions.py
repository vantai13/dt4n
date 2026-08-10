#!/usr/bin/env python3
"""Phase 20R.7 -- adjudicate the three predictions signed in Amendment 15 sec.7.

    P1  Spearman(median r(s), err) < 0, p < 0.05
    P2  argmax_rho |d2(loss)/d(rho)2| coincides with argmax_rho err,
        within one grid step, in at least three non-cbr configurations
    P3  |w_loss * d2(loss)/d(rho)2| > |d2(delay)/d(rho)2| at substantively
        relevant cells

P1 is read from ``margin_radius.json``. P3 is read from ``mechanism_maps.json``.

P2 needs work that neither artifact does, because the two argmaxes live on
different axes. ``err`` is indexed by ``rho_bar``; the link curvature map is
indexed by the per-link ``rho = rho_bar + LINK_OFFSET[link]``. A single link
curve at ``(bw, q)`` is shared by up to five links with five different offsets,
so its argmax has no single ``rho_bar`` preimage. Amendment 18 therefore puts
the curvature on the ``rho_bar`` axis at the PATH level, where the composition
is a scalar function of ``rho_bar`` and the comparison is well posed.

Why ``h = grid step`` stays legal off-node: for a piecewise-linear f with knot
spacing h, evaluating the second difference at ``x = knot_k + t*h`` gives
``(1-t)*D_k + t*D_{k+1}``, the linear interpolation of the node-level second
differences. It never sees sub-grid structure, so Amendment 16 is respected.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from measurements import decision_error_v2 as D
from measurements import margin_radius as MR
from measurements import residual_spec as RS
from twin import cost_v2 as C
from twin import topology_v7 as T7


MODES: Tuple[str, ...] = ("poisson", "h2")
MAPS = "results/phase-20R/mechanism_maps.json"
RADIUS = "results/phase-20R/margin_radius.json"
DEFAULT_OUT = "results/phase-20R/mechanism_predictions.json"
MAX_GRID_STEPS = 1.0


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def feasible_rho_bar(tt: D.TruthTable, mode: str, h: float) -> Tuple[float, float]:
    """Widest ``rho_bar`` window where every link stays inside its measured domain.

    ``rho_link = rho_bar + LINK_OFFSET[link]``, and the stencil reaches +-h, so
    the window shrinks by h on each side. Outside it the truth table would clip
    and the curvature would be an artifact of the clip, not of the queue.
    """
    lo = -math.inf
    hi = math.inf
    for link in T7.LINK_NAMES:
        bw, _base, q = T7.LINKS[link]
        grid = tt.curves[(str(mode), float(bw), int(q))][0]
        lo = max(lo, float(grid.min()) - C.LINK_OFFSET[link] + float(h))
        hi = min(hi, float(grid.max()) - C.LINK_OFFSET[link] - float(h))
    return float(lo), float(hi)


def path_loss_at(tt: D.TruthTable, mode: str, path: str, rho_bar: np.ndarray) -> np.ndarray:
    rb = np.asarray(rho_bar, dtype=float)
    keep = np.ones_like(rb)
    for link in T7.PATHS[str(path)]:
        _delay, loss = tt.delay_loss(str(mode), str(link), rb + C.LINK_OFFSET[link])
        keep *= 1.0 - loss
    return 1.0 - keep


def path_curvature_map(
    tt: D.TruthTable,
    mode: str,
    h: float,
    step: float,
) -> List[Dict[str, Any]]:
    lo, hi = feasible_rho_bar(tt, mode, h)
    grid = np.round(np.arange(math.ceil(lo / step) * step, hi + 1e-12, step), 6)
    rows: List[Dict[str, Any]] = []
    for path in T7.PATH_NAMES:
        f0 = path_loss_at(tt, mode, path, grid)
        fp = path_loss_at(tt, mode, path, grid + h)
        fm = path_loss_at(tt, mode, path, grid - h)
        d1 = (fp - fm) / (2.0 * h)
        d2 = (fp - 2.0 * f0 + fm) / (h * h)
        for i, rb in enumerate(grid):
            rows.append(
                {
                    "mode": str(mode),
                    "path": str(path),
                    "rho_bar": float(rb),
                    "loss_path": float(f0[i]),
                    "d1_loss_path": float(d1[i]),
                    "d2_loss_path": float(d2[i]),
                }
            )
    return rows


def prediction_1(radius_path: str = RADIUS) -> Dict[str, Any]:
    report = load_json(radius_path)
    h1 = report["h1_bound"]
    return {
        "statement": "Spearman(median r(s), err) < 0 with p < alpha",
        "source": radius_path,
        "radius_key": h1["radius_key"],
        "pooled": h1["pooled"],
        "by_mode": h1["by_mode"],
        "supported": bool(h1["supported"]),
        "note": h1["dependence_caveat"],
    }


def prediction_2(
    err: Mapping[Tuple[str, float], Mapping[str, float]],
    modes: Sequence[str] = MODES,
    h: float = 0.02,
    step: float = 0.02,
    max_grid_steps: float = MAX_GRID_STEPS,
) -> Dict[str, Any]:
    tt = D.TruthTable()
    rows: List[Dict[str, Any]] = []
    per_mode: Dict[str, Any] = {}

    for mode in modes:
        measured = sorted(rb for m, rb in err if m == str(mode))
        if len(measured) < 3:
            per_mode[str(mode)] = {"testable": False, "reason": "fewer than 3 measured rho_bar"}
            continue
        errs = [float(err[(str(mode), rb)]["err_total"]) for rb in measured]
        i_max = int(np.argmax(errs))
        rb_err = float(measured[i_max])
        # An argmax on the boundary of the measured rho_bar list is not
        # identified: the true peak may sit outside the measured window.
        identified = 0 < i_max < len(measured) - 1

        curve = path_curvature_map(tt, str(mode), h=h, step=step)
        paths: List[Dict[str, Any]] = []
        for path in T7.PATH_NAMES:
            cell = [r for r in curve if r["path"] == path]
            best = max(cell, key=lambda r: abs(float(r["d2_loss_path"])))
            gap = abs(float(best["rho_bar"]) - rb_err)
            paths.append(
                {
                    "path": path,
                    "argmax_rho_bar_curvature": float(best["rho_bar"]),
                    "d2_loss_path": float(best["d2_loss_path"]),
                    "argmax_rho_bar_err": rb_err,
                    "gap_rho_bar": gap,
                    "gap_grid_steps": gap / float(step),
                    "aligned": bool(gap <= max_grid_steps * float(step) + 1e-12),
                }
            )
        rows.extend(paths)
        per_mode[str(mode)] = {
            "testable": bool(identified),
            "argmax_rho_bar_err": rb_err,
            "err_at_argmax": float(errs[i_max]),
            "measured_rho_bar": [float(r) for r in measured],
            "argmax_identified": bool(identified),
            "reason": None if identified else "err argmax sits on the edge of the measured rho_bar window",
            "n_paths_aligned": sum(1 for p in paths if p["aligned"]),
            "n_paths": len(paths),
            "paths": paths,
        }

    testable = [m for m, row in per_mode.items() if row.get("testable")]
    n_aligned = sum(per_mode[m]["n_paths_aligned"] for m in testable)
    return {
        "statement": (
            "argmax_rho |d2(loss)/d(rho)2| coincides with argmax_rho err within one grid "
            "step, in at least three non-cbr configurations"
        ),
        "axis_fix": "curvature evaluated at PATH level on the rho_bar axis (Amendment 18)",
        "h": float(h),
        "grid_step": float(step),
        "max_grid_steps": float(max_grid_steps),
        "by_mode": per_mode,
        "n_testable_modes": len(testable),
        "n_configurations_aligned": int(n_aligned),
        "n_configurations_required": 3,
        "supported": bool(n_aligned >= 3),
    }


def prediction_3(maps_path: str = MAPS) -> Dict[str, Any]:
    report = load_json(maps_path)
    rows = [r for r in report["rows"] if bool(r["significant_d2_loss"])]
    detail = [
        {
            "mode": r["mode"],
            "bw": r["bw"],
            "q": r["q"],
            "rho": r["rho"],
            "abs_w_d2_loss_ms": abs(float(r["w_d2_loss_ms"])),
            "abs_d2_delay_ms": abs(float(r["d2_delay_ms"])),
            "ratio": abs(float(r["ratio_channel_d2"])),
            "loss_dominates": bool(abs(float(r["w_d2_loss_ms"])) > abs(float(r["d2_delay_ms"]))),
        }
        for r in rows
    ]
    n_ok = sum(1 for r in detail if r["loss_dominates"])
    ratios = [r["ratio"] for r in detail if math.isfinite(r["ratio"])]
    return {
        "statement": "|w_loss * d2(loss)/d(rho)2| > |d2(delay)/d(rho)2| at substantively relevant cells",
        "source": maps_path,
        "relevance_rule": "significant_d2_loss, i.e. |d2 loss| > %.1f * SE (Amendment 16 sec.4)"
        % float(report["estimator"]["sig_k"]),
        "n_cells": len(detail),
        "n_loss_dominates": int(n_ok),
        "ratio_min": min(ratios) if ratios else None,
        "ratio_max": max(ratios) if ratios else None,
        "ratio_median": float(np.median(ratios)) if ratios else None,
        "supported": bool(detail) and n_ok == len(detail),
        "cells": detail,
    }


def build_report(
    maps_path: str = MAPS,
    radius_path: str = RADIUS,
    modes: Sequence[str] = MODES,
    z: float = MR.Z_OPERATING,
    h: float = 0.02,
    step: float = 0.02,
) -> Dict[str, Any]:
    err = MR.load_err(z=z)
    p1 = prediction_1(radius_path)
    p2 = prediction_2(err, modes=modes, h=h, step=step)
    p3 = prediction_3(maps_path)
    return {
        "schema": "phase20r7/mechanism_predictions/v1",
        "phase": "20R.7",
        "amendments": ["00p-amendment-15", "00q-amendment-16", "00r-amendment-17", "00s-amendment-18"],
        "z": float(z),
        "P1_margin_radius": p1,
        "P2_curvature_argmax_alignment": p2,
        "P3_channel_dominance": p3,
        "summary": {
            "P1": "supported" if p1["supported"] else "not supported",
            "P2": "supported" if p2["supported"] else "not supported",
            "P3": "supported" if p3["supported"] else "not supported",
        },
        **RS.git_commit(),
    }


def print_summary(report: Mapping[str, Any]) -> None:
    p1 = report["P1_margin_radius"]
    p2 = report["P2_curvature_argmax_alignment"]
    p3 = report["P3_channel_dominance"]

    print("=== P1  margin radius vs err ===")
    print(
        "  pooled rho=%+.6f  p=%.6f  supported=%s"
        % (p1["pooled"]["rho"], p1["pooled"]["p_one_sided_negative"], p1["supported"])
    )

    print()
    print("=== P2  curvature argmax vs err argmax (path level, rho_bar axis) ===")
    for mode, row in sorted(p2["by_mode"].items()):
        if not row.get("testable"):
            print("  %-8s NOT TESTABLE: %s" % (mode, row["reason"]))
            continue
        print("  %-8s err argmax at rho_bar=%.3f (err=%.4f)" % (mode, row["argmax_rho_bar_err"], row["err_at_argmax"]))
        for p in row["paths"]:
            print(
                "      %s curvature argmax=%.3f  gap=%.3f (%.1f steps)  aligned=%s"
                % (p["path"], p["argmax_rho_bar_curvature"], p["gap_rho_bar"], p["gap_grid_steps"], p["aligned"])
            )
    print(
        "  aligned configurations = %d, required = %d, supported=%s"
        % (p2["n_configurations_aligned"], p2["n_configurations_required"], p2["supported"])
    )

    print()
    print("=== P3  loss channel dominates cost curvature ===")
    print(
        "  %d/%d relevant cells satisfy it; ratio min=%.2f median=%.2f max=%.2f; supported=%s"
        % (p3["n_loss_dominates"], p3["n_cells"], p3["ratio_min"], p3["ratio_median"], p3["ratio_max"], p3["supported"])
    )

    print()
    print("SUMMARY: P1=%s  P2=%s  P3=%s" % (report["summary"]["P1"], report["summary"]["P2"], report["summary"]["P3"]))


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--maps", default=MAPS)
    ap.add_argument("--radius", default=RADIUS)
    ap.add_argument("--z", type=float, default=MR.Z_OPERATING)
    ap.add_argument("--h", type=float, default=0.02)
    ap.add_argument("--step", type=float, default=0.02)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    report = build_report(
        maps_path=args.maps,
        radius_path=args.radius,
        z=float(args.z),
        h=float(args.h),
        step=float(args.step),
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
