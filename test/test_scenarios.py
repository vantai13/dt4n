#!/usr/bin/env python3
"""Pure tests for RL scenarios and injection channel."""

import json
from pathlib import Path
import sys
import threading


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mininet.topology_meta import toggleable_links  # noqa: E402
import mininet.traffic as traffic_mod  # noqa: E402
from rl.injection import InjectionChannel  # noqa: E402
from rl.oracle_policy import oracle_action, oracle_feasible  # noqa: E402
from rl.scenarios import (  # noqa: E402
    CongestionShift,
    FLOOD_PORT,
    LinkDegrade,
    LinkDown,
    TrafficFlood,
    make_scenario,
)


class FakeNode:
    def __init__(self, name):
        self.name = name


class FakeIntf:
    def __init__(self, node, name):
        self.node = node
        self.name = name
        self.configs = []
        self.bw = None
        self.delay = None

    def config(self, **kwargs):
        self.configs.append(dict(kwargs))
        if 'bw' in kwargs:
            self.bw = kwargs['bw']
        if 'delay' in kwargs:
            self.delay = kwargs['delay']


class FakeLink:
    def __init__(self, a, b, bw=20.0):
        self.intf1 = FakeIntf(FakeNode(a), '%s-ethX' % a)
        self.intf2 = FakeIntf(FakeNode(b), '%s-ethX' % b)
        self.dt4n_bw = bw


class FakeHost:
    def __init__(self, name, ip='10.0.0.1', pid=None):
        self.name = name
        self._ip = ip
        self.pid = pid
        self.commands = []

    def IP(self):
        return self._ip

    def cmd(self, command):
        self.commands.append(command)
        return ''


class FakeNet:
    def __init__(self):
        self.links = [FakeLink('s1', 's2')]
        self.hosts = {
            'h1': FakeHost('h1', '10.0.0.1'),
            'srv1': FakeHost('srv1', '10.0.0.4'),
        }

    def get(self, name):
        return self.hosts[name]


class CountingScenario:
    def __init__(self):
        self.applies = 0
        self.reverts = 0

    def apply(self, net):
        self.applies += 1

    def revert(self, net):
        self.reverts += 1

    def describe(self):
        return {'type': 'CountingScenario', 'applies': self.applies}


def _spec():
    return json.load(open(ROOT / 'ditto/topology_spec.json', encoding='utf-8'))


def test_link_degrade_revert_is_idempotent_and_restores_delay():
    net = FakeNet()
    scenario = LinkDegrade('s1-s2', factor=0.5, delay='2ms', baseline=20.0)

    scenario.apply(net)
    assert net.links[0].dt4n_bw == 10.0
    assert net.links[0].intf1.bw == 10.0
    assert net.links[0].intf1.delay == '2ms'

    scenario.revert(net)
    scenario.revert(net)

    assert net.links[0].dt4n_bw == 20.0
    assert net.links[0].intf1.bw == 20.0
    assert net.links[0].intf2.bw == 20.0
    assert net.links[0].intf1.delay == '2ms'


def test_traffic_flood_revert_is_idempotent_and_uses_dedicated_port():
    net = FakeNet()
    scenario = TrafficFlood('h1', 'srv1', rate_mbps=40)

    scenario.apply(net)
    scenario.revert(net)
    scenario.revert(net)

    h1_commands = '\n'.join(net.get('h1').commands)
    srv1_commands = '\n'.join(net.get('srv1').commands)
    assert str(FLOOD_PORT) in h1_commands
    assert str(FLOOD_PORT) in srv1_commands
    assert 'iperf -c 10.0.0.4 -u -b 40M' in h1_commands
    assert 'pkill -f "iperf.*%d"' % FLOOD_PORT in h1_commands


def test_link_down_is_severe_link_degrade():
    net = FakeNet()
    scenario = LinkDown('s1-s2', factor=0.98, delay='2ms', baseline=20.0)

    scenario.apply(net)
    assert net.links[0].dt4n_bw == 1.0
    assert net.links[0].intf1.bw == 1.0

    scenario.revert(net)
    scenario.revert(net)

    assert net.links[0].dt4n_bw == 20.0
    assert net.links[0].intf1.bw == 20.0


def test_congestion_shift_reverts_link_and_flood():
    net = FakeNet()
    scenario = CongestionShift(
        's1-s2', factor=0.5, delay='2ms', baseline=20.0,
        flood_src='h1', flood_dst='srv1', rate_mbps=25)

    scenario.apply(net)
    assert net.links[0].dt4n_bw == 10.0
    assert net.links[0].intf1.bw == 10.0

    scenario.revert(net)
    scenario.revert(net)

    h1_commands = '\n'.join(net.get('h1').commands)
    srv1_commands = '\n'.join(net.get('srv1').commands)
    assert net.links[0].dt4n_bw == 20.0
    assert 'iperf -c 10.0.0.4 -u -b 25M' in h1_commands
    assert 'pkill -f "iperf.*%d"' % FLOOD_PORT in h1_commands
    assert 'pkill -f "iperf.*%d"' % FLOOD_PORT in srv1_commands


