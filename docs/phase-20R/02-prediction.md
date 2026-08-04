# DU DOAN TRUOC CHIEN DICH -- Phase 20R

Ngay ky: 2026-08-04
Git tag: phase-20R-prediction
BAT BUOC: file nay phai duoc COMMIT TRUOC commit dau tien cua Lesson 20R.4.

## 0. Vai Tro

Day khong phai phong doan. Day la ve thu nhat cua phep tru:

```text
err_do_that - err_du_doan = dong gop cua e_model
```

Du doan chay tren `link_model_v2` voi `y_true := f2(rho(t))`, tuc gia
vo mo hinh dung tuyet doi va chi con `e_staleness`.

## 1. Du Doan Chinh

```text
mode     rho_bar | z=0.05  z=0.10  z=0.20  z=0.30  z=0.55 | d_sla(0.55)
-----------------------------------------------------------------------------------
cbr      0.700   | 0.0000  0.0000  0.0000  0.0000  0.0000 | +0.0000   <- PC1
cbr      0.850   | 0.0000  0.0000  0.0000  0.0000  0.0000 | +0.0000   <- PC1
cbr      0.925   | 0.0000  0.0000  0.0000  0.0000  0.0000 | +0.0000   <- PC1
cbr      0.960   | 0.0000  0.0000  0.0000  0.0000  0.0000 | +0.0000   <- PC1
h2       0.700   | 0.1354  0.1880  0.2576  0.3055  0.3889 | +0.1459
h2       0.850   | 0.1111  0.1560  0.2121  0.2518  0.3235 | +0.1095
h2       0.925   | 0.0320  0.0448  0.0601  0.0706  0.0902 | +0.0228
h2       0.960   | 0.0003  0.0003  0.0003  0.0003  0.0003 | +0.0001
poisson  0.700   | 0.0578  0.0799  0.1072  0.1261  0.1594 | +0.0644
poisson  0.850   | 0.1536  0.2123  0.2891  0.3457  0.4364 | +0.1825
poisson  0.925   | 0.1355  0.1880  0.2580  0.3077  0.3928 | +0.1470
poisson  0.960   | 0.0864  0.1208  0.1680  0.2016  0.2622 | +0.0838
```

Tom tat gate tai `z = 0.55 s`: 5 o du doan qua G1+G2+G3.

```text
h2@0.700       err=0.3889 d_sla=+0.1459 spearman=1.000
h2@0.850       err=0.3235 d_sla=+0.1095 spearman=1.000
h2@0.925       err=0.0902 d_sla=+0.0228 spearman=1.000
h2@0.960       err=0.0003 d_sla=+0.0001 spearman=0.943
poisson@0.700  err=0.1594 d_sla=+0.0644 spearman=1.000
poisson@0.850  err=0.4364 d_sla=+0.1825 spearman=1.000
poisson@0.925  err=0.3928 d_sla=+0.1470 spearman=1.000
poisson@0.960  err=0.2622 d_sla=+0.0838 spearman=1.000
```

## 2. Du Doan e_model

Tu `link_model_v2_fit.json`: `e_model_thuan = sqrt(resid_sd^2 - sigma_schedule^2)`.

```text
poisson 0.058 - 0.078 ms/link   efficiency 0.941 - 0.969
h2      0.047 - 0.080 ms/link   efficiency 0.958 - 0.978
cbr     4.980 - 6.216 ms/link   efficiency 0.184 - 0.426  (vung tri han, da loai)
```

```text
mode     rho_bar | resid_sd/link | err(z=0) | err(0.55) no-model | err(0.55) with-model | ratio
------------------------------------------------------------------------------------------------
h2       0.700   |    0.2177    |  0.0048  |      0.3889        |       0.3892        | 0.01
h2       0.850   |    0.2177    |  0.0013  |      0.3235        |       0.3236        | 0.00
h2       0.925   |    0.2177    |  0.0007  |      0.0902        |       0.0898        | 0.01
h2       0.960   |    0.2177    |  0.0000  |      0.0003        |       0.0003        | 0.03
poisson  0.700   |    0.2556    |  0.0790  |      0.1594        |       0.1857        | 0.43
poisson  0.850   |    0.2556    |  0.0177  |      0.4364        |       0.4378        | 0.04
poisson  0.925   |    0.2556    |  0.0071  |      0.3928        |       0.3921        | 0.02
poisson  0.960   |    0.2556    |  0.0041  |      0.2622        |       0.2629        | 0.02
```

D1: `err(z=0)` se nam trong `[0.000, 0.10]` o moi o vao gate. Neu
do that cho `err(z=0) > 0.20`, dung va kiem tra thuoc do.

D2: `err(z=0)/err(0.55) < 0.50` o moi o vao gate, nen ky vong
`e_staleness` chi phoi va G3 pass.

D3: o nhay nhat voi e_model la o co ti so lon nhat trong bang tren;
neu do that khac, cap nhat case study 21R bang amendment.

## 3. H6 -- Dinh Luat Ti Le

`err(z | che do)` chi phu thuoc z qua ti so khong thu nguyen
`z/tau_rho`. Kiem tren `poisson@0.925`:

```text
tau    z      z/tau    err
0.2   0.020   0.10    0.1824
1.0   0.100   0.10    0.1880
5.0   0.500   0.10    0.1946

0.2   0.060   0.30    0.2994
1.0   0.300   0.30    0.3077
5.0   1.500   0.30    0.3125

0.2   0.110   0.55    0.3811
1.0   0.550   0.55    0.3928
5.0   2.750   0.55    0.3824

0.2   0.200   1.00    0.4664
1.0   1.000   1.00    0.4750
5.0   5.000   1.00    0.4594

max_spread = 0.0156
```

Nguong pass da chot: do tan giua ba duong `< 0.05` tuyet doi tren
toan luoi `z/tau`. Hinh: `docs/phase-20R/figures/err_scaling_z_over_tau.svg`.

## 4. Do Nhay

```text
mode     rho_bar | tau=0.2  tau=1.0  tau=5.0 | a=0.2   a=0.9
---------------------------------------------------------------------------
h2       0.700   | 0.5712   0.3889   0.2146 | 0.1463  0.3889
h2       0.850   | 0.4745   0.3235   0.1784 | 0.0098  0.3235
h2       0.925   | 0.1193   0.0902   0.0482 | 0.0000  0.0902
h2       0.960   | 0.0008   0.0003   0.0001 | 0.0000  0.0003
poisson  0.700   | 0.2291   0.1594   0.0746 | 0.0000  0.1594
poisson  0.850   | 0.6333   0.4364   0.2417 | 0.2872  0.4364
poisson  0.925   | 0.5718   0.3928   0.2038 | 0.2338  0.3928
poisson  0.960   | 0.4064   0.2622   0.1301 | 0.0194  0.2622
```

`tau_rho` va `a` la hai bac tu do da co dinh, khong phai tham so vo hai.
Lesson 20R.6 se chay chung nhu doi chung do nhay.

## 5. Luat Dung

```text
lech > 2.0x     -> DUNG. Dieu tra thuoc do truoc khi tin con so.
lech 1.2 - 2.0x -> ghi lai, tim giai thich bang van ban, di tiep.
lech < 1.2x     -> xac nhan hieu biet, di tiep.
err(z=0) > 0.20 -> DUNG. Gan nhu chac chan co bug o luong tu hoa hoac bang tra do that.
```
