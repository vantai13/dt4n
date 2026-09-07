#!/usr/bin/env python3
"""L2.0a -- invariants behind docs/phase-L2/00a-addendum-F7-F8.md.

No root, no network. These lock F7 (pacing), F9 (no residual service term)
and F10 (F8 binds pointwise), and are the reason doc 00's MAIN table is
retracted rather than merely doubted.
"""

import json
import os

import pytest

from tools.l2_0a_pacing_check import (
    FRAME_BYTES,
    STAGE2_BURST_BYTES,
    S_MS,
    S_PHASE_L_MS,
    ZERO_LOAD_BW6_MS,
    g_us_needed_for_one_frame,
    gap_cv,
    hybrid_overshoot,
    residual_service_ms,
    stage2_queue_under_paced_input,
    tb_departures,
    transient_frames,
    watchdog_frames_per_wake,
)

FIT = "results/LIVE/phase-L/link_model_v2_fit.json"


def test_F7_backlogged_output_is_paced_for_every_burst():
    """The core of F7: burst does not change the steady-state departure process."""
    baseline = None
    for burst in (1, 4, 12, 50):
        cv, mean_gap = gap_cv(tb_departures(0.90, burst))
        assert cv == pytest.approx(0.0, abs=1e-9)
        assert mean_gap == pytest.approx(S_MS / 0.90, rel=1e-9)
        if baseline is None:
            baseline = mean_gap
        assert mean_gap == pytest.approx(baseline, rel=1e-12)


def test_F7_mean_gap_tracks_rho_not_burst():
    for rho in (0.60, 0.80, 0.95):
        _, mean_gap = gap_cv(tb_departures(rho, 12))
        assert mean_gap == pytest.approx(S_MS / rho, rel=1e-9)


def test_F7_burst_is_a_one_time_transient_only():
    """`burst` frames leave at t=0 and then never again -- a backlogged source
    never lets the bucket refill. Over a 60 s run this is negligible."""
    frames_in_60s = 60_000.0 / (S_MS / 0.90)
    for burst in (1, 4, 12, 50):
        assert transient_frames(burst) == burst
        assert transient_frames(burst) / frames_in_60s < 0.002


def test_F7_watchdog_granularity_cannot_restore_on_off():
    """The one escape hatch, closed by arithmetic."""
    need = g_us_needed_for_one_frame(0.90)
    assert need == pytest.approx(2136.0, abs=5.0)
    # a generous hrtimer wake of 50 us releases far less than one frame
    assert watchdog_frames_per_wake(0.90, 50.0) < 0.05
    cv, _ = gap_cv(tb_departures(0.90, 12, 20_000, g_us=50.0))
    assert cv < 0.02


def test_F9_stage2_bucket_saturates_under_paced_input():
    assert STAGE2_BURST_BYTES > FRAME_BYTES
    assert stage2_queue_under_paced_input() == 0.0


@pytest.mark.skipif(not os.path.exists(FIT), reason="phase-L fit artifact absent")
def test_F9_residual_service_term_is_refuted_by_phase_L():
    """cbr IS the paced regime. Its measured excess over floor is ~0, while
    rho*s/2 would demand +0.60..+0.96 ms. Two orders of magnitude apart."""
    with open(FIT, "r", encoding="utf-8") as handle:
        fit = json.load(handle)
    rho_all = fit["rho_all"]
    y = fit["links"]["cbr|6|13"]["delay_observed"]
    for rho in (0.60, 0.80, 0.90, 0.95):
        excess = y[rho_all.index(rho)] - ZERO_LOAD_BW6_MS
        demanded = residual_service_ms(rho, S_PHASE_L_MS)
        assert abs(excess) < 0.02
        assert demanded > 0.55
        assert demanded > 25.0 * abs(excess)
    i60, i95 = rho_all.index(0.60), rho_all.index(0.95)
    assert y[i95] / y[i60] == pytest.approx(1.0, abs=0.05)   # not 1.583


def test_F10_no_queue_without_pointwise_overshoot():
    delay, frac = hybrid_overshoot(0.95, 0.0)
    assert frac == 0.0
    assert delay == pytest.approx(0.0, abs=1e-9)


def test_F10_queue_appears_exactly_when_rho_exceeds_one():
    """F8 is true pointwise, not on average -- so (2a) is not structurally dead."""
    prev = -1.0
    for sigma in (0.0, 0.05, 0.10, 0.20, 0.30):
        delay, frac = hybrid_overshoot(0.90, sigma)
        assert delay >= prev
        prev = delay
    strong, frac = hybrid_overshoot(0.90, 0.30)
    assert frac > 0.0
    assert strong > 1.0          # a real queue, same order as phase-L poisson 5.725
