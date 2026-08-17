# AMENDMENT 23-22 -- Khoa thu tuc AURC cho GO-1 (Lesson 23.5[B])

Ngay: 2026-08-17
Commit: sau khi dong 23.5[A] (`phase-23-lesson-5a-complete` -> 97d4522),
TRUOC khi viet bat ky code nao cua Lesson 23.5[B].

Ly do: kiem toan `cert/baselines.py` va `cert/config_matrix.py` truoc khi chay
[B] tim ra **bay bay loi** trong duong ong AURC hien co. Mot trong so do lam
**doi dau ti so** tren cell chinh chi vi cach roi rac hoa. Neu chay [B] ma
khong khoa cac quyet dinh duoi day thi ket luan GO-1 khong xac dinh.

Toan bo so trong amendment nay do duoc tu artifact Phase 22 da commit
(`results/phase-22/config_matrix_*.json`). Khong co du lieu moi nao duoc sinh.

---

## 1. Bay da xac nhan (do lai, khong phai nho lai)

### 1.1. Bay 1 -- trong repo co HAI ham AURC, tinh hai thu khac nhau

```text
cert/config_matrix.py :: aurc(rows)
    x = acceptance (12 diem tu quet kappa)
    y = err_given_accept          <- rui ro TREN HANG DUOC CHAP NHAN
    dai = [x.min, x.max] quan sat duoc, chuan hoa / (x.max - x.min)
    co C0/C1/C2/C3

cert/baselines.py :: beneficial_band(...)["partial_aurc_060_100"]
    x = coverage (luoi 20001 diem)
    y = err_system                <- rui ro CA HE, DA gom fallback
    dai = [0.60, 1.00] co dinh, chuan hoa / 0.4
    KHONG co C0 -- nhan la B1..B6 va C3_conformal
```

`GO-1` phat bieu `AURC(C3)/AURC(C0) < 1.02`; PLAN cua 23.5[B] phat bieu "AURC
RIENG PHAN [0.6, 1.0]". **Hai cau tro vao hai ham khac nhau**: `C0` chi ton tai
o ham thu nhat, cua so `[0.6, 1.0]` chi ton tai o ham thu hai.

Ly do khai niem khien `err_system` khong dung duoc:

```text
err_given_accept = rui ro tren tap ACCEPT.  DON DIEU TANG theo acceptance.
                   Do la truc y cua AURC trong Chow / El-Yaniv / Geifman.
err_system       = coverage*err|accept + (1-coverage)*err|reject(fallback).
                   HINH CHU U -- chinh Amendment 23-12 da dat ten.
```

Tich phan mot duong chu U roi goi la "area under the RISK-COVERAGE curve" la
loi pham tru: dinh nghia AURC doi don dieu de "dien tich nho hon = bo chon tot
hon" co nghia. Them nua `err_system` phu thuoc lua chon fallback, ma 23.6 sap
tuyen bo fallback la tham so NGOAI SINH -- dua no vao gate GO-1 vi pham
`NT-v2-1`.

Da kiem chung tinh don dieu tren du lieu that (`err_given_accept` theo
acceptance):

```text
cell            config  n   dup  don dieu tang  vi pham
h2@0.700        C0     11    0      True          0
h2@0.700        C3     10    0      True          0
poisson@0.850   C0     11    0      True          0
poisson@0.850   C3     10    0      True          0
poisson@0.925   C0     11    0      True          0
poisson@0.925   C3     10    0      True          0
```

### 1.2. Bay 2 -- `return` som lam bien mat khoa

```python
if not beneficial.any():
    return {"beneficial": False, "improvement_area": 0.0}
    #      KHONG co khoa "partial_aurc_060_100"
```

Neu mot duong khong bao gio thang anchor, dict tra ve THIEU khoa. Mot script
viet `band.get("partial_aurc_060_100", 0.0)` se bien "khong tinh duoc" thanh
`0.0`, tuc **gia tri TOT NHAT co the**, tuc `ratio -> 0 < 1.02 -> PASS`.
Duong te nhat thanh duong tot nhat, im lang.

