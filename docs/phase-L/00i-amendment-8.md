# AMENDMENT 8 -- Phase L / L.7 residual band audit

Artifact:

```text
results/phase-L/link_model_v2_fit.json
docs/phase-L/07-fit.md
```

## A8-1  What we saw before the patch

The first L.7 fit reported:

```text
G-L7c_efficiency_mean  0.9999983111
G-L7c_efficiency_min   0.9999880949
G-L7c_efficiency_max   1.0
```

In the fit table, `sd_du` and `sigma_schedule` were equal to printed precision
on all 10 independent links. That was not a result; it was an identity.

The old band was computed with a full PCHIP interpolator fit on every measured
rho:

```text
PCHIP(rho_i) = ybar_i
resid_ij     = y_ij - PCHIP(rho_i)
             = y_ij - ybar_i
```

So `sd(resid) == sigma_schedule` by definition and `efficiency == 1`. This is
the same structural error as the Phase L.0 `NETEM_OCCUPANCY_COEF = 1.0`
failure: the comparison looked perfect because both sides were the same
formula.

## A8-2  Patch: leave-one-rho-out residuals

L.7 now computes residuals out of sample:

```text
for each rho_k:
    fit PCHIP on the grid except rho_k
    predict rho_k with that leave-one-rho-out model
    residual_kj = y_kj - f_{-k}(rho_k)
```

The endpoints `rho=0.50` and `rho=1.05` are reported separately as edge
residuals because leave-one-rho-out at an endpoint is extrapolation/clamping,
not interpolation.

The model now exports:

```text
noise_rms_ms              pooled within-cell seed noise on interior rho
noise_rms_all_ms          pooled within-cell seed noise on all rho
sigma_schedule_rms        RMS of per-rho sample SD values
bias_rms_interior_ms      RMS leave-one-rho-out interpolation bias
resid_sd_cv_interior_ms   actual out-of-sample residual band
resid_sd_cv_edge_ms       endpoint/extrapolation residual scale
sigma_by_rho              local per-rho residual scale
bias_by_rho               signed leave-one-rho-out model bias
```

`noise_rms_ms` is pooled on the same interior residual population as
`resid_sd_cv_interior_ms`; this avoids a degrees-of-freedom mismatch between
per-cell sample SDs and pooled residual SD. The all-rho and RMS variants remain
in JSON for audit.

## A8-3  Result after the patch

The new L.7 gate values are:

```text
G-L7c_efficiency_mean  0.7653108664
G-L7c_efficiency_min   0.1835043793
G-L7c_efficiency_max   0.9779416782
G-L7c_efficiency_pass  True
G-L7f_sentinel_oos     PASS
```

Band decomposition:

| mode | bw | q | noise rms | bias rms | sd cv band | efficiency | read |
|---|---:|---:|---:|---:|---:|---:|---|
| cbr | 4 | 10 | 1.1603 | 6.1806 | 6.3233 | 0.184 | model bias dominates |
| cbr | 6 | 13 | 2.7666 | 4.7340 | 6.5019 | 0.426 | model bias dominates |
| cbr | 8 | 18 | 1.7274 | 4.9474 | 5.2713 | 0.328 | model bias dominates |
| h2 | 4 | 10 | 0.2679 | 0.0801 | 0.2795 | 0.958 | near noise floor |
| h2 | 6 | 13 | 0.1943 | 0.0619 | 0.2016 | 0.964 | near noise floor |
| h2 | 8 | 18 | 0.2221 | 0.0495 | 0.2271 | 0.978 | near noise floor |
| onoff | 6 | 13 | 0.4847 | 0.1880 | 0.5171 | 0.937 | still good, more model error |
| poisson | 4 | 10 | 0.2187 | 0.0803 | 0.2324 | 0.941 | still good, more model error |
| poisson | 6 | 13 | 0.2595 | 0.0718 | 0.2680 | 0.968 | near noise floor |
| poisson | 8 | 18 | 0.2291 | 0.0674 | 0.2363 | 0.969 | near noise floor |

This is the desired shape: smooth stochastic modes remain near the irreducible
noise floor, while CBR exposes a real model limitation near the critical wall.

## A8-4  Local sigma is mandatory

For `cbr|6|13`, local sigma is not remotely homogeneous:

```text
rho          0.50   0.60   0.70   0.80   0.85   0.90   0.925  0.95   0.98   1.00   1.02   1.05
sigma ms     .004   .003   .006   .005   .005   .003   .008   .009   .080   7.377  .028   .034
bias ms     +.000  +.000  -.000  +.000  +.000  +.000  +.000  +.004 +1.566 +7.331 -12.958 -.487
```

The ratio `sigma_max/sigma_min` across all fitted links is `2525x`
(`cbr|6|13`). A single pooled SD is therefore misleading: it is far too wide in
the flat region and far too narrow around the critical wall. Phase 21R must use
normalized conformal scores:

```text
s_i  = |y_i - f(x_i)| / sigma(x_i)
band = f(x) +/- q_hat * sigma(x)
```

## A8-5  Sentinel out-of-sample check

The 23 block-E sentinels are excluded from the fit. They all use
`h2|6|13|rho=0.90|seed=999`, which is not one of the training seeds
`{11, 12, 13, 14, 15}`.

```text
model prediction     11.0411 ms
sentinel mean        10.8749 ms
sentinel sd           0.0122 ms
diff                 -0.1662 ms
local sigma(rho=.9)   0.2824 ms
z                    -0.59
gate                  PASS
```

This is the cleanest direct out-of-sample check in Phase L.

## A8-6  Revised gates

```text
G-L7c:
    efficiency_max < 0.9999
    band decomposition fields are present
    sigma(rho) and bias(rho) are printed in the report, not only exported

G-L7f:
    block-E sentinel OOS check passes when |diff| < 2 * sigma(rho)
```

The revised L.7 fit passes all gates:

```text
G-L7a predictive       10/10 PASS
G-L7b monotone         10/10 PASS
G-L7c efficiency       PASS
G-L7d sigma exported   PASS
G-L7e rho=1.05 marked  PASS
G-L7f sentinel OOS     PASS
```

## A8-7  Lesson for the paper

A perfect number is a warning sign, not a victory. Interpolators have zero
in-sample model error by construction, so residual bands intended for conformal
prediction must be calibrated out of sample.
