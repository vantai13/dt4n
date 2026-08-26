import pytest

from measurements import sla_manifest_exogenous_20_a069 as M
from measurements.sla_manifest_exogenous_14 import ALLOWED, LABEL


@pytest.fixture(scope="module")
def report():
    return M.build_manifest()


def test_a069_manifest_has_exact_20_unique_feasible_cells(report) -> None:
    cells = report["cells"]
    keys = {(c["mode"], float(c["rho_bar"])) for c in cells}
    assert len(cells) == len(keys) == 20
    assert report["summary"]["n_from_base_14"] == 14
    assert report["summary"]["n_from_a069"] == 6


def test_a069_six_cells_are_present_for_both_families(report) -> None:
    got = {(c["mode"], float(c["rho_bar"])) for c in report["cells"]}
    want = {(mode, rho) for mode in M.MODES for rho in M.RHOS}
    assert want <= got


def test_a069_manifest_is_uniform_exogenous_s_b_and_whitelisted(report) -> None:
    for cell in report["cells"]:
        assert set(cell) == ALLOWED
        assert cell["sla_source"] == LABEL
        assert float(cell["t_delay_ms"]) == 50.0
        assert float(cell["t_loss"]) == 0.01
        assert float(cell["w_loss"]) == 5000.0


def test_a069_manifest_does_not_mutate_base_14_cells(report) -> None:
    import json

    with open(M.BASE, encoding="utf-8") as fh:
        base = json.load(fh)
    assert report["cells"][:14] == base["cells"]
