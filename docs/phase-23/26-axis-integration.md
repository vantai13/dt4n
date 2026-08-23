# Lesson 23.19 Task E (con lai) -- tich hop truc tuoi do duoc

Ngay     : 2026-08-22
Prereg   : `docs/phase-23/00zzf-amendment-49.md` (tag `amendment-49`)
Ma nguon : `cert/build_calib_set_v3.py`, `measurements/aoi_model_v7.py`
Test     : `test/test_phase23_axis_integration.py` (15 test)

## 1. Quyet dinh kien truc: LC1, va LC2 BAT KHA

```text
LC1  tuoi co so SCALAR tu mo hinh + alpha qua AOI_PROFILES / off_steps   <- CHON
LC2  tuoi theo tung link ngay tu `_valid_rows`                           <- BAT KHA
```

`_valid_rows` tra ve `cur`/`old` dung de index ma tran rho cho **ca 8 link
cung luc**. MOT HANG cua calib set la MOT QUYET DINH, va quyet dinh can du
8 link tai CUNG mot thoi diem. Neu moi link co tap hang hop le rieng thi
khong dung duoc mot hang nao. Day la ly do BAN CHAT, khong phai tien loi.

LC1 khop dung hinh dang mo hinh, vi `build_calib_set_v3` DA tach san mot
truc SCALAR (`age`) va mot truc THEO LINK (`off`).

## 2. `U3` va `D_BASE` -- dan xuat, khong khai bao

`offset_steps()` cam offset am (`raise ValueError("offset am khong hop le")`),
ma `alpha` co 5/8 gia tri am. Test `test_u3_would_be_rejected_without_the_shift`
chung minh phep dich la BAT BUOC chu khong phai trang tri.

```text
U3     = (20.0, 25.0, 0.0, 0.0, 0.0, 0.0, 5.0, 15.0) ms   [thu tu T7.LINK_NAMES]
steps  = (   4,    5,   0,   0,   0,   0,   1,    3)
D_BASE = 115.9 - 8.125 = 107.775 ms
```

Ca hai la **HAM** cua `ALPHA_S` va `dt` (`u3_profile_ms()`, `d_base_s()`),
nen neu `alpha` duoc do lai thi chung tu doi theo, khong the lech nhau.

### Bay 0.565 ms

```text
trung binh DANH DINH cua phan dich = 8.690 ms
trung binh THUC (sau luong tu hoa) = 8.125 ms
```

Dung nham lam `mean(z_s)` lech `-0.565 ms`. Do duoc (PC-E4):

```text
D_BASE dung trung binh THUC     : mean(z_s) = 366.0140 ms   M-121 HIT
D_BASE dung trung binh DANH DINH: mean(z_s) = 365.4608 ms   M-121 FAIL
```

Bay nay **khong the thay bang mat**; chi `M-121` voi dai `+/-0.10 ms` bat duoc.

## 3. CORRECTION: `U1` va `U2` khong bao toan trung binh

```text
ho so   mean (ms)   sd (ms)
U0          0.000     0.000
U1         22.500    14.841    <- dich mean TUOI +22.5 ms
U2         12.500    12.500    <- dich mean TUOI +12.5 ms
U3          8.125     9.662    <- BU TRU qua D_BASE -> tuoi trung binh bao toan
```

So `U0/U1/U2` o Phase 22 la so **dong thoi** HINH DANG ho so VA MUC TUOI.
Rieng `U1` doi mean z `+22.5 ms`, tuong duong `q_hat +2.6%` qua do gian
`z^0.431`, khong lien quan gi den hinh dang. Cung cham `M-76` cua Lesson 23.8:
RMSE cua `U1/U2` so voi `alpha` thua MOT PHAN vi do lech trung binh.

Da them `U1c`/`U2c` (trung tam hoa, cung co che voi `U3`). Ket luan ve HINH
DANG chi duoc dung `U0/U1c/U2c/U3`; ket luan cu giu nhan
`CONFOUNDED_SHAPE_AND_LEVEL`. **Khong rut so cu.**

## 4. Ket qua BUOC 5a

### NC-E1 -- nhanh fail cung: PASS

```text
poisson@0.925, axis=legacy, U0, 5 seed, n = 200.000
  shape CU (999945, 24)   MOI (999945, 45)
  z_s        max|diff| = 0.000e+00   BIT-EXACT
  z_bin      max|diff| = 0.000e+00   BIT-EXACT
  z_bin2     max|diff| = 0.000e+00   BIT-EXACT
  gap_true   max|diff| = 0.000e+00   BIT-EXACT
```

Va `validate_v3` (vốn doi chieu voi ban v2, gom `V22-1` so hang va `V22-5`
so block o giao) PASS -- mot phep kiem bit-exact doc lap thu hai.

### Bon so cua truc MOI

