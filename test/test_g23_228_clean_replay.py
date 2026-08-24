"""Controls for the clean-replay comparator and its locked baseline."""
from __future__ import annotations

from tools import g23_228_clean_replay as C


def test_comparator_locks_numeric_trees_and_baseline_commit() -> None:
    assert C.BASELINE_COMMIT == "08b6879"
    assert C.SECTIONS == ("cells", "metrics", "live_definition_table")
    report = C.compare()
    assert report["all_numeric_trees_bit_exact"] is True
    assert report["total_mismatch_count"] == 0
    if report["current_schema"] == "live_region_sweep_slaB/v3":
        assert report["pass"] is True
        assert report["current_clean_claim_pass"] is True
        assert report["current_head_matches_provenance"] is True
    else:
        # Before the one-time clean replay, the 08b6879 artifact is the dirty v2.
        assert report["current_schema"] == "live_region_sweep_slaB/v2"
        assert report["pass"] is False
