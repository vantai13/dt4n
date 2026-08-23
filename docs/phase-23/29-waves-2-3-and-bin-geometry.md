# Lesson 23.20 Dot 2 + Dot 3, va phep kiem HINH HOC BIN

Ngay   : 2026-08-22
Prereg : `00zzh-amendment-49b.md`, `00zzj-amendment-49d.md`
Chay   : 30 build (Dot 1: 16, Dot 2: 8, Dot 3: 6) -- **13 phut**, 26 s/build

## 1. RUT chan doan "so mu thuc te < 0.431"

Bao cao Dot 1 muc 5 cua toi SAI DAU. Neu luat that la `r^beta` thi
`lech = r^(beta-0.431) - 1`, va moi `r > 1`, nen mot luat luy thua **khong
the doi dau**:

```text
bin      r        lech do duoc
B0    2.389     +0.82%     <- r LON NHAT, lech DUONG NHAT
B1    2.068     +0.19%
B2    1.737     -0.16%
B3    1.304     -0.67%     <- r NHO NHAT, lech AM NHAT

beta < 0.431 -> MOI o AM, AM NHAT o r lon nhat      (nguoc quan sat)
beta > 0.431 -> MOI o DUONG                          (nguoc quan sat)
=> KHONG so mu nao khop.
```

Cung ho loi voi "d lech phai" o amendment 23-48: mot tuong quan co ve hop
ly, nhung **dau va thu tu** khong duoc kiem.

## 2. Phep kiem HINH HOC BIN -- va no PHAN XU PARTIAL

Bin cu rong khong deu (`45/100/100/250 ms`), bin moi gan deu
(`141/125/125/150`). Nhung **ty so be rong cong tuyen voi ty so `z`**
(`corr = 0.88` tren 4 diem), nen tuong quan khong tach duoc hai gia thuyet.

Phep kiem tach duoc (`tools/check_bin_geometry.py`): bin lai **CA HAI truc
bang tu phan vi cua CHINH NO** -> ty so be rong `~1.00` o moi bin, trong khi
ty so `z` van bien thien.

```text
                  |lech| max   |lech| TB   corr(r, lech)   don dieu theo r
hinh hoc LECH        2.69%       0.97%        +0.9899           CO
hinh hoc KHOP        1.56%       0.69%        +0.5008          KHONG
```

```text
=> Phan CO HE THONG bien mat khi khop hinh hoc.
=> Nhung |lech| max chi tut 2.69% -> 1.56%, KHONG sup ve < 1%.
=> PHAN XU: PARTIAL -> L39
```

Gioi han cua phep kiem, phai ghi: khi khop hinh hoc, dai `r` hep lai
(`1.13-1.57` thay vi `1.30-2.39`) nen no it don bay hon de bat mot sai lech
so mu. Ket luan "phan he thong la hinh hoc bin" VUNG; ket luan "phan con lai
khong phai so mu" YEU hon.

## 3. Dot 3 -- ho so AoI co quan trong khong?

Gio moi hoi duoc, vi `M-132` (amendment 23-49a) da lam MOI ho so cung mot
muc tuoi. Kiem lai tren du lieu that:

```text
U0 366.023   U1 366.022   U2 366.022   U3 366.014 ms   (trai 0.009 ms)
```

`M-131` -- `q_hat(ho so) / q_hat(U0)` tren cung cell:

| cell | U0 | U1/U0 | U2/U0 | U3/U0 | dem? |
|---|---:|---:|---:|---:|:-:|
| h2@0.700 | 12.6195 | 0.9966 | 1.0003 | 0.9958 | CO |
| poisson@0.850 | 6.2157 | 1.0001 | 0.9985 | 0.9906 | CO |
| poisson@0.925 | 22.6037 | 0.9947 | 0.9988 | 0.9878 | CO |
| poisson@0.960 | 35.5819 | -- | -- | 0.9913 | CO |
| h2@0.850 | 32.7028 | -- | -- | 0.9999 | -- |
| h2@0.925 | 42.5189 | -- | -- | 1.0038 | -- |
| h2@0.960 | 47.0270 | -- | -- | 1.0003 | -- |
| poisson@0.700 | 0.4218 | -- | -- | 0.9979 | -- |

