#!/usr/bin/env python3
"""BUOC 5b -- ma tran chay cua Lesson 23.20.

Ba dot, moi dot tra loi MOT cau hoi (amendment 23-49b muc 4). Co checkpoint:
job da xong thi bo qua. Sau MOI cell chay bon cong nhanh; hong thi DUNG NGAY
thay vi chay tiep 20 cell nua roi moi phat hien.

Chay:
    python tools/run_23_20_matrix.py --wave 1 --dry
    python tools/run_23_20_matrix.py --wave 1
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

import pandas as pd

# DUNG 8 cell cua eight_cell_sweep.json de Bang 3 doi chieu duoc voi ban CU.
# `cbr@0.700` va `poisson@0.900` KHONG nam trong do (amendment 23-49b muc 2).
CELLS8 = ["h2@0.700", "h2@0.850", "h2@0.925", "h2@0.960",
          "poisson@0.700", "poisson@0.850", "poisson@0.925", "poisson@0.960"]
# cell song (err_neo >= 0.05, amendment 23-49b muc 1)
CELLS_LIVE = ["h2@0.700", "poisson@0.850", "poisson@0.925", "poisson@0.960"]
SEEDS = ["101", "102", "103", "104", "105"]
AX_LEG, AX_MEA = "legacy_sawtooth_51ms", "measured_v7"

WAVES = {
    1: [(c, "U0", ax) for c in CELLS8 for ax in (AX_LEG, AX_MEA)],
    2: [(c, "U3", AX_MEA) for c in CELLS8],
    3: [(c, p, AX_MEA) for c in CELLS_LIVE[:3] for p in ("U1", "U2")],
}
TARGET_MEAN_MS = 366.05


def stem_of(cell, profile, axis):
    mode, rho = cell.split("@")
    # amendment 23-49c muc 3: LIVE chi khi MOI truc duoc duyet. Truc SLA
    # (S14) chua duoc duyet den Lesson 23.21 -> tat ca vao SUPERSEDED.
    tier = "SUPERSEDED"
    return "results/%s/phase-21R/calib_set_%s_%.3f_%s_%s" % (
        tier, mode, float(rho), profile, axis)


def gates(path, axis) -> dict:
    """Bon cong NHANH sau moi cell. Hong -> DUNG toan bo dot."""
    cols = ["z_s", "z_bin", "block_id"]
    head = pd.read_parquet(path, columns=None).head(0)
    calib_col = next((c for c in ("is_calib", "split", "is_cal")
                      if c in head.columns), None)
    if calib_col:
        cols.append(calib_col)
    df = pd.read_parquet(path, columns=cols)
    z_ms = df.z_s.to_numpy(float) * 1000.0
    g = {"n_rows": int(len(df)), "mean_z_ms": float(z_ms.mean()),
         "z_min_ms": float(z_ms.min()), "z_max_ms": float(z_ms.max())}
    if axis == AX_MEA:
        g["G1_mean_z"] = abs(g["mean_z_ms"] - TARGET_MEAN_MS) < 0.10
        sh = df.z_bin.value_counts(normalize=True).sort_index()
        g["bin_share"] = [round(float(x), 4) for x in sh]
        g["G2_bin_share"] = bool(
            len(sh) == 4 and max(abs(sh.to_numpy() - 0.25)) < 0.02)
        g["n_out"] = int(df.z_bin.isna().sum())
        g["G3_no_overflow"] = g["n_out"] == 0
        sub = df[df[calib_col].astype(bool)] if calib_col else df
        nb = sub.groupby("z_bin").block_id.nunique()
        g["blocks_min"] = int(nb.min())
        g["G4_blocks"] = g["blocks_min"] >= 9
    else:
        for k in ("G1_mean_z", "G2_bin_share", "G3_no_overflow", "G4_blocks"):
            g[k] = True
    g["pass"] = all(g[k] for k in
                    ("G1_mean_z", "G2_bin_share", "G3_no_overflow", "G4_blocks"))
    return g


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wave", type=int, required=True, choices=[1, 2, 3])
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    jobs = WAVES[a.wave]
    # So ledger la SO SACH, khong phai artifact -> goc results/
    # (amendment 23-49c muc 5)
    ledger_path = "results/RUN_LEDGER_wave%d.json" % a.wave
    ledger = json.load(open(ledger_path)) if os.path.exists(ledger_path) else {}

    print("=" * 78)
    print("DOT %d -- %d job" % (a.wave, len(jobs)))
    print("=" * 78)
    for i, (cell, prof, axis) in enumerate(jobs, 1):
        stem = stem_of(cell, prof, axis)
        key = os.path.basename(stem)
        tag = "%2d/%d %-16s %-3s %-21s" % (i, len(jobs), cell, prof, axis)

        if not a.force and ledger.get(key, {}).get("pass"):
            print(tag + " [DA XONG]")
            continue
        if a.dry:
            print(tag + " -> " + stem + ".parquet")
            continue

        os.makedirs(os.path.dirname(stem), exist_ok=True)
        t0 = time.time()
        r = subprocess.run(
            [sys.executable, "-m", "cert.build_calib_set_v3",
             "--cell", cell.replace("@", "_"), "--axis", axis,
             "--aoi-profile", prof, "--seeds", *SEEDS, "--out-stem", stem],
            capture_output=True, text=True)
        dt = time.time() - t0
        if r.returncode != 0:
            print(tag + " *** BUILD HONG ***")
            print(r.stderr[-2500:])
            return 1

        g = gates(stem + ".parquet", axis)
        g.update({"seconds": round(dt, 1), "cell": cell,
                  "profile": prof, "axis": axis})
        ledger[key] = g
        json.dump(ledger, open(ledger_path, "w"), indent=1, sort_keys=True)

        print(tag + " %s %5.0fs mean_z=%8.3f bins=%s" % (
            "OK " if g["pass"] else "FAIL", dt, g["mean_z_ms"],
            g.get("bin_share", "-")))
        if not g["pass"]:
            print("\n*** CONG NHANH HONG -- DUNG DOT %d ***" % a.wave)
            print(json.dumps(g, indent=1))
            return 2

    print("\nDot %d xong. So ledger: %s" % (a.wave, ledger_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
