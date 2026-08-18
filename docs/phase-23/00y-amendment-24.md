# AMENDMENT 23-24 -- NT-v2-7, siet ket luan GO-1, va khoa thu tuc GO-2

Ngay: 2026-08-17
Commit: sau khi dong 23.5[B] (`949eabe`), TRUOC khi viet code Lesson 23.5[C].

---

## 1. NT-v2-7 -- toan ven tham chieu cua bang du doan

### 1.1. Su co lam lo ra van de

Dong thoi gian cua `A-5'`:

```text
Amendment 23-22  khoa A-5': "CI95_high lon nhat trong 3 cell thuoc [1.01, 1.06]"
                 Tai thoi diem do, luoi quyet dinh la PRIMARY.
                 => A-5' la mot du doan VE LUOI PRIMARY.

Amendment 23-23  khoa B-D13: "ket luan GO-1 dung KAPPA_REFINED"
                 => DOI TUONG cua A-5' vua bi thay doi.
                 Bang du doan KHONG duoc ra lai.

Do duoc:  primary  max CI95_high = 1.020352  thuoc [1.01, 1.06]   TRUNG
          refined  max CI95_high = 1.003173  ngoai [1.01, 1.06]   TRAT
```

`A-5'` trung tren doi tuong no duoc viet ra, va trat tren doi tuong no bi cham.

### 1.2. Nguyen tac moi

```text
NT-v2-7  MOI AMENDMENT THAY DOI DINH NGHIA, DOI TUONG, HOAC THU TUC DO CUA MOT
         DAI LUONG PHAI CHUA MOT MUC "RA SOAT DU DOAN": liet ke MOI dong du
         doan da khoa co nhac toi dai luong do, va voi moi dong ghi mot trong ba:

             GIU NGUYEN  -- doi tuong khong doi
             TAI BAN     -- doi tuong doi; dai moi + dai cu GIU CA HAI trong
                            bang, cham CA HAI
             RUT LAI     -- dai luong khong con duoc do; ghi ly do

         Amendment khong co muc nay thi khong duoc ky.
```

Ly do: pre-registration khong phai mot tai lieu, no la mot **co so du lieu co
rang buoc toan ven tham chieu**. Sua mot dinh nghia ma khong cap nhat moi ban
ghi tro toi no la lam hong khoa ngoai. Muc "ra soat du doan" chinh la
`ON UPDATE CASCADE`.

Neu `NT-v2-7` da ton tai, Amendment 23-23 buoc phai ghi *"A-5' -> TAI BAN"*, va
Lesson 23.5[B] se co HAI dong duoc cham (`A-5'-primary`, `A-5'-refined`) thay
vi mot dong bi cham sai doi tuong.

### 1.3. Xu ly hoi to cho A-5'

```text
KHONG duoc lam: "A-5' thuc ra PASS neu tinh tren luoi primary."
                Do la chon doi tuong sau khi thay ket qua -- p-hacking.

DA lam       : ghi MISS doi chieu dai da khoa (Lesson 23.5[B] muc 3.3).
BO SUNG      : ghi ro doi tuong da bi B-D13 doi, va con so tren luoi primary.
               Day la mot SU KIEN ve quy trinh, KHONG phai loi bien ho.
               Dong duoc cham la dong da khoa, va no MISS.
```

### 1.4. RA SOAT DU DOAN cua chinh Amendment nay (ap dung NT-v2-7 cho no)

Amendment nay doi thu tuc do cua GO-2 (C-D1, C-D2). Cac dong da khoa co nhac
toi dai luong GO-2:

| Dong da khoa | Nguon | Xu ly | Ly do |
|---|---|---|---|
| GO-2 "FWER ranking phu thuoc slot; khong neu thu tu toan phan" | `results/phase-23/go2_fwer_restatement.json` | **TAI BAN** thanh `C-5` | doi tuong doi tu 24 CI TUNG O sang dai DONG THOI |
| `n_contains_zero = 5/24` | artifact tren, `n_boot=200` | **RUT LAI** | khong on dinh o `B=200` (muc 4.2); thay bang `C-4` o `B=2000` |
| A-1'..A-4', A-7', A-8' | Amd 23-22/23 | GIU NGUYEN | `[MO TA]`, khong bi C-D nao dong toi |
| A-5' | Amd 23-22 | GIU NGUYEN (da cham MISS) | doi tuong da xu ly o muc 1.3 |
| A-6' | Amd 23-22 | **TAI BAN** thanh A-6'b | muc 3 doi cach phat bieu tu 95pct/cell sang co them can DONG THOI |

