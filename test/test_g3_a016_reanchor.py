"""Machine-checked ledger for the G-A016 re-anchor."""
from __future__ import annotations

import numpy as np
import pytest

from measurements.rho_from_counters import (
    actual_sample_times,
    emit4_prime,
    rho_from_counters,
    sampling_grid_diagnostics,
)
from mininet.modulated_emitter import (
    EmitterState,
    deadline_phase_fraction,
    emit_window,
)
from tools import g3_emitter_dryrun as E


class _Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class _Socket:
    def __init__(self, clock):
        self.clock = clock

    def send(self, payload):
        return len(payload)


def test_historical_gates_did_not_move():
    assert E.GATE_OVERRUN_FRACTION == 0.001
    assert E.GATE_SNAPSHOT_P99_S == 0.001
    assert E.GATE_TIMING_CORRELATION == 0.10
    assert E.GATE_QUANT_PREDICTION == 0.05


def test_reduced_design_is_separate_from_historical_ledger():
    assert E.REPLICATES == 16 and E.N_WINDOWS == 300
    assert E.A016_REPLICATES == 8
    assert E.A016_N_WINDOWS == 150
    assert E.A016_PREREG_TAG == "phase-G-g3-a016-prereg"


def test_detuning_changes_deadlines_but_not_counts():
    counts = []
    first_send_times = []
    for phase in (0.0, 0.2, 0.44):
        clock = _Clock()
        state = EmitterState()
        row = emit_window(
            0, 0.0, 0.2, 594.3, _Socket(clock), b"x" * 1400, [0], 0,
            state, phase_fraction=phase, spin_threshold_s=0.0,
            clock=clock, sleeper=clock.sleep,
        )
        counts.append(row.sent_packets)
        first_send_times.append((0.5 + phase) * 0.2 / row.sent_packets)
    assert counts == [119, 119, 119]
    assert first_send_times[0] < first_send_times[1] < first_send_times[2]
    assert deadline_phase_fraction(6, 8) == pytest.approx(0.3375)


def test_phase_fraction_refuses_out_of_window_values():
    clock = _Clock()
    with pytest.raises(ValueError):
        emit_window(
            0, 0.0, 0.2, 1.0, _Socket(clock), b"x", [0], 0,
            EmitterState(), phase_fraction=0.5,
        )


def test_actual_grid_and_rho_use_observed_intervals():
    lateness = np.array([0.001, 0.003, 0.002])
    times = actual_sample_times(lateness, 0.2, epoch_s=10.0)
    assert times == pytest.approx([10.201, 10.403, 10.602])
    counters = np.array([[100.0, 302.0, 501.0]])
    result = rho_from_counters(counters, lateness, np.array([8000.0]), 0.2)
    assert result["dt_actual_s"] == pytest.approx([0.202, 0.199])
    assert np.allclose(result["rho"], [[1.0, 1.0]])
    assert np.allclose(result["rho_nominal"], [[1.01, 0.995]])


def test_counter_and_time_regressions_are_refused():
    with pytest.raises(ValueError, match="non-monotone"):
        rho_from_counters(
            np.array([[0.0, 1.0]]), np.array([0.3, 0.0]),
            np.array([1.0]), 0.2,
        )
    with pytest.raises(ValueError, match="went backwards"):
        rho_from_counters(
            np.array([[2.0, 1.0]]), np.array([0.0, 0.0]),
            np.array([1.0]), 0.2,
        )


def test_emit4_prime_reports_common_mode_and_grid_limits():
    correction = np.array([
        [0.0, 0.002, -0.002],
        [0.0, 0.002, -0.002],
    ])
    result = emit4_prime(
        {"correction_rho": correction}, np.array([0.1, 0.1])
    )
    assert result["common_mode_ratio"] == pytest.approx(0.02)
    assert result["verdict"] == "PASS"
    grid = sampling_grid_diagnostics(np.array([0.2, 0.201, 0.199]), 0.2)
    assert grid["dt_actual_mean_s"] == pytest.approx(0.2)
    assert grid["grid_jitter_max_abs"] == pytest.approx(0.005)


def test_emit3_prime_null_uses_differenced_window_count():
    null = E.simulate_emit3_prime_null(
        trials=50, replicates=3, windows=19, seed=7, batch_size=10
    )
    assert null["windows"] == 19
    assert null["gate"] == pytest.approx(E.EMIT3_SAFETY_FACTOR * null["p99"])


def test_cpu_preflight_reports_psi_and_steal_evidence():
    detail = E.cpu_preflight(E.build_ladder_cpu_maps(tuple(range(8)))["L0"])
    assert set(detail["host_pressure"]) == {
        "cpu_psi", "steal_ticks_since_boot", "steal_fraction_since_boot",
        "load1", "quiet_load_threshold", "quiet",
    }


def _analysis_run(offset: int) -> dict[str, object]:
    sent = np.asarray([
        [10 + link + ((window + offset) % 2) for window in range(8)]
        for link in range(8)
    ], dtype=int)
    cumulative = np.cumsum(sent, axis=1)
    lateness = np.asarray([
        (link + 1) * (window + 1 + offset) * 1e-6
        for link in range(8) for window in range(8)
    ]).reshape(8, 8)
    return {
        "window_sent": sent,
        "target_packets": sent + np.linspace(0.1, 0.8, 8)[None, :],
        "window_lateness_s": lateness,
        "snapshot_sent": cumulative.copy(),
        "snapshot_measured": cumulative.copy(),
        "snapshot_spans_s": np.full(8, 1e-4),
        "tick_lateness_s": np.zeros(8),
        "overrun_counts": np.zeros(8, dtype=int),
        "overrun_max_s": np.zeros(8),
        "final_sent": cumulative[:, -1],
        "final_received": cumulative[:, -1],
    }


def test_old_proxy_gates_are_diagnostics_and_new_estimand_gates_block():
    cells = []
    for name, sigma_ref, tau_s in (
        ("anchor", 0.030348837209302317, 3.0),
        ("stress", 0.020232558139534878, 30.0),
    ):
        cells.append({
            "name": name,
            "sigma_ref": sigma_ref,
            "tau_s": tau_s,
            "level": "L0",
            "a0": E.a0_from_sigma_at("uA", sigma_ref),
            "runs": [_analysis_run(0), _analysis_run(1)],
        })
    null = {
        "trials": 1, "replicates": 2, "windows": 7, "seed": 1,
        "median": 0.1, "p95": 0.2, "p99": 0.5, "gate": 1.0,
        "gate_over_p99": 2.0,
    }
    artifact = E.analyze(
        cells,
        {"L0": {"emitter_core_count": 6, "emitters_per_core": 4 / 3}},
        {"pass": False},
        emit3_prime_null=null,
        legacy_emit3_null=null,
    )
    assert {row["id"] for row in artifact["checks"]} == {
        "EMIT-1", "EMIT-3'", "EMIT-4a", "EMIT-4'"
    }
    assert {row["id"] for row in artifact["diagnostics"]} == {
        "EMIT-2", "EMIT-3", "EMIT-4b", "EMIT-4c"
    }
