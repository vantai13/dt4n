#!/usr/bin/env python3
"""Execution-environment provenance for live measurement rows.

Layer 1 (data): seed + trajectory_digest + schedule_digest.
Layer 2 (code): git commit.
Layer 3 (environment): interpreter and platform fingerprint.

Without layer 3, a digest is only half a claim: Amendment 12 showed that the
same code and input can diverge across Python versions at ULP scale.
"""

from __future__ import annotations

import platform
import subprocess
import sys
from typing import Any, Dict


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return ""


def env_fingerprint() -> Dict[str, Any]:
    """Fingerprint the environment that produced a campaign row."""
    status = _git("status", "--porcelain")
    return {
        "python_version": sys.version.split()[0],
        "python_version_info": list(sys.version_info[:3]),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "git_commit": _git("rev-parse", "HEAD") or "unknown",
        "git_dirty": bool(status),
    }
