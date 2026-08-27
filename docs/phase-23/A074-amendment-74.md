# AMENDMENT 23-74 -- LESSON 23.24: KHONG GIAN HANH DONG HIEU DUNG

Ngay ky : 2026-08-27

Moc     : sau tag `lesson-23-23-complete`, TRUOC dong code cham diem dau
          tien cua Lesson 23.24  (`A071` R1)

Loai    : TIEN DANG KY mot chum phep do
          + PHAN XU `L21` / `L43` (hai cach doc "hanh dong chet")
          + KHOA dinh nghia bo dem "Lan bo qua" (`L129`)

## 0. Cau hoi chan (`A071` R4)

> "Neu KHONG chay Lesson 23.24, paper mat cau nao trong `CLAIMS.md`?"

```text
L43 (`LIMITS.md`, dong L43) ghi nguyen van: "pruning action chet con la
limitation OPTIONAL, chua duoc dung de dien giai ket qua."

Neu khong chay:
  · `L43` treo vinh vien -- moi ket qua cua paper phai in kem cau tren
  · `W7` ("prior P1 manh + hanh dong chet") khong duoc dinh luong
  · MAT co hoi phat bieu mot cau MOI: quan he giua so hanh dong va
    ngan sach `alpha`, tuc gia cua viec giu mot hanh dong vo dung

=> Mat mot phat bieu cu the => DUOC PHEP chay.
   Ngan sach: 4 gate (`A071` R1). Khong mo them.
```

## 1. Anh xa ID

```text
Gate    : G23-297 .. G23-300           (4 gate, dung ngan sach)
Do      : M-233 .. M-235  +  NC-23.24-1
Doc     : docs/phase-23/52-action-pruning.md
Code    : cert/action_pruning.py
Test    : test/test_action_pruning.py
Artifact: results/PENDING/phase-23/action_pruning.json
```

`PHASE_23_v3.md` cap `G23-118..120` va doc `27-...`; ca hai da bi chiem.
Gate cuoi that la `G23-296`, doc cuoi la `51-close-23-23.md`.

## 2. Khoa dinh nghia bo dem "Lan bo qua"  (`L129`)

`A071` N3 dat nguong 3 nhung khong dinh nghia "bo qua". Hau qua do duoc:
cot **Lan bo qua** dung o `0` tren MOI dong suot Lesson 23.23, ke ca cac
dong da ton tai tu truoc. Mot bo dem khong bao gio tang la mot bo dem
khong ton tai -- cung hinh dang voi `L101`, `L119` va `A073` muc 2.

```text
DINH NGHIA DA KY:
  Bo dem tang +1 cho mot dong khi VA CHI KHI
    (i)   trang thai la HOAN
    (ii)  dong da co trong BACKLOG TRUOC khi lesson hien tai bat dau
    (iii) lesson hien tai khong nhan no lam noi dung
  Thoi diem tang: luc RA LAI bang, tuc dau lesson, TRUOC khi ky amendment.
  Dong sinh ra trong lesson N khong tang o dau N; tang lan dau o dau N+1.
```

Luot 23.23 duoc DEM BU. Ly do: `A071` da co hieu luc trong suot 23.23, nen
day la THI HANH mot luat da ton tai, khong phai AP HOI TO mot luat moi --
`A071` N1 khong ap dung. Cac dong co truoc 23.23 -> `2`; cac dong sinh
trong 23.23 (`L125`..`L128`) -> `1`.

Canh bao da biet truoc: voi nguong 3, cac dong o muc `2` se cham nguong o
dau Lesson 23.25. Do la y do cua luat.

## 3. Phan xu `L21` -- hai cach doc "hanh dong chet"

Repo dang mang HAI cach doc mau thuan (`conflict_note` trong
`results/SUPERSEDED/phase-23/lesson23_7_range_calibration.json`):

```text
Cach doc A (L21, "bang mat")   : chi P2 chet  -> K_eff = 3, m = 2
Cach doc B (M-D4, nguong 0.05) : P2 va P4 chet -> K_eff = 2, m = 1
```

