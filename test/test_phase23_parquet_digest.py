#!/usr/bin/env python3
"""`G23-174` -- moi calib report phai mang van tay cua parquet CUA CHINH NO.

Gate nay ton tai vi `L51`: report cu chi luu `sha256` cua DAU VAO, nen khi tim
thay mot parquet tren dia thi KHONG chung minh duoc no thuoc report nao. Doi
chung am muc duong ong khi do that bai IM LANG, va `M-135`/`M-136` treo vi do.

Gia tri chung minh NGAY: hai lan chay `poisson@0.925` (mot voi `float32`, mot
voi `float64` khi tinh phan vi) cho CUNG `parquet_sha256`. Do la bang chung
BIT-IDENTICAL cua du lieu, va no khu bo mot gia thuyet sai (`L71`).
"""
from __future__ import annotations

import glob
import hashlib
import json
import os

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(REPO, "results", "LIVE", "phase-21R")


def _reports() -> list[str]:
    return sorted(glob.glob(os.path.join(LIVE, "calib_set_*_report.json")))


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _has_output(rep: dict) -> bool:
    return isinstance(rep.get("output"), dict)


@pytest.mark.parametrize("path", _reports())
def test_report_records_its_own_parquet_digest(path):
    rep = json.load(open(path, encoding="utf-8"))
    if not _has_output(rep):
        pytest.skip("report sinh TRUOC amendment 23-58")
    for k in ("parquet_path", "parquet_sha256", "parquet_bytes", "n_rows",
              "digest_scope"):
        assert k in rep["output"], "%s: `output` thieu %r" % (
            os.path.basename(path), k)
    assert len(rep["output"]["parquet_sha256"]) == 64
    assert rep["output"]["digest_scope"] == "bytes-on-disk-after-flush"


@pytest.mark.parametrize("path", _reports())
def test_parquet_on_disk_matches_the_recorded_digest(path):
    """Day moi la phep kiem THAT; cai tren chi kiem SU TON TAI cua truong.

    `skip` (khong `fail`) khi parquet vang mat la CO Y: muc dich cua
    `G23-174` la LUU DUOC van tay, khong phai GIU DUOC file (~70 MB/file).
    Neu `fail`, nguoi sau se XOA test thay vi giu file -- va ta mat cai chan.
    Mot test bi skip con hon mot test bi xoa.
    """
    rep = json.load(open(path, encoding="utf-8"))
    if not _has_output(rep):
        pytest.skip("report sinh TRUOC amendment 23-58")
    pq = rep["output"]["parquet_path"]
    if not os.path.isabs(pq):
        pq = os.path.join(REPO, pq)
    if not os.path.exists(pq):
        pytest.skip("parquet khong tren dia (da don kho) -- van tay VAN duoc "
                    "luu, do la muc dich cua G23-174")
    assert _sha256(pq) == rep["output"]["parquet_sha256"], (
        "%s: parquet tren dia KHAC file da sinh ra report.\n"
        "  -> hoac file bi ghi de, hoac report thuoc mot lan chay khac.\n"
        "  -> KHONG duoc dung lai file nay." % os.path.basename(path))


def test_no_two_reports_claim_the_same_parquet():
    """`G23-201`. Hai report tro cung mot parquet = mot cai da bi GHI DE.

    Loi `out_stem` tro nham tang da xay ra that o amendment 23-49c.
    """
    seen: dict[str, str] = {}
    for p in _reports():
        rep = json.load(open(p, encoding="utf-8"))
        if not _has_output(rep):
            continue
        key = rep["output"]["parquet_path"]
        assert key not in seen, (
            "%s va %s cung khai %s -- mot cai da bi GHI DE."
            % (os.path.basename(p), seen[key], key))
        seen[key] = os.path.basename(p)
