# G.1 closeout — quantisation mechanism and identifiability boundary

Date: 2026-08-31 UTC. Status: `REANALYSIS_EXISTING_RAW_NO_NETWORK`.
No Mininet run was executed for this closeout. It consumes the IPv6-off RAW
retained by G-A008. Public DOI remains null and the existing custody rules are
unchanged.

## Scope and audit correction

G.1 was asked to characterise the measurement path, establish the smallest
usable sigma, and estimate cross-link residual correlation `rho_eps`. The
first two are delivered conditionally. The third is delivered as an
identifiability boundary for static CBR controls.

The proposed closeout initially assumed that the modulated G.0 generator used
a cumulative carry accumulator, which would give variance `1/6` packet^2 and
lag-one correlation `-1/2`. A code and preregistration audit rejected that
assumption. `docs/phase-G/00-prereg-g0.md` explicitly locks independent
`round()` per window with no carry accumulator, and `mininet/rate_modulator.py`
implements exactly that mechanism.

A 500,000-window positive control separates the mechanisms:

| mechanism | measured Var(error), packet^2 | measured ACF(1) | theory |
|---|---:|---:|---|
| deployed independent `round()` | 0.08307--0.08336 | -0.0017--0.0016 | `1/12`, 0 |
| hypothetical cumulative `floor()` | 0.16621--0.16696 | -0.5007-- -0.4984 | `1/6`, `-1/2` |

Therefore applying the proposed MA(1) patch without changing the generator
would have made design and analysis inconsistent. `tools/g1_quant_model.py`
now exposes the two modes separately and every consumer must name its mode.

**G-L58:** quantisation variance and colour are properties of the packet
accounting mechanism, not universal constants. Independent window rounding
uses `1/12` and is approximately white; cumulative mixed-phase counting uses
`1/6` and MA(1); fixed-grid static CBR uses `f(1-f)` and is quasi-periodic.

## G-A009 — wire-byte accounting and single source of truth

The G.0 implementation used 1400 payload bytes to convert packet counts to
link utilisation, while `/proc/net/dev` measures the 1442-byte Ethernet/IPv4/
UDP frame. The floor was therefore understated by

    1442 / 1400 = 1.0300

not by `sqrt(2)*1442/1400 = 1.4566`; the extra `sqrt(2)` belongs only to a
different cumulative mechanism. The following paths now consume the same
explicit independent-round formula and 1442-byte wire size:

- `ModulatorConfig.sigma_quant_floor`, `n_pkt_per_window`, `quantize`, and
  `pace`;
- `tools/g0_feasibility.py`;
- the G.1 validation and conditional signal-fraction calculation.

`test/test_g1_quant_model.py` locks the static, independent-round, cumulative
MA(1), wire-size, and cross-layer agreement properties.

**G-L59:** payload-to-wire drift crossed a preregistered headroom boundary.
Recomputing the feasibility map reduces it from 17/40 to 9/40 cells even
though the numerical floor changes by only 3%. The surviving grid is

    dt = 0.2 s
    sigma in {0.0202326, 0.0303488, 0.0404651}
    tau in {3, 10, 30} s

with headroom 9.72--19.44. The full `dt=0.05 s` axis and `sigma=0.0101163`
row are below the locked headroom of 5 and are withdrawn from the campaign.

## Closed-form estimator, validated before measurement

For the independent-round model, `x = s + e`, with AR(1) signal `s` and
approximately white quantisation `e`:

    gamma_1 = sigma_s^2 * phi
    gamma_2 = sigma_s^2 * phi^2
    phi_hat = ACF(2) / ACF(1)
    sigma_s^2_hat = Var(x) * ACF(1) / phi_hat

Lag 3 is not fitted; it is a positive control. Invalid `phi`, negative signal
variance, or materially negative noise variance causes refusal rather than
clipping.

The mandatory synthetic stage ran the actual independent-round/wire-byte
pipeline over 12 `(sigma,tau)` cells and 16 seeds per cell. It passed 12/12:

    max |sf_hat - sf_true|       = 0.02152  (gate 0.03)
    max lag-3 control error      = 0.00328  (gate 0.03)
    valid seeds                  = 16/16 in every cell

`--stage measure` refuses to run without a PASS receipt for the same named
quantisation mode. This is NT 53 enforced by code.

**G-L60:** the MA(1) estimator remains available only for an explicitly
cumulative future generator. The deployed independent-round estimator uses
lags 1 and 2 for identification and lag 3 as its held-out control.

## Existing IPv6-off RAW decomposition

