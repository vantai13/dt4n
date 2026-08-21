# 15 -- Lesson 23.14: fallback bottleneck va objective robustness

Prereg: `docs/phase-23/00zo-amendment-38.md`  
Code: `cert/fallback_sweep.py`, `cert/objective_misspecification.py`  
Artifacts: `results/phase-23/fallback_sweep.json`,
`results/phase-23/objective_misspecification_sweep.json`  
Figure 2: `results/phase-23/fig2_objective_misspecification.png`

## 1. Ket qua fallback sweep

Moi scoring seed chi duoc cham bang policy fit/chon tu calibration rows cua
bon seed con lai. Tat ca fold dat row-disjoint va seed-disjoint. F6 chi dung
`(z_bin,m_hat_bin)` va frozen action map khi score. NC-C tai lap F2 legacy:

```text
poisson@0.925 : -0.0128688493440567
poisson@0.850 : +0.0031202059335916
h2@0.700      : +0.0038662551728414
max abs gap   : 2.08e-17
```

Policy duoc calibration chon trong moi fold:

| Cell | Family ca 5 fold | c* | err_F\|reject | gap err_F-c* | Delta |
|---|---|---:|---:|---:|---:|
| poisson@0.925 | F2 | 0.453347 | 0.394852 | -0.058495 | -0.012869 |
| poisson@0.850 | F6 | 0.456556 | 0.472257 | +0.015701 | +0.003454 |
| h2@0.700 | F6 | 0.364260 | 0.376151 | +0.011892 | +0.002616 |

F6 giam error fallback H2 tu `0.381833` xuong `0.376151`, nhung van thua
`c*=0.364260`. O poisson@0.850, calibration chon F6 nhung test error
`0.472257` con cao hon F2 `0.470739`. Day la transfer failure cua policy
selection, khong duoc thay bang oracle min tren test.

## 2. Cham M-40..M-45

| ID | Gia tri | Dai khoa | KQ |
|---|---:|---:|:--:|
| M-40 prior_deg spread | 4.111317x | 3.0--6.0 | HIT [TAT DINH] |
| M-41 twin_deg spread | 1.029335x | 1.00--1.15 | HIT [TAT DINH] |
| M-42 selected gap poisson@0.850 | +0.015701 | -0.05--0.00 | MISS |
| M-43 selected gap h2@0.700 | +0.011892 | -0.05--0.00 | MISS |
| M-44 common winning family held-out | none | CO | MISS |
| M-45 selected Delta < 0 ca ba cell | false | CO | MISS |

Khong co mot ho nao trong `F2/F2b/F2c/F4/F5/F6` co
`err_F|reject<c*` tren ca hai held-out cell. Ket qua xay dung da preregister
that bai; khong mo rong family va khong retune sau khi nhin test.

## 3. Bang day du cac ho fallback

Gia tri la `gap = err_F|reject-c*`; am la co loi.

| Family | poisson@0.925 | poisson@0.850 | h2@0.700 |
|---|---:|---:|---:|
| F2 always P1 | -0.058495 | +0.014183 | +0.017574 |
| F2b always P3 | +0.165083 | +0.097861 | +0.254480 |
| F2c calib-best constant | -0.058495 | +0.014183 | +0.017574 |
| F4 twin runner-up | +0.112998 | +0.116462 | +0.272254 |
| F5 top-2 50/50 | +0.056499 | +0.058231 | +0.136127 |
| F6 constant by Mondrian cell | -0.058495 | +0.015701 | +0.011892 |

F4/F5 that bai ro: tren tap cong reject vi margin thap, runner-up cua twin
khong tao ra fallback doc lap hay an toan. F6 co ich mot phan tren H2 nhung
khong giai quyet nguong hoa von.

## 4. Objective misspecification sweep

Gate C3, `y_hat`, ho fallback va action maps duoc dong bang tai objective
goc. Chi ground-truth cost va `a_star` duoc cham lai tren
`w_eff/w_loss=0.5..1.5`.

| Cell | Family frozen | Delta min | Delta @1.0 | Delta max | zero crossing noi suy |
|---|---|---:|---:|---:|---:|
| poisson@0.925 | F2 | -0.029420 | -0.012869 | -0.006918 | khong co trong dai |
| poisson@0.850 | F6 | -0.030336 | +0.003454 | +0.017407 | ~0.9161 |
| h2@0.700 | F6 | -0.013867 | +0.002616 | +0.008015 | ~0.8673 |

Crossing chi la noi suy tuyen tinh giua hai diem grid ke nhau, khong la
uoc luong endpoint moi. Cell chinh giu Delta am tren toan dai. Hai held-out
nhay voi objective va deu doi dau trong dai.

Tai residual ratio do duoc:

| Cell | measured ratio | measured Delta |
|---|---:|---:|
| poisson@0.925 | 0.835256 | -0.016299 |
| poisson@0.850 | 0.835256 | -0.003758 |
| h2@0.700 | 0.933616 | +0.001450 |

Residual do duoc dua poisson held-out sang phia co loi, nhung H2 van co hai.
Day xac nhan canh bao confound: huong objective shift hien tai co the co loi
cho fallback; khong duoc dien giai no nhu mot cai thien cua certificate.

## 5. Ket luan paper sau M-45

Ket qua fallback constructive khong dat. Vi vay headline hop le la:

1. certificate C3 loc twin-hard rows on dinh (`twin_deg` spread 1.029x);
2. fallback la nut co chai (`prior_deg` spread 4.111x);
3. C3 thoai hoa duyen dang hon B2 khi chuyen cell, nhung khong dam bao
   `Delta<0` tuyet doi;
4. dau cua Delta tren held-out phu thuoc manh vao objective weight.

L10 va campaign Mininet Amendment 36 van tam dung; khong ket qua nao o day
duoc dung de dong residual vi sai P1/P3.
