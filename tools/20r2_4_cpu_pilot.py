"""20R2.4 E3 -- PILOT do chi phi CPU that, khong ke thua hang so.

VI SAO VAN PHAI PILOT DU DA CO 1.1028 s/o
=========================================
`axis_audit.json` cho 1.1028 s/o, suy tu run_log cua `sweep_r2`. Nhung
`sweep_r2` chay o dieu kien KHAC:

    sweep_r2   SLA self_calibrated   luoi z  9 diem
    20R2       SLA exogenous         luoi z 13 diem   (prereg muc 4)

Mot hang so KHONG duoc ke thua qua ranh gioi dieu kien ma khong do lai. Do la
cung ky luat da bat loi RT20-4 (ti le 56x suy dien vs 1.4x do duoc).

HAI LUOI z -- va vi sao pilot do CA HAI
=======================================
    legacy         9 diem, phu mien [0.055, 0.550]
    20r2_measured 13 diem, phu mien measured [0.115, 0.615]   (prereg muc 4)

Do ca hai de TACH chi phi cua LUOI khoi chi phi cua MAY: neu chi do mot luoi
thi khong biet chenh lech den tu 13 diem hay tu may khac.

20R2-D3 (da go 2026-09-10): truoc day luoi 20R2 chi ton tai trong van ban
prereg, con ma chi co luoi legacy -- nen chay chien dich se lang le ra ket qua
truc legacy MA KHONG BAO LOI (ca hai luoi deu chay duoc). Gio CLI doi
`--z-grid` va khong co mac dinh.

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

# Luoi z cua 20R2 -- DOC TU MA, khong chep lai.
# Truoc 2026-09-10 tool nay giu mot BAN CHEP vi ma chua co ten nay (20R2-D3).
# Gio D3 da go, nen chep lai la tao mot nguon su that thu hai -- dung lop loi
# ma GLOSSARY canh bao khi mot hang so song o hai noi.
def _z_20r2():
    import measurements.decision_error_v2 as DE
    return tuple(float(z) for z in DE.Z_ALL_20R2)

INHERITED_S_PER_CELL = 1.1028   # axis_audit.json A7 corrected.seconds_per_cell
GATE_TOLERANCE = 0.30           # gate 4-3

# He so nang n song o artifact du doan DA KY, khong go tay o day.
MULT_SOURCE = "docs/phase-20R2/01-prediction-signed.json"


def _n_multiplier() -> dict:
    """He so nang n theo tau, DOC TU artifact da ky.

    G2 nang n tai tau=10/20/28 de moi o dat >= 200 chu ky doc lap. Nen ngan
    sach NEN (x1) KHONG con la con so se duoc doi chieu o gate 4-3 -- chien
    dich chay VOI he so.
    """
    path = REPO / MULT_SOURCE
    if not path.is_file():
        return {}
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {float(k): int(v)
            for k, v in doc["acceptance_band"]["n_multiplier"].items()}


# [20R2.5-P2] Truc SLA cua CHIEN DICH. Ngan sach da ky (74.53 phut) do TRUOC
# 20R2.5 nen chay tren mac dinh im lang self_calibrated -- xem prereg §16.
# KHONG can do lai, va ly do manh hon "thoi gian khong nhay voi truc":
# HAI truc cho DUNG 10 o kha thi nhu nhau (do duoc 2026-09-10), cung n, cung
# luoi z, nen moi mang co CUNG HINH DANG. Chi hang so vo huong w_loss doi,
# ma no khong doi khoi luong tinh. Ngan sach la ham cua hinh dang, khong phai
# cua gia tri.
CALIBRATION = "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json"


def _time_one(tau: float, z_values, out_path: str, multiplier: int = 1) -> float:
    import measurements.decision_error_v2 as DE
    from measurements.sla_calib_v2 import DEFAULT_DT, n_for_tau
    DE.Z_EXTRAP = (1.0, 2.0, 4.0)
    t0 = time.time()
    DE.run_fixed_grid(tau=tau, seeds=[SEEDS[0]], out_path=out_path,
                      calibration_path=CALIBRATION,          # [20R2.5-P2]
                      z_values=list(z_values),
                      n=n_for_tau(tau, DEFAULT_DT) * multiplier)
    return time.time() - t0


def run_pilot(taus) -> dict:
    import measurements.decision_error_v2 as DE
    legacy_z = tuple(float(z) for z in DE.Z_ALL)

    tmp = tempfile.mkdtemp()
    per_tau = []
    for tau in taus:
        s13 = _time_one(tau, _z_20r2(), os.path.join(tmp, "p13_%g.parquet" % tau))
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

    # --- ngan sach SAU khi nang n  [NT 50: doi NGUON thi phai xu ly PHAI SINH]
    #
    # DO, KHONG NGOAI SUY. Gia dinh "chi phi ti le tuyen tinh voi n" SAI:
    # do duoc tren may nay, nang n gap 4 ton 4.34x (tau=20) va 4.80x (tau=28)
    # -- TREN tuyen tinh. Ngoai suy tuyen tinh se UOC THAP ~10%, va mot uoc
    # tinh thap chinh la thu lam gate 4-3 truot khi chay that.
    mult = _n_multiplier()
    scaled_measured = []
    if mult and len(taus) == len(TAUS):
        for r in per_tau:
            m = mult.get(r["tau"], 1)
            if m == 1:
                secs = r["seconds_z20r2"]
                how = "measured_x1"
            else:
                secs = _time_one(
                    r["tau"], _z_20r2(),
                    os.path.join(tempfile.mkdtemp(), "scaled.parquet"),
                    multiplier=m)
                how = "measured_x%d" % m
            scaled_measured.append({
                "tau": r["tau"], "n_multiplier": m, "seconds": secs,
                "how": how,
                "ratio_vs_x1": secs / r["seconds_z20r2"],
            })
        branch_scaled = (sum(x["seconds"] for x in scaled_measured)
                         * len(A_VALUES) * len(SEEDS))
    else:
        branch_scaled = None

    # Gate 4-3 doi chieu voi ngan sach THAT SU se chay = ban DA NANG.
    gate_seconds = branch_scaled if branch_scaled else branch_s
    gate_s_per_cell = gate_seconds / n_cells
    drift = (s_per_cell - INHERITED_S_PER_CELL) / INHERITED_S_PER_CELL

    return {
        "schema": "dt4n.cpu_pilot.v1",
        "validity": _validity(),
        "generated_by": "tools/20r2_4_cpu_pilot.py",
        "measured_taus": list(taus),
        "extrapolated_from_subset": len(taus) != len(TAUS),
        "z_grids": {
            "z_20r2_prereg": list(_z_20r2()),
            "n_z_20r2": len(_z_20r2()),
            "z_legacy_in_code": list(legacy_z),
            "n_z_legacy": len(legacy_z),
            "d3_status": (
                "20R2-D3 DA GO 2026-09-10: ca hai luoi nam trong "
                "decision_error_v2.Z_GRIDS va CLI doi --z-grid (required=True). "
                "Truoc do luoi 20R2 chi ton tai trong van ban prereg, nen chay "
                "chien dich se lang le ra ket qua truc legacy MA KHONG BAO LOI."),
            "same_max_by_design": (
                "max(legacy) == max(20r2_measured) == 4.0 CO CHU DICH: "
                "scoring_window_start lay max cua luoi, nen hai luoi cham diem "
                "tren CUNG dai hang va so duoc voi nhau."),
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
            # --- ban DA NANG n. Day moi la ngan sach chien dich THAT SU chay.
            "n_multiplier_source": MULT_SOURCE,
            "n_multiplier": {str(k): v for k, v in sorted(mult.items())} or None,
            "scaled_per_tau_measured": scaled_measured or None,
            "scaling_is_measured_not_extrapolated": bool(scaled_measured),
            "why_not_linear": (
                "chi phi KHONG ti le tuyen tinh voi n: do duoc 4.34x (tau=20) "
                "va 4.80x (tau=28) cho mot lan nang x4. Ngoai suy tuyen tinh "
                "uoc THAP ~10%, va uoc thap la thu lam gate 4-3 truot khi chay "
                "that."),
            "seconds_one_branch_scaled": branch_scaled,
            "minutes_one_branch_scaled": (branch_scaled / 60.0) if branch_scaled else None,
            "minutes_two_branches_scaled": (branch_scaled / 30.0) if branch_scaled else None,
            "minutes_two_branches_scaled_plus_30pct": (
                branch_scaled / 30.0 * 1.3) if branch_scaled else None,
            "seconds_per_cell_scaled": (gate_s_per_cell if branch_scaled else None),
            "which_number_the_campaign_will_take": (
                "minutes_two_branches_scaled" if branch_scaled
                else "minutes_two_branches (chua nang -- ban --quick)"),
            "why_scaled_exists": (
                "G2 nang n tai tau=10 (x2), 20 va 28 (x4) de moi o dat >= 200 "
                "chu ky doc lap. Ban NEN (x1) chi de truy nguon. Doi NGUON ma "
                "khong xu ly PHAI SINH la NT 50 -- va o day hau qua cu the la "
                "gate 4-3 doc con so nen roi so voi thoi gian chay THAT, thay "
                "lech ~110%, va TRUOT OAN."),
        },
        "gate_4_3": {
            "inherited_seconds_per_cell": INHERITED_S_PER_CELL,
            "measured_seconds_per_cell": s_per_cell,
            "relative_drift": drift,
            "tolerance": GATE_TOLERANCE,
            # --quick do 3 tau roi nhan 8/3. Nhung QUICK_TAUS chua tau=28 --
            # tau DAT NHAT -- nen mau 3 diem THIEN LECH LEN va uoc tinh cao hon
            # thuc. Do duoc: quick cho FAIL trong khi ban day du cho PASS.
            # Mot uoc tinh thien lech KHONG duoc phep phan quyet mot gate, nen
            # ban quick tu khai la khong co tham quyen thay vi im lang tra
            # mot verdict sai.
            "verdict": ("NOT_AUTHORITATIVE" if len(taus) != len(TAUS)
                        else ("PASS" if abs(drift) <= GATE_TOLERANCE else "FAIL")),
            "authoritative": len(taus) == len(TAUS),
            "why_quick_is_not_authoritative": (
                "QUICK_TAUS = %s chua tau dat nhat (%g), nen ngoai suy x%.2f "
                "thien lech LEN. Dung --quick de kiem DAY CHUYEN, khong de "
                "phan quyet gate." % (QUICK_TAUS, max(QUICK_TAUS),
                                      len(TAUS) / len(QUICK_TAUS))),
            "why_it_drifts": (
                "luoi z 13 diem thay vi 9 (+~12%%, DUOI tuyen tinh vi sinh "
                "trace moi la phan dat, khong phai vong z) va may khac voi may "
                "da sinh run_log cua sweep_r2."),
        },
        "e4_fractional_design": {
            "needed": False,
            "threshold_hours": 8.0,
            "measured_minutes_two_branches": (branch_scaled / 30.0
                                              if branch_scaled else branch_s / 30.0),
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
    print("MOT nhanh (nen)   : %.2f phut" % b["minutes_one_branch"])
    print("HAI nhanh (nen)   : %.2f phut  (+30%%: %.2f)"
          % (b["minutes_two_branches"], b["minutes_two_branches_plus_30pct"]))
    print("s/o do duoc       : %.4f" % b["seconds_per_cell"])
    if b["minutes_two_branches_scaled"]:
        print("\n  he so nang n     : %s" % b["n_multiplier"])
        print("  HAI nhanh DA NANG: %.2f phut  (+30%%: %.2f)   <- CHIEN DICH CHAY SO NAY"
              % (b["minutes_two_branches_scaled"],
                 b["minutes_two_branches_scaled_plus_30pct"]))
        print("  s/o da nang      : %.4f" % b["seconds_per_cell_scaled"])
    print("\ngate 4-3: ke thua %.4f -> do duoc %.4f  = %+.1f%%  [%s, nguong +-%d%%]"
          % (g["inherited_seconds_per_cell"], g["measured_seconds_per_cell"],
             g["relative_drift"] * 100, g["verdict"], g["tolerance"] * 100))
    print("E4 phan doan      : %s" % ("CAN" if doc["e4_fractional_design"]["needed"] else "KHONG CAN"))
    print("\n-> %s" % os.path.relpath(args.out, REPO))


if __name__ == "__main__":
    main()
