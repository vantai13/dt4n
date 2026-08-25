# 44 -- Lesson 23.22 Task B: ma tran chuyen giao C3 vs B2

Ngay      : 2026-08-25
Lesson    : 23.22 Task B
Amendment : `A066` (tien dang ky), `A066b` (sua `NC-3` truoc khi chay),
            `A067` (`L97`/`L98`/`L99`, ky lai `M-197`/`M-198`, mo Task B-2)
Artifact  : `results/LIVE/phase-23/transfer_matrix.json`
Chay      : 8x8 = 64 o + 4x4 doi chung am + `NC-3`, 1 phut 40 giay

## 0. Ba cau truoc khi doc bang

```text
1. Cau chuyen da tien dang ky BI BAC BO -- nhung vi mot ly do CAU TRUC suy ra
   duoc TRUOC khi chay (`L97`), khong phai vi the gioi bat ngo.

2. Ket qua that cua Task B khong nam trong bang cham. No la: that bai cua C3
   duoi doi che do CO DAU, va du doan duoc gan nhu tat dinh tu MOT dai luong
   quan sat duoc.

3. Doi chung duong `NC-2` FIRE, va no bac bo chinh THANG DO chinh cua thiet
   ke (`L99`). Do la thu quan trong nhat lan chay nay san xuat ra.
```

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
-- ky lai sau khi xem so (`A067`), cham tren tap CHUA XEM --
M-197    Spearman >= +0.70 tren cell chet +0.9500 / +0.8915               HIT ***
         va phan tach theo dau            0.5866 > 0.0200                 HIT
M-198    rho(m_hat, scale) >= +0.85       +0.9650  (MU)                   HIT ***
         dau dung >= 48/56                53/56    (khong mu)             HIT
```

```text
G23-248  FAIL   M-193  -- xem muc 2: ve wiring THAT pass tuyet doi
G23-249  FAIL   M-194  *** -- xem muc 3: tien de sai ve cau truc
G23-250  FAIL   M-195  -- xem muc 5: dai hai phia che mot phan tach theo dau
G23-251  PASS   M-196
G23-252  PASS   M-190
G23-253  PASS   NC-1
G23-254  FAIL   NC-2   *** -- xem muc 6
G23-255  PASS   NC-3a
G23-256  PASS   NC-3b
G23-257  PASS   M-197  ***
G23-258  PASS   M-198  ***
G23-259  --     M-199, Task B-2
```

## 2. `M-193` FAIL KHONG mang thong tin -- duong ong SACH  (`L98`)

Gate co ba ve. Hai ve dau la kiem wiring THAT:

```text
max_abs_delta_violation_C3   = 0.000e+00      8/8 o
max_abs_delta_acceptance_C3  = 0.000e+00      8/8 o
```

Duong cheo cua ma tran chuyen giao **tai tao TUNG BIT** hang `variant_sweep`
@ `kappa=0.5` cua `taxonomy_audit.json`. Do la kiem wiring manh nhat co the
co, va no xanh tuyet doi.

Ve thu ba fail o `0.0206 > 0.02`. Nhung ve do la:

```text
| acceptance cua B2 do tren TEST  -  acceptance cua C3 do tren CALIB |
```

Do la **nhieu tach `calib`/`test`** cong khac biet quy tac (C3 dung ca ba slot
voi `.all()`, B2 chi dung `m_hat_1`). Doi chung: `T1_drift_C3` tren CUNG duong
cheo chay tu 0.0036 den **0.0173** -- cung co. Neu 0.0206 la bang chung duong
ong hong thi 0.0173 cung phai la, ma ve C3 lai trung bit.

```text
Gate GIU FAIL: dai la dai da ky, khong noi sau khi xem.
Nhung phat bieu dung la: duong ong KHONG hong. Ve thu ba dac ta sai.
```

## 3. `M-194` -- du doan chinh bi bac bo, va tien de sai ve CAU TRUC  (`L97`)

```text
T1 drift tren 30 o giua ho:
           min      q1      trung vi     q3      max
    C3   0.0047  0.1293    0.2090     0.3324  0.5186
    B2   0.0054  0.1292    0.2174     0.3398  0.5291
