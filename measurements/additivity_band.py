#!/usr/bin/env python3
"""Phase 20R.6 -- systematic-error band on the headline numbers.

``A' - A`` leaves an additive per-link residual after the burstiness term is
removed. If that residual is real, the truth table -- which plays "reality" in
``decision_error_v2`` -- is offset, and every headline number inherits the offset.
This propagates it onto ``err`` and ``d_sla`` at the SAWTOOTH operating point,
i.e. the estimator the headline actually used.

Design notes:

* The twin is ``cost_v2``, an independent analytic model. The residual perturbs
  only the truth side, so it does not cancel by symmetry.
* Evaluated at BOTH ends of the residual's CI90, never at the point estimate
  alone: the sign of the residual decides whether a headline number is an upper
  or a lower bound.
* Loss is floored at 0. A constant additive model must not be allowed to produce
  negative loss, which it otherwise does at the low-rho cells.
* Pooling the three link residuals into one common-mode value is only legitimate
  if they are homogeneous, so Cochran's Q is computed and reported rather than
  assumed.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence

import numpy as np

from measurements import decision_error_v2 as D
from twin import cost_v2 as C
from twin import topology_v7 as T7


DIAG_CA = "results/SUPERSEDED/phase-20R/diag_ca_late_inband.json"
CHECK_REPORT = "results/SMOKE/phase-20R/additivity_check_inband_bg.json"
OUT = "results/SUPERSEDED/phase-20R/additivity_band_sawtooth.json"
N_CLASS = 3
Z90 = 1.644854
G2_FLOOR = 0.03


def load_residuals(diag_ca: str = DIAG_CA, check_report: str = CHECK_REPORT) -> Dict[str, Dict[str, Any]]:
    """Per-mode residual: point estimate, pooled SE, and a homogeneity test."""
    with open(diag_ca, "r", encoding="utf-8") as f:
        sens = json.load(f)["burstiness_sensitivity"]
    with open(check_report, "r", encoding="utf-8") as f:
        checks = json.load(f)["checks"]
    se_link = {
        (str(r["mode"]), str(r["link"])): float(r["se_ms"])
        for r in checks
        if r.get("contrast") == "Aprime_minus_A_loss"
    }
    delay_path = {
        str(r["mode"]): float(r["mean_ms"])
        for r in checks
        if r.get("contrast") == "Aprime_minus_A_path_delay"
    }
    out: Dict[str, Dict[str, Any]] = {}
    for mode in sorted({str(r["mode"]) for r in sens}):
        rows = [r for r in sens if str(r["mode"]) == mode and r.get("residual_quad") is not None]
        vals = np.array([float(r["residual_quad"]) for r in rows], dtype=float)
        ses = np.array([se_link.get((mode, str(r["link"])), 0.0) for r in rows], dtype=float)
        w = 1.0 / np.maximum(ses, 1e-12) ** 2
        mean_w = float(np.sum(w * vals) / np.sum(w))
        # Cochran's Q: are the three link estimates compatible with ONE value?
        q = float(np.sum(w * (vals - mean_w) ** 2))
        df = max(len(vals) - 1, 1)
        i2 = max(0.0, (q - df) / q) if q > 0 else 0.0
        se_pooled = float(np.mean(ses) / math.sqrt(N_CLASS))
        point = float(np.mean(vals))
        out[mode] = {
            "point": point,
            "se_pooled": se_pooled,
            "ci90": [point - Z90 * se_pooled, point + Z90 * se_pooled],
            "per_link": {str(r["link"]): float(r["residual_quad"]) for r in rows},
            "cochran_q": q,
            "cochran_df": int(df),
            "i_squared": i2,
            "homogeneous": bool(i2 < 0.5),
            "delay_path_ms": float(delay_path.get(mode, 0.0)),
        }
    return out


class BiasedTruthTable(D.TruthTable):
    """Truth table plus a per-link additive residual, with loss floored at 0."""

    def __init__(self, resid_loss: float, resid_delay_ms: float, mode: str, parquet_path: str = D.TRUTH_TABLE):
        super().__init__(parquet_path)
        self._resid_loss = float(resid_loss)
        self._resid_delay = float(resid_delay_ms)
        self._mode = str(mode)

    def delay_loss(self, mode, link, rho):
        delay, loss = super().delay_loss(mode, link, rho)
        if str(mode) != self._mode:
            return delay, loss
        return delay + self._resid_delay, np.clip(loss + self._resid_loss, 0.0, 1.0)


def cell_metrics(tt: D.TruthTable, cv2: C.CostV2, cell: Mapping[str, Any], seeds: Sequence[int], n: int) -> Dict[str, float]:
    acc: Dict[str, List[float]] = {"err_total": [], "d_sla": []}
    for seed in seeds:
        series = D._sawtooth_metric_series(D._cell_arrays(tt, cv2, cell, seed=int(seed), n=int(n)))
        for key in acc:
            acc[key].append(float(np.mean(series[key])))
    return {key: float(np.mean(vals)) for key, vals in acc.items()}


def fragility(tt: D.TruthTable, cell: Mapping[str, Any], resid: float) -> Dict[str, Any]:
    """F = |path-loss shift| / distance from the nearest action to the threshold.

    ``d_sla`` counts threshold crossings, so what matters is not the size of the
    shift on its own but its size relative to how close an action already sits to
    ``t_loss``. ``min`` over actions, not the mean: one crossing is enough to move
    the count, and the nearest action crosses first.
    """
    mode = str(cell["mode"])
    rho = C.rho_vector(float(cell["rho_bar"]))
    losses = []
    for path in T7.PATH_NAMES:
        keep = 1.0
        for link in T7.PATHS[path]:
            _d, l = tt.delay_loss(mode, link, np.asarray([rho[link]], dtype=float))
            keep *= 1.0 - float(l[0])
        losses.append(1.0 - keep)
    t_loss = float(cell["t_loss"])
    gaps = [abs(v - t_loss) for v in losses]
    shift = abs(float(resid)) * N_CLASS
    return {
        "path_loss": losses,
        "signed_gap": [v - t_loss for v in losses],
        "min_gap": float(min(gaps)),
        "n_above": int(sum(1 for v in losses if v > t_loss)),
        "fragility_index": float(shift / max(min(gaps), 1e-12)),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--diag-ca", default=DIAG_CA)
    ap.add_argument("--check-report", default=CHECK_REPORT)
    ap.add_argument("--seeds", default="101,102,103,104,105")
    ap.add_argument("--n", type=int, default=120_000)
    ap.add_argument("--g2-floor", type=float, default=G2_FLOOR)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)
    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]

    resid = load_residuals(args.diag_ca, args.check_report)
    cv2 = C.CostV2()
    tt0 = D.TruthTable()
    cells = [c for c in D.feasible_cells(D.CALIBRATION, include_pc1=True) if str(c["mode"]) != "cbr"]

    print("=== PHAN DU, GOP, VA KIEM DONG NHAT (Cochran Q) ===")
    for mode, info in sorted(resid.items()):
        flag = "  <- CI CHUA 0" if info["ci90"][0] < 0.0 < info["ci90"][1] else ""
        print(
            "  %-8s %+.6f  se_gop %.6f  CI90 [%+.6f, %+.6f]  Q=%.2f (df=%d) I2=%.0f%% %s%s"
            % (mode, info["point"], info["se_pooled"], info["ci90"][0], info["ci90"][1],
               info["cochran_q"], info["cochran_df"], 100.0 * info["i_squared"],
               "dong nhat" if info["homogeneous"] else "DI DIEU -> gop kem tin cay", flag)
        )

    print()
    print("=== BANG SAI SO HE THONG -- diem van hanh sawtooth ===")
    hdr = "%-8s %7s %6s %4s | %8s %-20s | %8s %-20s | %s"
    print(hdr % ("mode", "rho_bar", "F", "n_up", "err", "bien d err", "d_sla", "bien d d_sla", "G2 xau nhat"))
    rows: List[Dict[str, Any]] = []
    for cell in sorted(cells, key=lambda c: (str(c["mode"]), float(c["rho_bar"]))):
        mode = str(cell["mode"])
        info = resid[mode]
        base = cell_metrics(tt0, cv2, cell, seeds, args.n)
        ends = []
        for r in info["ci90"]:
            tt = BiasedTruthTable(r, info["delay_path_ms"] / N_CLASS, mode)
            ends.append(cell_metrics(tt, cv2, cell, seeds, args.n))
        d_err = sorted(e["err_total"] - base["err_total"] for e in ends)
        d_sla = sorted(e["d_sla"] - base["d_sla"] for e in ends)
        worst = base["d_sla"] + d_sla[0]
        frag = fragility(tt0, cell, info["point"])
        # A cell whose baseline d_sla is already under the floor was never in the
        # G2 set; only a DAT -> TRUOT flip is caused by the band.
        g2_base = "DAT" if base["d_sla"] >= args.g2_floor else "ngoai tap"
        g2 = "DAT" if worst >= args.g2_floor else "TRUOT"
        flipped = bool(g2_base == "DAT" and g2 == "TRUOT")
        print(hdr % (mode, "%.3f" % float(cell["rho_bar"]), "%.1f" % frag["fragility_index"],
                     "%d/4" % frag["n_above"],
                     "%.4f" % base["err_total"], "[%+.4f, %+.4f]" % tuple(d_err),
                     "%.4f" % base["d_sla"], "[%+.4f, %+.4f]" % tuple(d_sla),
                     "%-10s %.4f%s" % (g2_base if g2_base != "DAT" else g2, worst,
                                       "  <- LAT" if flipped else "")))
        rows.append({
            "mode": mode, "rho_bar": float(cell["rho_bar"]),
            "t_loss": float(cell["t_loss"]), "t_delay_ms": float(cell["t_delay_ms"]),
            "fragility_index": frag["fragility_index"], "min_gap": frag["min_gap"],
            "n_actions_above_threshold": frag["n_above"], "signed_gap": frag["signed_gap"],
            "err": base["err_total"], "d_err_lo": d_err[0], "d_err_hi": d_err[1],
            "d_sla": base["d_sla"], "d_sla_lo": d_sla[0], "d_sla_hi": d_sla[1],
            "d_sla_worst": worst, "g2_under_band": g2,
            "g2_baseline": g2_base, "g2_flipped_by_band": flipped,
        })

    in_set = [r for r in rows if r["g2_baseline"] == "DAT"]
    fails = [r for r in rows if r["g2_flipped_by_band"]]
    print()
    print("Tap G2 (d_sla goc >= %.2f): %d/%d o. Bi bien LAT tu DAT sang TRUOT: %d"
          % (args.g2_floor, len(in_set), len(rows), len(fails)))
    for r in fails:
        print("  !! %s @ %.3f  d_sla %.4f -> %.4f   F=%.1f   t_loss=%.2e  min_gap=%.2e"
              % (r["mode"], r["rho_bar"], r["d_sla"], r["d_sla_worst"],
                 r["fragility_index"], r["t_loss"], r["min_gap"]))

    n_cons = sum(1 for r in rows if r["d_sla_hi"] <= 0.0)
    n_err_up = sum(1 for r in rows if r["d_err_hi"] > 0.0)
    print()
    print("huong lech: d_sla <= 0 o %d/%d o (con so cong bo la CAN TREN)" % (n_cons, len(rows)))
    print("            d_err  > 0 o %d/%d o (o do err cong bo la CAN DUOI -- KHONG bao thu)"
          % (n_err_up, len(rows)))

    report = {
        "phase": "20R.6",
        "kind": "additivity_band_sawtooth",
        "residual": resid,
        "seeds": seeds,
        "n": int(args.n),
        "z90": Z90,
        "g2_floor": float(args.g2_floor),
        "n_cells_in_g2_set": len(in_set),
        "n_cells_flipped_by_band": len(fails),
        "rows": rows,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True, default=str)
        f.write("\n")
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
