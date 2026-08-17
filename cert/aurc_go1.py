#!/usr/bin/env python3
"""Phase 23 / Lesson 23.5[B] -- AURC rieng phan tren luoi chung + GO-1.

Thu tuc khoa tai: docs/phase-23/00w-amendment-22.md  (B-D1..B-D11)
                  docs/phase-23/00x-amendment-23.md  (B-D12..B-D14)

VI SAO CO FILE NAY thay vi sua cert/config_matrix.py::aurc()
--------------------------------------------------------------
`aurc()` cu PHAI giu nguyen de con kiem tra tai lap Phase 22 (Amendment 22 §6).
Bay quan trong nhat no mac phai: C0 va C3 duoc lay mau o NHUNG DIEM acceptance
KHAC NHAU, roi moi ben chuan hoa theo dai rieng. Do duoc: ti so DOI DAU tren
poisson@0.925 (0.997272 luoi tho -> 1.002492 luoi chung).

DAI LUONG O DAY
---------------
    AURC[lo,hi] = (1/(hi-lo)) * integral_{lo}^{hi} R(gamma) d gamma
    R(gamma)    = err_given_accept tai acceptance = gamma
    ratio       = AURC(C3) / AURC(C0)

Ca hai duong duoc NOI SUY LEN CUNG MOT LUOI truoc khi tich phan (B-D2), va
chuan hoa bang HANG SO (hi-lo) chu khong bang dai rieng (B-D3).

BAT DINH
--------
Paired block bootstrap tren tap TEST, qhat CO DINH (B-D7). Dung thong ke du
theo block: acceptance va err|accept deu la TI SO CUA TONG, nen mot draw chi
la mot phep cong vector -> chinh xac tuyet doi, khong xap xi.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

# Dung LAI dung cac helper cua config_matrix: bao dam luat accept trong
# bootstrap GIONG HET luat accept trong uoc luong diem. Neu viet lai, hai
# duong ong co the troi khoi nhau ma khong ai phat hien.
from cert.config_matrix import (
    DEGENERATE_ERR,
    _accept,
    _mhat_cols,
    _q_rows,
    _score_cols,
    fit_config,
)
from cert.simultaneous_score import ALPHA


# ---------------------------------------------------------------------------
# 0. Hang so khoa -- moi thay doi phai qua amendment
# ---------------------------------------------------------------------------

WINDOW_LO = 0.60            # B-D3
WINDOW_HI = 1.00
WINDOW_N = 4001             # B-D2
GRID_NORM = WINDOW_HI - WINDOW_LO

CONFIG_NUM = "C3"           # tu so cua ti so GO-1
CONFIG_DEN = "C0"           # mau so
GO1_THRESHOLD = 1.02        # B-D8

N_BOOT = 2000               # B-D7
SEED_BOOT = 23601
B_LADDER = (200, 500, 1000, 2000)
MAX_FAILED_DRAW_FRAC = 0.01

MIN_KNOTS_IN_WINDOW = 6     # B-D14
MAX_SEGMENT_IN_WINDOW = 0.15

KAPPA_PRIMARY = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0)
KAPPA_REFINED = tuple(sorted(set(KAPPA_PRIMARY) | {          # B-D12
    0.05, 0.10, 0.15, 0.20, 0.30, 0.35, 0.40, 0.45, 0.55
}))


def _git(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# 1. Doc so an toan  (B-D10)
# ---------------------------------------------------------------------------

def as_float_nan(value: Any) -> float:
    """None -> nan. Bay 7: _json_clean map float khong huu han thanh JSON null,
    nen float(r['err_given_accept']) NEM TypeError tren chinh artifact vua ghi."""
    if value is None:
        return float("nan")
    return float(value)


def require(d: Mapping[str, Any], key: str) -> Any:
    """Thay cho d.get(key, <so>). Default so hoc tren du lieu thieu bien mot
    loi on ao thanh mot ket luan sai lang le (Bay 2)."""
    if key not in d:
        raise KeyError("thieu khoa bat buoc %r; co: %s" % (key, sorted(d)))
    return d[key]


# ---------------------------------------------------------------------------
# 2. AURC tren luoi chung
# ---------------------------------------------------------------------------

def prepare_curve(
    acceptance: np.ndarray,
    err_given_accept: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """Lam sach mot duong risk-coverage; KHONG monotonise (B-D11).

    - bo diem co err khong huu han (acceptance = 0 -> 0/0)
    - gop acceptance trung, giu err NHO NHAT  (B-D9)
    - BAO CAO so vi pham don dieu thay vi sua chung
    """
    x = np.asarray(acceptance, dtype=np.float64)
    y = np.asarray(err_given_accept, dtype=np.float64)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if x.size < 2:
        raise ValueError("can >= 2 diem huu han; nhan %d" % x.size)

    ux = np.unique(x)                                    # B-D9
    uy = np.array([y[x == v].min() for v in ux], dtype=np.float64)

    diffs = np.diff(uy)
    return ux, uy, {
        "n_points_raw": int(ok.size),
        "n_points_finite": int(ok.sum()),
        "n_points_after_dedup": int(ux.size),
        "n_duplicate_acceptance": int(ok.sum() - ux.size),
        "monotone_nondecreasing": bool(np.all(diffs >= -1e-12)),
        "n_monotonicity_violations": int((diffs < -1e-12).sum()),
    }


def aurc_window(
    acceptance: np.ndarray,
    err_given_accept: np.ndarray,
    lo: float = WINDOW_LO,
    hi: float = WINDOW_HI,
    n_grid: int = WINDOW_N,
    strict: bool = True,
) -> Dict[str, Any]:
    """AURC rieng phan tren luoi CHUNG. Chuan hoa bang HANG SO (hi-lo).

    strict=True  -> RAISE neu phai ngoai suy (B-D4). Dung cho uoc luong diem.
    strict=False -> tra aurc=nan va co extrapolated=True. Dung trong bootstrap,
                    noi mot draw hong khong duoc lam chet ca lan chay.
    """
    x, y, diag = prepare_curve(acceptance, err_given_accept)
    extrapolated = bool(x.min() > float(lo) + 1e-12 or x.max() < float(hi) - 1e-12)
    if extrapolated:
        msg = ("khong phu cua so [%.2f, %.2f]: acceptance quan sat duoc "
               "[%.4f, %.4f]. np.interp se pad PHANG bang y[0]/y[-1] -- so BIA."
               % (lo, hi, x.min(), x.max()))
        if strict:
            raise ValueError(msg)
        return {"aurc": float("nan"), "extrapolated": True, "note": msg, **diag}

    grid = np.linspace(float(lo), float(hi), int(n_grid))
    value = float(np.trapezoid(np.interp(grid, x, y), grid) / (float(hi) - float(lo)))

    # so KNOT that su chi phoi cua so -- Phat hien 8
    inside = x[(x > lo) & (x <= hi)]
    below = x[x <= lo]
    spanning = np.sort(np.concatenate([below[-1:], inside])) if below.size else inside
    widest = float(np.diff(spanning).max()) if spanning.size > 1 else float("nan")
    return {
        "aurc": value,
        "extrapolated": False,
        "n_knots_in_window": int(inside.size),
        "n_knots_effective": int(inside.size + (1 if below.size else 0)),
        "knot_below_window": float(below.max()) if below.size else None,
        "widest_segment_in_window": widest,
        "window": [float(lo), float(hi)],
        "grid_n": int(n_grid),
        "normaliser": float(hi) - float(lo),
        **diag,
    }


# ---------------------------------------------------------------------------
# 3. Thong ke du theo block  -- xuong song cua bootstrap
# ---------------------------------------------------------------------------

def block_sufficient_stats(
    test: pd.DataFrame,
    fit: Mapping[str, Any],
) -> Dict[str, np.ndarray]:
    """Ba dem moi block, du de tinh acceptance va err|accept o MOI draw.

        acceptance = sum n_acc      / sum n_rows
        err|accept = sum n_wrong_acc / sum n_acc

    Ca hai la TI SO CUA TONG, nen mot bootstrap draw chi la phep cong vector.
    Chinh xac tuyet doi, khong xap xi.
    """
    sim = bool(fit["simultaneous"])
    keys = list(fit["keys"])
    qrows = _q_rows(test, keys, fit["_q"], len(_score_cols(sim)))
    acc = _accept(test, _mhat_cols(sim), qrows, float(fit["kappa"]))
    wrong = test["wrong"].to_numpy(bool)

    codes, uniq = pd.factorize(test["block_id"].to_numpy(), sort=True)
    nb = len(uniq)
    return {
        "block_ids": np.asarray(uniq),
        "n_rows": np.bincount(codes, minlength=nb).astype(np.float64),
        "n_acc": np.bincount(codes, weights=acc.astype(np.float64), minlength=nb),
        "n_wrong_acc": np.bincount(
            codes, weights=(acc & wrong).astype(np.float64), minlength=nb
        ),
    }


def curve_from_stats(
    stats_by_kappa: Sequence[Mapping[str, np.ndarray]],
    picks: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Dung (acceptance, err|accept) cho MOT draw. picks=None -> tap test goc."""
    accs, errs = [], []
    for st in stats_by_kappa:
        if picks is None:
            n, a, w = st["n_rows"].sum(), st["n_acc"].sum(), st["n_wrong_acc"].sum()
        else:
            n = st["n_rows"][picks].sum()
            a = st["n_acc"][picks].sum()
            w = st["n_wrong_acc"][picks].sum()
        accs.append(a / n if n > 0 else float("nan"))
        errs.append(w / a if a > 0 else float("nan"))
    return np.asarray(accs, np.float64), np.asarray(errs, np.float64)


