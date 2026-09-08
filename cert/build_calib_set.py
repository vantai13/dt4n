#!/usr/bin/env python3
"""Phase 21 / Lesson 21.1 - build the conformal calibration table.

One row is one routing-decision time, not one ``(time, action)`` pair. This
keeps the effective sample size tied to blocks and makes the gate quantities
(``gap_twin``, signed-error scores, and ``u``) first-class columns.

The analysis unit is a physical block:
14.35 s = 5*tau_core. It is converted to samples per trace from dt_s.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from measurements.decision_error import (
    _viol_flags,
    build_cost_tables,
    decide,
    drop_warmup_matrix,
    read_trace_matrix,
    sawtooth_age_steps,
)
from twin.topology_v7 import JUMPS, K


# Frozen from Phase 20. Do not recalibrate in Phase 21.
W_LOSS = 1451.3765784675
T_DELAY = 14.513765784675
T_LOSS = 0.010
# DO DUOC tu trace v7 that (tai loi Mininet), KHAC voi tau_load = 1.0 la
# tham so THIET KE cua AR(1) tong hop. Hai dai luong, khong phai mau thuan
# -- da ghi o docs/phase-21R/00-preregistration.md R9.
# Vai tro: chuan hoa BIEN DIEU KIEN u (chia bin Mondrian), nen dung cong
# thuc CO DIEU KIEN sqrt(1-exp(-2z/tau)) chu khong phai cong thuc HIEU.
# Xem docs/GLOSSARY.md muc "sigma_z".
TAU_CORE_MEASURED_S = 2.87
# 14.35 giay, gio tu noi ra vi sao thay vi la mot hang so mo coi.
B_BLOCK_S = round(5.0 * TAU_CORE_MEASURED_S, 10)   # == 14.35 dung bang bit
WARMUP = 0.20
T0_S = 4.0
SIGMA_RHO = 0.010
EPS_REG = 1e-9

# Pre-registered Phase 21 bins.
AGE_EDGES = (0.06, 0.16, 0.26, 0.36, 0.46, 0.56)
MEASURED_AGE_EDGES = (0.10, 0.30, 0.70)
U_EDGES = (0.0, 1.0, 2.0, 3.0, np.inf)


def block_len_samples(dt_s: float) -> int:
    """Return the 5*tau block length in samples for this trace grid."""
    return max(1, int(round(B_BLOCK_S / float(dt_s))))


def t0_steps(dt_s: float) -> int:
    """Return the common Phase 20 window start in samples for this trace grid."""
    return max(1, int(round(T0_S / float(dt_s))))


def age_edges_for_dt(dt_s: float) -> tuple[float, ...]:
    """Use reduced measured-telemetry age bins when dt aliases the sawtooth."""
    return MEASURED_AGE_EDGES if float(dt_s) >= 0.05 else AGE_EDGES


def _sh(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def provenance(argv: Sequence[str]) -> dict:
    """Return reproducibility metadata, following the repo MAP rules."""
    return {
        "git_hash": _sh("git", "rev-parse", "HEAD"),
        "git_dirty": bool(_sh("git", "status", "--porcelain")),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "script": "cert/build_calib_set.py",
        "argv": list(argv),
        "constants": {
            "w_loss": W_LOSS,
            "t_delay_ms": T_DELAY,
            "t_loss": T_LOSS,
            "tau_core_s": TAU_CORE_MEASURED_S,
            "b_block_s": B_BLOCK_S,
            "warmup_frac": WARMUP,
            "t0_s": T0_S,
            "sigma_rho": SIGMA_RHO,
            "age_edges": list(AGE_EDGES),
            "measured_age_edges": list(MEASURED_AGE_EDGES),
            "u_edges": ["inf" if not np.isfinite(x) else x for x in U_EDGES],
        },
    }


def _bin_with_edge_warnings(values: np.ndarray, edges: Sequence[float]) -> tuple[np.ndarray, dict]:
    """Digitize values and clip out-of-edge values with explicit diagnostics.

    The offered-load trace has 10 ms samples and should not need clipping. The
    measured trace has coarser telemetry and can alias AoI to 0.0 s or 0.6 s;
    those rows are clipped for a robustness table, with warnings recorded.
    """
    raw = np.digitize(values, edges) - 1
    n_bins = len(edges) - 1
    low = raw < 0
    high = raw >= n_bins
    clipped = np.clip(raw, 0, n_bins - 1)
    # DEM SO HANG MOI BIN. Mot bin rong (hoac gan rong) khong lam conformal
    # SAI -- no lam q_hat = inf va coverage = 1.0 (cert/conformal_age.py),
    # tuc chung chi VO DUNG ma bao cao HOAN HAO. Khong dem thi khong thay.
    counts = np.bincount(clipped, minlength=n_bins).tolist()
    return clipped.astype(np.int8), {
        "n_bins": int(n_bins),
        "n_per_bin": [int(x) for x in counts],
        "n_min_bin": int(min(counts)) if counts else 0,
        "empty_bins": [i for i, x in enumerate(counts) if int(x) == 0],
        "n_low": int(low.sum()),
        "n_high": int(high.sum()),
        "min_value": float(np.min(values)) if len(values) else None,
        "max_value": float(np.max(values)) if len(values) else None,
        "n_unique_values": int(len(np.unique(values))),
    }


def build_one(rho: np.ndarray, dt_s: float, trace_id: int,
              tau_load: float | None = None) -> tuple[pd.DataFrame, dict]:
    """Convert one warmed-up rho trace into calibration rows.

    ``tau_load`` la THOI GIAN TUONG QUAN cua qua trinh SINH RA trace. Khi
    duoc truyen, ham them nhanh thu ba ``u_cond_load`` hieu chinh bang
    CHINH no thay vi bang ``TAU_CORE_MEASURED_S``. Truyen TUONG MINH qua
    tham so, KHONG qua mot bien module bi CLI ghi de: repo nay da co nam
    tool ghi de global luc import va lam hong thu tu test
    (tools/g3_dryrun.py DT_S) -- khong them mot cai nua.
    """
    n = int(len(rho))
    delay, loss, cost = build_cost_tables(rho, W_LOSS)
    viol = _viol_flags(delay, loss, T_DELAY, T_LOSS)
    opt_all, _tie = decide(cost)

    age = sawtooth_age_steps(n, dt_s)
    t0 = max(t0_steps(dt_s), int(age.max()))
    if t0 >= n:
        raise ValueError("trace is too short after warm-up and common-window cut")
    all_rows = np.arange(t0, n)
    local_block_all = all_rows // block_len_samples(dt_s)
    block_counts_all = np.bincount(local_block_all)
    physical_block_full_all = block_counts_all[local_block_all] == block_len_samples(dt_s)

    z_zero = age[all_rows] == 0
    if z_zero.any():
        print(
            "  [CANH BAO] %d hang co z=0 (twin = su that); loai khoi tap calib"
            % int(z_zero.sum())
        )
    rows = all_rows[~z_zero]
    physical_block_full = physical_block_full_all[~z_zero]
    src = rows - age[rows]
    if (src < 0).any():
        raise ValueError("computed negative source indices")
    if not (src != rows).any():
        print("  [CANH BAO] src == rows for all rows; AoI collapsed to zero")

    y = cost[rows]
    yhat = cost[src]
    e = y - yhat

    a1 = np.argmin(yhat, axis=1)
    e_a1 = e[np.arange(len(rows)), a1]
    s_maxabs = np.abs(e).max(axis=1)
    s_range = e.max(axis=1) - e.min(axis=1)
    s_vs_a1 = np.abs(e - e_a1[:, None]).max(axis=1)

    a_twin = opt_all[src]
    a_opt = opt_all[rows]
    regret = cost[rows, a_twin] - cost[rows, a_opt]
    wrong = (a_twin != a_opt) & (regret > EPS_REG)

    yhat_sorted = np.sort(yhat, axis=1)
    y_sorted = np.sort(y, axis=1)
    gap_twin = yhat_sorted[:, 1] - yhat_sorted[:, 0]
    gap_true = y_sorted[:, 1] - y_sorted[:, 0]

    z_s = age[rows] * float(dt_s)
    sig_z = SIGMA_RHO * np.sqrt(1.0 - np.exp(-2.0 * z_s / TAU_CORE_MEASURED_S))
    dist = np.min(
        np.abs(rho[src][:, :, None] - np.asarray(JUMPS, dtype=float)[None, None, :]),
        axis=2,
    )
    dist_min = dist.min(axis=1)
    u = dist_min / sig_z

    # --- NHANH NHAY CAM u_cond (prereg T2, QD-1) -------------------------
    # `u` o tren dung TU SO KHONG DIEU KIEN voi MAU SO CO DIEU KIEN: no do
    # khoang cach tu rho(t_src) den nguong, nhung chia cho do phan tan cua
    # rho(t_src + z). Phan bi bo qua la HOI QUY VE TRUNG BINH:
    #
    #     E[rho(t+z) | rho(t)] = mu + phi_z * (rho(t) - mu),  phi_z = exp(-z/tau)
    #
    # Do lon phan bo qua = (1 - phi_z) * |rho - mu|:
    #     z/tau=0.05 -> 4.9% | 0.19 -> 17% | 1.00 -> 63% | 2.50 -> 92%
    #
    # !! PHAM VI THAT CUA DUONG NAY, DO DUOC -- dung doc nham bang tren:
    #    z o day KHONG den tu mot luoi ma tu sawtooth_age_steps(), tuc CHU KY
    #    DONG BO (DEFAULT_SYNC_PERIOD_S = 0.5 s), va mau so dung TAU_CORE
    #    = 2.87 CO DINH. Ca hai deu KHONG phu thuoc tau_load. Nen quet truc
    #    tau cua T2 KHONG lam doi phi_z o day chut nao. Do duoc tren calib
    #    p0925_tau10 (5 seed):
    #        z_s in [0.055, 0.550] s  =>  z/tau_core in [0.019, 0.192]
    #        phi_z in [0.826, 0.981]  =>  phan bo qua in [1.9%, 17.4%]
    #    Hai hang 63% va 92% cua bang tren la z/tau_LOAD trong nhanh B cua
    #    measurements/decision_error_v2.py -- mot duong code KHAC, khong tinh
    #    `u` bao gio. KHONG voi toi duoc tu day.
    #
    # KHONG thay `u`: Mondrian conformal HOP LE voi moi taxonomy do duoc va
    # co dinh TRUOC hieu chuan, nen `u` cu KHONG mat bao dam bao phu -- no
    # chi KEM HIEU QUA. Doi `u` se XOA doi chung hoi quy Phase 21 va tron
    # hai thay doi (tau + dinh nghia u) vao mot phep so.
    # => Chay SONG SONG, bao cao HIEU. Chenh lech la DU LIEU, khong phai loi.
    #
    # tau dung o day la TAU_CORE_MEASURED_S, GIONG HET nhanh chinh: u_cond
    # sua MOI QUAN HE tu so/mau so, KHONG dung den truc tau cua T2 (F1).
    mu_link = rho.mean(axis=0)                              # (n_links,)
    phi_z = np.exp(-z_s / TAU_CORE_MEASURED_S)              # (n_rows,)
    rho_pred = mu_link[None, :] + phi_z[:, None] * (rho[src] - mu_link[None, :])
    dist_cond = np.min(
        np.abs(rho_pred[:, :, None] - np.asarray(JUMPS, dtype=float)[None, None, :]),
        axis=2,
    ).min(axis=1)
    u_cond = dist_cond / sig_z

    age_edges = age_edges_for_dt(dt_s)
    z_bin, z_diag = _bin_with_edge_warnings(z_s, age_edges)
    u_bin, u_diag = _bin_with_edge_warnings(u, U_EDGES)
    # CUNG U_EDGES: bien phan bin phai co dinh TRUOC khi nhin du lieu. Neu
    # phan bo u_cond lech khoi U_EDGES thi DO CHINH LA phat hien, khong phai
    # ly do de chinh bien cho vua.
    u_cond_bin, u_cond_diag = _bin_with_edge_warnings(u_cond, U_EDGES)

    # --- NHANH THU BA u_cond_load: hieu chinh bang tau cua CHINH tai -----
    # `u_cond` o tren hieu chinh bang tau_core = 2.87 -- tau DO DUOC cua
    # link `ac` tren trace Mininet v7. Voi mot trace sinh o tau_load KHAC,
    # do la SAI DAC TA, va sai ve CA HAI phia:
    #     tu so : co ve trung binh QUA TAY  (z=0.55, tau_load=10: 3.26 lan)
    #     mau so: sigma_z QUA LON           (cung diem: 1.75 lan)
    # Nen mot `u_cond` te hon `u` chua chac chung minh "hieu chinh khong
    # giup"; no co the chi dang do sai so cua tau.
    #
    # !! u_cond_load la mot ORACLE: no dung tau THIET KE, thu ma mot he
    #    trien khai that KHONG BIET. Ban dung duoc phai uoc luong tau_hat
    #    tu chinh trace (estimand da ky o QD-4 cua prereg T2). Ghi ro de no
    #    khong troi vao paper nhu mot phuong phap dung duoc.
    #
    # !! CANH BAO SO SANH: sigma_z cua nhanh nay NHO hon nhanh u_cond dung
    #    ty le sqrt((1-e^(-2z/tau_core))/(1-e^(-2z/tau_load))), nen u_cond_load
    #    bi THOI TO tuong ung. Duoi U_EDGES CO DINH, so sanh ba nhanh vi the
    #    bi tron voi mot phep doi THANG DO. Chi cach chia bin theo HANG
    #    (phan vi) moi tach duoc chat luong THU TU khoi thang do -- va do la
    #    CHAN DOAN, khong phai taxonomy de xuat.
    if tau_load is not None:
        tau_num = float(tau_load)
        phi_z_load = np.exp(-z_s / tau_num)
        rho_pred_load = (mu_link[None, :]
                         + phi_z_load[:, None] * (rho[src] - mu_link[None, :]))
        sig_z_load = SIGMA_RHO * np.sqrt(1.0 - np.exp(-2.0 * z_s / tau_num))
        dist_cond_load = np.min(
            np.abs(rho_pred_load[:, :, None]
                   - np.asarray(JUMPS, dtype=float)[None, None, :]),
            axis=2,
        ).min(axis=1)
        u_cond_load = dist_cond_load / sig_z_load
        u_cond_load_bin, u_cond_load_diag = _bin_with_edge_warnings(
            u_cond_load, U_EDGES)
    else:
        tau_num = None
        u_cond_load = u_cond_load_bin = u_cond_load_diag = None
        phi_z_load = None
    if z_diag["n_unique_values"] < len(age_edges) - 1:
        print(
            "  [CANH BAO] chi %d muc tuoi khac nhau (dt=%.6gs) - co the bi aliasing"
            % (z_diag["n_unique_values"], float(dt_s))
        )
    if z_diag["n_low"] or z_diag["n_high"]:
        print(
            "  [CANH BAO] %d tuoi duoi bin va %d tuoi tren bin da duoc clip"
            % (z_diag["n_low"], z_diag["n_high"])
        )

    local_block = rows // block_len_samples(dt_s)

    data = {
        "trace_id": np.full(len(rows), int(trace_id), dtype=np.int8),
        "block_id": (int(trace_id) * 100_000 + local_block).astype(np.int32),
        "block_full": physical_block_full,
        "t_idx": rows.astype(np.int32),
        "z_s": z_s.astype(np.float32),
        "z_bin": z_bin,
        "dist_min": dist_min.astype(np.float32),
        "u": u.astype(np.float32),
        "u_bin": u_bin,
        "u_cond": u_cond.astype(np.float32),
        "u_cond_bin": u_cond_bin,
        "phi_z": phi_z.astype(np.float32),
        "s_maxabs": s_maxabs.astype(np.float32),
        "s_range": s_range.astype(np.float32),
        "s_vs_a1": s_vs_a1.astype(np.float32),
        "a_twin": a_twin.astype(np.int8),
        "a_opt": a_opt.astype(np.int8),
        "gap_twin": gap_twin.astype(np.float32),
        "gap_true": gap_true.astype(np.float32),
        "regret": regret.astype(np.float32),
        "wrong": wrong,
        "viol_twin": viol[rows, a_twin],
        "viol_opt": viol[rows, a_opt],
    }
    if u_cond_load is not None:
        data["u_cond_load"] = u_cond_load.astype(np.float32)
        data["u_cond_load_bin"] = u_cond_load_bin
        data["phi_z_load"] = phi_z_load.astype(np.float32)

    for action in range(K):
        data[f"y_true_{action}"] = y[:, action].astype(np.float32)
        data[f"y_hat_{action}"] = yhat[:, action].astype(np.float32)

    diagnostics = {
        "trace_id": int(trace_id),
        "n_after_warmup": n,
        "dt_s": float(dt_s),
        "t0": int(t0),
        "block_len_samples": int(block_len_samples(dt_s)),
        "block_len_s": float(block_len_samples(dt_s) * float(dt_s)),
        "n_z_zero_excluded": int(z_zero.sum()),
        "n_rows": int(len(rows)),
        "age_edges": list(age_edges),
        "z_bin_diag": z_diag,
        "u_bin_diag": u_diag,
        "u_cond_bin_diag": u_cond_diag,
        "u_cond_tau_s": float(TAU_CORE_MEASURED_S),
        # Hai con so quan trong nhat cua nhanh nay: chung tra loi truc tiep
        # "bo qua hoi quy ve trung binh co THUC SU doi cach chia bin khong".
        # ~0 => hai dinh nghia tuong duong thuc dung (QD-1 duoc xac nhan
        # bang so); lon => co tac dong that, phai bao cao. CA HAI deu la
        # ket qua tot: khong outcome nao lam phep do that bai.
        "mean_abs_u_minus_u_cond": float(np.mean(np.abs(u - u_cond))),
        "frac_rows_bin_differs": float(np.mean(u_bin != u_cond_bin)),
        "tau_core_s": float(TAU_CORE_MEASURED_S),
        "tau_load_used": tau_num,
    }
    if u_cond_load is not None:
        zmax = float(z_s.max())
        diagnostics.update({
            "u_cond_load_bin_diag": u_cond_load_diag,
            # co QUA TAY: ty le phan co cua tau_core so voi tau_load tai z_max
            "phi_z_overshrink_ratio_at_zmax": float(
                (1.0 - np.exp(-zmax / TAU_CORE_MEASURED_S))
                / (1.0 - np.exp(-zmax / tau_num))),
            # THANG DO: u_cond_load bi thoi to dung ty le nay so voi u_cond
            "sigma_z_ratio_core_over_load_at_zmax": float(
                np.sqrt((1.0 - np.exp(-2.0 * zmax / TAU_CORE_MEASURED_S))
                        / (1.0 - np.exp(-2.0 * zmax / tau_num)))),
            "frac_rows_bin_differs_load_vs_u": float(
                np.mean(u_bin != u_cond_load_bin)),
            "oracle_warning": (
                "u_cond_load dung tau THIET KE cua trace tong hop -- mot he "
                "trien khai that KHONG biet so nay. Ban dung duoc phai uoc "
                "luong tau_hat (estimand da ky o QD-4). Day la CAN TREN cua "
                "hieu chinh, khong phai mot phuong phap."),
        })
    return pd.DataFrame(data), diagnostics


def build(trace_paths: Sequence[str], out_path: str, dt_s: float | None = None,
          tau_load: float | None = None) -> tuple[pd.DataFrame, list[dict]]:
    frames = []
    diagnostics = []
    for trace_id, path in enumerate(trace_paths):
        rho, dt = read_trace_matrix(path, dt_s)
        rho = drop_warmup_matrix(rho, WARMUP)
        print(f"[{trace_id}] {os.path.basename(path)}  n={len(rho)}  dt={dt:.6g}s")
        frame, diag = build_one(rho, dt, trace_id, tau_load=tau_load)
        frames.append(frame)
        diagnostics.append(diag)
    df = pd.concat(frames, ignore_index=True)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    df.to_parquet(out_path, index=False)
    return df, diagnostics


def self_check(df: pd.DataFrame) -> list[str]:
    """Return invariant failures. Violations are bugs, not scientific results."""
    failures = []
    if (df.s_maxabs < 0).any():
        failures.append("s_maxabs am")
    if not (df.s_range <= 2.0 * df.s_maxabs + 1e-3).all():
        failures.append("s_range > 2*s_maxabs -> sai truc hoac lech dau")
    if not (df.s_vs_a1 <= df.s_range + 1e-3).all():
        failures.append("s_vs_a1 > s_range -> a1 tinh sai")
    if not (df.regret >= -1e-6).all():
        failures.append("regret am -> a_opt khong phai argmin")
    if not (df.loc[~df.wrong, "regret"].abs() < 1e-6).all():
        failures.append("regret != 0 khi khong sai -> lech chi so hoac tie threshold")
    if not (df.gap_twin >= -1e-6).all():
        failures.append("gap_twin am -> sap xep sai")
    if df.groupby("trace_id")["block_id"].nunique().sum() != df.block_id.nunique():
        failures.append("block_id khong duy nhat toan cuc -> ro ri calib/test")
    if (df.z_bin < 0).any() or (df.z_bin > len(AGE_EDGES) - 2).any():
        failures.append("z_bin ngoai mien hop le")
    if (df.u_bin < 0).any() or (df.u_bin > len(U_EDGES) - 2).any():
        failures.append("u_bin ngoai mien hop le")
    if (df.groupby("z_bin")["s_vs_a1"].max() == 0).any():
        failures.append("mot bin co toan bo score = 0 -> nghi tron z=0 vao calib")
    u_finite = df.loc[df.u.notna(), "u"]
    if not np.isfinite(u_finite).all():
        failures.append("u co gia tri vo han -> sig_z = 0 (z=0?)")
    if len(u_finite) and float(u_finite.max()) > 1e3:
        failures.append("u_max = %.2e qua lon -> nghi chia cho gan 0" % float(u_finite.max()))
    if "u_cond" in df.columns:
        uc = df.loc[df.u_cond.notna(), "u_cond"]
        if not np.isfinite(uc).all():
            failures.append("u_cond co gia tri vo han -> sig_z = 0 (z=0?)")
        if (df.u_cond_bin < 0).any() or (df.u_cond_bin > len(U_EDGES) - 2).any():
            failures.append("u_cond_bin ngoai mien hop le")
        # BIEN THAI: phi_z -> 1 thi mu + 1*(rho-mu) = rho, nen u_cond -> u.
        # Bat sai DAU trong (rho - mu) va sai TRUC khi lay trung binh -- loai
        # loi ma mot test gia tri hardcode khong bat duoc.
        near = df.phi_z > 0.99
        if near.any():
            d = float((df.loc[near, "u"] - df.loc[near, "u_cond"]).abs().max())
            if d > 0.5:
                failures.append(
                    "u_cond lech u qua nhieu (%.3f) o phi_z>0.99 -> nghi sai dau "
                    "trong (rho - mu) hoac mu tinh tren truc sai" % d)
    return failures


def qhat_preview(scores: Iterable[float], alpha: float, n_eff: int) -> float:
    """Preview conformal quantile using block count as effective n."""
    k = int(np.ceil((int(n_eff) + 1) * (1.0 - float(alpha))))
    if k > int(n_eff):
        return float("inf")
    return float(np.quantile(np.asarray(list(scores), dtype=float), k / int(n_eff), method="higher"))


def _percentiles(values: np.ndarray, qs: Sequence[int]) -> dict:
    return {f"p{q}": float(np.percentile(values, q)) for q in qs}


def report(
    df: pd.DataFrame,
    *,
    alpha: float = 0.10,
    out_json: str | None = None,
    argv: Sequence[str] = (),
    trace_diagnostics: Sequence[dict] = (),
) -> dict:
    result = {
        "provenance": provenance(argv),
        "trace_diagnostics": list(trace_diagnostics),
    }
    full = df[df.block_full]

    print("\n" + "=" * 74)
    print(
        f"BANG: {len(df):,} hang | {df.block_id.nunique()} block "
        f"({full.block_id.nunique()} block DAY) | {df.trace_id.nunique()} trace"
    )

    print("\n=== SELF-CHECK CAU TRUC ===")
    failures = self_check(df)
    print("  " + ("TAT CA PASS" if not failures else "FAIL: " + "; ".join(failures)))
    result["self_check"] = failures

    print("\n=== V5 KIEM CHUNG NOI TAI - PHAI KHOP PHASE 20 ===")
    err = float(df.wrong.mean())
    d_sla = float(df.viol_twin.mean() - df.viol_opt.mean())
    regret_on_error = float(df.loc[df.wrong, "regret"].mean()) if df.wrong.any() else 0.0
    mean_regret = float(df.regret.mean())
    print(f"  err        = {err:.5f}      Phase 20 (n=5) = 0.18233")
    print(f"  d_sla      = {d_sla:.5f}      Phase 20 (n=5) = 0.07939")
    print(f"  regret|err = {regret_on_error:.3f} ms   Phase 20 trace0 = 33.67")
    print(
        f"  IC1: err x regret|err = {err * regret_on_error:.5f}"
        f"  vs  mean regret = {mean_regret:.5f}"
        f"   (lech {abs(err * regret_on_error - mean_regret):.2e})"
    )
    result["internal_check"] = {
        "err": err,
        "d_sla": d_sla,
        "regret_on_error_ms": regret_on_error,
        "mean_regret_ms": mean_regret,
        "err_abs_diff_from_phase20": abs(err - 0.18233),
        "d_sla_abs_diff_from_phase20": abs(d_sla - 0.07939),
    }

    print("\n=== V4 SO BLOCK MOI O MONDRIAN (z_bin x u_bin) - rang buoc >= 9 ===")
    ct = full.groupby(["z_bin", "u_bin"])["block_id"].nunique().unstack(fill_value=0)
    print(ct.to_string())
    counts = full.groupby(["z_bin", "u_bin"])["block_id"].nunique()
    bad = {f"{z}_{u}": int(v) for (z, u), v in counts.items() if v < 9}
    print("  O VI PHAM (<9 block):", bad if bad else "khong co")
    result["blocks_per_cell"] = {f"{z}_{u}": int(v) for (z, u), v in counts.items()}
    result["sparse_cells_lt_9_blocks"] = bad

    print("\n=== PHAN PHOI GAP COST - THANG DOI CHIEU CUA q_hat ===")
    result["gap"] = {}
    for name in ("gap_twin", "gap_true"):
        values = full[name].to_numpy()
        result["gap"][name] = _percentiles(values, (10, 25, 50, 75, 90, 99))
        print(
            f"  {name}: "
            + "  ".join(f"p{q}={np.percentile(values, q):8.3f}" for q in (10, 25, 50, 75, 90, 99))
        )
    print("  ^ P7: gate ACCEPT khi gap_twin >= q_hat - eps.")

    print(f"\n=== q_hat XEM TRUOC theo z_bin (alpha={alpha}, n_eff = SO BLOCK) ===")
    print(
        f"{'z_bin':>6} {'n_blk':>6} {'2q(s_maxabs,a/K)':>18} "
        f"{'q(s_range,a)':>14} {'q(s_vs_a1,a)':>14} "
        f"{'triet tieu':>11} {'gap_twin p50':>13}"
    )
    result["qhat_preview"] = {}
    for z_bin, sub in full.groupby("z_bin"):
        n_eff = int(sub.block_id.nunique())
        q_bonf = 2.0 * qhat_preview(sub.s_maxabs, alpha / K, n_eff)
        q_range = qhat_preview(sub.s_range, alpha, n_eff)
        q_vs_a1 = qhat_preview(sub.s_vs_a1, alpha, n_eff)
        ratio = q_bonf / q_vs_a1 if q_vs_a1 > 0 else float("inf")
        result["qhat_preview"][int(z_bin)] = {
            "n_blocks": n_eff,
            "two_q_bonf": q_bonf,
            "q_range": q_range,
            "q_vs_a1": q_vs_a1,
            "gap_twin_p50": float(sub.gap_twin.median()),
            "tightening_ratio": ratio,
        }
        print(
            f"{int(z_bin):>6} {n_eff:>6} {q_bonf:>18.3f} {q_range:>14.3f} "
            f"{q_vs_a1:>14.3f} {ratio:>11.2f}x {sub.gap_twin.median():>13.3f}"
        )

    print("\n=== PHAN PHOI s_vs_a1 THEO BIN ===")
    result["s_vs_a1_percentiles"] = {}
    for z_bin, sub in full.groupby("z_bin"):
        values = sub.s_vs_a1.to_numpy()
        med = max(float(np.median(values)), 1e-9)
        p75 = float(np.percentile(values, 75))
        p90 = float(np.percentile(values, 90))
        p99 = float(np.percentile(values, 99))
        result["s_vs_a1_percentiles"][int(z_bin)] = {
            "p50": med,
            "p75": p75,
            "p90": p90,
            "p99": p99,
            "p90_over_p50": p90 / med,
        }
        print(
            f"  z_bin {int(z_bin)}: p50={med:8.4f} p75={p75:8.3f} "
            f"p90={p90:8.3f} p99={p99:9.3f}  p90/p50={p90 / med:7.1f}x"
        )

    if out_json:
        os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True, default=str)
            f.write("\n")
        print(f"\n[ghi] {out_json}")
    return result


def main(argv: Sequence[str] | None = None) -> None:
    argv = sys.argv if argv is None else list(argv)
    parser = argparse.ArgumentParser(description="Build Phase 21 conformal calibration set")
    parser.add_argument("--traces", nargs="+", required=True, help="rho CSV trace files")
    parser.add_argument("--out", required=True, help="output parquet path")
    parser.add_argument("--report-json", default=None, help="optional JSON report path")
    parser.add_argument("--dt", type=float, default=None, help="dt_s if CSV has no dt_s column")
    parser.add_argument("--alpha", type=float, default=0.10)
    parser.add_argument("--tau-load", type=float, default=None,
                        help="THOI GIAN TUONG QUAN cua qua trinh sinh ra trace, "
                             "GIAY. Khi co, them nhanh thu ba u_cond_load hieu "
                             "chinh bang chinh no thay vi tau_core=2.87. "
                             "ORACLE: he that khong biet so nay.")
    args = parser.parse_args(argv[1:])

    df, diagnostics = build(args.traces, args.out, args.dt, tau_load=args.tau_load)
    report(
        df,
        alpha=args.alpha,
        out_json=args.report_json,
        argv=argv,
        trace_diagnostics=diagnostics,
    )
    print(f"\n[ghi] {args.out}  ({os.path.getsize(args.out) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
