# Preregistration — measurement-path coherence window W*

Date signed: 2026-08-30 UTC.  This is a post-G-A004 diagnostic design.  It
cannot reverse the locked G-A004 FAIL and does not read either half's
correlation outcome.

## Question and statistic

For each edge link, estimate local nugget variance in sliding windows
`W={50,100,200,400,750,1505}s` using the same eight-lag exponential-ACF fit.
Project the physical boundary as `v_projected=max(v_raw,0)` and calculate
`CV(v_projected)` across windows.  Stride is exactly `W/2`; the final endpoint
window is included when the stride does not land on it.

For each link and W, simulate 400 stationary traces using that link's full-run
`sf` and `tau`, refit `v` inside every window, and lock the pointwise p95 null
CV as the threshold.  This propagates local `sf` estimation error instead of
treating `sf` as known.  Seed is `20260831`.

```text
coherent(link,W) := CV_real(link,W) <= p95[CV_stationary_null(link,W)]
W* := largest identifiable W for which every edge link is coherent.
```

The p95 bands are pointwise, not simultaneous familywise confidence bands;
W* is a design diagnostic, not a confirmatory population parameter.

## Identifiability rule

At least two windows and finite CV in at least 95% of null simulations are
required.  The 1,504.8 s trace supplies only one window at requested `W=1505s`,
so that point must be `NOT_IDENTIFIABLE_ONE_WINDOW`.  No resampling of the same
full window may be used to fabricate across-window variation.

## Custody order

1. Commit/tag this design as `phase-G-coherence-threshold-prereg`.
2. Run only the stationary-null threshold stage; it records
   `physical_curve_read=false`.
3. Commit/tag its artifact as `phase-G-coherence-threshold-locked`.
4. Only then run the physical curve and report every W/link, including
   boundary fractions and non-identifiable points.

## Commands after their required tags

```bash
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python \
  tools/g_measurement_coherence.py --stage threshold
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python \
  tools/g_measurement_coherence.py --stage measure
```
