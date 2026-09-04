"""Synthetic G-A016 artifacts must point to commits containing their tools."""
from __future__ import annotations

import json
import hashlib
import subprocess
from pathlib import Path


ARTIFACT_ROOT = Path("results/SMOKE/phase-G")


def test_synthetic_artifacts_declare_a_commit_that_contains_their_tool():
    artifacts = sorted(ARTIFACT_ROOT.glob("g3_emit*_a016.json"))
    artifacts += sorted(ARTIFACT_ROOT.glob("host_jitter_*_quiesce.json"))
    assert len(artifacts) >= 4
    for artifact in artifacts:
        payload = json.loads(artifact.read_text(encoding="utf-8"))
        commit = payload["git_hash"]
        tool = payload["tool_path"]
        probe = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}:{tool}"],
            capture_output=True,
            check=False,
        )
        assert probe.returncode == 0, f"{artifact}: {commit} lacks {tool}"
        digest = hashlib.sha256(Path(tool).read_bytes()).hexdigest()
        assert digest == payload["tool_sha256"], (
            f"{artifact}: tool_sha256 does not match {tool}"
        )
