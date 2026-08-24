"""Locked controls for the exogenous-SLA live-region sweep (Lesson 23.21h)."""
from __future__ import annotations

import json
import os

import pytest

from cert import live_region_sweep as L


def _load(path: str) -> dict:
    if not os.path.exists(path):
        pytest.skip("artifact chua duoc sinh: %s" % path)
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_preregistered_cells_thresholds_and_output_are_locked() -> None:
    assert tuple(L.NEW_SPECS) == (
        "poisson@0.875",
        "poisson@0.900",
        "h2@0.650",
        "h2@0.675",
    )
    assert len(L.ANALYZED_CELLS) == len(set(L.ANALYZED_CELLS)) == 12
    assert L.DOMAIN_LIMIT == 1e-4
    assert L.LIVE_THRESHOLD == 0.05
    assert L.OUTPUT.startswith("results/LIVE/")
    assert all("parquet" not in spec for spec in L.NEW_SPECS.values())


def test_missing_wave4_template_fails_loudly() -> None:
    with pytest.raises(SystemExit, match="Truyen --calib-template"):
        L._calib_path(L.NEW_SPECS["h2@0.650"], None)


def test_exogenous_loader_preserves_domain_control_and_none_semantics() -> None:
    report = L.load_sla_exogenous()
    assert len(report["cells"]) == 14
    assert report["fallback_triggered"] is None
    assert len(report["requested_cells"]) == 4
    checked = [cell for cell in report["cells"] if "domain_control" in cell]
    assert len(checked) == 4
    for cell in checked:
        checks = cell["domain_control"]["rows"]
        assert len(checks) == 2 * len(L.SEEDS)
        assert {row["sigma_source"] for row in checks} == {
            "sla_regime",
            "calib_builder",
        }
        assert cell["domain_control"]["eligibility_distribution"] == "calib_builder"


def test_authoritative_regime_crosscheck_is_12_of_12() -> None:
    rows = L.authoritative_regimes(L.ANALYZED_CELLS)
    assert len(rows) == 12
    assert all(row["match"] for row in rows.values())
    assert sum(row["recomputed_regime"] == "LIVE" for row in rows.values()) == 6


def test_prepare_sla_is_removed_with_teaching_error(capsys) -> None:
    with pytest.raises(SystemExit):
        L.main(["--prepare-sla"])
    assert "SLA.calibrate_cell" in capsys.readouterr().err


def test_clean_replay_rejects_tracked_edits(monkeypatch) -> None:
    monkeypatch.setattr(L, "git", lambda *args: " M cert/live_region_sweep.py")
    with pytest.raises(SystemExit, match="G23-228"):
        L._require_clean_worktree()


def test_clean_replay_accepts_clean_tracked_tree(monkeypatch) -> None:
    monkeypatch.setattr(L, "git", lambda *args: "")
    L._require_clean_worktree()


def test_generated_artifact_has_all_new_gates_and_validity() -> None:
    report = _load(L.OUTPUT)
    assert len(report["analyzed_cells"]) == 12
    assert report["controls"]["NC_H_checked"] == 4
    assert report["controls"]["NC_H_passed"] == 4
    assert report["controls"]["NC_K_fallback_triggered"] is None
    assert report["controls"]["G23_214_regime_crosscheck"]["matched"] == 12
    assert report["controls"]["G23_214_regime_crosscheck"]["pass"] is True
    assert report["validity"]["aoi_axis"]["label"] == "measured_v7_uniform"
    assert report["validity"]["sla_axis"]["label"] == "exogenous_g114_S-B"
    expected_verdict = {
        "M_176_A_B_agreement_at_least_8_of_12",
        "M_177_rho_hit_in_0_900_0_925",
        "M_178_poisson_err_neo_both_in_0_20_0_30",
        "M_179_A_live_twin_deg_spread_in_1_00_1_50",
        "M_57_h2_A_live_lift_minus_swing_negative",
        "M_47b_delta_nonpositive_all_A_live_heldout",
    }
    if report["schema"] == "live_region_sweep_slaB/v2":
        # Kept only until the G23-228 clean replay replaces the old headline.
        assert set(report["verdict"]) == expected_verdict | {
            "M_54_poisson_sign_monotone"
        }
    else:
        assert report["schema"] == "live_region_sweep_slaB/v3"
        assert set(report["verdict"]) == expected_verdict
        diagnostic = report["diagnostics"]["M_54_poisson_sign_monotone"]
        assert diagnostic["status"] == "DIAGNOSTIC"
        assert diagnostic["chance_one_positive_in_last_position"] == 0.25
        assert diagnostic["evidence_bits"] == 2.0
        assert diagnostic["counted_in_verdict"] is False
        structure = report["exploratory"]["M_180_mode_structure"]
        assert structure["status"] == "EXPLORATORY_POST_HOC"
        assert structure["counted_as_preregistered"] is False
        assert structure["counts"] == {
            "poisson": {
                "LIVE": {"helpful": 0, "harmful": 3, "neutral": 0},
                "non_LIVE": {"helpful": 3, "harmful": 0, "neutral": 0},
            },
            "h2": {
                "LIVE": {"helpful": 3, "harmful": 0, "neutral": 0},
                "non_LIVE": {"helpful": 1, "harmful": 0, "neutral": 2},
            },
        }
        assert report["controls"]["NC_H_stress_checked"] == 4
        assert report["controls"]["NC_H_stress_passed"] == 0
        assert report["field_semantics"]["delta_system_vs_neo"][
            "compatibility_alias_for"
        ] == "delta_fallback_vs_twin_weighted"


def test_M179_recomputes_over_every_A_live_cell() -> None:
    report = _load(L.OUTPUT)
    live = report["metrics"]["M_179_A_live_cells"]
    values = [report["cells"][cell]["lift_swing_F2"]["twin_deg"] for cell in live]
    assert report["metrics"]["M_179_twin_deg_spread"] == pytest.approx(
        max(values) / min(values), abs=1e-15
    )
