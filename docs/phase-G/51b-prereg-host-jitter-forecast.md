# G-A016 host-jitter forecast preregistration

Recorded: 2026-09-04 UTC, before either host-jitter measurement and before the
reduced emitter benchmark. Status: `PREREG_NO_HOST_MEASUREMENT`.

## Question and operator

`tools/host_jitter_probe.py` runs the emitter's exact absolute-deadline pacing
loop on one CPU for 60 seconds, with the same 200 ms windows, fastest-link
cadence, spin threshold, and per-window maximum, but with no socket and no
sink. Its primary measurement is

    p_stall_1ms = fraction(window_max_lateness >= 1 ms).

At 60 seconds there are 300 windows and the point estimate has resolution
`1/300 = 0.00333`. This probe is a coarse admission screen; it cannot by
itself establish `p_stall < 0.0005` with useful confidence. The Wilson upper
endpoint is reported so that zero observed events is not misread as proof of
zero event probability.

CPU PSI is captured immediately before and after the paced interval. Only
`delta(total_us)/(elapsed_s*1e6)` is interpreted. Displayed PSI averages and
load average remain diagnostics.

## Predictions locked before measurement

| Scenario | Predicted `p_stall_1ms` | Expected timing EMIT-3 |
|---|---:|---:|
| Before quiesce | 0.02--0.20 | 0.66--0.99 |
| After quiesce | 0.001--0.02 | 0.18--0.80 |
| Needed for historical timing EMIT-3 <= 0.10 | below about 0.0005 | about 0.10 |

Primary prediction: quiescing guest services will reduce the measured stall
rate but will not make the historical timing EMIT-3 pass 0.10. A contrary
result is retained and reported as evidence rather than used to change a
threshold.

The measured probability is forecast with the reduced bench's exact shape
(`8` replicates, `150` windows) before the network bench. Forecast mode uses
an injected shared lateness conditional on being at least 1 ms; this matches
the probe's measured event definition. The older illustrative sweep is kept
as `legacy probability of an unconditional exponential event` and is not
silently reinterpreted.

## Admission and stop rules

- `GATE_P_STALL = 0.02` is a prospective coarse operational screen. With 300
  windows it permits at most six observed >=1 ms windows.
- The threshold determines whether spending eight minutes on the loopback
  bench is warranted. It does not adjudicate the campaign and does not replace
  EMIT-3' or EMIT-4'.
- Formal preflight requires an `after_quiesce` artifact of at least 60 seconds,
  a matching tool SHA256, and a commit that contains the declared tool.
- If the after-quiesce point estimate exceeds 0.02, stop before the network
  bench and report the result.
- The before-quiesce probe may be run in the coding session. Quiescing and the
  after-quiesce probe must run from plain tmux/SSH because quiescing stops
  coding agents by design.

No G-A016 preregistration tag is created by this document.
