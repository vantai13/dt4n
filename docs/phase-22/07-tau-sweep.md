# LESSON 22.6 -- tau_sweep.py

Ngay: 2026-08-13

Trang thai: da chay tren du lieu Phase 22 v3 that. Muc tieu la kiem tra
ratio tuoi B3/B0 ~ 2.17 la dinh luat co che cua AR(1), hay chi la artefact
cua tau=1.

## 1. San pham

| File | Vai tro |
|---|---|
| `cert/tau_sweep.py` | dung lai physics v3, override tau, block_s = 5*tau |
| `test/test_phase22_tau.py` | 13 golden tests khoa gate G22-10/G22-11 va cac doi chung |
| `results/phase-22/tau_sweep_*.json` | ket qua cho o chinh, o phu, va cbr positive control |

Lenh chinh:

```text
/tmp/dt4n-venv/bin/python -m cert.tau_sweep --mode poisson --rho-bar 0.925 \
  --out results/phase-22/tau_sweep_poisson_0.925.json
```

## 2. Mo hinh

Voi AR(1) dung yen:

```text
Var(rho(t) - rho(t-z)) = 2*sigma^2*(1 - exp(-z/tau))
rms_es(z) = A*sqrt(1 - exp(-z/tau))
rms_total(z)^2 = rms_em^2 + c*A^2*(1 - exp(-z/tau))
```

Trong do:

```text
A   = bien do staleness tren thang cost_ms; du doan doc lap voi tau
c   = 1 + 2*E[e_model*e_stale]/rms_es^2
em  = san sai so model; khong phai staleness
```

Ratio bao hoa:

```text
R_inf(tau) = sqrt((1 - exp(-0.425/tau)) / (1 - exp(-0.077/tau)))
R_inf(1.0) = 2.1614
```

Thiet ke song con: block la `5*tau`, khong phai 5 giay. Khi tau thay doi,
block length thay doi tu 2.5s den 25s; n_calib_blocks vi vay giam tu 1000
xuong 100.

## 3. O chinh poisson@0.925

Tat ca gate trong JSON deu PASS.

### Tham so bat bien

| tau | A | A spread % | c | c spread % | rms_em | A/em | max rel err |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 25.976 | 1.345 | 0.89770 | 0.588 | 2.1400 | 12.14 | 0.781% |
| 1.00 | 26.023 | 1.576 | 0.89412 | 0.644 | 2.1401 | 12.16 | 0.752% |
| 2.00 | 26.076 | 1.572 | 0.89044 | 1.174 | 2.1482 | 12.14 | 0.883% |
| 2.87 | 26.093 | 1.411 | 0.89027 | 1.058 | 2.1458 | 12.16 | 0.751% |
| 5.00 | 26.175 | 1.898 | 0.88837 | 1.963 | 2.1339 | 12.27 | 1.128% |

Tom tat:

```text
A      : 25.976 -> 26.175   span 0.762%
c      : 0.88837 -> 0.89770 span 1.046%
rms_em : 2.1339 -> 2.1482  span 0.664%
```

Ket luan: tau doi 10 lan, nhung A doi duoi 1%. Day la kiem tra co che
manh hon R2: tham so duoc du doan bat bien va that su bat bien.

### Ratio B3/B0

| tau | do duoc | ly thuyet finite | do/finite | bao hoa R_inf | qhat B0 |
|---:|---:|---:|---:|---:|---:|
| 0.50 | 1.9779 | 1.9647 | 1.0067 | 2.0029 | 15.5419 |
| 1.00 | 2.0990 | 2.0813 | 1.0085 | 2.1614 | 11.5878 |
| 2.00 | 2.1432 | 2.0942 | 1.0234 | 2.2514 | 8.5767 |
| 2.87 | 2.0834 | 2.0647 | 1.0091 | 2.2802 | 7.6411 |
| 5.00 | 2.0076 | 1.9770 | 1.0155 | 2.3092 | 6.3163 |

Ratio do duoc khong don dieu:

```text
1.9779 -> 2.0990 -> 2.1432 -> 2.0834 -> 2.0076
```

Mo hinh finite-floor khop ratio trong 0.7-2.3%. Mo hinh do tu tham so tai
tau=1 du doan dinh tai:

```text
tau* = 1.559, R = 2.1013
```

