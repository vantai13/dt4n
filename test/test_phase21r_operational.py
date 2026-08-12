import pytest

from cert import operational_sigma as O


def _cell(
    anchor,
    qhat,
    cov=0.905,
    cov_bin=None,
    curve=None,
    sigma=0.02,
    mode="poisson",
    rho_bar=0.850,
):
    return {
        "mode": mode,
        "rho_bar": rho_bar,
        "sigma_used": sigma,
        "sigma_mode": "operational",
        "anchor_err": anchor,
        "degenerate": anchor < O.DEGENERATE_ERR,
        "qhat": qhat,
        "qhat_ratio_last_over_first": qhat[max(qhat)] / qhat[min(qhat)],
        "coverage_marginal": cov,
        "coverage_by_bin": cov_bin or {i: cov for i in qhat},
        "n_test": 1000,
        "curve": curve
        or [
            {
                "kappa": 1.0,
                "acceptance_rate": 0.3,
                "err_given_accept": 0.03,
                "err_given_reject": 0.30,
                "risk_ratio": 0.15,
            }
        ],
    }


def test_O1_invariance_detects_stable_shape_ratio():
    results = {
        "poisson@0.700": _cell(0.20, {0: 1.0, 3: 2.15}, mode="poisson", rho_bar=0.7),
        "poisson@0.850": _cell(0.20, {0: 80.0, 3: 172.0}, mode="poisson"),
        "h2@0.925": _cell(0.20, {0: 24.0, 3: 51.4}, mode="h2", rho_bar=0.925),
    }
    report = O.invariance_report(results)
    assert report["ratio_rel_spread"] < 0.10
    assert report["qhat_scale_spread_factor"] > 50.0
    assert 2.0 < report["ratio_mean"] < 2.3


def test_O2_invariance_flags_unstable_ratio():
    results = {
        "poisson@0.700": _cell(0.20, {0: 1.0, 3: 1.2}, mode="poisson", rho_bar=0.7),
        "h2@0.850": _cell(0.20, {0: 80.0, 3: 400.0}, mode="h2"),
    }
    assert O.invariance_report(results)["ratio_rel_spread"] > 0.5


def test_O3_invariance_excludes_cbr_controls_but_not_h7_degenerate_h2():
    results = {
        "cbr@0.700": _cell(0.0, {0: 0.01, 3: 0.01}, mode="cbr", rho_bar=0.7),
        "h2@0.960": _cell(0.0005, {0: 24.0, 3: 51.0}, mode="h2", rho_bar=0.96),
    }
    report = O.invariance_report(results)
    assert report["n_cells"] == 1
    assert report["per_cell"][0]["cell"] == "h2@0.960"
    assert report["per_cell"][0]["h7_degenerate"]


def test_O4_nonmonotone_detected():
    results = {
        "poisson@%.3f" % rho: _cell(err, {0: 1.0, 3: 2.15}, mode="poisson", rho_bar=rho)
        for rho, err in zip((0.700, 0.850, 0.925, 0.960), (0.141, 0.331, 0.289, 0.199))
    }
    mono = O.monotonicity_in_rho(results)["poisson"]
    assert not mono["monotone_increasing"]
    assert not mono["monotone_decreasing"]
    assert mono["argmax_rho_bar"] == pytest.approx(0.850)


def test_O5_monotone_decreasing_detected():
    results = {
        "h2@%.3f" % rho: _cell(err, {0: 1.0, 3: 2.15}, mode="h2", rho_bar=rho)
        for rho, err in zip((0.700, 0.850, 0.925, 0.960), (0.301, 0.258, 0.078, 0.011))
    }
    assert O.monotonicity_in_rho(results)["h2"]["monotone_decreasing"]


def test_O6_rescue_flagged():
    fixed = _cell(0.0048, {0: 1.0, 3: 2.15}, sigma=0.0096)
    operational = _cell(0.2585, {0: 81.5, 3: 174.9}, sigma=0.04797)
    comparison = O.compare_paths(fixed, operational)
    assert comparison["rescued_by_operational"]
    assert comparison["sigma_ratio"] == pytest.approx(0.04797 / 0.0096, rel=1e-6)


def test_O7_no_rescue_when_both_real():
    fixed = _cell(0.2224, {0: 11.6, 3: 24.3}, sigma=0.0096)
    operational = _cell(0.2889, {0: 24.3, 3: 52.0}, sigma=0.0218)
    assert not O.compare_paths(fixed, operational)["rescued_by_operational"]


def test_O8_degenerate_marker_matches_threshold():
    assert _cell(0.0001, {0: 0.01, 3: 0.01})["degenerate"]
    assert not _cell(0.02, {0: 0.01, 3: 0.02})["degenerate"]


def test_O9_G4_uses_per_bin_not_only_marginal():
    bad = _cell(0.20, {0: 1.0, 3: 2.15}, cov=0.900, cov_bin={0: 0.98, 3: 0.82})
    assert not all(abs(v - 0.90) <= O.COV_TOL_PER_BIN for v in bad["coverage_by_bin"].values())


def test_O10_kappa_grid_covers_named_points():
    assert 0.5 in O.KAPPAS
    assert 1.0 in O.KAPPAS
    assert 2.0 in O.KAPPAS
