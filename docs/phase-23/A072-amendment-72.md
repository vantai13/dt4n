# AMENDMENT 23-72 -- LESSON 23.23: BASELINE CO NGUON + KHOANG KHONG-CONFORMAL

Ngay ky : 2026-08-26

Moc     : sau tag `lesson-23-22-complete`, TRUOC dong code cham diem dau tien
          cua Lesson 23.23 (`A071` R1)

Loai    : TIEN DANG KY mot chum phep do + mot hang so moi (`K08`)

## 0. Cau hoi chan (`A071` R4)

> "Neu KHONG chay Lesson 23.23, paper mat cau nao trong `CLAIMS.md`?"

Mat HAI cau, va ca hai deu chua ton tai:

```text
CL-12  "khoang khong-conformal KHONG giu duoc bao dam tren truc tuoi"
CL-13  "C3 TU CHOI cap chung nhan khi mau khong du; baseline khac thi khong"
```

Ngoai ra, KHONG co cau nao trong `CLAIMS.md` hien tai duoc chong do boi mot
baseline CO NGUON TRICH DAN. Toan bo `B0`..`B6` do tac gia tu dung. Do la
mon no `W9`.

=> DUOC PHEP chay. Ngan sach: 8 gate (`A071` R1), khong mo them.

## 1. Ngan sach va anh xa ID

```text
Gate    : G23-289 .. G23-296        (8 gate, dung ngan sach)
Do      : M-225 .. M-231 + NC-23.23-1
Doc     : docs/phase-23/50-literature-baselines.md
Code    : cert/baselines_lit.py
Test    : test/test_baselines_lit.py
Artifact: results/PENDING/phase-23/baselines_lit.json
```

## 2. Ba dieu chinh so voi `PHASE_23_v3.md` -- va ly do

`PHASE_23_v3.md` muc "LESSON 23.23" viet: `accept neu m_hat >= 1.645 * sigma_hat`.
Ban ke hoach do KHONG duoc thi hanh nguyen van. Ba loi:

```text
E1  `1.645` = Phi^{-1}(0.95), ung voi alpha = 0.10 KHONG hieu chinh.
    Code cham diem dung alpha_each = alpha/(K-1) = 0.0333 (`config_matrix._alpha_each`).
    So dung: z = 1.8339146358159146. Hut 11.5% neu dung 1.645.
    => B8 se "vo coverage" nhu mot HIEN VAT cua muc alpha sai. Vo nghia.

E2  Cong thuc thieu `mu_hat`. Score `s = |e(a_j) - e(a_1)| >= 0` nen `E[s] > 0`
    chac chan. Bo `mu_hat` la dung mot STRAWMAN.
    Da do: voi H0 DUNG, ban thieu mu_hat cho viol = 0.2746 thay vi 0.0333.
    => no hong vi thieu mot tham so, KHONG vi Gaussian sai.

E3  `s` la TRI TUYET DOI. Neu `d = e(a_j) - e(a_1) ~ N(mu, sigma^2)` thi
    `s = |d|` theo FOLDED NORMAL, khong phai normal.
    Tai theta = 0, phan vi cua |d| rong hon phan vi cua d 1.1604 lan.
```

Ngoai ra `PHASE_23_v3.md` cap ma `G23-114..117` va doc `26-...`; ca hai da bi
chiem. So thuc: gate cuoi `G23-288`, doc cuoi `49-close-23-22d.md`.

## 3. Hang so moi -- `K08`

Them mot dong vao `docs/phase-23/CONSTANTS.md`:

| ma | hang so | gia tri | fit the nao | nguon | dung o dau | sai so |
|---|---|---:|---|---|---|---|
| K08 | `CV_MAX_FOLDED` -- he so bien dong cuc dai cua ho folded normal | 0.755510639762867 | KHONG fit. Dan giai tich: `sup_theta CV = sqrt(pi/2 - 1)`, dat tai `theta = 0` (half-normal) | amendment nay muc 4 | `cert/baselines_lit.py`, `M-227` | 0 (hang so toan hoc, khong phai uoc luong) |

