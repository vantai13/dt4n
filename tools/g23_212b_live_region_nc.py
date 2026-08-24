#!/usr/bin/env python3
"""G23-212b: prove the patched live-region base path equals G23-212a."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from typing import Any, Dict

from cert import live_region_sweep as L
from tools import g23_212a_partial_nc as A


BASELINE = "results/RAW/phase-23/g23_212a_before.json"
OUTPUT = "results/RAW/phase-23/g23_212b_after.json"


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare(baseline_path: str = BASELINE) -> Dict[str, Any]:
    with open(baseline_path, "r", encoding="utf-8") as handle:
        before = json.load(handle)

    current_inputs = A.assert_inputs_pinned()
    same_inputs = before["input_parquet_sha256"] == current_inputs
    if not same_inputs:
        raise SystemExit(
            "DUNG: parquet dau vao DA DOI tu khi chup G23-212a; phep so vo nghia"
        )

    # This is the same helper used by run_sweep(), configured with the
    # 10-feasible-cell manifest semantics and the pinned U0 measured inputs.
    after_cells = L.analyze_base_cells(
        sla_path=L.SLA_EXOGENOUS_10,
        calib_template=A.CALIB_TEMPLATE,
        axis=A.AXIS,
        aoi_profile=A.AOI_PROFILE,
    )
    left, right = A._flat(before["cells"]), A._flat(after_cells)
    only = sorted(set(left) ^ set(right))
    exact_bad, reduced_bad = [], []
    for key in sorted(set(left) & set(right)):
        x, y = left[key], right[key]
        if (
            isinstance(x, (int, float))
            and isinstance(y, (int, float))
            and not isinstance(x, bool)
        ):
            delta = abs(float(x) - float(y))
            if delta == 0.0:
                continue
            if any(key.endswith("/" + field) for field in A.REDUCED_FIELDS):
                if delta > A.TOL_REDUCED * max(abs(float(x)), 1.0):
                    reduced_bad.append((key, x, y, delta))
            else:
                exact_bad.append((key, x, y, delta))
        elif x != y:
            exact_bad.append((key, x, y, None))

    passed = not only and not exact_bad and not reduced_bad
    return {
        "schema": "dt4n.g23_212b.v1",
        "gate": "G23-212b",
        "pass": passed,
        "claim": (
            "live_region_sweep.analyze_base_cells under the 10-feasible-cell "
            "S-B semantics reproduces the G23-212a side-A path"
        ),
        "baseline": baseline_path,
        "baseline_sha256": _sha256(baseline_path),
        "manifest": L.SLA_EXOGENOUS_10,
        "manifest_sha256": _sha256(L.SLA_EXOGENOUS_10),
        "calib_template": A.CALIB_TEMPLATE,
        "input_parquet_sha256": current_inputs,
        "cells": list(A.ALIVE_VERIFIED),
        "n_cells": len(after_cells),
        "n_common_fields": len(set(left) & set(right)),
        "n_fields_only_one_side": len(only),
        "n_group_A_exact_mismatch": len(exact_bad),
        "n_group_B_tolerance_mismatch": len(reduced_bad),
        "group_B_relative_tolerance": A.TOL_REDUCED,
        "only_one_side_sample": only[:10],
        "mismatch_sample": (exact_bad + reduced_bad)[:10],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default=BASELINE)
    parser.add_argument("--out", default=OUTPUT)
    args = parser.parse_args()
    report = compare(args.baseline)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("G23-212b  cell: %d" % report["n_cells"])
    print("G23-212b  truong so sanh: %d" % report["n_common_fields"])
    print("G23-212b  truong chi co mot ve: %d" % report["n_fields_only_one_side"])
    print(
        "G23-212b  NHOM A (bit-exact bat buoc) lech: %d"
        % report["n_group_A_exact_mismatch"]
    )
    print(
        "G23-212b  NHOM B (dung sai %.2e*|v|) lech: %d"
        % (
            report["group_B_relative_tolerance"],
            report["n_group_B_tolerance_mismatch"],
        )
    )
    print("G23-212b  %s" % ("PASS" if report["pass"] else "FAIL"))
    print("artifact -> %s" % args.out)
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
