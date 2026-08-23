# AMENDMENT 23-49 -- Tich hop truc tuoi do duoc vao build_calib_set_v3

Ngay ky : 2026-08-22
Tag     : amendment-49
Lesson  : 23.19 Task E (con lai) + 23.20
Loai    : QUYET DINH KIEN TRUC + CORRECTION + PREREGISTRATION

## 0. Va cham ma gate -- danh so lai TRUOC khi dung

Ban ke hoach danh so gate `G23-101 .. G23-114`. Nhung `G23-100 .. G23-108`
DA duoc cap (Lesson 23.19B va 23.19DE, xem `GATES.md`). Task E dung
**`G23-109` tro len**. Day la va cham ma thu NAM; `test_limits_ledger.py`
se duoc bo sung mot phep chan (muc 7).

## 1. QUYET DINH KIEN TRUC: alpha di duong offset san co (LUA CHON 1)

Hai lua chon neu o `25-zedges-and-task-e-controls.md` muc 4:

```text
LC1  tuoi co so SCALAR tu mo hinh + alpha qua AOI_PROFILES / off_steps
LC2  tuoi theo tung link ngay tu `_valid_rows`
```

**CHON LC1**, va khong phai vi tien: **LC2 BAT KHA**.

```text
`_valid_rows` tra ve `cur`/`old` dung de index ma tran rho cho CA 8 LINK
cung luc. MOT HANG cua calib set la MOT QUYET DINH, va quyet dinh can du
8 link tai CUNG mot thoi diem. Neu moi link co tap hang hop le rieng thi
khong dung duoc mot hang nao.
```

Va LC1 khop dung hinh dang mo hinh -- `build_calib_set_v3` DA tach san:

```text
age = sawtooth_age_steps(...)         SCALAR, chung 8 link   -> d + phase
off = offset_steps(profile, dt)       THEO LINK              -> alpha(link)
stale_rho: rho[old_idx[i] - off[l], l]
```

`z_bin` van gan tu tuoi SCALAR: bien dieu kien hoa cua Mondrian phai la
TUOI HE THONG, biet duoc tai thoi diem quyet dinh; `alpha` la nhieu loan
TRONG bin. Day la lua chon cua v2, giu nguyen de con so sanh duoc.

## 2. `U3` va bu tru `D_BASE`

`offset_steps()` (`build_calib_set_v3.py:163`) CAM offset am
(`raise ValueError("offset am khong hop le")`), ma `alpha` do duoc co 5/8
gia tri am. Nen `U3` phai DICH, roi lam tron len luoi `dt = 5 ms`:

```text
link  alpha      U3 danh dinh  steps  U3 THUC  luong tu hoa
uA    +12.111        20.801       4     20.0     -0.801
uB    +17.263        25.954       5     25.0     -0.954
ac     -8.690         0.000       0      0.0      0.000
ad     -8.541         0.149       0      0.0     -0.149
bc     -8.559         0.131       0      0.0     -0.131
bd     -6.721         1.970       0      0.0     -1.970   <- lon nhat
vC     -2.682         6.009       1      5.0     -1.009
vD     +5.819        14.510       3     15.0     +0.490
mean    0.000         8.690             8.125
```

BU TRU phai dung **TRUNG BINH THUC**, khong phai danh dinh:

```text
D_BASE = 115.9 - 8.125 = 107.775 ms          <- DUNG
neu lo dung 8.690  -> mean z lech -0.565 ms, KHONG AI THAY bang mat
```

Kiem: `mean z = D_BASE + mean(U3 thuc) + T/2 = 366.046 ms` (muc tieu 366.070;
lech 0.024 ms do lam tron `D_SYNC_S = 0.1159`).

`z_s` ghi ra parquet la **TUOI TRUNG BINH giua 8 link**:

```text
z_s = (cur - old) * dt + mean(off) * dt
```

Ly do: (a) la dai luong vat ly co nghia; (b) o `U0` thi `mean(off) = 0` nen
`z_s` KHONG doi -> giu bit-exact cho NC-E1; (c) khop `Z_EDGES_V7` von tinh
tren phan bo GOP 8 link.

## 3. CORRECTION: `U1` va `U2` KHONG bao toan trung binh

