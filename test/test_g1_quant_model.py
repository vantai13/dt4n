import numpy as np

from mininet.rate_modulator import ModulatorConfig, modulate, quantize
from tools.g1_quant_model import (
    quant_var_rho_cumulative_mixed,
    quant_var_rho_independent_round,
    quant_var_rho_static,
    sigma_quant_floor_rho,
)


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
