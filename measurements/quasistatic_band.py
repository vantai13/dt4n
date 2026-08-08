#!/usr/bin/env python3
"""Phase 20R.6 -- systematic-error band for the QUASI-STATIC assumption.

The quasi-static assumption says the system at instantaneous load ``rho(t)``
behaves like the steady state at that same load. If it is wrong, the error
enters exactly like an additive residual on the truth table -- the same shape as
the additivity residual -- so ``additivity_band.BiasedTruthTable`` applies
unchanged; only the source of the residual differs:

    additivity_band  : residual = A' - A                   (Lesson 20R.6)
    quasistatic_band : residual = err_dyn from Phase T     (Lesson T.6e)

This does not replace the live measurement. It converts a gap into a bounded
claim: if even the worst end of the Phase T interval moves no gate, the live
measurement becomes confirmatory rather than decisive.

The sweep also locates the BREAKDOWN THRESHOLD -- how large a residual would
have to be before a gate flips -- which is the number a reviewer asks for.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Optional, Sequence

from measurements import additivity_band as B
from measurements import decision_error_v2 as D
from twin import cost_v2 as C


PHASE_T_PAIRED = "results/phase-T/t6e_paired.json"
DELAY_SWEEP_MS = (0.0, -0.05, -0.10, -0.20, -0.50, -1.00, -2.00)
LOSS_SWEEP = (0.0, -0.0005, -0.0010, -0.0020, -0.0050, -0.0100, 0.0005, 0.0010, 0.0020, 0.0050)
G2_FLOOR = 0.03
OUT = "results/phase-20R/quasistatic_band.json"


def phase_t_err_dyn(path: str = PHASE_T_PAIRED) -> Dict[str, Dict[str, float]]:
    """Per-mode quasi-static error at LINK level, with the CI of the mean.

    A systematic offset applies to every link at once, so the relevant
    uncertainty is that of the mean, not the per-run spread. The per-run
    percentiles are carried along anyway because they bound a single window.
    """
    with open(path, "r", encoding="utf-8") as f:
        summary = json.load(f)["summary_dyn_by_mode"]
    out: Dict[str, Dict[str, float]] = {}
    for key, block in summary.items():
        mode = str(key).split("=", 1)[1]
        e = block["err_dyn_ms"]
        se = float(e["se_mean"])
        out[mode] = {
            "mean_ms": float(e["mean"]),
            "sd_ms": float(e["sd"]),
            "se_mean_ms": se,
            "n": int(e["n"]),
            "ci95_lo_ms": float(e["mean"]) - 1.96 * se,
            "ci95_hi_ms": float(e["mean"]) + 1.96 * se,
            "p05_ms": float(e["p05"]),
            "p95_ms": float(e["p95"]),
        }
    return out


def sweep(tt0, cv2, cells, seeds, n, resid_loss: float, resid_delay_ms: float) -> List[Dict[str, Any]]:
    """Inject one residual into every link and re-score the headline."""
    rows: List[Dict[str, Any]] = []
    for cell in sorted(cells, key=lambda c: (str(c["mode"]), float(c["rho_bar"]))):
        mode = str(cell["mode"])
        base = B.cell_metrics(tt0, cv2, cell, seeds, n)
        if resid_loss == 0.0 and resid_delay_ms == 0.0:
            pert = base
        else:
            pert = B.cell_metrics(B.BiasedTruthTable(resid_loss, resid_delay_ms, mode), cv2, cell, seeds, n)
        rows.append({
            "mode": mode,
            "rho_bar": float(cell["rho_bar"]),
            "err_base": base["err_total"],
            "d_sla_base": base["d_sla"],
            "d_err": pert["err_total"] - base["err_total"],
            "d_d_sla": pert["d_sla"] - base["d_sla"],
            "d_sla_perturbed": pert["d_sla"],
            "in_g2_set": bool(base["d_sla"] >= G2_FLOOR),
        })
    return rows


def verdict(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Only cells already in the G2 set can be flipped by the band."""
    g2 = [r for r in rows if r["in_g2_set"]]
    flipped = [r for r in g2 if r["d_sla_perturbed"] < G2_FLOOR]
    return {
        "max_abs_d_err": max(abs(r["d_err"]) for r in rows),
        "min_d_sla_in_g2": min((r["d_sla_perturbed"] for r in g2), default=None),
        "n_g2_cells": len(g2),
        "n_flipped": len(flipped),
        "flipped_cells": ["%s@%.3f" % (r["mode"], r["rho_bar"]) for r in flipped],
        "gate_survives": bool(not flipped),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", default="101,102,103")
    ap.add_argument("--n", type=int, default=120_000)
    ap.add_argument("--phase-t", default=PHASE_T_PAIRED)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)
    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]

    err_dyn = phase_t_err_dyn(args.phase_t)
    cv2, tt0 = C.CostV2(), D.TruthTable()
    cells = [c for c in D.feasible_cells(D.CALIBRATION, include_pc1=True) if str(c["mode"]) != "cbr"]

    print("=== SAI SO TUA TINH DO O PHASE T (muc link) ===")
    for mode in sorted(err_dyn):
        e = err_dyn[mode]
        print("  %-8s mean=%+8.4f ms  se=%.4f  n=%d  CI95=[%+.4f, %+.4f]  p05/p95=[%+.3f, %+.3f]"
              % (mode, e["mean_ms"], e["se_mean_ms"], e["n"], e["ci95_lo_ms"], e["ci95_hi_ms"],
                 e["p05_ms"], e["p95_ms"]))
    worst_ci = min(err_dyn[m]["ci95_lo_ms"] for m in err_dyn if m != "cbr")
    worst_p05 = min(err_dyn[m]["p05_ms"] for m in err_dyn if m != "cbr")
    print("  dau te nhat dung cho bien: CI95 %+.4f ms | mot cua so p05 %+.4f ms" % (worst_ci, worst_p05))

    report: Dict[str, Any] = {
        "phase": "20R.6", "kind": "quasistatic_systematic_band",
        "source_of_residual": args.phase_t,
        "phase_t_err_dyn": err_dyn,
        "g2_floor": G2_FLOOR, "seeds": seeds, "n": int(args.n),
        "delay_sweep": [], "loss_sweep": [],
    }

    print()
    print("=== KENH DELAY: bom phan du vao MOI link ===")
    print("%10s | %11s | %14s | %s" % ("resid_ms", "max|d err|", "min d_sla(G2)", "gate"))
    for r in DELAY_SWEEP_MS:
        rows = sweep(tt0, cv2, cells, seeds, args.n, 0.0, r)
        v = verdict(rows)
        report["delay_sweep"].append({"resid_delay_ms": r, "verdict": v, "rows": rows})
        print("%+10.3f | %11.5f | %14.4f | %s" % (r, v["max_abs_d_err"], v["min_d_sla_in_g2"],
              "SONG" if v["gate_survives"] else "LAT: " + ",".join(v["flipped_cells"])))

    print()
    print("=== KENH LOSS: tim NGUONG SUP DO ===")
    print("%10s | %11s | %14s | %s" % ("resid", "max|d err|", "min d_sla(G2)", "gate"))
    for r in LOSS_SWEEP:
        rows = sweep(tt0, cv2, cells, seeds, args.n, r, 0.0)
        v = verdict(rows)
        report["loss_sweep"].append({"resid_loss": r, "verdict": v, "rows": rows})
        print("%+10.4f | %11.5f | %14.4f | %s" % (r, v["max_abs_d_err"], v["min_d_sla_in_g2"],
              "SONG" if v["gate_survives"] else "LAT: " + ",".join(v["flipped_cells"])))

    neg = [e["resid_loss"] for e in report["loss_sweep"] if e["verdict"]["gate_survives"] and e["resid_loss"] < 0]
    pos = [e["resid_loss"] for e in report["loss_sweep"] if e["verdict"]["gate_survives"] and e["resid_loss"] > 0]
    dly = [e["resid_delay_ms"] for e in report["delay_sweep"] if e["verdict"]["gate_survives"]]
    report["breakdown"] = {
        "loss_max_negative_surviving": min(neg) if neg else None,
        "loss_max_positive_surviving": max(pos) if pos else None,
        "delay_max_surviving_ms": min(dly) if dly else None,
        "measured_additivity_residual": {"h2": -0.001884, "poisson": -0.000262},
    }
    print()
    print("nguong sup do: loss am toi %s | loss duong toi %s | delay toi %s ms"
          % (report["breakdown"]["loss_max_negative_surviving"],
             report["breakdown"]["loss_max_positive_surviving"],
             report["breakdown"]["delay_max_surviving_ms"]))

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, sort_keys=True, default=str)
        f.write("\n")
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
