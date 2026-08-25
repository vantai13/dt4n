# AMENDMENT 23-68 -- Task B-3: tai hieu chuan qua che do, va menh de bao toan

Ngay ky : 2026-08-25
Lesson  : 23.22 Task B-3
Loai    : TIEN DANG KY
Moc     : sau `a6e07e6` (Task B-2 + doc 45), truoc nhanh DO LUONG cua
          `cert/recalibrate_transfer.py`

## 0. Disclosure

### 0.1. DA XEM -- va do la ly do nhieu muc bi HA CAP

Toan bo `taxonomy_audit.json` (`cced37a`), `transfer_matrix.json`,
`recalibration_cost.json`. Cu the, hang `V-S @ kappa=0.5` tren 12 cell:

```text
cell             live    acceptance   viol|acc    err|acc
poisson@0.925    True      0.3955      0.0817     0.0840
poisson@0.850    True      0.3203      0.0834     0.0817
h2@0.700         True      0.5859      0.0759     0.0481
poisson@0.875    True      0.3422      0.0814     0.0857
poisson@0.900    True      0.3621      0.0789     0.0882
poisson@0.960    True      0.4220      0.0831     0.0675
h2@0.650         True      0.4664      0.0847     0.0651
h2@0.675         True      0.5200      0.0790     0.0513
-------------------------------------------------------
poisson@0.700    False     0.9941      0.0763     0.0028
h2@0.850         False     0.9735      0.0718     0.0017
h2@0.925         False     0.9949      0.0684     0.0002
h2@0.960         False     0.9936      0.0687     0.0004

tren 8 cell SONG:  sd(viol) = 0.00289    sd(acceptance) = 0.09201
                   mean(viol) = 0.08100  mean(acceptance) = 0.42679
                   ti so sd(acc)/sd(viol) = 31.8x
```

**Menh de bao toan o dang "toan `n`, `kappa`=0.5, in-distribution" DA DUOC DO.**
No KHONG duoc ky lam du doan. Xem muc 5.1 (`M-200`, KIEM WIRING).

Cung da xem: bang `n` cua Task B-2 (`n*` = 120 / 500 cho C3; 20 / 60 cho B2),
va toan bo ma tran chuyen giao mang-nguyen-`qhat` cua Task B.

### 0.2. CHUA XEM -- day la phan MU

```text
(a) bat ky ket qua nao o `n` HUU HAN duoi thu tuc mang `kappa_A` (n < 500)
(b) bat ky ket qua nao voi `kappa` khong thuoc {0, 0.25, 0.5, 1.0, 2.0}
    (luoi `variant_sweep` chi co 5 diem nay)
(c) `err|accept` cua B2-R khi `c` duoc tai uoc luong de trung `a*` tren B
(d) MOI dai luong o nhanh DO LUONG -- no chua duoc viet khi ky
```

⚠️ **Mot sai lech so voi khuon mau phai khai:** ban thao noi bo viet
"`cert/recalibrate_transfer.py` chua ton tai". Dieu do KHONG dung tai thoi
diem ky. File DA ton tai va chua **DUNG MOT thu**: nhanh PILOT cua muc 4
(`solve_kappa` / `acceptance_at_kappa` / `pilot`). Do la dai luong PHIA HIEU
CHUAN, mot DAU VAO cua thiet ke. Nhanh DO LUONG -- vong lap CRN, ba thu tuc,
va toan bo ham cham diem cua muc 5 -- chua ton tai. Viet dung su that o day
re hon la giu mot cau khuon mau khong con dung (`L78`, `L95`: mot gia tri
khong duoc di qua im lang duoi mot cai ten khong phai cua no).

## 1. Menh de trung tam

Task B do cai conformal KHONG hua ("mang nguyen `qhat` sang che do khac").
`M-194` MISS, va `L97` cho thay do la he qua CAU TRUC, khong phai phat hien.

Task B-3 do cai conformal CO hua:

> cho toi du lieu CO NHAN cua phan phoi moi, toi tra bao phu dung,
> KHONG can mo hinh dung.

Va do cai gia cua loi hua do o hai chieu chua ai do: `n` HUU HAN, va tham so
thiet ke `kappa` MANG TU CHE DO CU.

### 1.1. Thiet ke DOI XUNG -- moi ben mang MOT so, tai uoc luong MOT thong ke

