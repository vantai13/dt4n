#!/usr/bin/env python3
"""Phase T / T.6 -- blinded err_qs analysis.

This file is written before opening the real sealed Phase T response metrics.
All confirmatory choices are fixed here and exercised on fake sealed data first.

A13.1: report err_qs both raw and corrected.
A13.2: Delta_hat = 0.0158 ms, estimated only from C' controls.
A13.3: SE(Delta_hat) = 0.0023 ms, added as a system component.
A14.6: also report the homogeneous subset n_late_ratio < 1e-3.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from measurements.t4_validate import classify_err_qs, decompose
from measurements.t5_campaign import (
    BW,
    MODEL_PATH,
    Q,
    SEALED,
    STATE,
    make_traj,
)
from twin.link_model_v2 import LinkModelV2


DELTA_HAT_MS = 0.0158
DELTA_SE_MS = 0.0023
HOMOGENEOUS_N_LATE_MAX = 1e-3
CONTROL_STATE = "results/phase-T/control_state.json"
SCRIPT_VERSION = "t6_analyze_v4_t6e_paired"

# From docs/phase-T/01-two-timescales.md, locked before T.6b.
T_RELAX_P90_S = {
    ("h2", 0.700): 0.110,
    ("h2", 0.850): 0.104,
    ("h2", 0.925): 0.097,
    ("h2", 0.980): 0.123,
    ("poisson", 0.700): 0.090,
    ("poisson", 0.850): 0.194,
    ("poisson", 0.925): 0.274,
    ("poisson", 0.980): 0.300,
    ("cbr", 0.980): 0.879,
}


Row = Dict[str, Any]
Cell = Tuple[str, float]


def _mean(xs: Sequence[float]) -> float:
    return sum(float(x) for x in xs) / len(xs)


def _sd(xs: Sequence[float]) -> float | None:
    if len(xs) <= 1:
        return None
    m = _mean(xs)
    return math.sqrt(sum((float(x) - m) ** 2 for x in xs) / (len(xs) - 1))


def _se_mean(xs: Sequence[float]) -> float | None:
    sd = _sd(xs)
    return sd / math.sqrt(len(xs)) if sd is not None else None


def _pctl(xs: Sequence[float], q: float) -> float | None:
    if not xs:
        return None
    vals = sorted(float(x) for x in xs)
    k = int(math.ceil(float(q) * len(vals))) - 1
    return vals[min(max(k, 0), len(vals) - 1)]


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _number_summary(values: Iterable[Any]) -> Dict[str, Any]:
    xs = [float(x) for x in values if _finite(x)]
    if not xs:
        return {
            "n": 0,
            "mean": None,
            "sd": None,
            "se_mean": None,
            "min": None,
            "p05": None,
            "p50": None,
            "p95": None,
            "max": None,
        }
    return {
        "n": len(xs),
        "mean": _mean(xs),
        "sd": _sd(xs),
        "se_mean": _se_mean(xs),
        "min": min(xs),
        "p05": _pctl(xs, 0.05),
        "p50": _pctl(xs, 0.50),
        "p95": _pctl(xs, 0.95),
        "max": max(xs),
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _load_state_rows(path: str) -> List[Row]:
    with open(path, "r", encoding="utf-8") as f:
        state = json.load(f)
    rows = list(state.get("rows", []))
    rows.sort(key=lambda row: int(row["idx"]))
    return rows


def _load_sealed(pid: str, sealed_dir: str) -> Row:
    path = os.path.join(sealed_dir, pid + ".json")
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if str(payload.get("pid")) != str(pid):
        raise ValueError("%s: pid mismatch" % path)
    sealed = payload.get("sealed")
    if not isinstance(sealed, dict):
        raise ValueError("%s: missing sealed object" % path)
    if "q_mean_ms" not in sealed:
        raise ValueError("%s: sealed object missing q_mean_ms" % path)
    return dict(sealed)


def combine_rows(public_rows: Sequence[Row], sealed_dir: str) -> List[Row]:
    rows: List[Row] = []
    missing: List[str] = []
    for row in public_rows:
        pid = str(row["pid"])
        try:
            sealed = _load_sealed(pid, sealed_dir)
        except FileNotFoundError:
            missing.append(pid)
            continue
        combined = dict(row)
        combined.update(sealed)
        rows.append(combined)
    if missing:
        raise FileNotFoundError(
            "missing sealed rows: %d, first=%s" % (len(missing), missing[0])
        )
    return rows


def _core_terms(row: Mapping[str, Any], model: LinkModelV2) -> Row:
    traj = make_traj(dict(row))
    mode = str(row["mode"])
    bw = float(row.get("bw", BW))
    q = int(row.get("q", Q))
    rho_bar = float(row["rho_bar"])
    sigma_ref = model.sigma(mode, bw, q, rho_bar)
    dec = decompose(model, mode, bw, q, traj, float(row["q_mean_ms"]))

    err_raw = float(dec["err_qs_ms"])
    se_raw = float(dec["se_err_qs_ms"])
    err_corrected = err_raw - DELTA_HAT_MS
    se_corrected = math.sqrt(se_raw * se_raw + DELTA_SE_MS * DELTA_SE_MS)

    return {
        "q_psa_load_ms": dec["q_psa_load_ms"],
        "q_psa_time_ms": dec["q_psa_time_ms"],
        "q_ssa_ms": dec["q_ssa_ms"],
        "err_qs_raw_ms": err_raw,
        "err_qs_corrected_ms": err_corrected,
        "err_jensen_ms": dec["err_jensen_ms"],
        "d_sampling_ms": dec["d_sampling_ms"],
        "err_total_ms": dec["err_total_ms"],
        "se_err_qs_raw_ms": se_raw,
        "se_err_qs_corrected_ms": se_corrected,
        "n_pkt_model": dec["n_pkt"],
        "sigma_ref_ms": sigma_ref,
        "err_qs_raw_class": classify_err_qs(err_raw, sigma_ref, se_raw),
        "err_qs_corrected_class": classify_err_qs(
            err_corrected, sigma_ref, se_corrected
        ),
        "err_qs_corrected_z": err_corrected / max(se_corrected, 1e-12),
        "homogeneous_a14": float(row.get("n_late_ratio", 0.0))
        < HOMOGENEOUS_N_LATE_MAX,
        "trajectory_rho_mean": _mean(traj.rho),
        "trajectory_rho_min": min(traj.rho),
        "trajectory_rho_max": max(traj.rho),
        "trajectory_clamp_ratio": traj.clamp_ratio,
    }


def analyze_rows(rows: Sequence[Row], model: LinkModelV2) -> List[Row]:
    out: List[Row] = []
    for row in rows:
        enriched = dict(row)
        enriched.update(_core_terms(row, model))
        out.append(enriched)
    return out


def _cell(row: Mapping[str, Any]) -> Cell:
    return str(row["mode"]), round(float(row["rho_bar"]), 3)


def baseline_from_controls(rows: Sequence[Row]) -> Dict[Cell, Row]:
    grouped: Dict[Cell, List[Row]] = defaultdict(list)
    for row in rows:
        if abs(float(row.get("a", 0.0))) > 1e-12:
            continue
        grouped[_cell(row)].append(row)
    out: Dict[Cell, Row] = {}
    for cell, values in grouped.items():
        errs = [float(row["err_qs_corrected_ms"]) for row in values]
        sd = _sd(errs)
        out[cell] = {
            "mode": cell[0],
            "rho_bar": cell[1],
            "n_C": len(values),
            "baseline_C_ms": _mean(errs),
            "sd_C_ms": sd,
            "se_C_ms": sd / math.sqrt(len(errs)) if sd is not None else 0.0,
            "idx_C": [int(row["idx"]) for row in sorted(values, key=lambda r: int(r["idx"]))],
        }
    return out


def apply_baseline(rows: Sequence[Row], baseline: Mapping[Cell, Row]) -> List[Row]:
    out: List[Row] = []
    for row in rows:
        enriched = dict(row)
        cell = _cell(row)
        base = baseline.get(cell)
        if base is None:
            out.append(enriched)
            continue
        baseline_mean = float(base["baseline_C_ms"])
        baseline_se = float(base["se_C_ms"])
        err_dyn = float(row["err_qs_corrected_ms"]) - baseline_mean
        se_dyn = math.sqrt(
            float(row["se_err_qs_corrected_ms"]) ** 2 + baseline_se**2
        )
        enriched.update(
            {
                "baseline_cell": "mode=%s,rho_bar=%g" % cell,
                "baseline_C_ms": baseline_mean,
                "se_C_ms": baseline_se,
                "err_dyn_ms": err_dyn,
                "se_err_dyn_ms": se_dyn,
                "err_dyn_z": err_dyn / max(se_dyn, 1e-12),
                "err_dyn_class": classify_err_qs(
                    err_dyn, float(row["sigma_ref_ms"]), se_dyn
                ),
            }
        )
        out.append(enriched)
    return out


def _lambda_p90(row: Mapping[str, Any]) -> float | None:
    key = _cell(row)
    t_relax = T_RELAX_P90_S.get(key)
    if t_relax is None:
        return None
    return float(row["tau_rho"]) / t_relax


def _group_key(row: Mapping[str, Any], keys: Sequence[str]) -> str:
    parts = []
    for key in keys:
        value = row.get(key)
        if isinstance(value, float):
            value = "%g" % value
        parts.append("%s=%s" % (key, value))
    return ",".join(parts)


def summarize_rows(rows: Sequence[Row]) -> Dict[str, Any]:
    class_raw = Counter(str(row["err_qs_raw_class"]) for row in rows)
    class_corrected = Counter(str(row["err_qs_corrected_class"]) for row in rows)
    class_dyn = Counter(
        str(row["err_dyn_class"]) for row in rows if "err_dyn_class" in row
    )
    commits = Counter(
        str(row.get("env", {}).get("git_commit", "unknown"))[:8] for row in rows
    )
    out = {
        "n": len(rows),
        "err_qs_raw_ms": _number_summary(row["err_qs_raw_ms"] for row in rows),
        "err_qs_corrected_ms": _number_summary(
            row["err_qs_corrected_ms"] for row in rows
        ),
        "err_qs_corrected_z": _number_summary(
            row["err_qs_corrected_z"] for row in rows
        ),
        "err_jensen_ms": _number_summary(row["err_jensen_ms"] for row in rows),
        "d_sampling_ms": _number_summary(row["d_sampling_ms"] for row in rows),
        "q_mean_ms": _number_summary(row["q_mean_ms"] for row in rows),
        "loss": _number_summary(row.get("loss") for row in rows),
        "n_late_ratio": _number_summary(row.get("n_late_ratio") for row in rows),
        "class_raw": dict(sorted(class_raw.items())),
        "class_corrected": dict(sorted(class_corrected.items())),
        "commits": dict(sorted(commits.items())),
    }
    if class_dyn:
        out.update(
            {
                "err_dyn_ms": _number_summary(row.get("err_dyn_ms") for row in rows),
                "err_dyn_z": _number_summary(row.get("err_dyn_z") for row in rows),
                "class_dyn": dict(sorted(class_dyn.items())),
            }
        )
    return out


def grouped_summary(rows: Sequence[Row], keys: Sequence[str]) -> Dict[str, Any]:
    grouped: Dict[str, List[Row]] = defaultdict(list)
    for row in rows:
        grouped[_group_key(row, keys)].append(row)
    return {
        key: summarize_rows(grouped[key])
        for key in sorted(grouped)
    }


def baseline_cell_table(
    rows: Sequence[Row],
    baseline: Mapping[Cell, Row],
) -> List[Row]:
    regular = [row for row in rows if str(row.get("block")) != "S"]
    grouped: Dict[Cell, List[Row]] = defaultdict(list)
    for row in regular:
        grouped[_cell(row)].append(row)

    out: List[Row] = []
    for cell in sorted(baseline):
        main = grouped.get(cell, [])
        dyn = [row.get("err_dyn_ms") for row in main]
        corrected = [row.get("err_qs_corrected_ms") for row in main]
        se_batch = [row.get("se_batch_ms") for row in main]
        se_naive = [row.get("se_naive_ms") for row in main]
        item = dict(baseline[cell])
        item.update(
            {
                "n_main": len(main),
                "mean_err_qs_corrected_ms": _number_summary(corrected)["mean"],
                "mean_abs_err_qs_corrected_ms": _number_summary(
                    abs(float(x)) for x in corrected if _finite(x)
                )["mean"],
                "mean_err_dyn_ms": _number_summary(dyn)["mean"],
                "mean_abs_err_dyn_ms": _number_summary(
                    abs(float(x)) for x in dyn if _finite(x)
                )["mean"],
                "sd_err_dyn_ms": _number_summary(dyn)["sd"],
                "mean_se_batch_ms": _number_summary(se_batch)["mean"],
                "mean_se_naive_ms": _number_summary(se_naive)["mean"],
                "class_dyn": dict(
                    sorted(
                        Counter(
                            str(row.get("err_dyn_class"))
                            for row in main
                            if "err_dyn_class" in row
                        ).items()
                    )
                ),
            }
        )
        out.append(item)
    return out


def _wilcoxon_exact_two_sided_p(values: Sequence[float]) -> Dict[str, Any]:
    """Exact signed-rank p-value for n small, using ranks 1..n without ties."""
    vals = [float(x) for x in values if float(x) != 0.0]
    n = len(vals)
    order = sorted(range(n), key=lambda i: abs(vals[i]))
    ranks = [0] * n
    for rank, i in enumerate(order, 1):
        ranks[i] = rank
    w_plus = sum(rank for rank, value in zip(ranks, vals) if value > 0.0)
    total = n * (n + 1) // 2
    extreme = min(w_plus, total - w_plus)
    count = 0
    for mask in range(1 << n):
        wp = 0
        for i, rank in enumerate(ranks):
            if mask & (1 << i):
                wp += rank
        if min(wp, total - wp) <= extreme:
            count += 1
    return {
        "n": n,
        "w_plus": w_plus,
        "w_minus": total - w_plus,
        "p_two_sided_exact": count / float(1 << n),
    }


def _sign_test_two_sided_p(neg: int, n: int) -> float:
    extreme = min(int(neg), int(n) - int(neg))
    tail = sum(math.comb(int(n), k) for k in range(extreme + 1)) / float(1 << int(n))
    return min(1.0, 2.0 * tail)


def cell_level_test(cells: Sequence[Row]) -> Dict[str, Any]:
    """A17 -- test D-T2 at the cell level, not the point level.

    This supplements, and does not replace, the original per-point T.6 result.
    The analysis is exploratory under docs/phase-T/00r-amendment-17.md.
    """
    reg: List[Row] = []
    cbr: List[Row] = []
    for item in cells:
        cell = dict(item)
        n = int(cell["n_main"])
        sd_dyn = float(cell["sd_err_dyn_ms"])
        se_c = float(cell["se_C_ms"])
        se_stat = sd_dyn / math.sqrt(n)
        se_tot = math.sqrt(se_stat * se_stat + se_c * se_c)
        mean_dyn = float(cell["mean_err_dyn_ms"])
        cell.update(
            {
                "n": n,
                "rho": float(cell["rho_bar"]),
                "mean_dyn": mean_dyn,
                "sd_dyn": sd_dyn,
                "se_C": se_c,
                "se_stat": se_stat,
                "se_tot": se_tot,
                "t": mean_dyn / max(se_tot, 1e-12),
                "ub95": abs(mean_dyn) + 1.96 * se_tot,
            }
        )
        if str(cell["mode"]) == "cbr":
            cbr.append(cell)
        else:
            reg.append(cell)

    w = [1.0 / max(float(cell["se_tot"]) ** 2, 1e-24) for cell in reg]
    mu_w = sum(wi * float(cell["mean_dyn"]) for wi, cell in zip(w, reg)) / sum(w)
    se_w = 1.0 / math.sqrt(sum(w))

    means = [float(cell["mean_dyn"]) for cell in reg]
    n_reg = len(means)
    mu = _mean(means)
    sd = _sd(means)
    se = (sd / math.sqrt(n_reg)) if sd is not None else None
    t975_df7 = 2.365
    neg = sum(1 for value in means if value < 0.0)
    wilcoxon = _wilcoxon_exact_two_sided_p(means)
    pred = math.sqrt(_mean([float(cell["se_tot"]) ** 2 for cell in reg]))
    ratio = pred / max(float(sd), 1e-12)

    cbr_out = []
    for cell in cbr:
        se_batch = float(cell.get("mean_se_batch_ms", 0.0))
        excess = math.sqrt(max(float(cell["sd_dyn"]) ** 2 - se_batch**2, 0.0))
        cbr_out.append(
            {
                "mode": cell["mode"],
                "rho": cell["rho"],
                "mean": cell["mean_dyn"],
                "sd_dyn": cell["sd_dyn"],
                "se_batch": se_batch,
                "se_tot": cell["se_tot"],
                "t": cell["t"],
                "ub95": cell["ub95"],
                "du_vuot_nhieu_do": excess,
            }
        )

    t_cells = [
        {
            "mode": cell["mode"],
            "rho": cell["rho"],
            "mean_dyn": cell["mean_dyn"],
            "se_stat": cell["se_stat"],
            "se_C": cell["se_C"],
            "se_tot": cell["se_tot"],
            "t": cell["t"],
            "ub95": cell["ub95"],
        }
        for cell in reg + cbr
    ]

    return {
        "status": "exploratory_A17",
        "cell_table": t_cells,
        "bao_thu": {
            "mean": mu_w,
            "se": se_w,
            "t": mu_w / max(se_w, 1e-12),
            "ci95": [mu_w - 1.96 * se_w, mu_w + 1.96 * se_w],
            "ub_o_xau_nhat": max(float(cell["ub95"]) for cell in reg),
        },
        "thuc_nghiem": {
            "mean": mu,
            "sd_giua_o": sd,
            "se": se,
            "t": mu / max(float(se), 1e-12) if se is not None else None,
            "df": n_reg - 1,
            "ci95": [
                mu - t975_df7 * float(se),
                mu + t975_df7 * float(se),
            ]
            if se is not None
            else None,
        },
        "phi_tham_so": {
            "am": neg,
            "duong": n_reg - neg,
            "sign_test_p": _sign_test_two_sided_p(neg, n_reg),
            "wilcoxon_w_plus": wilcoxon["w_plus"],
            "wilcoxon_w_minus": wilcoxon["w_minus"],
            "wilcoxon_p_two_sided_exact": wilcoxon["p_two_sided_exact"],
        },
        "mau_thuan_SE": {
            "tan_du_doan": pred,
            "tan_quan_sat": sd,
            "ti_so": ratio,
            "canh_bao": ratio > 2.0,
        },
        "cbr_tach_rieng": cbr_out,
    }


def paired_cell_rows(main_rows: Sequence[Row], control_rows: Sequence[Row]) -> List[Row]:
    """A18 -- compute paired-by-seed dynamic error rows.

    The main campaign and C controls use the same seed set. Pairing first
    removes the schedule component shared by both sides, then estimates the
    cell error bar from the five seed-level differences.
    """
    main: Dict[Tuple[str, float, int], List[float]] = defaultdict(list)
    for row in main_rows:
        if str(row.get("block")) == "S" or int(row.get("seed", -1)) == 999:
            continue
        key = (str(row["mode"]), round(float(row["rho_bar"]), 3), int(row["seed"]))
        main[key].append(float(row["err_qs_corrected_ms"]))

    ctrl: Dict[Tuple[str, float, int], List[float]] = defaultdict(list)
    for row in control_rows:
        if abs(float(row.get("a", 0.0))) > 1e-12:
            continue
        key = (str(row["mode"]), round(float(row["rho_bar"]), 3), int(row["seed"]))
        ctrl[key].append(float(row["err_qs_corrected_ms"]))

    cells = sorted({(mode, rho) for mode, rho, _seed in ctrl})
    out: List[Row] = []
    for mode, rho in cells:
        paired = []
        seed_rows = []
        for seed in sorted({s for m, r, s in ctrl if m == mode and r == rho}):
            key = (mode, rho, seed)
            if key not in main or key not in ctrl:
                continue
            main_mean = _mean(main[key])
            ctrl_mean = _mean(ctrl[key])
            diff = main_mean - ctrl_mean
            paired.append(diff)
            seed_rows.append(
                {
                    "seed": seed,
                    "n_main": len(main[key]),
                    "n_control": len(ctrl[key]),
                    "mean_main_ms": main_mean,
                    "control_ms": ctrl_mean,
                    "diff_ms": diff,
                }
            )
        if len(paired) != 5:
            raise ValueError(
                "T6e paired cell %s@%g needs 5 seeds, got %d"
                % (mode, rho, len(paired))
            )
        if any(int(item["n_main"]) != 6 for item in seed_rows):
            raise ValueError("T6e paired cell %s@%g needs 6 main rows/seed" % (mode, rho))
        if any(int(item["n_control"]) != 1 for item in seed_rows):
            raise ValueError("T6e paired cell %s@%g needs 1 control row/seed" % (mode, rho))

        sd = _sd(paired)
        se = float(sd) / math.sqrt(len(paired)) if sd is not None else 0.0
        mu = _mean(paired)
        t975 = 2.776  # df = 4
        out.append(
            {
                "mode": mode,
                "rho": rho,
                "rho_bar": rho,
                "n_seed": len(paired),
                "mean_dyn": mu,
                "sd_paired": sd,
                "se_paired": se,
                "t_paired": mu / max(se, 1e-12),
                "df": len(paired) - 1,
                "ci95": [mu - t975 * se, mu + t975 * se],
                "seed_rows": seed_rows,
            }
        )
    return out


def assert_paired_mean_invariant(
    paired: Sequence[Row],
    t6d_cells: Sequence[Row],
    tol: float = 1e-9,
) -> Dict[str, Any]:
    """A18 guard: pairing may change error bars, never the point estimate."""
    ref = {
        (str(row["mode"]), round(float(row["rho_bar"]), 3)): float(
            row["mean_err_dyn_ms"]
        )
        for row in t6d_cells
    }
    diffs = []
    for row in paired:
        key = (str(row["mode"]), round(float(row["rho"]), 3))
        if key not in ref:
            raise ValueError("missing T6d reference cell for %s@%g" % key)
        diff = abs(float(row["mean_dyn"]) - ref[key])
        row["mean_dyn_t6d_reference_ms"] = ref[key]
        row["mean_dyn_abs_diff_ms"] = diff
        diffs.append(diff)
        if diff > float(tol):
            raise ValueError(
                "%s@%g: paired changed mean_dyn by %.12g"
                % (key[0], key[1], diff)
            )
    return {
        "tol": float(tol),
        "max_abs_diff_ms": max(diffs) if diffs else 0.0,
        "pass": all(diff <= float(tol) for diff in diffs),
    }


def paired_cell_test(paired: Sequence[Row]) -> Dict[str, Any]:
    """A18 -- summarize paired-by-seed cell error bars."""
    reg = [row for row in paired if str(row["mode"]) != "cbr"]
    cbr = [row for row in paired if str(row["mode"]) == "cbr"]

    se_values = [float(row["se_paired"]) for row in reg]
    means = [float(row["mean_dyn"]) for row in reg]
    sd_means = _sd(means)
    pred = math.sqrt(_mean([se * se for se in se_values]))
    ratio = pred / max(float(sd_means), 1e-12)
    n_t = sum(abs(float(row["t_paired"])) > 2.0 for row in reg)

    w = [1.0 / max(float(row["se_paired"]) ** 2, 1e-24) for row in reg]
    mu_w = sum(wi * float(row["mean_dyn"]) for wi, row in zip(w, reg)) / sum(w)
    se_w = 1.0 / math.sqrt(sum(w))

    mu = _mean(means)
    se_emp = float(sd_means) / math.sqrt(len(means))
    t975_df7 = 2.365

    abs_mean_by_cell = {
        "mode=%s,rho_bar=%g" % (row["mode"], float(row["rho"])): abs(float(row["mean_dyn"]))
        for row in paired
    }
    strongest = max(abs_mean_by_cell, key=lambda key: abs_mean_by_cell[key])

    return {
        "status": "exploratory_A18",
        "cell_table": list(paired),
        "R1_SE_paired": {
            "mean": _mean(se_values),
            "range_target_ms": [0.015, 0.030],
            "pass": 0.015 <= _mean(se_values) <= 0.030,
            "summary": _number_summary(se_values),
        },
        "R2_mau_thuan": {
            "tan_du_doan": pred,
            "tan_quan_sat": sd_means,
            "ti_so": ratio,
            "target": [0.7, 1.5],
            "pass": 0.7 <= ratio <= 1.5 and ratio < 2.0,
        },
        "R3_abs_t_gt_2": {
            "observed": n_t,
            "denominator": len(reg),
            "target": [6, 8],
            "pass": 6 <= n_t <= 8,
        },
        "R4_mean_gop": {
            "weighted_mean": mu_w,
            "weighted_se": se_w,
            "weighted_t": mu_w / max(se_w, 1e-12),
            "weighted_ci95": [mu_w - 1.96 * se_w, mu_w + 1.96 * se_w],
            "unweighted_mean": mu,
            "unweighted_se": se_emp,
            "unweighted_t": mu / max(se_emp, 1e-12),
            "unweighted_ci95": [
                mu - t975_df7 * se_emp,
                mu + t975_df7 * se_emp,
            ],
        },
        "R5_cbr_manh_nhat": {
            "observed_largest_cell": strongest,
            "pass": strongest == "mode=cbr,rho_bar=0.98",
            "abs_mean_by_cell_ms": abs_mean_by_cell,
        },
        "cbr_tach_rieng": list(cbr),
    }


def t6b_diagnostics(rows: Sequence[Row]) -> Dict[str, Any]:
    regular = [
        row
        for row in rows
        if str(row.get("block")) != "S" and "err_dyn_ms" in row
    ]
    hp = [row for row in regular if str(row.get("mode")) != "cbr"]
    for row in regular:
        row["lambda_p90"] = _lambda_p90(row)

    d2_rows = [
        row
        for row in hp
        if row.get("lambda_p90") is not None and float(row["lambda_p90"]) >= 10.0
    ]
    ratios = [
        abs(float(row["err_dyn_ms"])) / max(float(row["sigma_ref_ms"]), 1e-12)
        for row in d2_rows
    ]

    bands = (
        ("Lambda<3", lambda row: float(row["lambda_p90"]) < 3.0),
        (
            "3<=Lambda<10",
            lambda row: 3.0 <= float(row["lambda_p90"]) < 10.0,
        ),
        ("Lambda>=10", lambda row: float(row["lambda_p90"]) >= 10.0),
    )
    band_rows: Dict[str, List[Row]] = {}
    band_summary: Dict[str, Any] = {}
    for name, pred in bands:
        selected = [
            row for row in hp if row.get("lambda_p90") is not None and pred(row)
        ]
        band_rows[name] = selected
        vals = [abs(float(row["err_dyn_ms"])) for row in selected]
        band_summary[name] = {
            "n": len(selected),
            "mean_abs_err_dyn_ms": _number_summary(vals)["mean"],
            "median_abs_err_dyn_ms": _number_summary(vals)["p50"],
        }

    dynamic = band_rows["Lambda<3"]
    dyn_vals = [float(row["err_dyn_ms"]) for row in dynamic]
    mode_cell_abs = {
        "mode=%s,rho_bar=%g" % key: _number_summary(
            abs(float(row["err_dyn_ms"])) for row in values
        )
        for key, values in sorted(
            _group_by_cell(regular).items(), key=lambda item: item[0]
        )
    }
    cell_means = {
        key: value["mean"]
        for key, value in mode_cell_abs.items()
        if value.get("mean") is not None
    }
    largest_cell = max(cell_means, key=lambda key: float(cell_means[key])) if cell_means else None
    means = [band_summary[name]["mean_abs_err_dyn_ms"] for name, _ in bands]
    p2_pass = all(x is not None for x in means) and means[0] > means[1] > means[2]
    class_dyn = Counter(str(row.get("err_dyn_class")) for row in regular)
    mean_abs_hp = _number_summary(abs(float(row["err_dyn_ms"])) for row in hp)

    return {
        "D-T2_err_dyn_Lambda_ge_10": {
            "n": len(d2_rows),
            "pass_abs_ratio_lt_0p1": sum(ratio < 0.10 for ratio in ratios),
            "fail_abs_ratio_ge_0p1": sum(ratio >= 0.10 for ratio in ratios),
            "abs_ratio": _number_summary(ratios),
        },
        "D-T3_err_dyn_by_Lambda": band_summary,
        "D-T3_monotonic_P2_pass": bool(p2_pass),
        "D-T4_err_dyn_dynamic_sign": {
            "n": len(dyn_vals),
            "mean": _number_summary(dyn_vals)["mean"],
            "median": _number_summary(dyn_vals)["p50"],
            "neg": sum(x < 0.0 for x in dyn_vals),
            "pos": sum(x > 0.0 for x in dyn_vals),
        },
        "P1_mean_abs_err_dyn_h2_poisson": {
            "threshold_ms": 0.140,
            "observed_ms": mean_abs_hp["mean"],
            "pass": mean_abs_hp["mean"] is not None and mean_abs_hp["mean"] <= 0.140,
        },
        "P3_quasi_static_khong_dung": {
            "threshold": 80,
            "observed": class_dyn.get("quasi_static_khong_dung", 0),
            "pass": class_dyn.get("quasi_static_khong_dung", 0) <= 80,
        },
        "P4_cbr_0p98_largest": {
            "observed_largest_cell": largest_cell,
            "observed_mean_abs_ms": cell_means.get("mode=cbr,rho_bar=0.98"),
            "pass": largest_cell == "mode=cbr,rho_bar=0.98",
        },
        "mode_cell_abs_err_dyn_ms": mode_cell_abs,
    }


def _group_by_cell(rows: Sequence[Row]) -> Dict[Cell, List[Row]]:
    grouped: Dict[Cell, List[Row]] = defaultdict(list)
    for row in rows:
        grouped[_cell(row)].append(row)
    return grouped


def sentinel_summary(rows: Sequence[Row]) -> Dict[str, Any]:
    sentinels = [row for row in rows if str(row.get("block")) == "S"]
    if not sentinels:
        return {"n": 0}
    return {
        "n": len(sentinels),
        "idx": [int(row["idx"]) for row in sentinels],
        "schedule_digests": sorted(
            {str(row.get("schedule_digest", "")) for row in sentinels}
        ),
        "loss": _number_summary(row.get("loss") for row in sentinels),
        "n_recv_unique": _number_summary(row.get("n_recv_unique") for row in sentinels),
        "n_late_ratio": _number_summary(row.get("n_late_ratio") for row in sentinels),
        "q_mean_ms": _number_summary(row.get("q_mean_ms") for row in sentinels),
        "err_qs_corrected_ms": _number_summary(
            row.get("err_qs_corrected_ms") for row in sentinels
        ),
    }


def build_report(
    rows: Sequence[Row],
    state_path: str,
    sealed_dir: str,
    baseline_state: str | None = None,
    baseline_dir: str | None = None,
    baseline_rows: Sequence[Row] | None = None,
    baseline: Mapping[Cell, Row] | None = None,
    cell_level: bool = False,
    paired: bool = False,
) -> Dict[str, Any]:
    regular = [row for row in rows if str(row.get("block")) != "S"]
    homogeneous = [
        row for row in regular if bool(row.get("homogeneous_a14", False))
    ]
    report = {
        "metadata": {
            "script_version": SCRIPT_VERSION,
            "state_path": state_path,
            "sealed_dir": sealed_dir,
            "baseline_state": baseline_state,
            "baseline_dir": baseline_dir,
            "delta_hat_ms": DELTA_HAT_MS,
            "delta_se_ms": DELTA_SE_MS,
            "homogeneous_n_late_max": HOMOGENEOUS_N_LATE_MAX,
            "model_path": MODEL_PATH,
            "confirmatory_note": (
                "Script locked and fake-tested before reading real sealed data."
            ),
            "t6b_note": (
                "Baseline subtraction is exploratory under Amendment 15."
                if baseline is not None
                else None
            ),
            "t6d_note": (
                "Cell-level D-T2 restatement is exploratory under Amendment 17."
                if cell_level
                else None
            ),
            "t6e_note": (
                "Paired-by-seed error bars are exploratory under Amendment 18."
                if paired
                else None
            ),
        },
        "counts": {
            "n_all": len(rows),
            "n_regular": len(regular),
            "n_sentinel": len(rows) - len(regular),
            "n_homogeneous_regular": len(homogeneous),
            "n_warn_n_late_regular": sum(
                1 for row in regular if bool(row.get("warn_n_late", False))
            ),
        },
        "summary_all_regular": summarize_rows(regular),
        "summary_homogeneous_regular": summarize_rows(homogeneous),
        "summary_by_mode": grouped_summary(regular, ("mode",)),
        "summary_by_mode_a_tau": grouped_summary(
            regular, ("mode", "a", "tau_rho")
        ),
        "summary_by_cell": grouped_summary(
            regular, ("mode", "rho_bar", "a", "tau_rho")
        ),
        "sentinel": sentinel_summary(rows),
        "rows": list(rows),
    }
    if baseline is not None:
        cells = baseline_cell_table(rows, baseline)
        report["counts"]["n_baseline_control"] = (
            len(baseline_rows) if baseline_rows is not None else None
        )
        report["baseline_cells"] = cells
        report["baseline_control_summary"] = grouped_summary(
            list(baseline_rows or []), ("mode", "rho_bar")
        )
        report["summary_dyn_by_mode"] = grouped_summary(regular, ("mode",))
        report["summary_dyn_by_cell"] = grouped_summary(
            regular, ("mode", "rho_bar")
        )
        report["t6b_diagnostics"] = t6b_diagnostics(list(rows))
        if cell_level:
            report["t6d_cell_level"] = cell_level_test(cells)
        if paired:
            if baseline_rows is None:
                raise ValueError("paired analysis needs baseline_rows")
            paired_rows = paired_cell_rows(rows, baseline_rows)
            report["t6e_invariance"] = assert_paired_mean_invariant(
                paired_rows, cells
            )
            report["t6e_paired"] = paired_cell_test(paired_rows)
    return report


def write_fake_sealed(public_rows: Sequence[Row], sealed_dir: str, model: LinkModelV2) -> None:
    os.makedirs(sealed_dir, exist_ok=True)
    for row in public_rows:
        base = _core_terms({**row, "q_mean_ms": 0.0}, model)["q_psa_load_ms"]
        idx = int(row["idx"])
        jitter = 0.004 * math.sin((idx + 1) * 1.61803398875)
        q_mean = max(0.0, base + DELTA_HAT_MS + jitter)
        spread = max(0.01, abs(q_mean) * 0.05)
        sealed = {
            "q_mean_ms": q_mean,
            "q_sd_ms": spread,
            "q_p50_ms": q_mean,
            "q_p90_ms": q_mean + 0.80 * spread,
            "q_p95_ms": q_mean + 1.10 * spread,
            "q_p99_ms": q_mean + 1.70 * spread,
            "se_batch_ms": max(DELTA_SE_MS, spread / 12.0),
            "se_naive_ms": max(DELTA_SE_MS / 2.0, spread / 40.0),
            "probe_mean_ms": q_mean - 0.002,
            "delta_pasta_ms": 0.002,
        }
        payload = {"pid": row["pid"], "sealed": sealed}
        path = os.path.join(sealed_dir, str(row["pid"]) + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_jsonable(payload), f, indent=1, sort_keys=True)


def _print_report_summary(report: Mapping[str, Any]) -> None:
    counts = report["counts"]
    all_reg = report["summary_all_regular"]["err_qs_corrected_ms"]
    homog = report["summary_homogeneous_regular"]["err_qs_corrected_ms"]
    sentinel = report["sentinel"]
    print(
        "T6 rows all=%d regular=%d sentinel=%d homogeneous_regular=%d"
        % (
            counts["n_all"],
            counts["n_regular"],
            counts["n_sentinel"],
            counts["n_homogeneous_regular"],
        )
    )
    print(
        "err_qs_corrected regular: n=%d mean=%+.6f ms sd=%s p50=%+.6f ms"
        % (
            all_reg["n"],
            float(all_reg["mean"]),
            "None" if all_reg["sd"] is None else "%.6f ms" % float(all_reg["sd"]),
            float(all_reg["p50"]),
        )
    )
    print(
        "err_qs_corrected homogeneous: n=%d mean=%+.6f ms sd=%s p50=%+.6f ms"
        % (
            homog["n"],
            float(homog["mean"]),
            "None" if homog["sd"] is None else "%.6f ms" % float(homog["sd"]),
            float(homog["p50"]),
        )
    )
    if sentinel.get("n"):
        loss = sentinel["loss"]
        q_mean = sentinel["q_mean_ms"]
        print(
            "sentinel: n=%d loss_mean=%.8f q_mean_mean=%.6f ms"
            % (
                sentinel["n"],
                float(loss["mean"]),
                float(q_mean["mean"]),
            )
        )
    if "baseline_cells" in report:
        print("")
        print("T6b baseline cells (exploratory):")
        print(
            "mode      rho    nC baseline_C  SE_C    n_main mean_err_qs  mean_err_dyn  sd_err_dyn"
        )
        for item in report["baseline_cells"]:
            print(
                "%-8s %.3f %3d %+10.6f %.6f %6d %+11.6f %+12.6f %11s"
                % (
                    item["mode"],
                    float(item["rho_bar"]),
                    int(item["n_C"]),
                    float(item["baseline_C_ms"]),
                    float(item["se_C_ms"]),
                    int(item["n_main"]),
                    float(item["mean_err_qs_corrected_ms"]),
                    float(item["mean_err_dyn_ms"]),
                    (
                        "None"
                        if item["sd_err_dyn_ms"] is None
                        else "%.6f" % float(item["sd_err_dyn_ms"])
                    ),
                )
            )
        diag = report["t6b_diagnostics"]
        d2 = diag["D-T2_err_dyn_Lambda_ge_10"]
        d3 = diag["D-T3_err_dyn_by_Lambda"]
        d4 = diag["D-T4_err_dyn_dynamic_sign"]
        print("")
        print(
            "T6b D-T2 err_dyn Lambda>=10: pass=%d/%d fail=%d mean_abs_ratio=%.6f"
            % (
                int(d2["pass_abs_ratio_lt_0p1"]),
                int(d2["n"]),
                int(d2["fail_abs_ratio_ge_0p1"]),
                float(d2["abs_ratio"]["mean"]),
            )
        )
        for name in ("Lambda<3", "3<=Lambda<10", "Lambda>=10"):
            item = d3[name]
            print(
                "T6b D-T3 %-14s n=%3d mean|err_dyn|=%.6f ms median=%.6f ms"
                % (
                    name,
                    int(item["n"]),
                    float(item["mean_abs_err_dyn_ms"]),
                    float(item["median_abs_err_dyn_ms"]),
                )
            )
        print("T6b D-T3 P2 monotonic pass=%s" % diag["D-T3_monotonic_P2_pass"])
        print(
            "T6b D-T4 Lambda<3: n=%d mean=%+.6f ms median=%+.6f ms neg=%d pos=%d"
            % (
                int(d4["n"]),
                float(d4["mean"]),
                float(d4["median"]),
                int(d4["neg"]),
                int(d4["pos"]),
            )
        )
        print("T6b P1 = %s" % diag["P1_mean_abs_err_dyn_h2_poisson"])
        print("T6b P3 = %s" % diag["P3_quasi_static_khong_dung"])
        print("T6b P4 = %s" % diag["P4_cbr_0p98_largest"])
    if "t6d_cell_level" in report:
        t6d = report["t6d_cell_level"]
        bt = t6d["bao_thu"]
        emp = t6d["thuc_nghiem"]
        nonp = t6d["phi_tham_so"]
        se = t6d["mau_thuan_SE"]
        print("")
        print("T6d cell-level D-T2 restatement (exploratory):")
        print(
            "bao_thu: mean=%+.6f ms se=%.6f t=%+.3f ci95=[%+.6f,%+.6f] ub_worst=%.6f"
            % (
                float(bt["mean"]),
                float(bt["se"]),
                float(bt["t"]),
                float(bt["ci95"][0]),
                float(bt["ci95"][1]),
                float(bt["ub_o_xau_nhat"]),
            )
        )
        print(
            "thuc_nghiem: mean=%+.6f ms sd=%.6f se=%.6f t=%+.3f ci95=[%+.6f,%+.6f]"
            % (
                float(emp["mean"]),
                float(emp["sd_giua_o"]),
                float(emp["se"]),
                float(emp["t"]),
                float(emp["ci95"][0]),
                float(emp["ci95"][1]),
            )
        )
        print(
            "phi_tham_so: am=%d duong=%d sign_p=%.7f wilcoxon_w+=%s wilcoxon_p=%.7f"
            % (
                int(nonp["am"]),
                int(nonp["duong"]),
                float(nonp["sign_test_p"]),
                nonp["wilcoxon_w_plus"],
                float(nonp["wilcoxon_p_two_sided_exact"]),
            )
        )
        print(
            "mau_thuan_SE: tan_du_doan=%.6f tan_quan_sat=%.6f ti_so=%.3f canh_bao=%s"
            % (
                float(se["tan_du_doan"]),
                float(se["tan_quan_sat"]),
                float(se["ti_so"]),
                se["canh_bao"],
            )
        )
        for item in t6d["cbr_tach_rieng"]:
            print(
                "cbr_tach_rieng: rho=%.3f mean=%+.6f se_tot=%.6f t=%+.3f ub95=%.6f du_vuot_nhieu_do=%.6f"
                % (
                    float(item["rho"]),
                    float(item["mean"]),
                    float(item["se_tot"]),
                    float(item["t"]),
                    float(item["ub95"]),
                    float(item["du_vuot_nhieu_do"]),
                )
            )
    if "t6e_paired" in report:
        inv = report["t6e_invariance"]
        t6e = report["t6e_paired"]
        print("")
        print("T6e paired-by-seed error bars (exploratory):")
        print(
            "invariance: pass=%s max_abs_diff=%.12g ms tol=%.1e"
            % (
                inv["pass"],
                float(inv["max_abs_diff_ms"]),
                float(inv["tol"]),
            )
        )
        print(
            "mode      rho    n_seed mean_dyn   se_paired t_paired ci95_lo  ci95_hi"
        )
        for item in t6e["cell_table"]:
            print(
                "%-8s %.3f %6d %+9.6f %.6f %+8.3f %+8.6f %+8.6f"
                % (
                    item["mode"],
                    float(item["rho"]),
                    int(item["n_seed"]),
                    float(item["mean_dyn"]),
                    float(item["se_paired"]),
                    float(item["t_paired"]),
                    float(item["ci95"][0]),
                    float(item["ci95"][1]),
                )
            )
        r1 = t6e["R1_SE_paired"]
        r2 = t6e["R2_mau_thuan"]
        r3 = t6e["R3_abs_t_gt_2"]
        r4 = t6e["R4_mean_gop"]
        r5 = t6e["R5_cbr_manh_nhat"]
        print(
            "T6e R1 mean_SE_paired=%.6f pass=%s"
            % (float(r1["mean"]), r1["pass"])
        )
        print(
            "T6e R2 tan_du_doan=%.6f tan_quan_sat=%.6f ti_so=%.3f pass=%s"
            % (
                float(r2["tan_du_doan"]),
                float(r2["tan_quan_sat"]),
                float(r2["ti_so"]),
                r2["pass"],
            )
        )
        print(
            "T6e R3 |t|>2: %d/%d pass=%s"
            % (int(r3["observed"]), int(r3["denominator"]), r3["pass"])
        )
        print(
            "T6e R4 weighted mean=%+.6f +/- %.6f ms; unweighted=%+.6f +/- %.6f ms"
            % (
                float(r4["weighted_mean"]),
                float(r4["weighted_se"]),
                float(r4["unweighted_mean"]),
                float(r4["unweighted_se"]),
            )
        )
        print(
            "T6e R5 strongest=%s pass=%s"
            % (r5["observed_largest_cell"], r5["pass"])
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default=STATE)
    parser.add_argument("--sealed-dir", default=SEALED)
    parser.add_argument("--baseline-state", default=CONTROL_STATE)
    parser.add_argument(
        "--baseline-dir",
        default=None,
        help="sealed dir for exploratory T.6b C-block baseline subtraction",
    )
    parser.add_argument(
        "--cell-level",
        action="store_true",
        help="add exploratory A17 cell-level restatement of D-T2",
    )
    parser.add_argument(
        "--paired",
        action="store_true",
        help="add exploratory A18 paired-by-seed cell error bars",
    )
    parser.add_argument("--out", default="-")
    parser.add_argument(
        "--make-fake-sealed",
        default=None,
        help="write fake sealed files to this directory and exit",
    )
    args = parser.parse_args()
    if args.cell_level and not args.baseline_dir:
        raise SystemExit("--cell-level can dung --baseline-dir")
    if args.paired and not args.baseline_dir:
        raise SystemExit("--paired can dung --baseline-dir")

    public_rows = _load_state_rows(args.state)
    model = LinkModelV2.load(MODEL_PATH)

    if args.make_fake_sealed:
        write_fake_sealed(public_rows, args.make_fake_sealed, model)
        print(
            "wrote fake sealed rows: n=%d dir=%s"
            % (len(public_rows), args.make_fake_sealed)
        )
        return

    rows = analyze_rows(combine_rows(public_rows, args.sealed_dir), model)
    baseline_rows = None
    baseline = None
    if args.baseline_dir:
        baseline_public_rows = _load_state_rows(args.baseline_state)
        baseline_rows = analyze_rows(
            combine_rows(baseline_public_rows, args.baseline_dir), model
        )
        baseline = baseline_from_controls(baseline_rows)
        rows = apply_baseline(rows, baseline)

    report = build_report(
        rows,
        args.state,
        args.sealed_dir,
        baseline_state=args.baseline_state if args.baseline_dir else None,
        baseline_dir=args.baseline_dir,
        baseline_rows=baseline_rows,
        baseline=baseline,
        cell_level=args.cell_level,
        paired=args.paired,
    )
    text = json.dumps(_jsonable(report), indent=1, sort_keys=True)
    _print_report_summary(report)
    if args.out == "-":
        print(text)
    else:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print("wrote report -> %s" % args.out)


if __name__ == "__main__":
    main()
