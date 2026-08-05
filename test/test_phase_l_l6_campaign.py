#!/usr/bin/env python3
"""Phase L / L.6 -- pure tests for campaign plan, gates, and state."""

import json

from measurements.l6_campaign import (
    RHO,
    SENTINEL_EVERY,
    build_plan,
    campaign_summary,
    gate,
    load_state,
    save_state,
    select_todo,
    sentinel_summary,
)


def _good_row(**extra):
    row = {
        "rho": 0.9,
        "rho_actual": 0.9001,
        "rate_ratio": 1.0001,
        "socket_drops": 0,
        "n_foreign": 0,
        "n_late_ratio": 0.0,
        "max_late_ms": 0.0,
    }
    row.update(extra)
    return row


def test_build_plan_counts_blocks_and_unique_pids():
    plan = build_plan()
    assert len(plan) == 728
    assert sum(1 for p in plan if p["block"] == "A") == 540
    assert sum(1 for p in plan if p["block"] == "B") == 60
    assert sum(1 for p in plan if p["block"] == "C") == 45
    assert sum(1 for p in plan if p["block"] == "D") == 60
    assert sum(1 for p in plan if p["block"] == "E") == 23
    assert len({p["pid"] for p in plan}) == len(plan)


def test_sentinel_inserted_after_each_30_regular_points():
    plan = build_plan()
    sent_idxs = [i for i, p in enumerate(plan) if p["block"] == "E"]
    assert sent_idxs[0] == SENTINEL_EVERY
    assert sent_idxs[1] - sent_idxs[0] == SENTINEL_EVERY + 1


def test_plan_contains_critical_extra_seed_and_probe_zero_controls():
    plan = build_plan()
    assert any(p["block"] == "C" and p["rho"] == 1.00 and p["seed"] == 20 for p in plan)
    assert any(p["block"] == "D" and p["probe_pps"] == 0.0 and p["rho"] == 0.95 for p in plan)
    assert {p["rho"] for p in plan if p["block"] == "A"} == set(RHO)


def test_select_todo_respects_done_session_and_max_points():
    plan = build_plan()
    state = {"done_idx": [plan[0]["idx"], plan[1]["idx"]], "rows": [], "sentinels": []}
    todo = select_todo(plan, state, session=1, n_sessions=4, max_points=5)
    assert len(todo) == 5
    assert all(p["idx"] not in state["done_idx"] for p in todo)
    assert all(p["idx"] < 182 for p in todo)


def test_gate_bat_loi_van_hanh():
    assert gate(_good_row()) == []
    errs = gate(
        _good_row(
            socket_drops=1,
            n_foreign=1,
            rate_ratio=1.002,
            rho_actual=0.905,
            n_late_ratio=0.002,
            max_late_ms=60,
        )
    )
    assert len(errs) == 6


def test_sentinel_summary_flags_out_of_control():
    ok = sentinel_summary([
        {"q_mean_ms": 10.865},
        {"q_mean_ms": 10.885},
        {"q_mean_ms": 10.875},
        {"q_mean_ms": 10.872},
    ])
    assert ok["pass"] is True
    bad = sentinel_summary([{"q_mean_ms": 10.875}, {"q_mean_ms": 10.930}])
    assert bad["n_outside_3sigma"] == 1
    assert bad["pass"] is False


def test_state_atomic_round_trip(tmp_path):
    path = tmp_path / "state.json"
    state = {"order_seed": 9000, "done_idx": [1], "rows": [{"x": 1}], "sentinels": []}
    save_state(state, str(path))
    assert load_state(str(path)) == state
    assert not path.with_suffix(".json.tmp").exists()


def test_campaign_summary_coverage_and_fails():
    plan = build_plan()
    state = {
        "done_idx": [p["idx"] for p in plan[:720]],
        "rows": [{"gate_fail": []} for _ in range(719)] + [{"gate_fail": ["rate"]}],
        "sentinels": [{"q_mean_ms": 10.874}, {"q_mean_ms": 10.876}],
    }
    summary = campaign_summary(state, plan)
    assert summary["coverage_pass"] is True
    assert summary["fail_pass"] is True
    assert summary["sentinel"]["pass"] is True
