# AMENDMENT 23-26 -- Nhan [TAT DINH], nhay cam luoi cua K-6, va so gate kiem duoc bang may

Ngay: 2026-08-19
Commit: sau `9b163dd` (Amendment 23-25), TRUOC khi viet `cert/abstain_cost.py`.

Amendment nay KHONG sua mot dai khoa nao. No:

```text
(1) HA NHAN bon dong du doan K-1/K-3/K-4/K-5
(2) ghi ba phat hien hau kiem F-23.6-0/1/2 duoi nhan [TAT DINH] / [MO TA]
(3) khoa mot thu tuc MOI (NT-v2-11) cho cac lesson CHUA CHAY
(4) mo rong pham vi de dung so gate kiem duoc bang may
(5) khoa quy uoc dat ten file amendment sau khi bang chu cai het slot
(6) khoa mot quy tac hien thuc cho gamma = 0 (K-D8) -- lo hong cua K-D4
```

Moi con so trong tai lieu nay duoc tinh lai doc lap tu artifact trong repo
ngay 2026-08-19. Lenh tai tao nam o muc 9.

---

## 0. Quy uoc dat ten file amendment -- bang chu cai da het

```text
Hien tai: 00b = amd 1 ... 00z = amd 25. Het slot.
Chon    : 00za = amd 26, 00zb = 27, ... 00zz = 51.
Ly do   : "00z-" < "00za" theo thu tu byte ('-' = 0x2D < 'a' = 0x61),
          nen `ls` va `git ls-files` van cho dung thu tu thoi gian.
Bac bo  : "00aa" -- sap TRUOC "00b", pha thu tu doc lich su quyet dinh.
Bac bo  : doi ca 25 file sang zero-padded -- chi phi sua tham chieu cheo qua cao.
```

```text
NT-v2-10  Moi quy uoc dat ten dung lam KHOA SAP XEP phai co mot test chung minh
          thu tu TU DIEN trung voi thu tu SO. Khoa sap xep tu che luon het cho;
          neu no het cho mot cach im lang, lich su quyet dinh bi doc sai.
```

Thuc thi: `test/test_phase23_gate_ledger.py::test_amendment_filenames_sort_by_number`
va `::test_amendment_numbers_are_contiguous_from_one`.

---

## 1. NT-v2-9 -- nhan [TAT DINH] cho dai luong tinh duoc tu artifact da co

### 1.1. Phat hien

Bon dong `K-1`, `K-3`, `K-4`, `K-5` cua Lesson 23.6 duoc ky voi nhan
`[NGOAI SUY]` / `[CO CHE]`. Ca bon deu tinh duoc bang DAI SO DONG tu mot file
DA NAM TRONG REPO tu Lesson 23.3:

```text
nguon: results/phase-23/baseline_rankings_<cell>_C3_static.json
khoa : sweeps.C3_conformal[i].{coverage, err_accept, err_reject}
       anchor_always_trust.err

cong thuc: c*(gamma) = (R_neo - gamma * R|accept(gamma)) / (1 - gamma)
```

Khong can chay gi moi. Khong can du lieu moi. Ba phep tinh so hoc.

### 1.2. Nguyen tac

```text
NT-v2-9  Mot dong du doan chi duoc mang nhan [CO CHE] hoac [NGOAI SUY] neu
         dai luong do KHONG tinh duoc bang dai so dong tu artifact da co
         trong repo tai thoi diem ky.

         Thu tuc thuc thi -- voi MOI dong, truoc khi ky, hoi:
             "Toi co tinh duoc so nay ngay bay gio bang grep + may tinh khong?"
         Neu CO   -> nhan dung la [TAT DINH], va dong do KHONG tinh diem du doan.
         Neu KHONG -> nhan theo nguon suy dien nhu cu.

         Ly do: mot "du doan" ma nguoi ky co the tinh ra truoc khong kiem dinh
         dieu gi. No kiem tra TINH NHAT QUAN cua duong ong, mot viec CAN THIET
         nhung KHAC voi kiem dinh du doan. Gop hai thu lam mot lam phong dai
         thanh tich pre-registration.
```

