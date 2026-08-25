# 46 -- Lesson 23.22 Task B-3: tai hieu chuan qua che do, va menh de bao toan

Ngay      : 2026-08-25
Lesson    : 23.22 Task B-3
Amendment : `A068` (tien dang ky), tag `lesson-23-22-b3-prereg`
Artifact  : `results/LIVE/phase-23/recalibrate_transfer.json`
            `results/LIVE/phase-23/recalibrate_transfer_pilot.json`
Chay      : PILOT 12 cell (~11 phut) + nhanh R/D 3280 lan fit (40 phut 33 giay)

## 0. Cau hoi va cau tra loi

Task B do cai conformal **KHONG** hua: mang nguyen `qhat` sang che do khac.
`M-194` MISS, va `L97` cho thay do la he qua CAU TRUC. Task B-3 do cai no
**CO** hua: cho du lieu CO NHAN cua phan phoi moi, tra bao phu dung.

```text
Cau tra loi co BA ve:

  1. Tai hieu chuan KHOI PHUC HOAN TOAN bao dam bao phu. Tren 60 o co
     acceptance >= 0.20, so o co `viol > alpha` la **0 / 60**.
     Cai `kappa` sai lam mat KHONG PHAI tinh hop le -- ma la ACCEPTANCE.

  2. MENH DE BAO TOAN dung theo CA HAI chieu, va do duoc:
         C3-R  giu `viol`  (sd 0.0024)  de troi acceptance (sd 0.1101)  45.5x
         B2-R  giu acceptance (sd 0.0033) de troi `err`    (sd 0.0353)  10.8x

  3. GIA cua tai hieu chuan van la mot yeu cau CO MAU lon hon 4 lan:
     C3-R can 120 block de dat diem van hanh o >= 7/8 cell; B2-R can <= 30.
```

## 1. Bang cham -- 7/7 du doan HIT, 4/4 doi chung dat

| ma | gate | nguong da ky | do duoc | ket qua |
|---|---|---|---|---|
| `M-200` | G23-261 | max abs delta = 0.0 tren 8/8 | `0.000e+00` / `0.000e+00` | **HIT** (kiem wiring) |
| `M-201` | G23-262 | sd(viol) <= 0.020; sd(acc) trong [0.090, 0.180]; mean(viol) trong [0.05, 0.12] | 0.00242 / 0.11007 / 0.07413 | **HIT** |
| `M-202` | G23-263 | Spearman >= +0.90; do doc trong [0.40, 0.62] | +0.9674 / 0.4776 | **HIT** |
| `M-203` | G23-264 | >= 52/64 o | 60/64 | **HIT** |
| `M-204` | G23-265 | n\*(C3-R) trong [60,250]; n\*(B2-R) <= 60; ti so >= 2.0 | 120 / 30 / 4.00 | **HIT** |
| `M-205` | G23-266 | trung vi \|derr\| <= 0.02 | 0.00549 | **HIT** (ket qua AM) |
| `M-206` | G23-267 | sd(err B2-R) >= 0.020; sd(err C3-R) <= 0.025 | 0.03531 / 0.01500 | **HIT** |
| `NC-B3-1` | G23-268 | PHAI FIRE: 7/8 va 7/8 | 8/8 va 8/8 | **FIRED** |
| `NC-B3-2` | G23-269 | trung BIT theo truc A | 6/6 truong, `0.0e+00` | **HIT** |
| `NC-B3-3` | G23-269 | >= 3/4 cell chet sap ve anchor | 4/4 | **HIT** (xem muc 6.1) |
| `NC-B3-4` | G23-269 | ti le `qhat_source` sup > 0 | 96.1% | **HIT** |

⚠️ **Mot bang toan HIT la mot bang phai duoc doc nghi ngo.** Muc 6 chia bay
ma nay theo LUONG THONG TIN thuc su, va ha cap ba trong so do.

## 2. `M-200` -- kiem wiring, trung BIT   (`G23-261`)

