#!/usr/bin/env python3
"""So CONSTANTS: hang so cung trong code phai khop so.

Vi sao can file nay
-------------------
Kiem toan 2026-08-23 phat hien `beta = 0.431` -- tru cot lap luan cua `M-125b`
va dau vao cua Lesson 23.28 -- ton tai duy nhat duoi dang mot hang so cung o
`tools/check_bin_geometry.py:34`, va da di vao artifact
(`axis_remeasure_impact_wave1.json :: dilation_exponent`) ma khong co mot dong
nao trong repo noi no den tu dau.

Mot con so khong co provenance la mot con so MO COI: khong ai kiem lai duoc,
va khi reviewer hoi "so nay o dau ra" thi khong co cho de tro toi.

Day la cai chan de hang so thu hai khong roi vao tinh trang do.
"""
from __future__ import annotations

import os
import re

DOCS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "phase-23")
CONSTANTS = os.path.join(DOCS, "CONSTANTS.md")

ROW = re.compile(r"^\|\s*(K\d{2})\s*\|")


def _rows() -> dict[str, list[str]]:
    """Doc CONSTANTS.md thanh {ma: [cac o]}."""
    out: dict[str, list[str]] = {}
    with open(CONSTANTS, encoding="utf-8") as fh:
        for line in fh:
            if not ROW.match(line.strip()):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            out[cells[0]] = cells
    return out


def test_constants_ledger_exists():
    assert os.path.exists(CONSTANTS), "thieu docs/phase-23/CONSTANTS.md"


def test_ledger_is_not_empty():
    assert len(_rows()) >= 5, "so hang so qua it: %d dong" % len(_rows())


def test_no_duplicate_constant_ids():
    ids = []
    with open(CONSTANTS, encoding="utf-8") as fh:
        for line in fh:
            m = ROW.match(line.strip())
            if m:
                ids.append(m.group(1))
    dup = sorted({k for k in ids if ids.count(k) > 1})
    assert not dup, "ma hang so lap: %s" % dup


def test_every_row_has_a_source_and_an_error_column():
    """Cot "nguon" va cot "sai so" khong duoc de trong.

    De trong mot trong hai la tai lap dung tinh trang mo coi ma so nay sinh
    ra de chan. Ghi `--` kem ly do thi duoc; de rong thi khong.
    """
    bad = []
    for code, cells in _rows().items():
        if len(cells) < 7 or not cells[4].strip() or not cells[6].strip():
            bad.append(code)
    assert not bad, (
        "dong thieu cot nguon hoac cot sai so: %s. Ghi '--' kem ly do neu "
        "that su khong ap dung." % bad)


def test_beta_constant_matches_ledger():
    """Hang so cung trong code phai khop so. Doi mot noi -> test do."""
    from tools.check_bin_geometry import BETA

    cells = _rows()["K01"]
    assert abs(BETA - float(cells[2])) < 1e-12, (
        "tools/check_bin_geometry.BETA = %r nhung CONSTANTS.md K01 ghi %r"
        % (BETA, cells[2]))


def test_aoi_constants_match_ledger():
    """K02/K03/K04/K05 phai khop `measurements/aoi_model_v7.py`."""
    import measurements.aoi_model_v7 as A

    rows = _rows()

    edges = tuple(
        float(x) for x in re.findall(r"[\d.]+", rows["K02"][2]))
    assert edges == tuple(A.Z_EDGES_V7), (
        "Z_EDGES_V7 = %r nhung K02 ghi %r" % (A.Z_EDGES_V7, edges))

    # K03 ghi bang ms, code giu bang giay.
    d_ms = float(re.match(r"([\d.]+)", rows["K03"][2]).group(1))
    assert abs(A.D_SYNC_S * 1000.0 - d_ms) < 1e-9, (
        "D_SYNC_S = %r s nhung K03 ghi %r ms" % (A.D_SYNC_S, d_ms))

    d_base_ms = float(re.match(r"([\d.]+)", rows["K04"][2]).group(1))
    assert abs(A.d_base_s() * 1000.0 - d_base_ms) < 1e-6, (
        "d_base_s() = %r s nhung K04 ghi %r ms" % (A.d_base_s(), d_base_ms))


def test_beta_uncertainty_is_recomputable_from_phase22():
    """`sd(beta)` o K01 phai tai tinh duoc tu CI Phase 22, khong phai so troi.

    Neu ai do sua `sd(beta)` trong so ma khong sua nguon, test nay do. Day la
    cung nguyen tac voi `test_adjudicated_aliases_are_documented`: khoa hai
    nguon vao nhau thay vi tin tri nho.
    """
    import math

    # docs/phase-22/04-conformal-simultaneous.md:170 (block bootstrap, 200 draw)
    b0_mean, b0_ci = 15.2778, (15.0584, 15.5054)
    b3_mean, b3_ci = 32.2376, (31.8204, 32.6735)
    # docs/phase-22/00-preregistration.md:167
    z0, z3 = 0.077, 0.425

    sd_ln0 = ((b0_ci[1] - b0_ci[0]) / (2 * 1.96)) / b0_mean
    sd_ln3 = ((b3_ci[1] - b3_ci[0]) / (2 * 1.96)) / b3_mean
    sd_beta = math.sqrt(sd_ln0 ** 2 + sd_ln3 ** 2) / math.log(z3 / z0)

    with open(CONSTANTS, encoding="utf-8") as fh:
        txt = fh.read()
    # MOI lan xuat hien, khong chi lan dau. `sd(beta)` duoc ghi ca o bang (K01)
    # lan o muc giai thich; doi chung duong cho thay `re.search` chi bat lan
    # dau nen sua o code block van PASS -- mot phep kiem khong the do.
    found = re.findall(r"sd\(beta\)\s*=\s*([\d.]+)", txt)
    assert found, "CONSTANTS.md khong ghi `sd(beta) = ...`"
    bad = [v for v in found if abs(float(v) - sd_beta) >= 5e-4]
    assert not bad, (
        "sd(beta) trong so = %s nhung tai tinh tu CI Phase 22 cho %.4f "
        "(kiem tat ca %d lan xuat hien)" % (bad, sd_beta, len(found)))
