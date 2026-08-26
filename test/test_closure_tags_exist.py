"""Moi tag duoc claim trong doc HOAC artifact phai ton tai trong git.

Vi sao: custody dung tren tien de "co mot trang thai bat bien, chi vao
bang mot cai ten". Mot cai ten khong ton tai lam moi tuyen bo custody
khac thanh giay. `L114` ghi lai lan vi pham dau tien.

Tag trong ARTIFACT nghiem trong hon tag trong DOC: artifact la chung cu,
doc la dien giai. Ve artifact KHONG co ngoai le nao.
"""
from __future__ import annotations

import pathlib
import subprocess

import pytest

from tools.audit_tags import _git_tags, _scan_docs, _scan_json

# ---------------------------------------------------------------------------
# Ngoai le CHO VE DOC. Moi dong phai noi VI SAO. Mot allowlist khong giai
# thich la dung hinh dang PASS RONG ma `L79` da bat mot lan.
#
# Ba lop, ba ly do khac han nhau:
#   (1) tag CO Y KHONG TAO  -- doc tu ghi quyet dinh do
#   (2) TROI TEN            -- mot moc, hai cach viet trong cung lesson
#   (3) MOC CHUA XAC DINH   -- khong doc nao ghi hash; doan la bia
# ---------------------------------------------------------------------------
UNRESOLVED_DOC_CLAIMS: dict[str, str] = {
    "lesson-23-22c-prereg":
        "(1) CO Y KHONG TAO. `48-a069-pilot.md:110` ghi: `M-210..M-214` va "
        "sensitivity NOT_RUN trong lesson nay, 'khong tao tag "
        "lesson-23-22c-prereg'. Vang mat la DUNG y da ky.",
    "lesson-23-22d-prereg":
        "(2) TROI TEN cua `lesson-23-22d-a-prereg` (= b1a6c8c). `A070a` muc "
        "'Moc' viet thieu chu '-a'; `A070`, `A070b` va ca bon artifact deu "
        "dung ten day du. Tao tag thu hai tren cung commit se bia ra mot moc "
        "thu hai khong ton tai. Tai lieu DA KY khong sua -- anh xa o day.",
    "phase-20-complete": "(3) MOC CHUA XAC DINH",
    "phase-20-stage-frozen": "(3) MOC CHUA XAC DINH",
    "phase-20R-campaign-grid": "(3) MOC CHUA XAC DINH",
    "phase-20R-campaign-start": "(3) MOC CHUA XAC DINH",
    "phase-20R-complete": "(3) MOC CHUA XAC DINH",
    "phase-21-complete": "(3) MOC CHUA XAC DINH",
    "phase-21-start": "(3) MOC CHUA XAC DINH",
    "phase-21R-complete": "(3) MOC CHUA XAC DINH",
    "phase-21R-start": "(3) MOC CHUA XAC DINH",
    "phase-22-start": "(3) MOC CHUA XAC DINH",
    "phase-23-start": "(3) MOC CHUA XAC DINH",
    "phase-T-G3-start": "(3) MOC CHUA XAC DINH",
}


@pytest.fixture(scope="module")
def audit():
    return {
        "have": _git_tags(),
        "docs": _scan_docs(pathlib.Path("docs")),
        "json": _scan_json(pathlib.Path("results")),
    }


def test_no_artifact_claims_a_missing_tag(audit):
    """VE NANG: artifact la chung cu. Mot chung cu tro toi cai ten khong co
    la mot chung cu hong. KHONG co ngoai le -- neu ve nay do, phai gan tag
    hoac sinh lai artifact, khong duoc noi test."""
    missing = sorted(t for t in audit["json"] if t not in audit["have"])
    detail = {t: audit["json"][t][:3] for t in missing}
    assert not missing, f"artifact claim tag khong ton tai: {detail}"


def test_no_doc_claims_a_missing_tag(audit):
    """VE NHE: doc la dien giai. Van phai dung, nhung mot lenh trong doc
    khong chay duoc thi nguoi doc lai chi mat thoi gian, khong mat chung cu."""
    missing = sorted(t for t in audit["docs"]
                     if t not in audit["have"] and t not in UNRESOLVED_DOC_CLAIMS)
    detail = {t: audit["docs"][t][:3] for t in missing}
    assert not missing, f"doc claim tag khong ton tai: {detail}"


def test_unresolved_claims_are_each_justified():
    """Moi ngoai le phai mang mot ly do co noi dung, khong duoc de trong."""
    thin = {t: r for t, r in UNRESOLVED_DOC_CLAIMS.items() if len(r.strip()) < 20}
    assert not thin, f"ngoai le khong co ly do: {sorted(thin)}"


def test_unresolved_list_does_not_rot(audit):
    """Ngoai le phai con DUNG: mot dong da duoc gan tag, hoac khong con doc
    nao claim, la mot dong PHAI BO. Danh sach mien tru khong duoc phinh ra
    roi song lau hon ly do cua no."""
    stale = {}
    for name in UNRESOLVED_DOC_CLAIMS:
        if name in audit["have"]:
            stale[name] = "da co tag -- bo khoi danh sach mien tru"
        elif name not in audit["docs"]:
            stale[name] = "khong doc nao con claim -- bo khoi danh sach"
    assert not stale, f"ngoai le da het han: {stale}"


@pytest.mark.parametrize("name", ["lesson-23-22-complete",
                                  "lesson-23-22-prereg",
                                  "lesson-23-22-b3-prereg",
                                  "lesson-23-22d-a-prereg"])
def test_lesson_23_22_tags_are_annotated(name, audit):
    """Tag phai la ANNOTATED. Lightweight tag khong mang ngay tao, nen
    khong phan biet duoc tag goc voi tag hoi to -- va viec phan biet duoc
    do CHINH LA thu `L114` doi hoi."""
    if name not in audit["have"]:
        pytest.fail(f"thieu tag {name}")
    kind = subprocess.run(["git", "cat-file", "-t", name],
                          capture_output=True, text=True, check=True)
    assert kind.stdout.strip() == "tag", (
        f"{name} la lightweight tag; phai dung `git tag -a`")
    body = subprocess.run(["git", "cat-file", "-p", name],
                          capture_output=True, text=True, check=True).stdout
    assert "RETROACTIVE" in body, (
        f"{name} thieu khai bao RETROACTIVE (L114)")


def test_prereg_tag_carries_its_warning(audit):
    """`lesson-23-22-prereg` tro vao `7c23151`, la commit THEM
    `cert/taxonomy_audit.py` -- ma do luong DA co tai moc do. Ten tag noi
    'prereg', moc thi khong. Canh bao phai nam TRONG tag, vi nguoi doc lai
    se thay tag truoc khi thay `L114`."""
    name = "lesson-23-22-prereg"
    if name not in audit["have"]:
        pytest.fail(f"thieu tag {name}")
    body = subprocess.run(["git", "cat-file", "-p", name],
                          capture_output=True, text=True, check=True).stdout
    assert "NOT PREREG EVIDENCE" in body, (
        f"{name} thieu canh bao 'NOT PREREG EVIDENCE' (L114)")
