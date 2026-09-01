# G.3 dry-run gate addendum

Signed: 2026-09-01 UTC, after `phase-G-g3-prereg` and before the first
execution of `tools/g3_dryrun.py`. Status: `SYNTHETIC_NO_NETWORK`.

## Fixed execution design

- RNG seed: `20260905`.
- Anchor mean: 0.857 on every link.
- `a0=171679 bit/s`, `dt=0.2 s`, omega grid `{0,.25,.5,.75,1}`.
- Primary regimes: `(tau_p,tau_g)=(3,3)` and `(30,3)` seconds.
- Duration: `T=200*max(tau_p,tau_g)`.
- Replicates per cell: 16.
- Packet mechanism: independent `round()` in each window, 1442 wire bytes.
- Synthetic measurement residual: iid in time with covariance
  `R_eps=I+0.10*K_offdiag`; its per-link scale is the conservative G.1
  `v_nonquantized_raw` maximum. A numerical floor is used only if a certified
  scale is exactly zero and is recorded.
- Path component baseline: `3.25*a0` bit/s per path. Remaining mean capacity
  is assigned to the link-private baseline and must stay positive.

## Gates

| id | gate |
|---|---|
| DRY-0 | analytic link mean reconstruction error `<=1e-12`; covariance identities `<=1e-12` |
| DRY-C | maximum component clipping fraction `<=0.01`; aggregate target clipping `<=0.01` |
| DRY-Q | maximum `abs(ACF1(rho_sent-rho_target)) <=0.10` |
| DRY-W | maximum `abs(ACF1(rho_measured-rho_sent)) <=0.10` |
| DRY-R | maximum absolute error of residual off-diagonal correlation `<=0.06` |
| DRY-O | every cell: omega-hat median error `<=0.05` and SD `<=0.05` |
| DRY-T | lags 1--3 match the signed two-exponential mixture within `0.05`; median fitted persistence is monotone across omega |
| DRY-D-NC | kappa=1 pairwise flip-curve spread `<=6*max sqrt(0.25/(n-lag))` |
| DRY-D-PC | kappa=10 analytic flip spread `>=0.10`; simulated endpoint direction agrees |

The factor six in DRY-D-NC is the three-standard-error bound for the difference
of two independently estimated probabilities: `3*sqrt(2)*SE`, rounded upward.
It is derived before execution rather than selected from the observed spread.

Overall PASS requires every gate. Observational details remain in the artifact
even on failure. A failed dry-run prohibits a Mininet start but does not rewrite
the G.1/G.2 artifacts.
