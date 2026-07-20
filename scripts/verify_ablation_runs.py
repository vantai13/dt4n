#!/usr/bin/env python3
"""Verify Phase 11 ablation run manifests after the 10-run script finishes."""

from __future__ import annotations

import glob
import json
from collections import defaultdict
from pathlib import Path


EXPECTED_BRANCHES = {"aoi", "mask"}
EXPECTED_SEEDS = {0, 1, 2, 3, 4}


def load_runs() -> list[dict]:
    """Load all Phase 11 ablation train.json files."""
    rows = []
    for path in sorted(glob.glob("results/ablation/*/r_seed*/train.json")):
        with open(path) as handle:
            payload = json.load(handle)
        payload["_path"] = path
        rows.append(payload)
    return rows


def main() -> int:
    rows = load_runs()
    print(f"found train.json files: {len(rows)}")
    if len(rows) != 10:
        raise AssertionError("expected exactly 10 train.json files")

    by_branch = defaultdict(list)
    for row in rows:
        branch = row.get("ablation_branch")
        by_branch[branch].append(row)

    print("branches:", {key: len(value) for key, value in by_branch.items()})
    if set(by_branch) != EXPECTED_BRANCHES:
        raise AssertionError("expected branches {'aoi', 'mask'}")

    link_shas = {row.get("link_model_sha256") for row in rows}
    link_versions = {row.get("link_model_version") for row in rows}
    print("distinct link_model_sha256:", len(link_shas))
    print("distinct link_model_version:", len(link_versions))
    if len(link_shas) != 1 or len(link_versions) != 1:
        raise AssertionError("dynamics are not locked across all runs")

    seeds_by_branch = {
        branch: {int(row["agent_seed"]) for row in branch_rows}
        for branch, branch_rows in by_branch.items()
    }
    print("seeds_by_branch:", seeds_by_branch)
    if any(seeds != EXPECTED_SEEDS for seeds in seeds_by_branch.values()):
        raise AssertionError("each branch must have seeds 0..4")

    paired = {}
    for branch in EXPECTED_BRANCHES:
        paired[branch] = {
            int(row["agent_seed"]): row
            for row in by_branch[branch]
        }

    for seed in sorted(EXPECTED_SEEDS):
        aoi = paired["aoi"][seed]
        mask = paired["mask"][seed]
        if aoi["train_seeds"] != mask["train_seeds"]:
            raise AssertionError(f"seed {seed}: train_seeds are not paired")
        if aoi["z_steps_choices"] != mask["z_steps_choices"]:
            raise AssertionError(f"seed {seed}: z choices differ")
        if aoi["config"]["env"]["load_cfg"] != mask["config"]["env"]["load_cfg"]:
            raise AssertionError(f"seed {seed}: load_cfg differs")
        if aoi["config"]["train"]["episodes"] != mask["config"]["train"]["episodes"]:
            raise AssertionError(f"seed {seed}: episodes differ")
        if aoi["mask_aoi"] is not False or mask["mask_aoi"] is not True:
            raise AssertionError(f"seed {seed}: mask flags invalid")

    [sha] = list(link_shas)
    [version] = list(link_versions)
    print(f"PASS - 10 runs paired and dynamics locked")
    print(f"link_model_version = {version}")
    print(f"link_model_sha256 = {sha}")
    for row in rows:
        print(
            f"  {row['ablation_branch']:4s} seed={row['agent_seed']} "
            f"wall_time_s={row.get('wall_time_s', 0.0):.2f} "
            f"{Path(row['_path']).parent}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
