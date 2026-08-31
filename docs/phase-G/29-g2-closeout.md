# G.2 closeout — physically wireable omega axis

Date: 2026-08-31 UTC. Verdict: **PASS for analytic and synthetic design**.
Status: `SYNTHETIC_NO_NETWORK`; no Mininet or OVS process was started and no
RAW network measurement was created.

## Outcome

The physical path-rate parameterisation

    a   = a0*sqrt(omega)
    b_l = a0*sqrt((1-omega)*d_l)/C_l

preserves each link's variance while producing
`r_lm=omega*k_topo`. Topology is imported from `twin.topology_v7`; it gives 12
structured pairs, 16 null pairs, and `sum(k_topo^2)=4.999999999999999`.

Unlike the older link-normalised analytic construction, a path process has one
bit/s amplitude along its entire route. The resulting sigma is a vector:

| link | uA | uB | ac | ad | bc | bd | vC | vD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| sigma at the anchor | .0303 | .0405 | .0286 | .0429 | .0286 | .0286 | .0303 | .0405 |

The spread is exactly 1.5x. The campaign control is therefore `a0` (bit/s),
not a single scalar sigma.

## Algebra and controls

The successful run used source commit `69526dcc` and completed in 12.13 s
(maximum RSS 123,844 KiB).

| check | observed | verdict |
|---|---:|---|
| `ALG-G2-1`, sum k squared | 5.000000 | PASS |
| `ALG-G2-2`, omega=1 | max error `2.22e-16` | PASS |
| `ALG-G2-3`, linear omega law | max error `2.22e-16` | PASS |
| `INV-G2-1`, variance invariant | max error `2.17e-19` | PASS |
| `PC-G2-1`, old fixed-a model fires | ratio 2.000 | PASS |
| `NC-G2-1`, identity recovers zero | 0 | PASS |
| `NC-G2-2`, 16 null pairs stay zero | 0 | PASS |
| `PC-G2-2`, 120-seed round trip | max bias .0105; max SD .0363 | PASS |
| `INV-G2-2`, normalized lag covariance | max error `1.11e-16` | PASS |

The estimator uses `<r,k>/<k,k>`. Null pairs have zero LS weight because
`k=0`; they remain useful as explicit negative controls for common-mode or
other unmodelled correlation.

## Failed first tau gate and cause

The first algebra execution was deliberately not hidden. Its artifact version
is preserved at commit `21e2d596`; it failed the fixed
`tau_hat`-spread threshold with 0.05875 > 0.05. The omega gates already passed.

The cause was a contrast error: five independent finite-sample medians were
being used to test an exact marginal invariant. A post-failure null diagnostic
placed 0.05875 below the tau=10 p99 of 0.06281, while the model itself proves
`ACF_l(k)=exp(-k*dt/tau)` for every omega. Amendment
`28a-g2-amendment-tau-gate.md` therefore replaced that stochastic gate with
the exact lag-covariance identity. The observed spread 0.05875 and absolute
tau bias 0.04700 remain reported and were not converted into passes.

## Feasibility from the pinned G.1 certificate

The loader verified that measurement digest
`bb885be28cd29396a4705f6ac6499bc06d59d6d0f735c8823b8b546fdb15d52c`
is pinned by the conditional LIVE certificate. The three constraints were
then applied to each of eight links, not to a scalar surrogate.

| mode | rho_bar | closed-form a0 window (bit/s) | grid result |
|---|---:|---:|---|
| independent round | .8570 | [83,254, 213,953] | first two feasible; high cell clips uB/ad/vD |
| independent round | .9195 | [83,254, 117,054] | only low cell feasible |
| cumulative mixed robustness | .8570 | [117,739, 213,953] | only middle cell feasible |
| cumulative mixed robustness | .9195 | [117,739, 117,054] | empty window |

Total: **4/12 feasible cells**. At `rho_bar=.857`, the middle anchor
`sigma_ref(uA)=0.0303488372`, `a0=171,679 bit/s`, is the only grid point
feasible under both quantisation models. For the low cell in cumulative mode,
all four core links `ac/ad/bc/bd` fail headroom together. Capacity cancels from
this ratio; degree, not the 4 Mbps `ad` link alone, determines that floor.

The cumulative mode is correctly named `cumulative_mixed`; it is a robustness
counterfactual and does not override G.1's deployed `independent_round` scope.

## Run-length result

The run took 22.62 s (maximum RSS 39,508 KiB). All directly simulated
`T=200*tau` cells met `sd(omega_hat)<=.05`. The scaled-constant spread was
1.185x, below the shape-matched null p95 1.211x.

| summary | c | required T/tau | safety versus 200tau |
|---|---:|---:|---:|
| central median | .489 | 95.6 | 2.09x |
| conservative observed envelope | .523 | 109.3 | 1.83x |

The central estimate differs slightly from the draft expectation 94tau/2.13x
because the executed batch preserves a different deterministic RNG ordering.
The conservative envelope was preregistered before execution and is the budget
decision: `109.3 < 200`, so the G-A001 duration remains sufficient.

## Artifacts

| file | SHA-256 |
|---|---|
| `results/SMOKE/phase-G/g2_omega_algebra.json` | `ae72d0b07855b9a1f638e7e8594b3caa302def00b90b48890d55bfb0bf830e01` |
| `results/SMOKE/phase-G/g2_feasibility_omega.json` | `550f043afdd6da7246b0cbad06778401e116f55d6fe3c93224d49a1d31484795` |
| `results/SMOKE/phase-G/g2_runlength.json` | `132f09dd47e9eed900dcdb7372e0d39cf302a232241ba0ccbe56eed338836725` |

Focused verification passed 25/25 G.2 tests and 30/30 existing link-correlation
tests. Two extra G.2 tests, beyond the draft's 18, enforce the G.1 certificate
hash contract; five more parameterized cases lock the amended temporal
invariant.

## Scope boundary

G.2 proves that the axis is internally exact and identifies reachable design
cells. It does not prove that Mininet realises the covariance, does not measure
physical omega, and does not resolve G.1's deferred cross-link residual. Those
claims require the G.3 network experiment and its first-run quantisation check.
