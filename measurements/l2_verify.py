#!/usr/bin/env python3
"""Lesson L.2 -- validate the raw OWD measurement chain.

Checks:
  V-L0   software noise floor, no measured-direction qdisc, no background load
  V-L2   zero-load HTB equals the measured floor at 4/6/8 Mbps
  V-L2b  token-bucket staircase for 8 back-to-back 1512 B frames
"""

from __future__ import annotations

import json
import math
import os
import struct
import time
from statistics import median
from typing import Any, Dict, List, Tuple

from mininet.link import Link
from mininet.net import Mininet
from mininet.node import OVSBridge

from mininet.topology_split_qdisc import (
    DEFAULT_BURST_BYTES,
    FRAME_BYTES_1470,
    SplitQdiscTopo,
    fit_staircase,
    intf_toward,
    setup_measure_qdisc,
    setup_return_qdisc,
    sh,
)


REC_RX = struct.Struct("<Qdd")
PROBE_PORT = 5555
RAW = "results/phase-L/raw"
PY = "python3 -m measurements.owd_probe"
STAIR_REPS = 5


def mean(values: List[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def sd(values: List[float]) -> float:
    if len(values) <= 1:
        return float("nan")
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))


def owd_ms(path: str) -> Tuple[List[int], List[float]]:
    raw = open(path, "rb").read()
    if len(raw) % REC_RX.size:
        raise ValueError("%s: raw size not divisible by %d" % (path, REC_RX.size))
    n = len(raw) // REC_RX.size
    recs = [REC_RX.unpack_from(raw, i * REC_RX.size) for i in range(n)]
    recs.sort(key=lambda row: row[0])
    return ([int(row[0]) for row in recs], [(row[2] - row[1]) * 1e3 for row in recs])


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_pair(
    net: Mininet,
    tag: str,
    mode: str,
    rate: float,
    size: int,
    dur: float,
    burst_n: int = 0,
    run_id: int = 1,
) -> Tuple[str, str, Dict[str, Any], Dict[str, Any]]:
    h1, h2 = net.get("h1"), net.get("h2")
    cwd = os.getcwd()
    rx = "%s/%s_rx.bin" % (RAW, tag)
    tx = "%s/%s_tx.bin" % (RAW, tag)
    rx_log = "/tmp/%s_rx.log" % tag
    tx_log = "/tmp/%s_tx.log" % tag

    h1.cmd("pkill -f 'measurements.owd_probe' 2>/dev/null")
    h2.cmd("pkill -f 'measurements.owd_probe' 2>/dev/null")
    time.sleep(0.2)

    recv_duration = float(dur) + 3.0
    h2.cmd(
        "cd %s && %s recv --port %d --duration %g --out %s >%s 2>&1 &"
        % (cwd, PY, PROBE_PORT, recv_duration, rx, rx_log)
    )
    time.sleep(0.8)
    h1.cmd(
        "cd %s && %s send --dst 10.0.0.2 --port %d --mode %s --rate %g "
        "--size %d --duration %g --burst-n %d --run-id %d --out %s >%s 2>&1"
        % (cwd, PY, PROBE_PORT, mode, rate, size, dur, burst_n, run_id, tx, tx_log)
    )
    time.sleep(recv_duration + 0.6)

    rx_meta = load_json(rx + ".meta.json")
    tx_meta = load_json(tx + ".meta.json")
    return rx, tx, rx_meta, tx_meta


