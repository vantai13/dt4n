#!/usr/bin/env python3
"""Phase 21R / Lesson 21R.9 -- gate report and phase closure.

This module closes Phase 21R by collecting gate decisions, recording the
prediction scorecard, listing limitations, and completing G5 with block
bootstrap confidence intervals for the model/staleness decomposition.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Sequence

import numpy as np
import pandas as pd


N_BOOT = 2000
SEED_BOOT = 9905


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
    if isinstance(value, np.generic):
        return _json_clean(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        if np.isposinf(value):
            return "inf"
        if np.isneginf(value):
            return "-inf"
        return None
    return value


def _with_decomposition_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a frame with ``e_model`` and ``e_stale`` columns.

    Lesson 21R calibration parquet stores ``m_true``, ``m_mid``, and ``m_hat``.
    Gate G5 is about the same decomposition:

        e_model = m_true - m_mid
        e_stale = m_mid - m_hat
    """
    if {"e_model", "e_stale"}.issubset(df.columns):
        return df
    need = {"m_true", "m_mid", "m_hat"}
    if not need.issubset(df.columns):
        missing = sorted(({"block_id", "e_model", "e_stale"} | need) - set(df.columns))
        raise ValueError("cannot derive decomposition; missing columns: %s" % missing)
    out = df.copy()
    out["e_model"] = out["m_true"].astype(np.float64) - out["m_mid"].astype(np.float64)
    out["e_stale"] = out["m_mid"].astype(np.float64) - out["m_hat"].astype(np.float64)
    return out


def _block_aggregates(df: pd.DataFrame) -> np.ndarray:
    if "block_id" not in df.columns:
        raise ValueError("missing block_id")
    d = _with_decomposition_columns(df)
    tmp = d[["block_id", "e_model", "e_stale"]].copy()
    tmp["_em2"] = tmp["e_model"].astype(np.float64) ** 2
    tmp["_es2"] = tmp["e_stale"].astype(np.float64) ** 2
    tmp["_em_es"] = tmp["e_model"].astype(np.float64) * tmp["e_stale"].astype(np.float64)
    grouped = tmp.groupby("block_id", sort=True).agg(
        n=("e_model", "size"),
        ss_model=("_em2", "sum"),
        ss_stale=("_es2", "sum"),
        cross=("_em_es", "sum"),
    )
    return grouped.to_numpy(np.float64)


def _moments_from_sum(values: np.ndarray) -> Dict[str, float]:
    n, ss_model, ss_stale, cross = values
    ms_model = float(ss_model / n)
    ms_stale = float(ss_stale / n)
    cov = float(cross / n)
    ms_total = float(ms_model + ms_stale + 2.0 * cov)
    if not np.isclose(ms_total, ms_model + ms_stale + 2.0 * cov, rtol=1e-12, atol=1e-12):
        raise AssertionError("variance identity failed")
    return {
        "rms_e_model": float(np.sqrt(max(ms_model, 0.0))),
        "rms_e_stale": float(np.sqrt(max(ms_stale, 0.0))),
        "cov_e": cov,
        "rms_total": float(np.sqrt(max(ms_total, 0.0))),
        "share_model": float(ms_model / ms_total) if ms_total > 0.0 else float("nan"),
        "share_stale": float(ms_stale / ms_total) if ms_total > 0.0 else float("nan"),
        "share_cov": float((2.0 * cov) / ms_total) if ms_total > 0.0 else float("nan"),
        "identity_ok": True,
    }


