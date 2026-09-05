#!/usr/bin/env python3
"""Refuse to overwrite an artifact that is referenced by SHA256.

Why this exists: `tools/g2_kill_test.py` wrote to a fixed filename, so an
instrumented rerun silently overwrote the run whose hash
`docs/phase-G/60-kill-test-results.md` records. It was noticed and the file was
restored from git, but noticing is not a control. Overwriting a signed contract
is deleting evidence, not updating it.

    from tools.artifact_guard import write_contract_artifact
    write_contract_artifact(path, payload)          # refuses if path exists
    write_contract_artifact(path, payload, allow_overwrite=True)   # deliberate
"""
from __future__ import annotations

import hashlib
import json
import os
import pwd
from pathlib import Path
from typing import Any, Mapping


def sha256_of(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_contract_artifact(
    path: str | Path,
    payload: Mapping[str, Any],
    *,
    allow_overwrite: bool = False,
    chown_to_sudo_user: bool = True,
) -> str:
    """Write `payload` as JSON, refusing to clobber an existing artifact.

    Returns the SHA256 of what was written, so a caller can record it.
    """
    target = Path(path)
    if target.exists() and not allow_overwrite:
        raise FileExistsError(
            f"{target} already exists and may be referenced by SHA256.\n"
            f"  existing sha256: {sha256_of(target)}\n"
            "Write to a new name (for example *_run3.json), or pass\n"
            "allow_overwrite=True only after recording why in the decision log."
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if chown_to_sudo_user:
        name = os.environ.get("SUDO_USER")
        if name:
            info = pwd.getpwnam(name)
            os.chown(target, info.pw_uid, info.pw_gid)
    return sha256_of(target)
