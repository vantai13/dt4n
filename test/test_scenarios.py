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
from rl.injection import InjectionChannel  # noqa: E402
from rl.oracle_policy import oracle_action, oracle_feasible  # noqa: E402
from rl.scenarios import (  # noqa: E402
    FLOOD_PORT,
    LinkDegrade,
    TrafficFlood,
    _LocalRng,
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
    def __init__(self, name, ip='10.0.0.1'):
        self.name = name
        self._ip = ip
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


def test_make_scenario_is_deterministic_for_same_seed():
    spec = _spec()
    a = make_scenario(42, spec)
    b = make_scenario(42, spec)

    assert a.describe() == b.describe()


def test_link_degrade_only_uses_toggleable_links():
    spec = _spec()
    allowed = set(toggleable_links(spec))
    for seed in range(100):
        scenario = LinkDegrade.params_from_seed(_LocalRng(seed), spec)
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
    assert oracle_action(TrafficFlood('h1', 'srv1', 40)) == (
        'bw_up', 's2-s3')
    assert oracle_feasible(TrafficFlood('h1', 'srv1', 40), max_steps=10)


if __name__ == '__main__':
    tests = [
        test_link_degrade_revert_is_idempotent_and_restores_delay,
        test_traffic_flood_revert_is_idempotent_and_uses_dedicated_port,
        test_make_scenario_is_deterministic_for_same_seed,
        test_link_degrade_only_uses_toggleable_links,
        test_injection_channel_tracks_and_reverts_active_scenarios,
        test_oracle_names_recovery_action,
    ]
    for test in tests:
        test()
        print('PASS %s' % test.__name__)
    print('scenario tests passed')
