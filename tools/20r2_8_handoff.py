#!/usr/bin/env python3
"""20R2.8 -- BAN GIAO cho 21R2: do lai tren dieu kien 20R2 cai gi DINH DANH DUOC.

★ CANH BAO ESTIMAND -- doc truoc khi dung bang nay
==================================================
Co HAI dai luong khac nhau cung ten cot `rms_e_model`:

  decision_error_v2.rms_e_model  = RMS_ALLACTION_DELAY  (all_action, delay_ms)
  cert/tau_sweep.py rms_e_model  = margin, cost_ms      (di qua w_loss)

decision_error_v2.py:56-58 da ghi ro lich su: hai cai nay TUNG bi doc lan nhau va
lam T2.6 luot 2 do SAI dai luong so voi du doan da ky (A-T2-3).

Bang `em/A` o prereg §13.5 KE THUA so cua T2, va nguon cua no la
results/PENDING/phase-T2/sweep_r3 = `cert.tau_sweep`, TUC estimand margin/cost_ms.
=> KHONG duoc "nang cap" bang do bang so cua chien dich 20R2: chien dich dung
   decision_error_v2, tuc estimand KHAC. So sanh hai cot do la lap lai A-T2-3.
=> D4/D5 vi the CHI dong duoc bang `cert.tau_sweep` chay tren dieu kien 20R2.

CAI GI DINH DANH DUOC TU PARQUET CHIEN DICH
===========================================
Luat rms (cert/tau_sweep.py:268): rms_total(z) = sqrt(em^2 + c*A^2*(1 - e^(-z/tau)))

  em  DINH DANH DUOC TRUC TIEP. `rms_e_model` KHONG phu thuoc z -- do duoc: dung
      MOT gia tri o ca 13 diem z (vd poisson@0.850: 0.328274 o moi z).
  A   KHONG dinh danh duoc. Luat chi cho TICH `c*A^2` nhu MOT tham so, nen khong
      tach duoc A khoi c. Vi vay `em/A` va `span_ratio_to_pure` KHONG tinh duoc
      tu day, va tool nay KHONG bia ra chung.

    python -m tools.20r2_8_handoff --out docs/phase-20R2/08-handoff-measurements.json
"""
from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAN = "docs/phase-20R2/03-run-plan.json"
T2_SRC = "results/PENDING/phase-T2/rt24_bias_decomposition.json"
ESTIMAND_HERE = "RMS_ALLACTION_DELAY"
ESTIMAND_T2 = "margin / cost_ms (cert.tau_sweep) -- KHAC estimand, KHONG so sanh duoc"


def load_main() -> pd.DataFrame:
    plan = json.loads((ROOT / PLAN).read_text(encoding="utf-8"))
    fr = []
    for r in plan["runs"]:
        if r["is_canary"] or r["branch"] != "main":
            continue
        d = pd.read_parquet(ROOT / r["out"])
        d["a"] = float(r["a"])
        fr.append(d)
    return pd.concat(fr, ignore_index=True)


def em_table(d: pd.DataFrame) -> list:
    """em = rms_e_model, DO tren dieu kien 20R2 (exogenous SLA, luoi 20r2_measured).

    Kem BANG CHUNG rang em khong phu thuoc z -- neu no phu thuoc, ca luat rms sai.
    """
    out = []
    for (m, rb, a), g in d.groupby(["mode", "rho_bar", "a"]):
        per_z = g.groupby("z_s")["rms_e_model"].mean()
        out.append({
            "cell": "%s@%.3f" % (m, float(rb)), "a": float(a),
            "em_bar_20r2": float(per_z.mean()),
            "em_spread_over_z": float(per_z.max() - per_z.min()),
            "em_is_z_independent": bool((per_z.max() - per_z.min()) < 1e-9),
            "n_z": int(len(per_z)),
            "estimand": ESTIMAND_HERE,
            "conditions": "SLA exogenous_g114_S-B, luoi 20r2_measured, 5 seed, 8 tau",
            "source": "measured_20R2 (chien dich 20R2.5)",
        })
    return sorted(out, key=lambda r: (r["cell"], -r["a"]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    d = load_main()
    rows = em_table(d)

    bad = [r for r in rows if not r["em_is_z_independent"]]
    if bad:
        raise AssertionError("em PHU THUOC z o %d o -> luat rms sai: %r"
                             % (len(bad), [r["cell"] for r in bad][:3]))

    t2 = json.loads((ROOT / T2_SRC).read_text(encoding="utf-8"))
    t2_missing = sorted({"%s a=%.1f" % (c["cell"], c["a"]) for c in t2["cells"]
                         if c.get("em_bar") is None})

    doc = {
        "schema": "dt4n.handoff_20r2_8.v1", "generated_by": "tools/20r2_8_handoff.py",
        "WHAT_THIS_IS": ("BAN GIAO. Do lai tren dieu kien 20R2 cai gi DINH DANH DUOC "
                         "tu parquet chien dich. KHONG phai phan quyet."),
        "ESTIMAND_WARNING": {
            "this_table": ESTIMAND_HERE,
            "t2_em_over_A_table": ESTIMAND_T2,
            "why_not_comparable": (
                "Bang em/A o prereg §13.5 ke thua tu results/PENDING/phase-T2/sweep_r3 "
                "= cert.tau_sweep, tuc estimand margin/cost_ms. Chien dich 20R2 dung "
                "decision_error_v2, tuc RMS_ALLACTION_DELAY (all_action, delay_ms). "
                "HAI DAI LUONG KHAC NHAU CUNG TEN COT. So sanh chung la lap lai DUNG "
                "loi A-T2-3 (decision_error_v2.py:56-58)."),
            "consequence": ("D4/D5 KHONG dong duoc bang du lieu chien dich. Chung CHI "
                            "dong duoc bang cert.tau_sweep chay tren dieu kien 20R2."),
        },
        "identifiability": {
            "law": "rms_total(z) = sqrt(em^2 + c*A^2*(1 - exp(-z/tau)))  [tau_sweep.py:268]",
            "em": "DINH DANH DUOC -- rms_e_model khong phu thuoc z (do duoc, xem em_spread_over_z)",
            "A": ("KHONG dinh danh duoc -- luat chi cho TICH c*A^2 nhu MOT tham so. "
                  "Nen em/A va span_ratio_to_pure KHONG tinh duoc tu day."),
        },
        "em_measured_on_20r2": rows,
        "n_rows": len(rows),
        "closes_partially": {
            "20R2-D5": ("cbr@0.850 GIO DA CO em do tren dieu kien 20R2 (hai gia tri a) -- "
                        "nhung o estimand RMS_ALLACTION_DELAY, KHONG phai estimand cua "
                        "bang em/A. D5 nhu da phat bieu VAN MO."),
        },
        "t2_rows_missing_em": t2_missing,
    }
    (ROOT / a.out).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("em DO TREN DIEU KIEN 20R2  (estimand %s)" % ESTIMAND_HERE)
    print("%-15s %4s %12s %16s" % ("o", "a", "em_bar", "khong-phu-thuoc-z"))
    for r in rows:
        print("%-15s %4.1f %12.5f %16s" % (r["cell"], r["a"], r["em_bar_20r2"],
                                           r["em_is_z_independent"]))
    print("\n%d hang. em khong phu thuoc z o CA %d hang (bang chung cho luat rms)."
          % (len(rows), len(rows)))
    print("⚠️  KHONG so sanh voi bang em/A cua T2: KHAC ESTIMAND (xem ESTIMAND_WARNING).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
