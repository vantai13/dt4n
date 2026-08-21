# AMENDMENT 23-36 -- Campaign P1/P3 x load: dong S8 va L10

Ngay: 2026-08-21
Trang thai: **SAU KHI S8 AUDIT COMMIT d8d7f64; TRUOC KHI SUA ANALYZER
CAMPAIGN, TRUOC KHI CHAY MININET MOI, VA TRUOC KHI DOC KET QUA.**

## 1. Cau hoi va estimand

Voi moi path/load/seed, do nhom B (ba link) va C (end-to-end):

```text
B_loss       = 1 - product_i(1 - loss_B_i)
r_abs        = C_loss - B_loss
r_rel        = r_abs / B_loss
```

Ba cau hoi doc lap:

```text
Q1/S8 : r_rel(path, 0.850) / r_rel(path, 0.925) co on dinh?
Q2/L10: residual vi sai P1/P3 co nho hon khe chi phi?
Q3/NC : topology tandem cu tai 0.925 co tai lap residual -0.0095?
```

Loss la loss cua Poisson fixed-count probe 1470 B tren nen Poisson; `w_loss`
chi doi loss differential sang ms o Q2, khong tham gia uoc luong `r_rel`.

## 2. Grid va ngan sach live

Primary:

```text
path     = P1=(uA,ac,vC), P3=(uB,bc,vC)
rho_bar  = 0.850, 0.925
mode     = poisson
seed     = 101..108
```

Tong primary `2 x 2 x 8 = 32` nhom paired. Moi nhom co 3 B rows va 1 C row,
nen 128 live points.

Q3 khong the dung P1 thay cho topology cu: tandem goc la `(uA,ac,ad)`, trong
khi P1 la `(uA,ac,vC)`. De tai lap dung nghia, chay them 8 nhom control tren
T123 cu tai rho=0.925, seed 101..108 (32 live points). Tong campaign 160 diem.

Moi point: duration 70 s, warmup 10 s, payload 1470 B, carve-out 0.25,
point-timeout 180 s. Day la cau hinh cua phep do cascade goc; khong dung
duration 30 s cua pilot pre-S8.

## 3. Pairing va validity

B/C bat buoc trung schedule digest tren tung link, mode/rho/seed, payload,
probe policy va path spec. Moi row phai gate-clean theo Amendment 34 muc 3.
Thieu row, trung key, path proof sai, B/C digest lech hoac w_loss lech thi
analyzer dung; khong dien bang gia tri pooled.

CI90 dung paired bootstrap seed, 10,000 lan, RNG `20260821`. Q1 dung cung
bootstrap index cho hai load; Q2 dung cung index cho P1/P3.

## 4. M-31..M-33 khoa

| ID | Dai luong | Nhan | Dai khoa |
|---|---|---|---|
| M-31 | `mean(r_rel@0.850)/mean(r_rel@0.925)`, tung path, poisson, paired seed 101..108 | [CO CHE] | `0.7 .. 1.4` cho ca P1 va P3 |
| M-32 | safety bao thu tai rho=0.925: `q95_row(w*abs(loss_P1*rrel_P1-loss_P3*rrel_P3)) / q05_row(abs(cost_P1-cost_P3))`; cham bang upper CI90 bootstrap | [NGOAI SUY] | `< 1.0` |
| M-33 | point residual loss moi cua T123@0.925 nam trong CI90 goc `[-0.0101350818,-0.0089084907]` | [DOI CHUNG] | CO |

M-31 ngoai dai o mot path: S8 khong dong tren dai, paper phai thu hep scope
hoac dung residual theo tung cell. M-32 fail: L10 cho xep hang P1/P3 khong
dong, bao cao ket qua am. M-33 fail: dung dien giai M-31/M-32 va dieu tra drift.

Q2 dung `q95/q05` de khong che giau duoi trung binh. Neu `cost_P1=cost_P3`
tao q05=0 thi safety la vo han va M-32 fail, khong duoc bo row.

## 5. Output

```text
results/phase-23/relative_differential_campaign.json
results/phase-23/differential_live_v2/*.json
results/phase-23/raw_differential_v2/       # local, ignored
```

Khong sua `G23-43..48`: dinh nghia Lesson 23.8 van khong co trong repo.
