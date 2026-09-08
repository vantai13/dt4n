#!/usr/bin/env python3
"""A-T2-1/2: hygiene only, before reading outcome curves. Run from repo root."""
import glob, hashlib, json, numpy as np, pandas as pd, pathlib
D = "results/PENDING/phase-T2/sweep_r2"
log = [json.loads(l) for l in open(D + "/run_log.jsonl")]
plan = json.loads(pathlib.Path("docs/phase-T2/03-run-plan.json").read_text())
assert len(log) == len(plan["runs"]) == plan["n_runs"] + plan["n_canaries"], "incomplete campaign"
assert len({r["run_index"] for r in log}) == len(log)
assert len({r["git_commit"] for r in log}) == 1, "mixed code revisions"
for r, planned in zip(log, plan["runs"]):
    assert all(r[k] == planned[k] for k in ("run_index", "tau", "branch", "a", "seed", "is_canary"))
    assert r["returncode"] == 0
    assert hashlib.sha256(pathlib.Path(r["out"]).read_bytes()).hexdigest() == r["sha256"]
frames = [pd.read_parquet(r["out"]) for r in log]
all_rows = sum(map(len, frames))
d = pd.concat([f for r, f in zip(log, frames) if not r["is_canary"]])
# Canaries are repeats of seed 999, never a sixth seed in clip summaries.
assert set(d.seed) == {101, 102, 103, 104, 105}
assert np.isfinite(d[["ar1_clip_ratio", "tt_domain_clip_max", "ar1_cycles"]]).all().all()
out = {"phase": "T2.6 luot 2 -- sau A-T2-1 va A-T2-2",
       "n_commands": len(log), "n_rows": all_rows, "n_rows_without_canaries": int(len(d)),
       "git_commit": log[0]["git_commit"], "seconds": sum(r["seconds"] for r in log)}

# --- KIEM 1  NC-T2-4 diem canh
can = [r for r in log if r["is_canary"]]
fr = [pd.read_parquet(r["out"]) for r in can]
num = fr[0].select_dtypes("number").columns
span = max(float(np.ptp(np.array([f[c].to_numpy() for f in fr]), axis=0).max()) for c in num)
out["KIEM_1_canary_NC_T2_4"] = {
    "n_canary": len(can), "n_distinct_sha256": len({r["sha256"] for r in can}),
    "max_span_any_numeric_column": span,
    "verdict": "PASS" if span == 0.0 and len({r["sha256"] for r in can}) == 1 else "FAIL"}

# --- KIEM 2  hai loai kep, TRUNG VI qua seed (A-T2-1 muc d)
def per_cell(col):
    g = (d.groupby(["mode", "rho_bar", "tau_rho", "sigma_rho", "seed"])[col].max()
           .groupby(level=[0, 1, 2, 3]))
    return g.median(), g.min(), g.max()
med_ar1, mn_ar1, mx_ar1 = per_cell("ar1_clip_ratio")
med_tt,  mn_tt, mx_tt  = per_cell("tt_domain_clip_max")
clip_table = pd.DataFrame({"ar1_median": med_ar1, "ar1_min": mn_ar1, "ar1_max": mx_ar1,
                           "tt_median": med_tt, "tt_min": mn_tt, "tt_max": mx_tt})
clip_table.to_csv("results/PENDING/phase-T2/clip_summary_r2.csv")
assert (d.groupby(["mode", "rho_bar", "tau_rho", "sigma_rho"]).seed.nunique() == 5).all()
out["KIEM_2_clip"] = {
    "note": "Trung vi va min/max qua 5 seed; tau=28 co n*dt/tau=50, uoc luong duoi nhieu.",
    "ar1_clip": {"median_max_over_cells": float(med_ar1.max()),
                 "worst_cell": str(med_ar1.idxmax()),
                 "R5_threshold": 0.0009,
                 "verdict": "PASS" if med_ar1.max() < 0.0009 else "FAIL_R5",
                 "single_draw_max": float(mx_ar1.max())},
    "tt_domain_clip": {"median_max_over_cells": float(med_tt.max()),
                       "worst_cell": str(med_tt.idxmax()),
                       "single_draw_max": float(mx_tt.max()),
                       "note": "R7 -- ngoai suy phang, KHONG co nguong da ky"},
    "headline_cells": {
        str(k): {"ar1_median": float(med_ar1.loc[k[0], k[1]].max()),
                 "tt_median": float(med_tt.loc[k[0], k[1]].max())}
        for k in [("h2", 0.700), ("poisson", 0.850), ("poisson", 0.925)]}}

# --- KIEM 3  NC-T2-2 (nhom theo sigma_rho -- khong tron a=0.5 voi a=0.9)
s = d[(d.tau_rho == 1.0) & (d.z_s.round(6) == 0.10)]
assert (s.groupby(["mode", "rho_bar", "sigma_rho", "seed"]).size() == 2).all()
g = s.groupby(["mode", "rho_bar", "sigma_rho", "seed"])["err_total"].agg(["min", "max"])
g["rel"] = (g["max"] - g["min"]) / g["min"].replace(0, np.nan)
m = d[d.tau_rho == 1.0].groupby(["mode", "rho_bar", "sigma_rho", "seed"])["rms_e_model"].agg(["min", "max"])
m["rel"] = (m["max"] - m["min"]) / m["min"].replace(0, np.nan)
def relative_span(frame):
    delta = frame["max"] - frame["min"]
    return np.where(delta == 0, 0.0, np.where(frame["min"] == 0, np.inf, delta / frame["min"]))
g["rel"] = relative_span(g)
m["rel"] = relative_span(m)
out["KIEM_3_branch_join_NC_T2_2"] = {
    "max_rel_span_err_total": float(np.nanmax(g.rel)),
    "max_rel_span_rms_e_model": float(np.nanmax(m.rel)),
    "note": "rms_e_model KHONG phu thuoc z; khac 0 la bang chung cua so lech",
    "threshold": 0.01,
    "verdict": "PASS" if np.nanmax(g.rel) < 0.01 and np.nanmax(m.rel) < 1e-12 else "FAIL"}

p = pathlib.Path("results/PENDING/phase-T2/hygiene_checks_r2.json")
p.write_text(json.dumps(out, indent=2, sort_keys=True, default=str) + "\n")
for k in ("KIEM_1_canary_NC_T2_4", "KIEM_3_branch_join_NC_T2_2"):
    print(k, "->", out[k]["verdict"])
print("KIEM_2 ar1 ->", out["KIEM_2_clip"]["ar1_clip"]["verdict"])
print("-> " + str(p))
print(json.dumps(out, indent=2, sort_keys=True))