Day la mo rong tu nhien cua `NT-v2-8` (Amendment 23-25 muc 3.1) va dung tien le
da ap cho `A-1'..A-4'`, `A-7'`, `A-8'` (`00-preregistration.md`, ghi chu duoi bang).

### 1.3. Ap dung -- doi nhan, KHONG doi dai, KHONG doi ket qua

| Dong | Nhan cu | Nhan moi | Tinh diem du doan? |
|---|---|---|:--:|
| K-1 `c*_err(0.78)` | [NGOAI SUY] | **[TAT DINH]** | KHONG |
| K-2 `c*_err(0) = R_neo` | [TAT DINH] | [TAT DINH] (giu) | KHONG |
| K-3 `c*_err(0.50)` | [NGOAI SUY] | **[TAT DINH]** | KHONG |
| K-4 `F2` co vuot `c*` o 0.78? | [CO CHE] | **[TAT DINH]** | KHONG |
| K-5 so cell co `c*(0.78) > err_neo` | [CO CHE] | **[TAT DINH]** | KHONG |
| K-6 don dieu | [GATE bo chon] | [GATE bo chon] (giu) | -- (la gate) |
| K-7 `c_supt` tren 50 diem | [CO CHE] | [CO CHE] (giu) | **CO** |
| K-8 `c_supt / c_bonf(50)` | [CO CHE] | [CO CHE] (giu) | **CO** |

`K-7` va `K-8` giu nhan `[CO CHE]` vi chung la dai luong bootstrap: khong tinh
duoc bang dai so dong, va mot mo phong tong hop DA CHAY TRUOC khi ky
(Amendment 23-25 muc 7.1). Chung la hai dong du doan THAT cua Lesson 23.6.

### 1.4. Gia tri da tinh -- ghi lai voi provenance day du

Cac so duoi day duoc tinh SAU khi Amendment 23-25 duoc ky va commit tai
`9b163dd`. Do la do luong HAU-KHOA hop le, khong phai peeking. Ghi ra day de
`cert/abstain_cost.py` phai TAI TAO dung chung.

Diem van hanh la o luoi `coverage` chi so 78; coverage DO DUOC la `0.779999`,
khong phai `0.78` chan. Moi phep tinh duoi day dung coverage DO DUOC.

```text
cell             R_neo       gamma(do)   R|accept    c*(0.78)    c_F2(0.78)
─────────────────────────────────────────────────────────────────────────────
poisson@0.925   0.222399    0.779999    0.157259    0.453347     0.394852
poisson@0.850   0.220727    0.779999    0.154210    0.456556     0.470739
h2@0.700        0.126536    0.779999    0.059486    0.364260     0.381833
```

```text
K-1  0.453347031   trong dai 0.42-0.47   (khong tinh diem, [TAT DINH])
K-2  0.222398678   = R_neo               (dat theo DINH NGHIA; xem K-D8)
K-3  0.361248565   trong dai 0.30-0.40   (khong tinh diem, [TAT DINH])
K-4  c_F2 = 0.394852 < c* = 0.453347  -> F2 KHONG vuot; certificate CO LAI
K-5  3/3 cell co c*(0.78) > err_neo
     0.453347 > 0.222399 ; 0.456556 > 0.220727 ; 0.364260 > 0.126536
```

Ghi chu bat buoc cho `K-4`: dong nay noi ve CELL CHINH. Tren `poisson@0.850`
dau NGUOC lai (`c_F2 = 0.470739 > c* = 0.456556`), tuc F2 STATIC VUOT nguong
hoa von o do. Dieu nay nhat quan voi `05-cross-cell.md` (`gap_closed@0.78`
am o hai cell moi) va PHAI duoc viet ra o `11-abstain-cost.md`, khong duoc de
nguoi doc suy rong `K-4` ra ba cell.

### 1.5. K-D8 -- lo hong cua K-D4 tai `gamma = 0`

`K-D4` loai `gamma = 1.0` khoi luoi vi tap reject rong. Kiem tra doc lap cho
thay dau kia cua luoi cung hong, va `K-D4` IM LANG ve no:

