import copy

import pytest

from measurements import differential_residual as R
from mininet.topology_tandem import tandem_links_for_path


def _rows(path="P1", mode="poisson", rho=.925, seed=201):
    specs = tandem_links_for_path(path)
    digests = {row[0]: "sched-%s-%s-%d" % (path, row[0], seed) for row in specs}
    b = []
    for i, spec in enumerate(specs, start=1):
        b.append(
            {
                "branch": "B", "t7_path": path, "mode": mode, "rho_bar": rho,
                "seed": seed, "link": spec[0], "probe_loss": .01 * i,
                "q_mean_ms": 10.0 * i, "w_loss": 1000.0,
                "load_schedule_digests": digests,
            }
        )
    composed = 1.0
    for row in b:
        composed *= 1.0 - row["probe_loss"]
    composed = 1.0 - composed
    c = [{
        "branch": "C", "t7_path": path, "path": path, "mode": mode,
        "rho_bar": rho, "seed": seed, "probe_loss": composed + .002,
        "q_mean_ms": 60.5, "w_loss": 1000.0,
        "load_schedule_digests": digests,
    }]
    return b, c


def test_exact_topology_v7_path_specs():
    assert [row[1] for row in tandem_links_for_path("P1")] == ["uA", "ac", "vC"]
    assert [row[1] for row in tandem_links_for_path("P3")] == ["uB", "bc", "vC"]


def test_path_residual_algebra():
    b, c = _rows()
    row = R.path_residuals(b, c, "P1")[0]
    assert row["r_loss"] == pytest.approx(.002)
    assert row["r_delay_ms"] == pytest.approx(.5)
    assert row["r_cost_ms"] == pytest.approx(2.5)


def test_schedule_mismatch_is_fatal():
    b, c = _rows()
    c = copy.deepcopy(c)
    c[0]["load_schedule_digests"]["L2"] = "wrong"
    with pytest.raises(AssertionError, match="schedule mismatch"):
        R.path_residuals(b, c, "P1")


def test_bootstrap_is_deterministic_and_paired():
    a = R.bootstrap_mean([1.0, 2.0, 3.0, 4.0, 5.0], n_boot=200)
    b = R.bootstrap_mean([1.0, 2.0, 3.0, 4.0, 5.0], n_boot=200)
    assert a == b
    assert a["point"] == 3.0


@pytest.mark.parametrize(
    "ci,gap,want",
    [([-1.0, 1.0], 2.0, "SAFE_AT_POINT"), ([3.0, 4.0], 2.0, "UNSAFE_AT_POINT"), ([1.0, 3.0], 2.0, "INCONCLUSIVE")],
)
def test_point_verdict(ci, gap, want):
    assert R.point_verdict(ci, gap)["verdict"] == want
