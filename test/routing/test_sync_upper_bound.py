#!/usr/bin/env python3
"""Tests for the Phase 14B.0 sync upper-bound report."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, ".")

from measurements.sync_upper_bound import (  # noqa: E402
    BoundRow,
    RewardScale,
    bound_rows,
    cost_screen,
    main,
    max_bound,
    render_markdown,
    routing3_env_from_load_cfg,
)


def test_bound_rows_sort_and_compute_upper_bound():
    rows = bound_rows({
        "decision_regret": 0.25,
        "disagree_rate_by_z": {"5": 0.4, "0": 0.1, "1": None},
    })

    assert [row.z for row in rows] == [0, 5]
    assert rows[0].upper_bound == 0.025
    assert rows[1].upper_bound == 0.1
    assert max_bound(rows).z == 5


def test_cost_screen_lists_only_viable_z_values():
    rows = [BoundRow(0, 0.1, 0.01), BoundRow(5, 0.5, 0.05)]

    assert cost_screen(rows, 0.02) == "5"
    assert cost_screen(rows, 0.05) == "none"


def test_routing3_env_from_load_cfg_recovers_knobs():
    env = routing3_env_from_load_cfg(
        "EVENT_3PATH_V4_RATE_0.12_PROFILE_cliffband_BIAS_0"
    )

    assert env == {
        "ROUTING3_EVENT_RATE": "0.12",
        "ROUTING3_BAND_PROFILE": "cliffband",
        "ROUTING3_CRASH_BIAS_TEMP": "0",
    }


def test_render_markdown_records_break_even_and_reward_audit():
    payload = {
        "git_hash": "abc123",
        "topology": "routing3",
        "load_cfg": "EVENT_3PATH_V4_RATE_0.12_PROFILE_cliffband_BIAS_0",
        "objective": "cvar",
        "cvar_alpha": 0.1,
        "cases": 400,
        "mc_samples": 200,
        "seed": 0,
        "gap_mean": 0.012,
        "gap_ci95": 0.002,
        "gap_lower": 0.010,
        "verdict": "FAIL",
        "disagree_rate": 0.4,
        "n_disagree": 160,
        "decision_regret": 0.25,
        "q_margin": 0.1,
        "q_margin_marginalized": 0.09,
    }
    scale = RewardScale(
        n_samples=3,
        seed=0,
        terminal_mean=3.5,
        terminal_std=0.1,
        differential_mean=-1.5,
        differential_std=0.1,
        differential_abs_mean=1.5,
        r_arrived=5.0,
        delay_norm_ms=20.0,
    )

    text = render_markdown(
        payload=payload,
        result_path=Path("result.json"),
        result_sha="deadbeef0000",
        rows=[BoundRow(0, 0.1, 0.025), BoundRow(5, 0.5, 0.125)],
        costs=(0.01, 0.2),
        scale=scale,
        source_env={"ROUTING3_EVENT_RATE": "0.12"},
        command="python3 -m measurements.sync_upper_bound",
    )

    assert "c* = max_z upper_bound = 0.125000" in text
    assert "| 0.200000 | none | ruled out |" in text
    assert "R_ARRIVED" in text
    assert "A + C" in text


def test_main_writes_markdown_from_json_without_scale():
    payload = {
        "git_hash": "abc123",
        "topology": "routing3",
        "load_cfg": "EVENT_3PATH_V4_RATE_0.12_PROFILE_cliffband_BIAS_0",
        "objective": "cvar",
        "cvar_alpha": 0.1,
        "cases": 4,
        "mc_samples": 2,
        "seed": 0,
        "gap_mean": 0.1,
        "gap_ci95": 0.01,
        "gap_lower": 0.09,
        "verdict": "FAIL",
        "disagree_rate": 0.5,
        "n_disagree": 2,
        "decision_regret": 0.25,
        "q_margin": 0.1,
        "q_margin_marginalized": 0.09,
        "disagree_rate_by_z": {"0": 0.0, "5": 0.5},
    }
    with tempfile.TemporaryDirectory() as tmp:
        result = Path(tmp) / "result.json"
        out = Path(tmp) / "00-upper-bound.md"
        result.write_text(json.dumps(payload), encoding="utf-8")

        code = main([
            "--result",
            str(result),
            "--out",
            str(out),
            "--skip-scale",
        ])

        assert code == 0
        assert out.exists()
        assert "0.125000" in out.read_text(encoding="utf-8")


def _run_as_script():
    tests = [
        test_bound_rows_sort_and_compute_upper_bound,
        test_cost_screen_lists_only_viable_z_values,
        test_routing3_env_from_load_cfg_recovers_knobs,
        test_render_markdown_records_break_even_and_reward_audit,
        test_main_writes_markdown_from_json_without_scale,
    ]
    for test in tests:
        test()
        print(f"  PASS  {test.__name__}")
    print(f"\n{len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    _run_as_script()
