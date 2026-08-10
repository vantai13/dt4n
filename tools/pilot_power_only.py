#!/usr/bin/env python3
"""Phase 20R.6-v2 pilot power summary.

This intentionally does not print residual means.  The internal pilot may only
be used to estimate between-seed scatter and the seed count needed for power.
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Any, Dict, List, Optional, Sequence

import mpmath as mp
import numpy as np

from measurements import cascade_residual as CR


DEFAULT_LOSS_DELTAS = (0.005, 0.010)
DEFAULT_DELAY_DELTAS_MS = (0.44,)
SD_UPPER_CONFIDENCE = 0.95


def _parts(value: str) -> List[str]:
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _parse_deltas(value: str) -> List[float]:
    out = [float(part) for part in _parts(value)]
    if not out or any(delta <= 0.0 for delta in out):
        raise argparse.ArgumentTypeError("--deltas must contain positive numbers")
    return out


def _deltas_for_channel(deltas: Any, channel: str) -> List[float]:
    if isinstance(deltas, dict):
        return [float(x) for x in deltas[str(channel)]]
    return [float(x) for x in deltas]


def _n_seed_for(sd: float, delta: float) -> Optional[int]:
    if not math.isfinite(sd):
        return None
    return int(math.ceil((1.645 * float(sd) / float(delta)) ** 2))


def _chi2_cdf(x: float, df: int) -> float:
    if x <= 0.0:
        return 0.0
    return float(mp.gammainc(float(df) / 2.0, 0.0, float(x) / 2.0, regularized=True))


def _chi2_ppf(p: float, df: int) -> float:
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0,1)")
    if df <= 0:
        raise ValueError("df must be positive")
    lo, hi = 0.0, max(1.0, float(df))
    while _chi2_cdf(hi, df) < p:
        hi *= 2.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if _chi2_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return hi


def _sd_upper(sd: float, n_observed: int, confidence: float = SD_UPPER_CONFIDENCE) -> Optional[float]:
    if not math.isfinite(sd) or int(n_observed) < 2:
        return None
    df = int(n_observed) - 1
    chi2_lower = _chi2_ppf(1.0 - float(confidence), df)
    return float(sd) * math.sqrt(float(df) / max(float(chi2_lower), 1e-300))


def summarize(
    branch_b: Sequence[str],
    branch_c: Sequence[str],
    modes: Sequence[str],
    rho_bar: float,
    deltas: Sequence[float],
) -> Dict[str, Any]:
    rows_b_all = CR.load_rows(branch_b, "B")
    rows_c_all = CR.load_rows(branch_c, "C")

    rows: List[Dict[str, Any]] = []
    invariants: Dict[str, Any] = {}
    for mode in modes:
        rows_b = [
            row for row in rows_b_all
            if str(row.get("mode")) == str(mode) and abs(float(row.get("rho_bar")) - float(rho_bar)) <= 1e-9
        ]
        rows_c = [
            row for row in rows_c_all
            if str(row.get("mode")) == str(mode) and abs(float(row.get("rho_bar")) - float(rho_bar)) <= 1e-9
        ]
        invariant_error: Optional[str] = None
        try:
            invariants[str(mode)] = {
                "status": "ok",
                "details": CR.assert_structural_invariant(rows_b, rows_c),
            }
        except AssertionError as exc:
            invariant_error = str(exc)
            invariants[str(mode)] = {"status": "fail", "reason": invariant_error}

        for channel in ("loss", "delay_ms"):
            channel_deltas = _deltas_for_channel(deltas, channel)
            if invariant_error is not None:
                item = {
                    "mode": str(mode),
                    "channel": channel,
                    "status": "insufficient_data",
                    "reason": invariant_error,
                    "n_observed_seed": 0,
                    "seed_ids": [],
                    "sd_d_s": None,
                    "sd_d_s_upper_95": None,
                    "n_seed_required": {
                        ("delta_%g" % float(delta)): None
                        for delta in channel_deltas
                    },
                    "n_seed_required_conservative_95": {
                        ("delta_%g" % float(delta)): None
                        for delta in channel_deltas
                    },
                }
            else:
                try:
                    diffs, seeds = CR.paired_residuals(rows_b, rows_c, mode, rho_bar, channel)
                    sd = float(np.std(diffs, ddof=1)) if int(diffs.size) > 1 else float("nan")
                    sd_upper = _sd_upper(sd, int(diffs.size))
                    item = {
                        "mode": str(mode),
                        "channel": channel,
                        "status": "ok",
                        "n_observed_seed": int(diffs.size),
                        "seed_ids": [int(seed) for seed in seeds],
                        "sd_d_s": sd,
                        "sd_d_s_upper_95": sd_upper,
                        "n_seed_required": {
                            ("delta_%g" % float(delta)): _n_seed_for(sd, float(delta))
                            for delta in channel_deltas
                        },
                        "n_seed_required_conservative_95": {
                            ("delta_%g" % float(delta)): (
                                None if sd_upper is None else _n_seed_for(sd_upper, float(delta))
                            )
                            for delta in channel_deltas
                        },
                    }
                except (AssertionError, KeyError, ValueError) as exc:
                    item = {
                        "mode": str(mode),
                        "channel": channel,
                        "status": "insufficient_data",
                        "reason": str(exc),
                        "n_observed_seed": 0,
                        "seed_ids": [],
                    "sd_d_s": None,
                    "sd_d_s_upper_95": None,
                    "n_seed_required": {
                        ("delta_%g" % float(delta)): None
                        for delta in channel_deltas
                    },
                    "n_seed_required_conservative_95": {
                        ("delta_%g" % float(delta)): None
                        for delta in channel_deltas
                    },
                }
            rows.append(item)

    return {
        "schema": "phase20r6/pilot_power_only/v1",
        "note": "Pilot summary intentionally omits point estimates; use sd(d_s) only for power planning.",
        "sd_upper_confidence": SD_UPPER_CONFIDENCE,
        "sd_upper_method": "one-sided chi-square upper confidence bound for the between-seed standard deviation",
        "rho_bar": float(rho_bar),
        "deltas_by_channel": (
            {str(channel): [float(delta) for delta in values] for channel, values in deltas.items()}
            if isinstance(deltas, dict)
            else {channel: [float(delta) for delta in deltas] for channel in ("loss", "delay_ms")}
        ),
        "invariant_by_mode": invariants,
        "rows": rows,
    }


def print_summary(summary: Dict[str, Any]) -> None:
    print("=== PILOT POWER ONLY ===")
    print("rho_bar = %.6f" % float(summary["rho_bar"]))
    print(
        "deltas  = %s"
        % " | ".join(
            "%s:%s" % (channel, ",".join("%.6g" % float(delta) for delta in values))
            for channel, values in sorted(summary["deltas_by_channel"].items())
        )
    )
    print()
    hdr = "%-8s %-9s %8s %14s %14s %s"
    print(hdr % ("mode", "channel", "n_seed", "sd(d_s)", "sd95_hi", "n_seed_required_conservative"))
    for row in summary["rows"]:
        req = ", ".join(
            "%s=%s" % (key, val)
            for key, val in sorted(row["n_seed_required_conservative_95"].items())
        )
        sd_text = "INSUFFICIENT" if row["sd_d_s"] is None else "%.9g" % float(row["sd_d_s"])
        sd_hi_text = "INSUFFICIENT" if row.get("sd_d_s_upper_95") is None else "%.9g" % float(row["sd_d_s_upper_95"])
        print(
            hdr
            % (
                row["mode"],
                row["channel"],
                int(row["n_observed_seed"]),
                sd_text,
                sd_hi_text,
                req,
            )
        )
        if row.get("status") != "ok":
            print("  reason: %s" % row.get("reason", "insufficient data"))


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--branch-b", required=True, help="comma-separated branch B state files")
    ap.add_argument("--branch-c", required=True, help="comma-separated branch C state files")
    ap.add_argument("--modes", default="poisson,h2")
    ap.add_argument("--rho-bar", type=float, default=0.925)
    ap.add_argument("--deltas", type=_parse_deltas, default=None, help="legacy: apply the same deltas to all channels")
    ap.add_argument("--loss-deltas", type=_parse_deltas, default=list(DEFAULT_LOSS_DELTAS))
    ap.add_argument("--delay-deltas", type=_parse_deltas, default=list(DEFAULT_DELAY_DELTAS_MS))
    ap.add_argument("--out", help="optional JSON output path")
    args = ap.parse_args(argv)

    summary = summarize(
        _parts(args.branch_b),
        _parts(args.branch_c),
        _parts(args.modes),
        args.rho_bar,
        (
            args.deltas
            if args.deltas is not None
            else {"loss": args.loss_deltas, "delay_ms": args.delay_deltas}
        ),
    )
    print_summary(summary)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, sort_keys=True)
            f.write("\n")
        print()
        print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
