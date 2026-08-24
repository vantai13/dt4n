"""Gates for Phase 23 cross-cell G23-17 audits."""

from __future__ import annotations

import json
import os

import pytest

from cert import phase23_cell_margins as CM


HISTORICAL_REPORTS = {
    "g23-17a": (
        CM.run_report,
        "results/SUPERSEDED/phase-23/g23_17a_cell_margins.json",
    ),
    "g23-17b": (
        CM.run_code_sanity_report,
        "results/SUPERSEDED/phase-23/g23_17b_code_sanity.json",
    ),
    "g23-17c": (
        CM.run_scale_sla_report,
        "results/SUPERSEDED/phase-23/g23_17c_scale_and_sla.json",
    ),
}


def _require_cell_artifacts() -> None:
    for path in CM.DEFAULT_CELLS.values():
        if not os.path.exists(path):
            pytest.skip("thieu artifact G23-17 cross-cell: %s" % path)
        meta = CM._meta_path(path)
        if not os.path.exists(meta):
            pytest.skip("thieu metadata G23-17 cross-cell: %s" % meta)


def _without_artifact_identity(value, parent: str = ""):
    """Bo dung bon truong du kien doi khi sua L85; giu moi con so."""
    if isinstance(value, dict):
        return {
            key: _without_artifact_identity(item, parent=key)
            for key, item in value.items()
            if key not in {"artifact", "artifact_sha256"}
            and not (parent == "" and key == "provenance")
            and not (parent == "metadata" and key in {"path", "sha256"})
        }
    if isinstance(value, list):
        return [_without_artifact_identity(item, parent=parent) for item in value]
    return value


def test_G23_17c_decomposes_regret_ratio_into_three_factors() -> None:
    """Mechanism #8 must live in the artifact, not only in prose."""
    _require_cell_artifacts()
    out = CM.run_scale_sla_report(CM.DEFAULT_CELLS, rowset="test")
    assert out["checks"]["three_factor_identity_matches_regret_ratio"] is True
    assert out["checks"]["poisson_0p850_true_effect_ratios_near_one_within_tol"] is True
    assert out["checks"]["h2_true_effect_ratios_both_below_0p70"] is True

    rows = {row["cell"]: row for row in out["rows"]}
    h2 = rows["h2@0.700"]
    assert h2["regret_ratio_matches_m_true_ratio_within_tol"] is False
    assert h2["ratio_gap_fraction_of_m_true_ratio"] > 0.15
    for row in rows.values():
        assert row["three_factor_abs_error_vs_regret_ratio"] <= 1e-12


@pytest.mark.parametrize("audit", sorted(HISTORICAL_REPORTS))
def test_G23_225_canonical_input_preserves_published_numbers(audit: str) -> None:
    """L85 sua danh tinh input, khong duoc am tham sua ket luan G23-17."""
    _require_cell_artifacts()
    build, historical_path = HISTORICAL_REPORTS[audit]
    with open(historical_path, encoding="utf-8") as handle:
        historical = json.load(handle)
    current = build(CM.DEFAULT_CELLS, rowset="test")
    assert _without_artifact_identity(current) == _without_artifact_identity(
        historical
    )
