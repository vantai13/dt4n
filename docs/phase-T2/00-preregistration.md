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


---

## AMENDMENT A-T2-1 -- Tach hai dai luong "clip"; xac nhan R5; them R7

Ngay      : 2026-09-08
Commit    : commit them amendment (git log); SHA chay ghi trong sweep_r2/run_log.jsonl
Vong T2-7 : VONG 1 / 2 cua T2.6 (cung vong voi A-T2-2)

### DA NHIN THAY GI KHI QUYET DINH -- khai bao truoc

```text
DA NHIN:  results/PENDING/phase-T2/hygiene_checks.json (KIEM 1/2/3 luot 1)
          Huong dan nguoi dung cung cap: so 5 seed tai
          (poisson|h2, rho_bar=0.96, tau=28): 8.5639% seed=104;
          bon seed con lai 1.80 / 2.49 / 2.60 / 2.80%.
          Cac so nay la TRICH DAN huong dan, CHUA tu do lai o luot nay.
          mien luoi truth-table va RELIABLE_CEILING (doc tu code)
CHUA NHIN: err(tau), err_total, d_sla, rms_e_* theo tau.
           Bang du doan T2-5 chua duoc doi chieu voi bat ky so nao.
```

### DOI GI

```text
(a) TACH TEN. Cot parquet `clip_fraction_max` GOP HAI DAI LUONG:

      ar1_clip_ratio      rho ra ngoai [RHO_MIN, RELIABLE_CEILING]
                          = [0.50, 1.05] cho poisson/h2, [0.50, 0.95] cho cbr,
                          do trong sla_calib_v2.ar1_matrix.
                          ← DAY la dai luong ma R5 noi den.

      tt_domain_clip_max  rho ra ngoai MIEN LUOI DA DO cua truth table
                          mien phu thuoc link (bang chi tiet ben duoi),
                          do trong TruthTable.delay_loss (clip_log).
                          ← DAY la dai luong ma parquet luot 1 ghi.

    Doi ten cot: clip_fraction_max -> tt_domain_clip_max
    Them cot   : ar1_clip_ratio, ar1_cycles, extrapolation_contaminated
    Hai builder cert v2/v3 doc ten noi bo moi; giu schema artifact legacy.
    scalar_ou van tra ndarray mac dinh; chan doan AR1 la NaN (khong ap dung).

    LY DO: KIEM 2 luot 1 doc `clip_fraction_max` = 8.56% roi so voi R5
    ("kep AR(1) < 0.09%") va ket luan "vi pham 95 lan". Do la mot VA CHAM
    TEN (NT 64: mot ten, hai dai luong), khong phai mot vi pham. Hai so
    khong so sanh duoc voi nhau.

(b) R5 -- KET QUA THAT, phai DO LAI truoc khi ghi so.
    So so bo TRICH TU HUONG DAN (chua do lai o luot nay) cho thay kep AR(1) NHO HON hai bac so voi 8.56%:
      cbr@0.700         0.3050%   <- VUOT nguong 0.09%
      h2/poisson@0.850  0.0521%
      poisson@0.925     0.0204%
      h2/poisson@0.960  0.0118%
    (mot lan rut, tau=28, seed=104. Xem (d) ve tinh khong on dinh.)

    CO CHE o cbr@0.700 la KEP SAN, khong phai kep tran:
      mu(uA) = 0.70 - 0.0675 = 0.6325 ; RHO_MIN = 0.50 ; sigma = 0.046221
      khoang cach = 0.1325 = 2.87 sigma  =>  P ~ 0.2%
      RELIABLE_CEILING[cbr] = 0.95 con xa 4.06 sigma.
    R5 khong khai chieu nao, nen no bi vi pham o phia khong ai nhin.

    MUC NGHIEM TRONG: THAP. cbr da bi QD-3 loai khoi luoi song (A < 0.01,
    S37) va chi dong vai NC-T2-3 (doi chung AM: ratio ~ 1 o moi tau). Kep
    san khong pha vai tro do, nhung lam doi chung YEU HON ta tuong. Ghi lai.

    BAT BUOC: do lai co he thong o buoc kiem ve sinh luot 2 -- TRUNG VI qua
    5 seed, tren TOAN luoi tau -- roi moi ghi con so cuoi cung vao day.


    KET QUA THUC TE LUOT 2 -- 2026-09-08, TRUOC KHI DOC err(tau):
      Commit chay: d8956cf5650c023c809659aa0c58886b79388b4a
      166 lenh thanh cong; 10940 dong, 160 o mode/rho/tau/sigma.
      Moi o dung dung 5 seed 101..105; loai canary 999 khoi trung vi.
      AR1: trung vi lon nhat 0.086518% tai
        cbr@0.700, tau=28, sigma=0.0462209302326;
        dai 5 seed 0.027187% .. 0.305045%.
      R5 (<0.09%): PASS.
      TT: trung vi lon nhat 3.340500% tai
        h2@0.960, tau=0.5, sigma=0.00959302325581;
        dai 5 seed 2.935000% .. 3.790500%.
      R7 khong co nguong da ky; giu nhan 0.96, khong dung lam headline.
      Day la so do moi thay cho so tham chieu mot seed, KHONG doi nguong.
      cbr@0.700: max trung vi AR1=0.086518%; TT=0.020000%.
      h2@0.700: max trung vi AR1=0.086518%; TT=0.020000%.
      poisson@0.850: max trung vi AR1=0.069312%; TT=0.610000%.
      poisson@0.925: max trung vi AR1=0.043812%; TT=0.759000%.
      Nguon: results/PENDING/phase-T2/hygiene_checks_r2.json
             results/PENDING/phase-T2/clip_summary_r2.csv (ca dai min/max).

(c) RUI RO MOI R7 -- NGOAI SUY PHANG NGOAI MIEN BANG SU THAT.

    RELIABLE_CEILING[poisson] = RELIABLE_CEILING[h2] = 1.05
    Mien truth-table theo link (kiem tra truc tiep truoc luot 2):
      poisson/h2: uA,vC [0.50,0.96]; ad [0.60,1.04]; con lai [0.50,1.04]
      cbr:        uA,vC [0.50,0.85]; ad [0.60,0.95]; con lai [0.50,0.95]
    Huong dan cung cap da nham mien cua ad thanh mien chung moi link.
    Rieng tran link ad co dai 0.01 ma ar1_matrix CHO PHEP rho di toi nhung truth table
    KHONG CO PHEP DO. `np.interp` kep phang vao dau mut, IM LANG.

    CHIEU CUA THIEN LECH -- doc ky, no NGUOC voi truc giac:
      Dinh chinh theo code: d_true doc TruthTable; d_fresh doc CostV2
      (LinkModelV2 fit + luoi cache [0.50, 1.05]), KHONG doc cung bang.
      Kep phang cua oracle da xac nhan; khong the suy ra ca hai dong y
      hay chieu thien lech err_decision chi tu clip_log. R7 la nguy co
      ngoai mien do; chieu va do lon thien lech CHUA DUOC XAC LAP.
      Van danh dau o 0.96 va khong dung lam headline nhu pham vi da khai.

    DO DUOC (rho_bar = 0.96, mode poisson va h2):
      link cao nhat `ad`: mu = 0.96 + 0.0625 = 1.0225
      khoang cach toi 1.04 = 0.0175 = 1.82 sigma  (sigma(a=0.9) = 0.00959)
      tt_domain_clip qua 5 seed o tau=28: 1.80 / 2.49 / 2.60 / 2.80 / 8.56%

(d) DAI LUONG BAO CAO cho ca hai loai kep: TRUNG VI QUA SEED + DAI,
    KHONG phai MAX.
    LY DO: o tau=28, n*dt/tau = 1400/28 = 50 chu ky doc lap. Mot ti le duoi
    uoc tu 50 mau doc lap khong phai mot phep do -- no la mot lan rut. Trai
    do duoc 1.80-8.56% = 4.75 lan tren cung mot o. `max` qua seed se LUON
    tra ve gia tri ngoai le va bien nhieu thanh mot phat hien.
    Tot hon nua khi co the: gia tri GIAI TICH P(rho > hi) tu (mu_link, sigma),
    von khong nhieu chut nao.

(e) PHAM VI DOC.
    O rho_bar = 0.96 (poisson va h2) danh dau EXTRAPOLATION_CONTAMINATED.
    KHONG dung lam headline. KHONG loai khoi luoi chay.
      - KHONG loai vi: loai mot o SAU khi thay so cua no la cherry-picking.
      - Duoc danh dau vi: ly do (rho vuot mien da do cua truth table) phat
        bieu duoc DOC LAP voi ket qua, va da phat bieu o (c).
    QD-3 giu poisson@0.960 vi ly do BANG DOC DUOC. Ly do do khong bao ham
    ngoai suy, nen day la mot khai bao RIENG, khong ghi de QD-3.

    So tham chieu tu huong dan (se thay bang so luot 2): ba o headline cua D-T2.6-2 (h2@0.700, poisson@0.850, poisson@0.925) do
    duoc tt_domain_clip < 1.8%, ar1_clip < 0.06%. GHI SO, khong loai.
```

