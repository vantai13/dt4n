"""Gates for Phase 23 cross-cell interpretation."""

from __future__ import annotations

import os

import pytest

from cert import phase23_cross_cell as CC


def _require_inputs(paths) -> None:
    for path in paths:
        if not os.path.exists(path):
            pytest.skip("thieu artifact cross-cell: %s" % path)


def test_G23_23_lift_law_reconstructs_break_even_delta() -> None:
    """Benefit is exactly lift > swing on each rejected set."""
    _require_inputs([CC.DEFAULT_G23_17A, *CC.DEFAULT_AUDITS.values()])
    out = CC.lift_law_report()
    assert out["gate"] == "G23-23"
    assert out["checks"]["identity_pass"] is True
    assert out["checks"]["all_signs_match"] is True
    assert out["checks"]["n_rows"] == 12
    assert out["checks"]["c3_fails_both_new_cells_at_078"] is True
    assert out["checks"]["b3_beats_h2_at_078"] is True

    h2_b3 = next(
        row
        for row in out["rows"]
        if row["cell"] == "h2@0.700" and row["selector"] == "B3_aoi"
    )
    assert h2_b3["beneficial_by_lift"] is True
    assert h2_b3["delta_vs_anchor"] < 0.0
