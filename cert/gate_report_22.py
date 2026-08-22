#!/usr/bin/env python3
"""Phase 22 / Lesson 22.8 -- final gate report and GO decision.

The report is intentionally read-only: it consumes the artifacts produced by
Lessons 22.2--22.7 and never re-runs an experiment.  Missing evidence is
reported as NOT_RUN, because a blank spot is not a PASS.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Sequence


MAIN_CELL = "poisson_0.925"
RESULT_ROOT = Path("results/SUPERSEDED/phase-22")
DECISION_RULE = (
    "GO requires zero FAIL/ERROR and zero NOT_RUN. Prediction hit rate is "
    "REPORTED, never a gate: a missed prediction with an understood mechanism "
    "is a result, not a defect."
)


class MissingEvidence(KeyError):
    """Raised when an artifact is absent for a read-only gate."""


def _git(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def _json_clean(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _json_clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_clean(v) for v in value]
    if isinstance(value, tuple):
        return [_json_clean(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        if value > 0.0:
            return "inf"
        if value < 0.0:
            return "-inf"
        return None
    return value


def normalize_cell(cell: str) -> str:
    return str(cell).replace("@", "_")


def artifact_paths(cell: str = MAIN_CELL, root: str | os.PathLike[str] = RESULT_ROOT) -> Dict[str, Path]:
    suffix = normalize_cell(cell)
    base = Path(root)
    return {
        "calib": base / ("calib_set_v3_%s.json" % suffix),
        "conformal": base / ("conformal_sim_%s.json" % suffix),
        "selective": base / ("selective_%s.json" % suffix),
        "matrix": base / ("config_matrix_%s.json" % suffix),
        "tau": base / ("tau_sweep_%s.json" % suffix),
        "aoi": base / ("aoi_profiles_%s.json" % suffix),
    }


def _load_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_artifacts(cell: str = MAIN_CELL, root: str | os.PathLike[str] = RESULT_ROOT) -> Dict[str, Any | None]:
    return {name: _load_json(path) for name, path in artifact_paths(cell, root).items()}


def _require(artifacts: Mapping[str, Any | None], name: str) -> Any:
    value = artifacts.get(name)
    if value is None:
        raise MissingEvidence(name)
    return value


def _as_float(value: Any) -> float:
    if value is None:
        return float("nan")
    if isinstance(value, str):
        if value.lower() == "inf":
            return float("inf")
        if value.lower() == "-inf":
            return float("-inf")
        if value.lower() == "nan":
            return float("nan")
    return float(value)


def _nested(data: Mapping[str, Any], path: Sequence[str]) -> Any:
    cur: Any = data
    for key in path:
        cur = cur[key]
    return cur


def _bool_gate(artifacts: Mapping[str, Any | None], artifact: str, path: Sequence[str]) -> tuple[bool, Dict[str, Any]]:
    data = _require(artifacts, artifact)
    value = _nested(data, path)
    return bool(value), {"value": bool(value)}


def _gate_calib_bitwise(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    data = _require(artifacts, "calib")
    value = _as_float(data["V22_1_worst"])
    return value == 0.0, {"V22_1_worst": value}


def _gate_cross_cell_blocks(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    data = _require(artifacts, "calib")
    value = int(data["V22_5_min"])
    return value >= 9, {"min_calib_blocks_per_z_x_mhat_cell": value, "threshold": 9}


def _gate_corrected_coverage(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    ok, evidence = _bool_gate(artifacts, "conformal", ("gates", "G22_4_corrected_coverage_ge_0p88"))
    proc = _require(artifacts, "conformal")["procedures"]
    evidence["coverage_simultaneous_marginal"] = {
        name: proc[name]["coverage_simultaneous_marginal"]
        for name in ("bonferroni", "sidak", "maxscore")
    }
    return ok, evidence


def _gate_negative_control(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    return _bool_gate(artifacts, "conformal", ("gates", "G22_5_negative_control_collapses"))


def _gate_bridge_21r(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    return _bool_gate(artifacts, "conformal", ("gates", "V22_6_bridge_to_21R_exact"))


def _gate_pc22_3(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    data = _require(artifacts, "conformal")
    pc = data["PC22_3_variance_control"]
    return bool(pc["pass_PC22_3"]), {
        "coverage_sd_row": pc["coverage_sd_row"],
        "coverage_sd_block": pc["coverage_sd_block"],
        "sd_ratio_row_over_block": pc["sd_ratio_row_over_block"],
    }


def _gate_selective_valid(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    return _bool_gate(artifacts, "selective", ("gates", "G22_6_post_selection_valid_at_kappa1"))


def _gate_fixed_points(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    data = _require(artifacts, "selective")
    ok = bool(data["gates"]["G22_7_fixed_points_terminate"])
    return ok, {
        "fcr_n_iter_kappa1": _selective_row(data, "fcr", 1.0)["n_iter"],
        "selective_n_iter_kappa1": _selective_row(data, "selective", 1.0)["n_iter"],
    }


def _gate_nc22_2(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    return _bool_gate(artifacts, "selective", ("gates", "NC22_2_kappa0_reduces_to_21R"))


def _gate_h22_7_c3(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    data = _require(artifacts, "matrix")
    h = data["configs"]["C3"]["H22_7"]
    return bool(data["gates"]["G22_8_H22_7_C3_full_claim"]), {
        "kappa": h.get("kappa"),
        "acceptance": h.get("acceptance"),
        "risk_ratio": h.get("risk_ratio"),
        "err_given_accept": h.get("err_given_accept"),
    }


def _gate_matrix_monotone(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    return _bool_gate(artifacts, "matrix", ("gates", "G22_9_acceptance_and_risk_monotone"))


def _gate_frontier_not_degraded(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    data = _require(artifacts, "matrix")
    c0 = _as_float(data["configs"]["C0"]["aurc"])
    c3 = _as_float(data["configs"]["C3"]["aurc"])
    ratio = c3 / c0 if math.isfinite(c0) and c0 > 0.0 and math.isfinite(c3) else float("nan")
    ok = bool(ratio < 1.02 and data["gates"]["frontier_not_degraded_C3_vs_C0_within_8pct"])
    return ok, {"aurc_C0": c0, "aurc_C3": c3, "aurc_C3_over_C0": ratio, "threshold": 1.02}


def _gate_tau_bands(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    data = _require(artifacts, "tau")
    return bool(data["gates"]["G22_10_preregistered_ratio_bands"]), {
        "ratio_measured": data["summary"]["ratio_measured"],
    }


def _gate_tau_A(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    data = _require(artifacts, "tau")
    return bool(data["gates"]["G22_11_A_independent_of_tau"]), {
        "A_span_pct": data["summary"]["A_span_pct"],
        "threshold_pct": 2.0,
    }


def _gate_aoi_realistic_null(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    data = _require(artifacts, "aoi")
    return bool(data["gates"]["realistic_profiles_indistinguishable_from_uniform"]), {
        "U1_max_abs_ratio_deviation": _max_abs_ratio_deviation(data, "U1"),
        "U2_max_abs_ratio_deviation": _max_abs_ratio_deviation(data, "U2"),
        "threshold": 0.02,
    }


def _gate_pc22_4(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    data = _require(artifacts, "aoi")
    return bool(data["gates"]["PC22_4_extreme_offset_visible"]), {
        "PC4_ratio_vs_U0": data["qhat_ratio_vs_U0"]["PC4"],
    }


def _gate_aoi_coverage(artifacts: Mapping[str, Any | None]) -> tuple[bool, Dict[str, Any]]:
    data = _require(artifacts, "aoi")
    return bool(data["gates"]["coverage_all_profiles_at_least_0p88"]), {
        p: data["profiles"][p]["coverage_marginal"]
        for p in data["profiles_order"]
    }


GATE_SPECS: Sequence[Dict[str, Any]] = (
    {
        "id": "G22-2",
        "lesson": "22.2",
        "claim": "U0 reproduces calib_set_v2 bit-for-bit",
        "needs": ("calib",),
        "kind": "reproduction",
        "check": _gate_calib_bitwise,
    },
    {
        "id": "G22-3",
        "lesson": "22.2",
        "claim": "every (z_bin x m_hat_bin) cell has at least 9 calibration blocks",
        "needs": ("calib",),
        "kind": "positive",
        "check": _gate_cross_cell_blocks,
    },
    {
        "id": "G22-4",
        "lesson": "22.3",
        "claim": "corrected procedures achieve simultaneous coverage",
        "needs": ("conformal",),
        "kind": "positive",
        "check": _gate_corrected_coverage,
    },
    {
        "id": "G22-5",
        "lesson": "22.3",
        "claim": "negative control collapses without correction",
        "needs": ("conformal",),
        "kind": "negative_control",
        "check": _gate_negative_control,
    },
    {
        "id": "V22-6",
        "lesson": "22.3",
        "claim": "uncorrected slot 1 equals the 21R qhat exactly",
        "needs": ("conformal",),
        "kind": "reproduction",
        "check": _gate_bridge_21r,
    },
    {
        "id": "PC22-3",
        "lesson": "22.3",
        "claim": "row split collapses the coverage variance",
        "needs": ("conformal",),
        "kind": "positive_control",
        "check": _gate_pc22_3,
    },
    {
        "id": "G22-6",
        "lesson": "22.4",
        "claim": "post-selection validity is restored at kappa=1",
        "needs": ("selective",),
        "kind": "positive",
        "check": _gate_selective_valid,
    },
    {
        "id": "G22-7",
        "lesson": "22.4",
        "claim": "fixed points terminate",
        "needs": ("selective",),
        "kind": "positive",
        "check": _gate_fixed_points,
    },
    {
        "id": "NC22-2",
        "lesson": "22.4",
        "claim": "kappa=0 reduces to 21R",
        "needs": ("selective",),
        "kind": "negative_control",
        "check": _gate_nc22_2,
    },
    {
        "id": "G22-8",
        "lesson": "22.5",
        "claim": "H22-7 holds for the full C3 claim",
        "needs": ("matrix",),
        "kind": "positive",
        "check": _gate_h22_7_c3,
    },
    {
        "id": "G22-9",
        "lesson": "22.5",
        "claim": "risk-coverage curves are monotone in kappa",
        "needs": ("matrix",),
        "kind": "positive",
        "check": _gate_matrix_monotone,
    },
    {
        "id": "G22-9b",
        "lesson": "22.5",
        "claim": "frontier is not degraded: AURC(C3)/AURC(C0) < 1.02",
        "needs": ("matrix",),
        "kind": "positive",
        "check": _gate_frontier_not_degraded,
    },
    {
        "id": "G22-10",
        "lesson": "22.6",
        "claim": "all five tau ratios lie inside signed bands",
        "needs": ("tau",),
        "kind": "positive",
        "check": _gate_tau_bands,
    },
    {
        "id": "G22-11",
        "lesson": "22.6",
        "claim": "AR(1) amplitude A is independent of tau",
        "needs": ("tau",),
        "kind": "positive",
        "check": _gate_tau_A,
    },
    {
        "id": "G22-12",
        "lesson": "22.7",
        "claim": "realistic AoI profiles are indistinguishable from uniform",
        "needs": ("aoi",),
        "kind": "positive",
        "check": _gate_aoi_realistic_null,
    },
    {
        "id": "PC22-4",
        "lesson": "22.7",
        "claim": "extreme AoI offset is visible",
        "needs": ("aoi",),
        "kind": "positive_control",
        "check": _gate_pc22_4,
    },
    {
        "id": "G22-13",
        "lesson": "22.7",
        "claim": "coverage holds under every AoI profile",
        "needs": ("aoi",),
        "kind": "positive",
        "check": _gate_aoi_coverage,
    },
)


PREDICTIONS: Sequence[Dict[str, Any]] = (
    {"id": "P1", "lesson": "22.3", "what": "qhat_bonferroni_B0 / qhat_21R_B0", "lo": 1.28, "hi": 1.33},
    {"id": "P2", "lesson": "22.3", "what": "qhat_sidak_B0 / qhat_21R_B0", "lo": 1.27, "hi": 1.32},
    {"id": "P3", "lesson": "22.3", "what": "qhat_maxscore_B0 / qhat_21R_B0", "lo": 1.22, "hi": 1.30},
    {"id": "P4", "lesson": "22.3", "what": "pointwise coverage under simultaneous correction", "lo": 0.955, "hi": 0.975},
    {"id": "P5", "lesson": "22.3", "what": "negative-control simultaneous coverage", "lo": 0.74, "hi": 0.80},
    # Rows the phase missed. Kept on purpose: dropping a signed prediction
    # because it failed is the selective reporting this phase exists to avoid.
    {"id": "M1", "lesson": "22.3", "what": "qhat_maxscore / qhat_bonferroni", "lo": 0.94, "hi": 0.98},
    {"id": "M2", "lesson": "22.3", "what": "simultaneous coverage (bonferroni)", "lo": 0.88, "hi": 0.92},
    {"id": "P6", "lesson": "22.4", "what": "violation|accept before repair", "lo": 0.115, "hi": 0.13},
    {"id": "P7", "lesson": "22.4", "what": "violation|accept after fcr", "lo": 0.0, "hi": 0.10},
    {"id": "P8", "lesson": "22.4", "what": "violation|accept after mondrian", "lo": 0.0, "hi": 0.10},
    {"id": "P9", "lesson": "22.4", "what": "violation|accept after selective", "lo": 0.0, "hi": 0.10},
    {"id": "P10", "lesson": "22.4", "what": "fixed-point iterations", "lo": 3, "hi": 12},
    {"id": "M3", "lesson": "22.4", "what": "fcr multiplier at the fixed point", "lo": 1.45, "hi": 1.58},
    {"id": "P11", "lesson": "22.5", "what": "err|reject / err|accept at operating point", "lo": 3.0, "hi": None},
    {"id": "M4", "lesson": "22.5", "what": "C3 multiplier at the operating point", "lo": 1.72, "hi": 1.88},
    {"id": "M5", "lesson": "22.5", "what": "C3 acceptance at kappa=1", "lo": 0.075, "hi": 0.110},
    {"id": "M6", "lesson": "22.5", "what": "C3 acceptance at kappa=0.5", "lo": 0.30, "hi": 0.42},
    {"id": "M7", "lesson": "22.5", "what": "C3 acceptance at kappa=0.75", "lo": 0.15, "hi": 0.24},
    {"id": "M8", "lesson": "22.5", "what": "C3 err|accept at kappa=0.5", "lo": 0.045, "hi": 0.075},
    {"id": "S1", "lesson": "22.5", "what": "H22-7 holds at kappa in {0.5, 0.75}", "kind": "structural"},
    {"id": "P12", "lesson": "22.6", "what": "ratio at tau=0.50", "lo": 1.77, "hi": 2.16},
    {"id": "P13", "lesson": "22.6", "what": "ratio at tau=1.00", "lo": 1.87, "hi": 2.29},
    {"id": "P14", "lesson": "22.6", "what": "ratio at tau=2.00", "lo": 1.88, "hi": 2.30},
    {"id": "P15", "lesson": "22.6", "what": "ratio at tau=2.87", "lo": 1.86, "hi": 2.27},
    {"id": "P16", "lesson": "22.6", "what": "ratio at tau=5.00", "lo": 1.77, "hi": 2.17},
    {"id": "S2", "lesson": "22.6", "what": "ratio over tau is hump-shaped", "kind": "structural"},
    {"id": "S3", "lesson": "22.6", "what": "A is independent of tau (<2%)", "kind": "structural"},
    {"id": "P17", "lesson": "22.7", "what": "max |qhat(U1)/qhat(U0)-1|", "lo": 0.0, "hi": 0.02},
    {"id": "P18", "lesson": "22.7", "what": "max |qhat(U2)/qhat(U0)-1|", "lo": 0.0, "hi": 0.02},
    {"id": "M9", "lesson": "22.7", "what": "qhat(U1)/qhat(U0) at B2 (sign prediction)", "lo": 0.95, "hi": 1.00},
    {"id": "M10", "lesson": "22.7", "what": "qhat(U2)/qhat(U0) at B0 (sign prediction)", "lo": 0.96, "hi": 1.00},
    {"id": "S4", "lesson": "22.7", "what": "PC4 makes the Jensen effect visible", "kind": "structural"},
)


def _qhat_slot(data: Mapping[str, Any], procedure: str, z_bin: str = "0", slot: int = 0) -> float:
    return _as_float(data["procedures"][procedure]["qhat"][str(z_bin)][int(slot)])


def _selective_row(data: Mapping[str, Any], procedure: str, kappa: float) -> Mapping[str, Any]:
    for row in data["results"][procedure]:
        if abs(_as_float(row["kappa"]) - float(kappa)) < 1e-12:
            return row
    raise KeyError((procedure, kappa))


def _matrix_row(data: Mapping[str, Any], config: str, kappa: float) -> Mapping[str, Any]:
    for row in data["configs"][config]["rows"]:
        if abs(_as_float(row["kappa"]) - float(kappa)) < 1e-12:
            return row
    raise KeyError((config, kappa))


def _mean(values: Sequence[Any]) -> float:
    vals = [_as_float(v) for v in values]
    return float(sum(vals) / len(vals))


def _safe_ratio(num: Any, den: Any) -> float:
    n = _as_float(num)
    d = _as_float(den)
    if not math.isfinite(n) or not math.isfinite(d) or d == 0.0:
        return float("nan")
    return n / d


def _max_abs_ratio_deviation(data: Mapping[str, Any], profile: str) -> float:
    ratios = data["qhat_ratio_vs_U0"][profile]
    return max(abs(_as_float(v) - 1.0) for v in ratios.values())


def measure_scorecard_values(artifacts: Mapping[str, Any | None]) -> Dict[str, Any]:
    values: Dict[str, Any] = {}

    conformal = artifacts.get("conformal")
    if conformal is not None:
        q21 = _qhat_slot(conformal, "uncorrected", "0", 0)
        qbon = _qhat_slot(conformal, "bonferroni", "0", 0)
        qsid = _qhat_slot(conformal, "sidak", "0", 0)
        qmax = _qhat_slot(conformal, "maxscore", "0", 0)
        values.update(
            P1=_safe_ratio(qbon, q21),
            P2=_safe_ratio(qsid, q21),
            P3=_safe_ratio(qmax, q21),
            P4=_mean(conformal["procedures"]["bonferroni"]["coverage_pointwise_marginal"]),
            P5=conformal["procedures"]["uncorrected"]["coverage_simultaneous_marginal"],
            M1=_safe_ratio(qmax, qbon),
            M2=conformal["procedures"]["bonferroni"]["coverage_simultaneous_marginal"],
        )

    selective = artifacts.get("selective")
    if selective is not None:
        none1 = _selective_row(selective, "none", 1.0)
        fcr1 = _selective_row(selective, "fcr", 1.0)
        mon1 = _selective_row(selective, "mondrian", 1.0)
        sel1 = _selective_row(selective, "selective", 1.0)
        values.update(
            P6=none1["violation_given_accept"],
            P7=fcr1["violation_given_accept"],
            P8=mon1["violation_given_accept"],
            P9=sel1["violation_given_accept"],
            P10=sel1["n_iter"],
            M3=_safe_ratio(fcr1["qhat"]["0"], none1["qhat"]["0"]),
        )

    matrix = artifacts.get("matrix")
    if matrix is not None:
        c3_05 = _matrix_row(matrix, "C3", 0.5)
        c3_075 = _matrix_row(matrix, "C3", 0.75)
        c3_1 = _matrix_row(matrix, "C3", 1.0)
        c0_05 = _matrix_row(matrix, "C0", 0.5)
        values.update(
            P11=_safe_ratio(c3_05["err_given_reject"], c3_05["err_given_accept"]),
            M4=_safe_ratio(c3_05["qhat_slot1_mean"], c0_05["qhat_slot1_mean"]),
            M5=c3_1["acceptance"],
            M6=c3_05["acceptance"],
            M7=c3_075["acceptance"],
            M8=c3_05["err_given_accept"],
            S1=bool(matrix["configs"]["C3"]["H22_7"]["pass"] is True and c3_05["pass_coverage"]),
        )

    tau = artifacts.get("tau")
    if tau is not None:
        by_tau = {round(_as_float(row["tau"]), 2): row for row in tau["rows"]}
        values.update(
            P12=by_tau[0.50]["ratio_measured"],
            P13=by_tau[1.00]["ratio_measured"],
            P14=by_tau[2.00]["ratio_measured"],
            P15=by_tau[2.87]["ratio_measured"],
            P16=by_tau[5.00]["ratio_measured"],
            S2=bool(tau["gates"]["ratio_is_hump_not_monotone"]),
            S3=bool(tau["gates"]["G22_11_A_independent_of_tau"]),
        )

    aoi = artifacts.get("aoi")
    if aoi is not None:
        values.update(
            P17=_max_abs_ratio_deviation(aoi, "U1"),
            P18=_max_abs_ratio_deviation(aoi, "U2"),
            M9=aoi["qhat_ratio_vs_U0"]["U1"]["2"],
            M10=aoi["qhat_ratio_vs_U0"]["U2"]["0"],
            S4=bool(aoi["gates"]["PC22_4_extreme_offset_visible"]),
        )

    return values


def _score_one(pred: Mapping[str, Any], observed: Any) -> str:
    if observed is None:
        return "NOT_RUN"
    if pred.get("kind") == "structural":
        return "HIT" if bool(observed) else "MISS"
    value = _as_float(observed)
    lo = pred.get("lo")
    hi = pred.get("hi")
    if lo is not None and value < float(lo):
        return "MISS"
    if hi is not None and value > float(hi):
        return "MISS"
    return "HIT"


def score_predictions(artifacts: Mapping[str, Any | None]) -> list[Dict[str, Any]]:
    values = measure_scorecard_values(artifacts)
    rows = []
    for pred in PREDICTIONS:
        observed = values.get(str(pred["id"]))
        verdict = _score_one(pred, observed)
        rows.append(
            {
                **{k: v for k, v in pred.items() if k != "kind"},
                "observed": observed,
                "verdict": verdict,
            }
        )
    return rows


def summarize_scorecard(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    hit = sum(1 for row in rows if row["verdict"] == "HIT")
    miss = sum(1 for row in rows if row["verdict"] == "MISS")
    scored = hit + miss
    lessons = []
    for row in rows:
        lesson = str(row["lesson"])
        if lesson not in lessons:
            lessons.append(lesson)
    by_lesson = {}
    for lesson in lessons:
        sub = [row for row in rows if row["lesson"] == lesson and row["verdict"] in ("HIT", "MISS")]
        by_lesson[lesson] = "%d/%d" % (sum(1 for row in sub if row["verdict"] == "HIT"), len(sub))
    return {
        "n_hit": int(hit),
        "n_miss": int(miss),
        "n_not_run": int(sum(1 for row in rows if row["verdict"] == "NOT_RUN")),
        "n_scored": int(scored),
        "hit_rate": float(hit / scored) if scored else None,
        "hit_rate_by_lesson": by_lesson,
        "note": "All signed misses M1..M10 are retained to prevent selective reporting.",
    }


def evaluate_gates(artifacts: Mapping[str, Any | None]) -> list[Dict[str, Any]]:
    rows = []
    for spec in GATE_SPECS:
        base = {
            "id": spec["id"],
            "lesson": spec["lesson"],
            "claim": spec["claim"],
            "kind": spec["kind"],
            "needs": list(spec["needs"]),
        }
        missing = [name for name in spec["needs"] if artifacts.get(name) is None]
        if missing:
            rows.append({**base, "status": "NOT_RUN", "evidence": {"missing_artifacts": missing}})
            continue
        try:
            ok, evidence = spec["check"](artifacts)
            rows.append({**base, "status": "PASS" if ok else "FAIL", "evidence": evidence})
        except MissingEvidence as exc:
            rows.append({**base, "status": "NOT_RUN", "evidence": {"missing_artifacts": [str(exc)]}})
        except Exception as exc:  # pragma: no cover - exercised only by corrupt artifacts.
            rows.append({**base, "status": "ERROR", "evidence": {"error": "%s: %s" % (type(exc).__name__, exc)}})
    return rows


def decision_from_gate_rows(
    gates: Sequence[Mapping[str, Any]],
    prediction_summary: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    counts = {status: int(sum(1 for row in gates if row["status"] == status)) for status in ("PASS", "FAIL", "NOT_RUN", "ERROR")}
    blocking = [str(row["id"]) for row in gates if row["status"] in ("FAIL", "ERROR")]
    not_run = [str(row["id"]) for row in gates if row["status"] == "NOT_RUN"]
    if blocking:
        decision = "NO_GO"
    elif not_run:
        decision = "INCOMPLETE"
    else:
        decision = "GO"
    out = {
        "gates_pass": counts["PASS"],
        "gates_total": int(len(gates)),
        "gates_fail": counts["FAIL"],
        "gates_error": counts["ERROR"],
        "gates_not_run_count": counts["NOT_RUN"],
        "gates_blocking": blocking,
        "gates_not_run": not_run,
        "decision": decision,
        "rule": DECISION_RULE,
    }
    if prediction_summary is not None:
        out.update(
            predictions_hit=prediction_summary.get("n_hit"),
            predictions_scored=prediction_summary.get("n_scored"),
            predictions_miss=prediction_summary.get("n_miss"),
            hit_rate=prediction_summary.get("hit_rate"),
            hit_rate_by_lesson=prediction_summary.get("hit_rate_by_lesson"),
        )
    return out


def _frontier_scan(root: str | os.PathLike[str]) -> Dict[str, Any]:
    cells = []
    pattern = str(Path(root) / "config_matrix_*.json")
    for path in sorted(glob.glob(pattern)):
        suffix = Path(path).stem.replace("config_matrix_", "")
        if suffix.endswith("_V3"):
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        c0 = _as_float(data["configs"]["C0"]["aurc"])
        c3 = _as_float(data["configs"]["C3"]["aurc"])
        ratio = c3 / c0 if math.isfinite(c0) and c0 > 0.0 and math.isfinite(c3) else None
        cells.append(
            {
                "cell": data.get("cell", suffix.replace("_", "@", 1)),
                "aurc_C0": c0 if math.isfinite(c0) else None,
                "aurc_C3": c3 if math.isfinite(c3) else None,
                "aurc_C3_over_C0": ratio,
                "frontier_not_degraded": bool(ratio is not None and ratio < 1.02),
                "H22_7_C3": bool(data["gates"].get("G22_8_H22_7_C3_full_claim")),
            }
        )
    evaluable = [row for row in cells if row["aurc_C3_over_C0"] is not None]
    return {
        "cells": cells,
        "n_cells": int(len(cells)),
        "n_evaluable": int(len(evaluable)),
        "n_evaluable_frontier_pass": int(sum(bool(row["frontier_not_degraded"]) for row in evaluable)),
        "note": "Use this before claiming frontier invariance in the abstract; degenerate cells need a lower-scope claim.",
    }


def _paired_bootstrap_summary(conformal: Mapping[str, Any] | None) -> Dict[str, Any]:
    if conformal is None or "paired_bootstrap_delta_qhat" not in conformal:
        return {"available": False}
    boot = conformal["paired_bootstrap_delta_qhat"]
    rows = []
    for z_bin, by_proc in boot["by_bin"].items():
        for proc, vals in by_proc.items():
            for idx, (lo, hi, mean) in enumerate(zip(vals["ci95_low"], vals["ci95_high"], vals["delta_mean"])):
                rows.append(
                    {
                        "z_bin": str(z_bin),
                        "procedure": str(proc),
                        "slot": int(idx + 1),
                        "delta_mean": float(mean),
                        "ci95_low": float(lo),
                        "ci95_high": float(hi),
                        "ci95_contains_zero": bool(float(lo) <= 0.0 <= float(hi)),
                    }
                )
    return {
        "available": True,
        "baseline": boot.get("baseline"),
        "procedures": boot.get("procedures"),
        "n_boot": boot.get("n_boot"),
        "n_intervals": int(len(rows)),
        "n_intervals_containing_zero": int(sum(bool(row["ci95_contains_zero"]) for row in rows)),
        "intervals": rows,
        "note": "Use paired deltas before ranking FWER procedures; if a delta CI contains 0, report no statistical separation.",
    }


def phase_statement(artifacts: Mapping[str, Any | None]) -> Dict[str, Any]:
    matrix = artifacts.get("matrix")
    if matrix is None:
        return {"available": False}
    c3 = _matrix_row(matrix, "C3", 0.5)
    c0_aurc = _as_float(matrix["configs"]["C0"]["aurc"])
    c3_aurc = _as_float(matrix["configs"]["C3"]["aurc"])
    matched = matrix["matched_risk_ratio_vs_C0"]["C3"]
    return {
        "available": True,
        "cell": matrix.get("cell"),
        "operating_point": {
            "config": "C3",
            "kappa": 0.5,
            "acceptance": c3["acceptance"],
            "err_given_accept": c3["err_given_accept"],
            "risk_ratio_vs_anchor": c3["risk_ratio"],
            "violation_given_accept": c3["violation_given_accept"],
            "err_reject_over_accept": _safe_ratio(c3["err_given_reject"], c3["err_given_accept"]),
        },
        "frontier": {
            "aurc_C0": c0_aurc,
            "aurc_C3": c3_aurc,
            "aurc_C3_over_C0": _safe_ratio(c3_aurc, c0_aurc),
            "risk_delta_pct_at_same_acceptance": {
                key: 100.0 * (_as_float(value) - 1.0)
                for key, value in matched.items()
                if key in ("0.70", "0.50", "0.30")
            },
        },
        "can_say": (
            "Simultaneous K=4 and post-selection-valid certification is feasible on the main cell; "
            "the cost is a shift along the risk-coverage curve, not a degraded frontier."
        ),
        "cannot_say": (
            "Do not claim a universal frontier law, an FWER ranking, or completion of Amendment 1 "
            "without the recorded GO conditions."
        ),
    }


def go_conditions(artifacts: Mapping[str, Any | None], root: str | os.PathLike[str]) -> list[Dict[str, Any]]:
    return [
        {
            "id": "GO-1",
            "status": "CONDITION",
            "text": "Before putting frontier invariance in the abstract, confirm AURC(C3)/AURC(C0) < 1.02 on all non-degenerate cells.",
            "evidence": _frontier_scan(root),
        },
        {
            "id": "GO-2",
            "status": "CONDITION",
            "text": "Rank FWER procedures only with paired bootstrap deltas.",
            "evidence": _paired_bootstrap_summary(artifacts.get("conformal")),
        },
        {
            "id": "GO-3",
            "status": "FUTURE_WORK",
            "text": "Amendment 1 (studentized max-score) was signed but not run in Phase 22.",
            "evidence": {"record_in_future_work": True},
        },
    ]


def build_report(
    cell: str = MAIN_CELL,
    root: str | os.PathLike[str] = RESULT_ROOT,
    artifacts: Mapping[str, Any | None] | None = None,
) -> Dict[str, Any]:
    loaded = dict(artifacts) if artifacts is not None else load_artifacts(cell, root)
    paths = {name: str(path) for name, path in artifact_paths(cell, root).items()}
    gates = evaluate_gates(loaded)
    scorecard = score_predictions(loaded)
    prediction_summary = summarize_scorecard(scorecard)
    decision = decision_from_gate_rows(gates, prediction_summary)
    return {
        "phase": "22",
        "lesson": "22.8",
        "cell": normalize_cell(cell),
        "artifact_paths": paths,
        "gates": gates,
        "gate_summary": decision,
        "scorecard": scorecard,
        "prediction_summary": prediction_summary,
        "phase_statement": phase_statement(loaded),
        "go_conditions": go_conditions(loaded, root),
        "provenance": {
            "script": "cert/gate_report_22.py",
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "read_only": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell", default=MAIN_CELL)
    parser.add_argument("--root", default=str(RESULT_ROOT))
    parser.add_argument("--out")
    args = parser.parse_args()

    out_path = args.out or str(Path(args.root) / ("gate_report_%s.json" % normalize_cell(args.cell)))
    report = build_report(cell=str(args.cell), root=str(args.root))
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(_json_clean(report), f, indent=1, sort_keys=True)
        f.write("\n")
    print(json.dumps(_json_clean(report), indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