Pham vi ket luan: luoi tien dang ky `{0.5, 1.0, 2.0, 2.87, 5.0}` xac nhan
tinh KHONG DON DIEU, nhung khong do duoc chinh xac vi tri dinh. Muon kiem
vi tri dinh can mot luoi min hon va phai tien dang ky rieng.

### Doi chieu du doan

| # | Du doan da ky | Dai | Do duoc | KQ |
|---:|---|---:|---:|---|
| 1 | R(tau=0.50) | 1.77-2.16 | 1.9779 | PASS |
| 2 | R(tau=1.00) | 1.87-2.29 | 2.0990 | PASS |
| 3 | R(tau=2.00) | 1.88-2.30 | 2.1432 | PASS |
| 4 | R(tau=2.87) | 1.86-2.27 | 2.0834 | PASS |
| 5 | R(tau=5.00) | 1.77-2.17 | 2.0076 | PASS |
| 6 | R(tau) hinh chuong, khong don dieu | TRUE | khong don dieu | PASS |
| 7 | A doc lap voi tau | <2% | 0.762% | PASS |

Du doan: 7/7 dung.

## 4. Bao phu troi theo tau

| tau | n_calib_blocks | level finite-sample | coverage mean | cov - level |
|---:|---:|---:|---:|---:|
| 0.50 | 1000 | 0.9010 | 0.9006 | -0.0004 |
| 1.00 | 500 | 0.9020 | 0.9096 | +0.0076 |
| 2.00 | 250 | 0.9040 | 0.9068 | +0.0028 |
| 2.87 | 175 | 0.9086 | 0.9157 | +0.0072 |
| 5.00 | 100 | 0.9100 | 0.9222 | +0.0122 |

Bao phu tang khi tau tang khong phai loi mo hinh. Tau lon lam block dai hon,
so block calib it hon, va muc phan vi huu han mau
`ceil((n+1)*(1-alpha))/n` bao thu hon.

## 5. O phu va doi chung

| Cell | gates true/total | A span % | A/em | ratio tau grid |
|---|---:|---:|---:|---|
| `poisson@0.925` | 11/11 | 0.762 | 12.14-12.27 | 1.9779, 2.0990, 2.1432, 2.0834, 2.0076 |
| `poisson@0.850` | 10/11 | 0.828 | 9.23-9.95 | 1.9489, 2.1078, 2.0868, 2.0417, 1.9766 |
| `h2@0.700` | 10/11 | 0.123 | 6.66-6.74 | 1.9214, 1.9856, 1.9222, 1.8366, 1.7383 |
| `cbr@0.700` | 8/11 | 0.176 | 0.02-0.02 | 0.9874, 1.0011, 0.9964, 0.9982, 0.9984 |

`cbr@0.700` la PC22-1 quan trong: khi `A/rms_em` rat nho, ratio khong the
di toi vung 2.16. No gan 1.0 o moi tau. Day la cho mo hinh tien doan minh
se "vo", va du lieu xac nhan dung cho vo do.

## 6. Dong gioi han

```text
L3  Bao dam chi cho AR(1) tong hop, tau=1.0
    -> Dong mot phan: bao phu va co che giu tren tau in [0.5, 5.0],
       gom tau=2.87 do duoc cua tai loi that.
    -> Con mo: moi thu van la AR(1); tai that co the khong phai AR(1).

L8  Ratio tuoi 2.17 la quan sat, chua la dinh luat
    -> Dong: 2.17 la gia tri bao hoa cua R_inf(tau) khi A/rms_em lon.
       R_inf(1.0)=2.1614 gan 21R operational ratio 2.1766.
       cbr@0.700 xac nhan dieu kien vo khi A/rms_em nho.
```

## 7. Tests

```text
/tmp/dt4n-venv/bin/python -m pytest test/test_phase22_tau.py -q
13 passed in 0.36s

/tmp/dt4n-venv/bin/python -m pytest -q test/test_phase22_simscore.py test/test_phase22_calibv3.py test/test_phase22_conformalsim.py test/test_phase22_selective.py test/test_phase22_matrix.py test/test_phase22_tau.py
81 passed in 129.74s (0:02:09)

/tmp/dt4n-venv/bin/python -m pytest -q
718 passed, 4 skipped in 308.36s (0:05:08)
```
