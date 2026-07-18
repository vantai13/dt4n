#!/usr/bin/env python3
"""Calibrated routing link model from Lesson 9.0 Mininet measurements.

This replaces the previous M/M/1 curve. The measured Mininet/HTB links have
finite queues: delay does not blow up as utilization approaches 1.0; queueing
delay is approximately linear until the finite queue ceiling is reached, then
excess offered traffic is dropped.

Primary data:
    results/calib/raw_sweep_2node.csv
    results/calib/link_profiles.json
"""

# Queueing law: q_delay ~= base_delay * rho_measured.
QUEUEING_COEF = 1.0

# UDP offered-load overhead factor fitted from measured loss:
# loss = max(0, 1 - 1 / (OVERHEAD_FACTOR * rho_offered)).
OVERHEAD_FACTOR = 1.0790

# Serialization packet size used for queue-ceiling calculations.
MTU_BYTES = 1500

# Ditto observes delivered throughput, so deployable measured utilization caps
# at capacity.
RHO_CAP = 1.0


def _clamp_nonnegative(value: float) -> float:
    return max(float(value), 0.0)


def queue_ceiling_ms(bw_mbps, queue_pkts):
    """Return the finite queue drain time in milliseconds."""
    try:
        bw = float(bw_mbps)
        q = float(queue_pkts)
    except (TypeError, ValueError):
        return float("inf")
    if bw <= 0.0 or q <= 0.0:
        return float("inf")
    return q * MTU_BYTES * 8.0 / (bw * 1e6) * 1000.0


def queueing_delay_ms(base_delay_ms, rho, bw_mbps=None, queue_pkts=None):
    """Return measured queueing delay in milliseconds.

    ``rho`` is measured utilization, not offered load. Optional ``bw_mbps`` and
    ``queue_pkts`` apply the finite queue ceiling. Once measured utilization
    saturates at 1.0, the missing overload information is carried by loss; the
    measured delay sits at the finite queue drain time.
    """
    rho = min(_clamp_nonnegative(rho), RHO_CAP)
    ceiling = None
    if bw_mbps is not None and queue_pkts is not None:
        ceiling = queue_ceiling_ms(bw_mbps, queue_pkts)
        if rho >= RHO_CAP:
            return ceiling

    q_delay = QUEUEING_COEF * float(base_delay_ms) * rho
    if ceiling is not None:
        q_delay = min(q_delay, ceiling)
    return q_delay


def total_delay_ms(base_delay_ms, rho, bw_mbps=None, queue_pkts=None):
    """Return propagation plus calibrated queueing delay."""
    return float(base_delay_ms) + queueing_delay_ms(
        base_delay_ms,
        rho,
        bw_mbps=bw_mbps,
        queue_pkts=queue_pkts,
    )


def loss_rate(rho_offered):
    """Return loss as a function of offered utilization.

    The argument is ``rho_offered``. A measured rho cannot represent how far
    above capacity the sender tried to go because delivered throughput is
    clipped at 1.0.
    """
    inflated = OVERHEAD_FACTOR * _clamp_nonnegative(rho_offered)
    if inflated <= 1.0:
        return 0.0
    return min(1.0 - 1.0 / inflated, 1.0)


def rho_measured_from_offered(rho_offered):
    """Return the measured utilization that Ditto would expose."""
    return min(OVERHEAD_FACTOR * _clamp_nonnegative(rho_offered), RHO_CAP)