```

Hai phan phoi chong khit. Ti so trung vi 1.04x so voi nguong da ky >= 3x. Day
khong phai mot phep thu thieu luc: neu hieu ung ton tai o co 3x, 30 o da du.

**Vi sao tien de sai.** `A066` muc 1.2 lap luan C3 bat bien thang vi luat la
mot TI SO. Nhung trong ma tran, `qhat` bi DONG BANG tu cell A:

```text
m_hat_j / qhat_j^A >= kappa    <=>    m_hat_j >= kappa * qhat_j^A
                                                  ^^^^^^^^^^^^^^ HANG SO
```

C3-voi-`qhat`-dong-bang **cung la mot nguong tuyet doi** -- chi khac B2 o cho
no la mot nguong theo `z_bin` va slot thay vi mot nguong toan cuc. Ca hai deu
co thu nguyen; ca hai deu troi.

> 🔑 `M-194` MISS **khong phai mot ket qua thuc nghiem**. No la mot he qua cau
> truc le ra phai suy duoc truoc khi chay. `A066b` da bat nua lap luan nay cho
> `NC-3` nhung khong rut ra rang KHOI CHINH cung chay o che do do.

Nguyen tac (`L97`): *mot tinh chat cua LUAT khong tu dong la tinh chat cua
LUAT VOI THAM SO DONG BANG.*

## 4. ★ Ket qua that: that bai cua C3 CO DAU va du doan duoc

> ⚠️ Muc nay la **POST-HOC** o tap cell song. Da ky lai o `A067` muc 5.3 va
> cham MU tren ma tran 4x4 cell CHET (muc 4.3).

### 4.1. Phan tang theo huong

```text
T3 (viol|accept cua C3) tren 30 o GIUA HO, alpha = 0.10:

  poisson -> h2    n=15   min 0.0000   trung vi 0.0113   max 0.5273
  h2 -> poisson    n=15   min 0.0002   trung vi 0.2786   max 0.8396
                                        ^^^^^^^^^^^^^^^ chenh 25x
```

### 4.2. Bien giai thich: TI LE THANG cua `qhat`

`scale(cell)` = `qhat_slot1_mean` cua **V-M tai `kappa = 0`** trong
`taxonomy_audit.json` -- mot dai luong cua **Task A0**, khong phu thuoc mot
dai luong nao cua Task B.

```text
poisson@0.700   1.0467     h2@0.650   16.1809     poisson@0.900  34.4153
poisson@0.850  15.5590     h2@0.675   21.3514     poisson@0.925  44.1072
poisson@0.875  23.7692     h2@0.700   27.6184     poisson@0.960  62.3353
h2@0.850       52.7210     h2@0.925   60.5615     h2@0.960       65.4591
```

Tren 56 o ngoai duong cheo cua ma tran cell SONG:

```text
qhat mang sang QUA LON (scale_B < scale_A)  n=28  viol trung vi 0.0027   vuot alpha  0/28
qhat mang sang QUA NHO (scale_B > scale_A)  n=28  viol trung vi 0.3736   vuot alpha 27/28

Spearman( log(scale_B / scale_A) , viol|acc ):
   30 o giua ho          = +0.9813
   56 o ngoai duong cheo = +0.9874        gan tat dinh
```

**Co che:** thang cua `qhat` la thang cua `s`. Mang mot nguong do o mot phan
phoi NHO vao mot phan phoi LON thi nguong thieu -> `s > qhat` nhieu -> vo bao
phu. Chieu nguoc lai bao thu.

### 4.3. `M-197` -- cham MU tren tap CHUA XEM, va TRUNG

Artifact truoc `A067` chi ghi TRUNG VI cua `T1_drift` cho `NC-1`; khong mot
gia tri `T3` nao cua cell chet duoc ghi hay in ra. Nen 4 cell chet la mot tap
mu that.

```text
Spearman( log ti le thang , viol|acc C3 ) tren ma tran 4x4 cell CHET:
    12 o ngoai duong cheo   = +0.9500
    16 o ke ca duong cheo   = +0.8915
    -> dat nguong +0.70 duoi CA HAI cach doc
