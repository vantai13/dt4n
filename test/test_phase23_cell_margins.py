"""Gates for Phase 23 cross-cell G23-17 audits."""

from __future__ import annotations

import os

import pytest

from cert import phase23_cell_margins as CM


def _require_cell_artifacts() -> None:
    for path in CM.DEFAULT_CELLS.values():
        if not os.path.exists(path):
            pytest.skip("thieu artifact G23-17 cross-cell: %s" % path)
        meta = path[:-8] + ".json"
        if not os.path.exists(meta):
            pytest.skip("thieu metadata G23-17 cross-cell: %s" % meta)


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
