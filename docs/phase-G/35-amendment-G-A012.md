# G-A012 — persistent-rounding covariance at every estimator lag

Signed: 2026-09-01 UTC, after G-A011 and before execution of the amended v3
artifact. Status: `SYNTHETIC_NO_NETWORK`.

This is a forensic amendment, not a blind preregistration. G-A011 supplied the
closed-form lag-one ACF of independent-window rounding. Inspection then showed
that the same covariance persists at lags two and three used by the G.1
closed-form estimator. The G.1 variance certificate is not withdrawn: the
rounding variance remains `1/12` packet squared. The persistence estimator is
amended.

## Global lag formula

For an AR(1) target with stationary SD `sigma_packets` in packet quanta and
persistence `phi`, the lag-k increment has SD

    step_k = sigma_packets * sqrt(2*(1-phi**k)).

Substitution into the G-A011 sawtooth series gives

    c_k(phi) = (6/pi^2) * sum_{j>=1}
               exp(-2*pi^2*j^2*step_k^2) / j^2.

Thus independent-window rounding is not generally clean at lag two or three.
`tools/g1_quant_model.py` owns this extension as
`acf_predicted_mechanism_a_lag`.

## Estimator correction

For observed total variance `T`, known packet variance `v_pack`, and observed
autocorrelations `a_k`,

    T*a_k = sigma_signal^2*phi^k + v_pack*c_k(phi).

Using lags two and three eliminates the unknown signal variance:

    phi <- (T*a_3 - v_pack*c_3(phi))
           / (T*a_2 - v_pack*c_2(phi)).

The legacy `a_3/a_2` value seeds a fixed-point iteration. An invalid seed,
non-positive denominator, or iterate outside `(0,1)` is refused as NaN; no
physical boundary is manufactured by clipping. The implementation is
`solve_phi_nugget_corrected`.

The current repository estimator actually identifies phi with lags one and
two (`a_2/a_1`), while the supplied issue description assumed lags two and
three. Both legacy variants are therefore retained as diagnostics in the
amended stress artifact. The corrected estimator uses lags two and three after
analytic nugget subtraction.

## Pre-amendment diagnostic

A separate 32-replicate diagnostic used seed `20260907`, `n=30000`,
`sigma_ref(uA)=0.020232558139534878`, and `tau=30 s` before the formal v3 run.

| link | repo lag 1--2 | uncorrected lag 2--3 | corrected lag 2--3 |
|---|---:|---:|---:|
| uA | 26.359 s (-12.1%) | 28.577 s (-4.7%) | 28.917 s (-3.6%) |
| ad | 20.644 s (-31.2%) | 25.106 s (-16.3%) | 28.589 s (-4.7%) |

Finite-sample ratio bias means corrected Monte Carlo medians are not claimed to
be exactly 30 s. At exact population moments, the corrected fixed point returns
the design phi to numerical precision.

## Amended dry-run gate

The existing dangerous cell, seed and 16-replicate reduction are preserved.
For every link the artifact records:

- median total ACF at lags one through three;
- median tau from the repository lag-1--2 estimator;
- median tau from uncorrected lag 2--3;
- median tau from corrected lag 2--3;
- all three estimators evaluated at exact population moments.

`DRY-T-Q` requires maximum corrected median relative tau bias across links to
remain within the already signed PC-G2-3 budget of 0.15. The two legacy
estimates are reported evidence, not gates selected from their observed error.

The output is append-only:

    results/SMOKE/phase-G/g3_dryrun_a012.json

No emitter or Mininet execution is authorized by a failing amended dry-run.

## Lesson and provenance identifiers

**G-L79:** repairing a noise model at one lag is a global estimator event. All
lags consumed by downstream estimators must be re-audited.

The supplied note named this G-L78, but G-A011 already assigned G-L78 to static
decision margin. Identifiers remain append-only.

**G-L80:** preregistration evidence lives in remote tags, not merely commits.
After G-A012 closes, all Phase-G prereg/result tags must be pushed and verified
with `git ls-remote --tags origin`; successful default commit push output is
insufficient evidence of tag custody.
