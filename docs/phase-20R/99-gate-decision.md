> **SUPERSEDED cho hang G6 (2026-08-07).** Xem `08-gates.md` va
> `00n-amendment-13.md` §15. Hang `G6 NOT EVALUATED` duoi day VAN DUNG cho
> cascade (`C - sum(B)`); dieu kien tien quyet `A' - A` da duoc do va bao cao
> rieng thanh `G6-PRE`.

# Phase 20R -- Gate Decision

Ngay ghi: 2026-08-06

Ket luan ngan: decision-error gates chinh dat tru G4; G4/H3 FAIL nhu thong ke
da tien dang ky. Muc dich khoa hoc cua G4 van dat bang ket qua phu thuoc che do
va co che don dinh H7/H8. H6 PASS. `20R-G6` end-to-end additivity khong co
artifact trong lesson nay, nen khong duoc danh dau PASS neu chua co DC1 rieng.

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
