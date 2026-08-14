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
test/test_phase23_fallback.py test/test_phase23_thresholds.py
21 passed in 9.78s
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
| G23-8 full coverage quy ve neo twin | PASS |

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
| 0.30 | 7.172372 | 3.108050 | 2.105339 | T5 FAIL |
| 0.50 | 13.333832 | 10.551382 | 2.105339 | diagnostic |
| 0.78 | 21.142389 | inf | 2.105339 | T6 direction HIT, range MISS |

`r_CONG = inf` tai coverage cao nghia la nguong bin tre nhat da cham san
khong duong. Ho CONG khong chi "manh hon"; no bat dau mat hinh dang co dieu
kien o dau tre cua dai tuoi.

## 3. Matched-coverage comparison

Risk toan he thong voi fallback F2 STATIC:

| coverage | err NHAN | err CONG | NHAN-CONG | regret NHAN | regret CONG | sla NHAN | sla CONG |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.30 | 0.274667 | 0.272975 | +0.001692 | 2.562068 | 2.571643 | 0.172240 | 0.172543 |
| 0.50 | 0.237484 | 0.239513 | -0.002028 | 1.988702 | 2.053445 | 0.155783 | 0.157868 |
| 0.78 | 0.209438 | 0.216905 | -0.007467 | 1.575283 | 1.681166 | 0.145521 | 0.149265 |

T7 truot tren thang err: tai coverage 0.30, NHAN khong thang CONG; no te hon
`0.001692` err. Tuy vay NHAN da tot hon nhe tren regret va sla, nen day la mot
bat dong thang rui ro cuc bo, khong phai loi thiet bi.

T8 truot theo huong co gia tri khoa hoc. Tai coverage van hanh, hai ho phan
biet duoc:

```text
coverage_mul = 0.777689
coverage_add = 0.787930
accept intersection = 0.723118
accept symmetric difference = 0.119384

delta_err(NHAN - CONG) = -0.004500
CI95 paired block bootstrap = [-0.007578, -0.001432]
```

Nhanh FAIL cua Amendment 23-10 khong kich hoat theo chieu CONG thang. Ket qua
nguoc lai: NHAN van thang ro o diem van hanh Phase 23.

## 4. Slot diagnostic

T9 du doan slot hep nhat se chi phoi CONG nhieu hon NHAN. Thuc te slot 1 chi
phoi gan nhu tat ca quyet dinh reject o ca hai ho:

| coverage | slot1 share NHAN | slot1 share CONG | CONG-NHAN |
|---:|---:|---:|---:|
| 0.30 | 0.999960 | 0.999920 | -0.000040 |
| 0.50 | 0.999756 | 0.998620 | -0.001136 |
| 0.78 | 0.999960 | 0.999232 | -0.000728 |

T9 FAIL. Co che GO-2 "slot hep chi phoi" dung theo nghia rong, nhung no chi
phoi ca hai ho, khong phai rieng CONG.

## 5. G23-9 and Pareto

Spearman tren toan luoi coverage:

| sweep | rho(err,regret) | rho(err,sla) | rho(regret,sla) | min |
|---|---:|---:|---:|---:|
| NHAN | 1.000000 | 0.978873 | 0.978873 | 0.978873 |
| CONG | 0.995565 | 0.995565 | 0.986696 | 0.986696 |
| combined | 0.998318 | 0.990582 | 0.985873 | 0.985873 |

Ba thang dong bien manh. Vi vay Lesson 23.4 co the ve mot duong
risk-coverage chinh, nhung van nen giu mat Pareto nho vi argmin dia phuong
khong trung tuyet doi.

Mat Pareto co 2 diem, deu thuoc ho NHAN:

| family | param | coverage | err | regret | sla |
|---|---:|---:|---:|---:|---:|
| NHAN | 0.25 | 0.737973 | 0.210270 | 1.598988 | 0.145156 |
| NHAN | 0.20 | 0.793460 | 0.209172 | 1.567691 | 0.145638 |

## 6. Prediction ledger

| ID | Noi dung | Do duoc | KQ |
|---|---|---|---|
| T5 | `r_CONG(0.30) < r_NHAN`, range [1.2,1.8] | 3.108 > 2.105 | FAIL |
| T6 | `r_CONG(0.78) > r_NHAN`, range [2.5,6.0] | inf > 2.105 | HIT direction, MISS range |
| T7 | `err_system(NHAN) < err_system(CONG)` at 0.30 | +0.001692 | FAIL |
| T8 | two families indistinguishable at 0.78 | CI95 [-0.007578,-0.001432] | FAIL, useful |
| T9 | slot1 CONG share exceeds NHAN by >0.05 | -0.000728 at 0.78 | FAIL |

## 7. Conclusion

Lesson 23.2 khong ung ho cau chuyen "CONG co the thang o coverage cao vi dieu
kien theo tuoi manh hon". CONG that su tro nen manh hon, nhung manh qua nhanh:
nguong bin tre cham san va ranking doi khac du 11.94% hang tai diem van hanh.

Ket luan van hanh sau Lesson 23.2:

1. Ho NHAN tiep tuc la ho chinh cho Phase 23 o diem van hanh.
2. Ho CONG/REGRET la doi chung dai so quan trong, khong phai ung vien thay the
   tot hon tren artifact nay.
3. G23-9 khong ep chuyen sang mot mat Pareto lon; chi can bao cao hai diem
   Pareto NHAN `kappa=0.20` va `0.25` khi noi ve argmin.