### KHONG DOI GI

```text
- KHONG doi RELIABLE_CEILING (pha tai tao 20R/21R/22/23).
- KHONG mo rong luoi truth-table (can do lai tren Mininet; ngoai pham vi T2,
  vi B9/D10 da ky rang T2 la THUAN NUMPY, khong root).
- KHONG doi QD-3. Danh dau EXTRAPOLATION_CONTAMINATED la mot NHAN THEM.
- KHONG doi bat ky nguong nao cua T2-5. Bang du doan giu nguyen.
```

---

## AMENDMENT A-T2-2 -- Cua so cham diem phai DOC LAP VOI NHANH (NC-T2-2)

Ngay      : 2026-09-08
Commit    : commit them amendment (git log); SHA chay ghi trong sweep_r2/run_log.jsonl
Vong T2-7 : VONG 1 / 2 cua T2.6 -- SUA DUNG MOT THU: cua so cham diem.
            Con lai 1 vong. Het vong => dong INSTRUMENT_LIMIT voi
            TAU_GRID = {1, 3, 10} theo dung T2-7.

### DA NHIN THAY GI KHI QUYET DINH

```text
DA NHIN:  KIEM 3 luot 1 -- max rel_span = 2.19% vs nguong NC-T2-2 = 1%,
          2/100 nhom vi pham (nhom theo mode x rho_bar x sigma_rho).
          Bang chung co hoc: rms_e_model -- KHONG phu thuoc z chut nao --
          van khac 0.05% giua hai nhanh.
CHUA NHIN: err(tau). Khong mot dai luong nao cua T2-5 duoc doi chieu.
```

### LOI

```text
measurements/decision_error_v2.py:418  (run_cell -- duong T2.6 da chay)
measurements/decision_error_v2.py:548  (fixed_summary_with_bootstrap -- ban sao)

    common_start = max(int(round(z_s / dt)) for z_s in z_values)

`z_values` la luoi cua NHANH DANG CHAY, nen cua so cham diem PHU THUOC NHANH:

    tau=0.5   fixed max z=4.0 -> hang  800 | scaled max z=0.5 -> hang  100
    tau=1     fixed             hang  800 | scaled max z=1.0 -> hang  200
    tau=28    fixed             hang  800 | scaled max z=28  -> hang 5600

Hai nhanh cham diem tren HAI DAI HANG KHAC NHAU. Va do lech DOI DAU theo
tau: scaled bat dau SOM hon o tau nho, MUON hon o tau lon. Mot doi chung
co do lech doi dau theo chinh truc dang quet thi KHONG DOC DUOC.

DAY KHONG PHAI NHIEM TRANSIENT. sla_calib_v2.py:125 khoi tao
    x[0] = mu + sigma * randn()
tuc TU PHAN PHOI DUNG. Khong co burn-in. Cac hang lech nhau khong "ban" --
chung chi la NHUNG HANG KHAC, thong ke dong nhat. Nen day la NHIEU HUU HAN
MAU do cua so lech, khong phai THIEN LECH. Phan khong chong lan o tau=1 la
600/200000 = 0.3% so hang, nhung 600 hang o tau=1 chi la ~3 khoi tau doc
lap -- mang phuong sai lon so voi ti trong cua chung. Do la ly do 2.19%.

Phan biet nay QUAN TRONG cho cach sua:
    neu la transient   => phai CAT burn-in (doi ban chat phep do)
    vi la lech cua so  => chi can mot cua so CHUNG (khong doi ban chat)
```

### SUA

```text
common_start (va max_k) lay tu HOP luoi z cua CA HAI nhanh:

    def scoring_window_start(tau, dt):
        z_union = set(z_values_for(tau, scaled=False)) | set(z_values_for(tau, scaled=True))
        return max(int(round(float(z) / float(dt))) for z in z_union)

    tau=0.5,1,2,3  -> 800  (4.0 s, do Z_ALL chi phoi)
    tau=5          -> 1000
    tau=10         -> 2000
    tau=20         -> 4000
    tau=28         -> 5600 (28 s, do nhanh scaled chi phoi)

Sua o CA HAI dong 418 va 548. Chi sua 418 thi loi song lai lan sau ai do
chay --summarize-fixed.

KET QUA THAM CHIEU do nguoi dung cung cap (CHUA xac minh o luot nay):
    NC-T2-1 bit-exact               10/10 PASS  (golden la digest cua
                                     ar1_matrix, khong dung toi cua so)
    NC-T2-2 rel_span err_total       0.000000   (truoc: 0.021899)
    rel_span rms_e_model             0.000e+00  (truoc: ~5e-4)
```

### KIEM THU THUC TE TRUOC CHIEN DICH

2026-09-08: 98 passed (15.68 s), gom NC-T2-1 10 test, cua so 13 test,
clip 3 test va hoi quy decision/calibration v2/v3. Log: /tmp/t2_r2_tests.log.
Interpreter: /home/ubuntu/miniforge3/envs/sdn_rl/bin/python.
Test mien clip cua huong dan duoc sua vi mien THUC TE phu thuoc link.

### HE QUA

```text
Moi so cua T2.6 doi => PHAI chay lai toan bo chien dich (166 lenh, ~30 phut).
Ket qua luot 1 GIU NGUYEN o results/PENDING/phase-T2/sweep/ -- no la BANG
CHUNG cho amendment nay, khong duoc ghi de. Luot 2 ghi vao sweep_r2/.
```

---


KET QUA TOAN CHIEN DICH LUOT 2 (da do, 2026-09-08):
- NC-T2-4: PASS, 6 canary, 1 SHA256, numeric span=0.
- NC-T2-2: PASS, err_total rel_span=0.0,
  rms_e_model rel_span=0.0.
- Nguon: results/PENDING/phase-T2/hygiene_checks_r2.json.

GIOI HAN CONG DOC DUOC PHAT HIEN TRUOC KHI DOC DUONG err(tau):
Cong thuc RMS tai tao 22.6 trong sai so may, nhung 22.6 la RMS sai so
MARGIN CHI PHI hai hanh dong, con run_cell T2 la RMS sai so DELAY moi hanh
dong. Hai dai luong khac nhau du cung ten cot. Khong phan quyet du doan
RMS/ratio/peak/knee cua T2-5 bang parquet nay. Chua tinh tau_star tu du
lieu khong co lift conformal. Ghi NOT_EVALUATED, khong gia vo FAIL/PASS.
Day la ghi nhan gioi han, KHONG sua phep do/nguong hay tieu vong sua thu hai.
Bang chung: results/PENDING/phase-T2/rms_reference_check_r2.json.

