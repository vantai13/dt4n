# 44 -- Lesson 23.22 Task B: ma tran chuyen giao C3 vs B2

Ngay      : 2026-08-25
Lesson    : 23.22 Task B
Amendment : `A066-amendment-66.md` (tien dang ky), `A066b-amendment-66b.md`
            (sua `NC-3` TRUOC khi chay)
Artifact  : `results/LIVE/phase-23/transfer_matrix.json`
Chay      : 8x8 = 64 o + 4x4 doi chung am + `NC-3`, 1 phut 41 giay

## 0. Mot cau truoc khi doc bang

**Du doan chinh cua Task B bi bac bo, va doi chung duong cua no FIRE.** Ca hai
deu la ket qua that, va cai thu hai quan trong hon cai thu nhat.

## 1. Bang cham -- theo dai DA KY, khong noi mot dai nao

```text
ID       dai da ky                        do duoc                        hit
-----------------------------------------------------------------------------
M-193    C3 tai tao artifact <= 1e-9      0.000e+00  (8/8, TRUNG BIT)     ok
         B2 lech acceptance <= 0.02       0.02061    (h2@0.650)           MISS
M-194    trung vi drift B2 >= 3x C3       1.04x                           MISS ***
M-195    T3 trong dung sai >= 20/30       6/30                            MISS
M-196    trung vi |derr| <= 0.02          0.00526    (120 diem)           HIT
M-190    p->h2 troi hon h2->p             0.2352 > 0.1803                 HIT
NC-1     cell chet: ca hai <= 0.05        0.0276 / 0.0277                 HIT
NC-2     drift B1 >= drift B2             1.19e-05 vs 0.2174              MISS ***
NC-3a    C3 trung bit khi hieu chuan lai  lech = 0.0 chinh xac            HIT
NC-3b    ca hai troi > 0.05               0.2510 / 0.2553                 HIT
```

```text
G23-248  FAIL   M-193 (nhanh C3 trung bit; nhanh B2 truot 0.0006)
G23-249  FAIL   M-194  ***
G23-250  FAIL   M-195
G23-251  PASS   M-196
G23-252  PASS   M-190
G23-253  PASS   NC-1
G23-254  FAIL   NC-2   ***
G23-255  PASS   NC-3a
G23-256  PASS   NC-3b
```

## 2. `NC-2` -- ket qua quan trong nhat, va no la mot ket qua ve PHEP DO

```text
trung vi T1_drift tren 30 o GIUA HO:

    B1  (score NGAU NHIEN)      1.19e-05      <- it troi nhat
    C3  (conformal)             0.2090
    B2  (nguong tuyet doi)      0.2174
```

Mot score ngau nhien -- khong mang mot bit thong tin nao ve `a_twin = a*` --
**troi it hon bon van lan** so voi ca hai phuong phap that. Ly do tam thuong
khi da thay: `score_B1_random` la Uniform(0,1) o MOI cell, nen mot nguong dat
tren A cho dung ti le chap nhan do tren B. Phan phoi cua no BAT BIEN theo che
do vi no khong lien quan gi den che do.

```text
=> "acceptance drift thap" KHONG phai mot duc tinh.
   No la duc tinh cua mot luat KHONG NHIN vao du lieu.
```

`A066` muc 5 ky truoc: *"Neu B1 ~ C3 thi thang T1 khong phan biet duoc gi va
phai thiet ke lai."* Dieu kien do da xay ra, va manh hon du kien -- B1 khong
"~ C3", no TOT HON HAN C3 tren thang T1.

> 🔑 `T1` do do ON DINH cua ti le chap nhan, khong do do TOT cua phep chon.
> Mot thang nhu vay bi TOI DA HOA boi viec khong lam gi ca. No khong duoc lam
> thang chinh cua bat ky so sanh nao ve chat luong.

Day la ly do phai co doi chung duong. Neu chi cham `M-194`, ta se ket luan
"C3 va B2 ngang nhau ve chuyen giao" va khong bao gio biet rang thang do dung
de ket luan dieu do xep hang mot mau nhieu len tren ca hai.

## 3. `M-194` -- du doan chinh BI BAC BO, va khong phai sat bien

```text
T1 drift tren 30 o giua ho:

           min      q1      trung vi     q3      max
    C3   0.0047  0.1293    0.2090     0.3324  0.5186
    B2   0.0054  0.1292    0.2174     0.3398  0.5291
```

Hai phan phoi gan nhu chong khit. Ti so trung vi 1.04x so voi nguong da ky
>= 3x. Day khong phai mot phep thu thieu luc: neu hieu ung ton tai o co 3x,
30 o da du de thay.

`A066b` muc 3 da ky TRUOC khi chay rang khoi chinh cham C3 o che do "mang
nguyen `qhat_A` sang B", tuc `NC-3b`, va o che do do **ca hai tham so mang di
deu co thu nguyen**. Ket qua khop chinh xac voi phan tich do. Nhan
`[NGOAI SUY]` cua `M-194` (`A066` muc 4) la dung: no khong bao gio la mot he
qua cua co che.

## 4. `NC-3` -- co che la THAT, nhung no khong mua duoc thu ma `M-194` doi

