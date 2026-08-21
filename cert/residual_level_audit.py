#!/usr/bin/env python3
"""Lesson 23.7-bis -- kiem toan tang ap phan du (S7).

Ba nhanh confirmatory da khoa trong Amendment 23-32/33:

``H_path``
    Ap common shift o tang duong, khong cat. Day la nhanh kiem tra bat bien
    dai so; loss am (neu co) chi la doi chung, khong la mo hinh vat ly.
``H_link0``
    Chia residual duong cho ba link, khong cat loss tai 0. Nhanh nay co lap
    phi tuyen cua phep ghep ``1 - prod(1-p)``.
``H_link1``
    Chia residual duong cho ba link va cat loss tai 0. Day la hien thuc cu
    cua Lesson 23.7, duoc tai su dung tu :mod:`measurements.band_v2`.

Mot nhanh mo ta ``H_path_with_clip`` duoc ghi them de khong che giau tac dong
cua rang buoc mien neu no duoc ap ngay tai tang duong. Nhanh nay khong doi
cach cham M-23..M-26.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import numpy as np

from cert.cell_matrices import (
    RESIDUAL,
    TRUTH_TABLE,
    cell_matrices,
    git,
    json_clean,
    pin,
    prepare,
)
from measurements import band_v2 as B
from measurements import decision_error_v2 as D
from measurements import residual_spec as RS
from twin import topology_v7 as T7


R_STAR = -0.008868196569470351
N_LINKS_IN_PATH = 3

CELL_SPECS: Dict[str, Dict[str, Any]] = {
    "poisson@0.925": {"mode": "poisson", "rho_bar": 0.925, "slug": "poisson_0.925"},
    "poisson@0.850": {"mode": "poisson", "rho_bar": 0.850, "slug": "poisson_0.850"},
    "h2@0.700": {"mode": "h2", "rho_bar": 0.700, "slug": "h2_0.700"},
}
RAW_RELATIVE_B = "results/phase-20R/branch_b_fixed_s104_108.json"
RAW_RELATIVE_C = "results/phase-20R/branch_c_fixed_s104_108.json"


class PathShiftTruthTable(D.TruthTable):
    """Common loss shift at the measured (path) level, without clipping.

    Not clipping is deliberate: M-23 tests ``argmin(c_p + w*r)``. Clipping
    would make ``r`` action/row dependent and would no longer test that
    identity. Negative losses are counted and disclosed.
    """

    def __init__(
        self,
        resid_loss_path: float,
        mode: str,
        parquet_path: str = TRUTH_TABLE,
    ) -> None:
        super().__init__(parquet_path)
        self._r = float(resid_loss_path)
        self._mode = str(mode)
        self.negative_events = 0
        self.eval_count = 0

    def path_tables(
        self, mode: str, rho_mat: np.ndarray, w_loss: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        delay, loss, _cost = super().path_tables(mode, rho_mat, w_loss)
        if str(mode) != self._mode:
            return delay, loss, delay + float(w_loss) * loss
        self.eval_count += int(loss.size)
        shifted = loss + self._r
        self.negative_events += int(np.sum(shifted < 0.0))
        return delay, shifted, delay + float(w_loss) * shifted


class PathShiftClipTruthTable(PathShiftTruthTable):
    """Descriptive control: path-level shift with physical-domain clipping."""

    def __init__(
        self,
        resid_loss_path: float,
        mode: str,
        parquet_path: str = TRUTH_TABLE,
    ) -> None:
        super().__init__(resid_loss_path, mode, parquet_path)
        self.clip_events = 0

    def path_tables(
        self, mode: str, rho_mat: np.ndarray, w_loss: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        # Bypass PathShiftTruthTable.path_tables so counters are updated once.
        delay, loss, _cost = D.TruthTable.path_tables(self, mode, rho_mat, w_loss)
        if str(mode) != self._mode:
            return delay, loss, delay + float(w_loss) * loss
        self.eval_count += int(loss.size)
        shifted = loss + self._r
        n_clip = int(np.sum(shifted < 0.0))
        self.negative_events += n_clip
        self.clip_events += n_clip
        shifted = np.clip(shifted, 0.0, 1.0)
        return delay, shifted, delay + float(w_loss) * shifted


RelativePathShiftTruthTable = B.RelativePathShiftTruthTable


class LinkShiftNoClipTruthTable(D.TruthTable):
    """Evenly re-attributed per-link shift, without domain clipping."""

    def __init__(
        self,
        resid_loss_path: float,
        mode: str,
        n_links: int = N_LINKS_IN_PATH,
        parquet_path: str = TRUTH_TABLE,
    ) -> None:
        super().__init__(parquet_path)
        self._per_link = float(resid_loss_path) / int(n_links)
        self._mode = str(mode)
        self.negative_events = 0
        self.eval_count = 0

    def delay_loss(
        self, mode: str, link: str, rho: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        delay, loss = super().delay_loss(mode, link, rho)
        if str(mode) != self._mode:
            return delay, loss
        self.eval_count += int(np.asarray(rho).size)
        shifted = loss + self._per_link
        self.negative_events += int(np.sum(shifted < 0.0))
        return delay, shifted


def artifact_path(cell: str) -> str:
    return "results/phase-23/residual_level_audit_%s.json" % CELL_SPECS[cell]["slug"]


def relative_artifact_path(cell: str) -> str:
    return "results/phase-23/residual_relative_audit_%s.json" % CELL_SPECS[cell]["slug"]


def relative_point_from_raw(
    branch_b: str = RAW_RELATIVE_B,
    branch_c: str = RAW_RELATIVE_C,
    mode: str = "poisson",
) -> Dict[str, Any]:
    """Recompute absolute and relative loss residuals from raw B/C rows."""
    with open(branch_b, "r", encoding="utf-8") as handle:
        rows_b = json.load(handle).get("rows", [])
    with open(branch_c, "r", encoding="utf-8") as handle:
        rows_c = json.load(handle).get("rows", [])

    by_seed_b: Dict[int, list[float]] = {}
    by_seed_c: Dict[int, float] = {}
    rho_bars = set()
    for row in rows_b:
        if str(row.get("mode")) != str(mode):
            continue
        rho_bars.add(float(row["rho_bar"]))
        by_seed_b.setdefault(int(row["seed"]), []).append(float(row["loss"]))
    for row in rows_c:
        if str(row.get("mode")) != str(mode):
            continue
        rho_bars.add(float(row["rho_bar"]))
        by_seed_c[int(row["seed"])] = float(row["loss"])
    if len(rho_bars) != 1:
        raise ValueError("residual raw phai co dung mot rho_bar, thay %s" % sorted(rho_bars))
    if set(by_seed_b) != set(by_seed_c) or not by_seed_c:
        raise ValueError("B/C seed mismatch hoac rong")

    absolute, relative, baseline = [], [], []
    per_seed = {}
    for seed in sorted(by_seed_c):
        links = by_seed_b[seed]
        if len(links) != N_LINKS_IN_PATH:
            raise ValueError("seed %d co %d link, can 3" % (seed, len(links)))
        composed = 1.0 - float(np.prod([1.0 - value for value in links]))
        resid = float(by_seed_c[seed]) - composed
        absolute.append(resid)
        baseline.append(composed)
        relative.append(resid / composed)
        per_seed[str(seed)] = {
            "B_composed_loss": composed,
            "C_path_loss": float(by_seed_c[seed]),
            "absolute": resid,
            "relative": resid / composed,
        }
    absolute_point = float(np.mean(absolute))
    baseline_magnitude = float(np.mean(baseline))
    relative_point_ratio_of_means = absolute_point / baseline_magnitude
    relative_point_mean_of_ratios = float(np.mean(relative))
    published = _loss_record(mode)
    return {
        "mode": str(mode),
        "rho_bar_measured": float(next(iter(rho_bars))),
        "n_seed": len(absolute),
        "baseline_magnitude": baseline_magnitude,
        "absolute_point": absolute_point,
        # Amendment 37: M-28 extrapolates a ratio, so the primary estimand is
        # the mean of paired seed ratios.  Keep the other estimator diagnostic.
        "relative_point": relative_point_mean_of_ratios,
        "relative_point_mean_of_ratios": relative_point_mean_of_ratios,
        "relative_point_ratio_of_means": relative_point_ratio_of_means,
        "mean_seed_relative": relative_point_mean_of_ratios,
        "M_28_estimand": "mean_of_seed_ratios",
        "relative_sd": float(np.std(relative, ddof=1)),
        "matches_residual_cascade": bool(abs(absolute_point - float(published.point)) < 5e-4),
        "published_absolute_point": float(published.point),
        "scale": "loss_fraction",
        "level_tag": "per_path",
        "rowset": "branch_bc_seeds_104_108",
        "per_seed": per_seed,
    }


def _loss_record(mode: str, residual_path: str = RESIDUAL) -> RS.ResidualRecord:
    matches = [
        rec
        for rec in RS.load(residual_path)
        if str(rec.mode) == str(mode) and str(rec.channel) == "loss"
    ]
    if len(matches) != 1:
        raise ValueError(
            "can dung dung mot residual loss cho mode %s, thay %d" % (mode, len(matches))
        )
    rec = matches[0]
    if rec.level != "per_path":
        raise ValueError("S7 audit can residual level=per_path, thay %s" % rec.level)
    return rec


def endpoint_values(rec: RS.ResidualRecord) -> Dict[str, float]:
    """Three locked negative endpoints, record-specific after Amendment 23-33."""
    lo, hi = (float(x) for x in rec.ci90)
    return {
        "r_star": float(R_STAR),
        "point": float(rec.point),
        "ci90_worst": -max(abs(lo), abs(hi)),
    }


def _astar_from_rho(
    tt: D.TruthTable, mode: str, rho_mat: np.ndarray, w_loss: float
) -> np.ndarray:
    _delay, _loss, cost = tt.path_tables(mode, rho_mat, float(w_loss))
    return cost.argmin(axis=1)


def audit_rho_matrix(
    rho_mat: np.ndarray,
    mode: str,
    rec: RS.ResidualRecord,
    r_path: float,
    w_loss: float,
) -> Dict[str, Any]:
    """Small-array entry point used by golden tests."""
    if str(rec.mode) != str(mode) or rec.channel != "loss" or rec.level != "per_path":
        raise ValueError("cell/residual mode-channel-level khong khop")
    base = _astar_from_rho(D.TruthTable(TRUTH_TABLE), mode, rho_mat, w_loss)
    tt_path = PathShiftTruthTable(r_path, mode)
    tt_path_clip = PathShiftClipTruthTable(r_path, mode)
    tt_l0 = LinkShiftNoClipTruthTable(r_path, mode)
    tt_l1 = B.truth_table_for(rec, "common_mode", abs(float(r_path)), sign=-1.0)
    astars = {
        "H_path_correct_level": _astar_from_rho(tt_path, mode, rho_mat, w_loss),
        "H_path_with_clip_descriptive": _astar_from_rho(tt_path_clip, mode, rho_mat, w_loss),
        "H_link_no_clip": _astar_from_rho(tt_l0, mode, rho_mat, w_loss),
        "H_link_with_clip": _astar_from_rho(tt_l1, mode, rho_mat, w_loss),
    }
    return _summarize_astars(
        base,
        astars,
        row_mask=np.ones(len(base), dtype=bool),
        tables=(tt_path, tt_path_clip, tt_l0, tt_l1),
        r_path=float(r_path),
    )


def _flip_pairs(base: np.ndarray, changed: np.ndarray) -> Dict[str, int]:
    flip = base != changed
    codes = base[flip] * len(T7.PATH_NAMES) + changed[flip]
    values, counts = np.unique(codes, return_counts=True)
    return {
        "%s->%s"
        % (T7.PATH_NAMES[int(code) // len(T7.PATH_NAMES)], T7.PATH_NAMES[int(code) % len(T7.PATH_NAMES)]): int(count)
        for code, count in zip(values, counts)
    }


def _scope_metrics(
    base: np.ndarray, astars: Mapping[str, np.ndarray], mask: np.ndarray
) -> Dict[str, Any]:
    n = int(mask.sum())
    flips = {key: (value[mask] != base[mask]) for key, value in astars.items()}
    fractions = {key: float(value.mean()) for key, value in flips.items()}
    l0 = flips["H_link_no_clip"]
    l1 = flips["H_link_with_clip"]
    n_l1 = int(l1.sum())
    return {
        "n_rows": n,
        "n_flip": {key: int(value.sum()) for key, value in flips.items()},
        "flip_fraction": fractions,
        "decomposition": {
            "from_nonlinearity_fraction_difference": float(
                fractions["H_link_no_clip"] - fractions["H_path_correct_level"]
            ),
            "from_clipping_fraction_difference": float(
                fractions["H_link_with_clip"] - fractions["H_link_no_clip"]
            ),
            "clip_share_of_total": (
                float(
                    (fractions["H_link_with_clip"] - fractions["H_link_no_clip"])
                    / fractions["H_link_with_clip"]
                )
                if fractions["H_link_with_clip"] > 0.0
                else None
            ),
            "flip_set_relation": {
                "intersection": int(np.sum(l0 & l1)),
                "H_link0_only": int(np.sum(l0 & ~l1)),
                "H_link1_only": int(np.sum(l1 & ~l0)),
                "symmetric_difference": int(np.sum(l0 ^ l1)),
                "H_link0_subset_H_link1": bool(np.all(~l0 | l1)),
                "H_link1_total": n_l1,
            },
        },
        "flip_pairs": {
            key: _flip_pairs(base[mask], value[mask]) for key, value in astars.items()
        },
    }


def _table_diagnostics(tables: Sequence[D.TruthTable]) -> Dict[str, Any]:
    path, path_clip, link0, link1 = tables
    return {
        "H_path_correct_level": {
            "negative_events": int(getattr(path, "negative_events", 0)),
            "eval_count": int(getattr(path, "eval_count", 0)),
            "clipping_applied": False,
        },
        "H_path_with_clip_descriptive": {
            "clip_events": int(getattr(path_clip, "clip_events", 0)),
            "eval_count": int(getattr(path_clip, "eval_count", 0)),
            "clip_ratio": float(
                getattr(path_clip, "clip_events", 0)
                / max(int(getattr(path_clip, "eval_count", 0)), 1)
            ),
            "clipping_applied": True,
        },
        "H_link_no_clip": {
            "negative_events": int(getattr(link0, "negative_events", 0)),
            "eval_count": int(getattr(link0, "eval_count", 0)),
            "clipping_applied": False,
        },
        "H_link_with_clip": {
            "clip_events": int(getattr(link1, "clip_events", 0)),
            "eval_count": int(getattr(link1, "eval_count", 0)),
            "clip_ratio": float(
                getattr(link1, "clip_events", 0)
                / max(int(getattr(link1, "eval_count", 0)), 1)
            ),
            "clipping_applied": True,
        },
    }


def _summarize_astars(
    base: np.ndarray,
    astars: Mapping[str, np.ndarray],
    row_mask: np.ndarray,
    tables: Sequence[D.TruthTable],
    r_path: float,
) -> Dict[str, Any]:
    return {
        "r_path": float(r_path),
        "all_rows": _scope_metrics(base, astars, np.ones(len(base), dtype=bool)),
        "test_rows": _scope_metrics(base, astars, np.asarray(row_mask, dtype=bool)),
        "diagnostics": _table_diagnostics(tables),
        "level_tag": "per_path",
        "scale": "loss_fraction",
    }


def _audit_matrices(
    base_mats: Mapping[str, np.ndarray],
    changed_mats: Mapping[str, Mapping[str, np.ndarray]],
    tables: Sequence[D.TruthTable],
    r_path: float,
) -> Dict[str, Any]:
    base = np.asarray(base_mats["y_true"]).argmin(axis=1)
    astars = {
        key: np.asarray(value["y_true"]).argmin(axis=1)
        for key, value in changed_mats.items()
    }
    test = ~prepare(base_mats)["is_calib"]
    return _summarize_astars(base, astars, test, tables, r_path)


def audit_endpoint(
    base: Mapping[str, np.ndarray],
    mode: str,
    rho_bar: float,
    rec: RS.ResidualRecord,
    r_path: float,
) -> Dict[str, Any]:
    tt_path = PathShiftTruthTable(r_path, mode)
    tt_path_clip = PathShiftClipTruthTable(r_path, mode)
    tt_l0 = LinkShiftNoClipTruthTable(r_path, mode)
    tt_l1 = B.truth_table_for(rec, "common_mode", abs(float(r_path)), sign=-1.0)
    tables = (tt_path, tt_path_clip, tt_l0, tt_l1)
    changed = {
        "H_path_correct_level": cell_matrices(tt_path, mode=mode, rho_bar=rho_bar),
        "H_path_with_clip_descriptive": cell_matrices(tt_path_clip, mode=mode, rho_bar=rho_bar),
        "H_link_no_clip": cell_matrices(tt_l0, mode=mode, rho_bar=rho_bar),
        "H_link_with_clip": cell_matrices(tt_l1, mode=mode, rho_bar=rho_bar),
    }
    return _audit_matrices(base, changed, tables, float(r_path))


def negative_control(
    base: Mapping[str, np.ndarray], mode: str, rho_bar: float, rec: RS.ResidualRecord
) -> Dict[str, Any]:
    out = audit_endpoint(base, mode, rho_bar, rec, 0.0)
    fractions = out["all_rows"]["flip_fraction"]
    out["NC23v2_10_pass"] = bool(all(value == 0.0 for value in fractions.values()))
    return out


def _record_dict(rec: RS.ResidualRecord) -> Dict[str, Any]:
    return {
        "mode": rec.mode,
        "channel": rec.channel,
        "level": rec.level,
        "point": float(rec.point),
        "ci90": [float(x) for x in rec.ci90],
        "estimand": rec.estimand,
        "rho_bar_measured": float(rec.rho_bar_measured),
        "baseline_magnitude": float(rec.baseline_magnitude),
        "relative_point": float(rec.relative_point),
        "valid_range": rec.valid_range,
    }


def _verdict(report: Mapping[str, Any]) -> Dict[str, Any]:
    point = report["endpoints"]["point"]
    all_f = point["all_rows"]["flip_fraction"]
    test_f = point["test_rows"]["flip_fraction"]
    share = point["test_rows"]["decomposition"]["clip_share_of_total"]
    m23 = all(
        endpoint["all_rows"]["flip_fraction"]["H_path_correct_level"] == 0.0
        for endpoint in report["endpoints"].values()
    )
    if not m23:
        scenario = "UNRESOLVED_M23_FAILED"
    elif share is None:
        scenario = "UNRESOLVED_NO_H_LINK1_FLIPS"
    elif share > 0.90:
        scenario = "A"
    elif share >= 0.50:
        scenario = "B"
    else:
        scenario = "C"
    main = report["cell"] == "poisson@0.925"
    return {
        "scenario": scenario,
        "M_23_H_path_exact_zero": m23,
        "M_24_H_link0_point_in_0_0_02": bool(0.0 <= test_f["H_link_no_clip"] <= 0.020),
        "M_25_clip_share_gt_0_90": bool(share is not None and share > 0.90),
        "M_26_H_link1_reproduces_0_2130": (
            bool(abs(test_f["H_link_with_clip"] - 0.2130) < 0.005) if main else None
        ),
        "M_26_reason": None if main else "main_cell_only_by_definition",
        "point_all_rows": all_f,
        "point_test_rows": test_f,
        "clip_share_of_total_test": share,
    }


def run_cell(cell: str) -> Dict[str, Any]:
    if cell not in CELL_SPECS:
        raise ValueError("cell phai thuoc %s" % sorted(CELL_SPECS))
    spec = CELL_SPECS[cell]
    rec = _loss_record(spec["mode"])
    if rec.mode != spec["mode"]:
        raise AssertionError("mode mismatch")
    base = cell_matrices(D.TruthTable(TRUTH_TABLE), mode=spec["mode"], rho_bar=spec["rho_bar"])
    report: Dict[str, Any] = {
        "schema": "residual_level_audit/v1",
        "lesson": "23.7-bis",
        "cell": cell,
        "status": "APPLICABLE",
        "residual_record": _record_dict(rec),
        "endpoints": {},
        "controls": {
            "all_paths_have_three_links": bool(
                all(len(path) == N_LINKS_IN_PATH for path in T7.PATHS.values())
            ),
            "cell_residual_mode_match": bool(rec.mode == spec["mode"]),
        },
        "provenance": {
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit": git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(git("git", "status", "--porcelain")),
            "amendment_32": pin("docs/phase-23/00zh-amendment-32.md"),
            "amendment_33": pin("docs/phase-23/00zi-amendment-33.md"),
            "truth_table": pin(TRUTH_TABLE),
            "residual": pin(RESIDUAL),
        },
    }
    if not all(report["controls"].values()):
        raise AssertionError("input controls failed: %s" % report["controls"])
    report["negative_control"] = negative_control(
        base, spec["mode"], float(spec["rho_bar"]), rec
    )
    if not report["negative_control"]["NC23v2_10_pass"]:
        raise AssertionError("NC23v2-10 failed")
    for label, value in endpoint_values(rec).items():
        report["endpoints"][label] = audit_endpoint(
            base, spec["mode"], float(spec["rho_bar"]), rec, value
        )
    report["verdict"] = _verdict(report)
    return json_clean(report)


def run_relative_cell(cell: str) -> Dict[str, Any]:
    """Lesson 23.7-ter S8 audit using a multiplicative path residual."""
    if cell not in CELL_SPECS:
        raise ValueError("cell phai thuoc %s" % sorted(CELL_SPECS))
    spec = CELL_SPECS[cell]
    mode, rho_bar = str(spec["mode"]), float(spec["rho_bar"])
    rec = _loss_record(mode)
    relative = relative_point_from_raw(mode=mode)
    rel = float(relative["relative_point"])
    base = cell_matrices(D.TruthTable(TRUTH_TABLE), mode=mode, rho_bar=rho_bar)
    shifted_tt = RelativePathShiftTruthTable(rel, mode)
    shifted = cell_matrices(shifted_tt, mode=mode, rho_bar=rho_bar)
    prep = prepare(base)
    test = ~prep["is_calib"]
    base_astar = np.asarray(base["y_true"]).argmin(axis=1)
    shifted_astar = np.asarray(shifted["y_true"]).argmin(axis=1)
    flip = shifted_astar != base_astar
    min_path_loss = np.asarray(base["loss_true"], dtype=float).min(axis=1)
    q01 = float(np.quantile(min_path_loss[test], 0.01))
    ratio = abs(float(rec.point)) / q01
    flip_fraction = float(flip[test].mean())
    clip_ratio = float(shifted_tt.clip_events / max(shifted_tt.eval_count, 1))
    m27_expected = None
    if cell == "poisson@0.925":
        m27_expected = bool(ratio < 1.0)
    elif cell == "poisson@0.850":
        m27_expected = bool(ratio > 1.0)
    return json_clean({
        "schema": "residual_relative_audit/v1",
        "lesson": "23.7-ter",
        "cell": cell,
        "status": "APPLICABLE",
        "relative_residual": relative,
        "absolute_residual_record": _record_dict(rec),
        "metrics": {
            "q01_min_path_loss_test": q01,
            "M_27_abs_r_over_q01_min_path_loss": ratio,
            "M_29_flip_fraction_test": flip_fraction,
            "M_30_path_clip_ratio": clip_ratio,
            "n_test": int(test.sum()),
            "n_flip_test": int(flip[test].sum()),
        },
        "diagnostics": {
            "H_path_relative": {
                "clip_events": int(shifted_tt.clip_events),
                "eval_count": int(shifted_tt.eval_count),
                "clip_ratio": clip_ratio,
                "clipping_applied": False,
            },
        },
        "verdict": {
            "M_27": m27_expected,
            "M_28": bool(-0.20 <= float(relative["relative_point"]) <= -0.12) if mode == "poisson" else None,
            "M_28_label": "TAT_DINH" if mode == "poisson" else "poisson_only",
            "M_29": bool(0.0 <= flip_fraction <= 0.05),
            "M_30": bool(clip_ratio == 0.0),
        },
        "provenance": {
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit": git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(git("git", "status", "--porcelain")),
            "amendment_35": pin("docs/phase-23/00zk-amendment-35.md"),
            "truth_table": pin(TRUTH_TABLE),
            "residual": pin(RESIDUAL),
            "raw_branch_b": pin(RAW_RELATIVE_B),
            "raw_branch_c": pin(RAW_RELATIVE_C),
        },
    })


def write_json(path: str, payload: Mapping[str, Any]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _print_report(report: Mapping[str, Any], out: str) -> None:
    print("=== LESSON 23.7-bis: RESIDUAL LEVEL AUDIT ===")
    print("cell=%s  residual=%s/%s/%s" % (
        report["cell"], report["residual_record"]["mode"],
        report["residual_record"]["channel"], report["residual_record"]["level"],
    ))
    print("%-12s %11s %11s %11s %11s %9s" % (
        "endpoint", "H_path", "H_pathClip", "H_link0", "H_link1", "clipShare"
    ))
    for label in ("r_star", "point", "ci90_worst"):
        row = report["endpoints"][label]["test_rows"]
        f = row["flip_fraction"]
        share = row["decomposition"]["clip_share_of_total"]
        print("%-12s %11.6f %11.6f %11.6f %11.6f %9s" % (
            label,
            f["H_path_correct_level"], f["H_path_with_clip_descriptive"],
            f["H_link_no_clip"], f["H_link_with_clip"],
            "n/a" if share is None else "%.4f" % share,
        ))
    print("NC23v2-10=%s  scenario=%s" % (
        "PASS" if report["negative_control"]["NC23v2_10_pass"] else "FAIL",
        report["verdict"]["scenario"],
    ))
    print("artifact=%s" % out)


def _print_relative_report(report: Mapping[str, Any], out: str) -> None:
    metrics = report["metrics"]
    rel = report["relative_residual"]
    print("=== LESSON 23.7-ter: RELATIVE RESIDUAL (S8) ===")
    print("cell=%s  measured_at_rho=%.3f  relative=%+.6f" % (
        report["cell"], rel["rho_bar_measured"], rel["relative_point"],
    ))
    print("|r_abs|/q01(min path loss)=%.6f" % metrics["M_27_abs_r_over_q01_min_path_loss"])
    print("flip_fraction=%.6f  path_clip_ratio=%.6f" % (
        metrics["M_29_flip_fraction_test"], metrics["M_30_path_clip_ratio"],
    ))
    print("M-27=%s M-28=%s M-29=%s M-30=%s" % tuple(
        report["verdict"][key] for key in ("M_27", "M_28", "M_29", "M_30")
    ))
    print("artifact=%s" % out)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell", required=True, choices=sorted(CELL_SPECS))
    parser.add_argument("--out", default=None)
    parser.add_argument("--relative", action="store_true")
    args = parser.parse_args(argv)
    out = args.out or (relative_artifact_path(args.cell) if args.relative else artifact_path(args.cell))
    report = run_relative_cell(args.cell) if args.relative else run_cell(args.cell)
    write_json(out, report)
    (_print_relative_report if args.relative else _print_report)(report, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
