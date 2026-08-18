# PRE-REGISTRATION -- Phase 23
# Fallback semantics and system risk after rejection

Ngay ky    : 2026-08-14
Nguoi ky  : vantai (Codex-assisted)
Git tag   : phase-23-start
Tien de   : Phase 22 GO tai `0a3bea3` (17/17 gate PASS, 21/32 prediction hit)

Tai lieu nay khoa cac quyet dinh phan tich truoc khi chay cac lesson 23.1+.
Neu sua sau tag, phai them amendment co ngay, ly do, va chi ro la do loi code
hay do phep do moi, khong duoc sua vi ket qua dep/xau.

## 0. Pilot data disclosure

Trong Lesson 23.0, cac so sau da duoc nhin de kiem thiet bi do va provenance.
Chung phai duoc cong khai truoc khi ky.

| Dai luong | Gia tri | Vi sao nhin |
|---|---:|---|
| `calib_set_v3.parquet` | 999,945 hang | Rebuild artifact bi ignore khoi git |
| Luoi AoI cua B3 | 100 diem, `{0.01,...,1.00}` coverage | Kiem G23-10 |
| `err` neo, toan hang / test | 0.220835 / 0.222399 | Doi chieu anchor |
| `regret` neo, toan hang / test | 1.747214 / 1.767461 ms | Doi chieu thang risk |
| `d_sla` neo, toan hang / test | 0.060125 / 0.060752 | Doi chieu anchor va SLA |
| `P(a* = P1)`, toan hang / test | 0.656141 / 0.659724 | Mo ta F2 STATIC |
| `err|accept` cua B3 tai h=0.30 | 0.1767 | Kiem thiet bi do B3 (tu Lesson 23.0) |

Dong nao trong bang du doan duoc anh huong truc tiep boi disclosure nay duoc
danh dau `[THI DIEM]` hoac `[MO TA]` va khong tinh vao ti le prediction hit
confirmatory. Ket qua confirmatory phai den tu seed/test doc lap neu duoc dung
lam claim.

Nguon vao va sha256 duoc ghi tai:

```text
results/phase-23/INHERITED.sha256
```

## 1. Cau hoi trung tam

Phase 22 do nhanh accept cua trust gate. Phase 23 do ca he thong:

```text
R_system = P(accept) * R|accept + P(reject) * R|fallback
```

Tai kappa=0.5 cua Phase 22:

```text
P(accept) = 0.4911
err|accept = 0.0809
err neo test = 0.2224
```

Nguong hoa von:

```text
err|fallback < (0.2224 - 0.4911 * 0.0809) / 0.5089 = 0.3592
```

Neu fallback tren tap reject te hon 0.3592 thi certification lam he thong te
hon neo B0, du nhanh accept rat dep.

## 2. Quyet dinh khoa P1..P20

### P1..P16 -- ke thua tu Phase 22

P1  `y_true = TruthTable(rho(t))`, `y_hat = CostV2(rho(t-z))`, tai su dung
    `_cell_arrays`, khong viet lai vat ly.

P2  Score chinh `s_sim = max_j s_pair_j`; score phu `s_margin`, `s_pair_j`,
    `s_signed`.

P2b Slot la rank theo twin, khong phai danh tinh duong.

P2c Hieu chuan tung slot rieng, khong gop 3 score cung hang.

P3  `alpha = 0.10`, so so sanh `K-1 = 3`; Bonferroni, Sidak, max-score giu
    dung dinh nghia Phase 22.

P3c Half-normal bridge chi la diagnostic theo score, khong thay conformal.

P4  O chinh `poisson@0.925`; o phu `poisson@0.850`, `h2@0.700`; doi chung
    `cbr@0.700`, `poisson@0.700`.

P5  Z-bin giu nguyen 21R/22: B0 `[0.055,0.10)`, B1 `[0.10,0.20)`,
    B2 `[0.20,0.30)`, B3 `[0.30,0.550]`.