def build_stats(
    calib: pd.DataFrame,
    test: pd.DataFrame,
    config: str,
    kappas: Sequence[float],
    alpha: float = ALPHA,
    multiplicity: str = "bonferroni",
) -> list[Dict[str, np.ndarray]]:
    """Hieu chuan qhat MOT LAN moi kappa (CO DINH -- B-D7), roi rut thong ke du."""
    out = []
    for kappa in kappas:
        fit = fit_config(calib, config, float(kappa), alpha=alpha,
                         multiplicity=multiplicity)
        st = block_sufficient_stats(test, fit)
        st["kappa"] = float(kappa)
        st["qhat_slot1_mean"] = float(np.mean([float(v[0]) for v in fit["_q"].values()]))
        out.append(st)
    return out


# ---------------------------------------------------------------------------
# 4. Paired block bootstrap
# ---------------------------------------------------------------------------

def paired_bootstrap_ratio(
    stats_num: Sequence[Mapping[str, np.ndarray]],
    stats_den: Sequence[Mapping[str, np.ndarray]],
    n_boot: int = N_BOOT,
    seed: int = SEED_BOOT,
    lo: float = WINDOW_LO,
    hi: float = WINDOW_HI,
    n_grid: int = WINDOW_N,
    scale_num: float = 1.0,
) -> Dict[str, Any]:
    """CI95 cua ti so AURC bang paired block bootstrap tren tap TEST.

    GHEP CAP: MOT `picks` duy nhat moi draw, dung cho CA tu so lan mau so.
    Ghep cap triet tieu nhieu chung ("tap test nay tinh co kho/de"), chi de lai
    khac biet giua hai THU TUC. Neu quen dung chung picks, CI phong ~sqrt(2)
    va co the lat ket luan GO-1 -- do la thu NC-A-1 bat.

    scale_num: chi dung cho doi chung duong PC-A-1 (nhan err|accept cua tu so).
    """
    nb = len(stats_den[0]["n_rows"])
    if len(stats_num[0]["n_rows"]) != nb:
        raise ValueError("tu so va mau so phai co CUNG tap block")

    rng = np.random.default_rng(int(seed))
    ratios, a_num, a_den, failed = [], [], [], 0

    for _ in range(int(n_boot)):
        picks = rng.integers(0, nb, size=nb)          # MOT picks cho CA HAI
        xn, yn = curve_from_stats(stats_num, picks)
        xd, yd = curve_from_stats(stats_den, picks)
        rn = aurc_window(xn, yn * float(scale_num), lo, hi, n_grid, strict=False)
        rd = aurc_window(xd, yd, lo, hi, n_grid, strict=False)
        if not (np.isfinite(rn["aurc"]) and np.isfinite(rd["aurc"]) and rd["aurc"] > 0):
            failed += 1
            continue
        a_num.append(rn["aurc"])
        a_den.append(rd["aurc"])
        ratios.append(rn["aurc"] / rd["aurc"])

    arr = np.asarray(ratios, np.float64)
    frac_failed = failed / float(n_boot)
    if arr.size == 0:
        raise ValueError("moi draw deu hong (%d/%d)" % (failed, n_boot))

    an, ad = np.asarray(a_num), np.asarray(a_den)
    return {
        "n_boot": int(n_boot),
        "n_draws_used": int(arr.size),
        "n_draws_failed": int(failed),
        "frac_draws_failed": float(frac_failed),
        "pass_failed_draw_budget": bool(frac_failed <= MAX_FAILED_DRAW_FRAC),
        "ratio_mean": float(arr.mean()),
        "ratio_sd": float(arr.std(ddof=1)) if arr.size > 1 else float("nan"),
        "ci95_low": float(np.quantile(arr, 0.025)),
        "ci95_high": float(np.quantile(arr, 0.975)),
        "ci95_width": float(np.quantile(arr, 0.975) - np.quantile(arr, 0.025)),
        "aurc_num_ci95": [float(np.quantile(an, 0.025)), float(np.quantile(an, 0.975))],
        "aurc_den_ci95": [float(np.quantile(ad, 0.025)), float(np.quantile(ad, 0.975))],
        # tuong quan cao => ghep cap dang lam viec
        "corr_num_den": float(np.corrcoef(an, ad)[0, 1]) if an.size > 2 else float("nan"),
        "seed": int(seed),
        "paired": True,
        "scale_num": float(scale_num),
    }


