#!/usr/bin/env python3
"""RouteEnv reward, deliberately simple and auditable."""

from dataclasses import asdict, dataclass


REWARD_VERSION = 'r_v2'

W_LOSS = 0.5
W_HOP = 0.02
R_ARRIVED = 5.0
R_FAIL = -5.0
DELAY_NORM_MS = 20.0

# r_v1 inherited DELAY_NORM_MS=100 from the old 50-100 Mbps topology. TOPO V2
# uses a smaller 4-8 Mbps budget where routing-relevant delays are closer to
# 2-20ms. With W_HOP=0.10, the hop penalty dominated the delay/loss signal and
# Dijkstra chose by hop count instead of by load. r_v2 restores the E/F flip.


@dataclass
class RewardBreakdown:
    """Reward components recorded separately for later audit."""

    delay_term: float = 0.0
    loss_term: float = 0.0
    hop_term: float = 0.0
    terminal_term: float = 0.0
    total: float = 0.0

    def as_dict(self):
        return {f'r_{k}': round(float(v), 6) for k, v in asdict(self).items()}


def step_reward(delay_ms, loss, arrived=False, failed=False):
    """Compute reward from true link metrics."""
    b = RewardBreakdown()
    b.delay_term = -float(delay_ms) / DELAY_NORM_MS
    b.loss_term = -W_LOSS * float(loss)
    b.hop_term = -W_HOP
    if arrived:
        b.terminal_term = R_ARRIVED
    elif failed:
        b.terminal_term = R_FAIL
    b.total = b.delay_term + b.loss_term + b.hop_term + b.terminal_term
    return b
