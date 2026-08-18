#!/usr/bin/env python3
"""Phase 23 / Lesson 23.5[C] -- dai tin cay DONG THOI cho GO-2.

Thu tuc khoa tai: docs/phase-23/00y-amendment-24.md  (C-D1..C-D6)

VAN DE
------
GO-2 phat bieu "thu tu FWER phu thuoc slot" tu 24 khoang tin cay doc DONG THOI
(4 bin x 2 thu tuc x 3 slot). Duong ong Phase 22 co ba khiem khuyet cho phat
bieu do:

  (1) picks rut RIENG theo bin, trong khi MOI block trai qua ca 4 bin
      -> hop le cho CI tung o, SAI cho phat bieu dong thoi
  (2) B = 200 -> n_contains_zero dao dong 4..8 tren 10 seed
  (3) 24 khoang moi cai 95% -> ky vong 1.2 khoang loai tru 0 MOT CACH SAI.
      Bai bao ve hieu chinh da so sanh ma phan tich cua no chua hieu chinh
      da so sanh.

GIAI PHAP -- dai sup-t (simultaneous / max-t band)
--------------------------------------------------
    T^(b) = max_k |delta_k^(b) - delta_hat_k| / sigma_hat_k
    c     = quantile_{0.95}(T)
    dai   = delta_hat_k +/- c * sigma_hat_k     => P(ca 24 dung) >= 0.95

Chu y cau truc cua T: no CHINH LA  max_j s_j/sigma_j  cua Lesson 23.5[A],
chi khac tang -- [A] ap len 3 rank slot, [C] ap len 24 dai luong suy luan.
Va vi the [C] do duoc TRUC TIEP luan diem cua Phase 22: c_supt < c_bonferroni
dung bang muc ma 24 dai luong tuong quan voi nhau.

Tham khao: Montiel Olea & Plagborg-Moller (2019), "Simultaneous confidence
bands: theory, implementation, and an application to SVARs".
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

# Dung LAI helper cua Phase 22 de ngu nghia qhat GIONG HET duong ong cu.
from cert.conformal_simultaneous import _slot_cols, alpha_each
from cert.simultaneous_score import ALPHA, conformal_level, empirical_qhat


# ---------------------------------------------------------------------------
# 0. Hang so khoa
# ---------------------------------------------------------------------------

BASELINE = "maxscore"
PROCS = ("bonferroni", "sidak")
N_BOOT = 2000                       # C-D3
SEED_GO2 = 24001
FWER = 0.05
Z_TWO_SIDED_95 = 1.959964185778     # z_{0.975}
SIGMA_FLOOR = 1e-12
VARIANTS = ("A", "B", "C")

# Bang chung bat on dinh o B = 200  (C-D5) -- dung dung 10 seed da chay
SEEDS_INSTABILITY = tuple(range(7204, 7204 + 10 * 17, 17))
B_SMALL = 200

# Kiem hoi tu MC -- TIEU CHI DA SUA (Amendment 23-23)
MC_SEEDS = 30
MC_B_LO, MC_B_HI = 200, 2000
MC_WIDTH_TOL = 0.10                 # do rong dai phai ON DINH, khong co ve 0
MC_SHRINK_MIN = 1.8                 # sai so MC phai co it nhat 1.8x (ly thuyet 3.16x)


def _z(p: float) -> float:
    """Phan vi chuan tac; dung de tinh hang so Bonferroni/Sidak."""
    lo, hi = -12.0, 12.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if 0.5 * (1.0 + math.erf(mid / math.sqrt(2.0))) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def critical_values(k: int, fwer: float = FWER) -> Dict[str, float]:
    """Hang so co dien de doi chieu voi c_supt. Tat dinh, KHONG phai du doan.

    O k = 24 va FWER = 0.05, Bonferroni va Sidak chi cach nhau 0.0073 (0.24%).
    Vi vay MOI khoang cach dang ke giua c_supt va 3.078 la do TUONG QUAN, khong
    phai do chon Bonferroni hay Sidak.
    """
    bonf = _z(1.0 - fwer / (2.0 * int(k)))
    sid = _z(0.5 * (1.0 + (1.0 - fwer) ** (1.0 / int(k))))
    return {"k": int(k), "c_bonferroni": float(bonf), "c_sidak": float(sid),
            "c_pointwise_95": float(Z_TWO_SIDED_95),
            "bonferroni_minus_sidak": float(bonf - sid)}


def _git(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# 1. Cau truc block TOAN CUC  (C-D1)
# ---------------------------------------------------------------------------

def build_global_blocks(
    calib: pd.DataFrame,
    slots: Sequence[str],
    bin_col: str = "z_bin",
) -> Dict[str, Any]:
    """Mot chi so block DUY NHAT dung chung cho MOI bin.

    C-D1: picks rut MOT LAN, ap cho ca 4 bin. Rut rieng theo bin la SAI cho
    phat bieu dong thoi vi moi block trai qua ca 4 bin -- cung ly do vi sao
    Lesson 23.5[A] phai chia fold TOAN CUC (bac tu do D2).

    Moi o (bin, block) luu MOT ma tran (n_rows, m+1):
        cot 0..m-1 = s_pair_1..m ,  cot m = s_sim
    Giu chung trong CUNG mot ma tran de variant A doc duoc CA HANG (C-D6).
    """
    blocks = np.sort(pd.unique(calib["block_id"].to_numpy()))
    index = {int(b): i for i, b in enumerate(blocks.tolist())}
    cols = list(slots) + ["s_sim"]
    m = len(slots)

    by_bin: Dict[int, List[Optional[np.ndarray]]] = {}
    for g, sub in calib.groupby(bin_col, sort=True):
        cells: List[Optional[np.ndarray]] = [None] * len(blocks)
        for bid, bg in sub.groupby("block_id", sort=True):
            cells[index[int(bid)]] = bg[cols].to_numpy(np.float64)
        empty = [i for i, c in enumerate(cells) if c is None or c.shape[0] == 0]
        if empty:
            raise ValueError(
                "bin %s thieu %d block (vd. block_id=%s). Draw toan cuc doi hoi "
                "moi block xuat hien o moi bin; neu khong, n_eff theo bin khac "
                "nhau giua cac draw va dai dong thoi khong con dung."
                % (g, len(empty), blocks[empty[0]])
            )
        by_bin[int(g)] = cells

    return {"blocks": blocks, "n_blocks": int(len(blocks)),
            "by_bin": by_bin, "m": int(m), "cols": cols}


# ---------------------------------------------------------------------------
# 2. qhat cho MOT draw
# ---------------------------------------------------------------------------

def _reduce_cell(
    mat: np.ndarray, variant: str, row_pick: Optional[int]
) -> np.ndarray:
    """Rut gon MOT o (bin, block) thanh (k, m+1) theo variant.

    A: MOT hang duy nhat, doc TAT CA cac cot tu dung hang do  (C-D6)
       -> giu rang buoc s_sim = max_j s_pair_j trong hang
       -> va lam ghep cap giua cac thu tuc thanh TAT DINH
    B: tat ca cac hang
    C: cuc dai theo TUNG COT (giu nguyen ngu nghia Phase 22; cac cot co the
       den tu hang khac nhau -- do la dinh nghia cua variant C, khong phai loi)
    """
    if variant == "B":
        return mat
    if variant == "C":
        return mat.max(axis=0, keepdims=True)
    if variant == "A":
        return mat[int(row_pick) % mat.shape[0]][None, :]
    raise ValueError("variant phai la 'A', 'B' hoac 'C'")


def _stack_cells(
    cells: Sequence[np.ndarray],
    picks: np.ndarray,
    variant: str,
    row_picks: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Gop cac o duoc chon thanh MOT ma tran (n, m+1).

    Tach rieng khoi qvec de `deltas_for_draw` gop MOT LAN moi bin roi dung lai
    cho ca ba thu tuc, thay vi gop ba lan. Ket qua giong het, chi nhanh hon 3x.
    """
    parts = [
        _reduce_cell(cells[int(i)], variant,
                     None if row_picks is None else int(row_picks[t]))
        for t, i in enumerate(picks)
    ]
    return np.concatenate(parts, axis=0)


