# Lesson 23.19 Task D + E -- khoa `Z_EDGES` va bon doi chung

Ngay     : 2026-08-22
Prereg   : `docs/phase-23/00zze-amendment-48.md` (tag `amendment-48`)
Ma nguon : `measurements/aoi_model_v7.py`, `test/test_phase23_task_e_controls.py`

## 1. Hai sua truoc khi di tiep

### 1.1 RUT co che "d_transport lech phai"

Amendment 23-47 muc 2 quy lech trung vi `7.929 ms` cho skew cua `d`. **Sai.**
Bi loai bang ngan sach phuong sai va luat cong skew:

```text
Var(phase) + Var(alpha) = 20857.69 + 94.08 = 20951.77
Var(z) quan sat                            = 20927.80    -> con lai -23.97 (AM)

gamma_X = gamma_D * sigma_D^3 / sigma_X^3          <- LUY THUA BA
de dat mean-median = 7.929 ms can sigma_d = 49.74 ms
   -> sd(z) phai = 153.06 ms, quan sat 144.66 ms   MAU THUAN +8.39 ms
voi sigma_d = 5 ms  -> mean-median ~ 0.008 ms      thieu ~1000 lan
```

`corr = 0.9637` tren 8 diem cho biet **cung chieu**, khong cho biet **cung
do lon**. Tuong quan khong bao gio thay duoc ngan sach.

### 1.2 TU CHOI cach sua dai selfcheck bang `sigma_d`

De xuat: cong `sigma_d = 3.32 ms` vao dai -> `M-110` PASS. Khong nhan.

```text
d = mean_quan_sat - T/2  =>  bat dinh cua d TUONG QUAN HOAN TOAN voi mean
quan sat. Cong no vao dai la DEM HAI LAN.
```

Ba dac ta, cung 200 chien dich:

```text
                            p05            p50            p95
A  dai tho                 TRONG   TRONG (1.61)   NGOAI (2.26)
B  cong sigma_d            TRONG   TRONG (1.32)   TRONG (1.64)   <- moi thu PASS
C  chuan hoa theo mean     TRONG   NGOAI (4.10)   NGOAI (4.03)   <- DUNG
```

Dac ta **C** dung vi `d` triet tieu chinh xac trong `(phan vi - mean)`, va
tautology cua `mean` bi loai TU DONG. `M-110` = **1/3**.

Phan du `~8 ms` tren trung vi ghi thanh **`L35`**: da loai BON co che
(alpha / nghich ly kiem tra / cai luoc / `d` lech phai), van CHUA BIET.
`1.6%` cua `T`, nho hon hieu ung dang do (`65 ms`) 8 lan. Ghi va di tiep.

## 2. Task D -- `Z_EDGES_V7`

```text
Z_EDGES_V7 = (0.100, 0.241, 0.366, 0.491, 0.641)   [giay]

  B0 [100, 241) : 25.0071%   z_tb 178.1 ms
  B1 [241, 366) : 24.9875%   z_tb 303.5 ms
  B2 [366, 491) : 24.9852%   z_tb 428.5 ms
  B3 [491, 641) : 25.0203%   z_tb 553.9 ms
  ngoai dai     :  0.000000%
```

Canh trong la tu phan vi cua `z` mo hinh. Canh ngoai noi rong tu bien thuc
`(107, 634)` ra `(100, 641)` de phu ca `d` o hai dau CI `+/-6.5 ms` -- vi
neu `d` duoc chinh lai sau nay, bo canh chi phu diem uoc luong se lam MAT
hang. Noi rong **khong doi ty trong bin** (giong den chu so thu tu).

Bo canh CU vo hoan toan tren truc moi:

```text
B0 [ 55, 100) :  0.0000%   <- RONG => q_hat = +inf, n_g < 9, pipeline gay
B1 [100, 200) : 16.8110%
B2 [200, 300) : 19.9900%
B3 [300, 550) : 49.9897%
ngoai dai     : 13.2093%   <- MAT TRANG
```

## 3. Task E -- bon doi chung

