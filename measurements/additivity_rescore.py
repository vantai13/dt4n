#!/usr/bin/env python3
"""Phase 20R.6b -- rescore tandem rows from the background load stream.

Branch A in the truth table was built from the background/load packets. Early
20R.6 A' rows used a separate sparse probe stream for loss, which makes
``A' - A`` compare two different estimators. This script does not run Mininet;
it rereads the ``*_bg.bin`` and ``*_bgtx.bin`` files already written by
``measurements.additivity_live`` and writes a new state JSON.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence

from measurements.owd_analyze import analyze


DEFAULT_WARMUP_S = 10.0


def bg_prefix(row: Mapping[str, Any]) -> str:
    return os.path.join(
        str(row["raw_dir"]),
        "%s_load_L%d" % (str(row["pid"]), int(row["link_idx"])),
    )


def _copy_old_probe_fields(out: Dict[str, Any], row: Mapping[str, Any]) -> None:
    static_ms = float(row["static_ms"])
    out["probe_delay_ms"] = float(row.get("delay_ms", row.get("q_mean_ms")))
    out["probe_queue_mean_ms"] = out["probe_delay_ms"] - static_ms
    out["probe_loss"] = float(row.get("loss", row.get("probe_loss", 0.0)))
    out["probe_cost_ms"] = float(row.get("cost_ms"))


def rescore_row(row: Mapping[str, Any], warmup_s: float) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(row)
    if row.get("branch") == "C":
        out["rescore_status"] = "skipped_branch_C"
        return out
    if row.get("link_idx") is None:
        out["rescore_status"] = "skipped_no_link_idx"
        return out

    prefix = bg_prefix(row)
    rx = prefix + "_bg.bin"
    tx = prefix + "_bgtx.bin"
    if not (os.path.exists(rx) and os.path.exists(tx)):
        out["rescore_status"] = "missing_bg_files"
        out["rescore_missing"] = [p for p in (rx, tx) if not os.path.exists(p)]
        return out

    bg = analyze(rx, tx, warmup_s=float(warmup_s))
    owd = dict(bg["owd_ms"])
    counts = dict(bg["counts"])
    static_ms = float(row["static_ms"])
    w_loss = float(row["w_loss"])
    delay_bg = static_ms + float(owd["mean"])
    loss_bg = float(bg["loss_rate"])

    _copy_old_probe_fields(out, row)
    out["delta_pasta_ms"] = float(owd["mean"]) - out["probe_queue_mean_ms"]
    out["estimator"] = "bg_load_stream"
    out["queue_mean_ms"] = float(owd["mean"])
    out["queue_sd_ms"] = float(owd["sd"])
    out["delay_ms"] = delay_bg
    out["q_mean_ms"] = delay_bg
    out["q_sd_ms"] = float(owd["sd"])
    out["q_p50_ms"] = static_ms + float(owd["p50"])
    out["q_p90_ms"] = static_ms + float(owd["p90"])
    out["q_p95_ms"] = static_ms + float(owd["p95"])
    out["q_p99_ms"] = static_ms + float(owd["p99"])
    out["loss"] = loss_bg
    out["cost_ms"] = delay_bg + w_loss * loss_bg
    out["n_bg_sent"] = int(counts["n_sent"])
    out["n_bg_recv_unique"] = int(counts["n_recv_unique"])
    out["n_bg_duplicate"] = int(counts["n_duplicate"])
    out["rescore_status"] = "ok"
    return out


def write_json(path: str, obj: object) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--warmup", type=float, default=DEFAULT_WARMUP_S)
    args = ap.parse_args(argv)

    with open(args.state, "r", encoding="utf-8") as f:
        state = json.load(f)

    rows: List[Dict[str, Any]] = [rescore_row(row, args.warmup) for row in state.get("rows", [])]
    counts = {
        "ok": sum(1 for row in rows if row.get("rescore_status") == "ok"),
        "missing": sum(1 for row in rows if row.get("rescore_status") == "missing_bg_files"),
        "skipped": sum(1 for row in rows if str(row.get("rescore_status", "")).startswith("skipped")),
        "total": len(rows),
    }
    state_out = dict(state)
    state_out["rows"] = rows
    state_out["rescored_from"] = args.state
    state_out["rescore_warmup_s"] = float(args.warmup)
    state_out["rescore_estimator"] = "bg_load_stream"
    state_out["rescore_counts"] = counts
    write_json(args.out, state_out)
    print(json.dumps(counts, indent=2, sort_keys=True))
    print("rescored -> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
