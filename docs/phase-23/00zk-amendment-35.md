# AMENDMENT 23-35 -- Dinh chinh 23-34: S8 truoc, residual tuong doi

Ngay: 2026-08-21
Trang thai: **SAU KHI AMENDMENT 23-34 VA RUNNER P1/P3 DA COMMIT; SAU 43 ROW
PILOT, NHUNG TRUOC KHI VIET CODE S8 VA TRUOC KHI DOC KET QUA TUONG DOI.**

Amendment 23-34 da di thang tu S7 sang residual vi sai tuyet doi. Huong dan
hau kiem moi chi ra mot dieu kien con thieu: residual `-0.0095` duoc do tai
`rho_bar=0.925` nhung da bi ap nhu hang so tuyet doi tren ca dai. Day la S8.
Khong sua nguoc Amendment 23-34; file nay thay the thu tu va pham vi cua no.

## 1. Phan xu campaign da khoi dong

Runner da tao 43 row gate-clean:

```text
P1 poisson@0.925 : B=15, C=5
P1 poisson@0.850 : B=15, C=5
P1 h2@0.700      : B=3,  C=0
```

Chung duoc giu nguyen duoi `results/phase-23/differential_live/` nhu **PILOT
PRE-S8**. Khong row nao duoc dung de cham M-31..M-33 hay dong L10. Campaign
23-34 dung tai checkpoint; khong xoa du lieu va khong che giau viec da chay.

## 2. S8 va thu tu bat buoc moi

S8: residual tuyet doi do tai mot diem van hanh bi ap ngoai diem do tren mot
dai ma loss nen thay doi qua nhieu bac do lon. Clipping la dau do mat hieu luc,
khong phai ket qua vat ly.

Thu tu khoa:

```text
(1) sua ke toan/nhan/schema;
(2) audit residual TUONG DOI khong-Mininet tren ba cell;
(3) viet lai bao cao S8;
(4) chi sau do moi prereg va chay campaign Mininet moi.
```

## 3. M-27..M-30 khoa truoc code S8

| ID | Dai luong (thang / muc / tap hang) | Nhan | Dai khoa |
|---|---|---|---|
| M-27 | `abs(r_abs) / q01(min_p loss_p)`, loss fraction / per-path / test rows, tung cell | [CO CHE] | poisson@0.925 `<1`; poisson@0.850 `>1` |
| M-28 | `relative_point`, loss fraction ratio / per-path / raw B-C poisson seeds 104..108 tai rho=0.925 | [TAT DINH] | `-0.20 .. -0.12` |
| M-29 | flip fraction sau `loss_p*(1+r_rel)`, per-path multiplicative / test rows / point, tung cell | [NGOAI SUY] | `0.00 .. 0.05` ca 3 cell |
| M-30 | path clip ratio cung nhanh M-29, per-path / all evaluations / point, tung cell | [CO CHE] | `0.000000` chinh xac ca 3 cell |

M-28 tai lap tu artifact da co nen khong tinh prediction-hit khoa hoc. M-29
va M-30 duoc cham tren ca ba cell. `H_path_with_clip_descriptive` cu duoc giu
lam detector S8; `33.35%` chi la scope flag, khong la hieu ung mang.

## 4. Sua ke toan va nhan

M-24/M-25 phai cham tren held-out cell vi dai luong da khoa ap dung cho chung:

```text
poisson@0.850: M-24 HIT (0.000906), M-25 HIT (0.993257)
h2@0.700     : M-24 HIT (0.000320), M-25 HIT (0.998734)
```

M-26 chi dinh nghia tai cell chinh. Hai cell con lai giu `null` nhung bat buoc
co reason `main_cell_only_by_definition`.

Record channel `loss` phai ghi estimand la **chenh lech ton that**, khong ghi
`chi phi`. `w_loss` khong tham gia tinh residual loss.

## 5. Schema residual khoa moi

Moi `ResidualRecord` bat buoc co:

```text
rho_bar_measured
baseline_magnitude
relative_point = point / baseline_magnitude
valid_range = [rho_lo, rho_hi] hoac null
```

Voi loss, `baseline_magnitude` la loss ghep B trung binh. Voi delay, no la
tong delay B trung binh va `relative_point` chi la metadata scope, khong cap
quyen dung mo hinh nhan. Artifact cu phai duoc tai sinh tu raw; khong dien tay.

## 6. Campaign sau S8

Amendment rieng se khoa M-31..M-33 sau khi audit S8 xong va truoc Mininet:
`P1/P3 x rho={0.850,0.925} x seed=101..108`. Ket qua chinh dung `r_rel` theo
path/load; Q3 phai tai lap residual cu tai rho=0.925. Khong tiep tuc grid
`3 cell x seed 201..205` cua Amendment 23-34.
