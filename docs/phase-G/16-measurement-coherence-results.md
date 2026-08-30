# Measurement-path coherence result — no W* on the signed grid

Run date: 2026-08-30 UTC. This is a post-hoc diagnostic after the locked
G-A004 FAIL; it cannot change that verdict. The design and executable were
frozen at `phase-G-coherence-threshold-prereg` (`c4e5fb1f`). The 400-replicate
stationary-null artifact was then frozen at
`phase-G-coherence-threshold-locked` (`7d2b18bb`) before the physical curve
was read.

## Signed curve and verdict

Each cell is `CV(v_projected) / stationary-null p95`. A FAIL means the
physical across-window variation is larger than the pointwise threshold
locked for that link and W.

| link | 50 s | 100 s | 200 s | 400 s | 750 s | 1505 s |
|---|---:|---:|---:|---:|---:|---:|
| uA | 6.445 / 0.145 FAIL | 4.493 / 0.105 FAIL | 3.157 / 0.078 FAIL | 2.167 / 0.056 FAIL | 1.619 / 0.041 FAIL | N/A |
| uB | 0.530 / 0.136 FAIL | 3.644 / 0.097 FAIL | 2.547 / 0.072 FAIL | 1.780 / 0.055 FAIL | 1.313 / 0.039 FAIL | N/A |
| vC | 0.363 / 0.144 FAIL | 4.355 / 0.101 FAIL | 3.078 / 0.076 FAIL | 2.144 / 0.058 FAIL | 1.598 / 0.042 FAIL | N/A |
| vD | 0.168 / 0.136 FAIL | 3.876 / 0.098 FAIL | 2.736 / 0.072 FAIL | 1.928 / 0.053 FAIL | 1.426 / 0.038 FAIL | N/A |

```text
identifiable W                 = 50, 100, 200, 400, 750 s
all-link PASS at each W       = false, false, false, false, false
W* largest all-link PASS      = NONE ON THE SIGNED GRID
W=1505 s                      = NOT_IDENTIFIABLE_ONE_WINDOW
```

This result does not estimate a positive W* and must not be rewritten as a
numerical claim such as `W*<50 s`: the signed grid has no point below 50 s.
It says only that no all-link coherence window was found among the
identifiable candidates.

## Fit availability and boundary audit

At 50 s, 60 physical windows were attempted. Fits were available for
uA/uB/vC/vD in 60/58/59/59 windows. The missing fits are disclosed rather
than imputed. All available-window curves still exceeded their thresholds.
The projected-boundary fraction was 1/60 for uA at 50 s and zero for every
other reported link/W. At 100/200/400/750 s all local fits were available.

The endpoint localization is descriptive, not a second signed test. For
W=100--750 s, the largest local-v window is at the end of the run for both
source links (uA/uB), and at the beginning for both destination links
(vC/vD). This is consistent with the earlier stale-calibration/opposite-drift
diagnosis, but the same post-G-A004 data and estimator are involved, so it
does not prove that estimator defect is impossible.

As a separate post-hoc sensitivity check, keeping the held-out observations
and first-half phi fixed gives the following uA-uB re-solves:

| sf source | sf uA | sf uB | r true hat | absolute error |
|---|---:|---:|---:|---:|
| first half, used by G-A004 | 0.9763 | 0.9366 | 0.2232 | 0.1091 |
| full run | 0.8694 | 0.8568 | 0.1580 | 0.0439 |
| inferred second half | 0.7809 | 0.7731 | 0.0876 | 0.0265 |

The last row uses `v2=2*v_full-v1` and holds full-run signal variance fixed
when converting v2 to sf. It is therefore a sensitivity calculation, not an
independent estimate; signal-variance stationarity is an explicit unverified
assumption. The result demonstrates strong sensitivity to stale sf, while the
signed G-A004 combination remains FAIL.

## Consequence for G-A005

G-A005 is not signed or run here. Its proposed 750 s within-window
certification cannot pass the newly measured all-link coherence requirement.
A follow-up must first preregister either a shorter grid below 50 s with an
estimator-reliability gate, or collect fresh data under a stabilized
measurement path. The burned G-A004 second half remains burned.

## Reproduction and files

```bash
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python \
  tools/g_measurement_coherence.py --stage threshold
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python \
  tools/g_measurement_coherence.py --stage measure
```

- Signed design: `docs/phase-G/15-prereg-measurement-coherence.md`
- Stationary-null thresholds: `results/SMOKE/phase-G/g_coherence_thresholds.json`
- Physical CV curve and W* verdict:
  `results/SMOKE/phase-G/g_measurement_coherence.json`
- Executable: `tools/g_measurement_coherence.py`

Observed runtimes on the recorded host were 19.65 s for threshold calibration
and 0.32 s for physical measurement. The threshold artifact records
`physical_curve_read=false` and the physical result pins its SHA-256 as
`3344e5e6a21888b0122a7c29f9c579e22fae63101890d67eda6c7f0030127e31`.
