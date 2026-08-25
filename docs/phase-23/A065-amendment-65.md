# AMENDMENT 23-65 -- Sua nguong dung luong cua V-S, va tach bach M-186

Ngay ky : 2026-08-25
Lesson  : 23.22 (Task A0 sua loi + Task A mo rong)
Loai    : SUA LOI CODE + TIEN DANG KY MOT PHEP DO MOI + HAI HAU KIEM
Moc     : sau `eefd34a`, truoc lan chay lai `taxonomy_audit`

## 0. Disclosure -- ba muc do khac nhau, KHONG duoc tron

```text
[SUA LOI]  L91 la mot LOI CODE, khong phai mot ket qua. Sua no khong doi mot
           du doan da cham nao: ca ba cell bi anh huong deu la ROBUSTNESS.

[KY THAT]  M-188 chua duoc do bao gio; ham `m186_prime` chua ton tai. Day la
           du doan MU va DUOC cham diem.

[HAU KIEM] M-189 va M-190 duoc soan SAU khi xem `taxonomy_audit.json`. Ca hai
           mang nhan POST-HOC, KHONG duoc cham diem, va KHONG duoc dung de lat
           `G23-234` (van FAIL). Chung ton tai de: M-189 lam regression
           control cho lan chay lai; M-190 tro thanh du doan tien dang ky cho
           Task B.
```

Cac so DA XEM khi soan amendment nay (khai de khong dem hai lan):

```text
thu tu V-N >= V-M >= V-S tren 8 cell A=True     8/8 va 8/8
khoang cach V-N - V-S tren 8 cell A=True        duong 8/8, min +0.0128,
                                                trung vi +0.0286, max +0.0462
Spearman(spread_m, V-N - V-S) tren 8 cell       +0.833
                              tren ca 12 cell   -0.014
spread_m theo cap rho khop, h2 vs poisson       h2 lon hon 4/4 cap
trang thai hoi tu cua V-S tai kappa=1           6/12 suy bien, 3/12 qhat=inf
```

## 1. L91 -- nguong dung luong cua V-S dung SAI hang so

`cert/config_matrix.py:253`, nhanh `post == "selective"`:

```python
if min(nb.get(k, 0) for k in cells) < 9:
```

`9` la nguong dung luong cua `alpha = 0.10`. Nhung `fit_config` o day chay
`simultaneous=True, multiplicity="bonferroni"`, nen muc that la
`alpha_each = alpha/3 = 0.033333...`.

Do lai bang chinh `conformal_level`:

```text
alpha   = 0.10     ->  n_eff toi thieu =  9
alpha/3 = 0.03333  ->  n_eff toi thieu = 29
```

> Ban review noi nguong la **30**. Do lai bang `conformal_level` cho **29**.
> Chenh mot don vi khong doi ket luan (9 << 29), nhung amendment nay dung so
> DO DUOC, va code TINH no chu khong ghi hang so nao ca.

O co 9..28 block lot qua chot chan; `conformal_level` tra `None`; `_qhat` tra
`+inf`; vong lap di tiep MOT NHIP voi mot nguong vo han truoc khi chot chan
kip bat o vong sau.

Hau qua DO DUOC trong `results/LIVE/phase-23/taxonomy_audit.json`, tai
`kappa = 1`, bien the V-S:

```text
suy bien (converged=False)           6/12 cell
qhat_slot1_mean = null (tuc +inf)    3/12 cell
    poisson@0.875 (acc 0.0449)
    poisson@0.960 (acc 0.0949)
    h2@0.650      (acc 0.1196)      -- CA BA la ROBUSTNESS
```

`json_clean` bien gia tri khong huu han thanh `null`. Mot `qhat_slot1_mean`
bang `null` nghia la co it nhat mot `z_bin` nhan `qhat = +inf`, tuc o do
KHONG CHAP NHAN GI. "V-S giu bao phu" o nhung cell do mot phan kiem duoc bang
cach TU CHOI HANH DONG -- dung benh ma FCR mac o Lesson 22.4.

`cert/selective_conformal.py:277` co cung hang so `min_blocks = 9`. **O do no
DUNG**: module Phase 22 cham tren `s_margin` don le voi `alpha = 0.10`. Loi
phat sinh khi ban dong thoi tai su dung nguyen con so cho `alpha/3`.

> **Bai hoc:** mot nguong SUY RA tu tham so khac khong bao gio duoc hard-code.
> `9` dung cho mot muc va sai cho muc kia, va khong co gi trong code noi cho
> nguoi doc biet ho dang o muc nao.

### 1.1. Pham vi anh huong -- khai TRUOC khi chay

