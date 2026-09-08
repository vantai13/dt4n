#!/usr/bin/env python3
"""Sinh trace rho TONG HOP tu ar1_matrix ra CSV wide cho cert/build_calib_set.py.

Day la dau vao DUNG cho nhanh nhay cam `u_cond` cua T2 (prereg QD-1), khong
phai mot ban thay the tam cho trace Mininet da mat.

VI SAO KHONG DUNG results/phase-20/rho_offered_long*.csv:

  (1) Chung chua bao gio nam trong git: moi file > 100 MB nen khong duoc add
      (docs/phase-20/99-gate-decision.md:319). Do la mot quyet dinh custody
      co chu y, khong phai mot mat mat.

  (2) QUAN TRONG HON -- tau cua chung la DO DUOC va CO DINH RIENG TUNG LINK
      (docs/phase-20/00f-amendment-5.md muc A5.1):

          bc 2.441 | bd 2.605 | ac 2.869 | ad 3.958
          vC 17.38 | uB 21.70 | uA 22.87 | vD 32.00     (giay)

      Khong QUET duoc mot TRUC tren mot trace co tau dong bang. T2 can DAT
      tau in {0.5, ..., 28}; trace do khong cho dat.

  (3) B9/D10 da ky: truc tau cua T2 chay trong TWIN (NumPy), KHONG tren
      Mininet. Phu luc A: "ha tang Phase T2 = THUAN NUMPY, khong root".
      Dung trace Mininet lam dau vao la di nguoc dac ta da ky cua phase.

z KHONG den tu file nay. `build_calib_set` sinh z bang `sawtooth_age_steps()`,
tuc theo CHU KY DONG BO (DEFAULT_SYNC_PERIOD_S = 0.5 s). Do dung la dinh nghia
nhanh B: z co dinh theo chu ky dong bo, KHONG co gian theo tau. Nen nap mot
trace AR(1) tong hop tai tau = 10 vao day cho dung CHE DO VAN HANH ma T2 muon
do -- dieu ma trace Mininet cu khong cho.

    python3 tools/t2_make_synthetic_trace.py \
        --mode poisson --rho-bar 0.925 --a 0.9 --tau 10.0 --seed 101 \
        --out results/PENDING/phase-T2/traces/rho_p0925_tau10_s101.csv
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib

from measurements import sla_calib_v2 as SLA
from twin import cost_v2 as C
from twin import topology_v7 as T7

DT = 0.005          # khoa tu 20R

# Hang so cung trong cert/build_calib_set.py:51 ma trace nay se di qua.
# KHONG sua no o day va cung KHONG sua o do (sua se pha tai tao Phase 21);
# chi DO va GHI ti le lech, vi do la B3 trong docs/phase-T2/PHASE_T2.md.
CALIB_SIGMA_RHO = 0.010


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", required=True, choices=("cbr", "poisson", "h2"))
    ap.add_argument("--rho-bar", type=float, required=True)
    ap.add_argument("--a", type=float, required=True,
                    help="sigma = a * sigma_max_regime(mode, rho_bar)")
    ap.add_argument("--tau", type=float, required=True,
                    help="THOI GIAN TUONG QUAN cua tai, GIAY. BAT BUOC "
                         "(tau la TRUC, khong phai tien nghi).")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--dt", type=float, default=DT)
    ap.add_argument("--n", type=int, default=None,
                    help="mac dinh: n_for_tau(tau, dt)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    n = a.n if a.n is not None else SLA.n_for_tau(a.tau, a.dt)
    sigma = C.sigma_from_a_regime(a.mode, a.rho_bar, a.a)
    if sigma <= 0.0:
        raise SystemExit(
            "sigma_max_regime = 0 o (%s, %.3f): het headroom den tran do tin "
            "cay. O nay bi realizability_gate tu choi -- KHONG sinh trace."
            % (a.mode, a.rho_bar))

    # return_diagnostics la CO OPT-IN: duong tra ve mac dinh khong doi kieu,
    # nen NC-T2-1 (bit-exact) khong bi cham.
    rho, diag = SLA.ar1_matrix(a.mode, a.rho_bar, sigma,
                               tau=a.tau, dt=a.dt, n=n, seed=a.seed,
                               return_diagnostics=True)

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # WIDE format: read_trace_matrix (measurements/decision_error.py) doi
        # du MOI ten trong T7.LINK_NAMES va bo qua cot dt_s.
        w.writerow(list(T7.LINK_NAMES) + ["dt_s"])
        for row in rho:
            w.writerow(["%.17g" % v for v in row] + ["%.17g" % a.dt])

    meta = {
        "script": "tools/t2_make_synthetic_trace.py",
        "mode": a.mode,
        "rho_bar": float(a.rho_bar),
        "a": float(a.a),
        "sigma_design": float(sigma),
        # TEN DUNG la tau_load, KHONG phai "tau": tau_load la TRUC dat ra cho
        # qua trinh tong hop; tau_core (2.87) la mot dai luong DO DUOC khac
        # han. Xem docs/GLOSSARY.md muc tau_load va tau_core.
        "tau_load": float(a.tau),
        "dt": float(a.dt),
        "n": int(n),
        "seed": int(a.seed),
        "t_sim_s": float(n) * float(a.dt),
        "cycles": diag["cycles"],
        "n_clipped": diag["n_clipped"],
        "n_clipped_ratio": diag["n_clipped_ratio"],
        "sigma_hat": diag["sigma_hat"],
        "link_names": list(T7.LINK_NAMES),
        # --- hai canh bao PHAI di kem ket qua, khong duoc de nguoi doc tu doan
        "B3_sigma_scale_mismatch": {
            "calib_sigma_rho_hardcoded": CALIB_SIGMA_RHO,
            "trace_sigma_design": float(sigma),
            "ratio": float(sigma) / CALIB_SIGMA_RHO,
            "why": ("cert/build_calib_set.py:51 dung SIGMA_RHO = 0.010 CUNG de "
                    "tinh sigma_z, trong khi trace nay co sigma khac. `u` bi "
                    "lech thang theo dung ti so nay, nen nhieu diem se don ve "
                    "bin cao cua U_EDGES = (0,1,2,3,inf). KHONG pha so sanh "
                    "u vs u_cond (ca hai dung CHUNG sigma_z) nhung PHA viec "
                    "doc `u` tuyet doi so voi U_EDGES. Day la B3. KHONG sua "
                    "SIGMA_RHO -- sua se pha tai tao Phase 21."),
        },
        "tau_core_vs_tau_load": {
            "tau_core_used_for_sigma_z": 2.87,
            "tau_load_of_this_trace": float(a.tau),
            "why": ("sigma_z van dung tau_core = 2.87 (DO DUOC) chu KHONG dong "
                    "bo theo tau_load. Day la lua chon CO CHU Y theo QD-1/F1: "
                    "tau_core va tau_load la hai dai luong khac nhau. Ghi ca "
                    "hai so de khong ai doc nham thanh mot loi."),
        },
        "note": ("Trace TONG HOP. tau_load la THAM SO DAT, khong phai do duoc. "
                 "z do sawtooth_age_steps() cua build_calib_set quyet dinh "
                 "(chu ky dong bo), KHONG tu file nay."),
        "sha256_csv": hashlib.sha256(out.read_bytes()).hexdigest(),
    }
    meta_path = out.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")

    print("-> %s  (%d hang x %d link)" % (out, n, len(T7.LINK_NAMES)))
    print("-> %s" % meta_path)
    print("   sigma_hat=%.6g (design %.6g)  clip=%.4f%%  cycles=%.1f"
          % (diag["sigma_hat"], sigma,
             100 * diag["n_clipped_ratio"], diag["cycles"]))
    print("   B3: sigma trace / SIGMA_RHO calib = %.2fx"
          % (sigma / CALIB_SIGMA_RHO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
