# AMENDMENT 23-77 -- LESSON 23.25: ma tran tuong quan link + truc omega

Ngay ky : 2026-08-27

Moc     : sau tag `lesson-23-24b-complete`, TRUOC khi mo mot file CSV nao
          cho muc dich TUONG QUAN

Loai    : TIEN DANG KY mot phep do + DINH CHINH mot LAP LUAN cua ban ke hoach

Commit  : `ee6056c` (tag `lesson-23-24b-complete`)

## 1. Ngan sach gate (`A071` R1)

```text
Lesson 23.25 : 5 gate  (G23-307 .. G23-311).  Vuot -> DUNG lesson.
```

Bien minh R4 -- neu KHONG lam, paper mat cau nao trong `CLAIMS.md`?

```text
Mat pham vi cua moi phat bieu bi rang buoc boi `L46`: "`S_pivotal` do tren
mo hinh rho DOC LAP theo link; tuong quan tai that se lam cac duong vi pham
DONG THOI nhieu hon -> `S_pivotal` THAT nho hon so do duoc."
Hien uoc luong vung song chi la CAN TREN. Sau lesson nay no thanh mot KHOANG
co so.  => DUOC PHEP mo.
```

## 2. ★ DINH CHINH `PHASE_23_v3.md` -- mot LAP LUAN, khong phai mot ket qua

`NT 49` cam RUT ket qua. Muc nay khong rut ket qua nao; no doi nhan mot LAP
LUAN trong ban ke hoach NGOAI repo, va ghi anh xa tai day.

### 2a. Sai dau o buoc cuoi

Ban ke hoach suy: *tuong quan duong => `m` IT doi dau => `err_neo` THAP hon.*
Buoc cuoi SAI.

Da kiem bang dai so tren chinh topology:

```text
m(P1,P3) ~ (uA - uB) + (ac - bc),   v = [uA:+1, ac:+1, uB:-1, bc:-1]

Cac cap NULL o day:  k(uA,uB) = 0   ({P1,P2} ∩ {P3,P4} = rong)
                     k(ac,bc) = 0   ({P1}   ∩ {P3}     = rong)
Cac cap CO cau truc: k(uA,ac) = 0.70711,  k(uB,bc) = 0.70711
                     he so dau: (+1)(+1) = +1 va (-1)(-1) = +1  -> CONG vao

Var(m) = 4*sigma^2 + 2*(0.70711 + 0.70711)*sigma^2 = 6.82843*sigma^2
       => ti so 1.70711  ->  Var(m) TANG theo omega, khong giam.
```

`Var` lon hon => `m` dao dong RONG hon quanh trung binh cua no => bang qua
KHONG **nhieu** hon, khong phai it hon.

### 2b. Bo sot mot nhanh -- va nhanh do quan trong hon ca sai dau

Cong thuc doi dau Sheppard (1899): voi `(X,Y)` chuan hai chieu, TRUNG BINH 0,
tuong quan `r`:

```text
P( sign(X) != sign(Y) ) = arccos(r) / pi
```

Ve phai KHONG chua `Var`. Nen khi `E[m] = 0`, `err` BAT BIEN voi thang cua
`m`, tuc BAT BIEN voi `omega`. Ban ke hoach khong co nhanh nay.

`omega` tac dong QUA ti so `SNR_dec = |E[m]| / sd(m)`, tuc TUONG TAC voi truc
`swing` cua Lesson 23.27. Hai truc do KHONG doc lap.

### 2c. Du doan duoc DAO CHIEU va BO SUNG, ky TRUOC khi do

```text
err_neo TANG theo omega, voi do lon TI LE THEO swing.
Neu SNR_dec <~ 0.25 thi hieu ung < 1% va Lesson 23.26 KHONG duoc mo duoi
dang chien dich Mininet 3 tuan.
```

## 3. Mo hinh omega duoc khoa cho ca 23.25 va 23.26

