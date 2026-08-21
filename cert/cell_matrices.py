"""Module NEN cho Lesson 23.7 -- ma tran chi phi mot cell va conformal Mondrian.

Module nay la TANG DAY. No KHONG duoc import bat ky `cert.lesson23_7_*` nao,
va cung khong duoc import `cert.conditioning_audit`. Moi script hieu chuan va
script cham diem deu import XUONG day, khong bao gio import NGANG nhau.

Ly do (rut ra o buoc [3a]): truoc refactor, chuoi import la
    calibration_2b  ->  feasibility  ->  range_calibration
Sua mot ham o `range_calibration` se am tham doi ket qua cua `calibration_2b`,
trong khi artifact cua ca ba DA COMMIT. Mot chuoi ba tang giua cac script cung
cap bac la mot nguon lech khong ai nhin thay.

Thuc thi bang `test_ba_script_hieu_chuan_khong_import_lan_nhau`.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from typing import Any, Dict, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

from cert import simultaneous_score as SS
from cert.build_calib_set_v2 import (
    SEEDS,
    SIGMA,
    Z_EDGES_PRIMARY,
    assign_bin,
    block_len,
    split_by_block,
)
from cert.build_calib_set_v3 import (
    DT,
    N,
    N_MHAT_BINS,
    _load_cell,
    _valid_rows,
    assign_mhat_bin,
    y_hat_row_shift,
)
from cert.simultaneous_score import conformal_level, empirical_qhat
from measurements.decision_error_v2 import TruthTable, _cell_arrays
from twin import cost_v2 as C
from twin import topology_v7 as T7

# ---------------------------------------------------------------------------
# Hang so khoa -- dung chung cho ca ba buoc hieu chuan va buoc cham diem
# ---------------------------------------------------------------------------

MAIN_CELL = "poisson@0.925"
MAIN_CALIB = "results/phase-22/calib_set_v3.parquet"
MAIN_QHAT = "results/phase-23/fallback_poisson_0.925_k0.5.json"
MAIN_AUDIT = "results/phase-23/baseline_c3_b2_audit_poisson_0.925_C3_static.json"
SCAN_20R = "results/phase-20R/breakdown_scan_cascade.json"
TRUTH_TABLE = "results/phase-20R/truth_table.parquet"
SLA_CALIB = "results/phase-20R/sla_calibration.json"
RESIDUAL = "results/phase-20R/residual_cascade.json"

HELD_OUT_CELLS = ("poisson@0.850", "h2@0.700")
SCOPE_GUARD = (MAIN_CELL,)

ALPHA_FAMILY = 0.10
K_NOMINAL = 4
M_NOMINAL = K_NOMINAL - 1
ALPHA_EACH_NOMINAL = ALPHA_FAMILY / M_NOMINAL
DEAD_ACTION_THRESHOLD = 0.05
GAMMA_OP = 0.78
KAPPA_ANCHOR = 0.5

MODE = "poisson"
RHO_BAR = 0.925
CHANNEL = "loss"
VARIANT = "common_mode"

SLOTS = (1, 2, 3)
N_PATHS = len(T7.PATH_NAMES)

# M-D9: thang cat long nhau. Chi so = chi so DUONG (P1 = 0), khong phai slot.
LADDER: Tuple[Tuple[str, Tuple[int, ...]], ...] = (
    ("S0", ()),
    ("S1", (1,)),
    ("S2", (1, 3)),
)


# ---------------------------------------------------------------------------
# Tien ich
# ---------------------------------------------------------------------------

def git(*cmd: str) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=False).stdout.strip()
    except OSError:  # pragma: no cover
        return ""


def json_clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_clean(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        f = float(value)
        return f if np.isfinite(f) else None
    return value


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pin(path: str) -> Dict[str, Any]:
    """Ghim artifact buoc truoc vao provenance.

    Neu buoc truoc bi chay lai, buoc sau do ngay thay vi am tham lech.
    """
    try:
        return {"path": path, "sha256": sha256_of(path)}
    except OSError:
        return {"path": path, "sha256": None}


# ---------------------------------------------------------------------------
# Ma tran chi phi cua mot cell
# ---------------------------------------------------------------------------

def cell_matrices(
    tt: TruthTable,
    mode: str = MODE,
    rho_bar: float = RHO_BAR,
    seeds: Sequence[int] = SEEDS,
    n: int = N,
    w_loss_override: float | None = None,
    calibration_path: str = SLA_CALIB,
) -> Dict[str, np.ndarray]:
    """Ma tran chi phi that / du doan twin, theo dung duong ong `build_one_v3`.

    `y_true` di tu `tt`  -- THUC TE, co the bi bom residual.
    `y_hat`  di tu `cv2` -- MO HINH twin, KHONG bao gio bi bom.

    Su tach doi nay da co san trong `_cell_arrays`; day la ly do phan tich do
    nhay lam duoc ma khong phai sua kien truc.
    """
    cv = C.CostV2(strict_reliable=False)
    cell = _load_cell(
        str(mode), float(rho_bar), calibration_path=str(calibration_path)
    )
    lb = block_len(DT)
    yt, yh, lt, zs, bid, sd = [], [], [], [], [], []
    for seed in seeds:
        arr = _cell_arrays(
            tt,
            cv,
            cell,
            seed=int(seed),
            n=int(n),
            dt=DT,
            sigma_override=SIGMA,
            w_loss_override=w_loss_override,
        )
        cur, old, _ = _valid_rows(int(n), DT)
        yt.append(arr["c_true"][cur])
        yh.append(y_hat_row_shift(arr["c_fresh"], old))
        lt.append(arr["l_true"][cur])
        zs.append((cur - old) * float(DT))
        bid.append((int(seed) * 100_000 + cur // lb).astype(np.int32))
        sd.append(np.full(len(cur), int(seed), dtype=np.int16))
    return {
        "y_true": np.concatenate(yt, axis=0),
        "y_hat": np.concatenate(yh, axis=0),
        "loss_true": np.concatenate(lt, axis=0),
        "z_s": np.concatenate(zs, axis=0),
        "block_id": np.concatenate(bid, axis=0),
        "seed": np.concatenate(sd, axis=0),
    }


def prepare(base: Mapping[str, np.ndarray]) -> Dict[str, Any]:
    """Bin tuoi, chia calib/test theo block, va `a*` tren TOAN BO khong gian."""
    return {
        "z_bin": assign_bin(base["z_s"], Z_EDGES_PRIMARY),
        "is_calib": split_by_block(
            pd.DataFrame({"block_id": base["block_id"]})
        )["is_calib"].to_numpy(bool),
        "block_id": base["block_id"],
        "a_star_full": base["y_true"].argmin(axis=1),
    }


# ---------------------------------------------------------------------------
# Conformal Mondrian
# ---------------------------------------------------------------------------

def mhat_bin(values: np.ndarray, is_calib: np.ndarray, n_bins: int = N_MHAT_BINS) -> np.ndarray:
    """Bin phan vi tren `m_hat`, canh lay tu HANG CALIB.

    Dung `mhat_bin_edges` cua `build_calib_set_v3` -- KHONG phai tu toan bo
    cell. Lay tu toan bo cell lam ro ri test vao viec dinh nghia o Mondrian va
    lam lech ti le chap nhan (do duoc: 0.4917 thay vi 0.4911).
    """
    qs = np.linspace(0.0, 1.0, int(n_bins) + 1)[1:-1]
    edges = np.quantile(np.asarray(values, dtype=np.float64)[is_calib], qs)
    return assign_mhat_bin(np.asarray(values, dtype=np.float64), edges).astype(np.int64)


def fit_and_accept(
    z_bin: np.ndarray,
    m_bin: np.ndarray,
    block_id: np.ndarray,
    is_calib: np.ndarray,
    m_hat: np.ndarray,
    s_pair: np.ndarray,
    alpha_each: float,
    kappa: float,
) -> np.ndarray:
    """Mondrian conformal, dung `conformal_level` + `empirical_qhat` nhu C3."""
    n_slots = s_pair.shape[1]
    q: Dict[Tuple[int, int], np.ndarray] = {}
    for zb in np.unique(z_bin):
        for mb in np.unique(m_bin):
            sel = is_calib & (z_bin == zb) & (m_bin == mb)
            if not sel.any():
                continue
            n_eff = int(pd.unique(block_id[sel]).size)
            lvl = conformal_level(n_eff, float(alpha_each))
            q[(int(zb), int(mb))] = np.asarray(
                [empirical_qhat(s_pair[sel, j], lvl) for j in range(n_slots)],
                dtype=np.float64,
            )
    miss = np.full(n_slots, np.inf, dtype=np.float64)
    qrows = np.vstack([q.get((int(a), int(b)), miss) for a, b in zip(z_bin, m_bin)])
    return (m_hat >= float(kappa) * qrows).all(axis=1)


def acceptance_for(
    base: Mapping[str, np.ndarray],
    prep: Mapping[str, Any],
    pruned: Sequence[int],
    alpha_each: float,
    kappa: float = KAPPA_ANCHOR,
) -> Dict[str, Any]:
    """Ti le chap nhan tren TEST cho mot cau hinh (tap duong giu lai, alpha)."""
    keep = [p for p in range(N_PATHS) if p not in pruned]
    yt = base["y_true"][:, keep]
    yh = base["y_hat"][:, keep]
    m_hat = SS.pair_margins_hat(yh)
    s_pair = SS.pair_scores(yt, yh)
    m_b = mhat_bin(m_hat[:, 0], prep["is_calib"])
    acc = fit_and_accept(
        prep["z_bin"], m_b, prep["block_id"], prep["is_calib"],
        m_hat, s_pair, float(alpha_each), float(kappa),
    )
    return {
        "pruned": ["P%d" % (p + 1) for p in pruned],
        "n_slots": int(m_hat.shape[1]),
        "alpha_each": float(alpha_each),
        "acceptance_test": float(acc[~prep["is_calib"]].mean()),
    }
