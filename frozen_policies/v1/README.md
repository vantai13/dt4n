# Frozen Routing Policies v1

This directory contains the official Phase 9 frozen routing policies.

- Source runs: `results/train_scenario`
- Git hash: `fa6061d`
- Config hash: `f77ad6d`
- Seeds: `0, 1, 2, 3, 4`
- Behavioral gate: `delta(S1-S2) >= 0.5`

Re-evaluate without training:

```bash
python scripts/evaluate_frozen.py --version v1
```