# So seed de UOC LUONG mc_sd. Do lech chuan cua mot uoc luong do lech chuan co
# sai so tuong doi ~ 1/sqrt(2(n-1)): n=10 -> 23.6%, n=30 -> 13.1%. Ti so cua
# HAI do lech chuan vi vay co sai so ~33% o n=10, khong du de phan biet 1.8 voi
# 3.16 -- tuc chinh nguong cua gate. n=30 dua sai so xuong ~19%.
# Do duoc tren poisson@0.850: n=10 cho shrink 1.798 (FAIL), n=30 cho 2.333.
# NGUONG khong doi; chi do chinh xac cua PHEP DO duoc sua.
MC_N_SEEDS = 30
MC_WIDTH_STABLE_TOL = 0.10
MC_MIN_ERROR_SHRINK = 1.8


def mc_convergence(
    stats_num,
    stats_den,
    ladder: Sequence[int] = B_LADDER,
    seed: int = SEED_BOOT,
    n_seeds: int = MC_N_SEEDS,
) -> Dict[str, Any]:
    """Hoi tu Monte Carlo cua bootstrap. Hai kiem tra, va chung KHAC NHAU.

    CANH BAO VE MOT TIEU CHI SAI THUONG GAP
    ---------------------------------------
    Do rong CI **KHONG** co theo 1/sqrt(B). Khi B -> vo cung, CI hoi tu ve
    phan vi 2.5-97.5 cua phan phoi bootstrap THAT, va do rong do duoc dinh boi
    so BLOCK (o day 500), khong phai boi B. Do duoc: width 0.01154 (B=200) ->
    0.01201 (B=2000) -- gan nhu HANG SO, dung nhu ly thuyet.

    Thu co theo 1/sqrt(B) la SAI SO MONTE CARLO cua hai dau mut, do bang do
    lech chuan cua `ci95_high` GIUA CAC SEED.

    Neu ai do ap tieu chi "width ~ 1/sqrt(B)", mot bootstrap DUNG se FAIL, va
    "sua" code cho qua nghia la lam hong bootstrap.

    Kiem tra 1  width_stabilises : |w(B_max) - w(B_prev)| / w(B_max) <= 0.10
    Kiem tra 2  mc_error_shrinks : sd(ci95_high) o B_min / o B_max >= 1.8
                                   (ly thuyet du bao sqrt(B_max/B_min) = 3.16)
    """
    rows = []
    for b in ladder:
        widths, highs, lows = [], [], []
        for s in range(int(n_seeds)):
            r = paired_bootstrap_ratio(
                stats_num, stats_den, n_boot=int(b), seed=int(seed) + 100 * s
            )
            widths.append(r["ci95_width"])
            highs.append(r["ci95_high"])
            lows.append(r["ci95_low"])
        rows.append({
            "B": int(b),
            "n_seeds": int(n_seeds),
            "ci95_width_mean": float(np.mean(widths)),
            "ci95_high_mean": float(np.mean(highs)),
            "ci95_low_mean": float(np.mean(lows)),
            "mc_sd_ci95_high": float(np.std(highs, ddof=1)),
            "mc_sd_ci95_low": float(np.std(lows, ddof=1)),
        })

    base, top, prev = rows[0], rows[-1], rows[-2] if len(rows) > 1 else rows[-1]
    width_change = abs(top["ci95_width_mean"] - prev["ci95_width_mean"]) / max(
        top["ci95_width_mean"], 1e-12
    )
    shrink = base["mc_sd_ci95_high"] / max(top["mc_sd_ci95_high"], 1e-12)
    expected_shrink = float(np.sqrt(top["B"] / base["B"]))
    for row in rows:
        row["expected_mc_sd_1_over_sqrtB"] = float(
            base["mc_sd_ci95_high"] * np.sqrt(base["B"] / row["B"])
        )
        row["observed_over_expected"] = float(
            row["mc_sd_ci95_high"] / max(row["expected_mc_sd_1_over_sqrtB"], 1e-12)
        )
    return {
        "ladder": rows,
        "width_relative_change_top_two": float(width_change),
        "pass_width_stabilises": bool(width_change <= MC_WIDTH_STABLE_TOL),
        "mc_error_shrink_factor": float(shrink),
        "mc_error_shrink_expected": expected_shrink,
        "pass_mc_error_shrinks": bool(shrink >= MC_MIN_ERROR_SHRINK),
        "pass": bool(width_change <= MC_WIDTH_STABLE_TOL and shrink >= MC_MIN_ERROR_SHRINK),
        "note": (
            "Do rong CI hoi tu ve HANG SO (dinh boi so block), KHONG co theo "
            "1/sqrt(B). Thu co theo 1/sqrt(B) la SAI SO MC cua dau mut."
        ),
    }


