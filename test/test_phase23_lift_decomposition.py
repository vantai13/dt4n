"""Tests for the read-only G23-23 lift decomposition."""

from __future__ import annotations

import json

import pytest

from tools import lift_decomposition_by_cell as L


def _report():
    with open(L.INPUT, "r", encoding="utf-8") as handle:
        return L.analyze(json.load(handle))


def test_lift_decomposition_recomputes_existing_identity():
    report = _report()
    assert len(report["rows"]) == 3
    for row in report["rows"]:
        expected = row["reject_share"] * (row["swing"] - row["lift"])
        assert row["delta"] == pytest.approx(expected, abs=1e-12)


def test_axis_specific_spreads_expose_fallback_bottleneck():
    report = _report()
    assert report["spreads"]["twin_deg"]["max_over_min"] == pytest.approx(
        1.029335, rel=1e-5
    )
    assert report["spreads"]["prior_deg"]["max_over_min"] == pytest.approx(
        4.111333, rel=1e-5
    )
    assert report["bottleneck"]["component"] == "fallback_prior_deg"


def test_transfer_contrast_is_c3_minus_b2():
    report = _report()
    for row in report["transfer_C3_minus_B2"]:
        assert row["C3_minus_B2"] == pytest.approx(
            row["C3_delta"] - row["B2_delta"], abs=1e-15
        )
