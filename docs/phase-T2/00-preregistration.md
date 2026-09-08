# PRE-REGISTRATION -- Phase T2
# Thoi gian tuong quan cua tai nhu mot TRUC, va bao dam chung nhan theo tau

```text
Tag du kien  : phase-T2-prereg-signed
Ngay ky      : xem `git log -1 --format=%cI phase-T2-prereg-signed`
Nguoi ky     : xem muc T2-8 (dien tay) va tac gia cua tag annotated
```

> **TRANG THAI: DA KY -- CO HIEU LUC TU TAG `phase-T2-prereg-signed`.**
>
> Bon muc tung de trong DA DIEN XONG:
>   QD-2 `lift_min`  -> DUONG {0.05, 0.10, 0.20}, khong phai mot diem
>   QD-7 k = 3.0, san = 0.05  (nhat quan voi 02-band-window.json)
>   T2-4 ngan sach CPU -> 0.53 gio, 160 lenh (do duoc)
>   T2-7 kill clause -> 2 ngay / 2 vong / 8 ngay, kem no N-T2-1..4
>   (T2-5: D-T2.6-2/-3/-4 deu KHONG con o trong; tro vao artifact)
>
> CON LAI DUNG MOT VIEC: chu repo dien hai dong `Ky` va `Ngay` o muc T2-8,
> commit, tao tag ANNOTATED `phase-T2-prereg-signed`, va PUSH ca hai.
> Chi khi do trang thai moi la DA KY.
>
> KHONG dat trang thai thanh "DA KY" khi hai dong chu ky con trong: mot
> tai lieu tu khai da ky ma khong co tag la mot LOI CUSTODY THAT, dung
> nhu test/test_closure_tags_exist.py ghi.
>
> T2-5 DA GO CHAN o T2.5b: du doan gio suy tu artifact 22.6 da commit qua
> `tools/t2_1_prediction.py`, va muc T2-5 TRO VAO artifact thay vi chep so.
>
> KHONG chay bat ky o nao cua T2.6 truoc khi file nay duoc ky, commit, tag
> VA PUSH. Hieu luc den tu dau vet, khong den tu file markdown -- mot tag
> chua push la mot ghi chu ca nhan, khong phai mot dau vet.

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

CACH DOC NGUONG DO (chot TRUOC khi chay):

```text
(a) Day la nguong BAO CAO, KHONG phai nguong PASS/FAIL. Vuot 0.02 KHONG
    lam phase FAIL; no kich hoat mot NGHIA VU VIET o Threats to Validity.
    NT 56: tach gate TINH HOP LE khoi gate KET QUA.

(b) "o BAT KY o nao" = lay MAX tren cac o, KHONG lay trung binh. Trung binh
    pha loang mot o lech manh vao nhieu o lech nhe. Phai kem TEN O dat max
    (cung nguyen tac voi `_span_driver`: mot so bat thuong phai chi ra o
    nao sinh ra no).

(c) CHI so sanh tren o ma CA HAI nhanh deu READABLE (q_hat huu han VA
    n_blocks >= ceil(1/alpha)-1 o ca hai). O readable ben nay nhung khong
    ben kia thi hieu so VO NGHIA -- vi cov = 1.0 o do la theo DINH NGHIA,
    khong theo phep do. Truong hop do la MOT KET QUA rieng, bao cao dang
    DEM, khong nhet vao phep tru.

(d) KHONG doi nhanh chinh giua chung, ke ca khi u_cond dep hon. `u_cond`
    duoc chon SAU khi nhin du lieu thi moi bao dam conformal cua no mat
    hieu luc (dieu kien "taxonomy co dinh TRUOC hieu chuan" bi pha).
```

BA SO PHAI BAO CAO:

```text
QD1-R1  max_o |cov(u) - cov(u_cond)|  + TEN O          [nguong 0.02]
QD1-R2  n_degenerate(u)  vs  n_degenerate(u_cond)      [DEM, khong tru]
QD1-R3  mean q_hat(u) vs mean q_hat(u_cond) tren o readable
        ★ day la so do HIEU QUA: coverage bang nhau ma khoang HEP hon
          la efficiency gain duoi validity khong doi.
```

