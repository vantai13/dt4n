# Lesson 21R.3 -- decomposition.py

Ngay hoan thanh: 2026-08-12

## Artifact

Source:

```text
cert/decomposition.py
test/test_phase21r_decomp.py
```

Results:

```text
results/phase-21R/decomposition_poisson_0.925.json
results/phase-21R/decomposition_poisson_0.850.json
results/phase-21R/decomposition_h2_0.700.json
results/phase-21R/decomposition_cbr_0.700.json
```

## Dinh nghia

Phan ra chinh cua Phase 21R la muc BIEN tren thang COST. Cap `(a1,a2)` duoc
chon tu twin cu `y_hat`; sau do giu co dinh cap nay de tinh margin trong ba
world:

```text
e_model = m_true - m_mid
e_stale = m_mid  - m_hat
total   = m_true - m_hat
```

Khoa dong nhat:

```text
e_model + e_stale = total
Var(total) = Var(e_model) + Var(e_stale) + 2 * Cov(e_model,e_stale)
```

Ngoai decomposition chinh, script cung tinh ba doi chieu:

```text
margin/delay
path/cost
path/delay
```

Moi `z_cross` bat buoc kem nhan `(level, channel)`.

## Test

Lenh targeted:

```bash
/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_decomp.py -q
```

Ket qua:

```text
10 passed
```

Lenh Phase 21R lien quan:

```bash
/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_decomp.py test/test_phase21r_margin.py test/test_phase21r_calib.py -q
```

Ket qua:

```text
32 passed
```

## Lenh sinh artifact

```bash
/tmp/dt4n-venv/bin/python -m cert.decomposition --mode poisson --rho-bar 0.925 --out results/phase-21R/decomposition_poisson_0.925.json
/tmp/dt4n-venv/bin/python -m cert.decomposition --mode poisson --rho-bar 0.850 --out results/phase-21R/decomposition_poisson_0.850.json
/tmp/dt4n-venv/bin/python -m cert.decomposition --mode h2 --rho-bar 0.700 --out results/phase-21R/decomposition_h2_0.700.json
/tmp/dt4n-venv/bin/python -m cert.decomposition --mode cbr --rho-bar 0.700 --out results/phase-21R/decomposition_cbr_0.700.json
```

## z_cross

| Cell | z_cross(margin,cost) | z_cross(margin,delay) | z_cross(path,cost) | z_cross(path,delay) |
|---|---:|---:|---:|---:|
| poisson@0.925 | 0.007085 s | 0.008346 s | 0.017050 s | 0.077421 s |
| poisson@0.850 | 0.009929 s | 0.011903 s | 0.034245 s | 0.098733 s |
| h2@0.700 | 0.023260 s | 0.016294 s | 0.299489 s | 0.178182 s |
| cbr@0.700 | above grid | above grid | above grid | above grid |

Ket qua quan trong: `z_cross(margin,cost)` cua cell chinh la `0.007085 s`, nho
hon san vat ly `d_sync = 0.051 s`. Vi vay tren dai AoI co the dat duoc, sai so
do cu da chi phoi sai so mo hinh.

## Margin/cost tai hai moc

| Cell | z | rms_e_model | rms_e_stale | rms_total | corr | share_model | share_stale | share_cov |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| poisson@0.925 | 0.055 | 2.142350 | 5.981628 | 6.044955 | -0.149462 | 0.125636 | 0.979168 | -0.104804 |
| poisson@0.925 | 0.550 | 2.139427 | 16.814918 | 16.054032 | -0.411349 | 0.017770 | 1.097050 | -0.114820 |
| poisson@0.850 | 0.055 | 0.628577 | 1.446484 | 1.680970 | +0.185990 | 0.139856 | 0.740514 | 0.119630 |
| poisson@0.850 | 0.550 | 0.681015 | 4.053958 | 4.412706 | +0.466155 | 0.023819 | 0.844024 | 0.132157 |
| h2@0.700 | 0.055 | 2.050455 | 3.142926 | 3.688918 | -0.036839 | 0.308968 | 0.725920 | -0.034888 |
| h2@0.700 | 0.550 | 2.056400 | 8.898891 | 8.919991 | -0.105294 | 0.053182 | 0.995269 | -0.048450 |
| cbr@0.700 | 0.055 | 0.004567 | 0.000023 | 0.004567 | +0.013347 | 0.999842 | 0.000025 | 0.000133 |
| cbr@0.700 | 0.550 | 0.004567 | 0.000064 | 0.004570 | +0.034951 | 0.998817 | 0.000199 | 0.000984 |

`poisson@0.850` co covariance duong, trai dau voi cell chinh. Vi vay khong duoc
bo qua hang `2*Cov` hoac gan san dau am cho moi che do.

## Flatness va controls

| Cell | flatness rel spread | pass | NC1 max_abs_e_stale | NC2 max_abs_e_model |
|---|---:|---|---:|---:|
| poisson@0.925 | 0.001497 | true | 0.0 | 0.0 |
| poisson@0.850 | 0.093815 | false | 0.0 | 0.0 |
| h2@0.700 | 0.003260 | true | 0.0 | 0.0 |
| cbr@0.700 | 0.000000 | true | 0.0 | 0.0 |

Flatness false cua `poisson@0.850` den tu viec cap margin duoc chon boi twin cu
va co the doi khi `z` doi. Hai identity NC1/NC2 van dung tuyet doi.

## Noise floor

| Cell | observed rms_e_model | model true net of floor | noise variance share |
|---|---:|---:|---:|
| poisson@0.925 | 2.141802 | 1.543306 | 48.08% |
| poisson@0.850 | 0.639313 | 0.000000 | 100.00% |
| h2@0.700 | 2.051708 | 1.415621 | 52.39% |
| cbr@0.700 | 0.004567 | 0.000000 | 100.00% |

Noise floor dung trong script: `1.4851 ms`, lay tu audit ke thua. Voi cell
chinh, gan mot nua phuong sai `e_model` den tu nhieu do luong cua truth table.

## Dieu da hoc

1. Prediction `z_cross in [0.05, 0.10]` dung cho `path/delay`, nhung sai cho
   dai luong Phase 21R la `margin/cost`.
2. `z_cross(margin,cost)` cua cell chinh nam duoi san vat ly, nen giam AoI van
   co ich tren toan mien van hanh.
3. `q_hat` co kha nang lon hon du doan ban dau khoang 5-8 lan; ghi nhan la
   du doan `REVISED`, khong sua preregistration.
4. `corr(e_model,e_stale)` doi dau theo che do; moi bao cao RMS tong phai kem
   covariance.
