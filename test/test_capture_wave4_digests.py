"""The Wave-4 digest capture must be exact rather than glob-based."""
from tools import capture_wave4_digests as D


def test_planned_digest_set_is_exact_and_unique() -> None:
    paths = D.planned_parquets()
    assert len(paths) == len(set(paths)) == 12
    assert sum("/LIVE/" in str(path) for path in paths) == 8
    assert sum("/SUPERSEDED/" in str(path) for path in paths) == 4


def test_digest_build_covers_passing_ledger() -> None:
    payload = D.build()
    assert payload["schema"] == "dt4n.surviving_digests.v2"
    assert payload["ledger"]["jobs"] == payload["ledger"]["passed"] == 12
    assert len(payload["files"]) == 12