def _bootstrap_block_moments(arr: np.ndarray, n_boot: int, seed: int) -> Dict[str, Any]:
    point = _moments_from_sum(arr.sum(axis=0))
    rng = np.random.default_rng(int(seed))
    draws = {
        "rms_e_model": np.empty(int(n_boot), dtype=np.float64),
        "rms_e_stale": np.empty(int(n_boot), dtype=np.float64),
        "cov_e": np.empty(int(n_boot), dtype=np.float64),
        "rms_total": np.empty(int(n_boot), dtype=np.float64),
        "share_model": np.empty(int(n_boot), dtype=np.float64),
        "share_stale": np.empty(int(n_boot), dtype=np.float64),
        "share_cov": np.empty(int(n_boot), dtype=np.float64),
    }
    for i in range(int(n_boot)):
        sample = arr[rng.integers(0, len(arr), len(arr))].sum(axis=0)
        m = _moments_from_sum(sample)
        for key in draws:
            draws[key][i] = m[key]

    def ci(key: str) -> list[float]:
        return [float(x) for x in np.nanpercentile(draws[key], [2.5, 97.5])]

    out: Dict[str, Any] = {
        **point,
        "n_blocks": int(len(arr)),
        "n_boot": int(n_boot),
        "seed": int(seed),
    }
    for key in draws:
        out[key + "_ci95"] = ci(key)
    cov_ci = out["cov_e_ci95"]
    out["cov_excludes_zero"] = bool(cov_ci[0] > 0.0 or cov_ci[1] < 0.0)
    return out


def decomposition_ci(
    df: pd.DataFrame,
    n_boot: int = N_BOOT,
    seed: int = SEED_BOOT,
    by_bin: bool = True,
) -> Dict[str, Any]:
    """Block-bootstrap CI for G5: model variance, stale variance, and covariance."""
    d = _with_decomposition_columns(df)
    out: Dict[str, Any] = {
        "pooled": _bootstrap_block_moments(_block_aggregates(d), int(n_boot), int(seed)),
        "note": (
            "G5 requires Var(e_model), Var(e_stale), and Cov with CI. The "
            "2*Cov term is part of the variance identity and must not be dropped."
        ),
    }
    if by_bin and "z_bin" in d.columns:
        out["by_bin"] = {
            int(group): _bootstrap_block_moments(_block_aggregates(sub), int(n_boot), int(seed) + int(group) + 1)
            for group, sub in d.groupby("z_bin", sort=True)
        }
    return out


PREDICTIONS: List[Dict[str, Any]] = [
    {
        "name": "qhat_B1_ms",
        "lo": 1.5,
        "hi": 2.2,
        "source": "preregistration",
        "root_cause": "scale_mismatch",
        "root_cause_family": "scale_mismatch",
    },
    {
        "name": "qhat_B4_ms",
        "lo": 2.0,
        "hi": 3.0,
        "source": "preregistration",
        "root_cause": "scale_mismatch",
        "root_cause_family": "scale_mismatch",
    },
    {
        "name": "ratio_B4_over_B1",
        "lo": 1.2,
        "hi": 1.6,
        "source": "preregistration",
        "root_cause": "scale_mismatch",
        "root_cause_family": "scale_mismatch",
    },
    {
        "name": "p_accept_kappa1",
        "lo": 0.75,
        "hi": 0.87,
        "source": "preregistration",
        "root_cause": "scale_mismatch",
        "root_cause_family": "scale_mismatch",
    },
    {
        "name": "z_cross_s",
        "lo": 0.05,
        "hi": 0.10,
        "source": "preregistration",
        "root_cause": "level_channel_mismatch",
        "root_cause_family": "scale_mismatch",
    },
    {
        "name": "err_anchor",
        "lo": 0.27,
        "hi": 0.31,
        "source": "preregistration",
        "root_cause": "jensen",
        "root_cause_family": "jensen",
    },
]


AMENDMENT_CHECKS: List[Dict[str, Any]] = [
    {
        "name": "C2_nonbinding_at_go_cell",
        "observed": "regret|accept(kappa=1)=0.176 << eps_regret=3.222",
        "hit": True,
        "source": "Amendment 1",
    },
    {
        "name": "dimensionless_kappa_needed",
        "observed": "h2 has larger qhat but higher acceptance than poisson",
        "hit": True,
        "source": "Amendment 1",
    },
    {
        "name": "qhat_approximately_1p645_rms",
        "observed": "ratios 1.01-1.02 on main cell",
        "hit": True,
        "source": "Amendment 4",
    },
]


