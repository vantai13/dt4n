# AMENDMENT 23-19 -- Artifact parity va Co che #9

Ngay: 2026-08-15
Commit: truoc khi chay lai Step 3--5 tren hai cell moi.

Ly do: G23-21c tren `poisson@0.850` va `h2@0.700` lam lo hai viec cung luc:
mot phat hien co che lon hon ket luan cu, va mot lo hong artifact. Hai parquet
cell-specific chi co 40 cot, thieu `y_hat_a1` va `sla_viol_p0..p3`, nen Step 3
khong duoc chay tiep tren chung.

## F1 -- artifact parity

Da chon nhanh A: rebuild hai parquet voi cung builder `cert/build_calib_set_v3.py`
de co du 45 cot nhu main cell.

```text
poisson@0.850:
  artifact = results/phase-22/calib_set_v3_poisson_0.850.parquet
  sha256   = 1565767d87060304be9ee651a627c2fa0cb737e0fd11e578078b34579aa16f66
  columns  = 45
  has_y_hat_a1 = True
  sla_viol_p0..p3 = present
  builder fail = []
  V23_sla_twin_match = True
  V23_sla_star_match = True

h2@0.700:
  artifact = results/phase-22/calib_set_v3_h2_0.700.parquet
  sha256   = cae93a3c1008e39e7ef76b4f7f20dea07186b96cef256920725cc2a8bf08ce05
  columns  = 45
  has_y_hat_a1 = True
  sla_viol_p0..p3 = present
  builder fail = []
  V23_sla_twin_match = True
  V23_sla_star_match = True
```

G23-17a/b/c da duoc refresh tren artifact moi; cac so noi dung khong doi,
chi artifact hash/provenance doi. Manifest `results/phase-23/INHERITED.sha256`
da khoa hai hash moi.

## Co che #9 -- lift so voi ngan sach

Dat tai mot coverage co dinh va mot bo chon reject:

```text
twin_deg  = err_twin|reject - err_neo
prior_deg = err_P1|reject   - err_P1
swing     = err_P1 - err_neo
lift      = twin_deg - prior_deg

Co loi  <=>  err_P1|reject < err_twin|reject
        <=>  lift > swing
```

Dong nhat thuc can kiem:

```text
delta_vs_anchor = reject_share * (swing - lift)
```

Gate moi:

```text
G23-23  Voi moi (cell, selector) trong audit @ coverage 0.78, dau cua
        lift - swing phai khop dau cua -delta_vs_anchor, va delta phai duoc
        tai tao boi reject_share * (swing - lift) voi sai so <= 1e-9.
```

Ket qua tren sau dong trong yeu:

```text
cell           selector              lift      swing   lift-sw     delta     benefit
poisson@0.925  B3_aoi            0.060783   0.117878 -0.057095 +0.012561       False
poisson@0.925  C3_conformal      0.176372   0.117878 +0.058495 -0.012869        True
poisson@0.850  B3_aoi            0.053756   0.124442 -0.070686 +0.015551       False
poisson@0.850  C3_conformal      0.110259   0.124442 -0.014183 +0.003120       False
h2@0.700       B3_aoi            0.037182   0.030918 +0.006264 -0.001378        True
h2@0.700       C3_conformal      0.013344   0.030918 -0.017574 +0.003866       False
```

Check tu tool:

```text
identity_pass=True
all_signs_match=True
max_abs_delta_identity_error=2.17e-17
```

## Dao nguoc ket luan van hanh

Tai coverage 0.78:

```text
                    poisson@0.925   poisson@0.850    h2@0.700
C3 conformal         -0.012869      +0.003120       +0.003866
B2 constant gap      -0.012985      +0.004664       +0.007504
B3 AoI               +0.012561      +0.015551       -0.001378
B1 random            +0.026396      +0.027554       +0.007024
```

Do do:

```text
G23-15  C3 <= B3 tren dai kha di     FAIL o h2@0.700 tai 0.78; B3 tot hon C3.
G23-17  ket luan giu tren ba cell    FAIL; ket luan 23.3 la tinh chat cua
                                      cell poisson@0.925, khong phai bat bien.
```

Day khong phai NO-GO. Ket qua moi manh hon phat bieu cu: Phase 23 bay gio co
mot quy tac dieu kien cho biet khi nao abstain co loi, thay vi chi co mot diem
thuc nghiem tren main cell.

## Gioi han pham vi Co che #2

Co che #2 trong Lesson 23.1 noi: trong `poisson@0.925`, khi quet kappa, do
suy giam cua P1 tren tap reject gan nhu hang so quanh `0.052`, trong khi twin
deg thay doi manh. Phat bieu nay chi dung theo truc kappa trong mot cell.

Giua cac cell tai coverage 0.78, truc dao nguoc:

```text
C3:
  twin_deg   = 0.230948 / 0.235829 / 0.237724   gan bat bien
  prior_deg  = 0.054576 / 0.125570 / 0.224379   bien thien 4.1 lan

B3:
  twin_deg   = 0.061092 / 0.055446 / 0.035283
  prior_deg  = 0.000309 / 0.001689 / -0.001899 gan bang 0
```

Doc dung: `m_hat` la tin hieu manh ve twin, nhung khong trung lap voi fallback
P1; no reject dung vung P1 cung yeu. `z` yeu hon ve twin, nhung gan trung lap
voi P1 khi fallback la mot duong tinh static.

## Bang diem E4-moi tai diem hien co

```text
S1  poisson@0.850 giong poisson@0.925 tren err       FAIL
    delta C3 @0.78: -0.012869 vs +0.003120, lech 0.015989.

S3  h2@0.700 co |delta_best| < 0.008                 provisional PASS
    Tai @0.78 C3 delta +0.003866; can sweep day du de chot best.

S4  h2 beneficial band khong rong nhung hep hon       provisional PASS
    B3 da co loi @0.78; C3 can sweep day du de chot band rieng.

S5  gap_closed(h2) < 10.02%                           PASS
    C3 gap_closed @0.78 = -8.60%.

S6  G23-21c PASS ca hai cell moi                      PASS
    min effective blocks: 433 va 397.

S7  Ho NHAN Pareto-dominates ho CONG                  chua do
```

Bai hoc #12:

```text
Dai luong bien bang nhau khong suy ra hanh vi co dieu kien bang nhau.
err_neo, err_P1, swing cua poisson@0.850 va poisson@0.925 gan nhau,
nhung prior_deg tren tap reject lech 2.3 lan va ket luan dao chieu.
Muon so hai cell, phai do dai luong co dieu kien tren tap reject.
```

## Dieu kien tiep theo

Sau amendment nay moi duoc chay Step 3--5. Step 3 phai dung artifact 45 cot;
ket qua cross-cell phai bao cao:

```text
1. bang bon cot cho C3: beneficial band, improvement area,
   partial AURC [0.6,1], gap_closed;
2. bang selector @0.78 de ghi ro B3 la bo chon duy nhat co loi o h2@0.700;
3. G23-23 lift law report;
4. hinh err_system 3 panel tren coverage cho neo, C3, B2, B3, B6-sys.
```
