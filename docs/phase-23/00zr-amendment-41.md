# AMENDMENT 23-41 -- Lesson 23.16: domain control phai khop distribution duoc cham

Ngay: 2026-08-21
Trang thai: **SAU lan chay domain-only dau tien; TRUOC khi build bat ky calib
set moi va TRUOC khi tinh err_neo, lift, swing hoac Delta.**

## 1. Loi thiet ke control vua phat hien

Amendment 40 yeu cau dung dung rho generator nhung chua ghi ro bien do.
Implementation dau tien kiem dong thoi:

```text
sigma_sla_regime = sigma hieu chuan trong sla_calibration
sigma_builder    = 0.0096, hang so da khoa cua calib_set_v3
```

Calib-set Phase 23 thuc te chi duoc sinh va cham tai `sigma_builder=0.0096`.
Bat ca hai distribution cung PASS se loai cell vi mot distribution khong
nam trong estimand. Lan chay dau tien chi tao SLA/domain artifact; chua build
parquet va chua tinh bat ky outcome certificate nao.

Readout domain-only:

| Cell | max clip SLA-regime | max clip builder |
|---|---:|---:|
| poisson@0.875 | 0.005180 | 0.000000 |
| poisson@0.900 | 0.006330 | 0.000000 |
| h2@0.650 | 0.000325 | 0.000000 |
| h2@0.675 fallback diagnostic | 0.000770 | 0.000000 |

## 2. Sua control truoc outcome

Domain **gate** dung distribution se duoc build/cham:

```text
rho generator = calibration_ar1
sigma         = SIGMA=0.0096 tu cert.build_calib_set_v2
seeds         = 101..105
PASS          <=> max clip moi seed/link < 1e-4
```

Distribution `sigma_sla_regime` van duoc ghi day du thanh stress diagnostic,
nhung khong quyet dinh eligibility cua dataset khac. Khong duoc trộn stress
distribution vao ket luan cua builder distribution.

Theo rule nay ba primary candidate deu qua domain; fallback `h2@0.675` khong
duoc build. Khong co cell nao duoc chon bang `err_neo`, lift, swing hay Delta.

## 3. Phan khong doi

M-53..M-57, M-47b, M-48b, nguong song `0.05`, threshold domain `1e-4`, stop
rules va toan bo he thong dong bang cua Amendment 40 giu nguyen. Artifact
SLA/domain dau tien bi supersede va phai chay lai tu code da commit.