```text
KHONG DOI : census, spread, mhat_concentration   (dung nhanh `mondrian`)
KHONG DOI : moi khoa CU cua bootstrap             (goi `CM._qhat` truc tiep)
KHONG DOI : moi hang V-M va V-N cua variant_sweep
KHONG DOI : M-181 .. M-186, va M-187 tren 3 cell MAIN
CO THE DOI: hang V-S cua variant_sweep, o 6/12 cell suy bien
```

Neu mot muc trong danh sach "KHONG DOI" thay doi -> **G23-242 FAIL va DUNG
dong lesson**. Do se la bang chung rang phep sua da cham vao thu khac.

## 2. M-188 -- phep do tach bach thay cho M-186   [KY THAT]

`M-186` do be rong CI cua **trung binh `qhat` TREN CAC O**. `L90` ghi HAI hien
vat. Thuc ra co **BA**:

```text
(a) quy luat co gian phuong sai cua qhat    <- thu ta MUON do
(b) so o duoc lay trung binh (16 vs 4)      <- hien vat
(c) tuong quan cheo o qua block dung chung  <- hien vat
    (block_touch_ratio 0.873..0.915: moi o cham ~457/500 block)
```

Tinh ra, neu sai so cac o DOC LAP:

```text
phuong sai ~ 1/so HANG  : Var(T_M) = 4v/16 = v/4 = Var(T_F)   -> ti so 1.00
phuong sai ~ 1/so BLOCK : Var(T_M) = 1.093v/16, Var(T_F)=v/4  -> ti so 1.91
```

Hai hieu ung (a) va (b) TRIET TIEU nhau gan het duoi mo hinh HANG. Do duoc
1.0015..1.0639. Nhung (c) keo ti so xuong, nen mot the gioi BLOCK co tuong
quan cheo o manh CUNG cho ~1.0. **Ba an, mot phuong trinh -- khong dinh danh
duoc.**

### 2.1. Bo han viec lay trung binh

Hoi dung cau ma trien khai quan tam: *mot hang o o `(z, m)` nhan con so `qhat`
nao, va con so DO on dinh den dau?*

```text
Duoi V-M     : hang (z,m) nhan  qhat_mondrian(z,m)   31 237 hang / 457.5 block
Duoi V-N/V-S : hang (z,m) nhan  qhat_flat(z)        124 950 hang / 500.0 block

M-188 = width95[ qhat_flat(z) ] / width95[ qhat_mondrian(z,m) ]
        tinh cho TUNG cap (z,m), roi lay trung binh 16 ti so.
```

Khong lay trung binh tren o -> (b) bien mat. Khong gop o -> (c) khong ap dung.

### 2.2. Du doan va quy tac doc -- KY TRUOC

```text
M-188 du doan:  [0.45, 1.00]

do tren poisson@0.925:
    HANG chi phoi  :  sqrt(31237/124950) = 0.500
    BLOCK chi phoi :  sqrt(457.5/500.0)  = 0.957
```

Quy tac doc, ky truoc, KHONG duoc doi sau khi xem:

```text
M-188 <= 0.70        HANG chi phoi. 4x hang mua duoc ~2x do on dinh.
                     H-B DUNG o tang MUC conformal nhung SAI o tang UOC LUONG.
                     ==> bo truc m_hat CO loi ich co mau that, chi la no khong
                         nam o cho ban ke hoach noi.

M-188 >= 0.88        BLOCK chi phoi. Tuong quan noi block gan hoan toan.
                     H-B dung o CA HAI tang. Bo truc m_hat khong mua duoc gi ve
                     co mau; loi ich duy nhat la doi XAP XI lay LAP LUAN CHAT.

0.70 < M-188 < 0.88  Trung gian. Bao cao gia tri, KHONG ket luan nhi phan.
```

Ca ba nhanh deu cho ket qua dung duoc -- do la tieu chuan cua mot phep do tot,
va la thu `M-186` khong co.

`M-186` GIU NGUYEN trong artifact va giu nguyen MISS 0/3. KHONG duoc xoa.

## 3. M-189 -- quy tac vung song   [POST-HOC, khong cham diem]

Bon cell "V-N khong vo" o acceptance cao (0.864..0.961) chinh la bon cell ma
Lesson 23.21 DA PHAN LOAI bang tieu chi `A_err_neo_ge_0_05` (amendment 23-62):

```text
poisson@0.700, h2@0.850, h2@0.925, h2@0.960   ->  A = False
```

### 3.1. Doi chung nhat quan mien phi

`anchor_err` cua `taxonomy_audit` (do tren `U3`) va `err_neo` cua
`live_region_sweep_slaB` (do tren `U0`) la CUNG MOT dai luong, tinh boi hai
script doc lap. Do duoc tren ca 12 cell:

```text
max |anchor_err - err_neo| = 0.000e+00     -- trung den chu so cuoi
vd h2@0.700: 0.154525642539379 o CA HAI artifact
```