Amendment protocol: file nay duoc phep doi, nhung moi thay doi phai la mot
amendment danh so ghi ro DOI GI, VI SAO, va DA NHIN THAY DU LIEU NAO khi
quyet dinh. Cai lam no trung thuc la DAU VET, khong phai su bat bien.

---

## AMENDMENT A-T2-3 -- ESTIMAND CUA DU DOAN VA ESTIMAND CUA PHEP DO KHONG TRUNG NHAU

Ngay      : 2026-09-09
Commit    : commit them amendment (git log); SHA chay ghi trong sweep_r3/run_log.jsonl
Vong T2-7 : ERRATUM THIET KE -- KHONG tinh la vong sua. Xem muc "PHAN LOAI".
            Neu nguoi tham dinh doc day la vong 2 thi rounds_remaining = 0
            va moi thay doi sau day dong phase o INSTRUMENT_LIMIT.
            Ghi CA HAI cach doc; khong tu phan quyet co loi cho minh.

### DA NHIN THAY GI KHI QUYET DINH -- khai bao truoc

```text
DA NHIN:
  docs/phase-T2/01-prediction-signed.json          artifact DA KY, truoc chien dich
  results/SUPERSEDED/phase-22/tau_sweep_*.json     artifact 22.6 DA CONG BO
  results/PENDING/phase-T2/rms_reference_check_r2.json   kiem tra CONG THUC
  results/PENDING/phase-T2/adjudication_r2.json    trang thai vong, khong phai duong
  results/PENDING/phase-T2/realizability_grid.json cot not_evaluated
  docs/phase-T2/02-band-window.json                bang chap nhan (se, effect, verdict)
  tools/t2_band_window.py, cert/tau_sweep.py,
  measurements/decision_error_v2.py, cert/realizability_gate.py    MA NGUON
  results/PENDING/phase-T2/sweep_r2/*.parquet      CHI cot rms_e_model tai
      poisson@0.925, tau=0.5 -- de DOI CHIEU ESTIMAND (muc L1), khong doc theo tau.

CHUA NHIN:
  err(tau), R(tau), coverage(tau), lift(tau), tau* tren BAT KY luoi nao.
  adjudication_r2.json ghi outcome_curves_opened = false.
  Khong mot du doan D-T2.6-* nao duoc doi chieu voi so do.
```

### PHAN LOAI -- vi sao day la ERRATUM chu khong phai VONG SUA

```text
Ngan sach 2 vong cua T2-7 ap cho viec SUA PHEP DO TRONG MOT THIET KE DUNG.
Bon nhanh T2-6 (a)(b)(c)(d) deu thuoc loai do.

Cai xay ra khong nam trong bon nhanh. No la MAU THUAN NOI TAI cua thiet ke
da ky:

    T2-5 ky du doan tren estimand   RMS_MARGIN_COST     (margin / cost_ms)
    T2-4 chi dinh harness phat      RMS_ALLACTION_DELAY (all_action / delay_ms)

TIEU CHUAN de mot khiem khuyet duoc goi la erratum (dat o day de no khong
thanh cua sau ne kill clause): PHAI chung minh duoc HOAN TOAN tu artifact
commit TRUOC chien dich, khong dung mot byte du lieu KET QUA nao.

Tieu chuan nay THOA:
  B1  01-prediction-signed.json §provenance.estimand tu khai
      "quy uoc HIEU (1-exp(-z/tau)), khop e_stale cua
       measurements/decision_error_v2.py:402"
  B2  §provenance.inputs cua CHINH NO la 4 tep tau_sweep_*.json, va moi
      hang cua chung mang  "scale": "cost_ms",  "level": "margin"
      (do duoc: rows[0].scale, rows[0].level cua tau_sweep_poisson_0.925.json)
  => Mot artifact khai estimand cua minh la A trong khi nguon cua no tu khai
     la B. Mau thuan, thay duoc, KHONG can mot so nao cua T2.6.
```

### LOI -- ba cho, khong phai mot

```text
(L1) HARNESS SAI ESTIMAND            [da phat hien o SUMMARY_R2]
     T2.6 chay measurements/decision_error_v2.py --run-fixed
       e_model = d_true[cur] - d_fresh[cur]     ma tran (n, 4 duong)
       rms_e_model = RMS tren TOAN BO o          -> all_action / delay_ms
     Du doan suy tu cert/tau_sweep.py
       e_model = m_true - m_mid                  chenh lech HAI hanh dong
       chi phi co w_loss * loss                  -> margin / cost_ms
     Bang chung: results/PENDING/phase-T2/rms_reference_check_r2.json
       cross_phase_estimand_verdict = "INCOMPATIBLE"

     DO DUOC, cung o poisson@0.925, cung tau=0.5, cung seed 101..105:
       RMS_MARGIN_COST      2.1400 ms   (22.6, sigma = 0.0096)
                            nguon rows[0].ar1_fit.rms_e_model cua
                            results/SUPERSEDED/phase-22/tau_sweep_poisson_0.925.json
       RMS_ALLACTION_DELAY  0.3405 ms   (T2.6 luot 2, a = 0.9 => sigma = 0.021802)
                            0.3129 ms   (a = 0.5 => sigma = 0.012112)
                            nguon cot rms_e_model cua sweep_r2, nhanh fixed
     Doc theo HUONG, khong chi theo do lon: T2.6 chay voi sigma LON HON 2.27
     lan ma do duoc so NHO HON 6.29 lan. Voi CUNG mot estimand, RMS phai
     TANG theo sigma. Huong nguoc nhau la bang chung manh hon ti so.

(L2) BANG CHAP NHAN CUNG SAI ESTIMAND    [MOI -- phat hien o amendment nay]
     tools/t2_band_window.py:SRC doc 3 parquet decision_error cua 20R va
     tinh sd GIUA SEED cua  err_total_hi / err_total_lo,  merge tren khoa
     ["mode", "rho_bar", "seed", "z_over_tau"].
     => LECH BA CHO so voi diem du doan:
          dai luong : err_total (KHONG thu nguyen)  vs  rms_total (ms)
          muc/thang : all_action / delay_ms         vs  margin / cost_ms
          nhanh     : z_over_tau co dinh = NHANH A  vs  z co dinh = NHANH B
     HE QUA DINH LUONG: err_total la thong ke BAC THANG (tan suat argmin
     doi), nhieu hon nhieu bac so voi chuan L2 tron. Nen se bi thoi to.
     Do duoc trong 02-band-window.json:
          h2@0.925  se_used = 0.045941  ->  recommended_band = 0.137822
     quanh diem du doan ~0.24, tuc +/- 57% gia tri diem. Bang do NUOT hon
     nua bien do du doan [0.199, 0.461] => D-T2.6-2 gan nhu KHONG THE FAIL.
     Day dung la vi pham TRAN cua chinh QD-7:  b < |effect|.
     Cung loai loi voi bang "+/-3%" cua D-T2.6-4 ma QD-7 da bo vi VACUOUS.
     Ghi them, khong giau: se do uoc tu 3 seed legacy (101,102,103), dof=2,
     va chinh provenance cua file da ghi caveat do.

(L3) MUC CONFORMAL TROI THEO TAU          [MOI -- confound chua ai ghi]
     level = ceil((n_calib+1)(1-alpha))/n_calib   (cert/conformal_v2.py:72)
     va n_calib = T_sim/(5*tau)/2 moi bin  =>  GIAM khi tau tang.
     DO DUOC (5 seed, n = n_for_tau(tau, 0.005), alpha = 0.10, build that):
         tau        0.5     1      2      3      5     10     20     28
         n_calib   1000    500    250    167    100     50     25     25
         level   0.9010 0.9020 0.9040 0.9096 0.9100 0.9200 0.9600 0.9600
     => q_hat TUYET DOI va coverage bi thoi toi +6 diem phan tram o tau lon
        MA KHONG CO VAT LY NAO. Day la confound trung khit voi truc quet.
     => NHUNG R(tau) = q_hat[bin3]/q_hat[bin0] la ti so TRONG CUNG mot tau,
        cung n_calib, cung level  =>  muc TRIET TIEU trong ti so.
        D-T2.6-3 (hump cua R(tau)) DUOC BAO VE.
     Phan biet nay phai ky TRUOC, khong duoc phat hien sau khi thay so.
```

