#!/usr/bin/env python3
"""Phase 23 / Lesson 23.1 -- abstain with operational semantics.

Phase 22 measured risk on the accept branch.  A router cannot abstain: when the
certificate rejects, traffic still needs a path.  This module turns rejection
into three measurable fallback policies and decomposes total system risk via
the law of total probability.
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
    """F3-a -- wait once for the next refresh, then fall back to F1/F2."""
    assert_time_ordered(df)
    acc = np.asarray(accept, bool)
    a_twin = df["a_twin"].to_numpy(np.int64)
    z = df["z_s"].to_numpy(np.float64)

    if secondary == "sticky":
        base = fallback_sticky(df, acc)
    elif secondary == "static":
        base = fallback_static(df, acc)
    else:
        raise ValueError("secondary phai la 'sticky' hoac 'static'")

    nxt = _next_refresh_index(df)
    a_chosen = np.where(acc, a_twin, base)
    wait_s = np.zeros(len(df), dtype=np.float64)

    can_wait = (~acc) & (nxt >= 0)
    tgt = nxt[can_wait]
    retry_ok = acc[tgt]
    idx = np.flatnonzero(can_wait)
    a_chosen[idx[retry_ok]] = a_twin[tgt[retry_ok]]
    wait_s[idx] = (Z_MAX - z[idx]) + DT

    return {
        "a_chosen": a_chosen,
        "wait_s": wait_s,
        "n_reject": int((~acc).sum()),
        "n_wait_available": int(can_wait.sum()),
        "n_no_refresh_in_block": int(((~acc) & (nxt < 0)).sum()),
        "retry_accept_rate": float(retry_ok.mean()) if retry_ok.size else float("nan"),
        "secondary": secondary,
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
        "sticky_age_ms_mean": _mean_sticky_age_ms(df, acc),
        "reject_run_len_mean": _mean_reject_run(df, acc),
        "initial_state_share": _initial_state_share(df, acc),
    }

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
        "fit": fit,
        "policies": policies,
        "gates": {
            "G23_1_every_policy_has_rows": bool(all(policies[p]["n_rows"] == len(test) for p in POLICIES)),
            "G23_4_identity": bool(
                all(policies[p]["%s_identity_residual" % s] < 1e-9 for p in POLICIES for s in SCALES)
            ),
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
        "cell": "poisson@0.925" if "poisson_0.925" in os.path.basename(args.calib) else "unknown",
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
