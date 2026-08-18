# Lesson 23.5[B] -- AURC rieng phan [0.6, 1.0] va dong no GO-1

Ngay chay: 2026-08-17
Thu tuc khoa tai: `docs/phase-23/00w-amendment-22.md` (B-D1..B-D11),
`docs/phase-23/00x-amendment-23.md` (B-D12..B-D14).

Input: `results/phase-22/calib_set_v3_{poisson_0.925,poisson_0.850,h2_0.700,
poisson_0.700,cbr_0.700}.parquet`

Output: `results/phase-23/aurc_go1_<cell>.json` (ca 5 cell, ke ca 2 cell suy bien)

Code: `cert/aurc_go1.py` -- KHONG sua `cert/config_matrix.py::aurc()`, de ham cu
nguyen ven cho kiem tra tai lap Phase 22.

---

## 0. Ket qua quan trong nhat: Phat hien 8 DA LAT KET LUAN GO-1

```text
                     LUOI PRIMARY (12 kappa)          LUOI REFINED (21 kappa)
cell            ratio     CI95_high   GO-1        ratio     CI95_high   GO-1
poisson@0.925  1.002492   1.008745    PASS       1.000480   1.001992    PASS
poisson@0.850  1.006249   1.014382    PASS       1.000968   1.002946    PASS
h2@0.700       1.012345   1.020352    FAIL       0.999363   1.003173    PASS
                          ^^^^^^^^    ^^^^
                          > 1.02, GO-1 TRUOT trong gang tac
```

Neu chay `[B]` voi luoi `kappa` goc, `h2@0.700` cho `CI95_high = 1.020352` va
GO-1 **TRUOT** o nguong `1.02` -- truot vi `0.0004`. Sau khi lam min luoi
trong cua so, con so la `1.003173` va GO-1 dat.

Chenh lech do KHONG phai nhieu lay mau. No la **sai so roi rac hoa**: cua so
`[0.6, 1.0]` tren luoi goc chi tua tren ba nut, va C3 co doan cuoi rong hon C0
nen chiu sai so hinh thang lon hon (Amendment 23-23 muc 1).

**Tinh hop le cua viec dung luoi refined lam quyet dinh:** `B-D13` duoc khoa o
commit `61e360d` luc `15:13:30 +07:00`; artifact mang `git_hash = 61e360d` va
`timestamp_utc = 08:35Z = 15:35 +07:00`. Luoi quyet dinh duoc chon TRUOC khi
bootstrap chay lan dau. Neu chon sau khi thay primary truot va refined dat thi
day la p-hacking; provenance chung minh khong phai.

---

## 1. Cong: bon doi chung phai dat truoc khi doc CI

```text
cell            NC-A-1 width   corr(num,den)   PC-A-1   MC shrink   TAT CA
poisson@0.925      0.0e+00       0.999689       PASS      3.06x      PASS
poisson@0.850      0.0e+00       0.999532       PASS      2.33x      PASS
h2@0.700           0.0e+00       0.999452       PASS      2.65x      PASS
```

`NC-A-1` cho do rong CI **chinh xac bang 0** o ca ba cell: bootstrap C0 vs
chinh C0 tren cung `picks` cho `ratio = 1.0` o moi draw. Ghep cap hoat dong.

`corr(num, den) = 0.9995` xac nhan lai dieu do tu mot huong khac: hai AURC
di cung nhau gan nhu hoan toan qua cac draw, nen phan nhieu chung bi triet
tieu trong ti so.

`PC-A-1` (nhan `err|accept` cua C3 len 1.10) cho CI quanh `[1.095, 1.104]`,
loai tru `1.02` o ca ba cell. Phep do CO kha nang phat hien mot suy giam 10%.

### 1.1. Mot tieu chi MC sai da bi phat hien va sua

Thiet ke ban dau ghi: *"do rong CI phai co theo 1/sqrt(B)"*. **Sai.** Do duoc:

