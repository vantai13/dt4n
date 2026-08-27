#!/usr/bin/env python3
"""Phase 23 / Lesson 23.23 -- baseline co nguon va khoang khong-conformal.

Chay dung thu tu::

    python -m cert.baselines_lit --wiring
    python -m cert.baselines_lit --negative
    python -m cert.baselines_lit --run

B7 la mot diem van hanh theo reject rule (khong co phat bieu coverage).
B8a..B8d tu sinh q_hat. Moi thu tuc deu di qua ``score_procedure``.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.special import erf
from scipy.stats import norm, t as student_t

from cert import config_matrix as CM
from cert import fallback as FB
from cert.build_calib_set_v2 import split_by_block
from cert.build_calib_set_v3 import AOI_V7, Z_EDGES_V7
from cert.cell_matrices import ALPHA_FAMILY, git, json_clean, pin
from cert.taxonomy_audit import SLA_MANIFEST, W_LOSS, calib_path
from cert.transfer_matrix import KAPPA_OP, MULTIPLICITY, POST_VARIANT
from measurements.validity import validity_block

AMENDMENT = "docs/phase-23/A072-amendment-72.md"
OUTPUT = "results/LIVE/phase-23/baselines_lit.json"

N_MARGINS = len(CM.SIM_COLS)
ALPHA_EACH = CM.alpha_bonferroni(ALPHA_FAMILY, N_MARGINS)

SQRT_2_OVER_PI = float(np.sqrt(2.0 / np.pi))
CV_MAX_FOLDED = float(np.sqrt(np.pi / 2.0 - 1.0))
Z_BONF = float(norm.ppf(1.0 - ALPHA_EACH))

THETA_HI = 200.0
BISECT_ITERS = 200

ACCEPT_FLOOR = 0.20
N_BOOT = 2000
SEED_BOOT = 91101
SEED_NC = 232323
N_NC_DRAWS = 200


def _h(theta: np.ndarray | float) -> np.ndarray | float:
    """Ham moment don dieu tang cua folded normal tren [0, +inf)."""
    th = np.asarray(theta, dtype=np.float64)
    g = SQRT_2_OVER_PI * np.exp(-0.5 * th * th) + th * erf(th / np.sqrt(2.0))
    return g / np.sqrt(1.0 + th * th)


def cv_of(s: np.ndarray) -> float:
    """He so bien dong dung cho M-227."""
    s = np.asarray(s, dtype=np.float64)
    m1 = float(s.mean())
    if m1 <= 0.0:
        return float("nan")
    m2 = float((s * s).mean())
    return float(np.sqrt(max(m2 / (m1 * m1) - 1.0, 0.0)))


def fit_folded_normal(s: np.ndarray) -> Tuple[float, float, Dict[str, Any]]:
    """Fit folded normal bang method of moments, tra ``(mu, sigma, info)``."""
    s = np.asarray(s, dtype=np.float64)
    n = int(s.size)
    m1 = float(s.mean())
    m2 = float((s * s).mean())
    if not np.isfinite(m1) or not np.isfinite(m2) or m1 <= 0.0 or m2 <= 0.0:
        return 0.0, 0.0, {
            "degenerate": True, "n": n, "r": float("nan"),
            "cv": float("nan"), "outside_family": False, "theta": 0.0,
        }
    r = m1 / np.sqrt(m2)
    outside = bool(r < SQRT_2_OVER_PI)
    if outside:
        theta = 0.0
    else:
        lo, hi = 0.0, THETA_HI
        for _ in range(BISECT_ITERS):
            mid = 0.5 * (lo + hi)
            if _h(mid) < r:
                lo = mid
            else:
                hi = mid
        theta = 0.5 * (lo + hi)
    sigma = float(np.sqrt(m2 / (1.0 + theta * theta)))
    mu = float(theta * sigma)
    return mu, sigma, {
        "degenerate": False, "n": n, "r": float(r), "cv": cv_of(s),
        "outside_family": outside, "theta": float(theta),
    }


def folded_quantile(mu: float, sigma: float, p: float) -> float:
    """Giai phan vi cua ``|N(mu, sigma**2)|`` bang bisection co dinh."""
    if not np.isfinite(sigma) or sigma <= 0.0:
        return float(abs(mu))
    lo, hi = 0.0, abs(mu) + 40.0 * sigma
    for _ in range(BISECT_ITERS):
        mid = 0.5 * (lo + hi)
        f = norm.cdf((mid - mu) / sigma) - norm.cdf((-mid - mu) / sigma)
        if f < p:
            lo = mid
        else:
            hi = mid
    return float(0.5 * (lo + hi))


def qhat_C3(s: np.ndarray, n_eff: int) -> float:
    """Conformal; co the tu choi bang cach tra +inf."""
    lvl = CM.conformal_level(int(n_eff), ALPHA_EACH)
    if lvl is None:
        return float("inf")
    return float(CM.empirical_qhat(np.asarray(s, np.float64), lvl))


def qhat_B8a_naive(s: np.ndarray, n_eff: int) -> float:
    """Gaussian ngay tho [MO TA]: ``q = Z_BONF * sd(s)``, co y bo mu."""
    s = np.asarray(s, np.float64)
    if s.size < 2:
        return float("nan")
    return float(Z_BONF * np.std(s, ddof=1))


def qhat_B8b_folded(s: np.ndarray, n_eff: int) -> float:
    """Folded normal steel-man voi Student-t va prediction inflation."""
    s = np.asarray(s, np.float64)
    if s.size < 2:
        return float("nan")
    mu, sigma, _ = fit_folded_normal(s)
    if sigma <= 0.0:
        return float(abs(mu))
    n = max(int(n_eff), 2)
    df = n - 1
    infl_t = float(student_t.ppf(1.0 - ALPHA_EACH, df) / Z_BONF)
    sigma_pred = sigma * infl_t * float(np.sqrt(1.0 + 1.0 / n))
    return folded_quantile(mu, sigma_pred, 1.0 - ALPHA_EACH)


def qhat_B8c_plugin(s: np.ndarray, n_eff: int) -> float:
    """Phan vi mau thang, khong co hieu chinh conformal ``(n+1)``."""
    s = np.asarray(s, np.float64)
    if s.size < 1:
        return float("nan")
    return float(np.quantile(s, 1.0 - ALPHA_EACH, method="higher"))


def qhat_B8d_bootstrap(
    s: np.ndarray, n_eff: int, block_id: np.ndarray | None = None,
) -> float:
    """Block bootstrap percentile; ca hai lan deu lay phan vi 1-alpha'."""
    s = np.asarray(s, np.float64)
    if block_id is None:
        raise ValueError("B8d bat buoc co `block_id`: bootstrap phai theo BLOCK")
    b = np.asarray(block_id)
    uniq = np.unique(b)
    idx_by_block = {int(u): np.flatnonzero(b == u) for u in uniq}
    rng = np.random.default_rng(SEED_BOOT)
    draws = np.empty(N_BOOT, dtype=np.float64)
    for i in range(N_BOOT):
        pick = rng.integers(0, len(uniq), len(uniq))
        idx = np.concatenate([idx_by_block[int(uniq[j])] for j in pick])
        draws[i] = np.quantile(s[idx], 1.0 - ALPHA_EACH, method="higher")
    return float(np.quantile(draws, 1.0 - ALPHA_EACH, method="higher"))


