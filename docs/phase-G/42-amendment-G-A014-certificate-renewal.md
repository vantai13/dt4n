# G-A014 — certificate renewal, infrastructure gate, and kappa budget

Signed: 2026-09-03 UTC, after `phase-G-g3-emitter-reduction-prereg` and before
the first real-time emitter benchmark. Status: `SYNTHETIC_NO_NETWORK`.

This amendment is append-only. It rewrites no prior artifact, moves no tag, and
changes no already-recorded outcome. It closes one logical gap and two budget
risks found while auditing the path from G.1 to the first Mininet run.

## 1. The G.1 certificate does not transfer automatically

`results/LIVE/phase-G/measurement_path_cert.json` lists six expiry conditions.
One of them is verbatim:

    pacing process changes

The certificate was measured with `mininet/static_emitter.py`: deterministic
CBR, absolute cumulative batch pacing, `pace_tick_s=0.002`, and no spin. The
Phase-G campaign generator is `mininet/modulated_emitter.py`: per-packet
absolute deadlines, coarse sleep followed by a 200 us spin, and an independent
per-window `round()` that never carries a deficit. This is a change to the
pacing process.

Therefore the conditional certificate **has expired for the modulated
emitter**. Every downstream number that inherits it is currently unsupported
for the new generator:

| inherited quantity | value | source |
|---|---:|---|
| campaign sigma boundary | `sigma >= 0.020232558139534878` | G.1 closeout |
| feasible cells | 9 / 40 | G.1 closeout |
| G.2 anchor amplitude | `a0 = 171679 bit/s` | G.2 feasibility |
| per-link measurement nugget | independent-round `v_pack` | G.1 measure |

`G3-Q` in `31-prereg-g3.md` re-verifies the quantization **mechanism** by the
sign of `ACF1(eps_quant)`. It does not re-verify the quantization **variance**
or the headroom that generated the feasible grid. This amendment supplies the
missing renewal gates.

**G-L86:** an expiry clause is only enforceable if some later gate actually
tests the condition it names. A certificate that expires on "pacing process
changes" needs a renewal procedure attached to the process change, not only a
mechanism check.

## 2. Renewal gates G3-V and G3-F

Both are evaluated on the first physical run, on the same post-burn-in window
index set already required by the signed alignment gates, before any `G3-E` or
`rho_eps` outcome is read.

    quantum_l   = wire_bits / (C_l * dt)
    eps_pkt_l   = (rho_sent_l - rho_target_l) / quantum_l
    floor_l     = sqrt(1/12) * quantum_l

    G3-V:  abs( Var(eps_pkt_l) / (1/12) - 1 ) <= 0.15        for every link
    G3-F:  sd(rho_target_l) / floor_l         >= 5           for every link

`G3-V` renews the certified independent-round variance. `G3-F` renews the
headroom constraint that produced the 9-cell feasible grid; it is evaluated on
`rho_target` because a headroom loss there is a generator defect, not an
instrument defect.

Neither renewed constant is restated in the renewal module.
`tools/g3_cert_renewal.py` imports `1/12` from `tools.g1_quant_model`, the
headroom `5` from `tools.g0_feasibility`, and the `0.10` correlation gate from
`tools.g3_emitter_dryrun`, so a renewal gate cannot drift away from the
quantity it claims to renew. `test/test_g3_cert_renewal.py` asserts that
identity directly.

The 0.15 tolerance is chosen against the sampling error of a variance
estimate. At the smoke length `n=300` the iid approximation `sqrt(2/n)` is
0.082, so 0.15 is about 1.8 standard errors. At the campaign length `n=15000`
it is 0.012, so 0.15 is very wide and a failure there is a physical event
rather than sampling noise. Both lengths are reported.

Consequence of failure, fixed before data:

- `G3-V` FAIL: the certified `1/12` variance no longer describes the deployed
  emitter. Stop after the first run. The G.0 feasibility map and the G.2 `a0`
  window must be recomputed with the measured variance before any second cell.
