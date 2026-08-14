# LESSON 23.2 -- threshold families as rankings

Ngay: 2026-08-14

Trang thai: da chay sau Amendment 23-10.

Artifacts:

```text
results/phase-23/threshold_families_poisson_0.925_C3_static.json
results/phase-23/threshold_families_poisson_0.925_C3_static.csv
```

Lenh:

```bash
/tmp/dt4n-venv/bin/python cert/threshold_families.py --n-boot 1000
```

Targeted tests:

```text
test/test_phase23_thresholds.py
10 passed in 10.13s
```

Targeted Phase 22/23 regression:

```text
test/test_phase23_fallback.py test/test_phase23_thresholds.py
test/test_phase23_fallback_audit.py test/test_phase23_prereg.py
test/test_phase22_matrix.py
44 passed in 110.35s (0:01:50)
```

Full suite:

```text
769 passed, 1 skipped, 2 warnings in 293.76s (0:04:53)
```

## 1. Measurement device

Lesson 23.2 viet lai moi ho nguong thanh mot bang xep hang:

```text
NHAN : s(row) = min_j m_hat_j / q_hat_j
CONG : s(row) = min_j (m_hat_j - q_hat_j)
```

Nguong chi chon mot diem tren duong risk-coverage. Do do moi so sanh duoi day
duoc noi suy ve coverage chung `{0.30, 0.50, 0.78}`.

V23-4 va G23-6b deu xanh:

| Gate | Ket qua |
|---|---|
| V23-4 `CONG(delta=0) == NHAN(kappa=1)` bitwise | PASS |
| G23-6b `CONG == REGRET` bitwise tren luoi epsilon | PASS |
| G23-7 CONG thoai hoa tren interval | PASS |
| G23-7b CONG thoai hoa cuc bo theo age bin | PASS |
| G23-8 full coverage quy ve neo twin | PASS |
| G23-9 Spearman self-check bang rank doc lap | PASS |
| G23-9b Pareto tinh tren sweep gop 33 ung vien | PASS |

## 2. Shape of age conditioning

`q_hat_slot1(z)` gom C3 theo `z_bin` tren CALIB:

| z_bin | q_hat_slot1 |
|---:|---:|
| 0 | 15.078839 |
| 1 | 20.370154 |
| 2 | 25.212436 |
| 3 | 31.746064 |

Ty so hinh dang cua ho NHAN la bat bien:

```text
r_times = q3/q0 = 2.105339
q_bar   = 23.101873
```

CONG khong phang o coverage 0.30 nhu du doan. Ly do thuc nghiem: tai
`epsilon=0`, coverage da chi la `0.143581`; muon len coverage 0.30 phai dung
`epsilon > 0`, nen ho CONG da o nhanh dieu-kien-manh, khong o nhanh phang.

| coverage | epsilon noi suy | r_CONG | r_NHAN | prediction |
|---:|---:|---:|---:|---|
| 0.30 | 7.387378 | 3.166978 | 2.105339 | T5 FAIL |
| 0.50 | 13.176642 | 9.762092 | 2.105339 | diagnostic |
| 0.78 | 20.895185 | inf | 2.105339 | T6 direction HIT, range MISS |

`r_CONG = inf` tai coverage cao khong phai loi tinh. No la dau vet cua thoai
hoa cuc bo: `epsilon` da vuot nguong cua cac bin tuoi tre, nen mot so bin
khong con kha nang loc hang.

Chuoi thoai hoa cuc bo cua ho CONG:

| onset z_bin | epsilon* | coverage tai epsilon* | so bin da thoai hoa |
|---:|---:|---:|---:|
| 0 | 15.078839 | 0.576742 | 1 |
| 1 | 20.370154 | 0.765599 | 2 |
| 2 | 25.212436 | 0.908750 | 3 |
| 3 | 31.746064 | 1.000000 | 4 |

Diem van hanh `coverage ~= 0.78` cua ho CONG dung `epsilon = 20.895185`, lon
hon onset dau tien `5.816346` va nam sau onset thu hai. Noi cach khac, tai
diem van hanh, hai bin tuoi tre nhat da co nguong khong duong theo phep do
gom-theo-tuoi slot 1. Day la co che manh hon ket qua G23-7: G23-7 chi bat
thoai hoa toan cuc, con G23-7b cho thay thoai hoa bat dau som hon nhieu.

Hai bin da thoai hoa nay chiem `145000 / 499967 = 29.00%` test rows
(`290000 / 999945 = 29.00%` tren toan artifact). So voi coverage CONG tai diem
van hanh `0.780492`, do la `37.16%` nhanh accept: hon mot phan ba cac quyet
dinh duoc CONG chap nhan la chap nhan vo dieu kien theo age-bin, khong phai vi
hang do vuot qua mot phep kiem tra margin.