```text
B      ci95_width   ky vong 1/sqrt(B)   obs/exp
200     0.011544        0.011544         1.000
500     0.011583        0.007301         1.586
1000    0.011980        0.005163         2.320
2000    0.012006        0.003651         3.289
```

Do rong CI **hoi tu ve mot hang so**, dinh boi so BLOCK (500), khong phai boi
`B`. Khi `B -> vo cung`, CI hoi tu ve phan vi 2.5-97.5 cua phan phoi bootstrap
THAT. Thu co theo `1/sqrt(B)` la **sai so Monte Carlo cua hai dau mut**:

```text
B      sd(ci95_high) qua cac seed    ky vong 1/sqrt(B)
200          0.000690                    0.000690
2000         0.000137                    0.000218
                     -> co 5.0x, ly thuyet du bao 3.16x
```

Mot bootstrap DUNG se FAIL tieu chi cu, va "sua" code cho qua nghia la lam
hong bootstrap. `mc_convergence()` doi thanh hai kiem tra tach bach:

```text
pass_width_stabilises  |w(2000) - w(1000)| / w(2000) <= 0.10
pass_mc_error_shrinks  sd(ci95_high) o B=200 / o B=2000 >= 1.8
```

### 1.2. Gate MC tung TRUOT vi phep do cua chinh no qua nhieu

Lan chay dau, `poisson@0.850` cho `shrink = 1.798` voi `MC_N_SEEDS = 10` --
truot nguong `1.8` o chu so thu ba.

```text
n_seeds=10   shrink = 1.798   FAIL
n_seeds=30   shrink = 2.333   PASS
(width_relative_change = 0.0024 / 0.0036 -- on dinh o ca hai)
```

Do lech chuan cua mot uoc luong do lech chuan co sai so tuong doi
`~1/sqrt(2(n-1))`: `n=10 -> 23.6%`, `n=30 -> 13.1%`. Ti so cua HAI do lech
chuan vi vay co sai so `~33%` o `n=10` -- khong du de phan biet `1.8` voi
`3.16`, tuc chinh nguong cua gate.

`MC_N_SEEDS` nang tu 10 len 30. **NGUONG `1.8` KHONG DOI.** Cai duoc sua la do
chinh xac cua PHEP DO, khong phai vi tri cua vach. Day la cung mot loai loi
voi tran chan cua PC-S-1 o Lesson 23.5[A]: mot gate ma phep do cua no khong du
phan giai de cham vach thi khong phai gate.

---

## 2. Phat hien 8 da duoc xu ly

```text
                primary                     refined
cell         knots C3,C0 / widest      knots C3,C0 / widest
poisson@0.925    2, 2 / 0.2620            8,10 / 0.0555
poisson@0.850    2, 2 / 0.3182            7, 9 / 0.0653
h2@0.700         3, 4 / 0.1789           12,13 / 0.1488
```

`B-D14` (>= 6 nut, doan rong nhat < 0.15) dat o ca ba cell tren luoi refined,
va **truot o ca ba tren luoi primary**. Luoi mit khong phai trang tri.

---

## 3. Ket qua so

### 3.1. Kiem tra tai lap

Luoi `primary` cho lai **dung** ba con so ghi trong Amendment 23-22 muc 1.3:

```text
poisson@0.925  1.002492      poisson@0.850  1.006249      h2@0.700  1.012345
```

Duong ong moi (`cert/aurc_go1.py`) va duong ong kiem toan doc lap cho ket qua
trung khop den 6 chu so. Chot bang `test_A11`.

### 3.2. Sai so roi rac hoa

```text
cell            ratio primary   ratio refined   discretisation_bias
poisson@0.925      1.002492        1.000480         -0.002012
poisson@0.850      1.006249        1.000968         -0.005281
h2@0.700           1.012345        0.999363         -0.012982
```

Dau AM o ca ba cell, dung nhu co che du bao: duong LOI + doan cuoi cua C3 rong
hon C0 => hinh thang thoi phong AURC(C3) nhieu hon AURC(C0) => lam min HA ti so.

