#!/usr/bin/env python3
"""20R2.6c -- mo hinh G4 (Gauss tuyen tinh hoa, 4 hanh dong) cho err_stale/Sheppard.

MO HINH (KHONG tham so khop): vector chi phi TWIN c(t) in R^4 ~ N(mu, Sigma), tu
tuong quan r = exp(-z/tau) cho moi thanh phan (dung khi chi phi tuyen tinh theo
rho va moi link cung tau). Du doan:
    err_stale = P(argmin c(t) != argmin c(t-z))    -- tinh bang Monte Carlo
Cac truong hop da biet la TRUONG HOP RIENG:
    m = 0 va 2 hanh dong  -> dung cong thuc Sheppard arccos(r)/pi
    ky vong khac 0        -> NEN (hieu ung Rice 1944)
    >= 3 duong song       -> GIAN (nhieu ranh gioi quyet dinh -> nhieu co hoi lat)

VI SAO LAY (mu, Sigma) TU c_fresh, KHONG TU c_true
=================================================
err_stale so twin voi CHINH NO o thoi diem cu, nen cau truc bien phai lay tu chi
phi TWIN (c_fresh). Day la dinh chinh so voi 06b, noi m duoc tinh tu c_true.
(mu, Sigma) uoc tu seed 901-903 -- NGOAI thiet ke, khong dung vet chien dich.

VI SAO PHAI CO HOLDOUT -- CONG KHAI MOT LOI RE
==============================================
Ba mo hinh da duoc so tren DU LIEU KHAM PHA (a = 0.9) roi G4 duoc CHON vi khop
tot nhat. Do la mot loi re (garden of forking paths). Chinh vi the holdout la
BAT BUOC, va holdout phai la DIEU KIEN MOI (a = 0.5), khong phai seed moi:
m, so duong song va bang chi phi la tinh chat cua O, khong cua SEED -- chay seed
moi tren cung 8 o chi kiem nhieu lay mau, nen gan nhu chac chan "qua"
(severity THAP, Mayo 2018).

HAI CHE DO, dung THU TU:
  --predict : a=0.9 (KHAM PHA, doi chieu) + a=0.5 (HOLDOUT, KHONG doc mot dong
              err_stale nao cua a=0.5). Ghi 06c. Commit + tag
              phase-20R2-g4-frozen + push.
  --score   : guard doi tag tren remote; MOI doc err_stale cua a=0.5.

    python -m tools.20r2_6c_g4 --predict --out docs/phase-20R2/06c-g4-predictions.json
    python -m tools.20r2_6c_g4 --score   --out docs/phase-20R2/06c-g4-score.json
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import subprocess

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAN = "docs/phase-20R2/03-run-plan.json"
PRED_OUT = "docs/phase-20R2/06c-g4-predictions.json"
EXO = "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json"
TAG = "phase-20R2-g4-frozen"
TAUS = (0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 28.0)
Z, Z_SIGNED = 0.366, 0.365
STRUCT_SEEDS, STRUCT_TAU, STRUCT_N = (901, 902, 903), 3.0, 200_000
MC_N, MC_SEED = 1_000_000, 20263
# §19 -- DAN XUAT tu kham pha, KHONG chon tay:
#   0.10 = bien sai so lon nhat cua 7 o kham pha (~7.6%) + nhieu seed (~1-2%)
#   0.02 = SAN tuyet doi, vi co hai du doan gan 0 (0.022 va 0.000) noi sai so
#          TUONG DOI vo nghia
#   7/8  = khop dung hieu nang tren kham pha (mot o di thuong: poisson@0.700)
REL_TOL, ABS_TOL, MIN_CELLS = 0.10, 0.02, 7


def sheppard(z, tau):
    return math.acos(math.exp(-float(z) / float(tau))) / math.pi


def cost_moments(cell, a):
    """(mu, Sigma, argmin_shares) cua chi phi TWIN, tu seed NGOAI thiet ke."""
    import measurements.decision_error_v2 as DE
    from twin import cost_v2 as C
    cv2 = C.CostV2(strict_reliable=False)
    sig, _ = DE.resolve_sigma(cell, a_override=a)
    cs = []
    for seed in STRUCT_SEEDS:
        rho, _ = DE.rho_matrix_from_cell(cell["mode"], float(cell["rho_bar"]), sig, seed,
                                         tau=STRUCT_TAU, n=STRUCT_N, dt=DE.DT,
                                         source=DE.RHO_SOURCE, return_diagnostics=True)
        _, _, cf = cv2.tables_batch(rho, cell["mode"], float(cell["w_loss"]))
        cs.append(cf)
    c = np.vstack(cs)
    shares = np.bincount(c.argmin(axis=1), minlength=c.shape[1]) / len(c)
    return c.mean(axis=0), np.cov(c, rowvar=False), shares


def g4_ratio(mu, S, tau):
    r = math.exp(-Z / float(tau))
    rng = np.random.default_rng(MC_SEED)          # CRN qua tau: tat dinh
    k = len(mu)
    # Sigma co the gan suy bien o o ma mot duong ap dao -> dung eigh, kep am ve 0.
    w, V = np.linalg.eigh(S)
    L = V @ np.diag(np.sqrt(np.clip(w, 0.0, None)))
    z1 = rng.standard_normal((MC_N, k))
    z2 = rng.standard_normal((MC_N, k))
    X = mu + z1 @ L.T
    Y = mu + (r * z1 + math.sqrt(max(1.0 - r * r, 0.0)) * z2) @ L.T
    return float((X.argmin(axis=1) != Y.argmin(axis=1)).mean()) / sheppard(Z_SIGNED, tau)


def predictions(a):
    import measurements.decision_error_v2 as DE
    out = {}
    for c in DE.feasible_cells(EXO, include_pc1=True):
        if c["mode"] == "cbr":
            continue
        mu, S, shares = cost_moments(c, a)
        per_tau = [g4_ratio(mu, S, t) for t in TAUS]
        out["%s@%.3f" % (c["mode"], float(c["rho_bar"]))] = {
            "per_tau": per_tau, "tau_mean": float(np.mean(per_tau)),
            "argmin_shares": [float(x) for x in shares],
            "n_active": int((shares >= 0.05).sum())}
    return out


def observed(a):
    """err_stale/Sheppard theo tung o. CHI doc cac lan chay co a DUNG BANG tham so."""
    plan = json.loads((ROOT / PLAN).read_text(encoding="utf-8"))
    fr = [pd.read_parquet(ROOT / r["out"]) for r in plan["runs"]
          if not r["is_canary"] and r["branch"] == "main" and float(r["a"]) == a]
    d = pd.concat(fr, ignore_index=True)
    s = d[np.isclose(d["z_s"].to_numpy(float), Z) & (d["mode"] != "cbr")]
    g = s.groupby(["mode", "rho_bar", "tau_rho"])["err_stale"].mean().reset_index()
    obs = {}
    for (m, rb), gg in g.groupby(["mode", "rho_bar"]):
        per_tau = [float(gg[gg["tau_rho"] == t]["err_stale"].iloc[0]) / sheppard(Z_SIGNED, t)
                   for t in TAUS]
        obs["%s@%.3f" % (m, float(rb))] = {"per_tau": per_tau, "tau_mean": float(np.mean(per_tau))}
    return obs


def within(obs, pred):
    return bool(abs(obs - pred) <= max(REL_TOL * pred, ABS_TOL))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--predict", action="store_true")
    g.add_argument("--score", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    if a.predict:
        dp, do = predictions(0.9), observed(0.9)
        disc = {k: {"pred": dp[k]["tau_mean"], "obs": do[k]["tau_mean"],
                    "rel": (do[k]["tau_mean"] / dp[k]["tau_mean"] - 1.0
                            if dp[k]["tau_mean"] > 0 else None),
                    "within_tol": within(do[k]["tau_mean"], dp[k]["tau_mean"]),
                    "n_active": dp[k]["n_active"]} for k in dp}
        doc = {"schema": "dt4n.g4_20r2_6c.v1", "generated_by": "tools/20r2_6c_g4.py",
               "STATUS": "DU DOAN -- a=0.5 CHUA MO",
               "DISCLOSURE": ("BA mo hinh da duoc so tren du lieu KHAM PHA (a=0.9) roi G4 "
                              "duoc CHON vi khop tot nhat. Do la mot LOI RE. Holdout a=0.5 "
                              "la bat buoc chinh vi the. Mo hinh Gauss hai chieu khop "
                              "poisson@0.700 tot hon nhung truot nang o moi o >= 3 duong song."),
               "rule": {"rel_tol": REL_TOL, "abs_tol": ABS_TOL, "min_cells": MIN_CELLS,
                        "statistic": ("trung binh qua 8 tau cua err_stale/Sheppard(0.365), "
                                      "tai z=0.366, tung o gate"),
                        "pass_cell": "|obs - G4| <= max(0.10*G4, 0.02)",
                        "pass_P1": ">= 7/8 o",
                        "why_holdout_is_a05_not_new_seed": (
                            "m, so duong song va bang chi phi la tinh chat cua O, khong cua "
                            "SEED. Seed moi chi kiem nhieu lay mau -> severity THAP. a=0.5 "
                            "doi CAU TRUC bien (m tang, so duong song doi) nen mo hinh phai "
                            "du doan dung o dieu kien no CHUA THAY. Ton 0 phut CPU vi da chay.")},
               "discovery_a09": disc,
               "n_within_discovery": sum(v["within_tol"] for v in disc.values()),
               "holdout_a05_predictions": predictions(0.5)}
        (ROOT / a.out).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n",
                                  encoding="utf-8")
        for k in sorted(disc, key=lambda k: -disc[k]["pred"]):
            v = disc[k]
            print("KHAM PHA %-14s G4=%.3f obs=%.3f %+6.1f%%  %s" % (
                k, v["pred"], v["obs"], 100 * v["rel"] if v["rel"] is not None else 0.0,
                "trong" if v["within_tol"] else "NGOAI"))
        print("  -> %d/8 trong dung sai tren KHAM PHA" % doc["n_within_discovery"])
        print()
        for k in sorted(doc["holdout_a05_predictions"],
                        key=lambda k: -doc["holdout_a05_predictions"][k]["tau_mean"]):
            v = doc["holdout_a05_predictions"][k]
            print("HOLDOUT  %-14s G4=%.3f  duong song=%d" % (k, v["tau_mean"], v["n_active"]))
        return 0

    # ---- --score: MOI duoc doc a=0.5
    git = lambda *x: subprocess.run(["git", *x], cwd=ROOT, capture_output=True,
                                    text=True).stdout.strip()
    if not git("ls-remote", "--tags", "origin", TAG):
        raise SystemExit("DUNG: chua co tag %s tren remote -- du doan chua dong bang." % TAG)
    if git("diff", "--name-only", TAG, "HEAD", "--", "tools/20r2_6c_g4.py", PRED_OUT) \
            or git("status", "--porcelain", "--", "tools/20r2_6c_g4.py", PRED_OUT):
        raise SystemExit("DUNG: tool/du doan doi SAU khi dong bang.")
    pred = json.loads((ROOT / PRED_OUT).read_text(encoding="utf-8"))["holdout_a05_predictions"]
    obs = observed(0.5)
    rows = {k: {"pred": pred[k]["tau_mean"], "obs": obs[k]["tau_mean"],
                "rel": (obs[k]["tau_mean"] / pred[k]["tau_mean"] - 1.0
                        if pred[k]["tau_mean"] > 0 else None),
                "tol": max(REL_TOL * pred[k]["tau_mean"], ABS_TOL),
                "within_tol": within(obs[k]["tau_mean"], pred[k]["tau_mean"]),
                "n_active": pred[k]["n_active"]} for k in pred}
    n_ok = sum(v["within_tol"] for v in rows.values())
    doc = {"schema": "dt4n.g4_score_20r2_6c.v1", "generated_by": "tools/20r2_6c_g4.py",
           "STATUS": "HOLDOUT a=0.5 da mo MOT lan",
           "rule": {"rel_tol": REL_TOL, "abs_tol": ABS_TOL, "min_cells": MIN_CELLS},
           "rows": rows, "n_within": n_ok, "denominator": len(rows),
           "verdict": "PASS" if n_ok >= MIN_CELLS else "FAIL"}
    (ROOT / a.out).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for k in sorted(rows, key=lambda k: -rows[k]["pred"]):
        v = rows[k]
        print("  %-14s G4=%.3f obs=%.3f tol=%.3f  %s" % (
            k, v["pred"], v["obs"], v["tol"], "trong" if v["within_tol"] else "NGOAI"))
    print("HOLDOUT a=0.5: %d/%d trong dung sai -> %s" % (n_ok, len(rows), doc["verdict"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
