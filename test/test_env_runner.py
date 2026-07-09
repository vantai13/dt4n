#!/usr/bin/env python3
"""Small non-root tests for EnvRunner reset logic."""

from pathlib import Path
import logging
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mininet.env_runner import EnvRunner  # noqa: E402


def _runner_for_steady_test():
    return EnvRunner(
        sync_period=0.001,
        steady_cycles=3,
        steady_tol=0.05,
        steady_timeout=0.03,
        steady_min_norm=0.01,
        hard_every=0,
        mininet_log_level=None,
    )


def test_wait_steady_state_accepts_nonzero_stable_throughput():
    runner = _runner_for_steady_test()
    values = iter([0.30, 0.31, 0.305])
    runner._read_throughput_norm = lambda: next(values)

    ok, waited = runner._wait_steady_state()

    assert ok is True
    assert waited < runner.steady_timeout


def test_wait_steady_state_rejects_stable_zero_throughput():
    runner = _runner_for_steady_test()
    runner._read_throughput_norm = lambda: 0.0

    logger = logging.getLogger('env_runner')
    old_disabled = logger.disabled
    logger.disabled = True
    try:
        ok, waited = runner._wait_steady_state()
    finally:
        logger.disabled = old_disabled

    assert ok is False
    assert waited == runner.steady_timeout


def test_reset_collector_cache_clears_host_and_link_state():
    runner = _runner_for_steady_test()

    class Collector:
        def __init__(self):
            self._prev = {'h1': object()}
            self._prev_link = {'s1-s2': object()}

    class Net:
        pass

    runner.net = Net()
    runner.net.dt4n_collector = Collector()

    runner._reset_collector_cache()

    assert runner.net.dt4n_collector._prev == {}
    assert runner.net.dt4n_collector._prev_link == {}


if __name__ == '__main__':
    tests = [
        test_wait_steady_state_accepts_nonzero_stable_throughput,
        test_wait_steady_state_rejects_stable_zero_throughput,
        test_reset_collector_cache_clears_host_and_link_state,
    ]
    for test in tests:
        test()
        print('PASS %s' % test.__name__)
    print('env_runner tests passed')
