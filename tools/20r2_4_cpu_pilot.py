"""20R2.4 E3 -- PILOT do chi phi CPU that, khong ke thua hang so.

VI SAO VAN PHAI PILOT DU DA CO 1.1028 s/o
=========================================
`axis_audit.json` cho 1.1028 s/o, suy tu run_log cua `sweep_r2`. Nhung
`sweep_r2` chay o dieu kien KHAC:

    sweep_r2   SLA self_calibrated   luoi z  9 diem
    20R2       SLA exogenous         luoi z 13 diem   (prereg muc 4)

Mot hang so KHONG duoc ke thua qua ranh gioi dieu kien ma khong do lai. Do la
cung ky luat da bat loi RT20-4 (ti le 56x suy dien vs 1.4x do duoc).

CANH BAO -- LUOI z 20R2 CHUA CO TRONG MA
========================================
Do duoc 2026-09-10:
    measurements/decision_error_v2.py:76  Z_GRID = (0.0, 0.05, 0.10, 0.20,
                                                    0.30, 0.55)
    -> 6 diem + 3 ngoai suy = 9. Day la luoi LEGACY.
    prereg muc 4 khai Z_GRID_20R2_MEASURED = 9 diem measured + 1 doi chung
    + 3 ngoai suy = 13, nhung KHONG co ten do trong ma.

=> Chay chien dich HOM NAY se lang le dung luoi LEGACY, dung cai loi ma
   prereg muc A3' da chi ra ("luoi z tien dang ky phu KHIT mien legacy").
   Pilot nay do CA HAI luoi de tach chi phi cua luoi khoi chi phi cua may.

Chay:
    python -m tools.20r2_4_cpu_pilot --out results/PENDING/phase-20R2/cpu_pilot.json
    python -m tools.20r2_4_cpu_pilot --out ... --quick   # 3 tau thay vi 8
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import pathlib
import statistics
import tempfile
import time

REPO = pathlib.Path(__file__).resolve().parents[1]

TAUS = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 28.0]
QUICK_TAUS = [0.5, 3.0, 28.0]
A_VALUES = [0.5, 0.9]
SEEDS = [101, 102, 103, 104, 105]

# Luoi z cua 20R2 -- prereg muc 4. Ghi o day vi ma CHUA co ten nay.
Z_20R2 = (0.0,
          0.115, 0.170, 0.241, 0.305, 0.366, 0.430, 0.491, 0.555, 0.615,
          1.0, 2.0, 4.0)

INHERITED_S_PER_CELL = 1.1028   # axis_audit.json A7 corrected.seconds_per_cell
GATE_TOLERANCE = 0.30           # gate 4-3


def _time_one(tau: float, z_values, out_path: str) -> float:
    import measurements.decision_error_v2 as DE
    from measurements.sla_calib_v2 import DEFAULT_DT, n_for_tau
    DE.Z_EXTRAP = (1.0, 2.0, 4.0)
    t0 = time.time()
    DE.run_fixed_grid(tau=tau, seeds=[SEEDS[0]], out_path=out_path,
                      z_values=list(z_values), n=n_for_tau(tau, DEFAULT_DT))
    return time.time() - t0


def run_pilot(taus) -> dict:
    import measurements.decision_error_v2 as DE
    legacy_z = tuple(float(z) for z in DE.Z_ALL)

    tmp = tempfile.mkdtemp()
    per_tau = []
    for tau in taus:
        s13 = _time_one(tau, Z_20R2, os.path.join(tmp, "p13_%g.parquet" % tau))
        s9 = _time_one(tau, legacy_z, os.path.join(tmp, "p09_%g.parquet" % tau))
        per_tau.append({"tau": tau,
                        "seconds_z20r2": s13,
                        "seconds_zlegacy": s9,
                        "z20r2_over_legacy": s13 / s9})

    import pandas as pd
    df = pd.read_parquet(os.path.join(tmp, "p13_%g.parquet" % taus[0]))
    cells_per_cmd = df.groupby(["mode", "rho_bar"]).ngroups
    z_seen = int(df["z_s"].nunique())

    tot13 = sum(r["seconds_z20r2"] for r in per_tau)
    tot9 = sum(r["seconds_zlegacy"] for r in per_tau)
    scale = len(TAUS) / len(taus)          # neu chay --quick thi ngoai suy
    branch_s = tot13 * scale * len(A_VALUES) * len(SEEDS)
    n_cells = cells_per_cmd * len(TAUS) * len(A_VALUES) * len(SEEDS)
    s_per_cell = branch_s / n_cells
    drift = (s_per_cell - INHERITED_S_PER_CELL) / INHERITED_S_PER_CELL

    return {
        "schema": "dt4n.cpu_pilot.v1",
        "validity": _validity(),
        "generated_by": "tools/20r2_4_cpu_pilot.py",
        "measured_taus": list(taus),
        "extrapolated_from_subset": len(taus) != len(TAUS),
        "z_grids": {
            "z_20r2_prereg": list(Z_20R2),
            "n_z_20r2": len(Z_20R2),
            "z_legacy_in_code": list(legacy_z),
            "n_z_legacy": len(legacy_z),
            "WARNING": (
                "Luoi 20R2 KHONG co trong ma (decision_error_v2.py:76 van la "
                "Z_GRID legacy 6+3). Pilot nay TRUYEN luoi 20R2 qua tham so "
                "z_values. Chay chien dich ma khong sua ma se dung luoi LEGACY."),
        },
        "per_tau": per_tau,
        "harness": {
            "cells_per_command": cells_per_cmd,
            "z_values_seen": z_seen,
            "rows_per_command": cells_per_cmd * z_seen,
        },
        "budget": {
            "seconds_8tau_one_a_one_seed_z20r2": tot13 * scale,
            "seconds_8tau_one_a_one_seed_zlegacy": tot9 * scale,
            "n_grid_cells": n_cells,
            "seconds_one_branch": branch_s,
            "minutes_one_branch": branch_s / 60.0,
            "minutes_two_branches": branch_s / 60.0 * 2,
            "minutes_two_branches_plus_30pct": branch_s / 60.0 * 2 * 1.3,
            "seconds_per_cell": s_per_cell,
        },
        "gate_4_3": {
            "inherited_seconds_per_cell": INHERITED_S_PER_CELL,
            "measured_seconds_per_cell": s_per_cell,
            "relative_drift": drift,
            "tolerance": GATE_TOLERANCE,
            "verdict": "PASS" if abs(drift) <= GATE_TOLERANCE else "FAIL",
            "why_it_drifts": (
                "luoi z 13 diem thay vi 9 (+~12%%, DUOI tuyen tinh vi sinh "
                "trace moi la phan dat, khong phai vong z) va may khac voi may "
                "da sinh run_log cua sweep_r2."),
        },
        "e4_fractional_design": {
            "needed": False,
            "threshold_hours": 8.0,
            "measured_minutes_two_branches": branch_s / 60.0 * 2,
            "why": (
                "E4 doi thiet ke phan doan neu ngan sach > 8 gio. Do duoc chi "
                "~%.0f phut cho hai nhanh, tuc ~%.1f%% nguong. KHONG can phan "
                "doan -- va ly do duoc GHI RA thay vi de trong."
                % (branch_s / 60.0 * 2, branch_s / 60.0 * 2 / 480.0 * 100)),
        },
    }



def _validity() -> dict:
    """Artifact nay CHO gi de duoc promote khoi PENDING/.

    PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE. Khai chinh xac truc
    nao chua duyet, neu khong artifact se nam quen o day.
    """
    return {
        "schema": "dt4n.validity.v1",
        "axis_role": "cpu_pilot",
        "pending_on": ["aoi_axis", "sla_axis"],
        "aoi_axis": {
            "label": "UNREGISTERED",
            "z_grid_s": [],
            "note": "chi phi do bang cach TRUYEN luoi z 20R2 qua tham so; harness van dung luoi legacy (20R2-D3). Con so 35.7 phut chi dung sau khi noi luoi vao ma.",
        },
        "sla_axis": {
            "label": "UNREGISTERED",
            "match_method": "none",
            "note": "cho A5 (prereg muc 3) duoc KY; chua chay tren mot truc SLA nao",
        },
        "omega": None,
        "w_loss": None,
        "note": "chi phi do bang cach TRUYEN luoi z 20R2 qua tham so; harness van dung luoi legacy (20R2-D3). Con so 35.7 phut chi dung sau khi noi luoi vao ma.",
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--quick", action="store_true",
                    help="3 tau thay vi 8 (ngoai suy; ghi co trong artifact)")
    args = ap.parse_args()

    doc = run_pilot(QUICK_TAUS if args.quick else TAUS)
    doc["generated_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, ensure_ascii=True)
        fh.write("\n")

    b, g = doc["budget"], doc["gate_4_3"]
    print("=== 20R2.4 E3: pilot chi phi CPU ===")
    print("luoi z 20R2 = %d diem | luoi z trong MA = %d diem  <- CHUA SUA"
          % (doc["z_grids"]["n_z_20r2"], doc["z_grids"]["n_z_legacy"]))
    print("\ntau     z20R2(s)  legacy(s)  ti so")
    for r in doc["per_tau"]:
        print("%5.1f   %7.2f   %8.2f   %.3f"
              % (r["tau"], r["seconds_z20r2"], r["seconds_zlegacy"],
                 r["z20r2_over_legacy"]))
    print("\no/lenh            : %d" % doc["harness"]["cells_per_command"])
    print("tong o            : %d" % b["n_grid_cells"])
    print("MOT nhanh         : %.2f phut" % b["minutes_one_branch"])
    print("HAI nhanh         : %.2f phut  (+30%%: %.2f)"
          % (b["minutes_two_branches"], b["minutes_two_branches_plus_30pct"]))
    print("s/o do duoc       : %.4f" % b["seconds_per_cell"])
    print("\ngate 4-3: ke thua %.4f -> do duoc %.4f  = %+.1f%%  [%s, nguong +-%d%%]"
          % (g["inherited_seconds_per_cell"], g["measured_seconds_per_cell"],
             g["relative_drift"] * 100, g["verdict"], g["tolerance"] * 100))
    print("E4 phan doan      : %s" % ("CAN" if doc["e4_fractional_design"]["needed"] else "KHONG CAN"))
    print("\n-> %s" % os.path.relpath(args.out, REPO))


if __name__ == "__main__":
    main()
