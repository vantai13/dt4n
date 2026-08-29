# Phase G.0 result — packet-level sigma/tau round trip

Run date: 2026-08-29 UTC.  The first round trip ran after annotated tag
`phase-G-g0-prereg` at commit `4156a56067320c80fae6e1be4b83550e5e668efd`.
The artifact records that preregistration commit as its provenance hash.

## Commands and environment

The system `python` did not contain NumPy, so all numeric commands used the
repository's existing `sdn_net` Conda interpreter (Python 3.9.25, NumPy 2.0.2).

```text
/home/ubuntu/miniforge3/envs/sdn_net/bin/python -m tools.g0_feasibility
/home/ubuntu/miniforge3/envs/sdn_net/bin/python -m tools.g0_estimator_bias_sim
git tag -a phase-G-g0-prereg ...
/usr/bin/time -f 'elapsed=%E max_rss_kb=%M' \
  /home/ubuntu/miniforge3/envs/sdn_net/bin/python -m tools.g0_roundtrip
```

Observed round-trip resource use: elapsed `0:00.37`, maximum RSS `36,668 KiB`.

## Result

Overall verdict: **PASS** on the preregistered feasible grid.

- Feasibility: 12/20 cells included; 8 excluded before the round trip.
- All G0-1 through G0-5 per-cell gates passed in all 12 included cells.
- `sigma_hat/sigma`: 1.00886 to 1.00924 (gate: 0.90 to 1.10).
- `tau_hat_offered/tau`: 0.93085 to 0.93107 (gate: 0.80 to 1.20).
- `tau_hat_measured/tau`: 0.90984 to 0.93106 (diagnostic only).
- Maximum p95 clip fraction: 0.00525 (gate: at most 0.01).
- Empirical signal fraction: 0.97327 to 1.00067; all relative comparisons
  with the analytic control passed the 10% gate.
- G0-1b: maximum tau-ratio spread over sigma was 0.000222, passing at all
  four evaluable tau levels.  Coverage is 4/5 because tau=0.5 has only one
  feasible sigma and is explicitly `NOT_EVALUABLE`.

## Per-cell screen output

```text
  sigma     tau | sig_hat/s tau_hat/t | tau_meas/t   clip95   sf_emp | gates
   0.01     3.0 |     1.009     0.931 |     0.915   0.0000    0.984 | PASS
   0.01    10.0 |     1.009     0.931 |     0.931   0.0000    0.998 | PASS
   0.01    30.0 |     1.009     0.931 |     0.931   0.0000    1.000 | PASS
   0.03     1.0 |     1.009     0.931 |     0.910   0.0000    0.982 | PASS
   0.03     3.0 |     1.009     0.931 |     0.927   0.0000    0.998 | PASS
   0.03    10.0 |     1.009     0.931 |     0.929   0.0000    1.000 | PASS
   0.03    30.0 |     1.009     0.931 |     0.930   0.0000    1.000 | PASS
   0.05     0.5 |     1.009     0.931 |     0.911   0.0053    0.973 | PASS
   0.05     1.0 |     1.009     0.931 |     0.922   0.0053    0.993 | PASS
   0.05     3.0 |     1.009     0.931 |     0.928   0.0053    1.001 | PASS
   0.05    10.0 |     1.009     0.931 |     0.931   0.0053    1.000 | PASS
   0.05    30.0 |     1.009     0.931 |     0.931   0.0053    1.000 | PASS
```

The `sigma=0.10` row family was not run: it fails the locked clipping-headroom
design test at these constants.  This is an additional inconsistency found in
the supplied prose, which claimed only the three packet-headroom exclusions.

## Artifact locations and digests

```text
results/SMOKE/phase-G/g0_feasibility.json
  sha256 d7a8ca5a2531f4aa5da1f2d679b5875ea2531f2a5ededbe1c9598101f98f4052
results/SMOKE/phase-G/g0_estimator_bias.json
  sha256 82979cf0942b1f3ad296779e276cc7ca2ad9c66257274eda837faebb0802be97
results/SMOKE/phase-G/g0_roundtrip.json
  sha256 5638c36262b7dc14c9345c62cbac7edfa052e66f8c5c56b886d73993f667ee59
```

The result is a synthetic NumPy dry run (`SYNTHETIC_DRY_RUN_NO_NETWORK`), not
a Mininet or physical-network measurement and not new RAW experimental data.