```text
Tai gamma = 0:  n_accept = 0  =>  err_accept = null trong artifact.
Cong thuc khoa:  (R_neo - gamma * R|accept) / (1 - gamma)
                 = (0.222399 - 0.0 * null) / 1.0
                 = nan          <- KHONG phai 0.222399
```

Ve toan hoc `c*(0) = R_neo` la dung theo DINH NGHIA (`gamma = 0` => tu choi tat
ca => tap reject la toan bo tap test => `R|reject = R_neo`). Nhung cong thuc
khong tu suy ra dieu do, vi `0 * undefined` khong phai `0`.

```text
K-D8  `cert/abstain_cost.py` PHAI xu ly rieng `gamma = 0`:
          neu n_accept == 0 thi c*(gamma) := R_neo, khong danh gia cong thuc.
      `NC23v2-4` duoc doc lai la: doi chung nay kiem DINH NGHIA (nhanh dac
      biet), khong kiem cong thuc.
      Luoi K-D4 co 50 DIEM nhung chi 49 diem HUU HAN neu khong co nhanh nay.
```

Day la mot bac tu do CHUA khoa bi phat hien TRUOC khi chay code, nen viec khoa
no o day la hop le theo `NT-v2-3` -- khac han truong hop `F-23.6-2` (muc 4),
noi so da bi nhin.

---

## 2. F-23.6-0 -- dong nhat thuc tai tao chinh xac tu artifact v1

Trang thai: **[TAT DINH]**, kiem tra dung code, khong phai ket qua.

```text
Delta_du_bao = (1 - gamma) * (c_F2 - c*)        vs   Delta DO DUOC o Lesson 23.3
                                                     (err_delta_vs_anchor)

cell             du bao            do duoc          |sai lech|
──────────────────────────────────────────────────────────────
poisson@0.925   -0.01286884934    -0.01286884934     1.4e-17
poisson@0.850   +0.00312020593    +0.00312020593     6.1e-18
h2@0.700        +0.00386625517    +0.00386625517     1.3e-17
```

Sai lech KHONG phai `0` tuyet doi -- no la nhieu dau phay dong o muc `1e-17`,
tuc ~100 ulp cua `float64` quanh `1e-2`. `G23-32` dat nguong `1e-12`, con du
5 bac an toan.

`G23-32` (`R_system(gamma, c*) == R_neo`, nguong `1e-12`) DA dat TRUOC khi viet
code. Dieu nay xac nhan `K-D7`: dong nhat thuc la DINH LY, va `G23-32` la kiem
tra DUNG CODE chu khong phai mot ket qua khoa hoc.

---

## 3. F-23.6-1 -- "beneficial band" cua v1 CHINH LA vung `c_F2 < c*`

Trang thai: **[TAT DINH]**. Doi chung cheo BAT BUOC cho Lesson 23.6.

Ban thao dau tien cua muc nay chi doi chieu `band_low`. Kiem tra doc lap cho
thay `poisson@0.850` co HAI diem doi dau, khong phai mot -- va diem thu hai
chinh la `band_high`. Bo sot no la mot loi cua ban thao; doi chung dung phai
phu CA HAI dau mut.

```text
cell            band_low   khoang doi dau     band_high  khoang doi dau
                (v1)       cua (c_F2 - c*)    (v1)       cua (c_F2 - c*)
──────────────────────────────────────────────────────────────────────────
poisson@0.925    0.60760   (0.60, 0.61)       0.99995    ngoai luoi (> 0.99)
poisson@0.850    0.80910   (0.80, 0.81)       0.98920    (0.98, 0.99)
h2@0.700         0.84285   (0.84, 0.85)       0.99995    ngoai luoi (> 0.99)
```

Khop 4/4 dau mut nam trong luoi, moi cai trong mot buoc luoi `0.01`. Hai lesson
tinh HAI duong khac nhau tu CUNG du lieu; chung phai gap nhau.

