#!/usr/bin/env python3
"""POST-HOC (khai ro): do HIEU UNG MUC THUAN cua R(tau).

Hinh thanh SAU khi D-T2.6-10 FAIL. Ghi thu tu de nguoi doc tu danh gia.

Cau hoi: trong `rel_diff` cua D-T2.6-10, bao nhieu phan do MUC va bao nhieu
phan do RUT MAU? Kiem cu doi HAI thu cung luc (muc VA co mau) roi quy ca
chenh lech cho MOT thu -- do la mot confound.

Cach tach: doi DUNG MOT thu moi lan.
    R(day du, level goc)  vs  R(day du, level 0.96)   -> MUC thuan, khong rut
    R(25 blk, level 0.96) x 12 hat rut                 -> NHIEU rut

Cong cu nay KHONG sua mot nguong nao, KHONG doi mot artifact nao va KHONG
lat mot phan quyet nao. D-T2.6-10 van la FAIL.

    python3 tools/t2_6b_level_probe.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import cert.tau_sweep as TS                                # noqa: E402
from cert.conformal_v2 import empirical_qhat, conformal_level  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "results/PENDING/phase-T2/sweep_r3/level_probe_posthoc.json"

CELLS = (("h2", 0.700), ("poisson", 0.850), ("poisson", 0.925))
TAUS = (0.5, 1.0, 2.0, 3.0, 5.0, 10.0)     # tau=20,28 khong rut => vo nghia
SEEDS = (101, 102, 103, 104, 105)
K = 25
N_DRAW = 12
ALPHA = 0.10


def _R(df, level):
    cal = df[df["is_calib"]]
    q = {int(g): empirical_qhat(s["s_margin"].to_numpy(np.float64), level)
         for g, s in cal.groupby("z_bin", sort=True)}
    return float(q[3] / q[0])


def main() -> int:
    from measurements.sla_calib_v2 import n_for_tau
    rows = []
    for mode, rb in CELLS:
        for tau in TAUS:
            df = TS.build_at_tau(mode, rb, tau, seeds=SEEDS,
                                 n=n_for_tau(tau, 0.005), a=0.9)
            cal = df[df["is_calib"]]
            ids = np.sort(cal["block_id"].unique())
            nb = len(ids)
            lvl0 = conformal_level(nb, ALPHA)
            lvl1 = conformal_level(K, ALPHA)
            R_full_native = _R(df, lvl0)
            R_full_matched_level = _R(df, lvl1)
            draws = []
            for s in range(7201, 7201 + N_DRAW):
                rng = np.random.default_rng(s)
                keep = set(rng.choice(ids, size=K, replace=False).tolist())
                sel = df[(~df["is_calib"]) | df["block_id"].isin(keep)]
                draws.append(_R(sel, lvl1))
            d = np.array(draws)
            rows.append({
                "cell": "%s@%.3f" % (mode, rb), "tau": tau,
                "n_calib_blocks": int(nb),
                "level_native": lvl0, "level_matched": lvl1,
                "R_full_native": R_full_native,
                "R_full_at_matched_level": R_full_matched_level,
                "level_effect_rel": abs(R_full_matched_level / R_full_native - 1),
                "R_subsample_mean": float(d.mean()),
                "R_subsample_sd": float(d.std(ddof=1)),
                "subsample_noise_cv": float(d.std(ddof=1) / d.mean()),
                "n_draws": N_DRAW,
            })
            print("%-16s tau=%-5g nb=%-5d  MUC=%.4f%%  NHIEU cv=%.4f%%"
                  % (rows[-1]["cell"], tau, nb,
                     100 * rows[-1]["level_effect_rel"],
                     100 * rows[-1]["subsample_noise_cv"]), flush=True)

    lvl = [r["level_effect_rel"] for r in rows]
    cv = [r["subsample_noise_cv"] for r in rows]
    doc = {
        "status": "POST_HOC_DIAGNOSTIC",
        "formed_after": "D-T2.6-10 FAIL (max_rel_diff = 0.15962, tau=2, poisson@0.850)",
        "does_not_overturn": ("D-T2.6-10 VAN LA FAIL. Cong cu nay do THANH PHAN, "
                              "khong lat PHAN QUYET."),
        "question": "trong rel_diff cua D-T2.6-10, bao nhieu la MUC, bao nhieu la RUT MAU",
        "method": ("doi DUNG MOT thu moi lan: (a) level tren du lieu DAY DU "
                   "=> MUC thuan; (b) %d hat rut 25 block => NHIEU rut" % N_DRAW),
        "summary": {
            "level_effect_max_rel": max(lvl),
            "level_effect_median_rel": float(np.median(lvl)),
            "subsample_cv_max": max(cv),
            "subsample_cv_median": float(np.median(cv)),
            "verdict": ("NHIEU RUT MAU CHI PHOI" if max(cv) > 2 * max(lvl)
                        else "MUC CHI PHOI"),
        },
        "rows": rows,
    }
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    print("\n-> %s" % OUT.relative_to(ROOT))
    print("   MUC max %.3f%%  |  NHIEU cv max %.3f%%  |  %s"
          % (100 * max(lvl), 100 * max(cv), doc["summary"]["verdict"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
