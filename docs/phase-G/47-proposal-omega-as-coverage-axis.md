# Proposal — relocate omega from a decision axis to a coverage axis

STATUS: PROPOSAL + SYNTHETIC DRY-RUN. This document amends nothing.
`docs/phase-G/42-amendment-G-A014-certificate-renewal.md` and its selection of
`kappa = 5` remain in force. Any change to the kappa axis requires a separate
amendment, which this document does not make. It authorises no run.

## 0. Disclosure of timing

This proposal was written after the first emitter benchmark returned FAIL on
all four gates. That outcome supplies a MOTIVE, campaign cost, but not a
REASON. The case rests on G-A010 (`30-amendment-G-A010.md`, established before
the G.3 preregistration) and on closed-form and Monte Carlo results that
consume no network data. Deleting every sentence in this document that refers
to the benchmark leaves the argument intact; the reader is invited to check
that. No adjudicated outcome is reinterpreted here.

## 1. What G-A010 established

Under a single time scale the stale pairwise decision correlation is

    r(z) = [w*A*phi_p(z) + (1-w)*B*phi_g(z)] / [w*A + (1-w)*B]

and when `phi_p = phi_g` the omega-dependent factors cancel exactly, leaving
`r(z) = phi(z)` and `P(flip) = arccos(phi(z))/pi` independent of omega. G-A010
rescued the axis by giving the two components distinct time scales, which
introduced `kappa` as a new design parameter and multiplied run time by it.

## 2. The proposition

Omega does not vanish from SIMULTANEOUS coverage across K links at a single
time scale. If so, the axis carries content without kappa, and its operational
meaning sharpens: coupling matters for the GUARANTEE, not for the point
DECISION.

## 3. Gates, fixed before the recorded run

    COV-0  |simultaneous(w=0) - marginal(w=0)^K|   <= 0.005
    COV-1  max |marginal - (1-alpha)|              <= 0.010
    COV-2  simultaneous amplitude across omega     >= 0.050
    COV-3  monotone in omega, worst step           >= -0.002
    COV-4  amplitude / single-trace sd             >= 3.0
    OBS-COV-7   tau sweep of the calibration channel   REPORTED, not gated

Threshold disclosure. The thresholds were set after inspecting analytic
magnitudes, as for the kappa ladder of doc 42. No network data informs them.
They are deliberately loose relative to those magnitudes, 0.050 against 0.108
and 3.0 against 10.1, so that they are feasibility gates rather than lines
drawn around a result.

## 4. Results

    omega | marginal | simultaneous K=8 |    sd
     0.00 |  0.8983  |      0.4243      | 0.0092
     0.25 |  0.8983  |      0.4296      | 0.0106
     0.50 |  0.8983  |      0.4502      | 0.0110
     0.75 |  0.8983  |      0.4839      | 0.0112
     1.00 |  0.8986  |      0.5323      | 0.0114

    COV-0   0.00029  gate  0.00500  PASS
    COV-1   0.00172  gate  0.01000  PASS
    COV-2   0.10799  gate  0.05000  PASS
    COV-3   0.00536  gate -0.00200  PASS
    COV-4  10.08865  gate  3.00000  PASS

The marginal column is a negative control built into the estimand: it is flat
to four decimal places while the joint column moves 0.108. A result in which
both moved would mean omega had merely rescaled the variance.

A second negative control appears without being designed in. Sweeping the
subset size over the first K links in topology order gives amplitudes 0.0017,
0.0371 and 0.1080 at K = 2, 4 and 8. The first two links are `uA` and `uB`,
and `K_TOPO[uA,uB] = 0`: they are a topological null pair sharing no path, so
omega cannot couple them and the effect must vanish there. It does. The
subset is otherwise arbitrary, and the K sweep should be read as a control
rather than as a dose-response curve.

## 5. COV-0 anchor, and the number the previous gate produced

    |simultaneous(w=0) - marginal(w=0)^K|  = 0.00029   COV-0       PASS
    |simultaneous(w=0) - (1-alpha)^K|      = 0.00621   OBS-COV-1

The second number is not discarded with the gate that produced it. It is the
K-fold image of the marginal deficit COV-1 measures at 0.00172:
`3.826 * (-0.00172) = -0.00658` against an observed `-0.00621`.

