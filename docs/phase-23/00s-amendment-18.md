# AMENDMENT 23-18 -- Kha so sanh giua cac cell

Ngay: 2026-08-15
Commit: amendment commit nay, truoc moi sweep Lesson 23.4 tren hai cell moi.

Ly do: G23-17a/b/c cho thay ba cell khac nhau tren ba truc doc lap:

```text
cell                err_neo   med_m_true_1       t_d       t_l
poisson@0.925      0.222399      10.784947    32.222   0.02921
poisson@0.850      0.220727       3.211916    24.244   0.00722
h2@0.700           0.126536       9.552966    28.614   0.02645
```

Truc `err` gan bat bien giua hai cell poisson, nhung thang margin/regret
khong bat bien. Truc SLA con khac hon: threshold `t_d` va `t_l` la cac nguong
tuyet doi khac nhau giua cell, nen `sla_rate` khong phai cung mot dinh nghia
khi so sanh cross-cell.

## Quy tac bao cao cross-cell

1. Headline cross-cell duy nhat: `err`. Day la thang bat bien duoi phep nhan
   chi phi voi hang so, vi argmin khong doi.

2. `regret` cross-cell bat buoc bao cao bang phan ra ba thua so:

```text
regret_ratio = err_ratio x normpen_ratio x scale_ratio
normpen      = (regret / err) / median_m_true_1
scale_ratio  = median_m_true_1 ratio vs poisson@0.925
```

Ket qua G23-17c:

```text
cell            err_r   normpen_r  scale_r  product  regret_r
poisson@0.850  0.9925     0.9796   0.2978  0.28954   0.2896
h2@0.700       0.5690     0.5533   0.8858  0.27882   0.2788
```

Doc dung:

```text
poisson@0.850: hai thua so that gan 1; regret giam do thang don vi.
h2@0.700     : hai thua so that cung giam quanh 0.55; regret giam la hieu
               ung quyet dinh that, khong phai chi artifact don vi.
```

Cam bao cao `regret` tuyet doi giua cac cell ma khong kem phan ra nay.
`regret` tuyet doi van duoc bao cao trong tung cell rieng.

3. `sla_rate` cross-cell: cam lam headline. Chi bao cao trong tung cell, hoac
   bao cao delta da chuan hoa theo `sla_neo` cua chinh cell do va ghi ro rang
   threshold khac nhau.

4. Thang chuan hoa theo du dia duoc phep dung cho ca ba cell:

```text
gap_closed = (neo - risk) / (neo - B6sys)
```

5. Cam dung `delta/neo` lam headline. Thang nay thien vi cell co neo nho.

## Co che #8

Chenh lech `regret` giua hai cell phan ra dung thanh ba thanh phan: tan suat
sai, gia moi lan sai da chuan hoa, va thang margin. Chi thanh phan thu ba la
don vi. Bao cao `regret` tho giua cac cell ma khong phan ra se tron artifact
don vi voi hieu ung quyet dinh that.

## Scoreboard G23-17b/c

Bang diem du doan G23-17b:

```text
1. static_path same across cells                         PASS
2. h2 median_m_true_1 at least 30% lower than poisson    FAIL
3. h2 P(a*=P1) above poisson                             INVALID
```

Dong 3 vo hieu vi `P(a*=P1) = 1 - err_P1`; day la dong nhat thuc sau khi da
thay `err_P1`, khong phai mot du doan doc lap.

Bang diem S2 cua G23-17c:

```text
poisson@0.850: regret ratio tracks margin scale ratio   PASS
h2@0.700     : gap_pct = 68.52% > 15%                  FAIL
```

Bai hoc #11 ve ve sinh du doan: khong tinh mot dong nhat thuc, dinh nghia lai,
hoac he qua dai so cua cot da biet nhu mot prediction moi.

## Thu hep pham vi G23-17

Ba cell khong phai ba che do doc lap nhu nhau:

```text
poisson@0.925 va poisson@0.850:
  err_neo gan trung, err_P1 gan trung, swing gan trung, nhung margin scale
  lech 3.36x. Day la doi chung bat bien theo thang.

h2@0.700:
  err_neo thap hon ro, err_P1 thap hon ro, swing rat nho, correlation
  inflation cao. Day moi la cell khac che do quyet dinh.
```

Viet dung: `poisson@0.850` la scale-invariance control; `h2@0.700` la regime
khac do correlation inflation. Khong viet "ba che do van hanh doc lap".

## E4-moi -- ky truoc sweep Lesson 23.4

E4 cu bi bac tien de: `err_P1` khong bat bien theo topology
`0.340276 / 0.345169 / 0.157454`.

```text
S1  poisson@0.850 giong poisson@0.925 tren err:
      |delta_best(0.850) - delta_best(0.925)| < 0.004
      beneficial bands overlap > 80%

S3  h2@0.700 co |delta_best| < 0.008

S4  beneficial band cua h2@0.700 khong rong nhung hep hon poisson@0.925:
      band_low(h2) > band_low(0.925) = 0.6076

S5  gap_closed(h2@0.700) < gap_closed(poisson@0.925) = 10.02%

S6  G23-21c PASS ca hai cell moi. Nhanh fail: neu m_hat_bin=3 mong o h2,
    gop bin va ghi ro truoc sweep.

S7  Ho NHAN van Pareto-dominates ho CONG tren ca hai cell moi.
```

## No cu

Trang thai truoc Lesson 23.4:

```text
L21  alpha/3 vs alpha/4 da dong boi Amendment 23-16; pruning action chet
     con la limitation optional, chua duoc dung de dien giai ket qua.
L22  gamma != 1 da dong la diagnostic-only, khong guarantee-preserving.
C3-A Chung minh dong bang C3 da ghi trong 04-baselines.md.
beneficial_band grid labels da ghi ro: Lesson 23.1 dung luoi kappa min;
     Lesson 23.3 dung luoi coverage deu.
```

## Dieu kien tiep theo

Truoc khi chay sweep 23.4, phai chay G23-21c tren `poisson@0.850` va
`h2@0.700` voi artifact va nhan cell dung. Neu cell nao co
`cells_below_conservative_action_split_n_min > 0` hoac nonfinite qhat, dung lai
va xu ly truoc khi sweep.