Hai hang so phu, KHONG vao so vi chung suy tu `K08` va tu `ALPHA`:

```text
SQRT_2_OVER_PI = 0.7978845608028654    = sqrt(2/pi)
Z_BONF         = 1.8339146358159146    = Phi^{-1}(1 - 0.10/3)
THETA_HI       = 200.0                 can tren bisection; h(200) = 0.999987
BISECT_ITERS   = 200                   co dinh -> tai lap BIT-EXACT
```

`test_constants_ledger.py` phai ghim `K08` khop bieu thuc giai tich; khi
`cert/baselines_lit.py` duoc tao, test cua module phai ghim tiep hang so code.

## 4. Co so toan hoc cua `M-227` -- chan cau truc

Cho `d ~ N(mu, sigma^2)`, `s = |d|`. Dat `theta = mu/sigma >= 0` (WLOG).

```text
E[s^2] = mu^2 + sigma^2
E[s]   = sigma*sqrt(2/pi)*exp(-theta^2/2) + mu*erf(theta/sqrt(2))

r  = E[s] / sqrt(E[s^2]) = h(theta)
h(theta) = [sqrt(2/pi)*exp(-theta^2/2) + theta*erf(theta/sqrt(2))] / sqrt(1+theta^2)

h don dieu TANG, h(0) = sqrt(2/pi) = 0.7978846, h(inf) -> 1
```

Vi `r = 1/sqrt(1 + CV^2)`, dieu kien `r >= sqrt(2/pi)` tuong duong

```text
CV(s) <= sqrt(pi/2 - 1) = 0.755510639762867
```

MENH DE. Neu he so bien dong DAN SO cua score vuot `0.7555106`, thi KHONG
TON TAI cap `(mu, sigma)` nao khien `|N(mu,sigma^2)|` co cac moment dan so do.
Bat dang thuc la rang buoc CAU TRUC; voi mau huu han, ket luan bac bo phai qua
luat CI mot phia o muc 4.1, khong duoc dung CV mau tho.

### 4.1. Luat phan quyet -- va vi sao KHONG dung co tho

Do truoc (20000 lan rut, `mu = 0`, tuc H0 DUNG va nam DUNG TREN BIEN):

```text
n_eff     P(CV_mau > CV_MAX)
   29           0.407
   60           0.434
  120           0.453
  250           0.465
  457           0.476
 1000           0.487
```

Co tho co ti le bao dong gia 41--49%. No KHONG THE dung lam phep kiem.
Day la dung hinh dang `L119`.

LUAT DA KY: chi tuyen "NGOAI HO" khi

```text
CI95_lo(CV) > CV_MAX_FOLDED
```

voi `CI95` tu BLOCK bootstrap (`B = 2000`, hat giong `SEED_BOOT` cua
`build_calib_set_v2`), don vi lay lai mau la `block_id`, KHONG phai hang.

Muc sai lam loai I do duoc cua luat nay khi H0 dung tren bien:

```text
n =  60   0.0150
n = 250   0.0175
n = 457   0.0225        (muc danh dinh 0.025)
```

### 4.2. Bat doi xung PHAI in kem moi phat bieu ve `M-227`

```text
CV vuot nguong      -> Gaussian bi bac bo DUT KHOAT
CV khong vuot       -> KHONG KET LUAN DUOC GI
```

Do nhay do duoc: exponential (CV 1.000) FIRE; lognormal sigma=0.9 (1.115)
FIRE; hon hop 0.9N+0.1x6 (1.450) FIRE. Nhung lognormal sigma=0.6 (0.659) va
Pareto a=3 (0.619) KHONG FIRE du ca hai deu khong phai chuan.

=> `M-227` la dieu kien DU de bac bo, KHONG phai dieu kien CAN.
   CAM viet "CV trong nguong nen Gaussian phu hop".

## 5. Dinh nghia sau baseline

