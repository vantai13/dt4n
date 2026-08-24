#!/usr/bin/env python3
"""Phase 20R.6 -- H9 separability check from existing parquet artifacts."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from measurements.additivity_check import write_json


MODES = ("poisson", "h2")
Z_KEYS_MAIN = ("0.050", "0.100", "0.200", "0.300", "0.550")
OUT = "results/SUPERSEDED/phase-20R/h9_separability.json"
FIGURE = "docs/phase-20R/figures/decision_error_h9_separability.png"
H9_K_SD_THRESHOLD = 0.15
H9_C_SPEARMAN_THRESHOLD = 0.9
H9_R_THRESHOLD = 0.30
H8B_DELTA_THRESHOLD = 0.02
H8B_CI = "results/SUPERSEDED/phase-20R/margin_cv_ci.json"
H8B_CI_N800K = "results/SUPERSEDED/phase-20R/margin_cv_ci_n800k.json"

DESIGNS = (
    {
        "name": "sigma_fixed",
        "err_path": "results/SUPERSEDED/phase-20R/decision_error_unimodal.parquet",
        "cv_path": "results/SUPERSEDED/phase-20R/margin_cv_unimodal.parquet",
    },
    {
        "name": "operational",
        # amendment 23-60: file DA HA xuong SUPERSEDED/ (truc SLA `self_calibrated`,
        # loi S14). Duong doi theo file de script chay NGUYEN, bit-identical.
        # CHUA chuyen sang `..._slaB.parquet`: doi truc se doi SO cua hinh H9,
        # viec do thuoc lesson so huu hinh do, khong lam lut o day. Ghi `L76`.
        "err_path": "results/SUPERSEDED/phase-20R/decision_error_by_age_by_regime.parquet",
        "cv_path": "results/SUPERSEDED/phase-20R/margin_cv_operational.parquet",
    },
    {
        "name": "a02",
        "err_path": "results/SUPERSEDED/phase-20R/sensitivity_a02.parquet",
        "cv_path": "results/SUPERSEDED/phase-20R/margin_cv_a02.parquet",
    },
)

TAU_DESIGNS = (
    {
        "name": "tau_operational",
        "err_paths": (
            "results/SUPERSEDED/phase-20R/decision_error_tau0.2.parquet",
            "results/SUPERSEDED/phase-20R/decision_error_tau1.0.parquet",
            "results/SUPERSEDED/phase-20R/decision_error_tau5.0.parquet",
        ),
        "cv_path": "results/SUPERSEDED/phase-20R/margin_cv_by_tau_operational.parquet",
    },
)


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def parse_list(text: str) -> Tuple[str, ...]:
    return tuple(part.strip() for part in str(text).split(",") if part.strip())


def normal_cdf_neg(k: float, r: float) -> float:
    if float(r) <= 0.0:
        return 0.0
    return 0.5 * math.erfc(float(k) / (math.sqrt(2.0) * float(r)))


def phi_neg_over_r(k: float, r_values: Sequence[float]) -> np.ndarray:
    return np.asarray([normal_cdf_neg(float(k), float(r)) for r in r_values], dtype=float)


def spearman_no_scipy(x: Sequence[float], y: Sequence[float]) -> float:
    xr = pd.Series(x, dtype=float).rank(method="average")
    yr = pd.Series(y, dtype=float).rank(method="average")
    return float(xr.corr(yr))


def spearman_p_approx(rho: float, n: int) -> float:
    """Normal-tail approximation for display only; avoids scipy dependency."""
    if int(n) < 3 or abs(float(rho)) >= 1.0:
        return 0.0
    t = abs(float(rho)) * math.sqrt((int(n) - 2.0) / max(1.0 - float(rho) * float(rho), 1e-300))
    return float(math.erfc(t / math.sqrt(2.0)))


def fit_gaussian_gap(r_values: Sequence[float], y_values: Sequence[float], c_free: bool = True) -> Dict[str, Any]:
    r = np.asarray(r_values, dtype=float)
    y = np.asarray(y_values, dtype=float)
    best: Tuple[float, float, float, np.ndarray] = (float("inf"), math.nan, math.nan, np.asarray([], dtype=float))
    for step in (0.01, 0.001, 0.0001):
        if math.isnan(best[1]):
            k_values = np.arange(0.01, 3.0 + step / 2.0, step)
        else:
            center = best[1]
            k_values = np.arange(max(0.001, center - 10.0 * step), center + 10.0 * step + step / 2.0, step)
        for k in k_values:
            p = phi_neg_over_r(float(k), r)
            if c_free:
                den = float(np.sum(p * p))
                c = float(np.sum(y * p) / den) if den > 0.0 else 0.0
            else:
                c = 1.0
            pred = c * p
            sse = float(np.sum((pred - y) ** 2))
            if sse < best[0]:
                best = (sse, float(k), float(c), pred)
    pred = best[3]
    return {
        "form": "c*Phi(-k/R)" if c_free else "Phi(-k/R)",
        "n": int(len(y)),
        "k": float(best[1]),
        "c": float(best[2]),
        "mae": float(np.mean(np.abs(pred - y))),
        "rmse": float(np.sqrt(np.mean((pred - y) ** 2))),
    }


def fit_threshold_linear(r_values: Sequence[float], y_values: Sequence[float]) -> Dict[str, Any]:
    r = np.asarray(r_values, dtype=float)
    y = np.asarray(y_values, dtype=float)
    lo = max(0.0, float(np.min(r)) - 0.05)
    hi = min(float(np.max(r)) - 1e-6, 1.2)
    best: Tuple[float, float, float, np.ndarray] = (float("inf"), math.nan, math.nan, np.asarray([], dtype=float))
    for r0 in np.arange(lo, hi, 0.001):
        x = np.maximum(0.0, r - float(r0))
        den = float(np.sum(x * x))
        slope = float(np.sum(y * x) / den) if den > 0.0 else 0.0
        pred = slope * x
        sse = float(np.sum((pred - y) ** 2))
        if sse < best[0]:
            best = (sse, float(r0), slope, pred)
    pred = best[3]
    return {
        "form": "slope*max(0,R-R0)",
        "n": int(len(y)),
        "r0": float(best[1]),
        "slope": float(best[2]),
        "mae": float(np.mean(np.abs(pred - y))),
        "rmse": float(np.sqrt(np.mean((pred - y) ** 2))),
    }


def _err_rows(path: str, z_keys: Optional[Sequence[str]] = None) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df = df[df["mode"].isin(MODES)].copy()
    if z_keys is not None:
        df = df[df["z_key"].isin(tuple(z_keys))].copy()
    cols = ["mode", "rho_bar", "z_key", "z_s", "z_over_tau", "tau_rho"]
    return df.groupby(cols, sort=True)["err_total"].mean().reset_index()


def _cv_rows(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df = df[df["mode"].isin(MODES)].copy()
    return df.groupby(["mode", "rho_bar", "tau_rho"], sort=True)["margin_cv"].mean().reset_index()


def merge_design(err_path: str, cv_path: str, name: str, z_keys: Optional[Sequence[str]] = None) -> pd.DataFrame:
    merged = _err_rows(err_path, z_keys=z_keys).merge(_cv_rows(cv_path), on=["mode", "rho_bar", "tau_rho"], how="inner")
    merged["set"] = str(name)
    return merged


def pooled_three_designs(z_keys: Optional[Sequence[str]] = None) -> pd.DataFrame:
    return pd.concat(
        [merge_design(item["err_path"], item["cv_path"], item["name"], z_keys=z_keys) for item in DESIGNS],
        ignore_index=True,
    )


def tau_operational_rows() -> pd.DataFrame:
    frames = []
    for item in TAU_DESIGNS:
        for path in item["err_paths"]:
            frames.append(merge_design(path, item["cv_path"], item["name"]))
    return pd.concat(frames, ignore_index=True)


def model_comparison(df: pd.DataFrame) -> Dict[str, Any]:
    r = df["margin_cv"].to_numpy(float)
    y = df["err_total"].to_numpy(float)
    return {
        "threshold_linear": fit_threshold_linear(r, y),
        "phi_one_parameter": fit_gaussian_gap(r, y, c_free=False),
        "phi_two_parameter": fit_gaussian_gap(r, y, c_free=True),
    }


def threshold_report(df: pd.DataFrame, threshold: float = H9_R_THRESHOLD) -> Dict[str, Any]:
    low = df[df["margin_cv"] < float(threshold)].copy().sort_values(["margin_cv", "set", "mode", "rho_bar", "z_key"])
    bad = low[low["err_total"] > 0.0].copy()
    high = df[df["margin_cv"] >= float(threshold)].copy().sort_values("margin_cv")
    return {
        "threshold": float(threshold),
        "n_low": int(len(low)),
        "n_low_zero": int((low["err_total"] == 0.0).sum()),
        "n_low_nonzero": int(len(bad)),
        "pass_strict_zero": bool(len(low) > 0 and len(bad) == 0),
        "low_rows": low[["set", "mode", "rho_bar", "z_key", "z_over_tau", "tau_rho", "margin_cv", "err_total"]].to_dict("records"),
        "low_nonzero_rows": bad[["set", "mode", "rho_bar", "z_key", "z_over_tau", "tau_rho", "margin_cv", "err_total"]].to_dict("records"),
        "first_high_rows": high[["set", "mode", "rho_bar", "z_key", "z_over_tau", "tau_rho", "margin_cv", "err_total"]].head(5).to_dict("records"),
    }


def h9_by_group(df: pd.DataFrame, keys: Sequence[str]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for key, group in df.groupby(list(keys), sort=True):
        if not isinstance(key, tuple):
            key = (key,)
        fit = fit_gaussian_gap(group["margin_cv"], group["err_total"], c_free=True)
        row = {name: value for name, value in zip(keys, key)}
        row.update(fit)
        rows.append(row)
    k_values = [float(row["k"]) for row in rows]
    c_values = [float(row["c"]) for row in rows]
    z_values = [float(row.get("z_over_tau", row.get("z_s", 0.0))) for row in rows]
    k_sd = float(np.std(k_values, ddof=1)) if len(k_values) > 1 else 0.0
    c_s = spearman_no_scipy(z_values, c_values) if len(rows) > 1 else math.nan
    return {
        "keys": list(keys),
        "rows": rows,
        "k_sd": k_sd,
        "k_sd_threshold": H9_K_SD_THRESHOLD,
        "h9a_pass": bool(k_sd < H9_K_SD_THRESHOLD),
        "c_spearman_vs_z_over_tau": c_s,
        "c_spearman_threshold": H9_C_SPEARMAN_THRESHOLD,
        "h9b_pass": bool(c_s > H9_C_SPEARMAN_THRESHOLD),
    }


def default_h8b_ci_path() -> str:
    return H8B_CI_N800K if os.path.exists(H8B_CI_N800K) else H8B_CI


def h8b_ci_review(path: Optional[str] = None) -> Dict[str, Any]:
    path = path or default_h8b_ci_path()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rows = pd.DataFrame(data["rows"])
    rows = rows[rows["mode"].isin(MODES)].copy()
    base = rows[rows["tau_rho"] == 1.0].set_index(["mode", "rho_bar"])
    checks: List[Dict[str, Any]] = []
    for tau in (0.2, 5.0):
        comp = rows[rows["tau_rho"] == float(tau)].set_index(["mode", "rho_bar"])
        for idx, row in comp.iterrows():
            b = base.loc[idx]
            delta = float(row["margin_cv"] - b["margin_cv"])
            signed_lo = float(row["margin_cv_ci95_lo"] - b["margin_cv_ci95_hi"])
            signed_hi = float(row["margin_cv_ci95_hi"] - b["margin_cv_ci95_lo"])
            checks.append(
                {
                    "mode": idx[0],
                    "rho_bar": float(idx[1]),
                    "tau_rho": float(tau),
                    "delta_vs_tau1": delta,
                    "abs_delta_vs_tau1": abs(delta),
                    "ci95_signed_lo_conservative": signed_lo,
                    "ci95_signed_hi_conservative": signed_hi,
                    "ci95_abs_reaches_threshold_conservative": bool(max(abs(signed_lo), abs(signed_hi)) >= H8B_DELTA_THRESHOLD),
                }
            )
    worst_point = max(checks, key=lambda row: row["abs_delta_vs_tau1"])
    worst_ci = max(checks, key=lambda row: max(abs(row["ci95_signed_lo_conservative"]), abs(row["ci95_signed_hi_conservative"])))
    return {
        "path": path,
        "threshold": H8B_DELTA_THRESHOLD,
        "note": "CI range is conservative from separate R CIs, not a paired delta bootstrap.",
        "worst_point_delta": worst_point,
        "worst_conservative_ci": worst_ci,
        "any_ci_reaches_threshold_conservative": bool(any(row["ci95_abs_reaches_threshold_conservative"] for row in checks)),
        "pass_conservative": bool(not any(row["ci95_abs_reaches_threshold_conservative"] for row in checks)),
        "checks": checks,
    }


def write_figure(df: pd.DataFrame, out_path: str = FIGURE) -> str:
    ensure_parent(out_path)
    cache_dir = "/tmp/matplotlib-%s" % os.getuid()
    os.makedirs(cache_dir, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", cache_dir)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fit = fit_gaussian_gap(df["margin_cv"], df["err_total"], c_free=True)
    xs = np.linspace(max(0.01, float(df["margin_cv"].min()) * 0.8), float(df["margin_cv"].max()) * 1.05, 200)
    ys = float(fit["c"]) * phi_neg_over_r(float(fit["k"]), xs)
    colors = {"sigma_fixed": "#2f6f73", "operational": "#b4452c", "a02": "#3b5ca8"}
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    for name, group in df.groupby("set"):
        ax.scatter(group["margin_cv"], group["err_total"], s=58, color=colors.get(name, "#333333"), label=name, zorder=3)
    ax.plot(xs, ys, color="#111111", linewidth=1.8, label="c Phi(-k/R)")
    ax.axvline(H9_R_THRESHOLD, color="#777777", linestyle="--", linewidth=1.0, label="R=0.30")
    ax.set_xlabel("R = sd(cost margin) / mean(cost margin)")
    ax.set_ylabel("err_total at z=0.55")
    ax.set_title("H9 retrospective gap-crossing form")
    ax.grid(True, color="#dddddd", linewidth=0.7)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)
    return out_path


def analyze(write_fig: bool = True, h8b_ci_path: Optional[str] = None) -> Dict[str, Any]:
    z055 = pooled_three_designs(z_keys=("0.550",))
    rho_s = spearman_no_scipy(z055["margin_cv"], z055["err_total"])
    all_z = pooled_three_designs(z_keys=Z_KEYS_MAIN)
    tau_rows = tau_operational_rows()
    by_z = h9_by_group(all_z, ("z_over_tau",))
    by_tau_z = h9_by_group(tau_rows, ("tau_rho", "z_over_tau"))
    set_mae = []
    for name, group in z055.groupby("set", sort=True):
        fit = fit_gaussian_gap(group["margin_cv"], group["err_total"], c_free=True)
        set_mae.append({"set": name, "n": int(len(group)), "mae": fit["mae"], "rmse": fit["rmse"], "k": fit["k"], "c": fit["c"]})
    report = {
        "phase": "20R.6",
        "script": "measurements.h9_separability",
        "kind": "h9_zero_cost_retrospective_check",
        "pooled_z055": {
            "n": int(len(z055)),
            "spearman_R_err": rho_s,
            "spearman_p_approx": spearman_p_approx(rho_s, len(z055)),
            "model_comparison": model_comparison(z055),
            "threshold_R0p30": threshold_report(z055),
            "set_fit_summary": set_mae,
        },
        "h9_tau1_three_designs": {
            "z_keys": list(Z_KEYS_MAIN),
            "n": int(len(all_z)),
            "by_z_over_tau": by_z,
            "threshold_R0p30_all_z": threshold_report(all_z),
        },
        "h9_tau_operational": {
            "n": int(len(tau_rows)),
            "by_tau_and_z_over_tau": by_tau_z,
            "threshold_R0p30_all_tau": threshold_report(tau_rows),
        },
        "h8b_ci_review": h8b_ci_review(h8b_ci_path),
    }
    report["summary"] = {
        "pooled_spearman_R_err": rho_s,
        "pooled_n": int(len(z055)),
        "h9a_tau1_k_sd": by_z["k_sd"],
        "h9a_tau1_pass": by_z["h9a_pass"],
        "h9b_tau1_c_spearman": by_z["c_spearman_vs_z_over_tau"],
        "h9b_tau1_pass": by_z["h9b_pass"],
        "h9a_tau_operational_k_sd": by_tau_z["k_sd"],
        "h9a_tau_operational_pass": by_tau_z["h9a_pass"],
        "h9b_tau_operational_c_spearman": by_tau_z["c_spearman_vs_z_over_tau"],
        "h9b_tau_operational_pass": by_tau_z["h9b_pass"],
        "h9c_R0p30_z055_pass": report["pooled_z055"]["threshold_R0p30"]["pass_strict_zero"],
        "h9c_R0p30_all_z_pass": report["h9_tau1_three_designs"]["threshold_R0p30_all_z"]["pass_strict_zero"],
        "h9c_R0p30_all_tau_pass": report["h9_tau_operational"]["threshold_R0p30_all_tau"]["pass_strict_zero"],
        "h8b_ci_touches_0p02_conservative": report["h8b_ci_review"]["any_ci_reaches_threshold_conservative"],
    }
    if write_fig:
        report["figure"] = write_figure(z055)
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--h8b-ci", default="", help="margin_cv_ci JSON; defaults to n800k artifact when present")
    ap.add_argument("--no-figure", action="store_true")
    args = ap.parse_args(argv)
    report = analyze(write_fig=not args.no_figure, h8b_ci_path=args.h8b_ci or None)
    write_json(args.out, report)
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print("h9 -> %s" % args.out)
    if "figure" in report:
        print("plot -> %s" % report["figure"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
