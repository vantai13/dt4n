# LESSON 23.24 -- KHONG GIAN HANH DONG HIEU DUNG

Tien dang ky : `A074-amendment-74.md`
Sua truoc khi chay : `A074b-amendment-74b.md`
Sua khiem khuyet nguon du lieu : `A075-amendment-75.md`
Artifact : `results/LIVE/phase-23/action_pruning.json`  (xem muc 9)
Ban chay THU NHAT bi VOID (`w_loss` sai): `results/SUPERSEDED/phase-23/action_pruning_VOID_wloss_defect.json`
Ma : `cert/action_pruning.py` · Test : `test/test_action_pruning.py`
Cell : `poisson@0.925` · Truc AoI : `measured_v7`, ho so **`U0`** (`L133`) ·
Truc SLA : `exogenous_g114_S-B`, `w_loss = 5000.0` · `kappa = 0.50` ·
Bonferroni · `alpha_family = 0.10` · 999495 hang (499798 calib / 499697 test)

## 0. Ket qua mot dong

```text
G23-297  M-233        PASS   tap CAT tren CALIB = {P2}, dung dai da ky
G23-298  M-234        PASS   ti so q_hat 0.923007; Delta acceptance +0.042714
G23-299  M-235        PASS   budget_share(S1) = 0.994144
G23-300  NC-23.24-1   FAIL   ve (ii) MISS: Delta err|accept = -0.093702
```

**Kich ban thi hanh: `K2`** (`A074` muc 6). Cau K1 KHONG duoc phat bieu.
`L43` KHONG dong duoc.

## 1. `G23-297` / `M-233` -- hanh dong chet, tren CALIB

Tieu chi hai tang cua `A074` muc 3.2, cham tren `is_calib` rows:

| duong | `P_calib(a* = a)` | tang 1 (< 0.05) | `P_calib(a_twin = a)` | tang 2(a) (= 0) | ket |
|---|---:|:--:|---:|:--:|:--|
| P1 | 0.634032 | khong | 0.596101 | -- | GIU |
| P2 | **0.000000** | DAT | **0.000000** | DAT | **CAT** |
| P3 | 0.358323 | khong | 0.391914 | -- | GIU |
| P4 | 0.007645 | DAT | 0.011985 | HONG | GIU |

Tap CAT = `{P2}`. Dai da ky: `== {P2}`. **HIT.**

### Do lon cua winner's curse

`A074` muc 4 bat do lai tren CALIB vi artifact 23.7 ghi
`definition_uses = "P(a* = a) on test rows (M-D5)"`. Do lech do duoc:

| dai luong | 23.7 TREN TEST | 23.24 TREN CALIB |
|---|---:|---:|
| `P(a* = P2)` | 1.4001e-05 | **0.000000** |
| `P(a* = P4)` | 0.007170 | 0.007645 |
| `P(a_twin = P4)` | 0.011601 | 0.011985 |
| `P(a* = P1)` | 0.659724 | 0.634032 |

Ket luan ve tap CAT KHONG doi giua hai nguon. Winner's curse o day nho --
nhung dieu do chi biet duoc SAU khi do lai, va no la mot ket qua chu khong
phai mot gia dinh.

### `A074` N2 -- chan quy tac ba

`P_calib(a_twin = P2) = 0` tren `n_calib = 499798` hang. Chan tren mot phia:

```text
3 / 499798 = 6.0024e-06
```

Duoc phat bieu: *"twin de xuat P2 voi xac suat <= 6.0e-06"*.
KHONG duoc phat bieu: *"twin khong bao gio de xuat P2"*.

`A074` N2 uoc `n_calib ~ 250k` va chan `1.2e-05`. So THAT la gap doi hang
va chan chat gap doi. N2 da ky la "tinh tu `n_calib` do duoc, khong hard-code"
nen khong co gi phai sua.

## 2. `G23-298` / `M-234` -- thang cat

