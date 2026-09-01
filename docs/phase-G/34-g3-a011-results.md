# G-A011 quantisation-gate dry-run results

Date: 2026-09-01 UTC. Verdict: **PASS 11/11**. Status:
`SYNTHETIC_NO_NETWORK`. No Mininet/OVS process was started and no RAW network
data was created.

Source commit: `d88e4cdbb32046eae250ff700eaf9993770db7f6`.
The original v1 dry-run artifact remains unchanged; this run implements the
append-only amendment in `33-amendment-G-A011.md`.

## Why the old gate was wrong

Before changing code, a 32-replicate diagnostic at
`sigma_ref(uA)=0.020232558139534878`, `tau=30 s`, and `n=30000` reproduced the
problem. Independent per-window rounding produced median ACF1 `.077489` on uA
and `.221612` on ad, while cumulative flooring produced approximately `-.500`.
Thus `abs(ACF1)<=.10` rejects a healthy independent-round mechanism on ad.

The amended classifier uses the invariant sign:

    ACF1 >= -0.05  -> INDEPENDENT_ROUND
    ACF1 <= -0.25  -> CUMULATIVE
    otherwise      -> INCONCLUSIVE

## Amended gate results

| id | observed | gate | verdict |
|---|---:|---:|---|
| DRY-0 | analytic max error `2.22e-16` | `<=1e-12` | PASS |
| DRY-C | component `.001483`; target `.001083` | each `<=.01` | PASS |
| DRY-Q | min cell/link median `-.009681` | `>=-.05` | PASS |
| DRY-Q-PC | max packet-step prediction error `.010558` | `<=.05` | PASS |
| DRY-Q-B | cumulative error from `-.5`: `.002883` | `<=.05` | PASS |
| DRY-W | max `abs(ACF1(eps_path))=.053573` | `<=.10` | PASS |
| DRY-R | residual-correlation max error `.002228` | `<=.06` | PASS |
| DRY-O | omega median error `.015784`; max SD `.036395` | each `<=.05` | PASS |
| DRY-T | two-exponential ACF max error `.016174` | `<=.05` | PASS |
| DRY-D-NC | flip spread `.010033` | `<=.054864` | PASS |
| DRY-D-PC | analytic flip spread `.213436` | `>=.10` | PASS |

The descriptive maximum over all individual original-design replicates remains
`.074848`; it is no longer misused as a whiteness discriminator.

## Dangerous-cell result

The formal stress run uses 16 replicates and the independent seed `20260906`.

| link | step, packets | ACF1 observed | ACF1 predicted | abs error | cumulative control |
|---|---:|---:|---:|---:|---:|
| uA | .323490 | .076285 | .077087 | .000802 | -.499038 |
| uB | .323490 | .072494 | .077087 | .004593 | -.498306 |
| ac | .228742 | .223653 | .218871 | .004782 | -.497117 |
| ad | .228742 | .216609 | .218871 | .002262 | -.500419 |
| bc | .228742 | .219060 | .218871 | .000188 | -.499479 |
| bd | .228742 | .216039 | .218871 | .002833 | -.498962 |
| vC | .323490 | .075072 | .077087 | .002015 | -.499206 |
| vD | .323490 | .074783 | .077087 | .002303 | -.498677 |

All eight independent-round traces classify `INDEPENDENT_ROUND`; all eight
cumulative controls classify `CUMULATIVE`. The largest observed/predicted error
inside the stress cell is `.004782`, about one tenth of its gate.

## Artifact and verification

    results/SMOKE/phase-G/g3_dryrun_a011.json
    sha256 9e6b5e22d14317d990487481b3ab3b8a4a6daed1fe234ca162c59623997ed58b

Runtime was 23.90 s and maximum RSS was 77,440 KiB. Focused Phase-G verification
reported `87 passed` in 1.44 s. The artifact records
`network_authorized_by_dryrun=true`; this authorizes only the next emitter
dry-run stage, not a Mininet campaign.
