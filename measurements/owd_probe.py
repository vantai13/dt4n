#!/usr/bin/env python3
"""Phase L / Lesson L.2 -- raw one-way-delay probe.

This program only records raw measurements. Analysis lives in
``measurements.owd_analyze`` so raw data can be reused without rerunning the
network experiment.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import socket
import struct
import time
from typing import Optional, Tuple


MAGIC = b"DT4N"
PKT_VERSION = 1
KIND_BG = 0
KIND_PROBE = 1

HDR = struct.Struct("<4sBBHQdQ")
assert HDR.size == 32

REC_RX = struct.Struct("<Qdd")
REC_TX = struct.Struct("<Qd")


def pack_packet(kind: int, seq: int, t_send: float, run_id: int, size: int) -> bytes:
    head = HDR.pack(MAGIC, PKT_VERSION, int(kind), 0, int(seq), float(t_send), int(run_id))
    if int(size) < HDR.size:
        raise ValueError("size phai >= %d" % HDR.size)
    return head + b"\x00" * (int(size) - HDR.size)


def unpack_packet(buf: bytes) -> Optional[Tuple[int, int, float, int]]:
    """Return (kind, seq, t_send, run_id), or None for foreign packets."""
    if len(buf) < HDR.size:
        return None
    magic, ver, kind, _rsv, seq, t_send, run_id = HDR.unpack_from(buf, 0)
    if magic != MAGIC or ver != PKT_VERSION:
        return None
    return int(kind), int(seq), float(t_send), int(run_id)


def udp_socket_drops(port: int) -> int:
    """Read UDP socket drops from /proc/net/udp* for the listening port."""
    hexport = "%04X" % int(port)
    total = 0
    for path in ("/proc/net/udp", "/proc/net/udp6"):
        try:
            with open(path, "r", encoding="ascii") as f:
                next(f)
                for line in f:
                    cols = line.split()
                    if len(cols) < 13:
                        continue
                    if cols[1].split(":")[-1] == hexport:
                        total += int(cols[-1])
        except (OSError, StopIteration, ValueError):
            pass
    return total


def run_recv(
    port: int,
    duration_s: float,
    out_path: str,
    rcvbuf: int = 8 << 20,
    flush_every: int = 4096,
) -> dict:
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, int(rcvbuf))
    got = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
    sock.bind(("0.0.0.0", int(port)))
    sock.settimeout(0.25)

    drops0 = udp_socket_drops(port)
    buf = bytearray(65535)
    pending = []
    n_ok = 0
    n_bad = 0
    run_ids = set()
    t_end = time.monotonic() + float(duration_s)

    f = open(out_path, "wb", buffering=1 << 20)
    try:
        while time.monotonic() < t_end:
            try:
                nbytes, _addr = sock.recvfrom_into(buf)
            except socket.timeout:
                continue
            t_recv = time.monotonic()

            info = unpack_packet(memoryview(buf)[:nbytes])
            if info is None:
                n_bad += 1
                continue
            _kind, seq, t_send, run_id = info
            run_ids.add(run_id)
            pending.append(REC_RX.pack(seq, t_send, t_recv))
            n_ok += 1
            if len(pending) >= flush_every:
                f.write(b"".join(pending))
                pending.clear()
        if pending:
            f.write(b"".join(pending))
    finally:
        f.close()
        sock.close()

    drops1 = udp_socket_drops(port)
    meta = {
        "role": "recv",
        "port": int(port),
        "out": out_path,
        "n_records": n_ok,
        "n_foreign_packets": n_bad,
        "run_ids_seen": sorted(run_ids),
        "socket_rcvbuf_bytes": got,
        "socket_drops_delta": drops1 - drops0,
        "record_struct": "<Qdd",
    }
    with open(out_path + ".meta.json", "w", encoding="utf-8") as g:
        json.dump(meta, g, indent=2, sort_keys=True)
    return meta


def sleep_until(t_target: float, spin_margin: float = 0.0004) -> float:
    """Hybrid sleep/spin scheduler for low-jitter packet pacing."""
    while True:
        now = time.monotonic()
        dt = t_target - now
        if dt <= 0:
            return now
        if dt > spin_margin:
            time.sleep(dt - spin_margin)
        else:
            while time.monotonic() < t_target:
                pass
            return time.monotonic()


def run_send(
    dst_ip: str,
    port: int,
    mode: str,
    rate_pps: float,
    size: int,
    duration_s: float,
    run_id: int,
    seed: int,
    out_path: str,
    kind: int = KIND_PROBE,
    burst_n: int = 0,
) -> dict:
    """Send packets in poisson, cbr, or immediate burst mode."""
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 20)
    addr = (dst_ip, int(port))
    rng = random.Random(seed)

    recs = []
    seq = 0
    t0 = time.monotonic()

    if mode == "burst":
        for _ in range(int(burst_n)):
            t_send = time.monotonic()
            sock.sendto(pack_packet(kind, seq, t_send, run_id, size), addr)
            recs.append(REC_TX.pack(seq, t_send))
            seq += 1
    else:
        t_next = t0
        t_end = t0 + float(duration_s)
        mean_gap = 1.0 / float(rate_pps)
        while t_next < t_end:
            sleep_until(t_next)
            t_send = time.monotonic()
            sock.sendto(pack_packet(kind, seq, t_send, run_id, size), addr)
            recs.append(REC_TX.pack(seq, t_send))
            seq += 1
            gap = rng.expovariate(1.0 / mean_gap) if mode == "poisson" else mean_gap
            t_next += gap

    t1 = time.monotonic()
    sock.close()

    with open(out_path, "wb") as f:
        f.write(b"".join(recs))

    meta = {
        "role": "send",
        "mode": mode,
        "kind": int(kind),
        "n_sent": seq,
        "size_bytes": int(size),
        "frame_bytes_on_wire": int(size) + 42,
        "rate_pps_nominal": float(rate_pps) if mode != "burst" else None,
        "rate_pps_actual": seq / max(t1 - t0, 1e-9),
        "duration_s_actual": t1 - t0,
        "run_id": int(run_id),
        "seed": int(seed),
        "out": out_path,
        "record_struct": "<Qd",
    }
    with open(out_path + ".meta.json", "w", encoding="utf-8") as g:
        json.dump(meta, g, indent=2, sort_keys=True)
    return meta


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase L OWD probe (raw only)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    recv = sub.add_parser("recv")
    recv.add_argument("--port", type=int, required=True)
    recv.add_argument("--duration", type=float, required=True)
    recv.add_argument("--out", required=True)

    send = sub.add_parser("send")
    send.add_argument("--dst", required=True)
    send.add_argument("--port", type=int, required=True)
    send.add_argument("--mode", choices=["poisson", "cbr", "burst"], default="poisson")
    send.add_argument("--rate", type=float, default=20.0, help="packets/second")
    send.add_argument("--size", type=int, default=64, help="UDP payload bytes")
    send.add_argument("--duration", type=float, default=60.0)
    send.add_argument("--burst-n", type=int, default=0)
    send.add_argument("--run-id", type=int, required=True)
    send.add_argument("--seed", type=int, default=1)
    send.add_argument("--kind", type=int, default=KIND_PROBE)
    send.add_argument("--out", required=True)

    args = ap.parse_args()
    if args.cmd == "recv":
        meta = run_recv(args.port, args.duration, args.out)
    else:
        meta = run_send(
            args.dst,
            args.port,
            args.mode,
            args.rate,
            args.size,
            args.duration,
            args.run_id,
            args.seed,
            args.out,
            kind=args.kind,
            burst_n=args.burst_n,
        )
    print(json.dumps(meta, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
