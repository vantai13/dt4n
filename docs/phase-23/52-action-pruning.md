# LESSON 23.24 -- KHONG GIAN HANH DONG HIEU DUNG

Tien dang ky : `A074-amendment-74.md`
Sua truoc khi chay : `A074b-amendment-74b.md`
Artifact : `results/LIVE/phase-23/action_pruning.json`  (xem muc 9)
Ma : `cert/action_pruning.py` · Test : `test/test_action_pruning.py`
Cell : `poisson@0.925` · Truc : `measured_v7` · `kappa = 0.50` ·
Bonferroni · `alpha_family = 0.10` · 999495 hang (499798 calib / 499697 test)

## 0. Ket qua mot dong

```text
G23-297  M-233        PASS   tap CAT tren CALIB = {P2}, dung dai da ky
G23-298  M-234        PASS   ti so q_hat 0.923259; Delta acceptance +0.039508
G23-299  M-235        PASS   budget_share(S1) = 1.003850
G23-300  NC-23.24-1   FAIL   ve (ii) MISS: Delta err|accept = -0.091538
```

**Kich ban thi hanh: `K2`** (`A074` muc 6). Cau K1 KHONG duoc phat bieu.
`L43` KHONG dong duoc.

## 1. `G23-297` / `M-233` -- hanh dong chet, tren CALIB

Tieu chi hai tang cua `A074` muc 3.2, cham tren `is_calib` rows:

| duong | `P_calib(a* = a)` | tang 1 (< 0.05) | `P_calib(a_twin = a)` | tang 2(a) (= 0) | ket |
|---|---:|:--:|---:|:--:|:--|
| P1 | 0.652736 | khong | 0.612714 | -- | GIU |
| P2 | **0.000000** | DAT | **0.000000** | DAT | **CAT** |
| P3 | 0.340698 | khong | 0.376902 | -- | GIU |
| P4 | 0.006567 | DAT | 0.010384 | HONG | GIU |

Tap CAT = `{P2}`. Dai da ky: `== {P2}`. **HIT.**

### Do lon cua winner's curse

`A074` muc 4 bat do lai tren CALIB vi artifact 23.7 ghi
`definition_uses = "P(a* = a) on test rows (M-D5)"`. Do lech do duoc:

| dai luong | 23.7 TREN TEST | 23.24 TREN CALIB |
|---|---:|---:|
| `P(a* = P2)` | 1.4001e-05 | **0.000000** |
| `P(a* = P4)` | 0.007170 | 0.006567 |
| `P(a_twin = P4)` | 0.011601 | 0.010384 |
| `P(a* = P1)` | 0.659724 | 0.652736 |

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
| S0 K=4 | -- | 3 | 0.033333 | 29 | 0.434585 | 0.099774 | 0.093502 | 0.239147 |
| **S1 K=3** | P2 | 2 | 0.050000 | 19 | **0.474093** | 0.107732 | 0.103794 | 0.239141 |
| S2 K=2 | P2,P4 | 1 | 0.100000 | 9 | 0.558601 | 0.118299 | 0.119542 | 0.231690 |
| NC K=3 | P3 | 2 | 0.050000 | 0.860053 | -- | 0.078101 | 0.012256 | 0.044863 |

*(hang NC in o muc 4; no la doi chung, khong phai mot bac cua thang)*

**(a) Ti so `q_hat`** -- `q_hat(K=3, alpha/2) / q_hat(K=4, alpha/3)`,
4 bin x 2 slot chung:

```text
z0  0.911494  0.934655
z1  0.914025  0.936678
z2  0.920168  0.933417
z3  0.906012  0.929624
---------------------------------
trung binh 0.923259     dai [0.88, 0.94]   HIT
gia tri giai tich half-normal   0.921016
```

⚠️ **Mot du bao co huong SAI.** `A074` muc 5 lap luan rang du duoi
(+3.71..+7.55%, tang theo do sau phan vi) lam MAU SO bi thoi nhieu hon TU SO,
nen ti so quan sat "nen THAP hon 0.921016 mot chut". Do duoc **0.923259**,
tuc CAO hon 0.24%. Dai van dat, nhung co so cua viec dat lech tam xuong duoi
la SAI. Ghi lai de khong ai trich dan lap luan do nhu da duoc xac nhan.

**(b) `Delta acceptance(S1 vs S0)`** = `0.474093 - 0.434585` = **+0.039508**.
Dai [+0.01, +0.05]. **HIT.** (23.7 do +0.034504 tren Mondrian 2 truc / TEST.)

**(c) `Delta acceptance(S2 vs S0)`** = **+0.124015**. `[MO TA]`, khong cham
diem (`A074` muc 5). 23.7 do +0.131683.

`A074` N5: S2 KHONG duoc de xuat -- no hong tang 2(a).
`P_calib(a_twin = P4) = 0.010384 > 0`, nen **cat P4 DOI quyet dinh**, khong
mien phi.

## 3. `G23-299` / `M-235` -- phan ra hai kenh   ★ ket qua quan trong nhat

Thiet ke giai thua 2x2, `acceptance` tren TEST:

### Bac S1 (cat P2)

```text
S0 goc                                       0.434585
nhanh (i)   CHI cat P2, giu alpha cua S0     0.434285   Delta = -0.000300
nhanh (ii)  CHI noi alpha_each, khong cat    0.474245   Delta = +0.039660
nhanh (iii) ca hai                           0.474093   Delta = +0.039508
tuong tac = (iii) - (i) - (ii) + S0                     +0.000148
-------------------------------------------------------------------
budget_share      = 1.003850     >= 0.90   HIT
constraint_share  = -0.007598              <- AM
interaction_share =  0.003748
```

