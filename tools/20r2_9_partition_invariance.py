#!/usr/bin/env python3
"""20R2-E1-b -- phan hoach gate/pc1 co BAT BIEN voi truc SLA khong?"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, subprocess
from datetime import datetime, timezone
import numpy as np
from measurements.decision_error_v2 import TruthTable
from measurements import sla_calib_v2 as SLA

ROOT = pathlib.Path(__file__).resolve().parents[1]
SELF_CAL = ROOT / "results/LIVE/phase-20R/sla_calibration.json"
EXO      = ROOT / "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json"
T_DELAY_MS, T_LOSS, W_LOSS = 50.0, 0.01, 5000.0
VIOL_BAND = (0.10, 0.25)
TAU_REF, DT, N_REF, SEED_REF = 1.0, 0.005, 50_000, 100

def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _git(*a):
    try: return subprocess.check_output(["git",*a],text=True,cwd=ROOT,stderr=subprocess.DEVNULL).strip()
    except Exception: return ""

def viol_rate_exogenous(tt, mode, rho_bar, sigma):
    rho = SLA.ar1_matrix(mode, rho_bar, sigma, tau=TAU_REF, dt=DT, n=N_REF, seed=SEED_REF)
    d, l, cost = tt.path_tables(mode, rho, W_LOSS)
    opt = cost.argmin(axis=1); r = np.arange(len(opt))
    return float(((d[r,opt] > T_DELAY_MS) | (l[r,opt] > T_LOSS)).mean())

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="docs/phase-20R2/E1b-partition-invariance.json")
    ap.add_argument("--deterministic", action="store_true",
                    help="Omit time and commit metadata for byte-exact reproduction")
    a = ap.parse_args()
    tt = TruthTable(str(ROOT / "results/LIVE/phase-20R/truth_table.parquet"))
    manifest = json.loads(EXO.read_text())
    assert all((c["t_delay_ms"], c["t_loss"], c["w_loss"]) == (50.0, 0.01, 5000.0)
               for c in manifest["cells"]), "SLA constants differ from the E1 contract"
    self_cells = json.loads(SELF_CAL.read_text())["cells"]
    exo_cells  = {(c["mode"], round(float(c["rho_bar"]),6)): c
                  for c in json.loads(EXO.read_text())["cells"]}

    self_keys = {(c["mode"], round(float(c["rho_bar"]), 6)) for c in self_cells}
    assert len(self_keys) == len(self_cells) == len(manifest["cells"]) == len(exo_cells)
    assert self_keys == set(exo_cells), "Population differs across manifests"
    rows, mismatch, role_carried = [], [], []
    for c in self_cells:
        key = (c["mode"], round(float(c["rho_bar"]),6))
        role_self = c.get("role"); role_exo = exo_cells[key].get("role")
        if role_self != role_exo:
            role_carried.append({"cell": "%s@%.3f" % key, "self": role_self, "exo": role_exo})
        is_gate   = (role_self == "gate")
        axis_free = (c["mode"] != "cbr")
        if is_gate != axis_free:
            mismatch.append("%s@%.3f" % key)
        v_exo = ib_exo = None
        if c.get("feasible"):
            v_exo  = viol_rate_exogenous(tt, str(c["mode"]), float(c["rho_bar"]),
                                         float(c["sigma_rho"]))
            ib_exo = bool(VIOL_BAND[0] <= v_exo <= VIOL_BAND[1])
        rows.append({"cell": "%s@%.3f" % key, "mode": c["mode"], "rho_bar": float(c["rho_bar"]),
                     "feasible": bool(c.get("feasible")), "role": role_self,
                     "is_gate": is_gate, "axis_free_predicate_mode_ne_cbr": axis_free,
                     "predicate_matches_role": is_gate == axis_free,
                     "opt_viol_rate_self_calibrated": c.get("opt_viol_rate"),
                     "in_band_self_calibrated": c.get("in_band"),
                     "opt_viol_rate_exogenous": v_exo, "in_band_exogenous": ib_exo})

    feas  = [r for r in rows if r["feasible"]]
    flips = [r["cell"] for r in feas
             if r["in_band_self_calibrated"] != r["in_band_exogenous"]]

    out = {
      "WHAT_THIS_IS": ("Tinh chat MOI TRUONG. Khong doc mot cot ket qua nao. "
                       "Tra loi DUY NHAT cau: phan hoach gate/pc1 co phu thuoc truc SLA khong."),
      "schema": "dt4n.partition_invariance_20r2_e1.v1",
      "generated_by": "tools/20r2_9_partition_invariance.py",
      "generated_utc": datetime.now(timezone.utc).isoformat(),
      "git_commit": _git("rev-parse","HEAD"),
      "inputs_sha256": {str(SELF_CAL.relative_to(ROOT)): _sha(SELF_CAL),
                        str(EXO.relative_to(ROOT)): _sha(EXO),
                        "results/LIVE/phase-20R/truth_table.parquet":
                            _sha(ROOT / "results/LIVE/phase-20R/truth_table.parquet")},
      "constants": {"T_delay_ms": T_DELAY_MS, "T_loss": T_LOSS, "w_loss": W_LOSS,
                    "viol_band": list(VIOL_BAND), "tau": TAU_REF, "dt": DT,
                    "n": N_REF, "seed": SEED_REF},
      "P1_role_is_carried_verbatim_into_exogenous": {
          "verdict": "CARRIED" if not role_carried else "DIVERGES",
          "differences": role_carried,
          "why_it_matters": ("Manifest exogenous da XOA opt_viol_rate/in_band vi khong an toan "
                             "de doc, nhung GIU role -- ma role duoc SUY RA tu chinh in_band. "
                             "Bo nhiet ke, giu chan doan.")},
      "P2_partition_equals_axis_free_predicate": {
          "predicate": "role == 'gate'  <=>  mode != 'cbr'",
          "n_cells": len(rows), "n_match": sum(r["predicate_matches_role"] for r in rows),
          "mismatch": mismatch,
          "verdict": "PARTITION_IS_AXIS_FREE" if not mismatch else "PARTITION_DEPENDS_ON_AXIS"},
      "P3_negative_control_in_band_is_NOT_invariant": {
          "n_feasible": len(feas), "n_flip": len(flips), "flipped_cells": flips,
          "verdict": "CRITERION_NOT_INVARIANT" if flips else "CRITERION_INVARIANT",
          "reading": ("Tren truc self_calibrated MOI o kha thi khong suy bien deu ra DUNG "
                      "target_viol = 0.15 -- vi diem bat dong NHAM toi 0.15. Nen in_band la "
                      "TAUTOLOGY tren truc do: no chi phan biet 'phan phoi suy bien' voi "
                      "'khong suy bien'. Doi chung am nay la BANG CHUNG cho P2, khong phai loi.")},
      "rows": rows,
      "validity": {"schema": "dt4n.validity.v1", "axis_role": "measures_axis",
                   "note": ("Artifact DO tinh bat bien cua phan hoach. Co dung truc SLA "
                            "exogenous lam DOI CHUNG AM, khong dung lam nguon ket luan.")},
    }
    if a.deterministic:
        out.pop("generated_utc")
        out.pop("git_commit")
    out["source_sha256"] = {rel: _sha(ROOT / rel) for rel in (
        "tools/20r2_9_partition_invariance.py", "measurements/decision_error_v2.py",
        "measurements/sla_calib_v2.py", "twin/cost_v2.py",
        "twin/topology_v7.py", "twin/link_model.py")}
    p = ROOT / a.out; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    print("P1 role carried  :", out["P1_role_is_carried_verbatim_into_exogenous"]["verdict"])
    print("P2 partition     :", out["P2_partition_equals_axis_free_predicate"]["verdict"],
          "(%d/%d)" % (out["P2_partition_equals_axis_free_predicate"]["n_match"], len(rows)))
    print("P3 doi chung am  :", out["P3_negative_control_in_band_is_NOT_invariant"]["verdict"],
          "(%d/%d o lat)" % (len(flips), len(feas)))
    print("->", a.out)
    return int(bool(role_carried or mismatch or not flips))

if __name__ == "__main__":
    raise SystemExit(main())
