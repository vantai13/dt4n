#!/usr/bin/env python3
"""Chan artifact truc SAI khong cho vao results/LIVE/.   (Lesson 23.17)

Bai hoc R1 ("sensitivity chua thuc su chay") va loi cau truc S12 (d_sync=51ms
ke thua tu topology3 sang topology_v7) xay ra vi khong co gi CHAN duoc.
Day la cai chan do.

Hom nay test nay PASS mot cach tam thuong: results/LIVE/ chi co 7 file va tat
ca deu nam trong LEGACY_EXEMPT. Do la dung. Suc manh cua no the hien o Lesson
23.20: khi mot calib_set moi duoc dua vao LIVE, test bat ban phai cap nhat
`approved_for_live` -- va viec do bat ban phai viet mot amendment.
"""
from __future__ import annotations

import ast
import glob
import json
import os

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(REPO, "results", "LIVE")
REGISTRY = os.path.join(REPO, "docs", "phase-23", "axis_registry.json")
TIERS = ("RAW", "LIVE", "SUPERSEDED", "SMOKE")

# Artifact z-INDEPENDENT co TRUOC khi co co che validity.
# Moi muc PHAI kem ly do. Danh sach nay CHI duoc ngan di, khong duoc dai ra.
LEGACY_EXEMPT = {
    "phase-20R/truth_table.parquet":                     "bang tra do, khong dung z",
    "phase-20R/decision_error_by_age_by_regime.parquet": "luoi z co dinh, z-independent",
    "phase-20R/sla_calibration.json":                    "khong dung z; thay o 23.21 vi S14",
    "phase-L/link_model_v2_fit.json":                    "fit tren do Phase L, khong dung z",
    "phase-23/aoi_v7_estimates.json":                    "SO DO cua chinh truc z",
    "phase-23/dsync_sensitivity.json":                   "cong cu quet d_sync",
    "phase-23/a0_instrument_calibration.json":           "hieu chuan nhac cu do",
}


def _rel(path: str) -> str:
    return os.path.relpath(path, LIVE).replace(os.sep, "/")


def _live_json_files() -> list[str]:
    return sorted(glob.glob(os.path.join(LIVE, "**", "*.json"), recursive=True))


def _approved() -> dict:
    with open(REGISTRY, "r", encoding="utf-8") as fh:
        return json.load(fh)["approved_for_live"]


def test_registry_readable():
    ap = _approved()
    assert "aoi_axis" in ap and "sla_axis" in ap


def test_results_is_tiered():
    """results/ chi duoc chua bon tang -- khong con file mo coi o goc."""
    root = os.path.join(REPO, "results")
    # So sach cua chinh kho: khong phai artifact, khong thuoc tang nao.
    BOOKKEEPING = {"MANIFEST.md", "PATH_MAP.tsv", "_intent.json"}
    # so ledger cua ma tran 23.20: ghi cong nhanh + thoi gian moi job, khong
    # phai mot ket qua (amendment 23-49c muc 5)
    BOOKKEEPING |= {e for e in os.listdir(root) if e.startswith("RUN_LEDGER_")}
    stray = sorted(
        e for e in os.listdir(root)
        if e not in TIERS and e not in BOOKKEEPING and not e.startswith(".")
    )
    assert not stray, (
        "results/ con muc ngoai bon tang: %s\n"
        "  -> chay `python tools/tier_results.py` roi `--apply`." % stray
    )


def test_legacy_exempt_only_shrinks():
    """Moi muc exempt phai TON TAI. Danh sach chet dan, khong phinh ra."""
    missing = [k for k in LEGACY_EXEMPT
               if not os.path.exists(os.path.join(LIVE, k))]
    assert not missing, (
        "LEGACY_EXEMPT tro toi file khong con trong LIVE/: %s\n"
        "  -> xoa muc do khoi danh sach (danh sach nay chi duoc NGAN DI)." % missing
    )


