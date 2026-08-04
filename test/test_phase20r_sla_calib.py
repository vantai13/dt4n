"""Tests for Phase 20R.2 SLA calibration helpers."""

import json

import numpy as np
import pytest

from measurements import sla_calib_v2 as S
from twin import cost_v2 as C


def test_solve_percentile_returns_objective_not_fixed_p85():
    x = np.linspace(0.0, 1.0, 10_000)
    delay = np.column_stack([x, x + 1.0, x + 2.0, x + 3.0])
    loss = delay / 100.0
    opt = np.zeros(len(x), dtype=int)

    p, _td, _tl, viol = S.solve_percentile(delay, loss, opt, target=0.15)

    assert p == pytest.approx(85.0, abs=0.05)
    assert viol == pytest.approx(0.15, abs=0.001)


def test_ar1_matrix_clips_to_family_reliability_ceiling():
    sigma = C.sigma_from_a_regime("cbr", 0.70, 0.9)
    rho = S.ar1_matrix("cbr", 0.70, sigma, tau=1.0, dt=0.005, n=20_000, seed=20)

    assert float(rho.min()) >= C.RHO_MIN
    assert float(rho.max()) <= C.RELIABLE_CEILING["cbr"]


def test_cbr_high_load_is_q8_infeasible_before_calibration():
    cell = S.calibrate_cell(
        C.CostV2(strict_reliable=True),
        "cbr",
        0.925,
        seed=1,
        n=2_000,
    )

    assert cell["feasible"] is False
    assert cell["role"] == "pc1_excluded_by_q8"
    assert "sigma_max_regime = 0" in cell["reason"]


def test_loss_exchange_is_distinct_from_calibrated_t_loss():
    cell = S.calibrate_cell(
        C.CostV2(strict_reliable=True),
        "h2",
        0.70,
        seed=5,
        n=5_000,
    )

    assert cell["feasible"] is True
    assert cell["in_band"] is True
    assert cell["w_loss"] == pytest.approx(cell["t_delay_ms"] / S.LOSS_EXCHANGE)
    assert abs(cell["t_loss"] - S.LOSS_EXCHANGE) > 0.01


def test_small_report_is_bitwise_deterministic():
    a = S.run_calibration(n=2_000, seed=9)
    b = S.run_calibration(n=2_000, seed=9)

    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
