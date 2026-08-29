# Phase G.0 v2 closeout — G-A001

Run date: 2026-08-29 UTC.  The first v2 round trip ran after annotated tag
`phase-G-g0-amendment-v2-prereg` at commit
`35843ccd5fdeb53842cb2f703eb706e072fc5521`.

## Verdict

**PASS** for the synthetic code-correctness experiment.  This does not claim
physical sigma/tau orthogonality; that claim requires a later Mininet test.

- Feasibility: 17/40 cells included under the declared `dt` axis.
- Per-cell gates: 17/17 PASS.
- `sigma_hat/sigma`: 0.97146 to 1.00924.
- `tau_hat_offered/tau`: 0.87288 to 1.00629.
- Maximum p95 clipping fraction: 0.001605.
- G0-1b code-correctness check: maximum spread across amplitude at fixed
  `(dt,tau)` was `4.45e-16`; coverage 3/8 fixed `(dt,tau)` groups because
  `dt=0.05` permits only `a=0.8` under packet headroom.
- G0-1c anti-degeneracy control: PASS on 5/5 evaluable fixed `(dt,a)` axes;
  spread across tau was 0.10791 to 0.12452, above the locked minimum 0.02.

Round-trip resource use: elapsed `0:05.27`, maximum RSS `51,024 KiB`.
The matching estimator-bias diagnostic took `1:30.63`, maximum RSS
`47,620 KiB`, and passed all eight deployed `tau/dt` configurations with
`P(pass +/-20%)` from 0.96875 to 1.0.

## Artifacts

```text
results/SMOKE/phase-G/g0_feasibility_v2.json
  sha256 edb1caaa23ae27e7ec86d112634ec769eaa32c52f37b578079047c6287d9b218
results/SMOKE/phase-G/g0_estimator_bias_v2.json
  sha256 18b3d5a83801b08bc6e66dad521f0cb6fe3a12a8b9c618b370be9e791786374a
results/SMOKE/phase-G/g0_roundtrip_v2.json
  sha256 b36c3b4b57a1a80d83bfc33b1fb340700557686a60cca529389ae2ab281bcc2b
```

The historical v1 artifacts and tags remain in place.  Their automated PASS
receipt is preserved, while their scientific interpretation is superseded by
G-A001.
