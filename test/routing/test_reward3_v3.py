#!/usr/bin/env python3
"""Tests for the Phase 14C routing reward."""

import sys

sys.path.insert(0, ".")

from rl.routing3 import link_model as LM  # noqa: E402
from rl.routing3 import reward3, reward3_v3, topology3 as T3  # noqa: E402


def test_reward3_v3_default_eval_does_not_clip_delay():
    reward = reward3_v3.step_reward(delay_ms=30.0, loss=0.0)

    assert reward.delay_term == -1.5
    assert reward.total < -1.0


def test_reward3_v3_can_clip_delay_for_training_only():
    reward = reward3_v3.step_reward(
        delay_ms=30.0,
        loss=0.0,
        clip=reward3_v3.DELAY_CLIP_TRAIN,
    )

    assert reward.delay_term == -1.0


def test_reward3_v3_arrival_terminal_constant_is_zero():
    arrived = reward3_v3.step_reward(delay_ms=1.0, loss=0.0, arrived=True)
    failed = reward3_v3.step_reward(delay_ms=1.0, loss=0.0, failed=True)

    assert reward3_v3.R_ARRIVED == 0.0
    assert arrived.terminal_term == 0.0
    assert failed.terminal_term == reward3_v3.R_FAIL


def test_reward3_v3_criticality_scales_only_path_quality_terms():
    full = reward3_v3.step_reward(delay_ms=30.0, loss=0.2, criticality=1.0)
    low = reward3_v3.step_reward(delay_ms=30.0, loss=0.2, criticality=0.2)

    quality = full.delay_term + full.loss_term + full.sla_term
    expected = 0.2 * quality + full.hop_term
    assert abs(low.total - expected) < 1e-12
    assert low.hop_term == full.hop_term


def test_reward3_v3_loss_penalty_matches_expected_retransmissions():
    assert reward3_v3.loss_penalty(0.0) == 0.0
    assert abs(reward3_v3.loss_penalty(0.2) - 0.25) < 1e-12
    assert reward3_v3.loss_penalty(1.0) == reward3_v3.loss_penalty(
        reward3_v3.LOSS_SATURATION
    )


def test_reward3_v3_sync_cost_is_not_delay_conversion():
    assert reward3_v3.sync_cost(c_sync=0.023) == -0.023
    assert reward3_v3.sync_cost(criticality=0.2, c_sync=0.023) == -0.023


def test_reward3_v3_restores_overload_delay_dynamic_range():
    meta = T3.link_cfg()[T3.BOTTLENECK_LINKS["P1"]]

    def delay_loss(rho):
        delay_ms = LM.total_delay_ms(
            meta["base_delay"],
            rho,
            bw_mbps=meta["base_bw"],
            queue_pkts=meta["queue_pkts"],
        )
        return delay_ms, LM.loss_rate(rho)

    lo_delay, lo_loss = delay_loss(0.93)
    hi_delay, hi_loss = delay_loss(1.30)
    lo_v2 = reward3.step_reward(lo_delay, lo_loss)
    hi_v2 = reward3.step_reward(hi_delay, hi_loss)
    lo_v3 = reward3_v3.step_reward(lo_delay, lo_loss)
    hi_v3 = reward3_v3.step_reward(hi_delay, hi_loss)

    assert lo_v2.delay_term == hi_v2.delay_term == reward3.DELAY_CLIP
    assert abs(hi_v3.delay_term - lo_v3.delay_term) > 0.1
    assert abs(hi_v3.total - lo_v3.total) > abs(hi_v2.total - lo_v2.total)
    assert abs(hi_v3.loss_term - lo_v3.loss_term) > abs(
        hi_v2.loss_term - lo_v2.loss_term
    )


def _run_as_script():
    tests = [
        test_reward3_v3_default_eval_does_not_clip_delay,
        test_reward3_v3_can_clip_delay_for_training_only,
        test_reward3_v3_arrival_terminal_constant_is_zero,
        test_reward3_v3_criticality_scales_only_path_quality_terms,
        test_reward3_v3_loss_penalty_matches_expected_retransmissions,
        test_reward3_v3_sync_cost_is_not_delay_conversion,
        test_reward3_v3_restores_overload_delay_dynamic_range,
    ]
    for test in tests:
        test()
        print(f"  PASS  {test.__name__}")
    print(f"\n{len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    _run_as_script()
