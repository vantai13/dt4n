# Phase 11.2 - Load 6 scenario va chay verify truoc train

**Ngay:** 2026-07-20
**Muc tieu:** dua S5-S6 dynamic vao train Phase 11 de AoI co thong tin that su,
sau do verify ablation sach truoc khi train dai.

---

## 1. Kiem tra 6 scenario bang mat

Script:

```bash
python3 scripts/inspect_scenarios.py
```

Doc ket qua:

- S1-S4 phai co `drift=0.00` va quy dao C->E khong doi.
- S5-S6 phai co `drift=0.20` va quy dao C->E thay doi qua cac buoc.

Ket luan can thay: Phase 9 chi train S1-S4 tinh; Phase 11 them S5-S6 dong de
staleness co the lam thong tin cu khac su that trong episode.

## 2. Load config moi

`LOAD_CFG_ABLATION` trong `rl/routing/topology_r.py` gom:

- `SCENARIOS_TRAIN`: S1-S4 tinh
- `SCENARIOS_DYNAMIC`: S5-S6 dong

Khong dat `drift_sigma` o cap cha. Moi scenario tu giu `drift_sigma` rieng:
S1-S4 = 0, S5-S6 = 0.20.

Kiem tra:

```bash
python3 - <<'PY'
from rl.routing.topology_r import LOAD_CFG_ABLATION
mix = LOAD_CFG_ABLATION['scenario_mix']
print('scenario_mix:', mix)
print('so scenario:', len(mix))
print('parent drift_sigma:', LOAD_CFG_ABLATION.get('drift_sigma'))
assert len(mix) == 6
assert LOAD_CFG_ABLATION.get('drift_sigma') is None
print('OK')
PY
```

## 3. Config hai nhanh ablation

Hai file:

- `rl/routing/configs/train_r_ablation_aoi.yaml`
- `rl/routing/configs/train_r_ablation_mask.yaml`

Kiem tra diff:

```bash
diff -u rl/routing/configs/train_r_ablation_aoi.yaml rl/routing/configs/train_r_ablation_mask.yaml
```

Diff hop le chi co:

```diff
-version: train_r_ablation_aoi
+version: train_r_ablation_mask
-  mask_aoi: false
+  mask_aoi: true
```

## 4. Verify ablation sach

Chay:

```bash
conda activate sdn_rl
python -m pytest -q test/routing/test_ablation_clean.py
```

Ky vong:

```text
5 passed
```

Test nay chan cac confounder:

- load 6 scenario du S1-S6, S5-S6 van dynamic
- config pair khac dung `version` va `mask_aoi`
- n_params bang nhau (`4037 == 4037`)
- nhanh mask thay `obs[7]=obs[8]=0`; nhanh AoI thay tin hieu AoI tai z cao
- z train bien thien `{0, 1, 3, 5, 8, 12}`

## 5. Chay thu 1 seed ngan de do thoi gian

Chay 200 episode nhanh AoI:

```bash
time python -m rl.routing.train_r \
  --config rl/routing/configs/train_r_ablation_aoi.yaml \
  --seed 0 \
  --episodes 200 \
  --print-every 50
```

Doc log:

- `z=` phai thay thay doi qua cac dong.
- `eps=` phai giam dan.
- `train10` nen tang roi bot dao dong.
- dong cuoi `done in Xs` cho thoi gian that.

Tinh ngan sach:

`T_moi_episode = X / 200`

`Tong Phase 11 ~= T_moi_episode x 2000 x 10 run`

Ghi lai con so nay truoc khi train that 10 run.

Ghi chu doc log:

- `loss=n/a` o cac moc dau la binh thuong vi `warmup_steps=500`; moi episode chi
  co vai transition, nen phai den khoang ep 150 moi thuong thay loss.
- `baseline(end) drift: 0.0000` hoac rat nho nghia la eval baseline on dinh,
  khong leak state giua dau/cuoi train.
