"""Bánh cóc cho HAN CHE ke thua -- doi ngau voi "mac dinh im lang".

    mac dinh im lang   mot GIA TRI duoc ke thua ma khong ai khai
    han che roi im lang mot RANG BUOC DA KY bi MAT khi sang phase moi

Loai thu hai khong co cong cu nao bat. Da xay ra that: T2-R7 (ky 2026-09-08)
cam dung rho_bar = 0.96 lam headline; prereg 20R2 KHONG nhac mot dong nao, va
quan the headline 8 o cua 20R2 gom CA HAI o 0.96. Toan bo 3 MISS cua phan quyet
20R2.6 phu thuoc mot trong hai o do.

Co che: prereg cua moi phase trong `phases_in_scope` phai TRA LOI TUNG han che
bang `ACCEPT` hoac `OVERRIDE`. Khong nhac = DO. Giong axis_registry, nhung ap
cho RANG BUOC thay vi cho GIA TRI.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/inherited_restrictions.json"


@pytest.fixture(scope="module")
def registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def _active(reg):
    return [r for r in reg["restrictions"] if r["status"] == "ACTIVE"]


def test_registry_entries_are_complete(registry):
    """Mot han che thieu LY DO DOC LAP KET QUA thi khong dung duoc: no se bi
    tranh cai moi lan ai do thay so minh khong thich."""
    need = ("id", "title", "source", "signed_date", "scope",
            "reason_independent_of_results", "status", "phases_in_scope")
    for r in registry["restrictions"]:
        miss = [k for k in need if not r.get(k)]
        assert not miss, "han che %s thieu truong: %s" % (r.get("id"), miss)
        assert (ROOT / r["source"].split(" :: ")[0]).is_file(), \
            "nguon cua %s khong ton tai: %s" % (r["id"], r["source"])


def test_every_phase_in_scope_answers_every_active_restriction(registry):
    """DAY LA CAI CHAN. Prereg khong nhac mot han che => DO."""
    missing, not_started = [], []
    for r in _active(registry):
        for phase in r["phases_in_scope"]:
            p = ROOT / phase / "00-preregistration.md"
            if not p.is_file():
                # Phase CHUA BAT DAU -> chua phai vi pham. Banh coc TU LEN NONG:
                # ngay khi prereg cua phase do xuat hien, test nay doi no tra loi.
                not_started.append("%s @ %s" % (r["id"], phase))
                continue
            text = p.read_text(encoding="utf-8")
            if not re.search(r"%s\s*:\s*(ACCEPT|OVERRIDE)" % re.escape(r["id"]), text):
                missing.append("%s: prereg %s KHONG tra loi (can '%s: ACCEPT' "
                               "hoac '%s: OVERRIDE -- <ly do>')"
                               % (r["id"], phase, r["id"], r["id"]))
    assert not missing, "han che ke thua chua duoc tra loi:\n  " + "\n  ".join(missing)
    # Bao cao phan chua len nong -- KHONG im lang bo qua.
    if not_started:
        print("\nphase chua bat dau (banh coc se len nong khi co prereg): %s"
              % ", ".join(not_started))


def test_every_restriction_binds_at_least_one_existing_phase(registry):
    """Mot han che chi tro tuong lai thi khong rang buoc gi ca -- no se song mai
    ma khong bao gio duoc tra loi. Phai co IT NHAT MOT phase DA TON TAI trong scope."""
    for r in _active(registry):
        exists = [ph for ph in r["phases_in_scope"]
                  if (ROOT / ph / "00-preregistration.md").is_file()]
        assert exists, ("%s khong rang buoc phase nao DANG TON TAI -> no chi la mot loi "
                        "hua. Them mot phase da co prereg vao phases_in_scope." % r["id"])


def test_override_must_carry_a_reason(registry):
    """OVERRIDE khong kem ly do la mot cach im lang de bo mot rang buoc."""
    bad = []
    for r in _active(registry):
        for phase in r["phases_in_scope"]:
            p = ROOT / phase / "00-preregistration.md"
            if not p.is_file():
                continue
            for m in re.finditer(r"%s\s*:\s*OVERRIDE(.*)" % re.escape(r["id"]),
                                 p.read_text(encoding="utf-8")):
                if len(m.group(1).strip(" -–—:")) < 20:
                    bad.append("%s @ %s" % (r["id"], phase))
    assert not bad, "OVERRIDE khong co ly do du dai: %s" % bad


def test_T2_R7_cells_are_flagged_in_the_campaign_data():
    """Han che chi dung duoc neu co CO DO DUOC trong du lieu. Kiem HANH VI:
    dung hai o 0.96 phai mang extrapolation_contaminated = True, va cac o khac
    phai KHONG mang -- neu moi o deu mang co thi co do vo nghia."""
    import numpy as np
    import pandas as pd
    plan_p = ROOT / "docs/phase-20R2/03-run-plan.json"
    if not plan_p.is_file():
        pytest.skip("chua co ke hoach chien dich")
    plan = json.loads(plan_p.read_text(encoding="utf-8"))
    runs = [r for r in plan["runs"] if not r["is_canary"] and r["branch"] == "main"]
    if not runs or not (ROOT / runs[0]["out"]).is_file():
        pytest.skip("chua co du lieu chien dich")
    d = pd.read_parquet(ROOT / runs[0]["out"])
    g = d.groupby(["mode", "rho_bar"])["extrapolation_contaminated"].max()
    flagged = {("%s@%.3f" % k) for k, v in g.items() if bool(v)}
    expect = {"poisson@0.960", "h2@0.960"}
    assert flagged == expect, "co EXTRAPOLATION_CONTAMINATED lech: %s != %s" % (flagged, expect)
