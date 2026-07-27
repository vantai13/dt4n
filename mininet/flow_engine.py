#!/usr/bin/env python3
"""Resident UDP flow engine for one Phase 20 load channel.

The first Phase 20.1b implementation spawned one iperf client per synthetic
flow. At roughly 160 flows/second across eight links, fork/exec overhead became
part of the experiment. This module keeps one Python process alive per channel,
manages virtual Poisson/Pareto flows in memory, sends UDP at their aggregate
rate, and logs exact offered load:

    rho_offered(t) = sum(active_flow_rates) / link_capacity

That is the quantity consumed by ``twin.link_model``.
"""

from __future__ import annotations

import argparse
import csv
import heapq
import json
import math
import os
import random
import socket
import time
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


@dataclass(frozen=True)
class EngineConfig:
    cap_mbps: float
    rho_target: float
    sigma_target: float
    kappa: float
    size_min_kb: float

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
    def mean_duration_s(self) -> float:
        return self.mean_size_bits / self.rate_bps

    @property
    def min_duration_s(self) -> float:
        return self.size_min_bits / self.rate_bps

    @property
    def n_concurrent(self) -> float:
        return self.rho_target * self.cap_bps / self.rate_bps


class FlowEngine:
    """Manage virtual flows and send their aggregate UDP load."""

    def __init__(
        self,
        cfg: EngineConfig,
        dst_ip: str,
        dst_port: int,
        seed: int,
        rho_log_path: str,
        log_dt_s: float = 0.010,
        payload_bytes: int = 1400,
        warm_start: bool = True,
        warm_start_mode: str = "mean",
    ) -> None:
        if cfg.kappa <= 1.0:
            raise ValueError("kappa must be > 1")
        if log_dt_s <= 0.0:
            raise ValueError("log_dt_s must be positive")
        if payload_bytes <= 0:
            raise ValueError("payload_bytes must be positive")

        self.cfg = cfg
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)
        self.addr = (dst_ip, int(dst_port))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rho_log_path = rho_log_path
        self.log_dt_s = float(log_dt_s)
        self.payload_bytes = int(payload_bytes)
        self.warm_start_enabled = bool(warm_start)
        self.warm_start_mode = warm_start_mode
        self.active: List[Tuple[float, float]] = []
        self.rate_sum_bps = 0.0
        self.n_started = 0
        self.n_warm_started = 0
        self.n_packets = 0

    def pareto_size_bits(self) -> float:
        u = max(self.rng.random(), 1e-12)
        return self.cfg.size_min_bits * u ** (-1.0 / self.cfg.kappa)

    def spawn(self, now: float) -> None:
        dur_s = self.pareto_size_bits() / self.cfg.rate_bps
        heapq.heappush(self.active, (now + dur_s, self.cfg.rate_bps))
        self.rate_sum_bps += self.cfg.rate_bps
        self.n_started += 1

    def residual_duration_s(self) -> float:
        """Sample equilibrium residual life for Pareto flow duration."""
        k = self.cfg.kappa
        u_min = self.cfg.min_duration_s
        y = max(self.rng.random(), 1e-12)  # target survival P(R > r)
        if y > 1.0 / k:
            return (1.0 - y) * self.cfg.mean_duration_s
        return u_min * (k * y) ** (-1.0 / (k - 1.0))

    def warm_start(self, now: float) -> int:
        """Seed active flows from the M/G/inf stationary distribution."""
        if not self.warm_start_enabled:
            return 0
        if self.warm_start_mode == "poisson":
            n = int(self.np_rng.poisson(self.cfg.n_concurrent))
        elif self.warm_start_mode == "mean":
            n = int(round(self.cfg.n_concurrent))
        else:
            raise ValueError("unknown warm_start_mode: %s" % self.warm_start_mode)
        for _ in range(n):
            heapq.heappush(
                self.active,
                (now + self.residual_duration_s(), self.cfg.rate_bps),
            )
        self.rate_sum_bps += n * self.cfg.rate_bps
        return n

    def retire(self, now: float) -> None:
        while self.active and self.active[0][0] <= now:
            _end, rate = heapq.heappop(self.active)
            self.rate_sum_bps -= rate
        if self.rate_sum_bps < 0 and abs(self.rate_sum_bps) < 1e-6:
            self.rate_sum_bps = 0.0

    @property
    def rho_offered(self) -> float:
        return self.rate_sum_bps / self.cfg.cap_bps

    def _next_sleep(self, now: float, *times: float) -> float:
        future = [t for t in times if math.isfinite(t) and t > now]
        if not future:
            return 0.0
        return max(0.0, min(min(future) - now, 0.005))

    def run(self, duration_s: float) -> int:
        parent = os.path.dirname(os.path.abspath(self.rho_log_path))
        if parent:
            os.makedirs(parent, exist_ok=True)

        payload = b"x" * self.payload_bytes
        t0 = time.monotonic()
        t_end = t0 + float(duration_s)
        t_next_arrival = t0 + self.rng.expovariate(self.cfg.lam)
        t_next_log = t0
        t_next_send = math.inf
        rows = 0

        with open(self.rho_log_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=(
                    "sample_index",
                    "timestamp_s",
                    "rho_offered",
                    "n_active",
                    "rate_sum_bps",
                ),
            )
            writer.writeheader()
            sample_index = 0
            self.n_warm_started = self.warm_start(t0)
            if self.rate_sum_bps > 0.0:
                t_next_send = t0

            while True:
                now = time.monotonic()
                if now >= t_end:
                    break

                self.retire(now)

                while now >= t_next_arrival:
                    self.spawn(now)
                    t_next_arrival += self.rng.expovariate(self.cfg.lam)
                    if not math.isfinite(t_next_send):
                        t_next_send = now

                if self.rate_sum_bps > 0.0 and now >= t_next_send:
                    self.sock.sendto(payload, self.addr)
                    self.n_packets += 1
                    t_next_send = now + (self.payload_bytes * 8.0) / self.rate_sum_bps
                elif self.rate_sum_bps <= 0.0:
                    t_next_send = math.inf

                while now >= t_next_log:
                    writer.writerow(
                        {
                            "sample_index": sample_index,
                            "timestamp_s": "%.6f" % (now - t0),
                            "rho_offered": "%.8f" % self.rho_offered,
                            "n_active": len(self.active),
                            "rate_sum_bps": "%.3f" % self.rate_sum_bps,
                        }
                    )
                    sample_index += 1
                    rows += 1
                    t_next_log += self.log_dt_s

                sleep_s = self._next_sleep(
                    now,
                    t_next_arrival,
                    t_next_log,
                    t_next_send,
                    self.active[0][0] if self.active else math.inf,
                    t_end,
                )
                if sleep_s > 0.0:
                    time.sleep(sleep_s)

        return rows


