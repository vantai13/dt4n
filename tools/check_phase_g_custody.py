#!/usr/bin/env python3
"""Check the narrowly scoped custody gate for local Phase G work."""
from __future__ import annotations

import json
from pathlib import Path


MANIFEST = Path("results/DATA_MANIFEST.json")
WAIVER_STATUS = "OPEN_BY_USER_CUSTODY_WAIVER"


def evaluate() -> dict[str, object]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    doi = manifest.get("doi")
    custody = manifest.get("custody", {})
    backup = custody.get("offsite_backup", {})
    local = custody.get("phase_g_local_gate", {})

    public_archive = bool(isinstance(doi, str) and doi.startswith("10."))
    waiver = bool(
        backup.get("status") == "USER_ATTESTED_PRESENT"
        and local.get("status") == WAIVER_STATUS
        and local.get("public_doi_equivalent") is False
        and local.get("allows_historical_data_cleanup") is False
        and local.get("allows_claim_of_public_archival") is False
    )
    return {
        "pass": public_archive or waiver,
        "basis": "PUBLIC_VERSION_DOI" if public_archive else (
            "USER_ATTESTED_OFFSITE_BACKUP_WAIVER" if waiver else "NONE"
        ),
        "doi": doi,
        "phase_g_local_work_allowed": public_archive or waiver,
        "public_archival_claim_allowed": public_archive,
        "historical_cleanup_allowed": public_archive,
    }


def main() -> int:
    result = evaluate()
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
