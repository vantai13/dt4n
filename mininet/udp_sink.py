#!/usr/bin/env python3
"""Blocking UDP sink. Exists so the source's packets are consumed rather than
answered with ICMP port-unreachable, which would put reverse traffic on the
link under measurement. It blocks, so it costs no CPU while idle.
"""
from __future__ import annotations

import socket
import sys


def main(bind_ip: str, port: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 22)
    sock.bind((bind_ip, port))
    while True:
        try:
            sock.recv(65535)
        except OSError:
            continue


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
