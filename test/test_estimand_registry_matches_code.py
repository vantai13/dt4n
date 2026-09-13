"""20R2-E1-a -- SO DANG KY phai khop MA. Mot dinh chinh chi hoan tat khi no
cham toi NGUON CHAN LY, khong phai khi no cham toi noi vua phat hien ra loi.

Lich su: 20R2.7-B1 doi chinh don vi cua `d_sla` (khong thu nguyen, [-1,1]) va
ap vao decision_error_v2.py + docs/phase-20R2/07-dsla.md, nhung KHONG chep ve
docs/GLOSSARY.md. So dang ky -- nguon duoc coi la chan ly -- giu lai gia tri SAI.
Test nay lam viec do khong the lap lai lang le.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from measurements import decision_error_v2 as DE

GLOSSARY = pathlib.Path(__file__).resolve().parents[1] / "docs/GLOSSARY.md"

# HOP DONG. Doi mot dong o day = mot quyet dinh khoa hoc, phai co amendment.
CONTRACT = {
    "RMS_ALLACTION_DELAY": {"unit": "ms",            "level": "all_action"},
    "DECISION_ERR_BY_AGE": {"unit": "dimensionless", "level": "all_action"},
    "SLA_VIOL_BY_AGE":     {"unit": "dimensionless", "level": "all_action"},
}


def _entry(text: str, eid: str) -> str:
    marker = "ID              " + eid
    assert marker in text, "GLOSSARY thieu muc %r" % eid
    i = text.index(marker)
    j = text.find("\n------", i + 1)
    return text[i: j if j > 0 else len(text)]


@pytest.mark.parametrize("eid", sorted(CONTRACT))
def test_registry_declares_the_unit_the_contract_requires(eid: str) -> None:
    block = _entry(GLOSSARY.read_text(encoding="utf-8"), eid)
    m = re.search(r"^UNIT\s+(\S+)", block, re.M)
    assert m, "%s: thieu truong UNIT" % eid
    assert m.group(1) == CONTRACT[eid]["unit"], (
        "%s: GLOSSARY khai UNIT=%r, hop dong doi %r.\n"
        "  -> mot dinh chinh da duoc ap vao MA ma khong chep ve SO DANG KY."
        % (eid, m.group(1), CONTRACT[eid]["unit"]))


@pytest.mark.parametrize("eid", sorted(CONTRACT))
def test_registry_declares_all_seven_fields(eid: str) -> None:
    block = _entry(GLOSSARY.read_text(encoding="utf-8"), eid)
    for field in ("LEVEL", "POPULATION", "SCALE", "UNIT",
                  "BRANCH", "CODE", "ARTIFACT_FIELD"):
        assert re.search(r"^%s\s+\S" % field, block, re.M), \
            "%s: thieu truong bat buoc %s (H4 doi du 7)" % (eid, field)


def test_every_artifact_field_maps_to_a_registered_estimand() -> None:
    """Khong mot cot parquet nao duoc mang mot estimand_id khong co trong so."""
    unknown = {f: e for f, e in DE.ESTIMAND_BY_FIELD.items() if e not in CONTRACT}
    assert not unknown, "cot mang estimand_id chua dang ky: %r" % unknown


def test_d_sla_is_a_difference_of_rates_not_a_cost() -> None:
    """Doc THANG tu MA: `viol` la boolean, nen hieu hai trung binh la TI LE.

    Neu ai do doi dong 571 thanh mot phep tinh CHI PHI thi test nay do, va
    khi do UNIT trong so dang ky moi duoc phep doi theo.
    """
    src = pathlib.Path(DE.__file__).read_text(encoding="utf-8")
    assert 'return (delay > float(t_delay_ms)) | (loss > float(t_loss))' in src, \
        "_viol khong con la phep so NGUONG tra BOOLEAN -- xet lai UNIT cua d_sla"
    assert '"d_sla": float(viol[current, a_twin].mean() - viol[current, a_truth].mean())' in src, \
        "d_sla khong con la HIEU HAI TI LE -- xet lai UNIT trong docs/GLOSSARY.md"


def test_erratum_exists_and_is_referenced_from_the_registry() -> None:
    """Mot dinh chinh khong co van ban thi khong ai truy nguoc duoc."""
    root = GLOSSARY.parent
    assert (root / "phase-20R2/E1-erratum.md").exists(), "thieu E1-erratum.md"
    text = GLOSSARY.read_text(encoding="utf-8")
    assert "20R2.7-B1" in text, \
        "GLOSSARY khong dan nguon dinh chinh -- nguoi doc khong truy nguoc duoc"
