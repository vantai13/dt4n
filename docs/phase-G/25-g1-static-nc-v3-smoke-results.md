# NC-G1-static v3 smoke — paired-window regression is not identifiable

Date: 2026-08-30 UTC.

## Verdict

**INVALID: 0/9 runs valid.** All six A--F cells and the independent cell-D
`dt={0.2,0.5,1.0}` axis completed after preregistration, but every run failed
the byte-per-packet, background, residual-SD, and observed-alignment campaign
requirements at least once. The dt positive control failed on 5/8 links.
Therefore no LIVE certificate was issued and the 300-second x 3-repetition
campaign remains blocked.

This is an informative model failure, not evidence about `v_path` or
`rho_path`. Those fitted outcomes are retained for audit but are not interpreted
because their residual definition failed its own calibration gates.

## Pre-network and runtime receipts

The no-Mininet 2-ms-ledger cost gate passed: CPU p50 9.550%, p95 17.276%
(<25%), eight exit codes zero, zero swap and network drops. The network runs
all had the v3 tag in their ancestry, two sampler files, clean ledger stall
checks, and sampler read error below the signed limit.

| cell | dt (s) | CPU p50 | CPU p95 | final |
|---|---:|---:|---:|---|
| A | 0.2 | 25.694% | 52.540% | INVALID |
| B | 0.2 | 16.613% | 41.099% | INVALID |
| C | 0.2 | 11.950% | 40.292% | INVALID |
| D | 0.2 | 4.550% | 19.212% | INVALID |
| E | 0.2 | 12.412% | 29.088% | INVALID |
| F | 0.2 | 13.419% | 33.118% | INVALID |
| D_dt_0p2 | 0.2 | 8.000% | 18.769% | INVALID |
| D_dt_0p5 | 0.5 | 4.662% | 17.336% | INVALID |
| D_dt_1p0 | 1.0 | 4.775% | 17.479% | INVALID |

A, B, and C also fail the unchanged CPU p95 <40% boundary. The other six
runs demonstrate that the paired-regression failure persists without that
infrastructure failure.

## Gate audit

| run-level gate | pass |
|---|---:|
| engine and two samplers | 9/9 |
| fitted bytes per packet | 0/9 |
| fitted background | 0/9 |
| residual SD | 0/9 |
| residual ACF(1) | 3/9 |
| infrastructure | 6/9 |
| prereg ancestry | 9/9 |
| nominal alignment | 9/9 |
| observed alignment | 0/9 |
| no ledger stall | 9/9 |
| sampler read timing | 9/9 |

Across 72 link-runs, `B_hat` ranges from -986.336 to 1205.870 bytes and none
passes `abs(B_hat-1442)<=4`. The fitted intercept ranges from 23,010 to
1,035,645 bytes/window and none passes its background gate. Only 25/72 pass
the residual-SD gate, 66/72 pass the residual-ACF gate, and 0/72 pass the
observed maximum alignment gate.

The nominal alignment value is 0.657--1.128 packets, but the observed maximum
ledger gap is 4.015--15.751 ms, corresponding to 1.585--7.717 packets. Thus a
2-ms requested write interval is not a hard scheduling bound.

## Why the regression fails despite correct byte accounting

Cell D exposes the identification failure cleanly. Per-window `delta_N` has
only 2--4 distinct values and SD 0.247--0.628 packet, while the conservative
observed alignment uncertainty is larger. Its correlation with counter bytes
ranges from -0.470 to 0.803 depending on deterministic boundary phase. With an
intercept present, OLS assigns the large mean byte count to `c` and estimates
`B` almost entirely from this tiny, misaligned variation.

This does not mean the physical byte total is unknown. Over the full post-burn
interval, `sum(M)/sum(delta_N)` is 1441.924--1442.087 bytes/packet in cell D.
Across the independent dt runs the ranges are:

| run | aggregate byte/packet range |
|---|---:|
| D_dt_0p2 | 1442.003--1442.091 |
| D_dt_0p5 | 1441.919--1442.081 |
| D_dt_1p0 | 1441.916--1442.124 |

The aggregate accounting confirms 1442; the signed per-window OLS cannot
identify it. This result allocates G-L51: a deterministic CBR regressor with
near-zero window excitation cannot simultaneously calibrate `B`, estimate an
intercept, and define a path residual when boundary uncertainty exceeds the
regressor variation. A future design must calibrate `B` on an independently
identified cumulative horizon or introduce preregistered excitation, then
apply that calibration to window residuals. It may not replace this failed
fit post hoc.

## dt positive control

Observed `v_measured(0.2)/v_measured(0.5)` and
`v_measured(0.5)/v_measured(1.0)` pass the signed factor-two bands on only
`uB`, `ac`, and `ad` (3/8 links). The remaining five fail. Because all three
dt runs are already INVALID under the calibration and alignment gates, this
does not adjudicate the packetization law; it only rejects advancement.

The G.0 cross-phase table remains as preregistered: dt 0.2 admits tau
`{3,10,30}`, while dt 0.5 and 1.0 admit only `{10,30}` under `tau/dt>=10`.

## Provenance and artifacts

- Prereg commit/tag: `8254d632`,
  `phase-G-g1-static-nc-v3-prereg`.
- Cost receipt: `results/SMOKE/phase-G/g1_static_v3_cost_gate.json`.
- Compact result: `results/SMOKE/phase-G/g1_static_v3_smoke_cert.json`,
  SHA-256 `272364e0d37674328f9f2e37533f96a23613777d3872dc4ad6aad332905039cf`.
- Full detail: `results/SMOKE/phase-G/g1_static_v3_smoke_detail.json`,
  SHA-256 `f8cd1037263d80b03ac62c0985327d1163b2f7395019906162d38249b2ad175d`.
- Raw local custody: 336 files, about 159 MiB under
  `results/RAW/phase-G/g1-static-v3-smoke/`.

No v3 artifact is written under `results/LIVE`.
