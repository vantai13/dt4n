# G-A007 — paired residual after NC-G1-static v2

Date: 2026-08-30 UTC. This amendment reads the already-burned v2 smoke and
changes no v1/v2 verdict. All v2 cells remain INVALID under their signed gate,
and no v2 LIVE certificate exists. Existing G-L1--G-L44 retain their committed
meanings; this amendment allocates G-L45--G-L50.

## Why the v2 gate is withdrawn

G1S2-1 used `offered_share = v_offered/v_measured <= 0.10`. For a perfect
counter, measured and offered packet counts share the same physical boundary
event, so `v_measured=v_offered` and the ratio tends to one. Adding independent
path noise makes the ratio smaller. The gate therefore rewarded a dirtier
instrument and penalized a faithful one. This is G-L45, the shared-cause ratio
fallacy. The recorded v2 failure is not recomputed post hoc.

V3 instead pairs the counter bytes and emitter packet ledger on the same
absolute `CLOCK_MONOTONIC` endpoints and fits

```text
M_k = B * delta_N_k + c + R_k.
```

`R_k` is the counter component not explained by the emitted packet count.
`v_path=Var(R_k/(C*dt/8))` measures the path residual in rho-squared units.

## Distinct quantities and units

- G-L46: packet-boundary variance (`v_pack`) is physical and unavoidable;
  measurement-path variance (`v_path`) is an instrument residual. Campaign
  feasibility uses `v_pack+v_path`, while path cleanliness and cross-link
  correlation use only the paired residual.
- G-L47: correlation on raw `rho_measured` is attenuated by independent
  packetization. The v2 raw correlations cannot refute H6b, H6c, or H-SAMPLER;
  those claims remain INCONCLUSIVE until correlation is computed on `R_k`.
- G-L48: staircase alignment has finite uncertainty. The ledger interval is
  2 ms. V3 reports both the design value `rate_pps*ledger_tick` and the observed
  maximum `rate_pps*max_ledger_gap`; the latter is an additional conservative
  validity gate, not silently replaced by the nominal tick.
- G-L49: two phase-offset samplers have a deterministic packetization null
  sensitive to `frac(rate*dt)`. Same-link s0/s1 correlation is withdrawn as a
  gate. Its stable sign in v2 is descriptive evidence only; `bd` remains the
  preregistered exception to follow.
- G-L50: `1/(6*n_packet^2)` is relative packet-count variance. To add a floor
  to `Var(rho)`, V3 uses `(B/(C*dt/8))^2/6`. Both values are recorded with unit
  names so they cannot be interchanged.

## Locked byte-accounting audit

Before V3 network capture, cumulative v2 bytes divided by packets gave wire
bytes per packet of 1441.956--1442.014 across the eight links in clean cell D.
This supports, but does not replace, the V3 per-link gate around 1442 bytes.
Payload 1400 B plus UDP 8 B, IPv4 20 B, and Ethernet header 14 B predicts the
same total. Failure of the fitted gate stops advancement rather than changing
the expected value.

No historical raw file or prior tag is rewritten by this amendment.
