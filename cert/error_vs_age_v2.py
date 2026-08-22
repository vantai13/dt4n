#!/usr/bin/env python3
"""Phase 21R / Lesson 21R.4 -- error-vs-age curve for Mondrian evidence.

The statistic of interest is a quantile, not a mean: conformal calibration uses
``Q_{1-alpha}(score | age bin)``.  All uncertainty estimates resample whole
physical blocks, never individual rows.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Sequence

import numpy as np
import pandas as pd


ALPHA = 0.10
N_BOOT = 2000
ETA_BOOT = 1000
SEED_BOOT = 4104
BONF = 3


def _as_float_array(values: Sequence[float]) -> np.ndarray:
    return np.asarray(values, dtype=np.float64)


def _json_clean(value: Any) -> Any:
    """Convert numpy scalars and non-finite floats to JSON-friendly values."""
    if isinstance(value, Mapping):
        return {str(k): _json_clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_clean(v) for v in value]
    if isinstance(value, tuple):
        return [_json_clean(v) for v in value]
    if isinstance(value, np.generic):
        return _json_clean(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _git(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def rankdata(values: Sequence[float]) -> np.ndarray:
    """Average ranks for ties, avoiding a hard scipy dependency."""
    arr = _as_float_array(values)
    order = np.argsort(arr, kind="mergesort")
    ranks = np.empty(len(arr), dtype=np.float64)
    i = 0
    while i < len(arr):
        j = i + 1
        while j < len(arr) and arr[order[j]] == arr[order[i]]:
            j += 1
        ranks[order[i:j]] = (i + j - 1) / 2.0
        i = j
    return ranks


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    rx = rankdata(xs)
    ry = rankdata(ys)
    if rx.std(ddof=0) == 0.0 or ry.std(ddof=0) == 0.0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def bin_stats(
    df: pd.DataFrame,
    score: str = "s_margin",
    bin_col: str = "z_bin",
    q: float = 1.0 - ALPHA,
) -> pd.DataFrame:
    """Return one row per age bin and report both row-pooled and block quantiles."""
    rows = []
    for group, sub in df.groupby(bin_col, sort=True):
        s = sub[score].to_numpy(np.float64)
        rms = float(np.sqrt(np.mean(s * s)))
        sd = float(s.std(ddof=0))
        block_q = sub.groupby("block_id", sort=True)[score].quantile(q).to_numpy(np.float64)
        rows.append(
            {
                bin_col: int(group),
                "n": int(s.size),
                "n_block": int(sub["block_id"].nunique()),
                "z_lo": float(sub["z_s"].min()),
                "z_hi": float(sub["z_s"].max()),
                "z_mean": float(sub["z_s"].mean()),
                "mean": float(s.mean()),
                "sd": sd,
                "rms": rms,
                "p50": float(np.percentile(s, 50)),
                "q_pooled": float(np.percentile(s, 100 * q)),
                "q_block_median": float(np.percentile(block_q, 50)),
                "q_of_block_q": float(np.percentile(block_q, 100 * q)),
                "q95": float(np.percentile(s, 95)),
                "q_over_rms": float(np.percentile(s, 100 * q) / rms) if rms > 0.0 else float("nan"),
                "kurtosis": float(np.mean((s - s.mean()) ** 4) / sd**4) if sd > 0.0 else float("nan"),
                "mean_over_rms": float(s.mean() / rms) if rms > 0.0 else float("nan"),
            }
        )
    return pd.DataFrame(rows).sort_values(bin_col).reset_index(drop=True)


def eta_squared(df: pd.DataFrame, score: str = "s_margin", bin_col: str = "z_bin") -> float:
    """Return SS_between / SS_total, an effect size that does not inflate with n."""
    s = df[score].to_numpy(np.float64)
    g = df[bin_col].to_numpy()
    gm = float(s.mean())
    ss_between = 0.0
    for key in np.unique(g):
        mask = g == key
        ss_between += float(mask.sum()) * float(s[mask].mean() - gm) ** 2
    ss_total = float(((s - gm) ** 2).sum())
    return float(ss_between / ss_total) if ss_total > 0.0 else float("nan")


def _block_bin_quantile_matrix(
    df: pd.DataFrame,
    score: str,
    bin_col: str,
    q: float,
) -> pd.DataFrame:
    piv = df.groupby(["block_id", bin_col], sort=True)[score].quantile(q).unstack()
    if piv.isna().any().any():
        raise AssertionError("co (block, bin) rong -- kiem lai ranh gioi bin")
    return piv


def block_bootstrap_quantiles(
    df: pd.DataFrame,
    score: str = "s_margin",
    bin_col: str = "z_bin",
    q: float = 1.0 - ALPHA,
    n_boot: int = N_BOOT,
    seed: int = SEED_BOOT,
) -> np.ndarray:
    """Return ``(n_boot, n_bin)`` draws of block-resampled quantiles."""
    arr = _block_bin_quantile_matrix(df, score, bin_col, q).to_numpy(np.float64)
    rng = np.random.default_rng(int(seed))
    idx = rng.integers(0, arr.shape[0], size=(int(n_boot), arr.shape[0]))
    return np.stack([np.percentile(arr[i], 100 * q, axis=0) for i in idx])


def _block_bin_moments(df: pd.DataFrame, score: str, bin_col: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    tmp = df[[bin_col, "block_id", score]].copy()
    tmp["_score2"] = tmp[score].astype(np.float64) ** 2
    agg = tmp.groupby(["block_id", bin_col], sort=True).agg(
        n=(score, "size"),
        sum_s=(score, "sum"),
        sumsq=("_score2", "sum"),
    )
    counts = agg["n"].unstack().to_numpy(np.float64)
    sums = agg["sum_s"].unstack().to_numpy(np.float64)
    sumsq = agg["sumsq"].unstack().to_numpy(np.float64)
    if np.isnan(counts).any() or np.isnan(sums).any() or np.isnan(sumsq).any():
        raise AssertionError("co (block, bin) rong -- khong bootstrap eta duoc")
    return counts, sums, sumsq


def _eta_from_aggregates(counts: np.ndarray, sums: np.ndarray, sumsq: np.ndarray) -> np.ndarray:
    n_g = counts.sum(axis=1)
    sum_g = sums.sum(axis=1)
    total_n = n_g.sum(axis=1)
    total_sum = sum_g.sum(axis=1)
    gm = total_sum / total_n
    mean_g = np.divide(sum_g, n_g, out=np.zeros_like(sum_g), where=n_g > 0)
    ss_between = (n_g * (mean_g - gm[:, None]) ** 2).sum(axis=1)
    total_sumsq = sumsq.sum(axis=(1, 2))
    ss_total = total_sumsq - (total_sum * total_sum) / total_n
    return np.divide(ss_between, ss_total, out=np.full_like(ss_between, np.nan), where=ss_total > 0)


def block_bootstrap_eta_squared(
    df: pd.DataFrame,
    score: str = "s_margin",
    bin_col: str = "z_bin",
    n_boot: int = ETA_BOOT,
    seed: int = SEED_BOOT + 1,
) -> np.ndarray:
    """Block bootstrap draws for eta squared using sufficient statistics."""
    counts, sums, sumsq = _block_bin_moments(df, score, bin_col)
    rng = np.random.default_rng(int(seed))
    idx = rng.integers(0, counts.shape[0], size=(int(n_boot), counts.shape[0]))
    return _eta_from_aggregates(counts[idx], sums[idx], sumsq[idx])


def monotonicity_test(boot: np.ndarray, conf: float = 0.99, bonf: int = BONF) -> Dict[str, Any]:
    """Test consecutive increases using Bonferroni-adjusted intervals."""
    a = (1.0 - float(conf)) / int(bonf)
    steps = []
    for j in range(boot.shape[1] - 1):
        d = boot[:, j + 1] - boot[:, j]
        lo, hi = np.percentile(d, [100 * a / 2, 100 * (1 - a / 2)])
        steps.append(
            {
                "from_bin": int(j),
                "to_bin": int(j + 1),
                "diff_mean": float(d.mean()),
                "ci_lo": float(lo),
                "ci_hi": float(hi),
                "positive": bool(lo > 0.0),
            }
        )
    n_pos = int(sum(step["positive"] for step in steps))
    return {
        "steps": steps,
        "n_positive": n_pos,
        "n_steps": len(steps),
        "pass_G1_monotone": bool(n_pos >= int(np.ceil(2 * len(steps) / 3))),
        "confidence_family": float(conf),
        "bonferroni_m": int(bonf),
    }


def ratio_test(boot: np.ndarray, threshold: float = 1.3) -> Dict[str, Any]:
    r = boot[:, -1] / boot[:, 0]
    lo, hi = np.percentile(r, [2.5, 97.5])
    return {
        "ratio_mean": float(r.mean()),
        "ci95_lo": float(lo),
        "ci95_hi": float(hi),
        "threshold": float(threshold),
        "pass_H2": bool(lo >= threshold),
    }


def marginal_vs_conditional(
    df: pd.DataFrame,
    score: str = "s_margin",
    bin_col: str = "z_bin",
    q: float = 1.0 - ALPHA,
) -> Dict[str, Any]:
    """Report per-bin coverage if one marginal q-hat is used for all bins."""
    q_marg = float(np.percentile(df[score], 100 * q))
    rows = []
    for group, sub in df.groupby(bin_col, sort=True):
        coverage = float((sub[score] <= q_marg).mean())
        rows.append(
            {
                bin_col: int(group),
                "q_conditional": float(np.percentile(sub[score], 100 * q)),
                "coverage_if_marginal": coverage,
                "gap_from_target": float(coverage - q),
            }
        )
    tab = pd.DataFrame(rows).sort_values(bin_col)
    return {
        "q_marginal": q_marg,
        "per_bin": tab.to_dict(orient="records"),
        "max_over_coverage": float(tab["gap_from_target"].max()),
        "max_under_coverage": float(tab["gap_from_target"].min()),
    }


def sanity_m_hat_invariant(df: pd.DataFrame, bin_col: str = "z_bin", rtol: float = 1e-3) -> Dict[str, Any]:
    """Stationarity check: the marginal distribution of m_hat should not move."""
    quant = df.groupby(bin_col, sort=True)["m_hat"].quantile([0.1, 0.5, 0.9]).unstack()
    med = quant[0.5].to_numpy(np.float64)
    spread = float((med.max() - med.min()) / med.mean()) if med.mean() != 0.0 else float("nan")
    rows = []
    for group, values in quant.iterrows():
        rows.append(
            {
                bin_col: int(group),
                "p10": float(values[0.1]),
                "p50": float(values[0.5]),
                "p90": float(values[0.9]),
            }
        )
    return {
        "m_hat_quantiles_by_bin": rows,
        "m_hat_median_by_bin": [float(x) for x in med],
        "rel_spread": spread,
        "pass": bool(spread < float(rtol)),
    }


def sanity_half_normal(stats: pd.DataFrame) -> Dict[str, Any]:
    """Check whether ``s_margin`` looks close to half-normal in each bin."""
    q_theory = 1.6448536269514722
    k_theory = 3.869177303605973
    mean_theory = float(np.sqrt(2.0 / np.pi))
    q_over = stats["q_over_rms"].to_numpy(np.float64)
    return {
        "q_over_rms": [float(x) for x in q_over],
        "q_over_rms_mean": float(np.nanmean(q_over)),
        "q_over_rms_rel_spread": float((np.nanmax(q_over) - np.nanmin(q_over)) / np.nanmean(q_over)),
        "q_over_rms_theory": q_theory,
        "kurtosis": [float(x) for x in stats["kurtosis"].to_numpy(np.float64)],
        "kurtosis_theory": k_theory,
        "mean_over_rms": [float(x) for x in stats["mean_over_rms"].to_numpy(np.float64)],
        "mean_over_rms_mean": float(np.nanmean(stats["mean_over_rms"].to_numpy(np.float64))),
        "mean_over_rms_theory": mean_theory,
        "consistent": bool(np.allclose(q_over, q_theory, rtol=0.02, equal_nan=False)),
    }


def systematic_bias(df: pd.DataFrame) -> Dict[str, float]:
    """Summarize one-sided score bias and the model/stale mean components."""
    out = {
        "mean_s_signed": float(df["s_signed"].mean()),
        "sd_s_signed": float(df["s_signed"].std(ddof=0)),
        "skew_s_signed": float(((df["s_signed"] - df["s_signed"].mean()) ** 3).mean() / df["s_signed"].std(ddof=0) ** 3),
    }
    if {"m_true", "m_mid", "m_hat"}.issubset(df.columns):
        e_model = df["m_true"].to_numpy(np.float64) - df["m_mid"].to_numpy(np.float64)
        e_stale = df["m_mid"].to_numpy(np.float64) - df["m_hat"].to_numpy(np.float64)
        out["mean_e_model"] = float(e_model.mean())
        out["mean_e_stale"] = float(e_stale.mean())
    else:
        out["mean_e_model"] = float("nan")
        out["mean_e_stale"] = float("nan")
    return out


def analyse(
    df: pd.DataFrame,
    bin_col: str = "z_bin",
    score: str = "s_margin",
    q: float = 1.0 - ALPHA,
    n_boot: int = N_BOOT,
    eta_boot: int = ETA_BOOT,
    seed: int = SEED_BOOT,
) -> Dict[str, Any]:
    st = bin_stats(df, score=score, bin_col=bin_col, q=q)
    boot = block_bootstrap_quantiles(df, score=score, bin_col=bin_col, q=q, n_boot=n_boot, seed=seed)
    eta_point = eta_squared(df, score=score, bin_col=bin_col)
    eta_draws = block_bootstrap_eta_squared(df, score=score, bin_col=bin_col, n_boot=eta_boot, seed=seed + 1)
    eta_ci = np.percentile(eta_draws, [2.5, 97.5])
    return {
        "bin_col": bin_col,
        "score": score,
        "q": float(q),
        "stats": st.to_dict(orient="records"),
        "eta_squared": eta_point,
        "eta_squared_ci95": [float(eta_ci[0]), float(eta_ci[1])],
        "pass_G2_eta": bool(eta_point >= 0.05),
        "monotonicity": monotonicity_test(boot, bonf=max(int(boot.shape[1] - 1), 1)),
        "ratio": ratio_test(boot),
        "mondrian_value": marginal_vs_conditional(df, score=score, bin_col=bin_col, q=q),
        "sanity_half_normal": sanity_half_normal(st),
        "bootstrap": {"n_boot_quantile": int(n_boot), "n_boot_eta": int(eta_boot), "seed": int(seed)},
    }


def _g7_against_20r(
    out: Mapping[str, Any],
    ref_20r: str,
    mode: str,
    rho_bar: float,
) -> Dict[str, Any]:
    ref = pd.read_parquet(ref_20r)
    mask = (ref["mode"].astype(str) == str(mode)) & np.isclose(ref["rho_bar"].astype(float), float(rho_bar))
    ref = ref[mask]
    e20 = ref.groupby("z_s")["err_total"].mean()
    z_probe = [0.05, 0.10, 0.20, 0.30]
    if not all(z in e20.index for z in z_probe):
        return {"rho": float("nan"), "pass": False, "reason": "missing z_probe"}
    qs = [row["q_pooled"] for row in out["results"]["z_bin|s_margin"]["stats"]]
    es = [float(e20.loc[z]) for z in z_probe]
    rho = spearman(qs, es)
    return {"rho": rho, "pass": bool(np.isfinite(rho) and np.isclose(rho, 1.0)), "z_probe": z_probe, "err20": es}


def _forecast_lesson6(df: pd.DataFrame, stats: Sequence[Mapping[str, Any]], bin_col: str = "z_bin") -> Dict[str, Any]:
    rows = []
    total_block_median = 0.0
    total_block_q = 0.0
    total_pooled_q = 0.0
    for row in stats:
        group = int(row[bin_col])
        sub = df[df[bin_col] == group]
        q_block_median = float(row["q_block_median"])
        q_block = float(row["q_of_block_q"])
        q_pooled = float(row["q_pooled"])
        p_block_median = float((sub["m_hat"] >= q_block_median).mean())
        p_block = float((sub["m_hat"] >= q_block).mean())
        p_pooled = float((sub["m_hat"] >= q_pooled).mean())
        rows.append(
            {
                bin_col: group,
                "qhat_block_median": q_block_median,
                "p_accept_block_median": p_block_median,
                "qhat_block_quantile": q_block,
                "p_accept_block_quantile": p_block,
                "qhat_pooled": q_pooled,
                "p_accept_pooled_quantile": p_pooled,
            }
        )
        total_block_median += p_block_median * len(sub)
        total_block_q += p_block * len(sub)
        total_pooled_q += p_pooled * len(sub)
    p_accept_block_median = float(total_block_median / len(df))
    p_accept_block = float(total_block_q / len(df))
    p_accept_pooled = float(total_pooled_q / len(df))
    return {
        "per_bin": rows,
        "p_accept_block_median": p_accept_block_median,
        "p_accept_block_quantile": p_accept_block,
        "p_accept_pooled_quantile": p_accept_pooled,
        "pass_G12_not_too_easy_block_median": bool(p_accept_block_median <= 0.90),
        "pass_G12_not_too_easy_block_quantile": bool(p_accept_block <= 0.90),
        "pass_G12_not_too_easy_pooled_quantile": bool(p_accept_pooled <= 0.90),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calib", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--ref-20r", default="results/SUPERSEDED/phase-20R/decision_error_constant_sigma.parquet")
    parser.add_argument("--mode", required=True)
    parser.add_argument("--rho-bar", type=float, required=True)
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    parser.add_argument("--eta-boot", type=int, default=ETA_BOOT)
    args = parser.parse_args()

    df = pd.read_parquet(args.calib)
    out: Dict[str, Any] = {
        "cell": "%s@%.3f" % (args.mode, float(args.rho_bar)),
        "results": {},
        "provenance": {
            "script": "cert/error_vs_age_v2.py",
            "calib": args.calib,
            "ref_20r": args.ref_20r,
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "alpha": float(ALPHA),
            "n_boot": int(args.n_boot),
            "eta_boot": int(args.eta_boot),
            "seed_boot": int(SEED_BOOT),
        },
    }

    for bin_col in ("z_bin", "z_bin2"):
        for score in ("s_margin", "s_signed", "s_vs_a1", "s_maxabs"):
            out["results"]["%s|%s" % (bin_col, score)] = analyse(
                df,
                bin_col=bin_col,
                score=score,
                n_boot=int(args.n_boot),
                eta_boot=int(args.eta_boot),
                seed=SEED_BOOT,
            )

    out["sanity_m_hat_invariant"] = sanity_m_hat_invariant(df)
    out["systematic_bias"] = systematic_bias(df)
    out["corr_score_vs_m_hat"] = float(np.corrcoef(df["s_margin"], df["m_hat"])[0, 1])
    out["G7_spearman_vs_20R"] = _g7_against_20r(out, args.ref_20r, args.mode, float(args.rho_bar))
    out["forecast_lesson6"] = _forecast_lesson6(df, out["results"]["z_bin|s_margin"]["stats"])

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(_json_clean(out), f, indent=1, sort_keys=True)
        f.write("\n")

    key = out["results"]["z_bin|s_margin"]
    print(
        json.dumps(
            _json_clean(
                {
                    "cell": out["cell"],
                    "eta2": key["eta_squared"],
                    "eta2_ci95": key["eta_squared_ci95"],
                    "monotone": key["monotonicity"],
                    "ratio": key["ratio"],
                    "mondrian": key["mondrian_value"],
                    "half_normal": key["sanity_half_normal"],
                    "m_hat_invariant": out["sanity_m_hat_invariant"],
                    "bias": out["systematic_bias"],
                    "G7_spearman_vs_20R": out["G7_spearman_vs_20R"],
                    "forecast": out["forecast_lesson6"],
                }
            ),
            indent=1,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
