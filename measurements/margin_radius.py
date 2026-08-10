#!/usr/bin/env python3
"""Phase 20R.7 -- decision-margin radius r(s) and its link to decision error.

Amendment 15 sec.5 fixes the estimand:

    r(s) = (cost_second(s) - cost_best(s)) / (2 * ||grad_rho cost(s)||)

with the FULL cost gradient, ``grad delay + w_loss * grad loss``. A denominator
built from the delay channel alone, or with ``w_loss`` dropped, is a different
estimand and is not accepted.

Amendment 17 sec.2 fixes what was left open: costs and gradients are taken from
the MEASURED truth table, not from the twin, because ``err`` is defined against
measured truth and the fragility that produces ``err`` is a property of the true
landscape. The twin version is computed alongside as a diagnostic only.

The truth table is piecewise linear in rho, so its gradient is the exact slope
of the segment containing the sample. No finite difference is needed here, and
none is used: Amendment 16 banned sub-grid differences for the SECOND
derivative, and this module never needs one.
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
from measurements import residual_spec as RS
from measurements.decision_error import spearman_one_sided, spearman_rho
from twin import cost_v2 as C
from twin import topology_v7 as T7


MODES: Tuple[str, ...] = ("poisson", "h2")
Z_OPERATING = 0.55
SEEDS: Tuple[int, ...] = (101, 102, 103, 104, 105)
N_STEPS = 200_000
ERR_SUMMARY = D.SUMMARY_OUT
DEFAULT_OUT = "results/phase-20R/margin_radius.json"


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


class LinkInterp:
    """Delay, loss, and their exact rho-slopes for one measured link curve.

    ``TruthTable`` interpolates linearly, so d/drho is the slope of the segment
    the sample falls in. At a knot the left and right slopes differ; the mean of
    the two is used, which matches the subgradient midpoint and keeps the map
    continuous. Knot hits have measure zero for AR(1) samples and are counted.
    """

    def __init__(self, tt: D.TruthTable, mode: str, link: str):
        bw, _base, q = T7.LINKS[str(link)]
        grid, delay, loss, _se = tt.curves[(str(mode), float(bw), int(q))]
        self.mode = str(mode)
        self.link = str(link)
        self.bw = float(bw)
        self.q = int(q)
        self.static_ms = C.static_link_ms(str(link))
        self.grid = np.asarray(grid, dtype=float)
        self.delay = np.asarray(delay, dtype=float)
        self.loss = np.asarray(loss, dtype=float)
        dx = np.diff(self.grid)
        self.slope_delay = np.diff(self.delay) / dx
        self.slope_loss = np.diff(self.loss) / dx
        self.lo = float(self.grid[0])
        self.hi = float(self.grid[-1])
        self.n_out_of_domain = 0
        self.n_knot_hits = 0
        self.n_seen = 0

    def evaluate(self, rho: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Return ``(delay_ms, loss, d_delay_d_rho, d_loss_d_rho)``.

        Outside the measured domain the value is clipped, exactly as
        ``TruthTable`` does, and the slope is set to 0 so that a clipped sample
        cannot manufacture a large or small radius. Such samples are counted so
        the caller can gate on them.
        """
        r = np.asarray(rho, dtype=float)
        self.n_seen += int(r.size)
        outside = (r < self.lo) | (r > self.hi)
        self.n_out_of_domain += int(np.count_nonzero(outside))
        rq = np.clip(r, self.lo, self.hi)

        delay = np.interp(rq, self.grid, self.delay) + self.static_ms
        loss = np.interp(rq, self.grid, self.loss)

        k = np.clip(np.searchsorted(self.grid, rq, side="right") - 1, 0, self.slope_delay.size - 1)
        on_knot = np.isclose(rq, self.grid[k], rtol=0.0, atol=1e-12)
        interior_knot = on_knot & (k > 0)
        self.n_knot_hits += int(np.count_nonzero(interior_knot))

        d_delay = self.slope_delay[k].copy()
        d_loss = self.slope_loss[k].copy()
        if np.any(interior_knot):
            km = k[interior_knot] - 1
            d_delay[interior_knot] = 0.5 * (d_delay[interior_knot] + self.slope_delay[km])
            d_loss[interior_knot] = 0.5 * (d_loss[interior_knot] + self.slope_loss[km])

        d_delay[outside] = 0.0
        d_loss[outside] = 0.0
        return delay, loss, d_delay, d_loss

    def report(self) -> Dict[str, Any]:
        return {
            "link": self.link,
            "bw": self.bw,
            "q": self.q,
            "rho_domain": [self.lo, self.hi],
            "n_seen": self.n_seen,
            "n_out_of_domain": self.n_out_of_domain,
            "frac_out_of_domain": self.n_out_of_domain / max(self.n_seen, 1),
            "n_knot_hits": self.n_knot_hits,
        }