- `G3-F` FAIL: the campaign amplitude does not clear the quantization floor on
  some link. Stop. Do not re-scale `a0` after seeing which link failed;
  recompute the whole grid.

Neither gate may be relaxed, rounded, or evaluated on a link subset.

## 3. Infrastructure gate G3-C

`EMIT-3` measures whether emitters sharing CPUs manufacture cross-link timing
correlation. It is adjudicated on a bench with no Mininet, no OVS, no veth
pairs, no controller, and no telemetry bundle.

`G-L38` records that exactly this mechanism invalidated NC-G1-static v1, where
shared scheduler stalls produced `rho(uA,uB)` of 0.9912--0.9942 across cells;
the pattern disappeared once spin pacing was removed in v2.

The v3 receipts show that the infrastructure cost added by Mininet is not
negligible, and that the bench does not see it. The no-Mininet ledger cost
gate recorded CPU p50 9.550% and p95 17.276%. Inside Mininet, in the same
campaign and before any modulated generator existed, the cleanest cell D
reached CPU p95 19.212% and cell A reached 52.540%.

A bench PASS therefore does not license reading cross-link outcomes inside
Mininet.

    G3-C: on the first physical run, in the clean cell, the maximum absolute
          off-diagonal correlation of per-window maximum deadline lateness is
          at most 0.10, using the doc-41 reduction: mean the per-replicate
          correlation matrices elementwise, then take the pairwise maximum.

`G3-C` uses the same estimand, the same reduction order, and the same null
calibration as `EMIT-3` (`3000` trials, seed `20260909`, null p99 `0.051107`;
the gate is `1.957x` that p99). The implementation calls
`tools.g3_emitter_dryrun.mean_correlation_then_max` rather than duplicating it,
so the bench gate and the deployment gate cannot diverge. A link with zero
lateness variance is refused, not imputed.

Failure of `G3-C` means the infrastructure is still a confound. `G3-E` and
`rho_eps` must not be read on that run. This is a validity gate, not an
outcome.

**G-L87:** a gate that measures an instrument on a bench must be repeated in
the deployment environment before its verdict is transferred there. The bench
removes exactly the components whose interference the gate exists to detect.

## 4. Time-scale ratio and campaign budget

`31-prereg-g3.md` fixes the ordered regimes `(tau_p,tau_g) = (3,3)` and
`(30,3)` seconds, and `T = 200*max(tau_p,tau_g)`. That gives `T=6000 s` per
`kappa=10` run. With five omega values, three replicates for the two primary
regimes, one for the signed symmetry diagnostic, and 60 s of setup and burn-in
per run, the campaign costs 36.42 wall-clock hours. The signed stop rule is six
elapsed days. The three prior static campaigns each required at least one full
redesign, so a budget with no slack is not prudent.

`kappa` is a design parameter, and the run-time budget must be derived from it
rather than assumed. `tools/g3_kappa_ladder.py` computes, entirely
analytically and with no network data, the pairwise `P(flip)` spread of the
signed P1-P2 stale margin over the ladder `kappa in {1,2,3,4,5,6,8,10}` at
fixed `tau_g=3 s` and the signed staleness `z=2 s`. It imports `contrast`,
`quad_forms`, and `p_flip` from `tools.g2_decision_flow`, so its `kappa=10` row
reproduces the signed `DRY-D-PC` value `0.2134360846918576` by construction
rather than by agreement; `test/test_g3_kappa_ladder.py` asserts that
reproduction against the committed `g3_dryrun_a013.json`.

Selection rule, together with its safety factor, is recorded here before the
campaign: **the smallest kappa on the ladder whose analytic flip spread is at
least `1.5 x 0.10`**, where `0.10` is the inherited `DRY-D-PC` threshold. The
ladder, the selection rule, and the safety factor are all recorded together.
The safety factor 1.5 is a design choice, not a derived constant; it is fixed
here so that the selected regime retains stated margin above the inherited
threshold rather than sitting on it. No network data informs this selection.
The full ladder is reported whether or not a row is selected.