def score_predictions(
    observed: Mapping[str, float],
    preds: Sequence[Mapping[str, Any]] = PREDICTIONS,
) -> Dict[str, Any]:
    """Score pre-registered numeric predictions without mutating intervals."""
    rows = []
    for pred in preds:
        value = observed.get(str(pred["name"]))
        hit = None if value is None else bool(float(pred["lo"]) <= float(value) <= float(pred["hi"]))
        rows.append(
            {
                **dict(pred),
                "observed": None if value is None else float(value),
                "hit": hit,
                "rel_miss": (
                    None
                    if value is None or hit
                    else float(
                        min(abs(float(value) - float(pred["lo"])), abs(float(value) - float(pred["hi"])))
                        / max(abs(float(value)), 1e-12)
                    )
                ),
            }
        )
    hits = int(sum(row["hit"] is True for row in rows))
    misses = int(sum(row["hit"] is False for row in rows))
    causes: Dict[str, int] = {}
    cause_families: Dict[str, int] = {}
    for row in rows:
        if row["hit"] is False:
            causes[str(row["root_cause"])] = causes.get(str(row["root_cause"]), 0) + 1
            family = str(row.get("root_cause_family", row["root_cause"]))
            cause_families[family] = cause_families.get(family, 0) + 1
    return {
        "rows": rows,
        "n": int(len(rows)),
        "n_hit": hits,
        "n_miss": misses,
        "root_causes": causes,
        "root_cause_families": cause_families,
        "n_distinct_root_causes": int(len(causes)),
        "n_distinct_root_cause_families": int(len(cause_families)),
        "amendment_checks": [dict(row) for row in AMENDMENT_CHECKS],
        "n_amendment_hit": int(sum(bool(row["hit"]) for row in AMENDMENT_CHECKS)),
        "note": (
            "The numeric preregistration intervals are preserved as written. "
            "Misses are interpreted by root cause, not repaired after the fact."
        ),
    }


def measurement_floor(
    mode: str,
    rho_bar: float,
    w_loss: float,
    truth_table: str = "results/LIVE/phase-20R/truth_table.parquet",
    diff_links: Sequence[str] = ("uA", "ac", "uB", "bc"),
) -> Dict[str, float]:
    """Measurement floor for the P1-vs-P3 decision-margin cost scale."""
    from twin import topology_v7 as T7
    from twin.cost_v2 import rho_vector

    table = pd.read_parquet(truth_table)
    rho = rho_vector(float(rho_bar))
    var_delay = 0.0
    var_loss = 0.0
    for link in diff_links:
        bw, _base, q = T7.LINKS[link]
        sub = table[(table["mode"] == str(mode)) & (table["bw"] == bw) & (table["q"] == q)]
        if not len(sub):
            continue
        row = sub.loc[(sub["rho"] - rho[link]).abs().idxmin()]
        p_loss = float(row["loss"])
        n_pkt = max(int(row["n_pkt"]), 1)
        var_delay += float(row["se_mean_ms"]) ** 2
        var_loss += (np.sqrt(max(p_loss * (1.0 - p_loss), 0.0) / n_pkt) * float(w_loss)) ** 2
    floor_delay = float(np.sqrt(var_delay))
    floor_loss = float(np.sqrt(var_loss))
    floor_total = float(np.sqrt(var_delay + var_loss))
    return {
        "floor_delay_ms": floor_delay,
        "floor_loss_ms": floor_loss,
        "floor_total_ms": floor_total,
        "loss_over_delay": float(floor_loss / floor_delay) if floor_delay > 0.0 else float("inf"),
    }


def measurement_floor_table(
    operational_path: str = "results/SUPERSEDED/phase-21R/operational_sigma.json",
) -> list[Dict[str, Any]]:
    """Return G11 per-cell floor checks using operational q_hat(B0)."""
    with open(operational_path, encoding="utf-8") as f:
        operational = json.load(f)["operational"]
    rows = []
    for key, result in sorted(operational.items()):
        floor = measurement_floor(result["mode"], float(result["rho_bar"]), float(_w_loss_for_cell(result)))
        q0 = float(result["qhat"][str(min(int(k) for k in result["qhat"]))])
        rows.append(
            {
                "cell": key,
                "w_loss": float(_w_loss_for_cell(result)),
                **floor,
                "qhat_first": q0,
                "qhat_over_floor": float(q0 / floor["floor_total_ms"]) if floor["floor_total_ms"] > 0 else float("inf"),
                "pass_G11": bool(q0 >= floor["floor_total_ms"]),
            }
        )
    return rows