```text
C23v2-1  (doi chung cheo, BAT BUOC)
         Voi moi cell, tap diem doi dau cua (c_F2 - c*) tren luoi coverage phai
         khop tap dau mut {band_low, band_high} cua beneficial_band_err.C3_conformal
         (`baseline_rankings_<cell>_C3_static.json`), sai so <= 1 buoc luoi (0.02).
         Dau mut nam ngoai luoi (band_high = 0.99995) duoc MIEN, va viec mien
         phai duoc ghi ro trong artifact bang khoa `endpoint_out_of_grid`.
         Thuc thi: test/test_phase23_abstain_cost.py
```

Neu `cert/abstain_cost.py` cho diem cat khac `band_low` qua mot buoc luoi thi
CO BUG, va neu no bo sot `band_high` cua `poisson@0.850` thi cung CO BUG.

He qua ve dien giai, phai viet vao `06-reframe.md`:

```text
Lesson 23.6 KHONG kham pha ra vung co loi. v1 da do no roi (beneficial_band).
Cai 23.6 lam la: (a) DAT TEN cho no bang mot dai luong khong nhac den P1,
(b) do no KEM DAI TIN CAY lan dau, (c) tong quat hoa sang fallback bat ky.
Viet khac di la noi qua.
```

---

## 4. F-23.6-2 -- K-6 nhay cam voi do min cua luoi

Trang thai: **[MO TA]**, phat hien HAU KIEM, **KHONG tinh diem**,
**KHONG thay the K-6**.

### 4.1. K-6 duoc cham DUNG NHU DA KY -- khong dung toi

```text
K-6 phat bieu : c*(gamma) don dieu khong giam
K-6 luoi khoa : K-D4, np.arange(0.0, 1.0, 0.02) -> 50 diem, gamma = 1.0 bi loai
                49 diem huu han (gamma = 0 xu ly bang K-D8), 48 so gia
K-6 KET QUA   : PASS -- 0 vi pham tren 3/3 cell

Dong nay KHONG duoc sua. Dai khong duoc noi. Ket qua khong duoc dien giai lai.
```

### 4.2. Phat hien hau kiem

Tren luoi min gap doi (buoc `0.01`, co san tu `coverage_grid` cua Lesson 23.3):

```text
                     LUOI 0.02 (DA KHOA)      LUOI 0.01 (HAU KIEM, [MO TA])
cell                 n_huu_han  n_vi_pham     n_huu_han  n_vi_pham
────────────────────────────────────────────────────────────────────
poisson@0.925            49         0             99         4
poisson@0.850            49         0             99         3
h2@0.700                 49         0             99         0

Chi tiet vi pham tren luoi 0.01:
cell             gamma            do lon        n_reject tai diem sau
──────────────────────────────────────────────────────────────────────
poisson@0.925    0.88 -> 0.89     -0.000032          54,996
                 0.93 -> 0.94     -0.004843          29,998
                 0.97 -> 0.98     -0.008983           9,999
                 0.98 -> 0.99     -0.041453           5,000   << NGOAI luoi khoa
poisson@0.850    0.87 -> 0.88     -0.001640          59,996
                 0.97 -> 0.98     -0.004081           9,999
                 0.98 -> 0.99     -0.004557           5,000   << NGOAI luoi khoa
h2@0.700         --               --                 --
```

Trong pham vi luoi khoa (`gamma <= 0.98`): 3 / 2 / 0 vi pham.

Vi pham LON NHAT (`-0.041453`) nam o `gamma = 0.98 -> 0.99`, tuc HOAN TOAN
NGOAI luoi da khoa (`K-D4` dung o `0.98`). Khong co gi bat hop le o day, nhung
phai noi ro; neu khong, nguoi doc tuong con so bi giau.

### 4.3. Doc dung -- ba diem

