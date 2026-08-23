# AMENDMENT 23-49f -- Ba phat hien khi tich hop ha nguon

Ngay ky : 2026-08-22
Tag     : amendment-49f
Loai    : GHI NHAN quyet dinh ky thuat (sau khi gap loi, khong phai du doan)

## 1. `cell_matrices` co BAN SAO row-selection rieng

`cert/eight_cell_sweep.py` goi `cell_matrices()`, va ham do goi
`_valid_rows(n, DT)` **cua rieng no** (`cert/cell_matrices.py:177`) voi truc
MAC DINH. Khi `calib_set` chuyen sang truc do duoc, so hang lech:

```text
truc ke thua  999.945 hang     (d = 51 ms  -> bo ~11 buoc dau moi seed)
truc do duoc  999.495 hang     (d = 115.9 ms -> bo ~23 buoc dau)
-> AssertionError: truth/parquet length mismatch for poisson@0.925
```

**Loi ON AO, khong phai im lang** -- do la thiet ke tot cua ban goc. Nhung
no chi ra mot van de that: quy uoc "chon hang" song o HAI cho.

```text
SUA: `cell_matrices(..., axis=, aoi_profile=)` truyen xuong `_valid_rows`.
     `eight_cell_sweep` truyen tiep qua `analyze_cell` va `_objective_curve`.
     Mac dinh GIU NGUYEN truc ke thua -> doi chung am khong doi.
```

## 2. `NC-D` la doi chung CUA TRUC KE THUA

`eight_cell_sweep.run_eight_cells` ghim `delta_system_vs_neo` cua tam cell
(`LEGACY_DELTA`) va raise neu lech > 1e-12. Tren truc do duoc, cac gia tri
do **PHAI doi** -- do chinh la muc dich cua viec doi truc.

```text
=> NC-D khong ap dung cho truc khac. NHUNG KHONG TAT LANG LE:
   ghi `nc_d_status = {applies, max_absolute_gap, _note}` vao artifact,
   va van TINH gap de doi chieu duoc.
```

Doi chung am: chay `eight_cell_sweep` KHONG co co -> tai tao ban cu, moi gia
tri bit-exact (chi khac chuoi duong dan `results/phase-20R/...` ->
`results/LIVE/phase-20R/...`, he qua cua phan tang Lesson 23.17).

## 3. Dot 4 BI CHAN -- va chan dung cho

`live_region_sweep` can `h2@0.650`, `h2@0.675`, `poisson@0.875`,
`poisson@0.900`. Bon cell nay KHONG co trong `sla_calibration.json`
(chi co rho = 0.700/0.850/0.925/0.960).

Chung duoc tao boi chinh `live_region_sweep --prepare-sla`, va buoc do goi
`SLA.calibrate_cell(...)` -- **tuc chinh co che tu-hieu-chuan mang loi cau
truc S14**.

```text
=> Chay Dot 4 bay gio = chay lai co che S14 mot lan nua tren truc moi,
   tao ra mot artifact DOI DIEU KIEN (ca truc AoI lan truc SLA) va
   chac chan bi Lesson 23.21 vut bo.
=> QUYET DINH: Dot 4 HOAN den sau Lesson 23.21.
   M-125a giu 8 cell, M-125b giu 32 o. KHONG mo rong len 12/48 bay gio.
```

Day la mot vi du nua cua nguyen tac o amendment 23-49c: **sua mot truc khong
lam artifact sach**; o day no con manh hon -- viec MO RONG pham vi doi hoi
chay lai chinh co che dang bi loi.

```text
L41  `live_region_sweep` (va Dot 4) phu thuoc `--prepare-sla`, von goi
     `SLA.calibrate_cell` -- chinh co che S14. Khong the mo rong sang bon
     cell rho = 0.650/0.675/0.875/0.900 truoc Lesson 23.21.
```

## 4. Ket qua doi chieu `M-127..M-130`: 1/4 HIT -- bao cao NGUYEN

```text
ID      dai luong                        dai khoa          do duoc      KQ
M-127   err_neo poisson@0.925 moi/cu     +8% .. +14%       +5.5%       MISS
M-128   LS h2@0.700 doi dau thanh DUONG  CO                -0.000800   MISS
M-129   so cell co loi                   3                 3 -> 3      (*)
M-130   LS poisson@0.925 moi             +0.055..+0.085    +0.044154   MISS
```

`(*)` `M-129` ky tren tap NAM cell ("2/5 -> 3/5"); `eight_cell_sweep` co TAM
cell va cho `3 -> 3`. Con so `3` khop nhung TAP CELL KHAC -- **khong so sanh
truc tiep duoc**. Ghi la khong ket luan, khong tinh HIT.

### Vi sao ba MISS, va tat ca CUNG MOT HUONG

Ca ba deu lech theo huong **hieu ung NHO HON du doan**. Du doan o amendment
23-44 muc 5 duoc suy bang **noi suy tuyen tinh** tu
`dsync_sensitivity.json`:

```text
- artifact do mang `status: SENSITIVITY_ONLY`
- `limitation: does not measure AoI on topology_v7`
- dung `z_edges` CU (0.055..0.5501), khong phu dai z moi
- diem doi dau noi suy TUYEN TINH qua mot khoang 124 ms (51 -> 175 ms)
```

Dieu do da duoc ghi truoc thanh `L34` o amendment 23-47 muc 4:
*"la mot khoang cach AN TOAN, khong phai mot phep do chinh xac"*.

`M-128` minh hoa ro nhat: `LS(h2@0.700)` di tu `-0.017574` den `-0.000800`,
tuc **di duoc 95.4% quang duong ve 0** nhung KHONG doi dau. Noi suy tuyen
tinh cho diem doi dau o `98.3 ms`, con `d` do duoc la `115.9 ms` -- le ra da
vuot qua. Duong cong that KHONG tuyen tinh trong khoang do.

```text
=> Du doan CO CHE ve HUONG dung (moi cell di dung chieu du doan).
=> Du doan DO LON sai, va sai theo mot huong nhat quan.
=> Nguyen nhan da duoc ghi TRUOC (L34). Day khong phai mot bat ngo.
```

**KHONG dieu chinh dai khoa.** Chung da ky o amendment 23-44 muc 5; bao cao
nguyen, kem giai thich.

Chu ky: ____________
