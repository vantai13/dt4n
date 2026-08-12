# Phase 21R -- Figure And Table Plan

Ngay lap: 2026-08-12

This file lists the paper-facing figures and tables for Section 5. It does not
create new measurements; it maps existing artifacts to the story.

## Figures

### F1. Error Decomposition By Age

Source: Lesson 21R.3, `results/phase-21R/decomposition_poisson_0.925.json`.

Plot:

```text
x-axis: z_s, log scale, 0.005 to 0.550
y-axis: RMS on cost-margin scale, ms
lines : rms_e_model, rms_e_stale, rms_total
marks : z_cross=0.007085 s, d_sync=0.051 s
```

Message: staleness dominates model error over the entire physically reachable
AoI range.

### F2. Marginal Vs Mondrian Coverage

Source: Lesson 21R.4/21R.5, `results/phase-21R/error_vs_age_poisson_0.925.json`
and `results/phase-21R/conformal_poisson_0.925.json`.

Plot:

```text
bars: per-bin coverage under one marginal q_hat
horizontal line: 0.90
```

Message: marginal coverage can be correct while the oldest bin is undercovered.
This is the Phase 20R "average hides risk" lesson lifted to conformal scores.

### F3. q_hat By Age Bin With RMS Bridge

Source: Lesson 21R.5, `results/phase-21R/conformal_poisson_0.925.json`.

Plot:

```text
bars: q_hat = 11.59 / 15.63 / 19.65 / 24.32 ms
overlay: 1.645 * rms
```

Message: the conformal thresholds are explainable from the decomposition:
`q_hat ~= 1.645 * rms`, within about 2%.

### F4. Risk-Acceptance Frontier

Source: Lesson 21R.6, `results/phase-21R/usefulness_poisson_0.925.json`.

Plot:

```text
x-axis: acceptance rate
y-axis: err|accept
curve : kappa sweep
marks : kappa=0.5, 1.0, 2.0
reference: v7 point and anchor error
```

Message: the 21R gate accepts far more decisions than v7 at comparable risk.

### F5. Gate Discrimination

Source: Lesson 21R.6, `results/phase-21R/usefulness_poisson_0.925.json`.

Plot:

```text
x-axis: kappa
y-axis: error rate
lines : err|accept and err|reject
```

Message: rejected rows are much riskier than accepted rows; at `kappa=1`, the
reject/accept error ratio is about `9.01x`.

### F6. Iso-quality Frontier

Source: Lesson 21R.7, `results/phase-21R/freshness_poisson_0.925.json`.

Plot:

```text
x-axis: synchronization frequency, log scale
y-axis: acceptance rate at err|accept=1%
labels: kappa_star
mark  : knee at 10.2 Hz
```

Message: the first 5x synchronization increase buys about twice the acceptance
gain of the following 12x increase.

### F7. q_hat Age-shape Invariance

Source: Lesson 21R.8, `results/phase-21R/operational_sigma.json`.

Plot:

```text
x-axis: q_hat(B0), log scale, 1.01 to 81.46 ms
y-axis: q_hat(B3) / q_hat(B0)
line  : mean ratio 2.1766
```

Message: q_hat scale depends heavily on traffic regime, while age-shape is
nearly invariant on synthetic AR(1), tau=1.0.

## Tables

### T1. Gate Table

Source: [99-gate-decision.md](99-gate-decision.md).

Contents: G1-G12, threshold, measured value, status, source lesson.

### T2. Prediction Scorecard

Source: `results/phase-21R/prediction_scorecard.json`.

Contents: preregistered numeric interval, observed value, hit/miss, root cause.

### T3. Operational Sigma Robustness

Source: `results/phase-21R/operational_sigma.json`.

Contents: 10 cells, sigma, anchor, coverage, q_hat ratio, acceptance/risk at
`kappa=1`, H7 status.

### T4. Threats To Validity

Source: [99-gate-decision.md](99-gate-decision.md).

Contents: L1-L10 with scope and planned resolution.

## Section 5 Story Order

```text
1. F1: why age matters physically
2. F2: why marginal conformal is not enough
3. F3: why q_hat is explainable
4. F4/F5: why the gate is useful
5. F6: how to turn quality targets into system requirements
6. F7/T3: why conclusions survive operational sigma
7. T1/T2/T4: gate decision, preregistered self-audit, limits
```