### NGUYEN NHAN GOC

```text
docs/GLOSSARY.md dang ky dai luong theo DANG HAM, khong theo MUC va THANG.
Muc `sat` ghi "Khop voi measurements/decision_error_v2.py:402". Ve DANG HAM
dieu do DUNG -- ca hai deu la HIEU. Ve MUC va THANG thi SAI.
cert/tau_sweep.py DA ghi "scale"/"level" trong artifact tu 22.6, nhung
GLOSSARY khong chep sang, nen nguoi thiet ke T2.6 doc GLOSSARY va chon
harness sai.
Day la NT 64 dao chieu: khong phai mot dai luong nhieu ten, ma HAI DAI LUONG
MOT TEN (`rms_e_model`).
Ghi them mot khuyet tat nho cung loai: so dong ":402" da TROI. Trong ban
hien tai dong 402 nam trong CHU KY cua run_cell; e_stale o dong 466 (run_cell)
va 681 (fixed_summary). Mot tro dan file:dong khong co neo la mot tro dan se
sai sau vai commit -- vi vay so dang ky moi neo bang ARTIFACT_FIELD va CODE
theo TEN HAM, khong theo so dong.
```

### DOI GI

```text
(a) DANG KY ESTIMAND -- docs/GLOSSARY.md muc moi "SO DANG KY ESTIMAND"
    Moi estimand co ID + 7 truong bat buoc:
        LEVEL  POPULATION  SCALE  UNIT  BRANCH  CODE  ARTIFACT_FIELD
    Hai muc dau: RMS_MARGIN_COST va RMS_ALLACTION_DELAY.
    Sua dong "Khop voi ...:402" thanh mot canh bao KHONG TUONG THICH.

(b) MOI ARTIFACT PHAI MANG estimand_id
    cert/tau_sweep.py                 da co scale/level -> them ESTIMAND_ID
    measurements/decision_error_v2.py -> them ESTIMAND_ID va ghi vao run_cell
    Test canh: test/test_t2_estimand_registry.py (dung TRUOC khi sua code;
    log do luu o results/PENDING/phase-T2/tests_red_before_fix.log)

(c) HARNESS CUA T2.6 DOI SANG cert/tau_sweep.py
    LY DO KHOA HOC, khong phai "vi no cho so dep hon":
      1. No la harness DA SINH RA du doan da ky (cung estimand).
      2. No VON DA chay z co dinh: z_s = (cur - old)*dt tu _valid_rows,
         doc lap tau  =>  NHANH B theo dinh nghia.
      3. No la harness DUY NHAT phat q_hat / coverage / R(tau); 6/7 du doan
         can chung. decision_error_v2 khong chay conformal.
      4. No FAIL-LOUD khi thieu block: conformal_level tra None -> qhat vo
         nghia thay vi im lang. DO DUOC: 1 seed, n=200000, tau=28 ->
         blocks_total = 8 -> calib/bin = 4 -> conformal_level(4, 0.10) = None.
    LOAI TRU cach khac (ghi de nguoi doc tu danh gia):
      - Sua decision_error_v2 de tinh margin + conformal = viet lai
        cert/tau_sweep.py mot lan nua, rui ro cao hon, khong loi ich.
      - Doi du doan sang all_action/delay = TAI KY DU DOAN SAU KHI CHAY.
        CAM TUYET DOI.

(d) BA SUA BAT BUOC KEM THEO KHI DOI HARNESS
    d1  n = n_for_tau(tau, dt) THAY VI n = V3.N co dinh   [T2.2 da ky]
        DO DUOC: tau=28, 1 seed, n=200000 -> 8 block -> level = None
                 tau=28, 5 seed, n=280000 -> 50 block, 25 calib/bin >= 9 OK
                 block_len_for_tau(28) = 28000 mau = 140.0 s = 5*28
    d2  sigma = a * sigma_max_regime(mode, rho_bar), a in {0.5, 0.9}
        THAY VI V3.SIGMA = 0.0096 co dinh trong chu ky build_at_tau.
        Day KHONG phai mot truc them cho vui: DO DUOC tu twin/cost_v2.py
             cell             sigma_max   a=0.9      0.0096 lech
             cbr@0.700        0.051357    0.046221   4.81x
             h2@0.700         0.051357    0.046221   4.81x
             poisson@0.850    0.053295    0.047965   5.00x
             h2@0.850         0.053295    0.047965   5.00x
             poisson@0.925    0.024225    0.021802   2.27x
             h2@0.925         0.024225    0.021802   2.27x
             poisson@0.960    0.010659    0.009593   1.00x
             h2@0.960         0.010659    0.009593   1.00x
        0.0096 VUA KHIT o rho_bar = 0.96 va SAI 5.00 lan o rho_bar = 0.850.
        Toan bo 22.6 chay lop chung nhan voi bien do cua MOT o, ap cho moi o.
        Do la B3, ghi trong chinh file nay o QD-7 (dong 456-466): 2.18x o
        poisson@0.925, 4.80x o poisson@0.850, 4.62x o h2@0.700 -- do la so
        so voi SIGMA_RHO = 0.010; bang tren so voi 0.0096 nen lech chut.
        sigma va a LOAI TRU NHAU va KHONG CO MAC DINH IM LANG.
    d3  realizability_gate NHAN DU 9 THAM SO: them sigma, clip_fraction
        (tu ar1_clip_ratio), min_cell_blocks (tu min_calib_blocks).
        Hien 3 tieu chi la "not_evaluated" tren CA 96/96 o
        (censoring_ok, mondrian_cells_populated, sigma_feasible).
        DO DUOC sau khi truyen du: verdict REALIZABLE, failed [],
        not_evaluated [] -- rong.

(e) BANG CHAP NHAN TINH LAI TREN DUNG ESTIMAND        [sua L2]
    Chay cert/tau_sweep.py tren luoi tau CU {0.5, 1, 2, 2.87, 5}, MOI SEED
    MOT LAN, lay sd giua seed cua rms(tau=5)/rms(tau=0.5).
    DAY LA DU LIEU CU (22.6 da cong bo)  =>  KHONG VONG TRON.
    XAP XI PHAI KHAI: se do tren khoang [0.5, 5] duoc dung lam SAN cho ti so
    tren khoang [0.5, 28]. se cua mot LOG-TI SO on dinh theo do dai khoang,
    nen day la san BAO THU. Khai o day, khong giau.
    NEU khong dung duoc: chuyen sang bao cao DIEM + CI (Student-t, n = 5 seed)
    va phan quyet INSUFFICIENT_BAND -- KHONG PASS, KHONG FAIL (NT 56, QD-5).
    02-band-window.json duoc danh SUPERSEDED_BY_A-T2-3 trong
    docs/phase-T2/04-estimand-descriptor.json; FILE GIU NGUYEN, khong xoa.

(f) MUC CONFORMAL PHAI DUOC BAO CAO VA KHU            [sua L3]
    f1  moi hang ghi conformal_level_used va n_calib_blocks_per_bin
    f2  duong CHINH cua coverage(tau) dung PHAN TICH KHOP MUC: rut ngau
        nhien DUNG 25 block hieu chuan o MOI tau (seed rut = 7201) => moi
        tau cung level = 0.96 => muc khong con la ham cua tau
    f3  R(tau) doc tren DU LIEU DAY DU (muc triet tieu trong ti so)
    f4  DU DOAN KY TRUOC: bang level o muc (L3) phai TAI HIEN trong cot
        conformal_level_used. Lech => loi co hoc, dung ngay.
    KHONG sua n_for_tau: no la hang so T2.2 DA KY. Khu bang PHAN TICH,
    khong bang cach doi thiet ke.
```

