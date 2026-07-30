# AMENDMENT 9 -- Phase L / regime reliability audit

Artifact:

```text
results/phase-L/link_model_v2_fit.json
docs/phase-L/07-fit.md
```

## A9-1  A8-3 was directionally right, slightly optimistic

The LOO-CV patch in Amendment 8 turned `efficiency` from an identity into a
measurement. The signed prediction was right in direction and order of
magnitude, but a little optimistic:

| group | A8-3 signed expectation | measured after patch | read |
|---|---:|---:|---|
| h2, poisson | 0.97 to 0.999 | 0.94 to 0.98 | slightly lower, same conclusion |
| cbr | 0.30 to 0.70 | 0.18 to 0.43 | lower, same critical-wall conclusion |
| sentinel OOS | abs(diff) < 2 sigma | -0.59 sigma | PASS |

The important change is qualitative: efficiency now spans `0.18` to `0.98`.
It is no longer the tautology `1.0000000`.

## A9-2  CBR grouped efficiency hides two regimes

For `cbr|6|13`, the local LOO table is:

```text
rho       0.50   0.60   0.70   0.80   0.85   0.90   0.925  0.95   0.98   1.00    1.02   1.05
sigma     .004   .003   .006   .005   .005   .003   .008   .009   .080   7.377   .028   .034
bias     +.000  +.000  -.000  +.000  +.000  +.000  +.000  +.004 +1.566 +7.331 -12.958 -.487
```

Splitting the band by regime gives:

| regime | rho used | n | noise rms ms | bias rms ms | sd cv ms | efficiency | conclusion |
|---|---|---:|---:|---:|---:|---:|---|
| subcritical | 0.60, 0.70, 0.80, 0.85, 0.90, 0.925, 0.95 | 35 | 0.0055 | 0.0015 | 0.0063 | 0.872 | model bias is negligible |
| critical | 0.98, 1.00, 1.02 | 30 | 4.1099 | 8.6431 | 9.6060 | 0.428 | model bias dominates |
| grouped interior | 0.60 through 1.02 | 65 | 2.7666 | 4.7340 | 6.5019 | 0.426 | hides both facts |

The grouped `0.426` is misleading in the same way a grouped sigma was
misleading: it makes the CBR model look globally bad. The better statement is:

```text
CBR is reliable below rho <= 0.95.
CBR point prediction is not reliable for 0.95 < rho < 1.05.
```

The large error is not a generic fit failure. At `rho=1.02`, leave-one-out
removes the only node that resolves the jump. The nearest remaining nodes are
`rho=1.00` near `1 ms` and `rho=1.05` near `25 ms`, so the interpolator predicts
the middle of a step it cannot see. This is a grid-resolution limit exactly at
the A6-2 critical region.

## A9-3  Gate and report change

`G-L7c` now reports both:

```text
grouped LOO-CV efficiency
regime LOO-CV efficiency:
    subcritical_rho_le_0.95
    critical_rho_ge_0.98
```

The grouped value is retained for audit continuity, but it must not be used as
the scientific conclusion for CBR.

The new gate field is:

```text
G-L7c_regime_decomposition_present_pass = True
```

## A9-4  Handoff contract change

`LinkModelV2` now exposes:

```python
m.is_reliable(mode, bw, q, rho) -> bool
```

Runtime rule:

```text
mode == "cbr" and 0.95 < rho < 1.05  =>  False
otherwise inside measured domain      =>  True
```

Phase 20R must treat that CBR interval as a special region. It may use measured
nodes as descriptive data, but it must not silently consume point predictions
there as ordinary reliable link estimates.

## A9-5  ON/OFF threshold note

`onoff|6|13` has its own unresolved threshold:

```text
rho       0.70     0.80
delay     0.140    1.909 ms
sigma     0.004    0.627 ms
bias     +0.465   +0.281 ms
```

The sigma jump is about `140x`, and the `rho=0.70` leave-one-out bias is larger
than the local signal. This suggests the ON/OFF threshold is around `rho ~= 0.75`
and is under-resolved by the current grid.

Action: record this limitation, but do not block ON/OFF predictions yet. Unlike
CBR, ON/OFF has high stochastic variance after the threshold and does not show
the same narrow deterministic step at `rho ~= 1`.
