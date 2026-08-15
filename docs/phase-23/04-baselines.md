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

Ghi chu ve luoi: Amendment 23-12 bao cao `beneficial_band` tren luoi kappa min
cua Lesson 23.1:

```text
beneficial_band (luoi kappa min, Lesson 23.1)  = [0.6151, 1.0000]
best improvement                               = 0.013227 @ coverage 0.79345
improvement_area                               = 0.003368
```

Bang tren bao cao cung dai tren luoi coverage deu cua Lesson 23.3:

```text
beneficial_band (luoi coverage deu, 23.3)      = [0.6076, 0.99995]
best improvement                               = 0.013668874 @ coverage 0.81000
improvement_area                               = 0.003403849
```

Chenh lech `0.0075` o band_low la hieu ung luoi/noi suy, khong phai hai
artifact mau thuan. Headline cua 23.3 dung luoi coverage deu vi day la truc so
sanh chung cho moi baseline.

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
khong phan biet duoc bang paired block bootstrap. Tren thang `err`, dau cua
`C3 - B2` dao chieu `-, +, -` qua ba coverage 0.70/0.78/0.85, trong khi bien
do lon nhat `0.000686` nho hon ro so voi nua do rong CI. Vi vay diem 0.78
khong phai mot hieu ung that rieng; no la nhieu quanh mot hieu gan 0.

## Wasted Abstention

Voi F2 STATIC, neu `a_twin == P1` thi accept va reject cho cung mot hanh dong.
Tu choi cac hang do khong thay doi he thong.

Tai C3 coverage 0.78:

```text
P(a_twin = P1)                     = 0.619176866
P(a_twin = P1 | accept)            = 0.653105079
P(a_twin = P1 | reject)            = 0.498886293
P(a_star = P1) reference           = 0.659723542
reject_share                       = 0.220000520
wasted_reject_share_total_rows     = 0.109755244
wasted_reject_given_reject         = 0.498886293
actionable_reject_share_total_rows = 0.110245276
actionable_reject_given_reject     = 0.501113707
```

Tai B2 coverage 0.78:

```text
P(a_twin = P1 | accept)            = 0.651471637
P(a_twin = P1 | reject)            = 0.504677570
wasted_reject_share_total_rows     = 0.111029328
wasted_reject_given_reject         = 0.504677570
actionable_reject_share_total_rows = 0.108971192
actionable_reject_given_reject     = 0.495322430
```

L20 intervention-rate check:

```text
intervention_rate(C3) = 0.110245276
intervention_rate(B2) = 0.108971192
gap C3 - B2           = 0.001274084
abs_gap               = 0.001274084 <= 0.010000000
comparable_at_matched_coverage = True
```

Doc so nay: khoang mot nua ngan sach reject cua C3 va B2 tai 0.78 nam tren
cac hang ma reject khong doi hanh dong. Tuy vay intervention rate that cua hai
chinh sach chi lech 0.001274, nen so sanh C3 vs B2 tai matched coverage 0.78
la hop le theo L20.

## C3-A va B2-A dong bang ly thuyet

Y tuong C3-A: dung lang phi ngan sach reject len cac hang ma `a_twin == P1`;
chi reject cac hang co the can thiep that. Y tuong nay sai theo cau truc voi
fallback F2 STATIC.

Menh de: voi bat ky score C va nguong k, dat

```text
C(k)   = accept/reject theo score C
C-A(k) = C(k), nhung ep accept moi hang co a_twin == P1
```

Khi do `risk(C-A(k)) = risk(C(k))` voi moi k va moi thang do.

Chung minh: hai chinh sach chi khac nhau tren tap
`D = {row: a_twin == P1 va C(k) reject}`. Tren D:

```text
C(k)   reject -> hanh dong = P1
C-A(k) accept -> hanh dong = a_twin = P1
```

Cung mot hanh dong nen cung ton that per-row; ngoai D hai chinh sach dong
nhat. Do do risk trung binh bang nhau tren toan bo tap. He qua:
`min_k risk(C-A(k)) = min_k risk(C(k))`.