!! DINH CHINH PHAM VI CUA BANG TREN (do duoc, sua TRUOC khi ky):

```text
Bang z/tau o dau muc nay tinh voi tau = tau_LOAD. Nhung duong chung nhan
that su (cert/build_calib_set.py -> cert/conformal_age.py) KHONG dung
tau_load o bat ky dau:
    z    <- sawtooth_age_steps(), tuc CHU KY DONG BO 0.5 s
    phi_z <- exp(-z / TAU_CORE_MEASURED_S) voi tau_core = 2.87 CO DINH
Ca hai deu doc lap voi tau_load => QUET TRUC TAU CUA T2 KHONG LAM DOI
phan bi bo qua o day, du mot chut.

DO DUOC tren results/PENDING/phase-T2/calib_p0925_tau10.parquet (5 seed):
    z_s   in [0.055, 0.550] s  =>  z/tau_core in [0.019, 0.192]
    phi_z in [0.826, 0.981]    =>  phan BO QUA in [1.9%, 17.4%]

=> Hai hang "1.00 -> 63%" va "2.50 -> 92%" KHONG voi toi duoc tren duong
   chung nhan. Chung mo ta nhanh B cua measurements/decision_error_v2.py,
   la mot duong code KHAC va khong tinh `u` bao gio.
   Tran that cua hieu ung nay la ~17%, khong phai ~92%. Ghi lai de khong
   ai (ke ca chu repo) doc muc nay thanh mot loi hua manh hon su that.
```

KET QUA DA DO (luot mot, o poisson@0.925, tau_load = 10.0, 5 seed):

```text
Nguon  results/PENDING/phase-T2/conformal_u_main.json
       results/PENDING/phase-T2/conformal_u_cond.json
       (PENDING: "khong dung lam headline" -- chua duoc prereg da ky bao chung)

QD1-R1  max_o |cov(u) - cov(u_cond)| = 0.04401  tai o 402
        => VUOT nguong 0.02  => KICH HOAT nghia vu ghi GIOI HAN.
        Bon o vuot: 402 (0.0440), 2 (0.0275), 202 (0.0237), 201 (0.0206).
QD1-R2  n_degenerate(u) = 0 ; n_degenerate(u_cond) = 0
        (khong o nao co q_hat = inf, nen khong hieu so nao bi nhiem)
QD1-R3  mean q_hat(u) = 24.84 ; mean q_hat(u_cond) = 26.10
        => u_cond RONG hon 5.04%, tuc KEM HIEU QUA HON, KHONG phai hon.

CA HAI nhanh: H3 PASS va H4 PASS (marginal 0.9106 vs 0.9100).
=> Du doan ly thuyet cua QD-1 duoc XAC NHAN o phan VALIDITY: doi taxonomy
   khong lam mat bao dam bao phu. Nhung gia thuyet ngam rang taxonomy
   "dung hon" se HIEU QUA HON thi KHONG duoc xac nhan -- no di NGUOC lai.
   Ghi nguyen, khong dieu chinh: mot ket qua nguoc du doan van la ket qua.

PHAM VI DOC DUOC: mot o song, mot tau_load, mot muc a. KHONG duoc doc
thanh ket luan toan phase. Va vi phi_z doc lap voi tau_load (xem dinh
chinh tren), chay lai o tau_load khac se KHONG doi ba so nay mot cach co
he thong -- chi doi qua dong luc cua chinh chuoi rho.
```

QD1-R4  NHANH THU BA `u_cond_load` -- tach CONFOUND cua tau sai dac ta

