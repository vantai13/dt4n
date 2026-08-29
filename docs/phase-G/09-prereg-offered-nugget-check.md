# Preregistration — offered-ledger nugget check before G-A003

Signed before the first computation of `sf` on the aggregated `cellA_long`
offered ledger.  This check decides whether G-A003 may retain the current H6
measurement-path interpretation or must redesign it around a generator-side
fast component.

## Locked input and estimator

- Input: `results/RAW/phase-D/cellA_long/rho_offered_rep1.csv`.
- All eight links; no row selection and no burn.
- Average each consecutive 20 samples (`dt=0.01 s`) into one `dt=0.20 s` bin.
- Use `estimate_nugget(..., dt=0.20, n_fit_lags=8)` exactly as validated in
  G1-0a.  Do not clamp `sf` or `v` and retain boundary-invalid diagnostics.

## Locked A/B interpretation

- Result A: all eight links satisfy `abs(sf_hat-1)<=0.05`.  The offered ledger
  has no detected nugget at the measurement scale, supporting a
  measurement-path origin; G-A003 may proceed without rewriting H6.
- Result B: median edge `sf_hat<0.95`.  A fast component is present in the
  generator ledger itself; stop before G-A003 and rewrite H6/design.
- Anything else is `INCONCLUSIVE_MIXED_OFFERED_SF` and also stops G-A003.

The test is a preregistered diagnostic on existing data, not a new-data
confirmatory experiment.  Tag: `phase-G-offered-nugget-check-prereg`.
