# G-A013 variance-aware multi-lag dry-run results

Date: 2026-09-01 UTC. Verdict: **PASS 13/13**. Status:
`SYNTHETIC_NO_NETWORK`. No emitter, Mininet, OVS, or RAW network run was
started.

Source commit: `689751ae4590e5ced5f0cc0e52776e0ad8f8a002`.

## Reduction and uncertainty audit

`DRY-T-Q` gates the per-link median of 16 replicates. It does not gate one
realization. The v4 artifact now records sample SD and the approximate
`SE(median)=1.253314*SD/sqrt(16)` for every legacy and corrected estimator.

| link | two-lag median | two-lag SD | two-lag SE(median) |
|---|---:|---:|---:|
| uA | 27.975 | 3.649 | 1.143 |
| ad | 31.672 | 5.332 | 1.671 |
| bc | 29.483 | 6.143 | 1.925 |
| vD | 30.288 | 2.143 | .671 |

The executed `ad=31.672 s` is therefore a median with `SE≈1.671 s`, not an
assertion of residual +5.6% population bias. Its exact-moment corrected control
remains 30.000 s.

## Multi-lag result

`DRY-T-M` requires all 16 replicates to remain in the physical domain on every
link and maximum relative median bias `<=.15`. Observed minimum validity was
16/16 and maximum bias was `.077073`: **PASS**.

| link | multi-lag median | multi-lag SD | SE(median) | SD / two-lag SD |
|---|---:|---:|---:|---:|
| uA | 27.688 | 3.705 | 1.161 | 1.015 |
| uB | 28.731 | 3.312 | 1.038 | .942 |
| ac | 29.337 | 2.422 | .759 | .750 |
| ad | 30.840 | 4.250 | 1.332 | .797 |
| bc | 30.682 | 5.005 | 1.568 | .815 |
| bd | 28.833 | 3.741 | 1.172 | .777 |
| vC | 28.181 | 1.765 | .553 | .861 |
| vD | 30.541 | 2.180 | .683 | 1.017 |

Multi-lag recovers substantial precision on the difficult low-capacity links,
including a 20.3% SD reduction on ad. It is slightly noisier on uA and vD, so
no universal variance-dominance claim is made.

## Artifact and verification

    results/SMOKE/phase-G/g3_dryrun_a013.json
    sha256 dc18a722693993c7d658fdbb94550448fe8dbec23ce9a3f34e0c14cd87e00e18

Runtime was 24.73 s and maximum RSS was 77,632 KiB. Every earlier G-A011/A012
gate remained PASS. This closes the statistical prerequisite for writing the
real-time emitter; it does not authorize Mininet before the emitter dry-run.
