"""T2.4 -- test ghim cho realizability_gate.

Gate nay quyet dinh o nao bi loai khoi Phase T2. Neu no sai, mot o khong do
duoc se lot vao ket qua chinh, hoac mot o do duoc bi loai oan. Ca hai deu
khong phat hien duoc tu ket qua cuoi.
"""
from __future__ import annotations

import math

import pytest

from cert.realizability_gate import (
    CLIP_MAX,
    OMEGA_MAX,
    gate_grid,
    min_blocks,
    realizability_gate,
    tau_star_curve,
    tau_star_from_lift,
)
from cert.simultaneous_score import ALPHA
from measurements.sla_calib_v2 import n_for_tau

DT = 0.005
BASE = dict(mode="poisson", rho_bar=0.925, dt=DT)


def test_min_blocks_is_derived_from_alpha_not_hardcoded():
    """MIN_BLOCKS = ceil(1/alpha) - 1. Doi alpha thi no phai doi theo."""
    assert min_blocks(ALPHA) == 9
    assert min_blocks(0.10) == 9
    assert min_blocks(0.05) == 19
    assert min_blocks(0.20) == 4
    with pytest.raises(ValueError):
        min_blocks(0.0)


def test_gate_reproduces_the_t2_0_budget_table():
    """Doi chieu voi bang F5 cua T2.0: vo o tau=28 khi n khong scale."""
    expect = {0.5: True, 1.0: True, 2.0: True, 5.0: True,
              10.0: True, 20.0: True, 28.0: False}
    for tau, ok in expect.items():
        r = realizability_gate(tau=tau, n=200_000, **BASE)
        assert (r["verdict"] == "REALIZABLE") is ok, (tau, r["failed"])


def test_scaling_n_by_the_locked_rule_repairs_the_rejected_cell():
    """n_for_tau la cach DUNG de sua o bi loai vi ngan sach."""
    assert realizability_gate(tau=28.0, n=200_000, **BASE)["verdict"] == "REJECTED"
    r = realizability_gate(tau=28.0, n=n_for_tau(28.0, DT), **BASE)
    assert r["verdict"] == "REALIZABLE"
    assert r["derived"]["blocks_per_seed"] >= 10.0


def test_every_cell_on_the_signed_grid_is_realizable():
    """Luoi tau cua prereg T2-4 voi n_for_tau phai qua sach."""
    for tau in (0.5, 1, 2, 3, 5, 10, 20, 28):
        r = realizability_gate(tau=float(tau), n=n_for_tau(float(tau), DT), **BASE)
        assert r["verdict"] == "REALIZABLE", (tau, r["failed"])


def test_tau_below_resolution_is_rejected():
    """tau < 20*dt: AR(1) khong con phan giai duoc tren luoi dt."""
    r = realizability_gate(tau=0.05, n=200_000, **BASE)     # = 10*dt
    assert r["verdict"] == "REJECTED"
    assert "tau_resolves_dt" in r["failed"]
    r_ok = realizability_gate(tau=0.10, n=200_000, **BASE)  # = 20*dt
    assert "tau_resolves_dt" not in r_ok["failed"]


def test_omega_domain_is_kept_after_the_axis_was_retired():
    """G-A020 rut TRUC omega nhung GIU mien dau vao 0 <= omega <= 1."""
    assert realizability_gate(tau=1.0, n=200_000, omega=0.0, **BASE)["verdict"] == "REALIZABLE"
    assert realizability_gate(tau=1.0, n=200_000, omega=OMEGA_MAX, **BASE)["verdict"] == "REALIZABLE"
    bad = realizability_gate(tau=1.0, n=200_000, omega=1.5, **BASE)
    assert "omega_in_domain" in bad["failed"]


def test_unevaluated_criteria_are_not_silently_passed():
    """Khong truyen sigma/clip => 'not_evaluated', KHONG phai PASS.

    Day la cho de sinh loi im lang nhat: mot gate coi 'chua do' la 'dat'
    se cho qua dung nhung o chua ai kiem.
    """
    r = realizability_gate(tau=1.0, n=200_000, **BASE)
    assert r["checks"]["censoring_ok"]["pass"] is None
    assert r["checks"]["sigma_feasible"]["pass"] is None
    assert r["checks"]["mondrian_cells_populated"]["pass"] is None
    assert set(r["not_evaluated"]) == {"censoring_ok", "sigma_feasible",
                                       "mondrian_cells_populated"}


