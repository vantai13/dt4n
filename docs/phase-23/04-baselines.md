# Lesson 23.3 -- baselines as rankings

Trang thai: da chay sau khi ba gate doi chung 23.3 PASS.

Artifacts:

```text
results/phase-23/baseline_rankings_poisson_0.925_C3_static.json
results/phase-23/baseline_rankings_poisson_0.925_C3_static.csv
```

Lenh tai tao:

```bash
/tmp/dt4n-venv/bin/python cert/baselines.py
```

Artifact dau vao:

```text
results/phase-22/calib_set_v3.parquet
sha256 = e37965269d73191f3caf0c9a0d7645d7fced2c82bdc2c3e6217521b39d9b98b3
y_hat_a1 = present
```

## Gate truoc sweep

Ba gate phai xanh truoc khi doc bat ky baseline nao:

| Gate | Ket qua | Y nghia |
|---|---:|---|
| PC23-1 random baseline | PASS | B1 khong co tin hieu; err\|accept nam gan neo |
| G23-10b B4 == B3 | PASS | variance proxy chi la AoI threshold duoc tham so hoa lai |
| G23-12c B6-sys closed form | PASS | oracle he thong khop dang dong ba doan |

B6-sys closed form tren `err` + F2 STATIC:

| Diem gay | coverage do duoc | err closed-form | err do duoc |
|---:|---:|---:|---:|
| 0.000000000 | 0.000000000 | 0.340276458 | 0.340276458 |
| 0.246320257 | 0.246320257 | 0.093956201 | 0.093956201 |
| 0.871557523 | 0.871557523 | 0.093956201 | 0.093956201 |
| 1.000000000 | 1.000000000 | 0.222398678 | 0.222398678 |

Mass:

```text
s*=+1  0.246320257
s*= 0  0.625237266
s*=-1  0.128442477
AURC(B6-sys, err) = 0.132541771
```

## Tai coverage 0.78

Neo always-trust:

```text
err_anchor = 0.222398678
```

| Ranking | coverage | err_system | err\|accept | delta vs anchor |
|---|---:|---:|---:|---:|
| B1 random | 0.779999480 | 0.248794420 | 0.222543041 | +0.026395742 |
| B2 constant gap | 0.779999480 | 0.209413821 | 0.158474668 | -0.012984857 |
| B3 AoI | 0.779999480 | 0.234959507 | 0.205167524 | +0.012560829 |
| B4 variance proxy | 0.779999480 | 0.234959507 | 0.205167524 | +0.012560829 |
| B5 relative margin | 0.779999480 | 0.210421888 | 0.159005472 | -0.011976790 |
| B6 prediction oracle | 0.779999480 | 0.101436695 | 0.011216132 | -0.120961983 |
| B6-sys oracle | 0.779999480 | 0.093956201 | 0.103373558 | -0.128442477 |
| C3 conformal | 0.779999480 | 0.209529829 | 0.157259202 | -0.012868849 |

C3 vs B3 tai coverage 0.78:

```text
accept_overlap(C3, B3):
  coverage_C3          = 0.779999480
  coverage_B3          = 0.779999480
  intersection         = 0.617652765
  jaccard              = 0.655441459
  share_of_C3          = 0.791863047
  independence_ref     = 0.779999480
```

Doc so nay: `share_of_C3 = 0.7919` nam trong dai du doan `0.75--0.81`.
Hai bo loc gan doc lap theo co che, khong phai hai cach viet lai cua cung mot
tap accept.

## Beneficial band

`beneficial_band` la dai coverage ma `err_system` thap hon neo always-trust.

| Ranking | beneficial band | best improvement |
|---|---:|---:|
| B1 random | none | n/a |
| B2 constant gap | [0.634650, 0.999950] | 0.013124860 @ 0.850000 |
| B3 AoI | none | n/a |
| B4 variance proxy | none | n/a |
| B5 relative margin | [0.639900, 0.999950] | 0.012752839 @ 0.840000 |
| B6 prediction oracle | [0.483300, 0.999950] | 0.122444061 @ 0.790000 |
| B6-sys oracle | [0.117900, 0.999950] | 0.128442477 @ 0.250050 |
| C3 conformal | [0.607600, 0.999950] | 0.013668874 @ 0.810000 |

Ket luan hien tai:

```text
C3 vuot B3 ro tren err_system tai diem van hanh 0.78:
  C3 = 0.209529829
  B3 = 0.234959507
  diff C3 - B3 = -0.025429678

B3 khong co beneficial band trong luoi 0.00--1.00 buoc 0.01.
C3 co beneficial band tu 0.607600 tro len, tuc co the reject toi da 39.24%
ma van thang neo always-trust tren err_system.
```