PROCEDURES = {
    "C3": qhat_C3,
    "B8a": qhat_B8a_naive,
    "B8b": qhat_B8b_folded,
    "B8c": qhat_B8c_plugin,
    "B8d": qhat_B8d_bootstrap,
}


def _raw_qhat_by_cell(calib: pd.DataFrame, proc: str) -> Dict[tuple, np.ndarray]:
    """Mot buoc fit q_hat; n_eff luon dem theo block."""
    keys = CM._keys(POST_VARIANT)
    fn = PROCEDURES[proc]
    out: Dict[tuple, np.ndarray] = {}
    for key, sub in calib.groupby(keys, sort=True):
        k = CM._norm(key)
        n_eff = int(sub["block_id"].nunique())
        vals = []
        for col in CM.SIM_COLS:
            s = sub[col].to_numpy(np.float64)
            if proc == "B8d":
                vals.append(fn(s, n_eff, sub["block_id"].to_numpy()))
            else:
                vals.append(fn(s, n_eff))
        out[k] = np.asarray(vals, dtype=np.float64)
    return out


def fit_qhat_by_cell(
    calib: pd.DataFrame, proc: str, kappa: float = KAPPA_OP,
) -> Dict[tuple, np.ndarray]:
    """Fit q_hat tren dung bien the post-selection dang chay.

    Repo hien tai dung ``POST_VARIANT='selective'``. Vi vay chi fit phan vi
    tren toan CALIB (nhu ban nhap ban dau) se khong parity voi C3: C3 lap lai
    fit tren nhanh duoc chon. Vong lap duoi mirror ``CM.fit_config``; ham sinh
    q_hat la thu duy nhat thay doi giua cac thu tuc.
    """
    keys = CM._keys(POST_VARIANT)
    q = _raw_qhat_by_cell(calib, proc)
    if POST_VARIANT != "selective":
        return q

    cells = [CM._norm(k) for k, _ in calib.groupby(keys, sort=True)]
    seen: Dict[tuple[float, ...], int] = {}
    hist: List[Dict[tuple, np.ndarray]] = []
    floor = CM.conformal_min_blocks(ALPHA_EACH) if proc == "C3" else 2
    mhat = calib[list(CM.MHAT_COLS)].to_numpy(np.float64)
    for _ in range(int(CM.MAX_ITER)):
        q_rows = CM._q_rows(calib, keys, q, len(CM.SIM_COLS))
        selected = (mhat >= float(kappa) * q_rows).all(axis=1)
        sub = calib[selected]
        nb_raw = sub.groupby(keys, sort=True)["block_id"].nunique()
        nb = {CM._norm(k): int(v) for k, v in nb_raw.items()}
        if min(nb.get(k, 0) for k in cells) < floor:
            break
        q_new = _raw_qhat_by_cell(sub, proc)
        hist.append(q_new)
        sig = tuple(round(float(x), 12) for k in cells for x in q_new[k])
        rel = max(
            float(np.max(np.abs(q_new[k] - q[k]) / np.maximum(q[k], 1e-12)))
            for k in cells
        )
        if rel < CM.TOL:
            q = q_new
            break
        if sig in seen:
            cycle = hist[seen[sig]:]
            q = {k: np.max(np.vstack([h[k] for h in cycle]), axis=0) for k in cells}
            break
        seen[sig] = len(hist) - 1
        q = q_new
    return q


