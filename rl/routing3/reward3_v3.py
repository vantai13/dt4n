#!/usr/bin/env python3
"""Phase 14C routing reward, kept separate from the Phase 14A r_v2 reward.

This module fixes three technical issues diagnosed after Phase 14B.0 without
overwriting ``reward3.py``:

* clipping is an optional training choice, not the default evaluation metric;
* the terminal arrival constant is removed from route-action scoring;
* retransmission loss and SLA terms give overload/tail-risk a visible scale.
"""

from dataclasses import asdict, dataclass


REWARD_VERSION = "r_v3"

W_LOSS = 2.0
W_HOP = 0.02
DELAY_NORM_MS = 20.0

DELAY_CLIP_TRAIN = -1.0
DELAY_CLIP_EVAL = None

R_ARRIVED = 0.0
R_FAIL = -5.0

LOSS_SATURATION = 0.99
SLA_DELAY_MS = 10.0
W_SLA = 2.0

CRITICALITY_DEFAULT = 1.0


@dataclass
class RewardBreakdown:
    """Reward components recorded separately for audit."""

    delay_term: float = 0.0
    loss_term: float = 0.0
    sla_term: float = 0.0
    hop_term: float = 0.0
    terminal_term: float = 0.0
    criticality: float = CRITICALITY_DEFAULT
    total: float = 0.0

    def as_dict(self):
        return {f"r_{key}": round(float(value), 6)
                for key, value in asdict(self).items()}


def step_reward(
    delay_ms,
    loss,
    arrived=False,
    failed=False,
    criticality=CRITICALITY_DEFAULT,
    clip=DELAY_CLIP_EVAL,
):
    """Compute one-hop reward.

    ``clip=None`` is the evaluation/default mode.  Pass ``clip=-1.0`` only for
    training experiments that explicitly choose clipped delay rewards.
    """
    b = RewardBreakdown()
    v = float(criticality)
    b.criticality = v

    raw_delay = -float(delay_ms) / DELAY_NORM_MS
    b.delay_term = raw_delay if clip is None else max(float(clip), raw_delay)
    b.loss_term = -W_LOSS * loss_penalty(loss)

    excess_ms = max(0.0, float(delay_ms) - SLA_DELAY_MS)
    b.sla_term = -W_SLA * excess_ms / DELAY_NORM_MS
    b.hop_term = -W_HOP

    if arrived:
        b.terminal_term = R_ARRIVED
    elif failed:
        b.terminal_term = R_FAIL

    # Criticality scales only path-dependent quality terms.  Hop and terminal
    # terms remain outside it so they do not create artificial path preference.
    b.total = (
        v * (b.delay_term + b.loss_term + b.sla_term)
        + b.hop_term
        + b.terminal_term
    )
    return b


def loss_penalty(loss):
    """Expected extra transmissions: ``1 / (1 - loss) - 1``.

    Near zero loss this is approximately linear.  Near total loss it grows
    sharply, matching the operational cost of repeated retransmission attempts.
    """
    clipped = min(max(float(loss), 0.0), LOSS_SATURATION)
    return 1.0 / (1.0 - clipped) - 1.0


def sync_cost(criticality=CRITICALITY_DEFAULT, c_sync=0.05):
    """Return the reward-unit cost of a REQUEST_SYNC action.

    ``criticality`` is accepted for call-site symmetry with ``step_reward``.
    It is intentionally not used: sync cost is a control-plane parameter, not a
    conversion from data-plane delay.
    """
    del criticality
    return -float(c_sync)