```text
            MANG TU A              TAI UOC LUONG TREN B (n block co nhan)
C3-R        kappa_A (khong t.ng)   qhat(z_bin, m_hat_bin)  -- PHAN VI DUOI
B2-R        a*      (muc tieu)     c                       -- PHAN VI TRUNG TAM
B1-R        a*                     c tren score NGAU NHIEN   [doi chung duong]
```

`a*` = **0.42679** -- acceptance trung binh cua 8 cell song tai `kappa=0.5`
(DA DO, `taxonomy_audit.json`). Chon NEO TAI DIEM VAN HANH HIEN HANH, khong
phai mot so dep bia ra.

`kappa_A` = `kappa` sao cho C3 tren CALIB cua A dat acceptance = `a*`.
Giai bang bisection tren `[0, 8]`, dung sai `1e-4` tren acceptance, be rong
khoang `1e-6`, toi da 45 vong.

Ca hai ben deu duoc mot so hoc tu A va mot vong do lai tren B. Neu C3 van
thua, do la ket qua that.

### 1.2. Menh de bao toan -- phat bieu duoc kiem

```text
C3-R :  GIU  viol|accept ~ alpha      DE TROI  acceptance
B2-R :  GIU  acceptance = a*          DE TROI  err|accept

Khong thu tuc nao giu duoc CA HAI. Do khong phai khuyet diem cua thu tuc
nao -- do la duong bien risk-coverage, nhin theo truc CHE DO VAN HANH.
```

Day la `RQ-C` cua Phase 23 nhin theo mot truc moi, va khop `Nguyen tac 27`
(dong gop la DUONG BIEN, khong phai mot chien thang).

## 2. Cau truc suy duoc TRUOC khi chay -- khong duoc bao cao nhu phat hien

`L97` ap dung theo chieu NGUOC: suy cau truc truoc, roi moi ky.

```text
S-1  C3-R phu thuoc A qua DUNG MOT kenh: `kappa_A`.
     => ma tran 8x8 cua C3-R co HANG 1 theo truc A.
     => neu `kappa` la hang so toan cuc thi truc A SAP HOAN TOAN va
        C3-R(A->B) === C3-R(B->B) === Task B-2. Do la ly do B-3 PHAI mang
        `kappa_A`, khong duoc de `kappa = 0.5` co dinh.

S-2  B2-R va B1-R KHONG phu thuoc A (vi `a*` la hang so toan cuc).
     => 64 o cua chung chi co 8 gia tri khac nhau, lap 8 lan.
     => PHAI kiem TRUNG BIT theo truc A  (`NC-B3-2`).
     => CAM bao cao sd cua chung tren 64 o -- se tu chia cho sqrt(8).

S-3  |acceptance_B2R - a*| ~ 0 THEO DINH NGHIA.
     => KHONG duoc dung lam thang cham diem. Day la hinh dang `L99` lan thu
        TU trong do an. Ghi truoc de khong ai doc nham.

S-4  Tai `kappa_A = 0.5` va `n = 500`, C3-R PHAI trung bit duong cheo
     `transfer_matrix.json`. Do la kiem wiring co dap an biet truoc.
```

## 3. Thiet ke

```text
NHANH R  (CO CHAY)
    3 thu tuc x 8 cell A x 8 cell B x 5 muc `n` x 10 lan lay mau
    N_GRID = (30, 60, 120, 250, 500)
        30  ngay tren san hop le 29 (`L91`)   -> bat vung suy bien
        500 toan bo calib cua B               -> NEO WIRING
    Tai `n = 500` chi 1 lan lay mau: tap con la TOAN BO calib, chin lan kia
    chi ton may (cung quy uoc voi `cert/recalibration_cost.py`).
    CRN: cung `(B, n, draw)` -> CUNG tap block cho ca 3 thu tuc va ca 8 `kappa_A`
    SEED = 232301
    Lay block NGUYEN VEN, khong hoan lai
    (`cert/recalibration_cost.py::subsample_blocks` -- KHONG viet lai)

NHANH C  (KHONG CHAY MOI -- doc thang artifact, ky thuat `G23-247`)
    `taxonomy_audit.json::cells[].variant_sweep[V-S, kappa=0.5]`
    `transfer_matrix.json::` duong cheo
    -> neo wiring, va neo "toan n"

NHANH D  (doi chung am)
    4 cell CHET, cung duong ong, cung N_GRID
```

### 3.1. Dai luong ghi cho MOI o

