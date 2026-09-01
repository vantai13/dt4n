import ctypes
import os

import numpy as np
import pytest

from mininet.modulated_emitter import (
    EmitterState,
    atomic_int64_array,
    emit_window,
    sleep_until,
)
from mininet.tick_sampler import parse_proc_net_dev, sample_at
from tools.g3_emitter_dryrun import (
    _correlation_max_abs,
    build_ladder_cpu_maps,
    cpu_preflight,
    mean_correlation_then_max,
    parse_cpu_map,
    simulate_emit3_null,
)


class FakeClock:
    def __init__(self, now=0.0):
        self.now = float(now)
        self.sleeps = []

    def __call__(self):
        return self.now

    def sleep(self, duration):
        self.sleeps.append(duration)
        self.now += duration


class FakeSocket:
    def __init__(self, clock, send_cost_s=0.0):
        self.clock = clock
        self.send_cost_s = send_cost_s
        self.send_times = []

    def send(self, payload):
        self.send_times.append(self.clock())
        self.clock.now += self.send_cost_s
        return len(payload)


def test_sleep_until_uses_absolute_deadline():
    clock = FakeClock(10.0)
    sleep_until(10.125, spin_threshold_s=0.0, clock=clock, sleeper=clock.sleep)
    assert clock() == pytest.approx(10.125)
    assert sum(clock.sleeps) == pytest.approx(0.125)


def test_emit_window_rounds_independently_and_never_carries_deficit():
    clock = FakeClock()
    sock = FakeSocket(clock)
    shared = [0]
    state = EmitterState()
    results = []
    for window in range(3):
        results.append(emit_window(
            window,
            0.0,
            0.2,
            12.0,
            sock,
            b"x",
            shared,
            0,
            state,
            spin_threshold_s=0.0,
            clock=clock,
            sleeper=clock.sleep,
        ))
    assert [row.sent_packets for row in results] == [2, 2, 2]
    assert state.target_cum_packets == pytest.approx(7.2)
    assert state.sent_cum_packets == 6
    assert shared[0] == 6
    assert sock.send_times == pytest.approx([0.05, 0.15, 0.25, 0.35, 0.45, 0.55])


def test_emit_window_records_socket_overrun_without_compensation():
    clock = FakeClock()
    sock = FakeSocket(clock, send_cost_s=0.11)
    state = EmitterState()
    first = emit_window(
        0, 0.0, 0.2, 10.0, sock, b"x", [0], 0, state,
        spin_threshold_s=0.0, clock=clock, sleeper=clock.sleep,
    )
    assert first.sent_packets == 2
    assert first.overrun_s > 0.0
    assert state.overrun_windows == 1
    assert state.sent_cum_packets == 2


def test_shared_counter_is_native_aligned_int64():
    values = atomic_int64_array(8)
    assert ctypes.sizeof(values._type_) == 8
    assert ctypes.addressof(values) % 8 == 0
    values[7] = 2**40
    assert values[7] == 2**40


PROC_SAMPLE = """Inter-| Receive | Transmit
 face |bytes packets errs drop fifo frame compressed multicast|bytes packets errs drop fifo colls carrier compressed
  lo: 100 2 0 0 0 0 0 0 300 4 0 0 0 0 0 0
eth0: 1000 20 0 0 0 0 0 0 3000 40 0 0 0 0 0 0
"""


def test_parse_proc_net_dev_preserves_requested_order_at_reader_layer():
    parsed = parse_proc_net_dev(PROC_SAMPLE, ["eth0", "lo"], direction="tx")
    assert parsed == {"lo": (300, 4), "eth0": (3000, 40)}
    with pytest.raises(KeyError):
        parse_proc_net_dev(PROC_SAMPLE, ["missing"])


def test_sampler_records_one_grid_and_snapshot_span():
    clock = FakeClock(1.0)

    def read_counters():
        clock.now += 0.0002
        return [11, 21]

    row = sample_at(
        7,
        1.2,
        [10.4, 20.4],
        [10, 20],
        read_counters,
        spin_threshold_s=0.0,
        clock=clock,
        sleeper=clock.sleep,
    )
    assert row.window_index == 7
    assert row.target_cumulative_packets == (10.4, 20.4)
    assert row.sent_cumulative_packets == (10, 20)
    assert row.measured_cumulative_packets == (11, 21)
    assert row.snapshot_span_s == pytest.approx(0.0002)


def test_cpu_map_allows_shared_emitters_but_isolates_sampler_roles():
    emitters, sampler, sink = parse_cpu_map("0,1,2,3,4,5,6,7,8,9")
    assert emitters == tuple(range(8))
    assert (sampler, sink) == (8, 9)
    shared, sampler, sink = parse_cpu_map("0,1,2,0,1,2,0,1,6,7")
    assert len(set(shared)) == 3
    assert (sampler, sink) == (6, 7)
    with pytest.raises(ValueError):
        parse_cpu_map("0,1,2,0,1,2,0,1,1,7")
    with pytest.raises(ValueError):
        parse_cpu_map("0,1,2")


def test_cpu_preflight_refuses_unavailable_cpu():
    allowed = sorted(os.sched_getaffinity(0))
    unavailable = max(allowed) + 1000
    candidate = (allowed[0],) * 8 + (allowed[-2], unavailable)
    detail = cpu_preflight(candidate)
    assert not detail["pass"]
    assert unavailable in detail["missing"]


def test_ladder_maps_share_emitters_but_isolate_sampler_and_sink():
    maps = build_ladder_cpu_maps(tuple(range(8)))
    assert len(set(maps["L0"][:8])) == 6
    assert len(set(maps["L1"][:8])) == 3
    assert len(set(maps["L2"][:8])) == 1
    for cpu_map in maps.values():
        detail = cpu_preflight(cpu_map)
        assert detail["pass"]
        assert cpu_map[8] not in cpu_map[:8]
        assert cpu_map[9] not in cpu_map[:8]


def test_timing_correlation_refuses_zero_variance_and_reads_offdiagonal():
    value, _matrix = _correlation_max_abs(np.zeros((8, 100)))
    assert np.isinf(value)
    rng = np.random.default_rng(1)
    values = rng.standard_normal((8, 10000))
    values[1] = 0.4 * values[0] + np.sqrt(1.0 - 0.4**2) * values[1]
    value, matrix = _correlation_max_abs(values)
    assert value == pytest.approx(0.4, abs=0.03)
    assert matrix[0][1] == pytest.approx(0.4, abs=0.03)


def test_emit3_averages_matrices_before_maximizing_pairs():
    rng = np.random.default_rng(4)
    values = rng.standard_normal((16, 8, 2000))
    pairs = list(zip(*np.triu_indices(8, 1)))
    for replicate in range(16):
        left, right = pairs[replicate]
        values[replicate, right] = (
            0.8 * values[replicate, left]
            + 0.6 * values[replicate, right]
        )
    mean_then_max, _matrix = mean_correlation_then_max(values)
    max_then_mean = np.mean([
        _correlation_max_abs(values[index])[0] for index in range(16)
    ])
    assert mean_then_max < 0.10
    assert max_then_mean > 0.75


def test_emit3_null_is_feasible_only_after_replicate_matrix_averaging():
    null = simulate_emit3_null(
        trials=300, replicates=16, windows=300, seed=9, batch_size=25
    )
    assert null["p99"] < 0.07
    assert null["gate_over_p99"] > 1.4
