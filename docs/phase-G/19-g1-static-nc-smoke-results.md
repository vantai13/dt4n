# NC-G1-static network smoke — INVALID, full campaign blocked

Date: 2026-08-30 UTC.

## Verdict

The six-cell, one-repetition, 60-second network smoke completed, but all six
cells are `INVALID`. The locked G1S-2 white-noise gate failed in every cell;
only one of 48 link-runs passed it. Five cells also exceeded the locked 80%
CPU-p95 gate. The confirmatory 18-run campaign was therefore not executed:
under the preregistration, more data cannot convert an invalid instrument into
a low-v certificate.

This is a validity failure, not evidence that any sigma value is feasible or
infeasible. No `measurement_path_cert` was issued in `results/LIVE`.

## Pre-outcome lock and engineering receipt

- Preregistered code commit: `8e9aa9b9`.
- Annotated tag created before network data:
  `phase-G-g1-static-nc-prereg`.
- Local custody basis:
  `USER_ATTESTED_OFFSITE_BACKUP_WAIVER`; public DOI remains null.
- Offline geometry was as expected: 612.143 packet/s, 1.63361 ms gap,
  122.429 packet/0.2 s, quantization floor 0.00235791 for the 8-Mbit/s
  reference configuration.
- After the smoke, analysis initially stopped on repeated ledger timestamps.
  Inspection showed monotone cumulative bytes and only redundant observations
  created when one emitter loop serviced multiple log deadlines. Commit
  `803039ad` coalesces identical observed instants by retaining their final
  cumulative state. It changes no packet or counter observation and adds no
  interpolation. The final artifact records analyzer git hash `803039ad`.

## Locked gate results

| cell | G1S-1 flat links | G1S-2 white links | CPU p95 | read p95 (us) | implied timing error | final |
|---|---:|---:|---:|---:|---:|---|
| A | 4/8 | 0/8 | 95.460% | 1067.9 | 0.00534 | INVALID |
| B | 8/8 | 0/8 | 90.559% | 476.9 | 0.00238 | INVALID |
| C | 8/8 | 0/8 | 86.836% | 764.7 | 0.00382 | INVALID |
| D | 8/8 | 0/8 | 77.062% | 304.2 | 0.00152 | INVALID |
| E | 8/8 | 0/8 | 83.669% | 330.7 | 0.00165 | INVALID |
| F | 8/8 | 1/8 | 86.347% | 327.1 | 0.00164 | INVALID |

All runs had zero host network drops, zero swap, zero emitter send errors,
packet shortfall at most 0.01, and maximum emitter lag below 0.05 s. G1S-4
also passed: every run metadata hash is the preregistration commit itself.
Cell A additionally failed G1S-5 and four offered-flatness link gates.

The observed white ratios ranged from 0.205 to 1.784. Values well below one
show slow/shared components; values above 1.25 show that differencing amplifies
periodic/anti-correlated components. Either direction rejects the locked white
additive-nugget model.

## Diagnostic measurements only

The following values are retained for diagnosis but cannot be promoted to a
certificate because validity failed.

| cell | range of direct v across links | rho(uA,uB) TX | rho(ac,ad) TX | rho(bc,bd) TX | rho(vC,vD) TX | rho(vC,vD) RX |
|---|---:|---:|---:|---:|---:|---:|
| A | 1.0152e-5–5.2687e-3 | 0.7738 | 0.0612 | 0.1270 | -0.1198 | -0.1198 |
| B | 8.5445e-6–3.3604e-3 | 0.9915 | 0.0132 | -0.1408 | -0.1187 | -0.1325 |
| C | 8.6762e-6–3.3341e-3 | 0.9942 | 0.0707 | 0.1380 | 0.1296 | 0.1296 |
| D | 3.8181e-6–3.4086e-3 | 0.9777 | 0.0771 | 0.0244 | 0.0734 | 0.0734 |
| E | 8.4132e-6–3.7971e-3 | 0.9234 | 0.1338 | -0.0879 | 0.0009 | 0.0009 |
| F | 7.5325e-6–3.6318e-3 | 0.9912 | 0.7971 | -0.1774 | 0.0995 | 0.0995 |

No preregistered grouping was fully separated. H6b is not supported
descriptively because vC-vD stayed low while uA-uB was high. H6c is not
supported as a complete mechanism because ac-ad and bc-bd did not consistently
join uA-uB. The telemetry and sampler hypotheses are not adjudicated because
the cells are invalid.

The RX extension also exposed an identification limit, now G-L37: the runner
reads every root-namespace interface in one `/proc/net/dev` operation. TX and
RX labels therefore do not represent independent per-node counter samplers.
A future H-SAMPLER test must use per-node collectors or separately timestamped
counter reads.

## Artifacts and reproduction

- Compact gate/certificate result:
  `results/SMOKE/phase-G/g1_static_smoke_cert.json`.
- Full per-link/per-pair detail:
  `results/SMOKE/phase-G/g1_static_smoke_detail.json`.
- Local raw custody (219 files, about 18 MiB):
  `results/RAW/phase-G/g1-static-smoke/<cell>/rep1/`.
- Preregistration and locked thresholds:
  `docs/phase-G/18-prereg-g1-static-nc.md`.

Reanalyse without rerunning the network:

```bash
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python -m tools.g1_static_nc \
  --campaign results/RAW/phase-G/g1-static-smoke \
  --out results/SMOKE/phase-G/g1_static_smoke_cert.json \
  --detail-out results/SMOKE/phase-G/g1_static_smoke_detail.json
```

The next permissible action is a newly preregistered engineering redesign of
the negative control (CPU pacing and white/quantization decomposition), not the
locked 300-second confirmatory campaign.