```text
(1) VI TRI, khong phai DO LON, la thong tin chinh. MOI vi pham nam o
    gamma >= 0.87, tuc tap reject chi con 1-13% so hang (5,000 - 60,000 tren
    499,967). Do la vung phan giai thap, khong phai vung van hanh
    (diem van hanh la 0.78, noi tap reject con 109,993 hang).

(2) DO LON nam trong nhieu. Sai so chuan cua mot ti le tren tap reject o
    gamma = 0.97, voi don vi mau hieu dung la BLOCK (bai hoc muc 3 cua
    08-studentized-and-go-debts.md, n_calib_blocks = 500), co ~ sqrt(0.25/500)
    ~ 0.022. Vi pham lon nhat TRONG luoi khoa la 0.009 -- duoi mot SD.
    NHUNG day la LAP LUAN, chua phai PHEP DO. Xem K-10.

(3) DAY LA LAN THU HAI cung mot loai loi trong Phase 23:
       23.5[B] Phat hien 8 : GO-1 FAIL tren luoi kappa goc, PASS tren luoi min
       23.6    F-23.6-2    : K-6 FAIL tren luoi gamma min, PASS tren luoi tho
    Hai lan, hai CHIEU nguoc nhau, cung mot nguyen nhan goc: mot dai luong
    TICH PHAN hoac DON DIEU duoc danh gia tren luoi roi rac ma do min cua luoi
    KHONG duoc khoa -- vi pham NT-v2-3.
```

### 4.4. Vi sao KHONG sua K-6

```text
Sua nguong sau khi thay no truot la p-hacking, ke ca khi ly do ky thuat dung.
Tien le da lap trong repo nay:
   A-1'..A-4', A-7', A-8'  bi HA NHAN thay vi duoc noi dai (00-preregistration.md)
   A-5'                    giu MISS du luoi quyet dinh da doi (Amd 23-24 muc 1)
   S-5                     giu MISS (Amd 23-21 muc 3)
F-23.6-2 duoc xu ly GIONG HET: ghi lai, nhan [MO TA], khong tinh diem.
```

Phan biet phai giu ro trong dau:

```text
                 nhin de SUA DAI            nhin de PHAT HIEN THIEU SOT THU TUC
hanh dong        noi nguong cho vua so      phat hien mot bac tu do chua khoa
he qua           duong tinh gia             thu tuc chat hon cho tuong lai
xu ly            CAM                        ghi [MO TA], khoa thu tuc cho sau
vi du o day      "doi K-6 thanh <= tol"     "K-6 chua khoa do min luoi"
```

`K-D8` (muc 1.5) thuoc cot PHAI va duoc khoa binh thuong, vi no duoc phat hien
tu MA NGUON/ARTIFACT chu khong tu ket qua cham diem.

---

## 5. Thu tuc MOI -- khoa cho cac lesson CHUA CHAY

```text
NT-v2-11  MOI gate phat bieu ve mot TINH CHAT CUA DUONG CONG (don dieu, loi,
          bao hoa, giao nhau) phai khoa CA HAI:
             (a) luoi danh gia, va
             (b) mot luoi min gap doi de bao cao doi chieu.
          Ket luan chinh dung luoi (a). Luoi (b) BAT BUOC bao cao, va neu hai
          luoi khong dong y thi su khong dong y do la MOT KET QUA phai viet ra,
          khong phai mot chi tiet ky thuat duoc bo qua.

          Ap dung tu Lesson 23.9 tro di. Ap NGUOC lai cho 23.6 chi o muc
          BAO CAO (F-23.6-2), khong o muc GATE.
```

Ba dong du doan MOI. `K-9` va `K-11` da nhin so nen **khong tinh diem**;
`K-10` chua ai tinh nen **tinh diem**.

```text
K-9   So vi pham don dieu tren luoi 0.01, gamma <= 0.98, cell chinh
      Nhan [MO TA] -- DA NHIN SO, khong tinh diem.    Ghi: 3

K-10  Voi MOI vi pham, bootstrap ghep cap theo block cua so gia
          Delta(gamma) = c*(gamma + h) - c*(gamma)
      cho CI95 CHUA 0.
      Nhan [CO CHE], B = 2000, cung cau truc seed voi 23.5[B].
      Du doan: CO, voi moi vi pham tren ca hai cell (7 vi pham).
      TINH DIEM -- chua ai tinh CI nay.
      Neu SAI (mot CI nam hoan toan duoi 0): certificate xep hang SAI o vung
      gamma do, phai dieu tra, KHONG duoc bo qua.

K-11  Moi vi pham nam o gamma >= 0.85.
      Nhan [MO TA] -- DA NHIN SO, khong tinh diem.    Ghi: CO (min = 0.87)
```

