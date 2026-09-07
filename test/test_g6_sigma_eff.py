"""Check covariance algebra, scale behavior, and the limit of the proxy."""
import numpy as np
import pytest

from tools.g2_topology import CAP_BPS, INCIDENCE, K_TOPO, a0_from_sigma_at, design_covariance
from tools.g5_parameters import nugget_variance
from tools.g6_sigma_eff import contrast_sd, effective_sigma


def test_hand_computed_difference_variances():
    covariance = np.array([[4., 1., 0.], [1., 9., 2.], [0., 2., 16.]])
    np.testing.assert_allclose(contrast_sd(covariance, np.eye(3)), np.sqrt([11., 20.]))


def test_shared_path_component_cancels_in_contrasts():
    # Two paths share link 0. Its arbitrary variance cancels exactly.
    incidence = np.array([[1., 1.], [1., 0.], [0., 1.]])
    for shared_variance in (1., 1000.):
        assert contrast_sd(np.diag([shared_variance, 4., 9.]), incidence)[0] == pytest.approx(np.sqrt(13.))


def test_uniform_covariance_scaling_scales_all_sds():
    rng = np.random.default_rng(8)
    factor = rng.normal(size=(8, 8))
    covariance = factor @ factor.T
    np.testing.assert_allclose(contrast_sd(4 * covariance), 2 * contrast_sd(covariance))


def test_omega_covariance_is_not_a_uniform_scale_transform():
    a0 = a0_from_sigma_at('uA', .028)
    nugget = np.diag(nugget_variance(CAP_BPS, .1))
    ratio = contrast_sd(design_covariance(a0, 1.) + nugget) / contrast_sd(design_covariance(a0, 0.) + nugget)
    assert np.ptp(ratio) > .05  # Blocks an incorrect exact scale-equivariance claim.
    assert effective_sigma(0.)['c_analytic_proxy'] == pytest.approx(1.)
    assert effective_sigma(1.)['c_analytic_proxy'] == pytest.approx(1.3065354065464148)


def test_projection_matches_path_covariance_for_every_reference():
    a0 = a0_from_sigma_at('uA', .028)
    for omega in (0., .5, 1.):
        covariance = design_covariance(a0, omega) + np.diag(nugget_variance(CAP_BPS, .1))
        path_covariance = INCIDENCE.T @ covariance @ INCIDENCE
        for reference in range(4):
            expected = [np.sqrt(path_covariance[reference, reference] + path_covariance[j, j]
                                - 2 * path_covariance[reference, j]) for j in range(4) if j != reference]
            np.testing.assert_allclose(contrast_sd(covariance, reference=reference), expected)


def test_topological_correlation_identity_and_realizable_endpoint():
    a0 = a0_from_sigma_at('uA', .028)
    for omega in (0., .25, .5, .75, 1.):
        covariance = design_covariance(a0, omega)
        sd = np.sqrt(np.diag(covariance))
        expected = omega * K_TOPO + (1 - omega) * np.eye(8)
        np.testing.assert_allclose(covariance / np.outer(sd, sd), expected, atol=1e-15)
        assert np.linalg.eigvalsh(covariance).min() >= -1e-15


@pytest.mark.parametrize('kwargs', [{'omega': -1}, {'omega': 2}, {'omega': np.nan},
                                   {'omega': .5, 'sigma_ref': 0}, {'omega': .5, 'dt': 0},
                                   {'omega': .5, 'reference': 4}])
def test_invalid_design_rejected(kwargs):
    with pytest.raises(ValueError):
        effective_sigma(**kwargs)


def test_indefinite_covariance_rejected():
    with pytest.raises(ValueError):
        contrast_sd(np.diag([-1., 1.]), np.eye(2))