Trang thai hien tai: caller duy nhat, `cert/phase23_cross_cell.py::_band_payload`,
**da xu ly dung** -- no tra `None` chu khong phai `0.0`. Bay nay la bay DU
PHONG cho code [B] sap viet, khong phai loi dang song.

### 1.3. Bay 3 -- C0 va C3 duoc lay mau o nhung diem acceptance KHAC NHAU

Cung mot `kappa` cho acceptance khac nhau vi `qhat` khac nhau. Luoi that,
`poisson@0.925`:

```text
C0 n=11  0.000 0.001 0.007 0.048 0.121 0.187 0.284 0.413 0.586 0.788 1.000
   gaps:       0.001 0.006 0.041 0.073 0.066 0.096 0.129 0.173 0.202 0.212
C3 n=10  0.000 0.001 0.009 0.035 0.072 0.144 0.273 0.491 0.738 1.000
   gaps:       0.001 0.009 0.025 0.037 0.072 0.130 0.218 0.247 0.262
                                                              ^^^^^ rong hon 24%
```

`aurc()` chay `np.trapezoid` tren diem THO. Duong loi o doan cuoi nen hinh
thang uoc luong THUA, va C3 co khoang cuoi rong hon nen uoc luong thua NHIEU
HON. Mot phan chenh lech AURC la sai so roi rac hoa, khong phai khac biet
duong bien.

**Do muc do -- ti so DOI DAU tren cell chinh:**

```text
cell            RAW (luoi rieng)                COMMON grid [0.6,1.0] n=4001
                C0        C3        ratio       C0        C3        ratio
h2@0.700        0.033236  0.033522  1.008595    0.070238  0.071105  1.012345
poisson@0.850   0.090569  0.091342  1.008532    0.162170  0.163184  1.006249
poisson@0.925   0.091335  0.091085  0.997272    0.164133  0.164542  1.002492
                                    ^^^^^^^^                        ^^^^^^^^
                                    C3 TOT HON                      C3 TE HON
```

Ca hai deu `< 1.02` nen GO-1 PASS theo ca hai cach. Nhung cau viet vao abstract
thi khac nhau:

```text
luoi tho   : "C3 khop hoac nhinh hon C0"     <- ARTIFACT cua roi rac hoa
luoi chung : "C3 nam trong 0.25% cua C0"     <- DUNG
```

Day dung la canh bao cua Amendment 23-11 (grid-density confound), nhung
23-11 chi ap cho ho nguong; `config_matrix` chua ai kiem.

### 1.4. Bay 4 -- chuan hoa theo dai rieng, va roi diem khong deu

```python
return float(np.trapezoid(y, x) / (x.max() - x.min()))
```

(a) Chia cho dai cua CHINH NO -> dai luong la "rui ro trung binh tren mien
quan sat duoc cua rieng cau hinh do", khong phai dien tich. Ti so cua hai dai
luong nhu vay khong phai so sanh duong bien.

(b) `aurc()` loai hang co `err_given_accept` khong huu han. Dem that:
**C0 giu 11/12 diem, C3 giu 10/12 diem** o CA BA cell. Hai duong duoc tich
phan tren hai tap diem khac nhau roi moi ben chuan hoa theo dai rieng.

### 1.5. Bay 5 -- khong co CI, ma bien do toi nguong chi ~1%

```text
nguong GO-1        : 1.02
do duoc (luoi chung): 1.012345 / 1.006249 / 1.002492
bien do toi nguong : 0.008 - 0.018
so diem de tinh    : 10-11
```

Mot uoc luong diem cach nguong 0.8% dung tren 10 diem **khong phai mot quyet
dinh**. Resample diem tren duong cong la SAI: cac diem khong doc lap, chung la
cung mot tap hang o cac `kappa` khac nhau.

### 1.6. Bay 6 -- suy bien: `aurc()` khong biet `DEGENERATE_ERR`

`cert/config_matrix.py:49` da co `DEGENERATE_ERR = 0.02`, dung o `evaluate_H7`
(dong 339). `aurc()` KHONG dung no. Do duoc:

```text
cell            err_neo   suy bien?   aurc(C0)   aurc(C3)   nguy hiem?
cbr@0.700       0.0000    CO          nan        nan        khong (nan lan truyen)
poisson@0.700   0.0000    CO          0.000000   0.000000   CO -> ratio = 0/0
h2@0.700        0.1265    khong       0.033236   0.033522   -
poisson@0.850   0.2207    khong       0.090569   0.091342   -
poisson@0.925   0.2224    khong       0.091335   0.091085   -
```

