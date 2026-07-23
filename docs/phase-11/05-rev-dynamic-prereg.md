# Phase 11 Rev - Pre-registration (dynamic-heavy staging)

**Ngay ky:** 2026-07-23

## Ly Do Rev

Ba lan train truoc (symmetric / mild / Goldilocks) deu cho `VoI <= 0`.
`AoI-dependence gap` probe giai thich nguyen nhan bang so: cac scenario tinh
khong co action split theo AoI, va Goldilocks bi over-hedge sang direct F.

| design | gap (z>=1) | F\|fresh | F\|aware |
|---|---:|---:|---:|
| S1-S4 static | 0.000 | 0.430 | 0.430 |
| S1-S6 (33% dynamic) | 0.180-0.225 | 0.345 | 0.510-0.545 |
| Goldilocks | 0.000-0.020 | 0.665 | 0.665-0.675 |
| **DYNAMIC (75%)** | **0.315-0.333** | **0.160** | **0.460-0.477** |

Ket luan chan doan: scenario tinh cho gap = 0 do toan hoc (`drift_sigma = 0`
nen anh cu van bang su that). Goldilocks cho gap gan 0 do direct F da thang
truoc khi xet AoI. Chi thiet ke dynamic-heavy tao ra khoang trong that.

## Gia Thuyet

H1: `VoI(AoI=0) ~= 0` (`paired t-test p > 0.05`).

H2: `VoI(AoI >= 1.5s) > 0` (`paired t-test p < 0.05`).

H3: agent-AoI co `safe_path_freq` / `wrong_excess` tach o AoI cao.

## Hinh Dang Du Kien

Gap phang theo z (`0.315 -> 0.333`, khong tang manh), nen du doan VoI bao hoa,
khong bat buoc co dang chuong. Ket qua nay khop voi pre-registration goc muc 2
phuong an (b): tail phang o muc cao neu biet minh mu va rut ve hanh vi an toan
van huu ich.

## Bang Chung Agent Doc AoI

`policy_aoi_s0.pt` co Q-values FLIP tu viaE sang F khi `aoi_s` tang, voi swing
`2.22` tren case "E looks free". Agent co doc AoI; neu dynamic-heavy ablation
van hue, nguyen nhan khong phai agent khong doc duoc.

`policy_mask_s0.pt` cung FLIP khi bi dua AoI nonzero raw/OOD. Day khong phai
control hop le cho nhanh mask, vi eval that luon goi `mask_aoi(state)` truoc
khi agent thay observation. Control can dung: `probe_agent_reads_aoi.py
--mask-input`, trong do state sau mask phai giong nhau va Q-values phai phang.

## Gate

`LOAD_CFG_DYNAMIC` dat `gap >= 0.25` o moi z cao trong ban nhe va ban nang:

- default probe: `gap = 0.315-0.330`
- heavy probe (`--cases 400 --mc-samples 200`): `gap = 0.315-0.333`

**Quyet dinh:** GO train dynamic-heavy pair, `2 branch x 5 seed`.

## Config Khoa Truoc Train

- AoI: `rl/routing/configs/train_r_dyn_aoi.yaml`
- mask: `rl/routing/configs/train_r_dyn_mask.yaml`
- Hai config khac dung `version` va `train.mask_aoi`
- `env.load_cfg = LOAD_CFG_DYNAMIC`
- `train.episodes = 2000`
- `z_steps_choices = [0, 1, 3, 5, 8, 12]`

## Lenh Chay

```bash
conda activate sdn_rl
cd /home/ubuntu/dt4n

python3 measurements/probe_agent_reads_aoi.py \
  --ckpt frozen_policies/huong_a/policy_mask_s0.pt \
  --mask-input

python3 -m pytest -q test/routing/test_ablation_clean.py
ROUTE_REPRO_CONFIG=rl/routing/configs/train_r_dyn_aoi.yaml \
ROUTE_REPRO_ROOT_PREFIX=results/repro_dyn \
  python3 test/routing/test_train_repro_ablation.py

mkdir -p results/ablation_dyn
./scripts/train_ablation_10run.sh train_r_dyn results/ablation_dyn \
  2>&1 | tee results/ablation_dyn/train_log.txt

python3 scripts/eval_ablation_zsweep.py \
  --root results/ablation_dyn \
  --out results/ablation_dyn/zsweep.csv
python3 scripts/analyze_ablation.py \
  --csv results/ablation_dyn/zsweep.csv \
  --out results/ablation_dyn/analysis_summary.txt \
  --stats-csv results/ablation_dyn/analysis_by_z.csv
python3 scripts/plot_ablation.py \
  --csv results/ablation_dyn/zsweep.csv \
  --out-dir results/ablation_dyn
```