```

Van ban ky viet "16 o" trong khi phep phan tich theo dau chi co nghia o 12 o
ngoai duong cheo (o duong cheo co ti le = 1, log = 0). Da cham CA HAI, va
phan quyet khong doi -- ap dung truc tiep bai hoc `L94`.

Phan tach theo dau:

```text
viol trung vi nhom "qhat qua nho"   0.5866
viol trung vi nhom "qhat qua lon"   0.0200        chenh 29x
```

Bien do o cell CHET **lon hon** o cell song (0.5866 vs 0.3736), khong nho hon
nhu du kien khi ky. Ly do: dai thang o tap chet rong hon nhieu
(`poisson@0.700` = 1.05 den `h2@0.960` = 65.46, tuc 62.5x).

### 4.4. Chieu an toan bao hoa o TU CHOI TOAN BO

Ba o cua ma tran cell chet co `n_accept = 0`, nen `viol` khong xac dinh:

```text
o                              log ti le   n_accept
h2@0.960 -> poisson@0.700        -4.136        0
h2@0.925 -> poisson@0.700        -4.058        0
h2@0.850 -> poisson@0.700        -3.919        0
```

Mang mot `qhat` cua cell thang 65.5 vao mot cell thang 1.05 thi `kappa*qhat`
lon den muc **khong hang nao duoc chap nhan**. Do la cuc doan cua chieu "qua
lon": an toan tuyet doi cho bao phu, va vo dung tuyet doi cho van hanh.

```text
=> Chieu "qhat qua lon" KHONG phai chieu "tot". No la chieu ma phep do T3
   khong phat hien duoc gi, vi no bao thu den muc thoai hoa. Doc T3 mot minh
   o chieu do se nham "0 vi pham" voi "hoat dong tot" -- CUNG hinh dang voi
   `L99` (muc 6).
```

### 4.5. `M-198` -- chi bao KHONG CAN NHAN, va no TRUNG

`A066` muc 1.1 rut cau *"conformal hieu chuan lai duoc bang du lieu KHONG
NHAN"*, va rut dung: `qhat` la phan vi cua `s`, ma `s` can `y_true`. Nen ti le
thang `scale_B/scale_A` **can nhan**.

Nhung `m_hat` la dau ra cua CHINH twin -- **khong can nhan**:

```text
(1) Spearman( log median m_hat_1 tren tach TEST , log scale qhat )
    = +0.9650 tren 12 cell    [MU hoan toan, nguong +0.85]

(2) Dung ti le m_hat THAY ti le qhat de du doan DAU cua (viol - alpha)
    tren 56 o: dung 53/56     [KHONG MU -- bien ket qua da xem]
```

⚠️ Chi menh de (1) mang thong tin moi. Menh de (2) dung bien ket qua da xem
(`A067` muc 6.2) -- no chi kiem rang phep thay the khong lam hong gi.

```text
cell             scale qhat   median m_hat1   ti so
poisson@0.850       15.5590         5.3817    0.346    <- cell SONG: m_hat < qhat
h2@0.700            27.6184        17.9735    0.651
poisson@0.960       62.3353        27.1111    0.435
h2@0.850            52.7210        87.2940    1.656    <- cell CHET: m_hat > qhat
h2@0.960            65.4591       128.0478    1.956
poisson@0.700        1.0467         1.7470    1.669
```

Ti so `median m_hat / scale` tach SACH cell song (0.35..0.65) khoi cell chet
(1.66..2.01). Do la mot quan sat POST-HOC va khong duoc cham, nhung no khop
voi dinh nghia cua "cell chet": `m_hat` lon hon nguong nen moi thu duoc chap
nhan va khong co chon loc.

## 5. `M-195` -- dai HAI PHIA che chinh phan tach o muc 4

```text
T3 tren 30 o giua ho:  min 0.0000   trung vi 0.0881   max 0.8396
tieu chi DA KY |viol - 0.10| <= 0.05, tuc [0.05, 0.15]:   6/30   MISS

