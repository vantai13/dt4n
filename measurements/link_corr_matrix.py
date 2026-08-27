#!/usr/bin/env python3
"""Lesson 23.25 -- ma tran tuong quan link THAT, truc omega, quyet dinh 23.26.

Tien dang ky: docs/phase-23/A077-amendment-77.md
KHONG do moi. Doc `rho_measured_clean_*.csv` (da kiem sach o Lesson 23.24b).

SAU NHIEM VU:
    T0  kiem WIRING dai so (`M-242/243/244`) -- dap an biet truoc tu topology
    T1  ma tran tuong quan 8x8, TRONG TUNG RUN, gop bang Fisher z
    T2  `w_hat` (binh phuong toi thieu qua goc), `b_hat` (16 cap NULL),
        `w_hat_corrected` (da tru nen)
    T3  goodness-of-fit: phan du tach theo LOP `k`  -> `M-248`
    T4  `n_eff` + CI cua `w_hat` bang block bootstrap  -> `M-247`
    T5  `Var(margin)` duoi ma tran DO vs DON VI, TUNG cap duong
    T6  `SNR_dec` -> du bao `err(w)` qua Sheppard -> GO/NO-GO cho 23.26

CO SO LY THUYET (`A077` muc 3):
    r_lm(w) = w * k_lm,   k_lm = c_lm / sqrt(d_l * d_m)
    => tuyen tinh theo w, he so goc BIET TRUOC tu topology, khong phai fit.
    => w_hat = sum(r*k) / sum(k^2),  sum(k^2) = 5 tren butterfly 2x2.
    => sd(w_hat) = sd(r)/sqrt(5): CAU TRUC MUA DO CHINH XAC gap 2.236 lan.

★ DOI CHUNG DUONG `PC-25-1`: ban GOP-SAI (noi cac run roi `corrcoef`) duoc
  tinh LUON va in canh ben. No PHAI cho `w_hat >= 1.00`. Neu khong fire, phep
  do khong du nhay de phan biet hai cach tinh va MOI so khac mat gia tri.

Chay:
    python -m measurements.link_corr_matrix \\
        --campaign results/RAW/phase-23/aoi_v7_campaign \\
        --out results/LIVE/phase-23/link_corr_matrix.json
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import itertools
import json
import os
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from twin import cost_v2 as C
from twin import topology_v7 as T7

# --- HANG SO KHOA o `A077`. KHONG phai co dong lenh (chong p-hacking). ----
DT_MEASURED_S = 0.2       # `meta::measured_window_s`
BLOCK_TAU_MULT = 5.0      # cung quy uoc voi calib set (b = 5*tau)
MIN_BLOCKS_PER_RUN = 4    # `A077` muc 6b: block khong duoc dai qua n_run/4
TAU_RATIO_WARN = 3.0      # `block/tau < 3` -> CI la CAN DUOI (`L139`)
MODE = "poisson"          # `traffic_v7`: Poisson den + Pareto co. `L141`.
W_LOSS = 5000.0           # `CONSTANTS.md` K06, ngoai sinh tu SLA G.114
N_BOOT = 400
BOOT_SEED = 23825
SNR_FLAT = 0.25           # `A077` muc 9: nguong D1
SNR_STRONG = 1.00         # `A077` muc 9: nguong D2
Z_MEDIAN_S = 0.369        # trung vi AoI do duoc (Lesson 23.19/23.20)

# --- Lesson 23.25b (`A078`). CHI THEM, khong doi hang so cu. --------------
TIMESCALE_SLOW_S = 10.0   # `tau >=` nguong nay -> link CHAM.
                          # Do duoc: loi 2.74-4.17 s ; bien 20.03-27.67 s.
                          # Khe ho rong ~5 lan nen 10.0 nam giua va KHONG
                          # nhay cam. HANG SO KHOA, khong phai co dong lenh.
NULL_OUTLIER_MAD = 3.0    # cap NULL lech > 3 MAD -> ngoai lai

LINKS = tuple(T7.LINK_NAMES)
IDX = {l: i for i, l in enumerate(LINKS)}
PATH_PAIRS = tuple(itertools.combinations(T7.PATH_NAMES, 2))
RUN_KEY = re.compile(r"(clean|prod)_rho([0-9.]+)_rep([0-9]+)")


# ------------------------------------------------------- cau truc topology
def _paths_using() -> dict:
    return {l: {p for p in T7.PATH_NAMES if l in T7.PATHS[p]} for l in LINKS}


def structure_k() -> dict:
    """`k_lm = c_lm / sqrt(d_l d_m)`. Suy TU topology, khong fit, khong go tay."""
    uses = _paths_using()
    deg = {l: len(uses[l]) for l in LINKS}
    return {(a, b): len(uses[a] & uses[b]) / np.sqrt(deg[a] * deg[b])
            for a, b in itertools.combinations(LINKS, 2)}


K_PAIR = structure_k()
S_PAIRS = tuple(p for p, v in K_PAIR.items() if v > 0)      # 12 cap co cau truc
NULL_PAIRS = tuple(p for p, v in K_PAIR.items() if v == 0)  # 16 cap NULL
SUM_K2 = float(sum(K_PAIR[p] ** 2 for p in S_PAIRS))        # = 5.0


def structured_matrix(w: float) -> np.ndarray:
    """`R(w) = I + w*K`. Mot tham so, cau truc lay tu topology."""
    R = np.eye(len(LINKS))
    for (a, b), k in K_PAIR.items():
        R[IDX[a], IDX[b]] = R[IDX[b], IDX[a]] = w * k
    return R


# ---------------------------------------------------------------- doc file
def run_key(path: str) -> str:
    m = RUN_KEY.search(os.path.basename(path))
    return m.group(0) if m else os.path.basename(path)


def cell_of(path: str) -> str:
    m = RUN_KEY.search(run_key(path))
    if m is None:
        raise ValueError("ten file khong dung khuon chien dich: %r" % path)
    return "%s@%.3f" % (m.group(1), float(m.group(2)))


def load_run(path: str) -> np.ndarray:
    """Doc mot CSV DAI -> ma tran RONG `(n_samples, 8)`. Bo mau thieu link."""
    per = defaultdict(dict)
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            per[int(row["sample_index"])][row["link"]] = float(row["rho"])
    idxs = sorted(i for i, d in per.items() if len(d) == len(LINKS))
    if not idxs:
        return np.empty((0, len(LINKS)), dtype=float)
    return np.array([[per[i][l] for l in LINKS] for i in idxs], dtype=float)


def tau_from_meta(campaign: str) -> dict:
    """`A077` muc 6b -- DOC `tau` tu `meta_*.json`, khong gia dinh mot hang so.

    Ban thao de xuat `TAU_S = 3.5` "tu dai 2.82..4.28". Dai do chi dung cho
    bon link LOI. Link BIEN co `tau` gap ~7 lan (19.3 .. 26.7 s). Dung 3.5
    lam block bootstrap NOI DOI: tu tuong quan cua link bien chua bi pha nen
    SE qua hep va `n_eff` bi thoi phong (lop loi `L50`/`L52`).
    """
    per = defaultdict(list)
    for p in sorted(glob.glob(os.path.join(campaign, "**", "meta_*.json"),
                              recursive=True)):
        with open(p, encoding="utf-8") as fh:
            prof = json.load(fh).get("profile", {})
        for link, v in prof.items():
            if "tau_pred_s" in v:
                per[link].append(float(v["tau_pred_s"]))
    return {l: float(np.median(v)) for l, v in sorted(per.items())}


# ------------------------------------------------------------------- T1
def fisher_z(r):
    return np.arctanh(np.clip(r, -0.999999, 0.999999))


def pooled_corr(mats: list[np.ndarray]):
    """Gop tuong quan bang Fisher z.

    VI SAO Fisher z va khong phai trung binh `r`: phan phoi cua `r` bi chan o
    `[-1,1]` va lech; `artanh` dua no ve xap xi chuan, nen trung binh va CI
    moi co nghia.
    """
    zs = []
    for X in mats:
        if X.shape[0] < 10:
            continue
        with np.errstate(invalid="ignore"):
            R = np.corrcoef(X.T)
        R = np.nan_to_num(R, nan=0.0)
        np.fill_diagonal(R, 1.0)
        zs.append(fisher_z(R))
    if not zs:
        raise ValueError("khong co run nao du 10 mau")
    R = np.tanh(np.mean(zs, axis=0))
    np.fill_diagonal(R, 1.0)
    return R, len(zs)


# ------------------------------------------------------------------- T2
def omega_hat(R: np.ndarray) -> dict:
    """`w_hat = sum_S r*k / sum_S k^2` ; `b_hat` = trung binh 16 cap NULL.

    ★ VE THU BA -- `omega_hat_deattenuated`. Phep tru `b_hat` bo duoc phan
    CONG THEM cua mot confound common-mode, nhung KHONG bo duoc phan LAM
    LOANG ma no gay ra. Dai so: neu `eps_l = sqrt(w) F_l + sqrt(1-w) g_l + c*h`
    voi `h` chung cho moi link thi

        Var(eps_l) = 1 + c^2
        r_lm       = w*k_lm/(1+c^2) + c^2/(1+c^2)
        b_hat      = c^2/(1+c^2)              -> 1 - b_hat = 1/(1+c^2)
        w_hat_corr = w/(1+c^2) = w*(1 - b_hat)

    Nen `w = w_hat_corr / (1 - b_hat)`. Confound common-mode lam `w_hat_corr`
    BI THIEU DI, khong phai bi thoi phong. Da kiem bang `PC-25-2`.
    """
    num = sum(R[IDX[a], IDX[b]] * K_PAIR[(a, b)] for a, b in S_PAIRS)
    b_hat = float(np.mean([R[IDX[a], IDX[b]] for a, b in NULL_PAIRS]))
    num_c = sum((R[IDX[a], IDX[b]] - b_hat) * K_PAIR[(a, b)] for a, b in S_PAIRS)
    w_corr = float(num_c / SUM_K2)
    denom = 1.0 - b_hat
    return {
        "omega_hat": float(num / SUM_K2),
        "b_hat_null_pairs": b_hat,
        "omega_hat_corrected": w_corr,
        "omega_hat_deattenuated": (float(w_corr / denom)
                                   if abs(denom) > 1e-9 else None),
        "sum_k2": SUM_K2,
        "n_structured_pairs": len(S_PAIRS),
        "n_null_pairs": len(NULL_PAIRS),
        "r_structured": {"%s-%s" % p: float(R[IDX[p[0]], IDX[p[1]]])
                         for p in S_PAIRS},
        "r_null": {"%s-%s" % p: float(R[IDX[p[0]], IDX[p[1]]])
                   for p in NULL_PAIRS},
    }


# ------------------------------------------------------------------- T3
def goodness_of_fit(R: np.ndarray, w: float, b: float = 0.0) -> dict:
    """`M-248` -- phan du tach theo LOP `k`.

    Cau truc trong phan du = mo hinh mot-tham-so thieu. `L35`: co che chua
    biet thi KHONG duoc dieu chinh mo hinh de che.

    PHAN DU PHAI KHOP MO HINH DA FIT. `omega_hat_corrected` duoc suy tu
    `(r - b_hat)`, nen mo hinh la `r = b + w*k` va phan du la
    `r - b - w*k`. Ban dau tien bo quen `b` va do do phan du cua ca hai lop
    deu bi day len mot luong `b` -- lam mat dau hieu quan trong nhat, la hai
    lop lech NGUOC CHIEU nhau.
    """
    by = defaultdict(list)
    for pa, pb in S_PAIRS:
        k = K_PAIR[(pa, pb)]
        by[round(float(k), 4)].append(R[IDX[pa], IDX[pb]] - b - w * k)
    out = {}
    for k, v in sorted(by.items()):
        v = np.asarray(v, dtype=float)
        sd = float(v.std(ddof=1)) if v.size > 1 else float("nan")
        se = sd / np.sqrt(v.size) if v.size > 1 else float("nan")
        mean = float(v.mean())
        # `se = 0` voi `mean != 0` la bang chung MANH NHAT ve cau truc: mot
        # do lech HOAN TOAN HE THONG trong lop. Ban dau tien tra `None` o
        # day va do do KHONG BAO GIO gan co -- dung lop loi `L101` (mot co
        # che khong the kich hoat). Nay: ty so = vo cuc.
        if np.isfinite(se) and se > 0:
            ratio = abs(mean) / (2 * se)
        elif np.isfinite(sd) and abs(mean) > 1e-12:
            ratio = float("inf")
        else:
            ratio = None
        out[str(k)] = {
            "n_pairs": int(v.size),
            "mean_resid": mean,
            "sd_resid": sd,
            "abs_mean_over_2se": (None if ratio is None
                                  else (None if np.isinf(ratio) else ratio)),
            "systematic_offset_zero_spread": bool(ratio == float("inf")),
        }
    flags = [c["abs_mean_over_2se"] for c in out.values()
             if isinstance(c, dict) and c.get("abs_mean_over_2se") is not None]
    hard = [c.get("systematic_offset_zero_spread") for c in out.values()
            if isinstance(c, dict)]
    out["_verdict_structured_residual"] = bool(
        any(f > 1.0 for f in flags) or any(hard))
    return out


# ------------------------------------------------------------------- T4
def block_bootstrap(mats, rng, tau_system: float) -> dict:
    """`M-247` -- `n_eff` va CI cua `w_hat`. KHONG gia dinh iid (`L50`/`L52`).

    Do dai block phai du de PHA tu tuong quan cua link CHAM NHAT. Nhung do dai
    run (119.8 s) chi bang ~4.5 lan `tau` cua link bien, nen block bi CAP boi
    `n_run // MIN_BLOCKS_PER_RUN`. Khi bi cap, `block_len_over_tau_system` < 3
    va CI la mot CAN DUOI cua do rong that (`A077` muc 6b, `L139`).
    """
    n_min = min(X.shape[0] for X in mats)
    target = int(np.ceil(BLOCK_TAU_MULT * tau_system / DT_MEASURED_S))
    L = max(1, min(target, n_min // MIN_BLOCKS_PER_RUN))

    zs, ws = [], []
    for _ in range(N_BOOT):
        picks = []
        for X in mats:
            n = X.shape[0]
            if n < L:
                continue
            starts = rng.integers(0, n - L + 1, size=max(1, n // L))
            picks.append(np.concatenate([X[s:s + L] for s in starts], axis=0))
        if not picks:
            continue
        Rb, _ = pooled_corr(picks)
        zs.append([fisher_z(Rb[IDX[a], IDX[b]]) for a, b in S_PAIRS])
        ws.append(omega_hat(Rb)["omega_hat"])

    Zb, Wb = np.asarray(zs), np.asarray(ws)
    sd_z = float(np.mean(Zb.std(axis=0, ddof=1)))
    ratio = L * DT_MEASURED_S / tau_system
    return {
        "block_len_samples": int(L),
        "block_len_s": float(L * DT_MEASURED_S),
        "block_target_samples": int(target),
        "block_was_capped_by_run_length": bool(target > n_min // MIN_BLOCKS_PER_RUN),
        "tau_system_s": float(tau_system),
        "block_len_over_tau_system": float(ratio),
        "ci_is_lower_bound_on_width": bool(ratio < TAU_RATIO_WARN),
        "n_boot": int(Wb.size),
        "sd_fisher_z_mean_over_pairs": sd_z,
        "n_eff_per_pair": float(3.0 + 1.0 / sd_z ** 2) if sd_z > 0 else None,
        "sd_omega_hat_analytic": float(sd_z / np.sqrt(SUM_K2)) if sd_z > 0 else None,
        "sd_omega_hat_empirical": float(Wb.std(ddof=1)),
        "omega_hat_ci95": [float(np.percentile(Wb, 2.5)),
                           float(np.percentile(Wb, 97.5))],
        "note": ("Neu `ci_is_lower_bound_on_width` la true thi block khong du "
                 "dai de pha tu tuong quan cua link cham nhat; CI la CAN DUOI "
                 "cua do rong that va `n_eff` la CAN TREN. Xem `L139`."),
    }


# ------------------------------------------------------------------- T5
def margin_vector(pi: str, pj: str) -> np.ndarray:
    v = np.zeros(len(LINKS), dtype=float)
    for l in T7.PATHS[pi]:
        v[IDX[l]] += 1.0
    for l in T7.PATHS[pj]:
        v[IDX[l]] -= 1.0
    return v


def var_margin(R: np.ndarray, w: float) -> dict:
    """`Var(m) = v^T R v`, duoi ma tran DO va duoi ma tran DON VI.

    Bao cao THEO TUNG CAP DUONG, khong gop -- bai hoc `K4` ("khong bao gio
    bao cao so gop").

    Ba con so, khong phai mot:
      `var_measured_matrix`        tu `R` do duoc (nhieu o 28 o ngoai cheo)
      `var_structured_at_omega_hat` tu MOT tham so (nhieu it hon nhieu)
      `ratio_at_omega_1_analytic`  du doan ly thuyet, doi chieu `M-243/244`
    Neu ba so bat dong -> biet ngay la do nhieu `R` hay do mo hinh sai.
    """
    I = np.eye(len(LINKS))
    R_w = structured_matrix(w)
    R_1 = structured_matrix(1.0)          # TINH TRUC TIEP, khong chia cho w
    out = {}
    for pi, pj in PATH_PAIRS:
        v = margin_vector(pi, pj)
        v_id = float(v @ I @ v)
        out["m(%s,%s)" % (pi, pj)] = {
            "var_identity": v_id,
            "var_measured_matrix": float(v @ R @ v),
            "var_structured_at_omega_hat": float(v @ R_w @ v),
            "ratio_measured_over_identity": float(v @ R @ v) / v_id,
            "ratio_at_omega_1_analytic": float(v @ R_1 @ v) / v_id,
            "shared_link": bool(set(T7.PATHS[pi]) & set(T7.PATHS[pj])),
        }
    return out


# ------------------------------------------------------------------- T6
def sheppard(r: float) -> float:
    """`P(doi dau) = arccos(r)/pi` khi `E[m]=0`.

    KHONG chua `Var(m)` -- do la ca van de (`A077` muc 2b). Nen khi `E[m]=0`,
    `err` BAT BIEN voi thang cua `m`, tuc bat bien voi `omega`.
    """
    return float(np.arccos(np.clip(r, -1.0, 1.0)) / np.pi)


def err_bivariate(snr: float, r: float) -> float:
    """`P(sign(m_hat) != sign(m_true))` cho chuan hai chieu.

    `X = m_true ~ N(mu, s^2)`, `Y = m_hat` cung bien, tuong quan `r`.
    Voi `a = mu/s = SNR`:

        err = 1 - Phi2(-a, -a; r) - Phi2(a, a; r)

    Kiem: tai `a = 0` ta co `Phi2(0,0;r) = 1/4 + arcsin(r)/(2*pi)`, nen
    `err = 1/2 - arcsin(r)/pi = arccos(r)/pi` -- dung cong thuc Sheppard.
    Do la ly do `err` BAT BIEN voi thang khi `E[m] = 0` (`A077` muc 2b).
    """
    from scipy.stats import multivariate_normal as mvn
    cov = [[1.0, r], [r, 1.0]]
    lo = float(mvn.cdf([-snr, -snr], mean=[0.0, 0.0], cov=cov))
    hi = float(mvn.cdf([snr, snr], mean=[0.0, 0.0], cov=cov))
    return float(1.0 - lo - hi)


def err_forecast(snr_median: float, r: float) -> dict:
    """`M-251` -- du bao `err(w=1)/err(w=0)` tu `SNR_dec` do duoc.

    `omega` KHONG vao `err` truc tiep. No vao qua `sd(m)`: o `w = 1`,
    `Var(m)` nhan `V` (1.7071 cap KE, 1.9428 cap CHEO), nen
    `SNR(w=1) = SNR(w=0) / sqrt(V)`. `r` khong doi.
    """
    out = {}
    e0 = err_bivariate(snr_median, r)
    for name, V in (("adjacent_1.7071", 1.70711), ("crossed_1.9428", 1.94281)):
        e1 = err_bivariate(snr_median / np.sqrt(V), r)
        out[name] = {"var_inflation": V, "snr_at_omega1": snr_median / np.sqrt(V),
                     "err_at_omega0": e0, "err_at_omega1": e1,
                     "ratio_err_omega1_over_omega0": e1 / e0 if e0 > 0 else None}
    return out


def snr_and_forecast(mats, cells, tau_system: float) -> dict:
    """`SNR_dec = |E[m]|/sd(m)` tren cost THAT, + du bao `err(w)` qua Sheppard."""
    cv = C.CostV2(strict_reliable=False)     # cung quy uoc `cell_matrices`
    acc, clipped = defaultdict(list), 0.0
    for X, cell in zip(mats, cells):
        if X.size == 0:
            continue
        clipped = max(clipped, float(np.mean((X < C.RHO_MIN) | (X > C.RHO_MAX))))
        Xc = np.clip(X, C.RHO_MIN, C.RHO_MAX)
        _d, _l, cost = cv.tables_batch(Xc, MODE, W_LOSS)
        for pi, pj in PATH_PAIRS:
            m = (cost[:, T7.PATH_NAMES.index(pi)]
                 - cost[:, T7.PATH_NAMES.index(pj)])
            sd = float(m.std(ddof=1))
            if sd > 0:
                acc["%s|m(%s,%s)" % (cell, pi, pj)].append(
                    abs(float(m.mean())) / sd)
    snr = {k: float(np.mean(v)) for k, v in sorted(acc.items())}
    vals = [v for v in snr.values() if np.isfinite(v)]
    med = float(np.median(vals)) if vals else None

    # r giua `m_hat` (tre `z`) va `m_true`: AR(1) voi `tau` he thong.
    r_z = float(np.exp(-Z_MEDIAN_S / tau_system))
    if med is None:
        decision, band = "UNDECIDED", None
    elif med <= SNR_FLAT:
        decision, band = "D1_DO_NOT_OPEN_23_26_AS_MININET_CAMPAIGN", "<=0.25"
    elif med >= SNR_STRONG:
        decision, band = "D2_OPEN_23_26_FULL", ">=1.00"
    else:
        decision, band = "D3_OPEN_23_26_REDUCED_HIGHEST_SNR_CELL_ONLY", "(0.25,1.00)"

    return {
        "snr_by_cell_and_pair": snr,
        "snr_median": med,
        "snr_min": float(min(vals)) if vals else None,
        "snr_max": float(max(vals)) if vals else None,
        "snr_band": band,
        "rho_out_of_model_domain_share_max": clipped,
        "z_median_s": Z_MEDIAN_S,
        "tau_system_s": float(tau_system),
        "r_at_z_median": r_z,
        "err_reference_zero_mean_sheppard": sheppard(r_z),
        "M_251_err_forecast": (err_forecast(med, r_z) if med is not None
                               else None),
        "decision_for_lesson_23_26": decision,
        "decision_thresholds": {"D1_max": SNR_FLAT, "D2_min": SNR_STRONG},
    }


# ---------------------------------------------------------------- wiring
def wiring_checks() -> dict:
    """`M-242/243/244` -- dap an biet truoc tu topology.

    Kiem CAI DAT, khong phai phat hien (ha cap theo tien le `M-193`/`M-200`).
    Thu HET moi cap duong va kiem tinh DONG NHAT trong tung lop, thay vi giu
    lai gia tri cuoi cung cua vong lap.
    """
    R1 = structured_matrix(1.0)
    adj, crossed = [], []
    for pi, pj in PATH_PAIRS:
        v = margin_vector(pi, pj)
        ratio = float(v @ R1 @ v) / float(v @ v)
        (adj if set(T7.PATHS[pi]) & set(T7.PATHS[pj]) else crossed).append(ratio)
    return {
        "M_242_sum_k2": SUM_K2,
        "M_243_var_ratio_adjacent_at_omega1": float(np.mean(adj)),
        "M_244_var_ratio_crossed_at_omega1": float(np.mean(crossed)),
        "n_adjacent_pairs": len(adj),
        "n_crossed_pairs": len(crossed),
        "adjacent_is_homogeneous": bool(np.ptp(adj) < 1e-9),
        "crossed_is_homogeneous": bool(np.ptp(crossed) < 1e-9),
        "k_classes": sorted({round(float(v), 4) for v in K_PAIR.values() if v > 0}),
    }


# ============ Lesson 23.25b -- T7: kiem toan NEN cua `omega_hat` ==========
# `A078`. CHI THEM ham moi; `T0`..`T6` KHONG doi mot dong (`NC-25b-2`, `NT 49`).

def pair_family(a: str, b: str, tau: dict) -> str:
    """Phan loai cap theo THANG THOI GIAN.

    VI SAO CAN: `tau` cua link BIEN (20-28 s) gap ~7 lan link LOI (2.7-4.2 s).
    Hai qua trinh AR(1) cham hon cho `r` mau kem chinh xac hon NHIEU trong
    cung mot do dai chuoi. Gop chung vao MOT `b_hat` la tron mot phan phoi
    LUONG CUC roi bao cao trung binh cua no.
    """
    slow_a = float(tau[a]) >= TIMESCALE_SLOW_S
    slow_b = float(tau[b]) >= TIMESCALE_SLOW_S
    if slow_a and slow_b:
        return "slow-slow"
    if not slow_a and not slow_b:
        return "fast-fast"
    return "slow-fast"


def neff_pair(a, b, tau, n_samples, n_runs, dt=DT_MEASURED_S) -> float:
    """`n_eff` cua MOT cap, bi chi phoi boi link CHAM HON.

    ★ Tren butterfly, MOI cap co cau truc deu chua it nhat mot link BIEN:
    `k_lm > 0` doi hai link chung duong, ma moi link LOI thuoc DUNG MOT
    duong nen hai link loi khong bao gio chung duong. Do duoc: 0/12 cap la
    nhanh-nhanh. Nen `n_eff` thuc la 32-45, KHONG phai so gop 393 (`L142`).
    """
    tau_max = max(float(tau[a]), float(tau[b]))
    return max(2.0, n_runs * n_samples * dt / (2.0 * tau_max))


def null_homogeneity(R: np.ndarray, tau: dict) -> dict:
    """★ Lo hong cua `M-248`: `goodness_of_fit` CHI soi 12 cap CO CAU TRUC.

    Cau truc lon nhat trong du lieu nam o 16 cap NULL, va `b_hat` la mot VO
    HUONG nen no hut het cau truc do roi nem di phuong sai.
    """
    groups = defaultdict(list)
    for a, b in NULL_PAIRS:
        groups[pair_family(a, b, tau)].append(float(R[IDX[a], IDX[b]]))

    out: dict = {}
    for fam, v in sorted(groups.items()):
        arr = np.asarray(v, dtype=float)
        out[fam] = {"n_pairs": int(arr.size), "mean_r": float(arr.mean()),
                    "sd_r": float(arr.std(ddof=1)) if arr.size > 1 else None,
                    "min_r": float(arr.min()), "max_r": float(arr.max())}

    means = [c["mean_r"] for c in out.values()]
    vals = np.array([R[IDX[a], IDX[b]] for a, b in NULL_PAIRS], dtype=float)
    pooled_sd = float(vals.std(ddof=1))
    spread = float(max(means) - min(means)) if len(means) > 1 else 0.0

    med = float(np.median(vals))
    mad = float(np.median(np.abs(vals - med)) * 1.4826)
    outl = [(a, b) for a, b in NULL_PAIRS
            if mad > 0 and abs(R[IDX[a], IDX[b]] - med) > NULL_OUTLIER_MAD * mad]
    outl.sort(key=lambda p: -abs(R[IDX[p[0]], IDX[p[1]]]))

    out["_spread_between_families"] = spread
    out["_pooled_sd_all_null"] = pooled_sd
    out["_median_r"] = med
    out["_mad_r"] = mad
    out["_null_outliers"] = ["%s-%s" % p for p in outl]
    out["_verdict_null_set_heterogeneous"] = bool(
        spread > 2.0 * pooled_sd / np.sqrt(len(NULL_PAIRS)))
    return out


def omega_hat_stratified(R: np.ndarray, tau: dict) -> dict:
    """Nen RIENG cho tung ho thang do, thay vi mot `b_hat` duy nhat.

    CANH BAO DIEN GIAI: neu ho `slow-slow` chi co 2 cap va ca hai la ngoai
    lai thi nen cua ho do KHONG dang tin, va uoc luong se bi keo ra ngoai
    `[0,1]`. Mot ket qua NGOAI KHONG GIAN THAM SO la bang chung NEN SAI,
    khong phai bang chung `omega < 0`.
    """
    groups = defaultdict(list)
    for a, b in NULL_PAIRS:
        groups[pair_family(a, b, tau)].append(float(R[IDX[a], IDX[b]]))
    base = {fam: float(np.mean(v)) for fam, v in groups.items()}

    num = den = 0.0
    for a, b in S_PAIRS:
        k = K_PAIR[(a, b)]
        num += (R[IDX[a], IDX[b]] - base.get(pair_family(a, b, tau), 0.0)) * k
        den += k * k
    w = float(num / den) if den > 0 else None
    return {"baseline_by_family": base,
            "n_pairs_by_family": {f: len(v) for f, v in groups.items()},
            "omega_hat_stratified": w,
            "outside_parameter_space": bool(w is not None
                                            and not (0.0 <= w <= 1.0)),
            "note": ("`omega` la TI LE PHUONG SAI, phai thuoc [0,1]. Gia tri "
                     "ngoai khoang do la dau hieu NEN SAI, khong phai "
                     "`omega < 0`.")}


def omega_hat_weighted(R, tau, n_samples, n_runs) -> dict:
    """★ Binh phuong toi thieu CO TRONG SO + `sd` DUNG.

    Trong so `w = n_eff - 3 = 1/Var(z)` (Fisher z). Voi WLS toi uu,
    `Var(w_hat) = 1 / sum(w * k^2)`.

    So `sd` nay THAY CHO `T4.sd_omega_hat_analytic`: bootstrap khoi tren
    chuoi chi dai `4.3*tau` bi LECH VI TRI chu khong chi hep -- do duoc,
    `omega_hat` nam NGOAI CI95 cua chinh no (`L143`).
    """
    num = den = info = 0.0
    per = {}
    for a, b in S_PAIRS:
        k = K_PAIR[(a, b)]
        ne = neff_pair(a, b, tau, n_samples, n_runs)
        wt = max(0.0, ne - 3.0)
        num += wt * float(R[IDX[a], IDX[b]]) * k
        den += wt * k * k
        info += wt * k * k
        per["%s-%s" % (a, b)] = {"n_eff": float(ne), "weight": float(wt),
                                 "sd_r": float(1.0 / np.sqrt(max(ne - 3.0, 1.0))),
                                 "family": pair_family(a, b, tau)}
    w = float(num / den) if den > 0 else None
    sd = float(1.0 / np.sqrt(info)) if info > 0 else None
    return {"omega_hat_weighted": w,
            "sd_omega_hat_correct": sd,
            "ci95_correct": ([w - 1.96 * sd, w + 1.96 * sd]
                             if (w is not None and sd) else None),
            "sum_weight_k2": float(info),
            "n_eff_min": min(v["n_eff"] for v in per.values()),
            "n_eff_max": max(v["n_eff"] for v in per.values()),
            "n_pairs_fast_fast": sum(1 for v in per.values()
                                     if v["family"] == "fast-fast"),
            "per_pair": per,
            "note": ("MOI cap co cau truc chua it nhat mot link CHAM (do duoc: "
                     "0/12 cap la fast-fast), nen `n_eff` thuc la 32-45 chu "
                     "khong phai so gop 393. Xem `L142`.")}


def snr_sensitivity(t6: dict, sens: dict) -> dict:
    """`M-256`/`M-257` -- `SNR_dec` va quyet dinh `D` co ben vung khong?

    `SNR = |E[m]| / sd(m)`. Bo hai cap ngoai lai lam `Var(m)` doi tu
    `ratio_full` sang `ratio_without_dropped`, nen
    `sd(m)` nhan `sqrt(without/full)` va `SNR` nhan `sqrt(full/without)`.
    `E[m]` KHONG doi (no khong phu thuoc ma tran tuong quan).
    """
    scaled = {}
    for key, v in t6["snr_by_cell_and_pair"].items():
        pair = key.split("|", 1)[1]          # "m(P1,P3)"
        s2 = sens.get(pair)
        if s2 is None:
            continue
        f, w = s2["ratio_full"], s2["ratio_without_dropped"]
        scaled[key] = float(v * np.sqrt(f / w)) if w > 0 else None
    vals = [x for x in scaled.values() if x is not None and np.isfinite(x)]
    med = float(np.median(vals)) if vals else None
    if med is None:
        dec = "UNDECIDED"
    elif med <= SNR_FLAT:
        dec = "D1_DO_NOT_OPEN_23_26_AS_MININET_CAMPAIGN"
    elif med >= SNR_STRONG:
        dec = "D2_OPEN_23_26_FULL"
    else:
        dec = "D3_OPEN_23_26_REDUCED_HIGHEST_SNR_CELL_ONLY"
    return {"snr_median_without_outlier_pairs": med,
            "snr_median_full": t6["snr_median"],
            "decision_without_outlier_pairs": dec,
            "decision_full": t6["decision_for_lesson_23_26"],
            "decision_unchanged": bool(dec == t6["decision_for_lesson_23_26"]),
            "snr_by_cell_and_pair_scaled": scaled}


def var_margin_sensitivity(R: np.ndarray, drop_pairs) -> dict:
    """★ `Var(m)` co ben vung khi bo cac cap NULL ngoai lai khong?

    Bai hoc `K4`: khong bao gio bao cao so GOP khi mot phan tu chi phoi.
    """
    R0 = R.copy()
    for a, b in drop_pairs:
        R0[IDX[a], IDX[b]] = R0[IDX[b], IDX[a]] = 0.0
    out: dict = {"dropped": ["%s-%s" % (a, b) for a, b in drop_pairs]}
    for pi, pj in PATH_PAIRS:
        v = margin_vector(pi, pj)
        base = float(v @ v)
        full = float(v @ R @ v) / base
        drop = float(v @ R0 @ v) / base
        denom = (1.0 - full) + (drop - 1.0)
        out["m(%s,%s)" % (pi, pj)] = {
            "ratio_full": full,
            "ratio_without_dropped": drop,
            "share_explained_by_dropped": (float((1.0 - full) / denom)
                                           if abs(denom) > 1e-12 else None)}
    return out


# ===== Lesson 23.25c (`A079`): T8 -- kiem toan NHAN DANG ================
# CHI THEM. `T0`..`T7` khong doi (`NC-25c-1`).

LOAD_CHANNELS = {
    "uA": ("hsrc", "hA"), "uB": ("hsrc", "hB"),
    "ac": ("hA", "hC"), "ad": ("hA", "hD"),
    "bc": ("hB", "hC"), "bd": ("hB", "hD"),
    "vC": ("hC", "hdst"), "vD": ("hD", "hdst"),
}
BARTLETT_MAX_LAG_FRAC = 0.25


def shares_host(a: str, b: str) -> bool:
    return bool(set(LOAD_CHANNELS[a]) & set(LOAD_CHANNELS[b]))


def collinearity_audit() -> dict:
    """Kiem toan confound giua he so topology `k` va endpoint chung."""
    by = defaultdict(lambda: {"n": 0, "n_shared_host": 0, "pairs": []})
    all_pairs = []
    for a, b in itertools.combinations(LINKS, 2):
        k = round(float(K_PAIR[(a, b)]), 4)
        shared = shares_host(a, b)
        by[k]["n"] += 1
        by[k]["n_shared_host"] += int(shared)
        by[k]["pairs"].append("%s-%s" % (a, b))
        all_pairs.append({"pair": "%s-%s" % (a, b), "k": float(K_PAIR[(a, b)]),
                          "shared_host": shared,
                          "hosts": sorted(set(LOAD_CHANNELS[a])
                                          & set(LOAD_CHANNELS[b]))})
    for cell in by.values():
        cell["share"] = cell["n_shared_host"] / cell["n"]
    structured = {k: v for k, v in by.items() if k > 0}
    perfect = (all(v["share"] in (0.0, 1.0) for v in structured.values())
               and len({v["share"] for v in structured.values()}) > 1)
    return {
        "all_28_pairs": all_pairs,
        "by_k_class": {str(k): v for k, v in sorted(by.items())},
        "k_and_host_perfectly_collinear_within_structured": bool(perfect),
        "verdict": ("Lesson 23.25 la doi chung am/noise-floor calibration; "
                    "omega_hat khong duoc doc la tuong quan theo duong do "
                    "duoc tren generator mot-hop." if perfect
                    else "Khong co cong tuyen hoan hao trong tap co cau truc."),
    }


def neff_bartlett_empirical(mats, ia: int, ib: int,
                            max_lag_frac: float = BARTLETT_MAX_LAG_FRAC) -> float:
    """Do `n_eff` cua tuong quan cheo tu tong Bartlett cua ACF thuc nghiem.

    Dung cua so tam giac kieu Newey-West de khong cong don nhieu ACF mau o
    lag xa. Khong gia dinh AR(1), va khong dung `tau_pred_s`.
    """
    total_n = 0.0
    weighted_sum = 0.0
    for X in mats:
        n = int(X.shape[0])
        if n < 40:
            continue
        lag_max = max(1, int(max_lag_frac * n))
        xa = np.asarray(X[:, ia], dtype=float) - float(np.mean(X[:, ia]))
        xb = np.asarray(X[:, ib], dtype=float) - float(np.mean(X[:, ib]))
        va, vb = float(xa @ xa), float(xb @ xb)
        if va <= 0.0 or vb <= 0.0:
            continue
        bartlett_sum = 1.0
        for lag in range(1, lag_max + 1):
            ra = float((xa[:-lag] @ xa[lag:]) / va)
            rb = float((xb[:-lag] @ xb[lag:]) / vb)
            taper = 1.0 - lag / (lag_max + 1.0)
            bartlett_sum += 2.0 * taper * ra * rb
        total_n += n
        weighted_sum += n * max(bartlett_sum, 1.0)
    if total_n == 0.0:
        return 2.0
    mean_sum = weighted_sum / total_n
    return max(2.0, total_n / mean_sum)


def bartlett_neff_all_pairs(mats, tau: dict) -> tuple[dict, dict]:
    values, detail = {}, {}
    for a, b in itertools.combinations(LINKS, 2):
        ne = neff_bartlett_empirical(mats, IDX[a], IDX[b])
        values[(a, b)] = ne
        detail["%s-%s" % (a, b)] = {
            "n_eff": float(ne), "family": pair_family(a, b, tau),
            "k": float(K_PAIR[(a, b)]), "shared_host": shares_host(a, b),
        }
    return values, detail


def fit_joint_wls(R: np.ndarray, neff: dict, extra_covariates=None,
                  pairs=None, include_k: bool = True) -> dict:
    """Fit WLS Fisher-z; bao cao ca SE hinh thuc va quasi-WLS scaled."""
    extras = list(extra_covariates or [])
    coef_names = ["intercept_b"]
    if include_k:
        coef_names.append("omega")
    coef_names += [name for name, _ in extras]
    names, y, weights, rows = [], [], [], []
    selected = list(pairs or itertools.combinations(LINKS, 2))
    for a, b in selected:
        names.append("%s-%s" % (a, b))
        y.append(float(fisher_z(R[IDX[a], IDX[b]])))
        weights.append(max(float(neff[(a, b)]) - 3.0, 1.0))
        row = [1.0]
        if include_k:
            row.append(float(K_PAIR[(a, b)]))
        row += [float(fn(a, b)) for _name, fn in extras]
        rows.append(row)
    X = np.asarray(rows, dtype=float)
    yv = np.asarray(y, dtype=float)
    wv = np.asarray(weights, dtype=float)
    normal = X.T @ (wv[:, None] * X)
    rhs = X.T @ (wv * yv)
    coef = np.linalg.solve(normal, rhs)
    cov = np.linalg.inv(normal)
    sd = np.sqrt(np.diag(cov))
    resid = yv - X @ coef
    chi2 = float(np.sum(wv * resid * resid))
    dof = len(yv) - X.shape[1]
    chi2_over_dof = chi2 / dof
    scale = float(np.sqrt(max(1.0, chi2_over_dof)))
    sd_scaled = sd * scale
    return {
        "coef_names": coef_names,
        "coef": {name: float(value) for name, value in zip(coef_names, coef)},
        "sd": {name: float(value) for name, value in zip(coef_names, sd)},
        "t": {name: float(value / err)
              for name, value, err in zip(coef_names, coef, sd)},
        "ci95": {name: [float(value - 1.96 * err), float(value + 1.96 * err)]
                 for name, value, err in zip(coef_names, coef, sd)},
        "scale_factor_S": scale,
        "sd_scaled": {name: float(value)
                      for name, value in zip(coef_names, sd_scaled)},
        "t_scaled": {name: float(value / err)
                     for name, value, err in zip(coef_names, coef, sd_scaled)},
        "ci95_scaled": {
            name: [float(value - 1.96 * err), float(value + 1.96 * err)]
            for name, value, err in zip(coef_names, coef, sd_scaled)},
        "chi2": chi2, "dof": int(dof), "chi2_over_dof": chi2_over_dof,
        "normal_matrix": normal.tolist(),
        "pair_residuals_fisher_z": {name: float(value)
                                    for name, value in zip(names, resid)},
        "pair_chi2_contributions": {
            name: float(weight * value * value)
            for name, weight, value in zip(names, wv, resid)},
        "n_pairs": len(names),
        "note": ("chi2/dof >> 1: mo hinh thieu cau truc hoac n_eff qua lon; "
                 "chi2/dof << 1: n_eff co the bi uoc luong thap. `sd_scaled` "
                 "la quasi-WLS overdispersion diagnostic, KHONG sua model "
                 "misspecification."),
    }


def margin_acf_at_lag(mats, z_s: float = Z_MEDIAN_S,
                      dt: float = DT_MEASURED_S) -> dict:
    """Do ACF margin va noi suy log chinh xac tai `z` giua lag 1/2."""
    from measurements.acf_nugget import FIT_LAGS, acf, fit_nugget

    lag_float = z_s / dt
    lag_lo = max(1, int(np.floor(lag_float)))
    lag_hi = max(lag_lo + 1, int(np.ceil(lag_float)))
    frac = lag_float - lag_lo
    cv = C.CostV2(strict_reliable=False)
    series = defaultdict(list)
    for X in mats:
        Xc = np.clip(X, C.RHO_MIN, C.RHO_MAX)
        _delay, _loss, cost = cv.tables_batch(Xc, MODE, W_LOSS)
        for pi, pj in PATH_PAIRS:
            m = (cost[:, T7.PATH_NAMES.index(pi)]
                 - cost[:, T7.PATH_NAMES.index(pj)])
            series["m(%s,%s)" % (pi, pj)].append(m)
    out = {}
    for name, vectors in sorted(series.items()):
        a_lo_runs = [float(acf(v, (lag_lo,))[0]) for v in vectors]
        a_hi_runs = [float(acf(v, (lag_hi,))[0]) for v in vectors]
        a_lo, a_hi = float(np.mean(a_lo_runs)), float(np.mean(a_hi_runs))
        r_z = (float(np.exp(np.log(a_lo) + frac * (np.log(a_hi) - np.log(a_lo))))
               if a_lo > 0.0 and a_hi > 0.0 else None)
        fit_curve = np.mean([acf(v, FIT_LAGS) for v in vectors], axis=0)
        nugget = fit_nugget(fit_curve, FIT_LAGS)
        out[name] = {
            "acf_lag_lo": a_lo, "acf_lag_hi": a_hi,
            "r_margin_at_requested_z": r_z,
            "err_zero_mean_sheppard": (sheppard(r_z) if r_z is not None else None),
            "margin_nugget_fit": nugget,
            "acf_lag_lo_per_run": a_lo_runs,
            "acf_lag_hi_per_run": a_hi_runs,
        }
    return {"z_requested_s": float(z_s), "lag_float": float(lag_float),
            "lag_lo": lag_lo, "lag_hi": lag_hi,
            "interpolation": "log-linear", "by_path_pair": out,
            "supersedes": ("T6.err_reference_zero_mean_sheppard; T6 dung "
                           "tau_system=max(tau_pred), khong do ACF margin.")}


def sensitivity_ladder(R: np.ndarray, neff: dict) -> dict:
    levels = [
        ("L0_all_28", ()),
        ("L1_drop_endpoint_2", (("uA", "uB"), ("vC", "vD"))),
        ("L2_drop_endpoint_plus_bd_4",
         (("uA", "uB"), ("vC", "vD"), ("bd", "vC"), ("bd", "vD"))),
    ]
    all_pairs = list(itertools.combinations(LINKS, 2))
    out = {}
    for name, dropped in levels:
        keep = [p for p in all_pairs if p not in dropped]
        out[name] = {"dropped": ["%s-%s" % p for p in dropped],
                     "fit": fit_joint_wls(R, neff, pairs=keep)}
    return out


def assert_scenarios_are_exhaustive(outcome: dict) -> None:
    """L145 nang cap: nhanh mac dinh phai tu kiem tinh admissible."""
    omega = outcome["coef"].get("omega")
    if omega is None or not (0.0 <= omega <= 1.0):
        raise AssertionError("default branch tra omega ngoai [0,1]: %r" % omega)


def _snr_corrected_for_margin_nugget(t6: dict, margin_acf: dict) -> dict:
    corrected = {}
    for key, value in t6["snr_by_cell_and_pair"].items():
        pair = key.split("|", 1)[1]
        fit = margin_acf["by_path_pair"][pair]["margin_nugget_fit"]
        sf = fit.get("signal_fraction")
        corrected[key] = (float(value / np.sqrt(sf))
                          if sf is not None and sf > 0.0 else None)
    vals = [v for v in corrected.values() if v is not None and np.isfinite(v)]
    med = float(np.median(vals)) if vals else None
    if med is None:
        decision = "UNDECIDED"
    elif med <= SNR_FLAT:
        decision = "D1_DO_NOT_OPEN_23_26_AS_MININET_CAMPAIGN"
    elif med >= SNR_STRONG:
        decision = "D2_OPEN_23_26_FULL"
    else:
        decision = "D3_OPEN_23_26_REDUCED_HIGHEST_SNR_CELL_ONLY"
    return {"snr_by_cell_and_pair_corrected": corrected,
            "snr_median_measured": t6["snr_median"],
            "snr_median_corrected": med,
            "decision_measured": t6["decision_for_lesson_23_26"],
            "decision_corrected": decision,
            "decision_changed": (None if decision == "UNDECIDED" else
                                 decision != t6["decision_for_lesson_23_26"]),
            "method": "divide SNR by sqrt(signal_fraction_margin)"}


def _deattenuate_matrix(R: np.ndarray, nugget: dict | None) -> dict | None:
    if not nugget:
        return None
    signal, projected = {}, []
    for link in LINKS:
        row = nugget["per_link"][link]
        value = row.get("signal_fraction")
        # Nhanh DEFAULT: fit loi co slope am nhung intercept >1 duoc chieu
        # len bien vat ly `lambda=0`. Day la diagnostic hau nghiem, khong
        # bien fit thanh hop le va khong doi phan xu DEFAULT.
        if value is None and row.get("slope_per_s", 0.0) < 0.0 \
                and row.get("signal_fraction_raw", 0.0) > 1.0:
            value = 1.0
            projected.append(link)
        signal[link] = value
    if any(v is None or v <= 0.0 for v in signal.values()):
        return {"valid": False, "reason": "missing_signal_fraction_even_after_projection"}
    Rd = np.eye(len(LINKS))
    clipped = []
    for a, b in itertools.combinations(LINKS, 2):
        value = float(R[IDX[a], IDX[b]] / np.sqrt(signal[a] * signal[b]))
        if abs(value) >= 0.999999:
            clipped.append("%s-%s" % (a, b))
        value = float(np.clip(value, -0.999999, 0.999999))
        Rd[IDX[a], IDX[b]] = Rd[IDX[b], IDX[a]] = value
    return {"valid": True, "signal_fraction_by_link": signal,
            "boundary_projected_lambda_zero_links": projected,
            "clipped_pairs": clipped,
            "R_deattenuated": Rd.tolist(),
            "omega_raw_through_origin": omega_hat(R)["omega_hat"],
            "omega_deattenuated_through_origin": omega_hat(Rd)["omega_hat"],
            "warning": ("DIAGNOSTIC POST-HOC: fit invalid co intercept>1 "
                        "duoc project ve lambda=0; deattenuation cung phong "
                        "dai shortfall confound, clip cap |r|>=1, va co the "
                        "lam ma tran khong PSD. Khong la headline/can tin cay.")}


def _control_checks(neff: dict) -> dict:
    pc = fit_joint_wls(structured_matrix(0.5), neff)
    nc = fit_joint_wls(np.eye(len(LINKS)), neff)
    # Voi intercept, nghiem dung la can bac hai phan tu [omega,omega] cua
    # `(X'WX)^-1`; `1/sqrt(sum(w*k^2))` chi dung cho fit qua goc.
    analytic_sd = float(np.sqrt(np.linalg.inv(
        np.asarray(nc["normal_matrix"], dtype=float))[1, 1]))
    pc_omega = pc["coef"]["omega"]
    nc_omega = nc["coef"]["omega"]
    nc_sd = nc["sd"]["omega"]
    return {
        "PC_25c_1_known_omega_0_5": {
            "omega_hat": pc_omega, "expected_range": [0.45, 0.55],
            "fired": bool(0.45 <= pc_omega <= 0.55),
        },
        "NC_25c_2_identity": {
            "omega_hat": nc_omega, "sd_reported": nc_sd,
            "sd_from_inverse_normal_matrix": analytic_sd,
            "relative_error_sd": abs(nc_sd - analytic_sd) / analytic_sd,
            "passed": bool(abs(nc_omega) < 1e-12
                           and abs(nc_sd - analytic_sd) / analytic_sd < 0.05),
            "note": ("Gate dung cho WLS co intercept; cong thuc qua goc "
                     "1/sqrt(sum(w*k^2)) khong ap dung."),
        },
    }


def _t0_t7_block(report: dict) -> dict:
    return {k: v for k, v in report.items()
            if re.match(r"^T[0-7](?:_|b_)", k)}


def _canonical_hash(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def t8_identifiability(mats, R: np.ndarray, tau: dict, t6: dict,
                       host_probe: dict | None = None,
                       nugget: dict | None = None) -> dict:
    neff, detail = bartlett_neff_all_pairs(mats, tau)
    slow = {l: float(tau[l]) >= TIMESCALE_SLOW_S for l in LINKS}
    cov_host = ("shared_host", lambda a, b: shares_host(a, b))
    cov_host_slow = ("host_x_slow", lambda a, b:
                     shares_host(a, b) and slow[a] and slow[b])
    m1 = fit_joint_wls(R, neff)
    m2 = fit_joint_wls(R, neff, [cov_host])
    m3 = fit_joint_wls(R, neff, [cov_host_slow])
    controls = _control_checks(neff)
    ladder = sensitivity_ladder(R, neff)
    m1_drop2 = ladder["L1_drop_endpoint_2"]["fit"]
    equivalence = {
        "M3_is_M1_drop_two_pairs": bool(
            abs(m3["coef"]["intercept_b"] - m1_drop2["coef"]["intercept_b"])
            < 1e-10
            and abs(m3["coef"]["omega"] - m1_drop2["coef"]["omega"]) < 1e-10),
        "delta_intercept": float(m3["coef"]["intercept_b"]
                                 - m1_drop2["coef"]["intercept_b"]),
        "delta_omega": float(m3["coef"]["omega"]
                             - m1_drop2["coef"]["omega"]),
        "dummy_nonzero_pairs": ["uA-uB", "vC-vD"],
        "interpretation": ("M3 la sensitivity analysis tuong duong bo hai "
                           "cap, khong la bang chung co che doc lap."),
    }

    posthoc = None
    if host_probe:
        pair_rows = host_probe.get("pairs", {})

        def value(field):
            return lambda a, b: pair_rows["%s-%s" % (a, b)][field]

        short = ("r_shortfall", value("r_shortfall"))
        offered = ("r_offered", value("r_offered"))
        m4 = fit_joint_wls(R, neff, [short])
        m5 = fit_joint_wls(R, neff, [short], include_k=False)
        m6 = fit_joint_wls(R, neff, [short, offered], include_k=False)
        measured_values = np.asarray([pair_rows["%s-%s" % p]["r_measured"]
                                      for p in itertools.combinations(LINKS, 2)])
        short_values = np.asarray([pair_rows["%s-%s" % p]["r_shortfall"]
                                   for p in itertools.combinations(LINKS, 2)])
        offered_values = np.asarray([pair_rows["%s-%s" % p]["r_offered"]
                                     for p in itertools.combinations(LINKS, 2)])
        posthoc = {
            "label": "DIAGNOSTIC_POST_HOC_NOT_HEADLINE",
            "M4_b_omega_shortfall": m4,
            "M5_b_shortfall": m5,
            "M6_b_shortfall_offered": m6,
            "corr_r_measured_r_shortfall": float(np.corrcoef(
                measured_values, short_values)[0, 1]),
            "corr_r_measured_r_offered": float(np.corrcoef(
                measured_values, offered_values)[0, 1]),
        }

    slow_slow = [v["n_eff"] for v in detail.values()
                 if v["family"] == "slow-slow"]
    min_ss = min(slow_slow) if slow_slow else None
    if min_ss is None:
        duration = None
    elif min_ss >= 60.0:
        duration = 120
    elif min_ss >= 20.0:
        duration = 240
    else:
        duration = 415

    r_short = None
    r_measured = None
    if host_probe:
        pair = host_probe.get("pairs", {}).get("uA-uB", {})
        r_short = pair.get("r_shortfall")
        r_measured = pair.get("r_measured")
    m264_hit = 0.4 <= m3["chi2_over_dof"] <= 2.5
    if r_short is not None and r_short >= 0.30 and m264_hit:
        scenario = "K1_HOST_CONTENTION_CONFIRMED"
    elif (r_short is not None and r_short < 0.30
          and r_measured is not None and r_measured >= 0.40):
        scenario = "K2_SWITCH_OR_INSTRUMENT_ARTIFACT"
    elif r_short is None:
        scenario = "INCOMPLETE_HOST_PROBE_MISSING"
    else:
        scenario = "K3_DEFAULT_USE_M1"

    margin_acf = margin_acf_at_lag(mats)
    default_point_ok = 0.0 <= m1["coef"]["omega"] <= 1.0
    default_ci_zero = (m1["ci95_scaled"]["omega"][0] <= 0.0
                       <= m1["ci95_scaled"]["omega"][1])
    if scenario == "K3_DEFAULT_USE_M1" and not default_point_ok:
        scenario = "K3_DEFAULT_INADMISSIBLE_DISCLOSED"

    return {
        "prereg": "docs/phase-23/A079-amendment-79.md",
        "uncertainty_and_nugget_amendment": "docs/phase-23/A080-amendment-80.md",
        "collinearity": collinearity_audit(),
        "neff_bartlett_empirical": detail,
        "bartlett_max_lag_fraction": BARTLETT_MAX_LAG_FRAC,
        "M1_b_omega": m1,
        "M2_plus_host": m2,
        "M3_plus_host_slow": m3,
        "M3_equivalence_to_M1_drop_two": equivalence,
        "sensitivity_ladder": ladder,
        "posthoc_continuous_diagnostics": posthoc,
        "controls": controls,
        "margin_acf_measured": margin_acf,
        "snr_deattenuation_from_margin_nugget":
            _snr_corrected_for_margin_nugget(t6, margin_acf),
        "link_correlation_deattenuation": _deattenuate_matrix(R, nugget),
        "duration_decision_for_23_26": {
            "min_n_eff_slow_slow": min_ss,
            "recommended_run_duration_s": duration,
            "rule": ">=60: 120s; [20,60): 240s; <20: 415s",
        },
        "scenario_adjudication": {
            "scenario": scenario, "r_shortfall_uA_uB": r_short,
            "r_measured_uA_uB": r_measured,
            "M264_M3_chi2_over_dof_hit": bool(m264_hit),
            "point_estimate_in_parameter_space": bool(default_point_ok),
            "scaled_ci_contains_zero": bool(default_ci_zero),
            "default_branch_admissible": bool(default_point_ok),
            "admissibility_verdict": (
                "PASS" if default_point_ok
                else "DEFAULT_BRANCH_INADMISSIBLE_DISCLOSED"),
        },
        "note": ("T8 thay thanh sai so cu cua T4/T7 bang n_eff Bartlett do "
                 "tu ACF va WLS chung. T0..T7 duoc giu de bao toan lich su."),
    }


def _provenance(script: str, argv_extra: dict) -> dict:
    def git(*a):
        try:
            return subprocess.run(a, capture_output=True, text=True,
                                  check=True).stdout.strip()
        except Exception:
            return ""

    return {"script": script, "git_hash": git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "argv": argv_extra}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--baseline-artifact", default=None,
                    help="artifact 23.25b de kiem NC-25c-1 cho T0..T7")
    ap.add_argument("--host-probe", default=None,
                    help="artifact host_confound_probe.json cho G23-319")
    ap.add_argument("--nugget", default=None,
                    help="artifact acf_nugget.json cho G23-323..325")
    ap.add_argument("--csv-glob", default="rho_measured_clean_*.csv",
                    help="mac dinh CHI dung CLEAN: PROD khong tai lap (`L31`)")
    a = ap.parse_args()

    baseline_report = None
    baseline_path = a.baseline_artifact
    if baseline_path and os.path.isfile(baseline_path):
        with open(baseline_path, encoding="utf-8") as fh:
            baseline_report = json.load(fh)

    host_probe = None
    if a.host_probe and os.path.isfile(a.host_probe):
        with open(a.host_probe, encoding="utf-8") as fh:
            host_probe = json.load(fh)

    nugget = None
    if a.nugget and os.path.isfile(a.nugget):
        with open(a.nugget, encoding="utf-8") as fh:
            nugget = json.load(fh)

    paths = sorted(glob.glob(os.path.join(a.campaign, "**", a.csv_glob),
                             recursive=True))
    if not paths:
        raise SystemExit("khong tim thay %s trong %s" % (a.csv_glob, a.campaign))

    mats = [load_run(p) for p in paths]
    cells = [cell_of(p) for p in paths]
    keep = [i for i, X in enumerate(mats) if X.shape[0] >= 10]
    mats = [mats[i] for i in keep]
    cells = [cells[i] for i in keep]

    tau_by_link = tau_from_meta(a.campaign)
    tau_system = max(tau_by_link.values())

    R, n_runs = pooled_corr(mats)
    est = omega_hat(R)
    w = est["omega_hat_corrected"]

    # ★ PC-25-1 -- ban GOP-SAI, phai fire
    R_wrong, _ = pooled_corr([np.concatenate(mats, axis=0)])
    est_wrong = omega_hat(R_wrong)

    by_cell = {}
    for cell in sorted(set(cells)):
        sub = [X for X, c in zip(mats, cells) if c == cell]
        Rc, nc = pooled_corr(sub)
        ec = omega_hat(Rc)
        by_cell[cell] = {"n_runs": nc, "omega_hat": ec["omega_hat"],
                         "b_hat": ec["b_hat_null_pairs"],
                         "omega_hat_corrected": ec["omega_hat_corrected"]}

    rng = np.random.default_rng(BOOT_SEED)
    boot = block_bootstrap(mats, rng, tau_system)

    t6 = snr_and_forecast(mats, cells, tau_system)

    import measurements.link_corr_matrix as _self
    from measurements import validity as V

    report = {
        "schema": "dt4n.link.corr_matrix.v1",
        "lesson": "23.25",
        "prereg": "docs/phase-23/A077-amendment-77.md",
        "status": "MEASUREMENT_ESTIMATE",
        "locked_constants": {
            "DT_MEASURED_S": DT_MEASURED_S, "BLOCK_TAU_MULT": BLOCK_TAU_MULT,
            "MIN_BLOCKS_PER_RUN": MIN_BLOCKS_PER_RUN,
            "TAU_RATIO_WARN": TAU_RATIO_WARN, "MODE": MODE, "W_LOSS": W_LOSS,
            "N_BOOT": N_BOOT, "BOOT_SEED": BOOT_SEED,
            "SNR_FLAT": SNR_FLAT, "SNR_STRONG": SNR_STRONG,
            "Z_MEDIAN_S": Z_MEDIAN_S,
        },
        "tau_by_link_from_meta": tau_by_link,
        "tau_system_s": float(tau_system),
        "n_runs_used": n_runs,
        "csv_glob": a.csv_glob,
        "T0_wiring": wiring_checks(),
        "T1_corr_matrix_within_run": {
            "links": list(LINKS),
            "R": [[float(x) for x in row] for row in R],
        },
        "T2_omega": est,
        "T2b_omega_by_cell": by_cell,
        "T3_goodness_of_fit": goodness_of_fit(R, w, est["b_hat_null_pairs"]),
        "T4_block_bootstrap": boot,
        "T5_var_margin": var_margin(R, w),
        "T6_snr_and_decision": t6,
        "PC_25_1_pooled_wrong_control": {
            "omega_hat": est_wrong["omega_hat"],
            "b_hat_null_pairs": est_wrong["b_hat_null_pairs"],
            "fired": bool(est_wrong["omega_hat"] >= 1.00),
            "note": ("Noi cac run roi `corrcoef` -> do lai chinh NUM XOAY "
                     "`rho_bar` da van, khong phai tuong quan mang. Pooling "
                     "artifact / ecological fallacy. `b_hat` lon la co bao "
                     "truc tiep."),
        },
        "provenance": _provenance("measurements/link_corr_matrix.py",
                                  {"campaign": a.campaign, "out": a.out,
                                   "csv_glob": a.csv_glob}),
        "validity": V.measurement_validity_block(
            instrument_module=_self,
            inputs=paths[:1] + ["results/LIVE/phase-L/link_model_v2_fit.json"],
            note=("Artifact DO cau truc tuong quan tai (vai tro MEASURES). "
                  "Khong dung truc AoI. CO dung truc SLA qua `W_LOSS` = K06 "
                  "cho phan T6."),
        ),
    }

    # ---- Lesson 23.25b (`A078`): khoi MOI, `T0`..`T6` KHONG doi -------
    n_samp = int(np.median([X.shape[0] for X in mats]))
    homo = null_homogeneity(R, tau_by_link)
    wls = omega_hat_weighted(R, tau_by_link, n_samp, n_runs)
    drop = [tuple(x.split("-")) for x in homo["_null_outliers"][:2]]
    report["T7_null_audit"] = {
        "prereg": "docs/phase-23/A078-amendment-78.md",
        "n_samples_per_run_median": n_samp,
        "null_homogeneity": homo,
        "omega_hat_stratified": omega_hat_stratified(R, tau_by_link),
        "omega_hat_weighted": wls,
        "var_margin_sensitivity": var_margin_sensitivity(R, drop),
        "snr_sensitivity": snr_sensitivity(
            t6, var_margin_sensitivity(R, drop)),
        "omega_hat_outside_own_bootstrap_ci": bool(
            not (boot["omega_hat_ci95"][0] <= est["omega_hat"]
                 <= boot["omega_hat_ci95"][1])),
        "ci_width_ratio_correct_over_bootstrap": (
            float(wls["sd_omega_hat_correct"] / boot["sd_omega_hat_empirical"])
            if boot.get("sd_omega_hat_empirical") else None),
        "note": ("Khoi MOI cua Lesson 23.25b. `T0`..`T6` KHONG doi "
                 "(`NC-25b-2`). `sd_omega_hat_correct` THAY CHO "
                 "`T4.sd_omega_hat_analytic`: bootstrap khoi tren chuoi "
                 "4.3*tau bi LECH VI TRI, xem `L143`."),
    }

    # ---- Lesson 23.25c (`A079`): khoi MOI, `T0`..`T7` KHONG doi -------
    report["T8_identifiability"] = t8_identifiability(
        mats, R, tau_by_link, t6, host_probe=host_probe, nugget=nugget)
    current_block = _t0_t7_block(report)
    current_hash = _canonical_hash(current_block)
    if baseline_report is None:
        nc_25c_1 = {
            "baseline_artifact": baseline_path,
            "current_t0_t7_sha256": current_hash,
            "passed": None,
            "note": "Khong co baseline artifact de so sanh.",
        }
    else:
        baseline_block = _t0_t7_block(baseline_report)
        baseline_hash = _canonical_hash(baseline_block)
        nc_25c_1 = {
            "baseline_artifact": baseline_path,
            "baseline_t0_t7_sha256": baseline_hash,
            "current_t0_t7_sha256": current_hash,
            "baseline_keys": sorted(baseline_block),
            "current_keys": sorted(current_block),
            "canonical_diff_count": int(baseline_block != current_block),
            "passed": bool(baseline_block == current_block),
        }
    report["T8_identifiability"]["NC_25c_1_t0_t7_unchanged"] = nc_25c_1

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("[link_corr] omega_hat=%+.4f (corr %+.4f)  b_hat=%+.4f  CI95 %s"
          % (est["omega_hat"], w, est["b_hat_null_pairs"],
             [round(x, 4) for x in boot["omega_hat_ci95"]]))
    print("[link_corr] PC-25-1 pooled-wrong omega=%+.4f fired=%s"
          % (est_wrong["omega_hat"], est_wrong["omega_hat"] >= 1.0))
    print("[link_corr] block=%d mau (%.1fs) = %.2f*tau_sys(%.1fs)  CI can duoi=%s"
          % (boot["block_len_samples"], boot["block_len_s"],
             boot["block_len_over_tau_system"], tau_system,
             boot["ci_is_lower_bound_on_width"]))
    print("[link_corr] SNR_dec median=%.4f -> %s"
          % (t6["snr_median"], t6["decision_for_lesson_23_26"]))
    t8 = report["T8_identifiability"]
    m1, m3 = t8["M1_b_omega"], t8["M3_plus_host_slow"]
    print("[link_corr:T8] M1 omega=%+.4f +- %.4f chi2/dof=%.3f"
          % (m1["coef"]["omega"], m1["sd_scaled"]["omega"],
             m1["chi2_over_dof"]))
    print("[link_corr:T8] M3 omega=%+.4f +- %.4f host_x_slow=%+.4f "
          "chi2/dof=%.3f"
          % (m3["coef"]["omega"], m3["sd_scaled"]["omega"],
             m3["coef"]["host_x_slow"], m3["chi2_over_dof"]))
    print("[link_corr:T8] scenario=%s duration_23_26=%ss NC_T0_T7=%s"
          % (t8["scenario_adjudication"]["scenario"],
             t8["duration_decision_for_23_26"]["recommended_run_duration_s"],
             nc_25c_1["passed"]))


if __name__ == "__main__":
    main()
