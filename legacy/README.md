# legacy/ - Kho code cua cac cau hoi nghien cuu da dong

Khong xoa thu muc nay. Noi dung o day la bang chung cho cac phase cu va van can
cho artifact evaluation. Chung chi ra khoi tam mat hang ngay, khong ra khoi du an.

## Ben trong la gi

| Thu muc | Phase | Vai tro | Ly do dong |
|---|---:|---|---|
| `rl/a2/` | 5-7 | Cap phat tai nguyen bang RL | Cau hoi cu da dong |
| `rl/agent/` | 8-11 | DQN agent | v7 khong con dung RL lam loi |
| `rl/routing_2path/` | 8-11 | Topology 2 duong, ablation AoI | Negative-control evidence |
| `rl/routing3/` | 14A-14C | Reward/gate 3 duong | Gate/reward line da dong |
| `scripts/` | 8-14 | Train, eval, freeze policy | Gan voi RL cu |
| `frozen_policies/` | 9-11 | Policy da dong bang | Bang chung, khong phai runtime v7 |
| `measurements_v6/` | 10-14C | Probe/sampler tren simulator RL va phase cu | Sinh K-motive/K-gate evidence |
| `test_v6/` | 5-14C | Test cua RL va frozen-policy line | Chay lai tai tag `v6-final` |

## Script nao sinh ra so nao

| So trong narrative | Script hien o dau | Ket qua |
|---|---|---|
| Gap = disagree x regret | `measurements_v6/pilot_marginalized.py` | `results/phase-14c/` |
| Winner's curse / placebo | `measurements_v6/pilot_marginalized.py` | `results/phase-14c/placebo_honest.json` |
| Factorial 2x2 + controls | `measurements_v6/phase14c_factorial.py` | `results/phase-14c/factorial_honest_*.json` |
| Sync upper bound | `measurements_v6/sync_upper_bound.py` | `results/phase-14b/` |

## Chay lai code cu

Import path trong current tree da thay doi. De chay lai dung moi truong v6, dung
tag da tao truoc cleanup:

```bash
git checkout v6-final
pytest test/
git checkout cleanup/v7
```

## Cac file da duoc cuu ra khoi legacy

| File moi | Ly do |
|---|---|
| `twin/link_model.py` | Single source of truth cho calibrated delay/loss model |
| `twin/link_model_fit.py` | Cong cu tai sinh `results/calib/link_profiles.json` |
| `twin/topology3.py` | Tam giu de Lesson 20 thay topology moi |
| `twin/util_spec.py` | Cong thuc utilization dung cho measurement/deploy |

## Luu y provenance

`results/calib/` da duoc khoi phuc tu commit `7bcce0d^`, truoc khi commit
`7bcce0d` xoa nham artifacts vao 2026-07-19. Neu do lai, commit toan bo
`results/calib/**` va khong tao du lieu gia.