Ghi lam `G23-243`.

### 3.2. Co che -- va no XAC NHAN H-A chu khong bac bo

```text
err_neo ~ 0  ->  twin gan nhu khong bao gio sai
             ->  bai toan quyet dinh TAM THUONG
             ->  gate chap nhan 86..96%
             ->  tap ACCEPT ~ TOAN BO dan so
             ->  KHONG CO chon loc
             ->  KHONG THE co thien lech hau chon loc
```

Bon cell do la **doi chung AM** cua H-A, khong phai phan vi du. Chung cho ket
qua DUNG nhu H-A du doan cho mot the gioi khong co chon loc.

### 3.3. Quy tac -- ap tieu chi DA KY, khong dat nguong moi

> Moi phep cham lien quan den thien lech hau chon loc chi tinh tren cell co
> `err_neo >= 0.05` (tieu chi A, amendment 23-62). Cell `A = False` duoc BAO
> CAO nhu doi chung am, khong dem vao mau so.

**CANH BAO -- KHONG duoc loc bang cot `regime`.** `regime` tron HAI cau hoi:

```text
tieu chi A (err_neo >= 0.05)  "twin CO sai bao gio khong?"          <- can cai nay
S_pivotal                     "gate co xoay chuyen quyet dinh khong?" <- cau KHAC
regime = LIVE                 A ^ S_pivotal                          <- tron ca hai
```

Do duoc: `poisson@0.925` (`regime = COLLAPSED`, `err_neo = 0.2388`) va
`poisson@0.960` (`COLLAPSED`, `0.2161`). Ca hai PHAI nam trong mau, va cai dau
la cell MAIN. Loc bang `regime` se mat ca hai.

### 3.4. Du doan (POST-HOC, chi lam regression control)

```text
M-189  tren 8 cell co A = True, `V-N - V-S > 0` o >= 7/8
       (DA XEM: 8/8, min +0.0128, trung vi +0.0286, max +0.0462)
```

Muc dich: neu lan chay lai lam con so nay tut, do la dau hieu phep sua da pha
mot thu khac. No la CAI CHAN, khong phai bang chung.

### 3.5. Vi sao dung tieu chi A chu khong dung `DEGENERATE_ERR = 0.02`

`cert/config_matrix.py:49` co `DEGENERATE_ERR = 0.02`, va no cho ra DUNG bon
cell nhu tieu chi A (khoang cach qua lon: 0.0042 so voi 0.1545, nen nguong
0.02 hay 0.05 khong doi ket qua -- viec chon nguong KHONG do du lieu dat).

Nhung `DEGENERATE_ERR` la hang so NOI BO cua `evaluate_H7` cho mot muc dich
khac, con `A_err_neo_ge_0_05` la tieu chi DA KY trong amendment 23-62 va da
nam trong mot artifact LIVE. Dung cai da ky thi M-189 khong dat ra mot nguong
moi -- no AP LAI mot dinh nghia da ton tai. Do la dang manh hon.

## 4. M-190 -- hieu ung ho tai, chuyen thanh du doan cho Task B   [POST-HOC]

DA XEM. Thiet ke CAP theo `rho_bar` khop (khu hoan toan anh huong muc tai):

```text
rho_bar    poisson       h2      chenh
0.700       1.0704   1.2007    +0.1302
0.850       1.0286   1.1618    +0.1332
0.925       1.1149   1.2109    +0.0960
0.960       1.0636   1.1182    +0.0546
                     h2 > poisson  4/4 cap, khong ngoai le
```

Co che de xuat: `h2` la hyperexponential -- duoi nang, phuong sai lon hon o
cung ky vong. Duoi nang lam gian phan phoi cua `s` khi `m_hat` lon, tuc TANG
ghep noi `m_hat`--`s`.

### 4.1. KHONG xay cell moi de cham M-190 trong lesson nay

Ly do khai ro, da kiem:

```text
truth_table.parquet CO luoi rho buoc 0.02 (0.50..1.04) cho ca hai ho, nen
0.760 va 0.800 CO so do mang. (0.750 KHONG co -- luoi la 0.50, 0.52, ...)

NHUNG manifest SLA dang dung co rho_bar_grid = [0.70, 0.85, 0.925, 0.96].
=> phai sinh manifest 18 cell -> muc moi trong axis_registry.json
-> amendment rieng -> test_no_stale_axes doi cap nhat approved_for_live.

Do la MOT LESSON CON, khong phai mot muc cua amendment nay.
```

### 4.2. Thay vao do -- du doan cho Task B, do tren dung 12 cell da co

