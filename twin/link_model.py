#!/usr/bin/env python3
"""DEPRECATED tu Phase 20R. Giu de tai lap phu luc v7.

Dung ``twin/link_model_v2.py`` cho moi cong viec moi. Xem
``docs/phase-20/99c-erratum-2.md``.

Calibrated routing link model from Lesson 9.0 Mininet measurements.

This replaces the previous M/M/1 curve. The measured Mininet/HTB+netem links
have three regimes under UDP constant-rate load:

* below the cliff, qdisc backlog is BDP/netem occupancy, not a waiting queue;
* in a very narrow critical band, the queue is metastable;
* above the band, the finite queue sits near full and overload is represented
  by loss.

Primary data:
    results/SUPERSEDED/calib/raw_sweep_2node.csv
    results/SUPERSEDED/calib/link_profiles.json
    results/SUPERSEDED/calib/qdisc_density.csv
    results/SUPERSEDED/calib/density_bw{4,6,8}_*.csv
    results/SUPERSEDED/calib/cliff_fine_*.csv
"""

# Rev5 interpretation: below the cliff, q_delay ~= base_delay * rho_measured
# because qdisc backlog equals BDP/netem occupancy. This is not an M/M/1
# queueing law and not evidence of congestion before saturation.
NETEM_OCCUPANCY_COEF = 1.0

# UDP offered-load overhead factor fitted from measured loss:
# loss = max(0, 1 - 1 / (OVERHEAD_FACTOR * rho_offered)).
OVERHEAD_FACTOR = 1.0790

# Fine density sweep:
#   rho_off=0.925 -> BDP occupancy only
#   rho_off=0.930 -> metastable full-range queue, q ~= 0.71 * ceiling
#   rho_off=0.935 -> near-full queue
CLIFF_RHO_OFFERED = 0.9275
CRITICAL_WIDTH = 0.005
CRITICAL_CEILING_FRACTION = 0.71
LOW_TO_CRITICAL_RHO_OFFERED = CLIFF_RHO_OFFERED - CRITICAL_WIDTH / 2.0
CRITICAL_TO_FULL_RHO_OFFERED = CLIFF_RHO_OFFERED + CRITICAL_WIDTH

# Loss-derived threshold, kept as a calibration cross-check.
OFFERED_CLIFF = 1.0 / OVERHEAD_FACTOR

# qdisc backlog includes link-layer bytes; density probes match BDP better with
# 1512 bytes than with the IP MTU of 1500.
MTU_BYTES = 1512

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


def queueing_delay_ms(base_delay_ms, rho_offered, bw_mbps=None, queue_pkts=None):
    """Return measured qdisc-delay contribution in milliseconds.

    ``rho_offered`` is offered load, not deployable measured utilization.

    Lesson 9.0 rev5:
      * below the cliff, the measured backlog is BDP/netem occupancy, so the
        contribution is ``base_delay_ms * measured_rho``;
      * in the critical band around rho_offered ~= 0.930, the queue is
        metastable and measured near 0.71 of the finite ceiling;
      * above the band, the qdisc sits near the finite queue ceiling;
      * overload magnitude is carried by ``loss_rate()``.

    The offered-load argument is required because measured utilization clips
    near 1.0 and cannot distinguish the critical point from full overload.
    """
    offered = _clamp_nonnegative(rho_offered)
    measured = rho_measured_from_offered(offered)
    ceiling = None
    if bw_mbps is not None and queue_pkts is not None:
        ceiling = queue_ceiling_ms(bw_mbps, queue_pkts)

    if offered <= LOW_TO_CRITICAL_RHO_OFFERED:
        q_delay = NETEM_OCCUPANCY_COEF * float(base_delay_ms) * measured
        if ceiling is not None:
            q_delay = min(q_delay, ceiling)
        return q_delay

    if ceiling is None:
        ceiling = 39.0

    if offered >= CRITICAL_TO_FULL_RHO_OFFERED:
        return ceiling

    return CRITICAL_CEILING_FRACTION * ceiling


def total_delay_ms(base_delay_ms, rho_offered, bw_mbps=None, queue_pkts=None):
    """Return propagation plus calibrated queueing delay."""
    return float(base_delay_ms) + queueing_delay_ms(
        base_delay_ms,
        rho_offered,
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
