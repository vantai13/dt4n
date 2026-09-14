"""The Wave-4 digest capture must be exact rather than glob-based."""
import pytest

from tools import capture_wave4_digests as D


def test_planned_digest_set_is_exact_and_unique() -> None:
    paths = D.planned_parquets()
    assert len(paths) == len(set(paths)) == 12
    assert sum("/LIVE/" in str(path) for path in paths) == 8
    assert sum("/SUPERSEDED/" in str(path) for path in paths) == 4


# [20R2.9-C/C-3] G23-222: `D.build()` doi CA 12 parquet wave-4 (LIVE/phase-21R
# *_measured_v7 va SUPERSEDED *_legacy_sawtooth_51ms, ~67 MB moi file,
# .gitignore:167-168). Ke hoach digest o tren VAN chay tren clone sach.
@pytest.mark.custody
def test_digest_build_covers_passing_ledger() -> None:
    payload = D.build()
    assert payload["schema"] == "dt4n.surviving_digests.v2"
    assert payload["ledger"]["jobs"] == payload["ledger"]["passed"] == 12
    assert len(payload["files"]) == 12