```text
C3-R :  qhat_source, qhat_has_infinite, qhat_at_sample_max,
        min_blocks_at_final_qhat, n_iter, degenerate,
        acceptance_test, viol_given_accept, err_given_accept,
        n_accept, kappa_used
B2-R :  c, acceptance_test, err_given_accept, n_accept
        (KHONG ghi `viol` -- se phai muon `qhat` cua C3, cai bay `A066` muc 3
         da tu choi, va `A067b` muc 2 da phai go mot lan)
B1-R :  c_B1, acceptance_test, err_given_accept, n_accept
CHUNG:  anchor_err cua B, a*, n_blocks thuc te
```

### 3.1b. Quy uoc GOP -- ky truoc de khong chon sau khi xem so

```text
o(A, B, n)   = TRUNG BINH tren cac lan lay mau, chi tren gia tri HUU HAN.
               Day la don vi cua moi thong ke o muc 5 va 6.
truc A gop   = TRUNG VI tren 8 gia tri A (dung cho moi phat bieu "theo cell B").
sd           = `ddof=1`, tren cac o(A,B,n) da gop, KHONG tren tung lan lay mau.
```

### 3.2. HAI nguong rieng cho `viol` -- KHONG dai hai phia  (bai hoc `M-195`)

```text
VO       :  viol > alpha + 0.05 = 0.15
LANG PHI :  viol < alpha - 0.05 = 0.05  VA  acceptance < 0.20
DAT      :  phan con lai, VOI DIEU KIEN acceptance >= 0.20

San acceptance 0.20 la BAT BUOC cho MOI phat bieu ve `viol`
(bai hoc doc 45 muc 4.1 va doc 44 muc 4.4). No la mot LUA CHON THIET KE --
xem muc 9 `N5`.
```

### 3.3. Census `n_accept = 0`

```text
Moi o co `n_accept = 0` -> `viol` KHONG XAC DINH.
Ghi vao census rieng, LOAI khoi moi thong ke `viol`,
va KHONG BAO GIO dem la "0 vi pham".
```

## 4. PILOT -- duoc phep doc TRUOC khi ky muc 5

Duoc doc: gia tri `kappa_A` cua 8 cell song + 4 cell chet, va cac co suy bien
tai `kappa_A` tren CHINH cell A. Day la dai luong PHIA HIEU CHUAN, mot DAU VAO
cua thiet ke, khong phai mot ket qua. Tien le: `scale(cell)` cua Task B duoc
lay tu Task A0 theo dung cach nay (`A067` muc 5.1).

CHAN DUNG (stop rule): neu voi bat ky cell SONG nao,
  (a) `kappa_A` khong ton tai trong `[0, 8]`, HOAC
  (b) `fit_config` tra `qhat_source == degenerate_fallback_to_none` tai
      `kappa_A` tren CHINH cell A
thi RAISE, KHONG chay tiep, va viet mot amendment con.

### 4.1. Ket qua PILOT  (`results/LIVE/phase-23/recalibrate_transfer_pilot.json`)

Chay `python -m cert.recalibrate_transfer --pilot`, 12 cell, ~11 phut.

```text
cell             role   acc@k=.50   kappa_A   acc@kappa_A   |err|      qhat_source   min_blocks
h2@0.650         live      0.4664   0.558594     0.426868   7.9e-05   fixed_point          463
h2@0.675         live      0.5200   0.623779     0.426840   5.0e-05   cycle_max            453
h2@0.700         live      0.5859   0.693604     0.426874   8.5e-05   cycle_max            431
poisson@0.850    live      0.3203   0.409912     0.426714   7.6e-05   cycle_max            466
poisson@0.875    live      0.3422   0.429443     0.426874   8.5e-05   cycle_max            468
poisson@0.900    live      0.3621   0.448975     0.426696   9.4e-05   fixed_point          469
poisson@0.925    live      0.3955   0.480713     0.426726   6.4e-05   fixed_point          470
poisson@0.960    live      0.4220   0.509399     0.426748   4.2e-05   fixed_point          468
h2@0.850         dead      0.9735   1.611084     0.427771   9.8e-04   cycle_max            299
h2@0.925         dead      0.9949   1.836945     0.427085   2.9e-04   fixed_point          186
h2@0.960         dead      0.9936   1.877441     0.426866   7.7e-05   fixed_point          153
poisson@0.700    dead      0.9941   1.672363     0.426708   8.2e-05   cycle_max            286

acc@k=.50    tach TEST, tu `taxonomy_audit.json`   (de doi chieu)
acc@kappa_A  tach CALIB, do trong pilot            (`kappa_A` duoc giai o day)
```