```text
THU TU THOI GIAN (ghi de nguoi doc tu danh gia, khong de bien minh):
  1. Chay hai nhanh, thay QD1-R3 = +5.04% (u_cond RONG hon).
  2. SAU DO moi hinh thanh gia thuyet: u_cond dang hieu chinh bang SAI tau.
     Dong co la mot CO CHE tinh duoc bang giay but, khong phai mot so
     khong vua y: o z=0.55, tau_core=2.87 co ve trung binh QUA TAY 3.26
     lan so voi tau_load=10, va sigma_z lon hon 1.75 lan.
  3. Them nhanh thu ba, KHONG thay nhanh chinh. `u` van la nhanh chinh
     bat ke ket qua. Prereg CHUA KY nen day la THIET KE, khong phai
     amendment -- nhung thu tu van phai ghi.

`u_cond_load` la ORACLE: no dung tau THIET KE cua trace tong hop, thu ma
mot he trien khai that KHONG BIET. No do CAN TREN cua hieu chinh, khong
phai mot phuong phap dung duoc. Ban dung duoc phai uoc luong tau_hat --
va T2 DA co estimand do, da ky o QD-4.

KET QUA (poisson@0.925, tau_load=10, 5 seed, alpha=0.10):

  (A) DUOI U_EDGES DA TIEN DANG KY -- day la cau hoi DA KY:
        nhanh              mean q_hat    vs u     H3   H4  n_degen
        u                     24.8424   +0.00%  PASS PASS       0
        u_cond(2.87)          26.0953   +5.04%  PASS PASS       0
        u_cond_load(10)       27.2562   +9.72%  PASS PASS       0
      => CA HAI nhanh hieu chinh deu KEM HIEU QUA HON. Sua tau lam
         TE HON, khong phai tot hon. QD1-R3 DUNG, va manh hon vi co ba
         nhanh thay vi hai.

  (B) CHAN DOAN, bin theo PHAN VI (tach THANG DO khoi THU TU):
        u                     23.4750   +0.00%
        u_cond(2.87)          23.5271   +0.22%
        u_cond_load(10)       23.2066   -1.14%   <- HEP hon
      eta2 (do chat luong phan tang, phan vi, 5 seed):
        u 0.06601 | u_cond(2.87) 0.06171 | u_cond_load(10) 0.06849
        hieu ghep cap (u_cond_load - u) = +0.00248, cung dau 5/5 seed,
        4.9 sigma.

GIAI THICH -- hai ket qua tren KHONG mau thuan:
  Hieu chinh hoi quy ve trung binh voi DUNG tau THAT SU cai thien THU TU
  cua do kho (eta2 tang, q_hat giam 1.14% khi thang do bi loai bo).
  NHUNG no dong thoi doi THANG DO cua u: sigma_z(tau_load) nho hon
  sigma_z(tau_core) 1.75 lan, nen u_cond_load bi thoi to va 81.4% so hang
  don vao bin CAO NHAT cua U_EDGES (so voi 65.3% cua `u`).
  U_EDGES = (0,1,2,3,inf) la mot taxonomy PHU THUOC THANG DO, va no duoc
  dinh ra cho thang do cua `u`. Loi tu thang do LON HON lai tu thu tu.

KET LUAN CHO T2 (nhu da tien dang ky):
  `u` van la nhanh chinh, va no vua HOP LE vua HIEU QUA HON hai nhanh kia.
  Hieu chinh KHONG vo dung -- no KHONG TUONG THICH voi mot taxonomy bien
  CO DINH phu thuoc thang do. Do la mot phat bieu manh hon "hieu chinh
  khong giup", va no chi ra viec phai lam tiep.

NO CHUYEN TIEP (post-hoc, ghi ro): mot taxonomy dua tren HANG (scale-free)
se cho hieu chinh co co hoi tra cong. Gia thuyet nay hinh thanh SAU khi
nhin du lieu, nen KHONG duoc dung cho T2. No la thiet ke ung vien cho
21R2, va phai duoc tien dang ky o do truoc khi chay.
```

TRANG THAI CAI DAT (ghi TRUOC khi ky -- xem N-T2-1 muc T2-7):

```text
DA CO   cot u_cond/u_cond_bin/phi_z o cert/build_calib_set.py; chan doan
        mean_abs_u_minus_u_cond va frac_rows_bin_differs; kiem BIEN THAI
        trong self_check (phi_z -> 1 thi u_cond -> u); test/test_t2_u_cond.py.
CHUA CO ket qua conformal cua hai nhanh.
DAU VAO la trace TONG HOP sinh boi tools/t2_make_synthetic_trace.py.
        KHONG dung results/phase-20/rho_offered_long*.csv: tau cua chung la
        DO DUOC va CO DINH RIENG TUNG LINK (2.441 s o `bc` den 32.00 s o
        `vD` -- docs/phase-20/00f-amendment-5.md muc A5.1), nen KHONG QUET
        DUOC mot TRUC tren chung; va B9/D10 da ky rang truc tau cua T2 chay
        trong TWIN chu khong tren Mininet.
KET QUA nam o results/PENDING/ cho den khi duoc tham dinh -- PENDING theo
        dinh nghia la "khong dung lam headline" (docs/phase-D/01-data-
        classification.md).
```

