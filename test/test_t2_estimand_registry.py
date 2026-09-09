"""A-T2-3 -- hai dai luong mot ten KHONG duoc lap lai.

Bo test nay bao ve DINH NGHIA, khong bao ve ket qua. No khong biet gi ve
err(tau) hay tau*. No chi tra loi mot cau: "hai con so nay co so sanh duoc
khong?" -- va no tra loi bang DAU VET, khong bang tri nho.

Bai hoc no ghim: T2.6 luot 2 da do RMS_ALLACTION_DELAY (0.3405 ms) trong khi
du doan da ky noi ve RMS_MARGIN_COST (2.1400 ms), vi ca hai cung mang ten cot
`rms_e_model` va vi GLOSSARY dang ky theo DANG HAM chu khong theo MUC va THANG.

Cung tinh than voi test_phase_t_err_dyn_is_read_from_the_artifact_not_hardcoded.
"""
from __future__ import annotations

import hashlib
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GLOSSARY = ROOT / "docs/GLOSSARY.md"
DESCRIPTOR = ROOT / "docs/phase-T2/04-estimand-descriptor.json"
SIGNED = ROOT / "docs/phase-T2/01-prediction-signed.json"
PREREG = ROOT / "docs/phase-T2/00-preregistration.md"

REQUIRED_FIELDS = (
    "LEVEL", "POPULATION", "SCALE", "UNIT",
    "BRANCH", "CODE", "ARTIFACT_FIELD",
)
KNOWN_IDS = ("RMS_MARGIN_COST", "RMS_ALLACTION_DELAY")


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def descriptor():
    assert DESCRIPTOR.is_file(), "thieu 04-estimand-descriptor.json (A-T2-3)"
    return json.loads(DESCRIPTOR.read_text())


# ---------------------------------------------------------------- so dang ky

def test_glossary_registers_both_estimands_with_all_seven_fields():
    """Mot muc thieu mot truong la mot muc CHUA DINH NGHIA XONG."""
    text = GLOSSARY.read_text()
    assert "SO DANG KY ESTIMAND" in text, "GLOSSARY chua co so dang ky"
    for eid in KNOWN_IDS:
        assert eid in text, "GLOSSARY thieu ID %s" % eid
    for field in REQUIRED_FIELDS:
        assert field in text, "GLOSSARY thieu truong bat buoc %s" % field


def test_glossary_no_longer_claims_the_two_harnesses_match():
    """Dong 'Khop voi decision_error_v2.py:402' DA GAY MOT LOI THAT.

    No phai duoc thay bang mot canh bao KHONG TUONG THICH. Neu ai do khoi
    phuc lai cach dien dat cu, test nay do.
    """
    text = GLOSSARY.read_text()
    assert "KHONG TUONG THICH VE ESTIMAND" in text
    assert "DIEU KIEN CAN, khong phai DIEU KIEN DU" in text


def test_the_two_estimands_are_numerically_different_on_the_same_cell():
    """Neu hai ID cho cung mot so thi mot trong hai la thua.

    Chung KHONG cho cung mot so: 2.1400 ms vs 0.3405 ms tren CUNG o
    poisson@0.925, tau = 0.5, seed 101..105. Va cai do sau chay voi sigma LON
    HON 2.27 lan -- huong nguoc voi ky vong neu chung la mot dai luong.
    Day la canary chong "lang le dat bi danh dong hai dai luong".
    """
    text = GLOSSARY.read_text()
    assert "2.1400" in text and "0.3405" in text
    assert "MOT CONG THUC DUNG KHONG LAM HAI DAI LUONG BANG NHAU" in text


def test_glossary_warns_against_the_number_that_was_cited_by_mistake():
    """8.235915... la rms_total CUA 22.6, khong phai so do cua T2.6.

    Mot ban nhap cua A-T2-3 da dan no lam bang chung "hai estimand lech
    nhau". Canh bao phai o lai trong GLOSSARY de loi do khong quay lai.
    """
    text = GLOSSARY.read_text()
    assert "8.235915145897662" in text
    assert "KHONG phai mot so do cua T2.6" in text


# ------------------------------------------------- descriptor <-> artifact ky