def floor_stats(values: List[float]) -> Dict[str, float]:
    sorted_values = sorted(values)
    n = len(values)
    return {
        "n": n,
        "mean_ms": mean(values),
        "sd_ms": sd(values),
        "p50_ms": float(sorted_values[n // 2]),
        "p99_ms": float(sorted_values[int(0.99 * (n - 1))]),
        "max_ms": float(sorted_values[-1]),
    }


def meta_ok(rx_meta: Dict[str, Any]) -> bool:
    return (
        int(rx_meta.get("socket_drops_delta", -1)) == 0
        and int(rx_meta.get("n_foreign_packets", -1)) == 0
    )


def main() -> None:
    os.makedirs(RAW, exist_ok=True)
    stamp = time.strftime("%m%d_%H%M")
    report: Dict[str, Any] = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "raw_prefix": stamp,
        "checks": {},
    }

    net = Mininet(topo=SplitQdiscTopo(), link=Link, switch=OVSBridge, controller=None)
    net.start()
    try:
        s1, s2 = net.get("s1"), net.get("s2")
        if_measure = intf_toward(s1, "s2")
        if_return = intf_toward(s2, "s1")
        setup_return_qdisc(if_return, 3.0)

        print("\n=== V-L0  SAN NHIEU (khong qdisc, khong tai nen) ===")
        sh("tc qdisc del dev %s root 2>/dev/null" % if_measure)
        rx, tx, rx_meta, tx_meta = run_pair(
            net,
            "%s_vl0_floor" % stamp,
            "poisson",
            100.0,
            64,
            20.0,
            run_id=100,
        )
        _seq, owd = owd_ms(rx)
        floor = floor_stats(owd)
        for key, val in floor.items():
            print("   %-10s %s" % (key, val))
        ok0 = floor["sd_ms"] <= 0.2 and meta_ok(rx_meta)
        print("   socket_drops_delta %s" % rx_meta["socket_drops_delta"])
        print("   n_foreign_packets  %s" % rx_meta["n_foreign_packets"])
        print("   V-L0 %s  (nguong SD <= 0.2 ms)" % ("PASS" if ok0 else "* FAIL"))
        report["checks"]["V-L0_floor"] = {
            **floor,
            "pass": bool(ok0),
            "rx": rx,
            "tx": tx,
            "rx_meta": rx_meta,
            "tx_meta": tx_meta,
        }

        for bw, queue_pkts in ((8.0, 18), (6.0, 13), (4.0, 10)):
            print("\n=== bw=%g Mbps, q=%d ===" % (bw, queue_pkts))
            setup_measure_qdisc(if_measure, bw, queue_pkts)
            C_bytes_s = bw * 1e6 / 8.0

            rx, tx, rx_meta, tx_meta = run_pair(
                net,
                "%s_vl2_bw%g" % (stamp, bw),
                "poisson",
                100.0,
                64,
                15.0,
                run_id=int(200 + bw),
            )
            _seq, owd = owd_ms(rx)
            owd_mean = mean(owd)
            owd_sd = sd(owd)
            delta = abs(owd_mean - floor["mean_ms"])
            ok2 = delta < 0.3 and meta_ok(rx_meta)
            print(
                "  V-L2  tai 0 co HTB : mean=%.4f ms  sd=%.4f  (san=%.4f)"
                % (owd_mean, owd_sd, floor["mean_ms"])
            )
            print(
                "        |lech san| = %.4f ms  %s (nguong 0.3 ms)"
                % (delta, "PASS" if ok2 else "* FAIL")
            )
            print(
                "        socket_drops_delta=%s, n_foreign_packets=%s"
                % (rx_meta["socket_drops_delta"], rx_meta["n_foreign_packets"])
            )
            report["checks"].setdefault("V-L2", {})["bw%g" % bw] = {
                "mean_ms": owd_mean,
                "sd_ms": owd_sd,
                "delta_floor_ms": delta,
                "pass": bool(ok2),
                "rx": rx,
                "tx": tx,
                "rx_meta": rx_meta,
                "tx_meta": tx_meta,
            }

            print("  V-L2b BAC THANG (8 goi 1512 B lien tiep):")
            base = floor["mean_ms"]
            pred = [0.0, 0.0] + [
                ((k - 1) * FRAME_BYTES_1470 - DEFAULT_BURST_BYTES) / C_bytes_s * 1e3
                for k in range(3, 9)
            ]
            reps = []
            meta_pass = True
            for rep_i in range(STAIR_REPS):
                rx, tx, rx_meta, tx_meta = run_pair(
                    net,
                    "%s_vl2b_bw%g_r%d" % (stamp, bw, rep_i),
                    "burst",
                    0.0,
                    1470,
                    0.0,
                    burst_n=8,
                    run_id=int(3000 + bw * 10 + rep_i),
                )
                seq, owd = owd_ms(rx)
                measured_rep = [float(x - base) for x in owd[:8]]
                reps.append(
                    {
                        "rx": rx,
                        "tx": tx,
                        "seq": [int(x) for x in seq[:8]],
                        "measured_ms": measured_rep,
                        "rx_meta": rx_meta,
                        "tx_meta": tx_meta,
                    }
                )
                meta_pass = meta_pass and meta_ok(rx_meta) and len(measured_rep) >= 8

            measured = [
                float(median(rep["measured_ms"][idx] for rep in reps if len(rep["measured_ms"]) > idx))
                for idx in range(8)
            ]
            print("     k  median_do(ms)  du_doan  |lech|")
            errs = []
            for idx, meas in enumerate(measured):
                err = abs(meas - pred[idx])
                errs.append(err)
                print(
                    "     %d  %12.3f  %7.3f  %6.3f %s"
                    % (
                        idx + 1,
                        meas,
                        pred[idx],
                        err,
                        "" if err < 0.3 else "  <-- LECH",
                    )
                )
            okb = meta_pass and max(errs[2:] if len(errs) >= 3 else errs) < 0.3
            fit = fit_staircase(measured)
            fit_ok = (
                abs(fit["C_mbps"] - bw) / bw < 0.01
                and abs(fit["burst_bytes"] - DEFAULT_BURST_BYTES) / DEFAULT_BURST_BYTES < 0.10
                and fit["r2"] > 0.999
            )
            total_socket_drops = sum(int(rep["rx_meta"]["socket_drops_delta"]) for rep in reps)
            total_foreign = sum(int(rep["rx_meta"]["n_foreign_packets"]) for rep in reps)
            print(
                "     reps=%d, socket_drops_delta_total=%s, n_foreign_packets_total=%s"
                % (STAIR_REPS, total_socket_drops, total_foreign)
            )
            print(
                "     fit: C=%.4f Mbps, burst=%.1f B, R2=%.6f  %s"
                % (fit["C_mbps"], fit["burst_bytes"], fit["r2"], "PASS" if fit_ok else "* FAIL")
            )
            print(
                "     V-L2b %s  (|err| < 0.3 ms, |dC|<1%%, |dB|<10%%, R2>0.999)"
                % ("PASS" if (okb and fit_ok) else "* FAIL")
            )
            report["checks"].setdefault("V-L2b", {})["bw%g" % bw] = {
                "measured_ms": measured,
                "predicted_ms": pred,
                "reps": reps,
                "max_abs_err_ms_k_ge_3": float(max(errs[2:])) if len(errs) >= 3 else None,
                "fit": fit,
                "fit_pass": bool(fit_ok),
                "n_reps": STAIR_REPS,
                "pass": bool(okb and fit_ok),
            }
    finally:
        try:
            net.get("h1").cmd("pkill -f 'measurements.owd_probe' 2>/dev/null")
            net.get("h2").cmd("pkill -f 'measurements.owd_probe' 2>/dev/null")
        except Exception:
            pass
        net.stop()

    os.makedirs("results/phase-L", exist_ok=True)
    path = "results/phase-L/l2_probe_%s.json" % stamp
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    print("\nGhi -> %s" % path)


if __name__ == "__main__":
    main()
