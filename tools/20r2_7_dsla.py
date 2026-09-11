#!/usr/bin/env python3
"""20R2.7 -- d_sla: GIA cua sai, doc theo §20 (khoa TRUOC khi mo).

d_sla = mean_t[viol(t, a_twin) - viol(t, a_truth)]        (dong 567)
      = err_total * Delta_cond,  Delta_cond = E[viol_twin - viol_truth | twin SAI]
-> HIEU TI LE VI PHAM, KHONG THU NGUYEN, trong [-1, 1]. KHONG phai ms (§20.1).

Du doan da ky (§20.4):
  S0  DUNG CU, CHINH XAC  |d_sla| <= err_total o MOI hang       severity CAO
  S1  o DEGENERATE (07a)  |d_sla| < 0.01 o moi tau              severity THAP (khai)
  S2  o INFORMATIVE (07a) d_sla > 0 o moi tau                   severity VUA
Mo ta (khong phan quyet): Delta_cond theo o; gop 8 o dan nhan "bi so 0 CAU TRUC
chi phoi -- KHONG doc nhu gia cua sai".

    python -m tools.20r2_7_dsla --out docs/phase-20R2/07-dsla.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAN = "docs/phase-20R2/03-run-plan.json"
STRUCT = "docs/phase-20R2/07a-dsla-structure.json"
HYG = "docs/phase-20R2/05-hygiene.json"
PREREG = "docs/phase-20R2/00-preregistration.md"
TAG = "phase-20R2-dsla-frozen"
FROZEN = ("tools/20r2_7_dsla.py", "test/test_20r2_7_dsla.py", STRUCT, PREREG)
AXIS = "exogenous_g114_S-B"
Z = 0.366
S1_BOUND = 0.01


def guard():
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                                    text=True).stdout.strip()
    if not git("ls-remote", "--tags", "origin", TAG):
        raise SystemExit("DUNG: chua co tag %s tren remote -- chua dong bang." % TAG)
    if git("diff", "--name-only", TAG, "HEAD", "--", *FROZEN) \
            or git("status", "--porcelain", "--", *FROZEN):
        raise SystemExit("DUNG: tool/test/cau truc/prereg doi SAU khi dong bang.")
    if json.loads((ROOT / HYG).read_text(encoding="utf-8")).get("verdict") != "PASS":
        raise SystemExit("DUNG: hygiene khong PASS -- gate VALIDITY truoc gate OUTCOME.")


def load():
    plan = json.loads((ROOT / PLAN).read_text(encoding="utf-8"))
    fr = []
    for r in plan["runs"]:
        if r["is_canary"] or r["branch"] != "main":
            continue
        d = pd.read_parquet(ROOT / r["out"])
        d["a"] = float(r["a"])
        fr.append(d)
    return pd.concat(fr, ignore_index=True)


def classes():
    rows = json.loads((ROOT / STRUCT).read_text(encoding="utf-8"))["rows"]
    return {(r["cell"], r["a"]): r["class"] for r in rows if r["axis"] == AXIS}


def adjudicate(d: pd.DataFrame, cls: dict) -> dict:
    # S0 tren MOI hang, MOI z -- khong chi z = 0.366.
    s0_bad = int((d["d_sla"].abs() > d["err_total"] + 1e-12).sum())
    s = d[np.isclose(d["z_s"].to_numpy(float), Z, rtol=0.0, atol=1e-9) & (d["mode"] != "cbr")]
    g = s.groupby(["mode", "rho_bar", "a", "tau_rho"])[["d_sla", "err_total"]].mean().reset_index()
    rows, s1, s2 = [], [], []
    for _, r in g.iterrows():
        key = ("%s@%.3f" % (r["mode"], float(r["rho_bar"])), float(r["a"]))
        c = cls[key]
        dc = float(r["d_sla"] / r["err_total"]) if r["err_total"] > 0 else None
        row = {"cell": key[0], "a": key[1], "tau": float(r["tau_rho"]), "class": c,
               "d_sla": float(r["d_sla"]), "err_total": float(r["err_total"]),
               "delta_cond": dc}
        if c == "DEGENERATE":
            row["S1"] = bool(abs(row["d_sla"]) < S1_BOUND)
            s1.append(row["S1"])
        elif c == "INFORMATIVE":
            row["S2"] = bool(row["d_sla"] > 0.0)
            s2.append(row["S2"])
        rows.append(row)
    pooled = g[g["a"] == 0.9].groupby("tau_rho")["d_sla"].mean().tolist()
    return {"S0_instrument": {"rows_violating": s0_bad, "rows_checked": int(len(d)),
                              "verdict": "PASS" if s0_bad == 0 else "FAIL",
                              "severity": "CAO -- he qua DAI SO cua dinh nghia"},
            "S1_degenerate_near_zero": {"n": len(s1), "n_hold": int(sum(s1)),
                                        "verdict": "PASS" if s1 and all(s1) else "FAIL",
                                        "severity": ("THAP -- spread da la CAN TREN va ~0, "
                                                     "nen gan nhu chac chan dat")},
            "S2_informative_positive": {"n": len(s2), "n_hold": int(sum(s2)),
                                        "verdict": "PASS" if s2 and all(s2) else "FAIL",
                                        "severity": "VUA -- truot neu Delta_cond < 0"},
            "pooled_8_a09_DESCRIPTIVE": {
                "values": pooled,
                "label": ("bi chi phoi boi cac so 0 THEO CAU TRUC (13/16 to hop gate) -- "
                          "KHONG doc nhu 'gia cua sai'")},
            "rows": rows}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    guard()
    doc = {"schema": "dt4n.dsla_20r2_7.v1", "generated_by": "tools/20r2_7_dsla.py",
           "axis": AXIS,
           "WHAT_THIS_IS": ("d_sla = HIEU TI LE VI PHAM, khong thu nguyen [-1,1] (§20.1). "
                            "Ket qua CHINH cua 20R2.7 la CAU TRUC (07a), co TRUOC khi mo."),
           **adjudicate(load(), classes())}
    (ROOT / a.out).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for k in ("S0_instrument", "S1_degenerate_near_zero", "S2_informative_positive"):
        v = doc[k]
        print("%-26s %-5s %s" % (k, v["verdict"],
                                 {kk: vv for kk, vv in v.items()
                                  if kk not in ("verdict", "severity")}))
    inf = [r for r in doc["rows"] if r["class"] == "INFORMATIVE"]
    if inf:
        print("\nDelta_cond o cac to hop INFORMATIVE (gia cua MOT lan sai):")
        for r in sorted(inf, key=lambda r: (r["cell"], r["a"], r["tau"]))[:8]:
            print("  %-14s a=%.1f tau=%-5g d_sla=%+.4f err=%.4f Delta_cond=%+.3f" % (
                r["cell"], r["a"], r["tau"], r["d_sla"], r["err_total"], r["delta_cond"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