### QD-2  `lift_min` -- nguong dinh nghia tau*    [DA CHOT]

```text
tau*     = inf { tau : lift(tau) < lift_min }
lift(tau) = (err_baseline - err_certified) / err_baseline
```

```text
CHOT: KHONG chon mot lift_min duy nhat.
      Bao cao tau* nhu MOT DUONG tren  lift_min in {0.05, 0.10, 0.20}.
```

LY DO (viet TRUOC khi chay T2.6):

```text
(1) lift_min ma hoa CHI PHI VAN HANH cua abstain. Dai luong do khong suy
    ra duoc tu repo nay: no thuoc mot he trien khai dang chay, ma Phase 24
    moi cam day. Chon mot con so bay gio la chon mot ket luan bang mot gia
    dinh khong kiem duoc (NT 54: khi mot dai luong chuyen tu DO sang DAT,
    cau hoi nghien cuu phai doi theo).

(2) BANG CHUNG THUC NGHIEM cho luat nay, do trong CHINH phase nay: o T2.5c
    viec chon SAI mot tham so (tau trong hieu chinh u_cond) lam DOI DAU
    ket luan -- +9.72% duoi U_EDGES nhung -1.14% duoi bin phan vi. Mot
    tham so khong co can cu KHONG phai mot chi tiet.

(3) Mot DUONG ben hon mot DIEM vi ba le:
    - khong doi hoi mot quyet dinh khong co can cu;
    - doc gia co chi phi abstain KHAC doc duoc ket qua cua ho tren cung
      mot hinh;
    - DO NHAY CAM cua tau* theo lift_min tro thanh mot DAI LUONG DUOC BAO
      CAO, thay vi mot gia dinh bi giau.

Ba muc phu mot bac do lon: 0.05 (abstain re) / 0.10 (trung binh) /
0.20 (abstain dat). Chon TRUOC khi nhin bat ky so nao cua T2.6.
```

CACH BAO CAO -- chot o day:

```text
· tau*(lift_min) cho MOI (mode, rho_bar), kem CI tu bien thien GIUA SEED
· KHONG duoc THEM mot muc lift_min nao sau khi nhin du lieu T2.6
· tau* > max(luoi) o mot muc => ghi "> 28 s (ngoai luoi)".
  KHONG mo rong luoi de di tim tau* (T2-6c). Do la cherry-picking.
· HINH T2-1 ve BA duong ngang lift_min; giao diem la tau*.
```

CAI DAT: `cert/realizability_gate.tau_star_curve(taus, lifts, lift_mins)`
-- da co san, da unit-test, va `lift_min` KHONG co mac dinh o do.

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

### QD-7  Cua so bang kha thi va o suy bien   [DA CHOT]

GHI CHU them sau QD1-R4 (do duoc, khong phai suy doan):

```text
B3 -- sigma cua trace lech so voi SIGMA_RHO = 0.010 CUNG trong
cert/build_calib_set.py:51: 2.18x o poisson@0.925, 4.80x o poisson@0.850,
4.62x o h2@0.700 -- lam U_EDGES chia bin RAT mat can bang. Do duoc o
poisson@0.925: 65.3% so hang roi vao bin cao nhat voi `u`, 81.4% voi
`u_cond_load`.
=> Moi dai luong doc THEO O Mondrian phai kem SO DIEM/O. Mot eta2 hay mot
   chenh lech coverage tren bin mat can bang la mot phep do cua B3 TRUOC
   khi la mot phep do cua taxonomy.
=> Va vi U_EDGES phu thuoc THANG DO, so sanh hai nhanh co sigma_z khac
   thang do duoi cung bo bien la mot so sanh BI TRON. Xem QD1-R4 (B).
KHONG sua SIGMA_RHO -- sua se pha tai tao Phase 21. Ghi va bao cao.
```

