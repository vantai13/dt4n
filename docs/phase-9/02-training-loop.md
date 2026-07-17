# Lesson 9.2 - Training Loop + Seed Khoa

## Sua sai trong tai lieu

PHASE_9.md noi A2 khong co `set_global_seed` va khong tach agent seed voi
scenario seed. Doc code thi hai y nay sai:

- `rl/a2/train_a2.py` co `set_global_seed()`.
- `set_global_seed(args.seed)` duoc goi truoc khi tao `DQNAgent`.
- `--seed` la agent seed; `--train-seed-start` la scenario seed.

Ket luan: tai lieu la checklist gia thuyet, khong phai su that. Do truoc khi
sua.

## Loi seed that cua A2

A2 tao `train_seeds` chi tu `train_seed_start`, khong phu thuoc `--seed`. Nam
agent seed khac nhau gap cung chuoi scenario. Khi do `std` chu yeu do khoi tao
mang, khong gom phuong sai scenario, nen error bar co nguy co hep hon su that.

Routing dung:

```python
base = train_seed_start + agent_seed * train_seed_stride
train_seeds = range(base, base + episodes)
```

`train_seed_stride = 100000` de cac dai seed khong chong lan khi tang so
episode.

Eval seeds thi nguoc lai: co dinh cho moi agent/policy de paired comparison.

## QD-2: Train voi z ngau nhien

Train z=0 lam hai chieu AoI thanh hang so:

- `aoi_norm std = 0`
- `data_fresh std = 0`

Khi mot chieu state la hang so, `I(aoi_norm; return) = 0`: no khong mang thong
tin ve ket qua. Phase 11 ablation se rong do thiet ke, khong phai do agent kem.

Quyet dinh:

- Train: `z_steps_choices = [0, 1, 3, 5, 8, 12]`
- RQ1 eval: `z = 0`
- Phase 10/11: quet z

## Bootstrap

Routing co ket thuc that: toi `DST` thi `terminated=True`, khong bootstrap.
Voi timeout/truncation, state da co `hop_progress`, nen day la finite-horizon
MDP tuong minh. O gioi han thoi gian, khong con reward tuong lai trong bai toan
nay, nen:

```python
done_for_bootstrap = terminated or truncated
```

Ly le nay chi dung vi state co chieu thoi gian.

## Run Identity

Moi run duoc dat ten:

```text
r_seed{seed}_{git_hash}_{config_hash}
```

`git_hash` co hau to `-dirty` neu working tree co thay doi. Dirty flag quan
trong vi git hash sach chi noi commit cuoi, khong noi code chua commit da chay.

## Files

- `rl/routing/configs/train_r_v1.yaml`
- `rl/routing/train_r.py`
- `test/routing/test_train_repro.py`

## Validation

```bash
conda activate sdn_rl
python -m pytest test/routing/test_train_repro.py -v
python rl/routing/train_r.py --seed 0 --episodes 20 --out-root /tmp/dt4n_train_smoke
```

Repro:

```bash
python rl/routing/train_r.py --seed 0 --episodes 30 --out-root /tmp/rep1
python rl/routing/train_r.py --seed 0 --episodes 30 --out-root /tmp/rep2
python rl/routing/train_r.py --seed 1 --episodes 30 --out-root /tmp/rep3
```

Kiem tra:

- `/tmp/rep1/*/train.json` va `/tmp/rep2/*/train.json` co
  `epsilon_trace_head` giong nhau.
- `/tmp/rep1/*/train.json` va `/tmp/rep3/*/train.json` co `train_seeds` khac
  nhau nhung `val_seeds` giong nhau.
- `baseline_drift` nho hon `noise_floor` hoac phai ghi ro ke hoach xu ly.