## 3. Matched-coverage comparison

Risk toan he thong voi fallback F2 STATIC:

| coverage | err NHAN | err CONG | NHAN-CONG | regret NHAN | regret CONG | sla NHAN | sla CONG |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.30 | 0.274667 | 0.271652 | +0.003014 | 2.562068 | 2.560187 | 0.172240 | 0.171800 |
| 0.50 | 0.237484 | 0.237752 | -0.000268 | 1.988702 | 2.029071 | 0.155783 | 0.157050 |
| 0.78 | 0.209438 | 0.215212 | -0.005774 | 1.575283 | 1.659869 | 0.145521 | 0.148238 |

T7 truot tren thang err: tai coverage 0.30, NHAN khong thang CONG; no te hon
`0.003014` err. Tuy vay NHAN va CONG van gan nhau trong vung coverage thap, nen day la mot
bat dong thang rui ro cuc bo, khong phai loi thiet bi.

T8 truot theo huong co gia tri khoa hoc. Tai coverage van hanh, hai ho phan
biet duoc:

```text
coverage_mul = 0.777689
coverage_add = 0.780492
accept intersection = 0.717959
accept symmetric difference = 0.122262

delta_err(NHAN - CONG) = -0.005538
CI95 paired block bootstrap = [-0.008569, -0.002476]
```

Nhanh FAIL cua Amendment 23-10 khong kich hoat theo chieu CONG thang. Ket qua
nguoc lai: NHAN van thang ro o diem van hanh Phase 23.

## 4. Slot diagnostic

T9 du doan slot hep nhat se chi phoi CONG nhieu hon NHAN. Thuc te slot 1 chi
phoi gan nhu tat ca quyet dinh reject o ca hai ho. Bang duoi dung diagnostic
`slot1_decides_share`; artifact cung luu `slot1_rejects_given_reject`, cho
ket luan y het nhung gan truc tiep voi reject rows:

| coverage | slot1 share NHAN | slot1 share CONG | CONG-NHAN |
|---:|---:|---:|---:|
| 0.30 | 0.999960 | 0.999920 | -0.000040 |
| 0.50 | 0.999756 | 0.998620 | -0.001136 |
| 0.78 | 0.999960 | 0.999232 | -0.000728 |

T9 FAIL. Co che GO-2 "slot hep chi phoi" dung theo nghia rong, nhung no chi
phoi ca hai ho, khong phai rieng CONG. Tai coverage 0.78, ty le slot reject
cua NHAN la `[0.222271, 0.006822, 0.000000]`; cua CONG la
`[0.211302, 0.016235, 0.000102]`. Slot 3 gan nhu khong bao gio la rang buoc
chat. Dieu nay khong rut lai gia tri cua K=4, vi hieu chinh dong thoi van can
cho claim formal; nhung loi ich van hanh trong artifact nay tap trung gan het
vao cap slot 1 `{a1, a2}`.

## 5. G23-9 and Pareto

Spearman tren toan luoi coverage:

| sweep | rho(err,regret) | rho(err,sla) | rho(regret,sla) | min |
|---|---:|---:|---:|---:|
| NHAN | 1.000000 | 0.978873 | 0.978873 | 0.978873 |
| CONG | 0.999129 | 0.993031 | 0.989547 | 0.989547 |
| combined | 0.999091 | 0.991822 | 0.989096 | 0.989096 |

Ba thang dong bien manh. Vi vay Lesson 23.4 co the ve mot duong
risk-coverage chinh, nhung van nen giu mat Pareto nho vi argmin dia phuong
khong trung tuyet doi.

Nghi ngo "Spearman co bug do hai cap trung 16 chu so" duoc kiem bang
`scale_agreement_self_check`: tinh lai Spearman bang `pandas.rank` doc lap cho
tat ca cac cap, `max_abs_diff_vs_pandas_rank_check = 0.0` o ca ba sweep.
Voi NHAN, `rho(err,regret)=1.0` vi hai thang co cung thu hang tren luoi; he qua
bat buoc `rho(err,sla)=rho(regret,sla)` duoc thoa. Voi CONG, hai gia tri
mot so gia tri gan nhau la rank geometry cua thong ke roi rac, khong phai ghi
de sai khoa.

Mat Pareto duoc tinh tren sweep gop, khong chi tren NHAN:

```text
n_candidates_considered = 43 = 19 NHAN + 24 CONG
n_pareto_survivors = 2
families_surviving = {NHAN}
```

Vi da xet du ca 14 diem CONG ma khong diem nao song sot, ket qua manh hon
"NHAN thang tai coverage 0.78": tren luoi Lesson 23.2, NHAN troi hoan toan
CONG theo mat Pareto ba thang.