---

## 2. Ghi MISS -- tieu chi Monte Carlo sai khai niem

```text
Tieu chi ghi trong thiet ke 23.5[B]:
  "Sai so MC cua mot phan vi bootstrap ~ 1/sqrt(B). Chay B in {200,...,2000}:
   DO RONG CI phai co theo 1/sqrt(B)."

Cau dau DUNG. Cau sau SAI: no lan hai dai luong khac nhau.

  do rong CI     -> HOI TU VE MOT HANG SO khac 0, dinh boi n_block = 500.
                    B khong lam no nho di.
  sai so MC cua  -> CO VE 0 theo 1/sqrt(B). Day moi la thu B dieu khien.
  hai dau mut

Do duoc (poisson@0.925):
  do rong CI      B=200 -> 0.011544 ;  B=2000 -> 0.012006   (on dinh)
  sd(ci95_high)   B=200 -> 0.000690 ;  B=2000 -> 0.000137   (co 5.04x)
```

Ghi vao so MISS: `tieu chi MC 1/sqrt(B) tren DO RONG CI -- SAI, do nguoi huong
dan de xuat; sua thanh hai menh de tach roi tai Lesson 23.5[B]`.

Ghi chu ky thuat: `5.04x` so voi ly thuyet `sqrt(10) = 3.16x` khong bat thuong.
Sai so tuong doi cua mot uoc luong SD tu `n` seed la `~1/sqrt(2(n-1))`; ti so
hai SD gop lai `~33%` o `n=10`, `~19%` o `n=30`. Cong la MOT PHIA (`>= 1.8`) --
dung: co CHAM hon `1/sqrt(B)` moi dang ngo (goi y draw khong doc lap), co
NHANH hon chi la nhieu.

---

## 3. Siet ket luan GO-1 -- multiplicity tren 3 cell

### 3.1. Van de

```text
Cau da viet: "Chi phi duong bien duoi 0.32% o muc tin cay 95%."
0.32% = max CI95_high - 1 = 0.003173, lay tren CELL XAU NHAT trong ba cell,
moi cell mot CI 95% RIENG.

P(ca ba cung dung) KHONG phai 0.95. Duoi doc lap no la 0.95^3 = 0.857.
(Ba cell dung chung nguon du lieu nen khong doc lap that, nhung con so 0.857
la mot moc dung huong.)
```

Day dung la van de multiplicity ma ca Phase 22 noi ve, xuat hien lai o tang
meta -- y het `qhat` chung o tang slot.

### 3.2. Quyet dinh: dung CA ② VA ①

```text
GO1-M1  Abstract phat bieu TUNG CELL, khong phat bieu DONG THOI:
        "can tren 95% tren MOI che do danh gia duoc, cao nhat la 1.0032".
        Chinh xac, khong ton them tinh toan.

GO1-M2  Bao cao THEM can DONG THOI bang Bonferroni 3 cell (moi cell o muc
        1 - 0.05/3 = 98.33%), de nguoi doc muon phat bieu dong thoi thi co so.
```

Da tinh (thu tuc y het, chi doi muc phan vi):

```text
cell            per-cell 95pct           Bonferroni 98.33pct
poisson@0.925   [0.998950, 1.001992]     [0.998636, 1.002322]
poisson@0.850   [0.999067, 1.002946]     [0.998738, 1.003401]
h2@0.700        [0.995529, 1.003173]     [0.994641, 1.004125]

max per-cell 95pct       CI_high = 1.003173   GO-1 PASS
max Bonferroni 98.33pct  CI_high = 1.004125   GO-1 PASS (dong thoi >= 95pct)
du dia toi nguong 1.02 duoi Bonferroni: 4.8x
```

