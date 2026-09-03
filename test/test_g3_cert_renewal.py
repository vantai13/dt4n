"""Unit tests for the G-A014 certificate-renewal gates.

Every gate carries a matched pair: one test proving it PASSES when the
certified mechanism is in force, and one proving it FAILS on a concrete
defect.  A gate with only a passing test is a gate that may always pass.
"""
from __future__ import annotations

import numpy as np
import pytest

from tools.g0_feasibility import HEADROOM_MIN
from tools.g1_quant_model import QUANT_VAR_PACKETS_INDEPENDENT_ROUND
from tools.g2_topology import CAP_BPS, LINKS
from tools.g3_emitter_dryrun import GATE_TIMING_CORRELATION
from tools.g3_cert_renewal import (
    GATE_C_CORRELATION,
    GATE_F_HEADROOM,
    GATE_V_REL_ERROR,
    gate_g3c_infrastructure_correlation,
    gate_g3f_headroom,
    gate_g3v_quantization_variance,
    packet_rho_quantum,
    renewal_verdict,
    sigma_quant_floor,
)

DT_S = 0.2
N_WINDOWS = 3000


def _synthetic_target(sigma_scale: float, seed: int) -> np.ndarray:
    """Targets whose per-link sigma is a chosen multiple of the packet floor."""
    rng = np.random.default_rng(seed)
    floor = sigma_quant_floor(CAP_BPS, DT_S)
    sigma = sigma_scale * floor
    return 0.857 + sigma[:, None] * rng.standard_normal((len(LINKS), N_WINDOWS))


def _independent_round(target: np.ndarray) -> np.ndarray:
    quantum = packet_rho_quantum(CAP_BPS, DT_S)
    packets = np.round(target / quantum[:, None])
    return packets * quantum[:, None]


# ------------------------------------------------------------ single source
def test_renewal_gates_reuse_the_constants_they_renew():
    """A renewal gate must not carry its own copy of the renewed constant."""
    assert GATE_F_HEADROOM == HEADROOM_MIN
    assert GATE_C_CORRELATION == GATE_TIMING_CORRELATION


def test_quantization_floor_is_the_one_twelfth_root_of_the_quantum():
    floor = sigma_quant_floor(CAP_BPS, DT_S)
    quantum = packet_rho_quantum(CAP_BPS, DT_S)
    expected = np.sqrt(QUANT_VAR_PACKETS_INDEPENDENT_ROUND) * quantum
    assert np.allclose(floor, expected, rtol=0.0, atol=1e-15)


# ------------------------------------------------------------------- G3-V
def test_g3v_passes_on_true_independent_round():
    """POSITIVE CONTROL: the certified mechanism must renew the certificate."""
    target = _synthetic_target(sigma_scale=10.0, seed=101)
    sent = _independent_round(target)
    result = gate_g3v_quantization_variance(target, sent, CAP_BPS, DT_S)
    assert result["verdict"] == "PASS"
    assert result["value"] <= GATE_V_REL_ERROR
    for row in result["per_link"]:
        assert abs(row["var_packets"] - QUANT_VAR_PACKETS_INDEPENDENT_ROUND) < 0.01


def test_g3v_fails_when_variance_is_inflated():
    """NEGATIVE CONTROL: extra scheduler noise must be caught, not absorbed."""
    target = _synthetic_target(sigma_scale=10.0, seed=102)
    sent = _independent_round(target)
    quantum = packet_rho_quantum(CAP_BPS, DT_S)
    rng = np.random.default_rng(999)
    # inject an extra half-packet of jitter: Var goes 1/12 -> 1/12 + 0.25
    sent = sent + 0.5 * quantum[:, None] * rng.standard_normal(sent.shape)
    result = gate_g3v_quantization_variance(target, sent, CAP_BPS, DT_S)
    assert result["verdict"] == "FAIL"


def test_g3v_fails_on_cumulative_mechanism():
    """A cumulative floor pacer has Var = 1/6, exactly twice the certificate."""
    target = _synthetic_target(sigma_scale=10.0, seed=103)
    quantum = packet_rho_quantum(CAP_BPS, DT_S)
    wanted = target / quantum[:, None]
    cumulative = np.floor(np.cumsum(wanted, axis=1))
    packets = np.diff(cumulative, axis=1, prepend=0.0)
    sent = packets * quantum[:, None]
    result = gate_g3v_quantization_variance(target, sent, CAP_BPS, DT_S)
    assert result["verdict"] == "FAIL"
    assert result["value"] > 0.5