So do duoc, tren TEST (xem muc 4 -- day chinh la loi phai sua):

```text
P(a* = P1) = 0.659724      P(a_twin = P1) = 0.619177
P(a* = P2) = 0.000014      P(a_twin = P2) = 0.000000   <- twin CHUA BAO GIO chon
P(a* = P3) = 0.333092      P(a_twin = P3) = 0.369222
P(a* = P4) = 0.007170      P(a_twin = P4) = 0.011601
```

### 3.1. Nguyen tac phan xu

Giua mot NGUONG KHOA TRUOC va mot phan doan BANG MAT, luon theo nguong
khoa truoc. Neu khong thi nguong do ton tai de lam gi. (Tien le:
`A066` muc 3, `A072` muc 2, `A073` muc 2.)

Nhung nguong `0.05` mot minh chi cho TAP UNG VIEN, khong cho QUYET DINH
CAT. Cat mot hanh dong la mot thay doi HANH VI, khong phai mot phep loc
thong ke.

### 3.2. TIEU CHI HAI TANG -- ky TRUOC, cham TREN CALIB

```text
TANG 1 -- ung vien:  P_calib(a* = a) < DEAD_ACTION_THRESHOLD = 0.05
                     (hang so da khoa tu Lesson 23.7, KHONG doi)

TANG 2 -- an toan:   mot ung vien chi duoc CAT khi thoa CA HAI
   (a) P_calib(a_twin = a) = 0
       -- twin CHUA BAO GIO de xuat no, nen bien m_hat cua no CHUA BAO GIO
          la bien chan. Cat no khong doi mot quyet dinh nao, chi doi
          ngan sach `alpha`. Day dung la dinh nghia "mien phi".
   (b) cat no lam `err|accept` tren CALIB xau di khong qua 0.005 tuyet doi
```

Ap vao so hien co (se do lai tren CALIB o `M-233`):

```text
P2 :  tang 1 dat (1.4e-5 < 0.05);  tang 2(a) dat (P(a_twin=P2) = 0)  -> CAT
P4 :  tang 1 dat (7.2e-3 < 0.05);  tang 2(a) HONG (P(a_twin=P4)=0.0116) -> GIU
```

=> **CAU HINH CHINH: `K = 3`** (cat P2), `alpha_each = alpha/2 = 0.05`
   `K = 4` la ABLATION voi nhan "gia cua viec giu mot hanh dong vo dung"
   `K = 2` la CANH TAY DO NHAY, in kem canh bao tang 2(a) khong dat

`PHASE_23_v3.md` viet "K=3 chinh (bo P4)". Do la mot doc nham: `P4` trong
`pruning_profitability.path` la hanh dong duoc dem THU CAT o bac S2 cua
thang, khong phai hanh dong chet. Hanh dong chet dau tien la `P2`.
Amendment nay KHONG thi hanh cau do.

## 4. Loi phai sua truoc moi thu khac -- winner's curse

Artifact 23.7 ghi nguyen van:

```json
"definition_uses": "P(a* = a) on test rows (M-D5)"
```

Con `PHASE_23_v3.md` muc [4] cua chinh Lesson 23.24 ghi:

> "Viec bo P4 phai duoc bien minh TREN CALIB, khong phai tren TEST.
>  Neu chon hanh dong chet dua tren test -> winner's curse."

Bang chung hien co VI PHAM dung quy tac ma ke hoach tu dat ra. Tap TEST
vua duoc dung de CHON cai can cat, vua duoc dung de DANH GIA loi ich cua
viec cat -- nen loi ich do bi thoi phong boi chinh hanh vi chon.

=> `M-233` do lai TOAN BO tren CALIB. Moi so cu chi duoc trich dan voi
   nhan `[TREN TEST -- winner's curse]`.

## 5. Bon phep do

### `G23-297` / `M-233` -- xac dinh hanh dong chet TREN CALIB

