# AMENDMENT 3 -- Phase 21R

Ngay ky: 2026-08-12
Nguoi ky: Codex theo yeu cau owner repo DT4N
Boi canh: sau khi chay `cert/decomposition.py`.
CHUA tinh `q_hat`, CHUA tinh bat ky ti le accept nao.

## C1. Ghi nhan du doan truot #2: z_cross

```text
tien dang ky : z_cross in [0.05, 0.10] s
do duoc      : z_cross(margin,cost) = 0.007085 s
ket qua      : TRUOT -- thap hon can duoi 7.06 lan
```

Chan doan: day la loi khop thang do, khong phai loi tinh toan.

Co so du doan trong Lesson 0 lay tu artifact Phase 20R:

```text
rms_e_model = 0.3055 co dinh
rms_e_stale = 0.2475 @ z=0.05 -> 0.7278 @ z=0.55
```

Nhung cac cot do la muc DUONG, kenh DELAY. Dai luong Phase 21R chung nhan la
muc BIEN, thang COST.

Bon gia tri `z_cross` cho `poisson@0.925`:

| Level | Delay channel | Cost channel |
|---|---:|---:|
| path | 0.077421 s | 0.017050 s |
| margin | 0.008346 s | 0.007085 s |

Du doan `[0.05, 0.10]` trung cho `z_cross(path,delay)`, nhung truot cho
`z_cross(margin,cost)`. Tu nay khong ghi tran "z_cross = X"; moi so phai kem
nhan `(level, channel)`.

Quy tac bat buoc khi lay so tu artifact cu:

```text
1. THANG   : delay / cost / chuan hoa
2. MUC     : per-link / per-path / margin
3. TAP HANG: cua so chung nao, z nao, seed nao
```

Neu artifact khong ghi du ba nhan, do la loi tai lieu va phai bo sung.

## C2. Bao truoc du doan truot #3: q_hat

```text
tien dang ky : q_hat(B1) in [1.5, 2.2] ms ; q_hat(B4) in [2.0, 3.0] ms
du kien do   : q_hat(B1) ~ 11.4 ms ; q_hat(B4) ~ 23.9 ms
ket qua      : [ ] cho Lesson 21R.5 xac nhan
```

Co so du doan sua lai, nhan `REVISED`: day la bang chung yeu hon du doan goc
vi duoc viet sau khi da thay du lieu trung gian.

`rms_total` o muc BIEN, thang COST, cell `poisson@0.925`:

```text
z=0.055 ->  6.044955 ms
z=0.075 ->  6.911603 ms
z=0.100 ->  7.845685 ms
z=0.150 ->  9.388458 ms
z=0.200 -> 10.653855 ms
z=0.300 -> 12.639341 ms
z=0.400 -> 14.206729 ms
z=0.550 -> 16.054032 ms
```

Neu `s_margin` xap xi chuan, `q90(|s|) ~= 1.645 * rms`:

| Bin | z dai dien | rms_total | q_hat REVISED |
|---|---:|---:|---:|
| B1 | 0.075 s | 6.912 ms | 11.37 ms |
| B2 | 0.150 s | 9.388 ms | 15.44 ms |
| B3 | 0.250 s | 11.647 ms | 19.15 ms |
| B4 | 0.425 s | 14.515 ms | 23.88 ms |

He qua cho cac gate: ti so `q_hat(B4)/q_hat(B1) ~= 2.10`, nen H2 co ve de
dat hon du doan ban dau. `q_hat` nam khoang 11-24 ms, cung cap rui ro moi cho
H7: duong cong co du huu ich khong. Khong sua nguong gate nao trong amendment
nay.

## C3. San nhieu do luong cua e_model

Cho cell chinh `poisson@0.925`:

```text
rms_e_model observed (margin,cost) = 2.141802 ms
measurement noise floor            = 1.485100 ms
rms_model_true net of noise         = 1.543306 ms
noise variance share               = 48.08%
```

Phat bieu bat buoc: `e_model` do duoc bao gom nhieu lay mau cua campaign do
truth table. Neu muon tach `e_model` that ro hon, can tang goi do tren moi o
cua bang chan ly; chi doi mo hinh khong xoa duoc san nhieu nay. De ha ti trong
nhieu tu 48.08% xuong 10%, can tang `n_pkt` khoang 8.3 lan neu cac thanh phan
khac giu nguyen.

## C4. Thu tu uu tien dau tu

Cell chinh `poisson@0.925`, muc BIEN, thang COST:

```text
AoI hien tai xap xi 0.3025 s  -> rms_total ~ 12.68 ms
AoI san vat ly 0.055 s        -> rms_total =  6.04 ms
dong bo tuc thi z -> 0        -> rms_e_model observed = 2.14 ms
model true net of noise       -> 1.54 ms
```

`z_cross(margin,cost) = 0.007085 s` nam duoi san vat ly `d_sync = 0.051 s`.
Tren toan bo dai AoI dat duoc trong he nay, do cu chi phoi mo hinh; dau tu
dong bo nhanh hon co ich cho toi khi cham san vat ly.

## C5. Corr(e_model, e_stale) doi dau theo che do

Tai `z=0.550`, muc BIEN, thang COST:

| Cell | corr(e_model,e_stale) | Huong |
|---|---:|---|
| poisson@0.925 | -0.411349 | am |
| poisson@0.850 | +0.466155 | duong |
| h2@0.700 | -0.105294 | am |
| cbr@0.700 | +0.034951 | gan 0 |

Khong duoc gia dinh dau cua hiep phuong sai. Bao cao RMS tong phai dung:

```text
Var(total) = Var(e_model) + Var(e_stale) + 2 * Cov(e_model,e_stale)
```

## C6. Bo sung tai lieu Phase 20R

Da them `docs/phase-20R/99b-erratum-scale.md`. Noi dung chinh: cac cot
`rms_e_model`, `rms_e_stale`, `cov_e` trong artifact decision-error Phase 20R
la muc DUONG, kenh DELAY; chung khong phai thang COST va khong phai muc BIEN.
