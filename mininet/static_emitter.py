#!/usr/bin/env python3
"""Deterministic CBR emitter for the Phase G NC-G1-static control.

Packet ``k`` is scheduled against the absolute deadline ``t0 + k / rate_pps``.
Packets due at each wake-up are sent as a deterministic batch. Scheduler
delays therefore do not accumulate, while the emitter never busy-spins. The
cumulative ledger includes an absolute monotonic timestamp so an independent
sampler clock can expose stalls.
"""
from __future__ import annotations

import argparse
import csv
import os
import socket
import time
from dataclasses import dataclass

from mininet.flow_engine import udp_sink, write_summary


@dataclass(frozen=True)
class StaticConfig:
    """Configuration for one deterministic CBR channel."""

    cap_mbps: float
    rho_target: float
    payload_bytes: int = 1400

    def __post_init__(self) -> None:
        if self.cap_mbps <= 0.0:
            raise ValueError("cap_mbps must be positive")
        if not 0.0 < self.rho_target < 1.0:
            raise ValueError("rho_target must be in (0, 1)")
        if self.payload_bytes <= 0:
            raise ValueError("payload_bytes must be positive")

    @property
    def cap_bps(self) -> float:
        return self.cap_mbps * 1e6

    @property
    def payload_bits(self) -> float:
        return self.payload_bytes * 8.0

    @property
    def rate_bps(self) -> float:
        return self.cap_bps * self.rho_target

    @property
    def rate_pps(self) -> float:
        return self.rate_bps / self.payload_bits

    @property
    def gap_s(self) -> float:
        return 1.0 / self.rate_pps

    def n_pkt_per_window(self, dt_s: float) -> float:
        return self.rate_pps * float(dt_s)

    def sigma_quant_floor(self, dt_s: float) -> float:
        n_packets = self.n_pkt_per_window(dt_s)
        return 1.0 / (n_packets * (12.0**0.5)) if n_packets > 0 else float("inf")


