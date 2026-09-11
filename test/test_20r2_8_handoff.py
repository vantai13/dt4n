"""20R2.8 -- chan lai DUNG loi A-T2-3: hai dai luong cung ten cot `rms_e_model`.

    decision_error_v2.rms_e_model  = RMS_ALLACTION_DELAY  (all_action, delay_ms)
    cert/tau_sweep.py  rms_e_model = margin, cost_ms      (di qua w_loss)

Hai cai nay TUNG bi doc lan nhau va lam T2.6 luot 2 do SAI dai luong so voi du
doan da ky. Khi dong phase 20R2, ban giao SUYT lap lai dung loi do: bang em/A cua
§13.5 ke thua so tu cert.tau_sweep, va viec "nang cap" no bang so cua chien dich
(decision_error_v2) se la so sanh hai estimand khac nhau.
"""
from __future__ import annotations

import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "docs/phase-20R2/08-handoff-measurements.json"
T2_SRC = ROOT / "results/PENDING/phase-T2/rt24_bias_decomposition.json"


@pytest.fixture(scope="module")
def doc():
    if not HANDOFF.is_file():
        pytest.skip("chua co artifact ban giao")
    return json.loads(HANDOFF.read_text(encoding="utf-8"))


def test_handoff_declares_its_estimand_and_the_clash(doc):
    """Mot bang khong khai estimand cua no thi khong duoc dung de ket luan."""
    w = doc["ESTIMAND_WARNING"]
    assert w["this_table"] == "RMS_ALLACTION_DELAY"
    assert "tau_sweep" in w["t2_em_over_A_table"]
    assert "A-T2-3" in w["why_not_comparable"]
    for r in doc["em_measured_on_20r2"]:
        assert r["estimand"] == "RMS_ALLACTION_DELAY", \
            "hang %s khong khai estimand" % r["cell"]


def test_handoff_does_not_invent_em_over_A(doc):
    """A KHONG dinh danh duoc tu parquet chien dich (luat chi cho c*A^2).

    Neu mot ban sau them cot em_over_A / span_ratio vao day, test nay DO: do la
    mot con so KHONG the do duoc tu nguon nay, va no se duoc doc nhu do duoc.
    """
    banned = ("em_over_A", "span_ratio_to_pure", "A_bar", "span_measured")
    for r in doc["em_measured_on_20r2"]:
        for k in banned:
            assert k not in r, (
                "hang %s co '%s' -- A khong dinh danh duoc tu c*A^2, nen con so nay "
                "khong the do duoc tu parquet chien dich. Can cert.tau_sweep (D4/D5)."
                % (r["cell"], k))


def test_em_is_z_independent_everywhere(doc):
    """em phai KHONG phu thuoc z -- neu phu thuoc thi ca luat rms sai.

    Day la mot doi chung, khong phai mot gia dinh: em duoc do o 13 diem z.
    """
    bad = [r["cell"] for r in doc["em_measured_on_20r2"] if not r["em_is_z_independent"]]
    assert not bad, "em phu thuoc z o: %s -> luat rms sai" % bad
    assert all(r["n_z"] >= 13 for r in doc["em_measured_on_20r2"])


def test_D5_is_not_silently_marked_closed(doc):
    """cbr@0.850 GIO co em, nhung o estimand KHAC bang em/A. D5 phai VAN MO.

    Day la cho de mot nguoi sot sang nhat se go nham: "da co so roi, dong no di".
    """
    assert "20R2-D5" in doc["closes_partially"]
    assert "VAN MO" in doc["closes_partially"]["20R2-D5"]
    prereg = (ROOT / "docs/phase-20R2/00-preregistration.md").read_text(encoding="utf-8")
    assert "20R2-D5" in prereg


def test_the_two_rms_e_model_really_are_different_quantities():
    """KIEM HANH VI, khong kiem van ban: hai module khai hai estimand khac nhau."""
    import measurements.decision_error_v2 as DE
    de_src = (ROOT / "measurements/decision_error_v2.py").read_text(encoding="utf-8")
    ts_src = (ROOT / "cert/tau_sweep.py").read_text(encoding="utf-8")
    assert DE.ESTIMAND_BY_FIELD["rms_e_model"] == "RMS_ALLACTION_DELAY"
    assert "rms_e_model" in ts_src, "cert/tau_sweep khong con cot nay -- cap nhat test"
    assert "A-T2-3" in de_src, "canh bao A-T2-3 da bien mat khoi decision_error_v2"
