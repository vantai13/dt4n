#!/usr/bin/env python3
"""20R2.7 TRUOC KHI MO -- d_sla CO THE mang thong tin o o nao?

CHI doc MOI TRUONG (bang su that + nguong SLA). KHONG doc mot cot d_sla nao.

Voi moi o, moi a, moi TRUC SLA:
    viol_share[p] = ti le thoi gian duong p vi pham SLA (delay > T_d OR loss > T_l)
    spread        = mean_t[ max_p viol - min_p viol ]
                  = ti le thoi gian cac duong KHAC NHAU ve trang thai vi pham
Vi d_sla = mean_t[viol(t, a_twin) - viol(t, a_truth)], ta co CHAC CHAN
    |d_sla| <= spread    va    |d_sla| <= err_total
nen spread ~ 0  =>  d_sla ~ 0 THEO CAU TRUC, bat ke twin sai bao nhieu.

DO DUOC KHONG CO NGHIA LA MANG THONG TIN. Day la ket qua chinh cua 20R2.7, va
no co duoc TRUOC khi mo mot cot ket qua nao.

    python -m tools.20r2_7_structure --out docs/phase-20R2/07a-dsla-structure.json
"""
from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
AXES = {"exogenous_g114_S-B": "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json",
        "self_calibrated (DEPRECATED)": "results/LIVE/phase-20R/sla_calibration.json"}
SEEDS, TAU, N = (901, 902, 903), 3.0, 200_000   # NGOAI thiet ke; phan phoi dung khong phu thuoc tau
CLASS = ((0.01, "DEGENERATE"), (0.05, "WEAK"))  # §20.2 -- KY TRUOC khi mo


def classify(spread):
    for bound, name in CLASS:
        if spread < bound:
            return name
    return "INFORMATIVE"


def main(argv=None):
    import measurements.decision_error_v2 as DE
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    tt = DE.TruthTable(DE.TRUTH_TABLE)
    rows = []
    for axis, path in AXES.items():
        for c in DE.feasible_cells(path, include_pc1=True):
            for av in (0.9, 0.5):
                sig, _ = DE.resolve_sigma(c, a_override=av)
                vs, sp = [], []
                for seed in SEEDS:
                    rho, _ = DE.rho_matrix_from_cell(
                        c["mode"], float(c["rho_bar"]), sig, seed, tau=TAU, n=N,
                        dt=DE.DT, source=DE.RHO_SOURCE, return_diagnostics=True)
                    d, l, _ = tt.path_tables(c["mode"], rho, float(c["w_loss"]))
                    v = DE._viol(d, l, float(c["t_delay_ms"]), float(c["t_loss"]))
                    vs.append(v.mean(axis=0))
                    sp.append(float((v.max(axis=1).astype(int)
                                     - v.min(axis=1).astype(int)).mean()))
                spread = float(np.mean(sp))
                rows.append({"axis": axis, "cell": "%s@%.3f" % (c["mode"], float(c["rho_bar"])),
                             "a": av, "t_delay_ms": float(c["t_delay_ms"]),
                             "t_loss": float(c["t_loss"]), "w_loss": float(c["w_loss"]),
                             "viol_share_per_path": [round(float(x), 4)
                                                     for x in np.mean(vs, axis=0)],
                             "spread": spread, "class": classify(spread)})
                print("%-30s %-14s a=%.1f spread=%.4f %-11s %s" % (
                    axis, rows[-1]["cell"], av, spread, rows[-1]["class"],
                    rows[-1]["viol_share_per_path"]))
    doc = {"schema": "dt4n.dsla_structure_20r2_7.v1",
           "generated_by": "tools/20r2_7_structure.py",
           "WHAT_THIS_IS": ("Tinh chat MOI TRUONG, KHONG phai ket qua. Khong doc mot "
                            "cot d_sla nao. spread la CAN TREN cua |d_sla|."),
           "classes": {"DEGENERATE": "spread < 0.01", "WEAK": "0.01 <= spread < 0.05",
                       "INFORMATIVE": "spread >= 0.05"},
           "seeds": list(SEEDS), "tau": TAU, "n": N, "rows": rows}
    (ROOT / a.out).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