| bac | cat | `m` | `alpha_each` | `min_blocks` | acceptance | `viol\|acc` | `err\|acc` | `err_anchor` |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| S0 K=4 | -- | 3 | 0.033333 | 29 | 0.426382 | 0.100037 | 0.100037 | 0.244502 |
| **S1 K=3** | P2 | 2 | 0.050000 | 19 | **0.469096** | 0.107425 | 0.107420 | 0.244502 |
| S2 K=2 | P2,P4 | 1 | 0.100000 | 9 | 0.554248 | 0.119936 | 0.128773 | 0.236846 |
| NC K=3 | P3 | 2 | 0.050000 | 19 | 0.846649 | 0.078654 | 0.013719 | 0.050152 |

*(hang NC in o muc 4; no la doi chung, khong phai mot bac cua thang)*

**(a) Ti so `q_hat`** -- `q_hat(K=3, alpha/2) / q_hat(K=4, alpha/3)`,
4 bin x 2 slot chung:

```text
z0  0.909231  0.938673
z1  0.910767  0.939066
z2  0.919459  0.933409
z3  0.905550  0.927899
---------------------------------
trung binh 0.923007     dai [0.88, 0.94]   HIT
gia tri giai tich half-normal   0.921016
```

⚠️ **Mot du bao co huong SAI.** `A074` muc 5 lap luan rang du duoi
(+3.71..+7.55%, tang theo do sau phan vi) lam MAU SO bi thoi nhieu hon TU SO,
nen ti so quan sat "nen THAP hon 0.921016 mot chut". Do duoc **0.923007**,
tuc CAO hon 0.22%. Dai van dat, nhung co so cua viec dat lech tam xuong duoi
la SAI. Ghi lai de khong ai trich dan lap luan do nhu da duoc xac nhan.

**(b) `Delta acceptance(S1 vs S0)`** = `0.469096 - 0.426382` = **+0.042714**.
Dai [+0.01, +0.05]. **HIT.** (23.7 do +0.034504 tren Mondrian 2 truc / TEST.)

**(c) `Delta acceptance(S2 vs S0)`** = **+0.127865**. `[MO TA]`, khong cham
diem (`A074` muc 5). 23.7 do +0.131683.

`A074` N5: S2 KHONG duoc de xuat -- no hong tang 2(a).
`P_calib(a_twin = P4) = 0.011985 > 0`, nen **cat P4 DOI quyet dinh**, khong
mien phi.

## 3. `G23-299` / `M-235` -- phan ra hai kenh   ★ ket qua quan trong nhat

Thiet ke giai thua 2x2, `acceptance` tren TEST:

### Bac S1 (cat P2)

```text
S0 goc                                       0.426382
nhanh (i)   CHI cat P2, giu alpha cua S0     0.426534   Delta = +0.000152
nhanh (ii)  CHI noi alpha_each, khong cat    0.468846   Delta = +0.042464
nhanh (iii) ca hai                           0.469096   Delta = +0.042714
tuong tac = (iii) - (i) - (ii) + S0                     +0.000098
-------------------------------------------------------------------
budget_share      = 0.994144     >= 0.90   HIT
constraint_share  = 0.003561
interaction_share = 0.002295
```

### Bac S2 (cat P2 + P4)

```text
nhanh (i)   0.439084   Delta = +0.012702      constraint_share = 0.099336
nhanh (ii)  0.541554   Delta = +0.115172      budget_share     = 0.900726
nhanh (iii) 0.554248   Delta = +0.127865      interaction      = -0.000008
```

### Doc

Kenh RANG BUOC dong gop **0.36%** cua hieu ung (`+0.000152` tuyet doi) --
khong phan biet duoc voi 0. Kenh NGAN SACH dong gop **99.41%** (`+0.042464`).

Toan bo `+0.042714` den tu viec `alpha_each` duoc noi tu `0.033333` len
`0.050000`.

> Vi vay cau **"bo hanh dong chet thu ve +4.27% acceptance"** la mot cau GAY
> HIEU NHAM, dung nhu `A074` muc 5 da canh bao truoc khi chay. Cach viet dung
> la: *"giam so hanh dong tu 4 xuong 3 lam so bien Bonferroni giam tu 3 xuong
> 2, va CHINH DIEU DO thu ve +4.27% acceptance."*

Tuong tac rat nho (+0.000098 va -0.000008) -- hai kenh gan nhu tac dong len
hai tap hang khac nhau.

