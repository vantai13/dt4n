# G-A017 -- mechanism change and derived error budget

Date: 2026-09-05 UTC. STATUS: `PREREGISTRATION`. Signed before any data is
taken.

This record is desk work. It runs no experiment, touches no network, and
adjudicates nothing. It fixes the claims, the estimators, the run-length rule
and the thresholds of the successor branch to G.3, so that all of them are on
record before any observation exists.

## 1. What changes and what does not

**The MECHANISM changes.** G.3 drove per-link packet pacing from a userspace
deadline loop. `G-L98` records why that cannot work on the available hosts: a
machine-wide stall of duration `delta` deletes packets from every link's
window at once and with the same sign, giving a common-mode error of relative
size `(delta/dt)*rho_bar/sigma`, already 0.706 to 0.749 at `delta = 5 ms`.
G-A017 moves the schedule into the KERNEL, so that a common stall produces a
common PHASE SHIFT rather than a common ADDITIVE error.

**The CLAIMS do not change.** The estimand remains `err(z; sigma, tau, omega)`
and its certificate.

**No adjudicated result is reinterpreted.** `docs/phase-G/53-g3-stop-note.md`
closed the G.3 branch; docs 45, 46, 49, 50, 51 and 52 stand as published.
This preregistration does not inherit their receipts.

⚠️ **Carried caveat.** `G-L98`'s argument that a kernel-enforced schedule
escapes the limit is an argument about the FORM of the error term. No
kernel-enforced mechanism has been benchmarked in this project. The first
thing G'.2 does is try to falsify it (section 7).

## 2. Claims, and every threshold derived from one of them

Three claims. Every gate below traces to one of them through a written
formula. A gate with an empty "derived from" cell is not signed.

    A   |omega_hat - omega| <= 0.20
    B   |tau_hat/tau - 1|   <= 0.20   on the MEDIAN of 3 replicates,
                                       after the signed bias correction
    C   |sigma_hat/sigma - 1| <= 0.10

| Gate | Quantity | Target | Limit | Derived from | Measured by |
|---|---|---:|---:|---|---|
| B-1 | `v/sigma^2` (i.e. `sf`) | `sf >= 0.95` | `sf >= 0.90` | A. Uncorrected bias is `(1-sf)*rho_eps`; at the worst case `rho_eps = 1` this needs `sf >= 0.80`. Tightened to 0.95 so that the correction is a formality, not a dependency (section 2.1) | static NC, direct |
| B-2 | `rho_eps` | `<= 0.15` | `<= 0.30` | A at `sf = 0.95`: bias `= 0.05*rho_eps <= 0.015`, i.e. 7.5 percent of budget A. The margin is large ON PURPOSE (section 2.2) | dynamic NC at `omega = 0`, 28 pairs |
| B-3 | `sigma_hat/sigma` | `+/-0.05` | `+/-0.10` | C directly: `sigma_hat/sigma = 1/sqrt(sf)`; `sf = 0.95` gives 1.026, so C is self-satisfied once B-1 holds | sample sd, `ddof=1` |
| Q-1 | `sigma` | `>= 4.36*sigma_qfloor` | same | B-1 made explicit: the nugget floor is packet quantisation, `sigma_qfloor = 8L/(C*dt*sqrt(12))`. See doc 56 section 2 | computed from `dt` |
| T-1 | `T_run/tau` | `>= 200` | `>= 200` | B. Measured, not assumed: `T/tau = 55` gives 0/18 feasible cells and `T/tau = 100` gives 10/18, against 18/18 at 200 | run parameter |
| T-2 | `dt/tau` | `<= 1/20` | `<= 1/20` | B. At `tau = 1 s` the lag window must sit inside the region where the ACF is still large | run parameter |
| T-3 | tau estimator | log-linear ACF slope, **slope-only** | same | B. Bias `-2.0` to `-2.5` percent against `-7` to `-19` percent for the integral estimator, and independent of `sf` (section 3) | design choice |
| T-4 | bias correction `b(tau)` | signed table, section 4 | same | NT 53. Measured BEFORE signing, from `g1_bias_sim.json` | simulation |
| N-1 | `n_eff` | `>= 200` | `>= 100` | A. Fisher `z` half-width `1.96/sqrt(n_eff-3)`; `n_eff = 55` gives `+/-0.27`, wider than budget A | `n(1-phi^2)/(1+phi^2)` |
| C-1 | `clip_fraction` | `<= 0.005` | `<= 0.01` | C. Clipping truncates the tail, shrinking `sigma_hat` and distorting `tau` | direct count |
| S-1 | `r_actual/r_set` | `+/-0.02` | `+/-0.05` | C. One fifth of the 10 percent `sigma` budget allocated to the shaper stage | byte counter at sink |
| S-2 | rate-change latency | `<= dt/20` | `<= dt/4` | C. A phase shift contributes relative variance `2*delta^2/(dt*tau)`; at `delta = dt/4 = 50 ms`, `tau = 5 s` that is `5e-3`, far under the `1/19` allowed by B-1 | netlink timestamp |

