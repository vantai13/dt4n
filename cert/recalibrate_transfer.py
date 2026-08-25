#!/usr/bin/env python3
"""Lesson 23.22 / Task B-3 -- tai hieu chuan qua che do, va menh de bao toan.

Ky truoc o `docs/phase-23/A068-amendment-68.md`, tag `lesson-23-22-b3-prereg`.

Task B do cai conformal KHONG hua (mang nguyen `qhat` sang che do khac).
Task B-3 do cai no CO hua:

    cho toi du lieu CO NHAN cua phan phoi moi, toi tra bao phu dung,
    KHONG can mo hinh dung.

va do CAI GIA cua loi hua do o hai chieu chua ai do: `n` HUU HAN, va tham so
thiet ke `kappa` MANG TU CHE DO CU.

Thiet ke DOI XUNG -- moi ben mang MOT so, tai uoc luong MOT thong ke:

    C3-R    mang `kappa_A` (khong thu nguyen)   uoc luong lai `qhat`  (phan vi DUOI)
    B2-R    mang `a*`      (muc tieu acceptance) uoc luong lai `c`    (phan vi TRUNG TAM)
    B1-R    mang `a*`                            `c` tren score NGAU NHIEN

MENH DE BAO TOAN (muc 1.2 cua `A068`):

    C3-R :  GIU  viol|accept ~ alpha      DE TROI  acceptance
    B2-R :  GIU  acceptance = a*          DE TROI  err|accept

===========================================================================
SAU CAI BAY DA BIET, VA CHOT CHAN CHO TUNG CAI   (`A068` muc 2, 3.2, 3.3)
---------------------------------------------------------------------------
1. Thang bi TOI DA HOA boi mot quy tac khong nhin du lieu   (`NC-2`, `L99`)
   -> acceptance drift cua B2-R KHONG duoc cham diem (S-3).
      `NC-B3-1` bat buoc phai FIRE.
2. Dai HAI PHIA quanh alpha tron "bao thu" voi "vo"          (`M-195`)
   -> HAI nguong rieng + san acceptance 0.20.
3. "0 vi pham" dat duoc bang `n_accept = 0`                   (doc 44/45)
   -> census rieng; KHONG BAO GIO dem la 0.
4. Ky mot du doan ma dap an da nam trong artifact       (`M-194`, `M-193`)
   -> `M-200` bi HA xuong KIEM WIRING.
5. Muon `qhat` cua C3 cho B2 de "so cho cong bang"     (`A066` muc 3)
   -> KHONG ghi `viol` cho B2. O TRONG chinh la ket qua.
6. Co chan doan MU o vung giao cua hai co che suy bien        (`L100`)
   -> dung `qhat_source`, khong dung hai co cu.
===========================================================================

Chay:
    python -m cert.recalibrate_transfer --pilot     # muc 4, DA CHAY, da commit
    python -m cert.recalibrate_transfer --wiring    # NC-B3-0 + NC-B3-2 truoc
    python -m cert.recalibrate_transfer --run
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

from cert import baselines as BL
from cert import config_matrix as CM
from cert import recalibration_cost as RC
from cert import transfer_matrix as TM
from cert.build_calib_set_v3 import AOI_V7, Z_EDGES_V7
from cert.cell_matrices import ALPHA_FAMILY, git, json_clean, pin
from cert.taxonomy_audit import SLA_MANIFEST, W_LOSS
from measurements.validity import validity_block

AMENDMENT = "docs/phase-23/A068-amendment-68.md"
PILOT_OUT = "results/LIVE/phase-23/recalibrate_transfer_pilot.json"
OUTPUT = "results/LIVE/phase-23/recalibrate_transfer.json"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

POST_VARIANT = TM.POST_VARIANT           # "selective"
MULTIPLICITY = TM.MULTIPLICITY           # "bonferroni"
KAPPA_OP = TM.KAPPA_OP                   # 0.50 -- diem van hanh cua Task B

# `a*` -- MOT LUA CHON THIET KE, khai o `A068` muc 1.1 va muc 9 (`N2`).
# Bang so: `taxonomy_audit.json::cells[].variant_sweep[post=selective,
# kappa=0.5].acceptance`, trung binh tren 8 cell SONG.
A_STAR = 0.42679

# Bisection cho `kappa_A`. Can tren 8 la mot lua chon thiet ke: luoi
# `variant_sweep` chi den `kappa = 2`, va o cell CHET acceptance tai
# `kappa = 2` van gan 1.
KAPPA_LO, KAPPA_HI = 0.0, 8.0
KAPPA_TOL_ACC = 1e-4                     # dung sai tren ACCEPTANCE
KAPPA_TOL_WIDTH = 1e-6                   # dung sai tren be rong khoang
KAPPA_MAX_ITER = 45

# -- Nhanh R (`A068` muc 3) ------------------------------------------------
N_GRID = (30, 60, 120, 250, 500)         # 30 ngay tren san hop le 29 (`L91`)
N_DRAWS = 10
SEED = 232301
SEED_B1 = TM.SEED_B1                     # 23301 -- CUNG hat giong voi Task B

N_MAIN = 250          # muc `n` ma `M-201`/`M-203`/`M-205`/`M-206` duoc cham
N_FULL = 500          # muc `n` ma `M-200`/`M-202` duoc cham
ACCEPT_FLOOR = 0.20   # san acceptance, BAT BUOC cho moi phat bieu ve `viol`
BREAK_TOL = 0.05      # `viol > alpha + 0.05` = VO   (`A068` muc 3.2)
MATCHED_ACCEPTANCE = TM.MATCHED_ACCEPTANCE     # (0.70, 0.50, 0.30, 0.15)


# ---------------------------------------------------------------------------
# `_q_rows` nhanh -- CUNG SO, khong phai cung duong di
# ---------------------------------------------------------------------------

def key_index(df: pd.DataFrame, keys: Sequence[str]) -> Tuple[list, np.ndarray]:
    """Bang tra `(khoa duy nhat, chi so hang)` -- tinh MOT LAN cho moi cell B.

    `CM._q_rows` dung lai `CM._row_keys` cho MOI lan chay, tuc dung 500k
    tuple Python cho moi trong 3280 lan fit. O day khoa cua `test` KHONG doi
    trong suot mot cell B; chi `qhat` doi. Tach phan bat bien ra.
    """
    row_keys = CM._row_keys(df, list(keys))
    uniq = sorted(set(row_keys))
    pos = {k: i for i, k in enumerate(uniq)}
    idx = np.fromiter((pos[k] for k in row_keys), dtype=np.int64,
                      count=len(row_keys))
    return uniq, idx


def q_rows_from_index(uniq: Sequence[Any], idx: np.ndarray,
                      q: Dict[Any, np.ndarray], n_cols: int) -> np.ndarray:
    """Tra ve DUNG mang ma `CM._q_rows(df, keys, q, n_cols)` tra ve.

    Ghim boi `test_fast_q_rows_is_bit_identical_to_config_matrix`. Neu mot
    ngay nao do `CM._q_rows` doi, test do FAIL -- do la muc dich cua no. Mot
    duong ong thu hai duoc phep ton tai chi khi co mot test buoc no trung BIT
    voi duong ong thu nhat.
    """
    miss = np.full(int(n_cols), np.inf, dtype=np.float64)
    tab = np.vstack([np.asarray(q.get(k, miss), dtype=np.float64) for k in uniq])
    return tab[idx]


def _err_at_coverage(order: np.ndarray, wrong: np.ndarray,
                     coverage: float) -> float:
    """`err|accept` khi EP dung ti le chap nhan `coverage`, dung thu tu cho san.

    Cung phep chon `top-k` voi `BL._accept_at_coverage` (`k = floor(c*n+0.5)`,
    `argsort(-s, kind="mergesort")`); chi khac o cho thu tu duoc tinh mot lan
    roi dung lai cho ca bon muc. Ghim boi
    `test_err_at_coverage_matches_baselines_accept_at_coverage`.
    """
    n = int(len(order))
    k = max(0, min(n, int(np.floor(float(coverage) * n + 0.5))))
    if k == 0:
        return float("nan")
    return float(wrong[order[:k]].mean())


# ---------------------------------------------------------------------------
# `kappa_A` -- giai tren CALIB cua A
# ---------------------------------------------------------------------------

def acceptance_at_kappa(calib: pd.DataFrame, kappa: float) -> Tuple[float, Dict[str, Any]]:
    """Acceptance cua C3 tren chinh `calib`, tai mot `kappa`.

    Dung DUNG duong ong cua `TM.fit_on_A`: `fit_config` roi `_q_rows` roi
    `_accept`. Viet lai mot phep do acceptance thu hai la cach tao ra hai
    duong ong co the lech nhau ma khong ai biet.
    """
    fit = CM.fit_config(calib, "C3", float(kappa), alpha=ALPHA_FAMILY,
                        post_variant=POST_VARIANT, multiplicity=MULTIPLICITY)
    keys = CM._keys(POST_VARIANT)
    q_rows = CM._q_rows(calib, keys, fit["_q"], len(CM.SIM_COLS))
    acc = float(CM._accept(calib, CM.MHAT_COLS, q_rows, float(kappa)).mean())
    return acc, fit


def solve_kappa(calib: pd.DataFrame, target: float = A_STAR,
                lo: float = KAPPA_LO, hi: float = KAPPA_HI) -> Dict[str, Any]:
    """Bisection tren `[lo, hi]` cho acceptance(kappa) = `target`.

    acceptance(kappa) la mot ham BAC THANG cua mau huu han, nen `1e-4` co the
    khong voi toi duoc. Bisection giu lai diem TOT NHAT da gap va dung khi
    khoang co be hon `KAPPA_TOL_WIDTH`; ca hai dieu kien dung deu duoc ghi.
    """
    a_lo, fit_lo = acceptance_at_kappa(calib, lo)
    a_hi, fit_hi = acceptance_at_kappa(calib, hi)
    trace = [{"kappa": float(lo), "acceptance": a_lo},
             {"kappa": float(hi), "acceptance": a_hi}]

    best = min(((abs(a_lo - target), float(lo), a_lo, fit_lo),
                (abs(a_hi - target), float(hi), a_hi, fit_hi)),
               key=lambda t: t[0])
    bracketed = bool((a_lo - target) * (a_hi - target) <= 0.0)

    n_iter = 0
    if bracketed:
        x_lo, x_hi, y_lo = float(lo), float(hi), a_lo
        for n_iter in range(1, KAPPA_MAX_ITER + 1):
            mid = 0.5 * (x_lo + x_hi)
            a_mid, fit_mid = acceptance_at_kappa(calib, mid)
            trace.append({"kappa": float(mid), "acceptance": a_mid})
            if abs(a_mid - target) < best[0]:
                best = (abs(a_mid - target), float(mid), a_mid, fit_mid)
            if abs(a_mid - target) <= KAPPA_TOL_ACC:
                break
            if (y_lo - target) * (a_mid - target) <= 0.0:
                x_hi = mid
            else:
                x_lo, y_lo = mid, a_mid
            if (x_hi - x_lo) <= KAPPA_TOL_WIDTH:
                break

    err, kappa, acc, fit = best
    return {
        "kappa_A": float(kappa),
        "acceptance_at_kappa_A": float(acc),
        "abs_error": float(err),
        "bracketed": bracketed,
        "converged_on_acceptance": bool(err <= KAPPA_TOL_ACC),
        "n_iter": int(n_iter),
        "acceptance_at_lo": float(a_lo),
        "acceptance_at_hi": float(a_hi),
        "qhat_source": fit.get("qhat_source"),
        "qhat_has_infinite": bool(fit.get("qhat_has_infinite", False)),
        "qhat_at_sample_max": bool(fit.get("qhat_at_sample_max", False)),
        "min_blocks_at_final_qhat": fit.get("min_blocks_at_final_qhat"),
        "degenerate": bool(fit.get("degenerate", False)),
        "n_iter_fit": int(fit.get("n_iter", 0)),
        "trace": trace,
    }


# ---------------------------------------------------------------------------
# PILOT
# ---------------------------------------------------------------------------

def pilot() -> Dict[str, Any]:
    """`A068` muc 4. Chay TRUOC khi ky muc 5; ket qua duoc commit vao muc 4."""
    live, dead = TM.cells_by_role()
    ref = TM._diag_reference()          # hang V-S @ kappa=0.5, DA DO
    rows: list[Dict[str, Any]] = []
    for role, cells in (("live", live), ("dead", dead)):
        for cell in cells:
            calib, _test, _p = TM.load_cell(cell)
            r = solve_kappa(calib)
            r["cell"] = cell
            r["role"] = role
            r["n_calib_blocks"] = int(calib["block_id"].nunique())
            r["n_calib_rows"] = int(len(calib))
            r["acceptance_at_kappa_0_50"] = (
                float(ref[cell]["acceptance"]) if cell in ref else float("nan"))
            rows.append(r)
            del calib

    # CHAN DUNG (`A068` muc 4): tren cell SONG, `kappa_A` phai ton tai trong
    # [0, 8] VA `fit_config` khong duoc sup ve `none` tai `kappa_A`.
    stop: list[str] = []
    for r in rows:
        if r["role"] != "live":
            continue
        if not r["bracketed"]:
            stop.append("%s: kappa_A khong ton tai trong [%.1f, %.1f] "
                        "(acc %.4f -> %.4f)" % (r["cell"], KAPPA_LO, KAPPA_HI,
                                                r["acceptance_at_lo"],
                                                r["acceptance_at_hi"]))
        if r["qhat_source"] == "degenerate_fallback_to_none":
            stop.append("%s: qhat_source = degenerate_fallback_to_none tai "
                        "kappa_A = %.6f (`L95`)" % (r["cell"], r["kappa_A"]))

    return {
        "schema": "dt4n.recalibrate_transfer_pilot.v1",
        "lesson": "23.22",
        "task": "B-3 PILOT",
        "amendment": AMENDMENT,
        "config": {
            "a_star": A_STAR, "kappa_lo": KAPPA_LO, "kappa_hi": KAPPA_HI,
            "kappa_tol_acceptance": KAPPA_TOL_ACC,
            "kappa_tol_width": KAPPA_TOL_WIDTH,
            "kappa_max_iter": KAPPA_MAX_ITER,
            "post_variant": POST_VARIANT, "multiplicity": MULTIPLICITY,
            "alpha_family": ALPHA_FAMILY,
        },
        "rows": rows,
        "stop_rule_violations": stop,
        "validity": validity_block(
            aoi_generator=AOI_V7,
            z_edges=Z_EDGES_V7,
            sla_path=SLA_MANIFEST,
            w_loss=W_LOSS,
        ),
        "provenance": {
            "script": "cert/recalibrate_transfer.py::pilot",
            "git_hash": git("git", "rev-parse", "HEAD"),
            "git_dirty": git("git", "status", "--porcelain") != "",
            "utc": datetime.now(timezone.utc).isoformat(),
        },
    }


def print_pilot(out: Dict[str, Any]) -> None:
    print("a* = %.5f   (acceptance trung binh 8 cell song @ kappa=0.5)"
          % out["config"]["a_star"])
    print("%-16s %5s %10s %9s %11s %26s %11s"
          % ("cell", "role", "acc@k=.50", "kappa_A", "acc@kappa_A",
             "qhat_source@kappa_A", "min_blocks"))
    for r in out["rows"]:
        print("%-16s %5s %10.4f %9.4f %11.4f %26s %11s"
              % (r["cell"], r["role"], r["acceptance_at_kappa_0_50"],
                 r["kappa_A"], r["acceptance_at_kappa_A"],
                 str(r["qhat_source"]), str(r["min_blocks_at_final_qhat"])))
    ks = [r["kappa_A"] for r in out["rows"] if r["role"] == "live"]
    print("\nkappa_A tren 8 cell SONG: min %.4f  trung vi %.4f  max %.4f  "
          "ti so max/min %.2fx"
          % (min(ks), float(np.median(ks)), max(ks), max(ks) / max(min(ks), 1e-12)))
    if out["stop_rule_violations"]:
        print("\n!! CHAN DUNG:")
        for s in out["stop_rule_violations"]:
            print("   %s" % s)
    else:
        print("chan dung: KHONG co vi pham -- duoc phep ky muc 5")


# ---------------------------------------------------------------------------
# Nhanh R -- mot lan chay la mot bo (A, B, n, draw)
# ---------------------------------------------------------------------------

def load_kappa_A(path: str = PILOT_OUT) -> Dict[str, float]:
    """`kappa_A` doc THANG tu artifact pilot -- khong giai lai.

    Ky thuat cua `G23-247`: mot dai luong da do va da commit thi doc lai,
    khong chay lai. Giai lai ton 11 phut VA mo cua cho hai gia tri `kappa_A`
    khac nhau ton tai trong cung mot do an.
    """
    full = path if os.path.isabs(path) else os.path.join(REPO, path)
    if not os.path.exists(full):
        raise FileNotFoundError(
            "thieu artifact PILOT: %s -- chay `--pilot` truoc (`A068` muc 4)"
            % path)
    with open(full, encoding="utf-8") as fh:
        art = json.load(fh)
    if float(art["config"]["a_star"]) != A_STAR:
        raise RuntimeError("pilot chay voi a* = %r, module dang dung %r"
                           % (art["config"]["a_star"], A_STAR))
    if art["stop_rule_violations"]:
        raise RuntimeError("pilot co vi pham chan dung: %s"
                           % art["stop_rule_violations"])
    return {r["cell"]: float(r["kappa_A"]) for r in art["rows"]}


def prepare_test(test_B: pd.DataFrame) -> Dict[str, Any]:
    """Phan BAT BIEN cua mot cell B: tinh mot lan, dung cho 8 x 41 lan chay."""
    uniq, idx = key_index(test_B, CM._keys(POST_VARIANT))
    m1 = test_B["m_hat_1"].to_numpy(np.float64)
    return {
        "df": test_B,
        "uniq": uniq, "idx": idx,
        "mhat": test_B[list(CM.MHAT_COLS)].to_numpy(np.float64),
        "s": test_B[list(CM.SIM_COLS)].to_numpy(np.float64),
        "wrong": test_B["wrong"].to_numpy(bool),
        "m1": m1,
        "b1": BL.score_B1_random(test_B, seed=SEED_B1),
        "order_b2": np.argsort(-m1, kind="mergesort"),
        "n_rows": int(len(test_B)),
        "anchor_err": float(test_B["wrong"].mean()),
    }


def run_one(sub: pd.DataFrame, tv: Mapping[str, Any], kappa_A: float,
            matched: bool = False) -> Dict[str, Any]:
    """Mot lan chay: BA thu tuc tren CUNG `n` block cua B (CRN).

    B2-R va B1-R duoc tinh LAI trong vong lap A du chung KHONG phu thuoc A
    (S-2). Tinh mot lan roi chep sang 8 o se lam `NC-B3-2` thanh mot phep
    kiem VO NGHIA: no se trung bit vi ta da chep, khong vi thu tuc doc lap A.
    Gia phai tra la hai `np.quantile` -- vai mili giay.
    """
    kap = float(kappa_A)
    fit = CM.fit_config(sub, "C3", kap, alpha=ALPHA_FAMILY,
                        post_variant=POST_VARIANT, multiplicity=MULTIPLICITY)
    q_rows = q_rows_from_index(tv["uniq"], tv["idx"], fit["_q"],
                               len(CM.SIM_COLS))
    acc_c3 = (tv["mhat"] >= kap * q_rows).all(axis=1)
    viol = (tv["s"] > q_rows).any(axis=1)
    n_acc = int(acc_c3.sum())

    # -- B2-R: `c` de trung `a*` tren CHINH `n` block do
    c = RC.fit_B2(sub, A_STAR)
    acc_b2 = tv["m1"] >= c
    # -- B1-R: CUNG phep dat nguong, tren score NGAU NHIEN  (`NC-2`)
    c_b1 = float(np.quantile(BL.score_B1_random(sub, seed=SEED_B1),
                             1.0 - A_STAR, method="higher"))
    acc_b1 = tv["b1"] >= c_b1

    def _m(mask: np.ndarray, v: np.ndarray) -> float:
        return float(v[mask].mean()) if mask.any() else float("nan")

    row: Dict[str, Any] = {
        "n_blocks": int(sub["block_id"].nunique()),
        "kappa_used": kap,
        # -- C3-R
        "C3_qhat_source": fit.get("qhat_source"),
        "C3_qhat_has_infinite": bool(fit.get("qhat_has_infinite", False)),
        "C3_qhat_at_sample_max": bool(fit.get("qhat_at_sample_max", False)),
        "C3_min_blocks_at_final_qhat": fit.get("min_blocks_at_final_qhat"),
        "C3_degenerate": bool(fit.get("degenerate", False)),
        "C3_n_iter": int(fit.get("n_iter", 0)),
        "C3_acceptance_test": float(acc_c3.mean()),
        "C3_viol_given_accept": _m(acc_c3, viol),
        "C3_err_given_accept": _m(acc_c3, tv["wrong"]),
        "C3_n_accept": n_acc,
        # -- B2-R.  KHONG co `viol`: do no bang `s > qhat` la MUON `qhat` cua
        #    C3 cho B2 -- cai bay `A066` muc 3 da tu choi. O TRONG la ket qua.
        "c_B2": float(c),
        "B2_acceptance_test": float(acc_b2.mean()),
        "B2_err_given_accept": _m(acc_b2, tv["wrong"]),
        "B2_n_accept": int(acc_b2.sum()),
        "B2_has_no_coverage_claim": True,
        # -- B1-R  (doi chung DUONG)
        "c_B1": c_b1,
        "B1_acceptance_test": float(acc_b1.mean()),
        "B1_err_given_accept": _m(acc_b1, tv["wrong"]),
        "B1_n_accept": int(acc_b1.sum()),
        # -- chung
        "anchor_err": tv["anchor_err"],
        "a_star": A_STAR,
    }

    if matched:
        # `T2` cua Task B, do lai duoi tai hieu chuan. Chi tinh o `n` duoc ky
        # (`N_MAIN`) -- bon `argsort` tren 500k hang khong mien phi.
        sc3 = BL.score_C3(tv["df"], q_rows)
        order_c3 = np.argsort(-sc3, kind="mergesort")
        row["matched"] = {
            "%.2f" % t: {
                "err_C3R": _err_at_coverage(order_c3, tv["wrong"], t),
                "err_B2R": _err_at_coverage(tv["order_b2"], tv["wrong"], t),
            }
            for t in MATCHED_ACCEPTANCE
        }
    return row


def block_draws(calib: pd.DataFrame, rng: np.random.Generator
                ) -> list[Tuple[int, int, np.ndarray]]:
    """CRN: tap block chi phu thuoc `(B, n, draw)` -- KHONG phu thuoc A.

    Sinh MOT LAN cho moi cell B, roi 8 gia tri `kappa_A` va ca ba thu tuc dung
    lai dung tap do. Neu sinh trong vong lap A thi moi so sanh doc truc A se
    tron them nhieu lay mau.
    """
    n_all = int(calib["block_id"].nunique())
    out: list[Tuple[int, int, np.ndarray]] = []
    for n in N_GRID:
        # `n >= n_all`: tap con la TOAN BO calib, moi lan lay mau cho cung ket
        # qua. Mot lan la du (cung quy uoc voi `cert/recalibration_cost.py`).
        draws = 1 if int(n) >= n_all else N_DRAWS
        for d in range(draws):
            sub = RC.subsample_blocks(calib, int(n), rng)
            out.append((int(n), int(d),
                        np.sort(sub["block_id"].unique())))
    return out


def run_cell_matrix(cells: Sequence[str], kappa: Mapping[str, float],
                    label: str) -> Tuple[list, Dict[str, Any]]:
    """Ma tran |cells| x |cells| x N_GRID x N_DRAWS, ba thu tuc, CRN."""
    rows: list[Dict[str, Any]] = []
    paths: Dict[str, Any] = {}
    for b in cells:
        calib_B, test_B, path = TM.load_cell(b)
        paths[b] = pin(path)
        tv = prepare_test(test_B)
        draws = block_draws(calib_B, np.random.default_rng(SEED))
        for n, d, keep in draws:
            sub = calib_B[calib_B["block_id"].isin(keep)].reset_index(drop=True)
            for a in cells:
                r = run_one(sub, tv, kappa[a], matched=(int(n) == N_MAIN))
                r.update({"A": a, "B": b, "n": int(n), "draw": int(d),
                          "branch": label})
                rows.append(r)
            del sub
        del calib_B, test_B, tv
    return rows, paths


# ---------------------------------------------------------------------------
# Gop -- quy uoc DA KY o `A068` muc 3.1b
# ---------------------------------------------------------------------------

def _mean_finite(vals: Sequence[float]) -> float:
    v = np.asarray([x for x in vals], dtype=np.float64)
    v = v[np.isfinite(v)]
    return float(v.mean()) if v.size else float("nan")


def _median_finite(vals: Sequence[float]) -> float:
    v = np.asarray([x for x in vals], dtype=np.float64)
    v = v[np.isfinite(v)]
    return float(np.median(v)) if v.size else float("nan")


def _sd_finite(vals: Sequence[float]) -> float:
    v = np.asarray([x for x in vals], dtype=np.float64)
    v = v[np.isfinite(v)]
    return float(v.std(ddof=1)) if v.size > 1 else float("nan")


AGG_KEYS = ("C3_acceptance_test", "C3_viol_given_accept", "C3_err_given_accept",
            "B2_acceptance_test", "B2_err_given_accept",
            "B1_acceptance_test", "B1_err_given_accept",
            "C3_n_accept", "anchor_err")


def cells_at_n(rows: Sequence[Mapping[str, Any]], n: int
               ) -> Dict[Tuple[str, str], Dict[str, float]]:
    """o(A, B, n) = TRUNG BINH tren cac lan lay mau, chi tren gia tri HUU HAN."""
    grp: Dict[Tuple[str, str], list] = {}
    for r in rows:
        if int(r["n"]) == int(n):
            grp.setdefault((r["A"], r["B"]), []).append(r)
    out: Dict[Tuple[str, str], Dict[str, float]] = {}
    for ab, rs in grp.items():
        o = {k: _mean_finite([r[k] for r in rs]) for k in AGG_KEYS}
        o["n_draws"] = float(len(rs))
        o["n_draws_zero_accept"] = float(sum(1 for r in rs
                                             if int(r["C3_n_accept"]) == 0))
        out[ab] = o
    return out


def _by_B(cells: Mapping[Tuple[str, str], Mapping[str, float]], key: str,
          names: Sequence[str]) -> Dict[str, float]:
    """Gop truc A bang TRUNG VI -- quy uoc `A068` muc 3.1b."""
    return {b: _median_finite([v[key] for (a, bb), v in cells.items() if bb == b])
            for b in names}


# ---------------------------------------------------------------------------
# Cham diem -- dai DA KY o `A068` muc 5 va 6
# ---------------------------------------------------------------------------

def _tm_diagonal() -> Dict[str, Dict[str, float]]:
    """Duong cheo `transfer_matrix.json` -- dap an cua `M-200` (`A068` S-4)."""
    path = os.path.join(REPO, "results/LIVE/phase-23/transfer_matrix.json")
    with open(path, encoding="utf-8") as fh:
        art = json.load(fh)
    out: Dict[str, Dict[str, float]] = {}
    for cell in art["cells_live"]:
        r = art["cellwise"]["%s->%s" % (cell, cell)]
        out[cell] = {
            "acceptance": float(r["T1_acceptance_C3"]),
            "violation_given_accept": float(r["T3_viol_given_accept_C3"]),
        }
    return out


def score_M200(live: Sequence[str]) -> Dict[str, Any]:
    """`M-200` -- KIEM WIRING. Dap an DA BIET (`A068` muc 0.1 va 5.1).

    C3-R tai `kappa` EP BANG 0.50 va `n` = 500 (toan bo calib) PHAI la DUNG
    phep tinh cua duong cheo `transfer_matrix.json`. Vo o day = duong ong
    hong, KHONG phai mot phat hien.
    """
    ref = _tm_diagonal()
    per: list[Dict[str, Any]] = []
    for cell in live:
        calib, test, _p = TM.load_cell(cell)
        tv = prepare_test(test)
        r = run_one(calib, tv, KAPPA_OP)
        per.append({
            "cell": cell,
            "acceptance": r["C3_acceptance_test"],
            "acceptance_ref": ref[cell]["acceptance"],
            "delta_acceptance": abs(r["C3_acceptance_test"]
                                    - ref[cell]["acceptance"]),
            "viol": r["C3_viol_given_accept"],
            "viol_ref": ref[cell]["violation_given_accept"],
            "delta_viol": abs(r["C3_viol_given_accept"]
                              - ref[cell]["violation_given_accept"]),
        })
        del calib, test, tv
    d_acc = max(p["delta_acceptance"] for p in per)
    d_vio = max(p["delta_viol"] for p in per)
    return {
        "n_cells": len(per), "kappa_forced": KAPPA_OP, "n_blocks": N_FULL,
        "max_abs_delta_acceptance": float(d_acc),
        "max_abs_delta_violation": float(d_vio),
        "hit": bool(d_acc == 0.0 and d_vio == 0.0),
        "cells": per,
        "label": "KIEM WIRING -- dap an da biet (`A068` muc 0.1). "
                 "Vo = DUNG duong ong, khong phai phat hien.",
    }


def score_NC_B3_2(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """`NC-B3-2` -- B2-R va B1-R phai TRUNG BIT theo truc A (S-2)."""
    fields = ("c_B2", "B2_acceptance_test", "B2_err_given_accept",
              "c_B1", "B1_acceptance_test", "B1_err_given_accept")
    grp: Dict[Tuple[str, int, int], list] = {}
    for r in rows:
        grp.setdefault((r["B"], int(r["n"]), int(r["draw"])), []).append(r)
    worst = {f: 0.0 for f in fields}
    worst_at = {f: None for f in fields}
    n_groups = 0
    for key, rs in grp.items():
        if len(rs) < 2:
            continue
        n_groups += 1
        for f in fields:
            v = np.asarray([r[f] for r in rs], dtype=np.float64)
            ok = np.isfinite(v)
            if not ok.any():
                continue
            d = float(np.nanmax(v[ok]) - np.nanmin(v[ok]))
            if int(ok.sum()) != len(rs):     # huu han o o nay, nan o o kia
                d = float("inf")
            if d > worst[f]:
                worst[f], worst_at[f] = d, "%s n=%d draw=%d" % key
    return {
        "n_groups": int(n_groups),
        "n_A_per_group": int(max((len(v) for v in grp.values()), default=0)),
        "max_abs_delta": {f: float(worst[f]) for f in fields},
        "worst_group": {f: worst_at[f] for f in fields},
        "hit": bool(n_groups > 0 and all(worst[f] == 0.0 for f in fields)),
        "label": "S-2: `a*` la hang so toan cuc -> B2-R/B1-R KHONG phu thuoc "
                 "A. Khong trung bit = wiring hong, DUNG lai.",
    }


def score_predictions(rows: Sequence[Mapping[str, Any]],
                      live: Sequence[str],
                      kappa: Mapping[str, float]) -> Dict[str, Any]:
    """`M-201` .. `M-206`, dai DA KY o `A068` muc 5.2 -- 5.7."""
    main = cells_at_n(rows, N_MAIN)
    full = cells_at_n(rows, N_FULL)

    # -- M-201: bao toan co song sot o `n` huu han khong?  [MU]
    keep = [v for v in main.values() if v["C3_acceptance_test"] >= ACCEPT_FLOOR]
    sd_v = _sd_finite([v["C3_viol_given_accept"] for v in keep])
    sd_a = _sd_finite([v["C3_acceptance_test"] for v in keep])
    mu_v = _mean_finite([v["C3_viol_given_accept"] for v in keep])
    m201 = {
        "n": N_MAIN, "n_cells_total": len(main), "n_cells_above_floor": len(keep),
        "acceptance_floor": ACCEPT_FLOOR,
        "sd_viol": sd_v, "sd_acceptance": sd_a, "mean_viol": mu_v,
        "anchor_full_n": {"sd_viol": 0.00289, "sd_acceptance": 0.09201,
                          "mean_viol": 0.08100},
        "hit_sd_viol": bool(np.isfinite(sd_v) and sd_v <= 0.020),
        "hit_sd_acceptance": bool(np.isfinite(sd_a) and 0.090 <= sd_a <= 0.180),
        "hit_mean_viol": bool(np.isfinite(mu_v) and 0.05 <= mu_v <= 0.12),
    }
    m201["hit"] = bool(m201["hit_sd_viol"] and m201["hit_sd_acceptance"]
                       and m201["hit_mean_viol"])

    # -- M-202: gia cua `kappa` sai co du doan duoc khong?  [MU]
    def _kappa_fit(cells: Mapping[Tuple[str, str], Mapping[str, float]]
                   ) -> Dict[str, Any]:
        xs, ys = [], []
        for (a, b), v in cells.items():
            if a == b or not np.isfinite(v["C3_acceptance_test"]):
                continue
            xs.append(abs(float(np.log(kappa[a] / kappa[b]))))
            ys.append(abs(v["C3_acceptance_test"] - A_STAR))
        rho = TM._spearman(xs, ys)
        slope = (float(np.polyfit(xs, ys, 1)[0]) if len(xs) >= 3
                 else float("nan"))
        return {"n_cells": len(xs), "spearman": rho, "slope": slope}

    at_full = _kappa_fit(full)
    m202 = {
        "n": N_FULL, **at_full,
        "also_at_n_%d" % N_MAIN: _kappa_fit(main),
        "hit_spearman": bool(np.isfinite(at_full["spearman"])
                             and at_full["spearman"] >= 0.90),
        "hit_slope": bool(np.isfinite(at_full["slope"])
                          and 0.40 <= at_full["slope"] <= 0.62),
        "label": "do doc neo -0.509 do tren CALIB cua A (`A068` S-6); o day do "
                 "tren TEST cua B sau khi `qhat` da duoc uoc luong lai",
    }
    m202["hit"] = bool(m202["hit_spearman"] and m202["hit_slope"])

    # -- M-203: bao dam co duoc khoi phuc khong?  [MU]
    ok = [1 for v in main.values()
          if np.isfinite(v["C3_viol_given_accept"])
          and v["C3_viol_given_accept"] <= ALPHA_FAMILY
          and v["C3_acceptance_test"] >= ACCEPT_FLOOR]
    m203 = {
        "n": N_MAIN, "n_ok": int(sum(ok)), "n_cells": len(main),
        "alpha": ALPHA_FAMILY, "acceptance_floor": ACCEPT_FLOOR,
        "hit": bool(sum(ok) >= 52),
        "label": "o co `n_accept = 0` -> `viol` khong xac dinh -> KHONG dem "
                 "la dat (`A068` muc 3.3)",
    }

    # -- M-204: GIA phai tra, tinh bang `n`  [MU]
    def _n_star(which: str) -> Any:
        for n in N_GRID:
            c = cells_at_n(rows, n)
            if which == "C3":
                v_ = _by_B(c, "C3_viol_given_accept", live)
                a_ = _by_B(c, "C3_acceptance_test", live)
                good = sum(1 for b in live
                           if np.isfinite(v_[b]) and v_[b] <= ALPHA_FAMILY
                           and a_[b] >= ACCEPT_FLOOR)
            else:
                a_ = _by_B(c, "B2_acceptance_test", live)
                good = sum(1 for b in live
                           if np.isfinite(a_[b]) and abs(a_[b] - A_STAR) <= 0.05)
            if good >= 7:
                return int(n)
        return None

    n_c3, n_b2 = _n_star("C3"), _n_star("B2")
    ratio = (float(n_c3) / float(n_b2)) if (n_c3 and n_b2) else float("nan")
    m204 = {
        "n_star_C3R": n_c3, "n_star_B2R": n_b2, "ratio": ratio,
        "n_grid": list(N_GRID), "required_cells": 7, "n_cells": len(live),
        "hit_C3": bool(n_c3 is not None and 60 <= n_c3 <= 250),
        "hit_B2": bool(n_b2 is not None and n_b2 <= 60),
        "hit_ratio": bool(np.isfinite(ratio) and ratio >= 2.0),
        "anchor_task_B2_same_cell": {"C3": 120, "B2": 20},
    }
    m204["hit"] = bool(m204["hit_C3"] and m204["hit_B2"] and m204["hit_ratio"])

    # -- M-205: ve `err`, hai ben co khac nhau khong?  [KET QUA AM DU KIEN]
    gaps = [abs(v["err_C3R"] - v["err_B2R"])
            for r in rows if int(r["n"]) == N_MAIN and "matched" in r
            for v in r["matched"].values()
            if np.isfinite(v["err_C3R"]) and np.isfinite(v["err_B2R"])]
    med = _median_finite(gaps)
    m205 = {
        "n": N_MAIN, "median_abs_gap": med, "n_points": len(gaps),
        "matched_acceptance": list(MATCHED_ACCEPTANCE),
        "hit": bool(np.isfinite(med) and med <= 0.02),
        "anchor_M196": 0.00526,
        "label": "KY TRUOC de bao cao TRUNG THUC rang dong gop KHONG nam o day",
    }

    # -- M-206: ve DOI XUNG cua menh de bao toan  [MA DE MISS NHAT]
    err_b2 = _by_B(main, "B2_err_given_accept", live)
    err_c3 = _by_B(main, "C3_err_given_accept", live)
    sd_b2 = _sd_finite(list(err_b2.values()))
    sd_c3 = _sd_finite(list(err_c3.values()))
    m206 = {
        "n": N_MAIN,
        "sd_err_B2R": sd_b2, "sd_err_C3R": sd_c3,
        "err_by_cell_B2R": err_b2, "err_by_cell_C3R": err_c3,
        "anchor_C3_full_n": 0.01583,
        "hit_B2": bool(np.isfinite(sd_b2) and sd_b2 >= 0.020),
        "hit_C3": bool(np.isfinite(sd_c3) and sd_c3 <= 0.025),
        "reading_if_miss": (
            "Menh de bao toan ton tai o muc `viol`, KHONG o muc `err`. C3 giu "
            "bao dam ve SCORE, khong giu bao dam ve QUYET DINH. Cau noi giua "
            "hai muc la DIEU KIEN TACH ROI, chua duoc do o day. Ket qua AM "
            "nay BUOC paper phat bieu o muc `viol`. (`A068` muc 5.7)"),
    }
    m206["hit"] = bool(m206["hit_B2"] and m206["hit_C3"])

    return {"M_201": m201, "M_202": m202, "M_203": m203, "M_204": m204,
            "M_205": m205, "M_206": m206}


def score_controls(rows: Sequence[Mapping[str, Any]], live: Sequence[str],
                   dead_rows: Sequence[Mapping[str, Any]],
                   dead: Sequence[str]) -> Dict[str, Any]:
    """`NC-B3-1`, `NC-B3-2`, `NC-B3-3`, `NC-B3-4` -- `A068` muc 6."""
    main = cells_at_n(rows, N_MAIN)

    # -- NC-B3-1: doi chung DUONG. PHAI FIRE.
    acc_b1 = _by_B(main, "B1_acceptance_test", live)
    err_b1 = _by_B(main, "B1_err_given_accept", live)
    anch = _by_B(main, "anchor_err", live)
    n_hit_acc = sum(1 for b in live
                    if np.isfinite(acc_b1[b]) and abs(acc_b1[b] - A_STAR) <= 0.05)
    n_useless = sum(1 for b in live
                    if np.isfinite(err_b1[b]) and err_b1[b] >= 0.90 * anch[b])
    nc1 = {
        "n": N_MAIN, "n_cells": len(live),
        "n_cells_B1_hits_a_star": int(n_hit_acc),
        "n_cells_B1_no_better_than_anchor": int(n_useless),
        "acceptance_B1_by_cell": acc_b1,
        "err_B1_by_cell": err_b1, "anchor_by_cell": anch,
        "fired": bool(n_hit_acc >= 7 and n_useless >= 7),
        "label": "`L99` lan thu TU: 'trung muc tieu acceptance' MOT MINH la vo "
                 "gia tri. Doi chung nay PHAI FIRE.",
    }

    # -- NC-B3-2: trung bit theo truc A
    nc2 = score_NC_B3_2(rows)

    # -- NC-B3-3: doi chung AM tren cell CHET
    dmain = cells_at_n(dead_rows, N_MAIN)
    derr = _by_B(dmain, "C3_err_given_accept", dead)
    danch = _by_B(dmain, "anchor_err", dead)
    n_flat = sum(1 for b in dead
                 if np.isfinite(derr[b]) and abs(derr[b] - danch[b]) <= 0.02)
    nc3 = {
        "n": N_MAIN, "n_cells": len(dead), "n_cells_collapsed": int(n_flat),
        "err_by_cell": derr, "anchor_by_cell": danch,
        "hit": bool(n_flat >= 3),
        "kappa_A_range_dead": "1.611 .. 1.877 (`A068` S-5) -- diem van hanh "
                              "KHAC han cell song; khong doc doi chung nay "
                              "manh hon the",
        "label": "neu phan tach KHONG sap o cell chet -> con so o cell song la "
                 "hien vat duong ong. DUNG.",
    }

    # -- NC-B3-4: `L100` -- co duy nhat con nhin thay o vung giao
    low = [r for r in rows if int(r["n"]) == 30]
    n_low = len(low)
    r_src = (sum(1 for r in low
                 if r["C3_qhat_source"] == "degenerate_fallback_to_none")
             / n_low) if n_low else float("nan")
    r_old = (sum(1 for r in low
                 if r["C3_qhat_has_infinite"] or r["C3_qhat_at_sample_max"])
             / n_low) if n_low else float("nan")
    nc4 = {
        "n": 30, "n_runs": int(n_low),
        "rate_qhat_source_collapsed": float(r_src),
        "rate_two_old_flags": float(r_old),
        "hit": bool(n_low > 0 and r_src > 0.0),
        "label": "`L100`: hai co `L91`/`L93` MU o vung giao cua `L93` va "
                 "`L95`; `qhat_source` la co duy nhat con nhin thay",
    }
    return {"NC_B3_1": nc1, "NC_B3_2": nc2, "NC_B3_3": nc3, "NC_B3_4": nc4}


def census_zero_accept(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """`A068` muc 3.3 -- `n_accept = 0` la KHONG XAC DINH, khong phai 0 vi pham."""
    out: Dict[str, Any] = {}
    for n in N_GRID:
        sub = [r for r in rows if int(r["n"]) == int(n)]
        if not sub:
            continue
        z = sum(1 for r in sub if int(r["C3_n_accept"]) == 0)
        out[str(n)] = {
            "n_runs": len(sub), "n_zero_accept_C3": int(z),
            "rate": float(z / len(sub)),
            "n_zero_accept_B2": int(sum(1 for r in sub
                                        if int(r["B2_n_accept"]) == 0)),
        }
    hi = [v for k, v in out.items() if int(k) >= 120]
    rate_hi = (sum(v["n_zero_accept_C3"] for v in hi)
               / max(sum(v["n_runs"] for v in hi), 1)) if hi else 0.0
    out["_stop_rule_4"] = {
        "rate_zero_accept_at_n_ge_120": float(rate_hi),
        "threshold": 0.20,
        "triggered": bool(rate_hi > 0.20),
        "label": "> 20% -> thiet ke sai san acceptance, DUNG va ky lai san",
    }
    return out


# ---------------------------------------------------------------------------
# Chay
# ---------------------------------------------------------------------------

def wiring() -> Dict[str, Any]:
    """Buoc [7]: `NC-B3-0` va `NC-B3-2` chay TRUOC toan bo.

    `M-193` cua Task B da cho thay gia tri cua mot kiem wiring trung bit: khi
    no xanh tuyet doi, moi FAIL sau do chac chan la ve THE GIOI, khong phai
    ve CODE.
    """
    live, _dead = TM.cells_by_role()
    kappa = load_kappa_A()
    m200 = score_M200(live)

    # `NC-B3-2` tren MOT cell B o `n` nho -- du de bat wiring hong, va ton
    # 24 lan fit thay vi 2624.
    b = sorted(live)[0]
    calib_B, test_B, _p = TM.load_cell(b)
    tv = prepare_test(test_B)
    rng = np.random.default_rng(SEED)
    probe: list[Dict[str, Any]] = []
    for d in range(3):
        sub = RC.subsample_blocks(calib_B, 30, rng)
        for a in live:
            r = run_one(sub, tv, kappa[a])
            r.update({"A": a, "B": b, "n": 30, "draw": d, "branch": "probe"})
            probe.append(r)
    nc2 = score_NC_B3_2(probe)
    return {"M_200": m200, "NC_B3_2_probe": nc2, "probe_cell": b,
            "kappa_A": {k: float(v) for k, v in kappa.items()}}


def run() -> Dict[str, Any]:
    live, dead = TM.cells_by_role()
    kappa = load_kappa_A()

    rows, paths = run_cell_matrix(live, kappa, "live")
    dead_rows, dead_paths = run_cell_matrix(dead, kappa, "dead")

    m200 = score_M200(live)
    preds = score_predictions(rows, live, kappa)
    ctrl = score_controls(rows, live, dead_rows, dead)

    return {
        "schema": "dt4n.recalibrate_transfer.v1",
        "lesson": "23.22",
        "task": "B-3",
        "amendment": AMENDMENT,
        "prereg_tag": "lesson-23-22-b3-prereg",
        "config": {
            "a_star": A_STAR, "kappa_op_for_wiring": KAPPA_OP,
            "post_variant": POST_VARIANT, "multiplicity": MULTIPLICITY,
            "alpha_family": ALPHA_FAMILY,
            "n_grid": list(N_GRID), "n_draws": N_DRAWS, "seed": SEED,
            "seed_B1": SEED_B1,
            "n_main": N_MAIN, "n_full": N_FULL,
            "acceptance_floor": ACCEPT_FLOOR, "break_tol": BREAK_TOL,
            "matched_acceptance": list(MATCHED_ACCEPTANCE),
            "kappa_A": {k: float(v) for k, v in kappa.items()},
            "kappa_A_source": PILOT_OUT,
        },
        "cells_live": list(live),
        "cells_dead": list(dead),
        "M_200_wiring": m200,
        "predictions": preds,
        "controls": ctrl,
        "census_zero_accept": census_zero_accept(rows),
        "census_zero_accept_dead": census_zero_accept(dead_rows),
        "rows": rows,
        "rows_dead": dead_rows,
        "validity": validity_block(
            aoi_generator=AOI_V7,
            z_edges=Z_EDGES_V7,
            sla_path=SLA_MANIFEST,
            w_loss=W_LOSS,
        ),
        "provenance": {
            "script": "cert/recalibrate_transfer.py::run",
            "git_hash": git("git", "rev-parse", "HEAD"),
            "git_dirty": git("git", "status", "--porcelain") != "",
            "utc": datetime.now(timezone.utc).isoformat(),
            "parquet": {**paths, **dead_paths},
        },
    }


def print_run(out: Mapping[str, Any]) -> None:
    p, c = out["predictions"], out["controls"]
    w = out["M_200_wiring"]
    print("\n=== Task B-3 -- tai hieu chuan qua che do ===")
    print("M-200 WIRING : %s   max|dacc| = %.3e   max|dviol| = %.3e   (%d cell)"
          % (w["hit"], w["max_abs_delta_acceptance"],
             w["max_abs_delta_violation"], w["n_cells"]))
    m = p["M_201"]
    print("M-201 bao toan @n=%d : %s   sd(viol) = %.5f [<=0.020] | "
          "sd(acc) = %.5f [0.090..0.180] | mean(viol) = %.5f [0.05..0.12]  "
          "(%d/%d o tren san)"
          % (m["n"], m["hit"], m["sd_viol"], m["sd_acceptance"], m["mean_viol"],
             m["n_cells_above_floor"], m["n_cells_total"]))
    m = p["M_202"]
    print("M-202 gia kappa @n=%d : %s   Spearman = %+.4f [>=+0.90] | "
          "do doc = %.4f [0.40..0.62]  (%d o)"
          % (m["n"], m["hit"], m["spearman"], m["slope"], m["n_cells"]))
    m = p["M_203"]
    print("M-203 khoi phuc @n=%d : %s   %d/%d o  [>=52]"
          % (m["n"], m["hit"], m["n_ok"], m["n_cells"]))
    m = p["M_204"]
    print("M-204 gia bang n     : %s   n*(C3-R) = %s [60..250] | "
          "n*(B2-R) = %s [<=60] | ti so = %.2f [>=2.0]"
          % (m["hit"], m["n_star_C3R"], m["n_star_B2R"], m["ratio"]))
    m = p["M_205"]
    print("M-205 err (AM) @n=%d : %s   trung vi |derr| = %.5f [<=0.02]  "
          "(%d diem)" % (m["n"], m["hit"], m["median_abs_gap"], m["n_points"]))
    m = p["M_206"]
    print("M-206 doi xung @n=%d : %s   sd(err B2-R) = %.5f [>=0.020] | "
          "sd(err C3-R) = %.5f [<=0.025]"
          % (m["n"], m["hit"], m["sd_err_B2R"], m["sd_err_C3R"]))
    print("NC-B3-1 doi chung DUONG : fired = %s   (%d/%d trung a*, "
          "%d/%d khong hon anchor)"
          % (c["NC_B3_1"]["fired"], c["NC_B3_1"]["n_cells_B1_hits_a_star"],
             c["NC_B3_1"]["n_cells"],
             c["NC_B3_1"]["n_cells_B1_no_better_than_anchor"],
             c["NC_B3_1"]["n_cells"]))
    print("NC-B3-2 trung bit truc A: %s   max|delta| = %s"
          % (c["NC_B3_2"]["hit"],
             {k: "%.1e" % v for k, v in c["NC_B3_2"]["max_abs_delta"].items()}))
    print("NC-B3-3 cell CHET       : %s   %d/%d cell sap ve anchor"
          % (c["NC_B3_3"]["hit"], c["NC_B3_3"]["n_cells_collapsed"],
             c["NC_B3_3"]["n_cells"]))
    print("NC-B3-4 `L100` @n=30    : %s   qhat_source sup = %.0f%% vs hai co "
          "cu = %.0f%%"
          % (c["NC_B3_4"]["hit"], 100 * c["NC_B3_4"]["rate_qhat_source_collapsed"],
             100 * c["NC_B3_4"]["rate_two_old_flags"]))
    s4 = out["census_zero_accept"]["_stop_rule_4"]
    print("census n_accept=0 tai n>=120: %.1f%%  (chan dung 20%%: %s)"
          % (100 * s4["rate_zero_accept_at_n_ge_120"], s4["triggered"]))

    print("\n%5s %10s %10s %10s %10s %10s %10s" % (
        "n", "acc C3", "viol C3", "err C3", "acc B2", "err B2", "acc B1"))
    for n in N_GRID:
        cl = cells_at_n(out["rows"], int(n))
        if not cl:
            continue
        v = list(cl.values())
        print("%5d %10.4f %10.4f %10.4f %10.4f %10.4f %10.4f" % (
            n,
            _mean_finite([x["C3_acceptance_test"] for x in v]),
            _mean_finite([x["C3_viol_given_accept"] for x in v]),
            _mean_finite([x["C3_err_given_accept"] for x in v]),
            _mean_finite([x["B2_acceptance_test"] for x in v]),
            _mean_finite([x["B2_err_given_accept"] for x in v]),
            _mean_finite([x["B1_acceptance_test"] for x in v])))


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pilot", action="store_true",
                    help="giai `kappa_A` tren 12 cell (`A068` muc 4)")
    ap.add_argument("--wiring", action="store_true",
                    help="`NC-B3-0` + `NC-B3-2`, chay TRUOC (`A068` buoc 7)")
    ap.add_argument("--run", action="store_true", help="toan bo nhanh R + D")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(list(argv) if argv is not None else None)
    if sum(map(bool, (args.pilot, args.wiring, args.run))) != 1:
        ap.error("chon DUNG MOT trong --pilot / --wiring / --run")

    if args.pilot:
        out = pilot()
        path = args.out or PILOT_OUT
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(json_clean(out), fh, indent=1, sort_keys=True)
        print_pilot(out)
        print("-> %s" % path)
        return 0

    if args.wiring:
        out = wiring()
        w, n2 = out["M_200"], out["NC_B3_2_probe"]
        print("M-200 WIRING : %s   max|dacc| = %.3e   max|dviol| = %.3e"
              % (w["hit"], w["max_abs_delta_acceptance"],
                 w["max_abs_delta_violation"]))
        for r in w["cells"]:
            print("   %-16s acc %.12f vs %.12f | viol %.12f vs %.12f"
                  % (r["cell"], r["acceptance"], r["acceptance_ref"],
                     r["viol"], r["viol_ref"]))
        print("NC-B3-2 (probe tren %s, n=30, 3 draw, 8 kappa_A): %s"
              % (out["probe_cell"], n2["hit"]))
        for k, v in n2["max_abs_delta"].items():
            print("   %-22s max|delta| = %.3e" % (k, v))
        if not (w["hit"] and n2["hit"]):
            print("\n!! CHAN DUNG (`A068` muc 8): wiring hong. KHONG chay tiep.")
            return 1
        print("\nwiring xanh tuyet doi -> duoc phep chay `--run`")
        return 0

    out = run()
    path = args.out or OUTPUT
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(json_clean(out), fh, indent=1, sort_keys=True)
    print_run(out)
    print("-> %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