def _qvec_from_stacked(
    stacked: np.ndarray, n_eff: int, procedure: str, alpha: float, m: int
) -> np.ndarray:
    level = conformal_level(int(n_eff), alpha_each(procedure, alpha, m))
    if level is None:
        return np.full(m, float("inf"), dtype=np.float64)
    if procedure == BASELINE:
        q = empirical_qhat(stacked[:, m], level)          # cot s_sim
        return np.full(m, float(q), dtype=np.float64)
    return np.asarray(
        [empirical_qhat(stacked[:, j], level) for j in range(m)], np.float64
    )


def qvec_for_draw(
    cells: Sequence[np.ndarray],
    picks: np.ndarray,
    procedure: str,
    alpha: float,
    m: int,
    variant: str,
    row_picks: Optional[np.ndarray] = None,
) -> np.ndarray:
    """qhat (m,) cho MOT bin, MOT draw, MOT thu tuc.

    row_picks duoc TRUYEN VAO chu khong rut ben trong: do la thu lam ghep cap
    tat dinh. Loi cua Phase 22 la truyen mot rng dung chung roi de moi thu tuc
    TIEU THU no mot so lan khac nhau (maxscore 1 lan, bonferroni 3 lan).
    """
    stacked = _stack_cells(cells, picks, variant, row_picks)
    return _qvec_from_stacked(stacked, len(picks), procedure, alpha, m)


