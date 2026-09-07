#!/usr/bin/env python3
"""L2.0 -- analytic invariants behind docs/phase-L2/00-mechanism-gap-audit.md.

No root, no network, no measurement. These lock the three derivations the audit
signs, plus the two guard behaviours that a divide-by-nothing would hide.
"""

import json
import math
import os

import pytest

from tools.l2_0_audit_check import (
    BETA_MS,
    BFIFO_BYTES,
    FRAME_BYTES,
    PHASE_L_FRAME_BYTES,
    R_DETERMINISTIC,
    R_MD1,
    S_MS,
    amplification_ratio,
    delay_q_ms,
    sawtooth_stats,
    stage1_head_of_line_ms,
    vmax_ms,
)

FIT = "results/LIVE/phase-L/link_model_v2_fit.json"


def test_frame_time_matches_phase_g_constants():
    # tools/g2_kill_test.py:50 frame 1442 B on a 6 Mbps link
    assert S_MS == pytest.approx(1.922667, abs=1e-6)
    # docs/phase-L/01-infra.md:40 burst 1600 B is MORE than one frame of credit
    assert BETA_MS > S_MS


def test_measured_staircase_is_reproduced():
    """docs/phase-L/02-probe-validation.md:69-78, bw=6 q=13, frame 1512 B.

    The audit's vmax must reproduce the column that was actually measured, or
    the whole derivation is fitted to the wrong kernel behaviour.
    """
    c_bps, burst = 6_000_000.0, 1600.0
    predicted = [1.899, 3.915, 5.931, 7.947, 9.963, 11.979]
    for k, want in zip(range(3, 9), predicted):
        got = ((k - 1) * PHASE_L_FRAME_BYTES - burst) * 8.0 / c_bps * 1000.0
        assert got == pytest.approx(want, abs=0.002)
    # and k <= 2 is free: two frames pass on a 1600 B bucket, not one
    for k in (1, 2):
        assert ((k - 1) * PHASE_L_FRAME_BYTES - burst) <= 0.0


def test_burst_of_one_frame_yields_no_stage2_queue():
    """g2_kill_test.py:92 sets burst = one frame; that is the flat cell."""
    for rho in (0.60, 0.80, 0.90, 0.95, 0.99):
        assert delay_q_ms(rho, 1) == 0.0
    # the stage-2 burst credit swallows n=2 as well, so B=2 is a dead cell too
    assert vmax_ms(2) == 0.0
    assert delay_q_ms(0.95, 2) == 0.0


def test_delay_is_linear_in_rho_so_R_is_burst_independent():
    for n in (4, 8, 12):
        r = amplification_ratio({0.60: delay_q_ms(0.60, n), 0.95: delay_q_ms(0.95, n)})
        assert r == pytest.approx(R_DETERMINISTIC, abs=1e-9)
    assert R_DETERMINISTIC == pytest.approx(1.5833333, abs=1e-6)
    assert R_MD1 == pytest.approx(12.6666667, abs=1e-6)
    assert R_MD1 / R_DETERMINISTIC == pytest.approx(8.0, abs=1e-9)


def test_analytic_matches_independent_sawtooth_sampling():
    """The closed form is checked against Poisson sampling of the same process."""
    for n in (4, 8, 12):
        for rho in (0.60, 0.90, 0.95):
            mean, _sd, count = sawtooth_stats(rho, n)
            assert count > 20000
            assert mean == pytest.approx(delay_q_ms(rho, n), rel=0.03)


def test_planning_note_formula_overstates_because_it_drops_beta():
    """rho*(n-1)^2*s/(2n) omits the stage-2 burst credit.

    R is unaffected (beta is in the rho-independent prefactor), but the signed
    magnitudes are not, so the prereg table must not use the note's numbers.
    """
    for n, want_pct in ((4, 151.8), (8, 41.2), (12, 23.7)):
        note = 0.90 * (n - 1) ** 2 * S_MS / (2.0 * n)
        got = delay_q_ms(0.90, n)
        assert (note - got) / got * 100.0 == pytest.approx(want_pct, abs=0.2)


def test_amplification_ratio_returns_nan_not_zero_on_flat_denominator():
    """A 0 here would PASS the `R <= 3.0` gate by dividing by nothing."""
    r = amplification_ratio({0.60: 0.0, 0.95: 5.0})
    assert math.isnan(r)
    assert not math.isinf(r)
    r_neg = amplification_ratio({0.60: -0.01, 0.95: 5.0})
    assert math.isnan(r_neg)


def test_stage1_backlog_would_swamp_the_stage2_signal():
    """Probe injected behind the backlogged source cannot see stage 2.

    blast_source.py:29 blocks, so the stage-1 pfifo (g2_kill_test.py:95,
    limit 300) stays full. Head-of-line delay there is two orders of magnitude
    above the largest stage-2 cell.
    """
    hol = stage1_head_of_line_ms(0.90)
    assert hol > 600.0
    assert hol / delay_q_ms(0.90, 12) > 50.0


def test_bfifo_capacity_in_1442_byte_frames():
    """Phase L sized bfifo in 1512 B frames; Phase G' frames are 1442 B."""
    assert int(BFIFO_BYTES // FRAME_BYTES) == 13
    assert (12 - 1) * FRAME_BYTES < BFIFO_BYTES     # n=12 fits, no clipping
    assert (26 - 1) * FRAME_BYTES > BFIFO_BYTES     # n=26 overflows, OVF arm


@pytest.mark.skipif(not os.path.exists(FIT), reason="phase-L fit artifact absent")
def test_phase_l_campaign_already_separates_the_two_hypotheses():
    """The discriminator is calibrated on data that ALREADY EXISTS.

    cbr (c_a ~ 0) is flat; poisson (c_a ~ 1) lands on the M/D/1 prediction.
    h2 lands at 3.7 despite being strongly stochastic, because 8.9% loss
    truncates its tail -- which is why the gate cannot be read on R alone.
    """
    with open(FIT, "r", encoding="utf-8") as handle:
        fit = json.load(handle)
    rho = fit["rho_all"]
    i60, i95 = rho.index(0.60), rho.index(0.95)

    def ratio(mode):
        y = fit["links"]["%s|6|13" % mode]["delay_observed"]
        return y[i95] / y[i60]

    assert ratio("cbr") == pytest.approx(1.0, abs=0.05)
    assert ratio("poisson") > 6.0
    assert abs(ratio("poisson") - R_MD1) / R_MD1 < 0.25
    # h2 is stochastic yet falls in the note's INCONCLUSIVE band
    assert 3.0 < ratio("h2") < 6.0
    assert fit["links"]["h2|6|13"]["loss_observed"][i95] > 0.05
    assert fit["links"]["cbr|6|13"]["loss_observed"][i95] == 0.0
