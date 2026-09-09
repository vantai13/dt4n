#!/usr/bin/env python3
"""T2.6 vong 3 -- PHAN QUYET. Chi ap CHINH SACH DA KY.

Nguon chinh sach (khong mot nguong nao dat moi o day):
    QD-2  tau* la mot DUONG tren lift_min {0.05, 0.10, 0.20}
    QD-5  moi so bao cao kem n va bat dinh
    QD-6  nhan D-T2.6-*
    QD-7  k=3.0, san=0.05 -> docs/phase-T2/05-band-window-v2.json (A-T2-3 e)
    D-T2.6-3  tieu chi CONG SUAT: bien do / san nhieu; san nhieu =
              mean |ratio_measured - ratio_measured_sim| (hai uoc luong doc lap)
              NGUONG 5.0 / 2.0 -- DA KY o tools/t2_1_prediction.py:276-277,
              ghim boi test/test_t2_1_prediction.py:185-186, va ghi o
              00-preregistration.md:643-645. KHONG dung 10.0/3.0: xem
              ERRATUM A-T2-3.2 muc (3).
    A-T2-3 nhanh (c) + ERRATUM A-T2-3.2 muc (2): R(tau) doc tu ban KHOP MUC

Neu ban thay minh muon them mot nguong o day, DUNG LAI: no phai duoc ky o
prereg truoc, khong phai o day.

    python3 tools/t2_6b_adjudicate.py
"""
from __future__ import annotations

import glob
import json
import math
import pathlib
import sys
from typing import Any, Dict, List

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SWEEP = ROOT / "results/PENDING/phase-T2/sweep_r3"
SIGNED = ROOT / "docs/phase-T2/01-prediction-signed.json"
BANDS = ROOT / "docs/phase-T2/05-band-window-v2.json"
DESCR = ROOT / "docs/phase-T2/04-estimand-descriptor.json"
OUT = SWEEP / "adjudication_r3.json"

Z_FIXED = (0.05, 0.10, 0.30, 0.55)
TAU_LO, TAU_HI = 0.5, 28.0
LIFT_MIN_GRID = (0.05, 0.10, 0.20)          # QD-2
POWER_READABLE, POWER_WEAK = 5.0, 2.0       # DA KY, xem docstring
CONFIRMATORY = ("h2@0.700", "poisson@0.850", "poisson@0.925")
NEG_CONTROL = ("cbr@0.700",)


def rms_law(A: float, c: float, em: float, z: float, tau: float) -> float:
    """Luat AR(1) da ky. KHONG fit lai."""
    return math.sqrt(em ** 2 + c * A ** 2 * (1.0 - math.exp(-z / tau)))


def load_runs(pattern: str = "t2_6b_r*.json") -> List[Dict[str, Any]]:
    out = []
    for p in sorted(glob.glob(str(SWEEP / pattern))):
        d = json.loads(pathlib.Path(p).read_text())
        d["_path"] = pathlib.Path(p).name
        out.append(d)
    return out


def scope_of(cell: str) -> str:
    if cell in CONFIRMATORY:
        return "CONFIRMATORY"
    if cell in NEG_CONTROL:
        return "NEGATIVE_CONTROL"
    return "EXPLORATORY"


def _a_of(run: Dict[str, Any]):
    return run.get("sigma_axis", {}).get("a")


def _arm_key(run: Dict[str, Any]) -> str:
    """Ten arm sigma. Arm legacy dung sigma= tuyet doi nen a = None.

    Do duoc khi kiem co hoc tren legacy_*.json: "a=%.1f" % None crash voi
    TypeError o adj_3, adj_4, adj_6. Sua TRUOC khi tro vao luoi chinh.
    """
    ax = run.get("sigma_axis", {})
    if ax.get("a") is not None:
        return "a=%.1f" % float(ax["a"])
    if ax.get("sigma") is not None:
        return "sigma=%g" % float(ax["sigma"])
    return "sigma_axis_unknown"


def law_is_valid(run: Dict[str, Any]) -> bool:
    """Neu luat rms khong khop trong 2% thi D-T2.6-1/-2/-6 khong doc duoc."""
    return bool(run["gates"].get("ar1_rms_total_fit_within_2pct", False))