Hai diem song sot:

| family | param | coverage | err | regret | sla |
|---|---:|---:|---:|---:|---:|
| NHAN | 0.25 | 0.737973 | 0.210270 | 1.598988 | 0.145156 |
| NHAN | 0.20 | 0.793460 | 0.209172 | 1.567691 | 0.145638 |

AURC he thong, do tren toan bang xep hang:

| family | AURC err | AURC regret | AURC sla |
|---|---:|---:|---:|
| NHAN | 0.252450 | 2.251942 | 0.164305 |
| CONG | 0.253738 | 2.280195 | 0.165395 |
| NHAN-CONG | -0.001288 | -0.028253 | -0.001090 |

NHAN co AURC nho hon tren ca ba thang, nen ket luan khong chi dua vao ba lat
cat coverage. Tuy nhien, AURC nay chi duoc giu nhu bang phu:

1. Luu y mat do luoi: voi thang err, neu lay duong NHAN mau lai tren luoi thua
   cua CONG, AURC(NHAN) tang tu `0.252450` len `0.253428`. Do lech
   `+0.000978` bang 52% hieu AURC tren luoi cu `-0.001896`. Sau khi lam day
   luoi CONG, hieu AURC err con `-0.001288`; canh bao mat do luoi van dung,
   nhung da nho hon.
2. Luu y headline: `AURC_system_err(C3+F2) = 0.252450` lon hon neo
   `0.222399`. Day khong phai C3 te o diem van hanh; no chi cho thay AURC toan
   dai bi chi phoi boi coverage thap, noi fallback P1 duoc dung gan moi hang va
   he thong te hon neo.

Chi so van hanh thay the cho C3+F2:

```text
dai coverage co loi          = [0.6151, 1.0000]
max reject share van co loi   = 38.49%
improvement area err          = 0.003368
best improvement              = 0.013227 tai coverage 0.79345
partial AURC [0.60,1.00]      = 0.214012
partial-AURC / neo            = 0.9623
```

Ket luan Lesson 23.2 van dua tren paired delta tai coverage khop va Pareto
trong sweep gop, khong dua vao AURC toan dai.

## 6. Reject-branch diagnostic

`err_reject(F2)` cua NHAN xac nhan do phang cua nhanh fallback, nhung khong
dung neu goi `kappa=0.25` la cuc tieu toan luoi. Tren toan luoi, min nam o bien
reject-gan-het:

```text
global min err_reject = 0.340276 tai kappa=6.0/8.0, coverage=0
operational band kappa in [0.05, 0.50]:
  min = 0.391007 tai kappa=0.50
  max = 0.413250
```

Trong vung van hanh gan `0.20..0.35`, `kappa=0.25` van la diem tot ve
`err_reject` cuc bo, nhung `err_system` lai tot hon tai `kappa=0.20`. Day la
vi toi uu nhanh reject khac voi toi uu toan he: khi coverage doi, trong so cua
nhanh accept/reject cung doi.

## 7. Prediction ledger

| ID | Noi dung | Do duoc | KQ |
|---|---|---|---|
| T5 | `r_CONG(0.30) < r_NHAN`, range [1.2,1.8] | 3.167 > 2.105 | FAIL; co che tang theo coverage dung |
| T6 | `r_CONG(0.78) > r_NHAN`, range [2.5,6.0] | inf > 2.105 | HIT direction; thoai hoa cuc bo |
| T7 | `err_system(NHAN) < err_system(CONG)` at 0.30 | +0.003014 | FAIL |
| T8 | two families indistinguishable at 0.78 | CI95 [-0.008569,-0.002476] | FAIL, useful |
| T9 | slot1 CONG share exceeds NHAN by >0.05 | -0.000728 at 0.78 | FAIL; slot 1 chi phoi ca hai ho |

## 8. Conclusion

Lesson 23.2 khong ung ho cau chuyen "CONG co the thang o coverage cao vi dieu
kien theo tuoi manh hon". CONG that su tro nen manh hon, nhung manh qua nhanh:
nguong bin tre cham san va ranking doi khac du 11.94% hang tai diem van hanh.

Ket luan van hanh sau Lesson 23.2:

1. Ho NHAN tiep tuc la ho chinh cho Phase 23 o diem van hanh.
2. Ho CONG/REGRET la doi chung dai so quan trong, khong phai ung vien thay the
   tot hon tren artifact nay.
3. G23-9 khong ep chuyen sang mot mat Pareto lon; chi can bao cao hai diem
   Pareto NHAN `kappa=0.20` va `0.25` khi noi ve argmin.
4. Co che thua cua CONG la thoai hoa cuc bo cua ho dich tren nguong duong:
   tai diem van hanh, cac bin tuoi tre da mat kha nang loc.
