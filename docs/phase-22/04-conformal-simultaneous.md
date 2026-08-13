# LESSON 22.3 -- conformal_simultaneous.py

Ngay: 2026-08-13

Trang thai: da cham du lieu Phase 22 v3 that va da tinh qhat dong thoi.

## 1. San pham

| File | Vai tro |
|---|---|
| `cert/conformal_simultaneous.py` | fit/eval 4 thu tuc simultaneous conformal |
| `test/test_phase22_conformalsim.py` | 13 golden/characterization tests tren artifact v3 |
| `results/phase-22/conformal_sim_*.json` | report qhat, coverage, gate, controls |
| `docs/phase-22/00b-amendment-1.md` | amendment sau Lesson 22.3 |

Thu tuc confirmatory:

```text
uncorrected  : alpha tren tung slot, negative control
bonferroni   : alpha/(K-1)
sidak        : 1 - (1-alpha)^(1/(K-1))
maxscore     : qhat cua s_sim = max_j s_pair_j
```

## 2. O chinh poisson@0.925

Input: `results/phase-22/calib_set_v3_poisson_0.925.parquet`

| Dai luong | Gia tri |
|---|---:|
| n_rows | 999945 |
| n_blocks | 1000 |
| n_calib_blocks | 500 |
| n_test_blocks | 500 |
| alpha | 0.10 |
| K-1 | 3 |

### Coverage

| Thu tuc | simultaneous coverage | pointwise coverage slot 1/2/3 |
|---|---:|---|
| uncorrected | 0.770631 | [0.908684, 0.897867, 0.907376] |
| bonferroni | 0.925295 | [0.973414, 0.970668, 0.971404] |
| sidak | 0.920527 | [0.971486, 0.968500, 0.969622] |
| maxscore | 0.906662 | [0.974128, 0.964588, 0.954181] |

Ket luan gate:

| Gate | Ket qua |
|---|---|
| G22-4 corrected simultaneous coverage >= 0.88 | PASS |
| G22-5 negative control collapses | PASS |
| V22-6 slot1 reproduces 21R qhat exactly | PASS |

### qhat theo z-bin

| Thu tuc | B0 | B1 | B2 | B3 |
|---|---|---|---|---|
| uncorrected | [11.5878, 11.9642, 12.8007] | [15.6348, 16.1064, 17.2710] | [19.6461, 20.2414, 21.4442] | [24.3222, 25.1456, 27.3104] |
| bonferroni | [15.1842, 15.7504, 16.8561] | [20.6047, 21.3750, 22.8187] | [25.5811, 26.7319, 27.9769] | [32.1418, 33.4594, 35.8064] |
| sidak | [15.0121, 15.5480, 16.6354] | [20.3379, 21.0841, 22.5661] | [25.3315, 26.3860, 27.6775] | [31.7473, 33.0497, 35.3680] |
| maxscore | [15.2720, 15.2720, 15.2720] | [20.7210, 20.7210, 20.7210] | [25.7501, 25.7501, 25.7501] | [32.2521, 32.2521, 32.2521] |

V22-6:

```text
max_abs_diff(slot1 qhat, 21R qhat) = 0.0
qhat_21R = [11.587758, 15.634801, 19.646107, 24.322243]
```

## 3. Van hanh tai kappa=1

| Thu tuc | accept | P(wrong\|accept) | P(lose rank2\|accept) | slot1 decides |
|---|---:|---:|---:|---:|
| uncorrected | 0.283545 | 0.032992 | 0.030741 | 1.000000 |
| sidak | 0.172093 | 0.014493 | 0.013726 | 1.000000 |
| bonferroni | 0.167857 | 0.013691 | 0.013107 | 0.999778 |
| maxscore | 0.166569 | 0.013665 | 0.013077 | 1.000000 |

Slot 1 gan nhu quyet dinh toan bo rejection. Voi bonferroni:

```text
reject rates slot1/2/3 = [0.831921, 0.266648, 0.020223]
```

Voi maxscore:

```text
reject rates slot1/2/3 = [0.833431, 0.245688, 0.013479]
```

He qua: maxscore co coverage dep nhat, nhung operational acceptance tai
`kappa=1` lai nho nhat trong 3 thu tuc corrected vi slot 1 bi qhat chung chi
phoi.

## 4. Du doan vs do duoc

| # | Du doan | Do duoc | Ket qua |
|---:|---|---:|---|
| 1 | bonf B0 / 21R in [1.28, 1.33] | 1.3104 | HIT |
| 2 | sidak B0 / 21R in [1.27, 1.32] | 1.2955 | HIT |
| 3 | maxscore B0 / 21R in [1.22, 1.30] | 1.3179 | MISS high |
| 4 | maxscore / bonf in [0.94, 0.98] | slot1 1.0058, slot3 0.9060 | MISS / ill-posed |
| 5 | bonf coverage 0.90 +/- 0.02 | 0.9253 | MISS just outside |
| 6 | pointwise corrected 0.955 - 0.975 | 0.9542 - 0.9741 | HIT |
| 7 | uncorrected simultaneous 0.74 - 0.80 | 0.7706 | HIT |
| 8 | corr slots 0.20 - 0.35 | whole 0.266, within-bin 0.198 - 0.212 | HIT |