def path_cost_and_grad(
    interps: Mapping[str, LinkInterp],
    rho_mat: np.ndarray,
    w_loss: float,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """Return ``cost[t, path]`` and ``grad[t, path, link]`` on measured truth.

    For a path P with links i in P:

        cost_P   = sum_i delay_i + w_loss * (1 - prod_i (1 - p_i))
        dcost_P
        -------  = ddelay_i/drho_i + w_loss * dp_i/drho_i * prod_{j!=i}(1 - p_j)
        drho_i

    Links not on P get gradient 0, which is what makes ``grad_second - grad_best``
    a meaningful 8-dimensional vector: links shared by both paths cancel.
    """
    rho_mat = np.asarray(rho_mat, dtype=float)
    n = int(rho_mat.shape[0])
    idx = {link: i for i, link in enumerate(T7.LINK_NAMES)}

    delay = np.empty((n, len(T7.LINK_NAMES)), dtype=float)
    loss = np.empty_like(delay)
    d_delay = np.empty_like(delay)
    d_loss = np.empty_like(delay)
    for link, i in idx.items():
        delay[:, i], loss[:, i], d_delay[:, i], d_loss[:, i] = interps[link].evaluate(rho_mat[:, i])

    cost = np.zeros((n, T7.K), dtype=float)
    grad = np.zeros((n, T7.K, len(T7.LINK_NAMES)), dtype=float)
    for a, path in enumerate(T7.PATH_NAMES):
        links = [idx[link] for link in T7.PATHS[path]]
        keep = np.ones(n, dtype=float)
        for i in links:
            keep *= 1.0 - loss[:, i]
        cost[:, a] = delay[:, links].sum(axis=1) + float(w_loss) * (1.0 - keep)
        for i in links:
            others = np.ones(n, dtype=float)
            for j in links:
                if j != i:
                    others *= 1.0 - loss[:, j]
            grad[:, a, i] = d_delay[:, i] + float(w_loss) * d_loss[:, i] * others

    diag = {"links": [interps[link].report() for link in T7.LINK_NAMES]}
    return cost, grad, diag


def radius_series(cost: np.ndarray, grad: np.ndarray) -> Dict[str, np.ndarray]:
    """r(s) per sample, in the preregistered form and in the exact pair form."""
    order = np.argsort(cost, axis=1)
    rows = np.arange(cost.shape[0])
    best, second = order[:, 0], order[:, 1]
    margin = cost[rows, second] - cost[rows, best]

    g_best = grad[rows, best, :]
    g_second = grad[rows, second, :]
    norm_best = np.linalg.norm(g_best, axis=1)
    norm_second = np.linalg.norm(g_second, axis=1)

    # Amd 15 sec.5 form. 2*max(||g_a||,||g_b||) >= ||g_a - g_b|| by the triangle
    # inequality, so this is a conservative lower-bound distance to the flip.
    denom_bound = 2.0 * np.maximum(norm_best, norm_second)
    denom_exact = np.linalg.norm(g_second - g_best, axis=1)

    with np.errstate(divide="ignore", invalid="ignore"):
        r_bound = np.where(denom_bound > 0.0, margin / denom_bound, np.inf)
        r_exact = np.where(denom_exact > 0.0, margin / denom_exact, np.inf)

    return {
        "margin_ms": margin,
        "r_bound": r_bound,
        "r_exact": r_exact,
        "grad_norm_best": norm_best,
        "grad_norm_second": norm_second,
        "best": best,
        "second": second,
    }


def _finite_median(values: np.ndarray) -> Tuple[float, float]:
    v = np.asarray(values, dtype=float)
    finite = np.isfinite(v)
    frac = float(np.count_nonzero(~finite)) / max(v.size, 1)
    return (float(np.median(v[finite])) if np.any(finite) else math.nan), frac


def cell_radius(
    tt: D.TruthTable,
    cell: Mapping[str, Any],
    seeds: Sequence[int] = SEEDS,
    n: int = N_STEPS,
    tau: float = D.TAU,
) -> Dict[str, Any]:
    mode = str(cell["mode"])
    rho_bar = float(cell["rho_bar"])
    sigma = float(cell["sigma_rho"])
    w_loss = float(cell["w_loss"])
    interps = {link: LinkInterp(tt, mode, link) for link in T7.LINK_NAMES}

    per_seed: List[Dict[str, Any]] = []
    for seed in seeds:
        rho_mat = D.rho_matrix_from_cell(
            mode, rho_bar, sigma, int(seed), tau=float(tau), n=int(n), dt=D.DT, source=D.RHO_SOURCE
        )
        cost, grad, _diag = path_cost_and_grad(interps, rho_mat, w_loss)
        series = radius_series(cost, grad)
        finite_bound = series["r_bound"][np.isfinite(series["r_bound"])]
        med_bound, inf_bound = _finite_median(series["r_bound"])
        med_exact, inf_exact = _finite_median(series["r_exact"])
        per_seed.append(
            {
                "seed": int(seed),
                "median_r_bound": med_bound,
                "median_r_exact": med_exact,
                "frac_infinite_bound": inf_bound,
                "frac_infinite_exact": inf_exact,
                "median_margin_ms": float(np.median(series["margin_ms"])),
                "median_grad_norm_best": float(np.median(series["grad_norm_best"])),
                "p10_r_bound": float(np.percentile(finite_bound, 10)) if finite_bound.size else math.nan,
                "frac_r_bound_below_sigma": float(np.mean(series["r_bound"] < sigma)),
            }
        )

    def across(key: str) -> Dict[str, float]:
        vals = np.asarray([row[key] for row in per_seed], dtype=float)
        return {
            "mean": float(np.mean(vals)),
            "median": float(np.median(vals)),
            "sd": float(np.std(vals, ddof=1)) if vals.size > 1 else 0.0,
        }

    return {
        "mode": mode,
        "rho_bar": rho_bar,
        "sigma_rho": sigma,
        "w_loss": w_loss,
        "tau_rho": float(tau),
        "n": int(n),
        "seeds": [int(s) for s in seeds],
        "per_seed": per_seed,
        "median_r_bound": across("median_r_bound"),
        "median_r_exact": across("median_r_exact"),
        "median_margin_ms": across("median_margin_ms"),
        "frac_r_bound_below_sigma": across("frac_r_bound_below_sigma"),
        "link_domain": [interps[link].report() for link in T7.LINK_NAMES],
    }


def load_err(summary_path: str = ERR_SUMMARY, z: float = Z_OPERATING) -> Dict[Tuple[str, float], Dict[str, float]]:
    table = pd.read_parquet(summary_path)
    table = table[table["mode"].isin(MODES)]
    table = table[np.isclose(table["z"].to_numpy(float), float(z))]
    out: Dict[Tuple[str, float], Dict[str, float]] = {}
    for _i, row in table.iterrows():
        out[(str(row["mode"]), float(row["rho_bar"]))] = {
            "err_total": float(row["err_total"]),
            "err_total_ci95_lo": float(row["err_total_ci95_lo"]),
            "err_total_ci95_hi": float(row["err_total_ci95_hi"]),
            "d_sla": float(row["d_sla"]),
            "n_seed": int(row["n_seed"]),
        }
    return out


def spearman_negative(xs: Sequence[float], ys: Sequence[float]) -> Dict[str, float]:
    """Exact one-sided rank test for the preregistered direction rho < 0.

    ``spearman_one_sided`` returns the UPPER tail. Negating x maps the observed
    correlation to its negative, so the upper tail of the negated problem is the
    lower tail of the original.
    """
    flipped = [-float(x) for x in xs]
    upper = spearman_one_sided(flipped, ys)
    plain = spearman_rho(xs, ys)
    return {
        "rho": float(plain["rho"]),
        "n": int(plain["n"]),
        "p_one_sided_negative": float(upper["p_one_sided"]),
    }


def hypothesis_h1(
    cells: Sequence[Mapping[str, Any]],
    err: Mapping[Tuple[str, float], Mapping[str, float]],
    alpha: float = 0.05,
    radius_key: str = "median_r_bound",
) -> Dict[str, Any]:
    """Amd 15 sec.7 prediction 1: Spearman(median r(s), err) < 0 with p < alpha."""
    pooled_x: List[float] = []
    pooled_y: List[float] = []
    rows: List[Dict[str, Any]] = []
    for cell in cells:
        key = (str(cell["mode"]), float(cell["rho_bar"]))
        if key not in err:
            continue
        x = float(cell[radius_key]["mean"])
        y = float(err[key]["err_total"])
        pooled_x.append(x)
        pooled_y.append(y)
        rows.append({"mode": key[0], "rho_bar": key[1], "radius": x, "err_total": y})

    pooled = spearman_negative(pooled_x, pooled_y)
    by_mode: Dict[str, Any] = {}
    for mode in sorted({row["mode"] for row in rows}):
        sub = [row for row in rows if row["mode"] == mode]
        if len(sub) >= 3:
            by_mode[mode] = spearman_negative([r["radius"] for r in sub], [r["err_total"] for r in sub])
            by_mode[mode]["supported"] = bool(
                by_mode[mode]["rho"] < 0.0 and by_mode[mode]["p_one_sided_negative"] < alpha
            )
        else:
            by_mode[mode] = {"n": len(sub), "reason": "fewer than 3 cells"}

    supported = bool(pooled["rho"] < 0.0 and pooled["p_one_sided_negative"] < float(alpha))
    return {
        "radius_key": radius_key,
        "alpha": float(alpha),
        "z": Z_OPERATING,
        "points": rows,
        "pooled": pooled,
        "by_mode": by_mode,
        "supported": supported,
        "verdict": (
            "H1 supported: smaller decision-margin radius goes with larger decision error."
            if supported
            else "H1 NOT supported. Per Amendment 15 sec.7 the conclusion is that the "
            "mechanism map does not license a cost-margin-radius explanation of err. "
            "r(s) is not redefined, the channel is not changed, and no variant is added."
        ),
        "dependence_caveat": (
            "The eight cells are not eight independent draws: ar1_matrix seeds only on "
            "`seed`, so poisson and h2 at the same rho_bar share the rho trajectory up to "
            "the family reliability ceiling. The exact permutation p-value assumes "
            "exchangeability across cells and is therefore optimistic. Report it with this "
            "caveat, and read the per-family tests as the conservative view."
        ),
    }


def build_report(
    modes: Sequence[str] = MODES,
    seeds: Sequence[int] = SEEDS,
    n: int = N_STEPS,
    tau: float = D.TAU,
    z: float = Z_OPERATING,
    alpha: float = 0.05,
) -> Dict[str, Any]:
    tt = D.TruthTable()
    cells = [c for c in D.measurement_cells() if str(c["mode"]) in set(modes)]
    computed = [cell_radius(tt, cell, seeds=seeds, n=n, tau=tau) for cell in cells]
    err = load_err(z=z)
    return {
        "schema": "phase20r7/margin_radius/v1",
        "phase": "20R.7",
        "amendment": "00r-amendment-17",
        "estimand": "r(s) = (cost_second - cost_best) / (2 * ||grad_rho cost||), full cost gradient",
        "cost_source": "measured truth table",
        "gradient_method": "exact segment slope of the piecewise-linear interpolant",
        "modes": list(modes),
        "z": float(z),
        "n": int(n),
        "seeds": [int(s) for s in seeds],
        "tau_rho": float(tau),
        "truth_table": D.TRUTH_TABLE,
        "err_summary": ERR_SUMMARY,
        "cells": computed,
        "h1_bound": hypothesis_h1(computed, err, alpha=alpha, radius_key="median_r_bound"),
        "h1_exact_diagnostic": hypothesis_h1(computed, err, alpha=alpha, radius_key="median_r_exact"),
        **RS.git_commit(),
    }


def print_summary(report: Mapping[str, Any]) -> None:
    print("cost source: %s   gradient: %s" % (report["cost_source"], report["gradient_method"]))
    print("n=%d  seeds=%s  z=%.2f" % (report["n"], report["seeds"], report["z"]))
    print()
    print("=== per cell ===")
    print("  mode     rho_bar  w_loss     median r(s)   median margin  P[r<sigma]")
    for cell in report["cells"]:
        print(
            "  %-8s %-7.3f  %-9.1f  %-12.6f  %-13.4f  %.4f"
            % (
                cell["mode"],
                cell["rho_bar"],
                cell["w_loss"],
                cell["median_r_bound"]["mean"],
                cell["median_margin_ms"]["mean"],
                cell["frac_r_bound_below_sigma"]["mean"],
            )
        )
    for key in ("h1_bound", "h1_exact_diagnostic"):
        h1 = report[key]
        print()
        print("=== %s (%s) ===" % (key, h1["radius_key"]))
        print(
            "  pooled  rho=%+.6f  n=%d  p_one_sided(<0)=%.6f  supported=%s"
            % (h1["pooled"]["rho"], h1["pooled"]["n"], h1["pooled"]["p_one_sided_negative"], h1["supported"])
        )
        for mode, row in sorted(h1["by_mode"].items()):
            if "rho" in row:
                print(
                    "  %-8s rho=%+.6f  n=%d  p=%.6f  supported=%s"
                    % (mode, row["rho"], row["n"], row["p_one_sided_negative"], row["supported"])
                )
            else:
                print("  %-8s %s" % (mode, row["reason"]))
    print()
    print(report["h1_bound"]["verdict"])


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--modes", default=",".join(MODES))
    ap.add_argument("--seeds", default=",".join(str(s) for s in SEEDS))
    ap.add_argument("--n", type=int, default=N_STEPS)
    ap.add_argument("--tau", type=float, default=D.TAU)
    ap.add_argument("--z", type=float, default=Z_OPERATING)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    report = build_report(
        modes=tuple(p.strip() for p in args.modes.split(",") if p.strip()),
        seeds=tuple(int(p) for p in args.seeds.split(",") if p.strip()),
        n=int(args.n),
        tau=float(args.tau),
        z=float(args.z),
        alpha=float(args.alpha),
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