```text
B7   NGUONG TUOI CO NGUON TRICH DAN
     Ornee & Sun, "Sampling for Remote Estimation through Queues: Age of
     Information and Beyond", WiOpt 2019, DOI 10.23919/WiOPT47501.2019.9144087;
     ban mo rong "Sampling and Remote Estimation for the Ornstein-Uhlenbeck
     Process Through Queues: Age of Information and Beyond", IEEE/ACM ToN
     29(5), 2021, DOI 10.1109/TNET.2021.3078137.
     Tinh chat MUON: nguong duoc SUY RA bang bisection tren muc tieu MSE
     trung binh dai han, KHONG phai quet ra.
     Dieu chinh phai ghi ro trong doc 50:
       (a) bai goc quyet dinh "khi nao LAY MAU"; ta dung cho "khi nao TIN"
       (b) bai goc dung sai so uoc luong OU; ta dung `m_hat` cua twin
       (c) bai goc xet ca co va khong co rang buoc ti le lay mau; ta dung
           truong hop khong rang buoc
     => B7 KHAC B3: B3 quet nguong AoI, B7 suy nguong.

B8a  GAUSSIAN NGAY THO       q = Z_BONF * sd(s)                       [MO TA]
B8b  GAUSSIAN STEEL-MAN      folded normal + Student-t + sqrt(1+1/n)       *
B8c  PLUG-IN QUANTILE        np.quantile(s, 1-alpha_each)             [MO TA]
B8d  BLOCK BOOTSTRAP PERCENTILE, B = 2000, don vi = block
B9   ORACLE -- KHONG MO. Ap `A071` R4: `B6` va `B6-sys` da ton tai, da do,
     da khop closed form (`04-baselines.md`, AURC = 0.132541771).
     Khong cau `CL-*` nao bi mat neu bo B9.
```

Ba dieu BAT BUOC voi moi `B8*`:

```text
1. `n_eff` DEM THEO BLOCK (`block_id.nunique()`), y het C3.
   Dem theo hang la cho B8 mot loi the KHONG CONG BANG.
2. Moi bien the TU SINH `q_hat` cua rieng no.
   CAM muon `q_hat` cua C3 -- cai bay `A066` muc 3 da tu choi mot lan cho B2.
3. Chay tren CUNG split calib/test, CUNG block, CUNG hat giong (CRN).
```

## 6. Tam phep do va dai da ky

Moi dai duoi day duoc ky TRUOC khi nhin bat ky so nao cua nhanh do luong.

### `G23-289` / `M-225` -- KIEM WIRING (chay TRUOC TIEN)

```text
Thu tuc : chay duong ong B8 nhung thay ham q_hat bang DUNG `_qhat` cua
          `config_matrix`.
Dai     : `viol|accept` va `acceptance` trung C3 BIT-FOR-BIT.
Nhan    : NC duong. FAIL -> DUNG lesson, sua wiring, khong cham diem tiep.
```

### `G23-290` / `NC-23.23-1` -- DOI CHUNG AM (chay THU HAI)

```text
Thu tuc : giu nguyen C3 (da biet la hop le). Xao ngau nhien nhan `z_bin`,
          giu nguyen phan phoi score. 200 lan rut tham.
Do      : phan bo cua `viol|accept`, va p95 cua no.
Dai     : dai tuyen "VO" o `G23-291`/`G23-292` phai nam NGOAI p95 cua phan
          bo nay.
Nhan    : chan. Neu dai tuyen "VO" nam TRONG phan bo -> DUNG, ky lai dai,
          KHONG chay nhanh chinh.
```

Ly do ton tai: `L99`, `L101`, `L119` -- ba lan lien tiep cung mot hinh dang.

### `G23-291` / `M-226` -- B8b VO BAO DAM (tru phu)

