# G'.2 kill test -- preregistration

Date: 2026-09-05 UTC. STATUS: `PREREGISTRATION`. Signed before any data is
taken.

## 1. The hypothesis under test, and what a failure means

`H_shape`: with the rate enforced by the KERNEL and userspace only SETTING a
value once per window, a common stall of duration `delta` in the controlling
process produces a PHASE SHIFT rather than a common ADDITIVE error.

    e_l(t) = rho_l(t - delta) - rho_l(t) ~ -delta * rho'_l(t)

`delta` is common, but `rho'_l` differs per link, so:

    Prediction 1   at omega = 0,  r_meas ~ 0   (no common-mode contamination)
    Prediction 2   v/sigma^2  ~  2*E[delta^2]/(dt*tau)

`H_shape` is FALSE if `r_meas >> 0` at `omega = 0`, or if the measured nugget
is far from what the measured `delta` predicts.

This is an argument about the SHAPE of the error term, carried out of
`docs/phase-G/54-limits-G-L98.md` with an explicit caveat that no
kernel-enforced mechanism has ever been benchmarked in this project. This test
exists to falsify it.

> ★ **If this test fails, `G-L98` is broader than assumed. It does NOT mean the
> new mechanism needs tuning.** Widening a limit is the correct response;
> amending the mechanism is not. This clause is the countermeasure to the
> failure mode that consumed G.3, where seven amendments followed evidence
> that was already sufficient at doc 46.

## 2. Configuration -- deliberately severe

    8 links, full campaign concurrency        (NOT 2; contention is the point)
    omega = 0, sigma_ref = 0.030348837209302317 via the signed A0 scaling
    rho_bar ~ 0.857 per the signed topology
    tau = 2 s,  dt = 0.1 s,  T_run = 205*tau = 410 s,  4 replicates
    total 27.3 minutes of measurement
    rate path: tools.g3_dryrun.physical_trace, unchanged from G.3
    HOST NOT QUIESCED. Ditto, VS Code and docker are left running.

`dt = 0.1 s` follows the signed `T-2` rule `dt <= tau/20`. `T_run` follows the
signed `T-1` rule `205*tau`. No run-length rule is invented for this test: a
kill test that used a shorter run than the campaign would not be testing what
the campaign will do.

Running on a quiesced host would test a system this project will never
campaign on, which is the `NT 55` violation. `docs/phase-G/51d` measured a 26x
reduction in `p_stall_1ms` from quiescing; that reduction is deliberately NOT
taken here.

## 3. Gates -- signed before execution

| Gate | Quantity | Target | Hard | Derived from |
|---|---|---:|---:|---|
| KILL-1 | `max` over 28 pairs of `\|r_meas\|` at `omega = 0`, Fisher-z pooled over 4 replicates | `<= 0.10` | `<= 0.20` | claim A via `G-L100`: at `omega = 0`, `r_meas` IS `rho_c*v_c/(sigma^2+v)`, i.e. the bias itself. Gate B-1b of doc 57 |
| KILL-2 | shaper underrun fraction, windows with `backlog == 0` | `<= 0.001` | `<= 0.01` | the backlogged-source assumption of `H_shape`. If the backlog empties, the mechanism degrades to packet pacing and `G-L98` applies again |
| KILL-3 | `v_measured / v_predicted(delta)` | `[0.5, 3.0]` | `[0.5, 3.0]` | Prediction 2. Discriminates outcome (2) from (3) in section 5 |
| KILL-4 | `\|r_actual/r_set - 1\|` at the sink | `<= 0.05` | `<= 0.05` | an INDEPENDENT check that the `tc` commands landed. Guards the silent failure where `tc -batch` buffers stdin |

### 3.1 KILL-1 null calibration, computed before signing

A maximum over 28 pairs is biased upward under the null even when every true
correlation is zero. `results/SMOKE/phase-G2/g2_kill_null.json`, 400 trials at
the exact signed configuration:

| Statistic of `max\|r\|` under `H0` | Value |
|---|---:|
| median | 0.0558 |
| p95 | 0.0785 |
| p99 | 0.0884 |
| observed maximum over 400 trials | 0.0957 |

