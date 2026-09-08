# PRE-REGISTRATION -- Phase T2
# Thoi gian tuong quan cua tai nhu mot TRUC, va bao dam chung nhan theo tau

```text
Ngay ky      : ____________          <- DE TRONG. Xem muc "TRANG THAI".
Nguoi ky     : ____________
Tag du kien  : phase-T2-prereg-signed
Commit khi ky: ____________
SHA256 file  : ____________          <- tinh SAU khi dien xong, TRUOC khi tag
```

> **TRANG THAI: BAN THAO -- CHUA KY, CHUA CO HIEU LUC.**
>
> Con lai chua dien:
>   - QD-2 `lift_min`               (nguong dinh nghia tau*)
>   - QD-7 k va san cua cua so bang (quy tac loai o da co tieu chi do duoc)
>   (T2-5: D-T2.6-2 co cua so do duoc; -3 da khai pham vi doc duoc;
>    -4 da doi sang tieu chi khong thu nguyen -- ca ba KHONG con o trong)
>   (T2-4 ngan sach CPU: DA DIEN -- 0.53 gio, do duoc)
>   - T2-7 thoi han kill clause
>
> T2-5 DA GO CHAN o T2.5b: du doan gio suy tu artifact 22.6 da commit qua
> `tools/t2_1_prediction.py`, va muc T2-5 TRO VAO artifact thay vi chep so.
> Cai con thieu khong phai du doan ma la NGUONG PHAN QUYET quanh chung.
>
> KHONG chay bat ky o nao cua T2.6 truoc khi file nay duoc ky, commit, tag
> va push. Hieu luc den tu dau vet, khong den tu file markdown.

Tien de: Phase 22 dong tai lesson 22.6 (7/7 gate tren cell poisson@0.925).
Phase T2.0 va T2.2 da dong, xem muc T2-0 va T2-2.

Tai lieu bat buoc doc kem:

```text
docs/GLOSSARY.md                                so dang ky estimand
docs/phase-21/00-preregistration.md   muc P4b    dinh nghia u va sigma_z
docs/phase-21R/00-preregistration.md  muc R9     tau_load khac tau_core
docs/phase-21/99-erratum.md           muc E4     14.35 s khong mau thuan
docs/phase-L2/00-mechanism-gap-audit.md          S37, va F2 (cbr phang)
docs/phase-G/76-amendment-G-A020-omega-reduction.md   truc omega da rut
```

## Cau hoi cua phase

Phase 22.6 da do `ratio(tau)` tren nam diem va thay duong cong CO DINH.
Nhung moi phep quet tau tu truoc den nay deu giu `z/tau` co dinh. Phase T2
hoi mot cau khac:

```text
Trong trien khai that -- noi `z` do CHU KY DONG BO quyet dinh va KHONG co
gian theo tau -- thang thoi gian cua tai anh huong the nao den bao dam cua
lop chung nhan?
```

Ket qua chinh khong phai mot `tau*` don le. Ket qua chinh la duong
`err(tau)` o che do `z` co dinh, kem doi chung noi voi che do `z/tau` co dinh.

---

## Input da khoa (sha256)

```text
650b427fce13c48f9b965e266a31b43125bc481ce12a63489897917739b6d693
    results/RAW/phase-T2/golden/ar1_tau1.0_poisson_0.925_s101.json
    (DIGEST cua mang, khong phai mang: .gitignore:64 bo qua results/**/*
     tru *.json, va mang 200k x 8 float64 la 12.8 MB. Digest van cho doi
     chung BIT-EXACT va chay duoc tren CLONE SACH.
     sha256 cua mang: dbe26ba7b115ff67e126f2ba8faec1bc806ad5e040a7183e0e7a71641db9cba8)
0387d300dbdd039c004a7fc89d062a0e9219968be8ad0cfeac65e53cf34826db
    results/LIVE/phase-20R/sla_calibration.json
5260b8f8aabb59ca81e2af1168bbbc98a7dfd804aa0506a266d0b34fac5d927e
    results/LIVE/phase-20R/truth_table.parquet
```

Ban vang la doi chung hoi quy bit-exact (NC-T2-1). Sinh lai no bang code moi
la XOA doi chung, khong phai sua test. Hash duoc ghim trong
`test/test_t2_bit_exact.py`.

---

## Ke thua -- khong hieu chuan lai

