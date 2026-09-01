import numpy as np
import pytest

from mininet.rate_modulator import ModulatorConfig, modulate, quantize
from tools.g1_quant_model import (
    acf1_predicted_mechanism_a,
    acf_predicted_mechanism_a_lag,
    quant_var_rho_cumulative_mixed,
    quant_var_rho_independent_round,
    quant_var_rho_static,
    sigma_quant_floor_rho,
    solve_phi_nugget_corrected,
    solve_phi_multilag,
)


def test_independent_round_acf_predictor_matches_dangerous_steps():
    assert acf1_predicted_mechanism_a(0.0) == 1.0
    assert np.isclose(acf1_predicted_mechanism_a(0.229), 0.2183, atol=0.002)
    assert np.isclose(acf1_predicted_mechanism_a(0.323), 0.0775, atol=0.002)
    assert acf1_predicted_mechanism_a(1.0) < 1e-8


def test_independent_round_acf_predictor_is_nonnegative_and_monotone():
    predictions = [
        acf1_predicted_mechanism_a(step)
        for step in np.linspace(0.0, 1.5, 101)
    ]
    assert min(predictions) >= 0.0
    assert np.all(np.diff(predictions) <= 0.0)


def test_lag_predictor_generalizes_the_same_sawtooth_formula():
    sigma_packets = 1.98
    phi = np.exp(-0.2 / 30.0)
    predicted = [
        acf_predicted_mechanism_a_lag(sigma_packets, phi, lag)
        for lag in (1, 2, 3)
    ]
    assert predicted == pytest.approx([0.2180, 0.0766, 0.0276], abs=0.002)
    assert predicted[0] > predicted[1] > predicted[2] >= 0.0


@pytest.mark.parametrize(
    "sigma_packets,tau_s",
    [(4.21, 3.0), (4.21, 30.0), (2.81, 30.0), (1.98, 30.0),
     (1.98, 100.0)],
)
def test_nugget_corrected_solver_recovers_exact_persistence(
    sigma_packets, tau_s
):
    phi = np.exp(-0.2 / tau_s)
    signal_var = sigma_packets**2
    v_pack = 1.0 / 12.0
    total = signal_var + v_pack
    acfs = {}
    for lag in (2, 3):
        nugget_acf = acf_predicted_mechanism_a_lag(
            sigma_packets, phi, lag
        )
        acfs[lag] = (
            signal_var * phi**lag + v_pack * nugget_acf
        ) / total
    solved = solve_phi_nugget_corrected(
        acfs[2], acfs[3], total, v_pack, sigma_packets
    )
    assert solved == pytest.approx(phi, abs=1e-10)


def test_nugget_corrected_solver_refuses_nonphysical_input():
    assert np.isnan(solve_phi_nugget_corrected(0.0, 0.1, 1.0, 0.1, 2.0))
    assert np.isnan(solve_phi_nugget_corrected(0.2, 0.3, -1.0, 0.1, 2.0))


@pytest.mark.parametrize("sigma_packets,tau_s", [(1.98, 3.0), (1.98, 30.0),
                                                   (1.98, 100.0), (4.21, 30.0)])
def test_multilag_solver_recovers_exact_persistence(sigma_packets, tau_s):
    phi = np.exp(-0.2 / tau_s)
    signal_var = sigma_packets**2
    v_pack = 1.0 / 12.0
    total = signal_var + v_pack
    acfs = np.asarray([
        (
            signal_var * phi**lag
            + v_pack * acf_predicted_mechanism_a_lag(
                sigma_packets, phi, lag
            )
        ) / total
        for lag in range(1, 9)
    ])
    solved = solve_phi_multilag(acfs, total, v_pack, sigma_packets)
    assert solved == pytest.approx(phi, abs=1e-10)


def test_multilag_solver_refuses_nonpositive_corrected_covariance():
    acfs = np.asarray([0.5, 0.4, 0.3, 0.2, 0.1, 0.01, 0.001, 0.0001])
    assert np.isnan(solve_phi_multilag(acfs, 0.1, 1.0, 0.1))


def test_static_law_exact():
    """The cumulative CBR staircase has exact variance f*(1-f)."""
    dt = 0.2
    for n_target in (122.43, 98.7857, 99.9821):
        rate = n_target / dt
        times = np.arange(200_001) * dt
        counts = np.diff(np.floor(times * rate))
        f = n_target % 1.0
        assert abs(counts.var() - f * (1.0 - f)) < 1e-9


def test_independent_round_is_one_twelfth_and_white():
    """Guard the mechanism actually locked by the G.0 preregistration."""
    cfg = ModulatorConfig(
        cap_bps=8e6, rho_bar=0.857, sigma=0.03, tau_s=3.0, dt_s=0.2
    )
    modulation = modulate(cfg, 500_000, np.random.default_rng(20260901))
    packetized = quantize(modulation["rho_offered"], cfg)
    q = cfg.wire_bits / (cfg.cap_bps * cfg.dt_s)
    error_packets = (
        packetized["rho_measured"] - modulation["rho_offered"]
    ) / q
    centered = error_packets - error_packets.mean()
    acf1 = float(np.dot(centered[:-1], centered[1:]) / np.dot(centered, centered))
    assert abs(float(centered.var()) - 1.0 / 12.0) < 1e-3
    assert abs(acf1) < 0.01


def test_cumulative_mixed_is_one_sixth_ma1():
    """Keep the alternative carry-accumulator law separate and testable."""
    rng = np.random.default_rng(0)
    phase = rng.uniform(0.0, 1.0, 1_000_001)
    error = phase[:-1] - phase[1:]
    centered = error - error.mean()
    acf1 = float(np.dot(centered[:-1], centered[1:]) / np.dot(centered, centered))
    assert abs(float(centered.var()) - 1.0 / 6.0) < 1e-3
    assert abs(acf1 + 0.5) < 5e-3


def test_generator_analyzer_share_explicit_round_formula_and_wire_size():
    cfg = ModulatorConfig(
        cap_bps=8e6, rho_bar=0.857, sigma=0.03, tau_s=3.0, dt_s=0.2
    )
    assert cfg.wire_bytes == 1442.0
    assert np.isclose(
        cfg.sigma_quant_floor,
        sigma_quant_floor_rho(1442.0, 0.2, 8e6, mode="independent_round"),
    )
    assert not np.isclose(
        quant_var_rho_independent_round(1442.0, 0.2, 8e6),
        quant_var_rho_cumulative_mixed(1442.0, 0.2, 8e6),
    )


def test_static_rho_formula_has_wire_units():
    rate, dt, cap = 487.232142857, 0.2, 6e6
    f = (rate * dt) % 1.0
    q = 1442.0 * 8.0 / (dt * cap)
    assert quant_var_rho_static(rate, 1442.0, dt, cap) == np.float64(
        q * q * f * (1.0 - f)
    )
