# 16 -- Lesson 23.15: xac nhan tam cell

Prereg: `docs/phase-23/00zp-amendment-39.md` tai tag
`lesson-23.15-pre` (`b453703`)  
Runner: `cert/eight_cell_sweep.py` (`03e354e`)  
Artifact: `results/phase-23/eight_cell_sweep.json`  
Figures: `results/phase-23/fig1_lift_vs_swing_8cells.png`,
`results/phase-23/fig2_objective_eight_cells.png`

## 1. Doc lai theo vung song cua bai toan

Sap xep theo `err_neo=P(a_twin != a_star)` cho thay mot khoang tach roi:

| Cell | err_neo | swing | lift | lift-swing | Delta @1 | Phan tang |
|---|---:|---:|---:|---:|---:|---|
| poisson@0.700 | 0.000000 | +0.000000 | 0.000000 | +0.000000 | +0.000000 | chet |
| h2@0.925 | 0.000238 | +0.000000 | 0.000000 | +0.000000 | +0.000000 | chet |
| h2@0.960 | 0.000524 | +0.000000 | 0.000000 | +0.000000 | +0.000000 | chet |
| h2@0.850 | 0.002944 | -0.000316 | 0.001120 | +0.001436 | -0.000316 | chet |
| h2@0.700 | 0.126536 | +0.030918 | 0.013344 | -0.017574 | +0.003866 | song, hai |
| poisson@0.960 | 0.199493 | +0.100035 | 0.122909 | +0.022874 | -0.005032 | song, loi |
| poisson@0.850 | 0.220727 | +0.124442 | 0.110259 | -0.014183 | +0.003120 | song, hai |
| poisson@0.925 | 0.222399 | +0.117878 | 0.176372 | +0.058495 | -0.012869 | song, loi |

Cell chet cao nhat co `err_neo=0.002944`; cell song thap nhat co
`err_neo=0.126536`, tach nhau `43.0x`. Moi nguong trong `[0.005,0.12]` tao
cung mot phan hoach. Nguong `0.05` va ten goi song/chet la readout hau
nghiem cua Lesson 23.15, khong phai phan tang da preregister cho artifact nay.

`poisson@0.960` la cell giu kin dau tien vua khong suy bien vua co
`lift>swing` va `Delta<0`. Day la xac nhan ngoai mau dau tien cho huong cua
ket qua he thong, khac voi ba cell `Delta=0` khong co bai toan de cai thien.

Tren truc Poisson da do, dau doi giua `rho_bar=0.850` va `0.925`:

```text
rho_bar       0.700       0.850       0.925       0.960
lift-swing   +0.000000   -0.014183   +0.058495   +0.022874
Delta        +0.000000   +0.003120   -0.012869   -0.005032
```

Vi `Delta=reject_share*(swing-lift)`, bien quan sat duoc nam trong khoang
`(0.850,0.925)`. Day moi la bracket bon diem; chua duoc noi suy thanh mot
`rho_star` cho den khi co luoi preregister day hon.

## 2. Hai co che suy bien o hai dau

Bang sau cham truth-table tai vector tai hang `rho=rho_bar`, voi `w_loss`
lay tu SLA artifact cua tung cell. Day khong phai trung binh cost tren chuoi
AR(1):

| Mode | rho | P1 | P2 | P3 | P4 | P3-P1 | margin p10 AR(1) |
|---|---:|---:|---:|---:|---:|---:|---:|
| poisson | 0.700 | 15.4 | 18.8 | 17.3 | 17.7 | 1.89 | 0.365 |
| poisson | 0.850 | 29.4 | 45.2 | 35.4 | 40.0 | 6.05 | 1.405 |
| poisson | 0.925 | 94.0 | 136.2 | 113.5 | 131.5 | 19.54 | 3.585 |
| poisson | 0.960 | 194.0 | 254.0 | 223.2 | 250.7 | 29.19 | 3.902 |
| h2 | 0.700 | 71.1 | 124.8 | 94.1 | 115.5 | 23.04 | 3.801 |
| h2 | 0.850 | 446.5 | 599.4 | 519.7 | 590.0 | 73.24 | 14.443 |
| h2 | 0.925 | 846.2 | 1030.2 | 938.2 | 1026.4 | 91.91 | 27.753 |
| h2 | 0.960 | 1076.9 | 1268.0 | 1173.1 | 1265.3 | 96.18 | 75.465 |

