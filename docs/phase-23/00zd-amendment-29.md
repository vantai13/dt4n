# AMENDMENT 23-29 -- Dong no K-D12: cham 15 dong du doan cua Lesson 23.1/23.2/23.3

Ngay: 2026-08-20
Commit: sau `e37751f` (artifact 23.6), TRUOC khi viet `11-abstain-cost.md`.

```text
(1) AUDIT PROVENANCE truoc khi dien -- ket qua: DAT, 15 dong deu tinh diem
(2) SUA so mon no tu 14 -> 15, va ghi CO CHE bo sot (ong thoat trong markdown)
(3) dien 15 gia tri, tinh lai doc lap tu artifact trong repo
(4) K-D13: B4p va B3p do CUNG MOT dai luong -- khong duoc dem hai lan
(5) K-D14: B3p va B6p DOI KET QUA theo cach doc `err` -- ti le hit KHONG duy nhat
(6) NT-v2-17 (cau hoi mang khang dinh) va NT-v2-18 (test so o cua bang)
(7) F4 la du doan BAT KHA THI, khong phai du doan SAI -- Lesson 23.6 giai thich
```

---

## 1. Audit provenance -- BAT BUOC, va no DAT

Cham TRE khong lam mat hieu luc mot dong du doan. Cai lam mat hieu luc la dai bi
SUA sau khi thay so. Do la mot cau hoi ve provenance, va `git` tra loi duoc.

### 1.1. Dai duoc ky luc nao

```text
git log --follow -- docs/phase-23/00-preregistration.md   (dong dau tien)
   1c5b208   2026-08-14 08:59:41 +0700   "prereg(phase-23): sign fallback audit and GO debts"
   = 2026-08-14 01:59:41 UTC

git log --reverse -S'| F4 | 23.1' -- docs/phase-23/00-preregistration.md
   1c5b208   <- dong F4 duoc THEM tai chinh commit ky
```

### 1.2. Dai co bi sua sau do khong -- KHONG

Dem so commit cham vao TUNG chuoi dai:

```text
'0.21-0.27'    (F1)  : 1 commit      '0.212-0.232' (B1p) : 1 commit
'0.17-0.24'    (F2)  : 1 commit      '0.85-0.98'   (B2p) : 1 commit
'0.10-0.18'    (F3)  : 1 commit      '> 0.90'      (T3)  : 1 commit
'100-250 ms'   (F5)  : 1 commit
```

Moi dai xuat hien o DUNG MOT commit -- tuc commit ky. Khong dai nao bi sua.

### 1.3. Artifact duoc tao SAU khi ky

```text
                                              tao luc (UTC)          sau khi ky?
fallback_poisson_0.925_k0.5.json              2026-08-14 07:23:25    CO (+5h24m)
threshold_families_poisson_0.925_...json      2026-08-14 14:09:31    CO (+12h10m)
baseline_rankings_poisson_0.925_...json       2026-08-14 14:22:19    CO (+12h23m)
```

```text
KET LUAN AUDIT: ca 15 dong duoc ky TRUOC khi artifact tuong ung ton tai, va
khong dai nao bi sua sau do. 15 dong nay TINH DIEM.
Khac han K-1/K-3/K-4/K-5 (Amd 23-26), duoc ky KHI artifact DA ton tai -> [TAT DINH].
```

---

## 2. Mon no la 15 dong, khong phai 14 -- va co che bo sot

Amendment 23-28 muc 7 ghi 14 dong. **Sai. Dung la 15.** Dong bi sot la `B1p`.

### 2.1. Co che

```text
| B1p | 23.3 | err\|accept cua B1 tai coverage 0.5 | [CO CHE] | 0.212-0.232 | ___ | ___ |
                  ^^
                  ONG THOAT trong o mo ta
```

Mot phep cat tren MOI dau `|` cho dong nay **8 o thay vi 7**. Cot "Do duoc" truot
sang mot vi tri va tra ve `0.212-0.232` chu khong phai `___`. Khong loi nao duoc
nem. Dong don gian **bien mat** khoi ket qua quet.

