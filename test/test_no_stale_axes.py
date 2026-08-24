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
PENDING = os.path.join(REPO, "results", "PENDING")
REGISTRY = os.path.join(REPO, "docs", "phase-23", "axis_registry.json")
TIERS = ("RAW", "LIVE", "PENDING", "SUPERSEDED", "SMOKE")

# Artifact z-INDEPENDENT co TRUOC khi co co che validity.
# Moi muc PHAI kem ly do. Danh sach nay CHI duoc ngan di, khong duoc dai ra.
LEGACY_EXEMPT = {
    # `truth_table.parquet` va `decision_error_by_age_by_regime.parquet` DA RA
    # khoi danh sach nay o amendment 23-60: cai dau nay co sidecar
    # `truth_table_report.json` (vai tro MEASURES), cai sau da bi HA xuong
    # SUPERSEDED/ va thay bang `..._slaB.parquet` (vai tro AXIS_FREE, truc SLA
    # ngoai sinh). Mien tru NGAM -> vai tro TUONG MINH.
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

    # (1c) VAI TRO AXIS_FREE (amendment 23-60).
    # Artifact chay tren luoi z CO DINH: no khong CHO truc AoI, nhung van phai
    # cho truc SLA. Mien tru MOT truc, khong phai ca hai -- day chinh la cho
    # `LEGACY_EXEMPT` cu da mien qua tay.
    if v.get("axis_role") == "aoi_axis_free":
        assert "z_grid_s" in v.get("aoi_axis", {}), (
            f"{rel}: khai aoi_axis_free nhung khong ghim luoi z.")
        slbl = v["sla_axis"]["label"]
        assert slbl in approved["sla_axis"], (
            f"{rel}: sla_axis.label = {slbl!r} chua duoc duyet cho LIVE (S14).\n"
            f"  duyet hien tai: {approved['sla_axis']}")
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


def test_every_live_parquet_has_a_validity_sidecar():
    """Cai chan cu chi soi *.json, nen MOI parquet trong LIVE/ deu lot.

    Doi chung duong DA CHAY: `decision_error_by_age_by_regime.parquet` nam o
    LIVE/ voi truc SLA DEPRECATED (S14) tu Lesson 23.17 den 23.21 ma khong
    test nao keu -- khong phai vi LEGACY_EXEMPT viet sai, ma vi cai chan
    KHONG NHIN THAY parquet.

    Parquet khong mang duoc khoi `validity` (metadata chi co key b'pandas'),
    nen no phai di kem mot sidecar `<ten>_report.json`. Day la mau DA CO cua
    Phase 21R; amendment 23-60 ap no cho moi tang LIVE.
    """
    missing = []
    for p in sorted(glob.glob(os.path.join(LIVE, "**", "*.parquet"),
                              recursive=True)):
        side = p[: -len(".parquet")] + "_report.json"
        if not os.path.exists(side):
            missing.append(_rel(p))
    assert not missing, (
        "parquet trong LIVE/ khong co sidecar _report.json mang validity:\n"
        "  %s\n"
        "  -> sinh sidecar, hoac chuyen parquet sang SUPERSEDED/."
        % "\n  ".join(missing)
    )


# ---------------------------------------------------------------------------
# Tang PENDING (amendment 23-49d muc 4)
# ---------------------------------------------------------------------------


# Danh sach nay CHI DUOC NGAN DI, khong duoc dai ra. Moi muc la mot artifact
# da ton tai TRUOC amendment 23-60 va chua kip mang `validity`. Them muc moi =
# mot amendment, va phai kem ly do vi sao script sinh ra no KHONG THE goi
# validity_block(). Khoi tao RONG: khong ai duoc mien tru ngay tu dau.
PENDING_NO_VALIDITY_GRANDFATHERED: dict[str, str] = {
    # `L75`: artifact nay KHONG THE duoc dan nhan suy ra, vi ban ghi provenance
    # cua chinh no la SAI. No co `w_loss == 5000` o moi cell (bang chung no da
    # doc manifest ngoai sinh S-B) nhung `provenance.inputs` lai khai doc
    # `results/LIVE/phase-20R/sla_calibration.json` (truc S14 DEPRECATED), vi
    # `eight_cell_sweep.py` ghim HANG SO `SLA_ARTIFACT` thay vi `args.sla`.
    # Suy nhan tu mot ban ghi DA BIET LA SAI = vi pham Luat 2. Ma nguon da sua;
    # artifact phai SINH LAI. Sinh lai dang bi chan boi `L51` (thieu 4/8 parquet
    # phase-22). Muc nay bi XOA ngay khi `L51` mo khoa va no duoc sinh lai.
    "phase-23/eight_cell_sweep_U3_measured_v7_slaB.json":
        "L75: provenance khai sai nguon SLA; phai sinh lai; bi chan boi L51",
}


def _pending_json() -> list[str]:
    return sorted(glob.glob(os.path.join(PENDING, "**", "*.json"), recursive=True))


@pytest.mark.parametrize("path", _pending_json())
def test_pending_artifacts_declare_what_they_wait_for(path):
    """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

    Hai rang buoc, va cai thu hai lam tang nay TU DON:
      (1) phai khai `pending_on` -- truc nao chua duyet
      (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
          va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
    """
    rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        pytest.skip("khong phai artifact dang dict")

    # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
    # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
    # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
    # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
    # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
    if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
        pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])
    assert "validity" in payload, (
        f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
        f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
        f"sinh ra no,\n"
        f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
    )
    v = payload["validity"]
    pend = v.get("pending_on")
    assert pend, (
        f"{rel}: nam o PENDING/ nhung khong khai `pending_on`.\n"
        f"  -> khai chinh xac truc nao chua duyet, de Lesson 23.21 tim lai duoc."
    )
    approved = _approved()
    for axis in pend:
        assert axis in approved, f"{rel}: `pending_on` co truc la {axis!r}"
        label = v.get(axis, {}).get("label")
        assert label not in approved[axis], (
            f"{rel}: khai cho {axis} nhung truc {label!r} DA duoc duyet.\n"
            f"  -> PROMOTE artifact nay len LIVE/. Tang PENDING tu don la o day."
        )
