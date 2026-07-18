# Calibration Replaces The Old E/F Decision

## Finding

The old E/F route choice depended on an M/M/1 blow-up near `rho=1.0`. Lesson
9.0 Mininet measurements showed that this blow-up is not physical for the
HTB+netem links used here: delivered utilization saturates, subthreshold qdisc
backlog is BDP/netem occupancy rather than congestion, a narrow critical band
appears around `rho_offered=0.930`, and overload appears through a finite-queue
cliff plus loss.

## Consequence

Using only the old calibrated-linear delay made E win almost everywhere in the
original topology, so the agent could ignore utilization. Using the measured
finite-queue cliff restores a real decision:

- Below saturation, the narrow-fast E path can be cheaper because there is no
  measured congestion buildup.
- Above saturation, C/D->E jumps to the finite queue ceiling and loss appears,
  so the F path becomes cheaper.

## Design Changes

- `RouteEnv` now samples `rho_offered`, which may exceed `1.0`.
- `rho_snapshot` remains measured/deployable utilization and is capped at
  `1.0`.
- `loss_snapshot` carries overload information after utilization saturates.
- Route state is now 9-D: two util dimensions, two loss dimensions, one valid
  bit, and two AoI dimensions.
- The C/D->F base delay is set to `6.0ms` and `LOAD_CFG_TRAIN` uses
  `base_load=(0.75, 0.95)`, `e_load=(0.70, 1.00)` so the full route decision,
  including E->F and hop
  penalty, passes the pre-train oracle gate.

## Limitation

The cliff is now directly bracketed by the fine density sweep. Measurements
show `rho_offered=0.925` still has only BDP occupancy, while
`rho_offered=0.930` enters a metastable middle/high-queue regime and
`rho_offered>=0.935` is near the finite queue ceiling.

The density follow-up resolves the meaning of the low-load linear-looking
region: `q_delay ~= base_delay * rho_measured` is BDP/netem occupancy, not a
queueing law. See `docs/phase-9/02-density-resolves-law.md`.

## Gate Validation

The pre-train oracle gate includes negative controls. It rejects the
Phase-8-style load range and an obvious always-E range, proving the gate still
has discriminating power after drift-aware sampling.

## Baseline Steelman

`ospf_calibrated` uses expected link cost, `E[cost(rho)]`, not cost at mean
load, `cost(E[rho])`. This matters because the measured finite-queue cliff
makes the cost nonlinear near saturation. The baseline is therefore a competent
static admin policy that knows historical load/capacity but still does not use
realtime twin state.
