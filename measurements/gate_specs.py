#!/usr/bin/env python3
"""Phase T gate specifications.

Each gate declares its retry class and, when applicable, the noise model behind
its threshold. This keeps Phase T thresholds from becoming magic constants.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from measurements.t4_validate import ca_operational_se, ca_operational_threshold, rho_bias_sd


GateFn = Callable[[dict, object, object], float]


@dataclass(frozen=True)
class GateSpec:
    name: str
    kind: str
    threshold_fn: GateFn
    noise_fn: Optional[GateFn]
    must_catch: List[str]
    corr_group: Optional[str]
    reference_sd_source: str
    relax_policy: str = "threshold"
    notes: str = ""
    max_false_fail: float = 0.01


def _n_ca_gaps(_row: dict, sched, _traj) -> int:
    return max(len(getattr(sched, "send_times", [])) - 1, 1)


def _meas_s(row: dict, _sched, traj) -> float:
    duration = float(row.get("duration_s", getattr(traj, "duration_s", 0.0)))
    warm = float(row.get("warmup_s", min(15.0, duration / 2.0)))
    return float(row.get("meas_s", max(duration - warm, 1e-9)))


GATES: Dict[str, GateSpec] = {
    "V-T0_digest_khop": GateSpec(
        name="V-T0_digest_khop",
        kind="deterministic",
        threshold_fn=lambda _r, _s, _t: 0.0,
        noise_fn=None,
        must_catch=["wrong_seed"],
        corr_group="seed",
        reference_sd_source="exact",
        relax_policy="never",
        max_false_fail=0.0,
    ),
    "V-T3_clamp": GateSpec(
        name="V-T3_clamp",
        kind="deterministic",
        threshold_fn=lambda _r, _s, _t: 0.01,
        noise_fn=None,
        must_catch=["over_clamp"],
        corr_group=None,
        reference_sd_source="invariant",
        notes="Deterministic clamp invariant, not a statistical noise gate.",
    ),
    "V-T4a_ca_operational": GateSpec(
        name="V-T4a_ca_operational",
        kind="deterministic",
        threshold_fn=lambda r, s, t: ca_operational_threshold(r["mode"], _n_ca_gaps(r, s, t)),
        noise_fn=lambda r, s, t: ca_operational_se(r["mode"], _n_ca_gaps(r, s, t)),
        must_catch=["round_inverse", "thinning_cbr", "thinning_h2"],
        corr_group="seed",
        reference_sd_source="analytic",
    ),
    "V-T4b_ca_pooled": GateSpec(
        name="V-T4b_ca_pooled",
        kind="deterministic",
        threshold_fn=lambda _r, _s, _t: 0.05,
        noise_fn=None,
        must_catch=["thinning_h2"],
        corr_group="seed",
        reference_sd_source="invariant",
        notes="Deterministic schedule-shape invariant for operational-time rescaling.",
    ),
    "V-T5a_delegation": GateSpec(
        name="V-T5a_delegation",
        kind="deterministic",
        threshold_fn=lambda _r, _s, _t: 0.0,
        noise_fn=None,
        must_catch=[],
        corr_group="seed",
        reference_sd_source="exact",
        relax_policy="never",
        max_false_fail=0.0,
    ),
    "V-T5a_phase_l_digest": GateSpec(
        name="V-T5a_phase_l_digest",
        kind="deterministic",
        threshold_fn=lambda _r, _s, _t: 0.0,
        noise_fn=None,
        must_catch=[],
        corr_group="seed",
        reference_sd_source="exact",
        relax_policy="never",
        max_false_fail=0.0,
    ),
    "V-T5b_q_phase_l": GateSpec(
        name="V-T5b_q_phase_l",
        kind="deterministic",
        threshold_fn=lambda _r, _s, _t: 3.0,
        noise_fn=None,
        must_catch=[],
        corr_group=None,
        reference_sd_source="cross_seed",
        notes=(
            "Legacy 105s V-T5b uses cross-seed Phase L sd only for an aggregate "
            "z diagnostic; cross-seed variance includes design variation and "
            "must not be used as a per-row 2 percent gate."
        ),
    ),
    "V-T5b_same_seed": GateSpec(
        name="V-T5b_same_seed",
        kind="deterministic",
        threshold_fn=lambda _r, _s, _t: 0.005,
        noise_fn=None,
        must_catch=[],
        corr_group="seed",
        reference_sd_source="replicates",
    ),
    "V-T6a_rate_ratio": GateSpec(
        name="V-T6a_rate_ratio",
        kind="deterministic",
        threshold_fn=lambda _r, _s, _t: 0.001,
        noise_fn=None,
        must_catch=["bad_rate"],
        corr_group="seed",
        reference_sd_source="invariant",
        notes="Deterministic generated-rate invariant, not a statistical noise gate.",
    ),
    "V-T6b_rho_bias": GateSpec(
        name="V-T6b_rho_bias",
        kind="deterministic",
        threshold_fn=lambda r, s, t: 3.0
        * rho_bias_sd(r["mode"], r["rho_bar"], r["bw"], r.get("warmup_s", 15.0), _meas_s(r, s, t)),
        noise_fn=lambda r, s, t: rho_bias_sd(
            r["mode"], r["rho_bar"], r["bw"], r.get("warmup_s", 15.0), _meas_s(r, s, t)
        ),
        must_catch=["sender_drift"],
        corr_group="seed",
        reference_sd_source="analytic",
    ),
    "A5-7_socket_drops": GateSpec(
        name="A5-7_socket_drops",
        kind="transient",
        threshold_fn=lambda _r, _s, _t: 0.0,
        noise_fn=None,
        must_catch=[],
        corr_group=None,
        reference_sd_source="analytic",
    ),
    "A5-7_n_foreign": GateSpec(
        name="A5-7_n_foreign",
        kind="transient",
        threshold_fn=lambda _r, _s, _t: 0.0,
        noise_fn=None,
        must_catch=[],
        corr_group=None,
        reference_sd_source="analytic",
    ),
    "A5-7_n_late": GateSpec(
        name="A5-7_n_late",
        kind="transient",
        # Breakdown threshold, not a quality threshold. Operational fidelity is
        # guarded directly by V-T4a/V-T6a/V-T6b. See Amendment 14.
        threshold_fn=lambda _r, _s, _t: 0.01,
        noise_fn=None,
        must_catch=["sender_stall"],
        corr_group=None,
        reference_sd_source="empirical_g3_127",
        notes=(
            "A14: threshold 1e-2 is 40x the observed operating mean and 11x "
            "the observed max over the first 127 G3 rows. n_late is a "
            "breakdown sentinel; V-T4a/V-T6a/V-T6b guard design fidelity."
        ),
    ),
    "A5-7_max_late": GateSpec(
        name="A5-7_max_late",
        kind="transient",
        threshold_fn=lambda _r, _s, _t: 100.0,
        noise_fn=None,
        must_catch=["sender_stall"],
        corr_group=None,
        reference_sd_source="empirical_g3_127",
        notes="A14: catches long sender stalls that count-based n_late can miss.",
    ),
}


def gate_names_by_kind(kind: str) -> List[str]:
    return [name for name, spec in GATES.items() if spec.kind == kind]
