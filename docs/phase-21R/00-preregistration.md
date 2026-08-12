# PRE-REGISTRATION -- Phase 21R
# Conformal theo tuoi tren so do day + phan ra sai so (RQ-B)

Ngay ky : 2026-08-12
Nguoi ky: Codex theo yeu cau owner repo DT4N
Tag du kien: phase-21R-start

Tien de: Phase 20R PASS tai tag `phase-20R-complete`.

Tai lieu bat buoc doc kem:

```text
docs/phase-21R/01-inherited-audit.md
docs/phase-21/99-erratum.md
```

## Cau hoi cua phase

Phase 20R da cho thay twin co the sai quyet dinh o `poisson@0.925`, tai `z`
cao. Phase 21R hoi:

```text
Neu biet tuoi cua du lieu telemetry, co the dat mot certificate conformal vua
bao phu dung, vua huu ich cho quyet dinh routing hay khong?
```

Ket qua chinh khong phai mot `q_hat` don le. Ket qua chinh la duong
risk-coverage theo tuoi, kem phan ra `e_model` va `e_stale`.

## Input da khoa (sha256)

Tat ca script 21R phai doi chieu cac file nay truoc khi chay. Neu lech hash,
dung lai va dieu tra; khong duoc tiep tuc voi artifact im lang thay doi.

| File | sha256 |
|---|---|
| `results/phase-20R/truth_table.parquet` | `5260b8f8aabb59ca81e2af1168bbbc98a7dfd804aa0506a266d0b34fac5d927e` |
| `results/phase-20R/sla_calibration.json` | `0387d300dbdd039c004a7fc89d062a0e9219968be8ad0cfeac65e53cf34826db` |
| `results/phase-20R/decision_error_by_age_by_regime.parquet` | `5e4d4797a5b5471a93a0eb8898555fd4e682ea33a5356e4b11253deff962596f` |
| `results/phase-20R/decision_error_constant_sigma.parquet` | `cdc8263c7a69f7a4ad0e42363f3d88ce1278d828391c7315b7856db6ca8723e2` |
| `results/phase-20R/decision_error_sawtooth.json` | `96d59d8b8cb9c2d95fddef151d4370298621e047e70ade46bd1645f76f7ad4d8` |
| `results/phase-L/link_model_v2_fit.json` | `ab17908c40359572e35effdee561f8217477168ba77298831a734ab47cc9563b` |
| `twin/link_model_v2.py` | `17011990fa50c7d0c7155831cce475513684022c20b551440acead00ed1ef2a1` |
| `twin/cost_v2.py` | `ba591392e19ab6a10e10d6a45ec4782e83cb6516e2e616e54f744913ffd3bfab` |
| `twin/topology_v7.py` | `c8263ce17feffdd17031dbcb3694880a4f649c6870068ce7a1f6631ec859076a` |
| `measurements/decision_error_v2.py` | `ff16f35cd1536d71f5d9f7c3d8b94052cd7db45cbff3a22e53ce22e57adc4533` |
| `measurements/sla_calib_v2.py` | `7d8f5f50285a3de4ce20155648f24b91e4ee9287f3aa54ad0c07cd1aa0c46f3b` |

## Ke thua tu 20R -- khong hieu chuan lai

```text
w_loss, T_delay, T_loss : theo tung o, tu sla_calibration.json
                          poisson@0.925 -> 3222.2447 / 32.2224 ms / 0.0292
b_block                 : 5 * tau = 5.0 s = 1000 mau
tau                     : 1.0 s
dt                      : 0.005 s
sigma_rho               : 0.0096 co dinh moi o
AoI rang cua            : sync_period = 0.5 s, d_sync = 0.051 s
                          z thuc nhan in [0.055, 0.550], 100 muc deu
is_reliable             : cbr and 0.95 < rho < 1.05 -> loai
```

`sigma_rho = 0.0096` la sigma cua o chat nhat (`poisson@0.960`), de moi o deu
kha thi va de cat confound sigma-rho da cong bo o Phase 20R.

## Muoi quyet dinh -- chot, khong sua sau khi thay ket qua

### P1. Dai luong du doan

```text
y_true(a,t) = TruthTable.path_tables(mode, rho(t), w_loss)[2][a]
y_hat(a,t)  = CostV2.tables_batch(rho(t-z), mode, w_loss)[2][a]
cost        = delay + w_loss * loss
```

`y_true` noi suy TUYEN TINH tren luoi truth table 20R buoc 0.02, clip o bien,
va phai log ti le clip. Bat buoc tai su dung:

```text
measurements/decision_error_v2.py::TruthTable
measurements/decision_error_v2.py::rho_matrix_from_cell
```