**GO-1 dat theo ca hai cach doc.** Ket luan cua Lesson 23.5[B] khong doi.

### 3.3. A-6'b -- tai ban theo NT-v2-7

```text
A-6'   (cu)  Dua "frontier invariance" vao abstract?  <=> A-5' < 1.02
             -> CO. Da cham, dat.
A-6'b  (moi) Ket luan co giu duoi can DONG THOI Bonferroni 3 cell khong?
             [CO CHE]  du doan: CO  -> do 1.004125 < 1.02, dat.
             Nhan: [MO TA], vi da tinh trong amendment nay.
```

---

## 4. Ba van de cua GO-2 -- da kiem chung tren code va du lieu that

### 4.1. Ghep cap VO o variant A -- bom no cham, da xac nhan

```python
base = _bootstrap_qvec_from_blocks(..., picks, baseline, alpha, variant, rng)
for p in procedures:
    q = _bootstrap_qvec_from_blocks(..., picks, p, alpha, variant, rng)
    #                                                              ^^^
    #                        CUNG rng, nhung DA BI TIEU THU boi loi goi truoc
```

`_reduce_block_arrays` KHONG dung `rng` o variant `B` (concatenate) va `C`
(max theo block). O variant `A` no goi `rng.integers` cho MOI pick.

Nang hon: `maxscore` goi `_reduce_block_arrays` MOT lan (`sim_blocks`), con
`bonferroni`/`sidak` goi BA lan (mot moi slot). Nen ke ca so luot rut `rng`
cung khac nhau giua baseline va procedure.

**Do duoc** -- nguyen mau `NC-C-1`, bootstrap `maxscore` vs CHINH no, cung draw
(neu ghep cap con nguyen thi `delta = 0` chinh xac, `CI width = 0`):

```text
variant   max|delta_mean|    max CI width    ket luan
B           0.000000e+00     0.000000e+00    PASS
C           0.000000e+00     0.000000e+00    PASS
A           7.992773e-02     4.235592e+00    FAIL -- ghep cap vo
```

Artifact hien tai dung `variant="B"` nen chua no. Nhung Phase 22 co chay
variant A/C lam `variant_controls`; neu `[C]` mo rong sang variant A, no no
IM LANG.

### 4.2. `B = 200` khong du -- da do bang chung truc tiep

Artifact hien co: `n_boot = 200`, `n_contains_zero = 5/24`.

Dai luong duoc doc la NHI PHAN ("CI co chua 0 khong"), nen mot dau mut nhay vi
nhieu MC la o do LAT. Chay lai `B=200` voi 10 seed:

```text
seed   7204 7221 7238 7255 7272 7289 7306 7323 7340 7357
n_zero    5    8    7    8    6    8    4    5    8    7

min=4  max=8  bien do=4  mean=6.6  sd=1.51      -> KHONG ON DINH
```

Con so `5/24` trong artifact da commit nam **duoi trung binh** (6.6) va bien do
dao dong toi **4/24 o**. Phat bieu GO-2 hien tai khong on dinh o `B=200`.

Dong so nay duoc dua vao `docs/phase-23/10-*` lam bang chung "truoc-sau".

### 4.3. Multiplicity BEN TRONG chinh phan tich multiplicity

```text
GO-2 phat bieu dua tren 24 khoang tin cay doc DONG THOI (4 bin x 2 proc x 3 slot).
24 khoang, moi khoang 95%. Duoi null toan cuc, ky vong so khoang loai tru 0
SAI la 24 x 0.05 = 1.2.
Artifact bao cao 19/24 loai tru 0 -> khoang 1.2 cai co the la gia.
```

Bai bao noi VE hieu chinh da so sanh, ma phan tich cua chinh no chua hieu chinh
da so sanh.

Van de thu hai chong len, cung ho voi `D2` cua `[A]`:

```python
for g, payload in by_bin.items():
    for _ in range(int(n_boot)):
        picks = rng.integers(0, n, size=n)   # draw RIENG cho moi bin
```