```text
cell h2@0.650, nhan thang x2:

NC-3a  hieu chuan LAI tren che do moi, chuyen giao `kappa`
       qhat_ratio  = 2.0000000  chinh xac
       acceptance  0.46640864363804463 -> 0.46640864363804463
       lech        = 0.0  (dung bang khong, khong phai "nho")
       B2 mang nguyen `c`:  0.4631 -> 0.7184,  lech 0.2553

NC-3b  MANG NGUYEN `qhat_A` va `c`
       C3  0.4664 -> 0.7174,  lech 0.2510
       B2  0.4631 -> 0.7184,  lech 0.2553
```

Bat bien thang do cua C3 la **chinh xac tuyet doi** -- khong phai "gan dung
den sai so bin". `lambda = 2` la luy thua cua 2 nen phep nhan dung tung bit;
`conformal_level` chi phu thuoc `n_eff` va `alpha` nen khong doi;
`empirical_qhat` la mot thong ke thu tu nen gian dung `lambda`.

Nhung `NC-3b` cho thay dieu kien de co no:

```text
C3 chuyen giao duoc bang `kappa` -- mot tham so KHONG THU NGUYEN.
Nhung dieu do doi UOC LUONG LAI `qhat` tren che do moi, ma `qhat` la phan vi
cua `s`, ma `s` la ham cua `y_true`.  => VAN CAN NHAN o che do moi.

Neu KHONG hieu chuan lai (`NC-3b`), C3 troi 0.2510 -- gan bang B2 (0.2553).
```

> 🔑 Menh de dung ra khoi Task B: **C3 khong mien nhiem voi doi che do. Cai no
> co la mot tham so chuyen giao duoc (`kappa`) VA mot thu tuc da biet de tai
> lap phan con lai (`qhat`) tu du lieu co nhan cua che do moi, kem yeu cau co
> mau do duoc. B2 khong co ve thu hai.**