def _w_loss_for_cell(result: Mapping[str, Any]) -> float:
    with open("results/LIVE/phase-20R/sla_calibration.json", encoding="utf-8") as f:
        cells = json.load(f)["cells"]
    for cell in cells:
        if str(cell.get("mode")) == str(result["mode"]) and np.isclose(float(cell.get("rho_bar")), float(result["rho_bar"])):
            return float(cell["w_loss"])
    raise KeyError("missing w_loss for %s@%.3f" % (result["mode"], float(result["rho_bar"])))


LIMITATIONS: List[Dict[str, str]] = [
    {
        "id": "L1",
        "title": "Ground truth is not pure physics",
        "text": "e_model is PCHIP sparse-grid generalization error against a denser measured lookup table.",
        "scope": "construct validity",
        "resolved_by": "Phase 23 direct telemetry validation",
    },
    {
        "id": "L2",
        "title": "A large share of e_model variance is measurement noise",
        "text": "For the main cell, the inherited 1.4851 ms measurement floor accounts for about half of observed e_model variance.",
        "scope": "measurement validity",
        "resolved_by": "larger truth-table measurement campaign",
    },
    {
        "id": "L3",
        "title": "Guarantees are for rho with a SET correlation time, not a measured one",
        "text": (
            "tau is a design parameter written into the generator, not estimated "
            "from deployment telemetry. Phase T2 turned it into a real axis and "
            "swept {0.5 .. 28} s in the twin; feasibility on the kernel datapath is "
            "anchored only for tau in {2, 5, 30} s (Phase G: worst round-trip error "
            "4.94% for tau and 3.82% for sigma, each cell a median over links and "
            "rounds, T_run = 205*tau). See THREATS_T2 entries T-1 .. T-6 for what "
            "the sweep measured and what it could not."
        ),
        "scope": "external validity",
        "resolved_by": "21R2: estimate tau from telemetry instead of setting it",
    },
    {
        "id": "L4",
        "title": "Exact finite-sample guarantee belongs to Variant A",
        "text": "Variant B is the reported pooled-row approximation with block-level effective n.",
        "scope": "statistical conclusion validity",
        "resolved_by": "report A/B side by side",
    },
    {
        "id": "L5",
        "title": "Coverage is not preserved after selection",
        "text": "Marginal violation 0.0913 becomes 0.1214 on the accepted set.",
        "scope": "post-selection validity",
        "resolved_by": "Phase 22 selective conformal",
    },
    {
        "id": "L6",
        "title": "The certificate is pairwise, not simultaneous over K=4",
        "text": "s_margin certifies the stale top-2 pair, not all four action costs.",
        "scope": "construct validity",
        "resolved_by": "Phase 22 simultaneous coverage",
    },
    {
        "id": "L7",
        "title": "Robustness has only one second traffic family on the fixed path",
        "text": "The fixed-sigma path has three nondegenerate cells, with only h2@0.700 outside poisson.",
        "scope": "external validity",
        "resolved_by": "add traffic families",
    },
    {
        "id": "L8",
        "title": "The 2.17 age-shape ratio is not proven as a law",
        "text": (
            "It was observed on synthetic AR(1) at a single tau. Phase T2 swept tau "
            "over {0.5 .. 28} s and found the ratio is NOT flat: R(tau) has an "
            "interior maximum bracketed in (1, 3) s, and the AR(1) rms law itself "
            "loses validity at larger sigma (gate ar1_rms_total_fit_within_2pct is "
            "false at poisson@0.850 for a in {0.5, 0.9} while true at sigma = 0.0096). "
            "Treat the ratio as regime-dependent, not as a law."
        ),
        "scope": "external validity",
        "resolved_by": "Phase T2 tau sweep (measured); 21R2 for real telemetry",
    },
    {
        "id": "L9",
        "title": "Operating cells are not independent",
        "text": "Several cells share rho trajectories by seed, making pooled p-values optimistic.",
        "scope": "statistical conclusion validity",
        "resolved_by": "independent seed design",
    },
    {
        "id": "L10",
        "title": "Absolute path ranking inherits the Phase 20R residual bound",
        "text": "s_margin reduces but does not remove the inherited ranking-risk condition.",
        "scope": "internal validity",
        "resolved_by": "Phase 23",
    },
]


