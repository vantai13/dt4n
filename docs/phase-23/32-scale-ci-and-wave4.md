# Lesson 23.21b -- thang do, khoang tin cay, va Dot 4

Ngay    : 2026-08-23
Khoa boi: `00zzp-amendment-53.md` (tag `amendment-53`, commit `d2620fd`)
Artifact: `results/PENDING/phase-23/sla_exogenous_S-B_ci.json`,
          `results/PENDING/phase-23/t_loss_sweep.json`,
          `results/PENDING/phase-23/sla_exogenous_wave4.json`

## 1. Ket qua mot dong

```text
Sau khi them khoang tin cay, chi MOT cell trong luoi 8 cell goc song chac
chan. Nhung Dot 4 cho thay ly do la LUOI GOC LAY MAU SAI CHO, khong phai
mang khong co vung song: CA BON cell moi deu LIVE, va hai trong so do nam
NGOAI dai rho ma luoi goc phu.
```

## 2. Doi chieu du doan da ky

| id | dai da ky | do duoc | KQ |
|---|---|---|---|
| M-140 | `S_pivotal(poisson@0.875)` >= 0.30 | **0.81274** | **HIT** |
| M-141 | `S_piv(poisson@0.900)` < `S_piv(poisson@0.875)` | 0.32400 < 0.81274 | **HIT** |
| M-142 | dinh `S_pivotal(poisson, rho)` thuoc [0.850, 0.900] | dinh o `rho` = 0.850 | **HIT\*** |
| M-143 | `h2@0.700` CI95 CO chua 0.10 | [0.0956, 0.1269] | **HIT** |
| M-144 | so cell doi sang `AMBIGUOUS` = 1 (dai 1..3) | **1** (`h2@0.700`) | **HIT** |
| M-145 | ti so bien-pivotal >= 1 o >= 3/4 cell moi | **4/4** (1.055 .. 1.401) | **HIT** |
| M-146 | `n_LIVE` KHONG TANG tren nua chat cua quet | 2, 1, 2, 1 -- KHONG don dieu | **MISS** |

`M-142` mang dau `*`: dinh nam o **bien TRAI** cua dai da ky.

```text
poisson  rho    0.700   0.850   0.875   0.900   0.925
S_pivotal      0.0033  0.8932  0.8127  0.3240  0.0087
                        ^^^^^^ lon nhat, va la MUT TRAI cua dai [0.850, 0.900]
```

Dinh THAT co the nam DUOI 0.850, tuc NGOAI dai da ky. Luoi hien tai khong kep
duoc no. Day dung la lop loi da ghi o amendment 53 muc 8 (`suy duong cong tu it
diem`) -- lan nay no khong lam sai ket qua, nhung no lam ket qua KHONG KET LUAN
DUOC. Ghi `HIT*` chu khong ghi `HIT`.

## 3. `[1]` Khoang tin cay -- `h2@0.700` roi khoi `LIVE`

Block bootstrap, block = 1000 buoc = 5 s >> `tau` = 1 s, 200 block, 2000 draw:

```text
cell             regime       S_pivotal   CI95 (block)        w_blk    w_iid  ratio
cbr@0.700        TRIVIAL        0.00000   [0.0000, 0.0000]  0.00000  0.00000    --
cbr@0.850        TRIVIAL        0.00000   [0.0000, 0.0000]  0.00000  0.00000    --
poisson@0.700    TRIVIAL        0.00330   [0.0016, 0.0054]  0.00375  0.00050  7.45
poisson@0.850    LIVE           0.89321   [0.8799, 0.9060]  0.02605  0.00271  9.62
poisson@0.925    COLLAPSED      0.00869   [0.0051, 0.0128]  0.00774  0.00081  9.52
poisson@0.960    COLLAPSED      0.00000   [0.0000, 0.0000]  0.00000  0.00000    --
h2@0.700         AMBIGUOUS      0.11123   [0.0956, 0.1269]  0.03130  0.00276 11.36
h2@0.850         COLLAPSED      0.00000   [0.0000, 0.0000]  0.00000  0.00000    --
h2@0.925         COLLAPSED      0.00000   [0.0000, 0.0000]  0.00000  0.00000    --
h2@0.960         COLLAPSED      0.00000   [0.0000, 0.0000]  0.00000  0.00000    --

Tren luoi 8 cell GATE goc:  1 LIVE,  1 AMBIGUOUS,  1 TRIVIAL,  5 COLLAPSED.
```

`h2@0.700` co CI95 CHUA nguong 0.10 -> `AMBIGUOUS`. `PIVOTAL_MIN` KHONG doi.

### `G23-168` -- doi chung: tu tuong quan co that anh huong bao nhieu

```text
do rong CI block / do rong CI iid  =  7.45 .. 11.36 lan
n_eff suy nguoc tu CI block        =  1551 .. 3603
```

Doi chung PASS: bo qua tu tuong quan cho CI hep gia mot bac do lon.

