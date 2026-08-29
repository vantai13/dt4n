# Offered-ledger nugget check — result

Run date: 2026-08-29 UTC.  The first computation followed tag
`phase-G-offered-nugget-check-prereg` at commit `66465da2`.

## Verdict

**Result A: offered sf is at the no-detected-nugget boundary on all eight
links.**  G-A003 may proceed without rewriting H6 around a generator-side fast
component.

| Link | Class | sf offered | v estimate | sigma estimate | tau fit (s) | Boundary band |
|---|---|---:|---:|---:|---:|:---:|
| uA | edge | 1.0031 | -2.509e-06 | 0.02840 | 26.777 | IN |
| uB | edge | 1.0019 | -1.333e-06 | 0.02631 | 33.867 | IN |
| ac | core | 1.0327 | -3.589e-04 | 0.10651 | 3.869 | IN |
| ad | core | 1.0153 | -1.673e-04 | 0.10522 | 6.608 | IN |
| bc | core | 1.0421 | -4.203e-04 | 0.10204 | 3.278 | IN |
| bd | core | 1.0324 | -3.181e-04 | 0.10070 | 3.759 | IN |
| vC | edge | 1.0031 | -2.767e-06 | 0.02982 | 29.985 | IN |
| vD | edge | 1.0020 | -1.426e-06 | 0.02677 | 33.434 | IN |

- Edge sf median: `1.00256`, range `1.00193–1.00312`.
- Core sf median: `1.03253`, range `1.01535–1.04207`.
- Locked boundary band: `abs(sf_hat-1)<=0.05`; all 8/8 links are inside.
- No edge generator fast component was detected at the 0.20-second scale.

Negative `v` values are the unconstrained estimator's boundary fluctuation
when `sf_hat>1`; they are not physical negative variances and are not clamped.
The key contrast is that offered edge sf is approximately one while measured
edge sf in the same run was approximately 0.85–0.90.  This localizes the
detected nugget after the offered ledger, consistent with a measurement-path
origin.  It supports but does not independently confirm a specific telemetry
mechanism.

## Artifact

- Path: `results/SMOKE/phase-G/g1_offered_nugget_check.json`.
- SHA256: `4b5344b470779463ba49d6676a9849427c430c9fbb2370b608844d1ea0bdeac4`.
- Elapsed: `0:03.88`; maximum RSS: `135,900 KiB`.
- No Mininet and no new RAW data.

The next authorized design step is G-A003: synthetic validation of the reduced
boundary model, power gating, and a preregistered split-sample test.  It has not
been started in this result.
