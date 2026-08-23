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
import re
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
    Z_STEP_OFFSETS_PRIMARY,
    Z_STEP_OFFSETS_SECONDARY,
    assign_bin,
    block_bootstrap_anchor,
    block_len,
    compare_20R_constant_sigma,
    negative_control_z0,
    reproduce_20R_fixed_z,
    split_by_block,
    split_by_sample_V3,
    z_edges_for,
)
from measurements.aoi_model_v7 import (
    AoIModelV7, InstrumentSamples, Z_EDGES_V7, Z_EDGES_V7_SECONDARY,
    d_base_s, u3_profile_ms, u_centred_profile_ms,
)
from measurements.validity import validity_block
from measurements.decision_error import (
    DEFAULT_D_SYNC_S,
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
    rho_matrix_from_cell,
)
from twin import cost_v2 as C
from twin import topology_v7 as T7


N_MHAT_BINS = 4
MIN_BLOCKS_PER_CELL = int(np.ceil(1.0 / ALPHA)) - 1
D_SYNC = DEFAULT_D_SYNC_S
SYNC_PERIOD = DEFAULT_SYNC_PERIOD_S

# P11 -- locked nominal AoI profiles, milliseconds, ordered by T7.LINK_NAMES.
AOI_PROFILES: Dict[str, Tuple[float, ...]] = {
    "U0": (0.0,) * 8,
    "U1": (0.0, 6.0, 13.0, 19.0, 26.0, 32.0, 39.0, 45.0),
    "U2": (0.0, 0.0, 0.0, 0.0, 25.0, 25.0, 25.0, 25.0),
    "PC4": (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 500.0),
}

# Ho so DAN XUAT tu alpha do duoc (amendment 23-49 muc 2-3).
# U3  = alpha - min(alpha), luong tu hoa; phan dich bu tru o d_base_s().
# U1c/U2c = ban TRUNG TAM HOA cua U1/U2, vi hai ho so goc KHONG bao toan
#           trung binh (+22.5 va +12.5 ms) nen so chung voi U0 la so DONG
#           THOI hinh dang va muc tuoi.
AOI_PROFILES["U3"] = u3_profile_ms(DT)
AOI_PROFILES["U1c"] = u_centred_profile_ms(AOI_PROFILES["U1"], DT)
AOI_PROFILES["U2c"] = u_centred_profile_ms(AOI_PROFILES["U2"], DT)

# Truc tuoi DO DUOC (Lessons 23.8 / 23.18 / 23.19).
# profile="U0" o day vi alpha di duong off_steps, khong di trong mo hinh.
AOI_V7 = AoIModelV7(d_s=d_base_s(dt=DT), profile="U0")
AXIS_MEASURED = "measured_v7"
AXIS_LEGACY = "legacy_sawtooth_51ms"

OUT_PARQUET = "results/SUPERSEDED/phase-22/calib_set_v3.parquet"
OUT_REPORT = "results/SUPERSEDED/phase-22/calib_set_v3_report.json"
V2_TEMPLATE = "results/SUPERSEDED/phase-21R/calib_set_%s_%.3f.parquet"


def out_stem(axis: str, mode: str, rho_bar: float, profile: str) -> str:
    """Tien to duong dan dau ra -- theo TANG va mang DU DINH DANH.

    (a) TANG: artifact truc DO DUOC vao `LIVE/`; doi chung am (truc ke thua)
        vao `SUPERSEDED/`. `test_no_stale_axes.py` CHI quet `LIVE/`, nen neu
        artifact truc moi nam o SUPERSEDED thi cai chan cua Lesson 23.17 vo
        hieu MOT CACH AM THAM.
    (b) TEN mang ca HO SO va TRUC: chay U0 roi chay U3 se KHONG ghi de nhau,
        neu khong Dot 1 (cau hoi "sua truc da lam gi") bi mat.
    Xem amendment 23-49b muc 3.
    """
    # amendment 23-49c muc 3: LIVE chi khi MOI truc DA DUOC DUYET, khong
    # phai khi MOT truc da duoc sua. `calib_set` van dung nguong SLA mang
    # nhan `self_calibrated` (DEPRECATED, loi cau truc S14, sua o Lesson
    # 23.21), nen ke ca truc AoI da do duoc thi artifact VAN chua "sach".
    # PENDING = hien hanh nhung CHO mot truc duoc duyet (amendment 23-49d
    # muc 4). KHAC SUPERSEDED, von co nghia "da bi thay the".
    if axis != AXIS_MEASURED:
        tier = "SUPERSEDED"          # truc ke thua: da BI THAY THE that su
    else:
        # PENDING = hien hanh nhung CHO mot truc duoc duyet (23-49d muc 4).
        tier = "LIVE" if _all_axes_approved() else "PENDING"
    return "results/%s/phase-21R/calib_set_%s_%.3f_%s_%s" % (
        tier, mode, float(rho_bar), profile, axis)


