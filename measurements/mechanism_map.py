#!/usr/bin/env python3
"""Phase 20R.7 -- mechanism maps for cost, loss, and K4 fragility.

Estimand (Amd 15): mechanism is cost = delay + w_loss * loss, not delay alone.
This module keeps the K4 common-mode calculation explicit, including physical
clipping of loss under negative common-mode perturbations.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from measurements import decision_error_v2 as D
from measurements import residual_spec as RS
from twin import cost_v2 as C
from twin import topology_v7 as T7


H = 0.01
N_LINKS_IN_PATH = 3
DEFAULT_W_LOSS = {
    "poisson": 3222.244681647411,
    "h2": 4515.904012589386,
}


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def link_delay_loss(tt: D.TruthTable, mode: str, rho_by_link: Mapping[str, float]) -> Tuple[Dict[str, float], Dict[str, float]]:
    delay: Dict[str, float] = {}
    loss: Dict[str, float] = {}
    for link in T7.LINK_NAMES:
        d, l = tt.delay_loss(str(mode), str(link), np.asarray([float(rho_by_link[link])], dtype=float))
        delay[str(link)] = float(d[0])
        loss[str(link)] = float(l[0])
    return delay, loss


def path_loss_from_links(loss_by_link: Mapping[str, float], path: str, shift: float = 0.0) -> float:
    keep = 1.0
    for link in T7.PATHS[str(path)]:
        p = min(max(float(loss_by_link[str(link)]) + float(shift), 0.0), 1.0)
        keep *= 1.0 - p
    return float(1.0 - keep)


def path_delay_from_links(delay_by_link: Mapping[str, float], path: str) -> float:
    return float(sum(float(delay_by_link[str(link)]) for link in T7.PATHS[str(path)]))


def path_costs(
    delay_by_link: Mapping[str, float],
    loss_by_link: Mapping[str, float],
    w_loss: float,
    shift: float = 0.0,
) -> Dict[str, float]:
    return {
        path: path_delay_from_links(delay_by_link, path)
        + float(w_loss) * path_loss_from_links(loss_by_link, path, shift=shift)
        for path in T7.PATH_NAMES
    }


def path_loss_sensitivity(loss_by_link: Mapping[str, float], path: str) -> float:
    """Unclipped d(loss_path)/d(delta) at delta=0."""
    links = tuple(T7.PATHS[str(path)])
    total = 0.0
    for i, link_i in enumerate(links):
        prod = 1.0
        for j, link_j in enumerate(links):
            if i == j:
                continue
            prod *= 1.0 - float(loss_by_link[str(link_j)])
        total += prod
    return float(total)


def grad_cost(tt: D.TruthTable, mode: str, link: str, rho: float, w_loss: float, h: float = H) -> float:
    """Central difference gradient of full cost for one link class."""

    def cost_at(r: float) -> float:
        d, l = tt.delay_loss(str(mode), str(link), np.asarray([float(r)], dtype=float))
        return float(d[0] + float(w_loss) * l[0])

    return float((cost_at(float(rho) + float(h)) - cost_at(float(rho) - float(h))) / (2.0 * float(h)))


def curvature_cost(tt: D.TruthTable, mode: str, link: str, rho: float, w_loss: float, h: float = H) -> float:
    """Central second difference of full cost for one link class."""

    def cost_at(r: float) -> float:
        d, l = tt.delay_loss(str(mode), str(link), np.asarray([float(r)], dtype=float))
        return float(d[0] + float(w_loss) * l[0])

    h = float(h)
    return float((cost_at(float(rho) + h) - 2.0 * cost_at(float(rho)) + cost_at(float(rho) - h)) / (h * h))


def first_order_thresholds(
    costs: Mapping[str, float],
    sensitivities: Mapping[str, float],
    w_loss: float,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for a, b in itertools.combinations(T7.PATH_NAMES, 2):
        gap = abs(float(costs[str(a)]) - float(costs[str(b)]))
        d_s = abs(float(sensitivities[str(a)]) - float(sensitivities[str(b)]))
        row: Dict[str, Any] = {"pair": [str(a), str(b)], "gap": gap, "abs_dS": d_s}
        if d_s < 1e-15:
            row.update({"r_star_path": None, "reason": "equal S; common-mode invariant in first order"})
        else:
            row["r_star_path"] = float(N_LINKS_IN_PATH * gap / (float(w_loss) * d_s))
        out.append(row)
    return sorted(out, key=lambda row: float("inf") if row["r_star_path"] is None else float(row["r_star_path"]))


def _bisect_root(fn, lo: float, hi: float, steps: int = 80) -> float:
    flo = float(fn(lo))
    fhi = float(fn(hi))
    if abs(flo) < 1e-15:
        return float(lo)
    if abs(fhi) < 1e-15:
        return float(hi)
    if flo * fhi > 0.0:
        raise ValueError("root is not bracketed")
    for _ in range(int(steps)):
        mid = 0.5 * (float(lo) + float(hi))
        fm = float(fn(mid))
        if flo * fm <= 0.0:
            hi = mid
            fhi = fm
        else:
            lo = mid
            flo = fm
    return float(0.5 * (float(lo) + float(hi)))


def clipped_pair_roots(
    delay_by_link: Mapping[str, float],
    loss_by_link: Mapping[str, float],
    w_loss: float,
    pair: Sequence[str],
    sign: float,
    x_max: float = 0.05,
    n_grid: int = 2000,
) -> List[Dict[str, float]]:
    """Roots by per-link common-mode magnitude x, with shift = sign*x."""
    a, b = str(pair[0]), str(pair[1])

    def gap_at(x: float) -> float:
        costs = path_costs(delay_by_link, loss_by_link, float(w_loss), shift=float(sign) * float(x))
        return float(costs[a] - costs[b])

    xs = np.linspace(0.0, float(x_max), int(n_grid) + 1)
    vals = [gap_at(float(x)) for x in xs]
    roots: List[Dict[str, float]] = []
    for i in range(len(xs) - 1):
        if vals[i] * vals[i + 1] > 0.0:
            continue
        root = _bisect_root(gap_at, float(xs[i]), float(xs[i + 1]))
        if roots and abs(root - roots[-1]["x_link"]) < 1e-10:
            continue
        roots.append({"x_link": float(root), "r_star_path": float(N_LINKS_IN_PATH * root)})
    return roots


def clipped_thresholds(
    delay_by_link: Mapping[str, float],
    loss_by_link: Mapping[str, float],
    w_loss: float,
    sign: float,
    x_max: float = 0.05,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    base_costs = path_costs(delay_by_link, loss_by_link, w_loss, shift=0.0)
    for pair in itertools.combinations(T7.PATH_NAMES, 2):
        roots = clipped_pair_roots(delay_by_link, loss_by_link, w_loss, pair, sign, x_max=x_max)
        out.append(
            {
                "pair": [str(pair[0]), str(pair[1])],
                "sign": float(sign),
                "gap": abs(float(base_costs[str(pair[0])]) - float(base_costs[str(pair[1])])),
                "roots": roots,
                "first_r_star_path": None if not roots else float(roots[0]["r_star_path"]),
            }
        )
    return sorted(out, key=lambda row: float("inf") if row["first_r_star_path"] is None else float(row["first_r_star_path"]))


def scan_k4_lookup(scan_path: Optional[str]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    if not scan_path:
        return {}
    with open(scan_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    out: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for row in data.get("scans", []):
        if str(row.get("channel")) != "loss" or str(row.get("variant")) != "common_mode":
            continue
        out[(str(row.get("mode")), str(row.get("channel")))] = {
            "r_star": row.get("r_star"),
            "r_star_bracket": row.get("r_star_bracket"),
            "first_broken": row.get("first_broken"),
            "first_broken_detail": row.get("first_broken_detail"),
        }
    return out


def analyze_mode(
    tt: D.TruthTable,
    mode: str,
    rho_bar: float,
    w_loss: float,
    scan_lookup: Mapping[Tuple[str, str], Mapping[str, Any]],
) -> Dict[str, Any]:
    rho = C.rho_vector(float(rho_bar))
    delay, loss = link_delay_loss(tt, str(mode), rho)
    costs = path_costs(delay, loss, float(w_loss), shift=0.0)
    sensitivities = {path: path_loss_sensitivity(loss, path) for path in T7.PATH_NAMES}
    return {
        "mode": str(mode),
        "rho_bar": float(rho_bar),
        "w_loss": float(w_loss),
        "rho_by_link": {str(k): float(v) for k, v in rho.items()},
        "link_delay_ms": delay,
        "link_loss": loss,
        "path_cost": costs,
        "path_loss_sensitivity_S": sensitivities,
        "first_order_unclipped": first_order_thresholds(costs, sensitivities, float(w_loss)),
        "clipped_negative_loss_shift": clipped_thresholds(delay, loss, float(w_loss), sign=-1.0),
        "clipped_positive_loss_shift": clipped_thresholds(delay, loss, float(w_loss), sign=+1.0),
        "scan_cascade_loss_common_mode": dict(scan_lookup.get((str(mode), "loss"), {})),
    }


def build_report(
    rho_bar: float = 0.925,
    modes: Sequence[str] = ("poisson", "h2"),
    scan_path: Optional[str] = "results/SUPERSEDED/phase-20R/breakdown_scan_cascade.json",
) -> Dict[str, Any]:
    tt = D.TruthTable()
    scan_lookup = scan_k4_lookup(scan_path)
    rows = [
        analyze_mode(tt, str(mode), float(rho_bar), DEFAULT_W_LOSS[str(mode)], scan_lookup)
        for mode in modes
    ]
    return {
        "schema": "phase20r7/mechanism_map/v1",
        "phase": "20R.7",
        "rho_bar": float(rho_bar),
        "h": H,
        "n_links_in_path": N_LINKS_IN_PATH,
        "truth_table": D.TRUTH_TABLE,
        "scan_reference": scan_path,
        **RS.git_commit(),
        "modes": rows,
    }


def print_summary(report: Mapping[str, Any]) -> None:
    for row in report.get("modes", []):
        print("=== %s rho_bar=%.3f ===" % (row["mode"], float(row["rho_bar"])))
        print("path costs:")
        for path in T7.PATH_NAMES:
            print("  %-3s cost=%10.4f S=%.6f" % (
                path,
                float(row["path_cost"][path]),
                float(row["path_loss_sensitivity_S"][path]),
            ))
        unclipped = row["first_order_unclipped"][0]
        neg = next(
            (item for item in row["clipped_negative_loss_shift"] if item["first_r_star_path"] is not None),
            None,
        )
        print("unclipped first-order best: %s/%s r*=%.6f" % (
            unclipped["pair"][0],
            unclipped["pair"][1],
            float(unclipped["r_star_path"]),
        ))
        if neg is None:
            print("clipped negative best:      none in scanned range")
        else:
            print("clipped negative best:      %s/%s r*=%.6f" % (
                neg["pair"][0],
                neg["pair"][1],
                float(neg["first_r_star_path"]),
            ))
        scan = row.get("scan_cascade_loss_common_mode") or {}
        if scan.get("r_star") is not None:
            print("scan cascade K4 r*:        %.6f" % float(scan["r_star"]))
        print()


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rho-bar", type=float, default=0.925)
    ap.add_argument("--modes", default="poisson,h2")
    ap.add_argument("--scan", default="results/SUPERSEDED/phase-20R/breakdown_scan_cascade.json")
    ap.add_argument("--out", default="results/SUPERSEDED/phase-20R/mechanism_k4_closed_form.json")
    args = ap.parse_args(argv)

    modes = [part.strip() for part in args.modes.split(",") if part.strip()]
    unknown = sorted(set(modes) - set(DEFAULT_W_LOSS))
    if unknown:
        raise ValueError("unknown modes: %s" % unknown)
    report = build_report(float(args.rho_bar), modes=modes, scan_path=args.scan)
    print_summary(report)
    ensure_parent(args.out)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
