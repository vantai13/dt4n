# Phase 7.1 - Breaking Point Pilot

**Date:** 2026-07-15
**Data:** `results/pilot/z_range.json` (8 episodes x 3 scenarios x 6 z levels)
**Code revision:** `15d315c06ee7ef38c3746d47efd6649d906debe6`

## Result

| z | AoI (s) | blind_oracle | noop | blind - noop |
|---|---:|---:|---:|---:|
| 0 | 0.00 | 12.599 | 11.798 | +0.80 |
| 1 | 1.18 | 12.191 | 11.798 | +0.39 |
| 2 | 2.21 | 11.848 | 11.801 | +0.05 |
| 3 | 3.09 | 11.626 | 11.803 | -0.18 |
| 5 | 4.42 | 11.494 | 11.794 | -0.30 |
| 8 | 5.31 | 11.483 | 11.797 | -0.31 |

`blind - noop` crosses zero at about AoI ~= 2.3 seconds.  Past this point,
an optimizer that perfectly follows stale twin observations becomes worse than
a conservative policy that does nothing.

This is a digital-twin architecture result, not an RL result: `blind_oracle`
does not learn and is not algorithmically weak.  Its failure comes from stale
data.

## Metric Noise Floor

`clair_wrong` stayed near 12% for every z.  Clairvoyant reads true demand, so
this is not policy error.  It is the noise floor of `wrong_target`, caused by
ties and one-step greedy target definitions.

Report:

```text
wrong_excess = blind_wrong_rate - clair_wrong_rate
```

instead of interpreting raw `blind_wrong_rate` as pure AoI error.

## Gate Interpretation

| Gate | Question | Value | Status |
|---|---|---:|---|
| `cost_of_blindness >= 1.0` | Does AoI hurt? | 1.115 | PASS |
| Breaking point exists | When is stale twin worse than caution? | AoI ~= 2.3s | PASS |
| Saturation exists | Does stale damage flatten out? | z >= 5 | PASS |
| `voi_headroom >= 1.0` | Is there enough room for AoI-aware ablation? | 0.30 | FAIL |
| `dynamic_range >= 3.0` | Is there enough room for RL/control? | 0.81 | FAIL |

The two failed gates share the same root cause: the middle allocation is close
to optimal in too many episodes.  The next pilot version randomizes the initial
allocation and makes skewed scenarios more extreme before training any full
agent.