def deltas_for_draw(
    struct: Mapping[str, Any],
    picks: np.ndarray,
    alpha: float = ALPHA,
    variant: str = "B",
    procs: Sequence[str] = PROCS,
    baseline: str = BASELINE,
    row_picks_by_bin: Optional[Mapping[int, np.ndarray]] = None,
) -> np.ndarray:
    """Vector K = n_bin * n_proc * m delta cho MOT draw. Thu tu co dinh."""
    m = int(struct["m"])
    n_eff = int(len(picks))
    out: List[float] = []
    for g in sorted(struct["by_bin"]):
        cells = struct["by_bin"][g]
        rp = None if row_picks_by_bin is None else row_picks_by_bin[g]
        stacked = _stack_cells(cells, picks, variant, rp)   # gop MOT lan
        base = _qvec_from_stacked(stacked, n_eff, baseline, alpha, m)
        for p in procs:
            q = _qvec_from_stacked(stacked, n_eff, p, alpha, m)
            out.extend((q - base).tolist())
    return np.asarray(out, dtype=np.float64)


def label_index(struct: Mapping[str, Any],
                procs: Sequence[str] = PROCS) -> List[Dict[str, Any]]:
    """Nhan cho tung phan tu cua vector K, dung THU TU voi deltas_for_draw."""
    m = int(struct["m"])
    return [{"z_bin": int(g), "procedure": str(p), "slot": int(j + 1)}
            for g in sorted(struct["by_bin"]) for p in procs for j in range(m)]


# ---------------------------------------------------------------------------
# 3. Bootstrap + dai sup-t
# ---------------------------------------------------------------------------

def bootstrap_deltas(
    struct: Mapping[str, Any],
    n_boot: int = N_BOOT,
    seed: int = SEED_GO2,
    alpha: float = ALPHA,
    variant: str = "B",
    procs: Sequence[str] = PROCS,
    baseline: str = BASELINE,
) -> Dict[str, Any]:
    """Paired block bootstrap, draw TOAN CUC dung chung cho moi bin (C-D1)."""
    nb = int(struct["n_blocks"])
    rng = np.random.default_rng(int(seed))
    draws = []
    for _ in range(int(n_boot)):
        picks = rng.integers(0, nb, size=nb)         # MOT picks cho CA 4 bin
        row_picks = None
        if variant == "A":                            # C-D6: cho MOI draw, mot
            row_picks = {                             # chi so hang moi block-instance,
                g: rng.integers(0, 1 << 30, size=nb)  # dung chung cho MOI thu tuc
                for g in sorted(struct["by_bin"])
            }
        draws.append(deltas_for_draw(struct, picks, alpha, variant, procs,
                                     baseline, row_picks))
    arr = np.vstack(draws)

    point_picks = np.arange(nb)
    point_rows = (None if variant != "A"
                  else {g: np.zeros(nb, dtype=np.int64)
                        for g in sorted(struct["by_bin"])})
    point = deltas_for_draw(struct, point_picks, alpha, variant, procs,
                            baseline, point_rows)
    return {"draws": arr, "point": point, "n_boot": int(n_boot),
            "seed": int(seed), "variant": str(variant)}