# ------------------------------------------------------------------ D-1
def adj_1(runs) -> Dict[str, Any]:
    """rms don dieu GIAM theo tau, moi o song, moi z."""
    viol, checked, skipped = [], 0, []
    for r in runs:
        cell, sc = r["cell"], scope_of(r["cell"])
        if sc != "CONFIRMATORY":
            continue
        if not law_is_valid(r):
            skipped.append({"cell": cell, "a": _a_of(r),
                            "why": "ar1_rms_total_fit_within_2pct = false"})
            continue
        rows = sorted(r["rows"], key=lambda x: x["tau"])
        for z in Z_FIXED:
            seq = [rms_law(x["ar1_fit"]["A"], x["ar1_fit"]["c"],
                           x["ar1_fit"]["rms_e_model"], z, x["tau"])
                   for x in rows]
            checked += 1
            if not all(a >= b for a, b in zip(seq, seq[1:])):
                viol.append({"cell": cell, "a": _a_of(r), "z": z, "seq": seq})
    state = "PASS" if (not viol and checked) else ("FAIL" if viol else "NOT_EVALUATED")
    return {"state": state,
            "n_checked": checked, "n_violations": len(viol),
            "violations": viol[:8], "skipped_law_invalid": skipped,
            "basis": "luat rms voi A,c,em DO DUOC vong 3; luat da gate 2%"}


# ------------------------------------------------------------------ D-2
def adj_2(runs, signed, bands) -> Dict[str, Any]:
    """rms(28)/rms(0.5) o z co dinh, so voi diem ky +/- bang 05-v2."""
    pred = signed["signed_predictions"]["D-T2.6-2"]["per_cell"]
    per, n_in, n_out, skipped = {}, 0, 0, []
    for r in runs:
        cell = r["cell"]
        if scope_of(cell) != "CONFIRMATORY" or cell not in pred:
            continue
        if not law_is_valid(r):
            skipped.append({"cell": cell, "a": _a_of(r),
                            "why": "ar1_rms_total_fit_within_2pct = false"})
            continue
        a = _a_of(r)
        by_tau = {x["tau"]: x["ar1_fit"] for x in r["rows"]}
        if TAU_LO not in by_tau or TAU_HI not in by_tau:
            skipped.append({"cell": cell, "a": a, "why": "thieu tau 0.5 hoac 28"})
            continue
        band = bands["windows"].get(cell, {}).get("recommended_band")
        for z in Z_FIXED:
            f_lo, f_hi = by_tau[TAU_LO], by_tau[TAU_HI]
            got = (rms_law(f_hi["A"], f_hi["c"], f_hi["rms_e_model"], z, TAU_HI)
                   / rms_law(f_lo["A"], f_lo["c"], f_lo["rms_e_model"], z, TAU_LO))
            exp = pred[cell]["%.2f" % z]
            inside = band is not None and abs(got - exp) <= band
            n_in += inside
            n_out += (not inside)
            per.setdefault(cell, {}).setdefault(_arm_key(r), {})["%.2f" % z] = {
                "measured": got, "signed": exp, "band": band,
                "abs_diff": abs(got - exp), "inside": bool(inside)}
    state = ("NOT_EVALUATED" if (n_in + n_out) == 0
             else "PASS" if n_out == 0 else "FAIL")
    return {"state": state, "n_inside": n_in, "n_outside": n_out,
            "skipped": skipped,
            "band_source": "docs/phase-T2/05-band-window-v2.json (A-T2-3 e)",
            "per_cell": per}