P6  `m_hat_bin` tinh bang quantile tren calib sau split.

P7  Split block 5.0 s, 50/50, seed 7000; validation theo seed
    calib `{101,102,103}` / test `{104,105}`.

P8  Accept theo ho NHAN mac dinh: `m_hat >= kappa * q_hat(z_bin,m_hat_bin)`.
    Ghi chu sau G23-21b/G23-21c: notation age-only trong cac ghi chu cu la
    shorthand; implementation C3 that su dung Mondrian key 2D `z_bin x
    m_hat_bin`, voi 3 score slots.

P9  `eps_regret = 0.10 * T_delay` theo o, khong dat lai nguong theo ket qua.

P10 Neo 21R chi duoc dung khi thiet ke lay mau khong doi; neu doi AoI/load thi
     tinh neo rieng.

P11 Ho so AoI U0/U1/U2/PC4 giu dung Phase 22, thu tu link khoa theo
     `topology_v7`.

P12 Luoi tau `{0.5, 1.0, 2.0, 2.87, 5.0}` chi dung cho tau sweep, khong chen
     diem sau khi nhin ket qua.

P13 Thu tuc FCR/selective neu dung phai la fixed point, P(accept) do tren
     calib.

P14 Moi artifact phai co scale/level/rowset trong metadata neu sinh moi.

P15 Moi prediction phai noi ro thu tuc, slot/nhom, tap hang.

P16 Truoc prediction ve dau `X > Y`, phai uoc luong do lon hieu ung va san
     nhieu; neu duoi san nhieu thi khoa can thay vi khoa dau.

### P17..P20 -- moi cho Phase 23

P17  Ba fallback, dung du ba:

```text
F1 STICKY : giu duong da cai dat lan accept gan nhat; ban dau = P1.
            Reset ve P1 o dau moi block de khong ro ri calib/test.
F2 STATIC : luon P1.  P1 = uA + ac + vC = 2.0 + 3.0 + 2.0 = 7.0 ms.
F3 WAIT   : cho snapshot ke tiep, tuoi reset, quyet dinh lai cung chinh sach;
            bao cao them do tre quyet dinh.
```

Khong them fallback thu tu sau khi thay ket qua.

P18  Ba thang risk, bao cao du:

```text
err      = P(a_chon != a*)
regret   = E[cost_true(a_chon) - cost_true(a*)]          [ms]
sla_rate = P(delay_true(a_chon) > t_delay_ms OR loss_true(a_chon) > t_loss)
d_sla    = sla_rate(a_chon) - sla_rate(a*)
```

Dieu kien SLA ke thua `measurements.decision_error_v2._viol`. Cam dinh nghia
lai thanh `cost > SLA`.

P19  Hai ho nguong doc lap va mot cach dien giai:

```text
NHAN   : accept <=> m_hat >= kappa * q_hat(nhom)
CONG   : accept <=> m_hat >= q_hat(nhom) - epsilon
REGRET : dong nhat dai so voi CONG vi q_hat - m_hat <= epsilon
```

REGRET la cach doc cost-sensitive cua CONG, khong phai ho thu ba. Gate G23-6b
phai kiem accept mask CONG va REGRET giong bit-for-bit.

P20  Baseline B0..B6:

```text
B0 always trust twin
B1 random abstain tai cung coverage
B2 margin threshold phi-conformal
B3 AoI threshold
B4 oracle-risk threshold (upper-bound baseline, exploratory)
B5 learned logistic risk score (neu co training rieng)
B6 oracle action / wait-to-fresh lower bound
```

B3 la ham bac thang voi luoi coverage `{0.01,...,1.00}` do `z_s` co 100 gia
tri roi rac, moi gia tri chiem 1%. Moi so sanh C3 vs B3 phai noi suy ve cung
coverage.

## 3. Bang du doan khoa truoc

Nhan nguon:

