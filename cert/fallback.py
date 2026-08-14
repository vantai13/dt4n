#!/usr/bin/env python3
"""Phase 23 / Lesson 23.1 -- abstain with operational semantics.

Phase 22 measured risk on the accept branch.  A router cannot abstain: when the
certificate rejects, traffic still needs a path.  This module turns rejection
into row-level fallback policies and decomposes total system risk via the law
of total probability.
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

from twin import topology_v7 as T7


K_ACTIONS = len(T7.PATH_NAMES)
SCALES = ("err", "regret", "sla")
POLICIES = ("static", "sticky", "wait")
DT = 0.005
Z_MAX = 0.550
T_SYNC = 0.500


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


def path_static_shortest(topology=T7) -> int:
    """Index of the path with the smallest total base delay."""
    totals = [
        sum(topology.LINKS[link][1] for link in topology.PATHS[name])
        for name in topology.PATH_NAMES
    ]
    return int(np.argmin(totals))


def relcost_matrix(df: pd.DataFrame, k: int = K_ACTIONS) -> np.ndarray:
    """True cost relative to a1, shape (n, k)."""
    n = len(df)
    out = np.full((n, k), np.nan, dtype=np.float64)
    rows = np.arange(n)
    out[rows, df["a1"].to_numpy(np.int64)] = 0.0
    for slot in range(1, k):
        # In calib_set_v3, a_rank_1..3 are the identities of twin ranks 2..4.
        act = df["a_rank_%d" % slot].to_numpy(np.int64)
        out[rows, act] = df["m_true_%d" % slot].to_numpy(np.float64)
    if np.isnan(out).any():
        raise ValueError("a1 + a_rank_2..k khong phu het K hanh dong")
    return out


def loss_matrix(df: pd.DataFrame, scale: str, k: int = K_ACTIONS) -> np.ndarray:
    """Loss for every action at every row, shape (n, k)."""
    n = len(df)
    if scale == "err":
        a_star = df["a_star"].to_numpy(np.int64)
        return (np.arange(k)[None, :] != a_star[:, None]).astype(np.float64)
    if scale == "regret":
        rel = relcost_matrix(df, k)
        return rel - rel.min(axis=1, keepdims=True)
    if scale == "sla":
        cols = ["sla_viol_p%d" % j for j in range(k)]
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError("thieu cot SLA theo duong: %s" % missing)
        return np.column_stack([df[c].to_numpy(np.float64) for c in cols])
    raise ValueError("scale phai thuoc %r, nhan duoc %r" % (SCALES, scale))


def loss_of(df: pd.DataFrame, a_chosen: np.ndarray, scale: str) -> np.ndarray:
    """One incurred loss value per row."""
    lm = loss_matrix(df, scale)
    a = np.asarray(a_chosen, dtype=np.int64)
    if a.shape != (len(df),) or a.min() < 0 or a.max() >= lm.shape[1]:
        raise ValueError("a_chosen phai la (n,) trong [0, K)")
    return lm[np.arange(len(df)), a]


def assert_time_ordered(df: pd.DataFrame) -> None:
    """Stateful fallbacks require sorting by (block_id, t_idx)."""
    b = df["block_id"].to_numpy()
    t = df["t_idx"].to_numpy()
    if not np.all(b[1:] >= b[:-1]):
        raise ValueError("df phai sap tang theo block_id")
    same = b[1:] == b[:-1]
    if not np.all(t[1:][same] > t[:-1][same]):
        raise ValueError("trong moi block, t_idx phai tang nghiem ngat")


def sort_for_stateful(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(["block_id", "t_idx"]).reset_index(drop=True)


def fallback_static(df: pd.DataFrame, accept: np.ndarray) -> np.ndarray:
    """F2 -- use the static shortest path on reject."""
    p_static = path_static_shortest()
    return np.where(np.asarray(accept, bool), df["a_twin"].to_numpy(np.int64), p_static)


def fallback_sticky(df: pd.DataFrame, accept: np.ndarray) -> np.ndarray:
    """F1 -- forward-fill the last accepted twin action within each block."""
    assert_time_ordered(df)
    p_static = path_static_shortest()
    acc = np.asarray(accept, bool)
    seeded = pd.Series(
        np.where(acc, df["a_twin"].to_numpy(np.float64), np.nan),
        index=np.arange(len(df)),
    )
    filled = seeded.groupby(df["block_id"].to_numpy()).ffill()
    return filled.fillna(float(p_static)).to_numpy(np.int64)


def _next_refresh_index(df: pd.DataFrame) -> np.ndarray:
    """Next refresh row inside the same block, or -1 if unavailable."""
    z = df["z_s"].to_numpy(np.float64)
    blk = df["block_id"].to_numpy()
    n = len(df)
    is_refresh = np.zeros(n, dtype=bool)
    is_refresh[1:] = (z[1:] < z[:-1]) & (blk[1:] == blk[:-1])

    nxt = np.full(n, -1, dtype=np.int64)
    carry = -1
    for i in range(n - 1, -1, -1):
        if i + 1 < n and blk[i + 1] != blk[i]:
            carry = -1
        nxt[i] = carry
        if is_refresh[i]:
            carry = i
    return nxt


def fallback_wait(
    df: pd.DataFrame,
    accept: np.ndarray,
    secondary: str = "sticky",
) -> Dict[str, Any]:
    """F3-a -- physical installed-path accounting for one-refresh wait.

    While the controller waits, the data plane keeps forwarding on the route
    that is already installed.  With the preregistered sticky secondary, this is
    exactly F1 at row level; the wait horizon is only a diagnostic.  Scoring
    ``a_twin`` from the next refresh on the original row would use future
    information and is intentionally not done here.
    """
    assert_time_ordered(df)
    acc = np.asarray(accept, bool)
    z = df["z_s"].to_numpy(np.float64)

    if secondary == "sticky":
        a_chosen = fallback_sticky(df, acc)
        equivalent = "sticky"
    elif secondary == "static":
        a_chosen = fallback_static(df, acc)
        equivalent = "static"
    else:
        raise ValueError("secondary phai la 'sticky' hoac 'static'")

    nxt = _next_refresh_index(df)
    wait_s = np.zeros(len(df), dtype=np.float64)

    can_wait = (~acc) & (nxt >= 0)
    tgt = nxt[can_wait]
    retry_ok = acc[tgt]
    idx = np.flatnonzero(can_wait)
    wait_s[idx] = (Z_MAX - z[idx]) + DT

    horizon = 0.500 - z[idx] if idx.size else np.array([], dtype=np.float64)
    a_star = df["a_star"].to_numpy(np.int64)
    drift = (
        float((a_star[idx] == a_star[tgt]).mean())
        if idx.size
        else float("nan")
    )

    return {
        "a_chosen": a_chosen,
        "wait_s": wait_s,
        "n_reject": int((~acc).sum()),
        "n_wait_available": int(can_wait.sum()),
        "n_no_refresh_in_block": int(((~acc) & (nxt < 0)).sum()),
        "retry_accept_rate": float(retry_ok.mean()) if retry_ok.size else float("nan"),
        "secondary": secondary,
        "installed_path_equivalent": equivalent,
        "lookahead_future_share": float((horizon > 0).mean()) if horizon.size else float("nan"),
        "lookahead_horizon_ms_mean": float(horizon.mean() * 1e3) if horizon.size else float("nan"),
        "lookahead_horizon_ms_max": float(horizon.max() * 1e3) if horizon.size else float("nan"),
        "a_star_agree_over_wait": drift,
    }


def apply_fallback(df: pd.DataFrame, accept: np.ndarray, policy: str) -> Dict[str, Any]:
    """Return an action for every row."""
    if policy == "static":
        return {"a_chosen": fallback_static(df, accept), "wait_s": np.zeros(len(df))}
    if policy == "sticky":
        return {"a_chosen": fallback_sticky(df, accept), "wait_s": np.zeros(len(df))}
    if policy == "wait":
        return fallback_wait(df, accept)
    raise ValueError("policy phai thuoc %r" % (POLICIES,))


def _mean_sticky_age_ms(df: pd.DataFrame, acc: np.ndarray) -> float:
    """Mean age of the sticky decision on reject rows."""
    t = df["t_idx"].to_numpy(np.float64) * DT
    last = pd.Series(np.where(acc, t, np.nan)).groupby(df["block_id"].to_numpy()).ffill().to_numpy()
    age = t - last
    age = age[(~acc) & np.isfinite(age)]
    return float(age.mean() * 1e3) if age.size else float("nan")


def _mean_reject_run(df: pd.DataFrame, acc: np.ndarray) -> float:
    """Mean length of consecutive reject runs within blocks."""
    rej = (~acc).astype(np.int64)
    blk = df["block_id"].to_numpy()
    new = np.ones(len(df), dtype=bool)
    new[1:] = (rej[1:] != rej[:-1]) | (blk[1:] != blk[:-1])
    gid = np.cumsum(new) - 1
    lens = np.bincount(gid)
    starts_reject = rej[new] == 1
    return float(lens[starts_reject].mean()) if starts_reject.any() else 0.0


def _initial_state_share(df: pd.DataFrame, acc: np.ndarray) -> float:
    """Reject-row share using the initial P1 state before first accept in block."""
    reject = ~np.asarray(acc, bool)
    ever = pd.Series(acc.astype(np.int64)).groupby(df["block_id"].to_numpy()).cummax().to_numpy(bool)
    initial = reject & (~ever)
    return float(initial.sum() / max(int(reject.sum()), 1))


def sticky_diagnostics(df: pd.DataFrame, accept: np.ndarray) -> Dict[str, Any]:
    """Diagnostics explaining why F1 can be close to F2."""
    acc = np.asarray(accept, bool)
    rej = ~acc
    p_static = path_static_shortest()
    a_twin = df["a_twin"].to_numpy(np.int64)
    a_stky = fallback_sticky(df, acc)
    return {
        "p_sticky_equals_static_given_reject": (
            float((a_stky[rej] == p_static).mean()) if rej.any() else float("nan")
        ),
        "p_twin_equals_static_marginal": float((a_twin == p_static).mean()),
        "p_twin_equals_static_given_accept": (
            float((a_twin[acc] == p_static).mean()) if acc.any() else float("nan")
        ),
        "sticky_age_ms_mean": _mean_sticky_age_ms(df, acc),
        "reject_run_len_mean": _mean_reject_run(df, acc),
        "initial_state_share": _initial_state_share(df, acc),
    }


def risk_decomposition(
    df: pd.DataFrame,
    accept: np.ndarray,
    result: Mapping[str, Any],
    scales: Sequence[str] = SCALES,
) -> Dict[str, Any]:
    """Mean-risk decomposition.

    The identity ``R = P(A)R|A + P(~A)R|~A`` is linear and is only valid for
    means.  It must not be reused for medians, quantiles, or maxima.
    """
    acc = np.asarray(accept, bool)
    a = np.asarray(result["a_chosen"], dtype=np.int64)
    wait = np.asarray(result.get("wait_s", np.zeros(len(df))), dtype=np.float64)
    p_acc = float(acc.mean())
    out: Dict[str, Any] = {
        "p_accept": p_acc,
        "p_reject": 1.0 - p_acc,
        "n_rows": int(len(df)),
        "decision_delay_ms_mean": float(wait.mean() * 1e3),
        "decision_delay_ms_mean_given_reject": float(wait[~acc].mean() * 1e3) if (~acc).any() else 0.0,
        "decision_delay_ms_max": float(wait.max() * 1e3),
    }
    out.update(sticky_diagnostics(df, acc))

    for scale in scales:
        per_row = loss_of(df, a, scale)
        r_acc = float(per_row[acc].mean()) if acc.any() else float("nan")
        r_rej = float(per_row[~acc].mean()) if (~acc).any() else float("nan")
        r_sys = float(per_row.mean())
        out["%s_accept" % scale] = r_acc
        out["%s_reject" % scale] = r_rej
        out["%s_system" % scale] = r_sys
        rebuilt = (
            p_acc * (r_acc if acc.any() else 0.0)
            + (1.0 - p_acc) * (r_rej if (~acc).any() else 0.0)
        )
        out["%s_identity_residual" % scale] = float(abs(rebuilt - r_sys))

        if wait.max() > 0.0:
            w = wait / (wait + T_SYNC)
            sticky = loss_of(df, fallback_sticky(df, acc), scale)
            out["%s_system_exposed" % scale] = float((w * sticky + (1.0 - w) * per_row).mean())

    out["scale"] = "mixed"
    out["level"] = "system"
    out["rowset"] = "rows supplied"
    return out


def paired_block_bootstrap_delta(
    df: pd.DataFrame,
    accept: np.ndarray,
    policy: str,
    scale: str = "err",
    n_boot: int = 2000,
    seed: int = 23101,
) -> Dict[str, Any]:
    """Paired block-bootstrap CI for fallback system risk minus twin anchor."""
    acc = np.asarray(accept, bool)
    a_fb = apply_fallback(df, acc, policy)["a_chosen"]
    a_tw = df["a_twin"].to_numpy(np.int64)

    loss_fb = loss_of(df, a_fb, scale)
    loss_tw = loss_of(df, a_tw, scale)
    diff = loss_fb - loss_tw

    blocks = df["block_id"].to_numpy()
    uniq, inv = np.unique(blocks, return_inverse=True)
    n_blk = len(uniq)
    sum_d = np.bincount(inv, weights=diff, minlength=n_blk)
    cnt = np.bincount(inv, minlength=n_blk).astype(np.float64)

    rng = np.random.default_rng(int(seed))
    draws = np.empty(int(n_boot), dtype=np.float64)
    for b in range(int(n_boot)):
        pick = rng.integers(0, n_blk, size=n_blk)
        draws[b] = sum_d[pick].sum() / cnt[pick].sum()

    point = float(diff.mean())
    ci = np.quantile(draws, [0.025, 0.975])
    return {
        "scale": scale,
        "policy": policy,
        "delta_point": point,
        "delta_ci95": [float(ci[0]), float(ci[1])],
        "delta_se": float(draws.std(ddof=1)),
        "risk_fallback": float(loss_fb.mean()),
        "risk_anchor": float(loss_tw.mean()),
        "n_boot": int(n_boot),
        "seed": int(seed),
        "n_blocks": int(n_blk),
        "n_rows": int(len(df)),
        "n_reject": int((~acc).sum()),
        "p_reject": float((~acc).mean()),
        "nonzero_diff_on_accept": int((diff[acc] != 0).sum()),
        "share_rows_contributing": float((diff != 0).mean()),
        "ci_excludes_zero": bool(ci[0] > 0.0 or ci[1] < 0.0),
        "ci_strictly_improves_anchor": bool(ci[1] < 0.0),
    }


def matched_coverage_control(
    df: pd.DataFrame,
    accept_cert: np.ndarray,
    policy: str = "static",
    scale: str = "err",
    seed: int = 23102,
    n_rep: int = 200,
) -> Dict[str, Any]:
    """Random-reject control at the same coverage as the certificate."""
    acc_cert = np.asarray(accept_cert, bool)
    p_acc = float(acc_cert.mean())
    rng = np.random.default_rng(int(seed))

    a_cert = apply_fallback(df, acc_cert, policy)["a_chosen"]
    a_twin = df["a_twin"].to_numpy(np.int64)
    loss_cert = loss_of(df, a_cert, scale)
    loss_twin = loss_of(df, a_twin, scale)
    r_cert = float(loss_cert.mean())
    r_anchor = float(loss_twin.mean())

    reps = np.empty(int(n_rep), dtype=np.float64)
    if policy == "static":
        lm = loss_matrix(df, scale)
        loss_static = lm[:, path_static_shortest()]
        for i in range(int(n_rep)):
            acc_rnd = rng.random(len(df)) < p_acc
            reps[i] = float(np.where(acc_rnd, loss_twin, loss_static).mean())
    else:
        for i in range(int(n_rep)):
            acc_rnd = rng.random(len(df)) < p_acc
            a_rnd = apply_fallback(df, acc_rnd, policy)["a_chosen"]
            reps[i] = float(loss_of(df, a_rnd, scale).mean())

    ci = np.quantile(reps, [0.025, 0.975])
    return {
        "scale": scale,
        "policy": policy,
        "coverage": p_acc,
        "risk_anchor": r_anchor,
        "risk_cert": r_cert,
        "risk_random_mean": float(reps.mean()),
        "risk_random_ci95": [float(ci[0]), float(ci[1])],
        "risk_random_se": float(reps.std(ddof=1)),
        "value_of_information": float(reps.mean() - r_cert),
        "n_rep": int(n_rep),
        "seed": int(seed),
        "cert_better_than_random_ci95": bool(r_cert < ci[0]),
        "random_worse_than_anchor": bool(reps.mean() > r_anchor),
        "random_ci_low_above_anchor": bool(ci[0] > r_anchor),
    }


def oracle_switch_bound(df: pd.DataFrame, scale: str = "err") -> Dict[str, Any]:
    """Best possible row-wise switch between twin and static P1."""
    p1 = path_static_shortest()
    a_twin = df["a_twin"].to_numpy(np.int64)
    a_p1 = np.full(len(df), p1, dtype=np.int64)
    l_twin = loss_of(df, a_twin, scale)
    l_p1 = loss_of(df, a_p1, scale)
    oracle = np.minimum(l_twin, l_p1)
    return {
        "scale": scale,
        "oracle_switch": float(oracle.mean()),
        "anchor_twin": float(l_twin.mean()),
        "always_p1": float(l_p1.mean()),
        "share_switch_to_p1": float((l_p1 < l_twin).mean()),
        "share_twin_better": float((l_twin < l_p1).mean()),
        "share_tie": float((l_twin == l_p1).mean()),
        "room_closed_by_oracle_vs_anchor": float(l_twin.mean() - oracle.mean()),
    }


def truth_persistence_at_lag(
    df: pd.DataFrame,
    lags_ms: Sequence[float] = (50, 100, 150, 200, 250, 294, 300, 400, 500),
) -> Dict[str, Any]:
    """Autocorrelation of the true best path within each block."""
    a_star = df["a_star"].to_numpy(np.int64)
    blk = df["block_id"].to_numpy()
    probs = np.bincount(a_star, minlength=K_ACTIONS).astype(np.float64)
    probs /= probs.sum()
    p_inf = float(np.square(probs).sum())

    points = []
    out: Dict[str, Any] = {
        "p_infinity": p_inf,
        "a_star_probs": [float(x) for x in probs],
    }
    for lag_ms in lags_ms:
        steps = int(round(float(lag_ms) / (DT * 1e3)))
        if steps <= 0 or steps >= len(df):
            continue
        same_blk = blk[steps:] == blk[:-steps]
        if not same_blk.any():
            continue
        agree = float((a_star[steps:][same_blk] == a_star[:-steps][same_blk]).mean())
        effective_ms = float(steps * DT * 1e3)
        key = "agree_%gms" % float(lag_ms)
        row = {
            "requested_lag_ms": float(lag_ms),
            "effective_lag_ms": effective_ms,
            "steps": int(steps),
            "agree": agree,
            "n_pairs": int(same_blk.sum()),
        }
        out[key] = agree
        points.append(row)

    fit = []
    for row in points:
        ratio = (row["agree"] - p_inf) / max(1.0 - p_inf, 1e-12)
        if 0.0 < ratio < 1.0:
            fit.append((row["effective_lag_ms"] / 1e3, np.log(ratio)))
    if len(fit) >= 2:
        x = np.asarray([p[0] for p in fit], dtype=np.float64)
        y = np.asarray([p[1] for p in fit], dtype=np.float64)
        slope, intercept = np.polyfit(x, y, 1)
        out["tau_a_s_exp_fit"] = float(-1.0 / slope) if slope < 0.0 else float("nan")
        out["exp_fit_intercept"] = float(intercept)
    else:
        out["tau_a_s_exp_fit"] = float("nan")
        out["exp_fit_intercept"] = float("nan")
    out["points"] = points
    return out


def fit_accept_mask(
    df: pd.DataFrame,
    config: str = "C3",
    kappa: float = 0.5,
    alpha: float | None = None,
    multiplicity: str = "bonferroni",
) -> tuple[pd.DataFrame, np.ndarray, Dict[str, Any]]:
    """Fit a Phase 22 config on calib rows and return accept mask on test rows."""
    from cert import config_matrix as CM
    from cert.simultaneous_score import ALPHA

    alpha = ALPHA if alpha is None else float(alpha)
    calib = df[df["is_calib"]]
    test = sort_for_stateful(df[~df["is_calib"]])
    fit = CM.fit_config(calib, config, float(kappa), alpha=alpha, multiplicity=multiplicity)
    qrows = CM._q_rows(test, fit["keys"], fit["_q"], len(fit["score_cols"]))
    accept = CM._accept(test, fit["mhat_cols"], qrows, float(kappa))
    public_fit = {k: v for k, v in fit.items() if k != "_q"}
    return test, accept, public_fit


def run_report(
    df: pd.DataFrame,
    config: str = "C3",
    kappa: float = 0.5,
    alpha: float | None = None,
    multiplicity: str = "bonferroni",
) -> Dict[str, Any]:
    test, accept, fit = fit_accept_mask(df, config, kappa, alpha=alpha, multiplicity=multiplicity)
    policies = {}
    for policy in POLICIES:
        res = apply_fallback(test, accept, policy)
        payload = risk_decomposition(test, accept, res)
        payload.update({k: v for k, v in res.items() if k != "a_chosen" and k != "wait_s"})
        policies[policy] = payload
    a_twin = test["a_twin"].to_numpy(np.int64)
    anchor = {}
    for scale in SCALES:
        per_row = loss_of(test, a_twin, scale)
        anchor["%s_accept" % scale] = float(per_row[accept].mean()) if accept.any() else float("nan")
        anchor["%s_reject" % scale] = float(per_row[~accept].mean()) if (~accept).any() else float("nan")
        anchor["%s_system" % scale] = float(per_row.mean())
    p_acc = float(accept.mean())
    p_rej = 1.0 - p_acc
    err_accept = float(anchor["err_accept"])
    break_even = (
        float((anchor["err_system"] - p_acc * err_accept) / p_rej)
        if p_rej > 0.0
        else float("nan")
    )
    break_even_identity_residual = (
        float(abs(break_even - anchor["err_reject"])) if p_rej > 0.0 else 0.0
    )
    return {
        "config": config,
        "kappa": float(kappa),
        "multiplicity": multiplicity,
        "rowset": "test rows",
        "n_test_rows": int(len(test)),
        "p_static": int(path_static_shortest()),
        "accept": {
            "rate": float(accept.mean()),
            "n_accept": int(accept.sum()),
            "n_reject": int((~accept).sum()),
        },
        "anchor": anchor,
        "break_even_err_reject": break_even,
        "break_even_err_reject_identity_residual": break_even_identity_residual,
        "fit": fit,
        "policies": policies,
        "gates": {
            "G23_1_every_policy_has_rows": bool(all(policies[p]["n_rows"] == len(test) for p in POLICIES)),
            "G23_4_identity": bool(
                all(policies[p]["%s_identity_residual" % s] < 1e-9 for p in POLICIES for s in SCALES)
            ),
            "G23_4b_break_even_identity": bool(break_even_identity_residual < 1e-12),
            "G23_5_delay": bool(
                0.0 < policies["wait"]["decision_delay_ms_mean_given_reject"] < 252.5
                and policies["wait"]["decision_delay_ms_max"] <= (T_SYNC + DT) * 1e3 + 1e-9
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calib", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--cell-label", default="poisson@0.925")
    parser.add_argument("--config", default="C3")
    parser.add_argument("--kappa", type=float, default=0.5)
    parser.add_argument("--alpha", type=float)
    parser.add_argument("--multiplicity", default="bonferroni", choices=("bonferroni", "sidak"))
    args = parser.parse_args()

    df = pd.read_parquet(args.calib)
    report = run_report(
        df,
        config=str(args.config),
        kappa=float(args.kappa),
        alpha=args.alpha,
        multiplicity=str(args.multiplicity),
    )
    out = {
        "cell": str(args.cell_label),
        **report,
        "provenance": {
            "script": "cert/fallback.py",
            "calib": args.calib,
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(_json_clean(out), f, indent=1, sort_keys=True)
        f.write("\n")
    print(json.dumps(_json_clean(out), indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
