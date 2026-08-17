# AMENDMENT 23-21 -- Sua doi chung duong PC-S-1, ghi MISS cho S-5, khoa du doan 23.6/23.9/23.11

Ngay: 2026-08-17
Commit: sau khi chay artifact 23.5[A] ngay 2026-08-16, truoc khi dong 23.5[A].

Amendment nay lam ba viec, va PHAI doc theo dung thu tu do:

1. HUY BO mot con so da bao cao vi no bi tran chan.
2. GHI MISS cho mot dai du doan cua chinh Amendment 23-20, KHONG sua hoi to.
3. Khoa du doan cho 23.6 / 23.9 / 23.11 TRUOC khi chay chung.

---

## 1. HUY BO -- `PC_S_1_small_n` voi `subsample_blocks = 20`

### 1.1. Con so bi huy

```text
Artifact ngay 2026-08-16, khoa "PC_S_1_small_n", tham so subsample_blocks=20:

  cell            coverage_clean  coverage_leaked  coverage_drop
  poisson@0.925       0.9997273        0.9971364      0.0025909
  poisson@0.850       0.9995909        0.9976364      0.0019545
  h2@0.700            0.9997273        0.9987273      0.0010000

Ba dong nay VO NGHIA. Khong duoc trich dan o bat ky dau.
```

### 1.2. Nguyen nhan -- tran chan

`subsample_blocks=20` giu `2 x 20 = 40` block. `is_calib` chia doi con ~20
block hieu chuan, fold split chia doi lan nua. Do trong du lieu nay MOI block
trai qua ca 4 Mondrian bin, so block fold2 TRONG TUNG BIN la 9. Da do lai:

```text
OLD subsample_blocks=20 -> realized per-bin fold2 blocks and level:
  bin 0: n_eff_blocks_fold2=9  level=1.0
  bin 1: n_eff_blocks_fold2=9  level=1.0
  bin 2: n_eff_blocks_fold2=9  level=1.0
  bin 3: n_eff_blocks_fold2=9  level=1.0
coverage_marginal = 0.9997272727272727
```

Voi `n = 9`, `alpha = 0.10`:

```text
conformal_level(9, 0.10):  k = ceil((9+1) * 0.9) = ceil(9.0) = 9
                           k > n ?  9 > 9 -> False
                           level = 9/9 = 1.0        <- PHAN VI 100%
=> qhat = MAX cua fold2
=> coverage ~ 1.0 voi MOI thu tuc
=> nhanh ro ri va nhanh sach cho cung mot so
```

Doi chung bi TRAN CHAN: no khong the phan biet "khong co ro ri" voi
"phep do mu". `coverage_drop` do duoc chi la nhieu quanh tran.

### 1.3. Nguong dung -- `n >= 19`, KHONG phai `n >= 11`

`level < 1` khi va chi khi `ceil((n+1)(1-alpha)) <= n-1`, tuong duong
`n >= 2/alpha - 1`. O `alpha = 0.10` nguong la **19**. Da do:

```text
  n=   9  k=   9  level=1.0000  saturated=True
  n=  10  k=  10  level=1.0000  saturated=True
  n=  11  k=  11  level=1.0000  saturated=True   <- ceil(1/alpha)+1 = 11 VAN TRAN
  n=  12  k=  12  level=1.0000  saturated=True
  n=  15  k=  15  level=1.0000  saturated=True
  n=  18  k=  18  level=1.0000  saturated=True
  n=  19  k=  18  level=0.9474  saturated=False  <- nguong dung
  n=  30  k=  28  level=0.9333  saturated=False
```

Dan lai cho day du, de thanh cong thuc dung mai:

```text
level < 1  <=>  ceil((n+1)(1-alpha)) <= n-1
           <=>  (n+1)(1-alpha) <= n-1        (vi n-1 nguyen)
           <=>  n + 1 - alpha(n+1) <= n - 1
           <=>  2 <= alpha(n+1)
           <=>  n >= 2/alpha - 1             CHINH XAC, khong phai xap xi

alpha = 0.10 -> n >= 19    alpha = 0.05 -> n >= 39    alpha = 0.01 -> n >= 199
```

Ghi ro de khong ai lap lai: cong thuc `ceil(1/alpha) + 1 = 11` la SAI,
`conformal_level(11, 0.10) = 1.0`. Nguong dung la `2/alpha - 1 = 19`.