def _pending_axes() -> list:
    """Truc nao CHUA duoc duyet -- de artifact o PENDING/ khai bao chinh xac."""
    import json as _json
    with open("docs/phase-23/axis_registry.json", encoding="utf-8") as fh:
        ap = _json.load(fh)["approved_for_live"]
    return [k for k in ("aoi_axis", "sla_axis") if not ap.get(k)]


def _all_axes_approved() -> bool:
    """Ca truc AoI lan truc SLA deu nam trong `approved_for_live`?"""
    import json as _json
    with open("docs/phase-23/axis_registry.json", encoding="utf-8") as fh:
        ap = _json.load(fh)["approved_for_live"]
    return bool(ap.get("aoi_axis")) and bool(ap.get("sla_axis"))


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


def _load_cell(
    mode: str,
    rho_bar: float,
    calibration_path: str = CALIBRATION,
) -> Mapping[str, Any]:
    cells = {
        (str(c["mode"]), float(c["rho_bar"])): c
        for c in feasible_cells(calibration_path, include_pc1=True)
    }
    key = (str(mode), float(rho_bar))
    if key not in cells:
        raise SystemExit("o %s khong kha thi trong sla_calibration.json" % (key,))
    return cells[key]


def parse_cell_arg(cell: str) -> Tuple[str, float]:
    """Parse CLI cell names such as ``poisson_0.925``."""
    match = re.match(r"^(.+)_([0-9]+(?:\.[0-9]+)?)$", str(cell))
    if not match:
        raise ValueError("cell phai co dang <mode>_<rho>, vi du poisson_0.925")
    return str(match.group(1)), float(match.group(2))


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