`K-10` la dong quan trong. No bien mot LAP LUAN ("0.009 duoi mot SD") thanh mot
PHEP DO, dung nguyen tac da lap o `10-go2-simultaneous.md` muc 1.2:
*nguong phai dan tu do phan giai cua chinh phep do, khong tu mot hang so tuy y.*

---

## 6. RA SOAT DU DOAN (NT-v2-7 ap cho chinh amendment nay)

| Dong da khoa | Xu ly | Ly do |
|---|---|---|
| K-1, K-3, K-4, K-5 | **HA NHAN** -> [TAT DINH] | NT-v2-9; dai KHONG doi, ket qua KHONG doi |
| K-2 | GIU NGUYEN | da dung nhan; bo sung K-D8 lam ro cach tinh |
| K-6 | **GIU NGUYEN HOAN TOAN** | khong duoc sua sau khi nhin so (muc 4.4) |
| K-7, K-8 | GIU NGUYEN | du doan that, co mo phong truoc |
| C-1..C-5 (GO-2) | GIU NGUYEN | khong lien quan |
| A-*', S-5, S-8, G3a/G3b | GIU NGUYEN | khong lien quan |
| F0..F6, T2..T4, B1p..B6p | GIU NGUYEN | khong lien quan |
| H-23.11-1..6 | GIU NGUYEN; NT-v2-11 se ap o 23.11 | khong sua cai cu |
| K-D4 | KHONG SUA; BO SUNG K-D8 | K-D8 xu ly dau `gamma = 0`, khong dong toi luoi |

Ra soat `NT-v2-9` NGUOC lai toan bo bang hien co -- dong nao tinh duoc bang dai
so dong tu artifact tai thoi diem ky?

```text
Da o dung nhan [TAT DINH] hoac [MO TA] khong tinh diem:
   C-2, A-1', A-2', A-3', A-4', A-7', A-8', K-2, F0
Kiem lai va XAC NHAN van dung nhan suy dien:
   F1..F6, T2..T4, B1p..B6p  -- deu duoc ky TRUOC khi artifact tuong ung ton tai
   G3a, G3b, S-5, S-8        -- can chay studentized_score.py, chua ton tai luc ky
   C-1, C-3, C-4, C-5        -- can bootstrap 2000 draw, khong tinh dong duoc
   A-5', A-6', A-6'b         -- can CI bootstrap, khong tinh dong duoc
   K-7, K-8                  -- can bootstrap tren luoi gamma

Ket luan ra soat: CHI co K-1/K-3/K-4/K-5 bi sai nhan. Cac bang truoc khong
bi anh huong.
```

---

## 7. Mo rong pham vi -- so gate kiem duoc bang may

Bo sung vao pham vi cua Amendment 23-25 muc 8:

```text
* them docs/phase-23/GATES.md              -- so gate, mot dong mot gate
* them test/test_phase23_gate_ledger.py    -- lam do neu so gate lech

KHONG sua: cert/config_matrix.py, cert/conformal_simultaneous.py,
           cert/aurc_go1.py, cert/go2_simultaneous.py, cert/studentized_score.py
```

### 7.1. F-A1 -- do chinh xac cua phat hien, sau khi kiem lai

Ban thao dau tien phat bieu "toan bo tam ma `G23-24..G23-31` khong ton tai
trong repo". Phat bieu do QUA MANH. Do duoc:

```text
grep -rhoE "\bG23-[0-9]+[a-z]?\b" docs/ cert/ test/   (2026-08-19)

CO trong repo   : G23-25, G23-26, G23-27, G23-27b   (08-studentized-and-go-debts.md)
KHONG co        : G23-24, G23-28, G23-29, G23-30, G23-31
```

Nam ma thieu, khong phai tam. Ket luan van giu nhung phai phat bieu dung:

