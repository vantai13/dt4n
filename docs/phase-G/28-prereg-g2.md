# G.2 preregistration — the physically wireable omega axis

Date locked: 2026-08-31 UTC. Status: `SYNTHETIC_NO_NETWORK`.

This document is locked before the G.2 tools are executed. G.2 creates no RAW
network data, starts no Mininet process, and does not change the G.1 evidence.
It consumes the G.1 measurement artifact only after verifying its SHA-256
against the conditional LIVE certificate.

## Inherited G.1 contract

- Certificate: `results/LIVE/phase-G/measurement_path_cert.json`, required to
  have `status=CONDITIONAL_PASS`, `g1_closed=true`, and the G.1 validity block.
- Measurement artifact: `results/SMOKE/phase-G/g1_closed_form_sf.json`. Its
  digest must equal the value pinned by the certificate.
- Locked measurement conditions: independent per-window `round()`, no carry,
  1442 wire bytes, and `dt=0.2 s`.
- The counterfactual cumulative model is named `cumulative_mixed`, matching
  `tools/g1_quant_model.py`. It has variance `1/6` packet squared and is used
  only as a robustness grid, not as a description of the deployed modulator.
- Any change to the quantisation mechanism, wire size, interval, topology,
  telemetry, pacing, or scheduler isolation expires the inherited certificate.

## Design and estimand

Let `M[l,p]` indicate that path `p` traverses link `l`, `d_l=sum_p M[l,p]`,
and `C_l` be link capacity in bit/s. The physically wireable generator uses a
single bit-rate amplitude for each path process:

    rho_l = mu_l + (a/C_l) * sum_p M[l,p] f_p + b_l*g_l
    a     = a0*sqrt(omega)
    b_l   = a0*sqrt((1-omega)*d_l)/C_l

Hence

    Var(rho_l) = a0^2*d_l/C_l^2
    r_lm       = omega*k_lm
    k_lm       = shared_lm/sqrt(d_l*d_m)

The variance of every link is invariant while omega is swept, but sigma is a
per-link vector. The campaign axis is `a0` in bit/s; `sigma_ref` is only the
derived sigma at reference link `uA` and every artifact records all eight
values. This differs deliberately from the older link-normalised analytic
model in `measurements/link_corr_matrix.py`: that model enforces equal sigma
by scaling each link, while G.2 preserves a common physical bit-rate process
along an end-to-end path.

The one-parameter estimator is

    omega_hat = <r,k>/<k,k>.

Pairs with `k=0` contribute zero to this expression. They are retained and
reported as built-in negative controls for unmodelled common correlation;
they are not described as increasing the estimator denominator.

## Locked grids and gates

- `omega in {0,.25,.5,.75,1}`; `tau in {3,10,30} s`; `dt=0.2 s`.
- Algebra tolerance: `1e-12`; variance tolerance: `1e-12` in rho-squared.
- Positive control: the old fixed-`a` parameterisation at `omega=.25` must
  change sigma by a ratio of at least 1.5 (analytic expectation 2).
- Monte Carlo: 120 seeds per `(omega,tau)` at `T=200*tau`; maximum absolute
  median bias and maximum sample SD of omega_hat must each be at most 0.05.
- Tau invariance asks whether tau_hat varies across omega. Its relative spread
  at fixed true tau must be at most 0.05. Absolute finite-sample bias is an
  observation, not an omega-axis gate.
- Null correlations: all 16 topology pairs with `k=0` must be zero in the
  analytic design to tolerance `1e-12`.

Feasibility is evaluated independently on every link:

    sigma_l/sigma_pack,l >= 5
    sigma_l >= sigma_min,l
    rho_bar + 2.58*sigma_l <= 0.995

The exact G.0 sigma grid is read from the LIVE certificate boundary and its
`1x,1.5x,2x` multiples. Both `rho_bar in {0.857,0.9195}` and quantisation modes
`{independent_round,cumulative_mixed}` are reported. No scalar sigma is allowed
to stand in for the vector check.

## Run-length decision

The target is `sd(omega_hat)<=0.05`. The proposed scaling law is

    sd(omega_hat) = c*sqrt(tau/T).

It is evaluated at `T/tau in {25,50,100,200}`, all three tau values, five omega
values, and 120 seeds. The spread gate for scaled `c` is the 95th percentile
of a preregistered standard-normal null with the same 12 rows, five within-row
SD estimates, and 120 samples per estimate. The null is diagnostic; budget
sufficiency is separately required at `T/tau=200` for every simulated cell.

Two required-duration summaries are reported:

- central: `(median(c_row)/0.05)^2`;
- conservative observed envelope: `(max(c_row)/0.05)^2`.

The `T=200*tau` budget is accepted only if the conservative observed envelope
is at most 200 and every directly simulated `T/tau=200` cell meets the target.

## Outputs and stopping rule

- `results/SMOKE/phase-G/g2_omega_algebra.json`
- `results/SMOKE/phase-G/g2_feasibility_omega.json`
- `results/SMOKE/phase-G/g2_runlength.json`

Any failed algebra, positive-control, certificate-integrity, or budget gate
stops G.2. G.2 does not measure physical omega, wire the generator into
Mininet, or claim that the physical testbed realises the analytic covariance.
Those are G.3 questions.