The measure stage used three 40 s IPv6-off runs, 20 s burn-in, and 24
link-runs. Static CBR is evaluated with its exact `f(1-f)` floor. The raw
remainder after subtracting that floor is reported conservatively:

    sigma_nonquantized_raw = 0.00000 .. 0.00211
    conditional sigma_min for sf >= 0.85 = 0.01111

The maximum is the previously identified event-bearing `ad` run. This
quantity is deliberately named `v_nonquantized_raw`, not `v_path`: G-A008
showed that the remainder contains intermittent host scheduling/catch-up
batches and is not a stationary nugget. No event was silently censored.

The analytic G.0 headroom bound (`sigma >= 0.02023`) is stricter than the
conservative measured signal-fraction bound (`sigma >= 0.01111`). Therefore
the operational campaign boundary is `sigma >= 0.02023`, rounded in prose to
`sigma >= 0.02`.

**G-L61:** subtracting `f(1-f)` from a short static run does not manufacture a
stationary path variance. The remainder is an event-equivalent conservative
bound; ledger-aware event handling remains required in physical campaigns.

## `rho_eps` is not identifiable from the static control

`tools/g1_null_quasiperiodic.py` uses each run's actual sample boundaries and
`dt` values and randomises only independent initial packet phases. Results at
20,000 null replicates per pair are:

| run | observed inside pairwise 95% null | pairs separating `|r|=0.50` | max null SD / iid SD | null-model check |
|---|---:|---:|---:|---|
| matched | 23/28 | 27/28 | 4.0x | FAIL, 5 outside (`p=0.0117`) |
| tight | 25/28 | 19/28 | 5.8x | PASS |
| default | 28/28 | 18/28 | 5.8x | PASS |

The matched run's model-check failure prevents claiming that quasi-periodicity
is a complete residual model. It does not rescue identifiability: even under
the narrower matched null, the equal-rate `uA-vC` pair has an upper null limit
of 1.0. In the other two runs, 9/28 and 10/28 pairs respectively cannot even
separate `|r|=0.50` from the independent static null.

The threshold-separation diagnostic is not a full power calculation for a
specified shared-noise process, so the stronger claim "not identifiable at
any achievable run length" is not made.

**G-L62:** `rho_eps` is not identifiable at the preregistered `|r|=0.50`
threshold from these static controls. It is deferred to a modulated,
replicated experiment with offered same-realisation ground truth. Equal-rate
pairs must be detuned or handled with a joint mechanistic null.

## Ledger routing contract

| quantity | authoritative ledger | reason |
|---|---|---|
| regime label `(sigma,tau,omega)` | offered | controlled design parameters |
| long-run carried load | cumulative counters | wire accounting is exact in aggregate |
| twin input telemetry | `rho_measured` | instrument effects belong to the studied error |
| controlled `omega` | offered | set by design |
| physical `omega` | measured, conditionally corrected | requires the conditional scope below |
| scheduling-event mask | emitter ledger gaps/backlog | the counter series alone cannot identify send batching |

## G.1 verdict

`G1_closed = true` within this explicit scope:

- delivered: mode-specific quantisation laws, corrected wire accounting,
  9-cell feasible grid, self-validating independent-round estimator, raw
  non-quantised bound, conditional `sigma >= 0.02023` boundary, and ledger
  routing contract;
- not delivered: an unconditional stationary `v_path` or direct `rho_eps`;
  both are prohibited by the retained evidence rather than filled in by fit;
- expiry: any change to quantisation mode, packet size, `dt`, topology,
  telemetry path, pacing process, or scheduling isolation invalidates the
  conditional certificate.

G.2 may open as a NumPy-only stage. No new RAW is created by this closeout.

**G-L63:** the G.1 certificate is conditional on independent per-window
rounding, 1442-byte wire accounting, `dt=0.2 s`, the Phase-20 v7 topology,
and campaign `sigma >= 0.02023`; it is not a universal instrument property.

## Artifacts

- `tools/g1_quant_model.py`
- `tools/g1_closed_form_sf.py`
- `tools/g1_null_quasiperiodic.py`
- `test/test_g1_quant_model.py`
- `results/SMOKE/phase-G/g0_feasibility_v2.json`
- `results/SMOKE/phase-G/g1_closed_form_validation.json`
- `results/SMOKE/phase-G/g1_closed_form_sf.json`
- `results/SMOKE/phase-G/g1_null_matched_rep1.json`
- `results/SMOKE/phase-G/g1_null_tight_rep1.json`
- `results/SMOKE/phase-G/g1_null_default_rep1.json`
- `results/LIVE/phase-G/measurement_path_cert.json`
