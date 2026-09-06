# G′.5 — estimand transfer, preregistration

Status: SYNTHETIC STUDY, frozen before running the new generator.
Tag `phase-G2-g5-prereg`. No network runs. G4 measurements and the external
review have been seen. New null reanalysis is post hoc, not new acquisition.

## 1. Protected estimand and notation

Do not edit cert/simultaneous_score.py, cert/margin_score.py or the 23 Phase22
golden tests. Use their actual interfaces, including alpha_each for
qhat_per_slot. In this repo INCIDENCE is (8 links,4 paths), so row-wise link
errors map as eps_link @ INCIDENCE, not @ INCIDENCE.T.

Use kappa_nugget=2 for residual variance and kappa_time=5 for the still-signed
doc42 time-scale ratio. Phase22 also has a third kappa, the acceptance
multiplier: call it kappa_accept=1. New code uses explicit names through a
compatibility module; historical hash-referenced G4 code/JSON and doc42 are
not rewritten merely to rename symbols.

The requested qhat_per_slot(alpha_each=.10) is qhat_uncorrected, explicitly
a negative control in Phase22, not its max-score family certificate. Primary
T/NC gates test this requested rank-slot diagnostic. Report uncorrected,
Bonferroni, Sidak and maxscore together. A diagnostic PASS alone cannot retire
kappa_time for the production guarantee. Adoption additionally requires the
maxscore simultaneous-coverage amplitude to meet the same T-1=.020 and its
NC-1 to pass; otherwise report TRANSFER_FAILS_RUNTIME / no adoption.
This extra interpretation guard is fixed BEFORE running, not after results.

## 2. Input generator and finite budget

- Omega = [0,.25,.5,.75,1]; alpha=.10; four actions, three rank slots.
- Primary: dt=.1 s, tau=3 s (one scale), sigma_ref=.028 at uA;
  a0 and covariance from tools.g2_topology, no clipping in this synthetic
  error model. This is a model of twin error, not a physical packet run.
- Generate stationary Gaussian AR(1) link signal with covariance exactly
  design_covariance(a0,omega); initial state from its stationary distribution.
  Independent conserving nugget from uniform frame remainders:
  eps_noise=-(w[k]-w[k-1])*8/(C*dt), w~Uniform(0,1442).
  Noise variance from fixed kappa_nugget=2 certificate, no fitted sf.
- y_true ~ Uniform(10,110) cost_ms per action, independent of errors;
  y_hat=y_true + 100*eps_path. The conversion 100 ms/unit rho fixes the
  error-to-cost scale BEFORE outcomes. Ranking sees y_hat only.
- 200 independent replicate pairs. Calibration and test each 600 s (6000
  windows), generated with independent streams. Common random numbers across
  omega within each replicate/control. No same-trace calibration/testing.
- Frozen base seed 20260907. Dependence reduces effective information: the
  requested qhat function uses n_rows by default. Results are empirical
  synthetic coverage, not an exchangeability theorem for AR(1) data.
- NC-2: only uA/uB have signal AND nugget; use their covariance principal
  submatrix, zero all other links, then map through the same incidence and
  score/calibration pipeline. Submatrix is omega invariant, so reuse identical
  innovations. Do not change the scoring code or choose another subset.
- NC-3: simultaneous(0) minus product of achieved slot marginals, signed and
  absolute, plus mean score correlations. This dependence includes shared
  physical paths and ranking as well as shared e(a1), not a causal isolation
  of the common reference term.

## 3. Frozen gates and reporting

Aggregate each coverage over 200 replicates. Amplitude=max(mean)-min(mean);
T-2 divides by sqrt(mean across omega of per-replicate variances), not by SE.
T-3=min adjacent increase. NC-1=max across omega AND three slots of absolute
mean marginal difference from omega=0. Report MC SE and replicate data.

