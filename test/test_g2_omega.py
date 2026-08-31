"""G.2 drift locks for topology, omega algebra, and per-link feasibility."""
import json

import numpy as np
import pytest

from tools.g2_feasibility_omega import (
    DEFAULT_G1_CERTIFICATE,
    DEFAULT_G1_MEASUREMENT,
    QUANT_MODES,
    load_g1_contract,
    sigma_pack,
)
from tools.g2_topology import (
    CAP_BPS,
    DEGREE,
    K_TOPO,
    LINKS,
    NULL_PAIRS,
    PAIRS,
    SHARED,
    SUM_K2,
    a0_from_sigma_at,
    design_correlation,
    design_covariance,
    design_lag_covariance,
    estimate_omega,
    sigma_per_link,
)


A0 = a0_from_sigma_at("uA", 0.030348837209302317)


def test_topology_matches_repo_source_of_truth():
    from twin import topology_v7 as T7

    assert LINKS == tuple(T7.LINK_NAMES)
    assert np.allclose(CAP_BPS, [T7.LINKS[link][0] * 1e6 for link in LINKS])


def test_sum_k2_is_five():
    assert SUM_K2 == pytest.approx(5.0, abs=1e-12)


def test_sixteen_null_pairs_and_two_visual_traps():
    assert len(NULL_PAIRS) == 16
    got = {frozenset(pair) for pair in NULL_PAIRS}
    assert frozenset(("uA", "uB")) in got
    assert frozenset(("vC", "vD")) in got
    assert frozenset(("uA", "vD")) not in got
    assert frozenset(("uB", "vC")) not in got


@pytest.mark.parametrize("omega", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_correlation_is_exactly_omega_times_k_topo(omega):
    correlation = design_correlation(A0, omega)
    for i, j in PAIRS:
        assert correlation[i, j] == pytest.approx(
            omega * K_TOPO[i, j], abs=1e-12
        )


@pytest.mark.parametrize("omega", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_variance_is_invariant_across_omega(omega):
    assert np.allclose(
        np.diag(design_covariance(A0, omega)),
        sigma_per_link(A0) ** 2,
        atol=1e-18,
    )


def test_old_parameterisation_breaks_invariance_positive_control():
    def old_covariance(a_fixed, omega):
        shared = a_fixed**2 * SHARED / np.outer(CAP_BPS, CAP_BPS)
        independent = (
            (1.0 / omega - 1.0) * a_fixed**2 * DEGREE / CAP_BPS**2
        )
        return shared + np.diag(independent)

    sigma_quarter = np.sqrt(np.diag(old_covariance(A0, 0.25))).max()
    sigma_one = np.sqrt(np.diag(old_covariance(A0, 1.0))).max()
    assert sigma_quarter / sigma_one == pytest.approx(2.0, rel=1e-12)


def test_identity_matrix_recovers_zero_omega():
    assert estimate_omega(np.eye(len(LINKS))) == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("omega", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_normalized_lag_covariance_is_invariant_in_omega(omega):
    tau_s = 10.0
    lag = 3
    covariance = design_covariance(A0, omega)
    lag_covariance = design_lag_covariance(A0, omega, tau_s, 0.2, lag)
    normalized = np.diag(lag_covariance) / np.diag(covariance)
    assert np.allclose(normalized, np.exp(-0.2 / tau_s) ** lag, atol=1e-15)


def test_sigma_spread_is_exactly_three_halves():
    sigma = sigma_per_link(A0)
    assert sigma.max() / sigma.min() == pytest.approx(1.5, abs=1e-12)
    assert LINKS[int(np.argmax(sigma))] == "ad"


def test_headroom_is_independent_of_capacity():
    headroom = sigma_per_link(A0) / sigma_pack(
        0.2, QUANT_MODES["independent_round"]
    )
    core = [headroom[LINKS.index(link)] for link in ("ac", "ad", "bc", "bd")]
    edge = [headroom[LINKS.index(link)] for link in ("uA", "uB", "vC", "vD")]
    assert np.allclose(core, core[0], rtol=1e-12)
    assert np.allclose(edge, edge[0], rtol=1e-12)
    assert edge[0] / core[0] == pytest.approx(np.sqrt(2.0), rel=1e-12)


def test_cumulative_mode_floor_is_exactly_sqrt2_worse():
    cumulative = sigma_pack(0.2, QUANT_MODES["cumulative_mixed"])
    independent = sigma_pack(0.2, QUANT_MODES["independent_round"])
    assert np.allclose(cumulative / independent, np.sqrt(2.0), rtol=1e-12)


def test_g1_measurement_digest_is_pinned_by_live_certificate():
    _sigma_min, provenance = load_g1_contract(
        DEFAULT_G1_CERTIFICATE, DEFAULT_G1_MEASUREMENT
    )
    assert provenance["measurement_sha256_pinned"] is True


def test_g1_loader_refuses_an_unpinned_measurement(tmp_path):
    changed = json.loads(DEFAULT_G1_MEASUREMENT.read_text(encoding="utf-8"))
    changed["sigma_min_binding_all_runs"] += 1e-6
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(SystemExit, match="not pinned"):
        load_g1_contract(DEFAULT_G1_CERTIFICATE, path)
