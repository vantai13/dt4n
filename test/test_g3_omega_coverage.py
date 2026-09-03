"""Unit tests for the omega coverage dry-run.

The proposition under test is that omega moves SIMULTANEOUS coverage while
leaving MARGINAL coverage flat, at one time scale. Both halves are locked
here, together with the two finite-sample effects that make the anchor for
COV-0 the product of the ACHIEVED marginals rather than the nominal ones.
"""
from __future__ import annotations

import numpy as np
import pytest

from tools.g2_topology import LINKS
from tools.g3_omega_coverage_dryrun import (
    ALPHA,
    K_PRIMARY,
    SF_PRIMARY,
    Z,
    amplification_factor,
    coverage,
    trace,
)

WINDOWS = 3000          # the campaign length, not a convenient long one


def _iid_trace(rng, n=WINDOWS):
    return rng.standard_normal((len(LINKS), n))


# ------------------------------------------------------------- primitives
def test_z_is_the_two_sided_normal_quantile():
    from statistics import NormalDist
    assert Z == pytest.approx(NormalDist().inv_cdf(1.0 - ALPHA / 2.0))


def test_amplification_factor_is_the_derivative_of_the_product():
    assert amplification_factor(8, 0.10) == pytest.approx(8 * 0.9**7)
    assert amplification_factor(8, 0.10) == pytest.approx(3.8263752)
    numeric = ((0.9 + 1e-6) ** 8 - 0.9**8) / 1e-6
    assert amplification_factor(8, 0.10) == pytest.approx(numeric, rel=1e-5)


def test_coverage_refuses_a_degenerate_link():
    with pytest.raises(ValueError):
        coverage(np.ones((len(LINKS), 100)), (2,))


def test_coverage_refuses_k_outside_the_link_index():
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError):
        coverage(_iid_trace(rng, 200), (9,))


# ------------------------------------------- COV-0 anchor: marginal**K
def test_independence_anchor_is_the_product_of_achieved_marginals():
    """The correction COV-0 encodes, on the regime that motivated it.

    At omega=0 there is no cross-link coupling, so simultaneous coverage must
    equal the product of the achieved marginals. Under autocorrelation the
    achieved marginal sits below the nominal one, and the two candidate
    anchors separate by more than the Monte Carlo noise of the mean, so the
    comparison is decisive rather than a coin flip. Averaging is required:
    on a single trace at k=2 the gap is smaller than the noise.
    """
    rows = [
        coverage(trace(0.0, SF_PRIMARY, WINDOWS, np.random.default_rng(50 + i)),
                 (2, 4, 8))
        for i in range(24)
    ]
    marginal = float(np.mean([r[0] for r in rows]))
    assert marginal < 1.0 - ALPHA          # the deficit COV-1 measures
    for k in (2, 4, 8):
        simultaneous = float(np.mean([r[k] for r in rows]))
        achieved_error = abs(simultaneous - marginal**k)
        nominal_error = abs(simultaneous - (1.0 - ALPHA) ** k)
        assert achieved_error < 3e-3
        assert achieved_error < nominal_error


def test_the_marginal_deficit_reaches_k_links_amplified():
    """G-L93 as arithmetic: the K-fold anchor gap is the amplified deficit."""
    rows = [
        coverage(trace(0.0, SF_PRIMARY, WINDOWS, np.random.default_rng(50 + i)),
                 (K_PRIMARY,))
        for i in range(24)
    ]
    marginal = float(np.mean([r[0] for r in rows]))
    deficit = marginal - (1.0 - ALPHA)
    anchor_gap = marginal**K_PRIMARY - (1.0 - ALPHA) ** K_PRIMARY
    predicted = amplification_factor(K_PRIMARY, ALPHA) * deficit
    assert deficit < 0.0
    assert anchor_gap == pytest.approx(predicted, rel=0.05)


def test_iid_data_at_campaign_length_is_not_undercovered():
    """The deficit is NOT a sample-size effect: at n=3000 iid, the marginal
    sits on the nominal level. Only autocorrelation moves it."""
    rng = np.random.default_rng(12)
    marginal = np.mean([
        coverage(_iid_trace(rng), (K_PRIMARY,))[0] for _ in range(20)
    ])
    assert abs(marginal - (1.0 - ALPHA)) < 0.003


def test_autocorrelation_undercovers_the_marginal():
    """Jensen: coverage is concave in the estimated sd, and a larger tau
    widens that estimate's spread, so the deficit grows with tau."""
    fast = np.mean([
        coverage(trace(0.0, 1.0, WINDOWS, np.random.default_rng(20 + i), tau_s=1.0),
                 (K_PRIMARY,))[0] for i in range(12)
    ])
    slow = np.mean([
        coverage(trace(0.0, 1.0, WINDOWS, np.random.default_rng(20 + i), tau_s=30.0),
                 (K_PRIMARY,))[0] for i in range(12)
    ])
    assert slow < fast < 1.0 - ALPHA + 0.002
    assert slow < 1.0 - ALPHA


# --------------------------------------------------- the proposition itself
def test_omega_raises_simultaneous_coverage_and_leaves_marginal_flat():
    """COV-1 and COV-2 in miniature: the built-in negative control must hold."""
    marginal, simultaneous = [], []
    for omega in (0.0, 1.0):
        rows = [
            coverage(trace(omega, SF_PRIMARY, WINDOWS,
                           np.random.default_rng(30 + i)), (K_PRIMARY,))
            for i in range(12)
        ]
        marginal.append(np.mean([r[0] for r in rows]))
        simultaneous.append(np.mean([r[K_PRIMARY] for r in rows]))
    assert abs(marginal[1] - marginal[0]) < 0.005      # flat: negative control
    assert simultaneous[1] - simultaneous[0] > 0.05    # moves: the effect


def test_trace_refuses_omega_and_signal_fraction_outside_range():
    rng = np.random.default_rng(40)
    for bad in ((-0.1, 0.85), (1.1, 0.85)):
        with pytest.raises(ValueError):
            trace(bad[0], bad[1], 100, rng)
    for bad_sf in (0.0, 1.5):
        with pytest.raises(ValueError):
            trace(0.5, bad_sf, 100, rng)
