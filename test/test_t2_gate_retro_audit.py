"""Canh cho audit hoi to cua gate v2.

Audit nay la BANG CHUNG rang viec sua gate KHONG lam doi phan quyet vong 3.
Neu no muc, bang chung do bien mat ma khong ai thay.
"""
from __future__ import annotations

import hashlib
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = ROOT / "results" / "PENDING" / "phase-T2" / "gate_v2_retro_audit.json"


@pytest.fixture(scope="module")
def doc():
    if not AUDIT.is_file():
        pytest.skip("chua chay tools/t2_gate_v2_retro_audit.py")
    return json.loads(AUDIT.read_text())


def test_audit_read_the_artifacts_that_actually_exist(doc):
    """sha256 ghi trong audit phai KHOP tep tren dia HOM NAY.

    Neu lech: hoac artifact vong 3 da bi sua (vi pham N6), hoac audit da doc
    mot ban khac. Ca hai deu lam audit vo gia tri.
    """
    for a in doc["audits"]:
        p = ROOT / a["artifact"]
        assert p.is_file(), a["artifact"]
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert h == a["sha256"], (
            "%s da doi ke tu khi audit chay -- artifact vong 3 la BAT DONG "
            "(ban giao T2 muc N6)" % a["artifact"])


def test_audit_covers_every_run_artifact_of_round_three(doc):
    """Audit mot phan la audit khong ket luan duoc gi.

    "Artifact cua MOT lenh chay" = co CA `rows` VA `cell`. Tieu chi chi
    `rows` la qua rong: level_probe_posthoc.json cung co `rows` (moi hang
    la mot diem (o, tau) cua probe) nhung khong chay qua gate nao, nen no
    khong phai mot lenh chay va khong co gi de audit.
    """
    src = ROOT / "results" / "PENDING" / "phase-T2" / "sweep_r3"
    runs = []
    for p in sorted(src.glob("*.json")):
        d = json.loads(p.read_text())
        if isinstance(d, dict) and "rows" in d and "cell" in d:
            runs.append(p.name)
    assert doc["n_artifacts"] == len(runs), (doc["n_artifacts"], runs)
    audited = {pathlib.Path(a["artifact"]).name for a in doc["audits"]}
    assert audited == set(runs), sorted(set(runs) ^ audited)


def test_audit_states_the_effect_on_adjudication_explicitly(doc):
    """Ket qua phai duoc PHAT BIEU, khong de nguoi doc tu suy."""
    assert "adjudication_effect" in doc
    assert doc["gate_version_audited"] >= 2
    if doc["n_verdict_changed"] == 0:
        assert "KHONG DOI" in doc["adjudication_effect"]
    else:
        assert "KHONG duoc lat" in doc["adjudication_effect"]


def test_no_round_three_verdict_was_flipped_by_the_audit(doc):
    """Audit hoi to duoc phep THEM thong tin, khong duoc RUT so lieu.

    Test nay KHONG kiem 'so thay doi bang 0' -- do la mot KET QUA, co the
    khac 0 mot cach hop le. No kiem rang mau so va verdict DA KY khong bi
    dung toi  [NT 56: gate tinh hop le tach khoi gate ket qua].
    """
    adj = (ROOT / "results" / "PENDING" / "phase-T2" / "sweep_r3"
           / "adjudication_r3.json")
    signed = json.loads(adj.read_text())
    assert signed["summary"]["n_total"] == 7, "mau so 7 da ky, khong duoc doi"
    assert signed["summary"]["n_pass"] == 3, "verdict da ky, khong duoc lat"
