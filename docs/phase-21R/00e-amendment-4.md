# AMENDMENT 4 -- Phase 21R

Ngay ky: 2026-08-12
Nguoi ky: Codex theo yeu cau owner repo DT4N
Boi canh: sau khi chay `cert/error_vs_age_v2.py`.
CHUA tinh conformal coverage tren split calib/test cua Lesson 21R.5.

## D0. Quy uoc phan vi

Lesson 4 bao cao ba dai luong khac nhau, khong duoc tron:

```text
q_pooled        : q90 tren tat ca hang trong bin. Dung cho duong cong s(z) va
                  bang marginal-vs-conditional coverage.
q_block_median  : median cua cac q90 theo block. Bao cao phu cho du bao Lesson 6.
q_of_block_q    : q90 cua cac q90 theo block. Dung trong block bootstrap gate.
```

Ket luan gate G1/H2 duoi day dung `q_of_block_q` bootstrap theo nguyen block.
Bang chung Mondrian dung `q_pooled`, vi no hoi coverage tren tung hang trong
bin neu dung mot nguong bien duy nhat.

## D1. Du doan REVISED khop

So do duoc la `q_pooled` cua `s_margin`, cell `poisson@0.925`.

| Bin | Du doan REVISED Amd 3 | Do duoc q90 | Sai lech |
|---|---:|---:|---:|
| B1 | 11.37 ms | 11.377967 ms | +0.07% |
| B2 | 15.44 ms | 15.322567 ms | -0.76% |
| B3 | 19.15 ms | 19.276593 ms | +0.66% |
| B4 | 23.88 ms | 24.022124 ms | +0.60% |

Khop trong 0.8%. Luu y: du doan nay la `REVISED`, viet sau khi thay du lieu
phan ra, nen suc nang bang chung yeu hon du doan goc. Khong trinh bay no ngang
hang voi du doan tien dang ky. Du doan goc `[1.5, 2.2]` va `[2.0, 3.0] ms` van
la truot.

## D2. Gate dat tren cell chinh

Cell chinh: `poisson@0.925`, score `s_margin`, bin chinh.

```text
G1 don dieu: 3/3 hieu lien tiep co CI99 Bonferroni /3 > 0
  B2 - B1 = 5.0143   CI [4.3864, 5.5687]
  B3 - B2 = 5.3209   CI [4.4863, 5.9867]
  B4 - B3 = 5.9639   CI [4.8343, 7.1197]

H2 ratio q(B4)/q(B1) = 2.1510   CI95 [2.0879, 2.2135]  DAT, nguong 1.3
G2 eta^2(z)          = 0.0730   CI95 [0.0696, 0.0763]  DAT, nguong 0.05
G7 Spearman vs err(z) 20R = 1.0000                     DAT
```

Canh bao ve G2: `0.0730` chi vuot nguong `0.05` 1.46 lan. Khong viet "hieu ung
manh"; viet dung la hieu ung nho-den-vua nhung du de dich chuyen phan vi 90%
gan gap doi.

Bin phu deu-so-mau xac nhan ket luan khong phu thuoc cach chia bin:

```text
q_pooled: B1'=13.0185, B5'=25.7136  -> ratio = 1.975
block-gate ratio q_of_block_q       -> ratio = 2.011, CI95 [1.9577, 2.0727]
```

## D3. Phat hien: s_margin gan nua-chuan

Cell `poisson@0.925`, bin chinh:

```text
mean(|s|)/rms mean = 0.7970   ly thuyet half-normal = 0.79788
q90(|s|)/rms mean  = 1.6441   ly thuyet half-normal = 1.64485
kurtosis           = 3.8650, 3.9827, 3.9400, 4.0229
q90/rms theo bin   = 1.6444, 1.6447, 1.6458, 1.6416
```

He qua:

```text
q_hat(g) ~ 1.645 * sqrt(rms_em^2 + rms_es(z)^2 + 2*cov(z))
```

