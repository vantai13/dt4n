#!/usr/bin/env python3
"""Check Phase 20R.6 state-file structural invariants before final analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping


TOP_LEVEL_KEYS = ("probe_size_bytes", "duration_s", "carve_out_fraction")


def _load(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _probe_rate(state: Mapping[str, Any]) -> Any:
    value = state.get("probe_rate_pps")
    if value is not None:
        return value
    rows = list(state.get("rows", []))
    if not rows:
        return None
    return rows[0].get("probe_rate_pps_configured")


def check_pair(label: str, baseline_path: str, candidate_path: str) -> None:
    base = _load(baseline_path)
    cand = _load(candidate_path)
    problems = []
    for key in TOP_LEVEL_KEYS:
        if base.get(key) != cand.get(key):
            problems.append("%s: pilot=%r moi=%r" % (key, base.get(key), cand.get(key)))
    if _probe_rate(base) != _probe_rate(cand):
        problems.append("probe_rate_pps: pilot=%r moi=%r" % (_probe_rate(base), _probe_rate(cand)))
    if problems:
        raise AssertionError("LECH bat bien %s:\n  %s" % (label, "\n  ".join(problems)))
    print("%s bat bien cau truc KHOP" % label)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pilot-b", default="results/SMOKE/phase-20R/branch_b_fixed_pilot3.json")
    ap.add_argument("--pilot-c", default="results/SMOKE/phase-20R/branch_c_fixed_pilot3.json")
    ap.add_argument("--new-b", default="results/SUPERSEDED/phase-20R/branch_b_fixed_s104_108.json")
    ap.add_argument("--new-c", default="results/SUPERSEDED/phase-20R/branch_c_fixed_s104_108.json")
    args = ap.parse_args()

    missing = [path for path in (args.pilot_b, args.pilot_c, args.new_b, args.new_c) if not Path(path).exists()]
    if missing:
        raise SystemExit("missing state files: %s" % ", ".join(missing))

    check_pair("B", args.pilot_b, args.new_b)
    check_pair("C", args.pilot_c, args.new_c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
