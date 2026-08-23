# AMENDMENT 23-49e -- U1 == U2, can tren so mu, Dot 4, va `--calib-template`

Ngay ky : 2026-08-22
Tag     : amendment-49e
Loai    : GHI NHAN + can dinh luong + tien dang ky Dot 4

## 1. `U1` va `U2` cho `z_s` TRUNG KHIT -- so hoc, khong phai loi ghi

```text
ho so   mean(off)   d_base    d_base/dt   phan le
U0         0.000   115.900     23.1800     0.1800
U1        22.500    93.400     18.6800     0.6800   <-- cung phan le
U2        12.500   103.400     20.6800     0.6800   <-- cung phan le
U3         8.125   107.775     21.5550     0.5550
```

`mean(U1) - mean(U2) = 10 ms = DUNG 2 buoc dt`, nen `d_base` cung chenh dung
2 buoc -> cung phan le `0.6800` -> luoi lam tron trung khit; cong `mean(off)`
(chenh nguoc lai 2 buoc) thi `z_s` **bang nhau tuyet doi**.

Kiem: `max|z_s(U1) - z_s(U2)| = 0.000e+00`, `z_bin` giong hoan toan.

```text
=> KHONG phai copy-paste. Va no LAM MANH phep so:
   U1 va U2 co phan bo z Y HET NHAU, nen chenh lech q_hat giua chung la
   HIEU UNG HINH DANG THUAN KHIET -- khong con ca phan du 0.01 ms nhu khi
   so voi U0/U3. Day la cap so sanh SACH NHAT cho cau hoi "hinh dang ho so
   co quan trong khong".
```

## 2. Can tren dinh luong cho sai so so mu

Phep kiem hinh hoc bin (amendment 23-49d muc 2) ra `PARTIAL`; gioi han "it
don bay hon" duoc dinh luong:

```text
Neu phan du la sai so so mu:  lech = r^(delta_beta) - 1
r lon nhat cua phep kiem khop hinh hoc = 1.570,  ln r = 0.451
|lech| max quan sat = 0.0156
=>  |delta_beta| <= ln(1.0156)/ln(1.570) = 0.0344

=>  beta = 0.431 +/- 0.034   (tuong doi 8.0%)
```

Va no cho mot cong thuc dung duoc cho Lesson 23.28: ngoai suy `q_hat` qua ty
so `z` bang `R` co sai so do bat dinh so mu bi chan boi `R^0.034 - 1`:

```text
R = 2  ->  2.4%        R = 3  ->  3.9%        R = 5  ->  5.7%
```

Bo sung vao `L39`.

## 3. Dot 4 -- bon cell cua `live_region_sweep`

`live_region_sweep` can `h2@0.650`, `h2@0.675`, `poisson@0.875`,
`poisson@0.900` -- KHONG nam trong 8 cell da chay.

```text
Dot 4 = 4 cell x 3 bien the = 12 build (~3 phut)
    U3 @ measured                     -> headline (CONDITIONAL_ON_SLA_AXIS)
    U0 @ legacy va U0 @ measured      -> mo rong M-125a/b
```

```text
=> M-125a: 8 -> 12 cell
=> M-125b: 32 -> 48 o
Bon cell moi o rho = 0.650, 0.675, 0.875, 0.900 -- BA muc tai MOI, nen day
la kiem dinh luat o che do chua tung kiem.
```

Dai khoa cua `M-125a/b` GIU NGUYEN (`+5..+13%`, `+/-25%`). Nguong `err_neo
>= 0.05` cua amendment 23-49b van ap cho cell moi.

## 4. `--calib-template`: mot doi so, KHONG phai `--axis` cho tung script

Kiem CLI ca bay script ha nguon:

```text
conformal_v2        --calib --out                              KHONG can sua
baselines           --artifact --out-json --out-csv ...        KHONG can sua
threshold_families  --input --out-json --out-csv               KHONG can sua
phase23_cross_cell  --audit-json --baseline-json --out-*       KHONG can sua
abstain_cost        --cell --out-dir  + duong dan CUNG         SUA
eight_cell_sweep    --out             + 8 duong dan CUNG       SUA
live_region_sweep   --out --sla-out   + duong dan CUNG         SUA
```

Chi **3/7** can sua. Va **KHONG them `--axis`**: quy uoc duong dan
(`tang/phase/ten/ho so/truc`) phai song o MOT cho (runner), khong nhan ba
lan roi lech nhau.

```text
--calib-template  mac dinh = None  =>  DUNG NGUYEN duong dan cu, khong doi
                                       mot byte nao cua hanh vi mac dinh.
```

Mac dinh `None` (thay vi mot chuoi mau) la co y: no lam doi chung am ĐÚNG
THEO CAU TRUC -- chay khong co co thi ma nguon di dung nhanh cu.

Ly do khong dung mot chuoi mau lam mac dinh: ban do duong dan hien tai
KHONG deu -- `poisson@0.925` la `calib_set_v3.parquet` (khong hau to), con
lai la `calib_set_v3_<mode>_<rho>.parquet`. Mot mau se lam sai cell do, va
`abstain_cost.py:1122` da co san mot canh bao ve dung cai bay nay.

## 5. Ghi nhan: ban build cua toi tai lap ban phase-22

```text
poisson@0.925 : bit-exact tren ca 45 cot
h2@0.700      : 1-2 hang / 999.945 khac o s_pair_2/3, do lon 2-5e-10
                (epsilon cua float32); a_rank giong hoan toan
```

=> Duong ong nhat quan. Chenh lech o muc epsilon luu tru, khong phai co che.

## 6. KHONG duoc lam

```text
- KHONG doi dai khoa cua M-125a/b khi mo rong len 12 cell.
- KHONG doi dai khoa cua M-127..M-130: chung da ky o amendment 23-44 muc 5,
  doi chieu NHU LA, bao cao ca HIT lan MISS.
- KHONG doi mac dinh cua --calib-template thanh mot chuoi mau.
```

Chu ky: ____________