```text
NT-v2-12  Mot ID (gate, du doan, doi chung, gioi han) khong ton tai trong repo
          la mot ID KHONG TON TAI. Neu paper trich no ma `grep` khong tim ra,
          tinh tai tao bi vo o muc DINH DANH -- truoc ca muc so lieu.
```

`G23-71` ("bang gate du 4 muc, khong con NOT_RUN") KHONG kiem duoc bang may khi
5 trong so cac ma no phai kiem khong ton tai o dau ca. `GATES.md` dong lo hong do.

### 7.2. Muc CON NO van MO -- `PLAN_v2.md`

`PHASE_23_v2` van KHONG co trong repo (giong `MASTER_PLAN.md` va `PHASE_23.md`
goc; xem `docs/phase-23/PLAN.md` dong dau va Amendment 23-25 muc 1.3). Ban ke
hoach do khong nam trong tam tay khi viet amendment nay, nen KHONG duoc dua vao.

Hau qua phai ghi ro, khong duoc lam mo:

```text
* Anh xa lesson cua G23-33 .. G23-73 trong GATES.md la TAM DINH (provisional).
  No duoc chep tu ban ke hoach song NGOAI repo va CHUA doi chieu duoc.
* Can tren 73 cua tam gate cung la TAM DINH.
* K-D0b (Amendment 23-25) van MO: khi PLAN_v2.md vao repo, phai ra soat toan bo
  §8 cua no NGAY luc do, va doi chieu lai anh xa lesson trong GATES.md.
* Hai test doi chieu ke hoach trong test_phase23_gate_ledger.py se SKIP cho toi
  khi file do ton tai. Skip la mot mon no HIEN, khong phai mot test xanh.
```

### 7.3. Trang thai `DEBT` -- them vao tu vung, va ly do

Khi lap `GATES.md` day du (khong chi tam `24..73`), phat hien them:

```text
G23-10, G23-12a, G23-12b  -- DUOC DINH NGHIA (00-preregistration.md muc 5;
                             00o-amendment-14.md) nhung KHONG duoc cham o bat ky
                             bang gate nao cua 02/03/04/05/99-*.md.
G23-11                    -- la ALIAS cua PC23-1, khong phai gate rieng
                             (99-gate-decision.md, ghi chu ten).
```

Ba ma dau khong phai `NOT_RUN` (lesson cua chung DA DONG) va cung khong phai
`PASS`/`FAIL` (khong ai cham). Gan cho chung mot trong sau muc cu deu la noi doi.

```text
Them vao tu vung trang thai:
DEBT   gate DA DUOC DINH NGHIA nhung CHUA duoc cham o bat ky bang nao, trong
       mot lesson DA DONG. Day la mot mon no HIEN, phai co evidence tro toi
       noi no duoc dinh nghia.

Tap DEBT duoc GHIM trong test. Them mot mon no moi ma khong sua test se lam
DO test -- day chinh la muc dich: no khong duoc phep xuat hien im lang.
```

---

## 8. Cham lai gate cua Lesson 23.5 -- khong doi ket qua nao

Ghi vao `GATES.md` lan dau, tu bang chung DA CO trong repo:

```text
G23-24  PASS        00-preregistration.md dong 203-204 (G3a/G3b da dien)
G23-25  PASS        0.9095 / 0.9113 / 0.9048
G23-26  PASS        max_abs_diff = 0.0, 12/12 o
G23-27  UNDETECTED  drop 8.9e-4 / 3.5e-4 / 7.4e-4 -- KHONG PHAI PASS
G23-27b PASS        PC-S-1d, leaked vo don dieu theo p, 3/3 cell
G23-28  PASS        test_phase23_studentized.py::test_T8_status_label_is_enforced
G23-29  PASS        5/5 cell co aurc_go1_<cell>.json
G23-30  PASS        CI95_high refined 1.001992 / 1.002946 / 1.003173 < 1.02
G23-31  PASS        width_relative_change 0.0150; mc_error_shrink 2.565
```

