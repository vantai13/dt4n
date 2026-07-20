# Phase 11.3 - Eval z-sweep, paired tests, and plots

**Ngay:** 2026-07-20
**Muc tieu:** danh gia 10 checkpoint tren dai z, sau do doc ket qua theo H1/H2/H3.

---

## 1. Eval dải z

Chay:

```bash
conda activate sdn_rl
python scripts/eval_ablation_zsweep.py
```

Output:

- `results/ablation/zsweep.csv`
- 60 dong: `2 branch x 5 seed x 6 z`

Ghi chu quan trong: script dung `make_eval_env(cfg, seed, z)`, nen nhanh `mask`
van bi che AoI luc eval. Khong duoc eval mask-agent tren observation co AoI.

## 2. Analyze paired tests

Chay:

```bash
python scripts/analyze_ablation.py
```

Output:

- in bang return, wrong_rate, safe_path_freq
- `results/ablation/analysis_summary.txt`
- `results/ablation/analysis_by_z.csv`

Doc theo thu tu:

1. z=0 truoc: H1 can hue (`p > 0.05`, diff gan 0).
2. z cao sau: H2 can `mean_diff = return_aoi - return_mask > 0`.
3. wrong_rate: o z cao, neu `wrong_aoi < wrong_mask`, agent-AoI thang bang cach
   chon duong sai it hon.
4. effect size: doc `Cohen_d`; voi n=5, dung ca xu huong va effect size, khong
   chi nhin p-value le.

Neu z=0 da khac co y nghia, dung lai va dieu tra confounder truoc khi tuyen bo
nhan-qua.

## 3. Plot

Chay:

```bash
python scripts/plot_ablation.py
```

Output:

- `results/ablation/fig_return.png`
- `results/ablation/fig_wrong.png`
- `results/ablation/fig_safe.png`

`fig_return.png` co vach `tau ~= 2.0s` tu Phase 10 de doi chieu breaking point.

## 4. Bao cao lai de doc ket luan

Gui lai:

```bash
cat results/ablation/analysis_summary.txt
```

Neu can soi file:

```bash
head -80 results/ablation/zsweep.csv
cat results/ablation/analysis_by_z.csv
```
