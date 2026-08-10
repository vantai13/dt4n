# Phase 20R -- Bay cong, doc duoi bien sai so he thong

> **Cap nhat 2026-08-10.** Hang G6-PRE van la contrast chuyen topology
> `A' - A`. Cascade thuc su `C - sum(B)` da duoc do rieng trong Lesson
> 20R.6-v2 va bao cao o hang G6-CASCADE/G6-BAND ben duoi.

Ngay: 2026-08-10

Cot "Duoi bien" tra loi mot cau: *neu phan du cong tinh do duoc o Lesson 20R.6
la THAT, ket qua co doi khong?* Bien duoc tinh o HAI DAU CI90 cua phan du
(`measurements/additivity_band.py`), tai diem van hanh sawtooth -- tuc dung
estimator da sinh ra cac con so headline.

Nguon cu: `results/phase-20R/additivity_band_sawtooth.json`,
`results/phase-20R/g6_differential_inband.json`,
`results/phase-20R/additivity_check_inband_bg.json`.

Nguon cascade v2: `results/phase-20R/residual_cascade.json`,
`results/phase-20R/band_v2_cascade.json`,
`results/phase-20R/breakdown_scan_cascade.json`.

| Gate | Tieu chi | Ket qua goc | Duoi bien sai so cong tinh | Phan quyet |
|---|---|---|---|---|
| G1 | `err(0.55)` trong `[0.05, 0.40]` | DAT tren 6 o | `d err` trong `[-0.026, +0.022]`; khong o nao ra khoi khoang | **DAT** |
| G2 | `d_sla_lower >= 0.03` | DAT tren 6 o | 5/6 o giu DAT o dau xau nhat; `poisson @ 0.700` LAT sang TRUOT | **DAT co co** |
| G3 | `Spearman(err, z) > 0`, `p < 0.05` | DAT moi o | bien gan nhu khong doi theo `z` -> thu tu theo `z` giu nguyen | **DAT** |
| G4 | `Spearman(err, rho_bar) > 0` | FAIL co chu dich | khong lien quan (bien khong doi hinh dang `err(rho_bar)`) | **FAIL nhu da ky** |
| G5 | `NC1b = 0`, `NC2 = 0.747-0.751`, `PC1 = 0` | DAT | control noi bo, khong di qua bang tra path | **DAT** |
| G6-PRE | **dieu kien tien quyet** cua cong tinh: chuyen topology `A' - A` | ABS: h2 FAIL / poisson (loss PASS, delay PASS, **cost INCONCLUSIVE**)<br>DIFF: h2 INCONCLUSIVE / poisson PASS | -- | **co dieu kien** |
| G6-CASCADE | cong tinh thuc su: `C - sum(B)` | `r_path` am 4/4: poisson/loss `-0.009522` CI90 `[-0.010135,-0.008908]`; poisson/delay `-0.746400 ms`; h2/loss `-0.009351`; h2/delay `-0.449241 ms` | Dau am khop PBOO; twin cong tinh bao thu theo huong da ky | **do xong, bao thu co gioi han** |
| G6-BAND | band/scan cascade `n=120000` | `safety_published=0.868750`, binding `poisson/loss/common_mode`; `first_broken=K4_path_ranking_preserved` tai `poisson@0.925` | `clip_ratio=43.20%` nen bien am la can duoi; `differential/full/joint` unsupported vi residual muc duong | **LAT K4 trong pham vi cascade** |
| G7 | moi CI dung `se_batch` | DAT | khong doi | **DAT** |
| QS-DELAY | tua tinh, kenh delay | Phase T `err_dyn` CI95 [-0.068, -0.000] ms | gate song toi -2.0 ms/link = 29x | **DAT** |
| QS-LOSS | tua tinh, kenh loss | **CHUA DO** | nguong sup do `[-1e-3, +5e-5]` (8/8 o), `[-1e-3, +1e-3]` (7/8 o) | **CHUA DANH GIA** |

## Bang bien day du (sawtooth, 5 seed, n = 120k)

```text
mode     rho_bar     F  n_up |      err  bien d err            |   d_sla  bien d d_sla          | G2 xau nhat
h2         0.700   2.8   2/4 |   0.2997  [+0.0023, +0.0217]    |  0.0897  [-0.0374, -0.0088]    | DAT       0.0523
h2         0.850   2.5   2/4 |   0.2515  [+0.0000, +0.0003]    |  0.0688  [-0.0134, -0.0014]    | DAT       0.0554
h2         0.925   0.5   3/4 |   0.0726  [-0.0000, -0.0000]    |  0.0158  [-0.0037, +0.0023]    | ngoai tap 0.0121
h2         0.960   1.0   3/4 |   0.0014  [-0.0000, +0.0000]    |  0.0000  [+0.0000, +0.0000]    | ngoai tap 0.0001
poisson    0.700   3.9   1/4 |   0.1375  [-0.0261, -0.0000]    |  0.0429  [-0.0429, +0.0015]    | TRUOT     0.0000  <- LAT
poisson    0.850   0.8   2/4 |   0.3339  [+0.0000, +0.0065]    |  0.1188  [-0.0114, +0.0037]    | DAT       0.1073
poisson    0.925   0.5   2/4 |   0.2950  [-0.0000, +0.0011]    |  0.0986  [-0.0072, +0.0020]    | DAT       0.0914
poisson    0.960   1.9   2/4 |   0.1909  [-0.0000, +0.0000]    |  0.0551  [-0.0091, +0.0021]    | DAT       0.0460
```

`ngoai tap` = `d_sla` goc da duoi 0.03 truoc khi ap bien, nen o do chua bao gio
nam trong tap sau o cua G2. Chi mot chuyen tiep `DAT -> TRUOT` moi la do bien.

## Kiem tu ve

Doi seed va gap doi mau deu cho cung ket luan (6/8 o trong tap G2, dung 1 o lat):

```bash
python3 -m measurements.additivity_band --seeds 201,202,203,204,205
python3 -m measurements.additivity_band --n 240000
```

Bien thien cua `d_sla` giua ba lan chay < 4%.

## Huong lech -- va phan bat loi phai ghi

```text
d_sla: bien nam HOAN TOAN duoi 0 o 2/8 o  -> o do con so cong bo la CAN TREN.
       Cac o con lai bien HAI CHIEU -> khong duoc phat bieu "bao thu".
err  : dau tren cua bien DUONG o 5/8 o    -> o do con so cong bo la CAN DUOI.
       Dac biet h2 @ 0.700: `d err` toi +0.0217 (+7.2% tuong doi). KHONG bao thu.
```

Ca hai chieu deu duoc bao cao. Khong duoc chi trich dan chieu co loi.