def test_g3v_refuses_mismatched_ledgers():
    target = _synthetic_target(sigma_scale=10.0, seed=104)
    with pytest.raises(ValueError):
        gate_g3v_quantization_variance(target, target[:, :-1], CAP_BPS, DT_S)


# ------------------------------------------------------------------- G3-F
def test_g3f_passes_at_the_campaign_anchor():
    target = _synthetic_target(sigma_scale=10.0, seed=201)
    result = gate_g3f_headroom(target, CAP_BPS, DT_S)
    assert result["verdict"] == "PASS"
    assert result["value"] >= GATE_F_HEADROOM


def test_g3f_fails_below_the_locked_headroom():
    """Just under the boundary must FAIL; the gate is not rounded."""
    target = _synthetic_target(sigma_scale=4.5, seed=202)
    result = gate_g3f_headroom(target, CAP_BPS, DT_S)
    assert result["verdict"] == "FAIL"
    assert result["value"] < GATE_F_HEADROOM


def test_g3f_reports_every_link():
    target = _synthetic_target(sigma_scale=10.0, seed=203)
    result = gate_g3f_headroom(target, CAP_BPS, DT_S)
    assert [row["link"] for row in result["per_link"]] == list(LINKS)


# ------------------------------------------------------------------- G3-C
def _lateness(correlation: float, replicates: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(replicates):
        common = rng.standard_normal(300)
        private = rng.standard_normal((len(LINKS), 300))
        mixed = (
            np.sqrt(correlation) * common[None, :]
            + np.sqrt(1.0 - correlation) * private
        )
        out.append(np.abs(mixed))
    return out


def test_g3c_passes_on_independent_emitters():
    """NEGATIVE CONTROL: no shared CPU cause -> correlation stays under the gate."""
    result = gate_g3c_infrastructure_correlation(_lateness(0.0, 16, 301))
    assert result["verdict"] == "PASS"
    assert result["value"] <= GATE_C_CORRELATION


def test_g3c_fails_on_shared_scheduler_stalls():
    """POSITIVE CONTROL: the G-L38 failure mode must actually trip the gate."""
    result = gate_g3c_infrastructure_correlation(_lateness(0.5, 16, 302))
    assert result["verdict"] == "FAIL"
    assert result["value"] > GATE_C_CORRELATION


def test_g3c_refuses_a_constant_link():
    with pytest.raises(ValueError):
        gate_g3c_infrastructure_correlation([np.ones((len(LINKS), 300))])


def test_g3c_refuses_an_empty_campaign():
    with pytest.raises(ValueError):
        gate_g3c_infrastructure_correlation([])


def test_g3c_reduction_order_is_mean_then_max():
    """max-first would be biased upward; the gate must use mean-of-matrices."""
    replicates = _lateness(0.0, 16, 303)
    correct = gate_g3c_infrastructure_correlation(replicates)["value"]
    max_first = float(np.mean([
        np.max(np.abs(np.corrcoef(r)[np.triu_indices(len(LINKS), 1)]))
        for r in replicates
    ]))
    assert max_first > correct


# ------------------------------------------------------------- combination
def test_renewal_verdict_blocks_on_any_failure():
    checks = [
        {"id": "G3-V", "verdict": "PASS"},
        {"id": "G3-F", "verdict": "FAIL"},
        {"id": "G3-C", "verdict": "PASS"},
    ]
    verdict = renewal_verdict(checks)
    assert verdict["certificate_renewed"] is False
    assert verdict["failed_gates"] == ["G3-F"]
    assert "RECOMPUTE" in verdict["consequence"]


def test_renewal_verdict_transfers_only_when_every_gate_passes():
    checks = [
        {"id": "G3-V", "verdict": "PASS"},
        {"id": "G3-F", "verdict": "PASS"},
        {"id": "G3-C", "verdict": "PASS"},
    ]
    verdict = renewal_verdict(checks)
    assert verdict["certificate_renewed"] is True
    assert verdict["failed_gates"] == []
