# AMENDMENT 23-49d -- Rut chan doan so mu, tang PENDING, va nhan cho Dot 2

Ngay ky : 2026-08-22
Tag     : amendment-49d
Loai    : CORRECTION + tang moi + tien dang ky nhan

## 1. RUT chan doan "so mu thuc te < 0.431"

Bao cao Dot 1 muc 5 viet: *"lech cua B3 AM tren ca 8 cell ... goi y so mu
thuc te nho hon 0.431"*. **Sai dau.**

Neu luat that la `ratio = r^beta` thi `lech = r^(beta-0.431) - 1`, va moi
ty so `r > 1`, nen:

```text
beta < 0.431  ->  MOI o AM,   va AM NHAT o r LON NHAT
beta > 0.431  ->  MOI o DUONG
beta = 0.431  ->  MOI o bang 0
```

Do duoc (trung binh 4 cell dem duoc):

```text
bin      r        lech
B0    2.389    +0.82%     <- r LON NHAT, lech DUONG NHAT
B1    2.068    +0.19%
B2    1.737    -0.16%
B3    1.304    -0.67%     <- r NHO NHAT, lech AM NHAT
```

```text
=> lech DOI DAU giua cac bin. Mot luat luy thua KHONG THE doi dau khi moi
   r > 1. Va thu tu NGUOC voi ca hai kha nang beta.
=> KHONG so mu nao khop. Chan doan cu bi RUT.
```

Cung mot ho loi voi "d lech phai" o amendment 23-48: mot tuong quan co ve
hop ly, nhung **dau va thu tu** khong duoc kiem.

## 2. Co che thay the: HINH HOC BIN -- va no chi giai thich MOT PHAN

Bin cu rong khong deu (`45/100/100/250 ms`), bin moi gan deu
(`141/125/125/150`). `q_hat` cua mot bin la phan vi tren mot HON HOP `z`
trong bin; bin rong hon tron nhieu `z` hon -> duoi tren cua score bi day len.

**Van de:** ty so BE RONG cong tuyen voi ty so `z` tren bon diem
(`corr = 0.88`), nen tuong quan khong tach duoc hai gia thuyet.

**Phep kiem tach duoc** (`tools/check_bin_geometry.py`): bin lai CA HAI truc
bang TU PHAN VI CUA CHINH NO -> hai ben cung hinh hoc (ty so be rong ~1.00),
trong khi ty so `z` van bien thien.

```text
                    |lech| max   |lech| TB   corr(r, lech)   don dieu theo r
hinh hoc LECH          2.69%       0.97%        +0.9899           CO
hinh hoc KHOP          1.56%       0.69%        +0.5008          KHONG
```

```text
=> Phan CO HE THONG bien mat khi khop hinh hoc (don dieu -> khong; 0.99 -> 0.50).
=> Nhung |lech| max chi tut 2.69% -> 1.56%, KHONG sup ve < 1%.
=> PHAN XU: PARTIAL. Hinh hoc bin giai thich phan CO HE THONG, con lai ~1%
   tan xa CHUA GIAI THICH.
```

Gioi han cua phep kiem, phai ghi: khi khop hinh hoc, dai `r` hep lai
(`1.13-1.57` thay vi `1.30-2.39`), nen phep kiem it don bay hon de phat hien
mot sai lech so mu. Ket luan "phan he thong la hinh hoc bin" vung; ket luan
"phan con lai khong phai so mu" thi YEU hon.

```text
L39  Phan du cua M-125b: phan CO HE THONG do HINH HOC BIN (bin cu rong khong
     deu 45/100/100/250 vs bin moi ~125-150). Khop hinh hoc lam corr(r,lech)
     tut 0.99 -> 0.50 va mat tinh don dieu. Con ~1% tan xa CHUA GIAI THICH
     (nghi pham L35). Khi transfer giua cac bin CUNG hinh hoc, hieu ung nay
     triet tieu -> dinh luat chinh xac hon con so 2.6% bao cao o M-125b.
     Dau vao truc tiep cho Lesson 23.28.
```

## 3. Cell suy bien VAN khop -- mot phat bieu manh hon

