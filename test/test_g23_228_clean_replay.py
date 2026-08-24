"""Controls for the clean-replay comparator and its locked baseline."""
from __future__ import annotations

import json

from tools import g23_228_clean_replay as C


def test_comparator_locks_numeric_trees_and_baseline_commit() -> None:
    assert C.BASELINE_COMMIT == "08b6879"
    assert C.SECTIONS == ("cells", "metrics", "live_definition_table")
    report = C.compare()
    assert report["all_numeric_trees_bit_exact"] is True
    assert report["total_mismatch_count"] == 0
    assert report["current_schema"] == "live_region_sweep_slaB/v3"
    assert report["pass"] is True
    assert report["current_clean_claim_pass"] is True
    assert report["source_commit_is_ancestor_of_comparison_head"] is True

    with open(C.OUTPUT, "r", encoding="utf-8") as handle:
        at_replay = json.load(handle)
    assert at_replay["current_head_matches_provenance"] is True
