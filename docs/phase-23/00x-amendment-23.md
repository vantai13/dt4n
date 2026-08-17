# AMENDMENT 23-23 -- Luoi kappa mit trong cua so, va mot ban ghi ve viec do qua tay

Ngay: 2026-08-17
Commit: sau Amendment 23-22 (`4c9cbe3`), TRUOC khi chay Lesson 23.5[B].

---

## 1. Phat hien 8 -- cua so [0.6, 1.0] chi tua tren BA nut

Amendment 23-22 khoa luoi chung 4001 diem (B-D2) de sua loi so lech luoi. Kiem
tra tiep cho thay luoi chung sua duoc **so lech**, nhung khong them duoc
**thong tin**: `np.interp` noi suy tuyen tinh giua cac NUT, va so nut that su
chi phoi cua so la ba.

Do duoc tren `poisson@0.925`, luoi `KAPPA_GRID` goc:

```text
C0:  nut ngay duoi 0.60 :  kappa=0.5   acc=0.5855  err=0.10337
     nut TRONG cua so   :  kappa=0.25  acc=0.7878  err=0.15986
                           kappa=0.0   acc=1.0000  err=0.22240
     -> 3 nut hieu dung; be rong doan: 0.2023  0.2122

C3:  nut ngay duoi 0.60 :  kappa=0.5   acc=0.4911  err=0.08086
     nut TRONG cua so   :  kappa=0.25  acc=0.7380  err=0.14565
                           kappa=0.0   acc=1.0000  err=0.22240
     -> 3 nut hieu dung; be rong doan: 0.2468  0.2620
```

**Chi `kappa in {0, 0.25, 0.5}` -- ba trong muoi hai gia tri -- co anh huong
toi GO-1.** Chin gia tri con lai (`0.75 .. 8.0`) deu cho acceptance duoi 0.60.

### 1.1. Vi sao day la van de chu khong chi la mot quan sat

```text
(a) Luoi 4001 diem la AO GIAC ve do phan giai. Thong tin van la 3 nut.

(b) Duong LOI, hinh thang uoc luong THUA. Sai so mot doan ~ (h^3/12)*|R''|.
      C0 doan cuoi h = 0.2122      C3 doan cuoi h = 0.2620
      ti le h^3: (0.2620/0.2122)^3 = 1.88
    => C3 chiu sai so hinh thang lon gan GAP DOI C0.
    Ma ti so dang do lech khoi 1 chi 0.25%. Sai so roi rac hoa CUNG BAC DO LON
    voi dai luong can do.

(c) He qua cho GO-1: CI tu bootstrap phan anh nhieu LAY MAU nhung KHONG phan
    anh sai so ROI RAC HOA. CI se HEP GIA TAO, va co the dan toi ket luan
    "bat bien" dua tren mot artifact.
```

Day dung la co che Amendment 23-11 da dat ten (`grid-density inflation`); o do
no chiem 52% hieu AURC.

---

## 2. Quyet dinh khoa B-D12 .. B-D14

```text
B-D12  THEM luoi kappa mit TRONG cua so, GIU luoi goc lam kiem tra tai lap.

   KAPPA_PRIMARY = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0)
       -> tai lap A-1'..A-4' dung con so da ghi o Amendment 23-22. KHONG DOI.

   KAPPA_REFINED = KAPPA_PRIMARY | {0.05, 0.10, 0.15, 0.20, 0.30, 0.35, 0.40,
                                    0.45, 0.55}
       -> 21 gia tri kappa.

   BAO CAO CA HAI. Hieu giua chung LA uoc luong cua sai so roi rac hoa:
       discretisation_bias = ratio(KAPPA_REFINED) - ratio(KAPPA_PRIMARY)

B-D13  Ket luan GO-1 dung KAPPA_REFINED.
       Ly do: KAPPA_PRIMARY da duoc chung minh chi co 3 nut trong cua so, va
       sai so hinh thang KHONG doi xung giua C0 va C3.
       KAPPA_PRIMARY giu vai tro KIEM TRA TAI LAP, khong phai nguon ket luan.

B-D14  Kiem tra day du cua luoi mit, PHAI dat truoc khi doc ket qua:
       n_knots_in_window >= 6 va widest_segment_in_window < 0.15 o CA HAI
       cau hinh. Neu khong dat -> luoi mit la trang tri, phai them kappa.
```