`0.0` la **mot con so trong hop le**. Script chi loc `nan` se de
`poisson@0.700` lot qua va cho `0/0`.

Phan hoach `err_neo < DEGENERATE_ERR` cho dung 2 cell suy bien, khop chinh xac
`"3/3 cell danh gia duoc PASS, 2 cell suy bien"` o
`docs/phase-22/99-gate-decision.md` muc 7. **Mot tieu chi la du**; khong them
tieu chi "qhat cham san do luong" vi no cho cung phan hoach va chi tao kha nang
bat dong.

### 1.7. Bay 7 -- MOI: `err_given_accept = None` sau khi qua JSON

Bay nay khong co trong danh sach sau; tim ra khi chay doi chieu.

```text
`_json_clean` map float khong huu han -> JSON null.
`aurc()` goi float(r["err_given_accept"]) -> TypeError tren None.

=> aurc() CHAY DUOC tren dict trong bo nho (nan la float)
   va SUP DO tren chinh artifact no vua ghi ra.

Dem hang None trong artifact:
  h2@0.700       C0 1/12 (kappa 8.0)   C3 2/12 (kappa 6.0, 8.0)
  poisson@0.850  C0 1/12 (kappa 8.0)   C3 2/12 (kappa 6.0, 8.0)
  poisson@0.925  C0 1/12 (kappa 8.0)   C3 2/12 (kappa 6.0, 8.0)
```

Day cung la CO CHE cua bay 4(b): chenh lech 11 vs 10 diem den tu day. Bat ky
code [B] nao doc artifact deu phai un-map `None -> nan` TRUOC khi goi `aurc()`.

---

## 2. Quyet dinh khoa B-D1 .. B-D10

```text
B-D1  GO-1 chay tren cert/config_matrix.py, truc y = err_given_accept.
      partial_aurc_060_100 trong baselines.py KHONG dung cho GO-1 (truc y sai:
      err_system chu U, phu thuoc fallback -> vi pham NT-v2-1). No van duoc BAO
      CAO nhu diagnostic rieng, DOI TEN thanh
      partial_mean_system_risk_060_100 de khong ai doc nham la AURC.

B-D2  LUOI CHUNG bat buoc. Noi suy ca C0 va C3 len cung luoi acceptance truoc
      khi tich phan. Luoi: np.linspace(0.60, 1.00, 4001).
      Ly do: ti so DOI DAU tren poisson@0.925 khi doi cach roi rac hoa
      (0.997272 luoi tho -> 1.002492 luoi chung). Khong khoa thi ket luan
      khong xac dinh.

B-D3  Cua so [0.60, 1.00], KHONG toan dai (Amendment 23-11).
      Chuan hoa / 0.40 -- HANG SO, giong nhau moi cau hinh.
      KHONG chia cho dai rieng cua tung cau hinh.

B-D4  Ngoai suy bi CAM. Neu min(acceptance quan sat duoc) > 0.60 hoac
      max(...) < 1.00 o bat ky cau hinh nao, np.interp se pad phang bang
      y[0]/y[-1] -- so bia. -> RAISE, khong im lang pad.
      Trang thai hien tai: ca 3 cell khong suy bien deu phu [0.000, 1.000],
      nen dieu kien THOA; van phai chan bang code cho 23.11.

B-D5  Suy bien <=> err_neo < DEGENERATE_ERR = 0.02 (hang so DA khoa Phase 22).
      Cell suy bien: KHONG tinh ratio; ghi trang thai "DEGENERATE" kem err_neo.
      Mot tieu chi duy nhat.

B-D6  aurc() tra nan cho cell suy bien thay vi 0.0. Test chan.

B-D7  CI: paired block bootstrap tren tap TEST, qhat CO DINH, B = 2000.
      cho b = 1..B:
        1. resample NGUYEN BLOCK cua tap TEST (co hoan lai)
        2. voi qhat DA CO DINH (hieu chuan KHONG resample -- no la dieu kien),
           tinh lai acceptance va err|accept o moi kappa cho CA C0 va C3
        3. noi suy ca hai len LUOI CHUNG (B-D2), tinh AURC, lay TI SO
      -> phan phoi B ti so -> CI95 percentile.
      Buoc 2 PHAI dung CUNG draw cho C0 va C3 (paired); khong thi CI phong.

B-D8  Ket luan GO-1 NHI PHAN va dua tren CAN TREN CI95, khong phai diem:
      duoc dua "frontier invariance" vao abstract
        <=> CI95_high(ratio) < 1.02 tren MOI cell khong suy bien.

B-D9  Quy tac trung acceptance: neu hai hang cung acceptance, giu err|accept
      NHO NHAT (giong risk_at_acceptance da co). Do duoc hien tai: dup = 0 o
      6/6 duong, nen quy tac chua kich hoat -- khoa truoc cho 23.11.

B-D10 Doc artifact: un-map None -> nan TRUOC khi goi aurc() (bay 7).
      KHONG duoc dung .get(key, <so>) cho bat ky so lieu nao. Dung d[key] va
      de no no. Default so hoc tren du lieu thieu bien mot loi on ao thanh
      mot ket luan sai lang le.
```