def supt_band(
    draws: np.ndarray,
    point: np.ndarray,
    level: float = 1.0 - FWER,
    sigma_floor: float = SIGMA_FLOOR,
) -> Dict[str, Any]:
    """Dai tin cay DONG THOI kieu sup-t.

        T^(b) = max_k |delta_k^(b) - delta_hat_k| / sigma_hat_k
        c     = quantile_level(T)
        dai   = delta_hat +/- c * sigma_hat

    sigma_hat lay tu CHINH cac draw (plug-in scale) -- day la cau truc chuan
    cua sup-t band, khong phai mot xap xi tam thoi. Khong phai ro ri kieu [A]:
    sigma_hat khong tham gia vao viec SINH ra draw, no chi chuan hoa chung sau
    khi da sinh.

    o co sigma_hat ~ 0 bi LOAI khoi T (chia cho ~0 se ap dao max) va duoc GHI
    LAI; dai cua chung la mot diem. Bao dam dong thoi van giu vi mot o tat
    dinh khong the vi pham.
    """
    draws = np.asarray(draws, dtype=np.float64)
    point = np.asarray(point, dtype=np.float64)
    sd = draws.std(axis=0, ddof=1)
    live = sd > float(sigma_floor)
    if not live.any():
        raise ValueError("moi sigma_hat = 0: khong dung duoc dai sup-t")

    z = np.abs(draws[:, live] - point[None, live]) / sd[None, live]
    t_stat = z.max(axis=1)
    c = float(np.quantile(t_stat, float(level)))

    lo = point - c * sd
    hi = point + c * sd
    lo[~live] = point[~live]
    hi[~live] = point[~live]
    return {
        "c_supt": c,
        "level": float(level),
        "sigma_hat": [float(x) for x in sd],
        "lo": [float(x) for x in lo],
        "hi": [float(x) for x in hi],
        "n_degenerate_sigma": int((~live).sum()),
        "degenerate_indices": [int(i) for i in np.flatnonzero(~live)],
        "t_stat_mean": float(t_stat.mean()),
        "t_stat_max": float(t_stat.max()),
    }