```text
sigma_rho, w_loss, nguong SLA   <- 20R sla_calibration.json, GIU NGUYEN
truth table                     <- 20R truth_table.parquet, GIU NGUYEN
TAU_CORE_MEASURED_S = 2.87 s    <- do duoc tren trace v7, KHONG dat lai
Z_EDGES / U_EDGES               <- Phase 21 P4b/P5, GIU NGUYEN
```

---

## T2-0  KIEM TOAN TIEN DE  [DA DONG]

Sau phat hien, moi so tai dan tu artifact bang `tools/t2_0_tau_audit.py`:

```text
F1  tau_load=1.0 (thiet ke) khac tau_core=2.87 (do duoc). DA GHI o R9/E4.
    Trong toan repo chi co DUNG HAI gia tri tau that; ba "gia tri" khac
    la duong tinh gia cua grep theo ten (ti so, so chu ky, chu trong comment).
F2  cert/tau_sweep.py DA co truc tau: TAU_GRID, block_len = 5*tau/dt.
F3  22.6 do ratio(tau) 5 diem, hump-shaped o CA BON cell.
    Bo gate 7/7 la P12-P16+S2+S3, cham tren MOT cell (poisson@0.925).
    Ba cell con lai co fail rieng trong bo 11 gate cua artifact:
      cbr@0.700     8/11    h2@0.700  10/11    poisson@0.850  10/11
F4  20R quet tau nhung GIU z/tau CO DINH  => err(tau) "gan phang" (+4.5%)
    la TAUTOLOGY. sigma_z chi phu thuoc z/tau nen bat bien theo dinh nghia.
    DAY LA KHOANG TRONG THAT MA T2 PHAI LAP.
F5  Ngan sach block vo o tau=28 (7 block/seed < 9). n = max(2e5, 50*tau/dt).
F6  Hai quy uoc estimand cung ton tai va DEU DUNG:
      convA sqrt(1-exp(-2z/tau))  bien DIEU KIEN u   [tien dang ky P4b]
      convB sqrt(1-exp(-z/tau))   hoi quy SAI SO     [khop e_stale cua 20R]
    Quan he: convA(tau) == convB(tau/2). Hai truc tau KHONG so sanh truc tiep.
```

## T2-2  HA TANG  [DA DONG, 8/9 gate]

```text
tau la THAM SO BAT BUOC        khong con lenh gan DEFAULT_TAU nao
n_for_tau(tau, dt)             giu T_sim >= 50*tau  => >= 10 block/seed
block_s_for_tau(tau) = 5*tau   kenh (c) da noi
--tau, --z-mode                REQUIRED, khong co mac dinh im lang
docs/GLOSSARY.md               so dang ky estimand, 6 muc
NC-T2-1 bit-exact              PASS
```

Gate con mo: T2.2-9 (QD-1 duoi day) -- dong bang chinh file nay.

---

## SAU QUYET DINH -- chot, khong sua sau khi thay ket qua

### QD-1  Bien dieu kien `u`  [DA CHOT -- dong T2.2-9]

`u` hien dung tu so KHONG co dieu kien voi mau so CO DIEU KIEN, tuc bo qua
hoi quy ve trung binh `(1-phi_z)*|rho_hat-mu|`, voi `phi_z = exp(-z/tau)`.
Do lon phan bi bo qua:

```text
z/tau = 0.05  ->  phi_z = 0.951  ->  bo qua  4.9%
z/tau = 0.19  ->  phi_z = 0.827  ->  bo qua 17%     (vung Phase 21 chay)
z/tau = 1.00  ->  phi_z = 0.368  ->  bo qua 63%
z/tau = 2.50  ->  phi_z = 0.082  ->  bo qua 92%
```

CHOT phuong an (3):

```text
- nhanh CHINH giu `u` cu          => bao toan doi chung hoi quy Phase 21
- them `u_cond` = |mu + phi_z(rho_hat-mu) - nguong| / sigma_z  lam nhanh
  NHAY CAM, chay song song
- BAO CAO ca hai. Chenh lech coverage la DU LIEU, khong phai loi.
```

Ly do khong sua thang: Mondrian conformal HOP LE voi moi ham chia bin do
duoc, mien la chon TRUOC khi nhin diem hieu chuan. `u` sai chi lam bin KEM
HIEU QUA (khoang rong hon), KHONG lam mat bao dam bao phu. Day la van de
SUC MANH, khong phai DUNG SAI.

