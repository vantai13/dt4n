"""Tests for the Phase 20R.4 fine-grid campaign plan."""

import json
import time

import pytest

from measurements import l6_campaign_fine as F


def test_fine_grid_budget_matches_preregistered_new_work():
    rows = F.grid_summary(F.load_calibration())

    assert len(rows) == 9
    assert sum(row["n_new_levels"] for row in rows) == 118
    assert {row["mode"]: row["step"] for row in rows} == {
        "cbr": 0.05,
        "poisson": 0.02,
        "h2": 0.02,
    }


def test_full_plan_is_deterministic_randomized_and_has_expected_sentinels():
    a = F.build_full_plan()
    b = F.build_full_plan()

    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert F.stable_digest(a) == "ae9c409ea2956cae0eaf6e9bf1776f32783ac83be1b1cae0fa937c16fe60daf1"
    assert len(a) == 609
    assert sum(1 for point in a if point["block"] == "F") == 590
    assert sum(1 for point in a if point["block"] == "E") == 19
    assert all(not F.is_phase_l_rho(point["rho"]) for point in a if point["block"] == "F")
    assert [point["idx"] for point in a if point["block"] == "E"] == [
        30,
        61,
        92,
        123,
        154,
        185,
        216,
        247,
        278,
        309,
        340,
        371,
        402,
        433,
        464,
        495,
        526,
        557,
        588,
    ]


def test_smoke_and_continuity_plans_are_small_and_separate():
    smoke = F.build_smoke_plan()
    continuity = F.build_continuity_plan()

    assert len(smoke) == 10
    assert smoke[-1]["block"] == "E"
    assert len(continuity) == 8
    assert {point["block"] for point in continuity} == {"G"}
    assert {point["seed"] for point in continuity} == {F.CONTINUITY_SEED}
    assert all(F.is_phase_l_rho(point["rho"]) for point in continuity)


def test_gate_20r_is_stricter_than_phase_l_rate_gate():
    good = {
        "socket_drops": 0,
        "n_foreign": 0,
        "rate_ratio": 1.00009,
        "rho_actual": 0.7,
        "rho": 0.7,
        "n_late_ratio": 0.0,
        "max_late_ms": 1.0,
        "se_batch_ms": 0.3,
        "se_naive_ms": 0.03,
        "probe_pps": 20.0,
    }
    bad = {**good, "rate_ratio": 1.00011}

    assert F.gate_20r(good) == []
    assert F.gate_20r(bad) == ["rate=1.0001100"]


def test_campaign_output_paths_do_not_count_as_relevant_dirty_paths():
    assert F.is_campaign_output_path("results/SUPERSEDED/phase-20R/campaign_state.json")
    assert F.is_campaign_output_path("results/RAW/phase-20R/raw/example_tx.meta.json")
    assert F.is_campaign_output_path("logs/20r4_02_full.log")
    assert not F.is_campaign_output_path("measurements/l6_campaign_fine.py")


def test_deadline_raises_point_timeout():
    with pytest.raises(F.PointTimeout):
        with F.deadline(0.01, "unit-test"):
            time.sleep(0.05)


def test_campaign_summary_counts_timeout_history():
    plan = F.build_smoke_plan()
    state = {"stage": "smoke", "done_idx": [], "rows": [], "sentinels": [], "timeout_history": [{"idx": 0}]}

    summary = F.campaign_summary(state, plan)

    assert summary["n_timeout_history"] == 1
