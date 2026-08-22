#!/usr/bin/env python3
"""Flow-level traffic generator for the Phase 20 butterfly topology.

This replaces ``topology3.advance_levels()`` for Phase 20 measurements. The
old helper sampled rho from a table; this module creates real iperf flows:

* flow arrivals are Poisson with rate lambda,
* flow sizes are Pareto with shape kappa,
* each active flow sends at a fixed rate r_f.

The configuration is expressed in physical quantities. ``TrafficConfig`` derives
``r_f`` from target sigma and derives lambda from target rho.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
import os
import shlex
import sys
import time
from typing import Dict, Iterable, Mapping, Optional

from mininet.traffic import run_host_shell
from twin import topology_v7 as T7


LOAD_CHANNELS = {
    "uA": ("hsrc", "hA"),
    "uB": ("hsrc", "hB"),
    "ac": ("hA", "hC"),
    "ad": ("hA", "hD"),
    "bc": ("hB", "hC"),
    "bd": ("hB", "hD"),
    "vC": ("hC", "hdst"),
    "vD": ("hD", "hdst"),
}
CORE_LINKS = ("ac", "ad", "bc", "bd")
EDGE_LINKS = tuple(link for link in T7.LINK_NAMES if link not in CORE_LINKS)

LOAD_PORT_BASE = 5400
LOAD_PORTS = {
    link: LOAD_PORT_BASE + i
    for i, link in enumerate(T7.LINK_NAMES)
}


@dataclass(frozen=True)
class TrafficConfig:
    """Physical traffic design for one link.

    ``cap_mbps`` and ``rho_target`` set the mean load. ``sigma_target`` sets the
    per-flow rate through the M/G/inf relation:

        sigma_rho = sqrt(rho_target * r_f / C)
    """

    cap_mbps: float
    rho_target: float = 0.92
    sigma_target: float = 0.20
    kappa: float = 2.5
    size_min_kb: float = 20.0

    def __post_init__(self) -> None:
        if self.cap_mbps <= 0:
            raise ValueError("cap_mbps must be positive")
        if not (0.0 < self.rho_target < 1.0):
            raise ValueError("rho_target must be in (0, 1)")
        if self.sigma_target <= 0:
            raise ValueError("sigma_target must be positive")
        if self.kappa <= 1.0:
            raise ValueError("kappa must be > 1 so mean flow size is finite")
        if self.size_min_kb <= 0:
            raise ValueError("size_min_kb must be positive")

    @property
    def cap_bps(self) -> float:
        return self.cap_mbps * 1e6

    @property
    def size_min_bits(self) -> float:
        return self.size_min_kb * 1024.0 * 8.0

    @property
    def rate_bps(self) -> float:
        return self.cap_bps * self.sigma_target**2 / self.rho_target

    @property
    def mean_size_bits(self) -> float:
        return self.kappa * self.size_min_bits / (self.kappa - 1.0)

    @property
    def lam(self) -> float:
        return self.rho_target * self.cap_bps / self.mean_size_bits

    @property
    def n_concurrent(self) -> float:
        return self.rho_target * self.cap_bps / self.rate_bps

    @property
    def mean_duration_s(self) -> float:
        return self.mean_size_bits / self.rate_bps

    @property
    def tau_pred_s(self) -> float:
        """Predicted lag where Pareto M/G/inf ACF reaches 1/e."""
        u_min = self.size_min_bits / self.rate_bps
        return u_min * ((self.kappa / math.e) ** (1.0 / (1.0 - self.kappa)))

    @property
    def hurst(self) -> float:
        """Hurst exponent implied by the Pareto M/G/inf traffic model.

        The relation H = (3-kappa)/2 only applies for 1 < kappa < 2, where
        flow durations have infinite variance and create long-range
        dependence. For kappa >= 2 the variance is finite, so this model does
        not imply LRD and the neutral value is H = 0.5.
        """
        if 1.0 < self.kappa < 2.0:
            return (3.0 - self.kappa) / 2.0
        if self.kappa >= 2.0:
            return 0.5
        raise ValueError("kappa <= 1 gives infinite mean flow duration")

    def as_dict(self) -> Dict[str, float]:
        return {
            "cap_mbps": float(self.cap_mbps),
            "rho_target": float(self.rho_target),
            "sigma_target": float(self.sigma_target),
            "kappa": float(self.kappa),
            "size_min_kb": float(self.size_min_kb),
            "rate_bps": float(self.rate_bps),
            "lambda_flow_s": float(self.lam),
            "n_concurrent": float(self.n_concurrent),
            "mean_duration_s": float(self.mean_duration_s),
            "tau_pred_s": float(self.tau_pred_s),
            "hurst": float(self.hurst),
        }

    def summary(self) -> str:
        return (
            "lambda=%6.2f flow/s | r_f=%7.1f kbps | N_mean=%6.1f | "
            "E[D]=%5.3fs | tau_pred=%6.3fs | H=%4.2f"
            % (
                self.lam,
                self.rate_bps / 1e3,
                self.n_concurrent,
                self.mean_duration_s,
                self.tau_pred_s,
                self.hurst,
            )
        )


def pareto_size_bits(cfg: TrafficConfig, rng: random.Random) -> float:
    """Sample Pareto size using inverse-transform sampling."""
    u = max(rng.random(), 1e-12)
    return cfg.size_min_bits * u ** (-1.0 / cfg.kappa)


def link_caps_from_topology() -> Dict[str, float]:
    return {link: float(cfg[0]) for link, cfg in T7.LINKS.items()}


def default_rho_targets() -> Dict[str, float]:
    return {link: float(T7.LOAD_MEAN[link]) for link in T7.LINK_NAMES}


def traffic_profile(
    link_caps: Optional[Mapping[str, float]] = None,
    rho_targets: Optional[Mapping[str, float]] = None,
    sigma_target: float = 0.20,
    edge_sigma_target: Optional[float] = None,
    kappa: float = 2.5,
    size_min_kb: float = 20.0,
) -> Dict[str, TrafficConfig]:
    """Return per-link physical traffic configs."""
    caps = dict(link_caps or link_caps_from_topology())
    targets = dict(rho_targets or default_rho_targets())
    return {
        link: TrafficConfig(
            cap_mbps=float(caps[link]),
            rho_target=float(targets[link]),
            sigma_target=(
                float(edge_sigma_target)
                if edge_sigma_target is not None and link in EDGE_LINKS
                else float(sigma_target)
            ),
            kappa=float(kappa),
            size_min_kb=float(size_min_kb),
        )
        for link in T7.LINK_NAMES
    }


def print_profile(profile: Mapping[str, TrafficConfig]) -> None:
    print("Phase 20 v7 traffic profile (predicted, compare with measurement):")
    for link in T7.LINK_NAMES:
        print("  %s: %s" % (link, profile[link].summary()))


class ResidentLoadGenerator:
    """Launch one long-lived FlowEngine process for one load channel."""

    def __init__(
        self,
        net,
        link: str,
        cfg: TrafficConfig,
        seed: int,
        duration_s: float,
        python_bin: str,
        repo_root: str,
        log_dt_s: float,
        log_dir: str,
        payload_bytes: int = 1400,
    ) -> None:
        self.net = net
        self.link = link
        self.cfg = cfg
        self.seed = int(seed)
        self.duration_s = float(duration_s)
        self.python_bin = python_bin
        self.repo_root = repo_root
        self.log_dt_s = float(log_dt_s)
        self.log_dir = log_dir
        self.payload_bytes = int(payload_bytes)
        self.port = LOAD_PORTS[link]
        self.src_name, self.dst_name = LOAD_CHANNELS[link]
        self.rho_log_path = os.path.join(log_dir, "rho_offered_%s.csv" % link)
        self.run_summary_path = os.path.join(log_dir, "flow_%s_summary.json" % link)
        self.sink_summary_path = os.path.join(log_dir, "sink_%s_summary.json" % link)
        self.pid = None
        self.sink_pid = None
        self.error = None

    def _shell_prefix(self) -> str:
        return "cd %s && export PYTHONPATH=%s:${PYTHONPATH:-}" % (
            shlex.quote(self.repo_root),
            shlex.quote(self.repo_root),
        )

    def _background(self, host, command: str, log_path: str) -> Optional[int]:
        full = "%s && %s > %s 2>&1 & echo $!" % (
            self._shell_prefix(),
            command,
            shlex.quote(log_path),
        )
        out = run_host_shell(host, full, timeout=2).strip().splitlines()
        for line in reversed(out):
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
            "%s -m mininet.flow_engine sink --port %d --duration %.3f "
            "--summary-out %s"
            % (
                shlex.quote(self.python_bin),
                self.port,
                self.duration_s + 5.0,
                shlex.quote(self.sink_summary_path),
            )
        )
        self.sink_pid = self._background(
            dst,
            sink_cmd,
            os.path.join(self.log_dir, "sink_%s.log" % self.link),
        )
        time.sleep(0.05)

        run_cmd = (
            "%s -m mininet.flow_engine run "
            "--cap-mbps %.9f --rho-target %.9f --sigma-target %.9f "
            "--kappa %.9f --size-min-kb %.9f --dst-ip %s --dst-port %d "
            "--seed %d --duration %.3f --log-dt %.6f --payload-bytes %d "
            "--rho-log %s --summary-out %s"
            % (
                shlex.quote(self.python_bin),
                self.cfg.cap_mbps,
                self.cfg.rho_target,
                self.cfg.sigma_target,
                self.cfg.kappa,
                self.cfg.size_min_kb,
                shlex.quote(dst.IP()),
                self.port,
                self.seed,
                self.duration_s,
                self.log_dt_s,
                self.payload_bytes,
                shlex.quote(self.rho_log_path),
                shlex.quote(self.run_summary_path),
            )
        )
        self.pid = self._background(
            src,
            run_cmd,
            os.path.join(self.log_dir, "flow_%s.log" % self.link),
        )

    def summary(self) -> Dict[str, object]:
        data: Dict[str, object] = {
            "pid": self.pid,
            "sink_pid": self.sink_pid,
            "rho_log_path": self.rho_log_path,
            "summary_path": self.run_summary_path,
        }
        try:
            import json

            with open(self.run_summary_path, encoding="utf-8") as f:
                data.update(json.load(f))
        except OSError:
            pass
        return data


def start_all(
    net,
    link_caps: Optional[Mapping[str, float]] = None,
    rho_targets: Optional[Mapping[str, float]] = None,
    seed: int = 0,
    duration_s: float = 300.0,
    sigma_target: float = 0.20,
    edge_sigma_target: Optional[float] = None,
    kappa: float = 2.5,
    size_min_kb: float = 20.0,
    python_bin: Optional[str] = None,
    repo_root: Optional[str] = None,
    log_dt_s: float = 0.010,
    log_dir: str = "results/RAW/phase-20/flow_logs",
    payload_bytes: int = 1400,
    stop_event=None,
) -> Iterable[ResidentLoadGenerator]:
    """Start all eight resident load generators.

    ``stop_event`` is accepted for compatibility with the old threaded iperf
    implementation; resident engines are bounded by ``duration_s``.
    """
    profile = traffic_profile(
        link_caps=link_caps,
        rho_targets=rho_targets,
        sigma_target=sigma_target,
        edge_sigma_target=edge_sigma_target,
        kappa=kappa,
        size_min_kb=size_min_kb,
    )
    print_profile(profile)
    gens = []
    py = python_bin or sys.executable
    root = repo_root or os.getcwd()
    for i, link in enumerate(T7.LINK_NAMES):
        gen = ResidentLoadGenerator(
            net=net,
            link=link,
            cfg=profile[link],
            seed=int(seed) * 100 + i,
            duration_s=float(duration_s),
            python_bin=py,
            repo_root=root,
            log_dt_s=log_dt_s,
            log_dir=log_dir,
            payload_bytes=payload_bytes,
        )
        gen.start()
        gens.append(gen)
    return gens


def stop_traffic_for_v7_hosts(net) -> None:
    """Best-effort cleanup of resident engines on all Phase 20 v7 hosts."""
    names = sorted({name for pair in LOAD_CHANNELS.values() for name in pair})
    for name in names:
        try:
            run_host_shell(
                net.get(name),
                "pkill -f 'mininet.flow_engine' 2>/dev/null || true",
                timeout=1,
            )
        except Exception:
            pass


def stop_iperf_for_v7_hosts(net) -> None:
    """Backward-compatible name for cleanup callers."""
    stop_traffic_for_v7_hosts(net)