```text
M-190  Trong ma tran chuyen giao, thiet hai khi hieu chuan tren ho A va trien
       khai tren ho B BAT DOI XUNG theo huong:
           poisson -> h2   thiet hai LON HON   h2 -> poisson
       vi qhat hieu chuan tren poisson (spread_m thap) khong du rong cho duoi
       nang cua h2, trong khi chieu nguoc lai la bao thu.
       Cham o Task B. Nhan [TIEN DANG KY cho Task B].
```

## 5. L92 -- ho tai va muc tai BI RANG BUOC trong tap cell song

Tam cell co `A = True` phan bo:

```text
h2      : 0.650, 0.675, 0.700                 (rho THAP)
poisson : 0.850, 0.875, 0.900, 0.925, 0.960   (rho CAO)
```

**Khong mot gia tri `rho_bar` nao co CA HAI ho cung song.** Do la mot su that
ve he thong -- vung song nam o `rho_bar` khac nhau cho hai qua trinh den --
chu khong phai loi thiet ke. Nhung hau qua la:

> Mot ma tran chuyen giao `poisson <-> h2` tren tap cell song NHAT THIET cung
> la mot chuyen giao `rho cao <-> rho thap`. KHONG TACH DUOC hai hieu ung bang
> du lieu hien co.

```text
Phat bieu DUOC PHEP    : "chuyen giao qua CHE DO VAN HANH, noi ho tai va muc
                          tai bien thien cung nhau nhu chung bien thien trong
                          vat ly cua he"
Phat bieu KHONG DUOC   : "chuyen giao qua HO TAI"
```

Go bo can 4 cell moi tai `rho_bar` in {0.760, 0.800} -- tuc muc 4.1 tren.
Ghi lai lam viec ngo.

## 6. Gate

| Gate | Noi dung | Nguong |
|---|---|---|
| G23-239 | M-188 trong dai [0.45, 1.00], va nhanh doc duoc ap dung dung theo muc 2.2 | 3/3 cell MAIN |
| G23-240 | Sau khi sua L91: KHONG con `qhat_has_infinite = true` o bat ky cell nao tai `kappa <= 1` | 12/12 |
| G23-241 | So cell V-S suy bien tai `kappa = 1` duoc BAO CAO truoc va sau khi sua, khong lam tron | tat/bat |
| G23-242 | Bit-exact: `census`, `spread`, `mhat_concentration`, moi khoa CU cua `bootstrap`, va moi hang V-M/V-N cua `variant_sweep` trung khop tuyet doi voi `eefd34a` | 12/12 |
| G23-243 | `anchor_err` cua `taxonomy_audit` == `err_neo` cua `live_region_sweep_slaB` den 1e-12 | 12/12 |
| G23-244 | M-189 (regression control) >= 7/8 tren cell co `A = True` | tat/bat, khong diem |

## 7. Nhanh fail da dinh truoc

```text
G23-242 FAIL  -> phep sua da cham vao thu khac. DUNG NGAY, khong debug tiep
                 tren artifact moi. Revert, tim nguyen nhan tren ban cu.

G23-240 FAIL  -> con qhat vo han sau khi sua. Nghia la nguon INF khong phai
                 (chi) tu chot chan selective. Mo mot kiem toan rieng cho
                 `_qhat`; KHONG di tiep sang Task B.

M-188 > 1.00  -> taxonomy 4 o cho qhat KEM on dinh hon o TUNG o. Dieu do bat
                 kha thi duoi ca hai mo hinh, nen phai coi la LOI PHEP DO chu
                 khong phai ket qua. Kiem tra phep ghep cap (z,m) <-> (z) truoc.

M-188 trong [0.45,1.00] nhung ngoai ba nhanh doc -> bao cao gia tri, KHONG
                 ket luan. Khong duoc doi dai.

Toi da HAI vong. Moi vong sua dung mot thu.
```

## 8. Cai KHONG lam trong amendment nay

```text
- KHONG lat G23-234. No van FAIL. M-189 la POST-HOC.
- KHONG sua L90. Bo sung ve (c) vao dinh nghia, giu nguyen ket luan.
- KHONG xoa M-186 khoi artifact. No giu nguyen MISS 0/3.
- KHONG xay cell moi (muc 4.1).
- KHONG sua `selective_conformal.py:277` -- o do hang so `9` DUNG.
```

## 9. Output

```text
code      cert/config_matrix.py   (conformal_min_blocks + co qhat_has_infinite)
          cert/taxonomy_audit.py  (m186_prime, live_region_flags, M-188/189)
tool      tools/g23_242_taxonomy_rerun_diff.py
test      test/test_phase23_taxonomy_audit.py  (bo sung)
artifact  results/LIVE/phase-23/taxonomy_audit.json          (chay lai)
          results/RAW/phase-23/g23_242_rerun_diff.json
doc       docs/phase-23/43-taxonomy-audit.md  (cap nhat SAU khi chay)
```
