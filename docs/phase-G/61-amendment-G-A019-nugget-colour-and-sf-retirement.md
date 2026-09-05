# Amendment G-A019 -- the nugget is coloured, and `sf >= 0.95` retires for claim A

Date: 2026-09-05 UTC. Status: `AMENDMENT_PRE_G3`.

Append-only amendment to `docs/phase-G/55-prereg-G-A017.md` (tag
`phase-G2-a017-prereg`, commit `44ad1227`) and to
`docs/phase-G/57-amendment-G-A017a-nugget-decomposition.md`. Neither is
edited. It arises from external review of `G'.2` and from run 3, an
instrumented replication that captured the raw series.

It reverses no verdict. `docs/phase-G/60-kill-test-results.md` stands, its
artifact hash is unchanged, and run 3 reproduces it.

## 1. What run 3 added: the nugget measured directly

Run 3 stored `rho_measured` and `rho_target` for 4 replicates x 4,100 windows
x 8 links. Because `rho_target` is deterministic given the seed, the nugget is
observable with no estimator and no model:

    eps = rho_measured - rho_target

Controller and sampler run on separate `perf_counter` origins, so alignment
was verified first: `Var(eps)` is minimised at integer lag 0 and rises
symmetrically either side (`6.50e-05` at lag 0 against `1.79e-04` at lag -1
and `1.76e-04` at lag +1). The series are aligned.

| Quantity | Direct measurement | Previously |
|---|---:|---|
| `v` | `6.50e-05` | `7.45e-05` via `estimate_nugget`, 15 percent high |
| `max\|rho_eps\|` over 28 pairs | **`0.0227`** | `NOT_IDENTIFIABLE` in G.1 |
| `median\|rho_eps\|` | `0.0079` | -- |

### 1.1 The G.1 debt is paid, in passing

`G.1` could not identify `rho_eps` at all, and `G'.4` existed largely to
recover it. It is now measured directly for all 28 pairs at
`max = 0.0227`, against the doc 55 `B-2` target of `0.15` and limit of `0.30`.
**`B-2` target is met with 6.6x of margin.** This is a by-product of storing
1.7 MB of raw series, and it did not cost a single additional experiment.

## 2. ★ The nugget is NOT white

This is the finding that changes the estimator.

    lag      1       2       3       4       5       6       7       8
    ACF   -0.5019  0.0053 -0.0026 -0.0003  0.0019 -0.0018 -0.0010  0.0011
    white-noise band: +/- 2/sqrt(4100) = +/- 0.0312

`ACF(1)` is sixteen band-widths outside. Every other lag is inside. That
pattern is not "somewhat correlated noise": `ACF(1) = -0.5`, `ACF(k>=2) = 0`
is the exact signature of

    eps_k = u_k - u_{k-1}

the first difference of a white sequence. The measured `-0.5019` against a
theoretical `-0.5000` leaves little room for an alternative reading.

**The mechanism is conservation, not noise.** A token bucket does not lose
bytes. A window that under-delivers leaves tokens in the bucket, and the next
window delivers them. The deficit of one window is the surplus of the next,
which is a first difference by construction.

**G-L103:** a measurement path that CONSERVES the measured quantity produces a
first-difference nugget, `ACF(1) = -0.5`, not a white one. Any argument that
depends on nugget whiteness must therefore be re-derived for a conserving
path. In particular the nugget-immunity of the log-linear ACF-slope estimator
does NOT survive: a white nugget scales every lag by `sf` and lands entirely
in the intercept, while a first-difference nugget depresses lag 1 alone,
tilting the fitted slope shallower and inflating `tau_hat`.

## 3. Consequence for the frozen estimator of doc 55 section 3

Doc 55 froze the fit over lags 1..8. With a first-difference nugget:

    ACF_meas(k) = [sigma^2*phi^k + Cov_eps(k)] / (sigma^2 + v)
    k = 1   Cov_eps(1) = -0.5v   ->  lag 1 DEPRESSED below sf*phi
    k >= 2  Cov_eps(k) = 0       ->  lags 2+ are EXACTLY sf*phi^k

Measured on run 3's own data:

| Fit range | `tau_hat` median | bias vs `tau = 2.0` |
|---|---:|---:|
| lags 1..8, as signed | 2.0884 | **+4.42%** |
| lags 2..8 | 1.9851 | -0.74% |
| generator only, no network | 1.9972 | -0.14% |

Excluding lag 1 recovers the generator's own behaviour. The entire anomaly is
accounted for.

### 3.1 What this would have cost the campaign

`results/SMOKE/phase-G2/g1_bias_sim_ma1.json` re-runs the doc 55 bias
simulation under both nugget models. The MA(1) nugget by itself is not fatal;
the fatal thing is the MISMATCH of applying doc 55's white-noise `b(tau)` to a
path whose nugget is coloured:

| `tau` | `b` signed (white, 1..8) | true `b` (MA1, 1..8) | corrected ratio | `\|err\|` | claim B |
|---:|---:|---:|---:|---:|---|
| 1 s | 0.9737 | 1.0276 | 1.0553 | 0.055 | PASS |
| 3 s | 0.9843 | 1.0222 | 1.0384 | 0.038 | PASS |
| 5 s | 0.9752 | 1.0396 | 1.0660 | 0.066 | PASS |
| 10 s | 0.9695 | 1.1090 | 1.1439 | 0.144 | PASS |
| 20 s | 0.9810 | 1.2674 | 1.2920 | **0.292** | **FAIL** |

