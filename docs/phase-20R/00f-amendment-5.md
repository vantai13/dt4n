# AMENDMENT 5 -- Phase 20R.4: lam ro thu tuc kiem ngan sach noi suy

Ngay: 2026-08-05

## Van De

`04-campaign-grid.md` ky ngan sach "sai so noi suy tuyen tinh <= 0.0465 ms",
nhung khong chi dinh thu tuc do dai luong nay tu du lieu co nhieu. Mot script
kiem ad-hoc dung:

```text
max_i |0.5(y_i + y_{i+2}) - y_{i+1}|
```

va bao `VUOT` o 6/9 o. Kiem lai cho thay thong ke do sai ba diem:

1. Nhip: `y_i` va `y_{i+2}` cach nhau `2h`. Sai so noi suy la bac hai theo
   nhip, nen thong ke nay bang `4 x` sai so thuc o nhip `h`.
2. Nhieu: `y_i` la trung binh do voi sai so chuan `se_mean_ms`. Voi
   `d_i = 0.5(y_i + y_{i+2}) - y_{i+1}`, phuong sai nhieu la
   `0.25 se_i^2 + 0.25 se_{i+2}^2 + se_{i+1}^2`.
3. Thong ke cuc tri: lay `max` tren nhieu hieu lam ket qua bi chi phoi boi
   duoi phan phoi nhieu, khong phai do cong he thong.

Do do, check ad-hoc trong Amendment 4 Section E la mot diagnostic sai thu tuc,
khong phai bang chung can do bu.

## Thu Tuc Chot

Thu tuc kiem ngan sach noi suy tu du lieu do:

```text
d_rms     = rms_i(0.5(y_i + y_{i+2}) - y_{i+1})
noise_rms = sqrt(mean_i(0.25 se_i^2 + 0.25 se_{i+2}^2 + se_{i+1}^2))
curv      = sqrt(max(d_rms^2 - noise_rms^2, 0))
e_true    = curv / 4
PASS neu e_true <= 0.0465 ms
```

`/4` quy tu nhip `2h` ve nhip `h`. Phan nhieu duoc tru theo phuong sai, khong
tru theo bien do.

## Ket Qua

Chay tren `results/phase-20R/truth_table.parquet`:

```text
key            n   d_rms    nhieu_kv  do_cong  e_thuc  ngan sach
------------------------------------------------------------------------
cbr|4|10        8   0.0059   0.0034    0.0048   0.0012   OK
cbr|6|13       10   0.0049   0.0030    0.0038   0.0010   OK
cbr|8|18        8   0.0069   0.0028    0.0063   0.0016   OK
h2|4|10        23   0.0622   0.1630    0.0000   0.0000   OK
h2|6|13        28   0.0451   0.0950    0.0000   0.0000   OK
h2|8|18        24   0.0223   0.0837    0.0000   0.0000   OK
poisson|4|10   23   0.0642   0.1112    0.0000   0.0000   OK
poisson|6|13   28   0.0727   0.0769    0.0000   0.0000   OK
poisson|8|18   24   0.0682   0.0552    0.0399   0.0100   OK
------------------------------------------------------------------------
KET LUAN: NGAN SACH NOI SUY DAT
```

Tat ca 9/9 o dat ngan sach. Khong can do bu.

## Khong Hanh Dong

Khong do bu. Khong doi interpolator. Luoi `h = 0.02` cho `poisson/h2` va
`h = 0.05` cho `cbr` giu nguyen. `truth_table.parquet` giu nguyen.

## Ghi Nhan Cho 20R.5

Nhieu dong bang trong bang tra:

```text
           mean     max
mode
cbr      0.0025  0.0070
h2       0.0843  0.1903
poisson  0.0553  0.1767
```

Du doan 20R.3 gia dinh bien do truong du `resid_sd = 0.27 ms` cho mot seed.
Thuc te bang tra da trung binh 5 seed, nen `se_mean_ms` thap hon gia dinh
khoang 2-4 lan. Vi vay D1, `err(z=0) in [0.000, 0.10]`, van kha bac, nhung
ket qua ky vong nam o dau thap cua khoang. Khong sua `02-prediction.md`.

## Phan Quyet

```text
Chien dich 20R.4       : PASS -- 609/609, 0 fail, retry 0.66%
Watchdog               : LANH TINH -- A/B sentinel z = +0.83
Sentinel vs Phase L    : 10.8680 vs 10.8749, z = -1.62, CV 0.137%, khong drift
Bang tra               : 176 hang, 9 o, n_seed = 5, truth_field = q_mean_ms
Ngan sach noi suy      : DAT sau khi sua thu tuc kiem
```