C3-R voi `kappa` EP BANG 0.50 va `n` = 500 tai tao duong cheo
`transfer_matrix.json` tren ca 8 cell song, den chu so cuoi:

```text
cell             acceptance (B-3 / Task B)        viol|accept (B-3 / Task B)
h2@0.650         0.466408643638 / 0.466408643638  0.084702419517 / 0.084702419517
h2@0.675         0.519955092786 / 0.519955092786  0.078954660919 / 0.078954660919
h2@0.700         0.585945082720 / 0.585945082720  0.075920012295 / 0.075920012295
poisson@0.850    0.320306105500 / 0.320306105500  0.083364572400 / 0.083364572400
poisson@0.875    0.342195370394 / 0.342195370394  0.081353731710 / 0.081353731710
poisson@0.900    0.362091427405 / 0.362091427405  0.078917407260 / 0.078917407260
poisson@0.925    0.395461649760 / 0.395461649760  0.081721159247 / 0.081721159247
poisson@0.960    0.421989725774 / 0.421989725774  0.083052350534 / 0.083052350534

max |delta acceptance| = 0.000e+00      max |delta viol| = 0.000e+00
```

Chay TRUOC toan bo (`A068` buoc 7), cung voi `NC-B3-2` tren mot cell probe.
**Khi kiem wiring xanh tuyet doi, moi ket qua sau do chac chan la ve THE
GIOI, khong phai ve CODE.** Do la ca gia tri cua no; no KHONG mang mot bit
thong tin nao ve the gioi.

## 3. ★ Ket qua chinh: `kappa` sai lam mat ACCEPTANCE, khong lam mat TINH HOP LE

### 3.1. Cai gia duoc tra o dau

```text
Tai `n` = 500, tren 64 o:
                        acceptance          viol|accept
    duong cheo (8 o)    0.4155  sd 0.0025      0.0816
    ngoai (56 o)        0.4136  sd 0.1279      0.0805

Duong cheo bi GHIM vao `a*` theo dinh nghia (`kappa_B` duoc giai de dat
`a*` tren calib cua B). Toan bo do tan 0.1279 cua khoi ngoai duong cheo la
do `kappa` MANG SANG SAI -- khong phai do nhieu uoc luong.

Nhung `viol|accept` gan nhu KHONG DOI giua hai khoi: 0.0816 vs 0.0805.
```

### 3.2. Va cai gia do CO DAU, va DU DOAN DUOC   (`M-202`, `G23-263`)

```text
Tren 56 o ngoai duong cheo, `n` = 500:
    Spearman( |log(kappa_A/kappa_B)| , |acceptance_B - a*| )  = +0.9674
    do doc binh phuong toi thieu                              =  0.4776
    (tai `n` = 250: +0.9355 va 0.4906 -- bao cao kem, khong cham)

Neo cua do doc: -0.509, do tren CALIB cua chinh cell A trong PILOT
(`A068` S-6). Do duoc o day tren TEST cua cell B SAU khi `qhat` da duoc uoc
luong lai: 0.4776, lech -6.2%.
```

**Do doc cua `kappa` chuyen giao giua tach calib va tach test, va giua cac
cell.** Do la ve dinh luong that su rui ro cua `M-202` -- ve Spearman thi
gan nhu tat dinh sau khi S-6 duoc do (xem muc 6.2).

### 3.3. Bon o mat acceptance -- va chung la bon o nao

`M-203` cho 60/64. Bon o roi duoi san acceptance 0.20 la:

```text
    A -> B                            acceptance   viol   log(kappa_A/kappa_B)
    h2@0.700  -> poisson@0.850          0.1412    0.0655        +0.526   <- max
    h2@0.700  -> poisson@0.875          0.1621    0.0674        +0.479
    h2@0.700  -> poisson@0.900          0.1825    0.0681        +0.435
    h2@0.675  -> poisson@0.850          0.1940    0.0711        +0.420
```

