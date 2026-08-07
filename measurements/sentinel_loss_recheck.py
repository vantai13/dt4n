#!/usr/bin/env python3
"""Phase 20R.6 -- re-run the Phase L sentinel cell and test for drift on LOSS.

Phase L's sentinel guarded ``q_mean_ms`` only, so machine/kernel drift on the
``loss`` column has never been tested. ``A' - A`` subtracts two campaigns months
apart, so an untested drift term sits inside every topology-transfer number:

    A' - A = (topology transfer) + (table interpolation) + (temporal drift)

This module re-measures the sentinel cell on today's machine with the Phase L
runner (``l6_campaign.measure``) and the Phase L topology (``SplitQdiscTopo``),
then reports ``z = (today - phase_L) / sd_phase_L`` for both loss and delay. The
reference is read from the Phase L campaign state, not hardcoded.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
import sys
import time
from typing import Any, Dict, List, Mapping, Optional, Sequence

import pandas as pd

from measurements import l6_campaign as L


# The Phase L sentinel cell, verbatim. Changing any of these voids the contrast.
SENTINEL = {"mode": "h2", "bw": 6.0, "q": 13, "rho": 0.90, "seed": 999, "probe_pps": 20.0}
CAMPAIGN_STATE = "results/phase-20R/campaign_state.json"
OUT = "results/phase-20R/sentinel_loss_recheck.json"
RAW = "results/phase-20R/raw_sentinel_recheck"
N_REPS = 5
Z_ALERT = 3.0
IDX_BASE = 90000


def git_hash() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return "unknown"


def reference_stats(campaign_state: str = CAMPAIGN_STATE, cell: Mapping[str, Any] = SENTINEL) -> Dict[str, Any]:
    """Phase L sentinel statistics, gate-clean rows only."""
    with open(campaign_state, "r", encoding="utf-8") as f:
        rows = json.load(f)["rows"]
    df = pd.DataFrame(rows)
    df = df[df["gate_fail"].apply(lambda x: len(x) == 0)]
    sel = df[
        (df["mode"] == cell["mode"])
        & (df["bw"] == float(cell["bw"]))
        & (df["q"] == int(cell["q"]))
        & (df["rho"] == float(cell["rho"]))
        & (df["seed"] == int(cell["seed"]))
    ]
    if sel.empty:
        raise SystemExit("no gate-clean sentinel rows in %s" % campaign_state)
    out: Dict[str, Any] = {
        "n_ref": int(len(sel)),
        "source": campaign_state,
        "wall_utc_min": str(sel["wall_utc"].min()),
        "wall_utc_max": str(sel["wall_utc"].max()),
        "git_hash": sorted({str(h) for h in sel["git_hash"]}),
    }
    for field in ("loss", "q_mean_ms"):
        vals = sel[field].astype(float)
        out[field] = {
            "mean": float(vals.mean()),
            "sd": float(vals.std(ddof=1)),
            "se": float(vals.std(ddof=1) / math.sqrt(len(vals))),
        }
    return out


def z_score(today: Sequence[float], ref: Mapping[str, Any]) -> Dict[str, Any]:
    """Two-sample drift test between today's replicates and the Phase L sentinel.

    ``z_welch`` is the statistic that decides drift: it compares the two means
    using the standard error of each. ``z_mean`` is reported alongside for
    continuity with Phase L's single-run sentinel rule, but it is deliberately
    NOT the trigger -- dividing a mean-of-n by the sd of a single run understates
    the significance of a shift by roughly sqrt(n).
    """
    vals = [float(v) for v in today]
    mean = statistics.fmean(vals)
    sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
    se_today = sd / math.sqrt(len(vals)) if len(vals) > 1 else 0.0
    ref_sd = float(ref["sd"])
    ref_se = float(ref["se"])
    se_pooled = math.sqrt(se_today ** 2 + ref_se ** 2)
    return {
        "n": len(vals),
        "mean": mean,
        "sd": sd,
        "se": se_today,
        "ref_mean": float(ref["mean"]),
        "ref_sd": ref_sd,
        "delta": mean - float(ref["mean"]),
        "z_mean": (mean - float(ref["mean"])) / ref_sd if ref_sd > 0 else float("nan"),
        "z_welch": (mean - float(ref["mean"])) / se_pooled if se_pooled > 0 else float("nan"),
        "drift": bool(se_pooled > 0 and abs(mean - float(ref["mean"])) / se_pooled > Z_ALERT),
    }


def run_live(reps: int = N_REPS, raw_dir: str = RAW) -> List[Dict[str, Any]]:
    from mininet.link import Link
    from mininet.net import Mininet
    from mininet.node import OVSBridge

    from measurements import additivity_live as AL
    from mininet.topology_split_qdisc import (
        intf_toward,
        read_direct_packets,
        setup_and_verify_measure_qdisc,
        setup_return_qdisc,
        SplitQdiscTopo,
    )

    os.makedirs(raw_dir, exist_ok=True)
    saved_sysctl = AL.disable_ipv6_on_new_links()
    rows: List[Dict[str, Any]] = []
    setup_log: List[Dict[str, Any]] = []
    net = Mininet(topo=SplitQdiscTopo(), link=Link, switch=OVSBridge, controller=None)
    net.start()
    try:
        s1, s2 = net.get("s1"), net.get("s2")
        if_measure = intf_toward(s1, "s2")
        setup_return_qdisc(intf_toward(s2, "s1"), L.DELAY_MS)
        proof = setup_and_verify_measure_qdisc(
            if_measure, float(SENTINEL["bw"]), int(SENTINEL["q"]), log_sink=setup_log
        )
        for k in range(1, int(reps) + 1):
            point = dict(SENTINEL, idx=IDX_BASE + k, block="SENT_RECHECK")
            point["pid"] = L._pid(point, point["idx"])
            before = read_direct_packets(if_measure)
            row = L.measure(net, point)
            after = read_direct_packets(if_measure)
            # V-L1g-run: a direct packet inside the window invalidates the point.
            row["direct_packets_delta"] = int(after - before)
            row["vl1g_run_pass"] = bool(after == before)
            row["gate_fail"] = L.gate(row)
            rows.append(row)
            print(
                "[%d/%d] loss=%.6f  q_mean=%8.4f  rho_actual=%.6f  direct_delta=%d  gate_fail=%s"
                % (
                    k,
                    reps,
                    row["loss"],
                    row["q_mean_ms"],
                    row["rho_actual"],
                    row["direct_packets_delta"],
                    row["gate_fail"] or "[]",
                )
            )
    finally:
        net.stop()
        AL.restore_sysctl(saved_sysctl)
    for row in rows:
        row["qdisc_proof"] = {k: proof[k] for k in ("bfifo_limit_bytes", "ceiling_ms", "install_attempts")}
        row["qdisc_setup_log"] = list(setup_log)
    return rows


def summarize(rows: Sequence[Mapping[str, Any]], ref: Mapping[str, Any]) -> Dict[str, Any]:
    clean = [row for row in rows if not row.get("gate_fail") and row.get("vl1g_run_pass", True)]
    summary: Dict[str, Any] = {
        "n_run": len(rows),
        "n_clean": len(clean),
        "max_direct_packets_delta": max((int(r.get("direct_packets_delta", 0)) for r in rows), default=0),
        "z_alert": Z_ALERT,
    }
    if not clean:
        summary.update({"evaluated": False, "reason": "no gate-clean replicates"})
        return summary
    summary["evaluated"] = True
    for field in ("loss", "q_mean_ms"):
        summary[field] = z_score([row[field] for row in clean], ref[field])
    drift_fields = [f for f in ("loss", "q_mean_ms") if summary[f]["drift"]]
    summary["drift_fields"] = drift_fields
    summary["drift_detected"] = bool(drift_fields)
    # The loss column is what this recheck exists for: it is the term that enters
    # A' - A through w_loss and the one Phase L's sentinel never guarded.
    summary["loss_drift"] = bool(summary["loss"]["drift"])
    summary["verdict"] = "DRIFT:" + ",".join(drift_fields) if drift_fields else "STABLE"
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reps", type=int, default=N_REPS)
    ap.add_argument("--campaign-state", default=CAMPAIGN_STATE)
    ap.add_argument("--raw-dir", default=RAW)
    ap.add_argument("--out", default=OUT)
    ap.add_argument(
        "--from-report",
        default="",
        help="re-summarize the replicates already stored in a report instead of measuring again",
    )
    args = ap.parse_args(argv)

    ref = reference_stats(args.campaign_state)
    print(
        "Phase L sentinel: loss=%.6f sd=%.6f | q_mean=%.6f sd=%.6f | n=%d | %s -> %s"
        % (
            ref["loss"]["mean"],
            ref["loss"]["sd"],
            ref["q_mean_ms"]["mean"],
            ref["q_mean_ms"]["sd"],
            ref["n_ref"],
            ref["wall_utc_min"],
            ref["wall_utc_max"],
        )
    )
    if args.from_report:
        with open(args.from_report, "r", encoding="utf-8") as f:
            rows = json.load(f)["rows"]
        print("re-summarizing %d stored replicates from %s" % (len(rows), args.from_report))
    else:
        rows = run_live(reps=args.reps, raw_dir=args.raw_dir)
    summary = summarize(rows, ref)
    report = {
        "phase": "20R.6",
        "kind": "sentinel_loss_drift_recheck",
        "cell": dict(SENTINEL),
        "reference": ref,
        "summary": summary,
        "rows": rows,
        "git_hash": git_hash(),
        "argv": list(sys.argv),
        "raw_dir": args.raw_dir,
        "wall_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True, default=str)
        f.write("\n")

    print()
    for field in ("loss", "q_mean_ms"):
        if field not in summary:
            continue
        s = summary[field]
        print(
            "%-10s hom nay=%.6f (sd=%.6f, n=%d)  Phase L=%.6f (sd=%.6f)  z_mean=%+.2f  z_welch=%+.2f  %s"
            % (
                field,
                s["mean"],
                s["sd"],
                s["n"],
                s["ref_mean"],
                s["ref_sd"],
                s["z_mean"],
                s["z_welch"],
                "*** DRIFT ***" if s["drift"] else "on dinh",
            )
        )
    print("verdict=%s -> %s" % (summary.get("verdict"), args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
