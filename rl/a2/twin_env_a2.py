#!/usr/bin/env python3
"""A2 — TwinEnv allocation-centric. Ghep allocation + state + reward + demand.

Bai toan: agent phan bo bandwidth (budget cung C_total) giua 2 branch de
phuc vu demand. Action tuong doi (shift). State demand-centric. Reward fairness.

Luong step: apply action -> set bw Mininet -> cho Delta -> doc goodput ->
reward -> state -> truncate at horizon.
"""

import time
import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:
    class _Env:
        def reset(self, seed=None, options=None):
            return None

    class _Discrete:
        def __init__(self, n):
            self.n = int(n)

    class _Box:
        def __init__(self, low, high, shape, dtype):
            self.low = low
            self.high = high
            self.shape = shape
            self.dtype = dtype

    class _Spaces:
        Discrete = _Discrete
        Box = _Box

    class _Gym:
        Env = _Env

    gym = _Gym()
    spaces = _Spaces()

from mininet.topology_meta import canonical
from mininet.traffic import (
    IPERF_PORT,
    run_host_shell,
    start_iperf_server,
    stop_all_iperf,
)
from rl.a2.allocation import AllocationSpace
from rl.a2.demand_dynamic import DynamicDemand
from rl.a2.state_a2 import build_a2_state, A2_STATE_DIM
from rl.a2.reward_a2 import compute_reward_a2, RewardA2Config
from rl.a2.demand_scenario import make_demand_scenario, make_dynamic_scenario


BRANCH_A_LINK = 's1-s2'   # duong toi srv1
BRANCH_B_LINK = 's1-s3'   # duong toi srv2


