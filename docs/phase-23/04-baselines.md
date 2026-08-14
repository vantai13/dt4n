# Lesson 23.3 -- baselines as rankings

Trang thai: da chay sau khi ba gate doi chung 23.3 PASS.

Artifacts:

```text
results/phase-23/baseline_rankings_poisson_0.925_C3_static.json
results/phase-23/baseline_rankings_poisson_0.925_C3_static.csv
results/phase-23/baseline_c3_b2_audit_poisson_0.925_C3_static.json
```

Lenh tai tao:

```bash
/tmp/dt4n-venv/bin/python cert/baselines.py
/tmp/dt4n-venv/bin/python cert/baselines.py --audit-c3-b2 --n-boot 2000
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

Phat hien phai bao cao: B2 constant gap nhinh hon C3 tren `err_system` tai
diem van hanh, nhung hieu rat nho va CI ghep cap chua 0:

```text
C3 - B2, coverage 0.78:
  err    = +0.000116008, CI95 [-0.001968714, +0.002256247]
  regret = -0.005496808, CI95 [-0.033357486, +0.021128896]
  sla    = -0.000236016, CI95 [-0.001338032, +0.000852087]
```

Do do khong duoc viet "C3 vuot moi baseline" tren diem 0.78. Phat bieu dung
la: C3 vuot baseline AoI ro rang, nhung khong phan biet duoc voi nguong
hang so B2 tren risk he thong tai diem van hanh.

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

Tren chi so dai, C3 troi hon B2:

```text
band_low(C3) = 0.607600  vs  band_low(B2) = 0.634650
improvement_area(C3) lon hon B2 khoang 12%
partial_AURC_060_100/anchor(C3) = 0.961780
partial_AURC_060_100/anchor(B2) = 0.967010
```

Day la bai hoc "point vs band": so mot diem 0.78 mong manh; so tren dai
van hanh on dinh hon va dung voi Amendment 23-12.

## C3 vs B2 mechanism

C3 tot hon B2 tren nhanh accept, nhung phan bu reject cua C3 te hon cho P1.
Hai hieu ung gan nhu triet tieu:

| Thanh phan err @0.78 | C3 | B2 | C3 - B2 | dong gop |
|---|---:|---:|---:|---:|
| accept | 0.157259202 | 0.158474668 | -0.001215466 | -0.000948063 |
| reject | 0.394852400 | 0.390015728 | +0.004836671 | +0.001064070 |
| system | 0.209529829 | 0.209413821 | +0.000116008 | +0.000116008 |

Co che: chung nhan conformal toi uu hoa cau hoi "twin co dang tin khong".
Risk he thong can cau hoi "twin co tot hon fallback P1 khong". Phan bu cua
tap accept tot nhat khong phai tap reject tot nhat.

Paired block bootstrap cho C3 - B2:

| coverage | scale | delta | CI95 | contains 0 |
|---:|---|---:|---:|---|
| 0.70 | err | -0.000686045 | [-0.002960673, +0.001352368] | yes |
| 0.70 | regret | -0.000203114 | [-0.030217762, +0.028542651] | yes |
| 0.70 | sla | -0.000894059 | [-0.002198098, +0.000354196] | yes |
| 0.78 | err | +0.000116008 | [-0.001968714, +0.002256247] | yes |
| 0.78 | regret | -0.005496808 | [-0.033357486, +0.021128896] | yes |
| 0.78 | sla | -0.000236016 | [-0.001338032, +0.000852087] | yes |
| 0.85 | err | -0.000124008 | [-0.001744089, +0.001480250] | yes |
| 0.85 | regret | -0.010737003 | [-0.033234492, +0.010068589] | yes |
| 0.85 | sla | -0.000322021 | [-0.001322416, +0.000680095] | yes |

Ket luan: trong cac coverage 0.70, 0.78, 0.85 va tren ca ba thang, C3 va B2
khong phan biet duoc bang paired block bootstrap.

## Wasted Abstention

Voi F2 STATIC, neu `a_twin == P1` thi accept va reject cho cung mot hanh dong.
Tu choi cac hang do khong thay doi he thong.

Tai C3 coverage 0.78:

```text
P(a_twin = P1)                     = 0.619176866
reject_share                       = 0.220000520
wasted_reject_share_total_rows     = 0.109755244
wasted_reject_given_reject         = 0.498886293
actionable_reject_share_total_rows = 0.110245276
actionable_reject_given_reject     = 0.501113707
```

Doc so nay: khoang mot nua ngan sach reject cua C3 tai 0.78 nam tren cac hang
ma reject khong doi hanh dong. Day mo ra cau hoi 23.3b/C3-A, nhung chua chay
C3-A trong artifact nay.

Ket luan hien tai:

```text
C3 vuot B3 ro tren err_system tai diem van hanh 0.78:
  C3 = 0.209529829
  B3 = 0.234959507
  diff C3 - B3 = -0.025429678

B3 khong co beneficial band trong luoi 0.00--1.00 buoc 0.01.
C3 co beneficial band tu 0.607600 tro len, tuc co the reject toi da 39.24%
ma van thang neo always-trust tren err_system.

Nhung B2 constant gap la doi thu that: tai coverage 0.78, C3 khong phan biet
duoc voi B2 tren err/regret/sla. Dong gop chac chan cua C3 so voi B2 hien la
bao dam hinh thuc voi chi phi risk he thong khong do duoc, khong phai cai thien
rui ro diem van hanh.

C3 dong duoc 10.02% khoang cach tu neo always-trust toi B6-sys oracle tai 0.78.
```