### 2.1. Khong monotonisation

Van de bo sung: literature AURC doi khi ap bao loi duoi (lower convex envelope).
Do duoc: ca 6 duong DA don dieu tang, 0 vi pham (muc 1.1). Vi vay:

```text
B-D11 KHONG monotonise. Duong da don dieu tren du lieu that; them mot buoc
      bien doi ma khong can la them mot bac tu do khong bi rang buoc.
      Neu 23.11 sinh duong khong don dieu -> phai them amendment, khong duoc
      im lang bat monotonisation len.
```

### 2.2. Ghi chu cau truc: hai duong gap nhau o acceptance = 1.0

```text
Tai acceptance = 1.0, moi cau hinh chap nhan moi hang, nen
err|accept = err_neo voi CA C0 va C3. Do duoc: yN = 0.22240 = err_neo cua
poisson@0.925 (khop den 5 chu so o ca 3 cell).

He qua: ti so AURC hoan toan do phan TRONG cua cua so quyet dinh; hai dau mut
khong dong gop chenh lech nao. Doc dieu nay khi dien giai do lon ~1%.
```

---

## 3. Bang du doan khoa truoc cho Lesson 23.5[B]

| ID | Dai luong | Nguon | Dai khoa | Do duoc | KQ |
|---|---|---|---:|---:|---|
| A-1' | ratio AURC[0.6,1] C3/C0, poisson@0.925 | [MO TA] | 1.000 - 1.006 | ___ | ___ |
| A-2' | ratio AURC[0.6,1] C3/C0, poisson@0.850 | [MO TA] | 1.002 - 1.011 | ___ | ___ |
| A-3' | ratio AURC[0.6,1] C3/C0, h2@0.700 | [MO TA] | 1.007 - 1.018 | ___ | ___ |
| A-4' | So cell suy bien trong 5 | [CO CHE] | dung 2 | ___ | ___ |
| A-5' | **CI95_high lon nhat trong 3 cell** | [NGOAI SUY] | 1.01 - 1.06 | ___ | ___ |
| A-6' | Duoc dua "frontier invariance" vao abstract? | [CO CHE] | xem A-5' | ___ | ___ |

### 3.1. A-1'..A-4' KHONG con gia tri confirmatory -- ghi ro

```text
Bon dong A-1'..A-4' da duoc TINH trong qua trinh kiem toan bay (muc 1.3, 1.6),
bang DUNG thu tuc khoa o B-D2/B-D3. Uoc luong diem da biet:
    A-1'  1.002492      A-2'  1.006249      A-3'  1.012345      A-4'  2
Nhan [MO TA] la bat buoc. Chung duoc giu trong bang de lam kiem tra tai lap
(chay lai phai ra dung so nay), KHONG phai lam prediction-hit.

Xu ly giong het cach S-5 da duoc xu ly o Amendment 23-21: da nhin so thi khong
duoc tinh diem.
```

### 3.2. He qua thiet ke: noi dung confirmatory DUY NHAT cua [B] la CI