### 2.1 Why the design targets the UNCORRECTED case

`r_meas = sf*r_true + (1-sf)*rho_eps`. The correction requires knowing `sf`
and `rho_eps` accurately. `G.1` failed at exactly that point:
`rho_eps = NOT_IDENTIFIABLE`. A budget that depends on the correction
collapses if the certificate again fails to deliver `rho_eps`.

At `sf >= 0.95` the correction stops mattering. Propagating error at
`sf = 0.95`, `rho_eps = 0.15`, `r_meas ~ 0`:

    dr from d(sf)     = (rho_eps - r_meas)/sf^2 * d(sf)   = 0.166 * 0.02 = 0.003
    dr from d(rho_eps)= (1-sf)/sf * d(rho_eps)            = 0.053 * 0.10 = 0.005
    total ~ 0.006 against a budget of 0.20

The conclusion is insensitive to the calibration parameters. That is the point
of choosing the conservative branch, and it is what makes B-1 worth its cost.

### 2.2 Why B-2 is set 26x tighter than the arithmetic requires

Budget A alone would tolerate `rho_eps <= 4.0` at `sf = 0.95`, which is not a
constraint at all since `rho_eps <= 1` by construction. B-2 is set at 0.15
anyway, for two reasons that are not about budget A:

1. `rho_eps -> 1` is the exact failure signature of `G-L98`. A run with
   `rho_eps = 0.9` would satisfy budget A and still be measuring the host
   rather than the network. B-2 is a MECHANISM check wearing a threshold.
2. `rho_eps` is contamination, not attenuation: it manufactures correlation
   from nothing rather than shrinking it. An error that can only make you
   miss an effect deserves a loose gate; one that can make you report an
   effect that does not exist does not.

⚠️ B-2 is only meaningful if `rho_eps` is measurable. `G.1` could not measure
it. If the G'.4 certificate again returns `NOT_IDENTIFIABLE`, B-2 is unmet and
cannot be waived by reinterpretation.

## 3. Estimator specification, frozen

    tau     log-linear ACF slope. Regress log ACF(k) on k over lags 1..8
            whose ACF exceeds the noise floor 2/sqrt(n), at least 4 lags;
            tau = -dt/log(phi_hat).
            Implementation: tools/measurement_path_calib.py:18
            estimate_nugget(...) -> "tau_from_fit_s".
            ★ Read the SLOPE ONLY. Do NOT gate on the function's `ok` flag.
              See section 3.1.
            Then divide by the signed b(tau) of section 4.

    sigma   sample standard deviation, ddof = 1.

    sf      exp(intercept) of the SAME fit. Used as an independent
            cross-check on the G'.4 certificate, never as its replacement.

    r       Pearson on rho_measured; CI95 by Fisher z with
            n_eff = n(1-phi^2)/(1+phi^2).