# ------------------------------------------------------------------ D-3
def adj_3(runs, signed) -> Dict[str, Any]:
    """R(tau): NHANH CHINH = ban KHOP MUC (bien phap da ky, nhanh (c))."""
    node = signed["signed_predictions"]["D-T2.6-3"]
    pred = node["per_cell"]
    declared = node.get("power_scope_declared_before_run", {})
    per = {}
    for r in runs:
        cell = r["cell"]
        if scope_of(cell) == "EXPLORATORY":
            continue
        a = _a_of(r)
        rows = sorted(r["rows"], key=lambda x: x["tau"])
        noise_pairs = [(x["ratio_measured"], x["ratio_measured_sim"]) for x in rows
                       if x["ratio_measured"] is not None
                       and x["ratio_measured_sim"] is not None
                       and np.isfinite(x["ratio_measured"])
                       and np.isfinite(x["ratio_measured_sim"])]
        noise = float(np.mean([abs(u - v) for u, v in noise_pairs])) if noise_pairs else None

        def arm(key):
            if key == "matched":
                vals = [(x["tau"], (x.get("level_matched") or {}).get("ratio_measured"))
                        for x in rows]
            else:
                vals = [(x["tau"], x["ratio_measured"]) for x in rows]
            vals = [(t, v) for t, v in vals
                    if v is not None and np.isfinite(v)]
            if len(vals) < 3 or noise is None:
                return None
            taus = [t for t, _ in vals]
            rs = [v for _, v in vals]
            i = int(np.argmax(rs))
            amp = float(max(rs) - min(rs))
            ratio = amp / noise if noise > 0 else float("inf")
            scope = ("READABLE" if ratio >= POWER_READABLE else
                     "WEAK" if ratio >= POWER_WEAK else "INSUFFICIENT_POWER")
            return {"taus": taus, "R": rs,
                    "is_hump": bool(0 < i < len(rs) - 1),
                    "peak_tau": float(taus[i]),
                    "hump_amplitude": amp, "noise_floor": noise,
                    "amplitude_over_noise": ratio, "power_scope": scope,
                    "signed_peak_s": pred.get(cell),
                    "power_scope_declared_before_run":
                        declared.get(cell, {}).get("declared_scope")}

        per.setdefault(cell, {})[_arm_key(r)] = {
            "PRIMARY_level_matched": arm("matched"),
            "SENSITIVITY_full_data": arm("full"),
            "note": ("NHANH CHINH la ban khop muc theo bien phap DA KY o "
                     "A-T2-3 nhanh (c) va ERRATUM A-T2-3.2 muc (2). Arm day "
                     "du chi BAO CAO, khong lat verdict."),
        }

    scopes = [v[k]["PRIMARY_level_matched"]["power_scope"]
              for v in per.values() for k in v
              if v[k]["PRIMARY_level_matched"]]
    conf = [v[k]["PRIMARY_level_matched"]["power_scope"]
            for c, v in per.items() for k in v
            if scope_of(c) == "CONFIRMATORY" and v[k]["PRIMARY_level_matched"]]
    if not conf:
        state = "NOT_EVALUATED"
    elif all(s == "INSUFFICIENT_POWER" for s in conf):
        state = "INSUFFICIENT_POWER"
    else:
        state = "READ_BELOW_PER_CELL"
    return {"state": state, "power_scopes": scopes,
            "power_scopes_confirmatory": conf,
            "power_thresholds": {"READABLE": POWER_READABLE, "WEAK": POWER_WEAK,
                                 "source": "tools/t2_1_prediction.py:276-277"},
            "per_cell": per}


# ------------------------------------------------------------------ D-4
def adj_4(runs) -> Dict[str, Any]:
    """span GIUA-tau < spread TRONG-tau, cho X in {A, c, rms_e_model}."""
    per, n_pass, n_fail = {}, 0, 0
    for r in runs:
        cell = r["cell"]
        if scope_of(cell) != "CONFIRMATORY":
            continue
        a = _a_of(r)
        s = r["summary"]
        # !! SAN NHIEU la spread TRUNG BINH tren cac tau, KHONG phai max.
        #    Ban DA KY: tools/t2_1_prediction.py:256-257 -> passes = span < mean_w.
        #    Dung max() se NOI LONG tieu chi (max >= mean) va la mot nguong khac
        #    voi nguong da ky. Kiem tu than: adj_4 tren legacy_*.json phai tai
        #    tao n_fail_on_22_6 = 3 cua artifact da ky.
        spreads = {
            "A": [x["ar1_fit"]["A_spread_pct"] for x in r["rows"]],
            "c": [x["ar1_fit"]["c_spread_pct"] for x in r["rows"]],
            "em": [x["ar1_fit"]["rms_em_spread_pct"] for x in r["rows"]],
        }
        pairs = {
            "A": (s["A_span_pct"], spreads["A"]),
            "c": (s["c_span_pct"], spreads["c"]),
            "em": (s["rms_em_span_pct"], spreads["em"]),
        }
        for x, (span, w) in pairs.items():
            mean_w = float(np.mean(w))
            ok = span < mean_w
            n_pass += ok
            n_fail += (not ok)
            per.setdefault(cell, {}).setdefault(_arm_key(r), {})[x] = {
                "span_between_tau_pct": span,
                "spread_within_tau_pct_mean": mean_w,
                "spread_within_tau_pct_max": float(max(w)),
                "ratio_span_over_spread": span / mean_w if mean_w else None,
                "passes": bool(ok)}
    state = ("NOT_EVALUATED" if (n_pass + n_fail) == 0
             else "PASS" if n_fail == 0 else "FAIL")
    return {"state": state, "n_pass": n_pass, "n_fail": n_fail, "per_cell": per,
            "note": "khong thu nguyen, tu hieu chuan, khong can ky nguong"}