Mot bang chap nhan +/-b phai nam trong CUA SO:

```text
    b >= k*se        SAN   -- hep hon nhieu => gate la tung xu
    b <  |effect|    TRAN  -- rong hon hieu ung => du doan KHONG THE SAI
    cua so rong => INSUFFICIENT_POWER, khong doc theo CA HAI chieu (NT 56)
```

```text
CHOT  k    = 3.0
CHOT  san  = 0.05

LY DO cho k = 3.0:
  k phat bieu muc kiem soat MONG MUON theo don vi sigma CHUAN. Voi 5 seed
  (df = 4) va duoi t, k = 3 cho sai so loai I THUC SU la 3.99% MOI PHEP,
  khong phai 0.27% -- lech 15 lan. cert/adjudicate.band() DA quy doi qua
  phan vi t va BAT BUOC nhan n_seed; khong cho nao dung k*se tho.
  k = 2 se cho ~11%/phep: qua long cho mot bang chap nhan.

LY DO cho san = 0.05:
  San chan mot bang VI MO khi se tinh ra rat nho o mot o. Mot bang hep hon
  do phan giai that cua phep do bien gate thanh tung xu. 0.05 la ~2% cua
  bien do ti so du doan [0.199, 0.461] -- du chat de co rang, du rong de
  khong tung xu.

NHAT QUAN VOI ARTIFACT: hai gia tri nay DA nam trong
  docs/phase-T2/02-band-window.json §parameters
  {"k_sigma": 3.0, "band_floor": 0.05, "n_seed_projected": 5}
  va cua so tung o da tinh tu chung. Ky o day la XAC NHAN artifact,
  khong phai dat mot so moi.
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

## T2-5  BANG DU DOAN KY TRUOC     [DA GO CHAN -- BANG CHAP NHAN DA KY o QD-7]

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
          b(o) = max(k*se_seed(o), san),  k = 3.0, san = 0.05  [DA KY o QD-7].
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

## T2-7  DIEU KIEN DUNG (KILL CLAUSE)     [DA DIEN]

Moc dem: NGAY KY (ghi o khoi dau file va o T2-8).

```text
T2.4 gate   : 2 ngay.  Qua han => dung can giai tich,
              bound_source = "analytic_pre_T2", di tiep.
              [T2.4 DA cai dat + unit-test; han nay chi phu cho tieu chi
               mondrian_cells_populated va cac chan doan bin them o T2.2b.]

T2.6 sweep  : 2 vong.  Mot vong = mot lan chay TOAN luoi + mot lan phan
              quyet bang cert/adjudicate. Moi vong sua DUNG MOT thu, kem
              mot amendment danh so.
              Qua 2 vong => dong INSTRUMENT_LIMIT voi TAU_GRID = {1, 3, 10},
              ghi gioi han, chuyen sang 20R2.

Tong T2     : 8 ngay. Qua han => dong phase voi ket qua da co, chuyen
              phan con lai thanh NO CO TEN VA CO CHU (danh sach duoi).
```

NO DA BIET TAI THOI DIEM KY -- khong chan viec ky, nhung phai co ten:

```text
N-T2-1  Nhanh u_cond / u_cond_load (QD-1, QD1-R4) DA co ket qua o
        results/PENDING/phase-T2/ tai MOT diem (poisson@0.925, tau_load=10,
        5 seed). CHUA quet tren luoi tau. Ket qua nam o PENDING, KHONG
        dung lam headline cho den khi duoc tham dinh.
        Han: cung han tong T2.

N-T2-2  `z_over_tau_span` trong prereg la so CHEP TAY suy tu hai hang so
        khac (Z_FIXED_S, TAU_GRID_T2). Nen dua vao
        01-prediction-signed.json de no tu dan ra, dung nguyen tac T2-5.
        Han: truoc khi dong phase.

