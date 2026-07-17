# Lesson 9.3 - Pilot 1 Seed + Xem Tay

## Phat hien

`LOAD_CFG_V1` tot cho Dijkstra sweep vi cost of blindness manh va don dieu.
Nhung no khong tot de train DQN: voi `e_load=(0.80, 0.97)`, E gan nhu khong
bao gio la lua chon dung tai C/D. Agent co the hoc policy tinh "luon F", khong
doc utilization, roi mien nhiem voi AoI.

Tong quat hoa Nguyen tac 14: khong chi kiem state co bien thien hay khong; phai
kiem quyet dinh toi uu co bien thien hay khong.

## Thay doi

- Them `scripts/diag_decision_balance.py` de do `frac_E_better`.
- Them `scripts/pilot_load_cfg.py` de chon load train bang gate tien nghiem.
- Them `LOAD_CFG_TRAIN` trong `rl/routing/topology_r.py`.
- Doi `rl/routing/configs/train_r_v1.yaml` sang `load_cfg: LOAD_CFG_TRAIN`.
- Them `scripts/pilot_train_r.py` de pilot 1 seed va xem tay.

## Quyet dinh

Giu `LOAD_CFG_V1` cho RQ2/Dijkstra sweep. Dung `LOAD_CFG_TRAIN` cho DQN train:

```python
LOAD_CFG_TRAIN = {
    'base_load': (0.25, 0.40),
    'e_load': (0.60, 0.97),
    'drift_sigma': 0.15,
}
```

Day la domain randomization theo truc tai. Lesson 9.2 da randomize truc AoI
bang `z_steps_choices`.

So da do tren may nay:

- `LOAD_CFG_V1`: `frac_E_better=0.000`, `cost_bl max=0.5869`, `FAIL` cho train.
- `LOAD_CFG_TRAIN`: `frac_E_better=0.330`, `cost_bl max=0.4612`, `PASS`.
- Pilot 400 episode seed 0: `path_unique=4/10`, `q_spread=0.1790`,
  `safe_delta=0.5700`, `arrived_rate=1.0000`, `revisit_rate=0.0000`,
  verdict `GO`.

## Validation

```bash
conda activate sdn_rl
python scripts/diag_decision_balance.py
python scripts/pilot_load_cfg.py
python scripts/pilot_train_r.py --seed 0 --episodes 400
```

Gate truoc pilot:

- `LOAD_CFG_V1` phai hien ro static-policy risk.
- `LOAD_CFG_TRAIN` phai co `frac_E_better` trong `[0.20, 0.80]`.
- `cost_of_blindness(max)` phai lon hon `0.30`.

Gate sau pilot:

- `path_unique > 1`
- `q_spread > 0.05`
- `safe_path_freq(bottleneck_E) - safe_path_freq(normal) > 0.20`
- `arrived_rate > 0.95`
- `revisit_rate < 0.05`

Neu gate safe-path fail, dung lai: co the agent dang hoc policy tinh, va khi do
Phase 11 se rong do thiet ke.