# ------------------------------------------------------------------ D-5
def adj_5() -> Dict[str, Any]:
    src = ROOT / "results/PENDING/phase-T2/adjudication_r2.json"
    prev = json.loads(src.read_text())["verdicts"]["D-T2.6-5"]
    return {"state": prev["state"],
            "carried_from": str(src.relative_to(ROOT)),
            "estimand_id": "RMS_ALLACTION_DELAY",
            "why_a_different_estimand_is_legitimate_here": (
                "D-T2.6-5 la doi chung noi giua HAI NHANH cua "
                "measurements/decision_error_v2.py, khong phai mot khang dinh "
                "ve lop chung nhan. No song tren estimand cua chinh harness do."),
            "evidence": prev}


# ------------------------------------------------------------------ D-6
def adj_6(runs, signed) -> Dict[str, Any]:
    """tau_knee = tau nho nhat de rms ve trong 5% cua em."""
    pred = signed["signed_predictions"]["D-T2.6-6"]["per_cell"]
    grid_max = max(TAU_HI, 28.0)
    per = {}
    for r in runs:
        cell = r["cell"]
        if scope_of(cell) != "CONFIRMATORY" or cell not in pred:
            continue
        if not law_is_valid(r):
            continue
        a = _a_of(r)
        by_tau = {x["tau"]: x["ar1_fit"] for x in sorted(r["rows"],
                                                         key=lambda y: y["tau"])}
        for z in Z_FIXED:
            knee = None
            for tau in sorted(by_tau):
                f = by_tau[tau]
                if rms_law(f["A"], f["c"], f["rms_e_model"], z, tau) \
                        <= 1.05 * f["rms_e_model"]:
                    knee = tau
                    break
            per.setdefault(cell, {}).setdefault(_arm_key(r), {})["%.2f" % z] = {
                "measured_knee_s": knee,
                "measured_note": None if knee else "> %g s (ngoai luoi)" % grid_max,
                "signed_knee_s": pred[cell]["%.2f" % z],
                "signed_is_outside_grid": pred[cell]["%.2f" % z] > grid_max,
            }
    return {"state": "REPORTED",
            "note": ("Du doan DA BAO TRUOC rang phan lon knee nam NGOAI luoi. "
                     "'Ngoai luoi' la KET QUA HOP LE; KHONG mo rong luoi de "
                     "di tim knee (T2-6 nhanh c)."),
            "per_cell": per}


# ------------------------------------------------------------------ D-7
def adj_7(runs, signed) -> Dict[str, Any]:
    A_signed = signed["signed_predictions"]["D-T2.6-7"]["A_measured"]
    rows = []
    for r in runs:
        if r["cell"] not in NEG_CONTROL:
            continue
        for x in r["rows"]:
            rows.append({"a": _a_of(r), "tau": x["tau"],
                         "A": x["ar1_fit"]["A"],
                         "ratio_measured": x["ratio_measured"]})
    ratios = [v["ratio_measured"] for v in rows
              if v["ratio_measured"] is not None and np.isfinite(v["ratio_measured"])]
    if not rows:
        return {"state": "NOT_EVALUATED", "note": "khong co o doi chung am"}
    dead = bool(ratios) and max(abs(x - 1.0) for x in ratios) < 0.05
    return {"state": "PASS" if dead else "FAIL",
            "A_signed_at_22_6": A_signed,
            "A_range_measured": [min(v["A"] for v in rows),
                                 max(v["A"] for v in rows)],
            "max_abs_ratio_minus_one": (max(abs(x - 1.0) for x in ratios)
                                        if ratios else None),
            "note": "doi chung AM: cbr phai tiep tuc cho R ~ 1 o moi tau"}


