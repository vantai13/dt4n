#!/usr/bin/env python3
"""Phase 21 / Lesson 21.1 - build the conformal calibration table.

One row is one routing-decision time, not one ``(time, action)`` pair. This
keeps the effective sample size tied to blocks and makes the gate quantities
(``gap_twin``, signed-error scores, and ``u``) first-class columns.

The analysis unit is a physical block:
14.35 s = 5*tau_core. It is converted to samples per trace from dt_s.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from measurements.decision_error import (
    _viol_flags,
    build_cost_tables,
    decide,
    drop_warmup_matrix,
    read_trace_matrix,
    sawtooth_age_steps,
)
from twin.topology_v7 import JUMPS, K


# Frozen from Phase 20. Do not recalibrate in Phase 21.
W_LOSS = 1451.3765784675
T_DELAY = 14.513765784675
T_LOSS = 0.010
TAU_CORE = 2.87
B_BLOCK_S = 14.35
WARMUP = 0.20
T0_S = 4.0
SIGMA_RHO = 0.010
EPS_REG = 1e-9

# Pre-registered Phase 21 bins.
AGE_EDGES = (0.06, 0.16, 0.26, 0.36, 0.46, 0.56)
MEASURED_AGE_EDGES = (0.10, 0.30, 0.70)
U_EDGES = (0.0, 1.0, 2.0, 3.0, np.inf)


def block_len_samples(dt_s: float) -> int:
    """Return the 5*tau block length in samples for this trace grid."""
    return max(1, int(round(B_BLOCK_S / float(dt_s))))


def t0_steps(dt_s: float) -> int:
    """Return the common Phase 20 window start in samples for this trace grid."""
    return max(1, int(round(T0_S / float(dt_s))))


def age_edges_for_dt(dt_s: float) -> tuple[float, ...]:
    """Use reduced measured-telemetry age bins when dt aliases the sawtooth."""
    return MEASURED_AGE_EDGES if float(dt_s) >= 0.05 else AGE_EDGES


def _sh(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def provenance(argv: Sequence[str]) -> dict:
    """Return reproducibility metadata, following the repo MAP rules."""
    return {
        "git_hash": _sh("git", "rev-parse", "HEAD"),
        "git_dirty": bool(_sh("git", "status", "--porcelain")),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "script": "cert/build_calib_set.py",
        "argv": list(argv),
        "constants": {
            "w_loss": W_LOSS,
            "t_delay_ms": T_DELAY,
            "t_loss": T_LOSS,
            "tau_core_s": TAU_CORE,
            "b_block_s": B_BLOCK_S,
            "warmup_frac": WARMUP,
            "t0_s": T0_S,
            "sigma_rho": SIGMA_RHO,
            "age_edges": list(AGE_EDGES),
            "measured_age_edges": list(MEASURED_AGE_EDGES),
            "u_edges": ["inf" if not np.isfinite(x) else x for x in U_EDGES],
        },
    }


def _bin_with_edge_warnings(values: np.ndarray, edges: Sequence[float]) -> tuple[np.ndarray, dict]:
    """Digitize values and clip out-of-edge values with explicit diagnostics.

    The offered-load trace has 10 ms samples and should not need clipping. The
    measured trace has coarser telemetry and can alias AoI to 0.0 s or 0.6 s;
    those rows are clipped for a robustness table, with warnings recorded.
    """
    raw = np.digitize(values, edges) - 1
    n_bins = len(edges) - 1
    low = raw < 0
    high = raw >= n_bins
    clipped = np.clip(raw, 0, n_bins - 1)
    return clipped.astype(np.int8), {
        "n_bins": int(n_bins),
        "n_low": int(low.sum()),
        "n_high": int(high.sum()),
        "min_value": float(np.min(values)) if len(values) else None,
        "max_value": float(np.max(values)) if len(values) else None,
        "n_unique_values": int(len(np.unique(values))),
    }


def build_one(rho: np.ndarray, dt_s: float, trace_id: int) -> tuple[pd.DataFrame, dict]:
    """Convert one warmed-up rho trace into calibration rows."""
    n = int(len(rho))
    delay, loss, cost = build_cost_tables(rho, W_LOSS)
    viol = _viol_flags(delay, loss, T_DELAY, T_LOSS)
    opt_all, _tie = decide(cost)

    age = sawtooth_age_steps(n, dt_s)
    t0 = max(t0_steps(dt_s), int(age.max()))
    if t0 >= n:
        raise ValueError("trace is too short after warm-up and common-window cut")
    all_rows = np.arange(t0, n)
    local_block_all = all_rows // block_len_samples(dt_s)
    block_counts_all = np.bincount(local_block_all)
    physical_block_full_all = block_counts_all[local_block_all] == block_len_samples(dt_s)

    z_zero = age[all_rows] == 0
    if z_zero.any():
        print(
            "  [CANH BAO] %d hang co z=0 (twin = su that); loai khoi tap calib"
            % int(z_zero.sum())
        )
    rows = all_rows[~z_zero]
    physical_block_full = physical_block_full_all[~z_zero]
    src = rows - age[rows]
    if (src < 0).any():
        raise ValueError("computed negative source indices")
    if not (src != rows).any():
        print("  [CANH BAO] src == rows for all rows; AoI collapsed to zero")

    y = cost[rows]
    yhat = cost[src]
    e = y - yhat

    a1 = np.argmin(yhat, axis=1)
    e_a1 = e[np.arange(len(rows)), a1]
    s_maxabs = np.abs(e).max(axis=1)
    s_range = e.max(axis=1) - e.min(axis=1)
    s_vs_a1 = np.abs(e - e_a1[:, None]).max(axis=1)

    a_twin = opt_all[src]
    a_opt = opt_all[rows]
    regret = cost[rows, a_twin] - cost[rows, a_opt]
    wrong = (a_twin != a_opt) & (regret > EPS_REG)

    yhat_sorted = np.sort(yhat, axis=1)
    y_sorted = np.sort(y, axis=1)
    gap_twin = yhat_sorted[:, 1] - yhat_sorted[:, 0]
    gap_true = y_sorted[:, 1] - y_sorted[:, 0]

    z_s = age[rows] * float(dt_s)
    sig_z = SIGMA_RHO * np.sqrt(1.0 - np.exp(-2.0 * z_s / TAU_CORE))
    dist = np.min(
        np.abs(rho[src][:, :, None] - np.asarray(JUMPS, dtype=float)[None, None, :]),
        axis=2,
    )
    dist_min = dist.min(axis=1)
    u = dist_min / sig_z

    age_edges = age_edges_for_dt(dt_s)
    z_bin, z_diag = _bin_with_edge_warnings(z_s, age_edges)
    u_bin, u_diag = _bin_with_edge_warnings(u, U_EDGES)
    if z_diag["n_unique_values"] < len(age_edges) - 1:
        print(
            "  [CANH BAO] chi %d muc tuoi khac nhau (dt=%.6gs) - co the bi aliasing"
            % (z_diag["n_unique_values"], float(dt_s))
        )
    if z_diag["n_low"] or z_diag["n_high"]:
        print(
            "  [CANH BAO] %d tuoi duoi bin va %d tuoi tren bin da duoc clip"
            % (z_diag["n_low"], z_diag["n_high"])
        )

    local_block = rows // block_len_samples(dt_s)

    data = {
        "trace_id": np.full(len(rows), int(trace_id), dtype=np.int8),
        "block_id": (int(trace_id) * 100_000 + local_block).astype(np.int32),
        "block_full": physical_block_full,
        "t_idx": rows.astype(np.int32),
        "z_s": z_s.astype(np.float32),
        "z_bin": z_bin,
        "dist_min": dist_min.astype(np.float32),
        "u": u.astype(np.float32),
        "u_bin": u_bin,
        "s_maxabs": s_maxabs.astype(np.float32),
        "s_range": s_range.astype(np.float32),
        "s_vs_a1": s_vs_a1.astype(np.float32),
        "a_twin": a_twin.astype(np.int8),
        "a_opt": a_opt.astype(np.int8),
        "gap_twin": gap_twin.astype(np.float32),
        "gap_true": gap_true.astype(np.float32),
        "regret": regret.astype(np.float32),
        "wrong": wrong,
        "viol_twin": viol[rows, a_twin],
        "viol_opt": viol[rows, a_opt],
    }
    for action in range(K):
        data[f"y_true_{action}"] = y[:, action].astype(np.float32)
        data[f"y_hat_{action}"] = yhat[:, action].astype(np.float32)

    diagnostics = {
        "trace_id": int(trace_id),
        "n_after_warmup": n,
        "dt_s": float(dt_s),
        "t0": int(t0),
        "block_len_samples": int(block_len_samples(dt_s)),
        "block_len_s": float(block_len_samples(dt_s) * float(dt_s)),
        "n_z_zero_excluded": int(z_zero.sum()),
        "n_rows": int(len(rows)),
        "age_edges": list(age_edges),
        "z_bin_diag": z_diag,
        "u_bin_diag": u_diag,
    }
    return pd.DataFrame(data), diagnostics


def build(trace_paths: Sequence[str], out_path: str, dt_s: float | None = None) -> tuple[pd.DataFrame, list[dict]]:
    frames = []
    diagnostics = []
    for trace_id, path in enumerate(trace_paths):
        rho, dt = read_trace_matrix(path, dt_s)
        rho = drop_warmup_matrix(rho, WARMUP)
        print(f"[{trace_id}] {os.path.basename(path)}  n={len(rho)}  dt={dt:.6g}s")
        frame, diag = build_one(rho, dt, trace_id)
        frames.append(frame)
        diagnostics.append(diag)
    df = pd.concat(frames, ignore_index=True)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    df.to_parquet(out_path, index=False)
    return df, diagnostics


def self_check(df: pd.DataFrame) -> list[str]:
    """Return invariant failures. Violations are bugs, not scientific results."""
    failures = []
    if (df.s_maxabs < 0).any():
        failures.append("s_maxabs am")
    if not (df.s_range <= 2.0 * df.s_maxabs + 1e-3).all():
        failures.append("s_range > 2*s_maxabs -> sai truc hoac lech dau")
    if not (df.s_vs_a1 <= df.s_range + 1e-3).all():
        failures.append("s_vs_a1 > s_range -> a1 tinh sai")
    if not (df.regret >= -1e-6).all():
        failures.append("regret am -> a_opt khong phai argmin")
    if not (df.loc[~df.wrong, "regret"].abs() < 1e-6).all():
        failures.append("regret != 0 khi khong sai -> lech chi so hoac tie threshold")
    if not (df.gap_twin >= -1e-6).all():
        failures.append("gap_twin am -> sap xep sai")
    if df.groupby("trace_id")["block_id"].nunique().sum() != df.block_id.nunique():
        failures.append("block_id khong duy nhat toan cuc -> ro ri calib/test")
    if (df.z_bin < 0).any() or (df.z_bin > len(AGE_EDGES) - 2).any():
        failures.append("z_bin ngoai mien hop le")
    if (df.u_bin < 0).any() or (df.u_bin > len(U_EDGES) - 2).any():
        failures.append("u_bin ngoai mien hop le")
    if (df.groupby("z_bin")["s_vs_a1"].max() == 0).any():
        failures.append("mot bin co toan bo score = 0 -> nghi tron z=0 vao calib")
    u_finite = df.loc[df.u.notna(), "u"]
    if not np.isfinite(u_finite).all():
        failures.append("u co gia tri vo han -> sig_z = 0 (z=0?)")
    if len(u_finite) and float(u_finite.max()) > 1e3:
        failures.append("u_max = %.2e qua lon -> nghi chia cho gan 0" % float(u_finite.max()))
    return failures


def qhat_preview(scores: Iterable[float], alpha: float, n_eff: int) -> float:
    """Preview conformal quantile using block count as effective n."""
    k = int(np.ceil((int(n_eff) + 1) * (1.0 - float(alpha))))
    if k > int(n_eff):
        return float("inf")
    return float(np.quantile(np.asarray(list(scores), dtype=float), k / int(n_eff), method="higher"))


def _percentiles(values: np.ndarray, qs: Sequence[int]) -> dict:
    return {f"p{q}": float(np.percentile(values, q)) for q in qs}


def report(
    df: pd.DataFrame,
    *,
    alpha: float = 0.10,
    out_json: str | None = None,
    argv: Sequence[str] = (),
    trace_diagnostics: Sequence[dict] = (),
) -> dict:
    result = {
        "provenance": provenance(argv),
        "trace_diagnostics": list(trace_diagnostics),
    }
    full = df[df.block_full]

    print("\n" + "=" * 74)
    print(
        f"BANG: {len(df):,} hang | {df.block_id.nunique()} block "
        f"({full.block_id.nunique()} block DAY) | {df.trace_id.nunique()} trace"
    )

    print("\n=== SELF-CHECK CAU TRUC ===")
    failures = self_check(df)
    print("  " + ("TAT CA PASS" if not failures else "FAIL: " + "; ".join(failures)))
    result["self_check"] = failures

    print("\n=== V5 KIEM CHUNG NOI TAI - PHAI KHOP PHASE 20 ===")
    err = float(df.wrong.mean())
    d_sla = float(df.viol_twin.mean() - df.viol_opt.mean())
    regret_on_error = float(df.loc[df.wrong, "regret"].mean()) if df.wrong.any() else 0.0
    mean_regret = float(df.regret.mean())
    print(f"  err        = {err:.5f}      Phase 20 (n=5) = 0.18233")
    print(f"  d_sla      = {d_sla:.5f}      Phase 20 (n=5) = 0.07939")
    print(f"  regret|err = {regret_on_error:.3f} ms   Phase 20 trace0 = 33.67")
    print(
        f"  IC1: err x regret|err = {err * regret_on_error:.5f}"
        f"  vs  mean regret = {mean_regret:.5f}"
        f"   (lech {abs(err * regret_on_error - mean_regret):.2e})"
    )
    result["internal_check"] = {
        "err": err,
        "d_sla": d_sla,
        "regret_on_error_ms": regret_on_error,
        "mean_regret_ms": mean_regret,
        "err_abs_diff_from_phase20": abs(err - 0.18233),
        "d_sla_abs_diff_from_phase20": abs(d_sla - 0.07939),
    }

    print("\n=== V4 SO BLOCK MOI O MONDRIAN (z_bin x u_bin) - rang buoc >= 9 ===")
    ct = full.groupby(["z_bin", "u_bin"])["block_id"].nunique().unstack(fill_value=0)
    print(ct.to_string())
    counts = full.groupby(["z_bin", "u_bin"])["block_id"].nunique()
    bad = {f"{z}_{u}": int(v) for (z, u), v in counts.items() if v < 9}
    print("  O VI PHAM (<9 block):", bad if bad else "khong co")
    result["blocks_per_cell"] = {f"{z}_{u}": int(v) for (z, u), v in counts.items()}
    result["sparse_cells_lt_9_blocks"] = bad

    print("\n=== PHAN PHOI GAP COST - THANG DOI CHIEU CUA q_hat ===")
    result["gap"] = {}
    for name in ("gap_twin", "gap_true"):
        values = full[name].to_numpy()
        result["gap"][name] = _percentiles(values, (10, 25, 50, 75, 90, 99))
        print(
            f"  {name}: "
            + "  ".join(f"p{q}={np.percentile(values, q):8.3f}" for q in (10, 25, 50, 75, 90, 99))
        )
    print("  ^ P7: gate ACCEPT khi gap_twin >= q_hat - eps.")

    print(f"\n=== q_hat XEM TRUOC theo z_bin (alpha={alpha}, n_eff = SO BLOCK) ===")
    print(
        f"{'z_bin':>6} {'n_blk':>6} {'2q(s_maxabs,a/K)':>18} "
        f"{'q(s_range,a)':>14} {'q(s_vs_a1,a)':>14} "
        f"{'triet tieu':>11} {'gap_twin p50':>13}"
    )
    result["qhat_preview"] = {}
    for z_bin, sub in full.groupby("z_bin"):
        n_eff = int(sub.block_id.nunique())
        q_bonf = 2.0 * qhat_preview(sub.s_maxabs, alpha / K, n_eff)
        q_range = qhat_preview(sub.s_range, alpha, n_eff)
        q_vs_a1 = qhat_preview(sub.s_vs_a1, alpha, n_eff)
        ratio = q_bonf / q_vs_a1 if q_vs_a1 > 0 else float("inf")
        result["qhat_preview"][int(z_bin)] = {
            "n_blocks": n_eff,
            "two_q_bonf": q_bonf,
            "q_range": q_range,
            "q_vs_a1": q_vs_a1,
            "gap_twin_p50": float(sub.gap_twin.median()),
            "tightening_ratio": ratio,
        }
        print(
            f"{int(z_bin):>6} {n_eff:>6} {q_bonf:>18.3f} {q_range:>14.3f} "
            f"{q_vs_a1:>14.3f} {ratio:>11.2f}x {sub.gap_twin.median():>13.3f}"
        )

    print("\n=== PHAN PHOI s_vs_a1 THEO BIN ===")
    result["s_vs_a1_percentiles"] = {}
    for z_bin, sub in full.groupby("z_bin"):
        values = sub.s_vs_a1.to_numpy()
        med = max(float(np.median(values)), 1e-9)
        p75 = float(np.percentile(values, 75))
        p90 = float(np.percentile(values, 90))
        p99 = float(np.percentile(values, 99))
        result["s_vs_a1_percentiles"][int(z_bin)] = {
            "p50": med,
            "p75": p75,
            "p90": p90,
            "p99": p99,
            "p90_over_p50": p90 / med,
        }
        print(
            f"  z_bin {int(z_bin)}: p50={med:8.4f} p75={p75:8.3f} "
            f"p90={p90:8.3f} p99={p99:9.3f}  p90/p50={p90 / med:7.1f}x"
        )

    if out_json:
        os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True, default=str)
            f.write("\n")
        print(f"\n[ghi] {out_json}")
    return result


def main(argv: Sequence[str] | None = None) -> None:
    argv = sys.argv if argv is None else list(argv)
    parser = argparse.ArgumentParser(description="Build Phase 21 conformal calibration set")
    parser.add_argument("--traces", nargs="+", required=True, help="rho CSV trace files")
    parser.add_argument("--out", required=True, help="output parquet path")
    parser.add_argument("--report-json", default=None, help="optional JSON report path")
    parser.add_argument("--dt", type=float, default=None, help="dt_s if CSV has no dt_s column")
    parser.add_argument("--alpha", type=float, default=0.10)
    args = parser.parse_args(argv[1:])

    df, diagnostics = build(args.traces, args.out, args.dt)
    report(
        df,
        alpha=args.alpha,
        out_json=args.report_json,
        argv=argv,
        trace_diagnostics=diagnostics,
    )
    print(f"\n[ghi] {args.out}  ({os.path.getsize(args.out) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
