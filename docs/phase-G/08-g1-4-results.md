# G1-4 result — physical positive control and Phase-23 reanalysis

Run date: 2026-08-29 UTC.  The outcome-producing run followed tag
`phase-G-g1-4-prereg` at commit `407eee4e`.  An earlier attempt under the
`sdn_net` environment stopped at import because pandas was absent; it ran no
synthetic or physical calculation.  The recorded run used `sdn_rl`.

## Verdict

**G1-4 FAIL.  Do not claim physical certification of the two-band estimator or
a quantitative confirmation of H6 from this analysis.**

The unequal-timescale synthetic extension passed, so the failure is specific
to the physical traces/model assumptions rather than its two-by-two algebra.

| Gate | Result |
|---|:---:|
| G1-4S unequal-timescale synthetic control | PASS |
| G1-4A all 8 cellA nugget fits valid | FAIL |
| G1-4B all 28 cellA controls pass | FAIL |
| G1-4C all Phase-23 nugget fits valid | FAIL |
| G1-4D all 28 Phase-23 median controls pass | FAIL |
| G1-4E primary `r_true` near zero in both campaigns | FAIL |
| G1-4F primary `rho_epsilon` near one in both campaigns | FAIL |
| G1-4G cross-campaign `rho_epsilon` consistency | FAIL |

## Primary-pair screen output

| Campaign/pair | r measured | r offered | r true hat | rho eps hat | Physical control |
|---|---:|---:|---:|---:|:---:|
| cellA `uA-uB` | 0.1825 | 0.1053 | 0.1025 | 0.6877 | PASS |
| cellA `vC-vD` | 0.1231 | 0.0034 | 0.0505 | 0.6530 | PASS |
| Phase-23 `uA-uB`, median 3 rep | 0.7327 | 0.6064 | 0.6304 | 0.8819 | PASS |
| Phase-23 `vC-vD`, median 3 rep | 0.5088 | -0.5122 | -0.1399 | 0.8648 | FAIL |

The same-run offered ledger disproves the preregistered assumption that both
realized Phase-23 primary correlations would be near zero.  In these short
120-second traces, `uA-uB` offered correlation has median `+0.6064`; the three
individual offered values are `+0.6585`, `-0.3889`, and `+0.6064`.  This is a
finite-realization/low-effective-sample warning, not a population-level
coupling estimate.  The `vC-vD` mismatch remains large in all three reps.

## Failure anatomy

- `cellA_long`: 3/8 link fits returned inadmissible `sf>1` (`ac=1.027`,
  `bc=1.034`, `bd=1.022`).  Consequently only 10/28 pairs were valid.  All ten
  valid pairs passed the locked `0.10` ground-truth error gate.
- Phase-23 rep 1/2/3 had respectively 2/2/3 invalid core-link sf fits.  Valid
  pair counts were 15/14/10; passing pair counts were 8/8/6.
- Across Phase-23 medians, only 6/28 physical positive controls passed.
- CellA primary `rho_epsilon` was only `0.653–0.688`, versus `0.865–0.882` in
  Phase-23.  Cross-campaign differences were `0.194` and `0.212`; the latter
  exceeded the locked 0.20 gate.

No sf or correlation was clamped and no threshold was changed.  The result
shows two distinct limitations: the early-lag sf estimator cannot resolve
near-unity core-link sf without crossing the physical boundary, and the
white-nugget/two-band model does not reproduce the short Phase-23 offered
ground truth across the correlation matrix.

## Artifact

- Path: `results/SMOKE/phase-G/g1_4_physical_reanalysis.json`.
- SHA256: `8567552d1227a70249eade436189db6594911480ed4d5e10ff752205fc227bf0`.
- Elapsed: `0:04.28`; maximum RSS: `373,848 KiB`.
- Status: `PREREGISTERED_REANALYSIS_EXISTING_DATA`; no Mininet and no new RAW.

G2-0 is not opened from this result: G1-4 was intended as its physical
measurement foundation and did not pass.  Any redesign needs a new amendment
and synthetic identifiability audit rather than post-hoc clamping or threshold
relaxation.