# ------------------------------------------------------------------ main
def main() -> int:
    runs = load_runs()
    signed = json.loads(SIGNED.read_text())
    bands = json.loads(BANDS.read_text())

    v = {"D-T2.6-1": adj_1(runs),
         "D-T2.6-2": adj_2(runs, signed, bands),
         "D-T2.6-3": adj_3(runs, signed),
         "D-T2.6-4": adj_4(runs),
         "D-T2.6-5": adj_5(),
         "D-T2.6-6": adj_6(runs, signed),
         "D-T2.6-7": adj_7(runs, signed)}

    counted = {k: x["state"] for k, x in v.items()}
    n_pass = sum(s == "PASS" for s in counted.values())
    n_fail = sum(s == "FAIL" for s in counted.values())
    n_ip = sum(s == "INSUFFICIENT_POWER" for s in counted.values())

    expl = sorted({r["cell"] for r in runs if scope_of(r["cell"]) == "EXPLORATORY"})
    hyg = SWEEP / "hygiene_r3.json"
    doc = {
        "phase": "T2.6 round 3",
        "amendment": "A-T2-3 (+ ERRATUM A-T2-3.1, A-T2-3.2)",
        "estimand_id": "RMS_MARGIN_COST",
        "R_tau_primary_arm": "level_matched (bien phap DA KY, nhanh (c))",
        "hygiene": json.loads(hyg.read_text()) if hyg.is_file() else None,
        "verdicts": v,
        "summary": {"n_total": 7, "n_pass": n_pass, "n_fail": n_fail,
                    "n_insufficient_power": n_ip,
                    "states": counted,
                    "denominator_declared_before_reading": 7,
                    "note": ("INSUFFICIENT_POWER KHONG vao TU SO va VAN o "
                             "MAU SO. Mau so = 7, khai TRUOC khi doc "
                             "(ERRATUM A-T2-3.2 muc 4).")},
        "exploratory_cells": {
            "cells": expl, "state": "REPORTED_ONLY",
            "rule": ("khong sinh verdict, khong vao ti le dung, khong lat "
                     "verdict cua o CONFIRMATORY; chi de RA CAU HOI cho 21R2"),
        },
        "tau_star": {
            "state": "NOT_MEASURABLE_BY_THIS_INSTRUMENT",
            "why": ("tau* doi hoi lift(tau) = (err_baseline - err_certified)/"
                    "err_baseline. err_* song o RMS_ALLACTION_DELAY "
                    "(measurements/decision_error_v2.py); q_hat song o "
                    "RMS_MARGIN_COST (cert/tau_sweep.py). Khong harness nao co "
                    "ca hai (do bang grep, ERRATUM A-T2-3.2 muc 6). Suy tau* tu "
                    "R(tau) la DUNG loai loi vua sua."),
            "lift_min_grid_signed": list(LIFT_MIN_GRID),
            "handoff": "thiet ke do lift ban giao cho 21R2; xem T2.7",
        },
        "provenance": {"script": "tools/t2_6b_adjudicate.py",
                       "n_artifacts": len(runs),
                       "signed_prediction": str(SIGNED.relative_to(ROOT)),
                       "estimand_descriptor": str(DESCR.relative_to(ROOT)),
                       "band_window": str(BANDS.relative_to(ROOT))},
    }
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True,
                              default=float) + "\n")
    print(json.dumps(doc["summary"], indent=1))
    for k in sorted(v):
        print("  %-10s %s" % (k, v[k]["state"]))
    print("  tau_star   %s" % doc["tau_star"]["state"])
    print("-> %s" % OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
