from tools.check_phase_g_custody import evaluate


def test_local_phase_g_gate_is_open_but_public_archive_is_not():
    result = evaluate()

    assert result["pass"] is True
    assert result["basis"] == "USER_ATTESTED_OFFSITE_BACKUP_WAIVER"
    assert result["phase_g_local_work_allowed"] is True
    assert result["public_archival_claim_allowed"] is False
    assert result["historical_cleanup_allowed"] is False