### 2.1. Luoi mit da duoc kiem tra la DU (kiem tra thiet ke, khong phai ket qua)

```text
                 knots_in_window        widest_segment_in_window
grid        C0          C3           C0            C3
primary      2           2          0.2122        0.2620
refined     10           8          0.0435        0.0555
```

Dat `B-D14` o ca hai cau hinh. Buoc kiem tra nay BAT BUOC phai chay truoc khi
khoa `B-D12`: khong the khoa mot luoi ma chua biet no co lam duoc viec khong.

---

## 3. BAN GHI LOI PHUONG PHAP -- toi do qua tay, A-7'/A-8' mat tu cach confirmatory

### 3.1. Chuyen gi da xay ra

Thiet ke ban dau (ghi chep truoc) dat hai du doan:

```text
A-7'  |discretisation_bias| lon nhat trong 3 cell   [CO CHE]  0.001 - 0.010
A-8'  Dau cua discretisation_bias                   [CO CHE]  AM
      (vi C3 chiu sai so thua lon hon => lam mit se HA ratio)
```

De khoa `B-D12` toi phai kiem tra luoi mit co that su lam mit khong. Viec do
**chi can** `n_knots_in_window` va `widest_segment_in_window`. Nhung toi da
tinh luon ca AURC va ti so tren luoi mit, nen thay ngay:

```text
ratio(primary) = 1.002492      ratio(refined) = 1.000480
discretisation_bias = -0.002012        |bias| = 0.002012
```

`|bias|` nam trong dai `0.001 - 0.010`, dau AM. Ca hai du doan deu "trung" --
**nhung toi da nhin so truoc khi ky.**

### 3.2. Xu ly

```text
A-7' va A-8' ha nhan tu [CO CHE] xuong [MO TA].
KHONG tinh prediction-hit. Giu trong bang lam kiem tra tai lap.
```

Xu ly y het `S-5` (Amendment 23-21 muc 3) va `A-1'..A-4'` (Amendment 23-22
muc 3.1): **da nhin so thi khong duoc tinh diem**, bat ke so do co trung hay
khong. Viec no trung khong lam giam muc do nghiem trong -- neu duoc phep ghi
diem cho du doan da nhin ket qua thi bang pre-registration mat toan bo gia tri.

### 3.3. Bai hoc rieng cua lan nay

```text
CO MOT LOAI DU DOAN KHONG THE PRE-REGISTER: du doan ve HE QUA cua mot quyet
dinh thiet ke ma ban phai KIEM CHUNG truoc khi khoa.

Muon giu A-7'/A-8' la confirmatory, buoc kiem tra thiet ke phai duoc GIOI HAN
nghiem ngat vao cac dai luong KHONG dinh toi ket qua:
   duoc do : n_knots_in_window, widest_segment_in_window, so kappa roi vao
             cua so
   CAM do  : aurc, ratio, discretisation_bias
Toi da khong dat ranh gioi do truoc khi chay, nen mat.

Ghi vao so nhu mot mau lam viec: TRUOC khi chay bat ky doan kiem tra thiet ke
nao, viet ra danh sach dai luong duoc phep nhin. Danh sach do la mot phan cua
pre-registration.
```

### 3.4. Cai gi CON LAI la confirmatory

```text
A-5'  CI95_high lon nhat trong 3 cell           [NGOAI SUY]  1.01 - 1.06
A-6'  Duoc dua "frontier invariance" vao abstract?  [CO CHE]  xem A-5'
```

