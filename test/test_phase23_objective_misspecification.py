"""Tests for the frozen-system objective misspecification sweep."""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

from cert import objective_misspecification as O
from cert.build_calib_set_v3 import _load_cell
from cert.cell_matrices import TRUTH_TABLE, cell_matrices
from measurements import band_v2 as B
from measurements.decision_error_v2 import TruthTable
from twin import topology_v7 as T7


def test_relative_path_shift_dung_bang_rescale_w_loss_ve_cost():
    rho = np.full((7, len(T7.LINK_NAMES)), 0.7, dtype=np.float64)
    w_loss = 1451.3765784675
    rel = -0.16474422028424326
    relative = B.RelativePathShiftTruthTable(rel, "poisson")
    base = TruthTable(TRUTH_TABLE)
    _d1, _l1, cost_relative = relative.path_tables("poisson", rho, w_loss)
    _d2, _l2, cost_rescaled = base.path_tables("poisson", rho, w_loss * (1.0 + rel))
    assert np.allclose(cost_relative, cost_rescaled, rtol=0.0, atol=1e-12)


def test_cell_matrices_ratio_one_override_tai_lap_default():
    cell = _load_cell("poisson", 0.925)
    base = cell_matrices(TruthTable(TRUTH_TABLE), n=1200)
    same = cell_matrices(
        TruthTable(TRUTH_TABLE), n=1200, w_loss_override=float(cell["w_loss"])
    )
    assert np.array_equal(base["y_true"], same["y_true"])
    assert np.array_equal(base["y_hat"], same["y_hat"])


@pytest.mark.skipif(not os.path.exists(O.OUTPUT), reason="chua chay objective sweep")
def test_objective_sweep_co_11_diem_va_dong_bang_he_thong():
    with open(O.OUTPUT, "r", encoding="utf-8") as handle:
        report = json.load(handle)
    assert report["ratios"] == pytest.approx(O.RATIOS)
    for cell in O.CELL_META:
        payload = report["cells"][cell]
        assert len(payload["curve"]) == 11
        assert payload["controls"]["gate_frozen"] is True
        assert payload["controls"]["y_hat_frozen"] is True
        assert payload["controls"]["fallback_frozen"] is True
        assert payload["controls"]["ratio_1_reproduced_at_1e_12"] is True
        assert payload["controls"]["max_identity_residual"] <= 1e-12


@pytest.mark.skipif(not os.path.exists(O.OUTPUT), reason="chua chay objective sweep")
def test_measured_ratio_lay_tu_artifact_S8_da_dinh_chinh():
    with open(O.OUTPUT, "r", encoding="utf-8") as handle:
        report = json.load(handle)
    assert report["cells"]["poisson@0.925"]["measured_relative_point"][
        "ratio"
    ] == pytest.approx(0.8352557797157567)
    assert report["cells"]["h2@0.700"]["measured_relative_point"][
        "ratio"
    ] == pytest.approx(0.9336155778185988)