Khong viet lai logic noi suy; viet lai la mo lai mot bac tu do da dong o 20R.

### P2. Diem bat tuan chinh

Score chinh:

```text
s_margin(t) =
  | (y_true(a2,t) - y_true(a1,t)) - (y_hat(a2,t) - y_hat(a1,t)) |

a1 = argmin_a y_hat(a,t)
a2 = argmin_{a != a1} y_hat(a,t)
```

`a1` va `a2` chon THEO TWIN. Chon theo su that la ro ri va lam mat bao dam.
Guard bat buoc: test ham chon cap khong nhan `y_true` lam tham so.

Giai thich da khoa theo audit:

```text
v7 dung s_vs_a1 = max_a |e_a - e_a1|, da la score vi sai.
s_margin khong phai sua loi common-mode; no la siet chat:
lay cap duy nhat co the lat argmin.
s_margin <= s_vs_a1 luon dung.
```

Bao cao phu, khong dung de chon tieu chi chinh:

```text
s_vs_a1  -- de so truc tiep voi v7 va kiem H6
s_maxabs -- de so voi score tuyet doi
q_hat_delay va q_hat_loss*w_loss -- bat buoc tach kenh
```

### P3. Muc tin cay

```text
alpha = 0.10
coverage muc tieu = 90%
```

Tinh them:

```text
alpha/K = 0.025 voi K=4
alpha/2 = 0.050
```

Hai muc phu nay chi de kiem huong `q_hat` khi that chat alpha. Bao phu dong
thoi la viec cua Phase 22.

### P4. Che do

Chay toan bo pipeline rieng cho tung o. Che do la boi canh, khong phai nhom
Mondrian.

```text
CHINH:
  poisson @ 0.925

PHU:
  poisson @ 0.850
  poisson @ 0.700
  h2 @ 0.700
  h2 @ 0.850
  h2 @ 0.925

DOI CHUNG DUONG:
  cbr @ 0.700

LOAI:
  h2 @ 0.960
  cbr @ 0.925
  cbr @ 0.960
```

Ghi chu: `h2@0.925` co sawtooth err `0.080502`, khong nho hon `0.01`, nen van
chay va xep PHU. `h2@0.635` khong ton tai.

### P5. Bin tuoi

Ho tro thuc:

```text
z in [0.055, 0.550], 100 muc deu
```

Bin CHINH ke thua tu luoi `z` cua 20R:

| Bin | Ranh gioi | So muc | Ti le xap xi |
|---|---|---:|---:|
| B1 | `[0.055, 0.10)` | 9 | 9% |
| B2 | `[0.10, 0.20)` | 20 | 20% |
| B3 | `[0.20, 0.30)` | 20 | 20% |
| B4 | `[0.30, 0.550]` | 51 | 51% |

Bin PHU, tien dang ky truoc khi tinh score:

```text
[0.055, 0.155)
[0.155, 0.255)
[0.255, 0.355)
[0.355, 0.455)
[0.455, 0.550]
```

Bin CHINH quyet gate. Bin PHU chi la phan tich do ben da tien dang ky.

Rang buoc:

```text
n_g >= ceil(1/alpha) - 1 = 9 block moi bin
muc tieu >= 50 block moi bin
neu thieu: gop voi bin ke ben co n_g lon hon
```

### P6. Chia calib/test

```text
block_len = 1000 mau = 5.0 s = 5*tau
split     = 50/50 theo nguyen block
seed      = 7000
```

Voi moi `(block, bin)`, tinh mot so dai dien:

```text
s_rep(block, bin) = quantile_{1-alpha}(s trong phan giao block x bin)
```

Conformal chinh lay phan vi tren CAC BLOCK, khong tren tung mau. `n_g` dem theo
block.

```text
Coverage is guaranteed for exchangeable blocks of length 5*tau; within-block
dependence is not exchangeable and the guarantee is not claimed at sample
granularity.
```

Bien the de bao cao:

```text
MAIN-BLOCK : q_hat tu s_rep tren block.
LEGACY-B   : pooled samples tu cac block calib, chi de so v7/diagnostic.
A          : mot mau moi block, kiem chung do ben.
SEED-SPLIT : calib tren seed {101,102,103}, test tren {104,105}.
```

### P7. Tieu chi huu ich

Tinh ca ba, song song:

```text
C1 khoang tach roi : accept <=> gap_twin >= 2 * q_hat(z)
C2 chan tren regret: accept <=> ub_regret <= eps_regret
C3 ho tham so      : accept <=> gap_twin >= q_hat(z) - eps, quet eps
```

