# G-A002 preregistration — two-band G1-A estimator

Signed before the first run of `tools/g1a_two_band_validation.py`.
This amendment uses no experimental data and preserves the original G1-A
receipt unchanged.

## Reclassification of the existing receipt

- G1-0a: signal-fraction estimator PASS 5/5; do not rerun.
- G1-0b: measurement-error attenuation model PASS if the five existing raw
  difference correlations match `rho_epsilon/(1+lambda)` within 0.01, where
  `lambda=(1-phi)*sf/(1-sf)`.  The already-recorded maximum error is 0.000584.
- The raw difference statistic is retained as a positive control, not used as
  a direct `rho_epsilon` estimator outside negligible leakage.

## Locked G1-0c synthetic design

- `dt=0.20 s`, `tau=3.0 s`, `sigma=0.03`, `n=30,000`, 16 seeds.
- `sf in {0.30,0.50,0.70,0.85,0.95}`.
- Scenarios `(r_true,rho_epsilon) in {(0,1),(0.4,0.9)}`.
- Each signal pair is stationary AR(1) with the locked `r_true`; each white
  nugget pair has the locked `rho_epsilon`.
- The two-band estimator receives the known synthetic sf for both channels.

## Locked gates

- G1-0c: median `abs(r_true_hat-r_true) <= 0.05` in all ten cells.
- G1-0c: median `abs(rho_epsilon_hat-rho_epsilon) <= 0.05` in all cells.
- G1-0c validity: p95 `cond(A) <= 10` in all cells.
- G1-0d degeneracy guard: p05 `abs(w-sf) >= 0.05` in all cells.
- Report median, p05, p95, valid fraction, and physical-range fraction.
- Overall G1-0 PASS requires G1-0a, G1-0b, G1-0c, and G1-0d.

## Limits recorded before running

- G-L11: raw first-difference correlation has known sf-dependent bias and is
  only a positive control for the error model.
- G-L12: tightening raw leakage to 0.111 creates an empty intersection with
  the intended `sf>=0.85` operating region; it is not a viable main estimator.
- G-L13: the two-band estimator requires a well-conditioned system.  Retain
  `tau/dt>=10`; any relaxation requires a fresh condition-number audit.

Preregistration tag: `phase-G-g1a-g-a002-prereg`.