Vay C3-A khong the tot hon C3; no chi la phep tham so hoa lai cung mot ho
chinh sach theo truc coverage khac. Ghi chu: ti le reject vo ich gan nhu bang
nhau o ca C3 va B2 (`0.4989` vs `0.5047` given reject), nen ket luan nay ap
dung nguyen ven cho B2-A. "Tiet kiem ngan sach reject" la mot truc doc sai cho
F2 STATIC: coverage la dai luong dan xuat tu nguong, khong phai ngan sach chi
phi.

## Co che #7 -- nguong hoa von la nguong cung

Khong dung moc "dong xu 0.500". He co `K = 4` hanh dong, va ngay ca moc
`1/K` cung khong dung vi cac hanh dong co phan phoi bien khac nhau. Moc dung
la chance agreement tinh tu chinh tap con:

```text
agreement_independent = sum_j P(a_twin=j) * P(a_star=j)
```

Voi F2 STATIC va thang `err`, reject co ich khi fallback P1 dung tren tap reject
nhieu hon twin:

```text
reject co ich  <=>  P(a_twin = a* | rej) < P(a* = P1 | rej)
delta_vs_anchor = P(rej) * [P(a_twin=a*|rej) - P(a*=P1|rej)]
```

Cot `delta do duoc` ben duoi la `err_system - err_anchor`, nen so am la co loi:

| Bo chon | kap_rej | do tach | P(a_twin=a*\|rej) | P(a*=P1\|rej) | vuot? | delta do duoc |
|---|---:|---:|---:|---:|:--:|---:|
| B1 random | 0.526796 | -0.0020 | 0.778113 | 0.658133 | KHONG | +0.026396 |
| B3 AoI | 0.395617 | +0.1662 | 0.716509 | 0.659415 | KHONG | +0.012561 |
| B2 constant gap | 0.134122 | +0.5143 | 0.550962 | 0.609984 | CO | -0.012985 |
| C3 conformal | 0.126067 | +0.5245 | 0.546653 | 0.605148 | CO | -0.012869 |

Tai tao khep kin, dung cung cong thuc G23-21:

```text
B1: 0.220000520 * (0.778113153 - 0.658132790) = +0.026395742
B3: 0.220000520 * (0.716509232 - 0.659414690) = +0.012560829
B2: 0.220000520 * (0.550962334 - 0.609984272) = -0.012984857
C3: 0.220000520 * (0.546652969 - 0.605147600) = -0.012868849
```

Gate moi:

```text
G23-21  delta_vs_anchor tai coverage c phai bang
        P(reject) * [P(a_twin=a*|reject) - P(a*=P1|reject)]
        cho moi selector static-fallback tren thang err.

Ket qua @0.78: PASS, max_abs_identity_error <= 1.6e-17.
```

Doc bang:

1. B1 cho do tach gan 0, dung vai tro doi chung am.
2. B3 cho do tach `+0.1662`, bang 31.7% cua C3. Tuoi co mang tin hieu ve do
   tin cay cua argmin; ket luan cu "tin hieu khong nam o tuoi" bi rut lai.
3. B3 that bai vi chua vuot nguong hoa von, khong phai vi khong co tin hieu.
   `P(a*=P1|rej)` la nguong cung cua fallback; bo chon yeu co the lam hai thay
   vi tao mot phan loi ich.
4. B2 va C3 vuot nguong vi day `P(a_twin=a*|rej)` xuong duoi nguong P1.

Bang chance-agreement day du tai coverage 0.78:

| Bo chon | tieu chi reject | agree(acc) | ind(acc) | kappa(acc) | agree(rej) | ind(rej) | kappa(rej) |
|---|---|---:|---:|---:|---:|---:|---:|
| B1 random | ngau nhien | 0.777457 | 0.531683 | 0.524803 | 0.778113 | 0.531097 | 0.526796 |
| B3 AoI | tuoi z | 0.794832 | 0.531726 | 0.561864 | 0.716509 | 0.530942 | 0.395617 |
| B2 constant gap | m_hat | 0.841525 | 0.549225 | 0.648440 | 0.550962 | 0.481408 | 0.134122 |
| C3 conformal | m_hat/q_hat | 0.842741 | 0.549907 | 0.650607 | 0.546653 | 0.481257 | 0.126067 |

