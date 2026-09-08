#!/usr/bin/env python3
"""T2.1 -- suy DU DOAN cua Phase T2 tu artifact 22.6 DA COMMIT. CHI DOC.

Khong fit lai gi. Lay A, c, em da fit o 22.6 roi AP LUAT AR(1) len luoi tau
mo rong cua T2. Ket qua ghi ra mot artifact co provenance de prereg T2-5
TRO VAO thay vi chep so.

Luat (quy uoc HIEU, khop estimand cua 20R -- xem docs/GLOSSARY.md muc "sat"):

    rms_total(z, tau) = sqrt( em^2 + c * A^2 * (1 - exp(-z/tau)) )

Dai luong duoc du doan la `rms_total` (RMS sai so chi phi), KHONG phai
`err_total` (ti le quyet dinh sai). Luat nay khong mo hinh hoa phep bien doi
tu rms sang ti le quyet dinh sai, nen voi `err_total` chi ky duoc THU TU
(don dieu), khong ky duoc ti so.

Doi chung noi: script phai tai tao `ratio_pred_finite` cua chinh 22.6 tu
A, c, em doc ra. Lech > 1e-9 nghia la da doc sai artifact.

    python3 tools/t2_1_prediction.py
    python3 tools/t2_1_prediction.py --out docs/phase-T2/01-prediction-signed.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import subprocess
from typing import Any, Dict, List, Sequence

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "results/SUPERSEDED/phase-22"          # tang da chot, amendment 23-44
OUT = ROOT / "docs/phase-T2/01-prediction-signed.json"

# Luoi cua prereg T2-4.
# tau=0.5 CO trong luoi: no la mau so cua D-T2.6-2 (TAU_LO duoi day) va no
# qua realizability_gate (0.5 >= 20*dt = 0.1; 400 block/seed). Bo no ra khoi
# TAUS cua t2_6_plan la mot lech luoi -- du doan ky o mot diem khong chay.
TAU_GRID_T2: Sequence[float] = (0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 28.0)

# Nhanh B: z CO DINH theo chu ky dong bo, KHONG co gian theo tau.
# !! MOI GIA TRI O DAY PHAI CO TRONG measurements/decision_error_v2.py:Z_ALL.
#    Harness sinh z tu Z_ALL; mot muc z khong nam trong do se KHONG BAO GIO
#    duoc do, va du doan tai do la NOT_EVALUATED chu khong phai FAIL.
#    Z_ALL = (0.0, 0.05, 0.10, 0.20, 0.30, 0.55, 1.0, 2.0, 4.0)
#    Chon 4 muc trong phan NOI SUY (Z_GRID), tranh Z_EXTRAP.
Z_FIXED_S: Sequence[float] = (0.05, 0.10, 0.30, 0.55)

# Nhanh A: z/tau co dinh (tai tao 20R legacy).
Z_OVER_TAU: Sequence[float] = (0.10, 0.30, 0.55, 1.00)

# Cap tau dung cho ti so bao cao cua nhanh B. TAU_LO PHAI nam trong
# TAU_GRID_T2 va trong TAUS cua t2_6_plan.py.
TAU_LO, TAU_HI = 0.5, 28.0
# Khoa cua ti so trong artifact. Sinh MOT LAN tu TAU_HI/TAU_LO roi dung lai
# o moi cho doc: truoc day khoa duoc SINH dong o _branch_b nhung DOC bang
# chuoi cung "ratio_tau28_over_tau0.5", nen doi TAU_LO se gay KeyError.
RATIO_KEY = "ratio_tau%g_over_tau%g" % (TAU_HI, TAU_LO)
# tau_knee: tau nho nhat ma duong da ve trong KNEE_TOL cua tiem can em.
KNEE_TOL = 0.05
# Cell chet, giu lam doi chung am (QD-3 cua prereg).
DEAD_CELL = "cbr@0.700"


def rms(z: float, tau: float, A: float, c: float, em: float) -> float:
    """Luat AR(1) cua 22.6. z va tau cung don vi giay."""
    return math.sqrt(em * em + c * A * A * (1.0 - math.exp(-float(z) / float(tau))))


def tau_knee(z: float, A: float, c: float, em: float,
             tol: float = KNEE_TOL, hi: float = 1e4) -> float:
    """tau nho nhat sao cho rms(z,tau) <= (1+tol)*em.

    Giai tich: 1 - exp(-z/tau) <= ((1+tol)^2 - 1) * em^2 / (c*A^2)
    Tra ve inf khi ve phai >= 1 (khong tau nao du lon trong mo hinh nay
    -- nhung voi tol duong va c*A^2 > 0 thi luon co nghiem huu han).
    """
    rhs = (((1.0 + tol) ** 2) - 1.0) * em * em / (c * A * A)
    if rhs >= 1.0:
        return 0.0                      # da nam trong tol o moi tau
    return float(z) / (-math.log(1.0 - rhs))


def _load_cell(path: pathlib.Path) -> Dict[str, Any]:
    d = json.loads(path.read_text())
    rows = d["rows"]
    fits = [r["ar1_fit"] for r in rows]
    # A, c, em doc lap voi tau (gate G22_11 / S3). Lay trung binh tren luoi tau.
    A = sum(f["A"] for f in fits) / len(fits)
    c = sum(f["c"] for f in fits) / len(fits)
    em = sum(f["rms_e_model"] for f in fits) / len(fits)
    # spread TRONG mot tau (across z) = SAN NHIEU cua chinh uoc luong.
    # Mot span GIUA cac tau nho hon san nay thi khong noi len dieu gi.
    within = {
        "A": [f["A_spread_pct"] for f in fits],
        "c": [f["c_spread_pct"] for f in fits],
        "em": [f["rms_em_spread_pct"] for f in fits],
    }
    return {
        "cell": d["cell"],
        "A": A, "c": c, "rms_e_model": em,
        "within_tau_spread_pct": within,
        "A_span_pct": d["summary"]["A_span_pct"],
        "c_span_pct": d["summary"]["c_span_pct"],
        "rms_em_span_pct": d["summary"]["rms_em_span_pct"],
        "z_rep": d["z_rep"],
        "tau_grid_22_6": d["tau_grid"],
        "ratio_measured_22_6": d["summary"]["ratio_measured"],
        "ratio_measured_sim_22_6": [r["ratio_measured_sim"] for r in rows],
        "span_pct": {k: d["summary"][k] for k in
                     ("A_span_pct", "c_span_pct", "rms_em_span_pct")},
        "ratio_pred_finite_22_6": d["summary"]["ratio_pred_finite"],
        "peak_ref_22_6": d["summary"].get("ratio_pred_peak_from_tau1_fit"),
        "max_rel_err_vs_measured": max(f["max_rel_err_vs_measured"] for f in fits),
        "source": str(path.relative_to(ROOT)),
        "_rows_fits": fits,
    }


def _self_check(cell: Dict[str, Any]) -> Dict[str, Any]:
    """Tai tao ratio_pred_finite cua 22.6 TU CHINH A,c,em cua tung tau.

    Day la doi chung noi: neu khong khop, script dang doc sai artifact chu
    khong phai dang phat hien dieu gi ve mang.
    """
    z0, z3 = cell["z_rep"]
    worst = 0.0
    for f, want in zip(cell["_rows_fits"], cell["ratio_pred_finite_22_6"]):
        got = (rms(z3, f["tau"], f["A"], f["c"], f["rms_e_model"])
               / rms(z0, f["tau"], f["A"], f["c"], f["rms_e_model"]))
        worst = max(worst, abs(got - want))
    return {"max_abs_diff_vs_22_6_ratio_pred": worst, "pass": worst < 1e-9}


def _branch_b(cell: Dict[str, Any]) -> Dict[str, Any]:
    A, c, em = cell["A"], cell["c"], cell["rms_e_model"]
    curves = {
        "%.2f" % z: {"%g" % t: rms(z, t, A, c, em) for t in TAU_GRID_T2}
        for z in Z_FIXED_S
    }
    monotone = all(
        all(v["%g" % TAU_GRID_T2[i]] >= v["%g" % TAU_GRID_T2[i + 1]]
            for i in range(len(TAU_GRID_T2) - 1))
        for v in curves.values()
    )
    ratios = {"%.2f" % z: rms(z, TAU_HI, A, c, em) / rms(z, TAU_LO, A, c, em)
              for z in Z_FIXED_S}
    knees = {"%.2f" % z: tau_knee(z, A, c, em) for z in Z_FIXED_S}
    return {
        "z_fixed_s": list(Z_FIXED_S),
        "tau_grid": list(TAU_GRID_T2),
        "rms_curves": curves,
        "monotone_decreasing_in_tau": monotone,
        RATIO_KEY: ratios,
        "tau_knee_s": knees,
        "knee_tol": KNEE_TOL,
    }


def _branch_a(cell: Dict[str, Any]) -> Dict[str, Any]:
    """z/tau co dinh => (1-exp(-z/tau)) hang so => rms KHONG phu thuoc tau.

    Day chinh la tautology F4, phat bieu thanh mot du doan kiem duoc.
    """
    A, c, em = cell["A"], cell["c"], cell["rms_e_model"]
    flat = {
        "%.2f" % u: {"%g" % t: rms(u * t, t, A, c, em) for t in TAU_GRID_T2}
        for u in Z_OVER_TAU
    }
    spans = {}
    for u, curve in flat.items():
        vals = list(curve.values())
        spans[u] = (max(vals) - min(vals)) / min(vals) if min(vals) else float("nan")
    return {
        "z_over_tau": list(Z_OVER_TAU),
        "rms_curves": flat,
        "relative_span_across_tau": spans,
        "note": ("Voi A,c,em co dinh, rms o z/tau co dinh la HANG SO theo tau "
                 "(span = 0 dung bang so). Bien thien do duoc o T2.6 chi den tu "
                 "troi cua A,c,em -- do la thuoc do cua troi do, khong phai "
                 "mot hieu ung cua tau."),
    }


def _hump(cell: Dict[str, Any]) -> Dict[str, Any]:
    """Dinh cua R(tau) = rms(z3,tau)/rms(z0,tau) voi z0,z3 CO DINH."""
    A, c, em = cell["A"], cell["c"], cell["rms_e_model"]
    z0, z3 = cell["z_rep"]
    lo, hi, n = 0.05, 30.0, 6000
    best_t, best_r = float("nan"), -1.0
    for i in range(n + 1):
        t = lo + (hi - lo) * i / n
        r = rms(z3, t, A, c, em) / rms(z0, t, A, c, em)
        if r > best_r:
            best_r, best_t = r, t
    out = {"peak_tau_s": best_t, "peak_ratio": best_r,
           "z0": z0, "z3": z3,
           "measured_22_6_ratio": cell["ratio_measured_22_6"],
           "tau_grid_22_6": cell["tau_grid_22_6"]}
    # Doi chung cheo: 22.6 tu ghi mot dinh, tinh tu fit RIENG tai tau=1.0.
    # O day dung A,c,em TRUNG BINH tren luoi tau, nen hai so KHONG bang nhau
    # dung bang bit -- do la khac biet ve CO SO, khong phai sai so. Ghi ca hai
    # va do lech, de nguoi doc thay vi sao chung khac.
    ref = cell.get("peak_ref_22_6")
    if ref:
        out["peak_22_6_from_tau1_fit"] = ref
        out["peak_tau_abs_diff"] = abs(best_t - float(ref["tau"]))
        out["peak_basis_note"] = ("22.6 dung fit tai tau=1.0; day dung trung "
                                  "binh tren luoi tau. Khac CO SO, khong phai "
                                  "sai so.")
    return out


def _span_driver(live: Dict[str, Any]) -> Dict[str, Any]:
    """O nao / dai luong nao tao ra span lon nhat -- de no khong mo coi."""
    best = {"cell": None, "quantity": None, "span_pct": -1.0}
    for name, v in live.items():
        for q in ("A_span_pct", "c_span_pct", "rms_em_span_pct"):
            if v["fit"][q] > best["span_pct"]:
                best = {"cell": name, "quantity": q, "span_pct": v["fit"][q]}
    return best


def independence_criterion(cell: Dict[str, Any]) -> Dict[str, Any]:
    """D-T2.6-4 dang MOI: khong thu nguyen, tu hieu chuan, khong can ky so.

        span_GIUA_tau(X)  <  spread_TRONG_tau(X)      X in {A, c, em}

    Doc bang loi: "su phu thuoc vao tau nho hon nhieu uoc luong o tau co
    dinh" -- do CHINH LA nghia van hanh cua 'doc lap voi tau'.

    Vi sao khong dung bang "+/-3%": do la mot HANG SO TRAN, va no vi pham
    TRAN cua cua so kha thi. Do duoc o poisson@0.925:
        span giua-tau  = 0.762%   <- |effect|, tuc TRAN
        3*se           = 0.899%   <- SAN  (sd ~ spread/2.33, n=5)
        bang de xuat   = 3.000%   <- rong gap 4 lan TRAN
    => cua so [0.899%, 0.762%) RONG. Bang 3% khong the sai; siet lai cung
       khong cuu duoc. Mot du doan khong the sai la trang tri, khong phai
       du doan.

    Dang moi thi vi pham duoc: 3/9 FAIL tren du lieu 22.6 da co.
    """
    import statistics
    out: Dict[str, Any] = {}
    span_key = {"A": "A_span_pct", "c": "c_span_pct", "em": "rms_em_span_pct"}
    for X in ("A", "c", "em"):
        w = cell["within_tau_spread_pct"][X]
        span = float(cell["span_pct"][span_key[X]])
        mean_w = float(statistics.fmean(w))
        out[X] = {
            "span_between_tau_pct": span,
            "spread_within_tau_pct_mean": mean_w,
            "spread_within_tau_pct_max": float(max(w)),
            "ratio_span_over_spread": span / mean_w if mean_w else None,
            "passes": bool(span < mean_w),
        }
    return out


def power_scope_hump(cell: Dict[str, Any]) -> Dict[str, Any]:
    """D-T2.6-3: pham vi DOC DUOC, khai TRUOC khi chay.

    San nhieu = lech giua HAI uoc luong doc lap cua cung mot ti so
    (`ratio_measured` vs `ratio_measured_sim`). Neu bien do buou khong
    lon hon san do vai lan, vi tri dinh khong doc duoc -- va phai khai
    dieu do TRUOC, khong phai sau khi thay mot o khong khop.
    """
    import statistics
    rm = cell["ratio_measured_22_6"]
    sim = cell["ratio_measured_sim_22_6"]
    diff = statistics.fmean(abs(a - b) for a, b in zip(rm, sim))
    amp = max(rm) - min(rm)
    ratio = amp / diff if diff else None
    scope = ("READABLE" if ratio and ratio >= 5.0
             else "WEAK" if ratio and ratio >= 2.0 else "INSUFFICIENT_POWER")
    return {"mean_abs_diff_two_estimators": diff, "hump_amplitude": amp,
            "amplitude_over_noise": ratio, "declared_scope": scope}


def provenance() -> Dict[str, Any]:
    srcs = sorted(SRC.glob("tau_sweep_*.json"))
    def _git(*a: str) -> str:
        try:
            return subprocess.check_output(["git", *a], text=True, cwd=ROOT).strip()
        except Exception:
            return "unknown"
    return {
        "script": "tools/t2_1_prediction.py",
        "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
        "inputs": {str(p.relative_to(ROOT)):
                   hashlib.sha256(p.read_bytes()).hexdigest() for p in srcs},
        "derivation": ("A, c, em = trung binh tren luoi tau cua 22.6 (chung doc "
                       "lap voi tau, gate G22_11/S3). KHONG fit lai. "
                       "Luat: rms = sqrt(em^2 + c*A^2*(1-exp(-z/tau)))."),
        "estimand": ("quy uoc HIEU (1-exp(-z/tau)), khop e_stale cua "
                     "measurements/decision_error_v2.py:402. Xem docs/GLOSSARY.md."),
        "predicts": ("rms_total. KHONG du doan err_total (ti le quyet dinh sai): "
                     "luat khong mo hinh hoa phep bien doi rms -> ti le loi."),
        "z_ops_source": ("measurements/decision_error.py:37 "
                         "DEFAULT_SYNC_PERIOD_S = 0.5"),
    }


def build() -> Dict[str, Any]:
    cells: Dict[str, Any] = {}
    for p in sorted(SRC.glob("tau_sweep_*.json")):
        c = _load_cell(p)
        name = c["cell"]
        entry = {
            "source": c["source"],
            "fit": {"A": c["A"], "c": c["c"], "rms_e_model": c["rms_e_model"],
                    "A_span_pct": c["A_span_pct"], "c_span_pct": c["c_span_pct"],
                    "rms_em_span_pct": c["rms_em_span_pct"],
                    "law_max_rel_err_vs_measured": c["max_rel_err_vs_measured"]},
            "self_check": _self_check(c),
            "branch_B_operational": _branch_b(c),
            "branch_A_mechanism": _branch_a(c),
            "hump": _hump(c),
            "tau_independence": independence_criterion(c),
            "hump_power_scope": power_scope_hump(c),
            "role": "negative_control" if name == DEAD_CELL else "live",
        }
        cells[name] = entry

    live = {k: v for k, v in cells.items() if v["role"] == "live"}
    max_span = max(max(v["fit"]["A_span_pct"], v["fit"]["c_span_pct"],
                       v["fit"]["rms_em_span_pct"]) for v in live.values())
    ratios = [r for v in live.values()
              for r in v["branch_B_operational"][RATIO_KEY].values()]
    knees = [k for v in live.values()
             for k in v["branch_B_operational"]["tau_knee_s"].values()]
    return {
        "provenance": provenance(),
        "cells": cells,
        "signed_predictions": {
            "D-T2.6-1": {
                "claim": "nhanh B don dieu GIAM theo tau o moi o song, moi z",
                "basis": "giai tich: z co dinh, tau tang => (1-exp(-z/tau)) giam",
                "holds_in_model": all(v["branch_B_operational"]
                                      ["monotone_decreasing_in_tau"]
                                      for v in live.values()),
            },
            "D-T2.6-2": {
                "claim": "rms(tau=28)/rms(tau=0.5) o z co dinh",
                "point_range": [min(ratios), max(ratios)],
                "per_cell": {k: v["branch_B_operational"][RATIO_KEY]
                             for k, v in live.items()},
                "note": "BANG CHAP NHAN phai KY o prereg, khong doc tu day",
            },
            "D-T2.6-3": {
                "claim": "R(tau) co dinh (hump); vi tri dinh du doan",
                "power_scope_declared_before_run": {
                    k: v["hump_power_scope"] for k, v in live.items()},
                "per_cell": {k: v["hump"]["peak_tau_s"] for k, v in live.items()},
                "peak_range_s": [min(v["hump"]["peak_tau_s"] for v in live.values()),
                                 max(v["hump"]["peak_tau_s"] for v in live.values())],
                "cross_check_vs_22_6_max_abs_diff_s": max(
                    v["hump"].get("peak_tau_abs_diff", 0.0) for v in live.values()),
            },
            "D-T2.6-4": {
                "claim": ("span GIUA-tau cua X nho hon spread TRONG-tau cua X, "
                          "voi X in {A, c, em}"),
                "form": "khong thu nguyen, tu hieu chuan; KHONG can ky nguong",
                "why_not_a_percentage_band": (
                    "Bang '+/-3%' vi pham TRAN cua cua so kha thi: span giua-tau "
                    "do duoc chi 0.12-0.83%, nen bang 3% rong gap 4 lan hieu ung "
                    "va du doan KHONG THE SAI. Siet lai cung khong cuu: 3*se ~ "
                    "0.899% > span 0.762% => cua so RONG."),
                "per_cell": {k: v["tau_independence"] for k, v in live.items()},
                "n_fail_on_22_6": sum(
                    1 for v in live.values()
                    for q in v["tau_independence"].values() if not q["passes"]),
                "n_checks": 3 * len(live),
                "max_span_pct_measured_at_22_6": max_span,
                "driver": _span_driver(live),
                "note": ("Span lon nhat den tu `rms_em` cua poisson@0.850 -- "
                         "chinh o ma gate `rms_em_independent_of_tau` cua 22.6 "
                         "DA FAIL (T2.0 muc F3, prereg muc R4). Khong phai mot "
                         "con so la: no la bat thuong DA BIET, do lai tu huong "
                         "khac. Bang chap nhan phai ky co tinh den no, hoac "
                         "loai rieng dai luong nay o o nay kem ly do."),
            },
            "D-T2.6-6": {
                "claim": "tau_knee: tau nho nhat de rms ve trong %g%% cua em"
                         % (100 * KNEE_TOL),
                "range_s": [min(knees), max(knees)],
                "per_cell": {k: v["branch_B_operational"]["tau_knee_s"]
                             for k, v in live.items()},
            },
            "D-T2.6-7": {
                "claim": "cbr chet o moi tau (doi chung am)",
                "A_measured": cells[DEAD_CELL]["fit"]["A"] if DEAD_CELL in cells else None,
            },
        },
    }


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(OUT.relative_to(ROOT)))
    ap.add_argument("--print", action="store_true", help="in tom tat ra man hinh")
    a = ap.parse_args(argv)

    doc = build()
    bad = [k for k, v in doc["cells"].items() if not v["self_check"]["pass"]]
    if bad:
        print("DOI CHUNG NOI FAIL o: %s -- dang doc sai artifact, KHONG ghi." % bad)
        return 1

    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    print("-> %s" % out.relative_to(ROOT))
    print("   sha256 %s" % hashlib.sha256(out.read_bytes()).hexdigest())

    if a.print:
        for name, c in doc["cells"].items():
            b = c["branch_B_operational"]
            print("\n[%s]  %s" % (name, c["role"]))
            print("   A=%.4g c=%.4g em=%.4g  luat sai lech <= %.2f%%"
                  % (c["fit"]["A"], c["fit"]["c"], c["fit"]["rms_e_model"],
                     100 * c["fit"]["law_max_rel_err_vs_measured"]))
            print("   don dieu giam: %s   dinh R(tau) o tau=%.3f s"
                  % (b["monotone_decreasing_in_tau"], c["hump"]["peak_tau_s"]))
            print("   rms(28)/rms(0.5): %s"
                  % {k: round(v, 4) for k, v in
                     b[RATIO_KEY].items()})
            print("   tau_knee_s      : %s"
                  % {k: round(v, 2) for k, v in b["tau_knee_s"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