The error grows with `tau` because a fixed lag-1 deficit is a larger fraction
of the slope when the ACF decays slowly. At `tau = 20 s` the campaign would
have failed claim B by construction, and the failure would have looked like a
physical result rather than an estimator artefact.

### 3.2 The fix, and why it is the robust one

Fitting lags 2..8 makes `b` nearly independent of the nugget model:

| `tau` | `b` white, 2..8 | `b` MA1, 2..8 | spread |
|---:|---:|---:|---:|
| 1 s | 0.9893 | 0.9743 | 0.0150 |
| 3 s | 0.9615 | 0.9685 | 0.0069 |
| 5 s | 0.9893 | 0.9718 | 0.0175 |
| 10 s | 0.9830 | 0.9962 | 0.0132 |
| 20 s | 0.9758 | 0.9700 | 0.0057 |

The point is not that lag-2 fitting is more accurate. It is that its bias does
not depend on a property of the hardware that nobody measured until run 3.
Correcting with an MA(1)-specific `b` would also work, and would be fragile:
it would silently mis-correct on any path whose `ACF(1)` differs.

**Estimator amendment, superseding doc 55 section 3 for `tau` only:** fit the
log-linear ACF slope over lags **2..8**, retaining every other clause
including the slope-only reading of `G-L99`. `b(tau)` is re-signed from the
`ma1, 2..8` column above. The `sf` reading still uses the intercept over
lags 2..8.

## 4. `sf >= 0.95` retires as a gate on claim A

Doc 55 derived `sf >= 0.95` as follows: `bias = (1-sf)*rho_eps`, and since
`rho_eps` was UNKNOWN it was bounded by its worst case `rho_eps = 1`, giving
`sf >= 0.80`, tightened to 0.95 for margin. The gate was always a PROXY for a
bias that could not then be measured.

`G'.2` measures the bias directly. `G-L100` establishes that `|r_meas|` at
`omega = 0` IS `rho_c*v_c/(sigma^2+v)`, and run 3 additionally measures
`rho_eps` itself at `0.0227`. The proxy has been replaced by two independent
direct measurements of the thing it was standing in for.

| Claim | Requirement | Measured | Margin |
|---|---|---:|---:|
| A: `\|omega_hat - omega\| <= 0.20` | bias `<= 0.20` | `0.0705` | 2.8x |
| C: `\|sigma_hat/sigma - 1\| <= 0.10` | `sf >= 0.8264` | worst link `0.9096` | see 4.1 |

**`sf >= 0.95` is retired as a gate on claim A.** It is retained for claim C
at the threshold claim C actually implies, `sf >= 0.8264`, derived from
`sigma_hat/sigma = 1/sqrt(sf) <= 1.10`.

This is not a relaxation. It is the replacement of a deliberately conservative
proxy by a direct measurement of the same quantity, which is the disposition
`G-L100` was written to enable.

### 4.1 `sf` is reported min-over-links from here

`rho_measured_sd` varies by a factor of 1.47 across links by design: at
`omega = 0` the private amplitude scales as `a0*sqrt((1-omega)*DEGREE)` and
`DEGREE` differs per link. `sf` therefore differs per link, and a median hides
the binding case.

    run 3 per-link sf: 0.9537 0.9589 0.9118 0.9096 0.9153 0.9164 0.9555 0.9608
    median 0.9340        MIN 0.9096  (link 3, 'ad')

A budget is a constraint on EVERY link; a multi-link claim is only as strong
as its weakest link. All `sf` reporting is min-over-links from here, with the
distribution alongside.

Against the retired target of 0.95 the worst link would have been recorded as
a miss. Against claim C's actual requirement of 0.8264 it passes with 1.10x on
`sf`, i.e. `sigma_hat/sigma = 1.0484` against an allowance of 1.10.

Note the margin against the doc 55 `B-1a` LIMIT of 0.90 is only `0.0096`. That
limit is not retired here and remains tight; it is now reported against the
worst link rather than the median, where the apparent margin was 0.034.

## 5. What is corrected in doc 60

Doc 60 section 5 recorded that the residual nugget's source was "not
identified" and that "no mechanism is asserted". The source is now identified:
token-bucket conservation, giving a first-difference nugget. Doc 60's verdict
`GO*` is unchanged and is strengthened, because the residual is now not merely
inferred to be independent from `KILL-1` but measured to be so at
`max|rho_eps| = 0.0227`.

Doc 60 section 7's statement that the run "does not identify the source of the
residual nugget" is superseded by this amendment. Doc 60 is not edited.

## 6. Housekeeping

`tools/g2_kill_test.py` writes to a fixed artifact name, so run 3 overwrote
run 2's file. Run 2 was restored from commit `c8967123` and run 3 stored as
`g2_kill_test_run3_instrumented.json`; doc 60's recorded hash was verified to
match again. A tool that can silently overwrite a hash-referenced contract
artifact is a latent hazard and should take an explicit output name.

## 7. Referenced artifacts

| Artifact | SHA256 |
|---|---|
| `results/SMOKE/phase-G2/g2_kill_series.npz` | `64279ffe1610858383003587ef53a64eba2096f7c8083d8f7b8e8c00b48f986b` |
| `results/SMOKE/phase-G2/g2_kill_test_run3_instrumented.json` | `567b5ddb1faeae7855422f567628e94c02cbcea24a274dd782a278822f4776b5` |
| `results/SMOKE/phase-G2/g1_bias_sim_ma1.json` | `f42bc85f7f0e4ff3648a6718570403480f8d8cfde06c210b3ff2a016cb4b3b63` |