@pytest.mark.parametrize("path", _live_json_files())
def test_live_artifact_has_approved_axes(path):
    rel = _rel(path)
    if rel in LEGACY_EXEMPT:
        pytest.skip("legacy exempt: %s" % LEGACY_EXEMPT[rel])

    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        pytest.skip("khong phai artifact dang dict")

    # (1) phai CO khoi validity
    assert "validity" in payload, (
        f"{rel}: nam trong LIVE/ nhung KHONG co khoi validity.\n"
        f"  -> them validity_block(...) vao script sinh ra no,\n"
        f"     hoac chuyen file nay sang SUPERSEDED/."
    )
    v = payload["validity"]
    approved = _approved()

    # (1b) VAI TRO TRUC (amendment 23-45a).
    # Artifact DO chinh truc z khong the bi lam sai boi cai no dang do, nen
    # no khong phai cho `approved_for_live`. Nhung mien duyet KHONG phai
    # mien kiem: no van phai ghim ma nguon nhac cu va sha256 dau vao, va
    # KHONG duoc goi bat ky bo sinh z nao.
    if v.get("axis_role") == "measures_axis":
        inst = v.get("instrument", {})
        assert inst.get("source_sha256"), (
            f"{rel}: vai tro measures_axis nhung khong ghim sha256 ma nguon "
            f"nhac cu.")
        assert v.get("inputs_sha256"), (
            f"{rel}: vai tro measures_axis nhung khong ghim sha256 dau vao.")
        src = os.path.join(REPO, inst["source_path"])
        assert os.path.exists(src), f"{rel}: ma nguon nhac cu khong ton tai: {src}"
        # KHONG tin loi khai -- doc MA NGUON. Dung AST chu khong dung
        # tim chuoi: mot cau van xuoi nhac ten bo sinh trong docstring
        # KHONG phai la dung no.
        with open(src, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                used.add(node.attr)
            elif isinstance(node, ast.ImportFrom):
                used.add(node.module or "")
                used.update(al.name for al in node.names)
            elif isinstance(node, ast.Import):
                used.update(al.name for al in node.names)
        forbidden = {"sawtooth_age_steps", "DEFAULT_D_SYNC_S", "D_SYNC",
                     "measurements.decision_error", "cert.freshness_requirement"}
        clash = sorted(used & forbidden)
        assert not clash, (
            f"{rel}: khai la measures_axis nhung nhac cu "
            f"{inst['source_path']} THUC SU dung {clash}. Neu no DUNG truc z "
            f"thi vai tro dung la consumes_axis.")
        return

    # (2) nhan truc tuoi phai duoc DUYET
    lbl = v["aoi_axis"]["label"]

    # (4) UNREGISTERED nghia la ma nguon doi ma registry khong doi
    assert lbl != "UNREGISTERED", (
        f"{rel}: aoi_axis UNREGISTERED. Ma nguon bo sinh z da doi nhung\n"
        f"  docs/phase-23/axis_registry.json chua cap nhat.\n"
        f"  sha do duoc: {v['aoi_axis']['source_sha256']}\n"
        f"  -> them muc moi vao registry QUA MOT AMENDMENT, dung sua lut."
    )
    assert lbl in approved["aoi_axis"], (
        f"{rel}: aoi_axis.label = {lbl!r} chua duoc duyet cho LIVE.\n"
        f"  duyet hien tai: {approved['aoi_axis']}\n"
        f"  -> neu day la truc CU (assumed_sawtooth_51ms): chuyen sang SUPERSEDED/\n"
        f"  -> neu la truc MOI: them nhan vao approved_for_live QUA MOT AMENDMENT"
    )

    # (3) nhan SLA phai duoc DUYET
    slbl = v["sla_axis"]["label"]
    assert slbl in approved["sla_axis"], (
        f"{rel}: sla_axis.label = {slbl!r} chua duoc duyet cho LIVE (loi S14)."
    )
