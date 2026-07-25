#!/usr/bin/env python3
"""Diagnose Phase 14C reward dynamic range.

This is not a Phase 14C gate.  It is a deterministic/mechanical audit showing
whether r_v3 restores reward signal in the overload region where r_v2 clipped
the delay term.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rl.routing3 import link_model as LM
from rl.routing3 import reward3, reward3_v3, topology3 as T3


RHO_POINTS = (0.30, 0.70, 0.90, 0.925, 0.93, 1.00, 1.10, 1.30)
OVERLOAD_LO = 0.93
OVERLOAD_HI = 1.30
SUBCLIFF_LO = 0.30
SUBCLIFF_HI = 0.925


def bottleneck_meta():
    cfg = T3.link_cfg()
    return cfg[T3.BOTTLENECK_LINKS["P1"]]


def delay_loss(rho):
    meta = bottleneck_meta()
    delay_ms = LM.total_delay_ms(
        meta["base_delay"],
        float(rho),
        bw_mbps=meta["base_bw"],
        queue_pkts=meta["queue_pkts"],
    )
    return delay_ms, LM.loss_rate(float(rho))


def row_for_rho(rho):
    delay_ms, loss = delay_loss(rho)
    v2 = reward3.step_reward(delay_ms, loss, arrived=False)
    v3 = reward3_v3.step_reward(delay_ms, loss, arrived=False, criticality=1.0)
    v3_low = reward3_v3.step_reward(
        delay_ms,
        loss,
        arrived=False,
        criticality=0.2,
    )
    return {
        "rho": float(rho),
        "delay_ms": float(delay_ms),
        "loss": float(loss),
        "v2_delay_term": float(v2.delay_term),
        "v2_total_no_terminal": float(v2.total),
        "v3_delay_term": float(v3.delay_term),
        "v3_loss_term": float(v3.loss_term),
        "v3_loss_penalty": float(reward3_v3.loss_penalty(loss)),
        "v3_sla_term": float(v3.sla_term),
        "v3_total_no_terminal": float(v3.total),
        "v3_total_v02_no_terminal": float(v3_low.total),
    }


def span(rows, key, lo, hi):
    by_rho = {row["rho"]: row for row in rows}
    return abs(float(by_rho[hi][key]) - float(by_rho[lo][key]))


def diagnose():
    rows = [row_for_rho(rho) for rho in RHO_POINTS]
    return {
        "reward_v2": reward3.REWARD_VERSION,
        "reward_v3": reward3_v3.REWARD_VERSION,
        "rho_points": list(RHO_POINTS),
        "rows": rows,
        "spans": {
            "v2_delay_subcliff_0.30_0.925": span(
                rows, "v2_delay_term", SUBCLIFF_LO, SUBCLIFF_HI
            ),
            "v2_delay_overload_0.93_1.30": span(
                rows, "v2_delay_term", OVERLOAD_LO, OVERLOAD_HI
            ),
            "v2_total_overload_0.93_1.30": span(
                rows, "v2_total_no_terminal", OVERLOAD_LO, OVERLOAD_HI
            ),
            "v3_delay_overload_0.93_1.30": span(
                rows, "v3_delay_term", OVERLOAD_LO, OVERLOAD_HI
            ),
            "v3_total_overload_0.93_1.30": span(
                rows, "v3_total_no_terminal", OVERLOAD_LO, OVERLOAD_HI
            ),
            "v2_loss_overload_0.93_1.30": span(
                rows, "v2_total_no_terminal", OVERLOAD_LO, OVERLOAD_HI
            ),
            "v3_loss_term_overload_0.93_1.30": span(
                rows, "v3_loss_term", OVERLOAD_LO, OVERLOAD_HI
            ),
        },
        "notes": [
            "v2 delay span in overload is zero because DELAY_CLIP=-1.0.",
            "v2 total still has loss signal; the clipping bug specifically "
            "removes delay/tail-latency signal.",
            "v3 restores unclipped delay and adds an SLA tail penalty.",
        ],
    }


def render_text(payload):
    rows = payload["rows"]
    spans = payload["spans"]
    lines = [
        "=" * 86,
        "  PHASE 14C REWARD DYNAMIC-RANGE DIAGNOSTIC",
        "=" * 86,
        (
            f"{'rho':>6s} {'delay':>8s} {'loss':>8s} "
            f"{'v2_delay':>10s} {'v2_total':>10s} "
            f"{'v3_loss':>10s} {'v3_total':>10s} {'v3_v0.2':>10s}"
        ),
        "-" * 86,
    ]
    for row in rows:
        lines.append(
            f"{row['rho']:6.3f} {row['delay_ms']:8.3f} {row['loss']:8.4f} "
            f"{row['v2_delay_term']:10.4f} "
            f"{row['v2_total_no_terminal']:10.4f} "
            f"{row['v3_loss_term']:10.4f} "
            f"{row['v3_total_no_terminal']:10.4f} "
            f"{row['v3_total_v02_no_terminal']:10.4f}"
        )
    lines.extend([
        "",
        "Spans:",
        (
            "  v2 delay below cliff 0.30->0.925  = "
            f"{spans['v2_delay_subcliff_0.30_0.925']:.6f}"
        ),
        (
            "  v2 delay overload 0.93->1.30     = "
            f"{spans['v2_delay_overload_0.93_1.30']:.6f}"
        ),
        (
            "  v2 total overload 0.93->1.30     = "
            f"{spans['v2_total_overload_0.93_1.30']:.6f}"
        ),
        (
            "  v3 delay overload 0.93->1.30     = "
            f"{spans['v3_delay_overload_0.93_1.30']:.6f}"
        ),
        (
            "  v3 total overload 0.93->1.30     = "
            f"{spans['v3_total_overload_0.93_1.30']:.6f}"
        ),
        (
            "  v3 loss-term overload 0.93->1.30 = "
            f"{spans['v3_loss_term_overload_0.93_1.30']:.6f}"
        ),
    ])
    v2_total = spans["v2_total_overload_0.93_1.30"]
    v3_total = spans["v3_total_overload_0.93_1.30"]
    if v2_total > 0.0:
        lines.append(f"  v3/v2 total overload span ratio     = {v3_total / v2_total:.3f}")
    lines.append("=" * 86)
    return "\n".join(lines)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", default=None,
                        help="optional JSON output path")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    payload = diagnose()
    print(render_text(payload))
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
        print(f"-> wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
