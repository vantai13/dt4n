"""CI annotations must retain the state needed to diagnose a flaky failure."""
from __future__ import annotations

import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_annotation_keeps_multiline_failure_detail(tmp_path: pathlib.Path) -> None:
    report = tmp_path / "pytest.xml"
    report.write_text(
        """<?xml version='1.0' encoding='utf-8'?>
<testsuites><testsuite failures="1"><testcase classname="test.test_n1" name="case">
<failure message="AssertionError: replay failed">trace head
N1_STATE={&quot;affinity&quot;:[0],&quot;sha&quot;:&quot;abc&quot;}
STDERR_TAIL=real cause</failure></testcase></testsuite></testsuites>
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "tools/ci_annotate_failures.py", str(report)],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    assert "N1_STATE=" in result.stdout
    assert "STDERR_TAIL=real cause" in result.stdout
    assert "%0A" in result.stdout
