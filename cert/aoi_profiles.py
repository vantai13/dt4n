#!/usr/bin/env python3
"""Phase 22 / Lesson 22.7 -- non-uniform Age of Information.

21R shifted the whole 8-dimensional rho vector by one common lag. A real
collector polls links on a schedule, so link ``l`` carries age ``z + d_l``.
This module measures what that assumption costs.

The comparison is centred: each profile is advanced by its mean offset before
per-link offsets are applied. That keeps the mean age matched to U0 and isolates
the spread of per-link ages. For AR(1), the Jensen gap scales as
``Var(d) / tau**2``; with the realistic profiles here, that is far below the
sampling noise floor.
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
from cert.build_calib_set_v2 import Z_EDGES_PRIMARY, assign_bin, block_len, split_by_block
from cert.conformal_v2 import conformal_level, empirical_qhat
from cert.simultaneous_score import ALPHA
from twin import topology_v7 as T7


PROFILES = ("U0", "U1", "U2", "PC4")
KAPPA_REPORT = (0.0, 0.5, 1.0, 2.0)
Z_REP = (0.077, 0.425)
N_BOOT = 2000
SEED_BOOT = 22700
MIN_BLOCKS = int(np.ceil(1.0 / ALPHA)) - 1


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


def _parse_profiles(text: str) -> tuple[str, ...]:
    vals = tuple(x.strip() for x in str(text).split(",") if x.strip())
    if not vals:
        raise ValueError("can it nhat mot ho so AoI")
    unknown = sorted(set(vals) - set(PROFILES))
    if unknown:
        raise ValueError("ho so khong hop le: %s" % unknown)
    return vals


def _safe_ratio(num: float, den: float) -> float:
    return float(num / den) if np.isfinite(num) and np.isfinite(den) and float(den) != 0.0 else float("nan")


def _str_bin(g: Any) -> str:
    return str(int(g))


def centred_offsets(profile: str, dt: float = V3.DT) -> tuple[np.ndarray, int, Dict[str, Any]]:
    """Return per-link offsets, integer mean shift, and spread metadata."""
    off = V3.offset_steps(str(profile), float(dt))
    shift = int(round(float(off.mean())))
    ms = off.astype(np.float64) * float(dt) * 1000.0
    nominal = np.asarray(V3.AOI_PROFILES[str(profile)], dtype=np.float64)
    stats = {
        "mean_ms": float(ms.mean()),
        "sd_ms": float(ms.std(ddof=0)),
        "min_ms": float(ms.min()),
        "max_ms": float(ms.max()),
        "shift_steps": int(shift),
        "shift_ms": float(shift * float(dt) * 1000.0),
        "residual_mean_ms": float(ms.mean() - shift * float(dt) * 1000.0),
        "nominal_mean_ms": float(nominal.mean()),
        "quantization_max_abs_ms": float(np.abs(ms - nominal).max()),
    }
    return off, shift, stats


def jensen_gap_theory(z_bar: float, off_ms: np.ndarray, tau: float = V3.TAU) -> Dict[str, float]:
    """Exact and second-order Jensen gap of h(z)=1-exp(-z/tau)."""
    z_bar = float(z_bar)
    tau = float(tau)
    if tau <= 0.0:
        raise ValueError("tau phai duong")
    d = (np.asarray(off_ms, dtype=np.float64) - float(np.mean(off_ms))) / 1000.0

    def h(z_s: float) -> float:
        return 1.0 - math.exp(-float(z_s) / tau)

    h0 = h(z_bar)
    exact = float(np.mean([h(z_bar + float(di)) for di in d])) - h0
    second = -0.5 * math.exp(-z_bar / tau) * float(np.var(d)) / (tau ** 2)
    rel_h = exact / h0 if h0 != 0.0 else float("nan")
    return {
        "z_bar": z_bar,
        "tau": tau,
        "h_at_zbar": h0,
        "gap_exact": exact,
        "gap_second_order": second,
        "rel_gap_in_h": rel_h,
        "rel_gap_in_rms": math.sqrt(max(0.0, 1.0 + rel_h)) - 1.0 if np.isfinite(rel_h) else float("nan"),
        "var_d_s2": float(np.var(d)),
    }


def zero_offset_path_diagnostic(mode: str, rho_bar: float, seed: int = 101, n: int = 20_000) -> Dict[str, Any]:
    """G22-12: rho-shift and row-shift are identical when all offsets are zero."""
    tt = V3.TruthTable(V3.TRUTH_TABLE)
    cv = V3.C.CostV2(strict_reliable=False)
    cell = V3._load_cell(str(mode), float(rho_bar))
    arr = V3._cell_arrays(tt, cv, cell, seed=int(seed), n=int(n), dt=V3.DT, sigma_override=V3.SIGMA)
    cur, old, _n_z0 = V3._valid_rows(int(n), V3.DT)
    rho = V3.rho_matrix_from_cell(str(mode), float(rho_bar), V3.SIGMA, int(seed), tau=V3.TAU, n=int(n), dt=V3.DT)
    row = V3.y_hat_row_shift(arr["c_fresh"], old)
    shifted = V3.y_hat_rho_shift(cv, rho, old, V3.offset_steps("U0"), str(mode), float(arr["w_loss"]))
    return {
        "seed": int(seed),
        "n_rows": int(len(cur)),
        "max_abs_row_shift_vs_rho_shift_U0": float(np.abs(row - shifted).max()),
    }


def build_profile(
    mode: str,
    rho_bar: float,
    profile: str,
    seeds: Sequence[int] = V3.SEEDS,
    n: int = V3.N,
    dt: float = V3.DT,
    sigma: float = V3.SIGMA,
    tau: float = V3.TAU,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """Build one centred AoI profile using the v3 measured-truth physics."""
    tt = V3.TruthTable(V3.TRUTH_TABLE)
    cv = V3.C.CostV2(strict_reliable=False)
    cell = V3._load_cell(str(mode), float(rho_bar))
    off, shift, stats = centred_offsets(str(profile), float(dt))
    lb = block_len(float(dt))
    parts: list[pd.DataFrame] = []
    dropped = 0

    for seed in seeds:
        arr = V3._cell_arrays(
            tt,
            cv,
            cell,
            seed=int(seed),
            tau=float(tau),
            n=int(n),
            dt=float(dt),
            sigma_override=float(sigma),
        )
        cur, old, _n_z0 = V3._valid_rows(int(n), float(dt))
        old_adj = old + int(shift)
        need = int(off.max()) + 1
        keep = (old_adj >= need) & (old_adj <= cur)
        dropped += int((~keep).sum())
        cur = cur[keep]
        old_adj = old_adj[keep]

        rho = V3.rho_matrix_from_cell(
            str(cell["mode"]),
            float(cell["rho_bar"]),
            float(arr["sigma_rho"]),
            int(seed),
            tau=float(tau),
            n=int(n),
            dt=float(dt),
        )
        y_true = arr["c_true"][cur]
        y_hat = V3.y_hat_rho_shift(cv, rho, old_adj, off, str(cell["mode"]), float(arr["w_loss"]))
        y_mid = arr["c_fresh"][cur]

        order = V3.SS.top_k_by_twin(y_hat)
        row = np.arange(len(cur))
        a1, a2 = order[:, 0], order[:, 1]
        pair = V3.SS.pair_scores(y_true, y_hat)
        mh = V3.SS.pair_margins_hat(y_hat)
        mt = V3.SS.pair_margins_true(y_true, y_hat)
        z_bar = (cur - old_adj + float(off.mean())) * float(dt)
        z_clip = np.clip(z_bar, Z_EDGES_PRIMARY[0], Z_EDGES_PRIMARY[-1])

        parts.append(
            pd.DataFrame(
                {
                    "seed": np.full(len(cur), int(seed), np.int16),
                    "block_id": (int(seed) * 100_000 + cur // lb).astype(np.int32),
                    "t_idx": cur.astype(np.int32),
                    "z_s": z_bar.astype(np.float32),
                    "z_bin": assign_bin(z_clip, Z_EDGES_PRIMARY),
                    "z_clipped": ((z_bar < Z_EDGES_PRIMARY[0]) | (z_bar > Z_EDGES_PRIMARY[-1])),
                    "a1": a1.astype(np.int8),
                    "a2": a2.astype(np.int8),
                    "m_hat": mh[:, 0].astype(np.float32),
                    "m_true": mt[:, 0].astype(np.float32),
                    "m_mid": (y_mid[row, a2] - y_mid[row, a1]).astype(np.float32),
                    "s_margin": pair[:, 0].astype(np.float32),
                    "s_sim": pair.max(axis=1).astype(np.float32),
                    "wrong": (np.asarray(y_hat).argmin(axis=1) != arr["a_true"][cur]),
                    "aoi_profile": np.full(len(cur), str(profile), dtype=object),
                }
            )
        )

    df = split_by_block(pd.concat(parts, ignore_index=True))
    meta = {
        "profile": str(profile),
        "offset_ms": [float(x) for x in V3.AOI_PROFILES[str(profile)]],
        "offset_steps": [int(x) for x in off],
        "link_order": list(T7.LINK_NAMES),
        "rows_dropped": int(dropped),
        "z_bar_mean": float(df["z_s"].mean()),
        "frac_clipped": float(df["z_clipped"].mean()),
        **stats,
    }
    return df, meta


def qhat_by_bin(df: pd.DataFrame, score: str = "s_margin", alpha: float = ALPHA) -> Dict[str, float]:
    """Variant-B qhat per age bin, with block-level finite-sample correction."""
    cal = df[df["is_calib"]]
    out: Dict[str, float] = {}
    for group, sub in cal.groupby("z_bin", sort=True):
        n_eff = int(sub["block_id"].nunique())
        out[_str_bin(group)] = empirical_qhat(sub[score].to_numpy(np.float64), conformal_level(n_eff, alpha))
    return out


def coverage_by_bin(df: pd.DataFrame, qhat: Mapping[str, float], score: str = "s_margin") -> Dict[str, float]:
    """Evaluate marginal coverage by age bin on test rows."""
    test = df[~df["is_calib"]]
    out: Dict[str, float] = {}
    for group, sub in test.groupby("z_bin", sort=True):
        q = float(qhat[_str_bin(group)])
        out[_str_bin(group)] = float((sub[score].to_numpy(np.float64) <= q).mean()) if len(sub) else 1.0
    return out


def evaluate_kappas(
    df: pd.DataFrame,
    qhat: Mapping[str, float],
    kappas: Sequence[float] = KAPPA_REPORT,
    score: str = "s_margin",
    alpha: float = ALPHA,
) -> tuple[Dict[str, Any], float, float]:
    """Evaluate 21R-style acceptance using the profile-specific qhat."""
    test = df[~df["is_calib"]]
    q = test["z_bin"].map({int(k): float(v) for k, v in qhat.items()}).to_numpy(np.float64)
    s = test[score].to_numpy(np.float64)
    mh = test["m_hat"].to_numpy(np.float64)
    wrong = test["wrong"].to_numpy(bool)
    viol = s > q
    anchor = float(wrong.mean()) if len(test) else float("nan")
    coverage = float((~viol).mean()) if len(test) else 1.0
    out: Dict[str, Any] = {}
    for kappa in kappas:
        acc = mh >= float(kappa) * q
        n_acc = int(acc.sum())
        err_acc = float(wrong[acc].mean()) if n_acc else float("nan")
        viol_acc = float(viol[acc].mean()) if n_acc else float("nan")
        out["%.2f" % float(kappa)] = {
            "kappa": float(kappa),
            "acceptance": float(acc.mean()) if len(acc) else 0.0,
            "err_given_accept": err_acc,
            "risk_ratio": _safe_ratio(err_acc, anchor),
            "violation_given_accept": viol_acc,
            "n_accept": n_acc,
            "pass_coverage": bool(n_acc and viol_acc <= float(alpha) + 1e-12),
            "scale": "cost_ms",
            "level": "margin",
            "rowset": "test rows",
        }
    return out, anchor, coverage


def summarize_profile(
    df: pd.DataFrame,
    meta: Mapping[str, Any],
    qhat: Mapping[str, float],
    kappas: Sequence[float] = KAPPA_REPORT,
    alpha: float = ALPHA,
) -> Dict[str, Any]:
    coverage = coverage_by_bin(df, qhat)
    kappa, anchor, cov_marginal = evaluate_kappas(df, qhat, kappas=kappas, alpha=alpha)
    n_calib = {str(int(g)): int(sub["block_id"].nunique()) for g, sub in df[df["is_calib"]].groupby("z_bin", sort=True)}
    n_test = {str(int(g)): int(sub["block_id"].nunique()) for g, sub in df[~df["is_calib"]].groupby("z_bin", sort=True)}
    return {
        "meta": dict(meta),
        "qhat_margin": {str(k): float(v) for k, v in qhat.items()},
        "qhat_sim": qhat_by_bin(df, "s_sim", alpha),
        "coverage_by_bin": coverage,
        "coverage_marginal": cov_marginal,
        "anchor_err": anchor,
        "ratio_B3_over_B0": _safe_ratio(float(qhat["3"]), float(qhat["0"])),
        "n_rows": int(len(df)),
        "n_blocks": int(df["block_id"].nunique()),
        "n_calib_blocks": n_calib,
        "n_test_blocks": n_test,
        "min_calib_blocks": int(min(n_calib.values())),
        "kappa": kappa,
        "scale": "cost_ms",
        "level": "margin",
        "rowset": "test rows",
    }


def paired_bootstrap_ratios(
    frames: Mapping[str, pd.DataFrame],
    profiles: Sequence[str] = PROFILES,
    score: str = "s_margin",
    alpha: float = ALPHA,
    n_boot: int = N_BOOT,
    seed: int = SEED_BOOT,
) -> Dict[str, Dict[str, Any]]:
    """Bootstrap qhat ratios by resampling the same calibration blocks.

    The same sampled block ids are used for every profile. This common-random-
    numbers design removes most trajectory noise from the ratio.
    """
    profiles = tuple(str(p) for p in profiles)
    calib = {p: frames[p][frames[p]["is_calib"]] for p in profiles}
    block_sets = [set(c["block_id"].unique().tolist()) for c in calib.values()]
    common = np.asarray(sorted(set.intersection(*block_sets)), dtype=np.int64)
    if common.size < MIN_BLOCKS:
        raise ValueError("khong du block chung de bootstrap")
    bins = sorted(int(g) for g in frames[profiles[0]]["z_bin"].unique())
    level = conformal_level(int(common.size), alpha)
    rng = np.random.default_rng(int(seed))

    arrays: Dict[str, Dict[int, Dict[int, np.ndarray]]] = {}
    empty = np.array([], dtype=np.float64)
    for p in profiles:
        arrays[p] = {}
        for g in bins:
            sub = calib[p][calib[p]["z_bin"] == g]
            arrays[p][g] = {
                int(b): s[score].to_numpy(np.float64)
                for b, s in sub.groupby("block_id", sort=False)
            }

    draws: Dict[str, Dict[int, list[float]]] = {p: {g: [] for g in bins} for p in profiles}
    for _ in range(int(n_boot)):
        pick = common[rng.integers(0, len(common), size=len(common))]
        for g in bins:
            q: Dict[str, float] = {}
            for p in profiles:
                vals = np.concatenate([arrays[p][g].get(int(b), empty) for b in pick])
                q[p] = empirical_qhat(vals, level)
            base = q[profiles[0]]
            for p in profiles:
                draws[p][g].append(_safe_ratio(q[p], base))

    out: Dict[str, Dict[str, Any]] = {}
    for p in profiles:
        out[p] = {}
        for g in bins:
            vals = np.asarray(draws[p][g], dtype=np.float64)
            out[p][str(g)] = {
                "ratio_mean": float(vals.mean()),
                "ci95": [float(x) for x in np.percentile(vals, [2.5, 97.5])],
                "n_boot": int(n_boot),
                "n_common_blocks": int(common.size),
                "seed": int(seed),
            }
    return out


def theory_for_profiles(profiles: Sequence[str] = PROFILES, z_values: Sequence[float] = Z_REP) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for p in profiles:
        off, _shift, _stats = centred_offsets(str(p), V3.DT)
        off_ms = off.astype(np.float64) * V3.DT * 1000.0
        out[str(p)] = {"%.3f" % float(z): jensen_gap_theory(float(z), off_ms, V3.TAU) for z in z_values}
    return out


def _ratio_vs_u0(profile_summaries: Mapping[str, Mapping[str, Any]], profiles: Sequence[str]) -> Dict[str, Dict[str, float]]:
    base = profile_summaries["U0"]["qhat_margin"]
    return {
        str(p): {
            str(g): _safe_ratio(float(profile_summaries[str(p)]["qhat_margin"][str(g)]), float(base[str(g)]))
            for g in sorted(base, key=int)
        }
        for p in profiles
    }


def _gates(
    profiles_out: Mapping[str, Mapping[str, Any]],
    ratios: Mapping[str, Mapping[str, float]],
    theory: Mapping[str, Mapping[str, Any]],
    bootstrap: Mapping[str, Mapping[str, Any]],
    zero_diag: Mapping[str, Any],
    alpha: float = ALPHA,
) -> Dict[str, bool]:
    u0_mean = float(profiles_out["U0"]["meta"]["z_bar_mean"])
    pc4_ratio = ratios["PC4"]
    return {
        "G22_12_zero_offset_paths_identical": bool(float(zero_diag["max_abs_row_shift_vs_rho_shift_U0"]) == 0.0),
        "PC22_4_extreme_offset_visible": bool(
            pc4_ratio["0"] < 0.70
            and pc4_ratio["0"] < pc4_ratio["1"] < pc4_ratio["2"] < pc4_ratio["3"] < 1.0
            and all(float(bootstrap["PC4"][g]["ci95"][1]) < 1.0 for g in ("0", "1", "2", "3"))
        ),
        "mean_age_matched_within_one_dt": bool(
            all(abs(float(profiles_out[p]["meta"]["z_bar_mean"]) - u0_mean) <= V3.DT + 1e-6 for p in profiles_out)
        ),
        "jensen_gap_nonpositive": bool(
            all(float(theory[p][z]["gap_exact"]) <= 1e-12 for p in theory for z in theory[p])
        ),
        "realistic_profiles_indistinguishable_from_uniform": bool(
            all(abs(float(ratios[p][g]) - 1.0) < 0.02 for p in ("U1", "U2") for g in ("0", "1", "2", "3"))
            and all(
                float(bootstrap[p][g]["ci95"][0]) <= 1.0 <= float(bootstrap[p][g]["ci95"][1])
                for p in ("U1", "U2")
                for g in ("0", "1", "2", "3")
            )
        ),
        "coverage_all_profiles_at_least_0p88": bool(all(float(profiles_out[p]["coverage_marginal"]) >= 1.0 - float(alpha) - 0.02 for p in profiles_out)),
        "P10_anchor_recomputed_per_profile": bool(abs(float(profiles_out["PC4"]["anchor_err"]) / float(profiles_out["U0"]["anchor_err"]) - 1.0) > 0.10),
        "L13_age_ratio_law_breaks_under_PC4": bool(
            all(2.0 <= float(profiles_out[p]["ratio_B3_over_B0"]) <= 2.2 for p in ("U0", "U1", "U2"))
            and float(profiles_out["PC4"]["ratio_B3_over_B0"]) > 3.0
        ),
    }


def run_profiles(
    mode: str,
    rho_bar: float,
    profiles: Sequence[str] = PROFILES,
    seeds: Sequence[int] = V3.SEEDS,
    n: int = V3.N,
    alpha: float = ALPHA,
    n_boot: int = N_BOOT,
) -> Dict[str, Any]:
    profiles = tuple(str(p) for p in profiles)
    if "U0" not in profiles:
        raise ValueError("U0 phai co mat de tinh ti so")
    frames: Dict[str, pd.DataFrame] = {}
    out_profiles: Dict[str, Any] = {}
    for p in profiles:
        df, meta = build_profile(str(mode), float(rho_bar), p, seeds=seeds, n=int(n))
        qhat = qhat_by_bin(df, "s_margin", alpha)
        frames[p] = df
        out_profiles[p] = summarize_profile(df, meta, qhat, alpha=alpha)

    ratios = _ratio_vs_u0(out_profiles, profiles)
    theory = theory_for_profiles(profiles)
    boot = paired_bootstrap_ratios(frames, profiles=profiles, alpha=alpha, n_boot=int(n_boot))
    zero_diag = zero_offset_path_diagnostic(str(mode), float(rho_bar))
    gates = _gates(out_profiles, ratios, theory, boot, zero_diag, alpha=alpha)
    return {
        "cell": "%s@%.3f" % (str(mode), float(rho_bar)),
        "alpha": float(alpha),
        "profiles_order": list(profiles),
        "profiles": out_profiles,
        "qhat_ratio_vs_U0": ratios,
        "bootstrap_ratio_vs_U0": boot,
        "theory": theory,
        "zero_offset_path_diagnostic": zero_diag,
        "gates": gates,
        "summary": {
            "realistic_null_result": bool(gates["realistic_profiles_indistinguishable_from_uniform"]),
            "pc4_positive_control": bool(gates["PC22_4_extreme_offset_visible"]),
            "L12_closed": bool(gates["realistic_profiles_indistinguishable_from_uniform"] and gates["G22_12_zero_offset_paths_identical"]),
            "L13_opened": bool(gates["L13_age_ratio_law_breaks_under_PC4"]),
            "method_note": "P16: do not predict signs below the noise floor; predict a bound instead.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True)
    parser.add_argument("--rho-bar", type=float, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--profiles", default=",".join(PROFILES))
    parser.add_argument("--seeds", type=int, nargs="+", default=list(V3.SEEDS))
    parser.add_argument("--n", type=int, default=V3.N)
    parser.add_argument("--alpha", type=float, default=ALPHA)
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    args = parser.parse_args()

    result = run_profiles(
        str(args.mode),
        float(args.rho_bar),
        profiles=_parse_profiles(args.profiles),
        seeds=args.seeds,
        n=int(args.n),
        alpha=float(args.alpha),
        n_boot=int(args.n_boot),
    )
    out = {
        **result,
        "provenance": {
            "script": "cert/aoi_profiles.py",
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "seeds": [int(s) for s in args.seeds],
            "n": int(args.n),
            "dt": float(V3.DT),
            "tau": float(V3.TAU),
            "sigma_rho": float(V3.SIGMA),
            "n_boot": int(args.n_boot),
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
