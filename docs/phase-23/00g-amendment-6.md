# AMENDMENT 23-6 -- Retract F3-a look-ahead accounting

Ngay: 2026-08-14

Ly do: loi code phat hien khi kiem toan Lesson 23.1, sau ket qua fallback dau
tien va truoc khi chot ket luan Phase 23.

## Loi bi phat hien

Ban `fallback_wait` cu gan:

```text
a_chosen[t] = a_twin[t']
```

trong do `t'` la refresh ke tiep, roi cham diem action do tren hang goc `t`.
Voi `z(t) < 0.500`, anh chup dung de tao `a_twin[t']` nam sau thoi diem `t`.
Day la look-ahead bias / temporal leakage.

Ba so kiem toan tren artifact C3, kappa=0.5:

```text
ti le hang reject co the dung thong tin tuong lai = 0.8584
horizon trung binh                              = +168.5 ms
horizon lon nhat                                = +445.0 ms
P(a*(t) == a*(t')) tren hang reject co the cho  = 0.7753
```

Viec `a*(t)` va `a*(t')` chi trung nhau 77.53% cho thay drift la that; day
khong phai sai so ke toan vo hai.

## Quyet dinh truoc khi do lai

Lesson 23.1 khong mo fallback thu tu va khong chuyen sang F3-c. F3-a duoc ghi
la suy bien:

```text
F3-a WAIT == F1 STICKY theo row-level installed-path accounting.
```

Ly do vat ly: trong luc cho, data plane van chay tren duong dang cai. Tai
refresh, cung chinh sach duoc ap lai. Khong co hang nao ma F3-a co action
khac F1.

## He qua

Con so cu:

```text
err_system_exposed(F3-a) = 0.183222
```

bi rut lai. No khong do mot chinh sach hop le; no do loi ke toan dua action
tuong lai ve cham diem qua khu.

Du doan F3/F4/F6 neu trung nho con so nay duoc cham la VO HIEU, khong phai HIT.
Ket luan Lesson 23.1 phai do lai voi:

```text
F2 STATIC
F1 STICKY
F3-a WAIT diagnostic, row-level action == F1
```