```text
Do      : `viol|accept` cua B8b tren tap test, muc HO (alpha = 0.10),
          voi acceptance >= ACCEPT_FLOOR = 0.20.
Dai     : CI95 ghep cap cua (viol_B8b - alpha) co CAN DUOI > 0,
          tren >= 3/5 bin tuoi.
          Bao cao them ti so viol_B8b / alpha.

TIEU CHI DOI. `BREAK_TOL = 0.05` tuyet doi (dung o `recalibrate_transfer`)
KHONG duoc dung o day. Do truoc bang mo phong: B8b cho viol muc ho
~0.099--0.140, tuc DUOI nguong 0.15 cua `BREAK_TOL`. Mot nguong khong
the HIT la mot nguong vo nghia -- cung benh `L101`, chieu nguoc lai.
```

### `G23-292` / `M-227` -- CHAN CAU TRUC `CV` (tru chinh)

```text
Do      : `CV(s_j)` cho moi (bin tuoi, slot j), kem CI95 block bootstrap.
Dai     : ton tai >= 1 o co CI95_lo(CV) > 0.755510639762867.
Nhan    : bang chung CAU TRUC. Doc lap voi coverage, doc lap voi mau.
Ghi kem : bat doi xung o muc 4.2 PHAI in canh moi con so.
```

### `G23-293` / `M-228` -- B8a va B8c [MO TA]

```text
Do      : `viol|accept` cua B8a va B8c.
KHONG ky dai HIT/MISS. Ly do da do truoc:
  B8a  hong ngay ca khi H0 DUNG (viol 0.2746 vs 0.0333) -> STRAWMAN,
       chi dung lam thang do khoang cach toi B8b.
  B8c  hieu chinh `+1` qua nho o n = 457 (0.0338 vs 0.0333); o n = 29 thi
       B8c va C3 TRUNG KHIT (ca hai lay max mau).
Tien le ha nhan: Amendment 23-23 (`A-7'`/`A-8'`).
```

### `G23-294` / `M-229` -- B8d block bootstrap

```text
Do      : `viol|accept` cua B8d.
Dai     : |viol_B8d - viol_C3| <= 0.02 tren >= 4/5 bin.
Nghia   : neu DAT -> bootstrap va conformal khong phan biet duoc o n nay;
          dong gop cua conformal nam o CO CHE TU CHOI (M-230), khong o
          do rong khoang. Do la mot ket qua, khong phai that bai.
```

### `G23-295` / `M-230` -- CO CHE TU CHOI (tru chinh)

```text
Do      : dem so o (bin x cell) ma
             C3 tra q_hat = +inf
                (vi ceil((n+1)(1-alpha_each)) > n_eff)
             B8* tra mot so HUU HAN
Dai     : ton tai >= 1 o nhu vay.
Ghi kem : DAY LA HE QUA THIET KE cua `conformal_level`, KHONG phai mot phat
          hien thuc nghiem. Moi phat bieu ve `CL-13` phai in cau nay.
          Tien le: `CL-10` (`M-202` khong duoc trich dan nhu xac nhan mu).
Nguong  : n_eff toi thieu = 29 block voi alpha_each = 0.0333
          (`conformal_min_blocks`, `L91`).
```

### `G23-296` / `M-231` -- B7 so voi B3

```text
Do      : `err|accept` cua B7 va cua B3, tai CUNG acceptance,
          tren luoi acceptance (0.70, 0.50, 0.30, 0.20).
Dai     : |err_B7 - err_B3| > 0.01 tai >= 2/4 muc,
          HOAC accept_overlap(B7,B3).jaccard < 0.85.
Nghia   : neu KHONG dat, B7 la B3 duoc dat ten khac -- lap lai dung hien
          tuong `B4 == B3` (Amendment 23-13). Phai ghi thang nhu vay va
          KHONG duoc dem B7 nhu mot baseline doc lap trong paper.
```

## 7. Ba kich ban ket qua -- ket luan tuong ung, ky TRUOC