def three_interval_table(
    boot: Mapping[str, Any],
    labels: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    """BA khoang, de C-4 duoc phat bieu tren cap SO SANH DUOC (NT-v2-6).

      (1) percentile_per_cell  Q_0.025 / Q_0.975     <- noi tiep Phase 22
      (2) normal_per_cell      dhat +/- 1.96*sd      <- CUNG cau truc voi (3)
      (3) supt_simultaneous    dhat +/- c*sd         <- phat bieu GO-2

    C-4 phat bieu tren (2) vs (3). Vi c_supt > 1.96 luon dung voi K >= 2,
    (3) rong hon (2) o MOI o => so o chua 0 chi co the TANG. Do la bat bien
    CAU TRUC; so voi (1) thi khong, vi (1) bat doi xung.
    """
    arr = np.asarray(boot["draws"], np.float64)
    point = np.asarray(boot["point"], np.float64)
    sd = arr.std(axis=0, ddof=1)
    band = supt_band(arr, point)
    c = band["c_supt"]

    p_lo = np.quantile(arr, 0.025, axis=0)
    p_hi = np.quantile(arr, 0.975, axis=0)
    n_lo, n_hi = point - Z_TWO_SIDED_95 * sd, point + Z_TWO_SIDED_95 * sd
    s_lo, s_hi = np.asarray(band["lo"]), np.asarray(band["hi"])

    def zero_in(lo, hi):
        return (lo <= 0.0) & (0.0 <= hi)

    rows = []
    for k, lab in enumerate(labels):
        rows.append({
            **lab,
            "delta_point": float(point[k]),
            "delta_boot_mean": float(arr[:, k].mean()),
            "sigma_hat": float(sd[k]),
            "percentile_lo": float(p_lo[k]), "percentile_hi": float(p_hi[k]),
            "normal_lo": float(n_lo[k]), "normal_hi": float(n_hi[k]),
            "supt_lo": float(s_lo[k]), "supt_hi": float(s_hi[k]),
            "zero_percentile": bool(zero_in(p_lo[k], p_hi[k])),
            "zero_normal": bool(zero_in(n_lo[k], n_hi[k])),
            "zero_supt": bool(zero_in(s_lo[k], s_hi[k])),
            "sign_supt": ("0" if zero_in(s_lo[k], s_hi[k])
                          else ("+" if s_lo[k] > 0 else "-")),
            # do lech: khoang percentile lech bao nhieu so voi doi xung
            "skew_shift": float(((p_lo[k] + p_hi[k]) / 2.0) - point[k]),
        })

    n_zero_norm = int(sum(r["zero_normal"] for r in rows))
    n_zero_supt = int(sum(r["zero_supt"] for r in rows))
    crit = critical_values(len(rows))
    return {
        "rows": rows,
        "K": len(rows),
        "c_supt": c,
        **crit,
        "c_supt_over_bonferroni": float(c / crit["c_bonferroni"]),
        "c_supt_over_pointwise": float(c / Z_TWO_SIDED_95),
        "n_contains_zero_percentile": int(sum(r["zero_percentile"] for r in rows)),
        "n_contains_zero_normal": n_zero_norm,
        "n_contains_zero_supt": n_zero_supt,
        # C-4: bat bien CAU TRUC, phai luon dung
        "C4_containment_monotone": bool(n_zero_supt >= n_zero_norm),
        "C4_violations": [
            r for r in rows if r["zero_normal"] and not r["zero_supt"]
        ],
        "max_abs_skew_shift": float(max(abs(r["skew_shift"]) for r in rows)),
        "summary_by_slot_supt": _by_slot(rows),
    }


def _by_slot(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    for r in rows:
        d = out.setdefault(str(r["slot"]), {"n": 0, "zero": 0, "pos": 0, "neg": 0})
        d["n"] += 1
        d[{"0": "zero", "+": "pos", "-": "neg"}[r["sign_supt"]]] += 1
    return out


# ---------------------------------------------------------------------------
# 4. Doi chung va chan doan
# ---------------------------------------------------------------------------

def negative_control_self_delta(
    struct: Mapping[str, Any],
    variant: str = "B",
    n_boot: int = 200,
    seed: int = SEED_GO2,
    alpha: float = ALPHA,
) -> Dict[str, Any]:
    """NC-C-1: maxscore vs CHINH maxscore, cung draw -> delta = 0 CHINH XAC.

    Do rong > 0 <=> ghep cap HONG. Tren duong ong Phase 22 test nay DO o
    variant A (do duoc: max|delta_mean| = 7.99e-2, CI rong 4.24 ms).
    """
    b = bootstrap_deltas(struct, n_boot=n_boot, seed=seed, alpha=alpha,
                         variant=variant, procs=(BASELINE,), baseline=BASELINE)
    arr = np.asarray(b["draws"], np.float64)
    width = float(np.max(np.quantile(arr, 0.975, axis=0)
                         - np.quantile(arr, 0.025, axis=0)))
    max_abs = float(np.max(np.abs(arr)))
    return {"control": "NC-C-1", "variant": str(variant),
            "max_abs_delta": max_abs, "max_ci_width": width,
            "pass": bool(max_abs <= 1e-12 and width <= 1e-12)}


def positive_control_shift(
    struct: Mapping[str, Any],
    margin: float = 0.5,
    n_boot: int = 500,
    seed: int = SEED_GO2 + 1,
    alpha: float = ALPHA,
    variant: str = "B",
    shift_ms_diagnostic: float = 1.0,
) -> Dict[str, Any]:
    """PC-C-1: doi chung duong HAI PHIA, hieu chinh theo thang nhieu cua tung o.

    VI SAO KHONG DUNG "cong 1 ms roi doi moi o loai tru 0"
    ------------------------------------------------------
    Thiet ke dau tien lam vay va DO tren du lieu that (22/24 va 16/24). Hai
    khiem khuyet doc lap:

      (1) LOI DEM: no dem `lo > 0`, tuc "khoang nam hoan toan ben duong",
          chu khong phai "khoang KHONG chua 0". Cac o slot 1 co
          point ~ -2.4..-2.8 ms LOAI TRU 0 tu phia AM, va bi dem nham la truot.

      (2) LOI THIET KE: mot phep cong HANG SO khong phai doi chung duong hop le
          khi cac uoc luong diem trai tu -2.8 den +1.6 ms. No day mot so o RA XA
          0 va mot so o LAI GAN 0. Voi o co point = -1.0, cong dung 1 ms lam no
          THANH 0 -- tuc thiet ke tu tao ra that bai. Mot cai dat DUNG van truot.
          Cung ho loi voi tieu chi MC "do rong ~ 1/sqrt(B)" o Lesson 23.5[B]:
          nguong khong duoc dan tu do phan giai cua chinh phep do.

    THIET KE DUNG
    -------------
    Dat lai tam ve null (`delta - dbar`), roi bom mot tin hieu tinh theo DON VI
    sigma_hat cua tung o:

        draws = (delta - dbar) + s * sigma_hat
        point = s * sigma_hat
        => lo_k = s*sigma_k - c*sigma_k = (s - c) * sigma_k
        => loai tru 0  <=>  s > c

    Nen kiem duoc CA HAI PHIA, manh hon thiet ke cu:
        s = c + margin  ->  PHAI loai tru 0 o CA 24 o
        s = c - margin  ->  PHAI KHONG loai tru 0 o o nao

    Bao cao kem MDE (minimum detectable effect) theo ms de nguoi doc biet thang
    do phan giai that su cua dai.
    """
    b = bootstrap_deltas(struct, n_boot=n_boot, seed=seed, alpha=alpha,
                         variant=variant)
    arr = np.asarray(b["draws"], np.float64)
    point = np.asarray(b["point"], np.float64)
    base = supt_band(arr, point)
    c = float(base["c_supt"])
    sd = np.asarray(base["sigma_hat"], np.float64)
    centred = arr - arr.mean(axis=0, keepdims=True)

    def excludes(s: float) -> int:
        pt = float(s) * sd
        band = supt_band(centred + pt[None, :], pt)
        lo, hi = np.asarray(band["lo"]), np.asarray(band["hi"])
        return int(((lo > 0.0) | (hi < 0.0)).sum())

    k = int(len(sd))
    n_above = excludes(c + float(margin))
    n_below = excludes(max(c - float(margin), 0.0))

    # Chan doan (KHONG phai cong): thang ms that su can de tach khoi 0.
    mde = c * sd - np.abs(point)
    lo0, hi0 = np.asarray(base["lo"]), np.asarray(base["hi"])
    n_excl_observed = int(((lo0 > 0.0) | (hi0 < 0.0)).sum())
    n_excl_fixed_shift = 0
    if shift_ms_diagnostic:
        pt = point + float(shift_ms_diagnostic)
        bd = supt_band(arr + float(shift_ms_diagnostic), pt)
        l2, h2 = np.asarray(bd["lo"]), np.asarray(bd["hi"])
        n_excl_fixed_shift = int(((l2 > 0.0) | (h2 < 0.0)).sum())

    return {
        "control": "PC-C-1",
        "design": "signal injected in units of sigma_hat, two-sided",
        "c_supt": c,
        "margin_sigma": float(margin),
        "K": k,
        "s_above": float(c + margin),
        "n_excludes_zero_at_s_above": n_above,
        "s_below": float(max(c - margin, 0.0)),
        "n_excludes_zero_at_s_below": n_below,
        "pass_detects_when_it_should": bool(n_above == k),
        "pass_silent_when_it_should": bool(n_below == 0),
        "pass": bool(n_above == k and n_below == 0),
        "mde_ms_min": float(mde.min()),
        "mde_ms_median": float(np.median(mde)),
        "mde_ms_max": float(mde.max()),
        "n_excludes_zero_observed": n_excl_observed,
        "n_excludes_zero_after_fixed_shift_1ms": n_excl_fixed_shift,
        "note": (
            "n_excludes_zero_* dem 'khoang KHONG chua 0' (ca hai phia). Thiet ke "
            "dau tien dem 'lo > 0' nen bao truot cac o slot 1 co point ~ -2.6 ms "
            "von DA loai tru 0 tu phia am."
        ),
    }


def instability_at_small_B(
    struct: Mapping[str, Any],
    seeds: Sequence[int] = SEEDS_INSTABILITY,
    n_boot: int = B_SMALL,
    alpha: float = ALPHA,
    variant: str = "B",
) -> Dict[str, Any]:
    """C-D5: bang chung TRUC TIEP rang phat bieu GO-2 khong on dinh o B=200."""
    labels = label_index(struct)
    counts = []
    for s in seeds:
        b = bootstrap_deltas(struct, n_boot=n_boot, seed=int(s), alpha=alpha,
                             variant=variant)
        t = three_interval_table(b, labels)
        counts.append(t["n_contains_zero_percentile"])
    a = np.asarray(counts, np.float64)
    return {"n_boot": int(n_boot), "seeds": [int(s) for s in seeds],
            "n_contains_zero_by_seed": [int(x) for x in counts],
            "min": int(a.min()), "max": int(a.max()),
            "range": int(a.max() - a.min()),
            "mean": float(a.mean()), "sd": float(a.std(ddof=1)),
            "unstable": bool(a.max() - a.min() >= 2)}


def mc_convergence(
    struct: Mapping[str, Any],
    n_seeds: int = MC_SEEDS,
    b_lo: int = MC_B_LO,
    b_hi: int = MC_B_HI,
    seed0: int = SEED_GO2 + 100,
    alpha: float = ALPHA,
    variant: str = "B",
) -> Dict[str, Any]:
    """Kiem hoi tu MC -- TIEU CHI DA SUA (Amendment 23-23).

    HAI menh de KHAC NHAU, khong duoc gop:
      (1) DO RONG dai HOI TU VE MOT HANG SO khac 0.
          Hang so do do n_block quyet dinh, KHONG phai B.
          Tieu chi "do rong co theo 1/sqrt(B)" la SAI ve khai niem: mot
          bootstrap DUNG se truot no, va 'sua' code cho qua nghia la lam
          hong bootstrap (vd. resample theo HANG thay vi theo BLOCK).
      (2) SAI SO MC cua uoc luong dau mut CO theo 1/sqrt(B).
          Do bang SD cua c_supt qua nhieu seed. Ly thuyet: co sqrt(10)=3.16x
          khi B di 200 -> 2000. Nguong mot phia 1.8x: co CHAM hon moi dang
          ngo; co NHANH hon chi la nhieu.

    n_seeds = 30 chu khong phai 10: sai so tuong doi cua mot uoc luong SD la
    ~1/sqrt(2(n-1)) = 23.6% o n=10, va ti so hai SD ~33% -- khong du phan giai
    de phan biet 1.8 voi 3.16, tuc chinh nguong cua cong.
    """
    res = {}
    for b in (b_lo, b_hi):
        cs, widths = [], []
        for i in range(int(n_seeds)):
            bt = bootstrap_deltas(struct, n_boot=int(b), seed=int(seed0 + i),
                                  alpha=alpha, variant=variant)
            band = supt_band(np.asarray(bt["draws"]), np.asarray(bt["point"]))
            cs.append(band["c_supt"])
            widths.append(float(2.0 * band["c_supt"]
                                * np.mean(band["sigma_hat"])))
        res[b] = {"c_mean": float(np.mean(cs)), "c_sd": float(np.std(cs, ddof=1)),
                  "width_mean": float(np.mean(widths))}

    width_change = abs(res[b_hi]["width_mean"] - res[b_lo]["width_mean"]) \
        / max(res[b_lo]["width_mean"], 1e-12)
    shrink = res[b_lo]["c_sd"] / max(res[b_hi]["c_sd"], 1e-300)
    return {
        "n_seeds": int(n_seeds), "by_B": {str(k): v for k, v in res.items()},
        "width_relative_change": float(width_change),
        "pass_width_stabilises": bool(width_change <= MC_WIDTH_TOL),
        "mc_error_shrink_factor": float(shrink),
        "expected_shrink_1_over_sqrtB": float(math.sqrt(b_hi / b_lo)),
        "pass_mc_error_shrinks": bool(shrink >= MC_SHRINK_MIN),
        "pass": bool(width_change <= MC_WIDTH_TOL and shrink >= MC_SHRINK_MIN),
    }


# ---------------------------------------------------------------------------
# 5. Mot cell dau-den-cuoi
# ---------------------------------------------------------------------------

def run_cell(
    df: pd.DataFrame,
    alpha: float = ALPHA,
    bin_col: str = "z_bin",
    n_boot: int = N_BOOT,
    variant: str = "B",
    with_mc: bool = True,
) -> Dict[str, Any]:
    calib = df[df["is_calib"].to_numpy(bool)]
    slots = _slot_cols(df)
    struct = build_global_blocks(calib, slots, bin_col)
    labels = label_index(struct)

    boot = bootstrap_deltas(struct, n_boot=n_boot, seed=SEED_GO2,
                            alpha=alpha, variant=variant)
    table = three_interval_table(boot, labels)

    out: Dict[str, Any] = {
        "kind": "go2_simultaneous",
        "baseline": BASELINE, "procedures": list(PROCS), "variant": str(variant),
        "n_blocks_calib": int(struct["n_blocks"]),
        "n_boot": int(n_boot), "seed": SEED_GO2, "alpha": float(alpha),
        "global_draw": True,                                  # C-D1
        "band": table,
        "NC_C_1": {v: negative_control_self_delta(struct, variant=v)
                   for v in VARIANTS},                        # C-D4
        "PC_C_1": positive_control_shift(struct),
        "instability_at_B200": instability_at_small_B(struct),  # C-D5
        "allowed_claim_scope": (
            "Dai sup-t bao dam DONG THOI cho ca %d dai luong o muc %.2f. "
            "Thu tu FWER duoc phat bieu THEO SLOT; khong duoc neu mot thu tu "
            "toan phan." % (table["K"], 1.0 - FWER)
        ),
    }
    if with_mc:
        out["mc_convergence"] = mc_convergence(struct, variant=variant)
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--calib", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--alpha", type=float, default=ALPHA)
    p.add_argument("--bin-col", default="z_bin")
    p.add_argument("--n-boot", type=int, default=N_BOOT)
    p.add_argument("--variant", default="B", choices=VARIANTS)
    p.add_argument("--skip-mc", action="store_true")
    args = p.parse_args()

    df = pd.read_parquet(args.calib)
    res = run_cell(df, alpha=args.alpha, bin_col=args.bin_col,
                   n_boot=args.n_boot, variant=args.variant,
                   with_mc=not args.skip_mc)
    res.update(
        cell=os.path.basename(args.calib),
        provenance={
            "script": "cert/go2_simultaneous.py", "calib": args.calib,
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "amendments": ["docs/phase-23/00y-amendment-24.md"],
            "env": {"pandas": pd.__version__, "numpy": np.__version__},
        },
    )
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, sort_keys=True, default=float)
        f.write("\n")

    t = res["band"]
    print("NC-C-1: " + " | ".join(
        "%s width=%.3e %s" % (v, r["max_ci_width"], "PASS" if r["pass"] else "FAIL")
        for v, r in res["NC_C_1"].items()))
    pc = res["PC_C_1"]
    print("PC-C-1: s=c+%.1f -> %d/%d loai tru 0 (can %d) | s=c-%.1f -> %d (can 0) | %s"
          % (pc["margin_sigma"], pc["n_excludes_zero_at_s_above"], pc["K"], pc["K"],
             pc["margin_sigma"], pc["n_excludes_zero_at_s_below"],
             "PASS" if pc["pass"] else "FAIL"))
    print("        MDE ms: min=%.4f median=%.4f max=%.4f | quan sat: %d/%d o da loai tru 0"
          % (pc["mde_ms_min"], pc["mde_ms_median"], pc["mde_ms_max"],
             pc["n_excludes_zero_observed"], pc["K"]))
    ins = res["instability_at_B200"]
    print("B=200 bat on dinh: n_zero %s  range=%d sd=%.2f"
          % (ins["n_contains_zero_by_seed"], ins["range"], ins["sd"]))
    print("c_supt=%.4f  c_bonf=%.4f  c_sidak=%.4f  supt/bonf=%.4f  supt/1.96=%.4f"
          % (t["c_supt"], t["c_bonferroni"], t["c_sidak"],
             t["c_supt_over_bonferroni"], t["c_supt_over_pointwise"]))
    print("n_contains_zero  percentile=%d  normal=%d  supt=%d   C4_monotone=%s"
          % (t["n_contains_zero_percentile"], t["n_contains_zero_normal"],
             t["n_contains_zero_supt"], t["C4_containment_monotone"]))
    print("theo slot (supt):", json.dumps(t["summary_by_slot_supt"]))
    if "mc_convergence" in res:
        mc = res["mc_convergence"]
        print("MC: width_change=%.4f (%s)  shrink=%.3f vs %.3f (%s)"
              % (mc["width_relative_change"],
                 "PASS" if mc["pass_width_stabilises"] else "FAIL",
                 mc["mc_error_shrink_factor"],
                 mc["expected_shrink_1_over_sqrtB"],
                 "PASS" if mc["pass_mc_error_shrinks"] else "FAIL"))


if __name__ == "__main__":
    main()
