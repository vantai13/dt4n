> **SUPERSEDED cho hang G6.** Xem `08-gates.md`, `07b-design-validation-v2.md`,
> va `00o-amendment-14.md` §42. Hang `G6 NOT EVALUATED` duoi day la trang thai
> lich su ngay 2026-08-06; cascade `C - sum(B)` da duoc do trong Lesson
> 20R.6-v2 ngay 2026-08-10.

# Phase 20R -- Gate Decision

Ngay ghi: 2026-08-06

Ket luan ngan: decision-error gates chinh dat tru G4; G4/H3 FAIL nhu thong ke
da tien dang ky. Muc dich khoa hoc cua G4 van dat bang ket qua phu thuoc che do
va co che don dinh H7/H8. H6 PASS. Phan G6 trong bang lich su ben duoi la
trang thai truoc Lesson 20R.6-v2; phan cap nhat hien hanh nam o muc
`Phase 20R.8 -- Nhanh (a) GO`.

## Phase 20R.8 -- Nhanh (a) GO

Dieu kien nhanh (a) duoc thoa tai diem van hanh:

```text
mode = poisson
rho_bar = 0.925
n = 120000
seeds = 101,102,103,104,105

err_total = 0.295005
d_sla     = 0.098596
G3        = Spearman(err,z) positive
```

`err_total` nam trong `[0.05, 0.40]` va `d_sla` du 3.3 lan floor 0.03. CI95
baseline cua hai point estimate nay khong duoc luu trong artifact scan; khong
dien so CI khong co provenance.

## Bien sai so he thong sau Lesson 20R.6-v2

```text
Transfer topology:
  artifact = results/phase-20R/breakdown_scan_transfer_qt3_n120k.json
  safety_published = 3.713970
  binding = poisson/loss/common_mode
  first_broken = K4_path_ranking_preserved @ poisson@0.925

Cascade composition:
  artifact = results/phase-20R/breakdown_scan_cascade.json
  safety_published = 0.868750
  binding = poisson/loss/common_mode
  first_broken = K4_path_ranking_preserved @ poisson@0.925
  r* = [0.008805, 0.008868]
```

Ca hai nguon sai so he thong rang buoc cung mot ket luan va cung mot o:
`K4_path_ranking_preserved` tai `poisson@0.925`.

Kiem co che:

```text
poisson@0.925 path cost:
P1 = 112.9658
P3 = 120.5115
|P1-P3| = 7.5457  # khe nho nhat trong 6 cap
```

Cascade lam ranking doi tu `P1,P3,P4,P2` sang `P3,P1,P4,P2`, tuc lat dung cap
co khe quyet dinh nho nhat. Diem van hanh duoc chon cho Phase 21R cung la o
co xep hang mong manh nhat duoi phan du ghep. Day la phat hien co che, khong
phai trung hop.

## Pham vi hieu luc sua doi

```text
err, d_sla, Spearman(err,z), va thu tu family: giu nguyen hieu luc.
Xep hang tuyet doi cac duong tai poisson@0.925:
  chi giu trong pham vi residual cascade |r_path| < khoang 0.00886.
```

He qua cho Phase 21R: chung nhan phai nham vao HIEU chi phi giua cac duong,
khong phai chi phi tuyet doi tung duong. Hieu chi phi la dai luong quyet dinh
argmin, va cung la dai luong mong manh nhat tai diem van hanh GO.

## Gate Table

```text
Gate    Status          Evidence
G1      PASS            poisson@0.700, z=0.55: err=0.187870 in [0.05,0.40]
G2      PASS            same cell: d_sla_ci95_lo=0.065583 >= 0.03
G3      PASS            same cell: Spearman(err,z)=1.0, exact p=0.002778
G4      FAIL            H3 monotonic theo rho_bar bi bac bo; khong co p<0.05
G5      PASS            NC1b=0, NC2 in [0.74692,0.75124], PC1 cbr=0
G6      NOT EVALUATED   no end-to-end additivity DC1 artifact in decision-error v2
G7      PASS            CI95 from paired block bootstrap, not naive iid SE
H6      PASS            max spread across tau at fixed z/tau = 0.029201 < 0.05
H7      PASS/PARTIAL    poisson unimodal PASS; h2 peak below left edge PARTIAL; delay-only PASS
H8      PASS            H8b inconclusive at n=200k, PASS after n=800k CI recheck
```

## 20R-G4

Operational calibration does not support the original monotonic story:

```text
poisson: 0.1879, 0.4301, 0.3756, 0.2650
h2     : 0.3898, 0.3340, 0.1047, 0.0017
rho_bar: 0.700,  0.850,  0.925,  0.960
```

Nhu da tien dang ky, G4 FAIL. Operational calibration:

```text
poisson Spearman(err,rho_bar) = +0.2, exact p = 0.9167
h2      Spearman(err,rho_bar) = -1.0, exact p = 0.0833
```

