# G1-4 preregistration — physical positive control and Phase-23 reanalysis

Signed before the first execution of `tools/g1_4_physical_reanalysis.py` and
before any two-band outcome was computed on the physical traces.  Schema and
paths were inspected first.  Existing `sf` and raw-correlation summaries from
Phase D were already known; this is therefore a preregistered reanalysis of
existing data, not an independent new-data confirmatory experiment.

## Data and locked preprocessing

- `cellA_long`: one measured trace at nominal `dt=0.20 s` and its same-run
  offered ledger at `dt=0.01 s`.
- Phase-23 clean `rho_bar=0.925`: three measured/offered same-run pairs.
- Pivot all eight links by `sample_index`; no burn and no outcome-based row
  selection.
- Aggregate offered load by averaging each consecutive 20 samples, then take
  the first `n_measured` complete bins.  This yields a ground-truth correlation
  matrix at the measurement scale.
- Estimate each link's `sf` and early-lag exponential `phi` using the locked
  eight-lag G1-0a estimator.  No clipping of `sf`, `r_true`, or `rho_epsilon`.
- Use link-specific `phi_l` and `phi_m`.  For unequal memory, the difference
  equation's signal coefficient includes
  `q=(2-phi_l-phi_m)/(2*sqrt((1-phi_l)(1-phi_m)))`.

## Pre-physical synthetic gate

Before reading physical outcomes, validate the unequal-timescale extension at
`tau in {3,30} s`, asymmetric `sf`, two `(r_true,rho_epsilon)` scenarios,
30,000 samples and 16 seeds.  Median errors must be at most 0.05 and
`cond(A)<=10`.  On failure, the script exits before loading physical traces.

## Locked G1-4 gates

- G1-4A: all eight per-link nugget fits valid in `cellA_long`.
- G1-4B: all 28 `cellA_long` pairs valid and
  `abs(r_true_hat-r_offered)<=0.10`.
- G1-4C: all eight per-link nugget fits valid in every Phase-23 replicate.
- G1-4D: for all 28 Phase-23 pairs, all three estimates valid and the median
  `abs(r_true_hat-r_offered)<=0.10`.
- G1-4E: primary `uA-uB` and `vC-vD` have `abs(r_true_hat)<=0.15` in both
  campaigns.
- G1-4F: primary pairs have `abs(rho_epsilon_hat-1)<=0.20` in both campaigns.
- G1-4G: primary `rho_epsilon_hat` differs by at most 0.20 between campaigns.

Report all 28 pairs, every per-link `sf/phi`, condition numbers, physical-range
diagnostics, exact input SHA256 values, and all failed gates.  No threshold is
changed after execution.

Preregistration tag: `phase-G-g1-4-prereg`.