Overlap de dong no co che L20:

```text
accept_overlap(C3, B2) @0.78:
  intersection     = 0.758604068
  share_of_C3      = 0.972569966
  jaccard          = 0.946604571
  independent_ref  = 0.779999480

accept_overlap(C3, B3) @0.78:
  intersection     = 0.617652765
  share_of_C3      = 0.791863047
  jaccard          = 0.655441459
  independent_ref  = 0.779999480
```

Ket qua nay noi hai dieu cung luc: `m_hat` la tin hieu manh hon o diem van
hanh, nhung tuoi khong vo dung. `corr(z, m_hat) ~= 0` chi noi hai bo loc chon
hai tap gan doc lap; no khong noi tuoi khong mang tin hieu ve `a_twin = a*`.

## Phan phoi argmin va L21

Phan phoi bien:

```text
a_twin_distribution = [0.619176866, 0.000000000, 0.369222369, 0.011600766]
a_star_distribution = [0.659723542, 0.000014001, 0.333091984, 0.007170473]
```

Hanh dong 1 gan nhu chet: twin khong bao gio chon, va chan ly chi chon voi xac
suat `1.4e-5`. Threat moi:

```text
L21  Khong gian hanh dong hieu dung la 3 trong khi thiet ke danh nghia co
     K=4 action, tuc K-1=3 score slots. Neu action chet co the loai hop le,
     so so sanh hieu dung co the la 2 thay vi 3. Chi phi cua slot/action chet
     chua duoc luong hoa.
```

Ghi chu sau Amendment 23-16: phan dinh ly C3 da duoc chot theo `K-1=3` bien
voi `alpha/(K-1)`, khop code Phase 22--23. L21 con lai chi la cau hoi optional
ve pruning action chet de co the giam tiep xuong `K_eff-1=2`; chua co artifact
va khong duoc dung cho cac ket qua hien tai.

Tren tap reject, B2/C3 lam phan phoi `a_twin` gian ra, con B3 gan nhu giu
hinh dang bien:

```text
marginal  [0.6192, 0.0000, 0.3692, 0.0116]
B3 reject [0.6184, 0.0000, 0.3700, 0.0116]
B2 reject [0.5047, 0.0000, 0.4607, 0.0346]
C3 reject [0.4989, 0.0000, 0.4689, 0.0322]
```

Doc co che: `m_hat` nho bat che do twin ban khoan, argmin gian ra. `z` lon bat
che do twin tu tin nhung sai, argmin giu hinh dang gan nhu cu. Conformal theo
tuoi vi vay dang chuan hoa mot tin hieu co that nhung yeu hon nguong van hanh.

## Gamma sweep va G23-21b

Thuc nghiem re de xem tuoi dang bi duoi-trong-so hay that su khong them nhieu
o bien:

```text
score_gamma = min_j m_hat_j / q_hat_j(z_bin, m_hat_bin)^gamma
```

Pre-check: `gamma=0` trung bitwise voi B2 (`disagree=0`,
`max_abs_score_diff=0`). `gamma=1` la C3 hien tai va la diem duy nhat trong
bang con giu bao dam conformal da hieu chuan.

| gamma | err_system | delta vs anchor | overlap C3 | overlap B2 | guarantee? |
|---:|---:|---:|---:|---:|:--:|
| 0.0 | 0.209413821 | -0.012984857 | 0.972570 | 1.000000 | no |
| 0.5 | 0.208991793 | -0.013406885 | 0.986712 | 0.985858 | no |
| 1.0 | 0.209529829 | -0.012868849 | 1.000000 | 0.972570 | yes |
| 1.5 | 0.210313881 | -0.012084798 | 0.987007 | 0.959577 | no |
| 2.0 | 0.209549830 | -0.012848848 | 0.976263 | 0.948832 | no |
| 3.0 | 0.211097932 | -0.011300746 | 0.957448 | 0.930018 | no |
| 5.0 | 0.214762174 | -0.007636504 | 0.928947 | 0.901517 | no |

