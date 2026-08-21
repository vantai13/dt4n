#!/usr/bin/env python3
"""Phase 21R / Lesson 21R.2 -- build measured-ground-truth calibration sets.

One row is one routing-decision time.  One statistical unit is a physical
5-second block.  All physical calculations reuse Phase 20R helpers; this module
only assembles the conformal dataset and its locked diagnostics.
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
from measurements.decision_error import (
    DEFAULT_SYNC_PERIOD_S,
    sawtooth_age_steps,
)
from measurements.decision_error_v2 import (
    CALIBRATION,
    DT,
    N,
    TAU,
    TRUTH_TABLE,
    TruthTable,
    _cell_arrays,
    feasible_cells,
)
from twin import cost_v2 as C


BLOCK_S = 5.0
SIGMA = 0.0096
SEEDS = (101, 102, 103, 104, 105)
SEED_SPLIT = 7000
SEED_BOOT = 21200
ALPHA = 0.10
COMMON_K_20R = 800
N_BOOT = 2000

Z_EDGES_PRIMARY = (0.055, 0.10, 0.20, 0.30, 0.5501)
Z_EDGES_SECONDARY = (0.055, 0.155, 0.255, 0.355, 0.455, 0.5501)
Z_STEP_OFFSETS_PRIMARY = (0, 9, 29, 49)
Z_STEP_OFFSETS_SECONDARY = (0, 20, 40, 60, 80)

OUT_PARQUET = "results/phase-21R/calib_set.parquet"
OUT_REPORT = "results/phase-21R/calib_set_report.json"
CONST_SIGMA_PARQUET = "results/phase-20R/decision_error_constant_sigma.parquet"


def z_edges_for(
    d_sync_s: float,
    n: int,
    dt: float = DT,
    sync_period_s: float = DEFAULT_SYNC_PERIOD_S,
    offsets: Sequence[int] = Z_STEP_OFFSETS_PRIMARY,
) -> Tuple[float, ...]:
    """Derive age-bin edges while preserving their quantised step structure.

    With the inherited 51 ms delay this exactly reproduces the committed bin
    constants.  ``n`` is intentionally required because the realised maximum
    sawtooth step can depend on the build length.
    """
    steps = sawtooth_age_steps(
        int(n), float(dt), float(sync_period_s), float(d_sync_s)
    )
    k_min, k_max = int(steps.min()), int(steps.max())
    return tuple(
        [(k_min + int(offset)) * float(dt) for offset in offsets]
        + [k_max * float(dt) + 1e-4]
    )


def block_len(dt: float = DT, block_s: float = BLOCK_S) -> int:
    return int(round(float(block_s) / float(dt)))


def assign_bin(z_s: np.ndarray, edges: Sequence[float]) -> np.ndarray:
    """Assign preregistered age bins, raising if any value falls outside."""
    z_s = np.asarray(z_s, dtype=float)
    lo, hi = float(edges[0]), float(edges[-1])
    if (z_s < lo - 1e-12).any() or (z_s > hi + 1e-12).any():
        raise ValueError(
            "z ngoai mien bin da tien dang ky [%g, %g]: min=%g max=%g"
            % (lo, hi, float(z_s.min()), float(z_s.max()))
        )
    inner = np.asarray(edges[1:-1], dtype=float)
    return np.digitize(z_s, inner, right=False).astype(np.int8)


def build_one(
    cell: Mapping[str, Any],
    seed: int,
    tt: TruthTable,
    cv: C.CostV2,
    n: int = N,
    dt: float = DT,
    sigma: float = SIGMA,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Build one operating cell and one seed for sawtooth AoI."""
    arr = _cell_arrays(tt, cv, cell, seed=seed, n=n, dt=dt, sigma_override=sigma)

    age = sawtooth_age_steps(n, dt)
    rows = np.arange(int(n))
    valid = rows >= age
    cur = rows[valid]
    old = cur - age[valid]

    n_z0 = int((age[valid] == 0).sum())
    if n_z0:
        print("  [CANH BAO] %d hang co z=0 (twin = su that); loai khoi calib" % n_z0)
        keep = age[valid] != 0
        cur = cur[keep]
        old = old[keep]

    y_true = arr["c_true"][cur]
    y_hat = arr["c_fresh"][old]
    y_mid = arr["c_fresh"][cur]

    a1, a2, m_hat, m_true = MS.margins(y_true, y_hat)
    r = np.arange(len(cur))
    m_mid = y_mid[r, a2] - y_mid[r, a1]

    a_twin = arr["a_fresh"][old]
    a_star = arr["a_true"][cur]
    cost_true = arr["c_true"][cur]
    regret = cost_true[r, a_twin] - cost_true[r, a_star]
    y_sorted = np.sort(y_true, axis=1)
    gap_true = y_sorted[:, 1] - y_sorted[:, 0]
    viol = arr["viol"]
    z_s = (cur - old) * float(dt)
    lb = block_len(dt)

    df = pd.DataFrame(
        {
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
            "m_hat": m_hat.astype(np.float32),
            "m_true": m_true.astype(np.float32),
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
        }
    )

    meta = {
        "clip_fraction_max": float(max(arr["clip_fraction"].values())) if arr["clip_fraction"] else 0.0,
        "w_loss": float(arr["w_loss"]),
        "t_delay_ms": float(cell["t_delay_ms"]),
        "t_loss": float(cell["t_loss"]),
        "sigma_rho": float(arr["sigma_rho"]),
        "n_rows": int(len(df)),
        "n_z0_dropped": int(n_z0),
    }
    return df, meta


