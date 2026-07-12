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


def test_send_command_posts_to_ditto_controller_inbox():
    runner = _runner_for_steady_test()

    import requests
    import uuid
    from bridge.command_agent import (
        CONTROLLER_THING_ID,
        DITTO_AUTH,
        DITTO_BASE_URL,
        HTTP_TIMEOUT,
    )

    calls = []

    class Response:
        status_code = 202
        text = ''

    def fake_post(url, json=None, headers=None, auth=None, timeout=None):
        calls.append({
            'url': url,
            'json': json,
            'headers': headers,
            'auth': auth,
            'timeout': timeout,
        })
        return Response()

    old_post = requests.post
    old_uuid4 = uuid.uuid4
    requests.post = fake_post
    uuid.uuid4 = lambda: 'cid-fixed'
    try:
        result = runner.send_command({
            'subject': 'setBandwidth',
            'target': 'org.dt4n:link-s2-s3',
            'params': {'bw': 15.0},
        })
    finally:
        requests.post = old_post
        uuid.uuid4 = old_uuid4

    assert len(calls) == 1
    assert calls[0]['url'] == (
        '%s/things/%s/inbox/messages/setBandwidth?timeout=0' %
        (DITTO_BASE_URL, CONTROLLER_THING_ID)
    )
    assert calls[0]['json'] == {
        'target': 'org.dt4n:link-s2-s3',
        'clientCorrelationId': 'cid-fixed',
        'bw': 15.0,
    }
    assert calls[0]['headers']['correlation-id'] == 'cid-fixed'
    assert calls[0]['auth'] == DITTO_AUTH
    assert calls[0]['timeout'] == HTTP_TIMEOUT
    assert result['cid'] == 'cid-fixed'
    assert result['http_status'] == 202
    assert result['post_error'] is None


def test_kill_iperf_uses_global_term_then_kill_when_needed():
    runner = _runner_for_steady_test()

    class Host:
        def __init__(self):
            self.commands = []

        def cmd(self, command):
            self.commands.append(command)
            return ''

    class Net:
        def __init__(self):
            self.hosts = [Host(), Host()]

    runner.net = Net()
    runner._background_hosts = tuple(runner.net.hosts)

    import mininet.env_runner as env_runner_mod

    calls = []

    def fake_run(argv, capture_output=None, check=None):
        calls.append({
            'argv': argv,
            'capture_output': capture_output,
            'check': check,
        })
        return type('Result', (), {'stdout': b''})()

    counts = iter([2, 0])
    old_run = env_runner_mod.subprocess.run
    old_count = runner._count_iperf
    env_runner_mod.subprocess.run = fake_run
    runner._count_iperf = lambda: next(counts)
    try:
        runner._kill_iperf()
    finally:
        env_runner_mod.subprocess.run = old_run
        runner._count_iperf = old_count

    assert [call['argv'] for call in calls] == [
        ['pkill', '-f', env_runner_mod.IPERF_PROCESS_PATTERN],
        ['pkill', '-9', '-f', env_runner_mod.IPERF_PROCESS_PATTERN],
    ]
    for host in runner.net.hosts:
        assert host.commands == [
            'pkill -f iperf 2>/dev/null',
            'pkill -9 -f iperf 2>/dev/null',
        ]
    assert runner._background_hosts == ()


def test_iperf_leak_baseline_is_calibrated_from_first_episode_count():
    runner = _runner_for_steady_test()
    runner.iperf_leak_tolerance = 4

    assert runner._iperf_baseline is None
    assert runner._iperf_leaked(6) is False
    assert runner._iperf_baseline == 6
    assert runner._iperf_leaked(10) is False
    assert runner._iperf_leaked(11) is True


def test_aoi_norm_p95_uses_dynamic_things_only():
    runner = _runner_for_steady_test()
    runner.dynamic_thing_ids = {'dynamic-a', 'dynamic-b'}

    aoi_norm = runner._aoi_norm_p95({
        'dynamic-a': 1.0,
        'dynamic-b': 3.0,
        'static-switch': 100.0,
    })

    assert abs(aoi_norm - 0.58) < 1e-9


def test_wait_data_fresh_accepts_low_aoi():
    runner = _runner_for_steady_test()
    runner.dynamic_thing_ids = {'thing-a', 'thing-b'}
    runner.fresh_aoi_norm_threshold = 0.5
    runner.fresh_timeout = 0.03
    runner.observe_raw = lambda: ({}, {
        'data_fresh': 1.0,
        'aoi': {'thing-a': 0.8, 'thing-b': 1.2},
    })

    ok, waited, aoi_norm = runner._wait_data_fresh()

    assert ok is True
    assert waited < runner.fresh_timeout
    assert aoi_norm <= runner.fresh_aoi_norm_threshold


def test_wait_data_fresh_rejects_stale_aoi():
    runner = _runner_for_steady_test()
    runner.dynamic_thing_ids = {'thing-a', 'thing-b'}
    runner.fresh_aoi_norm_threshold = 0.5
    runner.fresh_timeout = 0.03
    runner.observe_raw = lambda: ({}, {
        'data_fresh': 1.0,
        'aoi': {'thing-a': 4.0, 'thing-b': 5.0},
    })

    logger = logging.getLogger('env_runner')
    old_disabled = logger.disabled
    logger.disabled = True
    try:
        ok, waited, aoi_norm = runner._wait_data_fresh()
    finally:
        logger.disabled = old_disabled

    assert ok is False
    assert waited == runner.fresh_timeout
    assert aoi_norm > runner.fresh_aoi_norm_threshold


if __name__ == '__main__':
    tests = [
        test_wait_steady_state_accepts_nonzero_stable_throughput,
        test_wait_steady_state_rejects_stable_zero_throughput,
        test_reset_collector_cache_clears_host_and_link_state,
        test_send_command_posts_to_ditto_controller_inbox,
        test_kill_iperf_uses_global_term_then_kill_when_needed,
        test_iperf_leak_baseline_is_calibrated_from_first_episode_count,
        test_aoi_norm_p95_uses_dynamic_things_only,
        test_wait_data_fresh_accepts_low_aoi,
        test_wait_data_fresh_rejects_stale_aoi,
    ]
    for test in tests:
        test()
        print('PASS %s' % test.__name__)
    print('env_runner tests passed')
