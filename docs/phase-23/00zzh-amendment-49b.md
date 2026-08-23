# AMENDMENT 23-49b -- Nguong dem cho M-125b, va ba quyet dinh duong dan

Ngay ky : 2026-08-22
Tag     : amendment-49b
Loai    : PREREGISTRATION (nguong) + quyet dinh ky thuat
Ky TRUOC: bat ky phep tinh M-125b nao ngoai PILOT mot cell da cong bo

## 0. DA XEM gi truoc khi ky

```text
DA XEM: err_neo CU cua 8 cell trong eight_cell_sweep.json (do tu Lesson 23.15,
        KHONG phai ket qua cua M-125b); pilot M-125b tren MOT cell
        (poisson@0.925, da cong bo o 27-mm125-pilot.md).
CHUA XEM: M-125b tren bat ky cell nao khac.
```

## 1. Nguong `err_neo >= 0.05` cho `M-125b`

Voi `err_neo -> 0`, `q_hat` duoc uoc luong tren rat it diem co tin hieu, nen
ty so `q_hat_moi / q_hat_cu` nhieu va khong tin duoc. Do tu artifact CU:

```text
cell               err_neo    nguong 0.05
h2@0.700          0.126536    GIU
h2@0.850          0.002944    LOAI (suy bien)
h2@0.925          0.000238    LOAI
h2@0.960          0.000524    LOAI
poisson@0.700     0.000000    LOAI
poisson@0.850     0.220727    GIU
poisson@0.925     0.222399    GIU
poisson@0.960     0.199493    GIU
                              GIU 4/8
```

```text
=> M-125b DEM tren 4 cell x 4 bin = 16 o.
=> Bon cell suy bien VAN duoc BAO CAO trong bang, nhung KHONG DEM,
   va co cot ghi ro "suy bien, khong dem".
```

Quyet dinh nay ky **TRUOC** khi tinh `M-125b` tren cac cell do. Neu de sau
khi thay bang moi loai, do la chon mau hau nghiem.

`G23-130` doi lai: `M-125b >= 90%` o trong `+/-25%` tren **16 o dem duoc**.

## 2. `cbr@0.700` va `poisson@0.900` khong nam trong `eight_cell_sweep`

Ban ke hoach liet ke `CELLS8` gom `cbr@0.700` va `poisson@0.900`, nhung
`eight_cell_sweep.json` phu `h2 x {0.700,0.850,0.925,0.960}` va
`poisson x {0.700,0.850,0.925,0.960}` -- khong co `cbr` va khong co `0.900`.

```text
=> Dot 1 chay tren DUNG 8 cell cua eight_cell_sweep, de Bang 3 doi chieu
   duoc voi ban CU. Them cell moi la mot cau hoi KHAC, khong thuoc 23.20.
```

## 3. Duong dan dau ra: theo TANG va mang DU DINH DANH

```text
OUT_PARQUET/OUT_REPORT hien tro `results/SUPERSEDED/phase-22/...` -- SAI TANG
cho artifact MOI. `test_no_stale_axes.py` CHI quet `results/LIVE/`, nen
artifact truc moi nam o SUPERSEDED se KHONG duoc canh -> cai chan cua
Lesson 23.17 vo hieu mot cach am tham.
```

```text
QUYET DINH
  tier   = LIVE khi axis == measured_v7, SUPERSEDED khi axis == legacy
  ten    = calib_set_<mode>_<rho>_<profile>_<axis>
           mang CA ho so VA truc -> chay U0 roi U3 KHONG ghi de nhau
  parquet trong LIVE/phase-21R KHONG commit (HANG 3, ~1.4 GB)
  report json THI commit -- no nho va mang khoi `validity`
```

Kiem: hien tai `.gitignore` dong 148 (`!results/**/phase-21R/**/*.parquet`)
lam parquet moi BI TRACK. 30 file x ~45 MB = **1.4 GB vao git**. Phai chan.

## 4. Ba dot, moi dot MOT cau hoi

```text
Dot 1  U0 @ legacy  vs  U0 @ measured      8 cell x 2 = 16 build
       "sua truc tuoi da lam gi" -- chi d va T doi, ho so giu nguyen U0
Dot 2  U3 @ measured                       8 cell x 1 =  8 build
       "he that cho ket qua gi" -- ho so DO DUOC (NT 44)
Dot 3  U1, U2 @ measured tren cell song    3 cell x 2 =  6 build
       "ho so AoI co quan trong khong" -- gio moi tach duoc HINH DANG
       khoi MUC nho amendment 23-49a muc 2
```

`U0 @ measured` la BIEN TRUNG GIAN: khong co no thi moi khac biet giua
`U0 @ legacy` va `U3 @ measured` deu mo ho giua "do truc" va "do ho so".

## 5. Pham vi cua ket qua pilot -- ghi de tranh doc sai

```text
- Do chinh xac +/-1.5% cua pilot la cua mot SO SANH GHEP CAP (paired):
  hai ve dung CUNG 5 seed, CUNG trace rho, CUNG truth table; chi truc z doi.
  Sai so lay mau tuong quan va TRIET TIEU phan lon trong ty so.
  KHONG duoc doc la "q_hat do duoc voi sai so 1.5%".
  Trong paper phai viet "paired comparison on identical load realisations".
- Ba trong bon bin la NOI SUY (z_tb moi 178/303/428 nam trong dai cu
  75..425). Chi B3 (553.4) la NGOAI SUY, vuot 30% ngoai dai da hieu chuan.
  Phat bieu dung: "dinh luat giu duoc khi ngoai suy 30%, kiem o MOT diem".
```

## 6. KHONG duoc lam

```text
- KHONG doi nguong err_neo sau khi thay bang M-125b.
- KHONG them cell ngoai 8 cell cua eight_cell_sweep vao Bang 3.
- KHONG commit parquet cua ma tran (HANG 3).
```

Chu ky: ____________