Nhung con so nay **dinh chinh** amendment 53 muc 2. O do ta viet `n_eff = 500`
va "sai so thuc lon gap ~20 lan", suy tu cong thuc AR(1) cua `rho`:

```text
n_eff(cong thuc, tren rho)  =  n(1-phi)/(1+phi)  =  500
n_eff(do duoc, tren chi bao pivotal)             =  1551 .. 3603
```

Cong thuc AR(1) mo ta tu tuong quan cua CHUOI `rho`. Cai duoc lay trung binh la
CHI BAO `pivotal`, mot ham NGUONG cua `rho`. Ham nguong pha tu tuong quan: hai
buoc canh nhau co `rho` gan bang nhau van co the cho chi bao khac nhau khi
`rho` di qua nguong. Nen `n_eff` cua chi bao LON HON `n_eff` cua `rho` -- cong
thuc AR(1) la mot CAN DUOI bao thu, khong phai gia tri dung.

Ket luan `AMBIGUOUS` KHONG doi: CI do duoc `[0.0956, 0.1269]` van chua 0.10.
Ghi vao `L52`.

> Loi cai dat da bat duoc: ban dau doi chung iid lay `n/100` mau -- do la
> SUBSAMPLE chu khong phai iid bootstrap, va no cho CI **rong hon** block o
> hai cell, tuc doi chung chay NGUOC. Da sua sang dang tich phan
> `sd = sqrt(p(1-p)/n)`.

## 4. `[2]` Quet `T_loss` -- "sup" la tinh chat cua CAP (cell, SLA)

`T_delay` giu 50 ms (rang buoc TRO, `percentile_of_t_delay` = 100.00 o ca 10 cell).

```text
S_pivotal              T_loss = 0.001  0.002  0.005  0.010  0.020  0.050  0.100
poisson@0.700                  0.6592 0.3037 0.0416 0.0033 0.0002 0.0000 0.0000
poisson@0.850                  0.0603 0.2276 0.7259 0.8932 0.5435 0.0405 0.0000
poisson@0.925                  0.0000 0.0000 0.0000 0.0087 0.3996 0.3508 0.0000
poisson@0.960                  0.0000 0.0000 0.0000 0.0000 0.0000 0.9702 0.0000
h2@0.700                       0.0000 0.0001 0.0084 0.1112 0.6735 0.4831 0.0014
h2@0.850                       0.0000 0.0000 0.0000 0.0000 0.0000 0.0134 0.7481
h2@0.925                       0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000
h2@0.960                       0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000

n_LIVE                              1      2      1      2      3      3      1
n_COLLAPSED                         7      6      6      5      4      3      2
```

Ba dieu bang nay noi ma ba spec roi rac KHONG noi duoc:

```text
(1) MOI cell co dinh RIENG theo T_loss, va cac dinh TRUOT theo tai:
        poisson@0.700  dinh o 0.001
        poisson@0.850  dinh o 0.010
        poisson@0.925  dinh o 0.020
        poisson@0.960  dinh o 0.050
    Tai cang cao -> SLA phai cang LONG thi viec chon duong moi con quyet dinh.
    Day la mot SONG NUI cheo trong mat phang (rho, T_loss), khong phai mot vung.

(2) "COLLAPSED" KHONG phai tinh chat cua cell. `poisson@0.960` -- cell "chet"
    nhat duoi S-B -- dat S_pivotal = 0.9702 tai T_loss = 5%. Cell khong chet;
    CAP (cell, SLA) moi chet.

(3) `h2@0.850` chi song o T_loss = 10%; `h2@0.925`/`h2@0.960` khong song o BAT
    KY diem nao trong quet. Do la cell chet that trong dai da xet.
```

`M-146` **MISS**: `n_LIVE` KHONG don dieu theo `T_loss` (2, 1, 2, 1 tren nua
chat). Ly do doc duoc tu bang: `n_LIVE` la so cell co dinh RIENG dang di qua
gia tri `T_loss` do, nen no dao dong theo viec cac dinh co trung nhau khong.
Du doan "don dieu" gia thiet mot vung song DUY NHAT; thuc te la nhieu dinh
truot. Gia thiet sai, khong phai do do sai.

## 5. `[3]` Dot 4 -- luoi goc lay mau SAI CHO

```text
cell             regime   S_pivotal   CI95              ti so bien-pivotal
poisson@0.875    LIVE       0.81274   [0.7915, 0.8326]        1.055
poisson@0.900    LIVE       0.32400   [0.2980, 0.3498]        1.326
h2@0.650         LIVE       0.67240   [0.6454, 0.6991]        1.155
h2@0.675         LIVE       0.28678   [0.2625, 0.3106]        1.401
```

**CA BON deu LIVE**, khong cell nao cham nguong.

```text
Ho h2, theo rho tang:
    0.650  0.6724  LIVE
    0.675  0.2868  LIVE
    0.700  0.1112  AMBIGUOUS
    0.850  0.0000  COLLAPSED
```