> ⚠️ **DA RUT (`A075` muc 6).** Ban dau tien cua doc nay viet
> "`constraint_share` AM ... no mua duoc mot luong AM rat nho". Do la HIEN VAT
> cua `w_loss = 3222.24` sai (`L132`). Tren du lieu dung, `constraint_share`
> la `+0.003561` -- duong nhung khong phan biet duoc voi 0. Ket luan
> ("gan nhu toan bo hieu ung den tu kenh ngan sach") KHONG doi; chi cach dien
> dat doi, va gio no khong phai giai thich mot dau am kho chiu.

## 4. `G23-300` / `NC-23.24-1` -- doi chung am   ★ FAIL

Ban sua `A074b` muc 4: ve (i) da BO TRUOC khi chay (nhieu mo neo); giu ve
(ii); them ve chan (iii).

```text
nhanh CHET  cat P2 :  acceptance 0.469096   err|accept 0.107420   mo neo doi 0.000000
nhanh SONG  cat P3 :  acceptance 0.846649   err|accept 0.013719   mo neo doi 0.389900

ve (iii) VE CHAN : P_calib(a_twin=P2) = 0  VA  P_calib(a_twin=P3) = 0.391914 > 0.05
                   -> DAT. Ket qua ve (ii) DIEN GIAI DUOC.

ve (ii)          : Delta err|accept = 0.013719 - 0.107420 = -0.093702
                   dai doi >= +0.02
                   -> KHONG DAT.  FAIL.
```

`anchor_moved_rate` xac nhan du bao cua `A074b`: **0.389900** o nhanh P3
(du bao ~0.369 tu so 23.7 tren TEST) va **0.000000** o nhanh P2. Do la ly do
ve (i) da duoc bo -- neu con, no se do lan ca hieu ung mo neo nay.

### Thi hanh kich ban `K2` -- nguyen van

`A074` muc 6 da ky truoc:

> K2 -- `NC-23.24-1` ve (ii) KHONG dat -> KHONG duoc phat bieu cau K1. Thay
> bang mot HAN CHE: "khong gian hanh dong cua testbed THUA -- ba trong bon
> duong co the bo ma khong do duoc thiet hai. Moi ket luan ve pruning bi gioi
> han o testbed nay." `L43` KHONG dong duoc; ghi ly do.

Dieu do duoc thi hanh. **`L43` van mo.** Moi ket qua cua paper van phai in
kem cau cua `L43`.

### Mot chan doan POST-HOC -- xem `L131`, KHONG dung de cuu gate

`err_anchor` (ti le sai khi nhan TAT CA, truoc khi cong tin cay vao cuoc)
sup tu **0.244502** (cat P2) xuong **0.050152** (cat P3). Vi `P3` la `a*`
tren 34.07% hang calib, bo no di lam bai toan quyet dinh con lai de hon HAN
ve mat co hoc: gan nhu chi con P1 (`P_calib(a*=P1) = 0.6340`).

