# 05 -- Cross-cell Lesson 23.4

Ngay: 2026-08-15

Lesson 23.4 da chay tren ba cell:

```text
poisson@0.925  main cell da dong o Lessons 23.1--23.3
poisson@0.850  scale-invariance control, rebuilt 45 cot
h2@0.700       regime shift, rebuilt 45 cot
```

Artifact parity da duoc sua truoc khi sweep: hai parquet moi co `y_hat_a1` va
`sla_viol_p0..p3`, builder `fail=[]`, va hash da khoa trong
`results/phase-23/INHERITED.sha256`.

## Bang bon cot cho C3

Bang nay dung rule cua Amendment 23-18: headline cross-cell la `err`, `regret`
chi doc kem decomposition, va `gap_closed` dung B6-sys lam oracle he thong.

| Cell | C3 beneficial band | Improvement area | partial AURC [0.6,1] | gap_closed @0.78 |
|---|---:|---:|---:|---:|
| poisson@0.925 | [0.6076, 0.99995] | 0.003403849 | 0.213898526 | +0.100191538 |
| poisson@0.850 | [0.8091, 0.9892] | 0.000596149 | 0.225453621 | -0.031775777 |
| h2@0.700 | [0.84285, 0.99995] | 0.000274377 | 0.130903199 | -0.086048789 |

Doc dung: C3 co dai co loi o ca ba cell, nhung o hai cell moi dai do bi day
ve coverage cao. Tai diem van hanh 0.78, C3 thua always-trust o ca hai cell
moi.

## Selector tai coverage 0.78

| Cell | Selector | err_system | delta vs neo | beneficial band |
|---|---|---:|---:|---|
| poisson@0.925 | B2 constant gap | 0.209413821 | -0.012984857 | [0.63465, 0.99995] |
| poisson@0.925 | B3 AoI | 0.234959507 | +0.012560829 | empty |
| poisson@0.925 | B5 relative margin | 0.210421888 | -0.011976790 | [0.63990, 0.99995] |
| poisson@0.925 | C3 conformal | 0.209529829 | -0.012868849 | [0.60760, 0.99995] |
| poisson@0.850 | B2 constant gap | 0.225390876 | +0.004664308 | [0.81780, 0.98665] |
| poisson@0.850 | B3 AoI | 0.236277594 | +0.015551026 | empty |
| poisson@0.850 | B5 relative margin | 0.225514884 | +0.004788316 | [0.81835, 0.98800] |
| poisson@0.850 | C3 conformal | 0.223846774 | +0.003120206 | [0.80910, 0.98920] |
| h2@0.700 | B2 constant gap | 0.134040847 | +0.007504495 | [0.87445, 0.99995] |
| h2@0.700 | B3 AoI | 0.125158260 | -0.001378091 | [0.59990, 0.99995] |
| h2@0.700 | B5 relative margin | 0.134812898 | +0.008276546 | [0.86865, 0.99995] |
| h2@0.700 | C3 conformal | 0.130402607 | +0.003866255 | [0.84285, 0.99995] |

Ket qua dao nguoc ket luan cu:

```text
poisson@0.850: khong selector nao trong bang chinh co loi tai 0.78.
h2@0.700     : B3 AoI la selector duy nhat co loi tai 0.78, va tot hon C3.
```

## G23-23 -- lift law

Co che #9:

```text
twin_deg  = err_twin|reject - err_neo
prior_deg = err_P1|reject   - err_P1
lift      = twin_deg - prior_deg
swing     = err_P1 - err_neo
co loi    <=> lift > swing
```

Audit G23-23:

```text
identity_pass=True
all_signs_match=True
max_abs_delta_identity_error=2.17e-17
```

Sau dong co che:

| Cell | Selector | lift | swing | lift - swing | delta vs neo | Benefit |
|---|---|---:|---:|---:|---:|:--:|
| poisson@0.925 | B3 AoI | 0.060783 | 0.117878 | -0.057095 | +0.012561 | no |
| poisson@0.925 | C3 conformal | 0.176372 | 0.117878 | +0.058495 | -0.012869 | yes |
| poisson@0.850 | B3 AoI | 0.053756 | 0.124442 | -0.070686 | +0.015551 | no |
| poisson@0.850 | C3 conformal | 0.110259 | 0.124442 | -0.014183 | +0.003120 | no |
| h2@0.700 | B3 AoI | 0.037182 | 0.030918 | +0.006264 | -0.001378 | yes |
| h2@0.700 | C3 conformal | 0.013344 | 0.030918 | -0.017574 | +0.003866 | no |

Day la ket qua chinh cua Lesson 23.4. C3 khong phai "luon tot"; C3 tot khi
lift cua no vuot ngan sach swing. B3 yeu hon ve twin signal, nhung trung lap
voi prior P1 hon; khi swing hep, tinh trung lap nay thang.

## Threshold families va S7

S7 du doan ho NHAN Pareto-dominates ho CONG tren ca hai cell moi. Ket qua:

| Cell | Pareto survivors | single-family dominance | mul-add delta @0.78 | CI95 |
|---|---|:--:|---:|---|
| poisson@0.850 | additive=2, multiplicative=1 | false | -0.002688177 | [-0.006094814, +0.001020532] |
| h2@0.700 | additive=2, multiplicative=1 | false | +0.003420226 | [+0.001685635, +0.005060487] |

S7 FAIL. Tren ca hai cell moi, Pareto front khong con la mot ho NHAN duy nhat.
O `h2@0.700`, tai coverage 0.78 ho NHAN con kem ho CONG ro tren `err`.

## Bang diem E4-moi

| ID | Ket qua | Ghi chu |
|---|---|---|
| S1 | FAIL | C3 delta @0.78 doi dau: -0.012869 vs +0.003120, lech 0.015989 |
| S3 | PASS | h2 best C3 improvement = 0.002956 < 0.008 |
| S4 | PASS | h2 C3 band nonempty va hep hon main: band_low 0.84285 > 0.6076 |
| S5 | PASS | h2 C3 gap_closed = -8.60% < +10.02% |
| S6 | PASS | G23-21c pass ca hai cell moi, min effective blocks 433 va 397 |
| S7 | FAIL | Ho NHAN khong Pareto-dominates ho CONG tren hai cell moi |

Bai hoc #12: dai luong bien bang nhau khong suy ra hanh vi co dieu kien bang
nhau. Muon so hai cell, phai do lift/prior_deg/twin_deg tren tap reject.

## Artifacts

```text
results/phase-23/g23_23_lift_law.json
results/phase-23/cross_cell_summary.json
results/phase-23/cross_cell_summary.csv
results/phase-23/cross_cell_err_panels.png
results/phase-23/threshold_families_poisson_0.850_C3_static.json
results/phase-23/threshold_families_h2_0.700_C3_static.json
results/phase-23/baseline_rankings_poisson_0.850_C3_static.json
results/phase-23/baseline_rankings_h2_0.700_C3_static.json
```

## Ket luan

Phat bieu cu "C3 cai thien rui ro he thong tren Phase 23" qua hep va khong
giu cross-cell. Phat bieu moi manh hon:

```text
Mot abstain selector co loi khi va chi khi lift > swing tren tap reject.
C3 co lift lon khi swing du rong va prior khong bi lam ban qua nhieu.
B3 co lift nho hon, nhung gan trung lap voi P1; no thang khi swing hep.
```