Disclosure. The COV-0 anchor was changed after an exploratory run, which is
also how the deficit was found. That run was not preregistered and no tool was
committed at the time; finding this class of specification error is what it
was for. The correction is derivable without looking at any number:
independence predicts the product of whatever marginals the estimator
ACHIEVES. The nominal level is measured separately by COV-1, so testing the
joint against the nominal product charged one gate with two distinct errors.

## 6. OBS-COV-7 — a second regime channel, independent of coupling

At `omega = 0` the links are independent, so the only departure from nominal
coverage is interval calibration. An interval built from a trace's own sd
undercovers: coverage is concave in the estimated sd, so Jensen pulls the
expectation below nominal. Autocorrelation widens the sampling spread of that
sd, so the deficit deepens with tau.

| tau (s) | phi | marginal | deficit | SE | ratio | SE |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | .8187 | .89958 | -.00042 | .00018 | not estimable | - |
| 3 | .9355 | .89829 | -.00171 | .00021 | 3.632 | .549 |
| 10 | .9802 | .89427 | -.00573 | .00039 | 4.058 | .262 |
| 30 | .9934 | .88193 | -.01807 | .00131 | 3.739 | .140 |

Predicted `K*(1-alpha)^(K-1) = 3.826`. At `tau = 1 s` the deficit is below the
0.001 threshold at which the ratio is estimable, so no ratio is reported: it
would be one small number divided by another and would imply a precision the
three estimable rows have but it does not. Each estimable row lies within
about one standard error of the prediction.

Relative size of the two channels, at K = 8 and alpha = 0.10:

    channel 1 (omega): joint coverage .4243 -> .5323, amplitude +.1080
    channel 2 (tau):   joint deficit against nominal, at omega = 0
                         tau =  1 s   -.0015      1.4% of channel 1
                         tau =  3 s   -.0062      5.8%
                         tau = 10 s   -.0232     21.5%
                         tau = 30 s   -.0676     62.5%

At `tau = 30 s` the two are of the same order and carry opposite signs. Both
are measured at a SINGLE time scale, so neither needs kappa.

## 7. What adoption would change, and what it would cost

    gains: kappa leaves the regime label; T_run returns to 600 s; the label
           returns to (rho_bar, sigma, tau, c_a, omega); omega acquires an
           effect that needs no two-scale construction; a second, orthogonal
           regime channel becomes available
    loses: the claim that omega moves the point decision. G-A010 proves it
           does not, at a single time scale, so nothing true is surrendered

## 8. Limits

- Simultaneous coverage over K LINKS is not the same estimand as the runtime
  K-variable coverage of Phase 22R. The transfer is asserted, not shown.
- Intervals are symmetric Gaussian with sd estimated from the trace.
  OBS-COV-7 is specifically a property of sd-estimated intervals; conformal
  intervals may calibrate differently.
- The nugget is white. An autocorrelated measurement path is not covered.
- The effect is diluted by the signal fraction: amplitude 0.1558 at sf = 1.00,
  0.1080 at the certified sf = 0.85, 0.0722 at sf = 0.70.
- The K sweep uses the first K links in topology order, an arbitrary subset.
- Duration buys precision, not effect: amplitude is 0.1080, 0.1053 and 0.1075
  at T = 600, 1800 and 3000 s while the SNR rises 10.1, 18.1, 25.4. The
  600 s budget is sufficient.

## 9. Decision rule

Passing all five gates is NECESSARY, not sufficient. Adoption requires a
separate amendment after Phase 22R's estimand is confirmed to inherit the
effect. Until then `kappa = 5` stands as signed in doc 42.

**G-L93:** the independence anchor for finite-sample joint coverage is the
product of the ACHIEVED marginals. Testing against the nominal product folds
an interval-calibration error into a dependence check.

**G-L94:** a marginal calibration deficit reappears in joint coverage
amplified by `K*(1-alpha)^(K-1)`, and under AR(1) that deficit grows with tau
through the sampling spread of the estimated sd. This is a regime-dependent
coverage channel independent of coupling. A ratio of two small deficits is
estimable only where the denominator clears a stated threshold.

## Artifacts

    results/SMOKE/phase-G/g3_omega_coverage_dryrun.json
    sha256 23d555b5966c14fd2be35b63ba9a00cb5a85b0187ae11077ce283eb3320bdae8

Preregistration: none. This is exploratory and is labelled as such.