# ---------------------------------------------------------------------------
# 5. Doi chung tu than  (NT-v2-2)
# ---------------------------------------------------------------------------

def negative_control_self_ratio(stats_den, n_boot: int = 200, seed: int = SEED_BOOT):
    """NC-A-1: C0 vs CHINH C0, cung draw -> ratio = 1.0 CHINH XAC moi draw.
    Do rong CI > 0  <=>  ghep cap bi hong (draw khong thuc su dung chung)."""
    r = paired_bootstrap_ratio(stats_den, stats_den, n_boot=n_boot, seed=seed)
    return {"control": "NC-A-1", "ci95_width": r["ci95_width"],
            "ratio_mean": r["ratio_mean"], "max_abs_dev_from_1": float(
                max(abs(r["ci95_low"] - 1.0), abs(r["ci95_high"] - 1.0))),
            "pass": bool(r["ci95_width"] <= 1e-12
                         and abs(r["ratio_mean"] - 1.0) <= 1e-12)}


def positive_control_shift(stats_num, stats_den, shift: float = 1.10,
                           n_boot: int = N_BOOT, seed: int = SEED_BOOT + 1):
    """PC-A-1: nhan err|accept cua tu so len `shift`.
    CI95 PHAI loai tru GO1_THRESHOLD va bao quanh ~ shift.
    Neu khong loai tru -> B chua du hoac CI tinh sai."""
    r = paired_bootstrap_ratio(stats_num, stats_den, n_boot=n_boot, seed=seed,
                               scale_num=float(shift))
    return {"control": "PC-A-1", "shift": float(shift),
            "ratio_mean": r["ratio_mean"],
            "ci95": [r["ci95_low"], r["ci95_high"]],
            "excludes_threshold": bool(r["ci95_low"] > GO1_THRESHOLD),
            "pass": bool(r["ci95_low"] > GO1_THRESHOLD)}