Da xac nhan o Lesson 23.5[A]: **moi block deu trai qua ca 4 bin**
(`blocks per z_bin = {0:1000, 1:1000, 2:1000, 3:1000}`). Bon bin dung CHUNG tap
block, tuong quan manh.

```text
Voi CI TUNG O    : draw rieng theo bin la HOP LE.
Voi phat bieu DONG THOI tren 24 o: SAI -- no coi bon bin doc lap trong khi
                                   chung chia se cung nguon ngau nhien.
```

### 4.4. Do thoi gian TRUOC khi toi uu -- ket luan: KHONG toi uu

```text
paired_bootstrap_deltas, B=200, poisson@0.925:  4.6 s
=> B=2000 khoang 46 s/cell.
```

Duoi nguong 30 phut/cell rat xa. **Khong viet duong nhanh (phan vi co trong
so).** Code nhanh ma sai dat hon code cham ma dung. Muc 5.2/5.3 cua thiet ke
(`weighted quantile`, `cua so quanh phan vi`) duoc GHI LAI lam ky thuat du
phong, khong trien khai o `[C]`.

Ghi chu ly thuyet van giu gia tri va phai vao doc:

```text
(n_rows, n_acc, n_wrong_acc) DU cho acceptance/err|accept vi ca hai la TI SO
CUA TONG -- phep toan la CONG, nen nen duoc.
KHONG DU cho qhat: phan vi khong phai ham cua tong, no phu thuoc TOAN BO phan
phoi. Hai block cung tong, cung so hang, phan bo khac nhau -> phan vi khac nhau.
Thong ke du cho mot phan vi duoi lay mau lai theo block la TOAN BO da tap gia
tri cua moi block.
```

---

## 5. Quyet dinh khoa C-D1 .. C-D6

```text
C-D1  Draw block TOAN CUC, MOT `picks` dung chung cho CA 4 bin trong moi draw.
      Ly do: moi block trai qua ca 4 bin; draw rieng theo bin coi chung doc lap
      trong khi chung khong. Cung nguyen tac D2 cua Lesson 23.5[A].

C-D2  Dai DONG THOI bang max-t la ket qua CHINH. Dai tung-o bao cao KEM,
      KHONG thay the.
        buoc 1  lay mau block mot lan, toan cuc
        buoc 2  moi draw b, tinh ca 24 delta  d_k^(b), k = 1..24
        buoc 3  sigma_k = SD bootstrap cua d_k
        buoc 4  T^(b) = max_k |d_k^(b) - dbar_k| / sigma_k
                c_maxt = phan vi_0.95(T)
        buoc 5  dai dong thoi:  dhat_k +/- c_maxt * sigma_k
                => P(ca 24 dai cung dung) >= 0.95

C-D3  B = 2000, seed khoa, kiem hoi tu MC bang tieu chi DA SUA (muc 2):
      width_stabilises + mc_error_shrinks. KHONG dung tieu chi cu.

C-D4  NC-C-1 chay cho CA BA variant A/B/C. Variant A PHAI DO (muc 4.1).
      Do la doi chung chung minh test co kha nang bat loi ghep cap.

C-D5  Bang chung bat on dinh o B=200 (10 seed, muc 4.2) dua vao doc.

C-D6  KHONG sua cert/conformal_simultaneous.py. Code moi o cert/go2_simultaneous.py.
      Ly do giong Amendment 23-22 muc 6: giu ham cu nguyen ven cho kiem tra tai
      lap Phase 22. Sua loi rng cua variant A trong FILE MOI, va ghi ro rang
      artifact Phase 22 dung variant B nen khong bi anh huong.
```

### 5.1. Vi sao max-t la lua chon dung, khong phai Bonferroni

