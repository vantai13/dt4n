"""Custody and verdict checks for the G-A004 paired split."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path("results/SMOKE/phase-G")


def load(name: str) -> dict[str, object]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_power_passed_without_reading_held_out_correlations():
    power = load("g_a004_paired_power.json")
    assert power["held_out_correlations_read"] is False
    assert power["gates"]["overall_pass"] is True
    assert power["gates"]["all_pairs_success_probability_wilson_lower"] >= 0.95
    assert power["gates"]["median_success_probability_wilson_lower"] >= 0.90


def test_held_out_verdict_is_not_softened_by_median_pass():
    result = load("g_a004_split_sample.json")
    assert result["held_out_correlations_read"] is True
    assert result["summary"]["dynamic_range_gate_pass"] is True
    assert result["summary"]["median_error_gate_pass"] is True
    assert result["summary"]["edge_pairs_error_pass"] == 5
    assert result["pairs"]["uA-uB"]["pair_error_gate_pass"] is False
    assert result["summary"]["verdict"] == "FAIL"
    assert result["summary"]["G1_closed"] is False


def test_test_artifact_pins_the_power_artifact_bytes():
    result = load("g_a004_split_sample.json")
    power_path = Path(result["power_artifact"])
    digest = hashlib.sha256(power_path.read_bytes()).hexdigest()
    assert digest == result["power_artifact_sha256"]