```text
K1  M-227 FIRE va M-226 DAT
    -> CL-12 dung o dang MANH. Gaussian bi bac bo bang ca hai duong:
       cau truc va coverage.

K2  M-227 FIRE nhung M-226 KHONG dat
    -> CL-12 dung o dang CAU TRUC. Phat bieu: "khong ton tai Gaussian nao
       khop du lieu; do rong khoang thi hai ben khong phan biet duoc o
       n nay". Dong gop chuyen trong so sang CL-13.

K3  M-227 KHONG fire va M-226 KHONG dat
    -> CL-12 KHONG duoc phat bieu. Ghi thang: "o che do van hanh nay,
       mot khoang Gaussian dung can than DU". Dong gop cua Lesson 23.23
       thu gon con CL-13 + W9 (baseline co nguon).
       Day KHONG phai that bai: no tra loi duoc cau hoi "khi nao thi CAN
       conformal", va cau tra loi la "o o thua, khong o o day".
```

Ba kich ban deu cho mot doan viet duoc. Khong kich ban nao duoc phep bi
dien giai lai sau khi nhin so.

## 8. Pham vi va gioi han cua chinh amendment nay

```text
N1  Cac con so mo phong o muc 4.1, 6 (`0.2746`, `0.0338`, `0.099--0.140`...)
    do tren DU LIEU GIA co hinh dang gia dinh giong score that. Chung dung
    de DAT DAI, KHONG phai du doan ket qua that. Doc 50 phai ghi ro cho nay.

N2  Hai hieu chinh steel-man (Student-t va sqrt(1+1/n)) chinh xac cho khoang
    du doan MOT PHIA tren `d`. Ap chung cho bai toan folded (`|d|`) la mot
    XAP XI. Ta chap nhan vi no luon lam `q_hat` RONG RA, tuc luon co loi cho
    doi thu. Phai khai trong Threats to Validity.

N3  MoM duoc chon thay MLE vi no XAC DINH va tai lap bit-exact. MLE cho
    folded normal co the co nhieu diem dung. Neu can, chay MLE nhu mot
    do nhay -- NGOAI ngan sach 8 gate, tuc lesson khac.

N4  `S-A5` trong `BACKLOG.md` tung ghi "LEN LICH 23.23 (M-232)". Ma `S-A5`
    KHONG duoc dinh nghia o bat ky dau trong repo hay trong `PHASE_23_v3.md`;
    cot (b) cua dong do RONG, nen theo `A071` R2 no KHONG duoc mo.
    => GO `S-A5` khoi lich 23.23. Ghi `L124`. `M-232` KHONG duoc cap.
```

## 9. Gate cau truc (khong do luong)

| Test | Noi dung |
|---|---|
| `test_k08_matches_analytic` | `CV_MAX_FOLDED == sqrt(pi/2 - 1)` toi 1e-15 |
| `test_folded_roundtrip` | sinh tu `(mu,sigma)` biet truoc -> fit lai, lech <= 1% o n = 2e6 |
| `test_folded_quantile_monotone` | `folded_quantile` tang theo `p` va theo `sigma` |
| `test_b8_neff_counts_blocks` | moi `B8*` goi `block_id.nunique()`, khong goi `len()` |
| `test_b8_does_not_import_c3_qhat` | quet AST: `baselines_lit` khong goi `config_matrix._qhat` ngoai duong wiring |
| `test_bisect_iters_fixed` | so vong bisection la HANG SO, khong phai dieu kien dung |

## 10. Xac minh nguon B7 truoc khi ky

Da doc ban WiOpt 2019 va ban mo rong IEEE/ACM ToN 2021 truoc khi ky. Ba diem
duoc nguon ho tro:

```text
1. Bai toan goc toi uu chinh sach LAY MAU de giam MSE uoc luong tu xa.
2. Tin hieu la OU/Gauss-Markov, truyen qua FIFO voi service time i.i.d.
3. Nghiem co cau truc nguong; tham so nguong duoc giai bang bisection.
   Ket qua xet ca truong hop co va khong co rang buoc toc do lay mau.
```

Vi vay B7 duoc GIU, nhung chi voi ba canh bao chuyen mien o muc 5. Khong duoc
viet nhu the Ornee & Sun da chung minh toi uu cho quyet dinh tin/tu choi cua
twin trong repo nay.