def test_descriptor_points_at_the_signed_artifact_by_hash(descriptor):
    """Mo ta phai NEO vao artifact bang hash. Neu artifact doi, test do."""
    d = descriptor["describes"]
    assert (ROOT / d["path"]).is_file()
    assert _sha256(ROOT / d["path"]) == d["sha256"], (
        "01-prediction-signed.json DA DOI. Artifact nay DA KY va KHONG duoc "
        "sua. Neu that su can doi, phai co amendment moi + tag moi."
    )


def test_signed_artifact_is_not_mutated_by_the_erratum(descriptor):
    """Erratum sua NHAN, khong sua SO. Artifact ky giu nguyen tung byte."""
    doc = json.loads(SIGNED.read_text())
    assert "estimand_id" not in doc.get("provenance", {}), (
        "KHONG duoc them truong vao artifact da ky. Dung "
        "04-estimand-descriptor.json."
    )
    assert descriptor["erratum"]["numbers_unchanged"] is True
    # cau tu khai cua artifact ky VAN la cau sai -- do la ly do co erratum
    assert "decision_error_v2" in doc["provenance"]["estimand"]


def test_prereg_hash_still_matches_the_signed_artifact():
    """Hash ghim trong prereg phai con dung sau moi thay doi cua A-T2-3."""
    assert _sha256(SIGNED) in PREREG.read_text()


# ------------------------------------------------- luat: du doan <-> phep do

def test_every_signed_prediction_declares_an_estimand_id(descriptor):
    doc = json.loads(SIGNED.read_text())
    signed_ids = set(doc["signed_predictions"])
    described = set(descriptor["predictions"])
    assert signed_ids <= described, (
        "du doan chua khai estimand: %s" % sorted(signed_ids - described)
    )
    for pid, meta in descriptor["predictions"].items():
        assert meta["estimand_id"] in KNOWN_IDS, pid


def test_the_six_reopened_predictions_all_live_on_the_margin_estimand(descriptor):
    """Day la LY DO doi harness, viet thanh mot assert de no khong bi quen."""
    reopened = ("D-T2.6-1", "D-T2.6-2", "D-T2.6-3",
                "D-T2.6-4", "D-T2.6-6", "D-T2.6-7")
    for pid in reopened:
        assert descriptor["predictions"][pid]["estimand_id"] == "RMS_MARGIN_COST"
        assert descriptor["predictions"][pid]["branch"] == "z_fixed"


def test_harness_map_sends_each_estimand_to_exactly_one_module(descriptor):
    hm = descriptor["harness_map"]
    assert hm["RMS_MARGIN_COST"] == "cert/tau_sweep.py"
    assert hm["RMS_ALLACTION_DELAY"] == "measurements/decision_error_v2.py"
    assert len(set(hm.values())) == len(hm), "hai estimand cung mot harness"


# ------------------------------------------------ code phai TU KHAI estimand

def test_tau_sweep_declares_its_estimand_in_code():
    """cert/tau_sweep.py DA ghi scale/level; A-T2-3 doi hoi them ESTIMAND_ID."""
    import cert.tau_sweep as TS
    assert getattr(TS, "ESTIMAND_ID", None) == "RMS_MARGIN_COST"


def test_decision_error_v2_declares_its_estimand_in_code():
    """TEST NAY PHAI DO TRUOC KHI SUA CODE (TDD).

    decision_error_v2 hien KHONG khai estimand nao -- do dung la lo hong da
    gay ra loi. Sau khi sua, no phai tu to cao chinh no.
    """
    import measurements.decision_error_v2 as DE
    assert getattr(DE, "ESTIMAND_ID", None) == "RMS_ALLACTION_DELAY"


def test_the_two_modules_do_not_declare_the_same_estimand():
    import cert.tau_sweep as TS
    import measurements.decision_error_v2 as DE
    assert getattr(TS, "ESTIMAND_ID", None) != getattr(DE, "ESTIMAND_ID", None)


# ------------------------------------------------ bang chap nhan cu bi thay

def test_the_old_band_window_is_marked_superseded(descriptor):
    """02-band-window.json GIU FILE nhung KHONG duoc dung lam bang.

    se cua no suy tu ti so err_total (RMS_ALLACTION_DELAY, nhanh A) trong khi
    diem du doan la RMS_MARGIN_COST, nhanh B.
    """
    sup = descriptor["superseded"]["docs/phase-T2/02-band-window.json"]
    assert sup["by"].startswith("A-T2-3")
    assert (ROOT / "docs/phase-T2/02-band-window.json").is_file(), (
        "KHONG duoc xoa artifact cu -- no la bang chung cua amendment"
    )