Tong ket: 5 HIT / 3 MISS. Miss lon nhat la gia dinh "mot qhat maxscore gan
bonferroni theo moi slot". Du lieu that co slot heterogeneity: slot cang xa
rank 1 thi score cang lon.

## 5. Co che

RMS score tren toan tap `poisson@0.925`:

| Score | RMS |
|---|---:|
| s_pair_1 | 12.5823 |
| s_pair_2 | 13.2181 |
| s_pair_3 | 14.0347 |
| s_sim | 18.5769 |

Bridge half-normal cho `s_sim`:

| z-bin | qhat maxscore | rms(s_sim) | qhat/(1.645*rms) |
|---:|---:|---:|---:|
| B0 | 15.2720 | 10.2033 | 0.9100 |
| B1 | 20.7210 | 13.8064 | 0.9124 |
| B2 | 25.7501 | 17.2793 | 0.9060 |
| B3 | 32.2521 | 21.5979 | 0.9079 |

P3c: `1.645*rms` la bridge phu thuoc score. Voi `s_sim`, chi dung de giai
thich ratio theo bin, khong dung lam du doan absolute qhat confirmatory.

## 6. Controls

### Seed validation

| Thu tuc | Coverage | Pass |
|---|---:|---|
| bonferroni | 0.918926 | True |
| maxscore | 0.904975 | True |

### PC22-3 variance positive control

| Dai luong | B0 | B1 | B2 | B3 |
|---|---:|---:|---:|---:|
| block mean | 0.901413 | 0.901905 | 0.900895 | 0.900305 |
| row mean | 0.901806 | 0.901459 | 0.901449 | 0.900982 |
| block SD | 0.004432 | 0.004304 | 0.004190 | 0.004332 |
| row SD | 0.001462 | 0.001368 | 0.001123 | 0.000802 |

```text
sd_ratio_row_over_block = 0.275563
pass_PC22_3 = True
```

### Variant A/C ratios vs Variant B

| Thu tuc | Variant A | Variant C |
|---|---|---|
| bonferroni | [1.0060, 0.9965, 0.9757, 1.0053] | [1.4910, 1.5797, 1.6160, 1.6285] |
| maxscore | [1.0426, 0.9761, 0.9616, 1.0401] | [1.6106, 1.6626, 1.6143, 1.7037] |

### Bootstrap maxscore qhat CI

Block bootstrap: 200 draws.

| z-bin | mean | CI95 |
|---:|---:|---|
| B0 | 15.2778 | [15.0584, 15.5054] |
| B1 | 20.7224 | [20.4248, 21.0348] |
| B2 | 25.7673 | [25.2925, 26.1418] |
| B3 | 32.2376 | [31.8204, 32.6735] |

## 7. Sweep tat ca artifact v3

| Artifact | Cell | uncorrected | bonferroni | sidak | maxscore |
|---|---|---:|---:|---:|---:|
| `conformal_sim_cbr_0.700.json` | cbr@0.700 | 0.794418 | 0.927119 | 0.922565 | 0.899829 |
| `conformal_sim_h2_0.700.json` | h2@0.700 | 0.774305 | 0.923099 | 0.918393 | 0.902250 |
| `conformal_sim_poisson_0.700.json` | poisson@0.700 | 0.760516 | 0.920885 | 0.915798 | 0.901658 |
| `conformal_sim_poisson_0.850.json` | poisson@0.850 | 0.759246 | 0.922649 | 0.917499 | 0.905742 |
| `conformal_sim_poisson_0.925.json` | poisson@0.925 | 0.770631 | 0.925295 | 0.920527 | 0.906662 |
| `conformal_sim_poisson_0.925_V3.json` | poisson@0.925_V3 | 0.762819 | 0.915724 | 0.913221 | 0.900139 |

Tat ca report tren co:

```text
G22_4_corrected_coverage_ge_0p88 = True
G22_5_negative_control_collapses = True
V22_6_bridge_to_21R_exact = True
```

## 8. Tests

```text
/tmp/dt4n-venv/bin/python -m pytest test/test_phase22_conformalsim.py -q
13 passed in 21.73s

/tmp/dt4n-venv/bin/python -m pytest -q test/test_phase22_simscore.py test/test_phase22_calibv3.py test/test_phase22_conformalsim.py
46 passed in 29.62s

/tmp/dt4n-venv/bin/python -m pytest -q
683 passed, 4 skipped in 199.23s (0:03:19)
```