Day la cau noi tu decomposition Lesson 21R.3 sang q_hat Lesson 21R.5. Nhung
day la quan sat hau nghiem, khong phai gia dinh; khong duoc dung no de bo
conformal.

## D4. Phat hien: twin chech he thong +3.64 ms

```text
s_signed = m_hat - m_true
mean(s_signed) = +3.638827 ms
sd(s_signed)   = 12.044626 ms
skew           = 0.098153
```

`mean > 0` nghia la twin danh gia khe quyet dinh rong hon thuc te trung binh
3.64 ms: twin qua tu tin mot cach he thong.

Phan ra mean tren margin:

```text
mean_e_model = -0.741876 ms
mean_e_stale = -2.896951 ms
s_signed     = -(e_model + e_stale)
```

Chenh chu yeu gan voi thanh phan staleness. Gia thuyet future work: cost loi
theo rho, nen twin nhin qua khu bo lo phan loi cua cost, tao hieu ung Jensen.
Khong sua bias trong Phase 21R vi do la mo them mot bac tu do moi.

Score mot phia `s_signed` nho hon score hai phia:

```text
q90(s_signed) = 10.3379, 13.8863, 17.6498, 22.2717 ms
q90(s_margin) = 11.3780, 15.3226, 19.2766, 24.0221 ms
```

## D5. Kiem hien thuc: m_hat khong doi theo bin

```text
bin   m_hat p10    p50        p90
B1    2.514757    12.847007  30.842481
B2    2.514757    12.847007  30.842481
B3    2.514757    12.847007  30.842481
B4    2.513934    12.845900  30.841530
```

Relative spread cua median: `8.62e-05`, PASS. Kiem nay chung minh bien thien
cua `q_hat` theo bin den tu sai so, khong phai do phan phoi khe quyet dinh
khac nhau giua cac bin.

`corr(s_margin, m_hat) = 0.1165`, yeu. Day la tin tot cho Lesson 21R.6: viec
loc theo `m_hat >= kappa*q_hat` khong bi tuong quan score-gap chi phoi manh.

## D6. Gia tri cua Mondrian

Neu khong chia nhom, dung mot `q_hat` bien duy nhat:

```text
q_hat bien q_pooled = 20.752588 ms
```

| Bin | q_hat_bin | coverage neu dung q_bien |
|---|---:|---:|
| B1 | 11.377967 | 0.9972 |
| B2 | 15.322567 | 0.9737 |
| B3 | 19.276592 | 0.9223 |
| B4 | 24.022125 | 0.8452 |

Trung binh van dung 0.90, nhung B1 bi bao phu thua 9.7 diem va B4 bi thieu
bao phu 5.5 diem. Day la luan diem Phase 20R dich len tang conformal: metric
bien che giau loi tap trung trong mot bin tuoi. O tang conformal, dieu nay nguy
hiem hon vi ta phat ra hop dong 90% ma khong giu duoc o bin tuoi lon nhat.

## D7. Du bao cho Lesson 21R.6

Output bao cao ba cach doc de tranh nham:

| Bin | q_block_median | P_accept | q_pooled | P_accept | q_of_block_q | P_accept |
|---|---:|---:|---:|---:|---:|---:|
| B1 | 10.844943 | 0.5689 | 11.377967 | 0.5508 | 14.206512 | 0.4527 |
| B2 | 14.832834 | 0.4323 | 15.322567 | 0.4162 | 19.164635 | 0.3066 |
| B3 | 18.460567 | 0.3240 | 19.276593 | 0.3038 | 24.519946 | 0.1936 |
| B4 | 23.403852 | 0.2163 | 24.022124 | 0.2043 | 30.417170 | 0.1050 |

Pooled:

```text
P_accept(q_block_median) = 0.3128
P_accept(q_pooled)       = 0.2978
P_accept(q_of_block_q)   = 0.1943
```

Tat ca deu dat G12 `P(accept) <= 0.90` rat rong. H8 "qua de" khong xay ra.
Rui ro chinh chuyen sang H7: duong cong risk-coverage co du huu ich khong.