```text
CHAN DUNG: KHONG co vi pham.
  - 12/12 cell co `kappa_A` trong [0, 8], bisection bat duoc khoang.
  - 0/12 cell co `qhat_source == degenerate_fallback_to_none` tai `kappa_A`.
  - 0/12 cell co `qhat_has_infinite` hay `qhat_at_sample_max` tai `kappa_A`.
  - `min_blocks_at_final_qhat` >= 431 tren MOI cell song (san on dinh 59).
=> duoc phep ky muc 5.
```

### 4.2. Cai PILOT DOI trong muc 5 -- va vi sao

Hai he qua cau truc chi lo ra SAU pilot, va ca hai deu lam mot du doan cua
ban thao noi bo tro thanh **HIT vo nghia**. Chung duoc ghi o day, TRUOC khi
nhanh do luong ton tai.

```text
S-5  Do rong cua truc A NHO hon nhieu so voi du kien.
     kappa_A tren 8 cell SONG:  min 0.4099  trung vi 0.4951  max 0.6936
                                ti so max/min = 1.692
     sd(log kappa_A) = 0.1733  =>  sd(log(kappa_A/kappa_B)) tren 64 o = 0.2451
                                   max |log(kappa_A/kappa_B)|          = 0.5260
     Cell CHET nam o mot vung KHAC HAN: kappa_A tu 1.611 den 1.877 (~3.5x).
     => nhanh D khong phai "cung thiet ke o mot cho de hon"; no la mot diem
        van hanh khac. Ghi de khong ai doc `NC-B3-3` qua manh.

S-6  Do doc d(acceptance)/d(log kappa) gan nhu MOT HANG SO tren ca 8 cell
     song, do tu chinh trace bisection cua pilot:

         h2@0.650  -0.535    poisson@0.850  -0.497    poisson@0.925  -0.500
         h2@0.675  -0.525    poisson@0.875  -0.493    poisson@0.960  -0.514
         h2@0.700  -0.516    poisson@0.900  -0.495
                                            trung binh ~ -0.509, bien do 8%

     => |acceptance_B(kappa_A) - a*| ~ 0.51 x |log(kappa_A/kappa_B)|
        GAN NHU TAT DINH tren tap nay.
```

Hai he qua truc tiep:

```text
(1) `M-202` (Spearman cua gia `kappa` sai) o nguong +0.60 la HIT gan nhu chac.
    S-6 khien quan he do gan tuyen tinh. Nguong DA DUOC NANG len +0.90, va
    them mot ve DINH LUONG that su rui ro: DO DOC. Xem muc 5.3.

(2) `M-201` ve sd(acceptance) >= 0.060 cung la HIT gan nhu chac:
        sd(acceptance) ~ 0.509 x 0.2451 ~ 0.125
    va -- day moi la diem quan trong -- **neo 0.09201 cua muc 0.1 KHONG phai
    neo dung cho dai luong nay**. Neo do la do TAN cua 8 cell tai `kappa` CO
    DINH. Duoi C3-R, duong cheo bi GHIM vao `a*` theo dinh nghia, nen sd tren
    64 o do DUY NHAT do lech `kappa`. Hai dai luong khac nhau, tinh co gan
    nhau ve so. Nguong DA DUOC DOI thanh mot KHOANG. Xem muc 5.2.
```

> 🔑 Day dung la cong dung cua muc 4: mot du doan chi duoc goi la du doan khi
> no co the SAI. Ca hai muc tren duoc sua TRUOC khi mot dong ma do luong nao
> ton tai, va ly do duoc ghi lai de ai cung kiem duoc.

## 5. Du doan

### 5.1. `M-200` -- KIEM WIRING, khong phai du doan   (dap an DA BIET, muc 0.1)

```text
Chay C3-R voi `kappa` EP BANG 0.50 va `n = 500` tren 8 cell song:
PHAI tai tao duong cheo `transfer_matrix.json` o muc BIT.

Nguong:  max |delta acceptance| = 0.0   VA   max |delta viol| = 0.0
         tren 8/8 cell song.

Vo o day = DUNG duong ong, khong phai phat hien.
```

