import json
from pathlib import Path

import pytest

from tools.check_phase_g_custody import evaluate


def test_local_phase_g_gate_is_open_but_public_archive_is_not():
    result = evaluate()

    assert result["pass"] is True
    assert result["basis"] == "VERIFIED_LOCAL_BACKUP_SEAL"
    assert result["phase_g_local_work_allowed"] is True
    assert result["public_archival_claim_allowed"] is False
    assert result["historical_cleanup_allowed"] is False


def test_verified_seal_opens_campaign_execution_without_a_doi():
    result = evaluate()

    assert result["campaign_execution_allowed"] is True
    assert result["doi"] is None


def test_seal_is_reverified_not_trusted_from_the_manifest(tmp_path, monkeypatch):
    """A seal whose file no longer matches must fall back, not silently pass."""
    import tools.check_phase_g_custody as module

    manifest = json.loads(Path("results/DATA_MANIFEST.json").read_text())
    manifest["custody"]["local_backup_seal"]["seal_sha256"] = "0" * 64
    forged = tmp_path / "DATA_MANIFEST.json"
    forged.write_text(json.dumps(manifest))
    monkeypatch.setattr(module, "MANIFEST", forged)

    result = module.evaluate()
    assert result["basis"] == "USER_ATTESTED_OFFSITE_BACKUP_WAIVER"
    assert result["campaign_execution_allowed"] is False
    assert "changed" in result["seal_detail"]


def test_shallow_check_still_catches_a_truncated_archive(tmp_path, monkeypatch):
    """Size is the cheap half of the archive check; it runs without --deep."""
    import tools.check_phase_g_custody as module

    manifest = json.loads(Path("results/DATA_MANIFEST.json").read_text())
    record = manifest["custody"]["local_backup_seal"]
    seal = json.loads(Path(record["seal_path"]).read_text())
    seal["artifacts"]["repo_bundle"]["bytes"] += 1
    forged_seal = tmp_path / "SEAL.json"
    forged_seal.write_text(json.dumps(seal))
    record["seal_path"] = str(forged_seal)
    record["seal_sha256"] = module._sha256(forged_seal)
    forged_manifest = tmp_path / "DATA_MANIFEST.json"
    forged_manifest.write_text(json.dumps(manifest))
    monkeypatch.setattr(module, "MANIFEST", forged_manifest)

    result = module.evaluate()
    assert result["campaign_execution_allowed"] is False
    assert "resized" in result["seal_detail"]


def test_seal_cannot_assert_public_archival():
    import tools.check_phase_g_custody as module

    held, detail = module._seal_holds(
        {"status": "VERIFIED_LOCAL_BACKUP_SEAL", "allows_claim_of_public_archival": True}
    )
    assert held is False and "public archival" in detail


def test_seal_file_itself_never_carries_a_doi():
    manifest = json.loads(Path("results/DATA_MANIFEST.json").read_text())
    seal = json.loads(Path(manifest["custody"]["local_backup_seal"]["seal_path"]).read_text())
    assert seal["doi"] is None
    assert seal["published_doi"] is None
    assert seal["is_doi_equivalent"] is False
    assert seal["public_archival_gate_pass"] is False
