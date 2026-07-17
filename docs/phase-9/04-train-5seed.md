# Lesson 9.4 - Train 5 Seed + std_agent

## Pilot GO

Lesson 9.3 pilot seed 0 passed:

| gate | value | threshold | result |
|---|---:|---:|---|
| safe_delta | 0.5700 | > 0.20 | PASS |
| q_spread | 0.1790 | > 0.05 | PASS |
| arrived_rate | 1.0000 | > 0.95 | PASS |
| revisit_rate | 0.0000 | < 0.05 | PASS |
| path_unique | 4/10 | > 1 | PASS |

The safe-path sequence `0.30 -> 0.75 -> 0.87` across
`normal -> borderline -> bottleneck_E` is direct evidence that the agent reads
utilization and reacts in the right direction.

## Known Imperfection: SRC->B

In the pilot paths, the agent often starts with `SRC -> B` even though
`SRC -> A` has lower base delay. This is recorded, not hidden.

Reason: the state exposes per-neighbor utilization, not per-neighbor base
delay. The SRC A/B difference is small, about 0.9% of return, while the E/F
decision is roughly 12x larger and is the decision AoI can flip. Adding
`base_delay_n0/base_delay_n1` would change state 7D to 9D and weaken the AoI
ablation from `2/7 = 28.6%` to `2/9 = 22.2%` for a tiny return gain.

Decision: do not change the state. Keep the small known imperfection in the
notes.

## Five-Seed Rule

Five seeds are the floor, not the ceiling. A seed is an agent initialization
sample. If one seed is bad, do not discard it. The only exception is a real
technical bug such as NaN or broken artifact; after fixing the cause, rerun all
five seeds.

## SNR Gate

This gate is fixed before looking at the 5-seed result:

```text
headroom_sweep = 0.5869

std_agent <= 0.1956  -> SNR >= 3 -> PASS
0.1956..0.2934       -> SNR 2..3 -> WARN, run 10 seeds
std_agent > 0.2934   -> SNR < 2 -> FAIL, investigate stage
```

`std_agent` is expected to exceed `std_oracle=0.0390` because the agent adds
network-initialization variance.

## Commands

Real run, only after commit:

```bash
conda activate sdn_rl
./scripts/train_5seed.sh rl/routing/configs/train_r_v1.yaml 500
python scripts/analyze_5seed.py
```

The train script stops on a dirty working tree so real 5-seed artifacts do not
get anonymous `-dirty` identities.

## Outputs

`scripts/analyze_5seed.py` writes:

- per-seed return and behavior gates,
- `std_agent`,
- `SNR = headroom_sweep / std_agent`,
- `safe_path_freq(AoI=0)` anchor for Phase 11,
- outlier warnings without excluding any seed.

Fill after the real run:

```text
std_agent = ______
SNR = ______
verdict = ______
safe_path_freq(AoI=0) = ______
```