```text
[CO CHE]     suy tu co che da khoa hoac artifact khac truc
[NGOAI SUY]  suy tu it diem so, dai rong
[KINH NGHIEM] truc giac co ghi ro
[THI DIEM]   da nhin du lieu lien quan, khong tinh confirmatory
[MO TA]      thong ke mo ta da cong khai, khong tinh confirmatory
```

| ID | Lesson | Du doan | Nguon | Dai khoa | Do duoc | KQ |
|---|---|---|---|---:|---:|---|
| F0 | 23.1 | `P(a* = P1)` tren o chinh | [MO TA] | 0.64-0.68 | 0.656141 | N/A |
| F1 | 23.1 | `err_system(F2)` tai kappa=0.5 | [CO CHE] | 0.21-0.27 | ___ | ___ |
| F2 | 23.1 | `err_system(F1)` tai kappa=0.5 | [CO CHE] | 0.17-0.24 | ___ | ___ |
| F3 | 23.1 | `err_system(F3)` tai kappa=0.5 | [CO CHE] | 0.10-0.18 | ___ | ___ |
| F4 | 23.1 | Thu tu risk: F2 > F1 > F3 | [CO CHE] | cau truc | ___ | ___ |
| F5 | 23.1 | Do tre quyet dinh trung binh F3 | [CO CHE] | 100-250 ms | ___ | ___ |
| F6 | 23.1 | `err_system(C3 + fallback tot nhat) < 0.2224` | [CO CHE] | cau truc | ___ | ___ |
| T2 | 23.2 | Ho CONG thoai hoa ve coverage 1.0 khi epsilon lon | [CO CHE] | cau truc | ___ | ___ |
| T3 | 23.2 | Spearman(err, regret) tren luoi coverage | [CO CHE] | > 0.90 | ___ | ___ |
| T4 | 23.2 | Spearman(err, sla_rate) tren luoi coverage | [NGOAI SUY] | > 0.80 | ___ | ___ |
| B1p | 23.3 | err\|accept cua B1 tai coverage 0.5 | [CO CHE] | 0.212-0.232 | ___ | ___ |
| B3p | 23.3 | err(C3)/err(B3) tai coverage 0.50 | [THI DIEM] | < 0.70 | ___ | ___ |
| B2p | 23.3 | err(C3)/err(B2) tai coverage 0.50 | [CO CHE] | 0.85-0.98 | ___ | ___ |
| B4p | 23.3 | err(C3)/err(B4) tai coverage 0.50 | [NGOAI SUY] | 0.6-0.9 | ___ | ___ |
| B5p | 23.3 | err(C3)/err(B5) tai coverage 0.50 | [KINH NGHIEM] | 0.7-1.0 | ___ | ___ |
| B6p | 23.3 | err(B6)/err(C3) tai coverage 0.50 | [CO CHE] | < 0.5 | ___ | ___ |
| G3a | GO-3 | `q_hat_stud/q_hat_max` o slot 1 (v1; xem Amendment 23-20) | [CO CHE] | 0.92-0.98 | 0.9525 | PASS |
| G3b | GO-3 | `q_hat_stud/q_hat_max` o slot 2 va 3 (v1; xem Amendment 23-20) | [CO CHE] | 0.98-1.02 | s2=0.9966; s3=1.0671 | PARTIAL/MISS v1; PASS v2 |
| S-5 | GO-3 | `sigma3/sigma1` (v2, `level=per_bin`; xem Amendment 23-21 muc 3) | [MO TA] | 1.05-1.50 | 1.1421 / 1.3325 / **1.6557** | **MISS** (h2@0.700 bin 0) |
| S-8 | GO-3 | Lift acceptance cua studentization -- "hieu ung nho 1-2 pp" (ghi chep truoc khi chay; xem Amendment 23-21 muc 4) | [KINH NGHIEM] | +1 den +2 pp | +11.5% / +42.5% / +48.1% tuong doi | **MISS** (ngoai suy 1 cell -> 3 cell) |