### 3.3. Bang du doan -- hai MISS

| ID | Nhan | Dai khoa | Do duoc | KQ |
|---|---|---:|---:|---|
| A-1' | [MO TA] | 1.000-1.006 | 1.002492 | trong dai (tai lap) |
| A-2' | [MO TA] | 1.002-1.011 | 1.006249 | trong dai (tai lap) |
| A-3' | [MO TA] | 1.007-1.018 | 1.012345 | trong dai (tai lap) |
| A-4' | [MO TA] | dung 2 | 2 (`poisson@0.700`, `cbr@0.700`) | trong dai |
| A-5' | **[NGOAI SUY]** | **1.01-1.06** | **1.003173** | **MISS (thap hon dai)** |
| A-6' | [CO CHE] | `A-5' < 1.02` | TRUE, ca 3 cell | dat |
| A-7' | [MO TA] | 0.001-0.010 | 0.012982 (`h2@0.700`) | **MISS (cao hon dai)** |
| A-8' | [MO TA] | AM | AM ca 3 cell | trong dai |

**A-5' MISS, va day la dong confirmatory DUY NHAT cua lesson nay.**
Du doan `CI95_high in [1.01, 1.06]` dat tren gia dinh "10-11 diem, bien do
0.8%, CI se rong". Do duoc `1.003173` -- **hep hon nhieu**. Hai ly do:

```text
(a) luoi refined loai bo phan lon sai so roi rac hoa (muc 3.2)
(b) ghep cap hieu qua den muc corr = 0.9995, triet tieu gan het nhieu chung
```

Dang chu y: tren luoi `primary`, `max CI95_high = 1.020352` -- **nam trong dai
1.01-1.06**. Du doan A-5' duoc hieu chinh cho the gioi luoi tho; chinh viec lam
min luoi da lam no truot. Ghi MISS, khong sua dai.

**A-7' MISS.** Dai `0.001-0.010` truot vi `h2@0.700` cho `0.012982`. Ghi chu ve
liem chinh: trong buoc kiem tra thiet ke o Amendment 23-23 toi CHI nhin
`poisson@0.925` (`-0.002012`, trong dai). Cell lam truot la cell toi CHUA nhin.
A-7' da bi ha xuong `[MO TA]` truoc do va khong tinh diem -- viec ha nhan la
dung thu tuc, va dai van truot.

---

## 4. Ket luan GO-1

```text
Cell suy bien (err_neo < DEGENERATE_ERR = 0.02): 2/5
    poisson@0.700  err_neo = 0.000000
    cbr@0.700      err_neo = 0.000000
Ca hai co artifact ghi trang thai DEGENERATE va ratio = null. Khong bo im lang.

Cell danh gia duoc: 3/5. GO-1 dat tren CAN TREN CI95 o ca ba:
    poisson@0.925   ratio 1.000480   CI95 [0.998950, 1.001992]
    poisson@0.850   ratio 1.000968   CI95 [0.999067, 1.002946]
    h2@0.700        ratio 0.999363   CI95 [0.995529, 1.003173]

max CI95_high = 1.003173 < 1.02 = GO1_THRESHOLD
```

`A-6' = TRUE`. Theo `B-D8`, cau khang dinh duoc phep vao abstract:

```text
"Certification giu nguyen duong bien risk-coverage tren moi che do danh gia
 duoc: ti so AURC rieng phan tren cua so van hanh coverage [0.60, 1.00] la
 0.9994 - 1.0010, voi can tren khoang tin cay 95% la 1.0032. Noi cach khac,
 chi phi duong bien cua certification duoi 0.32% o muc tin cay 95%."
```

Con so `0.32%` la thu dang dua vao abstract: mot **can tren co so** manh hon
mot khang dinh khong CI.

### 4.0. Multiplicity tren 3 cell -- GO1-M1 va GO1-M2 (Amendment 23-24 muc 3)

