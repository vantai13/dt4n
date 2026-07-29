#!/usr/bin/env python3
"""Phase L / L.5 -- tests for pilot planning and gates."""

import pytest

from measurements.l5_pilot import MODES, RHO_MAIN, RHO_VAR, SEEDS_VAR, gate_point, make_plan, summarize_pilot


def _row(mode, rho, seed, q):
    return {
        "mode": mode,
        "rho_nominal": rho,
        "seed": seed,
        "q_mean_ms": q,
        "delta_pasta_ms": 0.1,
        "loss": 0.0,
        "se_batch_ms": 0.2,
        "rate_ratio": 1.0,
        "rho_actual": rho,
        "socket_drops": 0,
        "n_foreign": 0,
        "n_late_ratio": 0.0,
        "max_late_ms": 0.0,
        "gate_fail": [],
    }


def test_plan_co_42_diem_va_du_cac_o_can_do():
    plan = make_plan()
    assert len(plan) == 42
    assert set(mode for mode, _rho, _seed in plan) == set(MODES)
    for mode in MODES:
        for rho in RHO_MAIN:
            assert (mode, rho, SEEDS_VAR[0]) in plan
        for rho in RHO_VAR:
            for seed in SEEDS_VAR:
                assert (mode, rho, seed) in plan


def test_plan_duoc_xao_tron_khong_chay_tang_rho_may_moc():
    plan = make_plan()
    sorted_plan = sorted(plan, key=lambda item: (item[0], item[1], item[2]))
    assert plan != sorted_plan


def test_gate_point_bat_dung_cac_loi_van_hanh():
    good = _row("poisson", 0.9, 11, 6.0)
    assert gate_point(good) == []

    bad = dict(good)
    bad.update(
        {
            "socket_drops": 1,
            "n_foreign": 2,
            "rate_ratio": 1.002,
            "rho_actual": 0.905,
            "n_late_ratio": 0.002,
            "max_late_ms": 60.0,
        }
    )
    errs = gate_point(bad)
    assert any("socket_drops" in err for err in errs)
    assert any("foreign" in err for err in errs)
    assert any("rate_ratio" in err for err in errs)
    assert any("rho" in err for err in errs)
    assert any("n_late" in err for err in errs)
    assert any("max_late" in err for err in errs)


def test_summarize_pilot_tinh_duoc_cac_gate_chinh():
    rows = []
    for mode, base in (("cbr", 0.15), ("poisson", 1.0), ("h2", 2.0)):
        for rho in RHO_MAIN:
            q = base + 10.0 * rho
            rows.append(_row(mode, rho, SEEDS_VAR[0], q))
        for rho in RHO_VAR:
            for seed in SEEDS_VAR[1:]:
                rows.append(_row(mode, rho, seed, base + 10.0 * rho + 0.05 * (seed - 13)))

    summary = summarize_pilot(rows, floor=0.0)
    assert summary["prediction"]["n_total"] == 18
    assert summary["monotonic"]["pass"] is True
    assert summary["separated"]["pass"] is True
    assert summary["point_gates"]["pass"] is True
    assert summary["power"]["n_for_gap_4p72_ms"] >= 2
