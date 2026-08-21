import copy

import pytest

from measurements import differential_residual as DR
from measurements import relative_differential_campaign as R
from mininet.topology_tandem import tandem_links_for_path


def _rows(path="P1", mode="poisson", rho=.925, seed=201):
    specs = tandem_links_for_path(path)
    digests = {row[0]: "sched-%s-%s-%d" % (path, row[0], seed) for row in specs}
    b = []
    for i, spec in enumerate(specs, start=1):
        b.append({
            "branch": "B", "t7_path": path, "mode": mode, "rho_bar": rho,
            "seed": seed, "link": spec[0], "probe_loss": .01 * i,
            "q_mean_ms": 10.0 * i, "w_loss": 1000.0,
            "load_schedule_digests": digests,
        })
    composed = 1.0
    for row in b:
        composed *= 1.0 - row["probe_loss"]
    c = [{
        "branch": "C", "t7_path": path, "path": path, "mode": mode,
        "rho_bar": rho, "seed": seed, "probe_loss": 1.0 - composed + .002,
        "q_mean_ms": 60.5, "w_loss": 1000.0,
        "load_schedule_digests": digests,
    }]
    return b, c


def test_paired_bootstrap_ratio_is_deterministic():
    low = [-0.10, -0.11, -0.09, -0.10, -0.12, -0.08, -0.10, -0.10]
    high = [-0.10] * 8
    a = R.paired_bootstrap_ratio(low, high, n_boot=500)
    b = R.paired_bootstrap_ratio(low, high, n_boot=500)
    assert a == b
    assert a["point"] == pytest.approx(1.0)


def test_relative_residual_uses_composed_B_as_denominator():
    b, c = _rows()
    row = DR.path_residuals(b, c, "P1")[0]
    assert row["r_relative_loss"] == pytest.approx(row["r_loss"] / row["B_loss"])


def test_duplicate_B_row_is_fatal():
    b, c = _rows()
    with pytest.raises(ValueError, match="duplicate B"):
        DR.path_residuals(b + [copy.deepcopy(b[0])], c, "P1")
