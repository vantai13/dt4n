import json
from pathlib import Path


ARTIFACT = Path("results/SMOKE/phase-G/g_a005_reclassification.json")


def load():
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_reclassification_does_not_rescue_g_a004():
    artifact = load()
    assert artifact["scope"]["changes_G_A004_numeric_verdict"] is False
    assert artifact["scope"]["G_A004_verdict"] == "FAIL"
    assert artifact["scope"]["G1_closed"] is False
    assert artifact["scope"]["pipeline_certified"] is False


def test_power_did_not_refit_the_full_pipeline():
    artifact = load()
    assert artifact["pipeline_mismatch"]["full_pipeline_refit_in_power"] is False
    assert artifact["scope"]["component_cause_identified_by_G_A004"] is False


def test_sensitivity_changes_result_without_condition_number_warning():
    solves = load()["uA_uB_sensitivity"]["solves"]
    assert solves["first_half_G_A004"]["pair_gate_pass"] is False
    assert solves["full_run_posthoc"]["pair_gate_pass"] is True
    assert solves["second_half_inferred_posthoc"]["pair_gate_pass"] is True
    assert all(row["cond_A"] < 10.0 for row in solves.values())


def test_h6c_is_explicitly_posthoc():
    grouping = load()["H6_grouping_posthoc"]
    assert grouping["old_H6b_same_telemetry_side_retained_as_confirmatory"] is False
    assert "fresh/direct static-control" in grouping["warning"]
