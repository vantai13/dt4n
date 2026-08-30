# G-A005 — reclassification of G-A004, not a rescue

Date: 2026-08-30 UTC. This amendment is post-hoc and reads already-burned
G-A004 outcomes. It changes no threshold and does not reopen either split.

## Reclassified scope

The numeric G-A004 verdict remains `FAIL`: uA-uB error was 0.10907 against
the signed 0.10 gate, only 5/6 pairs passed, and `G1_closed=false` remains.
The failure still rejects certification of the deployed
calibration-plus-two-band pipeline.

What changes is the component-level interpretation. G-A004 cannot identify
whether the failure came from the two-band algebra, nuisance estimation,
nuisance transfer/nonstationarity, or model misspecification. Its power stage
generated data using fixed `sf,phi` and supplied those exact values directly
to `estimate_two_band`; the physical stage estimated them on the first half
and transferred them to the second. These are not the same end-to-end
estimator. Therefore the claim “G-A004 proves the two-band component is
defective” is withdrawn; the broader pipeline FAIL is not withdrawn.

## Post-hoc sensitivity

Using the exact held-out trace and keeping first-half phi fixed:

| sf source | sf uA | sf uB | r true hat | absolute error | cond(A) |
|---|---:|---:|---:|---:|---:|
| first half used by G-A004 | 0.9763 | 0.9366 | 0.2232 | 0.1091 FAIL | 1.360 |
| full run | 0.8694 | 0.8568 | 0.1580 | 0.0439 PASS | 1.260 |
| inferred second half | 0.7809 | 0.7731 | 0.0876 | 0.0265 PASS | 1.443 |

The last row assumes `v2=2*v_full-v1` and unchanged full-run signal variance;
it is a sensitivity check, not an independent estimate. Exact condition
numbers and numerical derivatives are retained in the machine artifact.
The exercise shows that `cond(A)` can remain small while nuisance error moves
the answer across the decision gate: conditioning is conditional on supplied
`sf`, not a reliability assessment of `sf`.

## New limits, without identifier reuse

The input instruction proposed G-L27--G-L30 and NT56, but those identifiers
already have committed meanings. This amendment allocates G-L31--G-L34 and
NT59 instead.

- G-L31: `sf>1` with `v<0` is outside the estimator's physical model domain.
  It is a model-class warning, not a value to clamp. The present post-hoc data
  do not by themselves identify the source of misspecification.
- G-L32: the signed coherence diagnostic rejected fixed-configuration
  stationarity at all identifiable W=50--750 s. Calibrate-then-transfer is not
  certified on this run.
- G-L33: `cond(A)<=10` checks the two-by-two solve conditional on nuisance
  inputs; it does not check nuisance accuracy or transferability.
- G-L34: H6b's “same telemetry side” grouping does not match the held-out
  pattern. A code-backed candidate H6c groups by shared transmitting switch:
  uA/uB share sSRC while vC/vD transmit on distinct switches. H6c is post-hoc
  and must not be promoted without fresh/direct-control data.
- NT59: power simulation must execute the complete deployed pipeline,
  including re-estimation of nuisance parameters. A parameter supplied free
  in simulation but estimated in deployment defines a different estimator.

## DOI boundary

The user states that data have been backed up and authorizes opening existing
outcomes. No public Version DOI was found in the repository, attachments, or
public Zenodo search; `results/DATA_MANIFEST.json::doi` therefore remains
`null`. Backup authorization permits this reclassification, but it cannot be
represented as a Zenodo DOI and does not open the new-data G.3/G.4 gates.

## Reproduction

```bash
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python \
  tools/g_a005_reclassification.py
```

Machine result:
`results/SMOKE/phase-G/g_a005_reclassification.json`.