| A-1' | GO-1 | ratio AURC[0.6,1] C3/C0, poisson@0.925 (xem Amendment 23-22) | [MO TA] | 1.000-1.006 | 1.002492 | trong dai (tai lap) |
| A-2' | GO-1 | ratio AURC[0.6,1] C3/C0, poisson@0.850 (xem Amendment 23-22) | [MO TA] | 1.002-1.011 | 1.006249 | trong dai (tai lap) |
| A-3' | GO-1 | ratio AURC[0.6,1] C3/C0, h2@0.700 (xem Amendment 23-22) | [MO TA] | 1.007-1.018 | 1.012345 | trong dai (tai lap) |
| A-4' | GO-1 | So cell suy bien trong 5 (`err_neo < 0.02`) | [MO TA] | dung 2 | 2 | trong dai |
| A-5' | GO-1 | **CI95_high lon nhat cua ratio tren 3 cell danh gia duoc** | [NGOAI SUY] | 1.01-1.06 | **1.003173** | **MISS** (hep hon du bao) |
| A-6' | GO-1 | Duoc dua "frontier invariance" vao abstract? | [CO CHE] | `A-5' < 1.02` | CO, 3/3 cell | dat |
| A-7' | GO-1 | `\|discretisation_bias\|` lon nhat (xem Amendment 23-23) | [MO TA] | 0.001-0.010 | **0.012982** | **MISS** (cao hon dai) |
| A-8' | GO-1 | Dau cua `discretisation_bias` (xem Amendment 23-23) | [MO TA] | AM | AM, 3/3 cell | trong dai |
| A-6'b | GO-1 | Ket luan giu duoi can DONG THOI Bonferroni 3 cell? (Amd 23-24) | [MO TA] | CO | CO (1.004125) | dat |
| C-1 | GO-2 | `c_maxt` = phan vi 0.95 cua `T = max_k \|d_k-dbar_k\|/sigma_k` | [CO CHE] | 2.2-2.7 | ___ | ___ |
| C-2 | GO-2 | `c_bonferroni = z_{1-0.05/48}` | [TAT DINH] | 3.078088 | ___ | ___ |
| C-3 | GO-2 | `c_maxt / c_bonferroni` | [CO CHE] | 0.71-0.88 | ___ | ___ |
| C-4 | GO-2 | `n_contains_zero` voi dai DONG THOI | [CO CHE] | >= 5 va >= dai tung-o | ___ | ___ |
| C-5 | GO-2 | "Thu tu phu thuoc slot" con dung sau hieu chinh dong thoi? | [CO CHE] | CO | ___ | ___ |

`A-1'..A-4'`, `A-7'`, `A-8'` mang nhan `[MO TA]` va KHONG tinh prediction-hit.
`A-1'..A-4'`: uoc luong diem da tinh trong kiem toan bay cua Amendment 23-22
muc 1.3/1.6 (`1.002492 / 1.006249 / 1.012345 / 2`). `A-7'/A-8'`: da tinh trong
buoc kiem tra day du cua luoi mit, Amendment 23-23 muc 3 (`-0.002012`, dau AM)
-- ban dau chung duoc dat la `[CO CHE]` va bi HA nhan sau khi do qua tay.

Dai luong confirmatory DUY NHAT cua Lesson 23.5[B] la `A-5'`, va `A-6'` suy ra
tu no.

Ghi chu NT-v2-7 (Amendment 23-24 muc 1) cho `A-5'`: dong nay duoc viet o
Amendment 23-22 khi luoi quyet dinh con la PRIMARY. Amendment 23-23 (B-D13) doi
luoi quyet dinh sang REFINED nhung KHONG ra lai bang du doan. Tren luoi primary
`A-5'` cho `1.020352`, NAM TRONG dai; tren luoi refined no cho `1.003173`, ngoai
dai. Dong duoc cham la dong da khoa, va no MISS. Ghi nhan nay la mot SU KIEN ve
quy trinh, KHONG phai loi bien ho. Xu ly giong `S-5`: da nhin so thi khong duoc tinh diem, ke ca khi so do
trung dai.

