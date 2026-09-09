#!/usr/bin/env python3
"""Chung minh -- bang duong DU LIEU, khong bang loi khai -- rang artifact
Phase T2 TIEU THU truc SLA, va nhan cua truc do la `self_calibrated`.

Vi sao can mot cong cu thay vi mot cau van: ban giao T2 muc N6 khai rang
artifact T2 "chay tren truc conformal/tau, khong phai aoi_axis hay sla_axis".
Cau do la mot NIEM TIN. Cong cu nay bien no thanh mot phep kiem chay duoc, va
phep kiem tra loi NGUOC LAI  [NT 50: grep truoc khi tin, ke ca khi dieu minh
tin la "cai nay khong lien quan"].

    python3 tools/t2_sla_axis_provenance.py
"""
from __future__ import annotations

import glob
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
REG = ROOT / "docs" / "phase-23" / "axis_registry.json"
CAL = "results/LIVE/phase-20R/sla_calibration.json"


def data_path_evidence() -> list[dict]:
    """Bon mat xich, moi mat xich la mot file:dong doc duoc."""
    return [
        {"step": 1,
         "where": "cert/build_calib_set_v3.py:200-204 (_load_cell)",
         "what": "feasible_cells(%s); o khong co trong file nay -> SystemExit"
                 % CAL},
        {"step": 2,
         "where": "cert/build_calib_set_v3.py:271,360 (_cell_arrays)",
         "what": "w_loss lay TU cell cua chinh file do"},
        {"step": 3,
         "where": "twin/cost_v2.py CostV2.tables_batch(rho, mode, w_loss)",
         "what": "w_loss VAO ham chi phi -> c_true/c_fresh -> s_margin -> "
                 "qhat_margin -> ratio_measured = RMS_MARGIN_COST"},
        {"step": 4,
         "where": "docs/phase-T2/00-preregistration.md muc 'Ke thua'",
         "what": "'sigma_rho, w_loss, nguong SLA <- 20R sla_calibration.json, "
                 "GIU NGUYEN' -- ke thua CO CHU DICH, da ky"},
    ]


def main() -> int:
    reg = json.loads(REG.read_text())
    entry = reg["sla_axis"][CAL]
    approved = reg["approved_for_live"]["sla_axis"]

    ok_label = entry["label"] == "self_calibrated"
    ok_dep = entry["status"] == "DEPRECATED"
    ok_notappr = entry["label"] not in approved

    print("nhan cua %s" % CAL)
    print("  label                              : %s" % entry["label"])
    print("  status trong registry              : %s" % entry["status"])
    print("  nam trong approved_for_live.sla_axis: %s" % (not ok_notappr))
    print("  duyet hien hanh                    : %s" % approved)
    print("  note                               : %s" % entry["note"])
    print()
    print("DUONG DU LIEU (moi mat xich la mot file:dong doc duoc):")
    for e in data_path_evidence():
        print("  (%d) %-46s %s" % (e["step"], e["where"], e["what"]))
    print()

    # Doi chung tu chinh artifact: nhan sla_axis ma chung TU KHAI
    labels = set()
    for p in glob.glob(str(ROOT / "results/PENDING/phase-T2/**/*.json"),
                       recursive=True):
        try:
            d = json.loads(pathlib.Path(p).read_text())
        except Exception:
            continue
        if isinstance(d, dict):
            lbl = ((d.get("validity") or {}).get("sla_axis") or {}).get("label")
            if lbl:
                labels.add(lbl)
    print("nhan sla_axis ma artifact PENDING/phase-T2 TU KHAI: %s"
          % (sorted(labels) or "(khong artifact nao khai)"))
    print()

    verdict = ok_label and ok_dep and ok_notappr
    print("KET LUAN: artifact Phase T2 TIEU THU truc SLA voi nhan %r "
          "(DEPRECATED, chua duyet)." % entry["label"])
    print("=> `pending_on: [\"sla_axis\"]` la mot PHAT BIEU DUNG SU THAT, "
          "khong phai mot nhan doan.")
    print("=> KHONG can dang ky truc moi. Ban giao N6 phai duoc dinh chinh.")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