Ket qua chinh la duong bien risk-coverage cua C3, ve cung diem neo. Khong ket
luan huu ich bang mot diem duy nhat.

### P8. eps_regret

```text
eps_regret(o) = 0.10 * T_delay(o)
```

Vi du tu `sla_calibration.json`:

| Cell | eps_regret |
|---|---:|
| poisson@0.925 | 3.2222 ms |
| poisson@0.850 | 2.4244 ms |
| h2@0.700 | 2.8614 ms |

Con so den tu hieu chuan 20R da dong bang, khong tune tren du lieu 21R.

### P9. Nguon du lieu

```text
rho(t)    : measurements.sla_calib_v2.ar1_matrix, bit-exact
sigma     : 0.0096 co dinh
tau       : 1.0
dt        : 0.005
n         : 200000
seeds     : 101,102,103,104,105
AoI       : rang cua [0.055, 0.550]
```

Duong operational voi sigma theo tung o se bao cao rieng o Lesson 21R.8.

### P9b. Diem neo

Neo 20R khong duoc chep thang sang 21R vi thiet ke lay mau khac nhau.

```text
n=120000, z=0.55, sigma const       : err = 0.295005, d_sla = 0.098596
n=200000, z=0.55, sigma const       : err = 0.290467, d_sla = 0.092277
n=200000, rang cua, sigma van hanh  : err = 0.283220, d_sla = 0.093714
```

Quy tac: diem neo phai tinh tren dung cung thiet ke lay mau voi tap test 21R.
Lesson 21R.2 phai sinh:

```text
results/phase-21R/anchor.json
```

Thiet ke anchor moi:

```text
n=200000
AoI rang cua
sigma=0.0096
seeds=101..105
```

Du doan tien dang ky: `err_neo in [0.27, 0.31]`.

### P10. Neu fail thi sua gi

Tat ca nhanh duoi day duoc dien TRUOC khi xem ket qua 21R.

```text
(a) H1/H2 FAIL, s(z) phang:
    - Kiem san nhieu truoc. Neu q_hat dau da cham san 1.49 ms, day la gioi han
      do luong, khong phai fail khoa hoc.
    - Neu khong phai san, chuyen gate phu sang bin PHU deu-so-mau.

(b) H7 FAIL, duong cong vo dung:
    - Doi tieu chi chinh tu C1 sang C2.

(c) H8 FAIL, P(accept|C1,eps=0) > 0.90:
    - Ket qua chinh doi sang C2, vi C1 mat kha nang phan biet.
    - Bao cao bo sung voi alpha = 0.01 de xem duong cong co duoi ra khong.
    - Khong doi bin, score, cell, topology, hay truth table.

(d) H3/H4/H6/H9 FAIL:
    - Loi hien thuc. Sua code roi chay lai; khong ghi la ket qua khoa hoc.
```

## Gia thuyet va du doan

| Ma | Gia thuyet | Nguong | Ky vong |
|---|---|---|---|
| H1 | `q_hat` tang don dieu theo bin tuoi | Spearman = 1.0 | Dat |
| H2 | `q_hat(B4) / q_hat(B1) >= 1.3` | Ha tu 1.5 do san 1.49 ms | ~55% |
| H3 | Bao phu bien gan 90% | `abs(coverage - 0.90) <= 0.02` | Dat |
| H4 | Bao phu tung bin gan 90% | moi bin trong `0.90 +/- 0.05` | Dat |
| H5 | `rms(e_stale) > rms(e_model)` voi `z >= 0.10` o o chinh | so RMS | Dat |
| H6 | `s_margin` cho `P(accept)` >= `s_vs_a1` tai cung bao phu | moi o | Dat; neu fail la bug |
| H7 | C3 co diem huu ich | coverage >= 0.10 va `err|accept <= 0.5 * anchor` | ~85% |
| H8 | C1 khong qua de | `P(accept|C1,eps=0) <= 0.90` | ~50% |
| H9 | `q_hat` khong duoi san do luong | moi bin `q_hat >= 1.49 ms` | Dat |

Co so H5: `decision_error_constant_sigma.parquet`, `poisson@0.925`:

```text
rms_e_model = 0.3055
rms_e_stale = 0.2475 @ z=0.05 -> 0.7278 @ z=0.55
z_cross du doan in [0.05, 0.10]
```

Co so H8: `gap_twin` tinh chi tu twin tai `poisson@0.925`, `sigma=0.0096`.
Voi `q_hat` du doan `1.5-3.0 ms`, nguong `2*q_hat = 3-6 ms`, nen
`P(accept|C1)` du doan khoang `0.75-0.87`.

Du doan bang so:

