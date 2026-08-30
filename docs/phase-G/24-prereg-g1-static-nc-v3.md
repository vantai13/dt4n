# Preregistration — NC-G1-static v3 paired residual

Signed before the first v3 Mininet run. Tag:
`phase-G-g1-static-nc-v3-prereg`.

## Custody and engineering receipt

The public DOI remains null. K12's user-attested offsite backup permits local
Phase G capture but is not public archival custody and authorizes no cleanup.

Before this preregistration, eight v3 emitters ran for 30 seconds without
Mininet at ledger tick 0.002 s. Artifact
`results/SMOKE/phase-G/g1_static_v3_cost_gate.json` is PASS: CPU p50 9.550%,
CPU p95 17.276% (<25%), all 8 exit codes zero, zero swap and network drops.
Failure of this receipt would have blocked network capture.

## Locked generator, sampler, and campaign

- Eight deterministic CBR channels, payload 1400 B, `rho_bar=0.857`, absolute
  cumulative pacing, `pace_tick=0.002 s`, no spin.
- Emitter cumulative ledger tick 0.002 s. Each row records absolute monotonic
  time after the due send batch. Counter rows retain `monotonic_s` and add its
  explicit alias `sample_t_mono`.
- Two counter samplers remain for schema continuity and diagnostics; the
  phase-offset correlation is not a validity gate.
- Burn-in 20 s. Six A--F cells run for 60 s, one repetition at `dt=0.2 s`.
- The signed dt positive-control axis independently runs cell D for 60 s at
  `dt={0.2,0.5,1.0}`. Its 0.2-s run is not silently reused from the A--F axis.
- Only if every smoke certificate cell is VALID and the dt control passes may
  the six cells run for 300 s x 3 repetitions. The dt axis is also retained.
- Telemetry matrix and host are unchanged from v2.

## Locked paired model and per-link gates

For each link, cumulative packet count at a counter endpoint is the last ledger
state whose absolute time is not later than that endpoint. Linear interpolation
is forbidden. After burn-in, ordinary least squares fits
`M_k=B*delta_N_k+c+R_k`.

- G1S3-1: `abs(B_hat-1442) <= 4` bytes.
- G1S3-2: `abs(c_hat) <= 0.01*abs(B_hat)*mean(delta_N)`.
- G1S3-3: `sd(R)/abs(B_hat) <= 1.5` packets.
- G1S3-4: residual ACF(1) is in `[-0.60,0.15]`.
- G1S3-7: nominal alignment error `rate_pps*0.002 <= 1.2` packets.
- Conservative G1S3-7b: observed maximum ledger gap times `rate_pps <=1.2`
  packets. This prevents the nominal interval from masquerading as a bound
  during a scheduler stall.
- G1S3-8: ledger lag p95 <=0.02 s and maximum lag <=0.05 s.

Run gates retain v2 thresholds: CPU p95 <40%, zero swap/network drops/send
errors, packet shortfall <=0.01, emitter maximum lag <=0.05 s, sampler read
duration implying rate error <0.005, static engine, two sampler files, and
preregistration-tag ancestry. All gates apply without rounding.

## Signed outcomes and predictions

These are outcomes, not validity gates unless stated above.

1. Strong prediction: `B_hat=1442+/-2` on every link and cell.
2. Cell D prediction: `v_path/v_pack <0.3`, with both variances in rho-squared
   units.
3. In cell D, `rho_path(uA,uB)>=0.5` supports shared path/sampler noise;
   `<=0.15` supports a clean path; the interval between is INCONCLUSIVE.
4. Predicted path-variance order is `D < F < C < B < A`, matching the prior
   telemetry/CPU ordering. E is reported but not inserted post hoc.
5. The dt positive control expects measured variance ratios 6.25 for
   `0.2/0.5` and 4.0 for `0.5/1.0`. A per-link factor-two band is locked:
   `[3.125,12.5]` and `[2,8]`; all eight links must pass.

Certificate feasibility uses `v_pack_rho_units+v_path`; path correlation uses
only paired residuals. The analyzer also records `v_pack_relative_units` but
never adds it to rho-squared variance.

## G.0 cross-phase audit

G-A001 requires `tau/dt>=10` on tau grid `{0.5,1,3,10,30}` seconds.

| dt (s) | retained tau (s) | excluded by resolution |
|---:|---|---|
| 0.2 | 3, 10, 30 | 0.5, 1 |
| 0.5 | 10, 30 | 0.5, 1, 3 |
| 1.0 | 10, 30 | 0.5, 1, 3 |

The v3 dt control does not silently change the closed G.0 artifact. Any future
campaign must select dt per tau from this table and preserve all other G.0
feasibility gates.
