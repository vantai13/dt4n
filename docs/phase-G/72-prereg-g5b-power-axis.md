# G′.5b — can the power channel carry omega without kappa_time? Preregistration

Status: SYNTHETIC STUDY, frozen before running the new tool. No network runs.
Tag `phase-G2-g5b-prereg`. G5 results and the external review have been seen,
so this is a preregistration of a RETEST, not of a first look.

## 1. Why a retest, and what makes it a retest

Doc 70 section 4 observed, **descriptively and outside its signed gate table**,
that omega inflates qhat by 32.2 percent and costs 18.9 percent of accepted
windows at a single time scale. That observation generated the hypothesis that
omega can be a power axis. It cannot also test it: it has spent its degrees of
freedom, exactly the failure `P-7` (doc 64) and `RT-O1` (doc 66a) recorded.

Therefore:

- **Fresh seed 20260908.** No reuse of the G5 seed 20260907 or its streams.
- **One time scale.** tau_p = tau_g = 3 s throughout. kappa_time is absent from
  the generator, because whether one scale suffices is the question.
- **Protected sources untouched.** cert/simultaneous_score.py,
  cert/margin_score.py and the 23 golden tests are verified against
  `git show phase-G2-g5b-prereg:<path>` before and after execution, as in G5.

A PASS here does not by itself retire kappa_time. It establishes that the
axis survives on power at one scale; the retirement amendment is separate and
must also state what doc 42's PC regime was buying that is now unbought.

## 2. What is actually being decomposed

Doc 70a established that omega reaches the rank-slot estimand through two
channels, and that both are absorbed at the coverage level:

- scale: qhat inflates by c = 1.31309, per-slot spread 2.21 percent; conformal
  is exactly scale-equivariant, verified bit-identical at c in {1.3131, 2, 7.5}.
- ranking: 47.3 percent of rows change twin order at omega = 1, jumping to
  44.5 percent already at omega = 0.25; absorbed by rank-slot exchangeability.

Power is where they need not cancel. Acceptance is
`all_j(m_hat_j >= kappa_accept * qhat_j)`, and omega moves BOTH sides: qhat
through the scale channel, and the twin margins `m_hat` through the ranking
channel. The decomposition below separates them.

| symbol | definition |
|---|---|
| `A(w)` | acceptance at omega = w |
| `c(w)` | measured mean per-slot qhat ratio, omega = w versus omega = 0 |
| `A_scale(w)` | acceptance with `qhat = c(w) * qhat(0)` and `m_hat` from omega = 0 |
| `A_scale(w) - A(0)` | the part of the power loss explained by qhat inflation alone |
| `A(w) - A_scale(w)` | the part NOT explained by scale: the irreducible remainder |

**The surrogate multiplies the SCORE MATRIX, never the twin error.** Doc 70a
section 4 measured why: scaling the twin error re-ranks 9.1 percent of rows at
c = 1.3131 and 77.7 percent at c = 7.5, and drives qhat/qhat0 to 8.081 when c
is 7.5. A twin-error surrogate mixes both channels and cannot answer the
question. This correction is fixed here, BEFORE running.

## 3. Generator and finite budget

- omega grid [0, .25, .5, .75, 1]; alpha = .10; four actions, three rank slots.
- dt = 0.1 s, tau = 3 s, sigma_ref = 0.028 at uA, a0 and covariance from
  tools.g2_topology, certified fixed nugget kappa_nugget = 2, no fitted sf.
- Reuse `tools.g5_estimand_transfer.measured_errors` and `make_inputs` with the
  new seed, so the error model is the one G5 already published, not a new one.
- 200 replicates; calibration and test 600 s each from independent streams;
  common random numbers across omega within a replicate.
- Primary procedure is **max-score**, the Phase 22 certificate. Report the
  uncorrected control alongside, as in G5, but gate on max-score only: doc 70
  showed the uncorrected slot procedure is `PC22-2`, a negative control.
