#!/usr/bin/env python3
"""Launch the eight deterministic CBR channels for NC-G1-static."""
from __future__ import annotations

import json
import os
import shlex
import sys
import time
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional

from mininet.traffic import run_host_shell
from mininet.traffic_v7 import LOAD_CHANNELS, LOAD_PORTS
from twin import topology_v7 as T7


@dataclass(frozen=True)
class StaticProfile:
    cap_mbps: float
    rho_target: float
    payload_bytes: int

    @property
    def rate_pps(self) -> float:
        return self.cap_mbps * 1e6 * self.rho_target / (self.payload_bytes * 8.0)

    def n_pkt_per_window(self, dt_s: float) -> float:
        return self.rate_pps * float(dt_s)

    def sigma_quant_floor(self, dt_s: float) -> float:
        n_packets = self.n_pkt_per_window(dt_s)
        return 1.0 / (n_packets * (12.0**0.5)) if n_packets > 0 else float("inf")

    def as_dict(self) -> Dict[str, float]:
        return {
            "cap_mbps": self.cap_mbps,
            "rho_target": self.rho_target,
            "payload_bytes": self.payload_bytes,
            "rate_pps": self.rate_pps,
            "n_pkt_per_window_0p2s": self.n_pkt_per_window(0.20),
            "sigma_quant_floor_0p2s": self.sigma_quant_floor(0.20),
            "sigma_true": 0.0,
        }


def static_profile(
    link_caps: Mapping[str, float],
    rho_targets: Mapping[str, float],
    payload_bytes: int = 1400,
) -> Dict[str, StaticProfile]:
    return {
        link: StaticProfile(float(link_caps[link]), float(rho_targets[link]), int(payload_bytes))
        for link in T7.LINK_NAMES
    }


def print_static_profile(profile: Mapping[str, StaticProfile]) -> None:
    print("*** NC-G1-static profile (sigma_true = 0 by construction)")
    print("  %-4s %8s %8s %10s %12s %12s" % ("link", "C(Mbps)", "rho", "pps", "n_pkt/0.2s", "sigma_floor"))
    for link in T7.LINK_NAMES:
        cfg = profile[link]
        print(
            "  %-4s %8.3f %8.4f %10.1f %12.1f %12.6f"
            % (link, cfg.cap_mbps, cfg.rho_target, cfg.rate_pps, cfg.n_pkt_per_window(0.20), cfg.sigma_quant_floor(0.20))
        )


class StaticGenerator:
    def __init__(
        self,
        net,
        link: str,
        cfg: StaticProfile,
        duration_s: float,
        python_bin: str,
        repo_root: str,
        log_dt_s: float,
        log_dir: str,
        pace_tick_s: float,
    ) -> None:
        self.net = net
        self.link = link
        self.cfg = cfg
        self.duration_s = float(duration_s)
        self.python_bin = python_bin
        self.repo_root = repo_root
        self.log_dt_s = float(log_dt_s)
        self.log_dir = log_dir
        self.pace_tick_s = float(pace_tick_s)
        self.port = LOAD_PORTS[link]
        self.src_name, self.dst_name = LOAD_CHANNELS[link]
        self.rho_log_path = os.path.join(log_dir, "rho_offered_%s.csv" % link)
        self.run_summary_path = os.path.join(log_dir, "flow_%s_summary.json" % link)
        self.sink_summary_path = os.path.join(log_dir, "sink_%s_summary.json" % link)
        self.pid = None
        self.sink_pid = None

    def _shell_prefix(self) -> str:
        return "cd %s && export PYTHONPATH=%s:${PYTHONPATH:-}" % (
            shlex.quote(self.repo_root),
            shlex.quote(self.repo_root),
        )

    def _background(self, host, command: str, log_path: str) -> Optional[int]:
        full = "%s && %s > %s 2>&1 & echo $!" % (
            self._shell_prefix(), command, shlex.quote(log_path)
        )
        output = run_host_shell(host, full, timeout=2).strip().splitlines()
        for line in reversed(output):
            try:
                return int(line.strip())
            except ValueError:
                continue
        return None

    def start(self) -> None:
        src = self.net.get(self.src_name)
        dst = self.net.get(self.dst_name)
        os.makedirs(self.log_dir, exist_ok=True)
        sink_cmd = (
            "%s -m mininet.static_emitter sink --port %d --duration %.3f --summary-out %s"
            % (shlex.quote(self.python_bin), self.port, self.duration_s + 5.0, shlex.quote(self.sink_summary_path))
        )
        self.sink_pid = self._background(dst, sink_cmd, os.path.join(self.log_dir, "sink_%s.log" % self.link))
        time.sleep(0.05)
        run_cmd = (
            "%s -m mininet.static_emitter run --cap-mbps %.9f --rho-target %.9f "
            "--payload-bytes %d --dst-ip %s --dst-port %d --duration %.3f "
            "--log-dt %.6f --pace-tick %.6f --ledger %s --summary-out %s"
            % (
                shlex.quote(self.python_bin), self.cfg.cap_mbps, self.cfg.rho_target,
                self.cfg.payload_bytes, shlex.quote(dst.IP()), self.port, self.duration_s,
                self.log_dt_s, self.pace_tick_s, shlex.quote(self.rho_log_path),
                shlex.quote(self.run_summary_path),
            )
        )
        self.pid = self._background(src, run_cmd, os.path.join(self.log_dir, "static_%s.log" % self.link))

    def summary(self) -> Dict[str, object]:
        data: Dict[str, object] = {
            "pid": self.pid,
            "sink_pid": self.sink_pid,
            "rho_log_path": self.rho_log_path,
            "summary_path": self.run_summary_path,
        }
        try:
            with open(self.run_summary_path, encoding="utf-8") as handle:
                data.update(json.load(handle))
        except OSError:
            pass
        return data


def start_all_static(
    net,
    link_caps: Mapping[str, float],
    rho_targets: Mapping[str, float],
    duration_s: float = 300.0,
    payload_bytes: int = 1400,
    python_bin: Optional[str] = None,
    repo_root: Optional[str] = None,
    log_dt_s: float = 0.010,
    log_dir: str = "results/RAW/phase-G/g1-static/flow_logs",
    pace_tick_s: float = 0.002,
) -> Iterable[StaticGenerator]:
    profile = static_profile(link_caps, rho_targets, payload_bytes)
    print_static_profile(profile)
    generators = []
    py = python_bin or sys.executable
    root = repo_root or os.getcwd()
    for link in T7.LINK_NAMES:
        generator = StaticGenerator(
            net, link, profile[link], duration_s, py, root, log_dt_s,
            log_dir, pace_tick_s
        )
        generator.start()
        generators.append(generator)
    return generators


def stop_static_for_v7_hosts(net) -> None:
    names = sorted({name for pair in LOAD_CHANNELS.values() for name in pair})
    for name in names:
        try:
            run_host_shell(net.get(name), "pkill -f 'mininet.static_emitter' 2>/dev/null || true", timeout=1)
        except Exception:
            pass