def score_procedure(
    calib: pd.DataFrame, test: pd.DataFrame, proc: str,
    kappa: float = KAPPA_OP, policy: str = "static",
) -> Dict[str, Any]:
    """Ham cham diem duy nhat cho C3 va moi B8*."""
    keys = CM._keys(POST_VARIANT)
    q = fit_qhat_by_cell(calib, proc, kappa=kappa)
    q_rows = CM._q_rows(test, keys, q, len(CM.SIM_COLS))
    mhat = test[list(CM.MHAT_COLS)].to_numpy(np.float64)
    s = test[list(CM.SIM_COLS)].to_numpy(np.float64)
    accept = (mhat >= float(kappa) * q_rows).all(axis=1)
    viol = (s > q_rows).any(axis=1)
    wrong = test["wrong"].to_numpy(bool)
    res = FB.apply_fallback(test, accept, policy)
    loss_sys = FB.loss_of(test, res["a_chosen"], "err")

    def _m(mask: np.ndarray, values: np.ndarray) -> float:
        return float(values[mask].mean()) if mask.any() else float("nan")

    return {
        "procedure": proc,
        "kappa": float(kappa),
        "n_cells": len(q),
        "n_cells_infinite": int(sum(bool(~np.isfinite(v).all()) for v in q.values())),
        "acceptance": float(accept.mean()),
        "n_accept": int(accept.sum()),
        "viol_given_accept": _m(accept, viol),
        "viol_marginal": float(viol.mean()),
        "err_given_accept": _m(accept, wrong),
        "err_system": float(loss_sys.mean()),
        "meets_accept_floor": bool(accept.mean() >= ACCEPT_FLOOR),
        "qhat_by_cell": {str(k): [float(x) for x in v] for k, v in q.items()},
    }