`h2` co vung song o `rho <= 0.675`, va luoi 8 cell goc bat dau tu `rho = 0.700`
-- tuc no lay mau NGAY TAI MEP, va bo lo toan bo vung song cua ho `h2`. Dinh
cua `h2` nam DUOI 0.650, ngoai moi thu da do.

```text
DIEU CHINH KET LUAN CUA LESSON 23.21:
  "chi 1/8 cell song" la dung tren LUOI GOC, va sai neu doc thanh
  "mang chi co mot che do song". Do la mot phat bieu ve LUOI LAY MAU,
  khong phai ve MANG.
```

`M-145` HIT 4/4: ti so bien-pivotal / bien-trung-binh >= 1 o ca bon cell moi
(1.055, 1.326, 1.155, 1.401). Dung vao luc viec chon duong quyet dinh SLA, tin
hieu chi phi MANH HON binh thuong. Quan sat nay gio da duoc kiem tren du lieu
MOI, khong con la hau nghiem tren cung du lieu.

## 6. `G23-167` -- bang phan loai HAI CHIEU (luoi 8 cell goc)

```text
                     | err_neo < 0.05            | err_neo >= 0.05
---------------------+---------------------------+---------------------------
S_pivotal >= 0.10    |  (TRONG -- dung du kien)  |  SLA-PIVOTAL
                     |                           |    poisson@0.850
---------------------+---------------------------+---------------------------
CI chua nguong       |  --                       |  AMBIGUOUS
                     |                           |    h2@0.700
---------------------+---------------------------+---------------------------
S_pivotal <  0.10    |  ON DINH / TAM THUONG     |  HAN CHE THIET HAI
                     |    poisson@0.700          |    poisson@0.925
                     |    h2@0.850/0.925/0.960   |    poisson@0.960
---------------------+---------------------------+---------------------------
```

O goc tren-trai TRONG, dung nhu du kien o amendment 53 muc 4. Do la mot tien
doan kiem duoc: neu chon dung duong quyet dinh SLA thi twin cu PHAI sai du
nhieu de dang chung nhan. Khong cell nao vi pham no.

`HAN CHE THIET HAI` giu duoc `poisson@0.925` va `poisson@0.960` trong paper voi
mot ly do CO NGUYEN TAC: SLA da hong nen khong cuu duoc hop dong, nhung chon
dung duong VAN giam duoc ton that (`err_neo` = 0.2345 va 0.2151).

## 7. `M-135` -- nhac lai vi no la rui ro lon nhat

```text
bien: SLA 2-vs-6, err_neo 4-vs-4  ->  so trung chi nhan {2, 4, 6}
6/8 la TRAN co the dat
P(>= 6/8 | ngau nhien) = 0.2143      kappa = 0.5000      n = 8
```

Moi phat bieu ve `M-135` PHAI kem hai so tren (`G23-162`). Cau duy nhat duoc
phep viet: *"Hai phan hoach trung o muc tran co the dat, nhung voi n = 8 va
bien 2-vs-6, muc trung nay khong phan biet duoc voi ngau nhien."*

Sau khi `h2@0.700` doi sang `AMBIGUOUS`, bien SLA thanh 1-vs-7 va con so cang
mong hon. KHONG tinh lai `M-135` -- no da duoc ky va da duoc bao cao; viec tinh
lai sau khi doi phan loai la dung cai vong lap ma ca ky luat nay sinh ra de chan.

## 8. Han che moi

```text
  L52  Cong thuc `n_eff = n(1-phi)/(1+phi)` (amendment 53 muc 2) mo ta tu tuong
       quan cua CHUOI `rho`, khong phai cua CHI BAO `pivotal`. Do duoc:
       `n_eff` = 1551..3603 chu khong phai 500. Ham NGUONG pha tu tuong quan,
       nen cong thuc AR(1) la CAN DUOI bao thu. Ket luan `AMBIGUOUS` khong doi.
  L53  Dinh cua `S_pivotal(poisson, rho)` nam o MUT TRAI cua luoi ([0.850]);
       dinh cua ho `h2` nam DUOI 0.650, ngoai moi diem da do. Vi tri dinh
       CHUA duoc kep boi bat ky luoi nao hien co.
  L54  Ket luan "1/8 cell song" cua Lesson 23.21 la phat bieu ve LUOI LAY MAU
       (rho thuoc [0.700, 0.960]), KHONG phai ve mang. Dot 4 cho thay ho `h2`
       co vung song o `rho <= 0.675`, hoan toan ngoai luoi goc.
```

## 9. Chua lam

```text
- Kep dinh: can luoi rho MIN hon o [0.60, 0.90] cho poisson va [0.55, 0.70]
  cho h2. Chi phi ~1 s/cell tren `sla_exogenous`; KHONG can calib parquet.
- M-136 va doi chung muc duong ong: van bi chan boi `L51`.
- `G23-141`/`G23-142`: KHONG duoc tra boi ban nay (amendment 53 muc 0c).
- Duyet truc: `approved_for_live` van rong. Artifact o `PENDING/`.
```
