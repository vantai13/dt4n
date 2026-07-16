# Phase 7.2 - Pilot V3 Gates

Pilot v3 changes the task design after pilot v2 showed that extreme skew can
freeze one branch's satisfaction.

With the moderate skew used in v3, the achievable best-level gap on 7
allocation levels is smaller than the initial 4-6 guess.  The scenario
contract is therefore:

```text
S3_flip_near: gap = 1
S4_flip_far:  gap = 2
S5_scarce:    gap = 1..2
```

This is intentional: a larger gap would require more extreme skew, which is the
same failure mode that froze one branch in pilot v2.

## Gates

| Gate | Threshold | Reason |
|---|---:|---|
| `sat_a_variability` and `sat_b_variability` | >= 0.05 | Both satisfaction dimensions are alive. |
| `VoI headroom` | >= 1.0 | Main RQ2b gate: enough room for AoI-aware ablation. |
| `dynamic_range` | >= 1.5 | Enough signal for the agent to learn. |
| `cost_of_blindness` | >= 1.0 | RQ2: stale data must hurt. |
| breaking point | exists | RQ2: stale twin becomes worse than caution. |
| `clair` std across z | <= 0.05 | Sanity: clairvoyant does not read stale observations. |

`dynamic_range` is lowered from 3.0 to 1.5 because RQ1 has already served as a
pipeline sanity check.  RQ2b is governed by VoI headroom, not by rule-baseline
dominance.  This does not revise the measured breaking point.