class TwinEnvA2(gym.Env):
    def __init__(self, runner, cfg=None):
        super().__init__()
        self.runner = runner
        self.net = runner.net
        cfg = cfg or {}
        self.c_total = cfg.get('c_total', 20.0)
        self.delta_s = cfg.get('delta_s', 1.8)
        self.t_max = cfg.get('t_max_steps', 8)
        self.flow_duration = int(cfg.get('flow_duration', 120))
        self.dynamic = bool(cfg.get('dynamic', False))
        self._default_dynamic = self.dynamic
        self.scenario_name = cfg.get('scenario_name')
        self.base_mbps = float(cfg.get('base_mbps', 3.0))
        self.burst_mbps = cfg.get('burst_mbps', None)
        if self.burst_mbps is not None:
            self.burst_mbps = float(self.burst_mbps)

        self.alloc = AllocationSpace(c_total=self.c_total, n_levels=5)
        self.reward_cfg = RewardA2Config(**cfg.get('reward', {}))
        self.dd = None
        if self.dynamic:
            self._ensure_dynamic_demand()

        self.action_space = spaces.Discrete(self.alloc.n_actions)  # 3
        self.observation_space = spaces.Box(low=0.0, high=1.0,
                                            shape=(A2_STATE_DIM,), dtype=np.float32)

        self._scenario = None
        self._cur_demand = (0.0, 0.0)
        self._t = 0
        self._last_action = 0

    def _ensure_dynamic_demand(self):
        if self.dd is None:
            self.dd = DynamicDemand(
                self.net,
                base_mbps=self.base_mbps,
                flow_duration=self.flow_duration,
            )

    # ---------- Mininet helpers ----------
    def _find_link(self, key):
        target = str(key)
        if target.startswith('link-'):
            target = target[len('link-'):]
        for link in self.net.links:
            if canonical(link.intf1.node.name, link.intf2.node.name) == target:
                return link
        return None

    def _set_branch_bw(self, key, bw):
        link = self._find_link(key)
        if link is None:
            raise ValueError('link not found: %s' % key)
        cfg = {'bw': float(bw)}
        delay = getattr(link, 'dt4n_delay', None)
        if delay:
            cfg['delay'] = delay
        with self.runner.net_lock:
            link.intf1.config(**cfg)
            link.intf2.config(**cfg)
            link.dt4n_bw = float(bw)

    def _apply_allocation(self, cA, cB):
        self._set_branch_bw(BRANCH_A_LINK, cA)
        self._set_branch_bw(BRANCH_B_LINK, cB)

    def _start_demand_traffic(self, dA, dB):
        """Dat demand = chay iperf @dA, @dB (UDP). demand la thu TA BIET."""
        h1, h2 = self.net.get('h1'), self.net.get('h2')
        srv1, srv2 = self.net.get('srv1'), self.net.get('srv2')
        try:
            stop_all_iperf(*self.net.hosts)
        except Exception:
            pass
        start_iperf_server(srv1, udp=True)
        start_iperf_server(srv2, udp=True)
        time.sleep(1)
        run_host_shell(
            h1,
            'iperf -c %s -u -b %sM -p %d -t %d > /tmp/a2_a.log 2>&1 &'
            % (srv1.IP(), dA, IPERF_PORT, self.flow_duration),
        )
        run_host_shell(
            h2,
            'iperf -c %s -u -b %sM -p %d -t %d > /tmp/a2_b.log 2>&1 &'
            % (srv2.IP(), dB, IPERF_PORT, self.flow_duration),
        )

    def _read_goodput(self):
        snap = self.net.dt4n_collector.collect_all()
        things = snap.get('things', {})
        gA = (things.get('host-srv1', {}).get('features', {})
              .get('traffic', {}).get('rxRate', 0.0) or 0.0)
        gB = (things.get('host-srv2', {}).get('features', {})
              .get('traffic', {}).get('rxRate', 0.0) or 0.0)
        return float(gA) * 8.0 / 1e6, float(gB) * 8.0 / 1e6

    def _scenario_demand_at(self, t):
        if hasattr(self._scenario, 'demand_at'):
            return self._scenario.demand_at(t)
        return self._scenario.demand_A, self._scenario.demand_B

    def _sync_dynamic_demand(self, t, force=False):
        """Push the true demand for time t into the base+burst traffic layer."""
        dA, dB = self._scenario_demand_at(t)
        next_demand = (float(dA), float(dB))
        if not self.dynamic:
            self._cur_demand = next_demand
            return False

        changed = force or next_demand != self._cur_demand
        if changed:
            self.dd.set_demand('A', next_demand[0], self.burst_mbps)
            self.dd.set_demand('B', next_demand[1], self.burst_mbps)
            self._cur_demand = next_demand
        return changed

    def sync_true_demand_for_action(self):
        """Myopic-oracle hook: reveal true demand before choosing an action."""
        if self._scenario is None:
            return self._cur_demand
        self._sync_dynamic_demand(self._t)
        return self._cur_demand

    # ---------- Gym API ----------
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        s = seed if seed is not None else 0
        name = None
        if options and isinstance(options, dict):
            name = options.get('scenario')
        name = name or self.scenario_name
        if name:
            from rl.a2.scenarios.demand_scenarios import make_scenario

            self._scenario = make_scenario(
                name, s, c_total=self.c_total, t_max=self.t_max)
            self.dynamic = hasattr(self._scenario, 'demand_at')
        elif self._default_dynamic:
            self._scenario = make_dynamic_scenario(
                s, c_total=self.c_total, t_max=self.t_max)
            self.dynamic = True
        else:
            self._scenario = make_demand_scenario(s, c_total=self.c_total)
            self.dynamic = False
        if self.dynamic:
            self._ensure_dynamic_demand()
        self._t = 0
        self._last_action = 0
        # bat dau o allocation can bang
        cA, cB = self.alloc.reset()
        self._apply_allocation(cA, cB)
        dA, dB = self._scenario_demand_at(0)
        self._cur_demand = (float(dA), float(dB))
        if self.dynamic:
            self.dd.start()
            self._cur_demand = (0.0, 0.0)
            self._sync_dynamic_demand(0, force=True)
        else:
            self._start_demand_traffic(dA, dB)
        time.sleep(self.delta_s)
        obs = self._observe()
        info = {'scenario': self._scenario.describe()}
        return obs, info

    def _observe(self):
        gA, gB = self._read_goodput()
        return self._build_obs(gA, gB)

    def _build_obs(self, gA, gB):
        dA, dB = self._cur_demand
        return build_a2_state(
            alloc_level_norm=self.alloc.level_norm(),
            goodput_A=gA, goodput_B=gB,
            demand_A=dA, demand_B=dB,
            c_total=self.c_total,
            step_progress=self._t / max(self.t_max, 1),
            last_action=self._last_action,
            n_actions=self.alloc.n_actions)

    def step(self, action):
        action = int(action)
        self._last_action = action
        demand_changed = self._sync_dynamic_demand(self._t)
        # 1-2. apply action -> set bw
        cA, cB = self.alloc.apply(action)
        self._apply_allocation(cA, cB)
        # 3. cho Delta
        time.sleep(self.delta_s)
        # 4. doc goodput
        gA, gB = self._read_goodput()
        # 5. reward
        dA, dB = self._cur_demand
        bd = compute_reward_a2(gA, dA,
                               gB, dB,
                               action, self.reward_cfg)
        # 6. state
        self._t += 1
        obs = self._build_obs(gA, gB)
        satA = (
            min(gA / dA, 1.0)
            if dA > 1e-6 else 1.0
        )
        satB = (
            min(gB / dB, 1.0)
            if dB > 1e-6 else 1.0
        )

        # A2 la bai toan phan bo lien tuc, khong phai reach-goal recovery.
        # Khi tong demand > budget, co the khong ton tai trang thai "ca hai no".
        # Danh gia agent bang return tich luy; episode chi dung khi het horizon.
        terminated = False
        truncated = self._t >= self.t_max
        info = {
            'reward_breakdown': bd.__dict__, 'goodput_A': gA, 'goodput_B': gB,
            'sat_A': satA, 'sat_B': satB, 'alloc': (cA, cB),
            'total_sat': satA + satB, 'demand_A': dA, 'demand_B': dB,
            'demand_changed': demand_changed,
        }
        return obs, bd.total, terminated, truncated, info