```text
rho_l = mu_l + sigma * [ sqrt(w) * (sum_p M[l,p] f_p) / sqrt(d_l)
                       + sqrt(1-w) * g_l ]

f_p ~ N(0,1) doc lap  (nhan to tai theo DUONG, p = P1..P4)
g_l ~ N(0,1) doc lap  (nhieu rieng cua link)
M   = incidence matrix duong-link, tu `T7.PATHS`
d_l = so duong dung link l  (uA,uB,vC,vD: 2 ; ac,ad,bc,bd: 1)
```

Ba tinh chat, deu kiem duoc bang test:

```text
(i)   Var(rho_l) = sigma^2 voi MOI link va MOI w  -> `G23-125` thoa TU DONG
(ii)  w = TI LE PHUONG SAI den tu nhan to duong   -> doc duoc ve vat ly
(iii) r_lm(w) = w * k_lm,  k_lm = c_lm / sqrt(d_l d_m)
      TUYEN TINH theo w, he so goc BIET TRUOC tu topology.
```

He so `1/sqrt(d_l)` la CAI GIA cua rang buoc (i). Ghi thanh `L138`.

## 4. Du doan

Nhan `[TAT DINH]` = dap an biet truoc tu topology, dung KIEM WIRING, ha cap
theo tien le `M-193`/`M-200`, KHONG tinh la phat hien.

| ID | Dai luong | Nguon | Dai khoa | Do | KQ |
|---|---|---|---|---|---|
| M-242 | `sum_S k^2` tren 12 cap co cau truc | [TAT DINH] | = 5.0000 | ___ | ___ |
| M-243 | `Var(m)_{w=1} / Var(m)_{w=0}`, cap KE | [TAT DINH] | = 1.7071 | ___ | ___ |
| M-244 | nhu tren, cap CHEO (P1,P4)/(P2,P3) | [TAT DINH] | = 1.9428 | ___ | ___ |
| M-245 ★ | `w_hat` TRONG-run, gop Fisher-z, 15 run CLEAN | [NGOAI SUY] | 0.00 - 0.15 | ___ | ___ |
| M-246 ★ | `b_hat` = trung binh r tren 16 cap NULL | [NGOAI SUY] | -0.05 - +0.15 | ___ | ___ |
| M-247 | `n_eff` moi cap, block bootstrap | [NGOAI SUY] | 30 - 4000 | ___ | ___ |
| M-248 ★ | phan du fit mot-tham-so co CAU TRUC? | [CO CHE] | KHONG | ___ | ___ |
| M-249 ★ | `w_hat` tinh theo cach GOP-SAI | [CO CHE] | >= 1.00 | ___ | ___ |
| M-250 ★ | `SNR_dec` trung vi qua (cell x cap duong) | [MO TA] | bao cao | ___ | ___ |
| M-251 ★ | `err(w=1)/err(w=0)` DU BAO tu M-250 | [CO CHE] | bao cao | ___ | ___ |

Co so cua `M-245`/`M-246`: `traffic_v7.LOAD_CHANNELS` nap moi link bang MOT
luong MOT-CHANG rieng (`uA`: hsrc->hA; `ac`: hA->hC). Byte vao `uA` KHONG chay
tiep sang `ac`. Nen testbed la `omega ~ 0` THEO THIET KE, o ca tang twin lan
tang Mininet. Neu `w_hat` ra NGOAI dai -> co mot nguon tuong quan CHUA BIET
-> phat hien, phai truy, KHONG duoc lam phang.

`M-248` kiem cu the: tach phan du `r_do - w_hat * k` theo HAI LOP `k`
(`k = 0.5` voi 4 cap, `k = 0.70711` voi 8 cap). Neu `|mean_resid| > 2*se` o it
nhat mot lop -> mo hinh mot-tham-so KHONG du.

## 5. ★ Quy trinh BAT BUOC -- chong pooling artifact

15 run CLEAN trai tren `rho_bar` in {0.700, 0.850, 0.900, 0.925, 0.960}. Neu
noi 15 file roi goi `np.corrcoef`, tam cot cung len cung xuong theo NHOM RUN,
cho `r` lon o MOI cap, va `w_hat > 1`. Do la do lai chinh CAI NUM XOAY da van,
khong phai do tuong quan mang (ecological fallacy / pooling artifact).

