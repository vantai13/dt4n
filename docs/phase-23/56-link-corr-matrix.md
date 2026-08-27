# LESSON 23.25 -- MA TRAN TUONG QUAN LINK VA TRUC `omega`

Tien dang ky : `A077-amendment-77.md` (commit `79b2143`, tag `amendment-77-signed`)
Artifact     : `results/LIVE/phase-23/link_corr_matrix.json`
Ma           : `measurements/link_corr_matrix.py`
Test         : `test/test_link_corr_matrix.py` (22 test)
Nguon        : 15 run `rho_measured_clean_*.csv`, 599 mau/run, `dt = 0.2 s`
               (da kiem sach o Lesson 23.24b, 8/8 link CLEAN)

## 0. Ket qua mot dong

```text
G23-307  M-242/243/244  PASS   5.0000 / 1.7071 / 1.9428, khop giai tich
G23-308  omega + CI     PASS   omega_hat +0.0852, b_hat +0.1097, n_eff 393
G23-309  PC-25-1        PASS   ban GOP-SAI cho +1.0492 -- doi chung FIRE
G23-310  M-248 + Var(m) PASS   phan du KHONG co cau truc
G23-311  SNR + quyet dinh PASS SNR_dec 0.3752 -> ★ D3
```

**Tam du doan co cham diem deu HIT. Quyet dinh: `D3`.**

## 1. Cau truc mua do chinh xac

`A077` muc 3: `r_lm(w) = w * k_lm` voi `k_lm = c_lm / sqrt(d_l d_m)` suy TU
topology, khong fit. Nen `w_hat` la binh phuong toi thieu QUA GOC tren 12 cap:

```text
w_hat = sum_S(r*k) / sum_S(k^2),      sum(k^2) = 5.0000
sd(w_hat) = sd(r) / sqrt(5)  ->  CAU TRUC MUA DO CHINH XAC gap 2.236 lan
```

Hai lop `k`: `k = 0.5` (4 cap bien-bien), `k = 0.70711` (8 cap bien-loi).

16 cap con lai co `k = 0` -- **doi chung am CO SAN trong chinh topology**.
Chung cho `b_hat`, tuc muc NEN chung khong den tu cau truc duong.

```text
CAN THAN: (uA,vD) va (uB,vC) KHONG phai cap NULL -- chung chung `P2`/`P3`.
Doc so do bang mat rat de sai cho nay; `test_null_pairs_are_the_right_ones`
ghim lai.
```

## 2. `G23-307` -- kiem WIRING dai so `[TAT DINH]`

| dai luong | ly thuyet | do duoc | dong nhat trong lop |
|---|---:|---:|:--:|
| `sum_S k^2` | 5.0000 | **5.0000** | -- |
| `Var(m)_{w=1}/Var(m)_{w=0}` cap KE | 1.7071 | **1.7071** | 4/4 |
| nhu tren, cap CHEO | 1.9428 | **1.9428** | 2/2 |

Nhan `[TAT DINH]`: dap an biet truoc tu topology, dung KIEM CAI DAT, KHONG
tinh la phat hien (tien le `M-193`/`M-200`).

## 3. `G23-308` -- `omega_hat`, `b_hat`, `n_eff`

```text
omega_hat              = +0.0852     dai da ky [0.00, 0.15]   HIT
omega_hat_corrected    = -0.0828     (da tru nen `b_hat`)
omega_hat_deattenuated = -0.0930     (da khu lam loang)
b_hat (16 cap NULL)    = +0.1097     dai da ky [-0.05, +0.15] HIT
CI95 block bootstrap   = [-0.0314, +0.0475]
n_eff / cap            = 393         dai da ky [30, 4000]     HIT
```

Theo cell -- `omega_hat_corrected` AM o ca nam:

| cell | `omega_hat` | `omega_corr` | `b_hat` |
|---|---:|---:|---:|
| clean@0.700 | +0.0848 | -0.0166 | +0.0662 |
| clean@0.850 | +0.0685 | -0.0747 | +0.0935 |
| clean@0.900 | +0.1147 | -0.0930 | +0.1356 |
| clean@0.925 | +0.0928 | -0.0778 | +0.1114 |
| clean@0.960 | +0.0626 | -0.1370 | +0.1304 |

**Doc:** testbed la `omega ~ 0` DUNG NHU DU BAO co che (`A077` muc 4). Sau khi
tru nen chung, tuong quan theo CAU TRUC DUONG thuc te hoi AM. `b_hat ~ +0.11`
o moi cell rieng le -- tuc mot confound common-mode THAT (8 generator chung
mot host), khong phai hien vat quy trinh.

### ⚠️ `L139` -- CI la CAN DUOI, `n_eff` la CAN TREN

```text
tau_pred_s theo link:  ac 2.64  ad 4.00  bc 2.63  bd 2.66     <- LOI
                       uA 19.33 uB 26.42 vC 19.33 vD 26.74    <- BIEN
tau_system = 27.67 s   (max qua link)
5*tau      = 669 mau   VUOT do dai run (599 mau = 119.8 s)
block THAT = 149 mau (29.8 s) = 1.08 * tau_system   <- duoi nguong 3.0
```