Dung BON gia tri `log(kappa_A/kappa_B)` LON NHAT trong 56 o. `kappa_A` mang
sang QUA LON -> luat qua chat -> acceptance sup. Va `viol` cua chinh bon o do
(0.0655 .. 0.0711) van **duoi** `alpha` -- chung khong VO, chung LANG PHI.
Do la ly do `A068` muc 3.2 ky HAI nguong rieng chu khong mot dai hai phia
(`M-195`).

```text
Tren 60 o CON LAI (acceptance >= 0.20): so o co `viol > alpha` = 0 / 60.
=> `M-203` (60/64) va "so o tren san acceptance" (60/64) la CUNG MOT TAP.
   Rang buoc chat la ACCEPTANCE, khong phai bao phu.
```

## 4. ★ Menh de bao toan -- do duoc theo CA HAI chieu   (`M-201`, `M-206`)

```text
                    GIU                          DE TROI
    C3-R    viol|accept   sd 0.00242      acceptance   sd 0.11007     45.5x
    B2-R    acceptance    sd 0.00328      err|accept   sd 0.03531     10.8x

    (n = 250; C3-R tren 60 o tren san, B2-R tren 8 cell B)
    Neo toan-`n` cua Task B tai `kappa` co dinh: ti so 31.8x
```

Khong thu tuc nao giu duoc CA HAI. Do khong phai khuyet diem cua ben nao --
do la duong bien risk-coverage, nhin theo truc CHE DO VAN HANH.

### 4.1. `M-206` -- ve doi xung, va vi sao uoc luong tho cua no SAI 2.6 lan

`A068` muc 5.7 ky `sd(err B2-R) >= 0.020` kem mot canh bao rang tinh tho cho
~0.013, tuc **du doan nay rat co the MISS**. No HIT, va do duoc 0.03531.
Ly do tinh tho sai nam o dung mot gia thiet:

```text
GIA THIET (`A068` muc 5.7):  err|accept ~ err_neo x MOT HE SO gan nhu khong doi
DO DUOC:
    cell             err|acc / anchor           anchor
                     B2-R      C3-R
    h2@0.700         0.194     0.310            0.1545
    h2@0.675         0.226     0.284            0.1801
    h2@0.650         0.288     0.313            0.2055
    poisson@0.960    0.339     0.307            0.2161
    poisson@0.925    0.420     0.345            0.2388
    poisson@0.850    0.463     0.311            0.2535
    poisson@0.875    0.450     0.323            0.2570
    poisson@0.900    0.451     0.344            0.2524

    B2-R:  he so chay 0.194 -> 0.463   (2.39x)
    C3-R:  he so chay 0.284 -> 0.345   (1.22x)
    Spearman( anchor , he so cua B2-R ) = +0.9286
```

He so cua B2-R **khong** la hang so, va no bien thien **CUNG CHIEU** voi
`anchor`. Hai hieu ung NHAN nhau thay vi mot cai la hang so:

```text
uoc luong tho  = sd(anchor) x he so trung binh = 0.0378 x 0.355 = 0.0134
do duoc                                                          = 0.0353
```

> 🔑 Phat bieu manh hon `M-206` (va **POST-HOC**, khong dem diem):
> **C3-R giu `err|accept / anchor` gan nhu khong doi (0.284 .. 0.345, 1.22x)
> tren ca 8 che do; B2-R de no chay 2.39x, va chay theo chieu XAU -- che do
> cang kho thi risk TUONG DOI cua no cang te.** Day la mot menh de manh hon,
> nhung no den TU viec nhin so. Neu muon dung, phai ky lai va cham tren tap
> chua xem, dung nhu `M-197` da phai lam.

## 5. GIA phai tra, tinh bang `n`   (`M-204`, `G23-265`)