Sua so voi ban thao: `G23-28` KHONG co test ten `test_status_is_exploratory`.
Test that su thuc thi no la `test_T8_status_label_is_enforced`
(`test/test_phase23_studentized.py:104`). Tro sai ten test la dung loai loi ma
`NT-v2-12` noi toi.

`G23-27` mang trang thai rieng `UNDETECTED`. Cau duoc phep viet trong paper:

```text
DUOC:   "Doi chung duong cho ro ri sigma o p = 3 khong phat hien duoc su tut
         bao phu. Chung toi chung minh phep do KHONG mu: tang len p_per_bin =
         300 va 3000 cho tut 0.027 va 0.215 tren ca ba cell, don dieu theo p.
         Muc ro ri o p = 3 nam duoi do phan giai, dung nhu can O(p/n_eff)."
KHONG:  "Doi chung duong PASS."
```

---

## 9. Tai tao

```text
python - <<'PY'
import json
for c in ('poisson_0.925', 'poisson_0.850', 'h2_0.700'):
    d = json.load(open(f'results/phase-23/baseline_rankings_{c}_C3_static.json'))
    R = d['anchor_always_trust']['err']
    s = d['sweeps']['C3_conformal']
    cs = [R if r['n_accept'] == 0 else            # K-D8: gamma = 0
          (None if r['n_reject'] == 0 else        # K-D4: gamma = 1 loai
           (R - r['coverage'] * r['err_accept']) / (1.0 - r['coverage']))
          for r in s]
    for lo, hi, step, tag in ((0, 99, 2, '0.02 KHOA   g<=0.98'),
                              (0, 99, 1, '0.01 min    g<=0.98'),
                              (0, 100, 1, '0.01 min    g<=0.99')):
        ii = [i for i in range(lo, hi, step) if cs[i] is not None]
        v = [i for a, i in zip(ii, ii[1:]) if cs[i] - cs[a] < 0]
        print('%-14s %s  n_diem %3d  n_vi_pham %d' % (c, tag, len(ii), len(v)))
PY
```

Ket qua DO DUOC ngay 2026-08-19:

```text
poisson_0.925  0.02 KHOA   g<=0.98  n_diem  50  n_vi_pham 0
poisson_0.925  0.01 min    g<=0.98  n_diem  99  n_vi_pham 3
poisson_0.925  0.01 min    g<=0.99  n_diem 100  n_vi_pham 4
poisson_0.850  0.02 KHOA   g<=0.98  n_diem  50  n_vi_pham 0
poisson_0.850  0.01 min    g<=0.98  n_diem  99  n_vi_pham 2
poisson_0.850  0.01 min    g<=0.99  n_diem 100  n_vi_pham 3
h2_0.700       0.02 KHOA   g<=0.98  n_diem  50  n_vi_pham 0
h2_0.700       0.01 min    g<=0.98  n_diem  99  n_vi_pham 0
h2_0.700       0.01 min    g<=0.99  n_diem 100  n_vi_pham 0
```

Doc bang nay:

```text
* Dong `0.02 KHOA` la K-6 nhu DA KY:  0 vi pham, 3/3 cell, PASS.
* Dong `0.01 min g<=0.98` la K-9:     3 / 2 / 0 vi pham (TRONG pham vi luoi khoa).
* Dong `0.01 min g<=0.99` them mot vi pham moi cell o buoc 0.98 -> 0.99,
  tuc NGOAI luoi khoa. Do la cot cuoi cua bang muc 4.2.
* n_diem o day dem CA gamma = 0 (nho K-D8), nen lon hon bang muc 4.2 dung 1.
  So VI PHAM khong doi giua hai cach dem, vi c*(0) = R_neo la gia tri nho nhat
  tren duong nen so gia dau tien luon duong.
```

---

## 10. Chu ky

```text
Nguoi ky : vantai (Claude-assisted)
Ngay     : 2026-08-19
```

Toi xac nhan: khong mot dai khoa nao bi noi rong trong amendment nay; bon dong
bi HA NHAN va khong dong nao duoc doi dai; `K-6` giu nguyen phat bieu, giu
nguyen luoi, va giu nguyen ket qua `PASS`.