He qua thu hai: hang so `MIN_BLOCKS_FOLD = 9` khoa o Amendment 23-20 D5
KHONG chan duoc tran chan -- no dung bang muc tran. D5 chi chan `qhat = +inf`
(`level is None`), khong chan `level = 1.0`. Hai loi khac nhau.

Mau loi de ghi vao so:

```text
MOT HANG SO BAO VE HAI BAT BIEN KHAC NHAU THI NO CHI THAT SU BAO VE MOT.
MIN_BLOCKS_FOLD = 9 chan duoc qhat = +inf, va im lang khong chan qhat = max.
Sua: tach ten. MIN_BLOCKS_FINITE (chan inf, giu nguyen gia tri 9 cua D5) va
min_blocks_unsaturated(alpha) (chan tran, tinh tu alpha). Ten tu tai lieu hoa.
```

### 1.4. Sua

`cert/studentized_score.py`:

```text
* them min_blocks_unsaturated(alpha) -- tra ve n nho nhat co level < 1.0
* doi tham so positive_control_sigma_leak: subsample_blocks (so block GIU)
  -> n_blocks_fold2_target (so block MUC TIEU cua fold2). blocks_kept = 4*target.
* RAISE ValueError("... TRAN CHAN ...") khi conformal_level(target) >= 1.0
* RAISE lan hai khi level THUC TE do duoc sau khi chia fold >= 1.0
* lap tren 5 seed SEEDS_SUB = (23501..23505), bao cao mean +/- SD
* PC_TARGET_BLOCKS_FOLD2 = 30 -> conformal_level(30, 0.10) = 0.9333 < 1.0
```

`test/test_phase23_studentized.py`:

```text
* T16 -- PC-S-1 va PC-S-1d PHAI raise voi target in (9,10,11,15,18)
* T17 -- min_blocks_unsaturated(0.10) == 19 va (0.05) == 39
* T18 -- PC_TARGET_BLOCKS_FOLD2 = 30 khong tran
```

### 1.5. Ket qua sau khi sua

```text
target=30  level=0.9333        (khong con tran: clean ~ 0.936, khong phai 0.9997)

cell            clean               leaked              drop
poisson@0.925   0.93592 +/- 0.01634 0.93436 +/- 0.01609 0.00156 +/- 0.00028
poisson@0.850   0.93228 +/- 0.01781 0.93016 +/- 0.01885 0.00213 +/- 0.00187
h2@0.700        0.93048 +/- 0.01386 0.92880 +/- 0.01472 0.00167 +/- 0.00176
```

Doc dung: che do it du lieu MOT MINH khong cuu duoc doi chung. `drop ~ 1.6e-3`
nam sau duoi `SD ~ 1.8e-3` cua chinh no. Khac biet so voi truoc la BAY GIO cau
"khong phat hien duoc" moi co nghia, vi phep do khong con nam o tran.

---

## 2. Doi chung duong moi PC-S-1d -- sigma nhieu chieu

`PC-S-1b` cua Amendment 23-20 ("sigma theo block") khong dung duoc: sigma theo
block khong ap duoc len test, nen no la oracle chu khong phai thu tuc.

PC-S-1d thay bang mot sigma DEPLOYABLE: uoc rieng cho tung o
`(phan vi m_hat_1) x (rank slot)`. `m_hat_1` quan sat duoc luc chay that.

```text
CLEAN  : gia tri sigma tu fold1  -> bao dam PHAI GIU voi MOI p
LEAKED : gia tri sigma tu fold2  -> chuan hoa trong mau -> bao phu PHAI VO
Bien o (cell edges) lay tu fold1 o CA HAI nhanh, de chi co gia tri sigma di
chuyen. Dieu nay co lap co che "chuan hoa trong mau" khoi moi thay doi binning.
```

Quyet dinh: bao cao mot THANG p, khong phai mot diem. Mot diem khong tach duoc
"ro ri nho" voi "phep do mu"; mot thang don dieu thi tach duoc.
`cells_grid = (10, 100, 1000)` -> `p/bin = (30, 300, 3000)`.

---

## 3. GHI MISS -- dai v2 cua S-5

### 3.1. Ket qua