- NC-2 subset is `{uA, uB}` with the same masking G5 used, whose K_TOPO entry
  is 0 and whose coupling sum is 0, so the effect must vanish there.

## 4. Frozen gates

Aggregate over 200 replicates. Amplitude = max(mean) - min(mean).
P-2 divides by sqrt(mean over omega of per-replicate variances), not by SE.

| gate | quantity | threshold |
|---|---|---|
| `P-1` | acceptance amplitude over omega, max-score | >= 0.050 |
| `P-2` | amplitude / single-trace SD | >= 5.0 |
| `P-3` | worst adjacent step in acceptance, must be non-increasing | >= -0.005 |
| `P-4` | `\|A(1) - A_scale(1)\|`, irreducible remainder | **REPORT** |
| `P-5` | fraction of rows re-ranked versus omega = 0 | **REPORT** |
| `NC-1` | max-score simultaneous coverage amplitude | <= 0.005 |
| `NC-2` | acceptance amplitude on `{uA, uB}` | <= 0.010 |
| `NC-3` | per-slot scale heterogeneity, spread/mean | **REPORT** |
| `S-1` | qhat inflation versus the scale-channel prediction | **REPORT** |

`P-4` is diagnostic and is NOT gated, for the same reason `NC-3` was not gated
in G5: gating it would reward a design that makes omega look irreducible.

NC failure => `STOP_GENERATOR`, diagnose once, no threshold change.
P-1 failure => `POWER_TOO_WEAK`; omega leaves the regime label and is reported
as a measured invariance with the doc 70 section 7.4 bound of 0.0055.
P-1 PASS, P-2/P-3 failure => `ADOPT_WEAK`, no retirement amendment.
P-1/P-2/P-3 PASS => `POWER_AXIS_HOLDS`, and P-4 then classifies it:
small remainder => `REDUCIBLE_TO_EFFECTIVE_SIGMA`, large => `IRREDUCIBLE`.

Both classifications are usable outcomes. `REDUCIBLE` means the axis collapses
into an effective sigma and the campaign drops a dimension; `IRREDUCIBLE` means
it earns its place. Neither is a failure and the tool must not prefer either.

## 5. Signed predictions, entered before running

```
P-1  acceptance amplitude   0.07 - 0.13    (doc 70 section 4 saw 0.102, new seed)
P-2  SNR                    > 10
P-3  worst step             >= -0.003
P-4  |A(1) - A_scale(1)|    0.00 - 0.03    (scale channel expected to dominate)
P-5  rows re-ranked         0.44 - 0.48    (doc 70a measured 0.473 at omega=1)
NC-1 coverage amplitude     < 0.003
NC-2 amplitude on {uA,uB}   < 0.005
NC-3 scale heterogeneity    1.5% - 3.5%    (doc 70a measured 2.21%)
S-1  qhat inflation         30% - 34%      (doc 70a predicted 31.31, G5 saw 32.17)
```

## 6. Run-length arithmetic this feeds, and what it is not

Doc 42 fixes `T = 200 * max(tau_p, tau_g)` and the PC regime
`(tau_p, tau_g) = (15, 3) s, kappa_time = 5, T = 3000 s`, against the
one-scale `(3, 3) s, T = 600 s`. Retiring kappa_time therefore divides the
per-cell run length by 5 at tau_g = 3 s. The campaign total depends on the
G'.6 grid, which is not yet fixed, so no total hours are signed here; the
factor of 5 is the only claim, and it is doc 42's own arithmetic, not new.

This preregistration does not authorise changing `T = 200 * max(tau_p, tau_g)`,
the alignment gates, the omega round-trip gates, or any G3a/G3b/G4 verdict.
It authorises one synthetic study and, conditional on its result, a separate
amendment that must be written and signed on its own.

## 7. Deliverables

`tools/g5b_power_axis.py`, tests, protected-source hashes, results JSON and
CSV, `docs/phase-G/73-g5b-results.md`, and an amendment only if gates pass.
New artifacts refuse overwrite via `tools.artifact_guard`.