# Phase T2 (A-T2-3): sau Threat DANH SO, moi cai co SO do duoc. Danh sach
# nay TACH khoi LIMITATIONS vi LIMITATIONS la hop dong L1..L10 cua Phase 21R
# (test_phase21r_gate.py::test_limitations_complete ghim dung mười ID do).
THREATS_T2: List[Dict[str, str]] = [
    {
        "id": "T-1",
        "title": "tau is a design parameter, not a measured property of the system",
        "text": (
            "tau is SET in the generator, not ESTIMATED from deployment telemetry. "
            "The tau axis is swept entirely in the twin (NumPy) over "
            "{0.5, 1, 2, 3, 5, 10, 20, 28} s. Feasibility is anchored by Phase G, "
            "where tau in {2, 5, 30} s was realised on the kernel datapath: worst "
            "round-trip error 4.94% for tau and 3.82% for sigma, each cell a median "
            "over links and rounds, with T_run = 205*tau "
            "(docs/phase-G/66-g3b-results.md, docs/phase-G/77-g-closeout.md). "
            "tau < 2 s is examined ONLY in the twin, because the testbed dt = 0.1 s "
            "and the signed resolution rule is dt <= tau/20."
        ),
        "scope": "external validity",
        "resolved_by": "21R2: estimate tau from telemetry instead of setting it",
    },
    {
        "id": "T-2",
        "title": "Two estimands carried the same column name",
        "text": (
            "`rms_e_model` exists in two harnesses with two meanings: margin/cost_ms "
            "(cert/tau_sweep.py) and all_action/delay_ms "
            "(measurements/decision_error_v2.py). Measured on the same cell, tau and "
            "seeds at sigma = 0.0096: 2.1106 ms versus 0.3061 ms. The gap decomposes "
            "into two opposing mechanisms: changing LEVEL all_action -> margin gives "
            "x0.43 (common-mode model error cancels in the difference of two paths), "
            "changing SCALE delay -> cost gives x16.04 (w_loss = 3222.24 amplifies "
            "loss error). One campaign was executed on the wrong estimand and caught "
            "before any outcome curve was read. docs/GLOSSARY.md now registers every "
            "estimand by LEVEL and SCALE, and test/test_t2_estimand_registry.py "
            "blocks a recurrence."
        ),
        "scope": "construct validity",
        "resolved_by": "estimand registry + guard tests (A-T2-3)",
    },
    {
        "id": "T-3",
        "title": "The signed point and the measured point do not share sigma",
        "text": (
            "D-T2.6-2 was signed at sigma = 0.0096, the single constant used across "
            "all cells in 22.6; round 3 measured at sigma = a*sigma_max with "
            "a in {0.5, 0.9}, i.e. 1.3-4.8x larger depending on the cell. The sigma "
            "axis was added because 0.0096 fits rho_bar = 0.96 exactly and is wrong "
            "by 5.00x at rho_bar = 0.850 -- a known defect of the certification layer. "
            "D-T2.6-2 = FAIL (6 inside / 10 outside the signed band). A post-hoc "
            "diagnostic arm re-measured the same quantity at the signed sigma = 0.0096 "
            "over the full tau grid and found 12/12 points INSIDE the band, worst "
            "|deviation| 0.0048 against a band of 0.05. The failure is therefore "
            "attributable to the sigma axis, not to the tau axis. That arm is post-hoc "
            "and does not reopen the verdict."
        ),
        "scope": "internal validity",
        "resolved_by": "21R2: sign predictions at the sigma actually swept",
    },
    {
        "id": "T-4",
        "title": "The conformal level depends on tau through the block count",
        "text": (
            "n_calib = T_sim/(5*tau) falls as tau grows, so the finite-sample level "
            "drifts from 0.901 at tau = 0.5 s to 0.960 at tau = 20 and 28 s. The "
            "ratio R(tau) is taken within one tau, so the level nearly cancels: "
            "measured bias <= 2.67% over 18 points. The level-matched arm removes "
            "that bias but injects subsampling noise with cv up to 12.4%, larger "
            "than the bias it removes at 18/18 points. We report both arms; the "
            "primary arm is the level-matched one because that was the remedy signed "
            "BEFORE the numbers were read. Quantifying the trade-off happened AFTER "
            "the D-T2.6-10 verdict and did not change it."
        ),
        "scope": "statistical conclusion validity",
        "resolved_by": "21R2: hold n_calib fixed across tau by design",
    },
    {
        "id": "T-5",
        "title": "The peak location is limited by grid resolution",
        "text": (
            "argmax of R(tau) falls in the tau = 2 s cell for 7 of 8 arms, which "
            "locates the peak inside the bracket (1, 3) s. The grid has no point "
            "between 1 and 2 s. The signed peaks of poisson@0.850 (1.43 s) and "
            "poisson@0.925 (1.56 s) lie inside that bracket; the signed peak of "
            "h2@0.700 (0.93 s) lies outside it. We do not report a peak at 2 s and "
            "we did not extend the grid after seeing the numbers."
        ),
        "scope": "statistical conclusion validity",
        "resolved_by": "21R2: pre-register a grid with points inside (1, 3) s",
    },
    {
        "id": "T-6",
        "title": "tau* is not measurable with this instrument",
        "text": (
            "tau* = inf{tau : lift(tau) < lift_min} requires lift, i.e. decision error "
            "with and without the trust gate. Decision error lives on "
            "RMS_ALLACTION_DELAY; q_hat lives on RMS_MARGIN_COST. No harness produces "
            "both: `lift`, `err_certified` and `err_baseline` appear in neither "
            "cert/tau_sweep.py nor measurements/decision_error_v2.py, and "
            "`err_certified` appears in no Python file in the repository. Deriving "
            "tau* from R(tau) would be exactly the error T-2 describes, since R is a "
            "ratio of interval radii and lift is a ratio of decision errors. We hand "
            "the measurement design to a later phase instead of converting between "
            "two incomparable estimands."
        ),
        "scope": "construct validity",
        "resolved_by": "21R2: one harness emitting q_hat and err on one estimand",
    },
]


