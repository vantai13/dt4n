# AMENDMENT 7 -- Phase L / after campaign L.6

Campaign artifact:

```text
results/phase-L/campaign_state.json
```

## A7-1  Sentinel: clean machine, with one warm-up point

L.6 completed `728/728` points with `0` gate failures. The 23 sentinel points
use the same `h2, rho=0.90, bw=6, q=13, seed=999` schedule.

| sentinel set | n | mean ms | sd ms | CV |
|---|---:|---:|---:|---:|
| all sentinels | 23 | 10.8749 | 0.0122 | 0.112% |
| excluding first | 22 | 10.8733 | 0.0096 | 0.088% |

The first sentinel was `10.9109 ms`, which is `+3.92 sd` relative to the next
22 sentinels. This is a machine warm-up effect. The trend after that is
`-0.00078 ms/sentinel`, or `-0.017 ms` across the remaining campaign, only
`1.78 sd`.

Conclusion: the first 30 measured indices, about 4% of the campaign, may be
high by about 0.3%. This is too small to affect Phase L conclusions, but future
long campaigns should add a 10 minute machine warm-up before the first point.

## A7-2  Three-layer variance decomposition

At `bw=6, q=13, rho=0.90`:

| source | sigma ms | measurement |
|---|---:|---|
| machine noise | 0.0029 | `cbr`, 5 seeds, same schedule digest |
| repeat drift | 0.0096 | sentinel `h2` seed 999 repeated across 15.7 h |
| schedule draw | 0.2824 | `h2`, 5 different random schedules |

Ratios:

```text
sigma_schedule / sigma_repeat  = 29.4x
sigma_schedule / sigma_machine = 96.7x
schedule variance share        = 99.874%
```

Consequence: almost all single-run variation comes from which traffic schedule
was drawn, not from the measurement device. At alpha=0.10, the irreducible
single-run half-width floor is:

```text
1.645 * 0.2824 = 0.4646 ms
```

This is the theoretical floor for residual bands used downstream by Phase 21R.
If a future conformal width approaches this floor, the model is near optimal;
extra width beyond the floor is model error or conditioning error.

## A7-3  Signed prediction bias is real and small

For `h2, bw=6, q=13`, the pre-signed prediction curve is consistently below
the measured mean by about `+0.24 ms`. The sign is positive at every checked
rho. The bias is small relative to the curve in the high-load region and is
kept as a known reference-model bias, not patched after seeing the data.

Mechanism: packet-size offset accounts for about `+0.02 ms`; the remaining
`~0.22 ms` is a second-order token-bucket/model-shape error.

## A7-4  c_a is not sufficient

At `bw=6, q=13, rho=0.90`:

| mode | c_a mean | c_a sd | q mean ms | q sd ms | Reich mean ms |
|---|---:|---:|---:|---:|---:|
| cbr | 0.004 | 0.002 | 0.133 | 0.003 | 2.02 |
| poisson | 1.003 | 0.006 | 5.725 | 0.280 | 10.74 |
| h2 | 2.032 | 0.021 | 11.041 | 0.282 | 35.40 |
| onoff | 2.312 | 0.602 | 6.631 | 0.584 | 25.91 |

`onoff` has higher `c_a` than `h2`, but much lower delay. A model
`f(rho, c_a)` is therefore falsified by the L.6 data.

The Reich/Lindley workload order is:

```text
h2 > onoff > poisson > cbr
```

This matches the measured delay order, while `c_a` does not. The correlation
between mean Reich workload and measured delay across the four modes is
`r = 0.938`.

Action: keep the deployable model conditioned on traffic family:

```text
f(rho) per (mode, bw, q)
```

Do not replace it with `f(rho, c_a)`. A traffic-family-invariant model based on
Reich workload is future work, not part of L.7.

## A7-5  Provenance and gates

All L.6 rows passed the operational gates:

```text
rows completed        728/728
gate failures         0
socket_drops          0 on every row
n_foreign             0 on every row
max |rate_ratio - 1|  8.15e-05
```

`probe_pps=0` control rows are not mixed into model fitting. They remain a
separate control for probe intrusiveness. The raw binary data remains outside
git; `tools/raw_manifest.py` pins the bytes used for the offline fit.

## A7-6  L.7 modeling note

The CBR curve has a sharp critical transition near `rho=1.00`; held-out
interpolation at `rho=0.98` is not a fair smooth-curve test for that mode.
L.7 therefore gates CBR prediction by subcritical held-out RMSE for
`rho <= 0.90`, while the final PCHIP model still includes the measured critical
nodes `0.98, 1.00, 1.02, 1.05`.

For stochastic modes (`poisson`, `h2`, `onoff`), the held-out interpolation
gate remains `R2 >= 0.90`.