N-T2-3  Taxonomy PHU THUOC THANG. T2.5c do duoc: hieu chinh hoi quy ve
        trung binh cai thien THU TU do kho (-1.14% q_hat duoi bin phan vi,
        5/5 seed, 4.9 sigma) nhung lam VO THANG duoi U_EDGES co dinh
        (+9.72%). Mot taxonomy dua tren HANG (rank) hoac phan vi se tach
        duoc hai hieu ung nay.
        BI CAM TRONG T2: y tuong nay hinh thanh SAU khi nhin du lieu.
        Chuyen thanh no cua 21R2, tien dang ky rieng.

N-T2-4  u_cond_load la ORACLE: no dung tau THIET KE cua trace tong hop,
        thu mot he that KHONG BIET. Phien ban trien khai duoc phai dung
        tau_hat uoc luong -- estimand da ky o QD-4 (integral time scale,
        kem gate so voi ky vong huu han mau). Day la mach noi truc tiep
        T2 -> 21R2.
        Han: 21R2.
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

R6  TAXONOMY PHU THUOC THANG (do duoc o T2.5c, ghi TRUOC khi ky).
    U_EDGES = (0, 1, 2, 3, inf) la bien TUYET DOI, hieu chuan cho thang
    cua `u`. Bat ky bien doi nao lam doi THANG cua bien dieu kien deu lam
    mat phan tang, KE CA khi no cai thien THU TU do kho.
    Do duoc (poisson@0.925, tau_load=10, 5 seed):
        u              65.3% diem o bin tren cung   mean q_hat 24.84
        u_cond(2.87)   73.1%                        26.10  (+5.04%)
        u_cond_load    81.4%                        27.26  (+9.72%)
      nhung duoi bin PHAN VI (thang bi loai bo):
        u_cond_load    -1.14%   eta2 +0.00248, 5/5 seed, 4.9 sigma
    Nguyen nhan do duoc: sigma_z(2.87)/sigma_z(10) = 1.7483 lan.
    HE QUA CHO T2.6: khong duoc doc mot thay doi q_hat nhu mot thay doi ve
    CHAT LUONG taxonomy neu chua kiem so diem/bin. Moi artifact T2.6 phai
    mang `n_per_bin` (da co tu T2.2b).
    Giam nhe: bao cao ca hai che do bin, va tuyen bo ro rang bin phan vi la
    CHAN DOAN chu KHONG phai mot taxonomy de xuat.
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
Toi xac nhan da dien QD-2, QD-7, T2-4 (ngan sach), T2-5 (bang du doan) va
T2-7 (kill clause) TRUOC khi chay bat ky o nao cua T2.6.

Toi xac nhan ket qua QD1-R1..R4 (nhanh u / u_cond / u_cond_load) da duoc
NHIN THAY va da duoc ghi vao muc QD-1 kem thu tu thoi gian, TRUOC chu ky
nay -- chung KHONG phai ket qua cua T2.6.

Ky   : Đoàn Văn Tài
Ngay : 2026-09-08
```

DAU VET BAT BIEN cua file nay KHONG phai mot so chep tay o day. Mot hash
dan vao chinh file se lam doi hash cua file, va mot o tu tham chieu thi
khong bao gio kiem duoc -- mot o khong kiem duoc TE HON mot o trong.
Cung ly do voi mot dong "commit khi ky": ghi commit vao file roi commit
lai se doi chinh commit do.

Dau vet that la COMMIT ma tag tro toi. Kiem bang:

```bash
git rev-parse phase-T2-prereg-signed
git show phase-T2-prereg-signed:docs/phase-T2/00-preregistration.md | sha256sum
git log -1 --format=%cI phase-T2-prereg-signed      # ngay ky, do git giu
```

Quy trinh lam file nay co hieu luc:

```bash
git add docs/phase-T2/00-preregistration.md
git commit -m "prereg(T2): freeze design, thresholds and signed predictions"
git tag -a phase-T2-prereg-signed -m "Phase T2 pre-registration signed"
git push origin phase-T2-prereg-signed
sha256sum docs/phase-T2/00-preregistration.md
```

Amendment protocol: file nay duoc phep doi, nhung moi thay doi phai la mot
amendment danh so ghi ro DOI GI, VI SAO, va DA NHIN THAY DU LIEU NAO khi
quyet dinh. Cai lam no trung thuc la DAU VET, khong phai su bat bien.