NGUONG BAO CAO: neu `|cov(u) - cov(u_cond)| > 0.02` o bat ky o nao
=> ghi thanh gioi han, KHONG doi nhanh chinh giua chung.

### QD-2  `lift_min` -- nguong dinh nghia tau*    [★ CHUA KY -- CHU REPO DIEN]

```text
tau*     = inf { tau : lift(tau) < lift_min }
lift(tau) = (err_baseline - err_certified) / err_baseline
```

```text
CHOT: lift_min = ____________
LY DO (phai viet TRUOC khi chay, khong phai sau): ______________________
_______________________________________________________________________
```

> Day la nguong DUY NHAT trong phase nay anh huong truc tiep den ket qua
> chinh. No phu thuoc chi phi van hanh cua abstain trong he cua chu repo --
> mot dai luong khong suy ra duoc tu repo.
>
> KHUYEN NGHI: neu khong bien minh duoc MOT con so, dung chon mot con so.
> Thay bang: bao cao `tau*(lift_min)` cho `lift_min in {0.05, 0.10, 0.20}`
> nhu MOT DUONG. Mot duong ben hon mot diem, va no khong yeu cau mot quyet
> dinh khong co can cu.

### QD-3  O nao bi loai, va vi sao  [DA CHOT]

```text
LOAI  moi o bi realizability_gate tu choi          [dinh nghia o T2.4]
LOAI  mode = cbr
      CO CHE: S37 -- delay(rho) phang tren cbr, twin khong the sai.
      DO DUOC 22.6: A trong [9.957e-05, 9.975e-05]; ratio ~ 1.00 moi tau.
      => o nay KHONG co gi de chung nhan. Ghi vao Threats, KHONG debug.
      GIU lam DOI CHUNG AM: cbr phai tiep tuc cho ratio ~ 1.
GIU   moi o khac, KE CA o cho ket qua xau.
```

Ranh gioi cherry-picking: ly do loai `cbr` den tu du lieu 22.6 DA CONG BO va
tu mot co che DA PHAT BIEU TRUOC (S37), khong tu du lieu T2.6 chua chay. Loai
mot o vi co che da biet la HOP LE; loai no vi no lam duong cong xau la KHONG.
Phan biet nam o cho: quyet dinh duoc ky truoc hay sau khi nhin du lieu MOI.

KHONG duoc them tieu chi loai sau khi nhin du lieu T2.6.

### QD-4  Gate V-T2-2 tren `tau_hat`  [DA CHOT -- sua tu ban cu]

Gate cu `|tau_hat - tau_thiet_ke| / tau < 15%` tren MOT chuoi la gate HONG.
Do duoc (MC tren AR(1) thuan, 8 link x 60 rep):

```text
chu ky = T_sim/tau     E[tau_hat]/tau     sd cua MOT chuoi
   1000                    0.9971               4.6%
    200                    0.9878               9.9%
     50                    0.9400              18.5%
```

O 50 chu ky, mot chuoi HOP LE truot nguong 15% voi xac suat 44%, thuan do
may rui. Day dung la truong hop `INSUFFICIENT_POWER` cua NT 56: mot phep so
nhieu hon nguong phan quyet thi khong duoc doc theo ca hai chieu.

```text
GATE MOI:  | mean(tau_hat) - E[tau_hat | tau, n, dt] |  <=  3 * se
           mean tren n_seed * n_link chuoi;  se = sd_1chuoi / sqrt(n_seed*n_link)
           E[.] uoc bang Monte-Carlo tren AR(1) THUAN (khong offset, khong kep)
```

Voi 5 seed x 8 link = 40 chuoi: bang 3-sigma = +/-2.2% (1000 chu ky),
+/-4.7% (200), +/-8.8% (50).

Da cai dat: `test/test_t2_tau_hat_expectation.py`.

### QD-5  Moi so bao cao phai kem `n` va bat dinh  [DA CHOT]

Bai hoc T2.2: mot bang "do chech" tung duoc doc tu `n=1`, va ca ba so nam
trong 1.1 sigma cua nhieu. Tu mot lan rut KHONG THE tach bias khoi noise.

```text
CAM: viet mot con so do duoc ma khong kem n va don vi bat dinh.
     "tau_hat = 0.81*tau"                                 -> VO NGHIA
     "tau_hat = 0.81*tau (n=1, sd mot chuoi 18.5%)"       -> DUNG
Moi khoang tin cay dung BIEN THIEN GIUA SEED (Student-t), khong dung so mau
trong mot lan chay. Ke thua ky luat Phase L (00f-amendment-5 muc A5-2).
```