Do dai run chi bang ~4.3 lan `tau` cua link cham nhat. **Khong phep bootstrap
nao tao them thong tin duoc tu 119.8 giay du lieu.** Muon CI that phai chay
run dai hon (>= 5 phut) -- do la mot chien dich moi.

Ban thao de xuat `TAU_S = 3.5` (chi dung cho bon link LOI) se cho ti so 0.66
va THOI PHONG `n_eff` -- dung lop loi `L50`/`L52`.

## 4. `G23-309` -- ★ doi chung DUONG `PC-25-1` FIRE

| cach tinh | `omega_hat` | `b_hat` |
|---|---:|---:|
| DUNG: Fisher-z TRONG tung run | **+0.0852** | +0.1097 |
| SAI: noi 15 run roi `corrcoef` | **+1.0492** | +0.6103 |

Chenh **12 lan**. Ban SAI do lai chinh CAI NUM XOAY `rho_bar` da van, khong
phai tuong quan mang (ecological fallacy / pooling artifact).

Doi chung nay ton tai de chung minh phep do DU NHAY de phan biet hai cach
tinh. Neu no khong fire, moi so cua lesson nay mat gia tri -- cung hinh dang
`L101`.

## 5. `G23-310` -- `M-248` va `Var(m)`

```text
k = 0.5     n=4  mean_resid = -0.03192   |mean|/2se = 0.42
k = 0.7071  n=8  mean_resid = +0.01128   |mean|/2se = 0.16
_verdict_structured_residual = FALSE  ->  mo hinh MOT tham so DU
```

### ⚠️ Mot dinh nghia phai sua GIUA CHUNG -- `A077` muc 4b

Ban chay dau tien tinh phan du la `r - w*k`, THIEU `b_hat`. Nhung
`omega_hat_corrected` duoc suy tu `(r - b_hat)`, nen mo hinh da fit la
`r = b + w*k` va phan du DUNG la `r - b - w*k`.

```text
phan du SAI : k=0.5 -> +0.07779 (1.03) ; k=0.7071 -> +0.12099 (1.68)  TRUE
phan du DUNG: k=0.5 -> -0.03192 (0.42) ; k=0.7071 -> +0.01128 (0.16)  FALSE
```

Ban SAI day CA HAI lop len cung mot luong `b_hat = +0.1097`, lam mat dau hieu
quan trong nhat (hai lop lech NGUOC chieu). Ghi ca hai vi sua xay ra SAU khi
da nhin so lan dau.

### `Var(m)` theo TUNG cap duong -- KHONG gop (bai hoc `K4`)

| cap | `Var` do / don vi | ly thuyet tai `omega=1` | chung link |
|---|---:|---:|:--:|
| m(P1,P2) | 0.6940 | 1.7071 | co |
| m(P1,P3) | 0.7068 | 1.7071 | co |
| m(P1,P4) | 0.6506 | 1.9428 | khong |
| m(P2,P3) | 0.5417 | 1.9428 | khong |
| m(P2,P4) | 0.7013 | 1.7071 | co |
| m(P3,P4) | 0.6666 | 1.7071 | co |

Ca sau deu **DUOI 1**, tuc `Var(m)` THAP hon khi cac link doc lap. Nhat quan
voi `omega_corrected` am: theo huong bien, cac link hoi PHAN tuong quan.

`L46` ghi "`S_pivotal` do tren mo hinh rho DOC LAP la CAN TREN cua vung song".
Do duoc o day: he so la **0.54--0.71**, tuc uoc luong doc lap la can tren
KHONG CHAT, va vung song THAT rong hon -- theo huong CO LOI.

## 6. `G23-311` -- ★ `SNR_dec` va quyet dinh ngan sach

```text
SNR_dec = |E[m]| / sd(m)  tren cost `CostV2(poisson, w_loss=5000)`
          tu `rho` DO DUOC, 30 o = 5 cell x 6 cap duong

trung vi 0.3752      min 0.1115      max 0.9690
```

`SNR_dec` tang DON DIEU theo `rho_bar`:

```text
CAO   clean@0.960 | m(P1,P2)   0.9690
      clean@0.960 | m(P1,P4)   0.8572
      clean@0.960 | m(P2,P3)   0.7838
THAP  clean@0.700 | m(P1,P3)   0.1115
      clean@0.850 | m(P3,P4)   0.1152
```

### `M-251` -- du bao `err(w=1)/err(w=0)`

`omega` KHONG vao `err` truc tiep. No vao QUA `sd(m)`: o `w=1`, `Var(m)` nhan
`V`, nen `SNR(w=1) = SNR(w=0)/sqrt(V)`; `r` khong doi.