```text
(1) tinh tuong quan TRONG TUNG RUN -> 15 ma tran 8x8
(2) gop bang bien doi Fisher z = artanh(r), trung binh z, doi nguoc
(3) bao cao THEO CELL truoc, roi moi gop
(4) tinh LUON ban GOP-SAI va in canh ben  -> `M-249`, doi chung DUONG
```

## 6. ★ HAI HANG SO CUA BAN KE HOACH BI BAC BO -- do tu `meta_*.json`

Ban thao de xuat `TAU_S = 3.5` "tu `meta::profile.tau_pred_s` (2.82..4.28)".
Da do tren ca 30 `meta_*.json` (TRACKED, khong dung CSV):

```text
tau_pred_s : min 2.1583   max 30.2374   median 9.7642   mean 12.9704

trung binh theo link:
    ac 2.6448   ad 4.0019   bc 2.6333   bd 2.6564      <- LOI
    uA 19.3335  uB 26.4196  vC 19.3335  vD 26.7404     <- BIEN, gap ~7 lan
```

Dai "2.82..4.28" chi dung cho bon link LOI. Link BIEN co `tau` gap bay lan.

### 6a. Hau qua: block bootstrap voi `TAU_S = 3.5` se NOI DOI

```text
block = 5*tau/dt,  dt = 0.2 s,  do dai run = 599 mau = 119.8 s

tau = 3.50 s (ban thao)  -> block  88 mau (17.6 s)   6 block/run
tau = 26.74 s (uB, vD)   -> block 669 mau (133.8 s)  VUOT do dai run
```

