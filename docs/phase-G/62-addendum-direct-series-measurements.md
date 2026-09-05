# Addendum -- direct measurements from the stored series

Date: 2026-09-05 UTC. Status: `ADDENDUM_NO_VERDICT_CHANGE`.

Append-only addendum to `docs/phase-G/60-kill-test-results.md` and
`docs/phase-G/61-amendment-G-A019-nugget-colour-and-sf-retirement.md`, neither
edited. It arises from a second review round. It reverses nothing: doc 60's
`GO*` stands and its artifact hash is unchanged.

Artifact: `results/SMOKE/phase-G2/g2_series_analysis.json`.

## 1. The path CONSERVES, and the residual is a rate offset

If `eps_k = c_{k-1} - c_k` then the partial sums telescope to `c_0 - c_n`,
bounded by the bucket, whereas a white nugget of the same variance random-walks
as `sqrt(n)*SD`.

| Quantity | Value |
|---|---:|
| `max abs cumsum(eps)` observed | 0.1190 |
| predicted if WHITE, `sqrt(n)*SD` | 0.5049 |
| predicted if CONSERVING, `~2*burst` | 0.0369 |

Observed is 24 percent of the white prediction, so the path conserves. It is
3.2x the pure two-burst bound, and that excess is fully accounted for:

| Growth of `mean abs cumsum` with run fraction | 1/8 | 1/4 | 1/2 | 1 |
|---|---:|---:|---:|---:|
| observed | 0.0084 | 0.0076 | 0.0111 | 0.0177 |
| if `sqrt(n)` | 0.0084 | 0.0119 | 0.0168 | 0.0238 |
| if linear in `n` | 0.0084 | 0.0168 | 0.0336 | 0.0672 |

Growth is SUB-`sqrt(n)`, i.e. bounded, which is the conserving signature. The
single largest excursion, 0.1190, belongs to one link and is explained by a
systematic mean offset: `max|mean(eps)| = 2.79e-05`, and `2.79e-05 * 4100 =
0.1144` against the observed 0.1190. `KILL-4` independently measured a sink
rate ratio error of `4.89e-05`, the same order.

There is no loss source. There is a per-link rate offset of about `3e-05` in
`rho` units, three thousandths of one percent.

## 2. `rho_eps` is not distinguishable from zero

Doc 61 reported `max|rho_eps| = 0.0227` as meeting the `B-2` target of 0.15
"with 6.6x of margin". That understates the result. A small number without a
null is not a measurement, so the null was computed: MA(1) nugget, 8 links
independent BY CONSTRUCTION, 4 replicates Fisher-z pooled, 400 trials.

| Statistic | Observed | Null median | Null p95 | Null p99 | `P(null >= obs)` |
|---|---:|---:|---:|---:|---:|
| `max\|rho_eps\|` over 28 pairs | 0.0227 | 0.0211 | 0.0287 | 0.0331 | **0.335** |
| `median\|rho_eps\|` | 0.0079 | 0.0064 | 0.0086 | -- | 0.160 |

The observed maximum sits at the 66th percentile of what independent links
produce at this sample size.

> **The correct statement is not "`rho_eps` is small". It is "`rho_eps` is not
> distinguishable from zero, against a calibrated null."**

For the `G.1` debt this distinction is the whole point. `G.1` returned
`NOT_IDENTIFIABLE`. The return value is now `rho_eps = 0 to the resolution of
this measurement`, which is a statement with content rather than an absence.

## 3. Lag-1 contamination depresses `sf` as well as inflating `tau`

Doc 61 established that a conserving nugget tilts the fitted slope shallower,
inflating `tau_hat`. The same depressed lag 1 also lowers the fitted INTERCEPT,
and the intercept is `sf`. Both readings move, in opposite directions.

| Reduction | `sf` min over links | `sf` median | pooled `tau` bias |
|---|---:|---:|---:|
| lags 1..8, as originally signed | 0.9096 | 0.9350 | +4.42% |
| lags 2..8, per `G-A019` | 0.9294 | 0.9501 | -0.74% |
| direct, `1 - Var(eps)/Var(rho)` | 0.9270 | 0.9472 | -- |

The lag 2..8 fit agrees with the direct measurement to 0.0024 on the minimum;
the lags 1..8 fit is off by 0.0174, in the pessimistic direction.

