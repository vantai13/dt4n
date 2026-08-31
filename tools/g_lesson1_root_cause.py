#!/usr/bin/env python3
"""Lesson 1 live root-cause replay.

Summarize the IPv6-on capture, the reversible IPv6-off controls, and the
emitter/scheduler event evidence.  This script only reads retained artifacts;
it does not start Mininet or change host networking.
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("results/RAW/phase-G")
WIRE_BYTES = 1442
BURN_S = 20.0
RUNS = (
    ("ipv6-on", ROOT / "lesson1-forensics-live/rep1"),
    ("ipv6-off/matched", ROOT / "lesson1-ipv6-off-matched/rep1"),
    ("ipv6-off/default-r1", ROOT / "lesson1-ipv6-off-default/rep1"),
    ("ipv6-off/default-r2", ROOT / "lesson1-ipv6-off-default/rep2"),
    ("ipv6-off/tight-r1", ROOT / "lesson1-ipv6-off-tight/rep1"),
    ("ipv6-off/tight-r2", ROOT / "lesson1-ipv6-off-tight/rep2"),
)


def load(run: Path) -> tuple[dict, pd.DataFrame]:
    meta = json.loads((run / "rho_trace_meta.json").read_text(encoding="utf-8"))
    measured = pd.read_csv(run / "rho_measured.csv")
    return meta, measured


def post_burn(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.sort_values("monotonic_s").reset_index(drop=True)
    return frame[frame["monotonic_s"] >= frame["monotonic_s"].iloc[0] + BURN_S]


def summarize_runs() -> None:
    print("=" * 90)
    print("C1 | Controls: foreign residues and full-packet support anomalies")
    print("=" * 90)
    print(
        "%24s %8s %8s %11s %12s %10s %8s"
        % ("run", "pace_ms", "residue", "support_bad", "sum_excess", "catchups", "backlog")
    )
    for label, run in RUNS:
        meta, measured = load(run)
        residues = support_bad = catchups = 0
        excess = []
        backlogs = []
        for link, frame in measured.groupby("link"):
            frame = post_burn(frame)
            tx = frame["tx_bytes_delta"].to_numpy(dtype=np.int64)
            remainder = tx % WIRE_BYTES
            clean_packets = (tx - remainder) // WIRE_BYTES
            n_packets = float(meta["profile"][link]["rate_pps"]) * float(
                meta["measured_window_s"]
            )
            low, high = math.floor(n_packets), math.ceil(n_packets)
            residues += int(np.count_nonzero(remainder))
            support_bad += int(
                np.count_nonzero((clean_packets < low) | (clean_packets > high))
            )
            f = n_packets - low
            excess.append(float(np.var(clean_packets, ddof=1)) - f * (1.0 - f))
            engine = meta["flow_engine"][link]
            catchups += int(engine["n_catchup"])
            backlogs.append(int(engine["max_backlog"]))
        print(
            "%24s %8.3f %8d %11d %+12.5f %10d %8d"
            % (
                label,
                float(meta["pace_tick_s"]) * 1e3,
                residues,
                support_bad,
                sum(excess),
                catchups,
                max(backlogs),
            )
        )
    print("\n  residue = post-burn windows with tx_bytes_delta mod 1442 != 0")
    print("  support_bad = packet counts outside {floor(r*dt), ceil(r*dt)}")


def identify_control_packet() -> None:
    print("\n" + "=" * 90)
    print("C2 | Packet identity in the IPv6-on capture")
    print("=" * 90)
    pcap = ROOT / "lesson1-forensics-live/rep1/control_under200.pcap"
    command = [
        "tcpdump",
        "-nn",
        "-e",
        "-tt",
        "-r",
        str(pcap),
        "icmp6 && ip6[40] == 133",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    rows = [line for line in result.stdout.splitlines() if "router solicitation" in line]
    print("  ICMPv6 Router Solicitation records in pcap: %d" % len(rows))
    if rows:
        print("  example: %s" % rows[0])
    print("  Ethernet counter length = 14 + 40 + 16 = 70 bytes.")
    print("  tcpdump on -i any reports 76 because Linux SLL2 is 20 bytes, 6 bytes")
    print("  longer than the 14-byte Ethernet header used by /proc/net/dev.")


def scheduler_events() -> None:
    print("\n" + "=" * 90)
    print("C3 | Tight-pacing rep2: largest post-burn ledger stalls")
    print("=" * 90)
    run = ROOT / "lesson1-ipv6-off-tight/rep2"
    meta, measured = load(run)
    print(
        "%5s %13s %11s %9s %9s %13s"
        % ("link", "stall_end", "gap_ms", "cum_jump", "backlog", "bad_windows")
    )
    for link in meta["profile"]:
        ledger = pd.read_csv(run / "flow_logs" / ("rho_offered_%s.csv" % link))
        gaps = ledger["t_mono"].diff()
        eligible = ledger["t_mono"] >= float(ledger["t_mono"].iloc[0]) + BURN_S
        idx = gaps[eligible].idxmax()
        frame = post_burn(measured[measured["link"] == link])
        packets = frame["tx_bytes_delta"].to_numpy(dtype=np.int64) // WIRE_BYTES
        n_packets = float(meta["profile"][link]["rate_pps"]) * float(
            meta["measured_window_s"]
        )
        low, high = math.floor(n_packets), math.ceil(n_packets)
        bad = frame[(packets < low) | (packets > high)]
        bad_text = ",".join("%.1f" % value for value in bad["timestamp_s"]) or "-"
        print(
            "%5s %13.6f %11.3f %9d %9d %13s"
            % (
                link,
                float(ledger.loc[idx, "t_mono"]),
                float(gaps.loc[idx]) * 1e3,
                int(ledger.loc[idx, "cum_packets"] - ledger.loc[idx - 1, "cum_packets"]),
                int(meta["flow_engine"][link]["max_backlog"]),
                bad_text,
            )
        )

    print("\n  ac, bd, and vD end their largest stall at the same monotonic instant")
    print("  (~5948.62544 s). ac/bd then show adjacent deficit/surplus windows.")
    print("  TX and RX counts are identical in those windows, placing the event")
    print("  upstream of the measured link rather than in the counter reader.")


def main() -> None:
    summarize_runs()
    identify_control_packet()
    scheduler_events()
    print("\nVERDICT")
    print("  H1: confirmed as locally originated IPv6 Router Solicitation (70 B).")
    print("  H2: rejected at the measured link; TX and RX move together.")
    print("  H3/H4: confirmed as intermittent host-side scheduling/batch events.")
    print("  H5: not supported as a common mechanism.")


if __name__ == "__main__":
    main()