def grid_adequacy(rn: Mapping[str, Any], rd: Mapping[str, Any]) -> Dict[str, Any]:
    """B-D14. Luoi mit phai LAM GI DO, neu khong no la trang tri."""
    knots = min(int(rn["n_knots_in_window"]), int(rd["n_knots_in_window"]))
    widest = max(float(rn["widest_segment_in_window"]),
                 float(rd["widest_segment_in_window"]))
    return {
        "min_knots_in_window": knots,
        "max_widest_segment": widest,
        "pass_min_knots": bool(knots >= MIN_KNOTS_IN_WINDOW),
        "pass_max_segment": bool(widest < MAX_SEGMENT_IN_WINDOW),
        "pass": bool(knots >= MIN_KNOTS_IN_WINDOW and widest < MAX_SEGMENT_IN_WINDOW),
    }


# ---------------------------------------------------------------------------
# 6. Mot cell dau-den-cuoi
# ---------------------------------------------------------------------------

def run_cell(
    df: pd.DataFrame,
    alpha: float = ALPHA,
    multiplicity: str = "bonferroni",
    n_boot: int = N_BOOT,
) -> Dict[str, Any]:
    calib = df[df["is_calib"].to_numpy(bool)]
    test = df[~df["is_calib"].to_numpy(bool)]
    anchor_err = float(test["wrong"].to_numpy(bool).mean())

    # ---- B-D5: suy bien -> KHONG tinh ratio, ghi trang thai -----------------
    if anchor_err < DEGENERATE_ERR:
        return {
            "status": "DEGENERATE",
            "err_neo": anchor_err,
            "degenerate_threshold": float(DEGENERATE_ERR),
            "ratio": None, "ci95": None,
            "reason": ("err_neo = %.6f < %.2f: nhiem vu quyet dinh khong co do "
                       "kho, duong risk-coverage suy bien ve 0."
                       % (anchor_err, DEGENERATE_ERR)),
        }

    out: Dict[str, Any] = {"status": "EVALUABLE", "err_neo": anchor_err,
                           "alpha": float(alpha), "multiplicity": multiplicity}

    for grid_name, kappas in (("primary", KAPPA_PRIMARY), ("refined", KAPPA_REFINED)):
        sn = build_stats(calib, test, CONFIG_NUM, kappas, alpha, multiplicity)
        sd = build_stats(calib, test, CONFIG_DEN, kappas, alpha, multiplicity)

        xn, yn = curve_from_stats(sn)
        xd, yd = curve_from_stats(sd)
        rn = aurc_window(xn, yn, strict=True)          # B-D4: RAISE neu ngoai suy
        rd = aurc_window(xd, yd, strict=True)
        ratio = rn["aurc"] / rd["aurc"]

        boot = paired_bootstrap_ratio(sn, sd, n_boot=n_boot)
        block = {
            "kappas": [float(k) for k in kappas],
            "aurc_%s" % CONFIG_NUM: rn,
            "aurc_%s" % CONFIG_DEN: rd,
            "ratio_point": float(ratio),
            "bootstrap": boot,
            "grid_adequacy": grid_adequacy(rn, rd),
            "go1_pass_on_ci_high": bool(boot["ci95_high"] < GO1_THRESHOLD),
            "go1_pass_on_point_only": bool(ratio < GO1_THRESHOLD),
        }
        if grid_name == "refined":
            block["NC_A_1"] = negative_control_self_ratio(sd)
            block["PC_A_1"] = positive_control_shift(sn, sd)
            block["mc_convergence"] = mc_convergence(sn, sd)
        out["grid_%s" % grid_name] = block

    p = out["grid_primary"]["ratio_point"]
    r = out["grid_refined"]["ratio_point"]
    out["discretisation_bias"] = float(r - p)          # A-7', A-8'
    out["decision_grid"] = "refined"                   # B-D13
    out["ratio"] = r
    out["ci95"] = [out["grid_refined"]["bootstrap"]["ci95_low"],
                   out["grid_refined"]["bootstrap"]["ci95_high"]]
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--calib", required=True, help="parquet calib_set_v3_<cell>")
    p.add_argument("--out", required=True)
    p.add_argument("--alpha", type=float, default=ALPHA)
    p.add_argument("--multiplicity", default="bonferroni",
                   choices=("bonferroni", "sidak"))
    p.add_argument("--n-boot", type=int, default=N_BOOT)
    args = p.parse_args()

    df = pd.read_parquet(args.calib)
    res = run_cell(df, alpha=args.alpha, multiplicity=args.multiplicity,
                   n_boot=args.n_boot)
    res.update(
        cell=os.path.basename(args.calib),
        n_rows=int(len(df)),
        n_blocks=int(df["block_id"].nunique()),
        provenance={
            "script": "cert/aurc_go1.py",
            "calib": args.calib,
            "git_hash": _git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(_git("git", "status", "--porcelain")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "WINDOW": [WINDOW_LO, WINDOW_HI], "WINDOW_N": WINDOW_N,
            "GO1_THRESHOLD": GO1_THRESHOLD, "N_BOOT": int(args.n_boot),
            "SEED_BOOT": SEED_BOOT,
            "KAPPA_PRIMARY": list(KAPPA_PRIMARY),
            "KAPPA_REFINED": list(KAPPA_REFINED),
            "amendments": ["docs/phase-23/00w-amendment-22.md",
                           "docs/phase-23/00x-amendment-23.md"],
            "env": {"pandas": pd.__version__, "numpy": np.__version__},
        },
    )
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, sort_keys=True, default=float)
        f.write("\n")

    if res["status"] == "DEGENERATE":
        print("DEGENERATE  err_neo=%.6f  -> khong tinh ratio" % res["err_neo"])
        return
    for g in ("primary", "refined"):
        b = res["grid_%s" % g]
        print("%-8s ratio=%.6f  CI95=[%.6f, %.6f]  knots_in_window=%d/%d  "
              "widest_seg=%.4f"
              % (g, b["ratio_point"], b["bootstrap"]["ci95_low"],
                 b["bootstrap"]["ci95_high"],
                 b["aurc_%s" % CONFIG_NUM]["n_knots_in_window"],
                 b["aurc_%s" % CONFIG_DEN]["n_knots_in_window"],
                 b["aurc_%s" % CONFIG_NUM]["widest_segment_in_window"]))
    print("discretisation_bias = %+.6f" % res["discretisation_bias"])
    rb = res["grid_refined"]
    print("grid adequacy (B-D14): %s" % rb["grid_adequacy"]["pass"])
    print("NC-A-1 width=%.3e pass=%s | PC-A-1 CI=%s pass=%s | MC shrink=%.2fx pass=%s"
          % (rb["NC_A_1"]["ci95_width"], rb["NC_A_1"]["pass"],
             [round(x, 4) for x in rb["PC_A_1"]["ci95"]], rb["PC_A_1"]["pass"],
             rb["mc_convergence"]["mc_error_shrink_factor"],
             rb["mc_convergence"]["pass"]))
    print("corr(num,den) = %.6f   (ghep cap hoat dong khi gan 1)"
          % rb["bootstrap"]["corr_num_den"])
    print("GO-1 tren CI_high: %s" % rb["go1_pass_on_ci_high"])


if __name__ == "__main__":
    main()
