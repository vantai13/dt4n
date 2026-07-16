# Phase 7.1 - Breaking Point and Pilot V2 Reading

**Updated:** 2026-07-16
**Data:** `results/pilot/z_range_v2.json`
**Log:** `logs/pilot_v2.log`
**Runs:** 432 = 6 z levels x 3 scenarios x 8 seeds x 3 policies
**Code revision:** `b8b263fdd6f1170aab7ffbee26fc2a67248d894c`

## Result

| z | AoI(s) | clair | blind | noop | blind-noop | VoI headroom | wrong_excess |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.00 | 10.713 | 10.708 | 10.339 | +0.369 | 0.000 | 0.0% |
| 1 | 1.17 | 10.710 | 10.182 | 10.328 | -0.146 | 0.146 | 12.5% |
| 2 | 2.20 | 10.714 | 9.833 | 10.333 | -0.500 | 0.500 | 25.0% |
| 3 | 3.08 | 10.706 | 9.654 | 10.332 | -0.678 | 0.678 | 33.3% |
| 5 | 4.41 | 10.705 | 9.564 | 10.345 | -0.781 | 0.781 | 40.1% |
| 8 | 5.27 | 10.706 | 9.557 | 10.338 | -0.781 | 0.781 | 40.1% |

## Breaking Point

`blind - noop` crosses zero between z=0 and z=1:

```text
AoI ~= 1.17 * 0.369 / (0.369 + 0.146) = 0.84s
```

Past about **0.84 seconds**, a perfect optimizer that follows stale twin data
is worse than a conservative policy that does nothing.

This is not a universal constant.  It belongs to this testbed and this demand
tempo (`delta_s=1.1s`, one demand flip per episode).  A slower system should
have a later breaking point.

## VoI Curve

Pilot v2 matches the prior VoI prediction:

```text
VoI(0) = 0.000
VoI rises monotonically to 0.781
VoI saturates around z=5..8
```

This is useful evidence for RQ2b, but the headroom is still below the practical
gate of `1.0`, so full AoI-vs-no-AoI training is not ready yet.

## Noise and Sanity

`clair` is flat across z: 10.705 to 10.714.  The observed spread is about
0.009, which is a useful estimate of Mininet measurement noise for this pilot.

`wrong_excess(z=0) = 0.0%`, so the `wrong_target` metric no longer has the
12% noise floor seen in pilot v1.

## Pilot V2 Failure Lesson

Pilot v2 changed two things: random initial allocation and extreme skew.

Random initial allocation helped RQ2b:

```text
VoI headroom: 0.30 -> 0.781
breaking point: 2.3s -> 0.84s
```

Extreme skew hurt the control range:

```text
dynamic_range: 0.808 -> 0.374
```

Root cause: with `frac_a` in `[0.80, 0.92]`, a typical demand was around
`(20.2, 3.3)`.  The low branch demand dropped below the minimum allocation
of 4 Mbps, so that branch's satisfaction stayed at 1.0 for every level.  One
state dimension effectively froze, and the task collapsed toward one-dimensional
control.

Pilot v3 encodes this lesson by:

1. using moderate skew `[0.60, 0.68]` or `[0.32, 0.40]`;
2. using 7 allocation levels;
3. using `t_max=12`;
4. reporting `sat_a_variability` and `sat_b_variability` as a degeneracy check.

