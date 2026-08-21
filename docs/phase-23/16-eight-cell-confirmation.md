# 16 -- Lesson 23.15: xac nhan tam cell

Prereg: `docs/phase-23/00zp-amendment-39.md` tai tag
`lesson-23.15-pre` (`b453703`)  
Runner: `cert/eight_cell_sweep.py` (`03e354e`)  
Artifact: `results/phase-23/eight_cell_sweep.json`  
Figures: `results/phase-23/fig1_lift_vs_swing_8cells.png`,
`results/phase-23/fig2_objective_eight_cells.png`

## 1. Ket qua headline

Nam cell confirmation khong xac nhan bien objective hau nghiem theo tieu chi
nghiem ngat `Delta<0`. Ba cell suy bien co `Delta=0` tren toan bo 21 diem
ratio, nen `r_cross` chung khong ton tai:

| Cell moi | Delta F2 @1 | Delta selected @1 | Delta @r=0.835256 | So diem am / 21 |
|---|---:|---:|---:|---:|
| poisson@0.700 | +0.000000 | +0.000000 | +0.000000 | 0 |
| poisson@0.960 | -0.005032 | -0.005032 | -0.007254 | 21 |
| h2@0.850 | -0.000316 | -0.000316 | -0.000324 | 21 |
| h2@0.925 | +0.000000 | +0.000000 | +0.000000 | 0 |
| h2@0.960 | +0.000000 | +0.000000 | +0.000000 | 0 |

Do do M-46 va M-47 la MISS. Readout `r~0.867` van chi duoc phep o
Discussion; no khong duoc doi thanh bien objective da xac nhan. Mot readout
mo ta phu la khong cell moi nao co `Delta>0` tai ratio xac nhan, nhung
`non-inferior` khong phai estimand da khoa va khong duoc cham thanh HIT.

## 2. Cham M-46..M-52

| ID | Gia tri | Dai khoa | KQ |
|---|---:|---:|:--:|
| M-46 common `r_cross`, 5 cell moi | khong ton tai | 0.80--0.95 | MISS |
| M-47 `Delta(0.835256)<0`, 5/5 | 2/5 | CO | MISS |
| M-48 twin_deg spread, 8 cell | vo han (`min=0`) | 1.00--1.30 | MISS |
| M-49 prior_deg spread, 8 cell | vo han (`min=0`) | >3 | HIT [SUY BIEN] |
| M-50 identity dau | 8/8 | 8/8 | HIT [DINH LY] |
| M-51 mean F6 reject-bin nonempty | 5.25 | 4--8 | HIT |
| M-52 mean `(Delta_selected-Delta_F2)` | -0.000114508 | <=0 | HIT |

M-48 khong that bai vi spread lon huu han ma vi mau so `twin_deg=0` o
`poisson@0.700`. Tuong tu, M-49 dat theo nghia ty so vo han; day la HIT do
suy bien va khong nen dien giai nhu mot uoc luong spread huu han tot.

## 3. Lift--swing tren du 8 cell

| Cell | twin_deg | prior_deg | lift | swing | Delta F2 |
|---|---:|---:|---:|---:|---:|
| poisson@0.925 | 0.230948 | 0.054576 | 0.176372 | 0.117878 | -0.012869 |
| poisson@0.850 | 0.235830 | 0.125570 | 0.110259 | 0.124442 | +0.003120 |
| h2@0.700 | 0.237723 | 0.224379 | 0.013344 | 0.030918 | +0.003866 |
| poisson@0.700 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | +0.000000 |
| poisson@0.960 | 0.224443 | 0.101534 | 0.122909 | 0.100035 | -0.005032 |
| h2@0.850 | 0.010220 | 0.009100 | 0.001120 | -0.000316 | -0.000316 |
| h2@0.925 | 0.000844 | 0.000844 | 0.000000 | 0.000000 | +0.000000 |
| h2@0.960 | 0.001858 | 0.001858 | 0.000000 | 0.000000 | +0.000000 |

Dong nhat

```text
Delta = reject_share * (swing - lift)
```

dung tren 8/8 cell voi residual toi da duoi `1e-12`. Ba diem tai goc cho
thay mien mo rong gom ca cell khong co tin hieu he thong de cai thien, thay
vi mot truc swing lien tuc. Day la ly do khong duoc khoi phuc ke hoach sua
topology hau kiem.

## 4. Policy capacity va selection-vs-default

F6 co trung binh `5.25/16` reject-bin nonempty qua 40 fold. Bay cell co
trung binh 5 bin; `poisson@0.700` co 7 bin. Calibration chon F2 o toan bo
fold cua nam cell moi, nen selection khong thay doi ket qua cua chung.

Tren du 8 cell, chi hai cell cu co selection khac/anh huong so voi F2:

```text
poisson@0.850 : +0.000334  (selection lam xau)
h2@0.700      : -0.001250  (selection cai thien)
6 cell con lai: 0
mean 8 cell   : -0.000114508
```

M-52 dat, nhung bang chung van phu hop voi S10: mot mean am nho khong xoa
winner's curse da quan sat tai `poisson@0.850`.

## 5. Controls va provenance

```text
NC-D old-cell F2 parity max abs gap : 0.0       PASS
NC-E row/seed leakage + identity    : true      PASS
NC-F w_loss source                  : sla_calibration.json PASS
Objective ratio=1 parity max gap    : <=1e-12   PASS
Golden tests                        : 6 passed
Runner code commit                 : 03e354e
Artifact git_dirty                  : false
```

Nam calib-set report deu co `fail=[]`, V23 SLA path controls PASS va parity
Phase 20R co sai so toi da 0. Campaign Mininet Amendment 36 van tam dung o
5 row; Lesson 23.15 khong dung live data. Artifact AoI van chua duoc doc.

## 6. Ket luan paper

Lesson 23.15 bac bo phat bieu "co mot exchange-rate threshold chung tao cai
thien nghiem ngat tren moi gate cell". Ket qua manh hon con lai la chan doan:

1. dau Delta tiep tuc khop chinh xac can bang lift--swing;
2. policy capacity F6 nho hon nhieu so voi 16 o danh nghia;
3. cac cell moi tach thanh hai cell co loi o moi ratio va ba cell suy bien;
4. selection trung binh khong xau hon F2, nhung loi selection rieng le van co.

Khong ket qua nao o day dong L10 residual P1-P3, khoi dong Mininet, hay mo
scope AoI.
