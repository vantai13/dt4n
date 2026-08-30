# Preregistration — NC-G1-static direct measurement

This document is signed before the first network execution of
`scripts/g1_static_campaign.sh`. The tag is
`phase-G-g1-static-nc-prereg`.

## Scope and custody

NC-G1-static replaces the fit-based measurement-path branch as the primary
route to G.1 closure. Earlier FAIL and NON-IDENTIFYING artifacts remain intact.
The public Version DOI remains null. The user-attested offsite backup recorded
by K12 opens only local Phase G work; it is not a public archive claim and does
not authorize historical cleanup.

## Locked design

- Generator: deterministic UDP CBR with cumulative absolute-deadline pacing.
  `sigma_true=0` by construction; payload 1400 B.
- Mean-load projection: `rho_bar=0.857`; measured window 0.200 s; offered
  ledger 0.010 s; burn-in 20 s.
- Confirmatory campaign: 300 s/run, 3 reps, cells A–F below.
- TX and RX byte counters come from one `/proc/net/dev` read. The midpoint of
  the read defines the sample instant and its duration is logged.

| cell | Ditto sync | AoI probe | reconcile_every | mode |
|---|---|---|---:|---|
| A | on | on | 1 | prod, tol=0 |
| B | on | on | 30 | prod, tol=0 |
| C | on | off | 1 | prod, tol=0 |
| D | off | off | 30 | none |
| E | off | on | 1 | probe-only prod metadata |
| F | on | off | 30 | prod, tol=0 |

The supplied lesson draft used `clean` for all Ditto cells. Repo audit before
data generation found that `bridge.sync_agent.run` forces
`reconcile_every=1` in clean mode, which would make the stated 1-vs-30 factor
false. This preregistration therefore locks `prod,tol=0`: reconcile=1 remains
a full push every cycle, while reconcile=30 remains an actual contrast.

## Locked validity gates

All gates distinguish instrument validity from outcomes.

- G1S-0: every run metadata record has `engine == "static"`.
- G1S-1: every link has
  `Var(rho_offered@0.2s) / Var(rho_measured) <= 0.10`.
- G1S-2: every link has
  `abs((Var(diff(rho))/2)/Var(rho) - 1) <= 0.25`.
- G1S-3: each run has CPU p95 <80%, zero host network drops, zero swap,
  packet shortfall <=0.01, maximum emitter lag <=0.05 s, and zero send errors.
- G1S-4: the preregistration tag is an ancestor of the git hash stored in each
  run metadata record.
- G1S-5: counter-read p95 is reported and implies relative timing error <0.005.

A cell that fails any validity gate is `INVALID`; its variance may be reported
diagnostically but is not certified as a low-noise result.

## Locked outcomes

- Direct `v(config)=Var(rho_measured)` by link.
- Direct `rho_epsilon(config)=corr(rho_l,rho_m)` for all 28 pairs, on both TX
  and RX counters; level-vs-difference agreement is also reported.
- Feasible sigma grid `{0.01,0.02,0.03,0.05,0.10}` at `sf>=0.85`.
- Drift CV at windows 25, 50, 100, and 200 s against
  `sqrt(2/(k-1))`, using the locked two-times-null descriptive bound.

`sigma=0.01` is an outcome, never a validity gate.

## Locked discriminating predictions

| hypothesis | TX prediction |
|---|---|
| H6b same telemetry side | uA-uB and vC-vD high; core sibling pairs low |
| H6c same transmitting node | uA-uB, ac-ad, bc-bd high; vC-vD low |
| H-TELEMETRY | pair correlations track the A–F telemetry settings |
| H-SAMPLER | vC-vD is low on TX but high on RX |

“High” is median >=0.50 and “low” is median <=0.25. A grouping is fully
separated only if every in-group pair exceeds every out-group pair. Mixed and
negative outcomes are admissible.

## Limits fixed before outcomes

- G-L35: the counter instant is bounded rather than exact;
  `read_duration_us` bounds residual rate error.
- G-L36: the analytic variance-CV null assumes independent samples. The
  two-times-null bound absorbs only mild residual dependence.
- NT59 already requires power simulation to execute the full deployed
  nuisance-estimation pipeline; no identifier is reused here.

The certificate expires after 30 days or any change to telemetry config,
sampling interval, topology, or generator design.
