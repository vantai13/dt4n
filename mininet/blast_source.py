#!/usr/bin/env python3
"""Backlogged UDP source. It has NO timing requirement of its own.

The design principle of G-A017: every bit of timing precision lives in the
KERNEL (the HTB shaper). This process has exactly one job, which is to keep
the shaper's queue from running dry. If it is descheduled for 100 ms the
shaper keeps draining its backlog and the EGRESS RATE DOES NOT CHANGE. That
is the whole reason the mechanism escapes `G-L98`.

★ `setblocking(True)` is a design decision, not an option. When the qdisc
  fills, `send()` sleeps until there is room, so the process self-throttles at
  the shaper's rate and costs almost no CPU. That is kernel backpressure. A
  non-blocking spin loop would recreate the eight CPU-consuming processes that
  `G-L98` says this host cannot provision.
"""
from __future__ import annotations

import socket
import sys

PAYLOAD_BYTES = 1400


def main(dst_ip: str, dst_port: int) -> None:
    payload = b"\x00" * PAYLOAD_BYTES
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((dst_ip, dst_port))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 20)
    sock.setblocking(True)
    while True:
        try:
            sock.send(payload)
        except OSError:
            # ENOBUFS can still surface on some paths; back off by retrying.
            continue


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