```text
ho so   mean (ms)   sd (ms)
U0          0.000     0.000
U1         22.500    14.841     <- dich mean TUOI +22.5 ms
U2         12.500    12.500     <- dich mean TUOI +12.5 ms
U3          8.125     9.662     <- duoc BU TRU qua D_BASE
```

```text
=> So U0/U1/U2 o Phase 22 la so DONG THOI hai thu: HINH DANG ho so VA MUC
   TRUNG BINH cua tuoi. Rieng U1 da doi mean z +22.5 ms -> qua do gian
   z^0.431 la q_hat +2.6%, KHONG lien quan gi den hinh dang.
=> Cham ca M-76 (Lesson 23.8): RMSE cua U1/U2 so voi alpha do duoc thua MOT
   PHAN vi do lech trung binh, boi alpha co mean = 0 theo dinh nghia.
```

KHONG rut so cu. Them hai ho so TRUNG TAM HOA de tach bach:

```text
U1c = trung tam hoa U1 roi dich len >= 0 va bu qua D_BASE  (cung co che U3)
U2c = tuong tu
```

Ket luan ve HINH DANG chi duoc dung `U0/U1c/U2c/U3`. Ket luan cu giu voi
nhan `CONFOUNDED_SHAPE_AND_LEVEL`.

## 4. Du doan -- dien TRUOC khi chay

```text
ID       Dai luong                                       Nguon       Dai khoa        KQ
---------------------------------------------------------------------------------------
M-121 *  mean(z_s) cua calib_set moi                     [CO CHE]    366.07 +/-0.10  __
M-122 *  ty trong 4 bin, lech thiet ke 25%               [CO CHE]    < 2 diem %      __
M-123 *  ty le hang ngoai dai Z_EDGES_V7                 [CO CHE]    = 0.000%        __
M-124    so block hieu dung nho nhat tren MOI cell/bin   [MO TA]     >= 9            __
M-125 *  q_hat moi / cu, trung binh 4 bin                [NGOAI SUY] +5% .. +13%     __
M-126 *  q_hat(B3)/q_hat(B0) khop do gian trong +/-25%   [CO CHE]    1.62 +/- 25%    __
M-127    err_neo moi / cu, poisson@0.925                 [NGOAI SUY] +8% .. +14%     __
M-128 *  LS h2@0.700 doi dau thanh DUONG                 [NGOAI SUY] CO              __
M-129 *  so cell co loi trong 5                          [NGOAI SUY] 3               __
M-130    LS poisson@0.925 (moi)                          [NGOAI SUY] +0.055..+0.085  __
M-131    q_hat(U3) / q_hat(U0) tren cung cell            [CO CHE]    0.98 .. 1.03    __
```

## 5. Doi chung bat buoc

```text
NC-E1 *  axis=legacy + U0 + d=0.051 + T=0.5 -> BIT-EXACT ban cu, diff = 0
         => NHANH FAIL CUNG. Khong bit-exact = da doi HAI thu. DUNG.
NC-E3    axis=measured + U0 -> mean(z_s) = D_BASE + T/2 (alpha = 0)
PC-E3 *  axis=measured + Z_EDGES_LEGACY -> B0 RONG, test n_g PHAI fail
PC-E4 *  D_BASE dung 8.690 thay 8.125 -> M-121 PHAI fail (lech 0.565 ms)
V-E1     phase0 CHUNG: corr(z_uA - alpha_uA, z_ac - alpha_ac) = 1.0 (dai so)
```

## 6. KHONG duoc lam

```text
- KHONG chinh Z_EDGES_V7 sau khi nhin s(z) hay q_hat.
- KHONG dieu chinh D_BASE de M-121 lot dai. D_BASE la HAM cua alpha va dt.
- Neu M-125 lech ngoai +/-25% so voi do gian: DUNG, tim nguyen nhan.
  Nghi pham dau: L35 (du hinh dang 8 ms chua ro co che).
  Nghi pham hai: quen bu tru D_BASE (PC-E4).
- KHONG noi NC-E1 thanh "gan bit-exact".
```

## 7. Chan va cham ma

Bo sung `test/test_limits_ledger.py::test_no_duplicate_limit_ids`: quet
`docs/phase-23/*.md`, RAISE neu mot ma `L*` xuat hien voi hai noi dung khac
nhau. Day la va cham thu NAM (`L29`, `G23-97..99`, `amendment-47`, `L21`,
`G23-101..108`); phai co mot cai chan.

Chu ky: ____________
