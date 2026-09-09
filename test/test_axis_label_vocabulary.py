"""20R2: an axis label must come from the registry, not from a keystroke.

Vi sao can tep nay (do duoc 2026-09-09):
`test_no_stale_axes` chi hoi "nhan CO NAM TRONG approved_for_live khong?".
Voi artifact o PENDING/ no con hoi nguoc lai: "nhan KHONG duoc nam trong
approved_for_live" (vi PENDING nghia la chua duyet). Ca hai cau deu DUNG voi
mot chuoi bia dat: `MIXED_OR_MISSING` khong nam trong danh sach duyet, nen no
QUA test PENDING mot cach RONG (vacuous pass) -- dung lop loi ma chinh
`test_no_stale_axes.py` canh bao o muc `PENDING_NO_VALIDITY_GRANDFATHERED`.

`results/PENDING/phase-20R2/parquet_recovery.json` da mang dung nhan do, trong
khi 9/9 muc `source_axes` cua no deu ghi `self_calibrated` + `aoi_axis_free`.
Nhan bia khong chi thua -- no NOI SAI mot su that ma artifact da co san.

Nen test nay hoi cau con thieu: nhan co thuoc TU VUNG DA DANG KY khong?
Tu vung = nhan trong docs/phase-23/axis_registry.json, cong hai gia tri dac
biet do chinh ma nguon dinh nghia (`UNREGISTERED`, `ROLE_AXIS_FREE`).
Them mot nhan moi bay gio bat buoc phai sua registry -- tuc phai viet amendment.
"""
import glob
import json
import os

import pytest

from measurements.validity import ROLE_AXIS_FREE, UNREGISTERED

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(REPO, "docs", "phase-23", "axis_registry.json")
TIERS = ("LIVE", "PENDING")


def _registry() -> dict:
    with open(REGISTRY, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _vocabulary() -> dict:
    """Nhan hop le cho moi truc, SUY TU registry chu khong go tay o day."""
    reg = _registry()
    vocab = {}
    for axis in ("aoi_axis", "sla_axis"):
        labels = {entry["label"] for entry in reg[axis].values()}
        labels.add(UNREGISTERED)  # fail-loud sentinel, do validity.py dinh nghia
        vocab[axis] = labels
    # Artifact vai tro AXIS_FREE ghi chinh ten vai tro vao aoi_axis.label.
    vocab["aoi_axis"].add(ROLE_AXIS_FREE)
    return vocab


def _artifacts() -> list[str]:
    out = []
    for tier in TIERS:
        root = os.path.join(REPO, "results", tier)
        out += sorted(glob.glob(os.path.join(root, "**", "*.json"), recursive=True))
    return out


def _labelled(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        try:
            payload = json.load(fh)
        except json.JSONDecodeError:
            return None
    if not isinstance(payload, dict):
        return None
    v = payload.get("validity")
    return v if isinstance(v, dict) else None


@pytest.mark.parametrize("path", _artifacts(), ids=lambda p: os.path.relpath(p, REPO))
def test_axis_labels_come_from_the_registry(path):
    """Nhan phai SUY TU registry. Mot chuoi bia dat phai lam DO test nay."""
    v = _labelled(path)
    if v is None:
        pytest.skip("khong co khoi validity")
    vocab = _vocabulary()
    rel = os.path.relpath(path, REPO)
    for axis in ("aoi_axis", "sla_axis"):
        block = v.get(axis)
        if not isinstance(block, dict) or "label" not in block:
            continue
        label = block["label"]
        if label is None:
            # `null` la CACH NOI "artifact nay khong cham truc do" bang chinh
            # co che da co cua JSON, khong phai mot tu moi. Do dung la dieu bai
            # hoc C2 doi: khi chua xac dinh, dung co che DA CO, dung phat minh
            # tu vung. Vai artifact `measures_axis` (sla_manifest_exogenous_*)
            # dung dung duong nay -- do duoc 2026-09-09, 4 tep o LIVE/phase-20R.
            continue
        assert label in vocab[axis], (
            f"{rel}: {axis}.label = {label!r} KHONG co trong tu vung da dang ky.\n"
            f"  tu vung hien tai: {sorted(vocab[axis])}\n"
            f"  -> nhan phai duoc SUY RA tu thu da thuc su chay (measurements/validity.py),\n"
            f"     hoac them vao docs/phase-23/axis_registry.json QUA MOT AMENDMENT.\n"
            f"  -> mot chuoi bia dat QUA duoc test_no_stale_axes mot cach RONG,\n"
            f"     vi test do chi kiem 'khong nam trong approved_for_live'."
        )


def test_the_invented_label_that_motivated_this_test_would_now_fail():
    """Chung minh test nay CO RANG: nhan cu phai bi tu choi.

    Khong co dong nay thi test tren co the xanh vi ly do sai (vi du tu vung
    lo tay chua ca chuoi bia). Day la doi chung AM cho chinh co che.
    """
    vocab = _vocabulary()
    assert "MIXED_OR_MISSING" not in vocab["aoi_axis"]
    assert "MIXED_OR_MISSING" not in vocab["sla_axis"]


def test_null_is_absence_but_an_invented_string_is_not():
    """Phan biet hai cach noi "khong biet" -- day la trong tam bai hoc C2.

    `null`  = dung co che DA CO cua dinh dang de noi "khong ap dung".
    "MIXED_OR_MISSING" = mot tu MOI khong ai dinh nghia, khong qua registry,
    khong qua amendment. Cai dau kiem duoc; cai sau chi tao cam giac an toan.
    """
    vocab = _vocabulary()
    assert None not in vocab["aoi_axis"] and None not in vocab["sla_axis"], (
        "null KHONG phai mot nhan trong tu vung; no duoc xu ly rieng nhu 'vang mat'.")
    assert "MIXED_OR_MISSING" not in vocab["aoi_axis"] | vocab["sla_axis"]


def test_registry_vocabulary_is_not_empty():
    vocab = _vocabulary()
    for axis in ("aoi_axis", "sla_axis"):
        assert len(vocab[axis]) >= 3, (
            f"{axis}: tu vung qua nho ({sorted(vocab[axis])}) -- registry co the "
            f"da bi doc sai, khien test tren xanh MOT CACH RONG.")
