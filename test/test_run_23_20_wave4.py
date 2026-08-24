"""G23-226: runner Dot 4 phai dung manifest ngoai sinh 14 cell."""
from __future__ import annotations

import ast
from pathlib import Path

from tools import run_23_20_matrix as R


def test_wave4_has_exactly_12_unique_jobs_and_expected_cells() -> None:
    jobs = R.WAVES[4]
    assert len(jobs) == len(set(jobs)) == 12
    assert {job[0] for job in jobs} == set(R.CELLS_REGION)
    assert sum(profile == "U3" and axis == R.AX_MEA for _, profile, axis in jobs) == 4
    assert sum(profile == "U0" and axis == R.AX_MEA for _, profile, axis in jobs) == 4
    assert sum(profile == "U0" and axis == R.AX_LEG for _, profile, axis in jobs) == 4


def test_wave4_uses_live_for_approved_measured_axis_only() -> None:
    measured = R.stem_of("h2@0.650", "U3", R.AX_MEA, wave=4)
    legacy = R.stem_of("h2@0.650", "U0", R.AX_LEG, wave=4)
    assert measured.startswith("results/LIVE/")
    assert legacy.startswith("results/SUPERSEDED/")


def test_runner_forwards_calibration_to_builder() -> None:
    source = Path("tools/run_23_20_matrix.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
    ]
    rendered = "\n".join(ast.dump(call) for call in calls)
    assert "--calibration" in source
    assert "calibration" in rendered
    assert R.WAVE4_CALIBRATION.endswith("S-B_14cells.json")