Vi A-1'..A-4' da biet, dai luong that su chua biet chi con `A-5'` (va `A-6'`
suy tu no). Dieu do lam thay doi trong tam cua lesson:

```text
[B] KHONG phai mot lesson do AURC. AURC da do xong.
[B] la mot lesson do DO BAT DINH cua AURC, va bien do bat dinh do quyet dinh
    mot cau trong abstract.
Ngan sach cong suc phai doi theo: gan het cong suc vao B-D7 (bootstrap paired,
B=2000) chu khong vao viec tinh lai duong cong.
```

### 3.3. Canh bao ve A-5'

Voi 10-11 diem `kappa` va bien do toi nguong 0.8-1.8%, `CI95_high` co xac suat
thuc su vuot `1.02`. Neu vay, ket luan GO-1 duoc viet san:

```text
"Khong dua duoc 'frontier invariance' vao abstract duoi dang khang dinh.
 Du lieu nhat quan voi bat bien (uoc luong diem 1.0025 - 1.0123) nhung khong
 loai tru duoc suy giam toi CI95_high. Phat bieu dung la:
   KHONG CO BANG CHUNG VE SUY GIAM DUONG BIEN,
 khong phai
   CO BANG CHUNG VE BAT BIEN."
```

Hai menh de do khac nhau va rat nhieu paper gop lam mot. Chuan bi truoc tinh
than cho no thay vi xoay xo sau khi do.

---

## 4. Nhanh FAIL viet truoc

```text
Neu CI95_high > 1.02 o >= 1 cell khong suy bien:
   -> KHONG viet "frontier invariance" vao abstract
   -> viet: "certification cho mot bao dam hinh thuc ma chung toi khong do duoc
             chi phi duong bien nao; can tren cua suy giam la X% o muc tin cay
             95%"
   -> con so X% DI VAO ABSTRACT. Mot can tren co so manh hon mot khang dinh
      khong CI.

Neu ratio > 1.02 o DIEM uoc luong:
   -> do la ket qua that, bao cao, va dieu tra bang matched_risk_ratio_vs_C0
      (da co san o acceptance 0.70 / 0.50 / 0.30 / 0.15) xem suy giam tap trung
      o dau.
```

---

## 5. Nguyen tac moi -- NT-v2-6

Bay tren bay bay (1, 3, 4, 6, 7) thuoc CUNG MOT HO: so sanh hai dai luong duoc
tinh tren hai mien / luoi / tap diem khac nhau roi doc ti so nhu the chung cung
thang. Cung ho voi `S-5` (pooled vs per_bin) va `p` (per_bin vs total) o
Lesson 23.5[A]. **Ba lan lien tiep.**

```text
NT-v2-6  MOI TI SO PHAI CO TU SO VA MAU SO TREN CUNG MIEN, CUNG LUOI,
         CUNG TAP DIEM. Neu hai ve duoc tinh tu hai lan chay khac nhau, phai
         noi suy len mot truc chung TRUOC khi chia, va truc chung do phai duoc
         khoa BANG SO trong pre-registration.
```

Ghi chu: repo hien khong co file `MASTER_PLAN.md`; danh sach `NT-v2-*` nam
ngoai repo. `NT-v2-6` duoc phat bieu o day de no co mot ban tracked, va phai
duoc chep sang MASTER_PLAN khi file do vao repo.

---

## 6. Pham vi duoc phep chay sau amendment nay

```text
* them cert/aurc_go1.py (AURC luoi chung + paired block bootstrap)
* them test/test_phase23_aurc_go1.py
* doi ten khoa partial_aurc_060_100 -> partial_mean_system_risk_060_100
  trong cert/baselines.py va cert/phase23_cross_cell.py, GIU khoa cu nhu alias
  doc-duoc de khong pha artifact da commit
* sinh results/phase-23/aurc_go1_<cell>.json cho 5 cell
* cap nhat docs/phase-23/09-aurc-and-go1.md
```

Khong duoc sua `cert/config_matrix.py::aurc()` de doi ket qua Phase 22 da
commit. Neu can hanh vi moi thi viet ham moi trong `cert/aurc_go1.py` va de
`aurc()` nguyen ven cho kiem tra tai lap.