Do duoc:

```text
quet NGAY THO (split tren moi |) : 14 dong
quet DUNG     (bo qua \|)        : 15 dong      chenh lech: ['B1p']
```

### 2.2. Pham vi that su cua lo hong -- NAM dong, hai dong do CHINH TOI them

```text
dong 197  B1p    `err\|accept`                     8 o
dong 214  A-7'   `\|discretisation_bias\|`         9 o
dong 217  C-1    `max_k \|d_k-dbar_k\|/sigma_k`    9 o
dong 231  K-10   ... CHUA 0 ...                    9 o   <- toi them o Amd 23-26
dong 234  K-13   `max(\|drop\| / MDE)`             9 o   <- toi them o Amd 23-27
```

Ba dong dau da co san; hai dong cuoi la do chinh toi them vao khi ap Amendment
23-26 va 23-27. Toi da mo rong lo hong ma toi sau do di tim.

Ngoai ra, dong 26 (bang pilot disclosure) co mot ong **CHUA** thoat:

```text
| `err|accept` cua B3 tai h=0.30 | 0.1767 | ... |     -> 4 o thay vi 3
```

### 2.3. Lan thu BA cung mot loai loi

```text
lan 1  test so gate   "G23-1 ... G23-73"  -- KY HIEU KHOANG doc thanh hai gate
lan 2  23.5[B] PH#8   AURC luoi tho vs min -- ket luan doi theo do min
lan 3  quet prereg    ONG THOAT lam truot cot -- mot dong bien mat lang le
```