```text
Thu tuc : tinh `P_calib(a* = a)` va `P_calib(a_twin = a)` cho 4 duong,
          tren `is_calib` rows cua `split_by_block` (SEED_SPLIT khong doi).
          Ap tieu chi hai tang muc 3.2.
Dai     : tap CAT tren CALIB == {P2}
DIEU KIEN KHA THI (`A073` R5):
          co the fire theo ca hai chieu. `P_calib(a*=P2)` co the vuot 0.05
          neu split lech; `P_calib(a_twin=P4)` co the bang 0 neu P4 hiem
          trong nua calib. Ca hai deu la ket qua HOP LE va se doi ket luan.
Neu tap CAT != {P2} -> DUNG, khong dien giai lai, ghi ket qua that va
          chuyen cau hinh chinh theo dung tieu chi da ky.
```

### `G23-298` / `M-234` -- ti so `q_hat` va `Delta acceptance`

```text
Thu tuc : chay `score_procedure` (tai dung `cert/baselines_lit.py`) cho
          ba cau hinh S0 (K=4), S1 (K=3), S2 (K=2) tren CUNG split,
          CUNG `kappa = KAPPA_OP = 0.50`, CUNG 4 bin `z_bin`.

Dai (a) : `q_hat(K=3, alpha/2) / q_hat(K=4, alpha/3)`  thuoc [0.88, 0.94]
          trung binh tren 4 bin x 2 slot chung.

          Co so: Lesson 23.23 do `CV` trung binh 12 o = 0.756497, lech
          0.13% so voi hang so half-normal da khoa trong repo
          `K08_CV_MAX_FOLDED = 0.755511`. Duoi gia dinh
          `s ~ |N(0,sigma^2)|` ti so tinh duoc CHINH XAC:
              q/sigma  K=4: 2.128045   K=3: 1.959964   K=2: 1.644854
              ti so    K=3/K=4 = 0.921016   K=2/K=4 = 0.772941
          Du duoi do o 23.23 (+3.71/+4.62/+4.69/+7.55% theo bin, TANG theo
          do sau phan vi) lam TU SO bi thoi it hon MAU SO, nen ti so quan
          sat nen THAP hon 0.921016 mot chut. Dai [0.88, 0.94] dat lech tam
          theo huong do.

          `PHASE_23_v3.md` cap [0.90, 0.96] -- rong 6 diem quanh mot du
          doan tinh duoc toi 4 chu so. Amendment nay SIET lai. Ly do:
          `L119` -- mot dai khong the MISS la mot dai khong mang thong tin.

Dai (b) : `Delta acceptance(S1 vs S0)` thuoc [+0.01, +0.05]
          Co so: 23.7 do +0.034504 tren Mondrian 2 truc. Truc `m_hat` da
          bo (`CL-01`), nen phai do lai; dai giu quanh gia tri cu.

(c)     : `Delta acceptance(S2 vs S0)`  -- **[MO TA]**, KHONG cham HIT/MISS
          Ly do: 23.7 do +0.131683, ngoai moi dai hop ly cho mot bac
          "mien phi". S2 khong thoa tang 2(a) nen no khong phai cau hinh
          duoc de xuat; con so chi de tham chieu.

DIEU KIEN KHA THI: 4 bin x 500 block. `conformal_min_blocks` la 29 (K=4),
          19 (K=3), 9 (K=2) -- deu << 500, nen KHONG o nao tu choi o bat ky
          cau hinh nao. CAM ky bat ky dai dang "ton tai o tu choi" trong
          lesson nay. (`A073` R5; bai hoc `M-230`.)
```

### `G23-299` / `M-235` -- phan ra hai kenh

```text
Thu tuc : voi moi bac, tach `Delta acceptance` thanh ba phan bang thiet ke
          giai thua hai nhanh (tai dung so do cua 23.7):
            nhanh i   -- CHI bo rang buoc, giu `alpha_each` cua S0
            nhanh ii  -- CHI noi ngan sach, giu du 3 rang buoc
            nhanh iii -- ca hai
            tuong tac = iii - i - ii + 0

Dai     : `budget_share(S1) >= 0.90`
          Co so: 23.7 do 0.9930 tren Mondrian 2 truc.

Y nghia (PHAI in trong doc 52):
          Neu `budget_share` cao, thi cau "bo hanh dong chet thu ve X%
          acceptance" la mot cau GAY HIEU NHAM: X% do gan nhu toan bo den
          tu viec tu noi `alpha_each`, KHONG tu viec don khong gian hanh
          dong. Hai cau chuyen khoa hoc khac han nhau.
```