phan ra:  viol < 0.05          12/30   bao thu -- dai PHAT, du bao dam VAN GIU
          [0.05, 0.15]          6/30
          viol > 0.15          12/30   vo that
```

So mot phia theo CHIEU BAO DAM (`viol <= alpha`): **16/30**. Con so nay
**KHONG phai tieu chi da ky** va chi de mo ta.

Dai `|viol - alpha|` xep `0.0027` (an toan thua) **cung hang** voi `0.3736`
(vo tham hai). Do la ly do bang cham khong thay phat hien o muc 4: no bo DAU.

```text
Cung hinh dang, lan thu BA trong do an:
  Phase 14   92.2% gap den tu MOT atom z=0
  Lesson 22  spread_m = 1.12 che hieu ung don o m_hat_bin=3
  Task B     |viol - alpha| che mot phan tach 0/28 vs 27/28 theo DAU
```

Bai hoc thiet ke: mot dai hai phia quanh `alpha` tron "bao thu" voi "vo". Lan
sau phai ky HAI nguong rieng.

## 6. `NC-2` -- doi chung duong bac bo THANG DO CHINH  (`L99`)

```text
trung vi T1_drift tren 30 o giua ho:
    B1  (score NGAU NHIEN)      1.19e-05      <- it troi nhat
    C3  (conformal)             0.2090
    B2  (nguong tuyet doi)      0.2174
```

Mot score khong mang mot bit thong tin nao ve `a_twin = a*` troi it hon **bon
van lan** ca hai phuong phap that. Ly do: `score_B1_random` la `U(0,1)` o MOI
cell, nen phan phoi cua no khong doi khi che do doi, nen mot nguong hoc tren A
cho dung ti le chap nhan tren B.

> **Moi thang do co dang "X thay doi it den dau" deu duoc TOI DA HOA boi mot
> quy tac KHONG NHIN VAO DU LIEU.** Toi uu cua mot thang on dinh khong co so
> hang huu ich la mot hang so. `T1` KHONG duoc bao cao mot minh; phai luon kem
> mot SAN HUU ICH (`T2` hoac `T3`).

```text
Cung hinh dang, lan thu BA:
  Phase 22    FCR giu bao phu 0.0160 << alpha bang cach chap nhan 9.9%
  Lesson 22   V-S "giu 12/12" mot phan bang `qhat = max mau` (`L93`)
  Task B      B1 co drift nho nhat bang cach khong nhin du lieu
```

Neu chi cham `M-194`, ta se ket luan "C3 va B2 ngang nhau ve chuyen giao" ma
khong bao gio biet thang do dung de ket luan dieu do xep mot mau nhieu len
tren ca hai. **Doi chung duong la thu duy nhat trong ca thiet ke phat hien
duoc dieu nay.**

### 6.1. Mot hien vat DA sua truoc khi ket luan

Ban dau `T1_drift_B1` dung `_accept_at_coverage(sb1, acceptance_on_A)`, phep
do EP dung ti le chap nhan cua A nen drift = 0 **do dung**. Da doi sang mang
mot NGUONG `c_B1` do tren A, y het B2. Ket qua khong doi ve chat, nhung nay no
noi duoc dieu no khang dinh.

## 7. `M-196` -- ket qua AM, bao cao ngang hang

```text
trung vi |err|accept(C3) - err|accept(B2)| tai acceptance KHOP = 0.00526
tren 120 diem (30 o x 4 muc khop 0.70/0.50/0.30/0.15)
```

O cung ti le chap nhan, hai phuong phap gan nhu khong khac nhau ve risk. Khop
voi `04-baselines.md`: `Jaccard(C3, B2) @0.78 = 0.9466`.

`A066` muc 3 ky truoc rang thang nay PHAI co mat de bao cao trung thuc rang
dong gop KHONG nam o day. **No khong nam o day.**

## 8. `M-190`, `NC-1`, `NC-3` -- ba muc ngan

```text
M-190 HIT   trung vi T1_drift_C3   poisson->h2 0.2352  >  h2->poisson 0.1803
      ⚠️ `L92`: chieu nay CUNG LA (rho cao -> rho thap). Hai bien ghep hoan
         toan. DUOC PHEP noi "bat doi xung theo CHIEU CHUYEN CHE DO";
         KHONG duoc noi "theo HO TAI".