def test_mondrian_occupancy_is_enforced_when_supplied():
    """O Mondrian thieu block => q_hat=inf => coverage=1.0 theo DINH NGHIA.

    Nguong la chinh MIN_BLOCKS suy tu alpha, khong phai mot so moi.
    """
    mb = min_blocks(ALPHA)
    ok = realizability_gate(tau=1.0, n=200_000, min_cell_blocks=mb, **BASE)
    assert ok["verdict"] == "REALIZABLE"
    bad = realizability_gate(tau=1.0, n=200_000, min_cell_blocks=mb - 1, **BASE)
    assert "mondrian_cells_populated" in bad["failed"]


def test_censoring_and_sigma_are_enforced_when_supplied():
    ok = realizability_gate(tau=1.0, n=200_000, sigma=0.0218,
                            clip_fraction=0.00054, **BASE)
    assert ok["verdict"] == "REALIZABLE"
    bad = realizability_gate(tau=1.0, n=200_000, sigma=0.0,
                             clip_fraction=0.05, **BASE)
    assert set(bad["failed"]) == {"censoring_ok", "sigma_feasible"}
    assert CLIP_MAX == 0.01


def test_failures_are_attributable_per_criterion():
    """Mot FAIL phai quy duoc trach nhiem: NT 57."""
    r = realizability_gate(tau=28.0, n=200_000, **BASE)
    assert set(r["failed"]) == {"enough_blocks", "n_meets_budget", "run_covers_tau"}
    for name in r["failed"]:
        c = r["checks"][name]
        assert c["got"] is not None and c["need"] and c["why"]


# --- tau*: nguong KET QUA, tach khoi gate TINH HOP LE -------------------

def test_lift_min_has_no_default():
    """QD-2 chua ky: khong duoc co mac dinh im lang cho lift_min."""
    with pytest.raises(TypeError):
        tau_star_from_lift([1.0, 2.0], [0.5, 0.4])          # thieu lift_min
    with pytest.raises(ValueError):
        tau_star_from_lift([1.0, 2.0], [0.5, 0.4], None)


def test_tau_star_is_the_first_tau_below_the_threshold():
    taus = [1.0, 2.0, 5.0, 10.0, 20.0]
    lifts = [0.50, 0.40, 0.22, 0.08, 0.03]
    assert tau_star_from_lift(taus, lifts, 0.10) == 10.0
    assert tau_star_from_lift(taus, lifts, 0.05) == 20.0
    assert tau_star_from_lift(taus, lifts, 0.25) == 5.0


def test_tau_star_beyond_grid_is_infinite_not_extrapolated():
    """T2-6c: ghi '> max(luoi)', KHONG mo rong luoi de di tim tau*."""
    taus = [1.0, 2.0, 5.0]
    lifts = [0.50, 0.45, 0.40]
    assert math.isinf(tau_star_from_lift(taus, lifts, 0.10))
    c = tau_star_curve(taus, lifts, [0.05, 0.10, 0.20])
    assert c["all_beyond_grid"] is True
    assert c["tau_grid_max"] == 5.0


def test_tau_star_curve_reports_a_line_not_a_point():
    """QD-2 khuyen nghi: bao cao tau*(lift_min) nhu MOT DUONG."""
    taus = [1.0, 2.0, 5.0, 10.0, 20.0]
    lifts = [0.50, 0.40, 0.22, 0.08, 0.03]
    c = tau_star_curve(taus, lifts, [0.05, 0.10, 0.25])
    # lift(5)=0.22 KHONG nho hon 0.20, nen nguong 0.25 moi cho tau*=5.
    assert c["tau_star_by_lift_min"] == {0.05: 20.0, 0.10: 10.0, 0.25: 5.0}
    assert c["all_beyond_grid"] is False
    # duong phai don dieu: nguong cang chat thi tau* cang som
    vals = [c["tau_star_by_lift_min"][k] for k in sorted(c["tau_star_by_lift_min"])]
    assert vals == sorted(vals, reverse=True)


def test_gate_grid_reports_why_cells_were_rejected():
    cells = [dict(tau=t, n=200_000) for t in (1.0, 20.0, 28.0)]
    g = gate_grid(cells, **BASE)
    assert g["n_cells"] == 3 and g["n_rejected"] == 1
    assert g["rejected_by_reason"]["enough_blocks"] == 1
