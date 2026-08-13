#!/usr/bin/env python3
"""Phase 22 / Lesson 22.6 -- tau sweep for the age-ratio mechanism.

This module reruns the Phase 22 calibration-set physics while overriding the
AR(1) correlation time. The statistical block length follows the correlation
time: one block is always 5 tau, not always 5 seconds.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Sequence

import numpy as np
import pandas as pd

import cert.build_calib_set_v3 as V3
from cert.build_calib_set_v2 import Z_EDGES_PRIMARY, assign_bin, split_by_block
from cert.conformal_v2 import conformal_level, empirical_qhat
from cert.simultaneous_score import ALPHA


TAU_GRID = (0.5, 1.0, 2.0, 2.87, 5.0)
BLOCKS_PER_TAU = 5.0
Z0_REP = 0.077
Z3_REP = 0.425
MIN_BLOCKS = int(np.ceil(1.0 / ALPHA)) - 1

PREREG_RATIO_BANDS: Dict[float, tuple[float, float]] = {
    0.5: (1.77, 2.16),
    1.0: (1.87, 2.29),
    2.0: (1.88, 2.30),
    2.87: (1.86, 2.27),
    5.0: (1.77, 2.17),
}


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
    if isinstance(value, np.ndarray):
        return [_json_clean(x) for x in value.tolist()]
    if isinstance(value, np.generic):
        return _json_clean(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        if np.isposinf(value):
            return "inf"
        if np.isneginf(value):
            return "-inf"
        return None
    return value


def _parse_floats(text: str) -> tuple[float, ...]:
    vals = tuple(float(x.strip()) for x in str(text).split(",") if x.strip())
    if not vals:
        raise ValueError("can it nhat mot gia tri float")
    return vals


def _safe_ratio(num: float, den: float) -> float:
    return float(num / den) if np.isfinite(num) and np.isfinite(den) and float(den) != 0.0 else float("nan")


def _span_rel(values: Sequence[float]) -> float:
    arr = np.asarray(values, dtype=np.float64)
    mean = float(arr.mean())
    return float((arr.max() - arr.min()) / mean) if mean != 0.0 else float("nan")


def block_len_for_tau(tau: float, dt: float = V3.DT) -> int:
    """Return the block length in samples for one 5-tau analysis block."""
    tau = float(tau)
    dt = float(dt)
    if tau <= 0.0:
        raise ValueError("tau phai duong")
    if dt <= 0.0:
        raise ValueError("dt phai duong")
    return int(round(BLOCKS_PER_TAU * tau / dt))


def build_at_tau(
    mode: str,
    rho_bar: float,
    tau: float,
    seeds: Sequence[int] = V3.SEEDS,
    n: int = V3.N,
    dt: float = V3.DT,
    sigma: float = V3.SIGMA,
) -> pd.DataFrame:
    """Build the v3 U0 calibration rows with ``tau`` overridden.

    The measured truth table and the twin model are exactly the Phase 22 v3
    inputs. Only the AR(1) time constant and the derived block length change.
    """
    tau = float(tau)
    tt = V3.TruthTable(V3.TRUTH_TABLE)
    cv = V3.C.CostV2(strict_reliable=False)
    cell = V3._load_cell(str(mode), float(rho_bar))
    lb = block_len_for_tau(tau, dt)
    parts: list[pd.DataFrame] = []

    for seed in seeds:
        arr = V3._cell_arrays(
            tt,
            cv,
            cell,
            seed=int(seed),
            tau=tau,
            n=int(n),
            dt=float(dt),
            sigma_override=float(sigma),
        )
        cur, old, _n_z0 = V3._valid_rows(int(n), float(dt))
        y_true = arr["c_true"][cur]
        y_hat = arr["c_fresh"][old]
        y_mid = arr["c_fresh"][cur]

        order = V3.SS.top_k_by_twin(y_hat)
        a1, a2 = order[:, 0], order[:, 1]
        row = np.arange(len(cur))
        pair = V3.SS.pair_scores(y_true, y_hat)
        mh = V3.SS.pair_margins_hat(y_hat)
        mt = V3.SS.pair_margins_true(y_true, y_hat)
        z_s = (cur - old) * float(dt)

        parts.append(
            pd.DataFrame(
                {
                    "seed": np.full(len(cur), int(seed), np.int16),
                    "block_id": (int(seed) * 100_000 + cur // lb).astype(np.int32),
                    "t_idx": cur.astype(np.int32),
                    "tau": np.full(len(cur), tau, np.float32),
                    "z_s": z_s.astype(np.float32),
                    "z_bin": assign_bin(z_s, Z_EDGES_PRIMARY),
                    "a1": a1.astype(np.int8),
                    "a2": a2.astype(np.int8),
                    "m_hat": mh[:, 0].astype(np.float32),
                    "m_true": mt[:, 0].astype(np.float32),
                    "m_mid": (y_mid[row, a2] - y_mid[row, a1]).astype(np.float32),
                    "s_margin": pair[:, 0].astype(np.float32),
                    "s_sim": pair.max(axis=1).astype(np.float32),
                }
            )
        )

    return split_by_block(pd.concat(parts, ignore_index=True))


def decompose(df: pd.DataFrame) -> pd.DataFrame:
    """Split margin error into model and staleness parts for each exact age."""
    need = {"z_s", "m_true", "m_mid", "m_hat"}
    missing = sorted(need - set(df.columns))
    if missing:
        raise ValueError("thieu cot de phan ra: %s" % missing)

    e_model = df["m_true"].to_numpy(np.float64) - df["m_mid"].to_numpy(np.float64)
    e_stale = df["m_mid"].to_numpy(np.float64) - df["m_hat"].to_numpy(np.float64)
    rows: list[Dict[str, Any]] = []
    tmp = pd.DataFrame({"z_s": df["z_s"].to_numpy(np.float64), "em": e_model, "es": e_stale})
    for z_s, sub in tmp.groupby("z_s", sort=True):
        em = sub["em"].to_numpy(np.float64)
        es = sub["es"].to_numpy(np.float64)
        rms_em = float(np.sqrt(np.mean(em ** 2)))
        rms_es = float(np.sqrt(np.mean(es ** 2)))
        cov = float(np.mean(em * es))
        rows.append(
            {
                "z_s": float(z_s),
                "n": int(len(sub)),
                "rms_e_model": rms_em,
                "rms_e_stale": rms_es,
                "cov_e": cov,
                "rms_total": float(np.sqrt(np.mean((em + es) ** 2))),
                "corr_e": cov / (rms_em * rms_es) if rms_em * rms_es > 0.0 else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def fit_ar1(dec: pd.DataFrame, tau: float) -> Dict[str, Any]:
    """Estimate A, c and model floor, then score the AR(1) RMS law."""
    tau = float(tau)
    if tau <= 0.0:
        raise ValueError("tau phai duong")
    z = dec["z_s"].to_numpy(np.float64)
    sat = np.sqrt(1.0 - np.exp(-z / tau))
    rms_es = dec["rms_e_stale"].to_numpy(np.float64)
    rms_em = dec["rms_e_model"].to_numpy(np.float64)
    cov = dec["cov_e"].to_numpy(np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        a_by_z = rms_es / sat
        c_by_z = 1.0 + 2.0 * cov / (rms_es ** 2)
    finite_a = a_by_z[np.isfinite(a_by_z)]
    finite_c = c_by_z[np.isfinite(c_by_z)]
    if finite_a.size == 0 or finite_c.size == 0:
        raise ValueError("khong the khop AR(1): A/c khong huu han")

    A = float(finite_a.mean())
    c = float(finite_c.mean())
    em = float(rms_em.mean())
    pred = np.sqrt(em ** 2 + c * A ** 2 * (1.0 - np.exp(-z / tau)))
    measured = dec["rms_total"].to_numpy(np.float64)
    return {
        "tau": tau,
        "A": A,
        "A_min": float(finite_a.min()),
        "A_max": float(finite_a.max()),
        "A_spread_pct": float(100.0 * (finite_a.max() - finite_a.min()) / A) if A != 0.0 else float("nan"),
        "c": c,
        "c_min": float(finite_c.min()),
        "c_max": float(finite_c.max()),
        "c_spread_pct": float(100.0 * (finite_c.max() - finite_c.min()) / abs(c)) if c != 0.0 else float("nan"),
        "rms_e_model": em,
        "rms_em_min": float(rms_em.min()),
        "rms_em_max": float(rms_em.max()),
        "rms_em_spread_pct": float(100.0 * (rms_em.max() - rms_em.min()) / em) if em != 0.0 else float("nan"),
        "A_over_em": float(A / em) if em != 0.0 else float("nan"),
        "max_rel_err_vs_measured": float(np.max(np.abs(pred / measured - 1.0))),
    }


def ratio_saturated(tau: float, z0: float = Z0_REP, z3: float = Z3_REP) -> float:
    """Saturated staleness ratio for bins B3/B0."""
    tau = float(tau)
    if tau <= 0.0:
        raise ValueError("tau phai duong")
    return math.sqrt((1.0 - math.exp(-float(z3) / tau)) / (1.0 - math.exp(-float(z0) / tau)))


def ratio_finite(
    tau: float,
    A: float,
    c: float,
    em: float,
    z0: float = Z0_REP,
    z3: float = Z3_REP,
) -> float:
    """Finite-model-floor ratio predicted by the AR(1) decomposition."""
    tau = float(tau)
    if tau <= 0.0:
        raise ValueError("tau phai duong")

    def f(z_s: float) -> float:
        return math.sqrt(float(em) ** 2 + float(c) * float(A) ** 2 * (1.0 - math.exp(-float(z_s) / tau)))

    return f(z3) / f(z0)


def theoretical_peak(
    A: float,
    c: float,
    em: float,
    tau_min: float = 0.05,
    tau_max: float = 20.0,
    n_grid: int = 100_000,
) -> Dict[str, float]:
    """Grid-search the finite-floor theoretical peak of R(tau)."""
    taus = np.linspace(float(tau_min), float(tau_max), int(n_grid), dtype=np.float64)
    vals = np.array([ratio_finite(float(t), A, c, em) for t in taus], dtype=np.float64)
    i = int(np.argmax(vals))
    return {"tau": float(taus[i]), "ratio": float(vals[i])}


def qhat_by_bin(df: pd.DataFrame, score: str = "s_margin", alpha: float = ALPHA) -> Dict[int, float]:
    """Variant-B per-age-bin conformal qhat using block-level n_eff."""
    cal = df[df["is_calib"]]
    out: Dict[int, float] = {}
    for group, sub in cal.groupby("z_bin", sort=True):
        g = int(group)
        n_eff = int(sub["block_id"].nunique())
        level = conformal_level(n_eff, alpha)
        out[g] = empirical_qhat(sub[score].to_numpy(np.float64), level)
    return out


def coverage_by_bin(
    df: pd.DataFrame,
    qhat: Mapping[int, float],
    score: str = "s_margin",
) -> Dict[int, float]:
    """Evaluate per-bin coverage on the test rows."""
    test = df[~df["is_calib"]]
    out: Dict[int, float] = {}
    for group, sub in test.groupby("z_bin", sort=True):
        g = int(group)
        q = float(qhat.get(g, float("inf")))
        out[g] = float((sub[score].to_numpy(np.float64) <= q).mean()) if len(sub) else 1.0
    return out


def _levels_by_bin(n_blocks: Mapping[int, int], alpha: float) -> Dict[int, float | None]:
    return {int(g): conformal_level(int(n), alpha) for g, n in n_blocks.items()}


def _hump(values: Sequence[float]) -> bool:
    vals = [float(x) for x in values]
    return (
        not all(a <= b for a, b in zip(vals, vals[1:]))
        and not all(a >= b for a, b in zip(vals, vals[1:]))
        and 0 < int(np.argmax(vals)) < len(vals) - 1
    )


def summarize(rows: Sequence[Mapping[str, Any]], alpha: float = ALPHA) -> Dict[str, Any]:
    """Return compact gates and across-tau summary statistics."""
    A = [float(r["ar1_fit"]["A"]) for r in rows]
    c = [float(r["ar1_fit"]["c"]) for r in rows]
    em = [float(r["ar1_fit"]["rms_e_model"]) for r in rows]
    ratios = [float(r["ratio_measured"]) for r in rows]
    sat = [float(r["ratio_pred_saturated"]) for r in rows]
    finite = [float(r["ratio_pred_finite"]) for r in rows]
    coverage_ok = []
    for r in rows:
        level = conformal_level(int(r["min_calib_blocks"]), alpha)
        cov = float(np.mean(list(r["coverage"].values())))
        coverage_ok.append(level is not None and level - 0.005 <= cov <= level + 0.020)
    bands_ok = all(
        PREREG_RATIO_BANDS[float(r["tau"])][0] <= float(r["ratio_measured"]) <= PREREG_RATIO_BANDS[float(r["tau"])][1]
        for r in rows
        if float(r["tau"]) in PREREG_RATIO_BANDS
    )
    gates = {
        "G22_10_preregistered_ratio_bands": bool(bands_ok),
        "G22_11_A_independent_of_tau": bool(_span_rel(A) < 0.02 and all(float(r["ar1_fit"]["A_spread_pct"]) < 3.0 for r in rows)),
        "c_independent_of_tau": bool(_span_rel(c) < 0.02),
        "rms_em_independent_of_tau": bool(_span_rel(em) < 0.02),
        "ar1_rms_total_fit_within_2pct": bool(all(float(r["ar1_fit"]["max_rel_err_vs_measured"]) < 0.02 for r in rows)),
        "ratio_is_hump_not_monotone": bool(_hump(ratios)),
        "saturated_ratio_monotone_increasing": bool(all(a < b for a, b in zip(sat, sat[1:]))),
        "saturated_ratio_above_measured": bool(all(s > m for s, m in zip(sat, ratios))),
        "block_s_equals_5tau": bool(all(float(r["block_s"]) == 5.0 * float(r["tau"]) for r in rows)),
        "min_calib_blocks_at_least_9": bool(all(int(r["min_calib_blocks"]) >= MIN_BLOCKS for r in rows)),
        "coverage_drift_matches_finite_sample_level": bool(all(coverage_ok)),
    }
    peak = theoretical_peak(A[1], c[1], em[1]) if len(rows) > 1 else theoretical_peak(A[0], c[0], em[0])
    return {
        "A_range": [float(min(A)), float(max(A))],
        "A_span_pct": float(100.0 * _span_rel(A)),
        "c_range": [float(min(c)), float(max(c))],
        "c_span_pct": float(100.0 * _span_rel(c)),
        "rms_em_range": [float(min(em)), float(max(em))],
        "rms_em_span_pct": float(100.0 * _span_rel(em)),
        "ratio_measured": [float(x) for x in ratios],
        "ratio_pred_finite": [float(x) for x in finite],
        "ratio_pred_saturated": [float(x) for x in sat],
        "ratio_pred_peak_from_tau1_fit": peak,
        "gates": gates,
    }


def sweep(
    mode: str,
    rho_bar: float,
    taus: Sequence[float] = TAU_GRID,
    seeds: Sequence[int] = V3.SEEDS,
    n: int = V3.N,
    alpha: float = ALPHA,
) -> Dict[str, Any]:
    rows: list[Dict[str, Any]] = []
    for tau in taus:
        df = build_at_tau(str(mode), float(rho_bar), float(tau), seeds=seeds, n=int(n))
        dec = decompose(df)
        fit = fit_ar1(dec, float(tau))
        q_margin = qhat_by_bin(df, "s_margin", alpha)
        q_sim = qhat_by_bin(df, "s_sim", alpha)
        n_calib_blocks = {
            int(g): int(sub["block_id"].nunique())
            for g, sub in df[df["is_calib"]].groupby("z_bin", sort=True)
        }
        coverage = coverage_by_bin(df, q_margin, "s_margin")
        rows.append(
            {
                "tau": float(tau),
                "block_s": float(BLOCKS_PER_TAU * float(tau)),
                "block_len_samples": int(block_len_for_tau(float(tau))),
                "n_rows": int(len(df)),
                "n_blocks": int(df["block_id"].nunique()),
                "n_calib_blocks_total": int(df.loc[df["is_calib"], "block_id"].nunique()),
                "n_test_blocks_total": int(df.loc[~df["is_calib"], "block_id"].nunique()),
                "n_calib_blocks": n_calib_blocks,
                "min_calib_blocks": int(min(n_calib_blocks.values())),
                "enough_blocks": bool(min(n_calib_blocks.values()) >= MIN_BLOCKS),
                "conformal_level": _levels_by_bin(n_calib_blocks, alpha),
                "qhat_margin": {int(k): float(v) for k, v in q_margin.items()},
                "qhat_sim": {int(k): float(v) for k, v in q_sim.items()},
                "ratio_measured": _safe_ratio(q_margin.get(3, float("nan")), q_margin.get(0, float("nan"))),
                "ratio_measured_sim": _safe_ratio(q_sim.get(3, float("nan")), q_sim.get(0, float("nan"))),
                "ratio_pred_finite": ratio_finite(float(tau), fit["A"], fit["c"], fit["rms_e_model"]),
                "ratio_pred_saturated": ratio_saturated(float(tau)),
                "coverage": coverage,
                "coverage_mean_by_bin": float(np.mean(list(coverage.values()))),
                "ar1_fit": fit,
                "scale": "cost_ms",
                "level": "margin",
                "rowset": "test rows",
            }
        )
    summary = summarize(rows, alpha)
    return {
        "cell": "%s@%.3f" % (str(mode), float(rho_bar)),
        "alpha": float(alpha),
        "tau_grid": [float(t) for t in taus],
        "z_rep": [float(Z0_REP), float(Z3_REP)],
        "block_rule": "block_s = 5*tau",
        "blocks_per_tau": float(BLOCKS_PER_TAU),
        "min_blocks": int(MIN_BLOCKS),
        "preregistered_ratio_bands": PREREG_RATIO_BANDS,
        "rows": rows,
        "summary": summary,
        "gates": summary["gates"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True)
    parser.add_argument("--rho-bar", type=float, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--taus", default=",".join(str(x) for x in TAU_GRID))
    parser.add_argument("--seeds", type=int, nargs="+", default=list(V3.SEEDS))
    parser.add_argument("--n", type=int, default=V3.N)
    parser.add_argument("--alpha", type=float, default=ALPHA)
    args = parser.parse_args()

    result = sweep(
        str(args.mode),
        float(args.rho_bar),
        taus=_parse_floats(args.taus),
        seeds=args.seeds,
        n=int(args.n),
        alpha=float(args.alpha),
    )
    out = {
        **result,
        "provenance": {
            "script": "cert/tau_sweep.py",
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "seeds": [int(s) for s in args.seeds],
            "n": int(args.n),
            "dt": float(V3.DT),
            "sigma_rho": float(V3.SIGMA),
            "truth_table": V3.TRUTH_TABLE,
            "calibration": V3.CALIBRATION,
        },
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(_json_clean(out), f, indent=1, sort_keys=True)
        f.write("\n")
    print(json.dumps(_json_clean(out), indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
