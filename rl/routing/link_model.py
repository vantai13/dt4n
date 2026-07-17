#!/usr/bin/env python3
"""M/M/1 link model for RouteEnv.

The old routing simulator capped queueing delay directly. That hides the very
consequence this experiment needs: bad decisions near saturation must become
expensive. Here we cap utilization, a physical modeling choice, and leave the
M/M/1 curve itself intact.
"""

# UNCALIBRATED: inherited from the routing-sdn simulator lineage. Lesson 9.0
# measures these from Mininet and should replace them with link_profiles.json.
RHO_CAP = 0.97
LOSS_THRESHOLD = 0.85
LOSS_FULL = 1.20


def queueing_delay_ms(base_delay_ms: float, rho: float) -> float:
    """Return M/M/1 queueing delay in milliseconds."""
    rho = min(max(float(rho), 0.0), RHO_CAP)
    return float(base_delay_ms) * rho / (1.0 - rho)


def total_delay_ms(base_delay_ms: float, rho: float) -> float:
    """Return propagation plus queueing delay."""
    return float(base_delay_ms) + queueing_delay_ms(base_delay_ms, rho)


def loss_rate(rho: float) -> float:
    """Linear loss ramp once utilization passes LOSS_THRESHOLD."""
    rho = max(float(rho), 0.0)
    if rho <= LOSS_THRESHOLD:
        return 0.0
    overflow = (rho - LOSS_THRESHOLD) / (LOSS_FULL - LOSS_THRESHOLD)
    return min(max(overflow, 0.0), 1.0)
