"""Unit tests for the EMIT-3 decomposition diagnostic.

The tool adjudicates nothing, but doc 46 reads its reductions, so the
reductions themselves are machine checked: a diagnostic nobody can trust is
worse than no diagnostic, because it still gets quoted.
"""
from __future__ import annotations

import numpy as np
import pytest

from tools.g2_topology import LINKS
from tools.g3_emit3_decomposition import (
    ARMS,
    LIMITS,
    _rank,
    co_spike_fraction,
    co_spike_null,
    staggered_overlap_baseline,
)


# ------------------------------------------------------------- co-spike
def test_co_spike_null_matches_the_binomial_tail():
    from math import comb
    expected = sum(comb(8, k) * 0.1**k * 0.9**(8 - k) for k in range(6, 9))
    assert abs(co_spike_null() - expected) < 1e-15
    assert abs(co_spike_null() - 2.341e-05) < 1e-8


def test_co_spike_is_near_null_for_independent_links():
    rng = np.random.default_rng(1)
    values = [co_spike_fraction(np.abs(rng.standard_normal((len(LINKS), 100))))
              for _ in range(40)]
    assert float(np.mean(values)) < 0.01          # null is 2.3e-05


def test_co_spike_fires_on_a_rare_shared_stall():
    """POSITIVE CONTROL: a machine-wide stall must be counted, not averaged away."""
    rng = np.random.default_rng(2)
    matrix = np.abs(rng.standard_normal((len(LINKS), 100)))
    matrix[:, :5] += 8.0
    assert co_spike_fraction(matrix) >= 0.05


def test_co_spike_saturates_when_the_stall_is_not_rare():
    """The statistic is calibrated for RARE shared stalls, and says so.

    The threshold is each link's OWN empirical 90th percentile, so a stall
    occupying more than about a tenth of the windows raises the threshold it
    would have to cross and hides itself. The observed host value of 0.029
    sits well inside the usable range; a value near or above 0.10 would have
    to be read as saturation, not as absence of coupling.
    """
    rng = np.random.default_rng(5)
    matrix = np.abs(rng.standard_normal((len(LINKS), 100)))
    matrix[:, :40] += 8.0
    assert co_spike_fraction(matrix) < 0.15


# ---------------------------------------------------------------- rank
def test_rank_is_a_permutation_per_row():
    rng = np.random.default_rng(3)
    ranked = _rank(rng.standard_normal((len(LINKS), 50)))
    for row in ranked:
        assert sorted(row.tolist()) == list(range(50))


def test_spearman_is_insensitive_to_a_monotone_transform():
    rng = np.random.default_rng(4)
    base = np.abs(rng.standard_normal((len(LINKS), 200)))
    assert np.allclose(np.corrcoef(_rank(base)), np.corrcoef(_rank(np.exp(base))))


# ------------------------------------------------- staggered null baseline
@pytest.fixture(scope="module")
def baseline():
    return staggered_overlap_baseline(
        aligned_correlation_targets=(0.20,),
        stall_bins_grid=(1, 20, 40),
        replicates=60,
    )


def test_baseline_never_falls_below_the_overlap_coefficient(baseline):
    """The null invariant doc 46 relies on.

    Staggering with no synchronisation component can only remove correlation
    mechanically. A ratio meaningfully BELOW the overlap coefficient is the
    signature of a real synchronisation contribution, so the null must never
    produce one; otherwise the observed positive residual proves nothing.
    """
    for row in baseline:
        assert row["residual_median"] > -0.05


def test_baseline_residual_increases_with_stall_duration(baseline):
    """Dose-response: longer shared stalls survive a window offset better."""
    residuals = [row["residual_median"] for row in baseline]
    assert residuals[-1] > residuals[0]


def test_baseline_point_stall_is_close_to_the_raw_overlap_coefficient(baseline):
    """With point stalls the naive overlap coefficient is nearly unbiased.

    This is why the baseline has to be calibrated rather than assumed: the
    bias is a function of stall duration, not a constant.
    """
    point = next(row for row in baseline if row["stall_bins"] == 1)
    assert abs(point["residual_median"]) < 0.05


def test_baseline_reports_its_pair_count_and_replicates(baseline):
    for row in baseline:
        assert row["pairs"] == len(LINKS) * (len(LINKS) - 1) // 2
        assert row["replicates"] == 60


# ------------------------------------------------------------ declarations
def test_every_arm_declares_what_it_kills_and_limits_are_recorded():
    assert len(ARMS) == 4
    assert all(arm["kills"] for arm in ARMS)
    assert len(LIMITS) >= 4


def test_limits_record_the_two_confounds_doc_46_depends_on():
    text = " ".join(LIMITS).lower()
    assert "confounded" in text          # A1 syscall cost
    assert "mechanically" in text        # A3 window overlap
    assert "sampler" in text             # untested candidate cause