`0.32%` lay tren cell XAU NHAT trong ba cell, moi cell mot CI 95% RIENG. Xac
suat de ca ba cung dung KHONG phai 95%; duoi doc lap no la `0.95^3 = 0.857`.
Day dung la van de multiplicity ma ca Phase 22 noi ve, xuat hien lai o tang
meta -- y het `qhat` chung o tang slot.

```text
GO1-M1  Abstract phat bieu TUNG CELL ("can tren 95% tren MOI che do danh gia
        duoc, cao nhat la 1.0032"). Chinh xac, khong ton them tinh toan.
GO1-M2  Bao cao THEM can DONG THOI bang Bonferroni 3 cell (moi cell o muc
        1 - 0.05/3 = 98.33%).
```

Da tinh, cung thu tuc, chi doi muc phan vi:

```text
cell            per-cell 95pct           Bonferroni 98.33pct
poisson@0.925   [0.998950, 1.001992]     [0.998636, 1.002322]
poisson@0.850   [0.999067, 1.002946]     [0.998738, 1.003401]
h2@0.700        [0.995529, 1.003173]     [0.994641, 1.004125]

max per-cell 95pct       CI_high = 1.003173   GO-1 PASS
max Bonferroni 98.33pct  CI_high = 1.004125   GO-1 PASS (dong thoi >= 95pct)
du dia toi nguong 1.02 duoi Bonferroni: 4.8x
```

**GO-1 dat theo ca hai cach doc**, nen ket luan muc 4 khong doi. Neu can mot
cau DONG THOI cho abstract:

```text
"Chi phi duong bien cua certification duoi 0.41% dong thoi tren ca ba che do
 danh gia duoc, o muc tin cay 95% (Bonferroni tren 3 cell)."
```

### 4.1. Cau KHONG duoc viet

```text
KHONG viet: "C3 tot hon C0" du h2@0.700 cho ratio 0.999363 < 1.
            CI cua no la [0.995529, 1.003173], chua 1.0. Khong co bang chung
            ve cai thien, cung nhu khong co bang chung ve suy giam.

KHONG viet: "bat bien tren moi cell". Hai cell suy bien KHONG duoc danh gia,
            khong phai da PASS.
```

### 4.2. Kich ban khong xay ra

Nhanh FAIL viet truoc o Amendment 23-22 muc 4 (viet cau "khong do duoc suy
giam, can tren la X%") **khong duoc dung**, vi `CI95_high < 1.02` o ca ba cell.
Giu nguyen doan do trong amendment lam ban ghi: no da duoc viet TRUOC khi biet
ket qua.

---

## 5. So MISS cua Lesson 23.5[B]

```text
A-5'  CI95_high in [1.01, 1.06]   MISS -- do 1.003173, hep hon du bao
A-7'  |bias| in [0.001, 0.010]    MISS -- do 0.012982 tren h2@0.700
"width CI ~ 1/sqrt(B)"            SAI  -- tieu chi MC sai khai niem, da sua
MC_N_SEEDS = 10                   SAI  -- phep do gate qua nhieu de cham vach
```

Hai dong cuoi la loi trong thiet ke cua chinh lesson nay, phat hien bang cach
chay va doc, khong phai bang cach doan.

---

## 6. Chuyen giao cho Lesson 23.5[C] (GO-2)

`paired_bootstrap_ratio()`, `mc_convergence()`, `block_sufficient_stats()`, va
`negative_control_self_ratio()` dung lai duoc nguyen ven cho GO-2. Doi duy nhat
la dai luong: tu **ti so AURC** sang **hieu `qhat`** tren 24 delta FWER.

```text
Nguyen tac tai su dung: acceptance, err|accept, coverage, sla_rate deu la
TI SO CUA TONG theo block, nen thong ke du (n_rows, n_acc, n_wrong_acc) dung
lai duoc. Voi hieu qhat, thong ke du la mot dem khac -- phai dan lai truoc khi
dung, KHONG duoc gia dinh.
```
