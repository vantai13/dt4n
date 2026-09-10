#!/usr/bin/env python3
"""20R2.5 -- DOI CHUNG TWIN-HOAN-HAO, chay QUA CHINH run_cell.   [20R2.5-P4]

VI SAO PHAI VIET LAI
====================
prereg §13.5 goi doi chung twin-hoan-hao la "phep kiem dung cu that" cua 20R2.
Nhung ban cu (NC1b trong decision_error_v2.controls) la:

    a_true = c_true.argmin(axis=1)
    nc1b   = float((c_true.argmin(axis=1) != a_true).mean())

tuc so MOT THU VOI CHINH NO -- mot menh de LUON DUNG, bang 0 vi dai so chu
khong vi dung cu dung. No con KHONG goi run_cell, nen khong cham toi lag, cua
so cham diem, hay dispatch luoi z. Test canh no chi kiem rang MOT CAU VAN co
trong docstring.

KILL TEST (mutation testing, do 2026-09-10) -- cay loi lech-mot vao run_cell,
`lag_rows = current - k - 1`, o h2@0.700, tau=3, luoi 20r2_measured:

    doi chung MOI (qua run_cell)  err_total(z=0) = 0.026315   BAT DUOC
    NC1b CU                                        0.0        MU

HOP DONG (moi o, moi z) -- va day la cho nguoi moi hay sai:
  "twin hoan hao" KHONG co nghia err = 0 o moi z. Twin hoan hao ve MO HINH
  van dung du lieu CU. Hop dong dung la:

    err_model == 0 . rms_e_model == 0 . err_total == err_stale
    err_total(z = 0) == 0
    + DOI CHUNG CUA DOI CHUNG: ton tai z > 0 co err_total > 0. Neu khong,
      lag khong lam gi ca va hop dong thoa mot cach TAM THUONG (den xanh rong).

Chi chay a = 0.9: duong ong khong phu thuoc a ngoai duong sigma. ~3-4 phut.

    python -m tools.20r2_5_perfect_twin \\
        --calibration results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json \\
        --out results/SMOKE/phase-20R2/perfect_twin_pre.json

Ma thoat 0 = PASS, 1 = FAIL.
"""
from __future__ import annotations

import argparse
import importlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--taus", default="", help="danh sach tau, mac dinh: lay tu ke hoach")
    a = ap.parse_args(argv)

    import measurements.decision_error_v2 as DE
    from measurements.sla_calib_v2 import DEFAULT_DT, n_for_tau
    if a.taus:
        taus = tuple(float(x) for x in a.taus.split(","))
    else:
        # W4: MOT nguon su that cho luoi tau. Ten module bat dau bang chu so
        # nen khong import binh thuong duoc.
        taus = importlib.import_module("tools.20r2_5_plan").TAUS

    blocks = []
    for grid in sorted(DE.Z_GRIDS):
        for tau in taus:
            rep = DE.perfect_twin_control(
                a.calibration, tau=float(tau),
                n=int(n_for_tau(float(tau), DEFAULT_DT)), seed=999,
                z_values=DE.Z_GRIDS[grid], a_override=0.9)
            rep["z_grid"] = grid
            blocks.append(rep)
            print("  %-14s tau=%-5g  %4d diem, %d vi pham, max err(z>0)=%.4f" % (
                grid, tau, rep["n_checked"], len(rep["violations"]),
                rep["max_err_total_z_positive"]))

    n_viol = sum(len(b["violations"]) for b in blocks)
    # DOI CHUNG CUA DOI CHUNG: neu khong o dau co err > 0 tai z > 0 thi lag
    # khong lam gi, va "0 vi pham" khong chung minh duoc gi.
    nontrivial = any(b["max_err_total_z_positive"] > 0.0 for b in blocks)
    verdict = "PASS" if n_viol == 0 and nontrivial else "FAIL"

    doc = {
        "schema": "dt4n.perfect_twin_20r2_5.v1",
        "generated_by": "tools/20r2_5_perfect_twin.py",
        "WHAT_THIS_IS": ("DOI CHUNG DUNG CU qua run_cell -- KHONG phai ket qua "
                         "khoa hoc. No khong tra loi mot RQ nao."),
        "replaces": ("NC1b_perfect_twin trong decision_error_v2.controls, von la "
                     "mot menh de luon dung va khong goi run_cell [20R2.5-P4]"),
        "contract": ["err_model == 0", "rms_e_model == 0",
                     "err_total == err_stale", "err_total(z=0) == 0",
                     "ton tai z > 0 co err_total > 0 (doi chung cua doi chung)"],
        "calibration": a.calibration,
        "n_checked": sum(b["n_checked"] for b in blocks),
        "n_violations": n_viol,
        "control_of_control_nontrivial": nontrivial,
        "verdict": verdict,
        "blocks": blocks,
    }
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("perfect twin: %s (%d diem kiem, %d vi pham, nontrivial=%s)" % (
        verdict, doc["n_checked"], n_viol, nontrivial))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
