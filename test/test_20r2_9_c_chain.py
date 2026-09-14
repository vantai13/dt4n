"""20R2.9-C: portable CI, tracked ledgers, and explained nullable fields."""
from __future__ import annotations

import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
B3 = ROOT / "docs/phase-20R2/B3-axis-marginal.json"


def test_ci_checkout_fetches_history_and_tags() -> None:
    text = (ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    assert "fetch-depth: 0" in text
    assert "fetch-tags: true" in text


def test_t2_run_ledger_is_part_of_a_clean_clone() -> None:
    path = "results/PENDING/phase-T2/sweep/run_log.jsonl"
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", path], cwd=ROOT,
        check=True, capture_output=True, text=True,
    )


def _unexplained_nulls(value, pointer=""):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_pointer = pointer + "/" + key
            if child is None:
                reason = value.get(key + "_undefined_reason")
                if not isinstance(reason, str) or not reason.strip():
                    found.append(child_pointer)
            found.extend(_unexplained_nulls(child, child_pointer))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_unexplained_nulls(child, pointer + "/" + str(index)))
    return found


def test_every_b3_null_has_a_local_reason() -> None:
    assert not _unexplained_nulls(json.loads(B3.read_text(encoding="utf-8")))
