# Phase G.0 preregistration — packet-level sigma/tau orthogonality

Signed before running `tools/g0_roundtrip.py`.  The feasibility and estimator
bias simulations are design diagnostics with synthetic ground truth; they do
not contain experimental outcomes.

## Locked implementation and constants

- Generator: normalized AR(1), `phi = exp(-dt/tau)` and innovation scale
  `sqrt(1-phi^2)`.
- Packet quantization: independent `round()` per window; no carry accumulator.
- `C = 8 Mbps`, `rho_bar = 0.857`, `rho_max = 0.995`, payload `L = 1400 B`.
- `dt = tau/10`, packet-floor headroom at least 5.
- Seeds: 16 per feasible cell, `seed = 20260901 + 1000*i`, `i=0..15`.
- Duration: `T_run = 200*tau` after the signed-estimator diagnostic measured
  `P(pass +/-20%) = 0.960`, the smallest tested factor at or above 0.95.
- Estimator: integral ACF time scale, stopped at first non-positive ACF,
  `nlag = n//4`.

## Feasible grid locked before the round trip

The design diagnostic found 12/20 feasible cells.

- Included: `(sigma,tau)` = `(0.01,{3,10,30})`,
  `(0.03,{1,3,10,30})`, and `(0.05,{0.5,1,3,10,30})`.
- Excluded by packet headroom: `(0.01,0.5)`, `(0.01,1)`, `(0.03,0.5)`.
- Excluded by the clipping-headroom design gate: every `sigma=0.10` cell,
  because `0.857 + 2.58*0.10 > 0.995`.

This differs from the prose supplied with the implementation, which counted
only the three packet-headroom exclusions.  The round trip must consume this
feasibility artifact and must not run excluded cells.

## Locked gates

- G0-0: only cells marked feasible by `g0_feasibility.json` may run.
- G0-1: `abs(median16(tau_hat_offered)/tau - 1) <= 0.20` in every cell.
- G0-1b: at every tau with at least two feasible sigma values, the spread of
  `median16(tau_hat_offered)/tau` across sigma is at most 0.05.  Tau 0.5 has
  only one feasible sigma and is reported as `NOT_EVALUABLE`, not silently
  counted as a pass.
- G0-2: `abs(median16(sigma_hat_offered)/sigma - 1) <= 0.10` in every cell.
- G0-3: p95 clip fraction across seeds is at most 0.01 in every cell.
- G0-4: sigma/quantization-floor headroom is at least 5 in every cell.
- G0-5: empirical signal fraction differs from the analytic value by at most
  10% relative in every cell.
- G0-6: report median, p05, and p95 across all 16 seeds.
- G0-7: the synthetic G.0 workflow requires no root and should finish in less
  than 10 minutes.

Overall PASS requires all per-cell gates and G0-1b at all evaluable tau levels.
Coverage limitations remain visible in the artifact and are not converted
into evidence.

## Design-diagnostic receipt

`results/SMOKE/phase-G/g0_estimator_bias.json` measured:

| T/tau | median-8 median | p05 | p95 | P(pass +/-20%) |
|---:|---:|---:|---:|---:|
| 55 | 0.868 | 0.732 | 1.138 | 0.715 |
| 100 | 0.953 | 0.762 | 1.170 | 0.875 |
| 200 | 0.971 | 0.823 | 1.145 | 0.960 |
| 400 | 0.985 | 0.909 | 1.117 | 0.995 |
| 800 | 1.002 | 0.917 | 1.104 | 1.000 |

The preregistration tag is `phase-G-g0-prereg`.  It must point to the commit
containing this document, the generator, all three tools, and the two design
diagnostic artifacts, before `g0_roundtrip.py` is first executed.
