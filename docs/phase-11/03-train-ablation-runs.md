# Phase 11.2 - Train 10 run va khoa manifest

**Ngay:** 2026-07-20
**Muc tieu:** chay that `2 nhanh x 5 seed`, sau khi golden test tai lap pass.

---

## 1. Golden test tai lap

Chay truoc moi batch train dai:

```bash
conda activate sdn_rl
python test/routing/test_train_repro_ablation.py
```

Ky vong:

```text
run A[:5] = [...]
run B[:5] = [...]
PASS - same seed -> identical train_return sequence
```

Neu fail, dung lai. Paired-seed ablation khong co gia tri neu cung seed ma train
khong tai lap.

## 1b. Tuy chon: do std_agent tren LOAD_CFG_ABLATION

Gate chinh van la SNR Phase 10 tren `LOAD_CFG_SWEEP`, nhung neu muon biet nhieu
nen tren load 6 scenario:

```bash
python scripts/measure_std_ablation.py
```

Ky vong: `std_agent` co the khac `0.0450`, nhung SNR tu `0.3283/std` van nen
lon hon nguong GO `3`.

## 2. Train 10 run

Chay:

```bash
mkdir -p results/ablation
./scripts/train_ablation_10run.sh 2>&1 | tee results/ablation/train_log.txt
```

Script se train:

- branch `aoi`, seed `0..4`
- branch `mask`, seed `0..4`

Moi run ghi `train.json`, `episodes.csv`, `eval.csv`, `model.pt`. Manifest
`train.json` co them:

- `ablation_branch`
- `link_model_version`
- `link_model_sha256`

## 3. Verify sau train

Chay:

```bash
python scripts/verify_ablation_runs.py
```

Gate pass:

- co dung 10 `train.json`
- moi branch co seed `0..4`
- `aoi` seed k va `mask` seed k co cung `train_seeds`
- ca 10 run co cung `link_model_version` va `link_model_sha256`
- hai nhanh cung `LOAD_CFG_ABLATION`, cung z choices, cung episodes; khac
  `mask_aoi`

Neu pass, dynamics da khoa dung Muc 3 va paired seed hop le.

## 4. Doc log nhanh

Trong tung run:

- `loss=n/a` dau train la binh thuong vi `warmup_steps=500`.
- `z=` phai thay doi qua cac dong.
- `baseline(end) drift` phai nho hon `NOISE_FLOOR=0.04`.
- `done in Xs` cho toc do that moi run.

Sau khi 10 run xong, sang Phase 11.3: paired eval, t-test, va ve hinh VoI.
