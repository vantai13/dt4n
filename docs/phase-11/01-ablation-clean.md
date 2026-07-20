# Phase 11.1 - Config mask va verify ablation sach

**Ngay:** 2026-07-20
**Muc tieu:** truoc khi train Phase 11, chung minh hai nhanh AoI/noAoI khac
dung mot bien: thong tin AoI trong observation.

---

## 1. Config mask

Nhanh noAoI dung `rl/routing/configs/train_r_mask_aoi.yaml`, copy tu config
frozen that `rl/routing/configs/train_r_scenario.yaml`, khong copy tu
`train_r_v1.yaml`.

Khac biet hop le chi gom:

- `version: train_r_scenario` -> `version: train_r_mask_aoi`
- `train.mask_aoi: false` -> `train.mask_aoi: true`

Ly do: frozen v1 duoc train voi `train_r_scenario.yaml` (`episodes=2000`,
`load_cfg=SCENARIOS_TRAIN`). Neu copy tu config khac, ablation se lan them
confounder ve load/episode count.

## 2. Data flow cua mask

`train_r_mask_aoi.yaml` -> `train.mask_aoi=true` -> `train_r.make_train_env()`
-> `StalenessWrapper(..., mask_aoi_dims=True)` -> `_rebuild_obs()` ->
`mask_aoi(obs)` -> zero-out `obs[7]` va `obs[8]`.

State van la 9D, nen capacity cua agent khong doi.

## 3. Validation tests

Script test: `test/routing/test_ablation_clean.py`.

Cap nhat sau Lesson 11.2: test song hien tai chay tren cap config 6-scenario
`train_r_ablation_aoi.yaml` / `train_r_ablation_mask.yaml`. Logic verify van
la ba gate cua 11.1: dung luong bang nhau, mask that su che AoI, va z bien
thien.

Config diff ky vong:

```diff
-version: train_r_ablation_aoi
+version: train_r_ablation_mask
-  mask_aoi: false
+  mask_aoi: true
```

Lenh chay:

```bash
diff -u rl/routing/configs/train_r_ablation_aoi.yaml rl/routing/configs/train_r_ablation_mask.yaml
conda run -n sdn_rl python -m pytest -q test/routing/test_ablation_clean.py
```

Gate pass:

- Config diff chi co `version` va `mask_aoi`.
- `n_params` hai nhanh bang nhau: `4037 == 4037`.
- Nhanh mask co `obs[7]=obs[8]=0` tai `z=12`; nhanh AoI thay
  `obs[7]=1.0` tai `z=12`.
- Train z bien thien qua episode seed: `{0, 1, 3, 5, 8, 12}`.

## 4. Reviewer note: zero-out va permutation fallback

Reviewer co the hoi: zero-out co de lo thong tin qua vi tri khong, vi mang thay
hai dim AoI luon bang 0 o nhanh noAoI.

Tra loi: zero-out giu dung state_size va capacity, nen loai confounder dung
luong. Biet "toi dang bi mask" khong cung cap gia tri AoI that, nen khong giup
nhanh noAoI dung staleness de ra quyet dinh. Neu can doi chung manh hon, fallback
la permutation/shuffle AoI: giu phan bo AoI nhung pha tuong quan AoI voi state
episode, de kiem tra zero-out khong phai nguon ket qua.

Phase 11 dung zero-out lam thiet ke chinh; permutation la sensitivity check neu
reviewer yeu cau.