def udp_sink(port: int, duration_s: float, timeout_s: float = 0.2) -> int:
    """Receive and discard UDP packets for ``duration_s`` seconds."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", int(port)))
    sock.settimeout(float(timeout_s))
    deadline = time.monotonic() + float(duration_s)
    packets = 0
    while time.monotonic() < deadline:
        try:
            sock.recvfrom(65535)
            packets += 1
        except socket.timeout:
            pass
    return packets


def write_summary(path: str, data: object) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def parse_args():
    p = argparse.ArgumentParser(description="Resident Phase 20 flow engine")
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run")
    run.add_argument("--cap-mbps", type=float, required=True)
    run.add_argument("--rho-target", type=float, required=True)
    run.add_argument("--sigma-target", type=float, required=True)
    run.add_argument("--kappa", type=float, required=True)
    run.add_argument("--size-min-kb", type=float, required=True)
    run.add_argument("--dst-ip", required=True)
    run.add_argument("--dst-port", type=int, required=True)
    run.add_argument("--seed", type=int, required=True)
    run.add_argument("--duration", type=float, required=True)
    run.add_argument("--log-dt", type=float, default=0.010)
    run.add_argument("--payload-bytes", type=int, default=1400)
    run.add_argument("--warm-start-mode", choices=["mean", "poisson"], default="mean")
    run.add_argument("--rho-log", required=True)
    run.add_argument("--summary-out", required=True)

    sink = sub.add_parser("sink")
    sink.add_argument("--port", type=int, required=True)
    sink.add_argument("--duration", type=float, required=True)
    sink.add_argument("--summary-out", required=True)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.cmd == "sink":
        packets = udp_sink(args.port, args.duration)
        write_summary(args.summary_out, {"packets": packets, "port": int(args.port)})
        return

    cfg = EngineConfig(
        cap_mbps=args.cap_mbps,
        rho_target=args.rho_target,
        sigma_target=args.sigma_target,
        kappa=args.kappa,
        size_min_kb=args.size_min_kb,
    )
    engine = FlowEngine(
        cfg=cfg,
        dst_ip=args.dst_ip,
        dst_port=args.dst_port,
        seed=args.seed,
        rho_log_path=args.rho_log,
        log_dt_s=args.log_dt,
        payload_bytes=args.payload_bytes,
        warm_start_mode=args.warm_start_mode,
    )
    rows = engine.run(args.duration)
    write_summary(
        args.summary_out,
        {
            "rows": rows,
            "flows_started": engine.n_started,
            "warm_start_active": engine.n_warm_started,
            "packets_sent": engine.n_packets,
            "final_active": len(engine.active),
            "warm_start": engine.warm_start_enabled,
            "warm_start_mode": engine.warm_start_mode,
            "cap_mbps": cfg.cap_mbps,
            "rho_target": cfg.rho_target,
            "sigma_target": cfg.sigma_target,
            "kappa": cfg.kappa,
            "size_min_kb": cfg.size_min_kb,
        },
    )


if __name__ == "__main__":
    main()
