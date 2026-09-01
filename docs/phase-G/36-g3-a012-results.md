# G-A012 lag-corrected persistence dry-run results

Date: 2026-09-01 UTC. Verdict: **PASS 12/12**. Status:
`SYNTHETIC_NO_NETWORK`. No emitter, Mininet, OVS, or RAW network run was
started.

Source commit: `4ce510e992f71fe76fd9cf1faddde15210abb64d`.

## New gate

G-A012 generalized the independent-round sawtooth covariance to every lag and
subtracted its analytic contribution before estimating persistence from lags
two and three. `DRY-T-Q` observed a maximum corrected median tau bias of
`.067493`, below the inherited `.15` PC-G2-3 budget: **PASS**.

## Dangerous-cell estimators

The stress cell remains `sigma_ref(uA)=0.020232558139534878`, `tau=30 s`,
`n=30000`, 16 replicates and seed `20260906`.

| link | repo lag 1--2 | raw lag 2--3 | corrected lag 2--3 | corrected bias |
|---|---:|---:|---:|---:|
| uA | 25.076 | 27.686 | 27.975 | -6.75% |
| uB | 25.983 | 27.785 | 28.076 | -6.41% |
| ac | 20.044 | 25.548 | 29.497 | -1.68% |
| ad | 21.578 | 26.995 | 31.672 | +5.57% |
| bc | 21.064 | 25.558 | 29.483 | -1.72% |
| bd | 19.992 | 24.793 | 28.416 | -5.28% |
| vC | 25.698 | 27.904 | 28.194 | -6.02% |
| vD | 27.505 | 29.868 | 30.288 | +0.96% |

The actual repository estimator's lag-1--2 bias is substantially worse than
the originally reported lag-2--3 bias on the low-capacity links. Merely moving
to lags two and three helps but remains biased. Analytic nugget subtraction
brings every finite-sample median within 6.75% of truth.

At exact population moments, the two link classes give:

| step class | repo lag 1--2 | raw lag 2--3 | corrected lag 2--3 |
|---|---:|---:|---:|
| .323490 packet | 27.095 | 29.591 | 30.000 |
| .228742 packet | 20.713 | 25.888 | 30.000 |

This separates analytic correction from finite-sample ratio bias: the model
repair is exact at population moments, while the executed estimator is reported
with its real Monte Carlo spread.

## Full amended run

All prior G-A011 checks remained numerically stable:

- DRY-Q sign gate: minimum cell/link median `-.009681`, PASS;
- DRY-Q-PC packet-step error `.010558`, PASS;
- DRY-Q-B cumulative negative-control error `.002883`, PASS;
- DRY-O omega median error `.015784`, max SD `.036395`, PASS;
- DRY-T two-exponential mixture error `.016174`, PASS;
- DRY-D-PC analytic flip spread `.213436`, PASS.

## Artifact and verification

    results/SMOKE/phase-G/g3_dryrun_a012.json
    sha256 88efa9df2d3b93a57a871006c7fcd6f92c144820b4c4d756bd4510d0c17fbb24

Runtime was 24.44 s and maximum RSS was 76,496 KiB. The artifact records the
legacy and corrected estimator values for every link, plus exact-moment
controls. It authorizes only the next real-time emitter dry-run stage.