Constant-sigma diagnostic cung khong cuu monotonic law:

```text
poisson constant-sigma: 0.0000, 0.2870, 0.2905, 0.2650
h2 constant-sigma     : 0.1672, 0.0058, 0.0011, 0.0017
```

Khong goi fail la pass. Tuy vay muc dich cua G4 la chung minh che do van hanh
la bien dieu kien. Muc dich do DAT bang thong ke khac:

```text
poisson err qua rho_bar: 0.1879 .. 0.4301  ti so 2.3x
h2 err qua rho_bar     : 0.0017 .. 0.3898  ti so 229x
```

Bien thien nay lon hon CI block bootstrap nhieu lan. Ket qua H7 con cho thay
phu thuoc che do co dang don dinh/loss-driven, khong phai don dieu.

## H8 Mechanism

Bien dung cua he thong la:

```text
R = sd(cost_margin) / mean(cost_margin)
```

`R` duoc tinh tu twin va phan phoi rho, khong can measured truth. Phep kiem tau
sau Amendment 9:

```text
constant-sigma max |R_tau - R_tau=1| = 0.018882 < 0.02
operational max |R_tau - R_tau=1|   = 0.018696 < 0.02

tau=0.2  Spearman(R, err) = 1.000000
tau=1.0  Spearman(R, err) = 1.000000
tau=5.0  Spearman(R, err) = 1.000000
all tau  Spearman(R, err) = 0.988696
```

H8b, tuc `R` gan doc lap voi `tau`, khong duoc danh PASS tron voi artifact
cu `n=200000`. Worst point cu:

```text
tau=5, poisson rho_bar=0.85
point |Delta R| = 0.018882
conservative CI signed range = [-0.025670, +0.062551]
```

Khoang CI bao thu cu cham/vuot nguong `+-0.02`, nen ket luan dung tai thoi
diem do la `KHONG KET LUAN DUOC`. Phep va `n=800000`, 5 seed, `n_boot=2000`
da duoc chay rieng tai `results/phase-20R/margin_cv_ci_n800k.json` va cuu
duoc H8b:

```text
max |Delta R| = 0.006670
conservative signed CI envelope = [-0.016592, +0.015376]
threshold = +-0.020000
```

Ket luan co che: `rho_bar` la bien thiet ke; `R` la bien he thong phan ung
theo. `R` du doan thu hang risk tot; H8a/H8b/H8c PASS sau artifact n800k.

## Prediction Decision

Prediction at `z=0.55` matched the measured run tightly:

```text
h2      0.700  ratio=1.002
h2      0.850  ratio=1.032
h2      0.925  ratio=1.166
poisson 0.700  ratio=1.012
poisson 0.850  ratio=0.982
poisson 0.925  ratio=0.958
poisson 0.960  ratio=1.008
```

`h2@0.960` is handled by Amendment 6 near-zero absolute law:

```text
predicted=0.000330, measured=0.001675, abs_gap=0.001345 <= 0.02
```

## Final Read

Phase 20R.5 establishes the main decision-error result: measured truth, paired
block CI, sawtooth operational point, prediction validation, deconfounded sigma
diagnostic, and tau scaling. The paper claim should emphasize:

```text
1. staleness dominates model error in substantive cells;
2. model and stale error can cancel, so do not add them;
3. operational err is not monotonic in rho_bar;
4. the true mechanism is loss-driven and band/unimodal, not delay-driven;
5. cost-margin CV `R` collapses family/rho effects and is stable across tau
   after the n=800k conservative CI recheck;
6. z/tau scaling is empirically stable within 0.029 absolute spread.
```

## Lesson 20R.7 -- DONG

```text
Amendment ky trong lesson: 00q-16, 00r-17, 00s-18

Amd 15 sec.8 (nguong gay khep kin)  : 3/3 PASS
Amd 15 sec.7 P1 ban kinh le          : NOT SUPPORTED (p = 0.085491)
Amd 15 sec.7 P2 vi tri dinh do cong  : NOT SUPPORTED (lech 4.5 buoc luoi;
                                       h2 khong kiem duoc)
Amd 15 sec.7 P3 kenh loss chi phoi   : SUPPORTED (17/17 o, 3.74x - 3955.60x)

Thu hoi ky thuat: `curvature_cost` voi h < buoc luoi khong duoc dung cho ban do.
                  `grad_cost` (bac 1) van hop le. Ket qua K4 khong bi anh huong.

He qua cho 20R.8 va 21R:
  - chung nhan phai nham vao HIEU chi phi giua cac duong (da ghi tu 20R.6)
  - va vao thong ke le DA CHUAN HOA, khong phai gia tri le tho
  - gia thuyet ung vien cho lesson sau: P[r(s) < sigma_rho]
    (hien la POST-HOC, phai tien dang ky va kiem tren du lieu chua dung)
```