Voi block 17.6 s, tu tuong quan cua link BIEN (`tau ~ 27 s`) CHUA bi pha, nen
bootstrap coi cac mau con tuong quan la doc lap -> SE qua hep -> CI qua hep ->
`n_eff` bi THOI PHONG. Dung lop loi ma `L50`/`L52` da ghi ("khong duoc gia
dinh iid").

### 6b. Quy tac da ky, thay cho mot hang so

```text
TAU_BY_LINK  doc tu `meta_*.json`, trung vi qua 30 run, THEO TUNG LINK.
TAU_SYSTEM   = max qua 8 link  (block phai du dai cho link CHAM NHAT)
BLOCK_TARGET = ceil(BLOCK_TAU_MULT * TAU_SYSTEM / dt),  BLOCK_TAU_MULT = 5.0
BLOCK_LEN    = min(BLOCK_TARGET, n_run // MIN_BLOCKS_PER_RUN),
               MIN_BLOCKS_PER_RUN = 4

Artifact PHAI in `block_len_over_tau_system`. Neu ti so < 3.0 thi CI la mot
CAN DUOI cua do rong that, va `n_eff` la mot CAN TREN. Ghi `L139`.
```

Do la mot gioi han DA BIET TRUOC, khong phai mot ket qua xau. Do dai run
(119.8 s) chi bang ~4.5 lan `tau` cua link bien; khong phep bootstrap nao tao
them thong tin duoc.

## 7. Doi chung

```text
NC-25-1   chay hai lan cung seed -> ket qua giong bit-for-bit
          (tru `provenance.timestamp_utc`)
NC-25-2   sinh du lieu tong hop voi w DA BIET (0.00 / 0.35 / 0.75)
          -> `w_hat` phai hoi phuc trong +-0.05
NC-25-3   du lieu tong hop w = 0, KHONG confound -> `b_hat` in [-0.03, +0.03]

PC-25-1 ★ ban GOP-SAI -> `w_hat` >= 1.00 VA `b_hat` >= 0.50
          Muc dich: chung minh phep do DU NHAY de phan biet hai cach tinh.
          Neu KHONG fire -> moi so khac cua lesson nay mat gia tri (`L101`).
PC-25-2   bom confound common-mode nhan tao (cong mot chuoi AR(1) chung vao
          ca 8 link) -> `b_hat` PHAI tang, `w_hat_corrected` PHAI giu nguyen
```

## 8. Gate

| ma | noi dung | nguong |
|---|---|---|
| G23-307 | `M-242/243/244` kiem wiring dai so khop giai tich | = ly thuyet |
| G23-308 ★ | `w_hat` + `b_hat` + `w_hat_corr` co CI block bootstrap | bat buoc |
| G23-309 ★ | `PC-25-1`: ban GOP-SAI fire (`w_hat >= 1.00`) | nhi phan |
| G23-310 | `M-248` phan du khong co cau truc; `Var(m)` theo TUNG cap | bat buoc |
| G23-311 ★ | `SNR_dec` do duoc + quyet dinh GO/NO-GO 23.26 CO SO | nhi phan |

## 9. ★ Tieu chi quyet dinh cho Lesson 23.26 -- KY TRUOC KHI DO

Ban ke hoach viet hai nhanh ma CA HAI deu dan toi "23.26 BAT BUOC". Do khong
phai mot quyet dinh (`A071` R4). Thay bang tieu chi do duoc o chinh lesson nay:

```text
SNR_dec = |E[m]| / sd(m), tinh tren cost `CostV2(mode="poisson", w_loss=5000)`
tu `rho` DO DUOC, cho tung cap duong va tung cell.

D1  SNR_dec (trung vi) <= 0.25
    -> du bao err(w=1)/err(w=0) <= 1.01
    -> KHONG mo 23.26 duoi dang chien dich Mininet.
       Thay bang: quet omega trong TWIN (~1 gio may), cong bo tinh BAT BIEN
       nhu mot ket qua CO CHUNG MINH (Sheppard), + mot `L*` ghi pham vi.

D2  SNR_dec (trung vi) >= 1.00
    -> du bao err(w=1)/err(w=0) >= 1.24
    -> 23.26 DANG mo. Ngan sach 10 gate nhu `A071` R1 da cap.

D3  0.25 < SNR_dec < 1.00
    -> mo 23.26 NHUNG chi tren cell co SNR_dec CAO NHAT, va ghep voi truc
       swing (muc 2b). Ngan sach cat con 6 gate.
```

Khong kich ban nao duoc dien giai lai sau khi nhin so.

RUI RO QUAN TRI cua mot gate co dau ra la NGAN SACH: no tao dong co ngam cho
viec "muon mo 23.26" hoac "muon khoi mo 23.26" nan con so ve phia nguong.
Bit bang ba cach: (a) nguong `0.25`/`1.00` khoa TRONG MA NGUON truoc khi chay
va co test cam bien chung thanh co dong lenh; (b) `SNR_dec` tinh tu `rho` DO
DUOC, khong tu tham so nao chon duoc; (c) ca ba nhanh D1/D2/D3 deu dan toi
mot doan viet duoc, nen khong nhanh nao la "that bai".

## 10. Sua ma nguon duoc phep

```text
(a) `measurements/link_corr_matrix.py`   -- MOI
(b) `test/test_link_corr_matrix.py`      -- MOI
KHONG sua: `sla_calib_v2.ar1_matrix` (truc omega thuoc 23.26),
           `twin/cost_v2.py`, `twin/topology_v7.py`.
```

## 11. Pham vi va gioi han

```text
N1  Chi dung `rho_measured_clean_*.csv`. `L31`: PROD (delta-sync) khong tai
    lap duoc (`sd(p05)` gap 5.79x CLEAN). Tron PROD se them phuong sai khong
    kiem soat vao `R`. Ban PROD co the chay rieng va bao cao rieng.

N2  CSV lay mau o `dt = 0.2 s`, tuc moi gia tri DA la trung binh thong luong
    tren cua so 200 ms; twin sinh `rho(t)` o `dt = 0.005 s`. Lam muot thuong
    LAM TANG tuong quan. `w_hat` do duoc la mot CAN TREN o thang mili-giay.
    Ghi `L140`.

N3  `SNR_dec` do tren `rho` DO DUOC nhung cost tinh qua `CostV2` voi
    `mode="poisson"` CO DINH. Chien dich 23.8 dung `traffic_v7` (Poisson den
    + Pareto co, kappa = 2.5) nen `mode` la mot ANH XA hop ly, KHONG phai mot
    phep do `c_a`/`c_s` cua chinh chien dich. Ghi `L141`.

N4  Nguong quyet dinh la HANG SO MODULE, khong phai co dong lenh (muc 9).
```
