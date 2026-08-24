"""G23-224: phan tang artifact khong bao gio duoc ghi de dich."""

from __future__ import annotations

import importlib.util
from pathlib import Path


_PATH = Path(__file__).resolve().parents[1] / "tools" / "tier_results.py"
_SPEC = importlib.util.spec_from_file_location("tier_results", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
T = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(T)


def test_G23_224_existing_destination_stops_before_any_move(
    tmp_path, monkeypatch, capsys
) -> None:
    root = tmp_path / "results"
    src = root / "phase-X" / "artifact.json"
    dst = root / "SUPERSEDED" / "phase-X" / "artifact.json"
    src.parent.mkdir(parents=True)
    dst.parent.mkdir(parents=True)
    src.write_bytes(b"new source bytes")
    dst.write_bytes(b"old destination evidence")
    map_out = tmp_path / "map.tsv"

    monkeypatch.setattr(T, "ROOT", str(root))
    monkeypatch.setattr(T, "_tracked", lambda: set())

    rc = T.main(["--apply", "--map-out", str(map_out)])

    assert rc == 2
    assert src.read_bytes() == b"new source bytes"
    assert dst.read_bytes() == b"old destination evidence"
    assert not map_out.exists(), "preflight phai dung truoc ca output phu"
    err = capsys.readouterr().err
    assert "DUNG" in err
    assert str(src) in err and str(dst) in err


def test_no_replace_move_keeps_atomic_publication_without_clobber(tmp_path) -> None:
    src = tmp_path / "src.bin"
    dst = tmp_path / "dst.bin"
    src.write_bytes(b"complete artifact")

    T._move_untracked_no_replace(str(src), str(dst))

    assert not src.exists()
    assert dst.read_bytes() == b"complete artifact"


def test_no_replace_move_rejects_a_racing_destination(tmp_path) -> None:
    src = tmp_path / "src.bin"
    dst = tmp_path / "dst.bin"
    src.write_bytes(b"new")
    dst.write_bytes(b"old")

    try:
        T._move_untracked_no_replace(str(src), str(dst))
    except FileExistsError:
        pass
    else:
        raise AssertionError("positive control did not detect destination collision")

    assert src.read_bytes() == b"new"
    assert dst.read_bytes() == b"old"
