#!/usr/bin/env python3
"""Tests for the direct Phase 14B sync-headroom meter."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, ".")

from measurements.sync_headroom import main  # noqa: E402


def test_sync_regret_is_not_bounded_by_phase14a_margin_regret():
    """Sync regret has a floor and is not bounded by Phase 14A q-margin regret."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "sync.json"
        code = main([
            "--z-values",
            "5",
            "--cases",
            "20",
            "--mc-samples",
            "50",
            "--objective",
            "cvar",
            "--cvar-alpha",
            "0.1",
            "--seed",
            "123",
            "--out",
            str(out),
        ])

        assert code == 0
        payload = json.loads(out.read_text())
        row = payload["rows"][0]
        phase14a_regret = 0.028867
        assert row["sync_regret_when_disagree"] > 10.0 * phase14a_regret
        assert row["gap_mean"] > 0.5


def test_sync_headroom_z0_is_zero_for_current_snapshot():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "sync.json"
        code = main([
            "--z-values",
            "0",
            "--cases",
            "5",
            "--mc-samples",
            "10",
            "--seed",
            "0",
            "--out",
            str(out),
        ])

        assert code == 0
        payload = json.loads(out.read_text())
        row = payload["rows"][0]
        assert row["gap_mean"] == 0.0
        assert row["disagree_fresh"] == 0.0


def _run_as_script():
    tests = [
        test_sync_regret_is_not_bounded_by_phase14a_margin_regret,
        test_sync_headroom_z0_is_zero_for_current_snapshot,
    ]
    for test in tests:
        test()
        print(f"  PASS  {test.__name__}")
    print(f"\n{len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    _run_as_script()