Dai v2 cua Amendment 23-20 la `S-5 in [1.05, 1.50]`. Do duoc `sigma3/sigma1`
o muc PER-BIN:

```text
cell             bin0     bin1     bin2     bin3  |     max
poisson@0.925  1.1117   1.1110   1.1167   1.1421  |  1.1421   PASS
poisson@0.850  1.2787   1.2914   1.3051   1.3325  |  1.3325   PASS
h2@0.700       1.6557   1.4976   1.4268   1.3897  |  1.6557   MISS (> 1.50)
```

**S-5 dai v2 = MISS o h2@0.700 bin 0 (1.6557).**

### 3.2. Nguyen nhan -- loi MUC DO TONG HOP, khong phai loi co che

Dai `[1.05, 1.50]` duoc dan tu `rms_scores` trong
`results/phase-22/conformal_sim_*.json`, la rms GOP tren toan bang. No duoc ap
cho mot dai luong do o muc PER-BIN. Do la vi pham quy tac ba nhan
`scale / level / rowset`: du doan duoc dat ma khong ghi `level`.

Do doi chieu, o muc POOLED dai v2 khong bi vuot:

```text
sigma toan cuc (sigma_scope=global):
  poisson@0.925  [12.5057, 13.1693, 14.1736]  ratio3/1 = 1.1334
  poisson@0.850  [ 3.4254,  3.8183,  4.5274]  ratio3/1 = 1.3217
  h2@0.700       [ 7.0006,  8.6683,  9.9279]  ratio3/1 = 1.4181
```

Co che khong sai: `sigma` tang theo rank slot o 12/12 o. Chi cai NHAN sai.

### 3.3. Dieu KHONG duoc lam

```text
KHONG sua dai v2 roi tuyen bo PASS.
Mat mot dau tick khi ghi MISS. Mat TOAN BO gia tri cua bang pre-registration
khi sua dai sau khi nhin so. Loi nay den tu de xuat dai v2 trong Amendment
23-20, khong phai tu du lieu.
```

### 3.4. Tach S-5 -- CHI cho cac phase SAU, KHONG hoi to

```text
S-5-pooled   [scale=cost_ms][level=pooled ][rowset=calib fold1]  1.05 - 1.45
S-5-perbin   [scale=cost_ms][level=per_bin][rowset=calib fold1]  1.05 - 1.75
Nhan nguon: [MO TA] -- suy tu artifact 23.5A da chay. KHONG confirmatory.
```

Hai dong nay KHONG duoc dung de cham lai Lesson 23.5[A]. 23.5[A] ghi
`S-5 dai v2 = MISS`.

---

## 4. Ghi MISS thu hai -- du bao "hieu ung nho" cua 23.5[A]

Ghi chep truoc khi chay noi studentization "chi mua them 1-2 diem phan tram
acceptance". Do duoc:

```text
cell            sigma3/sigma1  acc_max   acc_stud   delta tuyet doi  delta TUONG DOI
poisson@0.925       1.1204     0.16657    0.18572      +0.01915        +11.50%
poisson@0.850       1.3019     0.09520    0.13562      +0.04042        +42.46%
h2@0.700            1.4924     0.26112    0.38674      +0.12562        +48.11%
```

Du bao dung tren main cell (+1.9 diem phan tram) va SAI tren hai cell phu. Loi
la ngoai suy tu MOT cell sang ca ba -- dung loi `S6` da dat ten: ba cell khong
phai mot truc thi nghiem. `sigma3/sigma1` bien thien `1.12 -> 1.49`, khong phai
hang so cua he.

---

## 5. Du doan khoa cho cac lesson SAU

Ky TRUOC khi chay cac lesson tuong ung.

### 5.1. Lesson 23.11 -- kiem gia thuyet lift

Do duoc o 23.5[A], `n = 3`, Spearman = 1.0:

```text
sigma3/sigma1 = 1.120 -> delta acceptance tuong doi +11.5%
                1.302 ->                            +42.4%
                1.492 ->                            +48.1%
ratio slot 1  = 0.9525 -> 0.8740 -> 0.7678   (don dieu giam)
```

Ba diem la GIA THUYET, khong phai dinh luat.