`poisson@0.700` co `err_neo = 0.000000` (khong co tin hieu quyet dinh nao)
ma `q_hat` van tuan dinh luat trong `4.5%`. Ba cell suy bien con lai cung vay.

```text
=> Dinh luat z^0.431 mo ta CAU TRUC CUA PHAN PHOI SCORE THEO TUOI,
   khong phai mot tinh chat cua BAI TOAN QUYET DINH.
=> Lesson 23.28 (transfer giua bin tuoi) kha thi CA O CHE DO ma chung nhan
   khong co loi.
```

Chung van KHONG DEM cho `M-125b` (nguong `err_neo >= 0.05` ky o 23-49b);
day la mot quan sat BO SUNG, khong doi cach dem.

## 4. Tang `PENDING/` -- vi `SUPERSEDED` sai ngu nghia

```text
SUPERSEDED = "da bi mot ban MOI HON thay the"      -> phat bieu ve LICH SU
16 calib_set cua Dot 1 = "hien hanh, nhung dieu kien tren mot truc chua duyet"
                                                    -> phat bieu ve HIEU LUC
```

Khong co gi thay the chung. Tron chung vao `SUPERSEDED` se phai DI SAN khi
Lesson 23.21 xong va can promote.

```text
results/
├── RAW/          du lieu do tho
├── LIVE/         MOI truc DA DUYET
├── PENDING/      hien hanh, CHO mot truc duoc duyet     <- MOI
├── SUPERSEDED/   da bi thay the
└── SMOKE/        pilot / attempt
```

Moi artifact o `PENDING/` phai khai `validity.pending_on` liet ke chinh xac
truc nao chua duyet. Va mot test lam no **tu don**:

```text
test_pending_artifacts_declare_what_they_wait_for
    - o PENDING ma khong khai `pending_on`            -> FAIL
    - khai cho mot truc DA duoc duyet                 -> FAIL (bat phai promote)
```

Test thu hai la diem chinh: khi Lesson 23.21 duyet truc SLA, test do THANH
DO va bat phai promote, thay vi de artifact nam quen o day.

## 5. Nhan cho ba dot -- Lesson 23.21 se doi `w_loss`

Lesson 23.21 sua `S14`: `w_loss` thanh mot gia tri (thay vi troi 1245->4722)
va nguong SLA lay tu nguon NGOAI. `w_loss` vao thang ham chi phi, nen **moi
`calib_set` phai build lai**. Nhung ba dot KHONG bi anh huong nhu nhau:

```text
Dot 1  U0@legacy vs U0@measured -- GHEP CAP, cung SLA ca hai ve
       -> SLA triet tieu trong ty so. M-125a/b VAN DUNG sau 23.21.
Dot 3  U0/U1/U2/U3 @ measured   -- GHEP CAP, cung SLA moi ve
       -> ket luan ve HINH DANG ho so VAN DUNG.
Dot 2  U3 @ measured -- con so TUYET DOI (LS, err_neo, acceptance, c*)
       -> phu thuoc truc tiep w_loss va nguong SLA. BI THAY THE boi 23.21.
```

```text
QUYET DINH
  Dot 1, Dot 3 -> ket qua CHINH THUC cua Lesson 23.20
  Dot 2        -> chay de doi chieu M-127..M-130 (du doan DA KY o amendment
                  23-44 muc 5) va de dong P23-A, nhung mang nhan
                  CONDITIONAL_ON_SLA_AXIS. Bang headline cuoi cung viet SAU
                  Lesson 23.21.
  KHONG bo Dot 2: du doan da ky thi phai doi chieu, du con so se duoc thay.
  O 26 s/build, chay lai 8 build sau 23.21 ton 4 phut.
```

## 6. KHONG duoc lam

```text
- KHONG chinh so mu 0.431 de che phan du. No khoa o Phase 22.
- KHONG go nhan CONDITIONAL_ON_DSYNC_51MS o Dot 2: dieu kien go (amendment
  23-44 muc 7) doi CA truc SLA, dung logic cua chinh amendment 23-49c.
- KHONG dem cell suy bien vao M-125b du chung khop.
```

Chu ky: ____________