Mot nguyen nhan: **phan tich mot dinh dang danh cho NGUOI DOC bang mot phep cat
danh cho MAY.** Bai hoc da rut o `test_phase23_gate_ledger.py` ("khong parse van
xuoi; doc tu mot REGISTRY co dinh dang co dinh") nhung chua ap cho bang prereg.

```text
NT-v2-18  Moi BANG duoc doc bang may phai co mot test khang dinh SO O CUA MOI
          DONG. Mot dong sai so o KHONG nem loi -- no bi bo qua lang le, va mot
          phep DEM tren no cho ket qua thieu ma trong nhu day du.
          Phep cat phai ton trong ky tu thoat: `re.split(r'(?<!\\)\|', ...)`.
          (NT-v2-12 noi ve ID khong ton tai; day noi ve DONG khong duoc doc.)
```

Thuc thi trong `test/test_phase23_prereg.py`:

```text
test_every_markdown_table_row_has_a_consistent_cell_count
test_prediction_table_rows_all_have_seven_cells
test_unfilled_prediction_set_is_pinned
test_naive_split_would_miss_B1p_and_the_escaped_parser_does_not
test_reading_dependent_rows_are_flagged_as_such
```

---

## 3. NT-v2-17 -- mot cau hoi "vi sao X" luon mang khang dinh rang X dung

Amendment 23-28 muc 2 bac bo tien de "F1/F3 khong rut gon duoc theo block". Tien
de do den tu mot cau hoi dat duoi dang "vi sao khong rut gon duoc", tuc no da
gia dinh san cau tra loi.

```text
NT-v2-17  Mot cau hoi "vi sao X" LUON mang mot khang dinh: rang X dung. Truoc
          khi tra loi, hoi "X co dung khong?" -- va TRA LOI bang cach doc MA
          NGUON hoac ARTIFACT, khong bang cach suy tu TEN GOI.

          "stateful" la mot TEN GOI. "state reset o dau moi block" la mot TINH
          CHAT DO DUOC. Ten goi khong suy ra tinh chat.
```

Cung ho voi `NT-v2-8` (`c_supt` khong suy duoc tu tom tat vo huong) va
`NT-v2-12` (ID khong co trong repo la ID khong ton tai). Ca ba la mot cau:
**dung suy tu nhan, hay do.**

---

## 4. Muoi lam gia tri -- tinh lai doc lap tu artifact

Nguon: `fallback_poisson_0.925_k0.5.json` (23.1),
`threshold_families_poisson_0.925_C3_static.json` (23.2),
`baseline_rankings_poisson_0.925_C3_static.json` (23.3, chi so luoi 50 =
coverage do duoc 0.500001).

```text
ID    Dai luong                                Dai khoa       Do duoc          KQ
──────────────────────────────────────────────────────────────────────────────────
F1    err_system(F2 STATIC) @ kappa=0.5        0.21 - 0.27    0.238685753      HIT
F2    err_system(F1 STICKY) @ kappa=0.5        0.17 - 0.24    0.236889635      HIT
F3    err_system(F3 WAIT)   @ kappa=0.5        0.10 - 0.18    0.236889635      MISS (cao)
F4    Thu tu risk F2 > F1 > F3                 cau truc       F2 > F1 = F3     MISS (xem muc 6)
F5    Do tre quyet dinh trung binh F3          100 - 250 ms   103.95 / 204.27  HIT (xem 4.1)
F6    err_system(C3 + fallback tot nhat)       < 0.222399     0.236889635      MISS (cao)
T2    CONG thoai hoa ve coverage 1.0           cau truc       max cov = 1.0    HIT
T3    Spearman(err, regret)                    > 0.90         0.9991 / 1.0000 / 0.9991  HIT
T4    Spearman(err, sla_rate)                  > 0.80         0.9930 / 0.9789 / 0.9918  HIT
B1p   err|accept cua B1 @ cov 0.50             0.212 - 0.232  0.222762257      HIT
B2p   err(C3)/err(B2) @ cov 0.50               0.85 - 0.98    0.916133         HIT
B3p   err(C3)/err(B3) @ cov 0.50               < 0.70         0.467929         HIT*
B4p   err(C3)/err(B4) @ cov 0.50               0.6 - 0.9      0.467929         MISS
B5p   err(C3)/err(B5) @ cov 0.50               0.7 - 1.0      0.919967         HIT
B6p   err(B6)/err(C3) @ cov 0.50               < 0.5          0.097099         HIT*
──────────────────────────────────────────────────────────────────────────────────
   * = doi ket qua theo cach doc `err`; xem muc 5.2. KHONG phai HIT chac chan.
```

T3/T4 ghi ba gia tri theo ba ho (`additive / multiplicative / combined`); ca ba
deu vuot nguong nen ket qua khong phu thuoc cach chon.

### 4.1. F5 -- HIT, nhung dong nay thieu nhan `rowset`

```text
"Do tre quyet dinh trung binh F3" khong ghi TAP HANG.
   103.95 ms  = trung binh tren MOI hang
   204.27 ms  = trung binh tren hang BI TU CHOI
Ca hai deu trong [100, 250] -> HIT du doc kieu nao.

NHUNG: neu so roi vao 95 ms va 210 ms thi cung mot dong vua MISS vua HIT.
Dong nay thoat nho MAY, khong nho THIET KE. Do la ly do P15 ("moi prediction
phai noi ro thu tuc, slot/nhom, tap hang") ton tai.
```

---

## 5. Hai loi ke toan trong chinh bang du doan

### 5.1. K-D13 -- B4p va B3p do CUNG MOT dai luong

```text
G23-10b da chung minh B4 == B3 bit-for-bit (B4 chi la AoI threshold duoc tham
so hoa lai). Do duoc o day: err(B3) == err(B4) CHINH XAC tren moi thang.

=> B3p va B4p KHONG phai hai du doan doc lap. Chung la HAI DAI khac nhau duoc
   ky cho CUNG MOT dai luong: `< 0.70` va `[0.6, 0.9]`.
   Gia tri do duoc (0.467929) roi vao dai thu nhat va ngoai dai thu hai.
```

```text
K-D13  Khi hai dong du doan duoc chung minh la do CUNG MOT dai luong, chung
       duoc gop thanh MOT dong khi bao cao ti le prediction-hit, va dong gop
       do mang trang thai CONFLICTED = MISS.

       Ly do: mot pre-registration ky HAI dai khong tuong thich cho cung mot
       dai luong la mot pre-registration da PHONG HAI CUA. Khong duoc nhan
       diem tu cua nao trung. Day la dang nhe cua "garden of forking paths",
       va cach xu ly phai giong nhau: khong cho diem.

       Mau so doc lap cua Lesson 23.1-23.3 la 14, khong phai 15.
```

### 5.2. K-D14 -- ti le hit KHONG DUY NHAT: `err` cua bon dong B*p thieu nhan MUC

`B1p` ghi ro `err|accept`. Bon dong `B2p..B6p` chi ghi `err(C3)/err(B*)`, khong
noi la `err_accept` hay `err_system`. Do duoc ca hai cach:

```text
ID    dai khoa       err_accept   KQ     err_system   KQ     ghi chu
────────────────────────────────────────────────────────────────────────
B1p   0.212-0.232    0.222762     HIT    0.222762     HIT    (cung mot so)
B2p   0.85-0.98      0.916133     HIT    0.972820     HIT    ROBUST
B3p   < 0.70         0.467929     HIT    0.914565     MISS   ** DOI **
B4p   0.6-0.9        0.467929     MISS   0.914565     MISS   ROBUST
B5p   0.7-1.0        0.919967     HIT    0.970549     HIT    ROBUST
B6p   < 0.5          0.097099     HIT    0.911362     MISS   ** DOI **
```

```text
K-D14  Cach doc CHINH la `err_accept`, va ly do la VAN BAN chu khong phai KET QUA:
       `B1p` -- dong DAU TIEN cua khoi B*p -- ghi ro `err|accept`, nen quy uoc
       trong khoi la `err|accept`.

       PHAI cong bo ca hai cach doc va PHAI danh dau `B3p`/`B6p` la
       READING-DEPENDENT. Chung KHONG duoc trinh bay nhu HIT chac chan.

       Cong bo bat buoc: cach doc duoc chon cho TI LE CAO HON (11/15 so voi
       9/15). Viec no duoc chon vi ly do van ban chu khong vi ly do ket qua la
       mot khang dinh ve DONG CO, va nguoi doc co quyen khong tin. Do la ly do
       ca hai bang phai duoc in.
```

### 5.3. Ti le -- BON con so, in ca bon

```text
                              tho (15 dong)      sau K-D13 (14 dai luong)
doc `err_accept` (chinh)      11 HIT / 4 MISS    10 HIT / 4 MISS
doc `err_system`               9 HIT / 6 MISS     9 HIT / 5 MISS
```

```text
K-D15  Khi bao cao ti le prediction-hit cua Lesson 23.1-23.3, phai in CA BON
       con so kem ly do, hoac khong in con so nao. Chon mot con so va bo ba
       con so kia la bao cao co chon loc.
```

---

## 6. F4 -- du doan BAT KHA THI, khong phai du doan SAI

```text
F4 du doan thu tu NGHIEM NGAT  F2 > F1 > F3.
Do duoc tren artifact CUA CHINH Lesson 23.1 tai kappa = 0.5:
        0.238685753  >  0.236889635  =  0.236889635
        (F2 STATIC)     (F1 STICKY)     (F3 WAIT)
Bat dang thuc thu nhat DUNG. Bat dang thuc thu hai la DANG THUC.
```

Theo `F-23.6-6` (Amendment 23-28 muc 1), dieu nay **khong the khac di voi bat ky
du lieu nao**: `fallback_wait(secondary="sticky")` tra ve chinh
`fallback_sticky(...)`, nen F1 va F3 la CUNG MOT hanh dong.

```text
=> F4 khong bi bac bo boi DU LIEU. No bi bac bo boi CAU TRUC KHONG GIAN THIET KE,
   va nguoi ky khong nhin thay dieu do luc ky.

Cham diem KHONG doi: F4 van la MISS, cham bang artifact 23.1 tai dieu kien da
khoa. F-23.6-6 dong vai tro GIAI THICH, khong dong vai tro BANG CHUNG.
```

```text
NT-v2-19  Mot phat hien o lesson SAU khong duoc dung de CHAM LAI mot dong o
          lesson TRUOC. No chi duoc dung de HIEU ket qua cham. Tron hai vai tro
          la mot dang cham diem hoi to.
```

Day la lan dau trong Phase 23 mot phat hien o lesson sau giai thich mot MISS o
lesson truoc ma luc do khong ai hieu. No cho thay `F-23.6-6` khong phai chi
tiet ky thuat -- no la mot su that ve khong gian thiet ke da am tham lam hong
mot du doan tu ba lesson truoc.

### 6.1. F3 va F6 -- cung mot nguyen nhan, va no la diem van hanh

```text
Ca hai gia dinh mot fallback nao do dua err_system XUONG DUOI neo (0.222399).
Do duoc: fallback TOT NHAT tai kappa = 0.5 cho 0.236890 -- CAO HON neo 6.5%.

Tai kappa = 0.5, coverage = 0.4911: mot nua so hang bi day sang fallback, va
tren nua do fallback te hon twin.

kappa = 0.5 nam NGOAI beneficial band [0.6076, 0.99995] do Lesson 23.3 do duoc.
Nguoi ky chon kappa = 0.5 lam diem cham TRUOC khi biet band nam o dau.

=> Mot du doan co the MISS vi DIEM VAN HANH duoc chon sai, chu khong vi CO CHE
   sai. Phai viet ro; dung de reviewer tu phat hien.
```

---

## 7. RA SOAT (NT-v2-7 ap cho chinh amendment nay)

| Dong da khoa | Xu ly | Ly do |
|---|---|---|
| F1..F6, T2..T4, B1p..B6p | DIEN ket qua | audit muc 1 DAT; dai KHONG doi |
| B3p, B4p | gop lam MOT khi tinh ti le | K-D13 |
| B3p, B6p | danh dau READING-DEPENDENT | K-D14 |
| F0, G3a, G3b, S-5, S-8, A-*, C-* | GIU NGUYEN | da cham tu truoc |
| K-1..K-15 | GIU NGUYEN | Lesson 23.6, khong lien quan |
| GATES.md | KHONG DOI | day la du doan, khong phai gate |

```text
Sau amendment nay, bang pre-registration KHONG con o `___` nao cho cac lesson
DA DONG. Mon no K-D12 DONG.
Ti le prediction-hit cua Phase 23 tro nen TINH DUOC -- voi dieu kien in du bon
con so cua K-D15.
```

---

## 8. Pham vi duoc phep chay sau amendment nay

```text
* sua docs/phase-23/00-preregistration.md: dien 15 dong; thoat ong o dong 26
* sua test/test_phase23_prereg.py: them 3 test (so o, tap chua dien duoc ghim,
  parser ton trong ky tu thoat)
* them docs/phase-23/06-reframe.md, docs/phase-23/11-abstain-cost.md
* them cert/plot_abstain_cost.py va hai hinh trong results/phase-23/

KHONG sua: GATES.md, cert/abstain_cost.py, moi module cert/ khac
```

---

## 9. Chu ky

```text
Nguoi ky : vantai (Claude-assisted)
Ngay     : 2026-08-20
```

Toi xac nhan: audit provenance o muc 1 duoc chay TRUOC khi dien bat ky gia tri
nao; khong mot dai nao bi sua; va cach doc `err_accept` o muc 5.2 duoc chon vi
ly do VAN BAN (`B1p` ghi ro nhan trong cung khoi), voi viec no cho ti le cao
hon duoc cong bo tuong minh.
