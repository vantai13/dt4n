# 13 -- Lesson 23.7-bis: residual-level audit (S7)

Code: `cert/residual_level_audit.py`  
Prereg: Amendment 23-32 va dinh chinh 23-33  
Artifacts: `results/phase-23/residual_level_audit_*.json`

## 1. Ket qua chinh

S7 duoc xac nhan theo **Kich ban A** tren ca ba cell. Tai endpoint `point`,
ty le doi `a*` tren test rowset la:

| Cell | H_path, dung tang/khong clip | H_path co clip [MO TA] | H_link0, khong clip | H_link1, co clip | Phan flip quy cho clipping |
|---|---:|---:|---:|---:|---:|
| poisson@0.925 | 0.000000 | 0.000000 | 0.000290 | 0.212960 | 0.998638 |
| poisson@0.850 | 0.000000 | 0.333466 | 0.000906 | 0.134373 | 0.993257 |
| h2@0.700 | 0.000000 | 0.000000 | 0.000320 | 0.252863 | 0.998734 |

Tren cell chinh, bom residual dung o tang duong cho `0/499,967` test rows
doi `a*`. Chia residual xuong link nhung chua clip chi lam `145/499,967`
rows doi (`0.0290%`). Hien thuc cu co clip lam `106,473/499,967` rows doi
(`21.2960%`). Tap 145 flips cua H_link0 la tap con cua H_link1; clipping them
106,328 flips va khong go flip nao.

Do do hon `99.86%` flip cua hien thuc Lesson 23.7 tai point den tu phep cat
mien sau khi tai phan bo residual, khong den tu residual common-mode do duoc.

## 2. Tai lap qua ba endpoint

Cell chinh `poisson@0.925`:

| Endpoint | r_path | H_path | H_link0 | H_link1 | clip share |
|---|---:|---:|---:|---:|---:|
| r_star | -0.008868197 | 0.000000 | 0.000258 | 0.196139 | 0.998685 |
| point | -0.009521786 | 0.000000 | 0.000290 | 0.212960 | 0.998638 |
| ci90_worst | -0.010135082 | 0.000000 | 0.000308 | 0.227297 | 0.998645 |

Bat bien H_path giu chinh xac tren ca `3 endpoint x 3 cell`. NC23v2-10 voi
shift bang 0 cung cho ca bon nhanh bang 0 chinh xac tren ca ba cell.

H_link1 tai point tai lap con so Lesson 23.7 tren cell chinh:

```text
cu, M-15 test fraction : 0.212960055363654
moi, H_link1           : 0.212960055363654
sai lech               : 0.0
```

Day la doi chung quan trong: ket qua moi khong den tu viec viet lai mot
pipeline gan giong; no tai su dung `measurements.band_v2.truth_table_for` va
`cert.cell_matrices.cell_matrices` cua phep do cu.

## 3. Cham prereg M-23..M-26 -- ke ca held-out

| ID | poisson@0.925 | poisson@0.850 | h2@0.700 | Dai khoa | KQ |
|---|---:|---:|---:|---:|:--:|
| M-23 H_path | 0.000000 | 0.000000 | 0.000000 | = 0 tai 9/9 endpoint-cell | PASS [TAT DINH] |
| M-24 H_link0@point | 0.000290 | 0.000906 | 0.000320 | 0.000--0.020 | HIT 3/3 |
| M-25 clip share | 0.998638 | 0.993257 | 0.998734 | > 0.90 | HIT 3/3 |
| M-26 tai lap 0.2130 | 0.212960 | n/a | n/a | cell chinh, sai so < 0.005 | PASS |

Hai gia tri M-26 held-out ghi `null` kem reason
`main_cell_only_by_definition`, khong con `null` tran. Kich ban khoa truoc:
**A**. M-23 va M-26 la kiem tra bat bien/doi chung, khong tinh prediction-hit.

## 4. Dinh ly argmin va dieu kien tien quyet

Voi cung `r` cho moi duong:

```text
cost'_p = delay_p + w_loss * (loss_p + r)
        = cost_p + w_loss*r

argmin_p cost'_p = argmin_p cost_p.
```

Audit cai H_path khong clip de do dung bat bien nay. Loss am (neu co) duoc
dem va cong khai; nhanh do la doi chung dai so, khong la mo hinh vat ly.

Nhanh mo ta H_path co clip cho thay mot gioi han quan trong hon du kien:

```text
poisson@0.925: path clip ratio = 0.000000 -> flip = 0.000000
poisson@0.850: path clip ratio = 0.683163 -> flip = 0.333466
h2@0.700     : path clip ratio = 0.000000 -> flip = 0.000000
```

Bat bien chi co quyen ap dung vat ly neu `loss_p + r >= 0` tren moi row/path.
Dieu kien nay do truc tiep bang `path_clip_ratio == 0`, khong duoc gia dinh.