### `G23-300` / `NC-23.24-1` -- DOI CHUNG AM: cat mot hanh dong SONG

```text
Thu tuc : lam DUNG nhu S1 nhung cat `P3` (`P_calib(a*) ~ 0.333`) thay vi
          `P2`. Moi thu khac giu nguyen: cung split, cung kappa, cung bin,
          cung `alpha_each = 0.05`.

Dai     : PHAI ra dung HINH DANG nay --
            (i)  |Delta acceptance(cat P3) - Delta acceptance(cat P2)| <= 0.02
                 -> xac nhan acceptance tang la hieu ung NGAN SACH, khong
                    phai hieu ung "hanh dong chet"
            (ii) `Delta err|accept (cat P3)` >= +0.02
                 -> xac nhan tinh CHET moi la thu mua duoc su mien phi

Vi sao gate nay ton mot suat trong 4:
          Cau muon viet la "bo mot hanh dong khong bao gio toi uu thu ve
          X% acceptance ma khong mat bao dam nao". Reviewer se noi ngay:
          "bo BAT KY hanh dong nao cung thu ve X%, vi ban duoc noi
          `alpha_each`". Va ho DUNG -- 23.7 do `budget_share(S1) = 99.30%`.
          `G23-300` la cach duy nhat tra loi.

DIEU KIEN KHA THI: ca (i) va (ii) deu co the fail. (i) fail neu viec cat
          P3 lam mat mot rang buoc that su dang chan; (ii) fail neu he
          khong nhay voi viec mat mot hanh dong song.
```

## 6. Ba kich ban ket qua -- ket luan tuong ung, ky TRUOC

```text
K1  M-233 cho tap CAT = {P2};  M-234(a)(b) DAT;  M-235 DAT;  NC dung hinh dang
    -> Phat bieu duoc, o dang CHINH XAC:
       "Noi hieu chinh da so sanh thu ve +X% acceptance BAT KE cat hanh
        dong nao. Thu ma TINH CHET cua hanh dong mua duoc khong phai
        acceptance, ma la quyen noi do MA KHONG PHAI TRA bang `err|accept`."
    -> `L43` duoc dong. `K = 3` thanh cau hinh chinh.

K2  NC-23.24-1 ve (ii) KHONG dat -- cat P3 cung khong lam `err|accept` xau
    -> He KHONG nhay voi viec mat mot hanh dong song.
    -> KHONG duoc phat bieu cau K1. Thay bang mot HAN CHE:
       "khong gian hanh dong cua testbed THUA -- ba trong bon duong co the
        bo ma khong do duoc thiet hai. Moi ket luan ve pruning bi gioi han
        o testbed nay."
    -> `L43` KHONG dong duoc; ghi ly do.

K3  M-233 cho tap CAT != {P2}  (vd calib bat them P4, hoac khong bat P2)
    -> Cau hinh chinh doi THEO TIEU CHI DA KY o muc 3.2, khong theo mong
       muon. Ghi thang su chenh lech giua CALIB va TEST -- do CHINH LA
       do lon cua winner's curse va la mot ket qua dang bao cao rieng.
```

Ba kich ban deu cho mot doan viet duoc. Khong kich ban nao duoc dien giai
lai sau khi nhin so.

## 7. Mot quan sat MIEN PHI (khong ton gate) -- noi voi `L125`

`conformal_min_blocks(alpha_each)` la ham DONG cua `alpha_each`:

```text
K = 4   alpha_each = 0.033333   min blocks = 29
K = 3   alpha_each = 0.050000   min blocks = 19
K = 2   alpha_each = 0.100000   min blocks =  9
```

Cat hanh dong chet do do cung HA NGUONG TU CHOI cua conformal. Day la so
GIAI TICH (`ceil((n+1)(1-alpha_each)) <= n`), khong phai phep do, nen no
KHONG ton gate va KHONG duoc trich dan nhu mot phat hien thuc nghiem
(tien le `CL-10`, `CL-13`).