Do la mot phat bieu hep hon nhieu so voi ban thao dau ("C3 chuyen giao duoc
ma khong can biet gi ve che do moi"), va no la phat bieu duy nhat du lieu
chong do duoc.

## 5. `M-193` -- wiring da duoc xac minh; cai truot la DAI

```text
nhanh C3   max |dviolation| = 0.000e+00      8/8 o
           max |dacceptance| = 0.000e+00     8/8 o
nhanh B2   lech acceptance lon nhat = 0.02061  (h2@0.650), dai da ky 0.02
           bay o con lai: 0.0039 .. 0.0184
```

Duong cheo cua ma tran TAI TAO tung bit hang `variant_sweep` @ `kappa=0.5`
cua `taxonomy_audit.json`. Do la kiem wiring manh nhat co the co, va no xanh.

Nhanh B2 truot 0.0006. `c` la mot PHAN VI MAU do tren `calib`, roi acceptance
duoc do tren `test` -- hai tach khac nhau cua cung mot cell, nen mot lech co
do lon nay la binh thuong. **KHONG noi dai sau khi xem.** `G23-248` ghi FAIL,
va ly do that cua no duoc ghi ngay canh: dai dat hoi chat cho mot phan vi mau,
khong phai duong ong hong.

## 6. `M-195` -- va mot dai HAI PHIA phat ca chieu bao thu

```text
T3 = P(s > qhat_A | accept) tren 30 o giua ho:
    min 0.0000   trung vi 0.0881   max 0.8396

theo tieu chi DA KY  |viol - 0.10| <= 0.05, tuc [0.05, 0.15]:   6/30   MISS
```

Phan ra:

```text
viol < 0.05        12/30      bao thu -- dai hai phia PHAT, du bao dam VAN GIU
viol trong [0.05, 0.15]   6/30
viol > 0.15        12/30      vo bao phu that
```

So mot phia theo CHIEU BAO DAM (`viol <= alpha = 0.10`): **16/30**. Con so nay
**KHONG phai tieu chi da ky** va chi de mo ta -- ghi o day de khong ai nham no
voi phan quyet.

Doc dung: bao dam conformal duoc phat bieu cho `calib` va `test` cung phan
phoi. O 30 o giua ho dieu do sai theo dinh nghia, va ket qua chia gan doi:
mot nua so o giu bao phu (nhieu o rat bao thu), mot nua vo, co o vo rat nang
(0.8396). `A066` muc 4 da ky nhan `[NGOAI SUY]` va ghi truoc rang MISS o day
**khong bac bo gi** -- no chi noi bao dam dung o dau no duoc phat bieu.

Bai hoc ve thiet ke dai: mot dai hai phia quanh `alpha` tron "bao thu" voi
"vo". Neu Task ke tiep can cham lai dai luong nay, phai ky HAI nguong rieng.

## 7. `M-196` -- ket qua AM, va no vung

```text
trung vi |err|accept(C3) - err|accept(B2)| tai acceptance KHOP = 0.00526
tren 120 diem (30 o x 4 muc khop 0.70/0.50/0.30/0.15)
```

O cung ti le chap nhan, hai phuong phap gan nhu khong khac nhau ve risk. Dieu
nay khop voi `04-baselines.md`: `Jaccard(C3, B2) @0.78 = 0.9466` -- hai bo loc
chon gan cung mot tap.

`A066` muc 3 ky truoc rang thang nay PHAI co mat de bao cao trung thuc rang
dong gop KHONG nam o day. No khong nam o day.

## 8. `M-190` -- HIT, voi rang buoc `L92` nguyen ven

```text
trung vi T1_drift_C3   poisson -> h2   0.2352
                       h2 -> poisson   0.1803
```

Chieu du doan o `A065` muc 4.2 dung. **Nhung `L92`:** trong tap 8 cell song,
`poisson` chi song o `rho_bar` CAO va `h2` chi song o THAP, nen
"poisson -> h2" CUNG LA "rho cao -> rho thap". Hai bien bi ghep hoan toan.

```text
DUOC PHEP noi : bat doi xung theo CHIEU CHUYEN CHE DO
KHONG duoc noi: bat doi xung theo HO TAI
```

Go rang buoc nay doi mot manifest 18 cell (`A065` muc 4.1) -- mot lesson con,
khong phai mot muc cua Task B.

## 9. `NC-1` -- doi chung am xanh, nen thiet hai do duoc la THAT

```text
12 o ngoai duong cheo cua ma tran 4x4 cell CHET:
    trung vi T1_drift   C3 0.0276   B2 0.0277     (nguong <= 0.05)
```

O cac cell `err_neo < 0.05` -- twin gan nhu khong bao gio sai, gate chap nhan
gan het -- chuyen giao gan nhu khong ton gi cho ca hai. Nen con so 0.21 do o
cell song KHONG phai hien vat cua duong ong.

## 10. Kiem `L95` tren duong ong Task B

Ca 8 cell hieu chuan deu chay `selective` THAT:

```text
cell            qhat_source    min_blocks   acceptance_on_A   c_B2
h2@0.650        fixed_point       485           0.4837        8.3944
h2@0.675        fixed_point       489           0.5346       11.2524
h2@0.700        fixed_point       490           0.5896       14.8745
poisson@0.850   cycle_max         421           0.3295        7.8184
poisson@0.875   fixed_point       429           0.3527       12.1719
poisson@0.900   fixed_point       443           0.3712       17.9582
poisson@0.925   cycle_max         461           0.4054       23.8750
poisson@0.960   fixed_point       471           0.4368       32.4450
```

Khong cell nao cho `degenerate_fallback_to_none`, nen chot chan cua `A066`
muc 2.1 khong phai kich hoat. `min_blocks` 421..490 khop DUNG bang `M-192`,
tuc diem van hanh `kappa = 0.5` hoat dong nhu da tien dang ky.

Chu y `c_B2` di tu 7.82 den 32.45 -- **4.1x chi trong rieng ho poisson**. Do
la thu nguyen cua `c`, va la ly do no khong chuyen giao duoc.

## 11. Ket luan cua Task B -- ba cau

```text
1. Khi mang nguyen mot luat da hieu chuan sang mot che do khac, C3 troi ngang
   B2 (1.04x, khong phai 3x). Du doan chinh BI BAC BO. Ly do da ky truoc o
   `A066b`: o che do do CA HAI tham so mang di deu co thu nguyen.

2. Bat bien thang do cua C3 la THAT va CHINH XAC TUNG BIT -- nhung chi khi
   `qhat` duoc uoc luong lai tren che do moi, va viec do van can NHAN. Cai C3
   thuc su co khong phai "khong can biet gi ve che do moi" ma la mot tham so
   chuyen giao duoc (`kappa`) cong mot thu tuc da biet de tai lap phan con lai.

3. `T1` (acceptance drift) bi TOI DA HOA boi mot score ngau nhien (1.19e-05,
   nho hon bon van lan ca hai phuong phap that). No do do ON DINH cua ti le
   chap nhan chu khong do do TOT cua phep chon, nen no khong duoc lam thang
   chinh. Doi chung duong `NC-2` la thu duy nhat trong ca thiet ke phat hien
   duoc dieu nay.
```

## 12. Cai con lai cho lan sau

```text
1. Dong gop cua C3 so voi B2 KHONG nam o T1 (M-194 MISS) va KHONG nam o T2
   (M-196 HIT, tuc hai ben ngang nhau). No chi con o T3 -- dai luong ma B2
   khong co. Nhung T3 duoi chuyen giao chia gan doi (16/30 giu bao phu). Mot
   phat bieu trung thuc phai la CO DIEU KIEN, va dieu kien do can duoc do.

2. Thang T1 phai duoc thay hoac ghep cap. Mot ung vien: do drift CO DIEU KIEN
   tren risk -- vi du drift cua `err|accept` tai acceptance khop, thay vi
   drift cua chinh acceptance. B1 se khong toi da hoa dai luong do.

3. Dai hai phia quanh `alpha` cho T3 tron "bao thu" voi "vo" (muc 6). Ky HAI
   nguong rieng cho lan sau.

4. `L92` van chua go duoc: moi phat bieu "giua ho" cua Task B thuc chat la
   "giua che do van hanh". Go no doi manifest 18 cell.
```