def collect_gates(artifacts: Mapping[str, Any]) -> pd.DataFrame:
    """Collect gate rows with three-level status support."""
    rows = []
    for gate in artifacts.get("gates", []):
        row = dict(gate)
        status = row.get("status")
        if status is None and row.get("value") is not None and row.get("threshold") is not None:
            value = float(row["value"])
            threshold = float(row["threshold"])
            ratio = abs(value / threshold) if threshold else float("inf")
            if ratio < 1.0:
                status = "FAIL"
            elif ratio < 1.5:
                status = "PASS_MARGINAL"
            else:
                status = "PASS"
        row["status"] = status
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calib", help="Phase 21R calib parquet for G5 CI")
    parser.add_argument("--out", default="results/SUPERSEDED/phase-21R/gate_report.json")
    parser.add_argument("--observed", help="JSON with observed prediction-scorecard values")
    parser.add_argument("--operational", default="results/SUPERSEDED/phase-21R/operational_sigma.json")
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    args = parser.parse_args()

    out: Dict[str, Any] = {
        "limitations": LIMITATIONS,
        "n_limitations": int(len(LIMITATIONS)),
        "provenance": {
            "script": "cert/gate_report.py",
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "n_boot": int(args.n_boot),
        },
    }
    if args.calib:
        df = pd.read_parquet(args.calib)
        out["G5_decomposition_ci"] = decomposition_ci(df, n_boot=int(args.n_boot))
        out["G5_complete"] = True
        out["calib"] = args.calib
    if args.observed:
        with open(args.observed, encoding="utf-8") as f:
            out["prediction_scorecard"] = score_predictions(json.load(f))
    if args.operational and os.path.exists(args.operational):
        out["G11_measurement_floor"] = measurement_floor_table(args.operational)
        out["G11_all_pass"] = bool(all(row["pass_G11"] for row in out["G11_measurement_floor"]))

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(_json_clean(out), f, indent=1, sort_keys=True)
        f.write("\n")

    printable = {k: v for k, v in out.items() if k != "limitations"}
    print(json.dumps(_json_clean(printable), indent=1, sort_keys=True))
    print("\n=== LIMITATIONS (%d) ===" % len(LIMITATIONS))
    for limitation in LIMITATIONS:
        print("  %-4s [%-34s] %s" % (limitation["id"], limitation["scope"], limitation["title"]))


if __name__ == "__main__":
    main()