### QD-6  Nhan du doan  [DA CHOT -- tranh va cham]

Nhan `D-T2` DA DUOC DUNG o `docs/phase-T/00-preregistration.md:225` cho mot
du doan khac han (`err_qs -> 0` khi `Lambda -> infinity`). Du doan cua phase
nay dung tien to `D-T2.6-*`. Day la lan thu NAM trong mach nay mot ky hieu
suyt gánh hai dai luong; xem `docs/GLOSSARY.md`.

---

### QD-7  Cua so bang kha thi va o suy bien   [CHUA KY -- CHU REPO KY]

Mot bang chap nhan +/-b phai nam trong CUA SO:

```text
    b >= k*se        SAN   -- hep hon nhieu => gate la tung xu
    b <  |effect|    TRAN  -- rong hon hieu ung => du doan KHONG THE SAI
    cua so rong => INSUFFICIENT_POWER, khong doc theo CA HAI chieu (NT 56)
```

```text
CHOT  k    = ______        (goi y 3; 2 neu chap nhan rui ro cao hon)
CHOT  san  = ______        (goi y 0.05)
```

`se` uoc tu bien thien GIUA SEED cua 20R legacy (KHONG tu so mau trong mot
lan chay). Nguon + hash o `docs/phase-T2/02-band-window.json`.

CANH BAO: `sd` uoc tu n=3 seed => dof=2. Bat dinh cua CHINH bang nay lon.
Phai do lai o DIEM CANH cua T2.6 va viet amendment neu lech qua 50 phan tram.

#### Quy tac loai o suy bien -- TIEU CHI DO DUOC, khong phai danh sach o

```text
LOAI neu  err_baseline < 0.01   HOAC   A < 0.01
```

Ap vao du lieu da commit (20R + 22.6), quy tac cho:

```text
LOAI  cbr (moi rho_bar)   err = 0.00000, A ~ 9.97e-05   co che S37
LOAI  h2@0.960            err = 0.00171                 sigma_max -> 0
GIU   poisson@0.960       err = 0.23132                 O SONG
```

CHU Y: `rho_bar = 0.96` KHONG dong nhat. Mot de xuat dau vao muon loai
`rho_bar=0.96` o MOI mode; lam vay se vut bo `poisson@0.960` von khoe
(err = 0.231, gap 135 lan nguong). Day chinh la ly do quy tac phai chay
tren SO chu khong tren TEN O: mot danh sach o viet tay thi sai, mot tieu
chi do duoc thi dung.

## T2-4  THIET KE T2.6 -- HAI NHANH

```text
NHANH A "co che"      --z-mode scaled    z/tau in {0.10, 0.30, 0.55, 1.00}
    MUC DICH: tai tao 22.6 / 20R legacy => doi chung noi phase
    KHONG dung lam ket qua chinh.

NHANH B "van hanh"    --z-mode fixed     z in {0.05, 0.10, 0.30, 0.55} s
    (BON muc nay deu nam trong Z_ALL cua harness -- decision_error_v2.py:52.
     Ban cu {0.05,0.15,0.30,0.50} co HAI muc khong ton tai trong harness,
     nen hai du doan se la NOT_EVALUATED chu khong phai FAIL. Sua TRUOC khi ky.)
    MUC DICH: ★ KET QUA CHINH. z do chu ky dong bo quyet dinh
    (DEFAULT_SYNC_PERIOD_S = 0.5 s), KHONG co gian theo tau.
    z/tau di tu 1.10 (tau=0.5, z=0.55) xuong 0.0018 (tau=28, z=0.05)
    -- 616 lan. (So cu "1.00 ... 0.025, 40 lan" tinh tren luoi z cu va
     tren tau=20; sua theo luoi da dong bo voi harness.)
```

DOI CHUNG NOI: tai `(tau=1.0, z=0.10)` hai nhanh PHAI trung trong 1%.
[DA XAC NHAN o T2.2: ca hai che do deu chua diem do; giao cua hai luoi z
tai tau=1.0 la {0.1, 0.3, 0.55, 1.0}]