### KHONG DOI GI

```text
- 01-prediction-signed.json: KHONG SUA MOT BYTE. So du doan VAN DUNG vi
  chung von suy tu 22.6 = margin/cost. Chi CAI NHAN sai. Nhan duoc sua o
  file MOI docs/phase-T2/04-estimand-descriptor.json; artifact ky giu nguyen
  sha256 68e975c2c08247e208cabc29f6e7f7710eeb01e46ba8018be0d9fda885608d7f
- QD-1 (`u` la nhanh chinh), QD-2 (lift_min la mot DUONG {0.05,0.10,0.20}),
  QD-3 (loai cbr, giu lam doi chung am), QD-4, QD-5, QD-6: GIU NGUYEN.
- QD-7 k = 3.0, san = 0.05: GIU NGUYEN. Chi doi NGUON cua se, khong doi k.
- TAU_GRID trong cert/tau_sweep.py: KHONG SUA. test/test_phase22_tau.py
  GT1 ghim no lam chu ky cua Phase 22 DA DONG. Luoi moi truyen qua --taus
  va dat ten rieng TAU_GRID_T2.
- Ket qua 166 lenh o sweep_r2/: GIU NGUYEN, khong ghi de. Xem "TAI SU DUNG".
- Toan bo Phase G, L2, 22.6: khong dung toi.
```

### TAI SU DUNG 166 LENH DA CHAY -- chung KHONG bi vut

```text
Chung do dai luong RMS_ALLACTION_DELAY, la dai luong HOP LE cho mot cau hoi
KHAC. Chuyen quyen so huu:

  err_total(tau, z), d_sla(tau, z)     -> Phase 20R2 muc (1) va (2)
                                          (twin sai bao nhieu, gia bao nhieu)
  err theo tau                          -> 20R2 muc (4), truc chinh cua v10
  ar1_clip_ratio, tt_domain_clip_max    -> V-T2-3 va Threats
  canary 6 lan / 1 SHA-256 / lech 0.0   -> bang chung moi truong on dinh
  NC-T2-2 rel_span = 0.0                -> bang chung hai nhanh chung luong
  R5 trung vi max 0.086518% < 0.09%     -> gate ve sinh PASS

Ghi vao results/PENDING/phase-T2/sweep_r2/OWNERSHIP.md, gan
estimand_id = RMS_ALLACTION_DELAY, va KHONG dung chung de phan quyet bat ky
du doan T2-5 nao.
```

### DU DOAN BO SUNG -- KY TRUOC KHI CHAY (khong duoc sua sau)

```text
D-T2.6-8   conformal_level_used(tau) do duoc KHOP bang (L3) tuyet doi < 1e-9
           o moi tau. Day la kiem CO HOC, khong phai vat ly.
           FAIL => dung ngay, loi cai dat.
D-T2.6-9   arm doi chung legacy (sigma = 0.0096, tau in {0.5,1,2,2.87,5},
           5 seed gop, n = 200000) TAI TAO tau_sweep_*.json cu voi
           |diff| < 1e-8 tren A, c, rms_e_model.
           FAIL => da doi them thu khac. DUNG, khong debug tiep.
           (cung vai tro voi NC-T2-1 bit-exact o T2.3)
D-T2.6-10  R(tau) do tren du lieu day du va R(tau) do tren phan tich khop
           muc LECH < 1% o moi tau. Co so: muc triet tieu trong ti so.
           FAIL => gia thuyet "muc triet tieu" SAI => phai bao cao, va moi
           doc R(tau) phai chuyen sang ban khop muc.
```

### NGAN SACH -- DO DUOC TRUOC KHI CHAY (khong doan)

```text
Do tren may nay, poisson@0.925, 5 seed, a = 0.9, luoi tau moi, CHI PHAN BUILD:
    tau   0.5   1     2     3     5     10    20    28
    n     200k  200k  200k  200k  200k  200k  200k  280k
    s     4.9   4.6   4.4   4.5   4.4   4.3   4.3   6.0     TONG 37.4 s

    Luoi chinh   9 o x 2 muc a x 37.4 s ~ 674 s ~ 11.2 phut
    Arm legacy   4 o x ~23 s            ~  92 s ~  1.5 phut
    ---------------------------------------------------------
    TOAN CHIEN DICH ~ 13 phut (BUILD)  <<  8 gio

GIOI HAN CUA CON SO NAY, khai ro: no CHI dem build_at_tau. decompose,
fit_ar1, qhat_by_bin va coverage_by_bin CHUA duoc tinh vao. Ngay ca khi
chung nhan doi tong so len 3 lan, chien dich van duoi 1 gio.
=> Quy tac "neu > 8 gio thi FRACTIONAL DESIGN" cua T2-4 TU GIAI QUYET:
   CHAY TOAN PHAN.
```

### PHAM VI DOC DUOC -- khai TRUOC

```text
CONFIRMATORY (co diem du doan da ky o 01-prediction-signed.json):
    h2@0.700 | poisson@0.850 | poisson@0.925
DOI CHUNG AM (QD-3):
    cbr@0.700   -- phai tiep tuc cho R ~ 1.00
EXPLORATORY (KHONG co diem ky; chi bao cao, KHONG phan quyet du doan):
    h2@0.850 | h2@0.925 | h2@0.960 | poisson@0.700 | poisson@0.960
h2@0.960 da bi 02-band-window danh INSUFFICIENT_POWER (se = 0.373,
recommended_band = null); giu nhan do.

Mot ket qua EXPLORATORY khong duoc trinh bay nhu mot du doan da xac nhan.
```

### NEU FAIL THI SAO -- dien TRUOC

```text
(a) D-T2.6-9 FAIL (khong tai tao duoc 22.6)
    -> gan nhu chac chan la co hoc: sigma truyen sai duong (sigma= vs a=),
       n khong dung 200000, hoac seeds khong dung (101..105).
    -> KHONG di tim loi khoa hoc. Kiem ba thu do theo dung thu tu.
(b) D-T2.6-8 FAIL (level khong khop bang)
    -> split_by_block chia calib/test khac ti le gia dinh 50/50.
       In n_calib_blocks_total va n_test_blocks_total, doi chieu.
(c) D-T2.6-10 FAIL (muc KHONG triet tieu trong ti so)
    -> DAY LA KET QUA, khong phai loi. Bao cao, va chuyen MOI phep doc
       R(tau) sang ban khop muc. Ghi vao Threats.
(d) Bang (e) khong dung duoc (se legacy khong tinh ra)
    -> chuyen sang DIEM + CI, phan quyet INSUFFICIENT_BAND.
       KHONG tu dat mot bang tron.

NGAN SACH: KHONG mo vong sua thu ba. Neu (a) hoac (b) FAIL sau MOT lan sua
co hoc, dong phase o INSTRUMENT_LIMIT theo dung T2-7.
```

### DINH CHINH TRONG CHINH BAN NHAP NAY -- ghi lai vi dau vet quan trong hon su sach se