```text
M-117  NC-E1  bit-exact voi bo sinh CU (3 cau hinh n/dt)         HIT
M-117b        `_valid_rows` (chon hang 21R) cung bit-exact       HIT
M-118  NC-E2  pha CHUNG cho 8 link -- kiem DAI SO (allclose)     HIT
M-119  PC-E1  ty trong bin phat hien duoc instrument_mode?       MISS
M-120  PC-E2  canh CU tren truc moi -> B0 RONG                   HIT
M-114         ty trong bin lech thiet ke < 2 diem %              HIT
M-115         hang ngoai dai = 0                                 HIT
```

### `M-119` MISS -- va do la ket qua quan trong nhat cua Task E

Du doan da ky: neu lo dung `instrument_mode` trong pipeline thi ty trong bin
lech `> 5 diem %`, tuc ta se PHAT HIEN duoc o ha nguon. **Do duoc: ~2 diem %.**

```text
Cai luoc co 5 rang moi chu ky (cach nhau T/5 = 100 ms) trong khi bin rong
125-150 ms, va pipeline gop 8 link co do lech doc khac nhau.
=> o DO PHAN GIAI 4 BIN, cai luoc gan nhu bi lam phang.
```

```text
=> KHONG duoc dua vao mot phep kiem HA NGUON de bat viec dung nham che do.
   Su tach bach phai duoc bao dam o MUC CAU TRUC:
     - hai ham ten khac nhau, docstring canh bao
     - test_two_modes_are_not_interchangeable kiem o DO PHAN GIAI 50 BIN,
       noi khac biet la ro rang (max/min ~7 vs 1.00)
```

Ghi chu ky thuat: o do phan giai 50 bin, "so bin rong" KHONG on dinh giua
cac pha ban dau (10/30 seed), nhung ty so `max/min` thi on dinh (29/30 seed
`> 3`). Test dung ty so tren nam pha co dinh.

## 4. Con lai cua Task E: mot quyet dinh CAU TRUC chua lam

Thay hang so trong `build_calib_set_v3` KHONG du. `sawtooth_age_steps` duoc
dung o hai cho voi mot y nghia rong hon mot hang so:

```text
cert/build_calib_set_v3.py:217  _valid_rows()  -> chon hang cua 21R
cert/build_calib_set_v3.py:328  age_steps      -> gan z_bin
```

Ca hai deu sinh **MOT chuoi tuoi cho ca cell**, trong khi mo hinh moi co
`alpha` **theo tung link**. Repo da co san co che offset theo link
(`AOI_PROFILES`, `Z_STEP_OFFSETS_PRIMARY`, `y_hat_rho_shift(..., off)`), nen
`alpha` anh xa duoc vao do -- nhung viec chon anh xa nao la mot **quyet dinh
cau truc**, khong phai mot phep thay hang so:

```text
lua chon 1  tuoi CO SO tu mo hinh (d + phase chung), alpha vao qua co che
            offset san co -> giu nguyen hinh dang pipeline
lua chon 2  tuoi theo tung link ngay tu `_valid_rows` -> doi ca cach chon
            hang, va `n_rows` se khac nhau giua cac link
```

Lua chon 2 lam `n_rows` lech theo link, anh huong den `n_g` cua tung bin va
do la thu `G23-100` (>= 9 block moi bin moi cell) dang canh gac. **Chua chon.
Can mot amendment rieng va la viec dau tien cua Lesson 23.20.**

API da san sang: `AoIModelV7.process_mode_steps()` (bi danh cung
`age_steps`) va `Z_EDGES_V7`.

## 5. Gate

| Gate | Noi dung | Trang thai |
|---|---|---|
| G23-103 | `Z_EDGES_V7` khoa TRUOC khi nhin `s(z)`; 4 bin ~25%, 0% ngoai dai | PASS |
| G23-104 | NC-E1 bit-exact (tuoi va chon hang) | PASS |
| G23-105 | NC-E2 pha CHUNG cho 8 link, kiem dai so | PASS |
| G23-106 | PC-E2 canh cu tren truc moi -> B0 rong | PASS |
| G23-107 | PC-E1 ty trong bin phat hien duoc dung nham che do | FAIL -- ~2 diem %, xem muc 3 |
| G23-108 | selfcheck chuan hoa theo mean, `mean` bi loai khoi phep kiem | PASS |