NC-1  HIT   12 o ngoai duong cheo cua ma tran cell CHET: trung vi T1_drift
      0.0276 (C3) / 0.0277 (B2), nguong <= 0.05. Nen con so 0.21 do o cell
      song KHONG phai hien vat cua duong ong.

NC-3a HIT   nhan CA calib va test x2 roi hieu chuan lai:
            qhat_ratio = 2.0 CHINH XAC
            acceptance C3  0.46640864363804463 -> 0.46640864363804463
            lech = 0.0 (dung bang khong)   |   B2 mang nguyen `c`: lech 0.2553
NC-3b HIT   mang nguyen `qhat_A` va `c`: CA HAI troi (0.2510 / 0.2553).
      Chan cach doc "C3 mien nhiem voi doi che do".
```

## 9. Kiem `L95` tren duong ong Task B

Ca 8 cell hieu chuan deu chay `selective` THAT -- khong cell nao cho
`degenerate_fallback_to_none`, nen chot chan cua `A066` muc 2.1 khong phai
kich hoat.

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

`min_blocks` 421..490 khop DUNG bang `M-192`, tuc diem van hanh `kappa = 0.5`
hoat dong nhu da tien dang ky. `c_B2` di tu 7.82 den 32.45 -- **4.1x chi
trong rieng ho poisson**. Do la thu nguyen cua `c`.

## 10. Menh de con lai -- hep, va co bang chung

```text
1. C3 KHONG mien nhiem voi doi che do. Mang nguyen mot luat da hieu chuan
   sang che do khac thi C3 troi ngang B2 (1.04x) -- va dieu do suy ra duoc tu
   cau truc (`L97`), khong phai mot phat hien.

2. Cai C3 co ma B2 khong:
   (a) mot tham so chuyen giao duoc KHONG THU NGUYEN (`kappa`) cong mot thu
       tuc da biet de tai lap phan con lai (`qhat`) tu du lieu CO NHAN cua
       che do moi, kem yeu cau co mau DO DUOC (`L91`, `L93`).
       Bat bien do la CHINH XAC TUNG BIT khi hieu chuan lai (`NC-3a`).
   (b) mot dai luong DONG HANH (`qhat`) khien that bai CO DAU va du doan
       duoc: Spearman +0.9874 tren 56 o, 0/28 vs 27/28, va +0.9500 tren tap
       CHUA XEM (`M-197`).
   (c) mot CHI BAO KHONG CAN NHAN cho biet dang o phia nao cua ranh gioi:
       `median m_hat_1` bam thang `qhat` voi rho = +0.9650 (`M-198`).
       B2 khong co gi tuong ung -- `c` la mot hang so tu do, khong co dai
       luong dong hanh nao de so.

3. (a) van CHUA duoc do: "yeu cau co mau DO DUOC" moi la mot khang dinh dinh
   tinh. Task B-2 (`M-199`, `G23-259`) do no.
```

## 11. Cai con lai cho lan sau

```text
1. Thang `T1` phai duoc thay hoac ghep cap (`L99`). Mot ung vien: drift CO
   DIEU KIEN tren risk -- drift cua `err|accept` tai acceptance KHOP, thay vi
   drift cua chinh acceptance. B1 se khong toi da hoa dai luong do.

2. Dai hai phia quanh `alpha` cho T3 tron "bao thu" voi "vo" (muc 5). Ky HAI
   nguong rieng. Va o chieu bao thu phai kem mot san ACCEPTANCE, neu khong
   "0 vi pham" se dat cho mot o `n_accept = 0` (muc 4.4).

3. `L92` van chua go duoc: moi phat bieu "giua ho" cua Task B thuc chat la
   "giua che do van hanh". Go no doi manifest SLA 18 cell -- mot lesson con.

4. Task B-2 (`M-199`): chi phi tai hieu chuan. Day la thi nghiem DUY NHAT
   chong do duoc menh de 2(a) o muc 10.
```
