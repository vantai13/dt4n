"""Lock the two things G5a/G5b can most easily get wrong."""
import numpy as np
import pytest

from cert import simultaneous_score as S
from tools import g5a_mechanism_audit as audit
from tools import g5b_power_axis as power


def test_coupling_sum_separates_the_null_pair_from_a_larger_uncoupled_set():
    """K is not the controlling variable; the in-subset coupling is."""
    assert audit.coupling_sum(('uA', 'uB')) == 0.0
    assert audit.coupling_sum(('ac', 'ad', 'bc', 'bd')) == 0.0
    assert audit.coupling_sum(('uA', 'ac')) == pytest.approx(0.707, abs=1e-3)
    # a K=2 coupled pair carries more coupling than a K=4 uncoupled set
    assert audit.coupling_sum(('uA', 'ac')) > audit.coupling_sum(('ac', 'ad', 'bc', 'bd'))


def test_conformal_is_exactly_scale_equivariant_on_the_score_matrix():
    """The reason coverage cannot move: qhat scales by c and the test is invariant."""
    rng = np.random.default_rng(0)
    cal, test = rng.gamma(2., 1., (500, 3)), rng.gamma(2., 1., (500, 3))
    base_q = S.qhat_maxscore(cal.max(axis=1), .10)
    base_cov = S.coverage_simultaneous(test, base_q)
    for c in (1.3131, 2.0, 7.5):
        q = S.qhat_maxscore((cal * c).max(axis=1), .10)
        assert q == pytest.approx(c * base_q, rel=1e-12)
        assert S.coverage_simultaneous(test * c, q) == base_cov


def test_surrogate_scales_scores_and_leaves_the_twin_margins_alone():
    """Scaling the twin error re-ranks rows; the surrogate must not do that."""
    rng = np.random.default_rng(1)
    scores, margins = rng.gamma(2., 1., (400, 3)), rng.gamma(2., 3., (400, 3))
    tight = power.scale_surrogate(scores, margins, 1.0)
    loose = power.scale_surrogate(scores, margins, 2.0)
    # a larger qhat can only reject more, never accept more
    assert loose['maxscore'] <= tight['maxscore']
    assert loose['uncorrected'] <= tight['uncorrected']


def test_adjudicate_takes_the_conservative_branch_when_a_gate_fails():
    strong = {'maxscore': {'amplitude': .10, 'snr': 8., 'worst_step': -.03,
                           'coverage_amplitude': .001, 'irreducible_remainder': .005}}
    null = {'maxscore': {'amplitude': 0.}}
    verdict = power.adjudicate(strong, null)
    assert verdict['verdict'] == 'ADOPT_WEAK'          # P-3 fails on a decreasing series
    assert verdict['classification'] is None           # no classification without a clean pass