| Dai luong | Du doan tien dang ky |
|---|---:|
| `q_hat(B1)` | 1.5-2.2 ms |
| `q_hat(B4)` | 2.0-3.0 ms |
| `q_hat(B4)/q_hat(B1)` | 1.2-1.6 |
| `P(accept|C1, eps=0)` | 0.75-0.87 |
| `z_cross` | 0.05-0.10 s |
| `err_anchor` | 0.27-0.31 |

## Gate 21R

| Gate | Tieu chuan |
|---|---|
| 21R-G1 | `q_hat(B4)/q_hat(B1) >= 1.3`, va it nhat `2/3` hieu lien tiep co CI99 Bonferroni > 0 |
| 21R-G2 | `eta^2(z) >= 0.05` tai o chinh |
| 21R-G3 | `abs(coverage_marginal - 0.90) <= 0.02` |
| 21R-G4 | moi bin co coverage trong `0.90 +/- 0.05` |
| 21R-G5 | bao cao `Var(e_model)`, `Var(e_stale)`, `Cov`, ca ba co CI |
| 21R-G6 | positive control V3 lam it nhat 1 bin lech coverage > 0.05, hoac SD ratio < 0.5 |
| 21R-G7 | Spearman(`q_hat` theo bin, `err(z)` tu 20R) = 1.0 |
| 21R-G8 | `q_hat_{alpha/K} > q_hat_alpha` o moi bin |
| 21R-G9 | huu ich: ton tai diem coverage >= 0.10 voi `err|accept <= 0.5 * anchor` |
| 21R-G10 | ben vung: lap tren it nhat 2 che do phu, G1/G3/G4 van dat |
| 21R-G11 | moi bin `q_hat >= 1.49 ms`; neu nho hon thi dieu tra bug truoc khi bao cao |
| 21R-G12 | `P(accept|C1, eps=0) <= 0.90`, gate qua-de |

## Doi chung bat buoc

```text
NC1  z = 0
     -> e_stale = 0 tuyet doi; s_margin chi con e_model.

NC2  twin = su that
     -> s = 0, q_hat = 0, accept 100%.

NC3  dong nhat thuc
     -> max |(e_model + e_stale) - s_signed| < 1e-12.

PC1  cbr @ 0.700
     -> q_hat ~ 0, P(accept) ~ 1.
     Co so: sawtooth err(cbr@0.7) = 0 va margin gan nhu hang so.

V3   chia ngau nhien theo mau thay vi theo block
     -> phai thay bao phu hong hoac SD ratio < 0.5.
     Co so: v7 offered co sd_ratio_mean = 0.349.

V5   tai tao 20R
     -> err tinh lai tu calib/test khop decision_error_constant_sigma.parquet
        trong 1e-6 tai cung z va cung n.
```

## Ngan sach lap

Toi da 2 vong sua neu H7 fail, moi vong chi sua MOT thu:

```text
1. Doi tieu chi chinh tu C1 sang C2.
2. Dung s_norm voi sigma tu link_model_v2.sigma(mode,bw,q,rho).
```

Khong duoc fit `sigma_hat` moi. Khong duoc doi alpha, bin chinh, mode, topology
hay truth table.

## Rui ro da biet

```text
R1  Kha hoan doi van co the bi vi pham du da chia block. V3 se lo ra.
    Neu V3 bat thuong, tang b len 10*tau roi chay lai theo amendment.

R2  s_margin phu thuoc a1,a2 chon theo twin. Khi twin sai thu tu, cap (a1,a2)
    khong phai cap thuc su canh tranh. Bao cao ti le pair_is_true_contender.

R3  QS-LOSS chua ket luan duoc cho h2 o 20R; ket qua h2 mang caveat.

R4  Xep hang tuyet doi chi giu trong |r_path| < 0.008868. s_margin giam nhe
    rui ro nay nhung khong xoa duoc.

R5  Cac o 20R khong doc lap hoan toan; poisson va h2 chung quy dao rho theo seed.

R6  sigma co dinh 0.0096 khac sigma van hanh. Lesson 21R.8 bao cao ca hai.

R7  e_model la sai so tong quat hoa cua PCHIP luoi thua so voi luoi do day,
    khong phai sai so so voi vat ly. Tai 12 diem huan luyen Phase L,
    e_model = 0 theo cau truc.

R8  San do luong truth_table khoang 1.49 ms tren thang cost, chi phoi boi kenh
    loss. Neu H2 fail, kiem tra co phai do san nen ti so truoc khi ket luan.

R9  tau = 1.0 s la tham so thiet ke cua AR(1) tong hop, khac tau = 2.87 s do
    duoc tren tai loi that. Bao dam bao phu chi phat bieu cho qua trinh tong hop.
```