```text
LUOI   rho_bar in {0.70, 0.85, 0.925, 0.96}          [RHO_BAR_GRID]
       tau     in {0.5, 1, 2, 3, 5, 10, 20, 28}
       (tau=0.5 la mau so cua D-T2.6-2; bo sung TRUOC khi ky, khong phai
        amendment. Qua realizability_gate: 400 block/seed.)
       a       in {0.5, 0.9}   (sigma = a * sigma_max_regime)
       mode    in {poisson, h2}          (cbr loai theo QD-3)
       omega   = 0 co dinh, ghi sigma_eff_proxy       [G-A020 da rut truc omega]
       seed    in {101, 102, 103, 104, 105}
n       = n_for_tau(tau, dt)      [T2.2]
block_s = 5 * tau                 [T2.2]
dt      = 0.005                   [khoa tu 20R]
```

```text
NGAN SACH CPU: 0.53 gio (~32 phut)   <- DO DUOC, khong doan
  don vi   : mot lenh = 1 tau x 1 seed x 10 o x 9 muc z
  do duoc  : tau=1.0 -> 11.81 s | tau=5.0 -> 11.29 s | tau=28 -> 15.28 s
             (scaled 9.37 s; a=0.5 11.10 s -- bien the < 20 phan tram)
  suy ra   : 8 tau x 5 seed x 2 nhanh x 2 muc a = 160 lenh ~ 1920 s
NEU > 8 gio => FRACTIONAL DESIGN: toan phan tren (tau, rho_bar); a va mode
lay 2 muc. GHI O DAY, khong cat sau khi nhin so.
=> 0.53 < 8 gio: quy tac da ky tu giai quyet. CHAY TOAN PHAN, khong cat luoi.
THU TU CHAY: ngau nhien toan phan, seed thu tu 7200
DIEM CANH  : moi 30 o, chay lai (poisson, rho_bar=0.925, a=0.9, tau=3, seed 999)
```

> Uoc ngan sach TRUOC la mot rang buoc chong cherry-picking, khong phai thu
> tuc: uoc sau khi nhin so se cat luoi o cho thuan tien.

---

## T2-5  BANG DU DOAN KY TRUOC     [DA GO CHAN -- BANG CHAP NHAN CHUA KY]

```text
Nguon    docs/phase-T2/01-prediction-signed.json
sha256   68e975c2c08247e208cabc29f6e7f7710eeb01e46ba8018be0d9fda885608d7f
Script   tools/t2_1_prediction.py     (CHI DOC; khong fit lai)
Suy tu   results/SUPERSEDED/phase-22/tau_sweep_{poisson_0.925,poisson_0.850,
         h2_0.700,cbr_0.700}.json      [DA DO o 22.6, hash trong artifact]
```

Muc nay TRO VAO artifact, KHONG chep so. Ly do: neu ai do sua nen 22.6, hash
lech va ta biet ngay du doan dang dua tren nen da doi. Chep so vao day se
lam mat dau vet do.

Luat duoc ap (quy uoc HIEU, khop e_stale cua 20R -- xem docs/GLOSSARY.md):

```text
rms_total(z, tau) = sqrt( em^2 + c*A^2 * (1 - exp(-z/tau)) )
A, c, em  = trung binh tren luoi tau cua 22.6 (chung doc lap voi tau,
            gate G22_11/S3). KHONG fit lai.
```

DOI CHUNG NOI cua script: tai tao `ratio_pred_finite` cua chinh 22.6 tu A,c,em
doc ra. Do duoc: sai lech toi da `4.44e-16` (do chinh xac may) tren ca bon o.
Lech lon hon nghia la doc sai artifact, khong phai phat hien ve mang.

DAI LUONG DUOC DU DOAN la `rms_total`, KHONG phai `err_total`. Luat khong mo
hinh hoa phep bien doi tu rms sang ti le quyet dinh sai, nen voi `err_total`
chi ky duoc THU TU (don dieu), khong ky duoc ti so.

### Du doan -- diem tu artifact, BANG CHAP NHAN phai ky

