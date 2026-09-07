#!/usr/bin/env python3
"""Phase T2.4 -- realizability gate: o nay CO DO DUOC khong?

Gate nay tra loi DUY NHAT mot cau: voi (mode, rho_bar, tau, dt, n, alpha),
thiet ke co du phan giai, du chieu dai va du block de mot certificate
conformal co nghia hay khong.

No KHONG tra loi "ket qua co dep khong". Do la mot gate khac.

    NT 56  power cua doi chung phai duoc chung minh TRUOC khi doc phep so
    NT 57  gate phai dat tren chinh thong ke ma phan quyet doc

Vi hai nguyen tac do, `lift_min` -- nguong dinh nghia tau* -- KHONG nam
trong ham nay. Tron mot nguong KET QUA vao mot gate TINH HOP LE se lam mot
FAIL khong quy trach nhiem duoc: khong biet o bi loai vi khong do duoc hay
vi ket qua xau. `tau_star_curve()` o duoi nhan `lift_min` rieng, va bat
buoc truyen tuong minh.

Moi tieu chi o day deu DA CHOT o T2.2 hoac suy ra tu alpha; khong tieu chi
nao duoc dat moi trong file nay. Nguon cua tung hang so ghi ngay ben canh.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Mapping, Sequence

from cert.simultaneous_score import ALPHA
from measurements.decision_error_v2 import BLOCKS_PER_TAU, block_s_for_tau
from measurements.sla_calib_v2 import (
    TAU_LOAD_MIN_CYCLES,
    TAU_MIN_DT_RATIO,
    n_for_tau,
)
from twin import cost_v2 as C

# V-T2-3, chot o T2.2. Do duoc tren toan luoi: < 0.09% moi o.
CLIP_MAX = 0.01

# G-A020 giu mien dau vao 0 <= omega <= 1 sau khi rut truc omega doc lap.
# Xem docs/phase-G/76-amendment-G-A020-omega-reduction.md muc T2.3.
OMEGA_MIN, OMEGA_MAX = 0.0, 1.0


def min_blocks(alpha: float = ALPHA) -> int:
    """MIN_BLOCKS = ceil(1/alpha) - 1. Suy tu alpha, khong dat truoc."""
    alpha = float(alpha)
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha phai trong (0,1)")
    return int(math.ceil(1.0 / alpha)) - 1


def realizability_gate(
    *,
    mode: str,
    rho_bar: float,
    tau: float,
    dt: float,
    n: int,
    alpha: float = ALPHA,
    omega: float = 0.0,
    sigma: float | None = None,
    clip_fraction: float | None = None,
) -> Dict[str, Any]:
    """Phan quyet mot o co DO DUOC khong. Chi doc, khong chay gi.

    Tra ve dict co ``verdict`` in {"REALIZABLE", "REJECTED"} va ``checks``
    liet ke tung tieu chi kem so DO DUOC, de mot FAIL luon quy duoc trach
    nhiem cho dung tieu chi.

    ``sigma`` va ``clip_fraction`` la tuy chon: neu khong truyen thi tieu
    chi tuong ung duoc ghi "not_evaluated" chu KHONG duoc coi la PASS.
    """
    tau = float(tau)
    dt = float(dt)
    n = int(n)
    t_sim = n * dt
    mb = min_blocks(alpha)
    block_s = block_s_for_tau(tau) if tau > 0 else float("nan")
    blocks_per_seed = (t_sim / block_s) if block_s > 0 else 0.0

    checks: Dict[str, Dict[str, Any]] = {}

    def add(name, ok, got, need, why):
        checks[name] = {"pass": ok, "got": got, "need": need, "why": why}

    add("tau_positive", tau > 0.0, tau, "> 0", "tau la thoi gian, phai duong")
    add("tau_resolves_dt", tau >= TAU_MIN_DT_RATIO * dt,
        tau, ">= %g*dt = %g" % (TAU_MIN_DT_RATIO, TAU_MIN_DT_RATIO * dt),
        "duoi nguong nay AR(1) khong con phan giai duoc tren luoi dt [T2.2]")
    add("run_covers_tau", t_sim >= TAU_LOAD_MIN_CYCLES * tau,
        t_sim, ">= %g*tau = %g s" % (TAU_LOAD_MIN_CYCLES, TAU_LOAD_MIN_CYCLES * tau),
        "T_sim/tau la SO CHU KY DOC LAP; duoi 50 thi uoc luong het power [T2.2]")
    add("n_meets_budget", n >= n_for_tau(tau, dt) if tau > 0 else False,
        n, ">= %d" % (n_for_tau(tau, dt) if tau > 0 else 0),
        "ngan sach mau suy tu tham so, khong dat truoc (khong co ID: xem\n         docs/NT_REGISTRY.md muc DA TU CHOI)")
    add("enough_blocks", blocks_per_seed >= mb,
        round(blocks_per_seed, 3), ">= %d" % mb,
        "conformal can >= ceil(1/alpha)-1 block MOI SEED de chia calib/test")
    add("omega_in_domain", OMEGA_MIN <= float(omega) <= OMEGA_MAX,
        float(omega), "[%g, %g]" % (OMEGA_MIN, OMEGA_MAX),
        "mien dau vao giu nguyen sau khi rut truc omega [G-A020]")

    if sigma is None:
        checks["sigma_feasible"] = {"pass": None, "got": None,
                                    "need": "> 0", "why": "not_evaluated"}
    else:
        add("sigma_feasible", float(sigma) > 0.0, float(sigma), "> 0",
            "sigma_max_regime = 0 nghia la het headroom den tran do tin cay")

    if clip_fraction is None:
        checks["censoring_ok"] = {"pass": None, "got": None,
                                  "need": "< %g" % CLIP_MAX, "why": "not_evaluated"}
    else:
        add("censoring_ok", float(clip_fraction) < CLIP_MAX,
            float(clip_fraction), "< %g" % CLIP_MAX,
            "kep AR(1) lam lech ca sigma_hat lan tau_hat [V-T2-3]")

    failed = sorted(k for k, v in checks.items() if v["pass"] is False)
    not_eval = sorted(k for k, v in checks.items() if v["pass"] is None)
    return {
        "cell": {"mode": mode, "rho_bar": float(rho_bar), "tau": tau,
                 "dt": dt, "n": n, "alpha": float(alpha), "omega": float(omega)},
        "derived": {"t_sim_s": t_sim, "block_s": block_s,
                    "blocks_per_seed": blocks_per_seed,
                    "cycles": (t_sim / tau) if tau > 0 else float("nan"),
                    "min_blocks": mb,
                    "blocks_per_tau": BLOCKS_PER_TAU},
        "checks": checks,
        "failed": failed,
        "not_evaluated": not_eval,
        "verdict": "REALIZABLE" if not failed else "REJECTED",
    }


def tau_star_from_lift(taus: Sequence[float], lifts: Sequence[float],
                       lift_min: float) -> float:
    """tau* = inf { tau : lift(tau) < lift_min }.

    ``lift_min`` KHONG co mac dinh: no la QD-2 cua prereg T2 va chua duoc ky.
    Mot mac dinh im lang o day se lang le quyet dinh ket qua chinh cua phase.

    Tra ve ``inf`` khi khong tau nao trong luoi tut duoi nguong -- doc la
    "tau* > max(luoi)", KHONG duoc mo rong luoi de di tim tau* (T2-6c).
    """
    if lift_min is None:
        raise ValueError("lift_min la THAM SO BAT BUOC (prereg T2, QD-2)")
    if len(taus) != len(lifts):
        raise ValueError("taus va lifts phai cung do dai")
    pairs = sorted(zip((float(t) for t in taus), (float(v) for v in lifts)))
    for tau, lift in pairs:
        if lift < float(lift_min):
            return tau
    return float("inf")


def tau_star_curve(taus: Sequence[float], lifts: Sequence[float],
                   lift_mins: Sequence[float]) -> Dict[str, Any]:
    """Bao cao tau* nhu MOT DUONG theo lift_min, khong phai mot diem.

    Day la hinh thuc bao cao duoc KHUYEN NGHI o QD-2: khi khong bien minh
    duoc mot lift_min duy nhat, mot duong ben hon mot diem va khong doi hoi
    mot quyet dinh khong co can cu.
    """
    curve = {float(lm): tau_star_from_lift(taus, lifts, lm)
             for lm in lift_mins}
    finite = [v for v in curve.values() if math.isfinite(v)]
    return {
        "tau_star_by_lift_min": curve,
        "all_beyond_grid": not finite,
        "tau_grid_max": max(float(t) for t in taus) if len(taus) else float("nan"),
        "note": ("tau* = inf khi khong tau nao trong luoi tut duoi nguong; "
                 "doc la 'tau* > tau_grid_max', KHONG mo rong luoi de tim."),
    }


def gate_grid(cells: Sequence[Mapping[str, Any]], **kw) -> Dict[str, Any]:
    """Chay gate tren mot danh sach o; tra ve tom tat + ly do bi loai."""
    rows = [realizability_gate(**{**kw, **dict(c)}) for c in cells]
    rejected = [r for r in rows if r["verdict"] == "REJECTED"]
    by_reason: Dict[str, int] = {}
    for r in rejected:
        for f in r["failed"]:
            by_reason[f] = by_reason.get(f, 0) + 1
    return {
        "n_cells": len(rows),
        "n_realizable": len(rows) - len(rejected),
        "n_rejected": len(rejected),
        "rejected_by_reason": dict(sorted(by_reason.items())),
        "rows": rows,
    }
