# Calibration Replaces The Old E/F Decision

## Finding

The old E/F route choice depended on an M/M/1 blow-up near `rho=1.0`. Lesson
9.0 Mininet measurements showed that this blow-up is not physical for the HTB
links used here: delivered utilization saturates, queueing delay is roughly
linear before saturation, and overload appears through finite-queue delay plus
loss.

## Consequence

Using only the old calibrated-linear delay made E win almost everywhere in the
original topology, so the agent could ignore utilization. Using the measured
finite-queue cliff restores a real decision:

- Below saturation, the narrow-fast E path can be cheaper.
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

The cliff is directly bracketed, not directly pinpointed. Measurements show
`rho_offered=0.90` still has low queueing delay, while `rho_offered=0.95`
hits the finite queue ceiling. The `0.927` threshold comes from the fitted
overhead factor, so a tighter calibration would need an extra sweep inside
`0.90..0.95`.

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
