#!/usr/bin/env python3
"""A-T2-3 (e) -- bang chap nhan tinh lai tren DUNG estimand.

02-band-window.json cu lay se tu ti so err_total tren z_over_tau co dinh
(RMS_ALLACTION_DELAY, nhanh A). Diem du doan la RMS_MARGIN_COST, nhanh B.
BA cho lech. File nay tinh lai se tren DUNG estimand.

KHONG VONG TRON: se lay tu luoi tau CU {0.5 .. 5} -- du lieu 22.6 DA CONG BO
-- phan tich lai THEO SEED. Khong dung mot byte nao cua luoi moi.

XAP XI PHAI KHAI: se do tren khoang [0.5, 5] dung lam SAN cho ti so tren
khoang [0.5, 28]. se cua mot LOG-TI SO on dinh theo do dai khoang, nen day
la san BAO THU. Khai o day, khong giau.

    python3 tools/t2_6b_band.py
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import subprocess
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import cert.tau_sweep as TS

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/phase-T2/05-band-window-v2.json"

CELLS = (("h2", 0.700), ("poisson", 0.850), ("poisson", 0.925), ("cbr", 0.700))
SEEDS = (101, 102, 103, 104, 105)
TAU_LO, TAU_HI = 0.5, 5.0
K_SIGMA = 3.0          # QD-7, KHONG DOI
BAND_FLOOR = 0.05      # QD-7, KHONG DOI
Z_FIXED = (0.05, 0.10, 0.30, 0.55)


def _git(*a: str) -> str:
    try:
        return subprocess.check_output(["git", *a], text=True, cwd=ROOT).strip()
    except Exception:
        return "unknown"


def _fit(mode, rho_bar, tau, seed):
    df = TS.build_at_tau(mode, rho_bar, tau, seeds=(seed,),
                         n=200_000, sigma=TS.SIGMA_LEGACY_22_6)
    return TS.fit_ar1(TS.decompose(df), tau)


def _rms(fit, tau, z_s):
    A, c, em = fit["A"], fit["c"], fit["rms_e_model"]
    return math.sqrt(em ** 2 + c * A ** 2 * (1.0 - math.exp(-z_s / tau)))


def main() -> int:
    windows, disp = {}, {}
    for mode, rb in CELLS:
        key = "%s@%.3f" % (mode, rb)
        per_seed = []
        for s in SEEDS:
            f_lo = _fit(mode, rb, TAU_LO, s)
            f_hi = _fit(mode, rb, TAU_HI, s)
            r = [_rms(f_hi, TAU_HI, z) / _rms(f_lo, TAU_LO, z) for z in Z_FIXED]
            per_seed.append(float(np.mean(r)))
        arr = np.array(per_seed, dtype=float)
        sd = float(arr.std(ddof=1))
        se = sd / math.sqrt(len(SEEDS))
        disp[key] = {"n_seed": len(SEEDS), "dof": len(SEEDS) - 1,
                     "ratio_mean": float(arr.mean()),
                     "sd_between_seed": sd, "se": se,
                     "per_seed": per_seed}
        windows[key] = {
            "band_floor_from_noise": K_SIGMA * se,
            "recommended_band": max(K_SIGMA * se, BAND_FLOOR),
            "se_used": se,
            "binding_constraint": ("floor" if K_SIGMA * se < BAND_FLOOR
                                   else "noise"),
        }
        print("  %-16s se=%.6f  band=%.4f (%s)"
              % (key, se, windows[key]["recommended_band"],
                 windows[key]["binding_constraint"]))

    OUT.write_text(json.dumps({
        "schema": "dt4n.band_window.v2",
        "authority": "docs/phase-T2/00-preregistration.md muc A-T2-3 (e)",
        "estimand_id": TS.ESTIMAND_ID,
        "branch": "z_fixed",
        "supersedes": "docs/phase-T2/02-band-window.json",
        "parameters": {"k_sigma": K_SIGMA, "band_floor": BAND_FLOOR,
                       "n_seed": len(SEEDS), "tau_lo": TAU_LO,
                       "tau_hi": TAU_HI, "z_fixed_s": list(Z_FIXED)},
        "approximation_declared": (
            "se do tren khoang [0.5, 5] dung lam SAN cho ti so tren khoang "
            "[0.5, 28]. se cua log-ti so on dinh theo do dai khoang => san "
            "BAO THU. Khai TRUOC khi chay luoi chinh."),
        "no_circularity": (
            "moi so o day suy tu luoi tau CU (22.6 da cong bo, sigma=0.0096, "
            "n=200000), phan tich lai theo tung seed. KHONG dung du lieu "
            "sweep_r3 luoi moi."),
        "provenance": {"script": "tools/t2_6b_band.py",
                       "amendment": "A-T2-3",
                       "git_commit": _git("rev-parse", "HEAD"),
                       "git_dirty": bool(_git("status", "--porcelain"))},
        "dispersion": disp,
        "windows": windows,
    }, indent=1, sort_keys=True) + "\n")
    print("-> %s" % OUT.relative_to(ROOT))
    print("   sha256 %s" % hashlib.sha256(OUT.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