| lop cap | `V` | `SNR` 0->1 | `err` 0->1 | ti so |
|---|---:|---|---|---:|
| KE | 1.7071 | 0.3752 -> 0.2871 | 0.048336 -> 0.049769 | **1.0296** |
| CHEO | 1.9428 | 0.3752 -> 0.2692 | 0.048336 -> 0.050019 | **1.0348** |

Tham chieu: neu `E[m] = 0` thi `err = arccos(r)/pi = 0.0519` voi
`r = exp(-z/tau) = 0.98675` (`z` trung vi 0.369 s, `tau` 27.67 s) -- va con
so do BAT BIEN voi `omega`. Do la ca van de (`A077` muc 2b).

### ★ QUYET DINH `D3` -- da ky TRUOC khi do

```text
0.25 < SNR_dec (0.3752) < 1.00
-> mo Lesson 23.26 NHUNG chi tren cell co `SNR_dec` CAO NHAT (`clean@0.960`,
   SNR 0.68 .. 0.97) va GHEP voi truc `swing` (`A077` muc 2b).
-> Ngan sach cat tu 10 xuong 6 gate.
```

`G23-311` la gate DUY NHAT trong Phase 23 co dau ra la mot QUYET DINH NGAN
SACH. Rui ro quan tri (nan so ve phia nguong) duoc bit ba cach: nguong khoa
trong ma nguon truoc khi chay va co test cam bien thanh co dong lenh;
`SNR_dec` tinh tu `rho` DO DUOC; va ca ba nhanh D1/D2/D3 deu dan toi mot doan
viet duoc, nen khong nhanh nao la "that bai".

## 6b. ★ DOI NHAN theo `A078` (Lesson 23.25b) -- doc TRUOC muc tren

Ba muc duoi day cua doc nay DA BI SUA PHAM VI. Ban goc KHONG bi rut
(`NT 49`); chi doi nhan.

```text
muc 3  "CI95 = [-0.0314, +0.0475]" va moi phat bieu ve DAU cua `omega_hat`
       -> RUT. `n_eff` thuc theo cap la 32.5-44.9 (khong phai so gop 393) vi
          MOI cap co `k>0` deu chua mot link BIEN. `sd` dung = 0.0754, CI95 =
          +-0.1479 -- RONG GAP 3.8 LAN. Phat bieu dung: `|omega| <= 0.15`,
          DAU khong xac dinh duoc. Xem `L142`.
       -> Them: `omega_hat` nam NGOAI CI95 bootstrap cua chinh no (lech 3.70
          sd) -- bootstrap LECH VI TRI. Xem `L143`.

muc 5  `M-248` "phan du KHONG co cau truc" la AM TINH GIA: `goodness_of_fit`
       CHI soi 12 cap CO CAU TRUC. Tap NULL 16 cap thi KHONG dong nhat --
       fast-fast +0.0163, slow-fast +0.0527, slow-slow +0.6181. Xem `T7`.

muc 5  `Var(m)_do/don_vi = 0.54-0.71` KHONG duoc dung lam "dinh luong `L46`":
       85-111% cua no den tu DUNG HAI phan tu `r(uA,uB)`=+0.599 va
       `r(vC,vD)`=+0.638, va co che cua chung (chung DIEM CUOI) NGUOC DAU voi
       co che cua `omega` (chung DUONG). Bo hai so -> ti so ve 0.95-1.06.

KHONG DOI: quyet dinh `D3` (da kiem do ben o `G23-314`: bo hai cap ngoai lai
       thi `SNR_dec` 0.3752 -> 0.3041 va quyet dinh van la `D3`).
KHONG DOI: ket luan DINH TINH "testbed la omega ~ 0".
```

Chi tiet: `58-close-23-25b.md`.

## 7. Ba lop rang buoc PHAI in kem moi so cua lesson nay

```text
L138  `omega=1` la vat ly DA CHUAN HOA (he so `1/sqrt(d_l)` la gia cua
      rang buoc `G23-125`), khong phai vat ly thuan.
L139  CI95 la CAN DUOI cua do rong that; `n_eff = 393` la CAN TREN.
L140  `omega_hat` do o `dt = 0.2 s` la CAN TREN cua tuong quan o thang ms
      -- nen ket luan "testbed la omega ~ 0" cang VUNG.
L141  `SNR_dec` dung `mode="poisson"` CO DINH; `c_a`/`c_s` cua chien dich
      23.8 CHUA duoc do. Neu `c_a > 1.5` thi `mode="h2"` moi dung va `D3`
      co the doi.
```

## 8. Tai tao

```bash
.venv/bin/python -m pytest test/test_link_corr_matrix.py -q
.venv/bin/python -m measurements.link_corr_matrix \
    --campaign results/RAW/phase-23/aoi_v7_campaign \
    --out results/LIVE/phase-23/link_corr_matrix.json
```

Thoi gian: ~1 s. Mac dinh CHI dung `clean`: `L31` ghi PROD (delta-sync) khong
tai lap duoc (`sd(p05)` gap 5.79x). Ban PROD chay duoc bang `--csv-glob` va
phai bao cao RIENG.