```text
Ban nhap dau cua amendment nay dan bang chung L1 la
    "8.2359 ms (T2.6)  vs  2.1400 ms (22.6)  =>  ti so 3.85x".
KIEM LAI TUNG FILE:DONG cho thay ve so nay SAI QUY GAN.
    8.235915145897662 la rms_total CUA CHINH 22.6 tai z = 0.055, tau = 0.5
    (results/PENDING/phase-T2/rms_reference_check_r2.json muc "example",
     va rms_reference_decomposition_r2.csv dong 2). No la ve trai cua phep
     kiem DONG NHAT THUC sqrt(em^2 + 2cov + es^2), KHONG phai mot so do cua
     T2.6, va KHONG phai RMS_ALLACTION_DELAY.
So do THAT cua T2.6 luot 2 tai cung o, cung tau, cung seed la 0.3405 ms
(a = 0.9) va 0.3129 ms (a = 0.5) -- xem muc (L1). Ket luan KHONG doi:
hai estimand van khong so sanh duoc, va bang chung con manh hon vi HUONG
sai (sigma to hon ma so nho hon). Chi con so bi thay.
Ghi lai o day de nguoi doc sau thay: mot bang chung dung ket luan van co the
dung sai so lieu, va cach chua la GREP TUNG FILE:DONG chu khong phai tin ban nhap.
```

### TAI LAP PHAN RA CO CHE (bo sung truoc khi ky)

Bang chung "huong nguoc nhau" o (L1) la suy luan GIAN TIEP vi hai so do o hai
muc sigma khac nhau. Do lai voi CUNG mot sigma = 0.0096 de loai bien sigma,
va doi TUNG TRUONG mot cua so dang ky:

```text
poisson@0.925, tau=0.5, seed=101, sigma=0.0096, CUNG hang, CUNG z,
cung mot xep hang theo twin CU tren thang chi phi:

    LEVEL=all_action  SCALE=delay  ->  0.3061 ms
    LEVEL=margin      SCALE=delay  ->  0.1316 ms      doi MUC
    LEVEL=margin      SCALE=cost   ->  2.1106 ms      doi THANG

    doi MUC   all_action -> margin :  x0.4298   (common-mode rejection)
    doi THANG delay      -> cost   :  x16.0422  (w_loss = 3222.244682)
    tich                           :  x6.8947

LENH TAI LAP (do duoc 2026-09-09 tren repo nay):

    import numpy as np, cert.build_calib_set_v3 as V3
    tt = V3.TruthTable(V3.TRUTH_TABLE); cv = V3.C.CostV2(strict_reliable=False)
    cell = V3._load_cell('poisson', 0.925)
    arr = V3._cell_arrays(tt, cv, cell, seed=101, tau=0.5, n=200000,
                          dt=0.005, sigma_override=0.0096)
    cur, old, _ = V3._valid_rows(200000, 0.005)
    order = V3.SS.top_k_by_twin(arr['c_fresh'][old])
    a1, a2 = order[:, 0], order[:, 1]; row = np.arange(len(cur))
    m = lambda T, M: (T[row, a2] - T[row, a1]) - (M[row, a2] - M[row, a1])
    rms = lambda x: float(np.sqrt((np.asarray(x, float) ** 2).mean()))
    rms(arr['d_true'][cur] - arr['d_fresh'][cur])            # 0.3061
    rms(m(arr['d_true'][cur], arr['d_fresh'][cur]))          # 0.1316
    rms(m(arr['c_true'][cur], arr['c_fresh'][cur]))          # 2.1106

=> Hai TRUONG cua so dang ky, moi truong mot dong gop DO DUOC, hai huong
   NGUOC nhau, tich khop dung ti so quan sat. Khong con la "hai so khac
   nhau" ma la "hai so khac nhau VI dung hai truong da dang ky".
```

### ERRATUM A-T2-3.1 -- BANG (L3) SAI MOT O; DUNG LAN SUA CO HOC DUY NHAT

Ngay   : 2026-09-09, SAU khi chay sweep_r3, TRUOC khi mo bat ky duong cong nao.
Trang thai: day la LAN SUA CO HOC theo nhanh (b) cua muc "NEU FAIL THI SAO".
            Sau erratum nay, ngan sach sua CO HOC = 0. Neu D-T2.6-8 con FAIL,
            dong phase o INSTRUMENT_LIMIT theo dung T2-7.

DO DUOC (18/18 artifact, 8 tau moi artifact):
    gate        PASS   0 REJECTED; not_evaluated RONG  => (d3) dat
    D-T2.6-8    FAIL   18 vi pham, TAT CA tai tau = 3.0
                       do duoc level 0.9101796  vs bang da ky 0.9096386
    D-T2.6-10   FAIL   max_rel_diff = 0.1596  (nguong 0.01)

