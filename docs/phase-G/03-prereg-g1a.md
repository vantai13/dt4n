# Phase G1-A preregistration — synthetic measurement-estimator validation

Signed before the first invocation of `tools/g1a_estimator_validation.py`.
This diagnostic reads no experimental data and creates no RAW network data.

## Locked synthetic truth

- `dt=0.20 s`, `tau=3.0 s`, `sigma=0.03`, `n=30,000`, 16 seeds.
- `sf_true in {0.30,0.50,0.70,0.85,0.95}`.
- Two independent normalized AR(1) signals, so `r_true=0` by construction.
- The same white nugget is added to both channels, so `rho_epsilon_true=1`.
- Nugget variance is `v=sigma^2*(1/sf_true-1)`.
- Signal-fraction fit uses at most the first eight ACF lags and retains only
  lags above the locked noise floor `2/sqrt(n)`.

## Locked G1-0 gates

- At every sf: `abs(sf_hat/sf_true-1) <= 0.15`.
- At every sf: `abs(rho_epsilon_hat-1) <= 0.10` for the raw first-difference
  estimator supplied for G1-C.
- Report the leakage estimate, analytically true leakage, validity fraction,
  and theoretical attenuated raw difference correlation at every sf.
- Overall PASS requires both gates at every sf.  On FAIL, neither estimator may
  be applied to Phase D data and no G1-B/G1-C scientific claim may be made.

The preregistration tag is `phase-G-g1a-prereg`.