```text
[ ] H-23.11-1  Them cot sigma3_over_sigma1 va delta_acceptance_relative vao
               bang ket qua cua MOI trong 5 profile tai. Chi phi ~0.
[ ] H-23.11-2  Du doan: Spearman(sigma3/sigma1, delta_acc_rel) >= 0.8 tren
               n = 5.  Nhan nguon: [NGOAI SUY] tu n=3.
[ ] H-23.11-3  Neu H-23.11-2 bi bac bo, ghi la DU LIEU (NT 21), khong phai rac:
               phat bieu lai la "sigma3/sigma1 la dieu kien CAN chu khong DU",
               va bao cao bien nao con lai giai thich phan du.
[ ] H-23.11-4  Do nesting_slack_min o CA 5 profile.
               Do o 23.5A: 1.0271 / 1.0071 / 1.0446 -- nesting giu nhung bien
               do chi con 0.7% - 4.5%.
               Du doan: slack GIAM don dieu khi swing tang, va co the < 1.0 o
               profile swing lon nhat.
               Neu < 1.0 -> only_max > 0 -> PHAI bao cao err tren hang BI MAT,
               khong chi hang duoc them.  Nhan nguon: [CO CHE].
```

Ly do H-23.11-4 dang o day: `only_max = 0` o 23.5[A] la QUAN SAT, khong phai
dinh ly. Nesting doi hoi do trai chi phi giua cac duong, tuc chinh truc ma
23.11 thay doi. Ghi truoc dieu kien se pha ket qua cua chinh minh, roi do no.

### 5.2. Lesson 23.9 (P23-E) -- transfer giua bin tuoi

Co so: phat hien F-23.5A-1 (muc 6 duoi day).

```text
[ ] E-1  |c(g0) - c(g)| / c(g0) tren MOI cap bin        du doan < 0.06
[ ] E-2  N* = so block can o bin dich de sigma du on dinh   du doan 20 - 60
[ ] E-3  coverage cua qhat ngoai suy  qhat(g,j) = c(g0)*sigma(g,j)
                                                        |do - 0.90| <= 0.05
Nhan nguon E-1: [MO TA] (do duoc o 23.5A). E-2/E-3: [NGOAI SUY].
```

### 5.3. Lesson 23.6 -- duong bien risk-coverage

```text
P(sai VA accept) = acceptance x p_wrong|accept, do o kappa = 1:

  poisson@0.925  stud  0.18572 x 0.01576 = 0.00293   ->  2.9% cua alpha=0.10
  poisson@0.850  stud  0.13562 x 0.01043 = 0.00141   ->  1.4%
  h2@0.700       stud  0.38674 x 0.00880 = 0.00340   ->  3.4%

[ ] R-23.6-1  kappa = 1 dang bao thu qua muc ~30 lan so voi ngan sach alpha.
              Du doan: duong bien 23.6 con RAT NHIEU du dia ve phia coverage
              cao, va argmin cua risk_system se nam o kappa < 1.
              Nhan nguon: [MO TA] tu 23.5A.
```

---

## 6. Phat hien ngoai du kien F-23.5A-1

Xem `docs/phase-23/08-studentized-and-go-debts.md` muc 6. Trang thai [MO TA],
KHONG confirmatory. Chuyen giao cho Lesson 23.9.

---

## 7. Pham vi duoc phep chay sau amendment nay

```text
* sua cert/studentized_score.py theo muc 1.4 va 2
* them test T16..T21 vao test/test_phase23_studentized.py
* ghi de results/phase-23/studentized_{poisson_0.925,poisson_0.850,h2_0.700}.json
* cap nhat docs/phase-23/08-studentized-and-go-debts.md
```

Khong duoc dong thoi sua dai du doan nao khac ngoai muc 3.4, va muc 3.4 chi
ap dung cho phase SAU.

## 8. Tag da duoc doi -- ghi ro, khong doi lang le

```text
Tag  phase-23-lesson-5a-complete  truoc day tro commit 259c094
     ("phase 23.5a: studentized max-score"), la commit CHUA sua PC-S-1.
Commit do chua PC_S_1_small_n bi tran chan (muc 1.1).
Tag duoc doi (git tag -f) sang commit dong 23.5[A] ngay 2026-08-17.

Ly do ghi lai: mot tag tro toi artifact da bi huy bo thi khong con dung nghia
"lesson complete". Doi tag ma khong ghi la viet lai lich su lang le.
Commit 259c094 VAN con trong lich su va van truy cap duoc bang hash.
```

