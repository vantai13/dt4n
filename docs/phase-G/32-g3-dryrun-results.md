# G.3 NumPy dry-run results

Date: 2026-09-01 UTC. Verdict: **PASS 9/9**. Status:
`SYNTHETIC_NO_NETWORK`. No Mininet/OVS process was started and no RAW network
data was created.

The dry-run was preregistered at tag `phase-G-g3-dryrun-prereg`. Source commit
`6e168fc4` was fixed before execution. Runtime was 21.49 s and maximum RSS was
63,848 KiB.

## Gate results

| id | observed | gate | verdict |
|---|---:|---:|---|
| DRY-0 | analytic max error `2.22e-16` | `<=1e-12` | PASS |
| DRY-C | component clip .001483; aggregate clip .001083 | each `<=.01` | PASS |
| DRY-Q | max `abs(ACF1(eps_quant))=.074848` | `<=.10` | PASS |
| DRY-W | max `abs(ACF1(eps_path))=.053573` | `<=.10` | PASS |
| DRY-R | residual-correlation max error `.002228` | `<=.06` | PASS |
| DRY-O | max omega median error `.015784`; max SD `.036395` | each `<=.05` | PASS |
| DRY-T | two-exponential ACF max error `.016174`; monotone | `<=.05` | PASS |
| DRY-D-NC | kappa=1 flip spread `.010033` | derived bound `.054864` | PASS |
| DRY-D-PC | kappa=10 analytic flip spread `.213436` | `>=.10` | PASS |

DRY-Q is the closest gate but retains 25% relative headroom. This validates the
synthetic classifier and independent-window rounding implementation; it does
not pre-confirm the physical emitter, whose scheduler and counter path remain
the subject of the first G.3 run.

## Omega and time-scale round trip

| tau_p | tau_g | omega | median omega_hat | SD | median tau_eff, s | median P(flip) |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 3 | 0 | .002 | .036 | 2.99 | .327 |
| 3 | 3 | .25 | .257 | .036 | 2.90 | .331 |
| 3 | 3 | .50 | .493 | .036 | 2.94 | .323 |
| 3 | 3 | .75 | .753 | .024 | 3.00 | .333 |
| 3 | 3 | 1 | .991 | .018 | 2.90 | .332 |
| 30 | 3 | 0 | -.004 | .008 | 2.99 | .328 |
| 30 | 3 | .25 | .247 | .011 | 3.88 | .263 |
| 30 | 3 | .50 | .497 | .019 | 5.46 | .216 |
| 30 | 3 | .75 | .740 | .018 | 9.14 | .165 |
| 30 | 3 | 1 | .984 | .017 | 29.36 | .117 |

At kappa=1, tau_eff and P(flip) remain flat within sampling uncertainty while
omega is recovered. At kappa=10, persistence moves from the link endpoint to
the path endpoint and the pairwise stale-margin error falls monotonically in
the preregistered direction.

## What the dry-run caught before network work

The executed pipeline includes corrections absent from the initial proposal:

- measurement nugget is an eight-link vector read through the G.1 certificate,
  not one hardcoded scalar;
- quantisation residual and measurement-path residual are distinct;
- component rates are nonnegative and checked before aggregation;
- time-scale regimes are ordered pairs, avoiding an accidental tau_p=300 s;
- DEC-4 uses current CostV2 and removes deterministic baseline margin;
- full four-path argmin error remains explicitly deferred.

The baseline construction reconstructs mean load 0.857 analytically on every
link. A path baseline of `3.25*a0` leaves all private-link baselines positive.
The worst observed component and aggregate clipping fractions are both below
0.15%, so the stationary covariance is not being obtained through extensive
clipping.

## Artifact and scope

Artifact:

    results/SMOKE/phase-G/g3_dryrun.json
    sha256 015e5fde3efd21ebfeda1ae46d71b4f790323d6900362a69a2af3045d144a86a

The artifact sets `network_authorized_by_dryrun=true`. This means only that the
synthetic contract is internally feasible. Before a physical run, an emitter
must still be built with three aligned ledgers and the exact stop conditions in
`31-prereg-g3.md`. No physical G3-Q, G3-E, rho-epsilon, or paper endpoint has
been measured yet.

## Verification

Focused G.1/G.2/G.3 verification passed 85/85. The full repository suite
reported `1899 passed, 70 skipped, 13 deselected, 2 failed` in 10:41. The two
failures exactly reproduce the pre-existing baseline failures recorded during
the G.1/G.2 closeout:

- seven restored Phase-22 parquet files remain in `KNOWN_DANGLING`;
- the historical `g23-17c` report differs from its current canonical rebuild.

Neither failure imports or exercises a Phase-G decision-flow/dry-run module.
They are reported rather than changed because this task does not authorize a
rewrite of Phase-22 custody metadata or published Phase-23 numbers.