def test_server_background_traffic_uses_mnexec_when_host_has_pid():
    class BgNet:
        def __init__(self):
            self.hosts = {
                'srv1': FakeHost('srv1', '10.0.0.4', pid=111),
                'srv2': FakeHost('srv2', '10.0.0.5', pid=222),
            }

        def get(self, name):
            return self.hosts[name]

    calls = []
    orig_run = traffic_mod.subprocess.run
    orig_sleep = traffic_mod.time.sleep

    def fake_run(argv, stdout=None, stderr=None, text=None, timeout=None,
                 check=None):
        calls.append({
            'argv': argv,
            'timeout': timeout,
            'text': text,
            'check': check,
        })
        return type('Result', (), {'stdout': ''})()

    traffic_mod.subprocess.run = fake_run
    traffic_mod.time.sleep = lambda _seconds: None
    try:
        net = BgNet()
        traffic_mod.start_server_to_server(net, rate_mbps=2, duration=60)
    finally:
        traffic_mod.subprocess.run = orig_run
        traffic_mod.time.sleep = orig_sleep

    assert len(calls) == 2
    assert calls[0]['argv'][:3] == ['mnexec', '-a', '222']
    assert calls[1]['argv'][:3] == ['mnexec', '-a', '111']
    assert net.get('srv1').commands == []
    assert net.get('srv2').commands == []


def test_make_scenario_is_deterministic_for_same_seed():
    spec = _spec()
    a = make_scenario(42, spec)
    b = make_scenario(42, spec)

    assert a.describe() == b.describe()


def test_scenario_golden_values():
    spec = _spec()
    got = [make_scenario(seed=s, spec=spec).describe()
           for s in (0, 1, 2, 42)]
    expected = [
        {
            'type': 'CongestionShift',
            'degrade_link': 's1-s3',
            'factor': 0.45395734275277405,
            'delay': '2ms',
            'baseline': 20.0,
            'flood_src': 'h1',
            'flood_dst': 'srv1',
            'rate_mbps': 21,
        },
        {
            'type': 'TrafficFlood',
            'src': 'h2',
            'dst': 'srv2',
            'rate_mbps': 59,
        },
        {
            'type': 'CongestionShift',
            'degrade_link': 's1-s2',
            'factor': 0.45969822868282467,
            'delay': '2ms',
            'baseline': 20.0,
            'flood_src': 'h2',
            'flood_dst': 'srv2',
            'rate_mbps': 29,
        },
        {
            'type': 'LinkDegrade',
            'link_key': 's2-s3',
            'factor': 0.3755513759008209,
            'delay': '2ms',
            'baseline': 5.0,
        },
    ]
    assert got == expected, 'Scenario RNG changed. Old results are invalid.'


def test_link_degrade_only_uses_toggleable_links():
    spec = _spec()
    allowed = set(toggleable_links(spec))
    for seed in range(100):
        scenario = make_scenario(seed, spec)
        if isinstance(scenario, LinkDegrade):
            assert scenario.link_key in allowed


def test_injection_channel_tracks_and_reverts_active_scenarios():
    net = FakeNet()
    lock = threading.RLock()
    channel = InjectionChannel(net, lock)
    scenario = CountingScenario()

    channel.apply(scenario)
    assert scenario.applies == 1
    assert channel.active()[0]['type'] == 'CountingScenario'

    channel.revert_all()
    channel.revert_all()

    assert scenario.reverts == 1
    assert channel.active() == []


def test_oracle_names_recovery_action():
    assert oracle_action(LinkDegrade('s1-s2', 0.5, '2ms', 20.0)) == (
        'bw_up', 's1-s2')
    assert oracle_action(LinkDown('s1-s2', 0.98, '2ms', 20.0)) == (
        'bw_up', 's1-s2')
    assert oracle_action(
        CongestionShift('s1-s3', 0.5, '2ms', 20.0, 'h1', 'srv1', 25)
    ) == ('bw_up', 's1-s3')
    assert oracle_action(TrafficFlood('h1', 'srv1', 40)) == (
        'bw_up', 's2-s3')
    assert oracle_feasible(TrafficFlood('h1', 'srv1', 40), max_steps=10)


if __name__ == '__main__':
    tests = [
        test_link_degrade_revert_is_idempotent_and_restores_delay,
        test_traffic_flood_revert_is_idempotent_and_uses_dedicated_port,
        test_link_down_is_severe_link_degrade,
        test_congestion_shift_reverts_link_and_flood,
        test_server_background_traffic_uses_mnexec_when_host_has_pid,
        test_make_scenario_is_deterministic_for_same_seed,
        test_scenario_golden_values,
        test_link_degrade_only_uses_toggleable_links,
        test_injection_channel_tracks_and_reverts_active_scenarios,
        test_oracle_names_recovery_action,
    ]
    for test in tests:
        test()
        print('PASS %s' % test.__name__)
    print('scenario tests passed')