```text
D-T2.6-1  nhanh B DON DIEU GIAM theo tau, moi o song, moi z
          co so: giai tich (z co dinh, tau tang => 1-exp(-z/tau) giam)
          BANG: khong can bang -- day la mot phat bieu ve THU TU
          DUNG NGAY neu sai: harness sai, z khong thuc su co dinh

D-T2.6-2  rms(tau=28)/rms(tau=0.5) o z co dinh
          diem  : artifact §signed_predictions.D-T2.6-2.per_cell
          mien  : [0.1993, 0.4611] tren ba o song x bon muc z
          BANG CHAP NHAN: theo O, doc tu docs/phase-T2/02-band-window.json
          sha256 ee5bc55c977b96f9f468333437a37f3055adac1de64d88b454eac453c19072a5
          b(o) = max(k*se_seed(o), san).  k va san CHUA KY (xem QD-7).
          Voi k=3, san=0.05 thi cua so cho:
             h2@0.700 0.050 | h2@0.850 0.067 | h2@0.925 0.138
             poisson@0.700 0.072 | @0.850 0.061 | @0.925 0.057 | @0.960 0.050
             h2@0.960  INSUFFICIENT_POWER -- khong doc theo ca hai chieu
          CANH BAO: mot bang PHANG +/-0.03 dung chung la SAI -- no hep hon
          3*se o bon o (toi 3.7 lan o h2@0.925). Cung loai loi voi gate
          |tau_hat-tau|/tau duoi 15 phan tram: dat nguong ma khong nhin do tan.

D-T2.6-3  R(tau) co dinh (hump); vi tri dinh
          diem  : h2@0.700 0.929 s | poisson@0.850 1.428 s | poisson@0.925 1.557 s
          doi chung cheo voi dinh 22.6 tu ghi: lech toi da 0.0213 s
          (khac CO SO: 22.6 dung fit tai tau=1.0, day dung trung binh luoi)

          PHAM VI DOC DUOC -- KHAI TRUOC KHI CHAY:
            san nhieu = lech giua HAI uoc luong doc lap cua cung ti so
                        (ratio_measured vs ratio_measured_sim, 22.6)
            poisson@0.925   bien do/nhieu = 10.9   DOC DUOC
            poisson@0.850   bien do/nhieu =  3.2   YEU
            h2@0.700        bien do/nhieu =  1.1   INSUFFICIENT_POWER
          => vi tri dinh CHI duoc doc o poisson@0.925 (va tam o poisson@0.850).
             O h2@0.700, do tan uoc luong xap xi TOAN BO chieu cao buou, nen
             khong duoc doc theo CA HAI chieu (NT 56). Khai o day de no khong
             tro thanh mot loi bien minh sau khi thay h2 khong khop.

D-T2.6-4  A, c, em doc lap voi tau
          DANG DA DOI -- khong con o trong nao de ky:

              span_GIUA_tau(X)  <  spread_TRONG_tau(X)     X in {A, c, em}

          Doc bang loi: "su phu thuoc vao tau nho hon nhieu uoc luong o tau
          co dinh" -- do chinh la nghia van hanh cua "doc lap voi tau".
          Khong thu nguyen, tu hieu chuan, khong doi mot chu ky nao.

          VI SAO BO BANG "+/-3%": no la mot HANG SO TRAN va vi pham TRAN cua
          cua so kha thi. Do duoc o poisson@0.925:
              span giua-tau = 0.762%   <- |effect|, tuc TRAN
              3*se          = 0.899%   <- SAN (sd ~ spread/2.33, n=5)
              bang de xuat  = 3.000%   <- rong gap 4 lan TRAN
          => cua so [0.899%, 0.762%) RONG. Bang 3% KHONG THE SAI, va siet lai
             cung khong cuu duoc. Mot du doan khong the sai la trang tri.

          DANG MOI CO RANG NGAY: 3/9 FAIL tren du lieu 22.6 da co --
              h2@0.700/em | poisson@0.850/c | poisson@0.850/em
          Ca hai FAIL cua `em` roi vao poisson@0.850, dung o ma gate
          `rms_em_independent_of_tau` cua 22.6 da FAIL (muc F3, rui ro R4).
          Ba duong doc lap cham cung mot cho.

D-T2.6-5  diem giao (tau=1.0, z=0.10) hai nhanh khop trong 1%
          khong can T2.1. DA XAC NHAN ve cau truc o T2.2.
          DUNG NGAY neu sai: hai nhanh chua cung mot luong, loi co hoc

D-T2.6-6  tau_knee (tau nho nhat de rms ve trong 5% cua em)
          diem  : artifact §signed_predictions.D-T2.6-6.per_cell
          mien  : [20.8, 709.1] s
          ★ CHU Y: phan lon tau_knee NAM NGOAI luoi tau (max = 28 s).
          Do la mot du doan hop le: no noi truoc rang T2.6 se KHONG thay
          knee tren luoi. Neu khong thay, ghi "> 28 s (ngoai luoi)" va
          KHONG mo rong luoi de di tim -- xem T2-6(c).

D-T2.6-7  cbr chet o moi tau  (doi chung am, da loai theo QD-3)
          A do duoc = 9.969e-05. Bien do AR(1) gan bang khong.
```

