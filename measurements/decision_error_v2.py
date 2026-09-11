#!/usr/bin/env python3
"""Phase 20R -- decision error with measured ground truth (Lesson 20R.5).

Compared with Phase 20, the true cost comes from the measured truth table while
the twin still uses ``link_model_v2``. Therefore ``err(z=0)`` is model error,
not a bug. Only the perfect-twin control is required to be exactly zero.

[20R2.5-P4] DAI LUONG NAO bang 0 -- cau tren MO HO, va chinh su mo ho do da
cho mot MENH DE LUON DUNG dung ten "doi chung" (NC1b: so c_true.argmin voi
chinh no). "Twin hoan hao" KHONG co nghia err = 0 o moi z: twin hoan hao ve
MO HINH van dung du lieu CU. Hop dong DUNG, cuong che boi perfect_twin_control:

    err_model == 0 . rms_e_model == 0 . err_total(z) == err_stale(z) moi z
    err_total(z = 0) == 0
    + doi chung cua doi chung: ton tai z > 0 co err_total > 0

Tuc "exactly zero" o tren la noi ve err_model va ve err_total TAI z = 0, KHONG
phai ve err_total tai moi z.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from measurements import sla_calib_v2 as SLA
from measurements.decision_error import check_z_grid, sawtooth_age_steps
from mininet.rho_spec import ou_trajectory
from twin import cost_v2 as C
from twin import topology_v7 as T7


DT = 0.005

# CHI dung cho doi chung hoi quy 20R/21R/22/23. KHONG duoc dung lam mac
# dinh cho run moi: moi run T2 phai truyen --tau tuong minh.
# Xem docs/GLOSSARY.md muc "tau_load".
TAU_LOAD_LEGACY = 1.0
# Bi danh giu nguyen hop dong import: cert/build_calib_set_v2.py va
# cert/build_calib_set_v3.py import truc tiep ten `TAU`. Doi ten cung
# o day se pha lo chung nhan, khong phai cai T2.2 nham toi.
TAU = TAU_LOAD_LEGACY

N = 200_000
CONTROL_N = 50_000

# --- A-T2-3: module nay PHAI tu khai estimand cua no --------------------
# Lich su: cot `rms_e_model` cua module nay (all_action / delay_ms) da bi doc
# nham thanh `rms_e_model` cua cert/tau_sweep.py (margin / cost_ms), lam T2.6
# luot 2 do sai dai luong so voi du doan da ky.
# Xem docs/GLOSSARY.md muc "SO DANG KY ESTIMAND".
ESTIMAND_ID = "RMS_ALLACTION_DELAY"

# ESTIMAND_ID o tren la nhan MUC ARTIFACT, va no KHONG DU DO PHAN GIAI: mot
# artifact cua run_cell mang MOT nhan, trong khi per_z[] cua no chua BA dai
# luong khac THANG va khac DON VI. Dung nhan muc-artifact de phan quyet mot
# du doan la lap lai DUNG loi A-T2-3, chi o do phan giai thap hon.
#
# Vi vay 20R2 khai theo TRUONG. Day moi la thu duoc trich dan khi phan quyet.
ESTIMAND_BY_FIELD = {
    # ti le hang sai, khong thu nguyen, [0, 1]
    "err_total": "DECISION_ERR_BY_AGE",
    "err_model": "DECISION_ERR_BY_AGE",
    "err_stale": "DECISION_ERR_BY_AGE",
    # [20R2.7-B1] HIEU TI LE VI PHAM, KHONG thu nguyen, [-1, 1]. Chu thich cu
    # ghi "chi phi, ms -- DI QUA ham chi phi" la SAI: _viol (dong 388) la mot
    # phep so NGUONG tra BOOLEAN, va dong 567 lay HIEU HAI TRUNG BINH cua no.
    # Ham chi phi chi cham vao GIAN TIEP qua viec chon argmin.
    "d_sla": "SLA_VIOL_BY_AGE",
    # do tre thuan, ms -- w_loss KHONG cham toi duoc
    "rms_e_model": "RMS_ALLACTION_DELAY",
    "rms_e_stale": "RMS_ALLACTION_DELAY",
    "cov_e": "RMS_ALLACTION_DELAY",
}

# Kenh (c): block conformal PHAI theo thoi gian tuong quan, khong phai
# theo giay. cert/tau_sweep.py da lam dung tu 22.6; day la day bi thieu.
BLOCKS_PER_TAU = 5.0
# Bi danh: measurements/band_v2.py:31 va test_phase20r6_band.py:423 doc
# `BLOCK_S`. Gio no TU DAN ra tu quy tac 5*tau thay vi la hang so 5 giay.
BLOCK_S = BLOCKS_PER_TAU * TAU_LOAD_LEGACY
N_BOOT = 2000
# --- LUOI z: HAI luoi, chon TUONG MINH  [20R2-D3] --------------------------
#
# Luoi LEGACY. GIU NGUYEN GIA TRI: 166 artifact cua T2 dieu kien theo no, va
# 20R2.3 dung chung lam neo hoi quy. Doi so o day = pha neo.
# A3' cua prereg 20R2 chi ra: luoi nay phu KHIT mien LEGACY [0.055, 0.550],
# nen chay 20R2 tren no la lang le tra loi cau hoi cua truc cu.
Z_GRID = (0.0, 0.05, 0.10, 0.20, 0.30, 0.55)
Z_EXTRAP = (1.0, 2.0, 4.0)
Z_ALL = Z_GRID + Z_EXTRAP

# Luoi 20R2, KY tai docs/phase-20R2/00-preregistration.md muc 4.
# Phu KHIT mien MEASURED [0.115, 0.615] (san that d_base = 0.115) thay vi
# mien legacy.
Z_GRID_20R2_MEASURED = (0.115, 0.170, 0.241, 0.305, 0.366,
                        0.430, 0.491, 0.555, 0.615)
Z_CONTROL_20R2 = (0.0,)          # doi chung: err(z=0) = err_model = SAN mo hinh
Z_ALL_20R2 = Z_CONTROL_20R2 + Z_GRID_20R2_MEASURED + Z_EXTRAP    # 13 diem

# max(Z_ALL) == max(Z_ALL_20R2) == 4.0 CO CHU DICH: scoring_window_start lay
# max cua luoi, nen HAI luoi cham diem tren CUNG dai hang. Doi max cua mot
# ben se lam hai luoi khong so duoc voi nhau -- xem docstring
# scoring_window_start ve loi "hai nhanh cham tren hai dai hang khac nhau".
Z_GRIDS = {"legacy": Z_ALL, "20r2_measured": Z_ALL_20R2}
Z_SCALED_RATIOS = (0.10, 0.30, 0.55, 1.00)


def z_grid_id_of(z_values: Sequence[float]) -> str:
    """SUY RA ten luoi tu CHINH cac diem z da chay -- khong nhan loi khai.

    Trong decision_error_v2, truc AoI KHONG di qua mot bo sinh nao; no di vao
    DUY NHAT qua VIEC CHON LUOI z (T2-L8 dinh chinh co che). Nen ten luoi LA
    nhan truc AoI cua artifact nay, va no phai duoc SUY RA nhu moi nhan khac
    (validity.py, Luat 2: nhan phai duoc suy ra, khong duoc khai bao).

    Do duoc 20R2.5-P5: mot sidecar sinh voi luoi LEGACY qua MOI kiem tang LIVE
    vi khong cai nao nhin thay truc AoI. Ham nay la thu cai chan can.
    """
    got = tuple(round(float(z), 12) for z in z_values)
    for name, grid in Z_GRIDS.items():
        if got == tuple(round(float(z), 12) for z in grid):
            return name
    return "UNREGISTERED_Z_GRID"

TRUTH_TABLE = "results/LIVE/phase-20R/truth_table.parquet"
CALIBRATION = "results/LIVE/phase-20R/sla_calibration.json"
CONTROLS_OUT = "results/SUPERSEDED/phase-20R/controls.json"
FIXED_OUT = "results/LIVE/phase-20R/decision_error_by_age_by_regime.parquet"
SUMMARY_OUT = "results/SUPERSEDED/phase-20R/decision_error_by_age_summary.parquet"
SAWTOOTH_OUT = "results/SUPERSEDED/phase-20R/decision_error_sawtooth.json"
MARGIN_CV_OUT = "results/SUPERSEDED/phase-20R/margin_cv_by_tau.parquet"
MARGIN_CV_CI_OUT = "results/SUPERSEDED/phase-20R/margin_cv_ci.json"
RHO_SOURCE = "calibration_ar1"
EXTRA_RHO_MODES = ("poisson", "h2")


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_json(path: str, data: object) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def z_key(z_s: float) -> str:
    return "%.3f" % float(z_s)


def load_calibration(path: str = CALIBRATION) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        report = json.load(f)
    return [dict(row) for row in report["cells"]]


def block_s_for_tau(tau: float) -> float:
    """Kenh (c): kich thuoc block conformal theo thoi gian tuong quan.

    'one block is always 5 tau, not always 5 seconds' -- cert/tau_sweep.py,
    Lesson 22.6. Giu 5 giay cung khi tau doi se lam so block moi seed sai,
    va conformal mat rang buoc calib/test.
    """
    tau = float(tau)
    if tau <= 0.0:
        raise ValueError("tau phai duong")
    return BLOCKS_PER_TAU * tau


def z_values_for(tau: float = TAU, scaled: bool = False,
                 z_grid: str = "legacy") -> Tuple[float, ...]:
    """Luoi z cua mot nhanh.

    `z_grid` CHI anh huong nhanh fixed. Nhanh scaled sinh z tu ti so nhan tau
    nen no khong doc luoi nao ca -- ghi ra day de khong ai tuong `--z-grid`
    doi duoc nhanh scaled.
    """
    if not scaled:
        try:
            grid = Z_GRIDS[z_grid]
        except KeyError:
            raise ValueError(
                "z_grid khong hop le: %r. Chon mot trong %s"
                % (z_grid, sorted(Z_GRIDS))) from None
        return tuple(float(z) for z in grid)
    return tuple(round(float(ratio) * float(tau), 12) for ratio in Z_SCALED_RATIOS)


def scoring_window_start(tau: float, dt: float) -> int:
    """Hang dau tien duoc cham diem -- DOC LAP VOI NHANH.

    Cu: common_start = max(z_values)/dt, lay tu luoi z cua NHANH DANG CHAY.
        fixed  dung Z_ALL          -> hang 800 voi MOI tau (4.0 s)
        scaled dung Z_SCALED*tau   -> hang 100 o tau=0.5, 5600 o tau=28
    => hai nhanh cham diem tren HAI DAI HANG KHAC NHAU, va do lech DOI DAU
       theo tau (scaled som hon o tau nho, muon hon o tau lon). Mot doi chung
       co do lech doi dau theo truc dang quet thi khong doc duoc.
    Bang chung: rms_e_model KHONG phu thuoc z chut nao ma van khac ~0.05%
                giua hai nhanh -- chi xay ra neu cua so khac nhau.

    LUU Y: viec bo qua cac hang dau KHONG phai de cat transient. ar1_matrix
    khoi tao x[0] = mu + sigma*N(0,1), tuc TU PHAN PHOI DUNG (sla_calib_v2
    dong 125), nen khong co burn-in. Cua so nay chi can du de lag_rows >= 0
    cho MOI muc z cua CA HAI nhanh. Neu ai do doi khoi tao x[0], dong nay
    phai duoc xet lai.
    """
    z_union = set(z_values_for(tau, scaled=False)) | set(z_values_for(tau, scaled=True))
    return max(int(round(float(z) / float(dt))) for z in z_union)


def z_over_tau(z_s: float, tau: float) -> float:
    if not float(tau):
        return math.nan
    return round(float(z_s) / float(tau), 12)


def resolve_sigma(cal_cell: Mapping[str, Any], sigma_override: Optional[float] = None, a_override: Optional[float] = None) -> Tuple[float, str]:
    if sigma_override is not None and a_override is not None:
        raise ValueError("sigma_override and a_override are mutually exclusive")
    if sigma_override is not None:
        return float(sigma_override), "override"
    if a_override is not None:
        return float(a_override) * float(cal_cell["sigma_max"]), "a_override"
    return float(cal_cell["sigma_rho"]), "calibration"


def feasible_cells(path: str = CALIBRATION, include_pc1: bool = True) -> List[Dict[str, Any]]:
    rows = []
    for cell in load_calibration(path):
        if not cell.get("feasible"):
            continue
        role = str(cell.get("role", ""))
        if role == "gate" or (include_pc1 and role.startswith("pc1")):
            rows.append(cell)
    return rows


def extra_calibrated_cells(
    rho_bars: Sequence[float],
    n: int = N,
    dt: float = DT,
    tau: float = TAU,
    seed: int = SLA.DEFAULT_SEED,
    modes: Sequence[str] = EXTRA_RHO_MODES,
) -> List[Dict[str, Any]]:
    if not rho_bars:
        return []
    cv2 = C.CostV2(strict_reliable=True)
    rows: List[Dict[str, Any]] = []
    for mode in modes:
        for rho_bar in rho_bars:
            cell = SLA.calibrate_cell(cv2, str(mode), float(rho_bar), seed=int(seed), n=int(n), dt=float(dt), tau=float(tau))
            if not cell.get("feasible"):
                raise ValueError("extra rho_bar %.3f infeasible for %s: %s" % (float(rho_bar), mode, cell.get("reason", "")))
            cell = dict(cell)
            cell["role"] = "h7_extra"
            cell["extra_rho_bar"] = True
            cell["extra_calibration_source"] = "measurements.sla_calib_v2.calibrate_cell"
            rows.append(cell)
    return rows


def measurement_cells(
    calibration_path: str = CALIBRATION,
    include_pc1: bool = True,
    rho_bar_extra: Sequence[float] = (),
    n: int = N,
    dt: float = DT,
    tau: float = TAU,
) -> List[Dict[str, Any]]:
    rows = feasible_cells(calibration_path, include_pc1=include_pc1)
    existing = {(str(row["mode"]), round(float(row["rho_bar"]), 12)) for row in rows}
    extra = []
    for cell in extra_calibrated_cells(rho_bar_extra, n=n, dt=dt, tau=tau):
        key = (str(cell["mode"]), round(float(cell["rho_bar"]), 12))
        if key not in existing:
            extra.append(cell)
            existing.add(key)
    return rows + extra


class TruthTable:
    """Measured lookup table. Linear interpolation, explicit clipping log."""

    def __init__(self, parquet_path: str = TRUTH_TABLE):
        table = pd.read_parquet(parquet_path)
        self.field = table.attrs.get("truth_field", "q_mean_ms")
        self.curves: Dict[Tuple[str, float, int], Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}
        for key, group in table.groupby(["mode", "bw", "q"], sort=True):
            group = group.sort_values("rho")
            self.curves[(str(key[0]), float(key[1]), int(key[2]))] = (
                group["rho"].to_numpy(float),
                group["delay_mean_ms"].to_numpy(float),
                group["loss"].to_numpy(float),
                group["se_mean_ms"].to_numpy(float),
            )
        self.clip_log: Dict[str, float] = {}

    def reset_clip_log(self) -> None:
        self.clip_log = {}

    def domain(self, mode: str, bw: float, q: int) -> Tuple[float, float]:
        rho = self.curves[(str(mode), float(bw), int(q))][0]
        return float(rho.min()), float(rho.max())

    def queue_delay_loss(self, mode: str, bw: float, q: int, rho: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        grid, delay, loss, _se = self.curves[(str(mode), float(bw), int(q))]
        rq = np.clip(np.asarray(rho, dtype=float), float(grid.min()), float(grid.max()))
        return np.interp(rq, grid, delay), np.interp(rq, grid, loss)

    def delay_loss(self, mode: str, link: str, rho: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        bw, base, q = T7.LINKS[link]
        grid, delay, loss, _se = self.curves[(str(mode), float(bw), int(q))]
        rho_arr = np.asarray(rho, dtype=float)
        lo, hi = float(grid.min()), float(grid.max())
        n_out = int(((rho_arr < lo) | (rho_arr > hi)).sum())
        self.clip_log["%s|%s" % (mode, link)] = n_out / max(int(rho_arr.size), 1)
        rq = np.clip(rho_arr, lo, hi)
        total_delay = float(base) + C.serialization_ms(bw) + np.interp(rq, grid, delay)
        return total_delay, np.interp(rq, grid, loss)

    def path_tables(self, mode: str, rho_mat: np.ndarray, w_loss: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        rho_mat = np.asarray(rho_mat, dtype=float)
        n = int(rho_mat.shape[0])
        delay = np.zeros((n, T7.K), dtype=float)
        keep = np.ones((n, T7.K), dtype=float)
        idx = {link: i for i, link in enumerate(T7.LINK_NAMES)}
        for action, path in enumerate(T7.PATH_NAMES):
            for link in T7.PATHS[path]:
                d, loss = self.delay_loss(mode, link, rho_mat[:, idx[link]])
                delay[:, action] += d
                keep[:, action] *= 1.0 - loss
        loss = 1.0 - keep
        return delay, loss, delay + float(w_loss) * loss


def rho_matrix_from_cell(
    mode: str,
    rho_bar: float,
    sigma: float,
    seed: int,
    tau: float = TAU,
    n: int = N,
    dt: float = DT,
    source: str = RHO_SOURCE,
    return_diagnostics: bool = False,
):
    """Return ``rho[t, link]`` for a Phase 20R operating cell.

    ``calibration_ar1`` matches ``sla_calib_v2`` and ``predict_err_quick``:
    independent AR(1) streams per link around the Q7 offset means. The
    ``scalar_ou`` source is kept only as a diagnostic because Q7 warns that
    common-mode rho can lock the path ranking and create artificial err ~= 0.
    """
    if source == "calibration_ar1":
        return SLA.ar1_matrix(mode, rho_bar, sigma, tau=tau, dt=dt, n=n, seed=seed,
                              return_diagnostics=return_diagnostics)
    if source != "scalar_ou":
        raise ValueError("unknown rho source %r" % source)
    traj = ou_trajectory(
        rho_bar=float(rho_bar),
        sigma_rho=float(sigma),
        tau_rho=float(tau),
        n_steps=int(n),
        seed=int(seed),
        dt=float(dt),
    )
    rho_t = np.asarray(traj.rho, dtype=float)
    out = np.stack(
        [np.clip(rho_t + C.LINK_OFFSET[link], C.RHO_MIN, C.RHO_MAX) for link in T7.LINK_NAMES],
        axis=1,
    )

    if return_diagnostics:
        return out, {"n_clipped_ratio": math.nan, "sigma_hat": math.nan, "cycles": math.nan}
    return out


def _viol(delay: np.ndarray, loss: np.ndarray, t_delay_ms: float, t_loss: float) -> np.ndarray:
    return (delay > float(t_delay_ms)) | (loss > float(t_loss))


def _cell_arrays(
    tt: TruthTable,
    cv2: C.CostV2,
    cal_cell: Mapping[str, Any],
    seed: int,
    tau: float = TAU,
    n: int = N,
    dt: float = DT,
    rho_source: str = RHO_SOURCE,
    sigma_override: Optional[float] = None,
    a_override: Optional[float] = None,
    w_loss_override: Optional[float] = None,
) -> Dict[str, Any]:
    mode = str(cal_cell["mode"])
    sigma, sigma_source = resolve_sigma(cal_cell, sigma_override=sigma_override, a_override=a_override)
    w_loss = float(w_loss_override) if w_loss_override is not None else float(cal_cell["w_loss"])
    tt.reset_clip_log()
    rho_mat, ar1_diag = rho_matrix_from_cell(
        mode,
        float(cal_cell["rho_bar"]),
        sigma,
        int(seed),
        tau=tau,
        n=n,
        dt=dt,
        source=rho_source,
        return_diagnostics=True,
    )
    d_true, l_true, c_true = tt.path_tables(mode, rho_mat, w_loss)
    d_fresh, l_fresh, c_fresh = cv2.tables_batch(rho_mat, mode, w_loss)
    a_true = c_true.argmin(axis=1)
    a_fresh = c_fresh.argmin(axis=1)
    return {
        "mode": mode,
        "rho_bar": float(cal_cell["rho_bar"]),
        "seed": int(seed),
        "tau_rho": float(tau),
        "sigma_rho": float(sigma),
        "sigma_rho_source": sigma_source,
        "w_loss": float(w_loss),
        "w_loss_source": "override" if w_loss_override is not None else "calibration",
        "n": int(n),
        "dt": float(dt),
        "rho_source": str(rho_source),
        "tt_domain_clip": dict(tt.clip_log),
        "ar1_clip_ratio": float(ar1_diag["n_clipped_ratio"]),
        "ar1_sigma_hat": float(ar1_diag["sigma_hat"]),
        "ar1_cycles": float(ar1_diag["cycles"]),
        "d_true": d_true,
        "l_true": l_true,
        "c_true": c_true,
        "d_fresh": d_fresh,
        "l_fresh": l_fresh,
        "c_fresh": c_fresh,
        "a_true": a_true,
        "a_fresh": a_fresh,
        "viol": _viol(d_true, l_true, float(cal_cell["t_delay_ms"]), float(cal_cell["t_loss"])),
    }


def _decomposition(
    d_true: np.ndarray,
    d_fresh: np.ndarray,
    k: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    m = slice(k, len(d_true))
    d_twin = d_fresh[: len(d_true) - k] if k else d_fresh
    e_model = d_true[m] - d_fresh[m]
    e_stale = d_fresh[m] - d_twin
    total = d_true[m] - d_twin
    if not np.allclose(e_model + e_stale, total, atol=1e-9):
        raise AssertionError("phan ra khong khop")
    return e_model, e_stale, total


def cost_margin_stats(cost: np.ndarray) -> Dict[str, float]:
    ordered = np.sort(np.asarray(cost, dtype=float), axis=1)
    margin = ordered[:, 1] - ordered[:, 0]
    mean = float(np.mean(margin))
    sd = float(np.std(margin, ddof=0))
    return {
        "margin_mean_ms": mean,
        "margin_sd_ms": sd,
        "margin_cv": sd / mean if mean > 0.0 else math.nan,
        "margin_p10_ms": float(np.percentile(margin, 10)),
        "margin_p50_ms": float(np.percentile(margin, 50)),
        "margin_p90_ms": float(np.percentile(margin, 90)),
    }


def run_cell(
    tt: TruthTable,
    cv2: C.CostV2,
    cal_cell: Mapping[str, Any],
    seed: int,
    tau: float = TAU,
    n: int = N,
    dt: float = DT,
    z_values: Sequence[float] = Z_ALL,
    rho_source: str = RHO_SOURCE,
    sigma_override: Optional[float] = None,
    a_override: Optional[float] = None,
    w_loss_override: Optional[float] = None,
) -> Dict[str, Any]:
    check_z_grid(z_values, dt)
    mode = str(cal_cell["mode"])
    rho_bar = float(cal_cell["rho_bar"])
    sigma, sigma_source = resolve_sigma(cal_cell, sigma_override=sigma_override, a_override=a_override)
    w_loss = float(w_loss_override) if w_loss_override is not None else float(cal_cell["w_loss"])
    t_delay = float(cal_cell["t_delay_ms"])
    t_loss = float(cal_cell["t_loss"])

    arrays = _cell_arrays(
        tt,
        cv2,
        cal_cell,
        seed,
        tau=tau,
        n=n,
        dt=dt,
        rho_source=rho_source,
        sigma_override=sigma_override,
        a_override=a_override,
        w_loss_override=w_loss_override,
    )
    d_true = arrays["d_true"]
    d_fresh = arrays["d_fresh"]
    a_true = arrays["a_true"]
    a_fresh = arrays["a_fresh"]
    viol = arrays["viol"]

    out: Dict[str, Any] = {
        "mode": mode,
        "rho_bar": rho_bar,
        "seed": int(seed),
        "tau_rho": float(tau),
        "sigma_rho": sigma,
        "sigma_rho_source": sigma_source,
        "w_loss": float(w_loss),
        "w_loss_source": "override" if w_loss_override is not None else "calibration",
        "n": int(n),
        "dt": float(dt),
        "rho_source": str(rho_source),
        "estimand_id": ESTIMAND_ID,
        "tt_domain_clip": dict(arrays["tt_domain_clip"]),
        "ar1_clip_ratio": float(arrays["ar1_clip_ratio"]),
        "ar1_cycles": float(arrays["ar1_cycles"]),
        "per_z": {},
    }
    rows = np.arange(int(n))
    common_start = scoring_window_start(tau, dt)
    if common_start >= int(n):
        raise ValueError("scoring window exceeds trace length")
    err_model_const = float((a_fresh[common_start:int(n)] != a_true[common_start:int(n)]).mean())
    for z_s in z_values:
        k = int(round(float(z_s) / float(dt)))
        if k > common_start or k >= int(n):
            raise ValueError("z %.3f exceeds trace length" % float(z_s))
        current = rows[common_start:int(n)]
        lag_rows = current - k
        a_twin = a_fresh[lag_rows]
        a_now = a_fresh[current]
        a_truth = a_true[current]
        e_model = d_true[current] - d_fresh[current]
        e_stale = d_fresh[current] - d_fresh[lag_rows]
        if not np.allclose(e_model + e_stale, d_true[current] - d_fresh[lag_rows], atol=1e-9):
            raise AssertionError("phan ra khong khop")
        out["per_z"][z_key(z_s)] = {
            "z_s": float(z_s),
            "z": float(z_s),
            "z_over_tau": z_over_tau(z_s, tau),
            "z_steps": int(k),
            "err_total": float((a_twin != a_truth).mean()),
            "err_model": err_model_const,
            "err_stale": float((a_twin != a_now).mean()),
            "d_sla": float(viol[current, a_twin].mean() - viol[current, a_truth].mean()),
            "rms_e_model": float(np.sqrt((e_model**2).mean())),
            "rms_e_stale": float(np.sqrt((e_stale**2).mean())),
            "cov_e": float(np.mean(e_model * e_stale)),
            "extrapolated": bool(float(z_s) in Z_EXTRAP),
        }
    return out


class PerfectTwin:
    """Twin HOAN HAO VE MO HINH: tra dung bang chi phi cua CHINH su that.

    Day la DOI CHUNG DUNG CU (do duong ong run_cell), khong phai do khoa hoc.
    Vi twin == su that nen err_model PHAI = 0. Nhung twin van dung du lieu CU
    (lag k buoc), nen err_total(z) = err_stale(z), KHONG phai 0 -- chi tai
    z = 0 moi bang 0.

    Thay cho NC1b [20R2.5-P4], von so `c_true.argmin` voi CHINH `a_true =
    c_true.argmin`, tuc mot MENH DE LUON DUNG, va khong he goi run_cell.
    """

    def __init__(self, tt: "TruthTable"):
        self.tt = tt

    def tables_batch(self, rho_mat: np.ndarray, mode: str, w_loss: float):
        return self.tt.path_tables(mode, rho_mat, w_loss)


def perfect_twin_control(
    calibration_path: str,
    *,
    tau: float,
    n: int,
    seed: int,
    z_values: Sequence[float],
    a_override: float,
    truth_path: str = TRUTH_TABLE,
) -> Dict[str, Any]:
    """Doi chung dung cu chay QUA CHINH run_cell -- nen no cham toi lag,
    cua so cham diem va dispatch luoi z, la nhung thu NC1b khong cham toi.

    HOP DONG (moi o, moi z):
      err_model == 0 . rms_e_model == 0 . err_total == err_stale
      err_total(z = 0) == 0
      + DOI CHUNG CUA DOI CHUNG: ton tai z > 0 co err_total > 0, neu khong thi
        lag khong lam gi ca va hop dong thoa mot cach TAM THUONG.

    Kill test 2026-09-10, cay loi lech-mot `lag_rows = current - k - 1`:
      doi chung nay err_total(z=0) = 0.026315 (BAT duoc) . NC1b = 0.0 (MU).
    """
    tt = TruthTable(truth_path)
    twin = PerfectTwin(tt)
    violations: List[Dict[str, Any]] = []
    max_err_pos = 0.0
    n_checked = 0
    for cell in feasible_cells(calibration_path, include_pc1=True):
        r = run_cell(tt, twin, cell, seed=seed, tau=tau, n=n,
                     z_values=z_values, a_override=a_override)
        for zk, m in r["per_z"].items():
            n_checked += 1
            broken = []
            if m["err_model"] != 0.0:
                broken.append("err_model != 0")
            if m["rms_e_model"] != 0.0:
                broken.append("rms_e_model != 0")
            if m["err_total"] != m["err_stale"]:
                broken.append("err_total != err_stale")
            if m["z_steps"] == 0 and m["err_total"] != 0.0:
                broken.append("err_total(z=0) != 0")
            if m["z_steps"] > 0:
                max_err_pos = max(max_err_pos, float(m["err_total"]))
            if broken:
                violations.append({
                    "cell": "%s@%.3f" % (cell["mode"], float(cell["rho_bar"])),
                    "z": zk, "broken": broken})
    return {"tau": float(tau), "n": int(n), "seed": int(seed),
            "n_checked": n_checked, "violations": violations,
            "max_err_total_z_positive": max_err_pos}


def block_bootstrap_paired(
    indicators: Mapping[str, np.ndarray],
    block_len: int,
    n_boot: int = N_BOOT,
    seed: int = 7,
) -> Dict[str, Tuple[float, float]]:
    n = len(next(iter(indicators.values())))
    n_blocks = n // int(block_len)
    if n_blocks <= 0:
        raise ValueError("block_len too large for n")
    rng = np.random.default_rng(int(seed))
    acc = {key: np.empty(int(n_boot), dtype=float) for key in indicators}
    offsets = np.arange(int(block_len))[None, :]
    for b in range(int(n_boot)):
        pick = rng.integers(0, n_blocks, size=n_blocks)
        idx = (pick[:, None] * int(block_len) + offsets).ravel()
        for key, values in indicators.items():
            acc[key][b] = np.asarray(values)[idx].mean()
    return {
        key: (float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5)))
        for key, values in acc.items()
    }


def _block_means(values: np.ndarray, block_len: int) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    n_blocks = len(arr) // int(block_len)
    if n_blocks <= 0:
        raise ValueError("block_len too large for values")
    return arr[: n_blocks * int(block_len)].reshape(n_blocks, int(block_len)).mean(axis=1)


def _bootstrap_from_block_means(
    by_name: Mapping[str, np.ndarray],
    n_boot: int = N_BOOT,
    seed: int = 7,
) -> Dict[str, Tuple[float, float]]:
    first = next(iter(by_name.values()))
    n_blocks = len(first)
    if any(len(v) != n_blocks for v in by_name.values()):
        raise ValueError("paired bootstrap needs equal block counts")
    rng = np.random.default_rng(int(seed))
    boot = {key: np.empty(int(n_boot), dtype=float) for key in by_name}
    for b in range(int(n_boot)):
        pick = rng.integers(0, n_blocks, size=n_blocks)
        for key, values in by_name.items():
            boot[key][b] = np.asarray(values, dtype=float)[pick].mean()
    return {
        key: (float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5)))
        for key, values in boot.items()
    }


def _fixed_metric_series(arrays: Mapping[str, Any], z_s: float, max_k: int) -> Dict[str, np.ndarray]:
    d_true = arrays["d_true"]
    d_fresh = arrays["d_fresh"]
    a_true = arrays["a_true"]
    a_fresh = arrays["a_fresh"]
    viol = arrays["viol"]
    n = int(arrays["n"])
    k = int(round(float(z_s) / float(arrays["dt"])))
    current = np.arange(max_k, n)
    twin_rows = current - k
    a_twin = a_fresh[twin_rows]
    a_now = a_fresh[current]
    a_truth = a_true[current]
    e_model, e_stale, _total = _decomposition(d_true[current], d_fresh[current], 0)
    stale = d_fresh[current] - d_fresh[twin_rows]
    if not np.allclose(e_model + stale, d_true[current] - d_fresh[twin_rows], atol=1e-9):
        raise AssertionError("phan ra khong khop")
    return {
        "err_total": (a_twin != a_truth).astype(float),
        "err_model": (a_now != a_truth).astype(float),
        "err_stale": (a_twin != a_now).astype(float),
        "d_sla": viol[current, a_twin].astype(float) - viol[current, a_truth].astype(float),
        "rms_e_model": np.mean(e_model * e_model, axis=1),
        "rms_e_stale": np.mean(stale * stale, axis=1),
        "cov_e": np.mean(e_model * stale, axis=1),
    }


def fixed_summary_with_bootstrap(
    truth_path: str = TRUTH_TABLE,
    calibration_path: str = CALIBRATION,
    out_path: str = SUMMARY_OUT,
    n: int = N,
    seeds: Sequence[int] = (101, 102, 103, 104, 105),
    tau: float = TAU,
    z_values: Sequence[float] = Z_ALL,
    block_s: float = BLOCK_S,
    n_boot: int = N_BOOT,
    rho_source: str = RHO_SOURCE,
    sigma_override: Optional[float] = None,
    a_override: Optional[float] = None,
    w_loss_override: Optional[float] = None,
) -> pd.DataFrame:
    check_z_grid(z_values, DT)
    block_len = int(round(float(block_s) / DT))
    max_k = scoring_window_start(tau, DT)  # A-T2-2: same window as run_cell
    if max_k >= int(n) or any(int(round(z / DT)) > max_k for z in z_values):
        raise ValueError("invalid scoring window for trace or z grid")
    tt = TruthTable(truth_path)
    cv2 = C.CostV2(strict_reliable=False)
    out_rows: List[Dict[str, Any]] = []
    for cell in feasible_cells(calibration_path, include_pc1=True):
        arrays_by_seed = [
            _cell_arrays(
                tt,
                cv2,
                cell,
                seed=seed,
                tau=tau,
                n=n,
                rho_source=rho_source,
                sigma_override=sigma_override,
                a_override=a_override,
                w_loss_override=w_loss_override,
            )
            for seed in seeds
        ]
        for z_s in z_values:
            by_metric_blocks: Dict[str, List[np.ndarray]] = {
                "err_total": [],
                "err_model": [],
                "err_stale": [],
                "d_sla": [],
                "rms_e_model": [],
                "rms_e_stale": [],
                "cov_e": [],
            }
            per_seed_means = {key: [] for key in by_metric_blocks}
            clip_max = 0.0
            for arrays in arrays_by_seed:
                clip_max = max(clip_max, max(arrays["tt_domain_clip"].values()) if arrays["tt_domain_clip"] else 0.0)
                series = _fixed_metric_series(arrays, z_s, max_k)
                for key, values in series.items():
                    if key.startswith("rms_"):
                        metric_values = np.sqrt(values)
                    else:
                        metric_values = values
                    per_seed_means[key].append(float(np.mean(metric_values)))
                    by_metric_blocks[key].append(_block_means(metric_values, block_len))
            blocks = {key: np.concatenate(parts) for key, parts in by_metric_blocks.items()}
            ci = _bootstrap_from_block_means(blocks, n_boot=n_boot, seed=7)
            row: Dict[str, Any] = {
                "mode": str(cell["mode"]),
                "rho_bar": float(cell["rho_bar"]),
                "z_key": z_key(z_s),
                "z_s": float(z_s),
                "z": float(z_s),
                "z_over_tau": z_over_tau(z_s, tau),
                "z_steps": int(round(float(z_s) / DT)),
                "tau_rho": float(tau),
                "sigma_rho": float(arrays_by_seed[0]["sigma_rho"]),
                "sigma_rho_source": str(arrays_by_seed[0]["sigma_rho_source"]),
                "w_loss": float(arrays_by_seed[0]["w_loss"]),
                "w_loss_source": str(arrays_by_seed[0]["w_loss_source"]),
                "n_seed": int(len(seeds)),
                "n": int(n),
                "block_len": int(block_len),
                "n_boot": int(n_boot),
                "rho_source": str(rho_source),
                "tt_domain_clip_max": float(clip_max),
                "extrapolated": bool(float(z_s) in Z_EXTRAP),
            }
            for key, means in per_seed_means.items():
                row[key] = float(np.mean(means))
                row[key + "_seed_sd"] = float(np.std(means, ddof=1)) if len(means) > 1 else 0.0
                row[key + "_ci95_lo"] = ci[key][0]
                row[key + "_ci95_hi"] = ci[key][1]
            out_rows.append(row)
    table = pd.DataFrame(out_rows)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(out, index=False)
    return table


def _sawtooth_metric_series(arrays: Mapping[str, Any]) -> Dict[str, np.ndarray]:
    d_true = arrays["d_true"]
    d_fresh = arrays["d_fresh"]
    a_true = arrays["a_true"]
    a_fresh = arrays["a_fresh"]
    viol = arrays["viol"]
    n = int(arrays["n"])
    dt = float(arrays["dt"])
    age = sawtooth_age_steps(n, dt)
    rows = np.arange(n)
    valid = rows >= age
    current = rows[valid]
    twin_rows = current - age[valid]
    a_twin = a_fresh[twin_rows]
    a_now = a_fresh[current]
    a_truth = a_true[current]
    e_model = d_true[current] - d_fresh[current]
    e_stale = d_fresh[current] - d_fresh[twin_rows]
    if not np.allclose(e_model + e_stale, d_true[current] - d_fresh[twin_rows], atol=1e-9):
        raise AssertionError("phan ra khong khop")
    return {
        "err_total": (a_twin != a_truth).astype(float),
        "err_model": (a_now != a_truth).astype(float),
        "err_stale": (a_twin != a_now).astype(float),
        "d_sla": viol[current, a_twin].astype(float) - viol[current, a_truth].astype(float),
        "rms_e_model": np.sqrt(np.mean(e_model * e_model, axis=1)),
        "rms_e_stale": np.sqrt(np.mean(e_stale * e_stale, axis=1)),
        "cov_e": np.mean(e_model * e_stale, axis=1),
        "age_s": age[valid].astype(float) * dt,
    }


def sawtooth_summary(
    truth_path: str = TRUTH_TABLE,
    calibration_path: str = CALIBRATION,
    out_path: str = SAWTOOTH_OUT,
    n: int = N,
    seeds: Sequence[int] = (101, 102, 103, 104, 105),
    tau: float = TAU,
    block_s: float = BLOCK_S,
    n_boot: int = N_BOOT,
    rho_source: str = RHO_SOURCE,
    sigma_override: Optional[float] = None,
    a_override: Optional[float] = None,
    w_loss_override: Optional[float] = None,
) -> Dict[str, Any]:
    check_z_grid(Z_ALL, DT)
    block_len = int(round(float(block_s) / DT))
    tt = TruthTable(truth_path)
    cv2 = C.CostV2(strict_reliable=False)
    rows = []
    summary_rows = []
    for cell in feasible_cells(calibration_path, include_pc1=True):
        by_metric_blocks: Dict[str, List[np.ndarray]] = {
            "err_total": [],
            "err_model": [],
            "err_stale": [],
            "d_sla": [],
            "rms_e_model": [],
            "rms_e_stale": [],
            "cov_e": [],
        }
        per_seed_means = {key: [] for key in by_metric_blocks}
        age_means = []
        age_min = math.inf
        age_max = 0.0
        clip_max = 0.0
        for seed in seeds:
            arrays = _cell_arrays(
                tt,
                cv2,
                cell,
                seed=seed,
                tau=tau,
                n=n,
                rho_source=rho_source,
                sigma_override=sigma_override,
                a_override=a_override,
                w_loss_override=w_loss_override,
            )
            clip_max = max(clip_max, max(arrays["tt_domain_clip"].values()) if arrays["tt_domain_clip"] else 0.0)
            series = _sawtooth_metric_series(arrays)
            age_means.append(float(np.mean(series["age_s"])))
            age_min = min(age_min, float(np.min(series["age_s"])))
            age_max = max(age_max, float(np.max(series["age_s"])))
            row = {
                "mode": str(cell["mode"]),
                "rho_bar": float(cell["rho_bar"]),
                "seed": int(seed),
                "tau_rho": float(tau),
                "sigma_rho": float(arrays["sigma_rho"]),
                "sigma_rho_source": str(arrays["sigma_rho_source"]),
                "w_loss": float(arrays["w_loss"]),
                "w_loss_source": str(arrays["w_loss_source"]),
                "n": int(n),
                "rho_source": str(rho_source),
                "tt_domain_clip_max": float(max(arrays["tt_domain_clip"].values()) if arrays["tt_domain_clip"] else 0.0),
                "age_mean_s": float(np.mean(series["age_s"])),
                "age_min_s": float(np.min(series["age_s"])),
                "age_max_s": float(np.max(series["age_s"])),
            }
            for key in by_metric_blocks:
                values = series[key]
                row[key] = float(np.mean(values))
                per_seed_means[key].append(row[key])
                by_metric_blocks[key].append(_block_means(values, block_len))
            rows.append(row)
        blocks = {key: np.concatenate(parts) for key, parts in by_metric_blocks.items()}
        ci = _bootstrap_from_block_means(blocks, n_boot=n_boot, seed=11)
        sigma, sigma_source = resolve_sigma(cell, sigma_override=sigma_override, a_override=a_override)
        summary = {
            "mode": str(cell["mode"]),
            "rho_bar": float(cell["rho_bar"]),
            "tau_rho": float(tau),
            "sigma_rho": float(sigma),
            "sigma_rho_source": sigma_source,
            "w_loss": float(w_loss_override) if w_loss_override is not None else float(cell["w_loss"]),
            "w_loss_source": "override" if w_loss_override is not None else "calibration",
            "n_seed": int(len(seeds)),
            "n": int(n),
            "block_len": int(block_len),
            "n_boot": int(n_boot),
            "rho_source": str(rho_source),
            "tt_domain_clip_max": float(clip_max),
            "age_mean_s": float(np.mean(age_means)),
            "age_min_s": float(age_min),
            "age_max_s": float(age_max),
        }
        for key, means in per_seed_means.items():
            summary[key] = float(np.mean(means))
            summary[key + "_seed_sd"] = float(np.std(means, ddof=1)) if len(means) > 1 else 0.0
            summary[key + "_ci95_lo"] = ci[key][0]
            summary[key + "_ci95_hi"] = ci[key][1]
        summary_rows.append(summary)
    report = {
        "phase": "20R.5",
        "script": "measurements.decision_error_v2",
        "kind": "sawtooth_operational",
        "config": {
            "n": int(n),
            "dt": DT,
            "tau": float(tau),
            "sigma_override": None if sigma_override is None else float(sigma_override),
            "a_override": None if a_override is None else float(a_override),
            "w_loss_override": None if w_loss_override is None else float(w_loss_override),
            "block_s": float(block_s),
            "block_len": int(block_len),
            "n_boot": int(n_boot),
            "seeds": [int(s) for s in seeds],
            "rho_source": str(rho_source),
        },
        "rows": rows,
        "summary": summary_rows,
    }
    write_json(out_path, report)
    return report


def _control_one(
    tt: TruthTable,
    cv2: C.CostV2,
    cal_cell: Mapping[str, Any],
    n: int,
    seed: int,
    rho_source: str,
    tau: float,
) -> Dict[str, Any]:
    mode = str(cal_cell["mode"])
    rho_mat = rho_matrix_from_cell(
        mode,
        float(cal_cell["rho_bar"]),
        float(cal_cell["sigma_rho"]),
        int(seed),
        # KHONG duoc la TAU: hang so do la 1.0, nen `--control --tau 10` se
        # im lang sinh rho o tau=1.0. NC3_one_step_churn phu thuoc TRUC TIEP
        # vao tau, va mot doi chung o tau SAI te hon khong co doi chung.
        tau=float(tau),
        n=int(n),
        dt=DT,
        source=rho_source,
    )
    tt.reset_clip_log()
    _d_true, _l_true, c_true = tt.path_tables(mode, rho_mat, float(cal_cell["w_loss"]))
    a_true = c_true.argmin(axis=1)

    # [20R2.5-P4] MENH DE LUON DUNG: `a_true` o tren CHINH LA c_true.argmin,
    # nen bieu thuc nay bang 0 vi DAI SO, khong vi dung cu dung. No cung khong
    # goi run_cell, nen khong cham toi lag / cua so cham diem / dispatch luoi z.
    # Kill test (lech-mot trong run_cell): cai nay 0.0, doi chung that 0.026315.
    # GIU LAI de khong pha bang so lich su; phep kiem dung cu THAT la
    # perfect_twin_control (tools/20r2_5_perfect_twin.py).
    nc1b = float((c_true.argmin(axis=1) != a_true).mean())
    rng = np.random.default_rng(99)
    nc2 = float((rng.integers(0, T7.K, size=int(n)) != a_true).mean())
    nc3 = float((a_true[:-1] != a_true[1:]).mean()) if int(n) > 1 else 0.0
    return {
        "mode": mode,
        "rho_bar": float(cal_cell["rho_bar"]),
        "seed": int(seed),
        "n": int(n),
        "rho_source": str(rho_source),
        "tau_rho": float(tau),
        "NC1b_perfect_twin": nc1b,
        "NC2_random_twin": nc2,
        "NC3_one_step_churn": nc3,
        "tt_domain_clip": dict(tt.clip_log),
    }


def controls(
    tt: TruthTable,
    cv2: C.CostV2,
    calibration_path: str = CALIBRATION,
    n: int = CONTROL_N,
    seed: int = 100,
    rho_source: str = RHO_SOURCE,
    *,
    tau: float,
) -> Dict[str, Any]:
    """Doi chung am. `tau` la KEYWORD-ONLY va KHONG co mac dinh.

    Keyword-only vi da co 5 tham so dung truoc: mot `tau` theo vi tri se
    doc duoc la mot con so vo nghia tai cho goi. Khong mac dinh vi tau la
    TRUC, khong phai tien nghi -- mot mac dinh im lang o day chinh la
    duong ma tau=1.0 len vao 20R/21R/22/23 ma khong ai ky (T2.0 muc F4).
    """
    check = check_z_grid(list(Z_ALL), DT)
    cells = feasible_cells(calibration_path, include_pc1=True)
    rows = [_control_one(tt, cv2, cell, n=n, seed=seed,
                         rho_source=rho_source, tau=tau) for cell in cells]
    pc1 = [row for row in rows if row["mode"] == "cbr"]
    return {
        "phase": "20R.5",
        "script": "measurements.decision_error_v2",
        "n_cells": len(rows),
        "n": int(n),
        "seed": int(seed),
        "rho_source": str(rho_source),
        "tau_rho": float(tau),
        "z_grid_check": check,
        "summary": {
            "NC1b_max_abs": float(max(abs(row["NC1b_perfect_twin"]) for row in rows)) if rows else math.nan,
            "NC2_min": float(min(row["NC2_random_twin"] for row in rows)) if rows else math.nan,
            "NC2_max": float(max(row["NC2_random_twin"] for row in rows)) if rows else math.nan,
            "NC2_pass_0p72_0p78": bool(rows and all(0.72 <= row["NC2_random_twin"] <= 0.78 for row in rows)),
            "PC1_cbr_one_step_churn_max": float(max((row["NC3_one_step_churn"] for row in pc1), default=0.0)),
        },
        "rows": rows,
    }


def flatten_cell_result(result: Mapping[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for z, metrics in result["per_z"].items():
        rows.append(
            {
                "mode": result["mode"],
                "rho_bar": result["rho_bar"],
                "seed": result["seed"],
                "tau_rho": result["tau_rho"],
                "sigma_rho": result["sigma_rho"],
                "sigma_rho_source": result["sigma_rho_source"],
                "w_loss": result["w_loss"],
                "w_loss_source": result["w_loss_source"],
                "n": result["n"],
                "dt": result["dt"],
                "z_key": z,
                **metrics,
                "tt_domain_clip_max": max(result["tt_domain_clip"].values()) if result["tt_domain_clip"] else 0.0,
                "ar1_clip_ratio": result["ar1_clip_ratio"],
                "ar1_cycles": result["ar1_cycles"],
                "extrapolation_contaminated": result["mode"] in ("poisson", "h2") and abs(result["rho_bar"] - 0.96) < 1e-9,
            }
        )
    return rows


def run_fixed_grid(
    truth_path: str = TRUTH_TABLE,
    calibration_path: Optional[str] = None,   # [20R2.5-P2] khong con mac dinh
    out_path: str = FIXED_OUT,
    n: int = N,
    seeds: Sequence[int] = (101, 102, 103, 104, 105),
    tau: float = TAU,
    z_values: Sequence[float] = Z_ALL,
    rho_source: str = RHO_SOURCE,
    sigma_override: Optional[float] = None,
    a_override: Optional[float] = None,
    w_loss_override: Optional[float] = None,
    rho_bar_extra: Sequence[float] = (),
) -> pd.DataFrame:
    if calibration_path is None:
        # [20R2.5-P2] PHAM VI: chi duong goi nay. fixed_summary_with_bootstrap,
        # sawtooth_summary va compute_margin_cv VAN con mac dinh -- xem §16.
        raise ValueError(
            "calibration_path phai truyen TUONG MINH: no CHON TRUC SLA. Mac dinh "
            "cu (self_calibrated) da lam se pilot 20R2 do bang chap nhan tren "
            "truc SAI ma khong bao mot loi nao [20R2.5-P2].")
    tt = TruthTable(truth_path)
    cv2 = C.CostV2(strict_reliable=False)
    rows = []
    cells = measurement_cells(calibration_path, include_pc1=True, rho_bar_extra=rho_bar_extra, n=n, tau=tau)
    for cell in cells:
        for seed in seeds:
            rows.extend(
                flatten_cell_result(
                    run_cell(
                        tt,
                        cv2,
                        cell,
                        seed=seed,
                        tau=tau,
                        n=n,
                        z_values=z_values,
                        rho_source=rho_source,
                        sigma_override=sigma_override,
                        a_override=a_override,
                        w_loss_override=w_loss_override,
                    )
                )
            )
    table = pd.DataFrame(rows)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(out, index=False)
    write_validity_sidecar(str(out), table, calibration_path, z_values)
    return table


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_validity_sidecar(
    out_path: str,
    table: pd.DataFrame,
    calibration_path: str,
    z_values: Sequence[float],
) -> str:
    """Ghi sidecar `<ten>_report.json` mang khoi `validity` (amendment 23-60).

    Parquet KHONG mang duoc khoi `validity` (metadata chi co key b'pandas'),
    nen no phai di kem mot file. Day la mau DA CO cua Phase 21R.

    KHONG khai `w_loss` bang tay: doc tu chinh bang vua sinh ra (Luat 2 --
    nhan phai duoc SUY RA, khong duoc KHAI BAO).
    """
    from measurements.validity import sla_only_validity_block

    w_set = sorted({float(x) for x in table["w_loss"]})
    side = out_path[: -len(".parquet")] + "_report.json"
    write_json(
        side,
        {
            "schema": "dt4n.decision_error.v2_report",
            "parquet": os.path.relpath(out_path, os.getcwd()),
            "parquet_sha256": _sha256_file(out_path),
            "n_rows": int(len(table)),
            "cells": sorted(
                {"%s@%.3f" % (r.mode, r.rho_bar) for r in table.itertuples()}
            ),
            "w_loss_values": w_set,
            "run_config": {          # [20R2.5] SUY RA tu bang vua sinh, khong khai
                "tau_rho": sorted({float(x) for x in table["tau_rho"]}),
                "n": sorted({int(x) for x in table["n"]}),
                "seeds": sorted({int(x) for x in table["seed"]}),
                "sigma_rho_source": sorted({str(x) for x in table["sigma_rho_source"]}),
            },
            "validity": {
                # A-T2-3: artifact nao khong khai estimand_id thi khong duoc
                # dung de phan quyet mot du doan da ky.
                "estimand_id": ESTIMAND_ID,
                # [20R2.5-P5] §12.7 da phat hien nhan muc-artifact KHONG du do
                # phan giai va da them ESTIMAND_BY_FIELD -- nhung khong noi nao
                # GHI no ra. Artifact van mang mot nhan cho ba dai luong khac
                # thang. Day la cho ghi no.
                "estimand_by_field": dict(ESTIMAND_BY_FIELD),
                # [20R2.5-P5] SUY RA tu diem z THUC SU chay, khong nhan loi khai.
                "z_grid_id": z_grid_id_of(z_values),
                **sla_only_validity_block(
                    sla_path=calibration_path,
                    w_loss=w_set[0] if len(w_set) == 1 else float("nan"),
                    z_grid=z_values,
                    note=(
                        "err_total/err_stale/d_sla PHU THUOC truc SLA; "
                        "rms_e_model/rms_e_stale/cov_e KHONG -- chung tinh tren "
                        "DELAY THUAN (d_true - d_fresh), khong qua ham chi phi, "
                        "nen w_loss khong cham toi duoc. Do duoc (G23-203): "
                        "max|diff| = 0.0 qua doi truc SLA."
                    ),
                ),
            },
        },
    )
    return side


def compute_margin_cv(
    calibration_path: str = CALIBRATION,
    out_path: str = MARGIN_CV_OUT,
    n: int = N,
    seeds: Sequence[int] = (101, 102, 103),
    tau_values: Sequence[float] = (TAU,),
    rho_source: str = RHO_SOURCE,
    sigma_override: Optional[float] = None,
    a_override: Optional[float] = None,
    w_loss_override: Optional[float] = None,
    rho_bar_extra: Sequence[float] = (),
) -> pd.DataFrame:
    cv2 = C.CostV2(strict_reliable=False)
    rows: List[Dict[str, Any]] = []
    for tau in tau_values:
        cells = measurement_cells(calibration_path, include_pc1=True, rho_bar_extra=rho_bar_extra, n=n, tau=float(tau))
        for cell in cells:
            mode = str(cell["mode"])
            rho_bar = float(cell["rho_bar"])
            sigma, sigma_source = resolve_sigma(cell, sigma_override=sigma_override, a_override=a_override)
            w_loss = float(w_loss_override) if w_loss_override is not None else float(cell["w_loss"])
            for seed in seeds:
                rho_mat = rho_matrix_from_cell(
                    mode,
                    rho_bar,
                    sigma,
                    int(seed),
                    tau=float(tau),
                    n=int(n),
                    dt=DT,
                    source=rho_source,
                )
                _delay, _loss, cost = cv2.tables_batch(rho_mat, mode, w_loss)
                stats = cost_margin_stats(cost)
                rows.append(
                    {
                        "mode": mode,
                        "rho_bar": rho_bar,
                        "seed": int(seed),
                        "tau_rho": float(tau),
                        "sigma_rho": float(sigma),
                        "sigma_rho_source": sigma_source,
                        "w_loss": float(w_loss),
                        "w_loss_source": "override" if w_loss_override is not None else "calibration",
                        "n": int(n),
                        "dt": DT,
                        "rho_source": str(rho_source),
                        **stats,
                    }
                )
    table = pd.DataFrame(rows)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(out, index=False)
    return table


def _cost_margin_series(cost: np.ndarray) -> np.ndarray:
    ordered = np.sort(np.asarray(cost, dtype=float), axis=1)
    return ordered[:, 1] - ordered[:, 0]


def _margin_cv_from_moments(mean: float, second_moment: float) -> float:
    var = max(float(second_moment) - float(mean) * float(mean), 0.0)
    return math.sqrt(var) / float(mean) if float(mean) > 0.0 else math.nan


def _margin_block_moments(values: np.ndarray, block_len: int) -> Tuple[np.ndarray, np.ndarray]:
    arr = np.asarray(values, dtype=float)
    n_blocks = len(arr) // int(block_len)
    if n_blocks <= 0:
        raise ValueError("block_len too large for margin series")
    blocks = arr[: n_blocks * int(block_len)].reshape(n_blocks, int(block_len))
    return blocks.mean(axis=1), (blocks * blocks).mean(axis=1)


def bootstrap_margin_cv_from_blocks(
    block_mean: np.ndarray,
    block_second_moment: np.ndarray,
    n_boot: int = N_BOOT,
    seed: int = 7,
) -> Dict[str, Any]:
    mean_blocks = np.asarray(block_mean, dtype=float)
    second_blocks = np.asarray(block_second_moment, dtype=float)
    if len(mean_blocks) != len(second_blocks):
        raise ValueError("block moment arrays must have equal length")
    if len(mean_blocks) <= 0:
        raise ValueError("need at least one block")
    observed_mean = float(np.mean(mean_blocks))
    observed_second = float(np.mean(second_blocks))
    observed = _margin_cv_from_moments(observed_mean, observed_second)
    rng = np.random.default_rng(int(seed))
    boot = np.empty(int(n_boot), dtype=float)
    for b in range(int(n_boot)):
        pick = rng.integers(0, len(mean_blocks), size=len(mean_blocks))
        boot[b] = _margin_cv_from_moments(float(np.mean(mean_blocks[pick])), float(np.mean(second_blocks[pick])))
    return {
        "margin_mean_ms": observed_mean,
        "margin_sd_ms": math.sqrt(max(observed_second - observed_mean * observed_mean, 0.0)),
        "margin_cv": observed,
        "margin_cv_ci95_lo": float(np.percentile(boot, 2.5)),
        "margin_cv_ci95_hi": float(np.percentile(boot, 97.5)),
        "margin_cv_boot_sd": float(np.std(boot, ddof=1)) if int(n_boot) > 1 else 0.0,
    }


def bootstrap_seed_mean_margin_cv(
    seed_blocks: Sequence[Tuple[np.ndarray, np.ndarray]],
    n_boot: int = N_BOOT,
    seed: int = 7,
) -> Dict[str, Any]:
    if not seed_blocks:
        raise ValueError("need at least one seed")
    rng = np.random.default_rng(int(seed))
    seed_cvs: List[float] = []
    seed_means: List[float] = []
    seed_sds: List[float] = []
    for block_mean, block_second in seed_blocks:
        mean_blocks = np.asarray(block_mean, dtype=float)
        second_blocks = np.asarray(block_second, dtype=float)
        if len(mean_blocks) != len(second_blocks):
            raise ValueError("block moment arrays must have equal length")
        if len(mean_blocks) <= 0:
            raise ValueError("need at least one block per seed")
        mean = float(np.mean(mean_blocks))
        second = float(np.mean(second_blocks))
        seed_means.append(mean)
        seed_sds.append(math.sqrt(max(second - mean * mean, 0.0)))
        seed_cvs.append(_margin_cv_from_moments(mean, second))
    boot = np.empty(int(n_boot), dtype=float)
    for b in range(int(n_boot)):
        cv_values = []
        for block_mean, block_second in seed_blocks:
            mean_blocks = np.asarray(block_mean, dtype=float)
            second_blocks = np.asarray(block_second, dtype=float)
            pick = rng.integers(0, len(mean_blocks), size=len(mean_blocks))
            cv_values.append(_margin_cv_from_moments(float(np.mean(mean_blocks[pick])), float(np.mean(second_blocks[pick]))))
        boot[b] = float(np.mean(cv_values))
    return {
        "margin_mean_ms": float(np.mean(seed_means)),
        "margin_sd_ms": float(np.mean(seed_sds)),
        "margin_cv": float(np.mean(seed_cvs)),
        "margin_cv_seed_sd": float(np.std(seed_cvs, ddof=1)) if len(seed_cvs) > 1 else 0.0,
        "margin_cv_ci95_lo": float(np.percentile(boot, 2.5)),
        "margin_cv_ci95_hi": float(np.percentile(boot, 97.5)),
        "margin_cv_boot_sd": float(np.std(boot, ddof=1)) if int(n_boot) > 1 else 0.0,
    }


def compute_margin_cv_ci(
    calibration_path: str = CALIBRATION,
    out_path: str = MARGIN_CV_CI_OUT,
    n: int = N,
    seeds: Sequence[int] = (101, 102, 103),
    tau_values: Sequence[float] = (TAU,),
    rho_source: str = RHO_SOURCE,
    sigma_override: Optional[float] = None,
    a_override: Optional[float] = None,
    w_loss_override: Optional[float] = None,
    rho_bar_extra: Sequence[float] = (),
    block_s: float = BLOCK_S,
    n_boot: int = N_BOOT,
) -> Dict[str, Any]:
    block_len = int(round(float(block_s) / DT))
    if block_len <= 0:
        raise ValueError("block_s too small")
    cv2 = C.CostV2(strict_reliable=False)
    rows: List[Dict[str, Any]] = []
    for tau in tau_values:
        cells = measurement_cells(calibration_path, include_pc1=True, rho_bar_extra=rho_bar_extra, n=n, tau=float(tau))
        for cell in cells:
            mode = str(cell["mode"])
            rho_bar = float(cell["rho_bar"])
            sigma, sigma_source = resolve_sigma(cell, sigma_override=sigma_override, a_override=a_override)
            w_loss = float(w_loss_override) if w_loss_override is not None else float(cell["w_loss"])
            seed_blocks: List[Tuple[np.ndarray, np.ndarray]] = []
            for seed in seeds:
                rho_mat = rho_matrix_from_cell(
                    mode,
                    rho_bar,
                    sigma,
                    int(seed),
                    tau=float(tau),
                    n=int(n),
                    dt=DT,
                    source=rho_source,
                )
                _delay, _loss, cost = cv2.tables_batch(rho_mat, mode, w_loss)
                margin = _cost_margin_series(cost)
                block_mean, block_second = _margin_block_moments(margin, block_len)
                seed_blocks.append((block_mean, block_second))
            stats = bootstrap_seed_mean_margin_cv(
                seed_blocks,
                n_boot=n_boot,
                seed=1301 + int(round(float(tau) * 1000)) + int(round(rho_bar * 1000)),
            )
            rows.append(
                {
                    "mode": mode,
                    "rho_bar": rho_bar,
                    "tau_rho": float(tau),
                    "sigma_rho": float(sigma),
                    "sigma_rho_source": sigma_source,
                    "w_loss": float(w_loss),
                    "w_loss_source": "override" if w_loss_override is not None else "calibration",
                    "n_seed": int(len(seeds)),
                    "n": int(n),
                    "dt": DT,
                    "block_s": float(block_s),
                    "block_len": int(block_len),
                    "n_blocks": int(sum(len(block_mean) for block_mean, _block_second in seed_blocks)),
                    "n_boot": int(n_boot),
                    "rho_source": str(rho_source),
                    **stats,
                }
            )
    report = {
        "phase": "20R.6",
        "script": "measurements.decision_error_v2",
        "kind": "margin_cv_block_bootstrap_ci",
        "config": {
            "n": int(n),
            "dt": DT,
            "seeds": [int(s) for s in seeds],
            "tau_values": [float(tau) for tau in tau_values],
            "sigma_override": None if sigma_override is None else float(sigma_override),
            "a_override": None if a_override is None else float(a_override),
            "w_loss_override": None if w_loss_override is None else float(w_loss_override),
            "rho_bar_extra": [float(rho) for rho in rho_bar_extra],
            "rho_source": str(rho_source),
            "block_s": float(block_s),
            "block_len": int(block_len),
            "n_boot": int(n_boot),
        },
        "rows": rows,
    }
    write_json(out_path, report)
    return report


def parse_int_list(text: str) -> Tuple[int, ...]:
    vals = [int(part.strip()) for part in str(text).split(",") if part.strip()]
    if not vals:
        raise ValueError("expected at least one seed")
    return tuple(vals)


def parse_float_list(text: str) -> Tuple[float, ...]:
    vals = [float(part.strip()) for part in str(text).split(",") if part.strip()]
    return tuple(vals)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--truth-table", default=TRUTH_TABLE)
    # [20R2.5-P2] KHONG CO MAC DINH. Mac dinh cu = sla_calibration.json, tuc
    # truc SLA self_calibrated (DEPRECATED, S14). Day la lan thu NAM cung mot
    # co che: DEFAULT_TAU, axis=AXIS_LEGACY, sigma=V3.SIGMA, --z-grid, va gio
    # --calibration. Do duoc: se pilot 20R2 da chay tren no du prereg §3 ky
    # exogenous -- xem docs/phase-20R2/00-preregistration.md §16.
    ap.add_argument("--calibration", required=True,
                    help="file SLA -- CHON TRUC SLA. 20R2: "
                         "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json. "
                         "Phat lai T2: results/LIVE/phase-20R/sla_calibration.json")
    ap.add_argument("--control", action="store_true", help="run mandatory controls first")
    ap.add_argument("--control-out", default=CONTROLS_OUT)
    ap.add_argument("--run-fixed", action="store_true", help="run fixed-z grid artifact")
    ap.add_argument("--summarize-fixed", action="store_true", help="run paired block bootstrap summary for fixed-z grid")
    ap.add_argument("--run-sawtooth", action="store_true", help="run operational sawtooth AoI summary")
    ap.add_argument("--compute-margin-cv", action="store_true", help="compute R = sd(cost margin) / mean(cost margin)")
    ap.add_argument("--compute-margin-cv-ci", action="store_true", help="compute block-bootstrap CI for R")
    ap.add_argument("--out", default=FIXED_OUT)
    ap.add_argument("--summary-out", default=SUMMARY_OUT)
    ap.add_argument("--sawtooth-out", default=SAWTOOTH_OUT)
    ap.add_argument("--n", type=int, default=None,
                    help="mac dinh: n_for_tau(tau, dt) -- giu >= 10 block moi seed")
    ap.add_argument("--control-n", type=int, default=CONTROL_N)
    ap.add_argument("--seeds", default="101,102,103,104,105")
    ap.add_argument("--rho-source", choices=("calibration_ar1", "scalar_ou"), default=RHO_SOURCE)
    ap.add_argument("--sigma-override", type=float, default=None)
    ap.add_argument("--a-override", type=float, default=None, help="set sigma_rho to a * sigma_max for every calibration cell")
    ap.add_argument("--w-loss-override", type=float, default=None)
    ap.add_argument("--rho-bar-extra", default="", help="comma-separated extra rho_bar values for h2/poisson H7 diagnostics")
    ap.add_argument("--tau", required=True,
                    help="THOI GIAN TUONG QUAN cua tai, GIAY. BAT BUOC, khong co "
                         "mac dinh (mot mac dinh im lang chinh la nguyen nhan F4). "
                         "Nhan mot tau hoac danh sach ngan cach bang dau phay cho "
                         "--compute-margin-cv.")
    ap.add_argument("--z-grid", choices=sorted(Z_GRIDS), required=True,
                    help="luoi z cho nhanh fixed. KHONG CO MAC DINH: mot mac "
                         "dinh im lang o day da dat dieu kien len toan bo T2 "
                         "ma khong ai ky [20R2-D3]. `legacy` phu mien "
                         "[0.055,0.550]; `20r2_measured` phu mien measured "
                         "[0.115,0.615] theo prereg 20R2 muc 4.")
    ap.add_argument("--z-mode", choices=("fixed", "scaled"), required=True,
                    help="fixed = NHANH B: z co dinh theo sync_period, KHONG co gian "
                         "theo tau (che do van hanh that, chua ai quet). "
                         "scaled = NHANH A: z/tau co dinh 0.10,0.30,0.55,1.00 "
                         "(tai tao 20R cu). Bat buoc chon tuong minh de lua chon "
                         "nay di vao provenance thay vi bi chon ngam.")
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--boot-metrics", default=None, help="accepted for audit compatibility; all metrics are bootstrapped")
    ap.add_argument("--block-s", type=float, default=None,
                    help="mac dinh: 5*tau (block_s_for_tau)")
    args = ap.parse_args(argv)
    if args.sigma_override is not None and args.a_override is not None:
        ap.error("--sigma-override and --a-override are mutually exclusive")
    if args.a_override is not None and args.a_override < 0.0:
        ap.error("--a-override must be non-negative")
    tau_values = parse_float_list(args.tau)
    if not tau_values:
        ap.error("--tau needs at least one value")
    if not (args.compute_margin_cv or args.compute_margin_cv_ci) and len(tau_values) != 1:
        ap.error("--tau may be a list only with --compute-margin-cv or --compute-margin-cv-ci")
    tau = tau_values[0]
    z_values = z_values_for(tau, scaled=(args.z_mode == "scaled"),
                            z_grid=args.z_grid)
    if args.n is None:
        args.n = SLA.n_for_tau(tau, DT)
    if args.block_s is None:
        args.block_s = block_s_for_tau(tau)
    rho_bar_extra = parse_float_list(args.rho_bar_extra)

    tt = TruthTable(args.truth_table)
    cv2 = C.CostV2(strict_reliable=False)
    if args.control:
        report = controls(tt, cv2, args.calibration, n=args.control_n,
                          rho_source=args.rho_source, tau=tau)
        write_json(args.control_out, report)
        print(json.dumps(report["summary"], indent=2, sort_keys=True))
        print("controls -> %s" % args.control_out)
    if args.run_fixed:
        table = run_fixed_grid(
            args.truth_table,
            args.calibration,
            args.out,
            n=args.n,
            seeds=parse_int_list(args.seeds),
            tau=tau,
            z_values=z_values,
            rho_source=args.rho_source,
            sigma_override=args.sigma_override,
            a_override=args.a_override,
            w_loss_override=args.w_loss_override,
            rho_bar_extra=rho_bar_extra,
        )
        print("fixed rows=%d -> %s" % (len(table), args.out))
    if args.summarize_fixed:
        table = fixed_summary_with_bootstrap(
            args.truth_table,
            args.calibration,
            args.summary_out,
            n=args.n,
            seeds=parse_int_list(args.seeds),
            tau=tau,
            z_values=z_values,
            block_s=args.block_s,
            n_boot=args.n_boot,
            rho_source=args.rho_source,
            sigma_override=args.sigma_override,
            a_override=args.a_override,
            w_loss_override=args.w_loss_override,
        )
        print("fixed summary rows=%d -> %s" % (len(table), args.summary_out))
    if args.run_sawtooth:
        report = sawtooth_summary(
            args.truth_table,
            args.calibration,
            args.sawtooth_out,
            n=args.n,
            seeds=parse_int_list(args.seeds),
            tau=tau,
            block_s=args.block_s,
            n_boot=args.n_boot,
            rho_source=args.rho_source,
            sigma_override=args.sigma_override,
            a_override=args.a_override,
            w_loss_override=args.w_loss_override,
        )
        print("sawtooth rows=%d -> %s" % (len(report["summary"]), args.sawtooth_out))
    if args.compute_margin_cv:
        table = compute_margin_cv(
            args.calibration,
            args.out,
            n=args.n,
            seeds=parse_int_list(args.seeds),
            tau_values=tau_values,
            rho_source=args.rho_source,
            sigma_override=args.sigma_override,
            a_override=args.a_override,
            w_loss_override=args.w_loss_override,
            rho_bar_extra=rho_bar_extra,
        )
        print("margin-cv rows=%d -> %s" % (len(table), args.out))
    if args.compute_margin_cv_ci:
        report = compute_margin_cv_ci(
            args.calibration,
            args.out,
            n=args.n,
            seeds=parse_int_list(args.seeds),
            tau_values=tau_values,
            rho_source=args.rho_source,
            sigma_override=args.sigma_override,
            a_override=args.a_override,
            w_loss_override=args.w_loss_override,
            rho_bar_extra=rho_bar_extra,
            block_s=args.block_s,
            n_boot=args.n_boot,
        )
        print("margin-cv-ci rows=%d -> %s" % (len(report["rows"]), args.out))
    if (
        not args.control
        and not args.run_fixed
        and not args.summarize_fixed
        and not args.run_sawtooth
        and not args.compute_margin_cv
        and not args.compute_margin_cv_ci
    ):
        ap.print_help()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
