# G-A006 — engineering reclassification after NC-G1-static v1 smoke

Date: 2026-08-30 UTC. This amendment reads the already-burned v1 smoke and is
therefore post-hoc. It changes no v1 outcome: all six cells remain INVALID and
the full v1 campaign remains correctly blocked.

The identifier is G-A006 because G-A005 already names the G-A004 component
reclassification. Existing G-L31--G-L37 retain their committed meanings; this
amendment allocates G-L38--G-L42.

## Four engineering defects identified by the smoke

1. G-L38 — the 1.5-ms busy-spin tail occupied most packet gaps. The static
   generator alone reached CPU p95 77.06% in cell D and up to 95.46% with the
   telemetry bundle. Shared scheduler stalls and catch-up batches contaminate
   both direct v and cross-link correlation. All v1 H6b/H6c verdicts are
   INCONCLUSIVE, not confirmed or refuted.
2. G-L39 — the v1 white gate used the wrong null. Deterministic cumulative
   packet counts conserve packets between adjacent windows; their fractional
   residual is differenced and can have negative lag-one correlation. Since
   `Var(diff(x))/2/Var(x)=1-ACF(1)`, a clean deterministic pacer can have a
   ratio above one. G1S-2 v1 is withdrawn.
3. G-L40 — v1 offered validation did not share an absolute time origin with
   the counter sampler. V2 records `CLOCK_MONOTONIC` timestamps in both files
   and projects cumulative bytes onto the independent measurement grid. Lag
   p95 and maximum ledger gap become explicit stall gates.
4. G-L41 — TX and RX from one `/proc/net/dev` snapshot are not independent
   instruments. V2 performs two separately timed reads, half a window apart.
   This tests independent read timing, not per-node sampler identity.

G-L42 records the scientific consequence without overstating the invalid
smoke: flow-level shot noise faster than the 0.2-s window can be spectrally
confounded with measurement noise in a lag-zero ACF decomposition. The lower
CBR diagnostic variances motivate a new valid control; they do not yet license
the numerical claim that a fixed percentage of the old nugget was traffic.

## Code correction

- `static_emitter.py` now sleeps and emits all packets due under the absolute
  cumulative schedule; it never busy-spins. `pace_tick=0.002 s` and maximum
  backlog are recorded.
- Ledger and measured CSV schemas add absolute `monotonic_s`.
- `RhoLogger` supports two independent reads at phases 0 and `dt/2`; sampler 0
  keeps the historical filename and sampler 1 uses `_s1.csv`.
- `g1_static_nc.py` replaces the withdrawn white gate with direct ACF(1), an
  effective pacing/quantization floor, noise classes, and independent-clock
  offered validation.

No v1 raw file is rewritten. V2 uses separate raw and compact artifact paths.