Y nghia thuc te: `L125` can mot cell co o duoi nguong tu choi. O `K = 3`
nguong la 19 thay vi 29, tuc `L125` de tim cell hon o cau hinh chinh moi.
Ghi vao doc 52; KHONG mo nhanh o day (`A071` R2).

## 8. Pham vi va gioi han cua chinh amendment nay

```text
N1  Moi so trich tu Lesson 23.7 trong amendment nay (0.034504, 0.131683,
    0.9930, 0.8496, P(a*), P(a_twin)) do tren MONDRIAN HAI TRUC va tren
    TEST rows. Chung dung de DAT DAI, KHONG phai du doan ket qua. Doc 52
    phai in nhan `[23.7 -- Mondrian 2 truc, TREN TEST]` canh moi so cu.

N2  Tieu chi tang 2(a) `P_calib(a_twin = a) = 0` la mot dang bang KHONG
    TUYET DOI tren mau huu han. No noi "chua bao gio quan sat duoc", khong
    noi "khong the xay ra". `M-233` PHAI ghi `n_calib` that su dung, va
    doc 52 PHAI in chan tren mot phia theo quy tac ba, `3 / n_calib`, canh
    MOI phat bieu ve tinh "mien phi" cua viec cat P2. Con so nay duoc TINH
    TU `n_calib` do duoc, khong duoc hard-code trong amendment.

N3  Ca lesson do tren MOT cell (`poisson@0.925`). Tap hanh dong chet co
    the KHAC o cell khac. Moi phat bieu gioi han o cell nay. Mo rong ra
    8 cell song la mot lesson khac -- KHONG mo o day (`A071` R2).

N4  Bonferroni duoc giu (`MULTIPLICITY = "bonferroni"`), khong doi sang
    Sidak. Doi se lam `alpha_each` roi tu 0.033333 sang 0.034511 va moi so
    cu het so sanh duoc. Sidak chi in nhu tham chieu giai tich trong doc 52:
      K=4: q/sigma = 2.114054   K=3: 1.948822   K=2: 1.644854

N5  `K = 2` KHONG duoc de xuat. No hong tang 2(a). Neu doc 52 in so cua
    K=2, phai in kem cau: "P(a_twin = P4) = 0.0116 tren TEST -- cat P4
    DOI quyet dinh, nen khong mien phi."

N6  SUA MOT SO TRONG BAN THAO amendment nay truoc khi ky: ban thao ghi gia
    tri half-normal la `0.755151` va do lech `0.18%`. Hang so da khoa
    trong repo la `K08_CV_MAX_FOLDED = 0.755510639762867`
    (`results/LIVE/phase-23/baselines_lit.json`, muc `constants`), va do
    lech that cua CV trung binh 12 o (0.7564965972137458) la `0.13%`. Muc
    5 dung con so DA SUA. Ket luan khong doi -- huong lech van la mot
    phia va dai [0.88, 0.94] khong phu thuoc con so nay.
```

## 9. Gate cau truc (khong do luong)

| Test | Noi dung |
|---|---|
| `test_dead_action_uses_calib_only` | quet AST: ham xac dinh hanh dong chet khong doc cot nao tu `test` frame |
| `test_dead_action_threshold_unchanged` | `DEAD_ACTION_THRESHOLD == 0.05`, khop `cell_matrices` |
| `test_two_tier_criterion_is_signed` | tieu chi hai tang trong code khop tung chu voi `A074` muc 3.2 |
| `test_alpha_each_ladder` | `alpha/3, alpha/2, alpha/1` cho `K = 4, 3, 2`; va `min_blocks` `29, 19, 9` |
| `test_nc_cuts_a_live_action` | `NC-23.24-1` cat duong co `P_calib(a*) > 0.05`, khong cat duong chet |
| `test_backlog_counter_definition_pinned` | dinh nghia bo dem o `A074` muc 2 khop dong quy tac trong `BACKLOG.md` |
