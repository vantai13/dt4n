# PHASE L -- GATE DECISION

Date: 2026-07-30

Commit for last completed input before this gate document: `81159ec`

Final tag target: `phase-L-done` after user sign-off.

Prerequisite: `docs/phase-L/00-preregistration.md`.

Amendments: `00b` through `00i` (8 amendments). Each amendment records what
was observed before changing the plan.

## 1. Question

How do delay and loss on a shaped single link depend on offered load, when the
queue is measured directly instead of inferred from backlog identities?

## 2. Audited Starting Assumptions

The old model failed for structural reasons:

| item | audit result |
|---|---|
| A1 | backlog = rho x BDP was Little's-law tautology, not a measurement model |
| A2 | link_model v1 assigned a fake slope to what was essentially a constant |
| A3 | the apparent cliff was rho_measured touching 1.0 |
| A4 | `OVERHEAD_FACTOR = 1.0790` was Ethernet framing plus iperf accounting |
| A5 | the actual flow-engine `c_a` was about 0.072, not 1.5 |

L.7 added a second audited tautology: in-sample PCHIP residuals made
`efficiency == 1` by definition. Amendment 8 replaced them with
leave-one-rho-out residuals.

## 3. Measurement Infrastructure

| item | result |
|---|---|
| V-L0 noise floor | mean 0.1453 ms, SD 0.1186 ms, PASS under 0.2 ms |
| V-L1 qdisc split | HTB on measured direction, BFIFO limit exact, netem only on return, PASS |
| V-L1 hidden queues | host/switch interfaces noqueue, `direct_packets_stat = 0`, PASS |
| V-L2 zero-load OWD | HTB at zero load equals software floor, not 1/bw serialization, PASS |
| V-L2b token bucket | max error k>=3: 0.0435/0.0398/0.0623 ms at 8/6/4 Mbps, PASS |
| V-L4 positive controls | cbr < poisson < h2 at rho=0.90, PASS |
| V-L4 buffer control | q=5/q=13 backlog ratio = 0.385 = 5/13, PASS |
| V-L7 probe intrusiveness | max deviation <=20 pps = 1.46%, PASS |

Serialization delay is not charged by Mininet per packet in the measured
direction. Phase 20R must add known serialization analytically.

## 4. Campaign

Artifact:

```text
results/phase-L/campaign_state.json
```

| item | value |
|---|---:|
| completed points | 728/728 |
| gate-fail rows | 0 |
| socket drops | 0 on every row |
| foreign packets | 0 on every row |
| max abs(rate_ratio - 1) | 8.15e-05 |
| sentinel points | 23 |
| phase-L tests | 90 passed |
| full test suite | 172 passed, 4 skipped |

Sentinel `h2|6|13|rho=0.90|seed=999`:

| set | n | mean ms | sd ms | CV |
|---|---:|---:|---:|---:|
| all | 23 | 10.8749 | 0.0122 | 0.112% |
| excluding first | 22 | 10.8733 | 0.0096 | 0.088% |

The first sentinel is a warm-up outlier (`+3.92 sd` relative to the next 22).
The remaining trend is only `-0.017 ms` across the campaign (`1.78 sd`).

![Sentinel control chart](figures/l7_sentinel_control.svg)

## 5. Main Variance Result

At `bw=6, q=13, rho=0.90`:

| source | sigma ms | ratio |
|---|---:|---:|
| machine noise | 0.0029 | 1x |
| repeat drift | 0.0096 | 3.3x machine |
| schedule draw | 0.2824 | 96.7x machine, 29.4x repeat |

Schedule realization explains `99.874%` of the measured single-run variance.
At alpha=0.10, the irreducible half-width floor is:

```text
1.645 * 0.2824 = 0.4646 ms
```

This is the floor Phase 21R should compare conformal width against.

## 6. Traffic-Family Result

At `bw=6, q=13, rho=0.90`:

| mode | c_a mean | q mean ms | Reich mean ms |
|---|---:|---:|---:|
| cbr | 0.004 | 0.133 | 2.02 |
| poisson | 1.003 | 5.725 | 10.74 |
| h2 | 2.032 | 11.041 | 35.40 |
| onoff | 2.312 | 6.631 | 25.91 |

`onoff` has higher `c_a` than `h2`, but much lower delay. Therefore
`f(rho, c_a)` is rejected. The deployable model remains conditioned on
traffic family: one curve per `(mode, bw, q)`.

Reich workload tracks delay across the four modes with `r = 0.938`, but a
Reich-conditioned invariant model is future work.