| Gate | Threshold |
|---|---|
| T-1, uncorrected slot joint amplitude | >=.020 |
| T-2, amplitude / single-trace SD | >=3 |
| T-3, worst adjacent increase | >=-.002 |
| NC-1, marginal drift | <=.005 |
| NC-2, uA/uB slot-joint amplitude | <=.005 |
| NC-3, dependence anchor at omega=0 | report only |
| R-1, MA1 versus white link-coverage amplitude | report only |
| R-2, link coverage at certificate sf | report only |

NC failure => STOP_GENERATOR (diagnose once; no threshold change).
T-1 failure => TRANSFER_FAILS for this finite synthetic design, not proof of
global invariance. T-1 PASS but T-2/T-3 failure => ADOPT_WEAK_DIAGNOSTIC only.
All diagnostic gates PASS => ADOPT_DIAGNOSTIC; runtime guard in section 1
must also pass before any separate retirement amendment. If it fails, doc42
stands. A G3a omega-recovery error .0271 is NOT a coverage-change bound and
must never be used to claim invariant Phase22 coverage.

Predictions supplied by review, retained rather than guaranteed:
slot amplitude .02–.09, NC-1/2 <.002, NC-3 .02–.10, link amplitude .13–.15.
Do not extend runs, change sigma/cost scale, choose K, or add favourable
generators after seeing outcomes. Report all four procedures regardless.

## 4. Recompute doc47, paired factorial comparison

Separate CLI --recompute-doc47, no historical edits. Reuse doc47's coverage
function, which fits sd to its own trace; do not confuse it with split-conformal
coverage. 200 replicates, 600s, tau3, same omega grid. Two dt values:
historical .2 and certified .1. For each dt cross noise family {white Gaussian,
Gaussian MA1, uniform-remainder MA1} with amplitude {sf=.85, certified formula
at sigma_ref=.028}. Hold marginal nugget variance fixed when comparing colour.
For sf=.85 use population signal variance*(1/.85-1), not random sample sd;
record this distinction from historical tool. dt=.2/formula is extrapolation,
not empirically validated by G4. Store K=2 and K=8 coverage and marginal.

## 5. G4 null addendum and forward-only Q-1 replacement

Do not overwrite certificate v2. Emit a hashed sidecar with MA1 Bartlett
Var(r) approximately 1.5/n, every per-run and pooled-cell standardized value,
two-sided normal p values, Bonferroni global control (.05) over 364 individual
run/pair tests, and separately 168 pooled pair/cell tests. Dependence among
pairs does not invalidate Bonferroni, but normal approximation remains an
assumption. Report iid-normal E[max abs Z] as a reference only; it is NOT a
test cutoff. max/SD also grows with the number of comparisons. No observation
below E[max] implies neither independence nor zero contamination.

G4 input datasets both have omega=0; no claim of validated omega=.5 here.
Kappa dataset differences are descriptive, not established by treating
IQR of link/cell aggregates as SE of independent runs. Report exact sf impact
and full per-run distribution, no fitting/correction.

Forward model-feasibility proxy: replace 4.36 with
sqrt(2*.8264/(1-.8264))≈3.086, preserving claim C tolerance .10. This replaces
the historical sf=.95 proxy for future theoretical design only; does not
certify unmeasured low-sigma operation, amended tau estimation, or remove
clipping, timing, n_eff, burst and infrastructure constraints. Report per-link
and reference-sigma boundaries and retain every historical Q-1 verdict.

## 6. DOI and deliverables

No Zenodo connection/token currently configured. Prepare a local reservation
request and preserve DOI=null until a real response/user record arrives.
Record reserved DOI separately from public archival status; a draft is not a
published immutable dataset. It cannot alone clear the public archival gate.
Deliver tools/g5_estimand_transfer.py, tests, protected-source hashes,
results JSON/CSV/figure, docs/phase-G/70-g5-results.md and any warranted
append-only decision. New data/results refuse overwrite.