Nghia la `err|accept` **khong so sanh duoc** giua hai khong gian hanh dong
khac nhau, vi ban than TAP NHAN doi. Nen so `-0.093702` KHONG chung minh
chan doan ma `A074` muc 6 K2 dua ra ("he khong nhay voi viec mat mot hanh
dong song") -- no chung minh mot dieu khac.

Chan doan nay la POST-HOC. No duoc ghi vao `L131` va **khong** duoc dung de
doi ket luan: `A074` muc 6 ky rang khong kich ban nao duoc dien giai lai sau
khi nhin so. Ve (ii) la MISS, `K2` duoc thi hanh nguyen van.

He qua thiet ke cho lan sau (vao `BACKLOG.md`, khong mo nhanh o day --
`A071` R2): mot doi chung am cho pruning phai GHEP TAP NHAN, vi du cham
`err|accept` chi tren hang ma `a*` nam trong CA HAI khong gian, hoac dung
mot metric bat bien voi viec doi tap nhan.

## 4b. `viol|accept` -- mot truc KHONG AI KY DAI   `[MO TA]`   (`L135`)

`A074` ky dai cho `acceptance`, ti so `q_hat`, `budget_share`, `Delta err`.
KHONG ai ky dai cho `viol|accept`. Nhung no nam san trong artifact:

```text
S0_K4  (K=4, alpha_each 0.033333)   viol|accept = 0.100037
S1_K3  (K=3, alpha_each 0.050000)   viol|accept = 0.107425     +7.4%  so voi S0
S2_K2  (K=2, alpha_each 0.100000)   viol|accept = 0.119936    +19.9%  so voi S0
```

Tang DON DIEU theo bac thang cat. Co che ro: `alpha_each` noi -> `q_hat` hep
-> nhan them nhung hang sat bien -> ti le vi pham trong tap nhan tang.

### Hai canh bao ve cach doc con so nay

```text
(1) `alpha` la ngan sach mat-bao-phu CUA BANG CONFORMAL, cham TREN CALIB va
    theo tung slot. `viol|accept` la mot dai luong CO DIEU KIEN tren viec
    NHAN, cham tren TEST. Hai doi tuong KHAC NHAU. "viol|accept > alpha"
    KHONG tu dong la mot bao dam bi pha.
(2) `S0_K4` -- cau hinh KHONG cat gi -- da o 0.100037, tuc DA o dung bien
    alpha TRUOC khi cat bat ky thu gi. Nen khong doc duoc thanh "viec cat
    lam vo mot bao dam von dang giu".
```

### Cau doc duoc

> Cat hanh dong chet mua `+4.27%` acceptance va tra bang `viol|accept` tang
> tu `0.1000` len `0.1074` (`+7.4%` tuong doi). Day khong phai mot mon mien
> phi ma la mot GIAO DICH CO GIA DO DUOC. Va toan bo giao dich nam o kenh
> ngan sach `alpha` (`99.41%`), khong o viec don khong gian hanh dong
> (`0.36%`).

**KY LUAT:** quan sat POST-HOC, khong dai nao duoc ky cho `viol`. Nhan
`[MO TA]`, KHONG duoc dem la mot `CL-*` moi. Muon phat bieu trong paper thi
phai tien dang ky o mot lesson sau. Ghi `L135`. (`A075` muc 7.)

## 5. Quan sat GIAI TICH (khong ton gate) -- `A074` muc 7

```text
K = 4   alpha_each = 0.033333   min blocks = 29
K = 3   alpha_each = 0.050000   min blocks = 19
K = 2   alpha_each = 0.100000   min blocks =  9
```

`ceil((n+1)(1-alpha_each)) <= n` -- dai so, KHONG phai phep do, KHONG duoc
trich dan nhu phat hien thuc nghiem (tien le `CL-10`, `CL-13`).

Y nghia cho `L125`: o `K = 3` san tu choi la 19 thay vi 29, tuc de tim mot
cell co o duoi san hon. Ghi lai; khong mo nhanh (`A071` R2).

## 6. Nhan bat buoc tren moi so cu   (`A074` N1)

Moi con so trich tu Lesson 23.7 trong doc nay -- 0.034504, 0.131683, 0.9930,
0.8496, `P(a*)`, `P(a_twin)` -- do tren **Mondrian HAI truc** va tren **TEST
rows**: `[23.7 -- Mondrian 2 truc, TREN TEST]`. Lesson 23.24 do tren MOT truc
(`selective`, `CL-01`) va, voi `M-233`, tren CALIB.

`A074` N3: ca lesson do tren MOT cell (`poisson@0.925`). Tap hanh dong chet
co the KHAC o cell khac. Moi phat bieu gioi han o cell nay.

`A074` N4: Bonferroni duoc giu. Sidak chi la tham chieu giai tich:
`K=4: 2.114054`, `K=3: 1.948822`, `K=2: 1.644854`.

## 7. Phat bieu duoc phep, va phat bieu KHONG duoc phep

```text
DUOC PHEP:
  · "Tren cell poisson@0.925, ho so AoI U0, mot trong bon duong (`P2`) khong
     bao gio la hanh dong toi uu tren tap hieu chinh (499798 hang), va twin
     khong bao gio de xuat no -- xac suat that <= 6.0e-06 (quy tac ba)."
  · "Bo duong do thu ve +4.27% acceptance, nhung phan ra hai kenh cho thay
     99.41% cua muc do dat den tu viec noi ngan sach Bonferroni tu alpha/3
     len alpha/2. Dong gop cua chinh viec don khong gian hanh dong la
     +0.36%, khong phan biet duoc voi 0."
  · "Ti so q_hat giua hai cau hinh (0.9230) khop du doan half-normal
     (0.9210) trong 0.22%."

KHONG DUOC PHEP:
  · "Bo mot hanh dong khong bao gio toi uu thu ve X% acceptance ma khong mat
     bao dam nao."  <- doi chung am KHONG chong duoc cau nay (`G23-300` FAIL)
  · "twin khong bao gio de xuat P2."  <- phai dung chan 6.0e-06 (`A074` N2)
  · "K = 2 la mot cau hinh de xuat."  <- hong tang 2(a) (`A074` N5)
  · Bat ky cau nao dua tren `err|accept` so sanh giua hai khong gian hanh
    dong khac nhau.  <- `L131`
  · "viol|accept vuot alpha nen bao dam conformal bi pha."  <- hai doi tuong
    khac nhau, va S0 da o bien truoc khi cat. Xem muc 4b (`L135`)
  · Bat ky cau nao ngoai suy sang ho so AoI `U3` (chuoi chung nhan chinh).
    Lesson nay do tren `U0`.  <- `L133`
```

## 8. Ngan sach

```text
Da tieu   : 24 / 35 tuan (MASTER_PLAN_v8 PART II)
Con lai   : 5 lesson (23.25..23.29) + Phase 24 + Phase 25
Gate lesson nay: 4 / 4  (`A071` R1 -- dung ngan sach, khong mo them)
```

Gioi han moi sinh trong lesson nay: `L130` (truc cua `prepare()`), `L131`
(`err|accept` khong so sanh duoc giua hai khong gian hanh dong), `L132`
(`w_loss` mac dinh -- DA SUA, `A075`), `L133` (`cell_matrices` khong sinh
duoc `U3` -> pham vi da tuyen), `L134` (`validity_block` nhan loi khai --
quy tac R6), `L135` (`viol|accept` chua co dai). Tat ca vao `BACKLOG.md`,
khong mo nhanh trong lesson nay (`A071` R2).

`G23-297..300` duoc thi hanh HAI LAN: lan dau tren `w_loss` sai (VOID), lan
hai tren du lieu dung. Theo `A075` muc 2 day KHONG tinh la 4 gate moi --
chay lai mot gate tren du lieu dung khong tieu them ngan sach.

## 9. Tai tao

```bash
.venv/bin/python -m pytest test/test_action_pruning.py -q
.venv/bin/python -m cert.action_pruning --dead    # G23-297, DUNG lai doc
.venv/bin/python -m cert.action_pruning --run     # G23-298..300
```

Thoi gian may: `--dead` 5.0 s, `--run` 16.2 s tren may tac gia.
`A074b` muc 6 da bac bo de nghi cache `/tmp`: khong can, va mot lop cache
khong can thiet la mot nguon lech im lang giua hai lan chay (`L118`).

Trinh thong dich la `.venv/bin/python` (ton tai o dot nay; xem `L117` ve
lan truoc no khong ton tai).

### Lech so voi `A074` muc 1: tang artifact

`A074` muc 1 cap `results/PENDING/phase-23/action_pruning.json`. Artifact
that su nam o `results/LIVE/phase-23/action_pruning.json`.

Ly do: `test_pending_artifacts_declare_what_they_wait_for` doi moi artifact o
`PENDING/` phai khai `pending_on` = truc CHUA duoc duyet, va no do neu truc do
DA duoc duyet. Ca hai truc cua artifact nay -- `measured_v7_uniform` va
`exogenous_g114_S-B` -- da nam trong `axis_registry.json::approved_for_live`,
nen tang dung la LIVE. Cai chan tu don o cho do.

Day KHONG phai mot lech ve khoa hoc: khong dai nao, khong so nao doi. Va no la
DUNG duong ma Lesson 23.23 da di -- `A072` muc 1 cung cap `PENDING/`, va
`baselines_lit.json` duoc promote len `LIVE/` o commit `6fa8365`.
