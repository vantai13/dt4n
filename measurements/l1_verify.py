#!/usr/bin/env python3
"""Lesson L.1 -- verify Phase L split-qdisc measurement infrastructure.

Run:
    sudo python3 -m measurements.l1_verify --bw 6 --queue 13 --delay 3

The script prints raw ``tc`` output, performs automatic checks, sweeps HTB
burst, and runs the V-L4 positive control that lowers bfifo from q=13 to q=5.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from mininet.link import Link
from mininet.net import Mininet
from mininet.node import OVSBridge

from mininet.topology_split_qdisc import (
    DEFAULT_BURST_BYTES,
    FRAME_BYTES_1470,
    SplitQdiscTopo,
    assert_measure_qdisc,
    assert_no_hidden_queue,
    change_measure_qdisc,
    intf_toward,
    parse_qdisc_tree,
    queue_bytes,
    queue_ceiling_ms,
    read_sysfs_tx_bytes,
    setup_measure_qdisc,
    setup_return_qdisc,
    show_class,
    show_qdisc,
)


BLASTER = r'''
import socket, sys, time

ip, port, secs, payload = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 20)
buf = b"x" * payload
end = time.monotonic() + secs
n = 0
while time.monotonic() < end:
    try:
        s.sendto(buf, (ip, port))
        n += 1
    except OSError:
        pass
print(n)
'''


SINK = r'''
import socket, sys

port = int(sys.argv[1])
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("0.0.0.0", port))
while True:
    s.recvfrom(65535)
'''


def hr(title: str) -> None:
    print("\n" + "=" * 74)
    print(title)
    print("=" * 74)


def read_sent_bytes(ifname: str) -> int:
    """Bytes dequeued from the root qdisc, falling back to sysfs tx_bytes."""
    layers = parse_qdisc_tree(show_qdisc(ifname))
    for layer in layers:
        if layer["is_root"] and layer["sent_bytes"] is not None:
            return int(layer["sent_bytes"])
    tx = read_sysfs_tx_bytes(ifname)
    return int(tx or 0)


def read_backlog(ifname: str) -> int:
    layers = parse_qdisc_tree(show_qdisc(ifname))
    for layer in layers:
        if layer["kind"] == "bfifo":
            return int(layer["backlog_bytes"] or 0)
    return 0


def node_qdisc(node: Any, ifname: str) -> str:
    """Read qdisc from a Mininet host namespace."""
    return node.cmd("tc qdisc show dev %s" % ifname).strip()


def hidden_queue_result(node: Any, ifname: str) -> Dict[str, Any]:
    raw = node_qdisc(node, ifname)
    return {
        "ifname": ifname,
        "raw": raw,
        "ok": ("noqueue" in raw) or ("pfifo_fast" in raw),
    }


def nearest_rank(values: List[int], q: float) -> int:
    if not values:
        return 0
    data = sorted(values)
    idx = int((q * len(data) + 0.999999999) // 1) - 1
    return data[min(max(idx, 0), len(data) - 1)]


def blast(net: Mininet, secs: float, payload: int = 1470) -> Tuple[float, Dict[str, Any]]:
    """Oversaturate h1->h2 and return shaped rate plus in-flight backlog stats."""
    h1, h2 = net.get("h1"), net.get("h2")
    ifname = intf_toward(net.get("s1"), "s2")

    h2.cmd("pkill -f /tmp/dt4n_sink.py 2>/dev/null")
    h1.cmd("pkill -f /tmp/dt4n_blast.py 2>/dev/null")
    h2.cmd("python3 /tmp/dt4n_sink.py 5555 >/dev/null 2>&1 &")
    time.sleep(0.3)

    b0 = read_sent_bytes(ifname)
    t0 = time.monotonic()
    h1.cmd(
        "python3 /tmp/dt4n_blast.py 10.0.0.2 5555 %g %d "
        ">/dev/null 2>&1 &" % (secs, payload)
    )
    end = t0 + float(secs)
    samples: List[int] = []
    while time.monotonic() < end:
        samples.append(read_backlog(ifname))
        time.sleep(0.02)
    t1 = time.monotonic()
    b1 = read_sent_bytes(ifname)

    h1.cmd("pkill -f /tmp/dt4n_blast.py 2>/dev/null")
    h2.cmd("pkill -f /tmp/dt4n_sink.py 2>/dev/null")
    dt = max(t1 - t0, 1e-6)
    stats = {
        "n_samples": len(samples),
        "mean_backlog_bytes": sum(samples) / len(samples) if samples else 0.0,
        "p95_backlog_bytes": nearest_rank(samples, 0.95),
        "peak_backlog_bytes": max(samples) if samples else 0,
        "poll_interval_ms": 20.0,
    }
    return (b1 - b0) * 8.0 / dt / 1e6, stats


def ping_mean_ms(output: str) -> Optional[float]:
    m = re.search(r"=\s*([0-9.]+)/([0-9.]+)/([0-9.]+)", output)
    return float(m.group(2)) if m else None


def write_helpers() -> None:
    with open("/tmp/dt4n_blast.py", "w", encoding="ascii") as f:
        f.write(BLASTER)
    with open("/tmp/dt4n_sink.py", "w", encoding="ascii") as f:
        f.write(SINK)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bw", type=float, default=6.0)
    ap.add_argument("--queue", type=int, default=13)
    ap.add_argument("--delay", type=float, default=3.0)
    ap.add_argument("--out-dir", default="results/phase-L")
    ap.add_argument("--blast-secs", type=float, default=5.0)
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    write_helpers()

    report: Dict[str, Any] = {
        "config": vars(args),
        "checks": {},
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    net = Mininet(topo=SplitQdiscTopo(), link=Link, switch=OVSBridge, controller=None)
    net.start()
    try:
        s1, s2 = net.get("s1"), net.get("s2")
        h1, h2 = net.get("h1"), net.get("h2")
        if_measure = intf_toward(s1, "s2")
        if_return = intf_toward(s2, "s1")
        if_h1 = intf_toward(h1, "s1")
        if_s1h1 = intf_toward(s1, "h1")
        if_h2 = intf_toward(h2, "s2")
        if_s2h2 = intf_toward(s2, "h2")

        report["interfaces"] = {
            "measure": if_measure,
            "return": if_return,
            "h1_to_s1": if_h1,
            "s1_to_h1": if_s1h1,
            "h2_to_s2": if_h2,
            "s2_to_h2": if_s2h2,
        }

        hr("BUOC 1 -- QDISC MAC DINH (truoc khi ta dat bat cu thu gi)")
        print("  Muc dich: biet diem xuat phat. Neu o day da co fq_codel/pfifo_fast")
        print("            thi cac link 'khong gioi han' KHONG he khong gioi han.\n")
        default_qdisc: Dict[str, str] = {}
        for name in (if_measure, if_return, if_h1, if_s1h1, if_h2, if_s2h2):
            raw = (
                node_qdisc(h1, name)
                if name == if_h1
                else node_qdisc(h2, name)
                if name == if_h2
                else show_qdisc(name, stats=False).strip()
            )
            default_qdisc[name] = raw
            print("--- %s ---" % name)
            print(raw or "(trong)")
        report["checks"]["default_qdisc"] = default_qdisc

        hr("BUOC 2 -- DUNG QDISC THEO THIET KE")
        cmds_m = setup_measure_qdisc(if_measure, args.bw, args.queue)
        cmds_r = setup_return_qdisc(if_return, args.delay)
        for cmd in cmds_m + cmds_r:
            print("  $ " + cmd)
        report["checks"]["tc_commands"] = cmds_m + cmds_r

        hr("BUOC 3 -- OUTPUT THO. DOC TUNG DONG BANG MAT.")
        qdisc_measure_raw = show_qdisc(if_measure).strip()
        class_measure_raw = show_class(if_measure).strip()
        qdisc_return_raw = show_qdisc(if_return).strip()
        print("\n>>> CHIEU DO  %s  (s1 -> s2)" % if_measure)
        print(qdisc_measure_raw)
        print("\n--- class ---")
        print(class_measure_raw)
        print("\n>>> CHIEU VE  %s  (s2 -> s1)" % if_return)
        print(qdisc_return_raw)
        print(
            """