def _cv_block_ci(
    s: np.ndarray, block_id: np.ndarray, n_boot: int = N_BOOT,
    seed: int = SEED_BOOT,
) -> Tuple[float, float, float]:
    """CI95 cua CV bang block bootstrap."""
    b = np.asarray(block_id)
    uniq = np.unique(b)
    idx_by_block = {int(u): np.flatnonzero(b == u) for u in uniq}
    rng = np.random.default_rng(int(seed))
    draws = np.empty(int(n_boot), dtype=np.float64)
    for i in range(int(n_boot)):
        pick = rng.integers(0, len(uniq), len(uniq))
        idx = np.concatenate([idx_by_block[int(uniq[j])] for j in pick])
        draws[i] = cv_of(s[idx])
    return cv_of(s), float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def structural_test(df: pd.DataFrame) -> Dict[str, Any]:
    """M-227: chi tuyen ngoai ho khi CI95_lo(CV) vuot chan K08."""
    keys = CM._keys(POST_VARIANT)
    rows: List[Dict[str, Any]] = []
    for key, sub in df.groupby(keys, sort=True):
        blk = sub["block_id"].to_numpy()
        for j, col in enumerate(CM.SIM_COLS, start=1):
            cv, lo, hi = _cv_block_ci(sub[col].to_numpy(np.float64), blk)
            rows.append({
                "cell": str(CM._norm(key)), "slot": j,
                "n_blocks": int(sub["block_id"].nunique()),
                "cv": cv, "cv_ci95_lo": lo, "cv_ci95_hi": hi,
                "outside_family": bool(lo > CV_MAX_FOLDED),
            })
    n_out = sum(r["outside_family"] for r in rows)
    return {
        "cv_max_folded": CV_MAX_FOLDED,
        "n_tested": len(rows),
        "n_outside_family": int(n_out),
        "M_227_hit": bool(n_out >= 1),
        "asymmetry_note": (
            "CV vuot -> bac bo dut khoat; CV khong vuot -> KHONG ket luan "
            "duoc gi. Dieu kien DU, khong CAN."
        ),
        "cells": rows,
    }


def refusal_audit(calib: pd.DataFrame) -> Dict[str, Any]:
    """M-230: dem o C3 tu choi trong khi B8 van tra nguong huu han."""
    keys = CM._keys(POST_VARIANT)
    n_min = CM.conformal_min_blocks(ALPHA_EACH)
    rows = []
    for key, sub in calib.groupby(keys, sort=True):
        n_eff = int(sub["block_id"].nunique())
        s = sub[CM.SIM_COLS[0]].to_numpy(np.float64)
        rows.append({
            "cell": str(CM._norm(key)), "n_blocks": n_eff,
            "C3_refuses": bool(CM.conformal_level(n_eff, ALPHA_EACH) is None),
            "B8a_finite": bool(np.isfinite(qhat_B8a_naive(s, n_eff))),
            "B8b_finite": bool(np.isfinite(qhat_B8b_folded(s, n_eff))),
            "B8c_finite": bool(np.isfinite(qhat_B8c_plugin(s, n_eff))),
        })
    gap = [r for r in rows if r["C3_refuses"] and r["B8b_finite"]]
    return {
        "alpha_each": ALPHA_EACH,
        "conformal_min_blocks": int(n_min),
        "n_cells": len(rows),
        "n_cells_C3_refuses": sum(r["C3_refuses"] for r in rows),
        "n_cells_gap": len(gap),
        "M_230_hit": bool(len(gap) >= 1),
        "design_note": (
            "he qua cua ceil((n+1)(1-alpha_each)) <= n; KHONG phai phat "
            "hien thuc nghiem -- xem CL-10 lam tien le"
        ),
        "cells": rows,
    }