### 5.2. `M-201` -- MU. Bao toan co song sot o `n` HUU HAN khong?

```text
Tai `n = 250`, tren cac o(A,B,250) co acceptance >= 0.20 (toi da 64 o):
    (a) sd(viol|accept)    <= 0.020            neo toan-n: 0.00289
    (b) sd(acceptance)     thuoc [0.090, 0.180]    (KHOANG -- xem muc 4.2)
    (c) mean(viol|accept)  thuoc [0.05, 0.12]  neo toan-n: 0.08100

HIT khi CA BA dat.
```

```text
[NEO (a)] sd(viol) = 0.00289 tai n = 500, in-distribution, kappa = 0.5.
[CO CHE]  `qhat` la phan vi mau; sai so ~ 1/sqrt(n_eff). Tu 500 -> 250 block,
          sd nhan ~sqrt(2) -> 0.0041. Cong nhieu do `kappa_A != kappa_B`
          (dich diem van hanh doc duong cong) -> noi rong ~5x.
[RUI RO]  neu bao toan VO o `n` huu han, sd(viol) se nhay len ~0.05+ -> MISS.
          Pilot KHONG do mot gia tri `viol` nao, nen (a) va (c) van MU hoan
          toan.

[VE (b)]  DOI so voi ban thao noi bo (`>= 0.060` -> khoang `[0.090, 0.180]`).
          Ly do o muc 4.2: neo 0.09201 la do tan cua 8 cell tai `kappa` CO
          DINH, con dai luong nay do do lech `kappa`. Uoc luong tho tu S-6:
              sd(acceptance) ~ 0.509 x 0.2451 ~ 0.125
          Khoang `[0.090, 0.180]` la +-45% quanh uoc luong do -- MISS duoc o
          CA HAI phia: qua hep neu duong cong phang hon o duoi/tren `a*`,
          qua rong neu co bien phi tuyen o acceptance thap.
```

### 5.3. `M-202` -- MU. Gia cua `kappa` sai co DU DOAN DUOC khong?

```text
Tai `n = 500` (toan bo calib cua B -- moi lech con lai la do `kappa` SAI,
khong phai do nhieu uoc luong), tren 56 o ngoai duong cheo:

    (a) Spearman( |log(kappa_A/kappa_B)| , |acceptance_B - a*| )  >= +0.90
    (b) DO DOC binh phuong toi thieu cua |acceptance_B - a*| tren
        |log(kappa_A/kappa_B)|  thuoc  [0.40, 0.62]

HIT khi CA HAI dat.
Bao cao kem (KHONG cham): cung hai dai luong do tai `n = 250`.
```

```text
[CO CHE]  `kappa` la mot TI SO; lech `kappa` dich diem van hanh doc duong cong
          risk-coverage cua B. Day la doi ung cua `scale ratio` o Task B.
[VE (a)]  Nguong DA DUOC NANG tu +0.60 (ban thao noi bo) len +0.90. Ly do o
          muc 4.2 / S-6: do doc gan nhu hang so tren 8 cell, nen quan he gan
          tuyen tinh va +0.60 se la mot HIT khong mang thong tin. Sua TRUOC
          khi nhanh do luong ton tai.
[VE (b)]  Day moi la ve RUI RO. Neo: -0.509 do tren tach CALIB cua chinh cell
          A, o `n` day du, KHONG tai hieu chuan `qhat`. `M-202` do no tren
          tach TEST cua cell B, sau khi `qhat` DA duoc uoc luong lai. Ba khac
          biet do co the lam do doc lech; `[0.40, 0.62]` la +-20% quanh 0.509.
          Neu do doc roi ra ngoai, ket luan la "elasticity cua `kappa` KHONG
          chuyen giao giua calib va test" -- mot ket qua co noi dung.
```

### 5.4. `M-203` -- MU. Bao dam co duoc KHOI PHUC khong?

```text
Tai `n = 250`:  so o(A,B,250) thoa  (viol|accept <= alpha = 0.10)
                                VA  (acceptance >= 0.20)
                >= 52 / 64
```

```text
[NEO]  Task B-2 TRONG CUNG CELL: viol <= alpha tu n = 30, nhung acceptance
       chi 0.209 o n = 30 va 0.3998 o n = 120.
[RUI RO] 52/64 = 81%; chua cho cho cac o `kappa` lech nang.
```

### 5.5. `M-204` -- MU. GIA phai tra, tinh bang `n`