Khong doc `gamma=0.5` nhu diem van hanh hop le. No duoc chon tren cung tap test
nen bi winner's curse, va `gamma != 1` khong guarantee-preserving: `q_hat^gamma`
khong con la phan vi conformal da hieu chuan. Doc dung: chieu gamma la mot
diagnostic do chi phi cua bao dam. Gia tri do duoc:

```text
gamma0.5 - gamma1, err delta = -0.000538036
CI95 paired block bootstrap  = [-0.001932176, +0.000872232]
CI chua 0                    = True
```

Vay chi phi diem cua bao dam formal, tren diagnostic nay, la khoang `0.000538`
err va khong phan biet duoc voi 0 bang CI ghep cap.

G23-21b kiem tra them gia thuyet "gamma noi B2 voi B3":

```text
qhat slots = 3, keys = z_bin,m_hat_bin
qhat monotone theo z trong moi m_hat_bin = True
qhat monotone theo z_s o row-level       = False
```

Do C3 dung Mondrian key `z_bin x m_hat_bin`, `gamma -> infinity` khong xep hang
theo tuoi thuan B3; no xep theo cau truc cell/slot cua `q_hat`. Ket qua:

| gamma | err_system | gap vs B3 | overlap B3 |
|---:|---:|---:|---:|
| 0.0 | 0.209413821 | -0.025545686 | 0.780129 |
| 0.5 | 0.208991793 | -0.025967714 | 0.786193 |
| 1.0 | 0.209529829 | -0.025429678 | 0.791863 |
| 2.0 | 0.209549830 | -0.025409677 | 0.801941 |
| 3.0 | 0.211097932 | -0.023861575 | 0.810031 |
| 5.0 | 0.214762174 | -0.020197333 | 0.822329 |
| 20.0 | 0.243768089 | +0.008808581 | 0.839433 |
| 100.0 | 0.248062372 | +0.013102865 | 0.839494 |

Check G23-21b:

```text
b2_to_b3_interpolation_supported            = False
gamma_max_within_0.002_of_B3                = False
no_gamma_gt2_beats_gamma1                   = True
err_system_monotone_for_gamma_ge1           = False
paired_gamma0.5_minus_gamma1_CI_contains_0  = True
```

Ket luan G23-21b: REFUTED. Du doan ky truoc "gamma noi B2 voi B3" duoc giu
lai trong log nay, nhung no TRUOT CO CHE cho implementation C3 hien tai.
Nguyen nhan khong phai gamma sweep bi nhieu, ma la taxonomy ban dau bi doc sai:
C3 khong dung notation age-only; C3 dung `q_hat(z_bin,m_hat_bin)` voi 3 score
slots. Vi vay `cell_mono_by_z=True` van co the dong thoi voi
`row_mono_by_z=False`, va khi `gamma` lon ranking bi cau truc cell/slot
`q_hat` chi phoi thay vi hoi tu ve B3 AoI.

Bai hoc phuong phap: truoc khi gan mot truc tham so voi mot co che vat ly
don gian, phai kiem tra taxonomy that su cua certificate. Mot marginal theo
age bin co the dung de ve hinh dang, nhung khong duoc thay cho key conformal
that su khi suy luan co che.

## G23-21c -- qhat cell sample support

Sau khi G23-21b xac nhan C3 la Mondrian 2D, guarantee formal phu thuoc vao
moi cell `z_bin x m_hat_bin` co du mau hieu dung de threshold `q_hat` khong
roi vao `+inf`. Code hien tai tinh conformal level bang
`block_id.nunique()` trong tung cell, nen audit bao cao ca so dong va so block
hieu dung.

```text
gate=G23-21c keys=z_bin,m_hat_bin cells=16 calib_rows=499978 calib_blocks=500 score_slots=3
actual alpha_each=0.033333333 n_min=29 pass=True
conservative action-split alpha_each=0.025000000 n_min=39 pass=True
min_rows=11241 min_eff_blocks=433 max_eff_blocks=484 below_actual=0 below_conservative=0 nonfinite_qhat=0
```

