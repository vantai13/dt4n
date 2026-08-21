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

## 3. Cham prereg M-23..M-26

| ID | Gia tri do duoc | Dai khoa | KQ |
|---|---:|---:|:--:|
| M-23 | H_path = 0.000000 tai 9/9 diem cell-endpoint | = 0 chinh xac | PASS [TAT DINH] |
| M-24 | H_link0@point = 0.000290 | 0.000--0.020 | HIT |
| M-25 | clip_share@point = 0.998638 | > 0.90 | HIT |
| M-26 | H_link1@point = 0.212960 | abs(value - 0.2130) < 0.005 | PASS |

Kich ban khoa truoc: **A**. M-23 va M-26 la kiem tra bat bien/doi chung,
khong duoc tinh nhu prediction-hit khoa hoc.

## 4. Dinh ly dung va gioi han cua no

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

Vi vay cau tong quat dung la:

> Common shift triet tieu trong argmin chi khi no van la common shift sau moi
> phep bien doi. Clipping o bat ky tang nao co the lam shift phu thuoc
> row/action va che tao thanh phan vi sai.

Con so `33.35%` khong duoc dien giai la tac dong vat ly that. Residual hien
tai la mot **trung binh per-path**; no khong do residual theo tung row va tung
duong, nen khong cap quyen ap cung mot so am vao moi row roi clip. Nhanh nay
chi chung minh rang rang buoc mien la mot nguon vi sai tiem tang phai duoc do,
khong duoc tu che.

## 5. Erratum cho Lesson 23.7 [C]

Rut phat bieu cu rang pooled common residual cho thay "khong co kich ban an
toan" hoac tu no dao dau ket luan 23.6. Phep bom cu da:

```text
(1) ha residual tu per_path xuong per_link;
(2) ap mot trung binh len tung row/action;
(3) clip loss tai 0;
(4) tao ra differential shift ma artifact goc khong do.
```

Ket luan co du bang chung sau audit:

```text
Phan common-mode khong clip: khong doi xep hang (do duoc 0 chinh xac).
Phi tuyen ghep loss per-link: tac dong rat nho (0.0290% tren cell chinh).
Clipping sau tai phan bo: co che chi phoi cua 21.2960% flip cu (99.86%).
```

## 6. L10 van mo

Audit nay sua S7 bang code, nhung khong dong L10. Artifact cascade hien tai
chi cho mot pooled residual theo mode, khong cho `r_P1 - r_P3` tren cung
traffic/seed. Phep do can tiep theo van la chien dich Mininet vi sai:

```text
r_p = end-to-end_p - composed-links_p, p in {P1, P3}
estimand quyet dinh = r_P1 - r_P3
```

Cho den khi phep do do chay, khong duoc noi xep hang an toan truoc residual
**vi sai**. Cung khong duoc dung nhanh H_path co clip o muc 4 thay cho phep do
vi sai truc tiep.

## 7. Kiem thu va provenance

Artifacts duoc tai sinh tu source commit `fd9b804`, voi `git_dirty=false`.

```text
test/test_phase23_residual_level.py                         8 passed
phase20r6_band + phase20r7_mechanism + phase23 structure  70 passed
phase23 gate ledger + prereg                              28 passed, 1 skipped
toan bo suite nhanh, loai slow/live                       995 passed, 2 skipped,
                                                          8 deselected (14m21s)
```

Mot virtualenv cuc bo `.venv/` duoc tao de chay vi interpreter Homebrew mac
dinh khong co pytest/numpy/pandas/pyarrow; thu muc nay da nam trong `.gitignore`
va khong tham gia artifact/provenance.