class StaticEmitter:
    """Send UDP at a fixed rate using cumulative-target pacing."""

    def __init__(
        self,
        cfg: StaticConfig,
        dst_ip: str,
        dst_port: int,
        ledger_path: str,
        log_dt_s: float = 0.010,
        pace_tick_s: float = 0.002,
    ) -> None:
        if log_dt_s <= 0.0:
            raise ValueError("log_dt_s must be positive")
        if pace_tick_s <= 0.0:
            raise ValueError("pace_tick_s must be positive")
        self.cfg = cfg
        self.addr = (dst_ip, int(dst_port))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ledger_path = ledger_path
        self.log_dt_s = float(log_dt_s)
        self.pace_tick_s = float(pace_tick_s)
        self.n_packets = 0
        self.max_lag_s = 0.0
        self.n_catchup = 0
        self.n_send_errors = 0
        self.max_backlog = 0
        self.t0_monotonic = 0.0
        self.max_ledger_gap_s = 0.0

    def run(self, duration_s: float) -> int:
        if duration_s <= 0.0:
            raise ValueError("duration_s must be positive")
        parent = os.path.dirname(os.path.abspath(self.ledger_path))
        if parent:
            os.makedirs(parent, exist_ok=True)

        payload = b"x" * self.cfg.payload_bytes
        sendto = self.sock.sendto
        addr = self.addr
        gap = self.cfg.gap_s
        t0 = time.monotonic()
        self.t0_monotonic = t0
        t_end = t0 + float(duration_s)
        t_next_log = t0
        rows = 0

        with open(self.ledger_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=(
                    "sample_index",
                    "timestamp_s",
                    "monotonic_s",
                    "t_mono",
                    "cum_packets",
                    "cum_bytes",
                    "lag_s",
                ),
            )
            writer.writeheader()
            sample_index = 0
            last_log_t = None

            while True:
                now = time.monotonic()
                if now >= t_end:
                    break

                due = int((now - t0) / gap) - self.n_packets
                if due > 0:
                    self.max_backlog = max(self.max_backlog, due)
                    self.max_lag_s = max(self.max_lag_s, due * gap)
                    if due > 1:
                        self.n_catchup += 1
                    for _ in range(due):
                        try:
                            sendto(payload, addr)
                        except OSError:
                            self.n_send_errors += 1
                        finally:
                            self.n_packets += 1

                # V3 records the cumulative state after the due batch.  Both
                # this timestamp and the counter sampler use CLOCK_MONOTONIC,
                # so a staircase lookup has a measured (not interpolated)
                # alignment uncertainty.
                now = time.monotonic()
                if now >= t_next_log:
                    due_packets = int((now - t0) / gap)
                    lag = max(0, due_packets - self.n_packets) * gap
                    writer.writerow(
                        {
                            "sample_index": sample_index,
                            "timestamp_s": "%.6f" % (now - t0),
                            "monotonic_s": "%.9f" % now,
                            "t_mono": "%.9f" % now,
                            "cum_packets": self.n_packets,
                            "cum_bytes": self.n_packets * self.cfg.payload_bytes,
                            "lag_s": "%.6f" % lag,
                        }
                    )
                    if last_log_t is not None:
                        self.max_ledger_gap_s = max(
                            self.max_ledger_gap_s, now - last_log_t
                        )
                    last_log_t = now
                    sample_index += 1
                    rows += 1
                    missed = int((now - t_next_log) / self.log_dt_s)
                    t_next_log += (missed + 1) * self.log_dt_s

                next_packet = t0 + (self.n_packets + 1) * gap
                target = min(next_packet, t_next_log, t_end)
                sleep_s = target - time.monotonic()
                if sleep_s > 0.0:
                    time.sleep(min(sleep_s, 0.005))
                else:
                    # Yield explicitly when late; continuing would recreate a
                    # busy loop and the reflexive CPU artifact found in v1.
                    time.sleep(self.pace_tick_s)

        self.sock.close()
        return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("--cap-mbps", type=float, required=True)
    run.add_argument("--rho-target", type=float, required=True)
    run.add_argument("--payload-bytes", type=int, default=1400)
    run.add_argument("--dst-ip", required=True)
    run.add_argument("--dst-port", type=int, required=True)
    run.add_argument("--duration", type=float, required=True)
    run.add_argument("--log-dt", type=float, default=0.010)
    run.add_argument("--pace-tick", type=float, default=0.002)
    run.add_argument("--ledger", required=True)
    run.add_argument("--summary-out", required=True)
    sink = sub.add_parser("sink")
    sink.add_argument("--port", type=int, required=True)
    sink.add_argument("--duration", type=float, required=True)
    sink.add_argument("--summary-out", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cmd == "sink":
        packets = udp_sink(args.port, args.duration)
        write_summary(args.summary_out, {"packets": packets, "port": int(args.port)})
        return

    cfg = StaticConfig(args.cap_mbps, args.rho_target, args.payload_bytes)
    emitter = StaticEmitter(
        cfg, args.dst_ip, args.dst_port, args.ledger, args.log_dt, args.pace_tick
    )
    rows = emitter.run(args.duration)
    expected = cfg.rate_pps * args.duration
    write_summary(
        args.summary_out,
        {
            "engine": "static_cbr",
            "rows": rows,
            "packets_sent": emitter.n_packets,
            "packets_expected": float(expected),
            "packet_shortfall_ratio": float(max(0.0, 1.0 - emitter.n_packets / expected)),
            "max_lag_s": emitter.max_lag_s,
            "max_backlog": emitter.max_backlog,
            "n_catchup": emitter.n_catchup,
            "n_send_errors": emitter.n_send_errors,
            "cap_mbps": cfg.cap_mbps,
            "rho_target": cfg.rho_target,
            "rate_pps": cfg.rate_pps,
            "gap_s": cfg.gap_s,
            "payload_bytes": cfg.payload_bytes,
            "pace_tick_s": emitter.pace_tick_s,
            "t0_monotonic": emitter.t0_monotonic,
            "ledger_tick_s": emitter.log_dt_s,
            "align_error_pkts_design": cfg.rate_pps * emitter.log_dt_s,
            "max_ledger_gap_s": emitter.max_ledger_gap_s,
            "align_error_pkts_observed_max": cfg.rate_pps
            * emitter.max_ledger_gap_s,
            "sigma_true": 0.0,
            "sigma_quant_floor_at_0p2s": cfg.sigma_quant_floor(0.20),
            "n_pkt_per_window_0p2s": cfg.n_pkt_per_window(0.20),
        },
    )


if __name__ == "__main__":
    main()
