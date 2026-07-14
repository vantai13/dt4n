#!/usr/bin/env python3
"""A2 phase 5: smooth dynamic demand via base + burst flows.

Old demand changes killed and restarted the only iperf flow, so the branch could
briefly look dead. This helper keeps a low-rate base flow alive and toggles only
an extra burst flow:

    demand = base + burst(if enabled)

Base uses the normal iperf port. Burst uses the next port, so killing burst does
not touch the base process.
"""

import shlex
import time

from mininet.traffic import IPERF_PORT, run_host_shell, stop_all_iperf


BURST_PORT = IPERF_PORT + 1


def _rate_text(mbps):
    return '%gM' % float(mbps)


class DynamicDemand:
    """Manage two-branch A2 demand with always-on base flows."""

    def __init__(self, net, base_mbps=3.0, flow_duration=3600,
                 base_port=IPERF_PORT, burst_port=BURST_PORT,
                 server_warmup_s=1.0):
        self.net = net
        self.base = float(base_mbps)
        self.flow_duration = int(flow_duration)
        self.base_port = int(base_port)
        self.burst_port = int(burst_port)
        self.server_warmup_s = float(server_warmup_s)

        self.h1, self.h2 = net.get('h1'), net.get('h2')
        self.srv1, self.srv2 = net.get('srv1'), net.get('srv2')
        self._burst_on = {'A': False, 'B': False}
        self._burst_rate = {'A': None, 'B': None}

    def start(self):
        """Start UDP servers and always-on base flows for both branches."""
        self.stop()
        for srv in (self.srv1, self.srv2):
            self._start_udp_server(srv, self.base_port, 'base')
            self._start_udp_server(srv, self.burst_port, 'burst')
        time.sleep(self.server_warmup_s)

        self._start_client(self.h1, self.srv1, self.base_port, self.base,
                           'dt4n_base_a')
        self._start_client(self.h2, self.srv2, self.base_port, self.base,
                           'dt4n_base_b')
        self._burst_on = {'A': False, 'B': False}
        self._burst_rate = {'A': None, 'B': None}

    def stop(self):
        """Stop all iperf processes owned by the A2 demand hosts."""
        try:
            stop_all_iperf(self.h1, self.h2, self.srv1, self.srv2)
        except Exception:
            pass
        self._burst_on = {'A': False, 'B': False}
        self._burst_rate = {'A': None, 'B': None}

    def set_demand(self, branch, demand_mbps, burst_mbps=None):
        """Set branch demand to base-only or base+burst.

        ``burst_mbps`` may be supplied for fixed two-level experiments. When it
        is omitted, the burst rate is derived from ``demand_mbps - base``.
        """
        demand_mbps = float(demand_mbps)
        if burst_mbps is None:
            burst_mbps = max(0.0, demand_mbps - self.base)
        need_burst = demand_mbps > self.base + 0.5
        self.set_burst(branch, need_burst, burst_mbps)

    def set_burst(self, branch, on, burst_mbps):
        """Enable or disable only the burst flow for one branch."""
        branch = self._normalize_branch(branch)
        burst_mbps = float(burst_mbps)
        host, srv = self._branch_hosts(branch)

        if on:
            if self._burst_on[branch]:
                active = self._burst_rate[branch]
                if active is not None and abs(active - burst_mbps) < 1e-9:
                    return
                self._stop_burst(branch)

            tag = 'dt4n_burst_%s' % branch.lower()
            self._start_client(host, srv, self.burst_port, burst_mbps, tag)
            self._burst_on[branch] = True
            self._burst_rate[branch] = burst_mbps
            return

        if self._burst_on[branch]:
            self._stop_burst(branch)

    def current_demand(self, branch):
        branch = self._normalize_branch(branch)
        burst = self._burst_rate[branch] if self._burst_on[branch] else 0.0
        return self.base + float(burst or 0.0)

    def snapshot(self):
        return {
            'demand_A': self.current_demand('A'),
            'demand_B': self.current_demand('B'),
            'base_mbps': self.base,
            'burst_A_on': self._burst_on['A'],
            'burst_B_on': self._burst_on['B'],
        }

    def _start_udp_server(self, host, port, tag):
        run_host_shell(
            host,
            'iperf -s -u -p %d > /tmp/%s_%s.log 2>&1 &'
            % (int(port), tag, host.name),
        )

    def _start_client(self, host, srv, port, mbps, tag):
        run_host_shell(
            host,
            'iperf -c %s -u -b %s -p %d -t %d > /tmp/%s.log 2>&1 &'
            % (srv.IP(), _rate_text(mbps), int(port),
               self.flow_duration, tag),
        )

    def _stop_burst(self, branch):
        branch = self._normalize_branch(branch)
        host, srv = self._branch_hosts(branch)
        rate = self._burst_rate[branch]
        if rate is not None:
            pattern = 'iperf -c %s -u -b %s -p %d' % (
                srv.IP(), _rate_text(rate), self.burst_port)
            run_host_shell(
                host,
                'pkill -f %s 2>/dev/null || true' % shlex.quote(pattern),
            )

        self._burst_on[branch] = False
        self._burst_rate[branch] = None

    def _branch_hosts(self, branch):
        branch = self._normalize_branch(branch)
        if branch == 'A':
            return self.h1, self.srv1
        return self.h2, self.srv2

    def _normalize_branch(self, branch):
        branch = str(branch).upper()
        if branch not in ('A', 'B'):
            raise ValueError('branch must be A or B, got %r' % branch)
        return branch