Con so `33.35%` **khong phai ket qua ve mang**. No la scope flag: tai
`poisson@0.850`, residual tuyet doi do o `rho=0.925` lon hon loss nen tren
68.3% evaluation va mo hinh residual da mat hieu luc truoc khi doc flip.

## 5. S8 -- residual tuyet doi bi ap ngoai diem do

Tai sinh tu raw B/C seeds 104..108 cho:

| mode | rho do | loss B ghep | residual tuyet doi | residual tuong doi |
|---|---:|---:|---:|---:|
| poisson | 0.925 | 0.0603007 | -0.0099371 | -0.164744 |
| h2 | 0.925 | 0.1426483 | -0.0094782 | -0.066384 |

Con so poisson tuyet doi khop artifact 8-seed `-0.009521786` trong sai so da
khoa. Nhan cua record da sua thanh **chenh lech ton that**; `w_loss` khong
tham gia tinh no. Schema residual v2 bat buoc ghi `rho_bar_measured`,
`baseline_magnitude`, `relative_point` va `valid_range`.

S8 la nguyen nhan: mot residual tuyet doi do tai mot diem khong the ngoai suy
qua dai co loss nen thay doi nhieu bac do lon. S7/clipping la trieu chung va
`clip_ratio` la detector validity.

## 6. Audit tuong doi M-27..M-30

Mo hinh hop le ve mien duoc khoa trong Amendment 35:

```text
loss'_p = loss_p * (1 + r_rel)
```

No khong cho bat bien argmin mien phi, vi delay khong bi nhan. Do do flip van
duoc do. Ket qua tai point:

| cell | abs(r_abs)/q01(min loss) | r_rel ap dung | flip test | clip ratio | M-27 | M-29 | M-30 |
|---|---:|---:|---:|---:|:--:|:--:|:--:|
| poisson@0.925 | 0.508794 | -0.164744 | 0.010105 | 0.000000 | HIT | HIT | PASS |
| poisson@0.850 | 2.518008 | -0.164744 | 0.026426 | 0.000000 | HIT | HIT | PASS |
| h2@0.700 | 0.615396 | -0.066384 | 0.004166 | 0.000000 | mo ta | HIT | PASS |

Amendment 37 dinh chinh estimand M-28 thanh **mean-of-ratios** tren tung
seed: poisson `r_rel=-0.164744` nam trong `[-0.20,-0.12]`. Gia tri
`-0.164793` truoc day la **ratio-of-means** va duoc giu nhu chan doan, khong
con la gia tri cham M-28. Ca hai van cho cung verdict HIT.

M-30 bang 0 chinh xac ca ba cell. M-29 HIT 3/3 va cho thay phep nhan vat ly
van co the doi argmin 0.42--2.64%; day la hieu ung hop le de do, khac artifact
clipping 13--25% cua phep cong sai scope.

## 7. Erratum cho Lesson 23.7 [C]

Rut phat bieu cu rang pooled common residual cho thay "khong co kich ban an
toan" hoac tu no dao dau ket luan 23.6. Phep bom cu da:

```text
(1) ha residual tu per_path xuong per_link;
(2) ap mot trung binh len tung row/action;
(3) clip loss tai 0;
(4) tao ra differential shift ma artifact goc khong do.
(5) ngoai suy residual tuyet doi tu rho=0.925 sang cell khac (S8).
```

Ket luan co du bang chung sau audit:

```text
Phan common-mode khong clip: khong doi xep hang (do duoc 0 chinh xac).
Phi tuyen ghep loss per-link: tac dong rat nho (0.0290% tren cell chinh).
Clipping sau tai phan bo: co che chi phoi cua 21.2960% flip cu (99.86%).
```

## 8. L10 van mo va pilot bi ha cap

Audit nay sua S7 bang code, nhung khong dong L10. Artifact cascade hien tai
chi cho mot pooled residual theo mode, khong cho `r_P1 - r_P3` tren cung
traffic/seed. Phep do can tiep theo van la chien dich Mininet vi sai:

```text
r_p = end-to-end_p - composed-links_p, p in {P1, P3}
estimand quyet dinh = r_P1 - r_P3
```

Campaign 23-34 da dung sau 43 row gate-clean va duoc ghi la **PILOT PRE-S8**;
khong row nao duoc dung de dong L10. Thiet ke tiep theo phai do
`P1/P3 x rho={0.850,0.925} x seed=101..108`, uoc luong `r_rel` theo path/load,
va co doi chung tai lap residual cu tai rho=0.925.

Cho den khi campaign do hoan tat, khong duoc noi xep hang an toan truoc
residual **vi sai**.

## 9. Kiem thu va provenance

Artifact S7 va S8 duoc tai sinh sau Amendment 35. Bo test truc tiep gom schema,
raw replay, invariant, held-out scoring va domain control; ket qua chay duoc
ghi cung commit ket qua, khong ke thua con so test cu cua 23.7-bis.