```text
poisson@0.925, axis=measured_v7, U3, 5 seed, n = 200.000

M-121  mean(z_s)         = 366.0140 ms       dai khoa 366.07 +/- 0.10    HIT
M-122  ty trong bin      = [0.2494, 0.2499, 0.2499, 0.2509]
       lech lon nhat     = 0.089 diem %      dai khoa < 2                HIT
M-123  hang ngoai dai    = 0                 dai khoa = 0                HIT
M-124  so block moi bin  = {0:500, 1:500, 2:500, 3:500}  min 500 >= 9    HIT

z_s: min 118.125 ms   max 618.125 ms
```

### `M-124` = 500 cho MOI bin -- va do la dieu da duoc du lieu truoc

Chu ky `T = 500 ms` ngan hon block `5 s` muoi lan, nen **mot block dong gop
hang cho CA BON bin**. So block "hieu dung" moi bin vi the la 500 (toan bo
block), khong phai `600 x 25% = 150`.

Day la tinh chat **DA CO tu v2** (rang cua cu cung `T = 500 ms`), khong phai
do bo canh moi gay ra. Nghia la rang buoc `n_g >= ceil(1/alpha) - 1 = 9`
duoc thoa rat rong -- nhung cung nghia la cac bin KHONG doc lap ve block, va
dieu do da dung voi v2 nen so sanh CU vs MOI van hop le.

## 5. Bang doi chung

```text
NC-E1  axis=legacy + U0 -> BIT-EXACT ban cu                        PASS
NC-E3  axis=measured + U0 -> mean(z_s) = D_BASE + T/2              PASS
PC-E3  axis=measured + canh CU -> B0 RONG, mat > 10% hang          PASS
PC-E4  D_BASE danh dinh -> M-121 FAIL (365.4608 vs 366.07)         PASS
V-E1   pha CHUNG cho 8 link, kiem dai so allclose                  PASS
L36    instrument_mode bi chan o KIEU DU LIEU trong `_valid_rows`  PASS
```

`L36` truoc day la `G23-107` FAIL (chan bang thong ke ha nguon khong duoc,
vi o do phan giai 4 bin cai luoc bi lam phang ~2 diem %). Nay chan o **kieu
du lieu**: `instrument_mode()` tra ve `InstrumentSamples`, va `_valid_rows`
raise `TypeError` neu nhan phai. Test `test_L36_guard_is_actually_in_valid_rows`
dung `monkeypatch` de chac chan cai chan nam TRONG pipeline chu khong chi
trong test.

## 6. Gate

| Gate | Noi dung | Trang thai |
|---|---|---|
| G23-109 | amendment 23-49 commit RIENG, co tag, TRUOC moi code | PASS |
| G23-110 | NC-E1 bit-exact, diff = 0 (nhanh fail cung) | PASS |
| G23-111 | M-121 mean(z_s) = 366.07 +/- 0.10 ms | PASS -- 366.0140 |
| G23-112 | M-122 ty trong 4 bin lech < 2 diem % | PASS -- 0.089 |
| G23-113 | M-123 0% hang ngoai dai | PASS -- 0 |
| G23-114 | M-124 moi bin >= 9 block | PASS -- min 500 |
| G23-115 | L36 chan o KIEU du lieu (thay cho chan thong ke da FAIL) | PASS |
| G23-116 | PC-E4: D_BASE danh dinh -> M-121 FAIL dung du kien | PASS |

### Va cham ma gate thu NAM

Ban ke hoach danh so `G23-101 .. G23-114`, nhung `G23-100 .. G23-108` DA
duoc cap (23.19B, 23.19DE). Task E dung `G23-109` tro len. Da bo sung
`test_no_duplicate_gate_or_limit_ids` de chan lan thu sau.

## 6b. Mot khoa DA CO bat duoc viec them ho so

`test_phase22_calibv3.py::test_GC1_profiles_locked` ghim tap ho so vao dung
`["PC4","U0","U1","U2"]`. Them `U3`/`U1c`/`U2c` lam no FAIL -- **dung**: do
la mot khoa chong them ho so lang le. Da cap nhat khoa (amendment 23-49 cho
phep) VA lam no chat hon: `test_GC1a_new_profiles_are_derived_not_typed`
kiem ba ho so moi bang DUNG gia tri dan xuat, nen go tay mot gia tri khac
vao `AOI_PROFILES` van bi bat.

## 7. Con lai (Lesson 23.20)

```text
BUOC 5b  chay du 8 cell + ha nguon (conformal_v2, baselines, threshold_families,
         abstain_cost, phase23_cross_cell, eight_cell_sweep, live_region_sweep)
BUOC 5c  kiem cheo do gian M-125/M-126 -- LAM TRUOC khi tin ket luan nao
BUOC 6   bang CU vs MOI, doi chieu M-127..M-131
BUOC 7   L21 (amendment 23-50)
```

`M-125` lech ngoai `+/-25%` so voi do gian `z^0.431` => DUNG. Nghi pham dau
la `L35` (du hinh dang 8 ms chua ro co che), nghi pham hai la quen bu tru
`D_BASE`.
