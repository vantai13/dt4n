# NC-G1-static v2 smoke — mechanism correction works, advancement blocked

Date: 2026-08-30 UTC.

## Verdict

The mandatory no-Mininet cost gate passed, and all six 60-second v2 network
cells completed. Nevertheless every cell is INVALID under the signed gates,
so the 300-second campaign and dt axis were not run.

This is not a rerun of the v1 failure. V2 removed the spin artifact and the
wrong white-noise null: 45/48 link-runs are QUANT_LIMITED, the remaining three
are MIXED only because ACF(1) is slightly below the locked -0.80 bound, and
48/48 pass the no-slow-component gate. The blocker is instead G1S2-1:
independent-clock offered variance is 11.3%--94.6% of measured variance, so
zero of 48 links pass the locked 10% share.

## Cost and infrastructure

The pre-network cost gate ran eight emitters for 30 seconds:

| quantity | result | gate |
|---|---:|---:|
| CPU p50 | 6.637% | diagnostic |
| CPU p95 | 14.094% | <25% PASS |
| emitter exit codes | 8/8 zero | PASS |
| swap / drops | 0 / 0 | PASS |

Network smoke CPU p95:

| cell | v1 CPU p95 | v2 CPU p95 | QUANT_LIMITED | no-slow links | final |
|---|---:|---:|---:|---:|---|
| A | 95.460% | 71.151% | 8/8 | 8/8 | INVALID |
| B | 90.559% | 50.139% | 8/8 | 8/8 | INVALID |
| C | 86.836% | 40.165% | 7/8 | 8/8 | INVALID |
| D | 77.062% | 19.220% | 7/8 | 8/8 | INVALID |
| E | 83.669% | 29.338% | 8/8 | 8/8 | INVALID |
| F | 86.347% | 38.741% | 7/8 | 8/8 | INVALID |

Batch pacing therefore removes the generator's reflexive CPU load: the clean
cell D falls by about fourfold and passes the v2 40% boundary. Cells A and B
remain beyond that boundary due to their telemetry configuration; C misses by
0.165 percentage point. The signed gate is not rounded or relaxed.

## Why the independent offered gate fails

All 48 links pass the direct stall diagnostic (`lag_p95<=0.02 s` and maximum
ledger gap <=0.05 s), but all fail offered share:

| cell | offered-share range | flat links | stall-clean links |
|---|---:|---:|---:|
| A | 0.178--0.946 | 0/8 | 8/8 |
| B | 0.113--0.839 | 0/8 | 8/8 |
| C | 0.266--0.873 | 0/8 | 8/8 |
| D | 0.286--0.742 | 0/8 | 8/8 |
| E | 0.344--0.804 | 0/8 | 8/8 |
| F | 0.352--0.755 | 0/8 | 8/8 |

The independent clock is doing what it was designed to do: it sees the real
window-to-window packet-count residual. When the counter is quantization
limited, the same packetization must also dominate measured variance. Thus
`offered_share<=0.10` and `QUANT_LIMITED` cannot generally both hold. This is
now G-L43. The v2 result is retained rather than post-hoc subtracting or
redefining the denominator.

A future design must directly form a same-grid residual between counter bytes
and offered packets, with link-layer bytes-per-packet fixed independently.
Only the variance of that residual can be called measurement-path nugget.

## Correlation outcomes remain inconclusive

After removing spin, the v1 near-one uA-uB pattern disappears:

| cell | rho(uA,uB) TX | rho(vC,vD) TX |
|---|---:|---:|
| A | -0.052 | -0.036 |
| B | 0.078 | 0.057 |
| C | 0.061 | -0.026 |
| D | 0.012 | 0.095 |
| E | -0.046 | 0.141 |
| F | 0.052 | 0.094 |

This supports G-L38's diagnosis that the v1 high correlations were dominated
by shared CPU stalls. It does not certify H6b or H6c because every v2 cell is
invalid.

Same-link s0/s1 correlations range from -0.658 to 0.599. The signed phase
offset causes the two samplers to measure different half-shifted packet-count
windows, whose conservation residual can itself be anti-correlated. Therefore
the preregistered low-correlation label cannot identify read-layer noise on
this invalid run; G-L44 records the required same-support/analytic-null fix.

## Provenance and artifacts

- V2 prereg commit/tag: `02fa6049`,
  `phase-G-g1-static-nc-v2-prereg`.
- Mechanical executable-mode commit: `f5a764eb`.
- Post-burn interval alignment correction before reading outcomes:
  `9c8ca857` (the original failure was only a pre-burn ledger-start boundary).
- Compact result:
  `results/SMOKE/phase-G/g1_static_v2_smoke_cert.json`.
- Full detail:
  `results/SMOKE/phase-G/g1_static_v2_smoke_detail.json`.
- Raw local custody: 225 files, about 24 MiB under
  `results/RAW/phase-G/g1-static-v2-smoke/`.

No v2 certificate is written to `results/LIVE`. The next permissible work is
a separately preregistered same-grid byte-residual control, not the locked full
v2 campaign.
