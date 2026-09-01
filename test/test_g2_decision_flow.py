"""Lock the G.2 decision cancellation and mechanisms that break it."""
import itertools

import numpy as np
import pytest

from tools.g2_decision_flow import (
    KAPPA_GRID,
    OMEGA_GRID,
    PATH_LINKS,
    SIGMA_REF,
    contrast,
    load_nugget_vector,
    p_flip,
    quad_forms,
)
from tools.g2_topology import LINKS, a0_from_sigma_at


A0 = a0_from_sigma_at("uA", SIGMA_REF)
GAMMA = np.ones(len(LINKS))
IDX = {link: index for index, link in enumerate(LINKS)}


@pytest.mark.parametrize("path,other", list(itertools.combinations(PATH_LINKS, 2)))
def test_shared_links_cancel_from_the_contrast(path, other):
    c_vector = contrast(path, other, GAMMA)
    for link in set(PATH_LINKS[path]) & set(PATH_LINKS[other]):
        assert c_vector[IDX[link]] == pytest.approx(0.0, abs=1e-15)


@pytest.mark.parametrize("path,other", list(itertools.combinations(PATH_LINKS, 2)))
def test_omega_cancels_exactly_under_a_single_shared_tau(path, other):
    path_variance, link_variance = quad_forms(
        contrast(path, other, GAMMA), A0
    )
    phi = float(np.exp(-2.0 / 3.0))
    values = [
        p_flip(omega, path_variance, link_variance, phi, phi)
        for omega in OMEGA_GRID
    ]
    assert max(values) - min(values) == pytest.approx(0.0, abs=1e-12)
    assert values[0] == pytest.approx(np.arccos(phi) / np.pi, abs=1e-12)


def test_omega_does_change_the_decision_variance_positive_control():
    path_variance, link_variance = quad_forms(
        contrast("P1", "P2", GAMMA), A0
    )
    assert path_variance / link_variance > 1.5


@pytest.mark.parametrize("kappa", [value for value in KAPPA_GRID if value != 1.0])
def test_two_timescales_break_the_cancellation(kappa):
    path_variance, link_variance = quad_forms(
        contrast("P1", "P2", GAMMA), A0
    )
    phi_path = float(np.exp(-2.0 / (3.0 * kappa)))
    phi_link = float(np.exp(-2.0 / 3.0))
    values = [
        p_flip(
            omega, path_variance, link_variance, phi_path, phi_link
        )
        for omega in OMEGA_GRID
    ]
    assert max(values) - min(values) >= 0.10


def test_omega_endpoints_inherit_the_two_timescales():
    path_variance, link_variance = quad_forms(
        contrast("P1", "P2", GAMMA), A0
    )
    phi_path = float(np.exp(-2.0 / 30.0))
    phi_link = float(np.exp(-2.0 / 3.0))
    assert p_flip(
        0.0, path_variance, link_variance, phi_path, phi_link
    ) == pytest.approx(np.arccos(phi_link) / np.pi, abs=1e-12)
    assert p_flip(
        1.0, path_variance, link_variance, phi_path, phi_link
    ) == pytest.approx(np.arccos(phi_path) / np.pi, abs=1e-12)


def test_independent_nugget_effect_is_negligible_on_this_testbed():
    c_vector = contrast("P1", "P2", GAMMA)
    path_variance, link_variance = quad_forms(c_vector, A0)
    nugget_vector, provenance = load_nugget_vector()
    assert provenance["measurement_sha256_pinned"] is True
    decision_nugget = float(np.sum(c_vector**2 * nugget_vector))
    phi = float(np.exp(-0.2))
    values = [
        p_flip(
            omega,
            path_variance,
            link_variance,
            phi,
            phi,
            nugget=decision_nugget,
        )
        for omega in OMEGA_GRID
    ]
    assert 0.0 < max(values) - min(values) < 0.01