Chua co bootstrap nao duoc chay. `A-5'` va `A-6'` van nguyen ven, va chung la
**noi dung confirmatory duy nhat** cua Lesson 23.5[B] (Amendment 23-22 muc 3.2
da bao truoc dieu nay). Ranh gioi bay gio ro rang:

```text
DA NHIN (khong tinh diem):  A-1' A-2' A-3' A-4' A-7' A-8'
CHUA NHIN (tinh diem)    :  A-5' A-6'
```

---

## 4. Bang du doan cap nhat

| ID | Dai luong | Nhan | Dai khoa | Trang thai |
|---|---|---|---:|---|
| A-1' | ratio AURC[0.6,1] C3/C0, poisson@0.925 | [MO TA] | 1.000-1.006 | da nhin |
| A-2' | ratio AURC[0.6,1] C3/C0, poisson@0.850 | [MO TA] | 1.002-1.011 | da nhin |
| A-3' | ratio AURC[0.6,1] C3/C0, h2@0.700 | [MO TA] | 1.007-1.018 | da nhin |
| A-4' | So cell suy bien trong 5 | [MO TA] | dung 2 | da nhin |
| A-5' | **CI95_high lon nhat trong 3 cell** | [NGOAI SUY] | 1.01-1.06 | **chua nhin** |
| A-6' | Dua "frontier invariance" vao abstract? | [CO CHE] | `A-5' < 1.02` | **chua nhin** |
| A-7' | \|discretisation_bias\| lon nhat | [MO TA] | 0.001-0.010 | da nhin |
| A-8' | Dau cua discretisation_bias | [MO TA] | AM | da nhin |

---

## 5. Doi chung tu than bat buoc (NT-v2-2)

```text
NC-A-1  DOI CHUNG AM: bootstrap C0 vs CHINH C0, cung draw.
        Moi draw phai cho ratio = 1.0 CHINH XAC -> CI = [1, 1], do rong 0.
        Do rong > 0 <=> ghep cap bi hong (draw khong thuc su dung chung).
        Bat duoc loi "quen dung chung picks" -- loi im lang lam CI phong
        ~sqrt(2) va co the lat ket luan GO-1.

PC-A-1  DOI CHUNG DUONG: nhan err|accept cua C3 len 1.10, giu nguyen C0.
        CI95 PHAI loai tru GO1_THRESHOLD va bao quanh ~1.10.
        Khong loai tru => B chua du hoac CI tinh sai.

MC      Hoi tu Monte Carlo: chay B in {200, 500, 1000, 2000}; do rong CI phai
        co theo 1/sqrt(B) trong +/-25%. Khong co => bootstrap sai cau truc
        (nhieu kha nang resample theo HANG chu khong theo BLOCK).
```

Thu tu doc ket qua BAT BUOC: `NC-A-1` -> `corr_num_den` -> `PC-A-1` -> `MC` ->
`n_knots` -> `ratio` -> `discretisation_bias` -> `ci95_high` -> `GO-1`.
Bon muc dau la CONG: fail bat ky muc nao thi `ci95_high` khong co nghia.

---

## 6. Pham vi duoc phep chay

```text
* them cert/aurc_go1.py va test/test_phase23_aurc_go1.py
* sinh results/phase-23/aurc_go1_<cell>.json cho CA 5 cell
  (GO-1 noi "moi cell", nen cell suy bien cung phai co artifact ghi
   trang thai DEGENERATE, khong duoc bo im lang)
* them docs/phase-23/09-aurc-and-go1.md
```

Khong duoc sua `cert/config_matrix.py`. `cert/aurc_go1.py` PHAI import
`_accept`, `_q_rows`, `_score_cols`, `_mhat_cols`, `fit_config` tu
`config_matrix` chu khong viet lai: neu viet lai, luat accept trong bootstrap
co the troi khoi luat accept trong uoc luong diem ma khong ai phat hien.