Consequence for the `B-1a` limit of 0.90: the originally signed reduction
reported a margin of `+0.0096` and made the limit look nearly violated. The
correct margin is `+0.0294`, three times larger. **A limit was almost recorded
as nearly-breached because of an estimator artefact.**

## 4. `tau` pools, `sf` does not

`physical_trace` calls `ar1(len(LINKS), tau_link_s, ...)`: all eight links
share ONE `tau`, so per-link `tau` differences can only be estimation noise.
Pooling all 32 fits is therefore both legitimate and more precise.

`sf` is the opposite. It differs per link BY CONSTRUCTION, because `sigma_l`
scales with `DEGREE` while `v` is common, so it takes min-over-links.

Checked rather than asserted: the observed per-link `tau_hat/tau` spans
`0.908..1.162`, and the bias simulation's median-of-3 spread at this
configuration is `0.888..1.145`. The observed spread is sampling noise.

**G-L104:** the reduction over links is determined by whether the parameter is
SHARED or PER-LINK, not by preference or by symmetry with other gates. A shared
parameter pools; a per-link parameter takes its worst case. Reading a shared
parameter per-link inflates its apparent spread: read this way, `tau` at lags
1..8 shows a worst-link deviation of 0.246 and would have been recorded as
failing claim B on what is demonstrably sampling noise.

## 5. The historical data path is also conserving -- OPEN ITEM

`mininet/run_sync_v7.py:178,190` constructs links with
`TCLink(..., use_htb=True)`. Every Phase G and Phase 23 measurement taken
through that harness therefore came through a token bucket, which is a
conserving path.

Three tools read `estimate_nugget` on that data, all at `N_FIT_LAGS = 8`
starting from lag 1: `tools/g_a003_split_sample.py:40`,
`tools/g1_4_physical_reanalysis.py:47`, `tools/g_measurement_coherence.py:30`.
`estimate_nugget` does not store the per-lag ACF, so no stored artifact can be
re-examined; only the RAW series can.

Preliminary check on the RAW series, fitting lags 2..8 and comparing the
measured `ACF(1)` against the extrapolation:

| Family | link-runs | `n` per link | fraction with lag 1 depressed | median relative deviation |
|---|---:|---:|---:|---:|
| `lesson1-*` | 9 | 199 | 0.89 | -1.35 |
| `g1-static-v3-smoke` | 14 | 299 | 0.86 | -3.93 |

**This is an indication, not an adjudication, and it is recorded as an open
item rather than a finding.** Two reasons for caution:

1. `n` of 199 to 299 gives an ACF noise floor of 0.116 to 0.142, so individual
   fits are weak. `G'.2` had `n = 4100`.
2. The repository already classifies the `g1-static-v3-smoke` family as
   `QUANT_LIMITED` under `G-L43` (45 of 48 cells). For a nearly flat CBR series
   the exponential extrapolation the test relies on is poorly founded, so the
   large negative deviations there may be an artefact of the test rather than
   evidence for it.

The named check, for whoever takes it up: re-run those analyses with the fit
restricted to lags 2..8 and compare `tau` and `sf`. No new measurement is
required; the RAW series are on disk and in the manifest. **No adjudicated
Phase G or Phase 23 result is challenged here.**

## 6. Contract artifacts are now guarded in code

`tools/g2_kill_test.py` wrote to a fixed filename, so run 3 overwrote the
artifact whose SHA256 doc 60 records. It was caught and restored from commit
`c8967123`, and doc 60's hash was verified to match again. Noticing is not a
control, so `tools/artifact_guard.py` now refuses to overwrite an existing
artifact unless `allow_overwrite=True` is passed deliberately.

## 7. Referenced artifacts

| Artifact | SHA256 |
|---|---|
| `results/SMOKE/phase-G2/g2_series_analysis.json` | `ec0a56ec27e6ffa2b6e3eef0dee1eb78b8d99dff56589786285a701d4fd7520a` |
| `tools/g2_series_analysis.py` | `82138648ebd99a4164693a218573f8531f076984c1b596a96b795d0896fffb0c` |
| `tools/artifact_guard.py` | `b78e32359f2349993c6c570926894809b00a81997a3372c483a402636cab8bb3` |
