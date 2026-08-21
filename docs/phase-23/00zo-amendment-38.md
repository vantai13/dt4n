# AMENDMENT 23-38 -- Lesson 23.14: quet fallback, xac dinh nut co chai

Ngay: 2026-08-21
Trang thai: **SAU BUOC A TAI PHAN TICH ARTIFACT 15/08; TRUOC KHI VIET
`cert/fallback_sweep.py`, TRUOC KHI CHAY, VA TRUOC KHI NHIN SO FALLBACK.**

## 1. Ly do va S9

Phan ra lift theo cell tu `g23_23_lift_law.json` khong do gi moi:

```text
twin_deg  spread max/min = 1.029x
prior_deg spread max/min = 4.111x
```

Nut co chai cross-cell la fallback, khong phai kha nang cua certificate trong
viec loc ra hang twin kho. Phat bieu Lesson 23.1 "khoan phat cua P1 gan nhu
hang so" dung theo truc `kappa` trong `poisson@0.925`, nhung khong phai bat
bien theo truc cell. Day la S9: bat bien chi co gia tri tren truc da do.

## 2. Dai khoa M-40..M-45

| ID | Dai luong (thang / muc / tap hang) | Nhan | Dai khoa |
|---|---|---|---|
| M-40 | `prior_deg` spread max/min qua 3 cell, C3, error fraction / reject | [TAT DINH] | `3.0 .. 6.0` |
| M-41 | `twin_deg` spread max/min qua 3 cell, C3 | [TAT DINH] | `1.00 .. 1.15` |
| M-42 | fallback duoc chon chi bang calibration: `err_F|reject-c*`, `poisson@0.850` | [NGOAI SUY] | `-0.05 .. 0.00` |
| M-43 | fallback duoc chon chi bang calibration: `err_F|reject-c*`, `h2@0.700` | [NGOAI SUY] | `-0.05 .. 0.00` |
| M-44 | F thang o ca hai cell held-out thuoc cung mot ho F | [CO CHE] | CO |
| M-45 | `Delta(C3,F_selected)<0` tren ca ba cell | [NGOAI SUY] | CO |

M-40/M-41 la tai tinh tu artifact da cong bo, khong tinh prediction-hit.
Neu M-45 fail, khong retune. Bao cao ket qua am va chuyen headline sang ket
qua transfer C3-B2: `+0.000116 / -0.001544 / -0.003638`.

## 3. Ho fallback preregistered

```text
F2   : luon P1
F2b  : luon P3
F2c  : mot path hang so; path chon bang calibration
F4   : runner-up cua argmin twin tai row
F5   : hon hop 50/50 top-1/top-2 cua twin; tinh expected error chinh xac,
       khong boc tham Monte Carlo
F6   : path hang so theo o (z_bin, m_hat_bin); action map chon bang calibration
```

Tie-break cho F2c/F6 la chi so path nho nhat. F6 chi duoc nhin `z_bin` va
`m_hat_bin` da co trong cong. No khong duoc doc vector `y_hat`, `a_twin`,
ground truth test, hoac bat ky cot tuong lai nao tai row scoring.

## 4. NC-A -- selection leakage va seed-disjoint cross-fitting

Ca **tham so policy** lan **lua chon ho F headline** phai dua tren calibration,
khong tren test. De ep tach seed ma van cham toan bo rowset test goc, dung
leave-one-seed-out cross-fitting tren seeds `101..105`:

```text
scoring rows seed=s : original test rows cua seed s
selection rows      : original calibration rows cua bon seed != s
```

Voi moi fold, F2c/F6 duoc fit lai va ho headline duoc chon bang conditional
calibration error. Ket qua test nam ngoai ca row indices va seed IDs da thay.
Artifact bat buoc ghi `indices_seen`, `seeds_seen`, `scoring_seed` va kiem tra
giao rong. Oracle minimum tren test (neu bao cao) chi la chan doan, tuyet doi
khong duoc dung cham M-42..M-45.

## 5. NC-B -- gioi han thong tin cua F6

Action map F6 duoc hoc tu `(z_bin,m_hat_bin,a_star)` tren selection-calibration.
Khi score, ham F6 chi nhan hai bin va map da dong bang. Test phai dung proxy
cam truy cap `y_hat`/`a_star` scoring; bat ky truy cap nao lam audit dung.

## 6. NC-C -- tai lap F2 legacy

Tren full original test rowset, voi F2 always-P1, pipeline moi phai tai lap:

```text
poisson@0.925 : Delta = -0.0128688493440567
poisson@0.850 : Delta = +0.0031202059335916
h2@0.700      : Delta = +0.0038662551728414
tolerance     : 1e-12
```

Sai mot cell thi dung truoc khi doc fallback moi.

## 7. Cach chon va cham

Trong moi cross-fit fold, tinh calibration proxy risk tren tap calibration ma
cong C3 danh dau kho theo cung score/ranking rule. Chon ho co risk nho nhat;
tie-break theo thu tu prereg `F2,F2b,F2c,F4,F5,F6`. Sau do score dung ho do
tren test rows cua seed giu ra. Noi nam fold thanh estimate chinh.

M-42/M-43 dung policy da chon calibration, khong dung `min` hau kiem tren
test. M-44 bao cao them moi ho prereg co `err_F|reject<c*` tren ca hai held-out
cell; verdict CO neu ton tai it nhat mot ho chung. M-45 dung policy headline
calibration-selected cua tung cell.

## 8. Quet objective misspecification sau fallback sweep

Sau khi artifact fallback da khoa, quet mo ta:

```text
w_eff / w_loss = 0.5, 0.6, ..., 1.5
cells          = poisson@0.925, poisson@0.850, h2@0.700
```

Tai moi diem, dong bang `y_hat`, C3 `accept_set`, bin definitions, ho fallback
va action maps da fit o objective goc. Chi `a_star`/error duoc cham lai bang
truth cost tai `w_eff`. Khong refit theo tung diem. Danh dau them diem do:

```text
poisson ratio = 1 - 0.164744220 = 0.835255780
h2 ratio      = 1 - 0.066384422 = 0.933615578
```

Day la robustness curve/descriptive Figure 2, khong co prediction range moi.
Output:

```text
results/phase-23/fallback_sweep.json
results/phase-23/objective_misspecification_sweep.json
results/phase-23/fig2_objective_misspecification.png
docs/phase-23/15-fallback-and-objective-robustness.md
```
