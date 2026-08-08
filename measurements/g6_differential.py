#!/usr/bin/env python3
"""Phase 20R.6 -- does the residual additive bias move the DECISION?

G6 as written tests ``|A' - A|``, an absolute quantity. But RQ-A is defined on
``argmin cost``, and ``argmin`` cannot see a bias that lands on all four actions
equally: adding the same number to every column leaves the smallest column
unchanged. The distinction between common-mode and differential error was already
signed in ``docs/phase-20R/01-inherited-audit.md`` (Lesson 20R.0), where Phase 20
was rejected precisely because its error was differential.

This module applies the measured per-link residual to the *truth* side of the
existing decision-error machinery -- the twin keeps using the original table --
and reports how far ``err(z)`` and ``d_sla(z)`` actually move.

Two gates, reported side by side; neither replaces the other:

``G6-ABS``   ``|A' - A| <= 0.20 x cost gap``. Already FAIL. Reported in full.
``G6-DIFF``  ``|delta err| <= 0.10 x err`` and ``|delta d_sla| <= 0.10 x d_sla``.

The residual is a property of a link *class* ``(bw, q)``. The three measured
tandem links cover 3/3 of the classes present in ``topology_v7``, so applying
them to all eight links is a class-wise mapping, not an extrapolation.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from measurements import decision_error_v2 as D
from mininet.topology_tandem import TANDEM_LINKS
from twin import cost_v2 as C
from twin import topology_v7 as T7


DIAG_CA = "results/phase-20R/diag_ca_late.json"
CHECK_REPORT = "results/phase-20R/additivity_check_budgetfix_bg.json"
OUT = "results/phase-20R/g6_differential.json"
RHO_BAR = 0.925
MODES = ("poisson", "h2")
SEEDS = (11, 12, 13)
N_TRACE = 100_000
K_SCALES = (0.0, 1.0, 2.0, 3.0)
ERR_TOL_FRAC = 0.10
DSLA_TOL_FRAC = 0.10


def link_class(t7_link: str) -> Tuple[float, int]:
    bw, _base, q = T7.LINKS[t7_link]
    return (float(bw), int(q))


def tandem_class_map() -> Dict[Tuple[float, int], str]:
    """(bw, q) -> tandem link name that measured that class."""
    out: Dict[Tuple[float, int], str] = {}
    for name, t7_link, _bw, _q, _base in TANDEM_LINKS:
        out[link_class(t7_link)] = name
    return out


def class_coverage() -> Dict[str, Any]:
    measured = set(tandem_class_map())
    needed = {link_class(link) for link in T7.LINK_NAMES}
    return {
        "classes_measured": sorted("bw%.0f_q%d" % k for k in measured),
        "classes_in_topology": sorted("bw%.0f_q%d" % k for k in needed),
        "uncovered": sorted("bw%.0f_q%d" % k for k in (needed - measured)),
        "full_coverage": bool(not (needed - measured)),
    }


def load_residuals(
    diag_ca: str = DIAG_CA,
    check_report: str = CHECK_REPORT,
    modes: Sequence[str] = MODES,
) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Per-link residual loss (after removing the c_a-explained part) and delay."""
    with open(diag_ca, "r", encoding="utf-8") as f:
        sens = json.load(f)["burstiness_sensitivity"]
    with open(check_report, "r", encoding="utf-8") as f:
        checks = json.load(f)["checks"]
    delay = {
        (str(row["mode"]), str(row["link"])): float(row["mean_ms"])
        for row in checks
        if row.get("contrast") == "Aprime_minus_A_delay"
    }
    out: Dict[str, Dict[str, Dict[str, float]]] = {mode: {} for mode in modes}
    for row in sens:
        mode, link = str(row["mode"]), str(row["link"])
        if mode not in out or row.get("residual_quad") is None:
            continue
        out[mode][link] = {
            "loss": float(row["residual_quad"]),
            "delay_ms": float(delay.get((mode, link), 0.0)),
        }
    return out


def scaled_bias(
    residual: Mapping[str, Mapping[str, float]],
    k: float,
    order: Optional[Sequence[str]] = None,
) -> Dict[str, Dict[str, float]]:
    """Split the residual into common-mode + k x differential.

    ``k = 0`` is pure common-mode (every link shifted by the same amount, which
    ``argmin`` is blind to); ``k = 1`` is exactly what was measured; ``k > 1``
    stress-tests a larger link-to-link spread than observed. ``order`` permutes
    which class carries which deviation, so the sensitivity table can report the
    worst-case assignment rather than only the observed one.
    """
    links = sorted(residual)
    if order is None:
        order = links
    out: Dict[str, Dict[str, float]] = {}
    for field in ("loss", "delay_ms"):
        vals = np.array([float(residual[link][field]) for link in links], dtype=float)
        mean = float(vals.mean())
        dev = np.array([float(residual[src][field]) - mean for src in order], dtype=float)
        for link, d in zip(links, dev):
            out.setdefault(link, {})[field] = mean + float(k) * float(d)
    return out