CHAN DOAN theo dung nhanh (b) da ky ("in n_calib_blocks_total va
n_test_blocks_total, doi chieu"):

    tau   n_blocks  calib  test   calib/tong
    0.5   2000      1000   1000   0.5000
    1     1000      500    500    0.5000
    2     500       250    250    0.5000
    3     335       167    168    0.4985   <-- DUY NHAT
    5     200       100    100    0.5000
    10    100       50     50     0.5000
    20    50        25     25     0.5000
    28    50        25     25     0.5000

    Nguyen nhan suy TU (n, dt, tau), KHONG can mot byte ket qua nao:
        block_len_for_tau(3.0, 0.005) = 3000 mau
        200000 / 3000 = 66.67  KHONG NGUYEN
        block_id = t_idx // lb  =>  ceil(200000/3000) = 67 id moi seed
        67 x 5 seed = 335 block, mot SO LE  =>  khong chia doi duoc
        335 -> 167 calib / 168 test = 0.4985
    Moi tau khac deu cho so block/seed NGUYEN nen tong chan va chia dung 50/50.
    Nhanh (b) da du doan DUNG ban chat: "chia calib/test khac ti le 50/50".

=> LOI NAM O BANG DA KY, KHONG o may do. So dung tai tau=3 la:
       n_calib = 167   va   conformal_level(167, 0.10) = 0.9101796407185628
   Bang (L3) o tren ghi 166 va 0.9096. Doc bang (L3) voi dinh chinh nay.

TAI SAO KIEM CHUNG TRUOC KHI KY KHONG BAT DUOC -- ghi lai, khong giau:
    Script kiem nhanh truoc khi ky tinh calib = (T_sim/(5*tau))*5/2 = 166.67,
    IN ra bang "%.0f" thanh "167" nhung TRUYEN int(166.67) = 166 vao
    conformal_level. No HIEN THI so dung va TINH so sai, nen mot bang sai
    lai "tai hien chinh xac". Mot phep kiem chung ma dau ra hien thi khong
    phai dau vao tinh toan thi khong kiem chung gi ca.

D-T2.6-10 FAIL LA MOT KET QUA, KHONG PHAI LOI (theo dung nhanh (c) da ky):
    Gia thuyet o (L3) -- "muc conformal TRIET TIEU trong ti so R(tau) vi hai
    bin cung mot tau dung cung n_calib" -- BI BAC BO bang so do:
        max_rel_diff = 0.1596 tai poisson@0.850, tau = 2   (nguong 0.01)
    Muc co triet tieu neu q_hat hai bin ti le voi nhau khi doi muc; do duoc
    thi khong. Nen ke tu day, MOI phep doc R(tau) phai dung BAN KHOP MUC
    (level_matched), va con so nay phai vao muc Threats.
    D-T2.6-3 KHONG con duoc doc tren du lieu day du.

KHONG DOI GI KHAC: khong dong toi n_for_tau, TAU_GRID, k, san, lift_min,
01-prediction-signed.json hay 05-band-window-v2.json.

### ERRATUM A-T2-3.2 -- CHINH SACH DOC CHO VONG 3; KHAI TRUOC KHI PHAN QUYET

Ngay      : 2026-09-09, SAU khi ba kiem co hoc xong, TRUOC khi chay
            tools/t2_6b_adjudicate.py va tools/t2_6b_level_probe.py.
Trang thai: KHONG dat mot nguong moi nao. Chi khai TRUOC cach ap cac luat DA KY.

### (1) D-T2.6-10 VAN LA FAIL -- khong co PASS hoi to

    max_rel_diff = 0.15962 tai poisson@0.850, tau=2, nguong 0.01.
    Phan quyet GIU NGUYEN va ghi vinh vien. Moi chan doan ve THANH PHAN cua
    con so nay deu la POST_HOC va KHONG duoc dung de lat phan quyet.

    Ghi them mot khiem khuyet CUA CHINH PHEP KIEM, de nguoi doc tu danh gia:
    D-T2.6-10 so R(day du, level goc) voi R(25 block, level 0.96), tuc doi
    HAI thu cung luc (muc VA co mau) roi quy ca chenh lech cho MOT thu (muc).
    Do la mot confound -- dung loai loi ma phase nay ton tai de chong. Phep
    kiem bi DAC TA SAI. Nhung no VAN FAIL theo dung dieu da ky, va bien phap
    da ky o nhanh (c) VAN duoc ap DAY DU. Khong sua dac ta sau khi thay so.

### (2) NHANH DOC CHINH CUA R(tau) -- ap bien phap da ky o nhanh (c)

    NHANH CHINH   level_matched (25 block/bin o MOI tau, level 0.96)
    ARM DO NHAY   du lieu day du (level goc) -- BAO CAO, KHONG phan quyet
    CAM           dung arm do nhay de lat mot verdict cua nhanh chinh.
                  Neu hai nhanh cho verdict khac nhau => do la KET QUA,
                  ghi ca hai, verdict cuoi = verdict cua NHANH CHINH.

### (3) TIEU CHI CONG SUAT -- DUNG NGUONG DA KY, KHONG DAT NGUONG MOI

    san nhieu = mean |ratio_measured - ratio_measured_sim|
                (hai uoc luong DOC LAP cua cung mot ti so)
    bien do   = max R - min R tren luoi tau
    NGUONG:   >= 5.0  READABLE
              >= 2.0  WEAK
              <  2.0  INSUFFICIENT_POWER

    NGUON cua ba nguong nay, khong phai tu van ban nay:
        tools/t2_1_prediction.py:276-277   (ham power_scope_hump)
        test/test_t2_1_prediction.py:185-186  ghim > 5.0 va < 2.0
        00-preregistration.md:643-645  ghi "3.2 YEU", "1.1 INSUFFICIENT_POWER"

    MOT DE XUAT DUNG 10.0 / 3.0 DA BI TU CHOI o day. Ly do: no nghiem khac
    HON nguong da ky, nhung no CHUA DUOC KY. Doi nguong sau khi thay so --
    du la doi theo huong nghiem khac hon -- van la doi nguong sau khi thay so.
    Ghi lai de nguoi doc biet lua chon nay da duoc can nhac va bi tu choi.

### (3b) D-T2.6-4 DUNG SPREAD TRUNG BINH, KHONG PHAI SPREAD LON NHAT

    Ban DA KY: tools/t2_1_prediction.py:256-257
        passes = span_GIUA_tau(X) < mean( spread_TRONG_tau(X) qua cac tau )
    Mot de xuat dung max(...) thay cho mean(...) DA BI TU CHOI o day: max >=
    mean nen no NOI LONG tieu chi, va no la mot nguong KHAC voi nguong da ky.

    KIEM TU THAN cua adjudicator (chay TRUOC khi phan quyet luoi chinh):
        adj_4 tren results/PENDING/phase-T2/sweep_r3/legacy_*.json (22.6)
        do lai : n_checks = 9,  n_fail = 3
        da ky  : n_checks = 9,  n_fail_on_22_6 = 3      => KHOP
    Voi max() no cho n_fail = 1, tuc BO SOT hai truong hop that bai that.
    Mot adjudicator khong tai tao duoc con so da ky tren du lieu cu thi khong
    duoc phep cham du lieu moi.

### (4) MAU SO CUA G-T2-8 -- khai TRUOC khi doc

    mau so = 7  (D-T2.6-1 .. -7)
    INSUFFICIENT_POWER KHONG vao TU SO va VAN o MAU SO.
    Neu >= 2 muc INSUFFICIENT_POWER thi gate ">= 5/7" khong dat duoc VE MAT
    SO HOC; khai dieu do THANG, KHONG doi mau so.
    D-T2.6-5 mang sang tu vong 2, va PHAI ghi ro no song tren estimand KHAC
    (RMS_ALLACTION_DELAY): no la doi chung noi HAI NHANH cua
    measurements/decision_error_v2.py, khong phai mot khang dinh ve lop
    chung nhan. Ngoai le nay hop le va phai hien ro tren moi bang.

### (5) O EXPLORATORY

    Tinh day du moi dai luong; gan nhan scope = EXPLORATORY tren MOI dong.
    KHONG sinh verdict PASS/FAIL -- chi REPORTED_ONLY.
    KHONG cong vao bat ky ti le "k/7" nao. KHONG dung de lat verdict cua o
    CONFIRMATORY. Duoc dung de RA CAU HOI cho 21R2.
    h2@0.960 giu nhan INSUFFICIENT_POWER da co tu 02-band-window.

### (6) tau* KHONG DO DUOC BANG DUNG CU NAY

    QD-2 dinh nghia tau* = inf { tau : lift(tau) < lift_min }, voi
    lift = (err_baseline - err_certified) / err_baseline.

    DO DUOC BANG GREP (2026-09-09), khong phai suy doan:
        "lift", "err_certified", "err_baseline" KHONG xuat hien trong
        cert/tau_sweep.py, KHONG trong measurements/decision_error_v2.py,
        va "err_certified" KHONG xuat hien trong bat ky tep .py nao cua repo.

    Truc tau nam o harness chung nhan (RMS_MARGIN_COST); sai so quyet dinh
    nam o harness quyet dinh (RMS_ALLACTION_DELAY). Hai estimand khong so
    sanh duoc (xem SO DANG KY ESTIMAND). Nen lift KHONG suy duoc tu vong nay.

    => tau_star = NOT_MEASURABLE_BY_THIS_INSTRUMENT, kem THIET KE BAN GIAO
       cho 21R2. CAM suy tau* tu R(tau): R la ti so BAN KINH KHOANG, lift la
       ti so SAI SO QUYET DINH. Quy doi giua chung dung loai loi ma A-T2-3
       vua sua xong.
    tau* CHUA BAO GIO nam trong bay du doan da ky D-T2.6-1..7, nen dieu nay
    KHONG lam thay doi mau so o muc (4).

### (7) GIA TRI R DA LO KHI CHAN DOAN -- ghi de khong ai noi la giau

    Kiem ve sinh da ky va chan doan D-T2.6-10 buoc phai tinh ti so. Ba diem
    da nhin thay TRUOC khi phan quyet, tat ca o a = 0.9:

        h2@0.700       tau=2     R_day_du = 2.2175   R_khop_muc = 2.4171
        poisson@0.850  tau=0.5   R_day_du = 2.1310   R_khop_muc = 2.1422
        poisson@0.850  tau=2     R_day_du = 2.3602   R_khop_muc = 2.7369

    KHONG doc R nhu mot ham cua tau, KHONG tim dinh, KHONG so voi diem ky.

### (8) tools/t2_6b_level_probe.py LA POST_HOC

    Cong cu nay hinh thanh SAU khi D-T2.6-10 FAIL. No tach chenh lech thanh
    thanh phan MUC (doi level tren du lieu DAY DU, khong rut) va thanh phan
    RUT MAU (nhieu hat rut khac nhau). No KHONG sua nguong, KHONG doi
    artifact, KHONG lat phan quyet. Moi so cua no phai mang nhan POST_HOC
    trong bao cao va chi duoc dung cho muc Threats.

### (9) NGAN SACH -- adjudicator chi chay MOT LAN CO HIEU LUC

    Ngan sach sua co hoc = 0 (da tieu o A-T2-3.1). Do do:
    tools/t2_6b_adjudicate.py duoc kiem CO HOC trên arm legacy truoc (no co
    chay khong, co doc dung khoa khong, co sinh du 7 muc khong). Chi khi
    sach tren legacy moi tro vao luoi chinh. Chay xong ma sua adjudicator roi
    chay lai KHONG phai sua co hoc -- do la TUNING PHAN QUYET va bi CAM.

### ERRATUM A-T2-3.3 -- CACH DOC KET QUA VONG 3; VIET TRUOC KHI CHAY THEM

Ngay: 2026-09-09, SAU adjudication_r3.json, TRUOC arm chan doan sigma va
      truoc moi hinh. Khong dat nguong moi; ap luat da ky va sua LOI PHAN
      LOAI trong cong cu.

### (a) cbr@0.700 BI LOAI KHOI D-T2.6-3 THEO QD-3 + QD-7

    Adjudicator ban dau ap tieu chi cong suat cua D-T2.6-3 len cbr@0.700 va
    cho "hump READABLE" (bien do 0.0636 quanh R ~ 1, san nhieu 0.00534,
    ti so 11.91). Do la LOI PHAN LOAI TRONG CONG CU, khong phai phat hien.

    Hai luat DA KY deu loai o nay khoi tap song:
        QD-3  loai mode = cbr theo CO CHE (S37: delay(rho) phang tren cbr)
        QD-7  loai neu err_baseline < 0.01 HOAC A < 0.01
              A do duoc vong 3: [2.20e-04, 3.63e-04]  <<  0.01  => LOAI
    cbr GIU vai tro DOI CHUNG AM, va phep kiem doi chung am that la
    D-T2.6-7 (da PASS: max|R-1| = 0.0161 < 0.05).

    GIOI HAN DA BIET, dang vao Discussion: mot tieu chi cong suat dang TI SO
    (bien do / nhieu) KHONG co khai niem "qua nho de quan tam". Tren o suy
    bien, tu va mau CUNG co lai nen ti so co the van qua nguong du ca hai
    dai luong vo nghia. O day o suy bien da bi loai bang mot tieu chi TUYET
    DOI doc lap (A < 0.01, QD-7) nen khiem khuyet nay khong anh huong ket
    qua -- nhung mot tieu chi ti so nen luon di kem mot san tuyet doi.

### (b) h2@0.700: HAI PHAM VI CONG SUAT CHO HAI DIEM THIET KE

    khai TRUOC tai diem 22.6 (sigma = 0.0096):  bien do/nhieu = 1.1
                                                 INSUFFICIENT_POWER
    do duoc tai diem vong 3:  a=0.5 (sigma = 0.0257, 2.68x) -> 11.84 READABLE
                              a=0.9 (sigma = 0.0462, 4.81x) -> 23.45 READABLE

    Day KHONG phai lat mot gioi han da khai. Cong thuc tinh scope va hai
    nguong (5.0 / 2.0) KHONG DOI; chi DAU VAO doi. sigma lon hon 2.7-4.8 lan
    => bien do buou lon hon => ti so tin/nhieu tot hon. Do la CO CHE.

    LUAT VIET: hai pham vi PHAI xuat hien CANH NHAU o moi cho nhac toi
    h2@0.700; khong bao gio chi mot.
    HEADLINE VAN LA poisson@0.925: no READABLE o CA HAI diem thiet ke
    (10.9 tai 22.6; 18.7-35.7 tai vong 3). Dung mot o vua moi tro nen doc
    duoc lam headline la moi nguoi tham dinh dat dung cau hoi bat loi.

### (c) VI TRI DINH BAO CAO DANG KHOANG BOC, KHONG PHAI "2 s"

    Luoi tau = {0.5, 1, 2, 3, 5, 10, 20, 28}. argmax roi vao o tau=2 o 7/8
    arm. Thong tin thu duoc la: dinh that nam trong KHOANG BOC (1, 3) s --
    vi neu dinh < 1 thi argmax se la 1 hoac 0.5; neu > 3 thi la 3 hoac 5.

        o                dinh KY    khoang boc DO DUOC   phan quyet
        h2@0.700         0.9285     (1, 3)               NGOAI  -- lech that
        poisson@0.850    1.4277     (1, 3)               TRONG
        poisson@0.925    1.5575     (1, 3)               TRONG

    CAM:  viet "dinh dich sang 2 s"        (luoi khong phan giai duoc)
          noi suy parabol qua 3 diem       (khong co co so ve dang R quanh dinh)
          them diem tau in {1.5, 1.75}     (mo rong luoi de di tim, T2-6(c) cam)
    DUOC: ghi vao ban giao "phan giai dinh trong (1,3) s can luoi min hon,
          tien dang ky o 21R2". De xuat tuong lai KHAC mo rong luoi hien tai.

### (d) ARM CHAN DOAN SIGMA -- BON RAO CHAN, KY TRUOC KHI CHAY

    Ly do ton tai: diem ky cua D-T2.6-2 o sigma = 0.0096, con vong 3 do o
    sigma = a*sigma_max (lon hon 1.3-4.8 lan). Arm legacy chi chay tau
    {0.5..5} nen KHONG co diem nao do D-T2.6-2 o dung sigma da ky. Do la
    mot khiem khuyet THIET KE cua chinh A-T2-3 (d2).

    (1) D-T2.6-2 = FAIL. PHAN QUYET DA DONG. Arm nay KHONG lat duoc no,
        ke ca neu no cho 8/8 trong bang.
    (2) Ket qua di DUY NHAT vao Threats to Validity. Khong vao bang verdict,
        khong vao ti le k/7, khong vao hinh nao cua Evaluation tru khi mang
        ky hieu RIENG va chu thich "hau nghiem".
    (3) Nhan POST_HOC_SIGMA_PROBE tren moi dong.
    (4) Cau hoi khai TRUOC, va CHI mot cau:
        "FAIL cua D-T2.6-2 do truc sigma moi hay do truc tau?"
        Ket qua khac ky vong thi GHI NGUYEN. KHONG chay lan hai.

    KHONG ngoai suy tuyen tinh theo sigma de tra loi cau nay: dai sigma rong
    2.7 lan, ngoai suy hau nghiem qua do khong du de viet vao paper. DO.

### (e) G-T2-8 KHONG DAT -- khai lai TRUOC khi viet bao cao

    3 PASS / 7. Mau so 7 giu nguyen (A-T2-3.2 muc 4). KHONG doi mau so,
    KHONG doi nguong, KHONG chuyen mot muc "doc rieng" thanh "dung".
    Hai FAIL deu quy duoc trach nhiem:
        D-T2.6-2  lan voi sai khac sigma do chinh (d2) tao ra
        D-T2.6-4  kiem lai mot gia dinh von DA FAIL 3/9 tren 22.6

### (f) NGUON DUY NHAT CHO HANG SO PHAN QUYET

    Bon lan trong bon luot, mot con so bi CHEP LAI thay vi DOC LAI tu nguon
    da gay loi (8.2359; bang level tau=3; nguong 10/3 vs 5/2; max vs mean).
    Bon loi, MOT co che.
    => POWER_READABLE / POWER_WEAK duoc nang thanh hang so CO TEN trong
       tools/t2_1_prediction.py va adjudicator IMPORT chung. Sau thay doi
       nay KHONG TON TAI kha nang hai noi bat dong.
    => Moi hang so phan quyet moi phai theo cung quy tac: mot nguon, import,
       khong chep.

### CHU KY

```text
Toi xac nhan da doc muc "DA NHIN THAY GI", da dien BA DU DOAN BO SUNG
(D-T2.6-8/-9/-10) va BON NHANH FAIL TRUOC khi chay bat ky lenh nao cua
sweep_r3, va da ky phan loai ERRATUM kem ca cach doc nguoc lai.

Ky:   Doan Van Tai -- ky trong phien lam viec ngay 2026-09-09; van ban duoc
      Claude Opus 5 dien theo chi dan da doc va da duoc chu repo xac nhan
      tiep tuc. Dau vet day du o git log va o transcript phien.
Ngay: 2026-09-09
```
