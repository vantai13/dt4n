"""Verify the one documented >5 MiB Git custody exception against staged bytes.

This is not a generic size-limit bypass. The allowlisted path and its expected
digest come from the existing frozen measurement certificate, and the staged
custody decision must explicitly opt into Git distribution.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys

TARGET = 'results/SMOKE/phase-G2/g3b_sigma_tau_series.npz'
RECORD = 'results/SMOKE/phase-G2/g3b_series_git_custody.json'
CERT = 'results/LIVE/phase-G2/measurement_path_cert_v2.json'


def matches_decision(path, content, decision, certificate):
    expected = certificate.get('evidence_sha256', {}).get(TARGET)
    return bool(path == TARGET and expected
                and decision.get('classification') == 'CITED_RAW'
                and decision.get('git_distribution_allowed') is True
                and decision.get('path') == TARGET
                and decision.get('bytes') == len(content)
                and decision.get('sha256') == expected
                and hashlib.sha256(content).hexdigest() == expected)


def main():
    if len(sys.argv) != 2 or sys.argv[1] != TARGET:
        return 1
    try:
        def staged(path):
            return subprocess.check_output(['git', 'show', ':' + path], stderr=subprocess.DEVNULL)
        ok = matches_decision(sys.argv[1], staged(TARGET), json.loads(staged(RECORD)),
                              json.loads(staged(CERT)))
    except (OSError, ValueError, subprocess.SubprocessError):
        return 1
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