## T2-6  BON NHANH SUA LOI  [dien TRUOC, khong de trong]

```text
(a) nhanh B co dinh (hump)   -> kiem harness TRUOC vat ly: z co that su co
                                dinh khong? in z_values_for(tau, scaled=False).
(b) A/c/em troi > nguong     -> luat vo o tau lon. DO LA KET QUA. Bao cao
                                mien hieu luc cua luat, KHONG ep fit.
(c) tau* khong ton tai       -> ghi "> 28 s (ngoai luoi)". KHONG mo rong luoi
                                de di tim tau*. Do la cherry-picking.
(d) coverage vo o tau lon    -> kiem n_blocks TRUOC. O tau=28, neu n khong
                                scale thi chi con 7 block/seed < 9. Nhieu huu
                                han mau, khong phai vat ly.
```

NGAN SACH: toi da 2 vong, moi vong sua DUNG MOT thu, kem mot amendment danh so.

---

## T2-7  DIEU KIEN DUNG (KILL CLAUSE)     [★ CHUA DIEN -- CHU REPO DAT HAN]

```text
T2.4 gate   : ____ ngay. Qua han => dung can giai tich,
              bound_source = "analytic_pre_T2", di tiep.
T2.6 sweep  : ____ vong.  Qua han => dong INSTRUMENT_LIMIT voi
              TAU_GRID = {1, 3, 10}, ghi gioi han.
Tong T2     : ____ ngay.  Qua han => dong phase voi ket qua da co,
              chuyen phan con lai thanh no.
```

> Kill clause khong co ngay cu the thi khong phai kill clause.

---

## Rui ro da biet

```text
R1  Diem du doan T2-5 DA CO (artifact, hash trong muc do). Con thieu BANG
    CHAP NHAN quanh chung -- van chan T2.6, nhung la mot muc nho hon nhieu.
    Bang phai ky TRUOC khi chay: mot bang ky sau khi nhin so khong con la gate.
R2  `u` bo qua hoi quy ve trung binh, nang o z/tau lon -- dung vung nhanh B
    di vao. Da xu ly bang QD-1 (nhanh nhay cam), khong xu ly bang sua `u`.
R3  Do chech tau_hat khong hang so tren luoi (theo T_sim/tau, khong theo tau).
    Da xu ly bang QD-4 (sua gate), KHONG bang tang n -- tang n de giu chech
    hang so can n ~ tau khong san, tuc 28x compute o tau=28.
R4  Ba trong bon cell cua 22.6 co gate rieng fail (F3). Bo 7/7 chi cham tren
    poisson@0.925. Khong duoc trich "22.6 PASS toan bo".
R5  Kep AR(1) < 0.09% moi o da do; khong phai rui ro, nhung van phai ghi
    `clip_fraction` vao moi artifact (co san tu 20R).
```

---

## Doi chung bat buoc

```text
NC-T2-1  bit-exact tai tau=1.0 voi ban vang        [PASS, test da ghim hash]
NC-T2-2  doi chung noi (tau=1.0, z=0.10) hai nhanh trung trong 1%
NC-T2-3  cbr cho ratio ~ 1 o moi tau               [doi chung AM]
NC-T2-4  diem canh lap lai moi 30 o, trung trong sai so lay mau
```

---

## T2-8  CHU KY

```text
Toi xac nhan da dien QD-2, T2-4 (ngan sach), T2-5 (bang du doan) va T2-7
TRUOC khi chay bat ky o nao cua T2.6.

Ky: ______________   Ngay: __________
SHA256 cua file nay sau khi dien: ______________
```

Quy trinh lam file nay co hieu luc:

```bash
git add docs/phase-T2/00-preregistration.md
git commit -m "prereg(T2): freeze design, thresholds and signed predictions"
git tag phase-T2-prereg-signed
git push origin phase-T2-prereg-signed
sha256sum docs/phase-T2/00-preregistration.md
```

Amendment protocol: file nay duoc phep doi, nhung moi thay doi phai la mot
amendment danh so ghi ro DOI GI, VI SAO, va DA NHIN THAY DU LIEU NAO khi
quyet dinh. Cai lam no trung thuc la DAU VET, khong phai su bat bien.
