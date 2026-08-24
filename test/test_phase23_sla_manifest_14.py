"""G23-210: manifest S-B 14 cell sach va dong nhat."""
from __future__ import annotations

import json

import pytest

from measurements import sla_manifest_exogenous_14 as M
from measurements.sla_manifest_exogenous import DERIVED_FROM_SLA, FIXPOINT_TRACES


@pytest.fixture(scope="module")
def report():
    return M.build_manifest()


def test_G23_210_has_14_unique_feasible_cells(report) -> None:
    cells = report["cells"]
    keys = {(cell["mode"], float(cell["rho_bar"])) for cell in cells}
    assert len(cells) == len(keys) == 14
    assert all(cell["feasible"] for cell in cells)
    assert report["summary"] == {
        "n_cells": 14,
        "n_feasible": 14,
        "n_from_base_feasible": 10,
        "n_from_wave4": 4,
        "endogenous": False,
    }


def test_G23_210_wave4_cells_are_present_once(report) -> None:
    got = {(cell["mode"], float(cell["rho_bar"])) for cell in report["cells"]}
    want = {("h2", 0.650), ("h2", 0.675), ("poisson", 0.875), ("poisson", 0.900)}
    assert want <= got


def test_G23_210_cells_obey_whitelist_and_have_no_old_axis_statistics(report) -> None:
    banned = set(FIXPOINT_TRACES) | set(DERIVED_FROM_SLA) | set(M.MEASURED_UNDER_AXIS)
    for cell in report["cells"]:
        assert set(cell) == M.ALLOWED
        assert not (set(cell) & banned)
        assert float(cell["w_loss"]) == 5000.0


def test_G23_210_keeps_same_axis_label_and_pins_both_sources(report) -> None:
    validity = report["validity"]
    assert validity["sla_axis"]["label"] == M.LABEL
    assert validity["instrument"]["source_path"] == M.SOURCE
    assert M.WAVE4 in validity["inputs_sha256"]
    assert report["inputs"]["wave4"] == M.WAVE4


def test_whitelist_positive_control_rejects_an_unclassified_field() -> None:
    wave = json.load(open(M.WAVE4, encoding="utf-8"))["cells"][0]
    wave["future_silent_field"] = 1
    with pytest.raises(ValueError, match="stray=.*future_silent_field"):
        M.clean_wave4_cell(wave, "citation")
