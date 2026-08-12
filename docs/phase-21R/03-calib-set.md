# Lesson 21R.2 -- build_calib_set_v2.py

Ngay hoan thanh: 2026-08-12

## Artifact

Source:

```text
cert/build_calib_set_v2.py
test/test_phase21r_calib.py
```

Results:

```text
results/phase-21R/calib_set_poisson_0.925.parquet
results/phase-21R/calib_set_poisson_0.925.json
results/phase-21R/calib_set_poisson_0.925_V3.parquet
results/phase-21R/calib_set_poisson_0.925_V3.json
results/phase-21R/calib_set_poisson_0.850.parquet
results/phase-21R/calib_set_poisson_0.850.json
results/phase-21R/calib_set_h2_0.700.parquet
results/phase-21R/calib_set_h2_0.700.json
results/phase-21R/calib_set_cbr_0.700.parquet
results/phase-21R/calib_set_cbr_0.700.json
results/phase-21R/calib_set_poisson_0.700.parquet
results/phase-21R/calib_set_poisson_0.700.json
results/phase-21R/calib_set_h2_0.850.parquet
results/phase-21R/calib_set_h2_0.850.json
results/phase-21R/calib_set_h2_0.925.parquet
results/phase-21R/calib_set_h2_0.925.json
results/phase-21R/anchor.json
```

## Schema

Mot hang la mot thoi diem quyet dinh. Don vi thong ke la block 5 s.

```text
seed, block_id, t_idx, z_s, z_bin, z_bin2
a1, a2, a_twin, a_star
m_hat, m_true, m_mid
s_margin, s_signed, s_vs_a1, s_maxabs
gap_true, regret, wrong, pair_ok, viol_twin, viol_star
is_calib
```

`m_mid` dung dung cap `(a1,a2)` chon theo `y_hat` cu. Validate khoa dong nhat:

```text
(m_true - m_mid) + (m_mid - m_hat) = m_true - m_hat
```

## Test

Lenh:

```bash
/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_calib.py test/test_phase21r_margin.py -q
```

Ket qua:

```text
22 passed
```

Full suite:

```bash
/tmp/dt4n-venv/bin/python -m pytest -q
```

```text
556 passed, 1 skipped, 2 warnings in 159.09s (0:02:39)
```

## V5

`V5_compare_20R.max_abs_diff = 0.0` cho moi artifact duoc sinh. Cua so dung la
`np.arange(800, n)`, khop cua so chung Phase 20R fixed-z.

Bang o chinh:

| z | reproduced | phase20R | abs diff |
|---:|---:|---:|---:|
| 0.05 | 0.101917671 | 0.101917671 | 0.0 |
| 0.10 | 0.138198795 | 0.138198795 | 0.0 |
| 0.20 | 0.189440763 | 0.189440763 | 0.0 |
| 0.30 | 0.225712851 | 0.225712851 | 0.0 |
| 0.55 | 0.290466867 | 0.290466867 | 0.0 |

## Block va bin

O chinh `poisson@0.925`:

```text
n_rows  = 999945
n_block = 1000
n_calib_blocks = 500
n_test_blocks  = 500
clip_fraction_max = 0.000000
NC1 e_stale_margin_max_abs = 0.0
```

Bin chinh:

```text
B0  90000 rows   1000 blocks
B1 200000 rows   1000 blocks
B2 200000 rows   1000 blocks
B3 509945 rows   1000 blocks
```

Bin phu:

```text
B0 200000 rows   1000 blocks
B1 200000 rows   1000 blocks
B2 200000 rows   1000 blocks
B3 200000 rows   1000 blocks
B4 199945 rows   1000 blocks
```

Moi bin co 1000 block truoc split, 500 block sau split; nguong conformal alpha
0.10 la 9 block.

## Diem neo

Nguon: `results/phase-21R/anchor.json`.

| Cell | Role | err_anchor | d_sla_anchor | CI95(err) | pair_ok |
|---|---|---:|---:|---:|---:|
| poisson@0.925 | CHINH | 0.220835 | 0.060125 | [0.213463, 0.227895] | 0.9876 |
| poisson@0.850 | PHU | 0.219062 | 0.059699 | [0.211749, 0.226113] | 0.9826 |
| h2@0.700 | PHU | 0.127259 | 0.001023 | [0.120588, 0.134359] | 0.9995 |
| cbr@0.700 | PC | 0.000000 | 0.000000 | [0.000000, 0.000000] | 1.0000 |
| poisson@0.700 | PC | 0.000000 | 0.000000 | [0.000000, 0.000000] | 1.0000 |
| h2@0.850 | LOAI | 0.004847 | 0.000118 | [0.003607, 0.006278] | 1.0000 |
| h2@0.925 | LOAI | 0.001175 | 0.000094 | [0.000544, 0.001935] | 1.0000 |

## Dieu da hoc

Du doan `err_anchor in [0.27, 0.31]` bi truot: do duoc `0.220835`. Nguyen
nhan la du doan neo vao `err(z_max)` thay vi `E_z[err(z)]` theo phan phoi AoI
rang cua. Viec nay duoc ghi trong `docs/phase-21R/00c-amendment-2.md` thay vi
sua nguoc pre-registration.