Hai dong `S-5` va `S-8` la MISS. Chung duoc dat o BANG CHINH nay chu khong chi
trong Amendment 23-21, vi nguoi doc mo pre-registration truoc, khong mo
amendment thu 21. Chi tiet nguyen nhan o `docs/phase-23/00v-amendment-21.md`
muc 3 va muc 4; dai da tach (`S-5-pooled` / `S-5-perbin`) CHI ap dung cho cac
phase SAU, khong cham lai Lesson 23.5[A].

Neu `PHASE_23.md` goc duoc them vao repo sau nay, cac dong E/A/R/X phai duoc
bo sung bang amendment truoc khi chay lesson tuong ung. Trong repo hien tai
khong co file `PHASE_23.md`, nen tai lieu nay chi khoa nhung muc co nguon ro
tu Phase 22 va Lesson 23.0 da dan.

## 4. Nhanh FAIL viet truoc

Neu C3 khong vuot B3 tai coverage 0.50, claim chinh thu hep thanh:

```text
Certification cho bao dam hinh thuc va do duoc gia he thong; no khong phai
mot bo chon policy tot hon threshold AoI don gian tren o nay.
```

Neu fallback tot nhat khong vuot neo B0, claim thu hep thanh:

```text
Nhanh accept huu ich nhung khong du de cai thien he thong. Ket qua chinh la
fallback semantics quyet dinh certification co gia tri van hanh hay khong.
```

Neu F2 te hon B0 hoac gan nguong hoa von, khong che giau:

```text
Duong tinh ngan nhat khong du lam fallback chung. Mot fallback naive co the
xoa sach loi ich cua nhanh accept.
```

Neu SLA risk khong dong bien voi err/regret, bao cao ba thang rieng va khong
gop thanh mot score tong hop sau khi thay ket qua.

## 5. Doi chung va gate bat buoc

```text
NC23-1  kappa=0 quy ve always-trust twin.
NC23-2  fallback gia chon a_twin moi hang -> R_system = neo, sai so 1e-9.
NC23-3  shuffle accept mask -> khong duoc tao loi ich co cau truc.
NC23-4  oracle action la lower bound, chi exploratory.
NC23-5  a_chon = a_twin moi hang -> err/regret/d_sla bang neo.

PC23-1  F2 STATIC phai khac twin neu a_star != P1.
PC23-2  B3 AoI threshold phai quet coverage voi buoc <= 0.02.
PC23-3  Ho CONG/REGRET phai cho mask giong bitwise.
PC23-4  Block split vs row split phai hien ro sai khac variance.
PC23-5  Tat ca risk system phai thoa law of total probability.

V23-1   Rebuild artifact co `sla_viol_p0..p3`.
V23-2   Cot `sla_viol_p*` tai tao dung `viol_twin` va `viol_star`.
V23-3   Seed validation: calib {101,102,103}, test {104,105}.
```

Gate them:

```text
G23-4   R_system = P(acc)R|acc + P(rej)R|fallback, sai so 1e-9.
G23-6b  CONG va REGRET accept mask giong bit-for-bit o moi epsilon.
G23-10  Moi baseline quet coverage [0,1] voi buoc <= 0.02; B3 duoc chap nhan
        vi co 100 diem deu 1%.
```

## 6. Chu ky

```text
Nguoi ky : vantai (Codex-assisted)
Ngay     : 2026-08-14
Commit   : commit duoc tag `phase-23-start`
```

Toi xac nhan muc 0 da cong khai cac so da nhin va khong co ket qua Phase 23
23.1+ nao duoc dung de chon lai prediction sau khi ky.
