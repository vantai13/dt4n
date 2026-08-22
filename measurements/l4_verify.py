#!/usr/bin/env python3
"""Lesson L.4 -- validate the load generator on the live Mininet topology."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

from mininet.link import Link
from mininet.net import Mininet
from mininet.node import OVSBridge

from measurements.owd_analyze import analyze
from mininet.load_spec import DESIGN_CA, MODES
from mininet.topology_split_qdisc import (
    SplitQdiscTopo,
    intf_toward,
    setup_measure_qdisc,
    setup_return_qdisc,
)


PORT = 5555
RAW = "results/RAW/phase-L/raw"
LG = "python3 -m measurements.load_gen"
PB = "python3 -m measurements.owd_probe"


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def one_point(
    net: Mininet,
    tag: str,
    bw: float,
    rho: float,
    mode: str,
    seed: int,
    dur: float = 40.0,
    warmup: float = 10.0,
    probe_pps: float = 20.0,
) -> Dict[str, Any]:
    h1, h2 = net.get("h1"), net.get("h2")
    cwd = os.getcwd()
    prefix = "%s/%s" % (RAW, tag)

    h1.cmd("pkill -f 'measurements.load_gen' 2>/dev/null")
    h2.cmd("pkill -f 'measurements.owd_probe' 2>/dev/null")
    time.sleep(0.2)

    h2.cmd(
        "cd %s && %s recv --port %d --duration %g --out-prefix %s >/dev/null 2>&1 &"
        % (cwd, PB, PORT, dur + 6.0, prefix)
    )
    time.sleep(0.8)
    h1.cmd(
        "cd %s && %s --dst 10.0.0.2 --port %d --bw %g --rho %g --mode %s "
        "--duration %g --seed %d --run-id %d --probe-pps %g --out-prefix %s "
        ">/dev/null 2>&1"
        % (cwd, LG, PORT, bw, rho, mode, dur, seed, seed, probe_pps, prefix)
    )
    time.sleep(6.5)

    tx = _load_json(prefix + "_tx.meta.json")
    rx = _load_json(prefix + "_rx.meta.json")
    bg = analyze(prefix + "_bg.bin", prefix + "_bgtx.bin", warmup_s=warmup)
    probe = None
    if probe_pps > 0 and os.path.getsize(prefix + "_probe.bin"):
        probe = analyze(prefix + "_probe.bin", prefix + "_prtx.bin", warmup_s=warmup)
    return {"tx": tx, "rx": rx, "bg": bg, "probe": probe}


def _pass_vl4(mode: str, row: Dict[str, Any]) -> bool:
    target = DESIGN_CA[mode]
    if target is not None:
        if target == 0.0:
            if abs(row["ca_schedule"]) > 1e-12 or row["ca_actual"] > 0.10:
                return False
        elif abs(row["ca_actual"] - target) / target > 0.10:
            return False
    return (
        abs(row["rate_ratio"] - 1.0) < 0.001
        and abs(row["rho_actual"] - 0.90) < 0.002
        and row["socket_drops"] == 0
        and row["n_foreign_packets"] == 0
        and row["n_late_ratio"] < 0.001
        and row["max_late_ms"] < 50.0
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
        setup_return_qdisc(intf_toward(s2, "s1"), 3.0)
        setup_measure_qdisc(if_measure, 6.0, 13)

        print("\n=== V-L3  DOI CHUNG AM (rho thap) ===")
        neg = one_point(net, "%s_l4_neg" % stamp, 6.0, 0.02, "cbr", 1)
        neg_row = {
            "mean_ms": neg["bg"]["owd_ms"]["mean"],
            "p99_ms": neg["bg"]["owd_ms"]["p99"],
            "loss": neg["bg"]["loss_rate"],
            "socket_drops": neg["rx"]["socket_drops_delta"],
            "n_foreign_packets": neg["rx"]["n_foreign_packets"],
            "pass": bool(
                neg["bg"]["loss_rate"] == 0
                and neg["rx"]["socket_drops_delta"] == 0
                and neg["rx"]["n_foreign_packets"] == 0
            ),
        }
        print(
            "   q_delay mean=%.4f ms  p99=%.4f ms  loss=%.5f  %s"
            % (
                neg_row["mean_ms"],
                neg_row["p99_ms"],
                neg_row["loss"],
                "PASS" if neg_row["pass"] else "* FAIL",
            )
        )
        report["checks"]["V-L3"] = neg_row

        print("\n=== V-L4  BON CHE DO tai rho = 0.90, bw = 6, q = 13 ===")
        print(
            "   %-9s %-9s %-9s %-9s %-9s %-9s %-8s %-6s"
            % ("mode", "c_a dat", "c_a do", "rate%", "rho", "q_ms", "loss", "pass")
        )
        rows: Dict[str, Dict[str, Any]] = {}
        for mode in MODES:
            point = one_point(net, "%s_l4_%s" % (stamp, mode), 6.0, 0.90, mode, 11)
            ca = point["tx"]["c_a"]
            counts = point["tx"]["counts"]
            sent_total = max(counts["n_bg_sent"] + counts["n_probe_sent"], 1)
            row = {
                "ca_design": DESIGN_CA[mode],
                "ca_schedule": ca["schedule_bg"],
                "ca_actual": ca["actual_bg"],
                "ca_aggregate": ca["aggregate_schedule"],
                "rate_ratio": point["tx"]["rates"]["rate_ratio"],
                "rho_actual": point["tx"]["rates"]["rho_actual"],
                "q_mean_ms": point["bg"]["owd_ms"]["mean"],
                "q_p95_ms": point["bg"]["owd_ms"]["p95"],
                "loss": point["bg"]["loss_rate"],
                "probe_mean_ms": point["probe"]["owd_ms"]["mean"] if point["probe"] else None,
                "n_late": counts["n_late"],
                "n_late_ratio": counts["n_late"] / sent_total,
                "max_late_ms": counts["max_late_ms"],
                "socket_drops": point["rx"]["socket_drops_delta"],
                "n_foreign_packets": point["rx"]["n_foreign_packets"],
                "steady_state_spread_ms": point["bg"]["steady_state"]["spread_ms"],
            }
            row["pass"] = bool(_pass_vl4(mode, row))
            rows[mode] = row
            print(
                "   %-9s %-9s %-9.4f %-9.4f %-9.4f %-9.3f %-8.4f %-6s"
                % (
                    mode,
                    str(DESIGN_CA[mode]),
                    row["ca_actual"],
                    row["rate_ratio"],
                    row["rho_actual"],
                    row["q_mean_ms"],
                    row["loss"],
                    "PASS" if row["pass"] else "FAIL",
                )
            )
        smoke = rows["cbr"]["q_mean_ms"] < rows["poisson"]["q_mean_ms"] < rows["h2"]["q_mean_ms"]
        report["checks"]["V-L4"] = {"rows": rows, "smoke_order_pass": bool(smoke)}

        print("\n   THU TU (SMOKE):")
        print(
            "   cbr %.3f < poisson %.3f < h2 %.3f -> %s"
            % (
                rows["cbr"]["q_mean_ms"],
                rows["poisson"]["q_mean_ms"],
                rows["h2"]["q_mean_ms"],
                "PASS" if smoke else "* DIEU TRA",
            )
        )

        print("\n   THIEN LECH PASTA (goi nen - probe):")
        for mode in MODES:
            row = rows[mode]
            if row["probe_mean_ms"] is not None:
                print(
                    "     %-9s pkt=%.3f  probe=%.3f  delta=%+.3f ms"
                    % (
                        mode,
                        row["q_mean_ms"],
                        row["probe_mean_ms"],
                        row["q_mean_ms"] - row["probe_mean_ms"],
                    )
                )

        print("\n=== V-L7  DO XAM LAN CUA PROBE (poisson, rho=0.90) ===")
        print("   mo phong: 20 goi/s tang delay khoang +0.4%; gate live <= 2%")
        sweep = []
        for pps in (0.0, 10.0, 20.0, 40.0):
            sweep_dur = 80.0 if pps <= 20.0 else 40.0
            point = one_point(
                net,
                "%s_l4_pr%g" % (stamp, pps),
                6.0,
                0.90,
                "poisson",
                11,
                dur=sweep_dur,
                probe_pps=pps,
            )
            q_mean = point["bg"]["owd_ms"]["mean"]
            item = {
                "probe_pps": pps,
                "duration_s": sweep_dur,
                "q_mean_ms": q_mean,
                "loss": point["bg"]["loss_rate"],
                "rate_ratio": point["tx"]["rates"]["rate_ratio"],
                "rho_actual": point["tx"]["rates"]["rho_actual"],
                "socket_drops": point["rx"]["socket_drops_delta"],
            }
            sweep.append(item)
            print("   probe=%-5.0f goi/s  q_delay=%.3f ms" % (pps, q_mean))
        base = sweep[0]["q_mean_ms"]
        dev_le20 = max(abs(item["q_mean_ms"] - base) / base for item in sweep[:3])
        report["checks"]["V-L7"] = {
            "sweep": sweep,
            "max_dev_le20": dev_le20,
            "pass": bool(dev_le20 < 0.02),
        }
        print(
            "   lech toi da tai <=20 goi/s: %.2f%%  %s"
            % (dev_le20 * 100.0, "PASS" if dev_le20 < 0.02 else "* FAIL")
        )
    finally:
        try:
            net.get("h1").cmd("pkill -f 'measurements.load_gen' 2>/dev/null")
            net.get("h2").cmd("pkill -f 'measurements.owd_probe' 2>/dev/null")
        except Exception:
            pass
        net.stop()

    report["pass"] = bool(
        report["checks"]["V-L3"]["pass"]
        and all(row["pass"] for row in report["checks"]["V-L4"]["rows"].values())
        and report["checks"]["V-L4"]["smoke_order_pass"]
        and report["checks"]["V-L7"]["pass"]
    )
    os.makedirs("results/SUPERSEDED/phase-L", exist_ok=True)
    path = "results/SUPERSEDED/phase-L/l4_loadgen_%s.json" % stamp
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    print("\nGhi -> %s" % path)


if __name__ == "__main__":
    main()