Nam cell mong nhat theo effective blocks:

| cell | n_rows | n_eff_blocks | margin vs 29 | margin vs 39 |
|---|---:|---:|---:|---:|
| z_bin=0,m_hat_bin=3 | 11250 | 433 | +404 | +394 |
| z_bin=1,m_hat_bin=3 | 25000 | 433 | +404 | +394 |
| z_bin=2,m_hat_bin=3 | 25000 | 433 | +404 | +394 |
| z_bin=3,m_hat_bin=3 | 63794 | 438 | +409 | +399 |
| z_bin=0,m_hat_bin=0 | 11241 | 451 | +422 | +412 |

Ket luan G23-21c: PASS. Khong co cell nao thieu support theo split thuc te
`alpha=0.1/3`, va cung qua ca diagnostic bao thu neu chia theo 4 action
`alpha=0.1/4`. Do do ket qua C3 hien tai khong bi treo boi van de "thin
Mondrian cell".

## Co che #8 -- phan ra regret cross-cell

Sau G23-17c, `regret` khong duoc doc nhu mot headline tho giua cac cell. Dong
nhat thuc can bao cao la:

```text
regret_ratio = err_ratio x normpen_ratio x scale_ratio
normpen      = (regret / err) / median_m_true_1
```

Ket qua tren TEST split:

| Cell | err_r | normpen_r | scale_r | product | regret_r |
|---|---:|---:|---:|---:|---:|
| poisson@0.850 | 0.9925 | 0.9796 | 0.2978 | 0.28954 | 0.2896 |
| h2@0.700 | 0.5690 | 0.5533 | 0.8858 | 0.27882 | 0.2788 |

Doc dung: `poisson@0.850` la doi chung bat bien theo thang, vi hai thua so
that gan 1 va thang margin giai thich chenh lech regret. `h2@0.700` thi khac:
hai thua so that cung giam quanh 0.55, nen regret giam la hieu ung quyet dinh
that, khong phai chi artifact don vi.

Quy tac khoa trong Amendment 23-18: headline cross-cell la `err`; `regret`
cross-cell phai kem phan ra ba thua so; `sla_rate` khong lam headline vi
threshold `t_d`/`t_l` khac nhau giua cell.

## Tie-break sensitivity

Tai coverage 0.78, thay stable row-order tie-break bang random tie-break ba seed:

| Selector | rowsort | rand s1 | rand s2 | rand s3 | spread |
|---|---:|---:|---:|---:|---:|
| B3 AoI | 0.234959507 | 0.234953507 | 0.234951507 | 0.234955507 | 0.000008001 |
| B2 constant gap | 0.209413821 | 0.209313815 | 0.209341817 | 0.209337816 | 0.000100007 |
| C3 conformal | 0.209529829 | 0.209529829 | 0.209529829 | 0.209529829 | 0.000000000 |

Spread B3 chi bang `0.000008`, nho hon nhieu so voi `|C3-B3| = 0.025430`.
Ket luan C3 vuot B3 tai 0.78 khong phu thuoc quy tac pha hoa.

## Ket luan hien tai

```text
C3 vuot B3 ro tren err_system tai diem van hanh 0.78:
  C3 = 0.209529829
  B3 = 0.234959507
  diff C3 - B3 = -0.025429678

B3 khong co beneficial band trong luoi 0.00--1.00 buoc 0.01.
Khong duoc ket luan B3 vo tin hieu: B3 co 31.7% suc tach kappa cua C3 nhung
chua vuot nguong hoa von cua fallback P1.

Nhung B2 constant gap la doi thu that: tai coverage 0.78, C3 khong phan biet
duoc voi B2 tren err/regret/sla. Gamma sweep khong cap phep chon gamma khac 1;
no do chi phi cua bao dam formal, va chi phi do nho hon thanh sai so.

C3 co beneficial band tu 0.607600 tro len, tuc co the reject toi da 39.24%
ma van thang neo always-trust tren err_system.
C3 dong duoc 10.02% khoang cach tu neo always-trust toi B6-sys oracle tai 0.78.
```