```text
    n      C3-R dat mucieu   med acc   med viol      B2-R dat   med acc
    30         4/8            0.2064    0.0036          8/8      0.3925
    60         6/8            0.2988    0.0395          8/8      0.4109
   120         8/8            0.3914    0.0645          8/8      0.4130
   250         8/8            0.4053    0.0733          8/8      0.4150
   500         8/8            0.4142    0.0814          8/8      0.4155

dieu kien C3-R: med_A(viol) <= 0.10 VA med_A(acceptance) >= 0.20
dieu kien B2-R: |acceptance - a*| <= 0.05

n*(C3-R) = 120     n*(B2-R) = 30 (SAN CUA LUOI)     ti so >= 4.00
```

Hai dieu phai doc dung:

```text
(a) n*(C3-R) = 120 TRUNG DUNG con so cua Task B-2 TRONG CUNG CELL (doc 45
    muc 3). Mang `kappa_A` tu mot che do khac KHONG lam tang yeu cau co mau.
    Toan bo cai gia cua `kappa` sai duoc tra bang ACCEPTANCE o mot vai o,
    khong bang `n`.

(b) n*(B2-R) = 30 la SAN CUA LUOI (`N_GRID` bat dau tu 30), nen ti so 4.00
    la mot CAN DUOI. Task B-2 do B2 dat trong 0.05 tu `n` = 20.
```

Cot `med viol` o `n` = 30 (0.0036) tai lap dung cai bay doc 45 muc 4.1:
`viol` thap o day khong phai vi thu tuc tot ma vi no gan nhu khong chap nhan
gi (acceptance 0.2064). San acceptance 0.20 -- ky truoc o `A068` muc 3.2 --
la thu chan cach doc do; no chinh la thu keo C3-R xuong 4/8 o `n` = 30.

## 6. Doc dung -- bay ma nay thuc su noi duoc gi

### 6.1. Ba ma bi HA CAP sau khi xem ket qua

```text
`M-200`   KHONG mang thong tin THEO THIET KE. Dap an nam san trong
          `taxonomy_audit.json`; no da duoc khai la KIEM WIRING o `A068`
          muc 0.1, dung tien le `M-193`.

`M-201`(a) `sd(viol) <= 0.020` do duoc 0.00242 -- HIT voi bien 8 lan, va
          THAP HON ca neo toan-`n` 0.00289. Dai da ky rong gap ~5 lan uoc
          luong tho (0.0041) vi "chua biet `kappa` lech bao nhieu". Sau
          PILOT thi da biet: `kappa_A` chi trai 1.69x. Dai le ra phai duoc
          siet cung luc voi `M-201`(b) va `M-202`. **HIT nay mang rat it
          bang chung.** Ghi lai thanh `L103`.
          (doi chung: sd KHONG gop draw = 0.00362, van << 0.020)

`NC-B3-3` nguong TUYET DOI 0.02 tren cell CHET, noi ca dai luong deu <= 0.0042:
              cell            err|acc C3-R   anchor    delta
              h2@0.850           0.00000     0.00417   0.00417
              poisson@0.700      0.00001     0.00346   0.00345
              h2@0.960           0.00000     0.00052   0.00052
              h2@0.925           0.00000     0.00024   0.00024
          Doi chung nay KHONG THE FAIL. 4/4 la mot phep dem, khong phai mot
          bang chung. Tieu chi dung phai la TUONG DOI. Ghi lai thanh `L101`.
```

### 6.2. Bon ma con lai mang thong tin -- va thong tin do la gi

```text
`M-201`(b) sd(acceptance) trong [0.090, 0.180] -> 0.11007.
          Dai HAI PHIA, va no duoc dat sau khi S-6 cho uoc luong 0.125.
          Do duoc lech -12% so voi uoc luong. MISS duoc o ca hai phia.

`M-202`(b) do doc trong [0.40, 0.62] -> 0.4776.
          Neo -0.509 do tren CALIB cua A; cau hoi that su la elasticity co
          chuyen giao sang TEST cua B sau khi `qhat` duoc uoc luong lai
          khong. Cau tra loi: CO, lech -6.2%.

`M-204`   n*(C3-R) = 120 = dung con so TRONG CUNG CELL cua Task B-2.
          Day la mot menh de am co noi dung: mang `kappa_A` KHONG lam tang
          yeu cau co mau.

`M-206`   Ve doi xung. Do la ma duy nhat ma chinh `A068` du bao se MISS
          (uoc luong tho 0.013 < nguong 0.020), va no HIT o 0.03531. Ly do
          uoc luong sai da truy duoc (muc 4.1) va la mot phat hien that.
```