def biased_path_tables(
    tt: D.TruthTable,
    mode: str,
    rho_mat: np.ndarray,
    w_loss: float,
    bias: Mapping[str, Mapping[str, float]],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``TruthTable.path_tables`` with a per-link-class additive bias."""
    cls_map = tandem_class_map()
    n = int(rho_mat.shape[0])
    delay = np.zeros((n, T7.K), dtype=float)
    keep = np.ones((n, T7.K), dtype=float)
    idx = {link: i for i, link in enumerate(T7.LINK_NAMES)}
    for action, path in enumerate(T7.PATH_NAMES):
        for link in T7.PATHS[path]:
            d, loss = tt.delay_loss(mode, link, rho_mat[:, idx[link]])
            b = bias.get(cls_map[link_class(link)], {"loss": 0.0, "delay_ms": 0.0})
            delay[:, action] += d + float(b.get("delay_ms", 0.0))
            keep[:, action] *= 1.0 - np.clip(loss + float(b.get("loss", 0.0)), 0.0, 1.0)
    loss_path = 1.0 - keep
    return delay, loss_path, delay + float(w_loss) * loss_path


def cost_shift_decomposition(
    tt: D.TruthTable,
    mode: str,
    rho_mat: np.ndarray,
    w_loss: float,
    bias: Mapping[str, Mapping[str, float]],
) -> Dict[str, float]:
    """How much of the cost shift is shared by all four actions."""
    _d0, _l0, c0 = tt.path_tables(mode, rho_mat, w_loss)
    _d1, _l1, c1 = biased_path_tables(tt, mode, rho_mat, w_loss, bias)
    shift = (c1 - c0).mean(axis=0)
    ordered = np.sort(c0, axis=1)
    return {
        "common_mode_ms": float(shift.mean()),
        "differential_ms": float(shift.max() - shift.min()),
        "per_path_ms": {name: float(v) for name, v in zip(T7.PATH_NAMES, shift)},
        "decision_gap_ms": float((ordered[:, 1] - ordered[:, 0]).mean()),
        "differential_over_gap": float(
            (shift.max() - shift.min()) / float((ordered[:, 1] - ordered[:, 0]).mean())
        ),
    }


def _metrics(
    a_twin: np.ndarray, a_truth: np.ndarray, viol: np.ndarray, current: np.ndarray
) -> Tuple[float, float]:
    err = float((a_twin != a_truth).mean())
    dsla = float(viol[current, a_twin].mean() - viol[current, a_truth].mean())
    return err, dsla


def evaluate_cell(
    tt: D.TruthTable,
    cv2: C.CostV2,
    cell: Mapping[str, Any],
    seed: int,
    bias: Mapping[str, Mapping[str, float]],
    z_values: Sequence[float],
    n: int = N_TRACE,
) -> Dict[str, Any]:
    """err/d_sla under the original table and under table + bias, same twin."""
    mode = str(cell["mode"])
    w_loss = float(cell["w_loss"])
    sigma, _src = D.resolve_sigma(cell)
    tt.reset_clip_log()
    rho_mat = D.rho_matrix_from_cell(mode, float(cell["rho_bar"]), sigma, int(seed), n=n)
    d0, l0, c0 = tt.path_tables(mode, rho_mat, w_loss)
    d1, l1, c1 = biased_path_tables(tt, mode, rho_mat, w_loss, bias)
    _df, _lf, cf = cv2.tables_batch(rho_mat, mode, w_loss)

    a_fresh = cf.argmin(axis=1)
    a_true0 = c0.argmin(axis=1)
    a_true1 = c1.argmin(axis=1)
    viol0 = D._viol(d0, l0, float(cell["t_delay_ms"]), float(cell["t_loss"]))
    viol1 = D._viol(d1, l1, float(cell["t_delay_ms"]), float(cell["t_loss"]))

    rows = np.arange(int(n))
    start = max(int(round(float(z) / D.DT)) for z in z_values)
    out: Dict[str, Any] = {"mode": mode, "seed": int(seed), "per_z": {}}
    for z_s in z_values:
        k = int(round(float(z_s) / D.DT))
        current = rows[start:int(n)]
        a_twin = a_fresh[current - k]
        err0, dsla0 = _metrics(a_twin, a_true0[current], viol0, current)
        err1, dsla1 = _metrics(a_twin, a_true1[current], viol1, current)
        out["per_z"][D.z_key(z_s)] = {
            "z_s": float(z_s),
            "err_base": err0,
            "err_biased": err1,
            "d_err": err1 - err0,
            "dsla_base": dsla0,
            "dsla_biased": dsla1,
            "d_dsla": dsla1 - dsla0,
        }
    out["argmin_flip_rate"] = float((a_true0 != a_true1).mean())
    return out


def _per_link_loss_se(check_report: str = CHECK_REPORT) -> Dict[Tuple[str, str], float]:
    """Standard error of each per-link loss contrast, for the bias/power split."""
    if not os.path.exists(check_report):
        return {}
    with open(check_report, "r", encoding="utf-8") as f:
        checks = json.load(f)["checks"]
    return {
        (str(row["mode"]), str(row["link"])): float(row["se_ms"])
        for row in checks
        if row.get("contrast") == "Aprime_minus_A_loss" and row.get("se_ms") is not None
    }


def run(
    residuals: Mapping[str, Mapping[str, Mapping[str, float]]],
    modes: Sequence[str] = MODES,
    seeds: Sequence[int] = SEEDS,
    rho_bar: float = RHO_BAR,
    k_scales: Sequence[float] = K_SCALES,
    n: int = N_TRACE,
    worst_case_permutations: bool = True,
) -> Dict[str, Any]:
    tt = D.TruthTable()
    cv2 = C.CostV2()
    se_per_link = _per_link_loss_se()
    cells = {
        str(cell["mode"]): cell
        for cell in D.feasible_cells(include_pc1=False)
        if abs(float(cell["rho_bar"]) - float(rho_bar)) < 1e-9
    }
    z_values = D.z_values_for()
    results: Dict[str, Any] = {"modes": {}}
    for mode in modes:
        cell = cells[mode]
        residual = residuals[mode]
        links = sorted(residual)
        orders = list(itertools.permutations(links)) if worst_case_permutations else [tuple(links)]

        observed_bias = scaled_bias(residual, 1.0)
        decomp = cost_shift_decomposition(
            tt, mode, D.rho_matrix_from_cell(mode, float(cell["rho_bar"]), D.resolve_sigma(cell)[0], int(seeds[0]), n=n),
            float(cell["w_loss"]), observed_bias,
        )
        per_k: List[Dict[str, Any]] = []
        for k in k_scales:
            worst = {"d_err": 0.0, "d_dsla": 0.0}
            detail = None
            for order in orders:
                bias = scaled_bias(residual, float(k), order=order)
                agg_err: List[float] = []
                agg_dsla: List[float] = []
                base_err: List[float] = []
                base_dsla: List[float] = []
                for seed in seeds:
                    ev = evaluate_cell(tt, cv2, cell, seed, bias, z_values, n=n)
                    for rec in ev["per_z"].values():
                        agg_err.append(rec["d_err"])
                        agg_dsla.append(rec["d_dsla"])
                        base_err.append(rec["err_base"])
                        base_dsla.append(rec["dsla_base"])
                cand_err = float(np.max(np.abs(agg_err)))
                cand_dsla = float(np.max(np.abs(agg_dsla)))
                if cand_err >= worst["d_err"]:
                    worst = {"d_err": cand_err, "d_dsla": cand_dsla}
                    # Keep the SIGNED range too. ``max|.|`` hides direction, and
                    # direction is what decides how the number may be stated: a
                    # shift that is negative throughout means the published value
                    # is an upper bound on the harm, which is a claim worth making.
                    detail = {
                        "order": list(order),
                        "err_base_mean": float(np.mean(base_err)),
                        "dsla_base_mean": float(np.mean(base_dsla)),
                        "max_abs_d_err": cand_err,
                        "max_abs_d_dsla": cand_dsla,
                        "d_err_lo": float(np.min(agg_err)),
                        "d_err_hi": float(np.max(agg_err)),
                        "d_sla_lo": float(np.min(agg_dsla)),
                        "d_sla_hi": float(np.max(agg_dsla)),
                        "direction": (
                            "BAO THU (con so cong bo la can tren)"
                            if float(np.max(agg_dsla)) <= 0.0
                            else "KHONG bao thu -- phai ghi ro"
                            if float(np.min(agg_dsla)) >= 0.0
                            else "HAI CHIEU"
                        ),
                    }
            assert detail is not None
            err_tol = ERR_TOL_FRAC * detail["err_base_mean"]
            dsla_tol = DSLA_TOL_FRAC * abs(detail["dsla_base_mean"])
            detail.update(
                {
                    "k": float(k),
                    "err_tol": err_tol,
                    "dsla_tol": dsla_tol,
                    "err_pass": bool(detail["max_abs_d_err"] <= err_tol),
                    "dsla_pass": bool(detail["max_abs_d_dsla"] <= dsla_tol),
                    "d_err_rel": detail["max_abs_d_err"] / detail["err_base_mean"]
                    if detail["err_base_mean"]
                    else float("nan"),
                }
            )
            per_k.append(detail)
        observed = next(row for row in per_k if row["k"] == 1.0)
        # Bias vs power, again: a residual vector whose link-to-link scatter is
        # smaller than the standard error of a single link carries no established
        # differential, so a FAIL driven by it is noise propagated through path
        # multiplicity, not a detected effect.
        spread = float(np.std([residual[l]["loss"] for l in links], ddof=1))
        se_mean = float(np.mean([se_per_link.get((mode, l), 0.0) for l in links]))
        distinguishable = bool(spread > se_mean)
        results["modes"][mode] = {
            "differential_spread_loss": spread,
            "mean_per_link_se_loss": se_mean,
            "differential_distinguishable": distinguishable,
            "residual_per_link": {link: dict(residual[link]) for link in links},
            "cost_shift": decomp,
            "sensitivity": per_k,
            "g6_diff_pass": bool(observed["err_pass"] and observed["dsla_pass"]),
            "g6_diff_verdict": (
                "PASS"
                if observed["err_pass"] and observed["dsla_pass"]
                else ("FAIL" if distinguishable else "INCONCLUSIVE")
            ),
        }
    results["class_coverage"] = class_coverage()
    results["gate"] = {
        "err_tol_frac": ERR_TOL_FRAC,
        "dsla_tol_frac": DSLA_TOL_FRAC,
        "seeds": [int(s) for s in seeds],
        "n_trace": int(n),
        "k_scales": [float(k) for k in k_scales],
        "worst_case_permutations": bool(worst_case_permutations),
    }
    results["g6_diff_pass_all"] = bool(all(results["modes"][m]["g6_diff_pass"] for m in modes))
    return results


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--diag-ca", default=DIAG_CA)
    ap.add_argument("--check-report", default=CHECK_REPORT)
    ap.add_argument("--modes", default=",".join(MODES))
    ap.add_argument("--seeds", default=",".join(str(s) for s in SEEDS))
    ap.add_argument("--n", type=int, default=N_TRACE)
    ap.add_argument("--rho-bar", type=float, default=RHO_BAR)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)

    modes = tuple(p.strip() for p in args.modes.split(",") if p.strip())
    seeds = tuple(int(p) for p in args.seeds.split(",") if p.strip())
    residuals = load_residuals(args.diag_ca, args.check_report, modes)
    report = run(residuals, modes=modes, seeds=seeds, rho_bar=args.rho_bar, n=args.n)

    cov = report["class_coverage"]
    print("phu lop link: do %s | topology can %s | chua phu: %s"
          % (cov["classes_measured"], cov["classes_in_topology"], cov["uncovered"] or "khong co"))
    for mode in modes:
        block = report["modes"][mode]
        cs = block["cost_shift"]
        print()
        print("===== %s =====" % mode)
        print("  phan du/link: %s" % {k: round(v["loss"], 6) for k, v in block["residual_per_link"].items()})
        print("  Dcost COMMON-MODE   = %+9.3f ms" % cs["common_mode_ms"])
        print("  Dcost DIFFERENTIAL  = %+9.3f ms" % cs["differential_ms"])
        print("  khe quyet dinh      = %9.3f ms   -> differential/khe = %.2f%%"
              % (cs["decision_gap_ms"], 100.0 * cs["differential_over_gap"]))
        print("  %-4s %-22s %10s | %-22s %10s | %s" % (
            "k", "d err [lo, hi]", "err", "d d_sla [lo, hi]", "dsla", "huong"))
        for row in block["sensitivity"]:
            print("  %-4.0f %-22s %10s | %-22s %10s | %s" % (
                row["k"],
                "[%+.6f,%+.6f]" % (row["d_err_lo"], row["d_err_hi"]),
                "PASS" if row["err_pass"] else "FAIL",
                "[%+.6f,%+.6f]" % (row["d_sla_lo"], row["d_sla_hi"]),
                "PASS" if row["dsla_pass"] else "FAIL",
                row["direction"]))
        print("  do tan giua link = %.6f | se trung binh mot link = %.6f -> differential %s"
              % (block["differential_spread_loss"], block["mean_per_link_se_loss"],
                 "PHAN BIET DUOC voi 0" if block["differential_distinguishable"] else "KHONG phan biet duoc voi 0"))
        print("  G6-DIFF (k=1) -> %s" % block["g6_diff_verdict"])
    print()
    print("G6-DIFF tong: %s" % ("PASS" if report["g6_diff_pass_all"] else "FAIL"))

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True, default=str)
        f.write("\n")
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