```text
T = max_k |d_k - dbar_k| / sigma_k

Day CHINH XAC la cau truc  s_std = max_j s_j / sigma_j  cua Lesson 23.5[A],
chi khac tang: [A] ap len 3 rank slot, [C] ap len 24 dai luong suy luan.

Va no cho mot co hoi hiem: so TRUC TIEP c_maxt voi Bonferroni NGAY TRONG phan
tich cua minh. 24 dai luong tuong quan manh (chung block, chung slot), nen
max-t se cho hang so nho hon. Hieu so do DINH LUONG chinh xac luan diem cua
Phase 22 -- max-score hieu qua hon Bonferroni khi cac claim tuong quan --
nhung lan nay o tang meta, tren chinh bang ket qua cua minh.
```

---

## 6. Bang du doan cho Lesson 23.5[C]

| ID | Dai luong | Nhan | Dai khoa |
|---|---|---|---:|
| C-1 | `c_maxt` = phan vi 0.95 cua `T` | [CO CHE] | 2.2 - 2.7 |
| C-2 | `c_bonferroni` = `z_{1-0.05/48}` | [TAT DINH] | **3.078088** |
| C-3 | `c_maxt / c_bonferroni` | [CO CHE] | **0.71 - 0.88** |
| C-4 | `n_contains_zero` voi dai DONG THOI | [CO CHE] | `>= 5`, va `>=` gia tri cua dai tung-o |
| C-5 | Phat bieu "thu tu phu thuoc slot" con dung sau hieu chinh dong thoi? | [CO CHE] | CO |

### 6.1. Sua hai con so cua ban thiet ke goc

```text
Thiet ke goc ghi: C-2 = z_{1-0.05/48} = 2.82  -> SAI.
Tinh lai:         0.05/48 = 0.00104167
                  z_{1 - 0.00104167} = 3.078088
(2.82 gan voi z_{1-0.05/24} = 2.863, tuc quen chia doi cho hai phia.)

C-2 la HANG SO TAT DINH, khong phai du doan. Khoa gia tri 3.078088.

C-3 = C-1 / C-2, nen dai cua no LA HE QUA SO HOC, khong doc lap:
     [2.2, 2.7] / 3.078088 = [0.715, 0.877]  -> khoa [0.71, 0.88].
Ban goc ghi [0.78, 0.96] vi dung mau so sai 2.82.
```

### 6.2. Vai tro cua tung dong

```text
C-1  du doan THAT (chua do). Dong confirmatory chinh cua [C].
C-2  hang so, kiem tra so hoc.
C-3  he qua cua C-1 va C-2; khong cong them thong tin, giu de doc de.
C-4  dong AN TOAN: dai dong thoi RONG HON dai tung-o, nen so o chua 0 chi co
     the TANG. Neu no GIAM -> code sai. Bat duoc loi dao dau/nham sigma.
C-5  dong CO RUI RO THAT: neu sau hieu chinh ma slot 1 va slot 2 khong con tach
     duoc nhau, phat bieu GO-2 phai YEU DI. Day la loi du doan dang ky.
```

---

## 7. Pham vi duoc phep chay sau amendment nay

```text
* them cert/go2_simultaneous.py  (draw toan cuc + max-t + NC-C-1 ba variant)
* them test/test_phase23_go2.py
* sinh results/phase-23/go2_simultaneous_<cell>.json
* them docs/phase-23/10-go2-simultaneous.md
* cap nhat docs/phase-23/09-aurc-and-go1.md muc 4 voi can Bonferroni (GO1-M2)
* cap nhat bang chinh 00-preregistration.md: A-6'b, C-1..C-5, ghi chu A-5'

KHONG sua cert/conformal_simultaneous.py va cert/config_matrix.py.
```

## 8. Thu tu doc ket qua [C] -- bat buoc

```text
(1) NC-C-1 width = 0 o variant B va C, VA DO o variant A     <- cong
(2) tuong quan giua cac delta (ghep cap toan cuc hoat dong)  <- cong
(3) kiem hoi tu MC bang tieu chi da sua                      <- cong
(4) c_maxt vs c_bonferroni                                   <- C-1, C-2, C-3
(5) n_contains_zero: tung-o vs dong thoi                     <- C-4
(6) phat bieu GO-2 con dung khong                            <- C-5  KET LUAN

(1)-(3) la CONG. Fail bat ky muc nao thi (6) khong co nghia.
```
