#!/usr/bin/env python3
"""Lesson 23.21 -- SLA NGOAI SINH. Dong loi cau truc S14.

Vi sao file nay ton tai
-----------------------
`measurements/sla_calib_v2.py` GIAI NGUOC nguong SLA tu chinh du lieu duoc
danh gia, qua mot vong diem bat dong:

    w_loss --(2)--> argmin cost --(3)--> phan vi p --(1)--> t_delay --> w_loss

Hau qua co hoc, kiem duoc tren artifact cu:

    w_loss == t_delay_ms * 100   o CA 10 cell kha thi (sai so < 1e-9)
    opt_viol_rate == 0.15        o CA  8 cell "gate", trong sai so bisection
                                 {0.149995, 0.150000, 0.150005}

Hai dang thuc tren KHONG mang thong tin ve mang; chung la dinh nghia viet lai.
File nay cat vong lap: nguong den tu ITU-T G.114, `w_loss` den tu ty gia
equal-budget, va ca hai deu la DAU VAO.

Uoc luong chinh -- `S_pivotal`
------------------------------
    S_trivial   = P( khong duong nao vi pham )
    S_collapsed = P( moi duong deu vi pham )
    S_pivotal   = 1 - S_trivial - S_collapsed

`S_pivotal` bat bien voi `w_loss`: no chi nhin TAP duong, khong nhin duong nao
duoc CHON. Bat bien do khong duoc bao dam bang cach KIEM gia tri ma bang cach
lam cho no khong the bi vi pham -- `regime_shares()` khong nhan `w_loss` va
khong nhan `opt`. Xem `test_regime_shares_signature_has_no_w_loss`.

Quan he voi `sla_calib_v2`
--------------------------
File nay KHONG sua `sla_calib_v2`. Hai the gioi ton tai song song, va doi
chung am `G23-159` doi hoi dung the: nap lai nguong + `w_loss` noi sinh cu vao
duong ong nay phai tai tao artifact cu BIT-EXACT.

Khoa boi: docs/phase-23/00zzo-amendment-52.md (tag amendment-52).
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, Mapping, Tuple

import numpy as np

from measurements import sla_calib_v2 as S14      # tai su dung ar1_matrix
from measurements.provenance import env_fingerprint
from twin import cost_v2 as C


# -- KHOA O AMENDMENT 23-52 muc 2 --------------------------------------------
SLA_SPECS: Dict[str, Dict[str, Any]] = {
    "S-A": {
        "t_delay_ms": 150.0, "t_loss": 0.010,
        "source": "ITU-T G.114: one-way mouth-to-ear <= 150 ms chap nhan duoc",
    },
    "S-B": {                                        # CHINH
        "t_delay_ms": 50.0, "t_loss": 0.010,
        "source": "ITU-T G.114: phan bo MOT chang trong ngan sach end-to-end",
    },
    "S-C": {
        "t_delay_ms": 20.0, "t_loss": 0.001,
        "source": "che do dieu khien chat (tele-control / cong nghiep)",
    },
}
PRIMARY_SPEC = "S-B"
W_LOSS_SWEEP: Tuple[float, ...] = (1250.0, 5000.0, 20000.0)

PIVOTAL_MIN = 0.10                  # nguong phan loai CHINH (muc 5)
VIOL_OPT_BAND = (0.01, 0.50)        # dai thu cap, doi chieu M-133/M-134

AXIS_LABEL = "exogenous_itu_g114_50ms_1pct"
LEGACY_SLA = "results/LIVE/phase-20R/sla_calibration.json"
OUT_DIR = "results/PENDING/phase-23"   # PENDING cho toi khi mot amendment duyet truc


def w_loss_equal_budget(t_delay_ms: float, t_loss: float) -> float:
    """Ty gia doi ngang ngan sach: dung het ngan sach TRE == dung het MAT GOI.

    cost = delay_ms + w_loss * loss.  Tai diem nguong hai so hang bang nhau:

        T_delay = w_loss * T_loss   =>   w_loss = T_delay / T_loss

    Day la mot lua chon CO NGUYEN TAC, khong phai mot fit. Xem amendment 23-52
    muc 2a, va muc 2b ve viec no hop nhat lai thu ma Amendment 2 da tach.
    """
    if t_loss <= 0.0:
        raise ValueError("T_loss phai duong")
    return float(t_delay_ms) / float(t_loss)


# -- UOC LUONG ---------------------------------------------------------------
def regime_shares(
    delay: np.ndarray, loss: np.ndarray, t_delay_ms: float, t_loss: float
) -> Dict[str, Any]:
    """Phan hoach ba phan cua thoi gian theo viec CHON DUONG co y nghia khong.

    `delay`, `loss`: (n, K). Ba ti le tra ve cong lai dung bang 1.

    KHONG nhan `w_loss` va KHONG nhan `opt`. Do KHONG phai thieu sot -- do
    chinh la co che lam ba ti le nay bat bien voi ham muc tieu (`G23-160`).
    Them mot trong hai tham so do vao day la lam hong lap luan cua muc 4, nen
    `test_regime_shares_signature_has_no_w_loss` chan o cap chu ky ham.
    """
    viol = (delay > float(t_delay_ms)) | (loss > float(t_loss))   # (n, K) bool
    n_viol = viol.sum(axis=1)                                     # (n,)
    k = viol.shape[1]
    s_trivial = float((n_viol == 0).mean())
    s_collapsed = float((n_viol == k).mean())
    return {
        "S_trivial": s_trivial,
        "S_collapsed": s_collapsed,
        "S_pivotal": float(1.0 - s_trivial - s_collapsed),
        "mean_paths_violating": float(n_viol.mean()),
        "_viol": viol,                       # noi bo; bi go truoc khi ghi file
    }


def classify(shares: Mapping[str, float]) -> str:
    """Phan loai che do. Nguong khoa o amendment 23-52 muc 5."""
    if float(shares["S_pivotal"]) >= PIVOTAL_MIN:
        return "LIVE"
    if float(shares["S_trivial"]) >= float(shares["S_collapsed"]):
        return "TRIVIAL"
    return "COLLAPSED"


def evaluate_cell(
    cv2: C.CostV2, mode: str, rho_bar: float, *,
    t_delay_ms: float, t_loss: float, w_loss: float,
    seed: int = S14.DEFAULT_SEED, n: int = S14.DEFAULT_N,
    dt: float = S14.DEFAULT_DT, tau: float = S14.DEFAULT_TAU,
    a: float = S14.DEFAULT_A,
) -> Dict[str, Any]:
    """Danh gia MOT cell duoi SLA CO DINH. Khong giai nguoc gi ca."""
    sigma = C.sigma_from_a_regime(mode, rho_bar, a)
    base = {
        "mode": mode, "rho_bar": float(rho_bar), "a": float(a),
        "sigma_max": float(C.sigma_max_regime(mode, rho_bar)),
        "sigma_rho": float(sigma), "tau_rho": float(tau), "dt": float(dt),
        "n": int(n), "seed": int(seed),
        # `loss_exchange` GIU nghia cu: "so chia sinh ra w_loss tu t_delay".
        # Voi equal-budget no bang T_loss -- xem amendment 23-52 muc 2b.
        "loss_exchange": float(t_loss),
        "target_viol": None,                     # khong con muc tieu de ep
        "reliable_ceiling": float(C.RELIABLE_CEILING[mode]),
        "sla_spec_source": "amendment-52",
    }
    if sigma <= 0.0:                             # GIU y het logic kha thi cu
        return {**base, "feasible": False, "in_band": False,
                "role": "pc1_excluded_by_q8" if mode == "cbr" else "excluded",
                "regime": "INFEASIBLE",
                "reason": "sigma_max_regime = 0 (het headroom den tran do tin cay)"}

    rho_mat = S14.ar1_matrix(mode, rho_bar, sigma, tau, dt, n, seed)
    delay, loss, cost = cv2.tables_batch(rho_mat, mode, w_loss)
    opt = np.argmin(cost, axis=1)
    rows = np.arange(int(n))

    sh = regime_shares(delay, loss, t_delay_ms, t_loss)
    viol = sh.pop("_viol")
    regime = classify(sh)

    d_opt, l_opt = delay[rows, opt], loss[rows, opt]
    opt_viol = float(viol[rows, opt].mean())

    srt = np.sort(cost, axis=1)
    margin = srt[:, 1] - srt[:, 0]
    n_viol = viol.sum(axis=1)
    piv = (n_viol > 0) & (n_viol < viol.shape[1])

    return {
        **base, **sh,
        "feasible": True,
        # `role` la truong DUONG ONG ("script nao chay tren cell nao") -- GIU
        # y nguyen semantics cu. Ket luan khoa hoc di vao `regime`. Amendment
        # 23-52 muc 8: gan role = regime lam eight_cell_sweep nem ValueError.
        "role": "pc1" if mode == "cbr" else "gate",
        "regime": regime,
        "t_delay_ms": float(t_delay_ms),
        "t_loss": float(t_loss),
        "w_loss": float(w_loss),
        # Phan vi cu la NGHIEM cua mot bai toan nguoc. Gio khong con bai toan
        # nguoc, nen de None la TRUNG THUC; dien mot so cho "day bang" la bia.
        "percentile": None,
        "percentile_of_t_delay": float((d_opt <= t_delay_ms).mean() * 100.0),
        "percentile_of_t_loss": float((l_opt <= t_loss).mean() * 100.0),
        "opt_viol_rate": opt_viol,
        "in_band": bool(VIOL_OPT_BAND[0] <= opt_viol <= VIOL_OPT_BAND[1]),
        "clip_fraction": S14._clip_fraction(rho_mat, mode),
        "cost_margin_mean_ms": float(margin.mean()),
        "cost_margin_p10_ms": float(np.percentile(margin, 10)),
        # M-138: bien CHI tren nhung buoc ma viec chon duong QUYET DINH SLA.
        # Chu y (bay 1): cost co don vi phu thuoc w_loss, nen chi duoc so
        # GIUA CAC CELL o CUNG mot w_loss, va bang TI SO chu khong bang HIEU.
        "cost_margin_pivotal_mean_ms":
            float(margin[piv].mean()) if bool(piv.any()) else None,
        "pivotal_steps": int(piv.sum()),
        "opt_path_share": S14._opt_path_share(opt),
        "fixpoint_rounds": 0,                    # khong con vong lap -- day la DIEM
        "fixpoint_converged": True,
    }


def run_spec(spec_id: str, w_loss: float | None = None, **kw) -> Dict[str, Any]:
    """Chay toan bo luoi cell duoi MOT spec SLA."""
    spec = SLA_SPECS[spec_id]
    w = (w_loss_equal_budget(spec["t_delay_ms"], spec["t_loss"])
         if w_loss is None else float(w_loss))
    cv2 = C.CostV2(strict_reliable=True)
    cells = [
        evaluate_cell(cv2, mode, rb, t_delay_ms=spec["t_delay_ms"],
                      t_loss=spec["t_loss"], w_loss=w, **kw)
        for mode in S14.MODE_GRID for rb in S14.RHO_BAR_GRID
    ]
    feas = [c for c in cells if c["feasible"]]
    return {
        "phase": "23.21",
        "script": "measurements.sla_exogenous",
        "sla_spec_id": spec_id,
        "sla_axis_label": (AXIS_LABEL if spec_id == PRIMARY_SPEC
                           else "exogenous_%s" % spec_id),
        "prereg": "docs/phase-23/00zzo-amendment-52.md",
        "config": {
            "t_delay_ms": spec["t_delay_ms"], "t_loss": spec["t_loss"],
            "t_delay_source": spec["source"],
            "w_loss": w, "w_loss_rule": "equal_budget: w = T_delay / T_loss",
            "pivotal_min": PIVOTAL_MIN, "viol_opt_band": list(VIOL_OPT_BAND),
            "mode_grid": list(S14.MODE_GRID),
            "rho_bar_grid": list(S14.RHO_BAR_GRID),
            "n": kw.get("n", S14.DEFAULT_N),
            "seed": kw.get("seed", S14.DEFAULT_SEED),
            "dt": kw.get("dt", S14.DEFAULT_DT),
            "tau": kw.get("tau", S14.DEFAULT_TAU),
            "a": kw.get("a", S14.DEFAULT_A),
            "endogenous": False,
        },
        "summary": {
            "n_design_cells": len(cells), "n_feasible": len(feas),
            "n_LIVE":      sum(1 for c in feas if c["regime"] == "LIVE"),
            "n_TRIVIAL":   sum(1 for c in feas if c["regime"] == "TRIVIAL"),
            "n_COLLAPSED": sum(1 for c in feas if c["regime"] == "COLLAPSED"),
        },
        "provenance": env_fingerprint(),
        "cells": cells,
    }


def run_w_loss_sensitivity(spec_id: str = PRIMARY_SPEC, **kw) -> Dict[str, Any]:
    """Do nhay theo `w_loss`, GIU nguong SLA co dinh.

    Dong thoi la doi chung `G23-160`: `S_pivotal` phai BAT BIEN qua ca ba
    `w_loss`. Neu khong, lap luan "phan hoach doc lap ham muc tieu" SAI.
    """
    out: Dict[str, Any] = {}
    piv: Dict[str, Dict[str, float]] = {}
    for w in W_LOSS_SWEEP:
        art = run_spec(spec_id, w_loss=w, **kw)
        key = "w=%g" % w
        out[key] = {
            "%s@%.3f" % (c["mode"], c["rho_bar"]): {
                "regime": c["regime"], "S_pivotal": c.get("S_pivotal"),
                "opt_viol_rate": c.get("opt_viol_rate"),
                "opt_path_share": c.get("opt_path_share"),
                "cost_margin_mean_ms": c.get("cost_margin_mean_ms"),
            } for c in art["cells"] if c["feasible"]
        }
        piv[key] = {k: v["S_pivotal"] for k, v in out[key].items()}
    ref = "w=%g" % W_LOSS_SWEEP[0]
    keys = sorted(piv[ref])
    max_dev = max(abs(piv["w=%g" % w][k] - piv[ref][k])
                  for w in W_LOSS_SWEEP for k in keys)
    return {
        "phase": "23.21", "script": "measurements.sla_exogenous --sensitivity",
        "sla_spec_id": spec_id, "w_loss_sweep": list(W_LOSS_SWEEP),
        "prereg": "docs/phase-23/00zzo-amendment-52.md",
        "G23_160_S_pivotal_max_dev": float(max_dev),
        "G23_160_pass": bool(max_dev == 0.0),
        "provenance": env_fingerprint(), "by_w_loss": out,
    }


# -- DOI CHUNG ---------------------------------------------------------------
def selftest(n: int = S14.DEFAULT_N) -> Dict[str, Any]:
    """Doi chung chay TRUOC moi ket qua. Khong ghi file, khong lo ket qua.

    NC-1  (G23-159) SLA + w_loss NOI SINH cu -> tai tao artifact cu bit-exact
          (LUON chay o `n`/`seed` cua artifact cu, bat ke tham so `n`)
    NC-2  ba ti le cong dung bang 1
    NC-3  (G23-160) S_pivotal bat bien qua w_loss
    PC-1  SLA bat kha thi (0 ms, 0%)   -> S_collapsed == 1
    PC-2  SLA de vo han (inf, 100%)    -> S_trivial   == 1
    """
    with open(LEGACY_SLA, "r", encoding="utf-8") as fh:
        legacy = {(c["mode"], float(c["rho_bar"])): c
                  for c in json.load(fh)["cells"] if c.get("feasible")}
    cv2 = C.CostV2(strict_reliable=True)
    res: Dict[str, Any] = {"NC1": [], "NC2": [], "NC3": [], "PC1": [], "PC2": []}

    for (mode, rb), old in sorted(legacy.items()):
        # `n` phai lay tu artifact CU, khong tu tham so CLI. NC-1 la doi chung
        # BIT-EXACT: doi `n` la doi so mau, va no se "do" vi mot ly do KHAC
        # han cai no dinh bat -- mot phep kiem do sai ly do con te hon mot
        # phep kiem khong do.
        cell = evaluate_cell(cv2, mode, rb,
                             t_delay_ms=old["t_delay_ms"], t_loss=old["t_loss"],
                             w_loss=old["w_loss"], n=int(old["n"]),
                             seed=int(old["seed"]))
        res["NC1"].append({
            "cell": "%s@%.3f" % (mode, rb),
            "d_opt_viol": abs(cell["opt_viol_rate"] - old["opt_viol_rate"]),
            "d_margin": abs(cell["cost_margin_mean_ms"] - old["cost_margin_mean_ms"]),
            "d_share": max(abs(cell["opt_path_share"][p] - old["opt_path_share"][p])
                           for p in old["opt_path_share"]),
        })
        res["NC2"].append(abs(cell["S_trivial"] + cell["S_pivotal"]
                              + cell["S_collapsed"] - 1.0))

    for mode, rb in (("poisson", 0.925), ("h2", 0.700)):
        sp = [evaluate_cell(cv2, mode, rb, t_delay_ms=50.0, t_loss=0.01,
                            w_loss=w, n=n)["S_pivotal"] for w in W_LOSS_SWEEP]
        res["NC3"].append({"cell": "%s@%.3f" % (mode, rb),
                           "max_dev": max(abs(x - sp[0]) for x in sp)})
        res["PC1"].append(evaluate_cell(cv2, mode, rb, t_delay_ms=0.0, t_loss=0.0,
                                        w_loss=5000.0, n=n)["S_collapsed"])
        res["PC2"].append(evaluate_cell(cv2, mode, rb, t_delay_ms=float("inf"),
                                        t_loss=1.0, w_loss=5000.0, n=n)["S_trivial"])

    return {
        "NC1_max_d_opt_viol": max(r["d_opt_viol"] for r in res["NC1"]),
        "NC1_max_d_margin":   max(r["d_margin"]   for r in res["NC1"]),
        "NC1_max_d_share":    max(r["d_share"]    for r in res["NC1"]),
        "NC1_n_cells": len(res["NC1"]),
        "NC2_max_abs_err": max(res["NC2"]),
        "NC3_max_dev": max(r["max_dev"] for r in res["NC3"]),
        "NC3_by_cell": res["NC3"],
        "PC1_S_collapsed": res["PC1"],
        "PC2_S_trivial": res["PC2"],
    }


# -- CLI ---------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description="SLA ngoai sinh (Lesson 23.21)")
    p.add_argument("--spec", default=PRIMARY_SPEC, choices=sorted(SLA_SPECS))
    p.add_argument("--all-specs", action="store_true")
    p.add_argument("--sensitivity", action="store_true")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--n", type=int, default=S14.DEFAULT_N)
    p.add_argument("--out-dir", default=OUT_DIR)
    a = p.parse_args()

    if a.selftest:
        print(json.dumps(selftest(n=a.n), indent=2, sort_keys=True))
        return

    os.makedirs(a.out_dir, exist_ok=True)
    if a.sensitivity:
        art = run_w_loss_sensitivity(a.spec, n=a.n)
        path = os.path.join(a.out_dir, "w_loss_sensitivity.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(art, fh, indent=1, sort_keys=True)
        print("[ok] sensitivity -> %s" % path)
        return

    for s in (sorted(SLA_SPECS) if a.all_specs else [a.spec]):
        art = run_spec(s, n=a.n)
        path = os.path.join(a.out_dir, "sla_exogenous_%s.json" % s)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(art, fh, indent=1, sort_keys=True)
        print("[ok] %s  ->  %s" % (s, path))


if __name__ == "__main__":
    main()
