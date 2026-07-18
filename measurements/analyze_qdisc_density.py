#!/usr/bin/env python3
"""Analyze qdisc-density probe output.

The important question after the density probe is whether the low-load 0/1
packet distribution depends on propagation delay. This script fits P(1p)
against measured utilization for the non-saturated rows and reports the
forbidden-zone mass P(2..q-2) separately from the near-full mass P(q-1..q).
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
from collections import defaultdict


DIST_RE = re.compile(r"(\d+)p:([0-9.]+)")


def _float(row, key, default=0.0):
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def _int(row, key, default=0):
    try:
        return int(float(row.get(key, default)))
    except (TypeError, ValueError):
        return int(default)


def parse_distribution(text):
    return {int(pkt): float(frac) for pkt, frac in DIST_RE.findall(text or "")}


def distribution_masses(row):
    q = _int(row, "cfg_queue_pkts", 13)
    dist = parse_distribution(row.get("netem_distribution", ""))
    p0 = dist.get(0, _float(row, "p0"))
    p1 = dist.get(1, _float(row, "p1"))
    p_forbidden = sum(frac for pkt, frac in dist.items() if 2 <= pkt <= q - 2)
    p_near_full = sum(frac for pkt, frac in dist.items() if pkt >= q - 1)
    # If old summary rows only stored p_full, keep that signal.
    if not dist:
        p_near_full = _float(row, "p_full")
        p_forbidden = max(0.0, 1.0 - p0 - p1 - p_near_full)
    return p0, p1, p_forbidden, p_near_full


def linreg(xs, ys):
    if len(xs) < 2:
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx <= 0.0:
        return None
    slope = sxy / sxx
    intercept = my - slope * mx
    corr = sxy / math.sqrt(sxx * syy) if syy > 0.0 else 0.0
    return slope, intercept, corr


def load_rows(paths):
    rows = []
    for path in paths:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                row["_source"] = path
                rows.append(row)
    return rows


def cfg_key(row):
    return (
        _float(row, "cfg_bw_mbps"),
        _float(row, "cfg_delay_ms"),
        _int(row, "cfg_queue_pkts"),
        os.path.basename(row.get("_source", "")),
    )


def fmt(value, digits=3):
    if value is None:
        return "n/a"
    return ("%." + str(digits) + "f") % float(value)


def summarize_group(key, rows, packet_bytes):
    bw, delay, queue, source = key
    pkt_ms = packet_bytes * 8.0 / (bw * 1e6) * 1000.0 if bw > 0 else 0.0
    rows = sorted(rows, key=lambda r: _float(r, "rho_offered"))

    print("\n=== %s | bw=%gM base=%gms q=%d pkt=%.3fms ===" % (
        source,
        bw,
        delay,
        queue,
        pkt_ms,
    ))
    print("rho_off rho_meas mean_p bdp_p err_p  p0    p1    p2..q-2 p(q-1..q) q_ms  loss")

    fit_x = []
    fit_y = []
    bdp_errors = []
    last_clean = None
    first_saturated = None
    max_forbidden = 0.0

    for row in rows:
        p0, p1, p_forbidden, p_near_full = distribution_masses(row)
        max_forbidden = max(max_forbidden, p_forbidden)
        rho_off = _float(row, "rho_offered")
        rho_meas = _float(row, "rho_measured")
        mean_pkts = _float(row, "mean_netem_pkts")
        bdp_pkts = (rho_meas * delay / pkt_ms) if pkt_ms > 0.0 else 0.0
        bdp_err = abs(mean_pkts - bdp_pkts)
        q_ms = mean_pkts * pkt_ms
        loss = _float(row, "loss_rate")

        print(
            "%7.3f %8.3f %6.2f %5.2f %5.2f %5.2f %5.2f %8.3f %10.3f %5.2f %5.3f"
            % (
                rho_off,
                rho_meas,
                mean_pkts,
                bdp_pkts,
                bdp_err,
                p0,
                p1,
                p_forbidden,
                p_near_full,
                q_ms,
                loss,
            )
        )

        clean = p_near_full < 0.05 and loss < 0.005
        saturated = p_near_full >= 0.05 or loss >= 0.005
        if clean:
            fit_x.append(rho_meas)
            fit_y.append(p1)
            bdp_errors.append(bdp_err)
            last_clean = rho_off
        elif saturated and first_saturated is None:
            first_saturated = rho_off

    fit = linreg(fit_x, fit_y)
    if fit is None:
        print("fit low-load P(1p): n/a")
        fit_summary = None
    else:
        slope, intercept, corr = fit
        print(
            "fit low-load P(1p) = %.3f*rho_meas %+ .3f | corr=%.3f | n=%d"
            % (slope, intercept, corr, len(fit_x))
        )
        fit_summary = {
            "bw": bw,
            "delay": delay,
            "queue": queue,
            "slope": slope,
            "intercept": intercept,
            "corr": corr,
            "n": len(fit_x),
        }

    if last_clean is not None and first_saturated is not None:
        print("phase cliff bracket: rho_off in (%.3f, %.3f]" % (last_clean, first_saturated))
    else:
        print("phase cliff bracket: n/a")
    if bdp_errors:
        print(
            "low-load mean_p ~= BDP: MAE=%.3fp max=%.3fp"
            % (sum(bdp_errors) / len(bdp_errors), max(bdp_errors))
        )
    print("max middle-zone mass P(2..q-2): %.3f" % max_forbidden)
    if max_forbidden > 0.05:
        print("note: middle packets can come from BDP>1 or from the critical band.")
    return fit_summary


def parse_args():
    p = argparse.ArgumentParser(description="Analyze qdisc density CSV files")
    p.add_argument("csv", nargs="+", help="summary CSV files from qdisc_density_probe.py")
    p.add_argument(
        "--packet-bytes",
        type=float,
        default=1512.0,
        help="packet size used for qdelay-from-backlog display",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_rows(args.csv)
    groups = defaultdict(list)
    for row in rows:
        groups[cfg_key(row)].append(row)

    fits = []
    for key in sorted(groups):
        fit = summarize_group(key, groups[key], args.packet_bytes)
        if fit:
            fits.append(fit)

    if len(fits) >= 2:
        slopes = [item["slope"] for item in fits]
        intercepts = [item["intercept"] for item in fits]
        print("\n=== base-delay check ===")
        print("slope range: %.3f..%.3f" % (min(slopes), max(slopes)))
        print("intercept range: %.3f..%.3f" % (min(intercepts), max(intercepts)))
        print("P(1p) is not universal; use mean_p ~= BDP for the physical check.")


if __name__ == "__main__":
    main()