### 6.3. `M-205` HIT, nhung trung vi GOP che mot xu the mot chieu

```text
Tai `n` = 250, khop acceptance, gop 640 lan chay:

    acceptance   err C3-R   err B2-R   trung vi |derr|
       0.70        0.1374     0.1392       0.00183
       0.50        0.0911     0.0970       0.00570
       0.30        0.0479     0.0596       0.01125
       0.15        0.0217     0.0321       0.00981

    trung vi tren CA BON muc = 0.00549   (nguong <= 0.02  -> HIT)
```

Trung vi gop HIT, va ket luan da ky ("dong gop KHONG nam o `err`") duoc giu.
**Nhung bang tren cho thay khoang cach TANG DON DIEU khi acceptance giam,
va C3-R tot hon o CA BON muc.** O acceptance 0.15 no la 0.0217 vs 0.0321 --
giam 32% tuong doi.

Day dung la hinh dang cua `NT 51` / `M-186` / `M-197`: **mot dai luong GOP
che mot hieu ung don ve MOT PHIA.** Lan nay no che theo truc MUC ACCEPTANCE.

```text
KHONG duoc ket luan "C3 tot hon o acceptance thap" tu bang nay: no la mot
quan sat POST-HOC tren bien ket qua da xem. No phai duoc ky lai va cham tren
tap chua xem. Ghi lai thanh `L102`.
```

## 7. `NC-B3-1` -- doi chung DUONG da FIRE, va no fire manh hon du kien

```text
    cell             acc B1-R   |acc - a*|   err B1-R   anchor   ti le
    h2@0.650          0.4277      0.0009      0.2054    0.2055   0.999
    h2@0.675          0.4277      0.0009      0.1812    0.1801   1.006
    h2@0.700          0.4277      0.0009      0.1553    0.1545   1.005
    poisson@0.850     0.4277      0.0009      0.2538    0.2535   1.001
    poisson@0.875     0.4277      0.0009      0.2573    0.2570   1.001
    poisson@0.900     0.4277      0.0009      0.2526    0.2524   1.001
    poisson@0.925     0.4277      0.0009      0.2389    0.2388   1.000
    poisson@0.960     0.4277      0.0009      0.2156    0.2161   0.998

    8/8 trung `a*`   VA   8/8 co `err|accept` >= 0.90 x anchor
```

**B1-R -- mot score NGAU NHIEN -- trung `a*` CHINH XAC HON B2-R** (0.0009 so
voi 0.0123), va `err|accept` cua no bang dung anchor: no khong loc duoc gi.

```text
=> "trung muc tieu acceptance" MOT MINH la mot thang do VO GIA TRI.
=> va do la ly do `A068` S-3 cam dung `|acceptance_B2R - a*|` lam thang cham
   diem. Neu da dung, B2 se "thang" mot cach TAM THUONG, va B1 se thang B2.
```

`L99` lan thu **TU** trong do an -- nhung lan nay doi chung duoc ky TRUOC va
FIRE dung nhu ky, thay vi duoc phat hien sau khi da ket luan.

## 8. `NC-B3-4` -- `L100` do lai o truc `n` moi   (`G23-269`)

```text
     n    lan chay   sup ve `none`   hai co `L91`/`L93`   fixed_point   cycle_max
    30       640        96.1%              3.9%              3.0%          0.9%
    60       640         0.9%             78.0%             49.2%         21.2%
   120       640         0.0%              6.2%             48.8%         44.7%
   250       640         0.0%              1.4%             52.0%         46.7%
   500        64         0.0%              0.0%             42.2%         57.8%
```