```text
Dieu kien theo cell B (gop truc A bang TRUNG VI):
    C3-R :  median_A(viol|accept) <= 0.10  VA  median_A(acceptance) >= 0.20
    B2-R :  |acceptance_B2R - a*| <= 0.05

n*(X) = `n` nho nhat trong N_GRID sao cho dieu kien cua X dat o >= 7/8 cell B.

Du doan:  n*(C3-R) thuoc [60, 250]
          n*(B2-R) <= 60
          n*(C3-R) / n*(B2-R) >= 2.0

HIT khi CA BA dat.
```

```text
[NEO]    Task B-2 TRONG CUNG CELL: C3 = 120 (|drift| <= 0.05), B2 = 20.
[CANH BAO] N_GRID bat dau tu 30, nen "n*(B2-R) <= 60" chi co the la 30 hoac
          60. Can duoi 10 cua ban thao KHONG kiem duoc va da bi bo -- ky mot
          can duoi khong the MISS la ky mot cai khong phai du doan.
```

### 5.6. `M-205` -- MU. Ve `err`, hai ben co khac nhau khong?  [KET QUA AM DU KIEN]

```text
Tai acceptance KHOP (luoi 0.70 / 0.50 / 0.30 / 0.15), `n = 250`:
    trung vi | err_C3R - err_B2R |  <= 0.02
    (trung vi tren TAT CA cap (o, muc acceptance) co ca hai ve huu han)

Ky truoc de bao cao TRUNG THUC rang dong gop KHONG nam o day.
Doi ung cua `M-196` (do duoc 0.00526), va dung CHUNG nguong 0.02 de hai ket
qua so sanh duoc voi nhau.
```

### 5.7. `M-206` -- MU. Ve DOI XUNG cua menh de bao toan

```text
Tren 8 cell B, tai `n = 250` (gop truc A bang TRUNG VI):
    sd( err|accept cua B2-R )   >= 0.020     <- B2 de risk TROI
    sd( err|accept cua C3-R )   <= 0.025     <- C3 giu risk

HIT khi CA HAI dat.
```

```text
[NEO]    sd(err|accept) tren 8 cell song, kappa=0.5 toan n, C3 = 0.01583.
         B2-R KHONG co neo nao -- hoan toan mu.
[CO CHE] B2-R ep acceptance = 0.4268 o MOI cell. Nhung do kho cua cell rat
         khac nhau: `err_neo` chay 0.1545 -> 0.2570 (1.66x). Ep cung
         acceptance tren cac cell co `err_neo` khac nhau => `err|accept` phai
         troi theo `err_neo`.
[THO]    neu err|accept ~ err_neo x he so gan nhu khong doi thi
         sd(err_B2R) ~ 0.0387 x 0.33 ~ 0.013 -- KHONG lon hon 0.0158 cua C3
         mot cach ro rang. Day la mot du doan THUC SU RUI RO. Rat co the MISS.
```

⚠️ **Cach doc neu MISS theo chieu nguoc -- ghi TRUOC:**

> Menh de bao toan ton tai o muc `viol`, KHONG o muc `err`. C3 giu bao dam ve
> SCORE, khong giu bao dam ve QUYET DINH. Cau noi giua hai muc la DIEU KIEN
> TACH ROI, va no chua duoc do o day. Day la mot ket qua AM quan trong: no
> BUOC paper phat bieu o muc `viol` va cam truot sang muc `err`, va no chi
> thang sang Phase 24.

`M-206` la ma DE MISS NHAT cua bo nay -- co y. Mot amendment ma moi ma deu
HIT la mot amendment ky qua de.

## 6. Doi chung