## 7. link_model_v2

Artifact:

```text
results/phase-L/link_model_v2_fit.json
twin/link_model_v2.py
docs/phase-L/07-fit.md
```

Model split:

| component | role | result |
|---|---|---|
| Kingman with ceiling | explanation | R2 range 0.6831 to 0.9632; not the deployment predictor |
| monotone PCHIP | prediction | predictive gate 10/10 PASS |
| local sigma(rho) | normalized conformal scale | exported and reported |
| LOO-CV residuals | honest residual band | Amendment 8 |

L.7 gates:

| gate | result |
|---|---:|
| G-L7a predictive | 10/10 PASS |
| G-L7b monotone | 10/10 PASS |
| G-L7c efficiency | mean 0.7653, min 0.1835, max 0.9779 PASS |
| G-L7d sigma exported | PASS |
| G-L7e rho=1.05 marked extrapolated | PASS |
| G-L7f sentinel OOS | diff -0.1662 ms, z -0.59 PASS |

Band decomposition:

| family | efficiency range | read |
|---|---:|---|
| cbr | 0.184 to 0.426 | model bias dominates at the critical wall |
| h2 | 0.958 to 0.978 | near noise floor |
| poisson | 0.941 to 0.969 | near noise floor, small interpolation bias |
| onoff | 0.937 | good, but less smooth than h2/poisson |

The largest `sigma_max/sigma_min` ratio is `2525x` on `cbr|6|13`, so
Phase 21R must use normalized nonconformity scores.

![Delay curves](figures/l7_ref_curves.svg)

![Local sigma curves](figures/l7_ref_sigma.svg)

![Band decomposition](figures/l7_band_decomposition.svg)

## 8. Decision

Phase L status:

```text
PASS -- hand off link_model_v2 and its local residual band to Phase 20R/21R.
```

The pass is conditional only on the normal release step: cut `phase-L-done`
after this gate document is committed and reviewed.

## 9. Handoff API Contract

Use:

```python
from twin.link_model_v2 import LinkModelV2

m = LinkModelV2.load("results/phase-L/link_model_v2_fit.json")
m.predict_delay(mode, bw, q, rho)  # mean queueing delay in ms
m.predict_loss(mode, bw, q, rho)   # loss ratio
m.sigma(mode, bw, q, rho)          # local residual scale
m.domain(mode, bw, q)              # [0.50, 1.05], strict by default
m.irreducible_floor_ms(mode, bw, q)
m.model_efficiency(mode, bw, q)
```

Total one-link delay for Phase 20R:

```text
total_delay_ms =
    base_delay_ms
  + frame_bytes * 8 / bw_bps * 1000
  + link_model_v2.predict_delay(mode, bw, q, rho)
```

Do not use the v1 formula `base + base * rho`; it was a tautology-backed
surrogate, not a measured queueing model.

Phase 21R conformal contract:

```text
s_i  = |y_i - f(x_i)| / sigma(x_i)
band = f(x) +/- q_hat * sigma(x)
```

Report `(average conformal half-width) / irreducible_floor_ms`. Values near 1
mean the model is close to the noise floor; excess width is model or
conditioning error.

## 10. Threats to Validity

| item | limitation |
|---|---|
| L1 | Mininet does not charge per-packet serialization in the measured direction; add it analytically |
| L2 | Guarantees are conditional on the traffic family; matching `c_a` alone is insufficient |
| L3 | Mean queueing delay is additive; path quantiles are not additive |
| L4 | CBR at rho near 1.0 is singular, with slow relaxation and nonconvergent-looking sample means |
| L5 | ON/OFF normalization intentionally removes slow mean-rate drift while retaining short-scale burstiness |
| L6 | The pre-signed reference model has a small systematic +0.24 ms bias at h2 bw=6 |
| L7 | Probe 20 pps changes the measured delay by up to 1.46% at the reference point |
| L8 | The first about 4% of the long campaign shows a small warm-up effect |

## 11. Reproduction

Core commands:

```bash
cd /home/ubuntu/dt4n
python3 -m measurements.l7_fit
pytest test/test_phase_l_*.py -q
pytest test/ -q
```

Expected test results for this gate:

```text
90 passed
172 passed, 4 skipped
```

Raw-data manifest:

```text
results/phase-L/raw/MANIFEST.sha256.json
n_files     3386
total_bytes 977837824
archive DOI not assigned yet
```

The raw binary files are intentionally not committed to git. The manifest pins
their SHA-256 digests for archive upload.