| Gate | `P(pass)` under `H0` | Safety factor over null p99 |
|---:|---:|---:|
| 0.10 | 1.0000 | 1.13 |
| 0.15 | 1.0000 | 1.70 |
| 0.20 | 1.0000 | 2.26 |

The target of 0.10 is reachable, with 13 percent of margin over the null p99.
The hard gate of 0.20 carries 2.26x. Both are therefore signable, and the
`G-L90` failure mode -- a threshold unreachable by construction -- does not
apply.

### 3.2 Mutual satisfiability of this gate set

No gate here is a tolerance-free boolean. `KILL-2` is the closest, and it is
deliberately expressed as a FRACTION with a tolerance of 0.001 rather than as
`underrun == 0`, precisely so that a single scheduling artefact in 4,100
windows does not decide the branch.

`KILL-1` and `KILL-2` do not constrain a common variable in opposite
directions: more backlog makes the shaper more immune, which lowers `r_meas`.
They pull the same way.

## 4. The backlogged-source condition

`H_shape` requires the shaper queue never to empty, so that a stall in the
source is absorbed by inventory rather than passed through as a rate dip.

    inventory needed  B >= C*delta_max
    C = 8 Mbps, delta_max = 100 ms  ->  100,000 B = 69.3 frames of 1442 B
    signed qdisc limit = 300 frames -> absorbs a stall of 433 ms

The source uses a BLOCKING socket. When the qdisc fills, `send()` sleeps and
the process self-throttles at the shaper's rate. This is kernel backpressure,
not a busy loop; a non-blocking spin loop would recreate the eight
CPU-consuming processes that `G-L98` says this host cannot provision.

## 5. Reading the result -- four outcomes, four different actions

| `r ~ 0`? | `KILL-3` ratio in range? | Verdict | Action |
|---|---|---|---|
| yes | yes | **GO** | `H_shape` holds. Proceed to G'.3 |
| yes | no | **GO\*** | an unmodelled INDEPENDENT nugget source. Harmless to claim A by `G-L100`. Record a limit, proceed |
| no | yes | **DIAG** | an unmodelled COMMON path that `delta` does not explain. One diagnostic round |
| no | no | **STOP** | `H_shape` is false. Widen `G-L98`. Phase G' terminates |

## 6. Diagnostic round -- ONE only, parameter chosen NOW

    if KILL-2 fails -> raise the qdisc limit from 300 to 1000 frames, rerun once
    else            -> run a 2-link arm, rerun once (localises to contention)

A second failure STOPS Phase G'. There is no third round. Choosing the
diagnostic parameter after seeing the numbers would be p-hacking, so it is
fixed here.

## 7. Instruments recorded regardless of verdict

- controller `delta`: mean, p50, p95, p99, max, **rms**
- sampler `delta`: the same six
- shaper backlog and drops per window
- sink byte counters, for `KILL-4`
- the full 28-pair correlation matrix, per replicate and pooled
- `n_eff` per link
- `sf_hat` from the log-linear intercept, as a forward cross-check on G'.4

`delta_rms` rather than `delta_mean` enters the `KILL-3` prediction, because
the formula contains `E[delta^2]` and the tail dominates it.

## 8. Stop rules

- Maximum 1 diagnostic round for this lesson.
- Not negotiable: the `KILL-1` hard gate, and the section 5 verdict mapping.
- No threshold may be widened from an observation it failed.
- The verdict is `GO`, `GO*`, `DIAG` or `STOP`. There is no fifth state and no
  "close enough".

## 9. Referenced artifacts

| Artifact | SHA256 |
|---|---|
| `results/SMOKE/phase-G2/g2_kill_null.json` | `08cd52b5da8b16673043f3ea76025c4e14e1cfa72553a81ae7ac4faa85894803` |
| `tools/g2_kill_null.py` | `08cd52b5da8b16673043f3ea76025c4e14e1cfa72553a81ae7ac4faa85894803_TOOL` |