def b7_threshold(calib: pd.DataFrame, scale: str = "err") -> Dict[str, Any]:
    """Nguong du lieu dinh doat theo Chow reject rule, dat tren tuoi."""
    a_twin = calib["a_twin"].to_numpy(np.int64)
    a_fb = np.full(len(calib), FB.path_static_shortest(), dtype=np.int64)
    l_fb = float(FB.loss_of(calib, a_fb, scale).mean())
    loss_twin = FB.loss_of(calib, a_twin, scale)
    prof = (
        calib.assign(_l=loss_twin)
        .groupby("z_bin", sort=True)
        .agg(z_hi=("z_s", "max"), L_act=("_l", "mean"), n=("_l", "size"))
    )
    ok = prof.index[prof["L_act"].to_numpy() <= l_fb]
    h_star = float(prof.loc[ok, "z_hi"].max()) if len(ok) else 0.0
    return {
        "rule": "Chow(1970) reject rule, nguong dat tren z theo Sun et al.(2017)",
        "free_parameters": 0,
        "L_fallback": l_fb,
        "h_star_s": h_star,
        "profile": [
            {"z_bin": int(i), "z_hi": float(r.z_hi), "L_act": float(r.L_act), "n": int(r.n)}
            for i, r in prof.iterrows()
        ],
    }


def score_B7(
    calib: pd.DataFrame, test: pd.DataFrame, policy: str = "static",
) -> Dict[str, Any]:
    th = b7_threshold(calib)
    accept = test["z_s"].to_numpy(np.float64) <= th["h_star_s"]
    wrong = test["wrong"].to_numpy(bool)
    res = FB.apply_fallback(test, accept, policy)
    return {
        "procedure": "B7",
        "threshold": th,
        "acceptance": float(accept.mean()),
        "err_given_accept": float(wrong[accept].mean()) if accept.any() else float("nan"),
        "err_system": float(FB.loss_of(test, res["a_chosen"], "err").mean()),
        "has_no_coverage_claim": True,
        "_accept": accept,
    }


def wiring_parity(calib: pd.DataFrame, test: pd.DataFrame) -> Dict[str, Any]:
    """G23-289: duong scoring moi phai parity bit voi C3 hien hanh."""
    keys = CM._keys(POST_VARIANT)
    fit = CM.fit_config(
        calib, "C3", KAPPA_OP, alpha=ALPHA_FAMILY,
        post_variant=POST_VARIANT, multiplicity=MULTIPLICITY,
    )
    q_ref = CM._q_rows(test, keys, fit["_q"], len(CM.SIM_COLS))
    q_new = CM._q_rows(
        test, keys, fit_qhat_by_cell(calib, "C3"), len(CM.SIM_COLS),
    )
    both_inf = ~np.isfinite(q_ref) & ~np.isfinite(q_new)
    bit_equal = bool(
        np.array_equal(q_ref[~both_inf], q_new[~both_inf])
        and np.array_equal(np.isfinite(q_ref), np.isfinite(q_new))
    )
    finite = np.isfinite(q_ref) & np.isfinite(q_new)
    mine = score_procedure(calib, test, "C3")
    return {
        "qhat_bit_identical": bit_equal,
        "max_abs_diff": float(np.max(np.abs(q_ref[finite] - q_new[finite]))) if finite.any() else 0.0,
        "acceptance": mine["acceptance"],
        "viol_given_accept": mine["viol_given_accept"],
        "G23_289_pass": bit_equal,
    }