⚠️ Changing any line above voids this preregistration.

### 3.1 Why the `ok` flag must not gate the tau reading

`estimate_nugget` sets `ok = (0 < sf_hat <= 1)`. When the measurement path is
nearly clean, `sf_hat` scatters around 1 and lands above it about half the
time, so `ok` is false for a record that is not defective but merely cleaner
than the nugget model permits. `G-L21` and `G-L31` already record `sf_hat > 1`
as a model-class warning.

Simulation shows this is not merely data loss. At `sf_true = 1.00`,
`T/tau = 200`:

| tau | `ok` fraction | median of KEPT records | median of ALL records |
|---:|---:|---:|---:|
| 1 | 0.46 | 1.032 | 0.976 |
| 5 | 0.53 | 1.025 | 0.976 |
| 30 | 0.48 | 1.013 | 0.992 |

Conditioning on `sf_hat <= 1` discards about half the records NON-RANDOMLY and
moves the apparent bias from about `-2.4` percent to about `+2.5` percent. The
estimator then looks unbiased because of the selection, not despite it.

The nugget scales the ACF by a constant, so `sf` lands in the intercept and
`tau` comes from the slope. A record with `sf_hat > 1` has an uninterpretable
NUGGET and a perfectly valid TAU. The two readings are therefore taken as
separate decisions, and only the `sf` reading is gated on `0 < sf_hat <= 1`.

**G-L99:** a validity flag derived from one output of a joint fit must not be
used to gate a DIFFERENT output of the same fit. `estimate_nugget` reports
`ok` from the intercept (`0 < sf_hat <= 1`), and the intercept carries the
nugget; the slope carries `tau` and is unaffected by it. Gating `tau` on `ok`
therefore conditions on a quantity independent of the one being read, and
because `sf_hat > 1` becomes a coin flip as the measurement path approaches
clean, it discards about half of the best records non-randomly and inverts the
sign of the apparent bias.

Scope: this is a PROSPECTIVE constraint on how G-A017 reads the fit. It is not
a retrospective defect finding. `tools/g1_4_physical_reanalysis.py:181` already
reads `tau_from_fit_s` without consulting `ok`, and
`tools/g_a005_reclassification.py:147` classifies `sf > 1, v < 0` as
`OUTSIDE_PHYSICAL_DOMAIN_MODEL_CLASS_WARNING` rather than dropping it, which is
the correct handling. `tools/g_a003_split_sample.py:166` does gate on `ok`, but
gates the CALIBRATION reading, which is the output `ok` actually describes.

## 4. Run-length rule and the signed bias correction

    T_run = 205*tau   (200 analysed + 5 burn-in)
    dt    = min(0.2, tau/20)
    3 replicates; the gate reads the MEDIAN of the three
    grid: tau in {1, 3, 5, 10, 20} s

Signed bias factors `b(tau)`, from
`results/SMOKE/phase-G2/g1_bias_sim.json`, log-linear slope-only, `T/tau=200`,
`sf = 0.95`. The reported estimate is `tau_hat / b(tau)`.

| tau | dt | b(tau) | spread of b over sf in {1.00, 0.95, 0.90} |
|---:|---:|---:|---:|
| 1 s | 0.05 | 0.9754 | 0.0099 |
| 3 s | 0.15 | 0.9610 | 0.0182 |
| 5 s | 0.20 | 0.9795 | 0.0076 |
| 10 s | 0.20 | 0.9723 | 0.0160 |
| 20 s | 0.20 | 0.9816 | 0.0068 |

The spread column is itself a result: `b` moves by at most 0.018 while the
nugget goes from zero to `v = sigma^2/9`. The bias correction does not depend
on `sf`, which is the practical content of the nugget-immunity claim.

★ These factors are signed HERE, before any data. Measuring `b` after seeing a
result would be p-hacking in a subtle form.

## 5. Estimator bias simulation (NT 53)

