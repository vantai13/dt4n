#!/usr/bin/env python3
"""Phase L / Lesson L.2 -- analyze raw files from owd_probe.

This program only reads raw files. Percentiles use nearest-rank by preregistered
choice; warm-up/tail windows are cut by t_send.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
from typing import Iterable, List, Sequence, Tuple


REC_RX = struct.Struct("<Qdd")
REC_TX = struct.Struct("<Qd")
PERCENTILE_METHOD = "nearest-rank"


def pctl(sorted_values: Sequence[float], q: float) -> float:
    if len(sorted_values) == 0:
        return float("nan")
    k = int(math.ceil(q * len(sorted_values))) - 1
    return float(sorted_values[min(max(k, 0), len(sorted_values) - 1)])


def mean(values: Sequence[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def sd(values: Sequence[float]) -> float:
    if len(values) <= 1:
        return float("nan")
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))


def load(path: str, rec: struct.Struct) -> List[Tuple]:
    with open(path, "rb") as f:
        raw = f.read()
    if len(raw) % rec.size:
        raise ValueError("%s: kich thuoc khong chia het cho %d byte -- file HONG" % (path, rec.size))
    return [rec.unpack_from(raw, i * rec.size) for i in range(len(raw) // rec.size)]


def _blocks(rx_w: Iterable[Tuple[int, float, float]], lo: float, hi: float, k: int) -> dict:
    rx_list = list(rx_w)
    if not rx_list:
        return {"block_means_ms": [], "spread_ms": None}
    width = (hi - lo) / float(k)
    edges = [lo + i * width for i in range(k + 1)]
    means = []
    for i in range(k):
        vals = [
            (r[2] - r[1]) * 1000.0
            for r in rx_list
            if edges[i] <= r[1] < edges[i + 1]
        ]
        means.append(mean(vals) if vals else None)
    finite = [m for m in means if m is not None and math.isfinite(m)]
    return {
        "block_means_ms": means,
        "spread_ms": (max(finite) - min(finite)) if finite else None,
    }


def analyze(rx_path: str, tx_path: str, warmup_s: float, tail_s: float = 0.0) -> dict:
    rx = load(rx_path, REC_RX)
    tx = load(tx_path, REC_TX)
    if not tx:
        raise ValueError("file gui rong")

    t0 = tx[0][1]
    lo = t0 + float(warmup_s)
    hi = tx[-1][1] - float(tail_s)

    tx_w = [row for row in tx if lo <= row[1] <= hi]
    rx_w = [row for row in rx if lo <= row[1] <= hi]

    n_sent = len(tx_w)
    seqs = [int(row[0]) for row in rx_w]
    owd = [(row[2] - row[1]) * 1000.0 for row in rx_w]

    uniq = set(seqs)
    n_uniq = len(uniq)
    n_dup = len(seqs) - n_uniq
    reorder = sum(1 for prev, cur in zip(seqs, seqs[1:]) if cur < prev)
    n_neg = sum(1 for x in owd if x < 0)

    o_sorted = sorted(owd)
    tx_times = [float(row[1]) for row in tx_w]
    inter_arrival = [b - a for a, b in zip(tx_times, tx_times[1:])]
    ia_mean = mean(inter_arrival) if inter_arrival else float("nan")
    ca = (
        sd(inter_arrival) / ia_mean
        if len(inter_arrival) > 1 and ia_mean > 0
        else None
    )

    return {
        "window": {
            "warmup_s": float(warmup_s),
            "tail_s": float(tail_s),
            "t_lo": lo,
            "t_hi": hi,
            "cut_on": "t_send",
        },
        "counts": {
            "n_sent": n_sent,
            "n_recv_total": len(seqs),
            "n_recv_unique": n_uniq,
            "n_duplicate": n_dup,
            "n_reorder": reorder,
            "n_owd_negative": n_neg,
        },
        "loss_rate": (n_sent - n_uniq) / n_sent if n_sent else float("nan"),
        "owd_ms": {
            "mean": mean(o_sorted),
            "sd": sd(o_sorted),
            "min": float(o_sorted[0]) if o_sorted else float("nan"),
            "p50": pctl(o_sorted, 0.50),
            "p90": pctl(o_sorted, 0.90),
            "p95": pctl(o_sorted, 0.95),
            "p99": pctl(o_sorted, 0.99),
            "max": float(o_sorted[-1]) if o_sorted else float("nan"),
            "percentile_method": PERCENTILE_METHOD,
        },
        "arrival": {
            "rate_pps_actual": n_sent / max(hi - lo, 1e-9),
            "c_a_measured": ca,
            "c_s_measured": 0.0,
        },
        "steady_state": _blocks(rx_w, lo, hi, 6),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rx", required=True)
    ap.add_argument("--tx", required=True)
    ap.add_argument("--warmup", type=float, default=10.0)
    ap.add_argument("--tail", type=float, default=0.0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    res = analyze(args.rx, args.tx, args.warmup, args.tail)
    res["inputs"] = {"rx": args.rx, "tx": args.tx}
    text = json.dumps(res, indent=2, sort_keys=True)
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