```text
M-131: U3/U0 = 0.9878 .. 0.9958 tren 4 cell dem duoc
       dai khoa 0.98 - 1.03   ->   HIT
```

### Ket luan cua Dot 3

```text
Khi MUC TUOI duoc giu bang nhau, HO SO AoI gan nhu KHONG anh huong q_hat:
    lech lon nhat 1.2% (U3 vs U0), phan lon duoi 0.5%.
Doi chieu: doi TRUC tuoi cho +8.90%.
=> Bien dieu khien la MUC tuoi trung binh, khong phai HINH DANG phan bo
   tuoi theo link.
=> Va do la LY DO amendment 23-49a muc 2 quan trong: truoc khi `d_base`
   thanh ham cua ho so, `U1` co mean z cao hon `U0` 22.5 ms, tuc "+1.67%
   qua do gian" -- lon hon TOAN BO hieu ung hinh dang. So U0/U1/U2 o
   Phase 22 vi the do CHU YEU muc tuoi, khong phai hinh dang. (L37)
```

## 4. Dot 2 -- mang nhan `CONDITIONAL_ON_SLA_AXIS`

Lesson 23.21 se doi `w_loss` (mot gia tri thay vi troi 1245->4722) va nguong
SLA (nguon NGOAI). `w_loss` vao thang ham chi phi, nen **moi `calib_set` phai
build lai**. Ba dot KHONG bi anh huong nhu nhau:

```text
Dot 1  GHEP CAP, cung SLA ca hai ve  -> SLA triet tieu   -> VAN DUNG
Dot 3  GHEP CAP, cung SLA moi ve     -> triet tieu       -> VAN DUNG
Dot 2  con so TUYET DOI (LS, err_neo, acceptance, c*)    -> BI THAY THE
```

```text
=> Dot 1 va Dot 3: ket qua CHINH THUC cua Lesson 23.20.
=> Dot 2: chay de doi chieu M-127..M-130 (du doan DA KY o amendment 23-44
   muc 5) va de dong P23-A, nhung mang nhan CONDITIONAL_ON_SLA_AXIS.
   Bang headline cuoi cung viet SAU Lesson 23.21.
```

## 5. Tang `PENDING/`

`SUPERSEDED` sai ngu nghia cho 22 artifact truc do duoc: khong co gi thay
the chung, chung **CHO** truc SLA duoc duyet.

```text
results/
├── RAW/  LIVE/  PENDING/  SUPERSEDED/  SMOKE/
                 ^^^^^^^^ moi
```

Moi artifact o `PENDING/` khai `validity.pending_on = ["aoi_axis","sla_axis"]`.
Va tang nay **TU DON**:

```text
test_pending_artifacts_declare_what_they_wait_for
  (1) o PENDING ma khong khai pending_on          -> FAIL
  (2) khai cho mot truc DA duoc duyet             -> FAIL, bat PROMOTE
```

Doi chung duong da chay: gia vo duyet `sla_axis` -> test DO voi thong bao
*"PROMOTE artifact nay len LIVE/"*; khoi phuc -> xanh.

## 6. Gate

| Gate | Noi dung | Trang thai |
|---|---|---|
| G23-127 | Dot 2 (8 job): bon cong nhanh PASS | PASS -- 8/8 |
| G23-128 | Dot 3 (6 job) + M-132 moi ho so cung mean z | PASS -- trai 0.009 ms |
| G23-131 | M-131 `q_hat(U3)/q_hat(U0)` trong 0.98-1.03 | PASS -- 0.9878..0.9958 |
| G23-135 | phep kiem hinh hoc bin, phan xu bang cong thuc | PASS -- PARTIAL |
| G23-136 | tang PENDING + `pending_on` + test tu don | PASS (co doi chung duong) |