| kappa | tau_p (s) | T_pc (s) | flip spread | campaign hours | note |
|---:|---:|---:|---:|---:|---|
| 1 | 3 | 600 | 0.00000 | 6.42 | negative control, omega inert |
| 2 | 6 | 1200 | 0.08265 | 9.75 | below the inherited 0.10 gate |
| 3 | 9 | 1800 | 0.12394 | 13.08 | clears the gate, misses the margin |
| 4 | 12 | 2400 | 0.14966 | 16.42 | misses the margin by 0.00034 |
| **5** | **15** | **3000** | **0.16763** | **19.75** | **selected** |
| 6 | 18 | 3600 | 0.18109 | 23.08 | |
| 8 | 24 | 4800 | 0.20023 | 29.75 | |
| 10 | 30 | 6000 | 0.21344 | 36.42 | regime signed in 31-prereg-g3 |

The `kappa=4` row is reported precisely because it is close. It clears the
inherited gate and is still excluded, because the rule stated above is the
rule that was applied, not a rule chosen after reading the column.

Amended primary regimes:

    NC        (tau_p,tau_g) = ( 3,  3) s    kappa = 1      T =  600 s
    PC        (tau_p,tau_g) = (15,  3) s    kappa = 5      T = 3000 s
    SYMMETRY  (tau_p,tau_g) = ( 3, 15) s    kappa = 0.2    T = 3000 s

Everything else in `31-prereg-g3.md` is unchanged: the omega grid, the duration
law `T=200*max(tau_p,tau_g)`, the omega round-trip gates, the alignment gates,
`G3-Q`, `G3-E`, and every stop condition. The 46% saving is spent on redesign
slack inside the six-day rule, not on additional cells.

A synthetic control accompanies the selection. At the selected regime, over the
five omega values, 40 replicates, seed `20260910` and `T=3000 s`, the maximum
absolute median omega bias is 0.010058 and the maximum sample SD is 0.032040,
against the signed 0.05 gates. The `kappa=1` flip spread is exactly zero to
numerical precision, retained as the quantitative negative control required by
G-A010.

Ladder gates, all adjudicated by the tool before the campaign:

| id | check | value | gate |
|---|---|---:|---:|
| KAP-1 | selected kappa flip spread | 0.167632 | >= 0.150000 |
| KAP-2 | kappa=1 negative control flat | 0.000000 | <= 1e-12 |
| KAP-3a | omega round-trip max abs median bias | 0.010058 | <= 0.05 |
| KAP-3b | omega round-trip max sd | 0.032040 | <= 0.05 |
| KAP-4 | mixture ACF monotonicity violation | 0.000000 | <= 0 |
| KAP-5 | campaign wall-clock hours | 19.75 | <= 24.0 |

**G-L88:** a design parameter that multiplies run time must be selected by a
rule stated with its ladder and its margin, before any campaign starts.
Selecting it after a physical run would be an outcome-based budget change.
Computing the ladder is not outcome peeking: it is pure algebra over the signed
topology and contains no network data.

## 5. Scope boundary

This amendment authorizes nothing new to execute. Mininet remains prohibited
until the L0 emitter gates of `40-amendment-g3-emitter-ladder.md` and
`41-amendment-g3-emitter-reduction.md` pass. `G3-V`, `G3-F`, and `G3-C` are
gates on the first physical run, not on the bench benchmark.

The public DOI remains null. K12's user-attested offsite backup permits local
Phase-G capture only.

## Artifacts

- `tools/g3_kappa_ladder.py`
- `tools/g3_cert_renewal.py`
- `test/test_g3_kappa_ladder.py`
- `test/test_g3_cert_renewal.py`
- `results/SMOKE/phase-G/g3_kappa_ladder.json`

`tools/g3_dryrun.py` is touched only to rename the private `_ar1` helper to
`ar1` so the ladder can reuse it instead of copying it. No dry-run value
changes.

Preregistration tag: `phase-G-g3-a014-prereg`.
