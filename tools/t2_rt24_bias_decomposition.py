#!/usr/bin/env python3
"""RT2-4: bien do duong R(tau) do TAU hay do SAN MO HINH tinh (em) chi phoi?

Phan ra DA CO SAN trong chinh luat rms:
    rms_total(z, tau) = sqrt( em^2 + c*A^2*(1 - exp(-z/tau)) )
                             ^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^
                        SAN MO HINH  BIEN DO THEO TUOI (tau vao o day)
`em` CHINH LA bias tinh, nen khong can "tru di" -- chi can DAT em = 0.

Va khi em = 0, A va c TRIET TIEU chinh xac:
    R(tau) = sqrt( (1 - e^(-z3/tau)) / (1 - e^(-z0/tau)) )
=> con lai MOT duong tau THUAN, giong nhau o MOI o. Do la mau so tu nhien,
   khong phai mot lua chon tuy tien: no la gioi han cua chinh cong thuc khi
   san mo hinh bi dua ve 0.

CHI DOC. Khong sinh lai, khong fit lai, khong RNG.

    python3 tools/t2_rt24_bias_decomposition.py
"""
from __future__ import annotations

import datetime
import json
import pathlib

from scipy.stats import pearsonr, spearmanr

from cert.tau_sweep import ratio_finite
from measurements.validity import sla_only_validity_block

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "results" / "PENDING" / "phase-T2" / "sweep_r3"
OUT = ROOT / "results" / "PENDING" / "phase-T2" / "rt24_bias_decomposition.json"


def main() -> int:
    cells, x, y = [], [], []
    z0 = z3 = None

    for p in sorted(SRC.glob("t2_6b_r*.json")):
        d = json.loads(p.read_text())
        a = (d.get("sigma_axis") or {}).get("a")
        if a is None:
            continue
        if z0 is None:
            z0, z3 = d["z_rep"]
        rows = d["rows"]
        taus = [r["tau"] for r in rows]
        A = [r["ar1_fit"]["A"] for r in rows]
        C = [r["ar1_fit"]["c"] for r in rows]
        E = [r["ar1_fit"]["rms_e_model"] for r in rows]
        Ab, Eb = sum(A) / len(A), sum(E) / len(E)

        pure = [ratio_finite(t, 1.0, 1.0, 0.0, z0, z3) for t in taus]
        meas = [ratio_finite(t, a_, c_, e_, z0, z3)
                for t, a_, c_, e_ in zip(taus, A, C, E)]
        # em DONG BANG o trung binh: co lap DO TROI cua em khoi MUC cua em
        froz = [ratio_finite(t, a_, c_, Eb, z0, z3)
                for t, a_, c_ in zip(taus, A, C)]

        s_pure = max(pure) - min(pure)
        s_meas = max(meas) - min(meas)
        s_froz = max(froz) - min(froz)
        degenerate = Ab < 1e-3          # cbr: A ~ 1e-4, o suy bien QD-3/QD-7

        rec = {
            "cell": d["cell"], "a": a,
            "em_bar": Eb, "A_bar": Ab,
            "em_over_A": (Eb / Ab) if Ab > 0 else None,
            "span_pure_tau": s_pure,
            "span_measured": s_meas,
            "span_em_frozen": s_froz,
            "span_ratio_to_pure": (s_meas / s_pure) if s_pure > 0 else None,
            "drift_contribution": (abs(s_meas - s_froz) / s_meas) if s_meas else None,
            "degenerate": degenerate,
        }
        cells.append(rec)
        if not degenerate:
            x.append(rec["em_over_A"])
            y.append(rec["span_ratio_to_pure"])

    rho, pval = spearmanr(x, y)
    r_p, p_p = pearsonr(x, y)
    h2_700 = {"a=%s" % c["a"]: c for c in cells if c["cell"] == "h2@0.700"}

    payload = {
        "schema": "dt4n.phase_t2.rt24_decomposition.v1",
        "question": ("RT2-4: bien do R(tau) o h2 do TAU hay do bias mo hinh "
                     "tinh (em) chi phoi?"),
        "method": ("Dat em = 0 trong luat rms -> A va c triet tieu -> duong "
                   "tau THUAN, giong nhau moi o, dung lam mau so. So bien do "
                   "do duoc voi no. Rieng cot `span_em_frozen` dong bang em o "
                   "trung binh de co lap DO TROI cua em khoi MUC cua em."),
        "z_rep": [z0, z3],
        "pure_tau_span": cells[0]["span_pure_tau"] if cells else None,
        "correlation_em_over_A_vs_span_ratio": {
            "spearman_rho": float(rho), "spearman_p": float(pval),
            "pearson_r": float(r_p), "pearson_p": float(p_p), "n": len(x),
            "note": "cbr loai: A ~ 1e-4, o suy bien theo QD-3/QD-7"},
        "rt24_verdict": {
            "h2@0.700": h2_700,
            "not_the_same_as_L2_L6": (
                "L2-L6 = twin thua 16.55% cho h2 tai rho_bar=0.925, don vi ms "
                "delay. `em` o day la rms_e_model tren thang CHI PHI, tai "
                "rho_bar cua tung o. LIEN QUAN nhung KHONG dong nhat -- khong "
                "duoc dat canh nhau nhu cung mot thang."),
        },
        "cells": sorted(cells, key=lambda c: (c["em_over_A"] is None,
                                              c["em_over_A"])),
        # Artifact nay CHI DOC tu sweep_r3, va sweep_r3 tieu thu truc SLA
        # `self_calibrated` (tools/t2_sla_axis_provenance.py). Nen no ke thua
        # dung trang thai CHO do. Khai NGAY TU LUC SINH, khong va sau.
        "validity": {
            **sla_only_validity_block(
                sla_path="results/LIVE/phase-20R/sla_calibration.json",
                w_loss=float("nan"),
                z_grid=[z0, z3],
                note=("Chi doc lai ar1_fit cua sweep_r3 va ap luat rms; "
                      "khong sinh chuoi, khong fit lai. Truc SLA ke thua tu "
                      "chinh cac artifact nguon."),
            ),
            "pending_on": ["sla_axis"],
            "pending_on_source": (
                "sla_axis.label = self_calibrated la nhan DEPRECATED (S14) va "
                "khong nam trong approved_for_live.sla_axis. Duong du lieu: "
                "tools/t2_sla_axis_provenance.py"),
        },
        "provenance": {
            "script": "tools/t2_rt24_bias_decomposition.py",
            "source_dir": str(SRC.relative_to(ROOT)),
            "reads_only": True,
            "timestamp_utc": datetime.datetime.now(
                datetime.timezone.utc).isoformat()},
    }
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")

    print("duong tau thuan: span = %.5f  (z_rep = %s)"
          % (payload["pure_tau_span"], payload["z_rep"]))
    print("Spearman(em/A, span/span_pure) = %.4f  p = %.3g  n = %d"
          % (rho, pval, len(x)))
    print("Pearson                        = %.4f  p = %.3g" % (r_p, p_p))
    print()
    print("%-16s %-5s %10s %11s %12s" % ("cell", "a", "em/A", "span/pure",
                                         "do troi em"))
    for c in payload["cells"]:
        if c["degenerate"]:
            continue
        print("%-16s %-5s %10.4f %11.3f %11.1f%%"
              % (c["cell"], c["a"], c["em_over_A"], c["span_ratio_to_pure"],
                 100 * c["drift_contribution"]))
    print("\n-> %s" % OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
