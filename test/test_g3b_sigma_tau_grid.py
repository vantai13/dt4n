"""Controls for the G3b recurrence guard, axis analysis and evidence custody."""
import numpy as np
import pytest

from tools import g3_dryrun
from tools.g3b_sigma_tau_grid import (
    GRID, adjudicate, assert_realised_tau, orthogonality, save_series,
)


def ideal_cells():
    return [dict(tau_s=t, sigma_ref=s, tau_hat_median=t,
                 sigma_ratio_median=1., tau_rel_error=0., sigma_rel_error=0.,
                 lag_span_over_tau=.4, quantisation_headroom_min=4.76,
                 all_estimates_finite=True, sf_min_over_links=.91,
                 max_target_clip=0., max_abs_sink_error=0., max_underrun=0.)
            for t, s, _ in GRID]


def test_guard_checks_recurrence_and_detects_wrong_module_step(monkeypatch):
    monkeypatch.setattr(g3_dryrun, "DT_S", .1)
    for tau in (2, 5, 30):
        assert_realised_tau(tau)
    monkeypatch.setattr(g3_dryrun, "DT_S", .2)
    for tau in (2, 5, 30):
        with pytest.raises(RuntimeError, match="G-L101"):
            assert_realised_tau(tau)


def test_axis_sensitivity_recovers_known_exponents():
    cells = ideal_cells()
    for c in cells:
        c["tau_hat_median"] *= (c["sigma_ref"] / .028) ** .12
        c["sigma_ratio_median"] *= (c["tau_s"] / 2) ** -.07
    fit = orthogonality(cells)
    assert fit["d_log_tau_hat_d_log_sigma"] == pytest.approx(.12)
    assert fit["d_log_sigma_ratio_d_log_tau"] == pytest.approx(-.07)
    assert adjudicate(cells, fit)["verdict"] == "STOP_NOT_ORTHOGONAL"


def test_adjudication_never_passes_missing_or_nonfinite_measurements():
    cells = ideal_cells()
    assert adjudicate(cells, orthogonality(cells))["verdict"] == "GO"
    assert adjudicate(cells[:-1], orthogonality(cells[:-1]))["verdict"] == "INCOMPLETE"
    cells[0]["all_estimates_finite"] = False
    assert adjudicate(cells, orthogonality(cells))["verdict"] == "INVALID_ESTIMATES"


def test_stop_and_tau_ceiling_are_distinct():
    cells = ideal_cells()
    cells[-1]["tau_rel_error"] = .21
    assert adjudicate(cells, orthogonality(cells))["verdict"] == "LIMIT_TAU_CEILING"
    cells[0]["tau_rel_error"] = .21
    assert adjudicate(cells[:1], {"available": False})["verdict"] == "STOP_MECHANISM"


def test_raw_series_cannot_be_overwritten(tmp_path):
    path = tmp_path / "t2_s0.028_rep0.npz"
    save_series(path, rho=np.arange(3))
    with pytest.raises(FileExistsError):
        save_series(path, rho=np.arange(10))
    with np.load(path) as data:
        np.testing.assert_array_equal(data["rho"], np.arange(3))
