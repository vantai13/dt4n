# LESSON 22.2 -- calib_set_v3

Ngay: 2026-08-13

Trang thai: chạm dữ liệu 21R thật. Không tính bất kỳ `q_hat` Phase 22 nào.

## 1. San pham

| File | Vai tro |
|---|---|
| `cert/build_calib_set_v3.py` | build calib set v3, them cot Phase 22 |
| `test/test_phase22_calibv3.py` | 10 golden/characterization tests |
| `results/phase-22/calib_set_v3_*.parquet` | calib set v3 cho 5 o + V3 split |
| `results/phase-22/calib_set_v3_*.json` | report gate va provenance |

## 2. Ket qua gate tren artifact

| Artifact | split | V22-1 worst | V22-2 | V22-3 | V22-5 min | pair_ok | corr(z,m_hat) | fail |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `calib_set_v3_cbr_0.700.json` | block | 0.0 | 0.0 | 0.0 | 403 | 1.000000000000 | -0.00058394 | [] |
| `calib_set_v3_h2_0.700.json` | block | 0.0 | 0.0 | 0.0 | 397 | 0.999480971453 | 0.00058542 | [] |
| `calib_set_v3_poisson_0.700.json` | block | 0.0 | 0.0 | 0.0 | 398 | 1.000000000000 | 0.00069627 | [] |
| `calib_set_v3_poisson_0.850.json` | block | 0.0 | 0.0 | 0.0 | 433 | 0.982649045698 | -0.00005007 | [] |
| `calib_set_v3_poisson_0.925.json` | block | 0.0 | 0.0 | 0.0 | 433 | 0.987571316422 | -0.00005666 | [] |
| `calib_set_v3_poisson_0.925_V3.json` | sample_V3 | n/a | 0.0 | 0.0 | 876 | 0.987571316422 | -0.00051604 | [] |

V22-1 la approval test voi artifact 21R da dong. Trong moi U0 block artifact,
24 cot dung chung khop v2 bit-for-bit: `max|diff| = 0.0`.

## 3. O chinh poisson@0.925

| Dai luong | Gia tri |
|---|---:|
| n_rows | 999945 |
| n_blocks | 1000 |
| n_calib_blocks | 500 |
| n_test_blocks | 500 |
| pair_ok | 0.9875713164224033 |
| m_hat_bin_edges | [6.1732754707, 13.0294189453, 21.9347305298] ms |
| m_hat bin shares (calib) | [0.249811, 0.250055, 0.250035, 0.250099] |
| min n_block `(z_bin x m_hat_bin)` | 433 |
| corr(z_s, m_hat) calib | -0.00005666 |

Phan bo `m_hat_bin` theo `z_bin` gan nhu truc giao:

| z_bin | m0 | m1 | m2 | m3 |
|---:|---:|---:|---:|---:|
| 0 | 24.98 | 25.00 | 25.02 | 25.00 |
| 1 | 24.98 | 25.00 | 25.02 | 25.00 |
| 2 | 24.98 | 25.00 | 25.02 | 25.00 |
| 3 | 24.9822 | 25.0108 | 24.9876 | 25.0194 |

Ket luan: R22-1 dong voi bang chung. Hai chieu Mondrian `(z_bin, m_hat_bin)`
khong lam rong o giao; min block 433 so voi nguong ly thuyet 9.

## 4. Staleness path diagnostic

Tren `poisson@0.925`, seed 101, cua so diagnostic 19889 hang:

| Ho so | max abs row-shift vs rho-shift |
|---|---:|
| U0 | 0.0 ms |
| U1 | 10.6448293764 ms |
| U2 | 9.1490973627 ms |
| PC4 | 8.1034984622 ms |

Sai implementation "shift theo offset trung binh" lech:

```text
max_abs_per_link_vs_mean_shift_U1 = 5.5730414736 ms
```

Ket luan: dich bang chi phi khong tuong duong dich `rho` theo tung link. Sai
khac cung co voi `q_hat(B0)` cua 21R, nen Lesson 22.7 bat buoc dung rho-shift.

## 5. a_star_rank

Toan tap `poisson@0.925`:

| Rank cua a* theo twin | Share |
|---:|---:|
| 1 | 0.7791648541 |
| 2 | 0.2084064624 |
| 3 | 0.0123246779 |
| 4 | 0.0001040057 |

Theo z-bin:

| z_bin | rank 1 | rank 2 | rank 3 | rank 4 |
|---:|---:|---:|---:|---:|
| 0 | 0.880556 | 0.116122 | 0.003322 | 0.000000 |
| 1 | 0.836530 | 0.157535 | 0.005930 | 0.000005 |
| 2 | 0.786945 | 0.201980 | 0.011075 | 0.000000 |
| 3 | 0.735721 | 0.247166 | 0.016912 | 0.000202 |

Lo hong P22-A tang theo tuoi: `rank >= 3` la 0.3322% o B0 va 1.7114% o B3.
Rank 4 gan nhu khong ton tai, nhung khong duoc doi P3 thanh top-3 sau khi da
nhin du lieu. Ghi Future Work: chung nhan top-3 can prereg rieng.

## 6. Cot moi

| Cot | Nghia |
|---|---|
| `s_sim` | max-score dong thoi |
| `s_pair_1..3` | score tung rank slot |
| `m_hat_1..3` | twin gap tung rank slot |
| `m_true_1..3` | true gap tung rank slot |
| `a_rank_1..3` | danh tinh duong o hang 2,3,4 |
| `a_star_rank` | rank twin gan cho action that tot nhat |
| `m_hat_bin` | quantile bin tinh tren calib |
| `aoi_profile` | U0/U1/U2/PC4 |

Khong luu `z_s_per_link`; metadata report gom `link_order`, offset danh nghia,
offset step, va offset thuc te.

## 7. Tests

```text
/tmp/dt4n-venv/bin/python -m pytest test/test_phase22_calibv3.py -q
10 passed in 5.83s

/tmp/dt4n-venv/bin/python -m pytest -q
670 passed, 4 skipped in 216.18s
```