O dau tai thap `poisson@0.700`, loss gan 0 va chi phi gan nhu delay tinh;
topology khoa thu hang nen twin luon dung. O dau tai cao burst H2, thanh
phan loss va `w_loss` lon lam P1 thong tri cau truc; dao dong rho khong du
lat thu hang. Vung giua la noi delay va loss canh tranh, thu hang co the doi,
va bai toan quyet dinh moi co noi dung.

Day la S11: moi danh gia selective/certified decision phai khai bao vung
song cua bai toan; ngoai vung do, `Delta=0` la suy bien cua bai toan, khong
la bang chung thanh cong hay that bai cua phuong phap.

## 3. Bien phan tang va sua cach doc MISS

`err_neo` khong dung C3, `q_hat`, `kappa`, fallback hay `Delta`; no chi dung
twin va truth table de do bai toan co sai so quyet dinh ban dau hay khong.
Do do no co the duoc tinh truoc thi nghiem certificate va dung lam bien phan
tang tien nghiem trong mot lesson tuong lai. Tuy nhien nguong `0.05` duoc
phat hien sau khi nhin Lesson 23.15, nen moi phep cham theo nguong nay phai
duoc preregister moi, khong duoc sua hoi to M-47/M-48.

M-47 van la MISS: tieu chi `<0` tron `Delta=0` (khong co hieu ung) voi
`Delta>0` (hieu ung nguoc). Day la loi thiet ke dải du doan vi khong co dieu
kien tien de khong suy bien, khong phai bang chung rang ba cell `Delta=0`
bi lam xau. NT48: tieu chi phan quyet tren dai luong co the suy bien ve 0
phai tach `<=0` khoi dieu kien tien de xac dinh vung song.

M-48 cung giu MISS tren 8 cell vi mau so 0. Readout mo ta tren bon cell song:

```text
twin_deg  min=0.224443 max=0.237723 spread=1.059170x
prior_deg min=0.054576 max=0.224379 spread=4.111317x
```

No cho thay chuan doan S9 van dung khi mo rong tu ba len bon cell song, gom
cell giu kin `poisson@0.960`. Gia tri `1.059` la tai tinh hau nghiem, khong
tinh prediction-hit; M-48b chi duoc dat ten va cham trong amendment sau.

## 4. Objective confirmation theo tieu chi da khoa

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

## 5. Cham M-46..M-52

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

## 6. Lift--swing tren du 8 cell

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

## 7. Policy capacity va selection-vs-default

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

## 8. Controls va provenance

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

## 9. Ket luan paper

Lesson 23.15 bac bo phat bieu "co mot exchange-rate threshold chung tao cai
thien nghiem ngat tren moi gate cell". Dong thoi no cung cap mot xac nhan
ngoai mau co noi dung tai `poisson@0.960`. Ket qua manh hon con lai la:

1. dau Delta tiep tuc khop chinh xac can bang lift--swing;
2. policy capacity F6 nho hon nhieu so voi 16 o danh nghia;
3. cac cell moi tach thanh hai cell co loi o moi ratio va ba cell suy bien;
4. selection trung binh khong xau hon F2, nhung loi selection rieng le van co.
5. `err_neo` tao mot phan hoach song/chet co separation gap `43.0x` va can
   duoc kiem chung tien nghiem trong lesson tiep theo.

Khong ket qua nao o day dong L10 residual P1-P3, khoi dong Mininet, hay mo
scope AoI.
