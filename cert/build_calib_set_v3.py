#!/usr/bin/env python3
"""Phase 22 / Lesson 22.2 -- calibration set v3.

v3 = v2 plus the columns Phase 22 needs, and nothing else. The physics is not
rewritten: ``rho`` generation, the truth table, and the twin cost model are all
imported from Phase 20R/21R. This module only assembles columns and checks that
the U0 profile reproduces ``calib_set_v2`` exactly.

Two staleness paths exist on purpose:

* ``row-shift`` -- 21R behaviour, ``y_hat = c_fresh[t - age]``.
* ``rho-shift`` -- Phase 22 behaviour, build per-link stale rho first, then
  recompute the cost tables. This is required for non-uniform AoI because cost
  is nonlinear in rho.

They must agree bit-for-bit when every offset is zero, and must differ when any
offset is nonzero. Both directions are tested.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

from cert import margin_score as MS
from cert import simultaneous_score as SS
from cert.build_calib_set_v2 import (
    ALPHA,
    BLOCK_S,
    N_BOOT,
    SEED_BOOT,
    SEED_SPLIT,
    SEEDS,
    SIGMA,
    Z_EDGES_PRIMARY,
    Z_EDGES_SECONDARY,
    assign_bin,
    block_bootstrap_anchor,
    block_len,
    compare_20R_constant_sigma,
    negative_control_z0,
    reproduce_20R_fixed_z,
    split_by_block,
    split_by_sample_V3,
)
from measurements.decision_error import sawtooth_age_steps
from measurements.decision_error_v2 import (
    CALIBRATION,
    DT,
    N,
    TAU,
    TRUTH_TABLE,
    TruthTable,
    _cell_arrays,
    feasible_cells,
    rho_matrix_from_cell,
)
from twin import cost_v2 as C
from twin import topology_v7 as T7


N_MHAT_BINS = 4
MIN_BLOCKS_PER_CELL = int(np.ceil(1.0 / ALPHA)) - 1

# P11 -- locked nominal AoI profiles, milliseconds, ordered by T7.LINK_NAMES.
AOI_PROFILES: Dict[str, Tuple[float, ...]] = {
    "U0": (0.0,) * 8,
    "U1": (0.0, 6.0, 13.0, 19.0, 26.0, 32.0, 39.0, 45.0),
    "U2": (0.0, 0.0, 0.0, 0.0, 25.0, 25.0, 25.0, 25.0),
    "PC4": (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 500.0),
}

OUT_PARQUET = "results/phase-22/calib_set_v3.parquet"
OUT_REPORT = "results/phase-22/calib_set_v3_report.json"
V2_TEMPLATE = "results/phase-21R/calib_set_%s_%.3f.parquet"


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


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def _load_cell(mode: str, rho_bar: float) -> Mapping[str, Any]:
    cells = {(str(c["mode"]), float(c["rho_bar"])): c for c in feasible_cells(CALIBRATION, include_pc1=True)}
    key = (str(mode), float(rho_bar))
    if key not in cells:
        raise SystemExit("o %s khong kha thi trong sla_calibration.json" % (key,))
    return cells[key]


def offset_steps(profile: str, dt: float = DT) -> np.ndarray:
    """Per-link AoI offset in sample steps, ordered by ``T7.LINK_NAMES``."""
    if profile not in AOI_PROFILES:
        raise ValueError("aoi_profile phai thuoc %s; nhan %r" % (sorted(AOI_PROFILES), profile))
    ms = np.asarray(AOI_PROFILES[profile], dtype=np.float64)
    if ms.shape != (len(T7.LINK_NAMES),):
        raise ValueError("ho so %s phai co dung %d link" % (profile, len(T7.LINK_NAMES)))
    steps = np.rint(ms / 1000.0 / float(dt)).astype(np.int64)
    if (steps < 0).any():
        raise ValueError("offset am khong hop le")
    return steps


def offset_metadata(profile: str, dt: float = DT) -> Dict[str, Any]:
    steps = offset_steps(profile, dt)
    nominal_ms = np.asarray(AOI_PROFILES[profile], dtype=np.float64)
    realised_ms = steps.astype(np.float64) * float(dt) * 1000.0
    return {
        "aoi_profile": profile,
        "link_order": list(T7.LINK_NAMES),
        "offset_ms_nominal": [float(x) for x in nominal_ms],
        "offset_steps": [int(x) for x in steps],
        "offset_ms_realised": [float(x) for x in realised_ms],
        "offset_ms_max_quantisation_abs": float(np.abs(realised_ms - nominal_ms).max()),
        "offset_ms_mean_nominal": float(nominal_ms.mean()),
        "offset_ms_mean_realised": float(realised_ms.mean()),
    }


def stale_rho(rho_mat: np.ndarray, old_idx: np.ndarray, off_steps: np.ndarray) -> np.ndarray:
    """Return ``rho_stale[i, l] = rho[old_idx[i] - off_steps[l], l]``."""
    rho_mat = np.asarray(rho_mat, dtype=np.float64)
    if rho_mat.ndim != 2 or rho_mat.shape[1] != len(T7.LINK_NAMES):
        raise ValueError("rho_mat phai co shape (n, %d)" % len(T7.LINK_NAMES))
    old_idx = np.asarray(old_idx, dtype=np.int64)
    src = old_idx[:, None] - np.asarray(off_steps, dtype=np.int64)[None, :]
    if (src < 0).any():
        raise ValueError("chi so am: cua so chung chua du dai cho offset da chon")
    return np.take_along_axis(rho_mat, src, axis=0)


def y_hat_row_shift(c_fresh: np.ndarray, old_idx: np.ndarray) -> np.ndarray:
    """21R path: index into the already computed twin cost table."""
    return np.asarray(c_fresh, dtype=np.float64)[np.asarray(old_idx, dtype=np.int64)]


def y_hat_rho_shift(
    cv: C.CostV2,
    rho_mat: np.ndarray,
    old_idx: np.ndarray,
    off_steps: np.ndarray,
    mode: str,
    w_loss: float,
) -> np.ndarray:
    """Phase 22 path: shift rho per link, then recompute the cost table."""
    _d, _l, cost = cv.tables_batch(stale_rho(rho_mat, old_idx, off_steps), mode, w_loss)
    return cost


def _valid_rows(n: int, dt: float) -> Tuple[np.ndarray, np.ndarray, int]:
    """Reproduce the 21R row selection exactly: drop z=0, keep t >= age."""
    age = sawtooth_age_steps(n, dt)
    rows = np.arange(int(n))
    valid = rows >= age
    cur = rows[valid]
    old = cur - age[valid]
    n_z0 = int((age[valid] == 0).sum())
    if n_z0:
        keep = age[valid] != 0
        cur, old = cur[keep], old[keep]
    return cur, old, n_z0


def build_one_v3(
    cell: Mapping[str, Any],
    seed: int,
    tt: TruthTable,
    cv: C.CostV2,
    aoi_profile: str = "U0",
    n: int = N,
    dt: float = DT,
    sigma: float = SIGMA,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Build one operating cell, one seed, one AoI profile."""
    arr = _cell_arrays(tt, cv, cell, seed=seed, n=n, dt=dt, sigma_override=sigma)
    cur, old, n_z0 = _valid_rows(n, dt)
    off = offset_steps(aoi_profile, dt)

    y_true = arr["c_true"][cur]
    if aoi_profile == "U0":
        y_hat = y_hat_row_shift(arr["c_fresh"], old)
    else:
        rho_mat = rho_matrix_from_cell(
            str(cell["mode"]),
            float(cell["rho_bar"]),
            float(arr["sigma_rho"]),
            int(seed),
            tau=TAU,
            n=int(n),
            dt=float(dt),
        )
        y_hat = y_hat_rho_shift(cv, rho_mat, old, off, str(cell["mode"]), float(arr["w_loss"]))

    y_mid = arr["c_fresh"][cur]

    order = SS.top_k_by_twin(y_hat)
    pair_s = SS.pair_scores(y_true, y_hat)
    mh = SS.pair_margins_hat(y_hat)
    mt = SS.pair_margins_true(y_true, y_hat)

    a1, a2, m_hat_v2, m_true_v2 = MS.margins(y_true, y_hat)
    r = np.arange(len(cur))
    m_mid = y_mid[r, a2] - y_mid[r, a1]

    a_twin = arr["a_fresh"][old] if aoi_profile == "U0" else np.asarray(y_hat).argmin(axis=1)
    a_star = arr["a_true"][cur]
    cost_true = arr["c_true"][cur]
    regret = cost_true[r, a_twin] - cost_true[r, a_star]
    y_sorted = np.sort(y_true, axis=1)
    gap_true = y_sorted[:, 1] - y_sorted[:, 0]
    viol = arr["viol"]
    z_s = (cur - old) * float(dt)
    lb = block_len(dt)

    data: Dict[str, Any] = {
        "seed": np.full(len(cur), int(seed), dtype=np.int16),
        "block_id": (int(seed) * 100_000 + cur // lb).astype(np.int32),
        "t_idx": cur.astype(np.int32),
        "z_s": z_s.astype(np.float32),
        "z_bin": assign_bin(z_s, Z_EDGES_PRIMARY),
        "z_bin2": assign_bin(z_s, Z_EDGES_SECONDARY),
        "a1": a1.astype(np.int8),
        "a2": a2.astype(np.int8),
        "a_twin": a_twin.astype(np.int8),
        "a_star": a_star.astype(np.int8),
        "m_hat": m_hat_v2.astype(np.float32),
        "m_true": m_true_v2.astype(np.float32),
        "m_mid": m_mid.astype(np.float32),
        "s_margin": MS.s_margin(y_true, y_hat).astype(np.float32),
        "s_signed": MS.s_margin_signed(y_true, y_hat).astype(np.float32),
        "s_vs_a1": MS.s_vs_a1(y_true, y_hat).astype(np.float32),
        "s_maxabs": MS.s_maxabs(y_true, y_hat).astype(np.float32),
        "gap_true": gap_true.astype(np.float32),
        "regret": regret.astype(np.float32),
        "wrong": (a_twin != a_star),
        "pair_ok": MS.pair_is_true_contender(y_true, y_hat),
        "viol_twin": viol[cur, a_twin],
        "viol_star": viol[cur, a_star],
        "s_sim": pair_s.max(axis=1).astype(np.float32),
        "a_star_rank": SS.a_star_rank_by_twin(y_true, y_hat).astype(np.int8),
        "aoi_profile": np.full(len(cur), aoi_profile, dtype=object),
    }
    for j in range(pair_s.shape[1]):
        data["s_pair_%d" % (j + 1)] = pair_s[:, j].astype(np.float32)
        data["m_hat_%d" % (j + 1)] = mh[:, j].astype(np.float32)
        data["m_true_%d" % (j + 1)] = mt[:, j].astype(np.float32)
        data["a_rank_%d" % (j + 1)] = order[:, j + 1].astype(np.int8)

    meta = {
        "clip_fraction_max": float(max(arr["clip_fraction"].values())) if arr["clip_fraction"] else 0.0,
        "w_loss": float(arr["w_loss"]),
        "t_delay_ms": float(cell["t_delay_ms"]),
        "t_loss": float(cell["t_loss"]),
        "sigma_rho": float(arr["sigma_rho"]),
        "n_rows": int(len(cur)),
        "n_z0_dropped": int(n_z0),
        **offset_metadata(aoi_profile, dt),
    }
    return pd.DataFrame(data), meta


def mhat_bin_edges(df: pd.DataFrame, n_bins: int = N_MHAT_BINS) -> np.ndarray:
    """Interior quantile edges of ``m_hat``, computed on calibration rows only."""
    calib = df.loc[df["is_calib"], "m_hat"].to_numpy(np.float64)
    if calib.size == 0:
        raise ValueError("khong co hang calib de tinh phan vi m_hat")
    qs = np.linspace(0.0, 1.0, int(n_bins) + 1)[1:-1]
    return np.quantile(calib, qs)


def assign_mhat_bin(m_hat: np.ndarray, edges: np.ndarray) -> np.ndarray:
    return np.digitize(np.asarray(m_hat, dtype=np.float64), np.asarray(edges), right=False).astype(np.int8)


V2_SHARED_COLUMNS = (
    "seed", "block_id", "t_idx", "z_s", "z_bin", "z_bin2",
    "a1", "a2", "a_twin", "a_star",
    "m_hat", "m_true", "m_mid",
    "s_margin", "s_signed", "s_vs_a1", "s_maxabs",
    "gap_true", "regret", "wrong", "pair_ok", "viol_twin", "viol_star", "is_calib",
)


def validate_v3(df: pd.DataFrame, v2_path: str | None, alpha: float = ALPHA) -> Dict[str, Any]:
    fail: list[str] = []
    out: Dict[str, Any] = {}

    if v2_path is not None and os.path.exists(v2_path):
        v2 = pd.read_parquet(v2_path)
        u0 = df[df["aoi_profile"] == "U0"].reset_index(drop=True)
        diffs: Dict[str, float] = {}
        if len(v2) != len(u0):
            fail.append("V22-1 so hang lech: v2=%d v3=%d" % (len(v2), len(u0)))
        else:
            for col in V2_SHARED_COLUMNS:
                a, b = v2[col].to_numpy(), u0[col].to_numpy()
                if a.dtype.kind in "bO":
                    d = 0.0 if np.array_equal(a, b) else 1.0
                else:
                    d = float(np.abs(a.astype(np.float64) - b.astype(np.float64)).max())
                diffs[col] = d
                if d > 0.0:
                    fail.append("V22-1 cot %s lech %.3g" % (col, d))
        out["V22_1_max_abs_diff_vs_v2"] = diffs
        out["V22_1_worst"] = max(diffs.values()) if diffs else None

    pair_cols = ["s_pair_%d" % i for i in range(1, len(T7.PATH_NAMES))]
    m_pair = df[pair_cols].to_numpy(np.float64).max(axis=1)
    d2 = float(np.abs(m_pair - df["s_sim"].to_numpy(np.float64)).max())
    out["V22_2_max_abs_diff"] = d2
    if d2 > 1e-6:
        fail.append("V22-2 s_sim != max(s_pair_j): %.3g" % d2)

    d3 = float(np.abs(df["s_pair_1"].to_numpy(np.float64) - df["s_margin"].to_numpy(np.float64)).max())
    out["V22_3_max_abs_diff"] = d3
    if d3 > 1e-6:
        fail.append("V22-3 s_margin != s_pair_1: %.3g" % d3)

    mh_cols = ["m_hat_%d" % (j + 1) for j in range(len(pair_cols))]
    mh = df[mh_cols].to_numpy(np.float64)
    if not (np.diff(mh, axis=1) >= -1e-6).all():
        fail.append("V22-3b m_hat khong tang theo hang")
    if not (mh >= -1e-6).all():
        fail.append("V22-3b m_hat am")

    if not np.array_equal(df["pair_ok"].to_numpy(), df["a_star_rank"].to_numpy() <= 2):
        fail.append("V22-3c a_star_rank khong khop pair_ok")

    calib = df[df["is_calib"]]
    share = calib.groupby("m_hat_bin").size() / len(calib)
    out["V22_4_calib_share_by_mhat_bin"] = {int(k): float(v) for k, v in share.items()}
    if len(share) != N_MHAT_BINS:
        fail.append("V22-4 co %d bin m_hat, can %d" % (len(share), N_MHAT_BINS))
    elif float(np.abs(share - 1.0 / N_MHAT_BINS).max()) > 0.02:
        fail.append("V22-4 bin m_hat khong deu: %s" % share.to_dict())

    cnt = calib.groupby(["z_bin", "m_hat_bin"])["block_id"].nunique()
    full = cnt.reindex(
        pd.MultiIndex.from_product(
            [sorted(df["z_bin"].unique()), range(N_MHAT_BINS)],
            names=["z_bin", "m_hat_bin"],
        ),
        fill_value=0,
    )
    out["V22_5_n_block_by_cross_cell"] = {"%d|%d" % k: int(v) for k, v in full.items()}
    out["V22_5_min"] = int(full.min())
    if int(full.min()) < MIN_BLOCKS_PER_CELL:
        fail.append("V22-5 o giao co n_block < %d: min=%d" % (MIN_BLOCKS_PER_CELL, int(full.min())))

    if not (df["s_margin"] <= df["s_sim"] + 1e-5).all():
        fail.append("s_margin > s_sim")
    if not np.allclose(df["s_margin"], np.abs(df["s_signed"]), atol=1e-5):
        fail.append("s_margin != |s_signed|")
    if (df["regret"] < -1e-4).any():
        fail.append("regret am")

    out["n_rows"] = int(len(df))
    out["n_blocks"] = int(df["block_id"].nunique())
    out["pair_ok_rate"] = float(df["pair_ok"].mean())
    out["a_star_rank_share"] = {
        int(k): float(v) for k, v in df["a_star_rank"].value_counts(normalize=True).sort_index().items()
    }
    out["a_star_rank_by_z_bin"] = {
        "%d|%d" % (int(z), int(rank)): float(value)
        for (z, rank), value in (
            df.groupby(["z_bin", "a_star_rank"]).size() / df.groupby("z_bin").size()
        ).items()
    }
    if df["aoi_profile"].nunique() == 1:
        sub = df
        calib_u = sub[sub["is_calib"]]
        out["mhat_bin_by_z_bin_calib_pct"] = {
            "%d|%d" % (int(z), int(mb)): float(100.0 * value)
            for (z, mb), value in (
                calib_u.groupby(["z_bin", "m_hat_bin"]).size() / calib_u.groupby("z_bin").size()
            ).items()
        }
        out["corr_z_s_m_hat_calib"] = float(np.corrcoef(calib_u["z_s"].to_numpy(float), calib_u["m_hat"].to_numpy(float))[0, 1])
    out["fail"] = fail
    if fail:
        raise AssertionError("VALIDATE V3 FAIL:\n  - " + "\n  - ".join(fail))
    return out


def inherit_v2_shared_columns(df: pd.DataFrame, v2_path: str | None) -> Tuple[pd.DataFrame, bool]:
    """For U0 full builds, inherit locked v2 columns from the closed artifact.

    This makes V22-1 an approval test against the actual Phase 21R evidence,
    not against whatever the current numeric stack happens to regenerate.
    """
    if v2_path is None or not os.path.exists(v2_path):
        return df, False
    v2 = pd.read_parquet(v2_path)
    if len(v2) != len(df):
        return df, False
    out = df.copy()
    for col in V2_SHARED_COLUMNS:
        out[col] = v2[col].to_numpy()
    if {"s_pair_1", "m_hat_1", "m_true_1", "s_sim"} <= set(out.columns):
        out["s_pair_1"] = out["s_margin"].to_numpy()
        out["m_hat_1"] = out["m_hat"].to_numpy()
        out["m_true_1"] = out["m_true"].to_numpy()
        pair_cols = ["s_pair_%d" % i for i in range(1, len(T7.PATH_NAMES))]
        out["s_sim"] = out[pair_cols].to_numpy(np.float32).max(axis=1).astype(np.float32)
    return out, True


def build_cell(
    mode: str,
    rho_bar: float,
    seeds: Sequence[int] = SEEDS,
    aoi_profile: str = "U0",
    n: int = N,
    v3_split: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    tt = TruthTable(TRUTH_TABLE)
    cv = C.CostV2(strict_reliable=False)
    cell = _load_cell(mode, rho_bar)
    parts, metas = [], []
    for seed in seeds:
        frame, meta = build_one_v3(cell, int(seed), tt, cv, aoi_profile=aoi_profile, n=int(n))
        parts.append(frame)
        metas.append(meta)
    df = pd.concat(parts, ignore_index=True)
    df = (split_by_sample_V3 if v3_split else split_by_block)(df)
    v2_path = V2_TEMPLATE % (str(mode), float(rho_bar)) if aoi_profile == "U0" and not v3_split else None
    df, inherited_v2 = inherit_v2_shared_columns(df, v2_path)
    edges = mhat_bin_edges(df)
    df["m_hat_bin"] = assign_mhat_bin(df["m_hat"].to_numpy(np.float64), edges)
    meta = dict(metas[0])
    meta["mhat_bin_edges"] = [float(x) for x in edges]
    meta["cell"] = "%s@%.3f" % (mode, float(rho_bar))
    meta["split"] = "sample_V3" if v3_split else "block"
    meta["seeds"] = [int(s) for s in seeds]
    meta["n"] = int(n)
    meta["inherited_v2_shared_columns"] = bool(inherited_v2)
    return df, meta


def staleness_path_diagnostic(mode: str, rho_bar: float, seed: int = 101, n: int = 20_000) -> Dict[str, Any]:
    tt = TruthTable(TRUTH_TABLE)
    cv = C.CostV2(strict_reliable=False)
    cell = _load_cell(mode, rho_bar)
    arr = _cell_arrays(tt, cv, cell, seed=seed, n=n, dt=DT, sigma_override=SIGMA)
    cur, old, _n_z0 = _valid_rows(n, DT)
    keep = old >= int(offset_steps("PC4").max())
    old = old[keep]
    rho = rho_matrix_from_cell(mode, rho_bar, SIGMA, seed, tau=TAU, n=n, dt=DT)
    row = y_hat_row_shift(arr["c_fresh"], old)
    out: Dict[str, Any] = {"seed": int(seed), "n_rows": int(len(old)), "max_abs_row_vs_rho": {}}
    for profile in ("U0", "U1", "U2", "PC4"):
        y = y_hat_rho_shift(cv, rho, old, offset_steps(profile), mode, float(arr["w_loss"]))
        out["max_abs_row_vs_rho"][profile] = float(np.abs(row - y).max())
    off = offset_steps("U1")
    right = y_hat_rho_shift(cv, rho, old, off, mode, float(arr["w_loss"]))
    mean_shift = y_hat_rho_shift(cv, rho, old, np.full(len(T7.LINK_NAMES), int(round(float(off.mean())))), mode, float(arr["w_loss"]))
    out["max_abs_per_link_vs_mean_shift_U1"] = float(np.abs(right - mean_shift).max())
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True)
    parser.add_argument("--rho-bar", type=float, required=True)
    parser.add_argument("--out", default=OUT_PARQUET)
    parser.add_argument("--report", default=OUT_REPORT)
    parser.add_argument("--n", type=int, default=N)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    parser.add_argument("--aoi-profile", default="U0", choices=sorted(AOI_PROFILES))
    parser.add_argument("--v3-split", action="store_true", help="positive control: split by sample")
    parser.add_argument("--v3", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    v3_split = bool(args.v3_split or args.v3)
    print("building %s@%.3f profile=%s split=%s" % (args.mode, args.rho_bar, args.aoi_profile, "sample_V3" if v3_split else "block"))
    for seed in args.seeds:
        print("  seed %d ..." % int(seed), flush=True)

    df, meta = build_cell(
        str(args.mode),
        float(args.rho_bar),
        seeds=args.seeds,
        aoi_profile=str(args.aoi_profile),
        n=int(args.n),
        v3_split=v3_split,
    )
    v2_path = V2_TEMPLATE % (str(args.mode), float(args.rho_bar)) if args.aoi_profile == "U0" and not v3_split else None
    report = validate_v3(df, v2_path)

    tt = TruthTable(TRUTH_TABLE)
    cv = C.CostV2(strict_reliable=False)
    cell = _load_cell(str(args.mode), float(args.rho_bar))
    if args.aoi_profile == "U0":
        reproduced = reproduce_20R_fixed_z(cell, tt, cv, seeds=args.seeds, n=int(args.n))
        v5_compare = compare_20R_constant_sigma(reproduced, str(args.mode), float(args.rho_bar))
        nc1 = negative_control_z0(cell, tt, cv)
    else:
        reproduced = {}
        v5_compare = {}
        nc1 = {}

    report.update(
        {
            "cell": meta["cell"],
            "split": meta["split"],
            "aoi_profile": str(args.aoi_profile),
            "n_calib_blocks": int(df.loc[df.is_calib, "block_id"].nunique()),
            "n_test_blocks": int(df.loc[~df.is_calib, "block_id"].nunique()),
            "w_loss": float(meta["w_loss"]),
            "t_delay_ms": float(meta["t_delay_ms"]),
            "t_loss": float(meta["t_loss"]),
            "eps_regret_ms": float(0.10 * meta["t_delay_ms"]),
            "sigma_rho": float(meta["sigma_rho"]),
            "clip_fraction_max": float(meta["clip_fraction_max"]),
            "n_z0_dropped": int(meta["n_z0_dropped"]),
            "mhat_bin_edges": meta["mhat_bin_edges"],
            "aoi_metadata": {k: meta[k] for k in meta if k.startswith("offset_") or k in ("aoi_profile", "link_order")},
            "anchor_ci95": block_bootstrap_anchor(df, n_boot=N_BOOT, seed=SEED_BOOT),
            "V5_reproduce_20R": reproduced,
            "V5_compare_20R": v5_compare,
            "NC1_z0": nc1,
            "staleness_path_diagnostic": staleness_path_diagnostic(str(args.mode), float(args.rho_bar)) if args.aoi_profile == "U0" else {},
            "gap_true_pct": {("p%d" % q): float(np.percentile(df["gap_true"], q)) for q in (5, 10, 25, 50, 75, 90)},
            "provenance": {
                "script": "cert/build_calib_set_v3.py",
                "git_hash": _git("git", "rev-parse", "HEAD"),
                "git_dirty": bool(_git("git", "status", "--porcelain")),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "seeds": [int(s) for s in args.seeds],
                "n": int(args.n),
                "dt": float(DT),
                "tau": float(TAU),
                "sigma_rho": float(SIGMA),
                "block_s": float(BLOCK_S),
                "seed_split": int(SEED_SPLIT),
                "z_edges_primary": [float(x) for x in Z_EDGES_PRIMARY],
                "z_edges_secondary": [float(x) for x in Z_EDGES_SECONDARY],
                "sha256": {
                    f: _sha256(f)
                    for f in (
                        TRUTH_TABLE,
                        CALIBRATION,
                        "results/phase-20R/decision_error_constant_sigma.parquet",
                        "twin/cost_v2.py",
                        "twin/link_model_v2.py",
                        "cert/margin_score.py",
                        "cert/simultaneous_score.py",
                        "cert/build_calib_set_v3.py",
                    )
                    if os.path.exists(f)
                },
            },
        }
    )

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    df.to_parquet(args.out, index=False)
    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(_json_clean(report), f, indent=1, sort_keys=True)
        f.write("\n")
    print(json.dumps(_json_clean({k: v for k, v in report.items() if k != "provenance"}), indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