def _valid_rows(
    n: int, dt: float, d_sync: float = D_SYNC, axis: str = AXIS_LEGACY,
    aoi: "AoIModelV7 | None" = None,
) -> Tuple[np.ndarray, np.ndarray, int]:
    """Chon hang: bo z=0, giu t >= age.

    axis = AXIS_LEGACY   rang cua ke thua d = 51 ms  -> NEGATIVE CONTROL
    axis = AXIS_MEASURED truc do duoc, d_base + Uniform[0, T]
    """
    if axis == AXIS_MEASURED:
        # `aoi` mang d_base DA BU TRU theo ho so dang dung (amendment 23-49a
        # muc 2). Mac dinh AOI_V7 (bu tru cho U3) chi de tuong thich nguoc.
        age = (aoi or AOI_V7).base_age_steps(n, dt)
    elif axis == AXIS_LEGACY:
        age = sawtooth_age_steps(n, dt, SYNC_PERIOD, d_sync)
    else:
        raise ValueError("axis phai la %r hoac %r" % (AXIS_MEASURED, AXIS_LEGACY))
    # L36: cai luoc khong phat hien duoc bang thong ke ha nguon -> chan o KIEU
    if isinstance(age, InstrumentSamples):
        raise TypeError(
            "instrument_mode khong duoc dung trong pipeline (L36). "
            "Pipeline phai dung process_mode/base_age_steps.")
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
    d_sync: float = D_SYNC,
    axis: str = AXIS_LEGACY,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Build one operating cell, one seed, one AoI profile."""
    arr = _cell_arrays(tt, cv, cell, seed=seed, n=n, dt=dt, sigma_override=sigma)
    off = offset_steps(aoi_profile, dt)
    if axis == AXIS_MEASURED:
        # d_base phu thuoc HO SO: moi ho so cho cung mot muc tuoi trung binh,
        # nen so hai ho so la so RIENG HINH DANG (amendment 23-49a muc 2).
        aoi_model = AoIModelV7(
            d_s=d_base_s(tuple(off * float(dt) * 1000.0), dt), profile="U0")
    else:
        aoi_model = None
    cur, old, n_z0 = _valid_rows(n, dt, d_sync, axis=axis, aoi=aoi_model)
    if axis == AXIS_MEASURED:
        # canh KHOA o amendment 23-48 muc 4 -- KHONG duoc dan xuat lai
        z_edges_p = Z_EDGES_V7
        z_edges_s = Z_EDGES_V7_SECONDARY
        # z_s ghi ra la TUOI TRUNG BINH giua 8 link, khong phai tuoi co so.
        # O U0 thi mean(off) = 0 nen z_s KHONG doi -> giu bit-exact NC-E1.
        z_shift_s = float(np.mean(off)) * float(dt)
    else:
        z_edges_p = z_edges_for(
            d_sync, n, dt, SYNC_PERIOD, offsets=Z_STEP_OFFSETS_PRIMARY
        )
        z_edges_s = z_edges_for(
            d_sync, n, dt, SYNC_PERIOD, offsets=Z_STEP_OFFSETS_SECONDARY
        )
        z_shift_s = 0.0

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
    y_hat_a1 = y_hat[r, a1]
    m_mid = y_mid[r, a2] - y_mid[r, a1]

    a_twin = arr["a_fresh"][old] if aoi_profile == "U0" else np.asarray(y_hat).argmin(axis=1)
    a_star = arr["a_true"][cur]
    cost_true = arr["c_true"][cur]
    regret = cost_true[r, a_twin] - cost_true[r, a_star]
    y_sorted = np.sort(y_true, axis=1)
    gap_true = y_sorted[:, 1] - y_sorted[:, 0]
    viol = arr["viol"]
    z_s = (cur - old) * float(dt) + z_shift_s
    lb = block_len(dt)

    data: Dict[str, Any] = {
        "seed": np.full(len(cur), int(seed), dtype=np.int16),
        "block_id": (int(seed) * 100_000 + cur // lb).astype(np.int32),
        "t_idx": cur.astype(np.int32),
        "z_s": z_s.astype(np.float32),
        "z_bin": assign_bin(z_s, z_edges_p),
        "z_bin2": assign_bin(z_s, z_edges_s),
        "a1": a1.astype(np.int8),
        "a2": a2.astype(np.int8),
        "a_twin": a_twin.astype(np.int8),
        "a_star": a_star.astype(np.int8),
        "y_hat_a1": y_hat_a1.astype(np.float32),
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
        **{
            "sla_viol_p%d" % j: viol[cur, j]
            for j in range(len(T7.PATH_NAMES))
        },
        "s_sim": pair_s.max(axis=1).astype(np.float32),
        "a_star_rank": SS.a_star_rank_by_twin(y_true, y_hat).astype(np.int8),
        "aoi_profile": np.full(len(cur), aoi_profile, dtype=object),
    }
    for j in range(pair_s.shape[1]):
        data["s_pair_%d" % (j + 1)] = pair_s[:, j].astype(np.float32)
        data["m_hat_%d" % (j + 1)] = mh[:, j].astype(np.float32)
        data["m_true_%d" % (j + 1)] = mt[:, j].astype(np.float32)
        data["a_rank_%d" % (j + 1)] = order[:, j + 1].astype(np.int8)

    z_bin = np.asarray(data["z_bin"], dtype=np.int8)
    age_steps = sawtooth_age_steps(n, dt, SYNC_PERIOD, d_sync)
    meta = {
        # amendment 23-49: truc phai HIEN trong metadata, khong duoc de an
        "axis": axis,
        "z_shift_ms": z_shift_s * 1000.0,
        "d_base_ms": (aoi_model.d * 1000.0 if axis == AXIS_MEASURED else None),
        "T_ms": (AOI_V7.T * 1000.0 if axis == AXIS_MEASURED
                 else SYNC_PERIOD * 1000.0),
        "offset_ms_realised": [float(x) for x in off * float(dt) * 1000.0],
        "offset_mean_ms": float(np.mean(off)) * float(dt) * 1000.0,
        "clip_fraction_max": float(max(arr["clip_fraction"].values())) if arr["clip_fraction"] else 0.0,
        "w_loss": float(arr["w_loss"]),
        "t_delay_ms": float(cell["t_delay_ms"]),
        "t_loss": float(cell["t_loss"]),
        "sigma_rho": float(arr["sigma_rho"]),
        "n_rows": int(len(cur)),
        "n_valid_rows": int(len(cur)),
        "n_z0_dropped": int(n_z0),
        "d_sync_s": float(d_sync),
        "d_sync_source": (
            "inherited_negative_control"
            if float(d_sync) == float(D_SYNC)
            else "sensitivity_sweep"
        ),
        "sync_period_s": float(SYNC_PERIOD),
        "z_edges_primary": [float(x) for x in z_edges_p],
        "z_edges_secondary": [float(x) for x in z_edges_s],
        "z_step_k_min": int(age_steps.min()),
        "z_step_k_max": int(age_steps.max()),
        "z_min_realised_s": float(z_s.min()),
        "z_max_realised_s": float(z_s.max()),
        "bin_shares": [float((z_bin == i).mean()) for i in range(4)],
        "status": (
            "PRIMARY" if float(d_sync) == float(D_SYNC) else "SENSITIVITY_ONLY"
        ),
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

    sla_cols = ["sla_viol_p%d" % j for j in range(len(T7.PATH_NAMES))]
    missing_sla = [c for c in sla_cols if c not in df.columns]
    if missing_sla:
        fail.append("thieu cot SLA theo duong: %s" % missing_sla)
    else:
        mat = np.column_stack([df[c].to_numpy(bool) for c in sla_cols])
        rows = np.arange(len(df))
        twin = mat[rows, df["a_twin"].to_numpy(np.int64)]
        star = mat[rows, df["a_star"].to_numpy(np.int64)]
        out["V23_sla_twin_match"] = bool(np.array_equal(twin, df["viol_twin"].to_numpy(bool)))
        out["V23_sla_star_match"] = bool(np.array_equal(star, df["viol_star"].to_numpy(bool)))
        if not out["V23_sla_twin_match"]:
            fail.append("sla_viol_p* khong tai tao viol_twin")
        if not out["V23_sla_star_match"]:
            fail.append("sla_viol_p* khong tai tao viol_star")

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
    calibration_path: str = CALIBRATION,
    d_sync: float = D_SYNC,
    axis: str = AXIS_LEGACY,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    tt = TruthTable(TRUTH_TABLE)
    cv = C.CostV2(strict_reliable=False)
    cell = _load_cell(mode, rho_bar, calibration_path=calibration_path)
    parts, metas = [], []
    for seed in seeds:
        frame, meta = build_one_v3(
            cell,
            int(seed),
            tt,
            cv,
            aoi_profile=aoi_profile,
            n=int(n),
            d_sync=float(d_sync),
            axis=str(axis),
        )
        parts.append(frame)
        metas.append(meta)
    df = pd.concat(parts, ignore_index=True)
    df = (split_by_sample_V3 if v3_split else split_by_block)(df)
    v2_path = (
        V2_TEMPLATE % (str(mode), float(rho_bar))
        if aoi_profile == "U0"
        and not v3_split
        and float(d_sync) == float(D_SYNC)
        else None
    )
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
    meta["calibration_path"] = str(calibration_path)
    meta["d_sync_s"] = float(d_sync)
    return df, meta


def staleness_path_diagnostic(
    mode: str,
    rho_bar: float,
    seed: int = 101,
    n: int = 20_000,
    calibration_path: str = CALIBRATION,
) -> Dict[str, Any]:
    tt = TruthTable(TRUTH_TABLE)
    cv = C.CostV2(strict_reliable=False)
    cell = _load_cell(mode, rho_bar, calibration_path=calibration_path)
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
    parser.add_argument("--cell", help="shortcut for --mode/--rho-bar, e.g. poisson_0.925")
    parser.add_argument("--mode")
    parser.add_argument("--rho-bar", type=float)
    parser.add_argument("--out", default=None)
    parser.add_argument("--report", default=None)
    parser.add_argument("--out-stem", default=None,
                        help="tien to duong dan dau ra; mang ca ho so va truc "
                             "de khong ghi de nhau giua cac dot")
    parser.add_argument("--n", type=int, default=N)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    parser.add_argument("--aoi-profile", default="U0", choices=sorted(AOI_PROFILES))
    parser.add_argument("--calibration", default=CALIBRATION)
    parser.add_argument("--axis", default=AXIS_LEGACY,
                        choices=[AXIS_LEGACY, AXIS_MEASURED],
                        help="truc tuoi: legacy (doi chung am) | measured (23.20)")
    parser.add_argument("--d-sync", type=float, default=D_SYNC)
    parser.add_argument("--v3-split", action="store_true", help="positive control: split by sample")
    parser.add_argument("--v3", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.cell:
        mode, rho_bar = parse_cell_arg(args.cell)
        if args.mode is not None and args.mode != mode:
            parser.error("--cell mau thuan voi --mode")
        if args.rho_bar is not None and abs(float(args.rho_bar) - rho_bar) > 1e-12:
            parser.error("--cell mau thuan voi --rho-bar")
        args.mode = mode
        args.rho_bar = rho_bar
    if args.mode is None or args.rho_bar is None:
        parser.error("can --cell hoac ca --mode va --rho-bar")

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
        calibration_path=str(args.calibration),
        d_sync=float(args.d_sync),
        axis=str(args.axis),
    )
    v2_path = (
        V2_TEMPLATE % (str(args.mode), float(args.rho_bar))
        if args.aoi_profile == "U0"
        and not v3_split
        and float(args.d_sync) == float(D_SYNC)
        and str(args.axis) == AXIS_LEGACY
        else None
    )
    report = validate_v3(df, v2_path)

    tt = TruthTable(TRUTH_TABLE)
    cv = C.CostV2(strict_reliable=False)
    cell = _load_cell(
        str(args.mode), float(args.rho_bar), calibration_path=str(args.calibration)
    )
    if args.aoi_profile == "U0":
        reproduced = reproduce_20R_fixed_z(cell, tt, cv, seeds=args.seeds, n=int(args.n))
        try:
            v5_compare = compare_20R_constant_sigma(
                reproduced, str(args.mode), float(args.rho_bar)
            )
        except ValueError as exc:
            if "got 0" not in str(exc):
                raise
            v5_compare = {
                "status": "NOT_APPLICABLE_NO_PHASE20R_REFERENCE",
                "reason": str(exc),
                "max_abs_diff": None,
                "by_z": {},
            }
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
            "n_valid_rows": int(meta["n_valid_rows"]),
            "d_sync_s": float(meta["d_sync_s"]),
            "d_sync_source": str(meta["d_sync_source"]),
            "sync_period_s": float(meta["sync_period_s"]),
            "z_step_k_min": int(meta["z_step_k_min"]),
            "z_step_k_max": int(meta["z_step_k_max"]),
            "z_min_realised_s": float(meta["z_min_realised_s"]),
            "z_max_realised_s": float(meta["z_max_realised_s"]),
            "bin_shares": list(meta["bin_shares"]),
            "status": str(meta["status"]),
            "mhat_bin_edges": meta["mhat_bin_edges"],
            "aoi_metadata": {k: meta[k] for k in meta if k.startswith("offset_") or k in ("aoi_profile", "link_order")},
            "anchor_ci95": block_bootstrap_anchor(df, n_boot=N_BOOT, seed=SEED_BOOT),
            "V5_reproduce_20R": reproduced,
            "V5_compare_20R": v5_compare,
            "NC1_z0": nc1,
            "staleness_path_diagnostic": staleness_path_diagnostic(
                str(args.mode),
                float(args.rho_bar),
                calibration_path=str(args.calibration),
            ) if args.aoi_profile == "U0" else {},
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
                "d_sync_s": float(meta["d_sync_s"]),
                "sync_period_s": float(meta["sync_period_s"]),
                "z_edges_primary": list(meta["z_edges_primary"]),
                "z_edges_secondary": list(meta["z_edges_secondary"]),
                "sha256": {
                    f: _sha256(f)
                    for f in (
                        TRUTH_TABLE,
                        str(args.calibration),
                        "results/SUPERSEDED/phase-20R/decision_error_constant_sigma.parquet",
                        "twin/cost_v2.py",
                        "twin/link_model_v2.py",
                        "cert/margin_score.py",
                        "cert/simultaneous_score.py",
                        "cert/build_calib_set_v3.py",
                    )
                    if os.path.exists(f)
                },
            },
            # Lesson 23.17 -- pham vi hieu luc, SUY RA tu bo sinh z that su
            # duoc goi o dong 217/328, khong phai mot chuoi khai bao tay.
            "validity": validity_block(
                aoi_generator=(AOI_V7 if str(args.axis) == AXIS_MEASURED
                               else sawtooth_age_steps),
                z_edges=(Z_EDGES_V7 if str(args.axis) == AXIS_MEASURED
                         else meta["z_edges_primary"]),
                sla_path=str(args.calibration),
                w_loss=float(meta["w_loss"]),
                omega=None,          # truc omega chua ton tai (Lesson 23.26)
            ) | ({"pending_on": _pending_axes()} if not _all_axes_approved()
                 else {}),
        }
    )

    # Duong dan dau ra: uu tien --out/--report; neu khong thi dung --out-stem;
    # neu ca hai deu khong co thi DAN XUAT theo tang + dinh danh (23-49b muc 3).
    if args.out is None or args.report is None:
        stem = args.out_stem or out_stem(
            str(args.axis), str(args.mode), float(args.rho_bar),
            str(args.aoi_profile))
        args.out = args.out or (stem + ".parquet")
        args.report = args.report or (stem + "_report.json")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    df.to_parquet(args.out, index=False)
    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(_json_clean(report), f, indent=1, sort_keys=True)
        f.write("\n")
    print(json.dumps(_json_clean({k: v for k, v in report.items() if k != "provenance"}), indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