def negative_control(
    calib: pd.DataFrame, test: pd.DataFrame, n_draws: int = N_NC_DRAWS,
) -> Dict[str, Any]:
    """G23-290: xao nhan z_bin va do phan bo viol|accept cua C3."""
    rng = np.random.default_rng(SEED_NC)
    viols, accs = [], []
    for _ in range(int(n_draws)):
        c = calib.copy()
        t = test.copy()
        c["z_bin"] = rng.permutation(c["z_bin"].to_numpy())
        t["z_bin"] = rng.permutation(t["z_bin"].to_numpy())
        r = score_procedure(c, t, "C3")
        viols.append(r["viol_given_accept"])
        accs.append(r["acceptance"])
    v = np.asarray(viols, dtype=np.float64)
    return {
        "n_draws": int(n_draws),
        "viol_mean": float(np.nanmean(v)),
        "viol_p95": float(np.nanpercentile(v, 95)),
        "viol_max": float(np.nanmax(v)),
        "acceptance_mean": float(np.nanmean(accs)),
        "alpha_family": ALPHA_FAMILY,
        "break_band_lower_bound_required": float(np.nanpercentile(v, 95)),
        "note": (
            "dai tuyen VO cua G23-291 PHAI nam tren p95 nay. Neu khong -> "
            "DUNG, ky lai dai truoc khi chay nhanh chinh."
        ),
    }


def load_cell(mode: str, rho: float) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
    path = calib_path(mode, rho)
    df = pd.read_parquet(path)
    if "block_full" in df.columns:
        df = df[df["block_full"]].copy()
    original = df["is_calib"].to_numpy(bool) if "is_calib" in df.columns else None
    df = split_by_block(df)
    if original is not None and not np.array_equal(original, df["is_calib"].to_numpy(bool)):
        raise ValueError("split_by_block khong khop split is_calib da ghim trong parquet")
    return (
        df[df.is_calib].reset_index(drop=True),
        df[~df.is_calib].reset_index(drop=True),
        path,
    )


def _base_artifact(args: argparse.Namespace, path: str) -> Dict[str, Any]:
    return {
        "schema": "baselines_lit/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "amendment": AMENDMENT,
        "cell": "%s@%.3f" % (args.mode, args.rho),
        "config": {
            "post_variant": POST_VARIANT,
            "multiplicity": MULTIPLICITY,
            "alpha_family": ALPHA_FAMILY,
            "alpha_each": ALPHA_EACH,
            "kappa_op": KAPPA_OP,
            "n_margins": N_MARGINS,
        },
        "constants": {
            "K08_CV_MAX_FOLDED": CV_MAX_FOLDED,
            "Z_BONF": Z_BONF,
            "THETA_HI": THETA_HI,
            "BISECT_ITERS": BISECT_ITERS,
        },
        "provenance": {
            "git_head": git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(git("git", "status", "--porcelain")),
            "inputs": [pin(AMENDMENT), pin(path), pin(SLA_MANIFEST)],
        },
        "validity": validity_block(
            aoi_generator=AOI_V7,
            z_edges=Z_EDGES_V7,
            sla_path=SLA_MANIFEST,
            w_loss=W_LOSS,
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="poisson")
    ap.add_argument("--rho", type=float, default=0.925)
    ap.add_argument("--wiring", action="store_true", help="G23-289, chay dau tien")
    ap.add_argument("--negative", action="store_true", help="G23-290, chay thu hai")
    ap.add_argument("--run", action="store_true", help="G23-291..296")
    ap.add_argument("--out", default=OUTPUT)
    args = ap.parse_args(argv)
    if sum((args.wiring, args.negative, args.run)) != 1:
        ap.error("chon dung mot trong --wiring, --negative, --run")

    calib, test, path = load_cell(args.mode, args.rho)
    art = _base_artifact(args, path)
    if args.wiring:
        art["G23_289_wiring"] = wiring_parity(calib, test)
        if not art["G23_289_wiring"]["G23_289_pass"]:
            raise SystemExit("G23-289 FAIL: duong ong co nhanh re an. DUNG lesson.")
    elif args.negative:
        art["G23_290_negative_control"] = negative_control(calib, test)
    else:
        art["G23_292_structural"] = structural_test(calib)
        art["G23_295_refusal"] = refusal_audit(calib)
        art["procedures"] = {
            p: score_procedure(calib, test, p) for p in PROCEDURES
        }
        b7 = score_B7(calib, test)
        b7.pop("_accept", None)
        art["G23_296_B7"] = b7

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(json_clean(art), fh, indent=2, sort_keys=True)
    print("wrote %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