### Bac S2 (cat P2 + P4)

```text
nhanh (i)   0.446705   Delta = +0.012119      constraint_share = 0.097725
nhanh (ii)  0.546275   Delta = +0.111690      budget_share     = 0.900613
nhanh (iii) 0.558601   Delta = +0.124015      interaction      = +0.000206
```

### Doc

`constraint_share(S1)` **AM**. Nghia la: bo `P2` ra khoi tap ung vien, trong
khi GIU nguyen ngan sach `alpha` cua S0, lam ti le chap nhan **giam** 0.0003.
Viec don khong gian hanh dong tu no khong nhung khong mua duoc acceptance --
no mua duoc mot luong AM rat nho.

Toan bo `+0.039508` den tu viec `alpha_each` duoc noi tu `0.033333` len
`0.050000`, tuc tu kenh NGAN SACH.

> Vi vay cau **"bo hanh dong chet thu ve +3.95% acceptance"** la mot cau GAY
> HIEU NHAM, dung nhu `A074` muc 5 da canh bao truoc khi chay. Cach viet dung
> la: *"giam so hanh dong tu 4 xuong 3 lam so bien Bonferroni giam tu 3 xuong
> 2, va CHINH DIEU DO thu ve +3.95% acceptance."*

Tuong tac nho (+0.000148 va +0.000206) -- hai kenh gan nhu tac dong len hai
tap hang khac nhau.

## 4. `G23-300` / `NC-23.24-1` -- doi chung am   ★ FAIL

Ban sua `A074b` muc 4: ve (i) da BO TRUOC khi chay (nhieu mo neo); giu ve
(ii); them ve chan (iii).

```text
nhanh CHET  cat P2 :  acceptance 0.474093   err|accept 0.103794   mo neo doi 0.000000
nhanh SONG  cat P3 :  acceptance 0.860053   err|accept 0.012256   mo neo doi 0.374783

ve (iii) VE CHAN : P_calib(a_twin=P2) = 0  VA  P_calib(a_twin=P3) = 0.376902 > 0.05
                   -> DAT. Ket qua ve (ii) DIEN GIAI DUOC.

ve (ii)          : Delta err|accept = 0.012256 - 0.103794 = -0.091538
                   dai doi >= +0.02
                   -> KHONG DAT.  FAIL.
```

`anchor_moved_rate` xac nhan du bao cua `A074b`: **0.374783** o nhanh P3
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
sup tu **0.239141** (cat P2) xuong **0.044863** (cat P3). Vi `P3` la `a*`
tren 34.07% hang calib, bo no di lam bai toan quyet dinh con lai de hon HAN
ve mat co hoc: gan nhu chi con P1 (`P_calib(a*=P1) = 0.6527`).

Nghia la `err|accept` **khong so sanh duoc** giua hai khong gian hanh dong
khac nhau, vi ban than TAP NHAN doi. Nen so `-0.091538` KHONG chung minh
chan doan ma `A074` muc 6 K2 dua ra ("he khong nhay voi viec mat mot hanh
dong song") -- no chung minh mot dieu khac.

Chan doan nay la POST-HOC. No duoc ghi vao `L131` va **khong** duoc dung de
doi ket luan: `A074` muc 6 ky rang khong kich ban nao duoc dien giai lai sau
khi nhin so. Ve (ii) la MISS, `K2` duoc thi hanh nguyen van.

He qua thiet ke cho lan sau (vao `BACKLOG.md`, khong mo nhanh o day --
`A071` R2): mot doi chung am cho pruning phai GHEP TAP NHAN, vi du cham
`err|accept` chi tren hang ma `a*` nam trong CA HAI khong gian, hoac dung
mot metric bat bien voi viec doi tap nhan.

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
  · "Tren cell poisson@0.925, mot trong bon duong (`P2`) khong bao gio la
     hanh dong toi uu tren tap hieu chinh (499798 hang), va twin khong bao
     gio de xuat no -- xac suat that <= 6.0e-06 (quy tac ba)."
  · "Bo duong do thu ve +3.95% acceptance, nhung phan ra hai kenh cho thay
     100.4% cua muc do dat den tu viec noi ngan sach Bonferroni tu alpha/3
     len alpha/2. Dong gop cua chinh viec don khong gian hanh dong la
     -0.03%, tuc AM."
  · "Ti so q_hat giua hai cau hinh (0.9233) khop du doan half-normal
     (0.9210) trong 0.24%."

KHONG DUOC PHEP:
  · "Bo mot hanh dong khong bao gio toi uu thu ve X% acceptance ma khong mat
     bao dam nao."  <- doi chung am KHONG chong duoc cau nay (`G23-300` FAIL)
  · "twin khong bao gio de xuat P2."  <- phai dung chan 6.0e-06 (`A074` N2)
  · "K = 2 la mot cau hinh de xuat."  <- hong tang 2(a) (`A074` N5)
  · Bat ky cau nao dua tren `err|accept` so sanh giua hai khong gian hanh
    dong khac nhau.  <- `L131`
```

## 8. Ngan sach

```text
Da tieu   : 24 / 35 tuan (MASTER_PLAN_v8 PART II)
Con lai   : 5 lesson (23.25..23.29) + Phase 24 + Phase 25
Gate lesson nay: 4 / 4  (`A071` R1 -- dung ngan sach, khong mo them)
```

Gioi han moi sinh trong lesson nay: `L130` (truc cua `prepare()`), `L131`
(`err|accept` khong so sanh duoc giua hai khong gian hanh dong). Ca hai vao
`BACKLOG.md`, khong mo nhanh trong lesson nay (`A071` R2).

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
