import json

import pytest

from measurements import sla_manifest_exogenous_32_a070 as M
from measurements.sla_manifest_exogenous_14 import ALLOWED, LABEL


@pytest.fixture(scope="module")
def report():
    return M.build_manifest()


def test_a070_manifest_has_exact_32_unique_cells(report) -> None:
    cells = report["cells"]
    keys = {(c["mode"], float(c["rho_bar"])) for c in cells}
    assert len(cells) == len(keys) == 32
    assert report["summary"]["n_from_base_20"] == 20
    assert report["summary"]["n_from_a070_window"] == 12


def test_a070_window_is_dense_and_has_both_families(report) -> None:
    assert M.RHOS == (0.744, 0.750, 0.756, 0.760, 0.764, 0.770)
    got = {(c["mode"], float(c["rho_bar"])) for c in report["cells"]}
    assert {(mode, rho) for mode in M.MODES for rho in M.RHOS} <= got


def test_a070_manifest_preserves_base_20_and_s_b_contract(report) -> None:
    with open(M.BASE, encoding="utf-8") as fh:
        base = json.load(fh)
    assert report["cells"][:20] == base["cells"]
    for cell in report["cells"]:
        assert set(cell) == ALLOWED
        assert cell["sla_source"] == LABEL
        assert float(cell["w_loss"]) == 5000.0
