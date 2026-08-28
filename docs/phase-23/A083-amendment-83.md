# AMENDMENT 23-83 -- PHAN RA R, TRUY CO CHE

Ngay ky : 2026-08-28
Moc     : sau A082/23.25f (M-276 MISS), TRUOC khi chay T13
Loai    : TIEN DANG KY T13. G23-339 dung so A082 DA BIET, mang nhan hau kiem.

## 1. Vi sao A082 khong ket luan duoc

Doi chung am cua A082 gia dinh: "cell 0.700 khong censoring => measured ~
offered". Gia dinh nay sai vai tro: shortfall, residual tuong quan T9 va lech
thoi gian co the lam measured khac offered o moi cell. Cell 0.700 chi la
control cho censoring, khong la control sach cho measured-vs-offered.

M-275/M-276 giu nguyen ket qua lich su va gate G23-334 van FAIL. A083 khong
doi no thanh HIT; A083 thay estimand de truy co che cua R.

## 2. Dinh nghia T13

```text
R_num = |E[m]|_measured / |E[m]|_offered
R_den = sd(m)_measured / sd(m)_offered
R = R_num / R_den
```

Quet cross-correlation measured/offered tren +-10 s, `dt=0.2 s`.
`max |lag|` la maximum qua 15x8 link-run, nen rat nhay voi mot chuoi mu;
van cham dung M-281 da ky, dong thoi bat buoc in median/p90/ti le cham bien.

`R_num` VAN la ti so va mau so `|E[m]|_offered` co the gan 0. Khong loai mau
sau khi xem. Artifact bat buoc in min denominator, quantile va sensitivity
`ratio_of_medians`; neu hai cach doc lech lon, M-280 chi la diagnostic.

## 3. Du doan bang so (khoa truoc T13)

| ID | Dai luong | Dai ky |
|---|---|---:|
| M-279 | R_den median, gop 15 run | 0.80 .. 1.10 |
| M-280 | R_num median, gop 15 run | 1.00 .. 1.25 |
| M-281 | max `abs(lag)` khi quet +-10 s | <= 1 mau |
| M-282 | R_den(n_noisy=2) < R_den(n_noisy=1) | bao cao; khong cham |
| M-283 | `abs(mean shift)` lon nhat theo link | bao cao; khong cham |
| M-284 | denominator/sensitivity cua R_num | bao cao; khong cham |

## 4. Nhanh phu kin

```text
M-281 >1 mau -> TIME_MISALIGNMENT_SUSPECTED. Moi dien giai tri so
                measured-vs-offered TREO; can can chinh truoc.
Neu M-281 dat:
  R_den <0.95 -> SD_COMPRESSION_CORRELATED_RESIDUAL; ghi limit.
  R_num >1.10 -> MEAN_SHIFT_SHORTFALL; hieu chuan mean truoc khi dung rho.
  ca hai ~1  -> NO_DOMINANT_MECHANISM; bo R, dung phan ra.
```

Nhanh co the chong lap. Uu tien time-alignment nhu code; khong duoc chon
verdict gan nhat sau khi xem bang.

## 5. Rut lai tu A082

M-275/M-276 khong duoc doc lam ket luan ve censoring. K09=1.009410 ha
`p_censored` ve 0.0004--0.0361, nen lo ngai "49% censored" bi bac. M-278
Spearman=+0.10, p=0.87, n=5 KHONG ho tro quan he censoring->R, nhung cung
khong phai mot kiem dinh tuong duong va khong chung minh null.

## 6. G23-339 -- phan xu HAU KIEM ve bat bien thu hang

So duoi da co trong artifact A082 truoc khi ky A083:

```text
SNR_measured: 0.850 < 0.700 < 0.900 < 0.925 < 0.960
SNR_offered : 0.850 < 0.900 < 0.700 < 0.925 < 0.960
```

Cham may: Spearman giua hai thu hang, argmax co trung khong, va
`SNR_offered(0.960)>SNR_FLAT=0.25`. Neu argmax trung va ve cuoi dat, cho phep
chon cell `clean@0.960` cho 23.26 o muc QUYET DINH KY THUAT. Khong nang thanh
bang chung tien dang ky; do lon SNR va D2/D3 corrected van UNDECIDED.

## 7. Gate

```text
G23-337  phan ra R_num/R_den, gop va theo cell
G23-338  can chinh thoi gian, quet +-10 s
G23-339  bat bien thu hang cell [POST-HOC ADJUDICATION]
```