Cung hinh dang voi doc 45 muc 5 va tai lap tren mot luoi khac: o `n` = 30,
**96.1%** so lan chay la `none` doi ten, va he thong co cu chi bat duoc
**3.9%**. Truong `qhat_source` la co duy nhat con nhin thay o vung giao cua
`L93` va `L95`.

Census `n_accept = 0`: **0 / 3264** lan chay o moi muc `n`, ke ca `n` = 30 --
khac Task B-2, noi `n` = 10 va 20 nam DUOI san hop le 29 va `qhat = +inf`.
Chan dung so 4 cua `A068` muc 8 khong kich hoat (0.0% << 20%).

## 9. Ket luan Task B-3 -- bon cau

```text
1. Tai hieu chuan KHOI PHUC bao dam bao phu, hoan toan. Tren 60 o co
   acceptance >= 0.20, 0 o co `viol > alpha`. Cai `kappa` mang sai lam mat
   la ACCEPTANCE, khong phai TINH HOP LE.   (`M-203`, `G23-264`)

2. Cai gia do CO DAU va DU DOAN DUOC tu mot dai luong quan sat duoc:
   |acceptance - a*| ~ 0.478 x |log(kappa_A/kappa_B)|, Spearman +0.967.
   Doi ung cua `scale ratio` o Task B, nhung o day no do mot dai luong
   KHONG THU NGUYEN.   (`M-202`, `G23-263`)

3. MENH DE BAO TOAN dung theo ca hai chieu:
       C3-R giu `viol` (sd 0.0024) va de acceptance troi (sd 0.1101)
       B2-R giu acceptance (sd 0.0033) va de `err` troi (sd 0.0353)
   Khong ben nao giu ca hai. Do la duong bien, khong phai mot chien thang.
   (`M-201`, `M-206`, `G23-262`, `G23-267`)

4. Ve `err` tai acceptance KHOP, hai ben van gan nhu khong khac nhau:
   trung vi |derr| = 0.00549, so voi 0.00526 cua `M-196`. Dong gop cua C3
   KHONG nam o risk.   (`M-205`, `G23-266`)
```

> 🔑 Task B, B-2, B-3 cung tra loi mot cau, o ba chieu:
> **C3 khong mua duoc mot quyet dinh tot hon. No mua duoc mot PHAT BIEU ve
> quyet dinh do, kem mot thu tuc de lay lai phat bieu do o che do moi, kem
> mot yeu cau co mau do duoc.** B2 cho quyet dinh gan y het, khong phat
> bieu nao, va khong dai luong nao de biet khi nao no dang doan.

## 10. Cai con lai

```text
1. `a*` = 0.42679 la MOT lua chon thiet ke (`A068` N2). Do nhay theo `a*`
   chua do. San acceptance 0.20 cung vay (`N5`).

2. `kappa_A` duoc giai tren CALIB cua A voi `n` DAY DU (`N3`). Chi phi uoc
   luong chinh `kappa_A` tu `n` huu han chua do -- va no la buoc con thieu
   de phat bieu "chuyen giao" o dang tron ven.

3. `L92` van rang buoc: 8 cell song van co ho tai ghep hoan toan voi muc
   tai. Moi phat bieu o day la "qua CHE DO VAN HANH", KHONG phai "qua HO
   TAI".

4. Hai quan sat POST-HOC dang gia, chua duoc ky (`L101`, `L102`):
   (a) C3-R giu `err|accept / anchor` gan nhu khong doi (1.22x) trong khi
       B2-R de no chay 2.39x theo chieu xau  (muc 4.1)
   (b) khoang cach `err` giua C3-R va B2-R tang don dieu khi acceptance
       giam  (muc 6.3)
   Ca hai phai duoc ky lai va cham tren tap chua xem, dung nhu `M-197`.

5. `NC-B3-3` can mot tieu chi TUONG DOI, khong phai tuyet doi (`L101`).
   Doi chung am o cell chet, o dang hien tai, khong the fail.
```
