# G.1 closeout run summary

Run date: 2026-08-31 UTC. No new Mininet run was used.

## Mechanism audit

The supplied continuation assumed cumulative packet accounting (`1/6`,
`ACF(1)=-0.5`). The repository is preregistered and implemented as independent
per-window `round()` with no carry accumulator. A 500,000-window check measured
`Var(error)=0.08307--0.08336` and `ACF(1)=-0.0017--0.0016`, confirming
`1/12` and white error. The cumulative comparison measured
`Var(error)=0.16621--0.16696` and `ACF(1)=-0.5007-- -0.4984`.

The two laws are now separate explicit modes in `tools/g1_quant_model.py`.

## Results

- Wire accounting corrected from 1400 payload bytes to 1442 wire bytes.
- Feasibility: 17/40 -> 9/40 cells.
- Surviving grid: `dt=0.2`, sigma `{0.02023,0.03035,0.04047}`, tau
  `{3,10,30}`.
- Independent-round validation: 12/12 PASS; maximum signal-fraction error
  `0.02152`, maximum held-out lag-3 error `0.00328`.
- Existing IPv6-off RAW: 24 link-runs; raw non-quantised sigma
  `0.00000--0.00211`.
- Conservative measured `sigma_min(sf>=0.85) = 0.01111`.
- Binding campaign boundary remains the analytic headroom gate:
  `sigma >= 0.0202326`.
- Static cross-link `rho_eps`: not identifiable at the declared
  `|r|=0.50` threshold. Mechanistic null width reaches 5.8 times the iid
  approximation.

## Artifact locations

- Validation: `results/SMOKE/phase-G/g1_closed_form_validation.json`
- RAW replay: `results/SMOKE/phase-G/g1_closed_form_sf.json`
- Nulls: `results/SMOKE/phase-G/g1_null_{matched,tight,default}_rep1.json`
- Closeout: `docs/phase-G/27-g1-closeout.md`
- Conditional certificate: `results/LIVE/phase-G/measurement_path_cert.json`
