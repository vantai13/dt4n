#!/usr/bin/env python3
"""Tests for Phase 14 noise-floor calibration."""

import json
import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, ".")

from measurements.noise_floor import main  # noqa: E402


def test_noise_floor_can_use_reward3_v3_and_write_json():
    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "noise.json"
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main([
                "--topology",
                "routing3",
                "--reward-model",
                "r_v3",
                "--seeds",
                "2",
                "--cases",
                "2",
                "--mc-samples",
                "1",
                "--out",
                str(out_path),
            ])

        assert code == 0
        assert "reward_model      : r_v3" in stdout.getvalue()

        payload = json.loads(out_path.read_text())
        assert payload["reward_model"] == "r_v3"
        assert payload["estimator"] == "honest"
        assert payload["reward_model_path"] == "rl/routing3/reward3_v3.py"
        assert len(payload["reward_model_sha"]) == 12
        assert "threshold_2x" in payload


def _run_as_script():
    tests = [
        test_noise_floor_can_use_reward3_v3_and_write_json,
    ]
    for test in tests:
        test()
        print(f"  PASS  {test.__name__}")
    print(f"\n{len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    _run_as_script()
