# Preregistration — NC-G1-static v2

This design is signed after the no-network engineering cost check and before
the first v2 Mininet run. Tag: `phase-G-g1-static-nc-v2-prereg`.

## Custody and scope

The public DOI remains null. K12's user-attested offsite backup permits local
Phase G capture only; it is not public archival custody and authorizes no
historical cleanup. V1 remains preserved at tag
`phase-G-g1-static-smoke-invalid`.

## Locked generator and sampler

- Eight deterministic CBR channels, payload 1400 B, `rho_bar=0.857`.
- Absolute cumulative batch pacing, no spin, `pace_tick=0.002 s`.
- Ledger interval 0.010 s; burn-in 20 s.
- Emitters run 2 s beyond the requested sampler duration so sequential process
  startup cannot leave the final absolute measurement grid outside a ledger;
  the guard interval is never analysed.
- Two independent `/proc/net/dev` reads at phases 0 and `dt/2`, each with its
  own counter baseline and absolute monotonic timestamps.
- Main smoke: six A--F cells, 60 s, one repetition, `dt=0.200 s`.
- Full campaign, only after a valid smoke: six cells, 300 s, three repetitions,
  plus cell D at `dt={0.1,0.2,0.5}` for one preregistered repetition.
- Telemetry cells retain the v1 corrected matrix: Ditto uses `prod,tol=0` so
  reconcile 1 and 30 are real contrasts; E is probe-only.

## Mandatory pre-network cost gate

Eight emitters run for 30 s without Mininet. The gate is fixed at system CPU
p95 <25%, all emitter exit codes zero. Failure blocks all v2 network work.
Artifact: `results/SMOKE/phase-G/g1_static_v2_cost_gate.json`.
The signed engineering receipt is PASS: CPU p50 6.637%, CPU p95 14.094%,
8/8 emitter exit codes zero, zero swap and zero network drops.

## Per-link model and classifications

`acf1=1-Var(diff(x))/(2 Var(x))`. The effective floor uses
`2*max(1,rate_pps*pace_tick)^2/(12*n_pkt_window^2)` exactly as implemented
before network outcomes.

- QUANT_LIMITED: `v_ratio<=3` and `-0.80<=acf1<=0.05`.
- WHITE: `abs(acf1)<0.10` outside the quant-limited rule.
- SLOW: `acf1>0.15`.
- MIXED: all remaining cases.

## Locked smoke advancement gates

- Every run uses static engine, two sampler files, and prereg tag ancestry.
- Every link: independent-grid offered share <=0.10, ledger lag p95 <=0.02 s,
  maximum ledger gap <=0.05 s, and ACF(1) <=0.15.
- At least 6/8 links per cell are QUANT_LIMITED.
- Every run: CPU p95 <40%, zero swap/network drops/send errors, packet
  shortfall <=0.01, emitter maximum lag <=0.05 s.
- Combined sampler read-duration p95 implies timing error <0.005.

All six cells must be VALID to advance. A telemetry cell with CPU p95 >=40%
is an instrument boundary on this host; gates are not relaxed and the full
campaign remains blocked.

## Independent-sampler and dt outcomes

For each link, sampler-1 rho is interpolated onto sampler-0 absolute time.
Same-link correlation >=0.80 is labelled PHYSICAL-DOMINATED, <=0.20 is
SAMPLER-DOMINATED, and intermediate values are MIXED/INCONCLUSIVE. These are
outcomes, not validity gates.

For the full cell-D dt control, the locked quantization prediction is
`v proportional to 1/dt^2`. A link supports it if
`v(0.1)/v(0.2)` lies in [2,8] and `v(0.2)/v(0.5)` lies in [3.125,12.5]. This
factor-two band is fixed before data and reported per link; no aggregate is
silently substituted for a failing link.

H6b and H6c remain competing outcomes. V1 supplies no adjudication because
its shared CPU stalls dominate; no v2 threshold may be tuned to reproduce the
v1 correlation pattern.