```text
NC-B3-0  WIRING     `M-200`, muc 5.1.

NC-B3-1  DUONG      Tai `n = 250`, B1-R (score NGAU NHIEN) trung `a*` KHONG
                    kem B2-R:
                        |acc_B1R - a*| <= 0.05           o >= 7/8 cell B
                    NHUNG
                        err|accept(B1R) >= 0.90 x anchor_err   o >= 7/8 cell B
                    => "trung muc tieu acceptance" mot minh la VO GIA TRI.
                    Doi ung `NC-2` / `L99`. Doi chung nay PHAI FIRE.

NC-B3-2  CAU TRUC   B2-R va B1-R TRUNG BIT theo truc A (S-2), tren MOI
                    `(B, n, draw)`: max |delta| = 0.0 tren 8 gia tri A,
                    cho ca `acceptance_test`, `err_given_accept`, `c`.
                    Khong trung => wiring hong, DUNG lai.

NC-B3-3  AM         Tren 4 cell CHET tai `n = 250` (gop truc A bang trung vi):
                    | err|accept(C3-R) - anchor_err | <= 0.02  o >= 3/4 cell.
                    => con so do o cell song khong phai hien vat duong ong.

NC-B3-4  AM         Tai `n = 30` (ngay tren san 29): ti le lan chay co
                    `qhat_source == degenerate_fallback_to_none` phai DUONG
                    va duoc bao cao. (`L100`: hai co cu se MU o vung nay --
                    dung `qhat_source`.)
```

## 7. Gate

| Gate | Noi dung | Nguong |
|---|---|---|
| G23-261 | `M-200` kiem wiring: C3-R tai `kappa`=0.50, `n`=500 tai tao duong cheo `transfer_matrix.json` | max abs delta = 0.0 tren 8/8 |
| G23-262 | `M-201` bao toan o `n` huu han (n=250) | sd(viol) <= 0.020 VA sd(acc) trong [0.090, 0.180] VA mean(viol) trong [0.05, 0.12] |
| G23-263 | `M-202` gia cua `kappa` sai co du doan duoc (n=500, 56 o) | Spearman >= +0.90 VA do doc trong [0.40, 0.62] |
| G23-264 | `M-203` bao dam duoc khoi phuc (n=250) | >= 52/64 o |
| G23-265 | `M-204` gia tinh bang `n` | n*(C3-R) trong [60,250] VA n*(B2-R) <= 60 VA ti so >= 2.0 |
| G23-266 | `M-205` ket qua AM ve `err` tai acceptance khop (n=250) | trung vi \|derr\| <= 0.02 |
| G23-267 | `M-206` ve DOI XUNG cua bao toan (n=250) | sd(err B2-R) >= 0.020 VA sd(err C3-R) <= 0.025 |
| G23-268 | `NC-B3-1` doi chung DUONG -- PHAI FIRE | 7/8 VA 7/8 |
| G23-269 | `NC-B3-2` + `NC-B3-3` + `NC-B3-4` | trung bit; 3/4; ti le > 0 |

## 8. Chan dung (stop rules)

```text
1. Pilot fail (muc 4)                       -> RAISE, amendment con
2. `NC-B3-2` khong trung bit                -> wiring hong, DUNG
3. `M-200` khong trung bit                  -> duong ong hong, DUNG
4. > 20% o co `n_accept = 0` tai `n >= 120` -> thiet ke sai san acceptance,
                                               DUNG va ky lai san
```

## 9. No ghi TRUOC (se khong duoc coi la phat hien sau)

```text
N1  `L92` van rang buoc: 8 cell song van co ho tai ghep hoan toan voi muc tai.
    Moi phat bieu cua B-3 la "qua CHE DO VAN HANH", KHONG phai "qua HO TAI".
N2  `a*` la MOT lua chon thiet ke. Do nhay theo `a*` chua do.
N3  `kappa_A` duoc do tren CALIB cua A voi `n` DAY DU. Chi phi uoc luong chinh
    `kappa_A` tu `n` huu han chua do.
N4  `L100` chua sua trong `config_matrix.py` (co y). Dung `qhat_source`.
N5  San acceptance 0.20 la mot LUA CHON. Neu dat 0.30 thi `n*` se nhay len;
    do nhay theo san chua do.
N6  `a*` = 0.42679 duoc do tren tach TEST (`taxonomy_audit.json`), con
    `kappa_A` duoc giai tren tach CALIB. Hai tach khac nhau, nen acceptance
    cua C3-R tren duong cheo se lech `a*` mot chut ngay ca o `n = 500`. Do la
    nhieu tach mau, cung hinh dang voi `L98`; no KHONG duoc doc thanh "C3
    khong trung muc tieu".
```

## 10. Pham vi anh huong

```text
KHONG doi mot con so nao cua `transfer_matrix.json` hay
    `recalibration_cost.json`.
KHONG doi phan quyet `G23-248 .. G23-260`.
Task B-3 la mot module MOI, khong dung vao duong ong Task B / B-2 ngoai
    viec DOC LAI `subsample_blocks`, `fit_config`, `load_cell`, `cells_by_role`.
```
