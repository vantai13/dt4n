# Phase 7.0 - VoI Prediction

**Written:** 2026-07-15, before the full pilot-v2 reading.

## Prior Prediction

From Value of Information intuition:

```text
VoI(AoI) = E[return | policy can read AoI]
           - E[return | policy cannot read AoI]
```

Expected shape:

1. `VoI(z=0) = 0`: when data is fresh, knowing "I am fresh" adds no useful
   information.
2. `VoI` rises with staleness: when observations become stale, knowing that
   they are stale lets a policy become conservative.
3. `VoI(z -> infinity) -> 0`: when observations are completely unusable, both
   policies should learn to ignore them, so the extra AoI bit loses value.

Therefore the expected curve is bell-shaped.  The useful z range should sit on
the rising side or near the peak.  If z is too large, both agents are blind and
an AoI ablation can look empty even when the idea is correct.