BAN PHAI TU TRA LOI BON CAU SAU TRUOC KHI DI TIEP:
  (a) Chieu DO co bao nhieu tang qdisc?  Co tang nao ten `netem` khong?
  (b) So sau `limit` o tang bfifo la bao nhieu, va don vi la `b` hay `p`?
  (c) So sau `burst` trong class la bao nhieu?  Co phai 1600 khong?
  (d) Chieu VE co tang nao ten `htb` khong?  (KHONG duoc co)
"""
        )
        report["checks"]["raw_after_setup"] = {
            "measure_qdisc": qdisc_measure_raw,
            "measure_class": class_measure_raw,
            "return_qdisc": qdisc_return_raw,
        }

        hr("BUOC 4 -- KIEM TU DONG V-L1a..V-L1f")
        info = assert_measure_qdisc(if_measure, args.bw, args.queue)
        print("  V-L1a  htb o root chieu DO ................ PASS")
        print("  V-L1b  KHONG co netem o chieu DO .......... PASS")
        print(
            "  V-L1c  bfifo limit = %d b (%d goi x %d B) . PASS"
            % (info["bfifo_limit_bytes"], args.queue, FRAME_BYTES_1470)
        )
        print("  V-L1d  burst = %d b ....................... PASS" % DEFAULT_BURST_BYTES)
        print(
            "  V-L1g  direct_packets_stat = %s ............ PASS"
            % info["direct_packets_stat"]
        )

        ret_layers = parse_qdisc_tree(show_qdisc(if_return))
        assert any(layer["kind"] == "netem" for layer in ret_layers), (
            "V-L1e FAIL: chieu VE khong co netem"
        )
        assert not any(layer["kind"] == "htb" for layer in ret_layers), (
            "V-L1e FAIL: chieu VE co htb"
        )
        print("  V-L1e  chieu VE chi co netem .............. PASS")

        hidden = [
            hidden_queue_result(h1, if_h1),
            assert_no_hidden_queue(if_s1h1),
            hidden_queue_result(h2, if_h2),
            assert_no_hidden_queue(if_s2h2),
        ]
        for item in hidden:
            flag = "PASS" if item["ok"] else "* CANH BAO"
            print(
                "  V-L1f  %-10s khong co hang doi an .. %s   [%s]"
                % (item["ifname"], flag, item["raw"])
            )
        report["checks"]["measure_qdisc_assert"] = info
        report["checks"]["hidden_queue"] = hidden
        print(
            "\n  TRAN BUFFER LY THUYET = %.2f ms   (= %d B x 8 / %g Mbps)"
            % (info["ceiling_ms"], queue_bytes(args.queue), args.bw)
        )

        hr("BUOC 5 -- PING: xac nhan netem chieu VE that su hoat dong")
        ping_out = h1.cmd("ping -c 10 -i 0.2 10.0.0.2")
        rtt = ping_mean_ms(ping_out)
        print(ping_out.strip())
        print(
            "\n  RTT trung binh = %s ms   (mong doi ~ %.1f ms = netem chieu ve)"
            % (rtt, args.delay)
        )
        print("  Neu RTT ~ 0.1 ms -> netem KHONG duoc ap dung -> DUNG LAI.")
        report["checks"]["ping_output"] = ping_out.strip()
        report["checks"]["ping_rtt_ms"] = rtt

        hr("BUOC 6 -- * QUET BURST: chon gia tri NHO NHAT dat >= 98% rate")
        print("  Ly do: burst lon HAP THU burstiness -> triet tieu hieu ung c_a.")
        print("         burst qua nho -> HTB khong dat du toc do.")
        print("  Ta can gia tri NHO NHAT ma van dat toc do.\n")
        print("  %-10s %-14s %-10s" % ("burst(B)", "rate dat(Mbps)", "%danh nghia"))
        burst_rows: List[Dict[str, Any]] = []
        for burst in (1600, 2400, 3200, 6400, 15000):
            change_measure_qdisc(if_measure, args.bw, args.queue, burst_bytes=burst)
            time.sleep(0.2)
            rate, backlog_stats = blast(net, secs=args.blast_secs)
            pct = 100.0 * rate / args.bw
            row = {
                "burst_bytes": burst,
                "rate_mbps": rate,
                "pct": pct,
                **backlog_stats,
            }
            burst_rows.append(row)
            print(
                "  %-10d %-14.3f %-10.1f%s"
                % (burst, rate, pct, "  <-- OK" if pct >= 98 else "")
            )
        report["checks"]["burst_sweep"] = burst_rows
        chosen = next((row["burst_bytes"] for row in burst_rows if row["pct"] >= 98.0), None)
        print("\n  ==> BURST DA CHON: %s B   (ghi amendment neu != 1600)" % chosen)
        report["checks"]["burst_chosen"] = chosen

        hr("BUOC 6b -- RAW TC SAU QUA TAI: overlimits PHAI tang")
        if chosen is not None:
            change_measure_qdisc(if_measure, args.bw, args.queue, burst_bytes=chosen)
            time.sleep(0.2)
            proof_rate, proof_backlog = blast(net, secs=args.blast_secs)
            print(
                "  Da doi ve burst chot %d B va bom qua tai: rate=%.3f Mbps, "
                "p95_backlog=%d B, peak_backlog=%d B"
                % (
                    chosen,
                    proof_rate,
                    proof_backlog["p95_backlog_bytes"],
                    proof_backlog["peak_backlog_bytes"],
                )
            )
        post_burst_qdisc = show_qdisc(if_measure).strip()
        post_burst_class = show_class(if_measure).strip()
        print("\n>>> CHIEU DO sau quet burst")
        print(post_burst_qdisc)
        print("\n--- class ---")
        print(post_burst_class)
        report["checks"]["raw_after_burst"] = {
            "proof_rate_mbps": proof_rate if chosen is not None else None,
            "proof_backlog": proof_backlog if chosen is not None else None,
            "measure_qdisc": post_burst_qdisc,
            "measure_class": post_burst_class,
        }

        hr("BUOC 7 -- * DOI CHUNG DUONG (V-L4): giam buffer thi tran PHAI giam")
        print("  Neu doi buffer ma khong thay doi gi -> buffer KHONG duoc ap dung")
        print("  -> chinh la loi ban da mac o topology_v7. DUNG LAI neu xay ra.\n")
        pos_rows: List[Dict[str, Any]] = []
        for queue_pkts in (args.queue, 5):
            change_measure_qdisc(if_measure, args.bw, queue_pkts, burst_bytes=chosen or 1600)
            time.sleep(0.2)
            rate, backlog_stats = blast(net, secs=args.blast_secs)
            backlog = int(backlog_stats["p95_backlog_bytes"])
            ceil_ms = queue_ceiling_ms(queue_pkts, args.bw)
            backlog_ms = backlog * 8.0 / (args.bw * 1e6) * 1000.0
            pos_rows.append(
                {
                    "queue_pkts": queue_pkts,
                    "rate_mbps": rate,
                    "ceiling_ms": ceil_ms,
                    "backlog_bytes": backlog,
                    "backlog_ms": backlog_ms,
                    "backlog_stats": backlog_stats,
                }
            )
            print(
                "  q=%2d goi  tran ly thuyet=%6.2f ms  backlog p95=%6d B = %6.2f ms  (%.0f%% tran)"
                % (
                    queue_pkts,
                    ceil_ms,
                    backlog,
                    backlog_ms,
                    100.0 * backlog_ms / ceil_ms if ceil_ms else 0,
                )
            )
        ratio = pos_rows[1]["backlog_ms"] / max(pos_rows[0]["backlog_ms"], 1e-9)
        want = 5.0 / args.queue
        ok = abs(ratio - want) / want < 0.25
        print(
            "\n  ty le backlog(q=5)/backlog(q=%d) = %.3f   mong doi %.3f   %s"
            % (args.queue, ratio, want, "PASS" if ok else "* FAIL -> DUNG LAI")
        )
        report["checks"]["positive_control"] = {
            "rows": pos_rows,
            "ratio": ratio,
            "expected": want,
            "pass": bool(ok),
        }

        change_measure_qdisc(if_measure, args.bw, args.queue, burst_bytes=chosen or 1600)

    finally:
        try:
            net.get("h2").cmd("pkill -f /tmp/dt4n_sink.py 2>/dev/null")
        except Exception:
            pass
        net.stop()

    os.makedirs(args.out_dir, exist_ok=True)
    path = os.path.join(args.out_dir, "l1_infra_%s.json" % time.strftime("%m%d_%H%M"))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    print("\nGhi -> %s" % path)


if __name__ == "__main__":
    main()