def split_by_block(df: pd.DataFrame, seed_split: int = SEED_SPLIT) -> pd.DataFrame:
    """Assign ``is_calib`` by whole block, never cutting through a block."""
    blocks = np.sort(df["block_id"].unique())
    rng = np.random.default_rng(int(seed_split))
    perm = rng.permutation(len(blocks))
    calib_blocks = set(blocks[perm[: len(blocks) // 2]].tolist())
    out = df.copy()
    out["is_calib"] = out["block_id"].isin(calib_blocks)
    return out


def split_by_sample_V3(df: pd.DataFrame, seed_split: int = SEED_SPLIT) -> pd.DataFrame:
    """Positive control V3: intentionally wrong sample-level split."""
    rng = np.random.default_rng(int(seed_split) + 1)
    out = df.copy()
    out["is_calib"] = rng.random(len(out)) < 0.5
    return out


def validate(df: pd.DataFrame, alpha: float = ALPHA) -> Dict[str, Any]:
    """Validate locked invariants and return reportable summary fields."""
    fail = []
    if not (df["m_hat"] >= 0).all():
        fail.append("m_hat am -> a1/a2 bi hoan doi")
    if not (df["s_margin"] <= df["s_vs_a1"] + 1e-5).all():
        fail.append("s_margin > s_vs_a1 -> vi pham bat dang thuc H6")
    if not (df["s_signed"] <= df["s_margin"] + 1e-5).all():
        fail.append("s_signed > s_margin -> sai dau")
    if not np.allclose(df["s_margin"], np.abs(df["s_signed"]), atol=1e-5):
        fail.append("s_margin != |s_signed|")

    lhs = (df["m_true"] - df["m_mid"]) + (df["m_mid"] - df["m_hat"])
    if not np.allclose(lhs, df["m_true"] - df["m_hat"], atol=1e-4):
        fail.append("dong nhat thuc phan ra bien khong khop")
    if (df["regret"] < -1e-4).any():
        fail.append("regret am -> a_star khong phai argmin")
    if not (df.loc[~df["wrong"], "regret"].abs() < 1e-4).all():
        fail.append("wrong=False nhung regret != 0")

    n_min = int(np.ceil(1.0 / float(alpha))) - 1
    cnt = df.groupby("z_bin")["block_id"].nunique()
    cnt2 = df.groupby("z_bin2")["block_id"].nunique()
    if (cnt < n_min).any():
        fail.append("bin CHINH co n_block < %d: %s" % (n_min, cnt.to_dict()))
    if (cnt2 < n_min).any():
        fail.append("bin PHU co n_block < %d: %s" % (n_min, cnt2.to_dict()))

    if fail:
        raise AssertionError("VALIDATE FAIL:\n  - " + "\n  - ".join(fail))

    return {
        "n_rows": int(len(df)),
        "n_blocks": int(df["block_id"].nunique()),
        "n_block_by_bin": {int(k): int(v) for k, v in cnt.items()},
        "n_block_by_bin2": {int(k): int(v) for k, v in cnt2.items()},
        "n_row_by_bin": {int(k): int(v) for k, v in df.groupby("z_bin").size().items()},
        "n_row_by_bin2": {int(k): int(v) for k, v in df.groupby("z_bin2").size().items()},
        "err_anchor": float(df["wrong"].mean()),
        "d_sla_anchor": float(df["viol_twin"].astype(float).mean() - df["viol_star"].astype(float).mean()),
        "pair_ok_rate": float(df["pair_ok"].mean()),
        "pair_ok_by_bin": {int(k): float(v) for k, v in df.groupby("z_bin")["pair_ok"].mean().items()},
    }


def block_bootstrap_anchor(df: pd.DataFrame, n_boot: int = N_BOOT, seed: int = SEED_BOOT) -> Dict[str, Any]:
    """Block bootstrap CI for the always-trust anchor metrics."""
    by_block = df.assign(
        wrong_f=df["wrong"].astype(float),
        d_sla=df["viol_twin"].astype(float) - df["viol_star"].astype(float),
    ).groupby("block_id")[["wrong_f", "d_sla"]].mean()
    values = by_block.to_numpy(dtype=float)
    rng = np.random.default_rng(int(seed))
    draws = np.empty((int(n_boot), 2), dtype=float)
    for i in range(int(n_boot)):
        pick = rng.integers(0, len(values), size=len(values))
        draws[i] = values[pick].mean(axis=0)
    return {
        "n_boot": int(n_boot),
        "seed": int(seed),
        "err_ci95": [float(x) for x in np.percentile(draws[:, 0], [2.5, 97.5])],
        "d_sla_ci95": [float(x) for x in np.percentile(draws[:, 1], [2.5, 97.5])],
    }


def reproduce_20R_fixed_z(
    cell: Mapping[str, Any],
    tt: TruthTable,
    cv: C.CostV2,
    z_list: Sequence[float] = (0.05, 0.10, 0.20, 0.30, 0.55),
    seeds: Sequence[int] = SEEDS,
    n: int = N,
    dt: float = DT,
    sigma: float = SIGMA,
) -> Dict[str, float]:
    """V5: reproduce Phase 20R fixed-z errors using its common window."""
    out = {}
    for z in z_list:
        k = int(round(float(z) / float(dt)))
        errs = []
        for seed in seeds:
            arr = _cell_arrays(tt, cv, cell, seed=seed, n=n, dt=dt, sigma_override=sigma)
            cur = np.arange(COMMON_K_20R, int(n))
            errs.append(float((arr["a_fresh"][cur - k] != arr["a_true"][cur]).mean()))
        out["z=%.2f" % float(z)] = float(np.mean(errs))
    return out


def compare_20R_constant_sigma(reproduced: Mapping[str, float], mode: str, rho_bar: float) -> Dict[str, Any]:
    table = pd.read_parquet(CONST_SIGMA_PARQUET)
    subset = table[(table["mode"] == str(mode)) & np.isclose(table["rho_bar"], float(rho_bar))]
    rows = {}
    max_abs = 0.0
    for key, value in reproduced.items():
        z = float(key.split("=")[1])
        hit = subset[np.isclose(subset["z_s"], z)]
        if len(hit) != len(SEEDS):
            raise ValueError("expected %d rows for %s rho=%.3f z=%.2f, got %d" % (len(SEEDS), mode, rho_bar, z, len(hit)))
        ref = float(hit["err_total"].mean())
        diff = abs(float(value) - ref)
        max_abs = max(max_abs, diff)
        rows[key] = {"reproduced": float(value), "phase20R": ref, "abs_diff": float(diff)}
    return {"max_abs_diff": float(max_abs), "by_z": rows}


def negative_control_z0(
    cell: Mapping[str, Any],
    tt: TruthTable,
    cv: C.CostV2,
    seed: int = 101,
) -> Dict[str, float]:
    """NC1: at z=0, the stale margin component must be exactly zero."""
    arr = _cell_arrays(tt, cv, cell, seed=seed, n=50_000, sigma_override=SIGMA)
    y_true, y_hat = arr["c_true"], arr["c_fresh"]
    a1, a2, m_hat, m_true = MS.margins(y_true, y_hat)
    rows = np.arange(len(y_true))
    m_mid = y_hat[rows, a2] - y_hat[rows, a1]
    return {
        "e_stale_margin_max_abs": float(np.abs(m_mid - m_hat).max()),
        "err_at_z0": float((arr["a_fresh"] != arr["a_true"]).mean()),
        "s_margin_mean": float(np.abs(m_true - m_hat).mean()),
    }


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True)
    parser.add_argument("--rho-bar", type=float, required=True)
    parser.add_argument("--out", default=OUT_PARQUET)
    parser.add_argument("--report", default=OUT_REPORT)
    parser.add_argument("--n", type=int, default=N)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    parser.add_argument("--v3", action="store_true", help="positive control: split by sample")
    args = parser.parse_args()

    tt = TruthTable(TRUTH_TABLE)
    cv = C.CostV2(strict_reliable=False)
    cell = _load_cell(args.mode, args.rho_bar)

    parts, metas = [], []
    for seed in args.seeds:
        print("  seed %d ..." % int(seed), flush=True)
        frame, meta = build_one(cell, int(seed), tt, cv, n=int(args.n))
        parts.append(frame)
        metas.append(meta)
    df = pd.concat(parts, ignore_index=True)
    df = (split_by_sample_V3 if args.v3 else split_by_block)(df)

    report = validate(df)
    reproduced = reproduce_20R_fixed_z(cell, tt, cv, seeds=args.seeds, n=int(args.n))
    report.update(
        {
            "cell": "%s@%.3f" % (str(args.mode), float(args.rho_bar)),
            "split": "sample_V3" if args.v3 else "block",
            "n_calib_blocks": int(df.loc[df.is_calib, "block_id"].nunique()),
            "n_test_blocks": int(df.loc[~df.is_calib, "block_id"].nunique()),
            "w_loss": float(metas[0]["w_loss"]),
            "t_delay_ms": float(metas[0]["t_delay_ms"]),
            "t_loss": float(metas[0]["t_loss"]),
            "eps_regret_ms": float(0.10 * metas[0]["t_delay_ms"]),
            "sigma_rho": float(metas[0]["sigma_rho"]),
            "clip_fraction_max": float(max(m["clip_fraction_max"] for m in metas)),
            "n_z0_dropped": int(sum(m["n_z0_dropped"] for m in metas)),
            "anchor_ci95": block_bootstrap_anchor(df),
            "V5_reproduce_20R": reproduced,
            "V5_compare_20R": compare_20R_constant_sigma(reproduced, str(args.mode), float(args.rho_bar)),
            "NC1_z0": negative_control_z0(cell, tt, cv),
            "gap_true_pct": {("p%d" % q): float(np.percentile(df["gap_true"], q)) for q in (5, 10, 25, 50, 75, 90)},
            "provenance": {
                "script": "cert/build_calib_set_v2.py",
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
                    )
                },
            },
        }
    )

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    df.to_parquet(args.out, index=False)
    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, sort_keys=True)
        f.write("\n")
    print(json.dumps({k: v for k, v in report.items() if k != "provenance"}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
