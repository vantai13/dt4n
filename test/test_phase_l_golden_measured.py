#!/usr/bin/env python3
"""Phase L / L.3 -- golden tests on hand-validated L.2 measurements."""

import json
import os

import pytest

from mininet.tc_spec import DEFAULT_BURST_BYTES, fit_staircase


GOLDEN = "results/phase-L/golden/l2_staircase_golden.json"
pytestmark = pytest.mark.skipif(not os.path.exists(GOLDEN), reason="chua sinh golden file")


def _golden():
    with open(GOLDEN, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("bw", [4.0, 6.0, 8.0])
def test_c_trich_tu_delay_khop_danh_nghia_trong_1_phan_tram(bw):
    delays = _golden()["staircase_ms"]["bw%g" % bw]
    fit = fit_staircase(delays)
    assert fit["C_mbps"] == pytest.approx(bw, rel=0.01)


@pytest.mark.parametrize("bw", [4.0, 6.0, 8.0])
def test_burst_trich_tu_delay_khop_danh_nghia_trong_10_phan_tram(bw):
    fit = fit_staircase(_golden()["staircase_ms"]["bw%g" % bw])
    assert fit["burst_bytes"] == pytest.approx(DEFAULT_BURST_BYTES, rel=0.10)


@pytest.mark.parametrize("bw", [4.0, 6.0, 8.0])
def test_bac_thang_tuyen_tinh_gan_hoan_hao(bw):
    assert fit_staircase(_golden()["staircase_ms"]["bw%g" % bw])["r2"] > 0.999


def test_owd_tai_khong_khong_phu_thuoc_bw():
    zero = _golden()["zero_load_mean_ms"]
    spread = abs(zero["bw4"] - zero["bw8"])
    h0_spread = 106 * 8 / 1e6 * 1000 * (1 / 4 - 1 / 8)
    assert spread < 0.3 * h0_spread


def test_san_nhieu_van_trong_nguong():
    floor = _golden()["floor"]
    assert floor["sd_ms"] <= 0.2
    assert floor["mean_ms"] <= 0.5