Artifact `results/SMOKE/phase-G2/g1_bias_sim.json`, 54 cells, 600 trials each,
seed 20260905, produced by `tools/g1_estimator_bias_sim.py`.

Feasible cells, out of 18 `tau` x `T/tau` combinations per `sf` level. A cell
is feasible when the bias-corrected median of 3 replicates has both its 5th
and 95th percentile inside `+/-0.20`.

| `sf` | integral | log-linear, `ok`-gated | log-linear, slope-only |
|---:|---:|---:|---:|
| 1.00 | 0 | 11 | 9 |
| 0.95 | 0 | 9 | 9 |
| 0.90 | 0 | 10 | 10 |

By run length, slope-only, all `sf` pooled:

| `T/tau` | feasible |
|---:|---|
| 55 | **0 / 18** |
| 100 | 10 / 18 |
| 200 | **18 / 18** |

**Cells EXCLUDED from the signed grid, and why:**

- **All cells at `T/tau = 55`.** Zero of 18 feasible, at every `sf` including
  `sf = 1.00`, i.e. with a perfect measurement path. The inherited
  `T_run = 55*tau` rule cannot meet a 20 percent `tau` gate under any noise
  assumption. This is the single most consequential result of the simulation.
- **All cells at `T/tau = 100` except `tau in {20, 30}`.** Feasibility there
  depends on `sf`, which is not knowable in advance.
- **Every cell of the integral estimator, at every `T/tau` tested**, including
  200. Its bias-corrected p95 stays between 1.29 and 1.59.
- **`tau = 30 s`**, on campaign cost, not on feasibility. See doc 56 section 3.

**Cell admitted with a recorded reservation:** `tau = 1 s` is feasible in
simulation, but doc 56 section 2.2 shows its `sigma` window is only a factor
of 1.52 wide because `T-2` forces `dt = 0.05 s`. It is the canary cell.

## 6. Mutual satisfiability (G-L90)

`docs/phase-G/56-mutual-satisfiability.md`, artifact
`results/SMOKE/phase-G2/g1_mutual_sat.json`. Twelve pairs checked, zero empty
intersections. The checker reproduces the historical `EMIT-4` failure at
`4.261e-34`, matching doc 45.

**No gate in this preregistration is a tolerance-free boolean.**

## 7. What would falsify the mechanism

Kill test `G'.2`: with the kernel-enforced shaper at `omega = 0`, measure
`r_meas` across link pairs.

    PASS   |r_meas| <= 0.20
    FAIL   |r_meas| >  0.20

A FAIL means the common-mode term survived the move into the kernel, i.e. the
`G-L98` escape argument is wrong. **One diagnostic round is permitted. A
second failure stops Phase G'.**

This test is deliberately placed first. It is cheap, and it is the only
experiment whose negative result would make the remaining ones pointless.

## 8. Stop rules

- Maximum 2 rounds per lesson. `G'.2`: maximum 1 diagnostic round.
- Not negotiable: `B-1`, and the `G'.2` kill-test verdict.
- A threshold may not be widened from an observation it failed.
- Any change of estimator, `b(tau)`, or run-length rule voids this record and
  requires a new preregistration, a new commit and a new tag.

## 9. Referenced artifacts

| Artifact | SHA256 |
|---|---|
| `results/SMOKE/phase-G2/g1_bias_sim.json` | `e73310f51d6903a6d27ff4380c98eb1134d4f7babea0e1620a85c30c644657ea` |
| `results/SMOKE/phase-G2/g1_mutual_sat.json` | `cc104618a4adcef1e6f4dd939eb6dddf1ecfe306abfb944ecb4154ca591a02bd` |
| `tools/g1_estimator_bias_sim.py` | `df740ccb5aa8ad2030553db2965266b6774e42ee2d2e4c0eea0de2144810e7b8` |
| `tools/g1_mutual_satisfiability.py` | `ae74542cc770e77cdb0525f5f0db7043c232a0bcaa5601f3077de293ec08584f` |
