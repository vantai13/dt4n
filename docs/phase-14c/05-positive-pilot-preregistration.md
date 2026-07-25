# Phase 14C.5 - Positive pilot preregistration for routing3 with r_v3

Ngay ky: 2026-07-24
Git hash at signing: `4cf5846`
Reward sha: `4fb73b561a44`

> Ky truoc khi chay positive pilot. Khong sua sau khi nhin so.

## Scope

This pilot changes one factor relative to the final Phase 14A routing3 stage:
the reward model changes from `r_v2` to `r_v3`. It does not add `criticality`
and does not add `REQUEST_SYNC`.

This is an OFAT check. If the result changes, the attribution is reward redesign
rather than a bundle of reward + criticality + sync.

## Prior evidence

- Static routing3 negative control with `ROUTING3_EVENT_RATE=0` is clean:
  `gap = 0`, `disagree_rate = 0`, `n_disagree = 0`.
- Static routing3 with r_v3 has `q_margin ~= 2.117`, much larger than the
  Phase 14A r_v2 routing3 margins (`0.031 -> 0.358` in the recorded configs).
- The two-path negative control is not sensitive to r_v2 vs r_v3 in headline
  `gap`: both rewards give the same gap across seeds 0,1,2, while r_v3 raises
  q_margin by about 3.5x.
- r_v3 increases overload reward span by about 3.4x relative to r_v2.

## Prediction

Prediction: `r_v3` alone will still FAIL the Phase 14A gate.

Directional prediction: `gap` will stay roughly the same as r_v2 or decrease,
not increase enough to matter.

Confidence: 0.65.

Reason: r_v3 increases regret scale in overload, but it also raises q_margin.
The Phase 14A law says `gap = disagree_rate x decision_regret`; if the larger
q_margin suppresses disagreement faster than r_v3 increases regret, headroom
will stay small. The two-path control is a warning example: reward scale changed
q_margin a lot while `gap` did not move.

Concrete expectation:

```text
mean objective: gap <= 0.0123, FAIL
CVaR alpha=0.1: may be the better of the two objectives, but lower CI95 < 0.10
```

If this prediction is wrong and r_v3 passes, report it as a positive reward-only
result. If it fails, the next pre-registered step is criticality, and both
reward-only and reward+criticality results must be reported.

## Locked configuration

Run exactly these six pilots:

```text
topology       = routing3
reward_model   = r_v3
cases          = 400
mc_samples     = 200
seeds          = 0, 1, 2
objectives     = mean, cvar
cvar_alpha     = 0.1
EVENT_RATE     = default routing3 value (0.12)
LOAD_PROFILE   = default routing3 value (cliffband)
CRASH_BIAS_TEMP= default routing3 value (0.0)
```

## Gate

Keep the Phase 14A gate:

```text
PASS iff lower CI95 >= 0.10
```

Do not lower the threshold after seeing results.

## Commands

```bash
for s in 0 1 2; do
python3 -m measurements.pilot_marginalized \
  --topology routing3 --reward-model r_v3 \
  --cases 400 --mc-samples 200 --seed "$s" \
  --objective mean \
  --out "results/phase-14c/pilot3_v3_mean_seed${s}.json"
done

for s in 0 1 2; do
python3 -m measurements.pilot_marginalized \
  --topology routing3 --reward-model r_v3 \
  --cases 400 --mc-samples 200 --seed "$s" \
  --objective cvar --cvar-alpha 0.1 \
  --out "results/phase-14c/pilot3_v3_cvar01_seed${s}.json"
done
```

## Commitment About Criticality

If this reward-only gate fails, run at most one additional pre-registered round
with `criticality`. Report both rounds. If both fail, stop the redesign path and
write the negative result rather than adding a third rescue mechanism.
