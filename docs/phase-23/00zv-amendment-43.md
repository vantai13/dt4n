# AMENDMENT 23-43 -- Lesson 23.8[A4]: chien dich do AoI tren topology_v7

Ngay: 2026-08-22  
Trang thai: **SAU A0--A3 va NC-do-1/2/3; TRUOC moi lan do outcome A4.**

## 1. Bon estimand

```text
E1  d_sync      = P05 cua aoi_s trong MODE-CLEAN, gop 8 link.
E2  T_eff[l]    = trung vi khoang cach giua hai gia tri tSource[l] khac nhau.
E3  offset[l]   = alpha_l trong aoi ~ mu + alpha_l + beta*read_pos,
                  voi sum(alpha_l)=0.
E4  shape       = CV, p50, p95, p99, max; kem ty le chu ky overrun.
```

## 2. Hai che do va ma tran do

```text
MODE-CLEAN  tol=0,   reconcile_every=1,  period=0.5 s
MODE-PROD   tol=0.5, reconcile_every=30, period=0.5 s

2 mode x 5 rho_bar {0.700,0.850,0.900,0.925,0.960} x 3 repeat = 30 run.
Moi run 120 s; probe interval 0.1 s; counterbalance fwd/rev.
Thu tu run duoc shuffle mot lan bang seed 23843.
```

Moi repeat co traffic seed rieng, quyet dinh tu vi tri trong ma tran canonical,
khong tu outcome. Runner va schema `dt4n.aoi.v7.v1` da dong bang trong commit
`e34cd1f`.

## 3. So lieu chi duoc phep dung de khoa du doan

Day la so kiem chuan nhac cu, khong phai outcome A4:

```text
A0 CLEAN synthetic: p95-p05=448.080 ms; CV=0.556914;
                    CV dai so=0.556343; gap=0.000572.
A2/A3 smoke CLEAN 30 s, khong traffic:
  63 cycles; overrun=0; full push=63/63; negative AoI=0;
  P05=180.178 ms; CV=0.363245; median T_eff=500.038 ms;
  max offset spread=40.075 ms; beta=-2.466 ms/read_pos;
  profile RMSE: U0=14.023, U1=24.273, U2=21.697 ms.
```

## 4. Du doan khoa M-70 .. M-77

| ID | Dai luong | Nhan | Dai khoa |
|---|---|---|---|
| M-70 | E1 d_sync, CLEAN, gop 8 link | [NGOAI SUY] | 140 .. 220 ms |
| M-71 | bien thien E1 tren 5 muc rho_bar | [CO CHE] | <= 40 ms |
| M-72 | E4 CV MODE-CLEAN | [NGOAI SUY] | 0.32 .. 0.41 |
| M-72b | sai lech `abs(CV_obs - T/sqrt(12)/(d+T/2))` | [CO CHE] | <= 0.05 |
| M-73 | E4 CV MODE-PROD | [CO CHE] | > 0.41 |
| M-74 | E2 T_eff trung vi MODE-PROD | [CO CHE] | > 0.5 s |
| M-75 | E3 max offset giua 8 link, CLEAN | [NGOAI SUY] | 20 .. 70 ms |
| M-76 | E3 profile gan nhat | [NGOAI SUY] | U0 |
| M-77 | corr(AoI,rho), MODE-PROD | [CO CHE] | am, abs > 0.2 |

M-72 trong khung 23-43 ban dau la `0.44 .. 0.52`. Truoc A4, NC-do-2 va
Amendment 23-42c da chung minh CV cua `Uniform[d,d+T]` phu thuoc `d`:
`CV=T/sqrt(12)/(d+T/2)`. Vi vay giu dai 0.44--0.52 sau khi biet `d>0` se la
khoa mot du doan da biet sai. M-72 tren la du doan raw-CV theo smoke; M-72b
la gate dung de kiem dinh dang rang cua. Viec sua estimand nay xay ra truoc
outcome A4 va se khong duoc retune.

## 5. Controls va stop rule

```text
NC-R  beta phai khac 0 dang ke; bao cao rank va condition number.
NC-S  tong so aoi_s < 0 phai bang 0. FAIL -> dung chien dich.
NC-T  bao cao overrun_ratio; neu >0.05, canh bao E1 bi confound boi lock.
NC-U  CLEAN: n_pushed == n_things moi chu ky. FAIL -> dung chien dich.
NC-V  moi header phai co SHA-256 cua topology_v7_spec.json.

M-70 HIT va M-72b HIT -> duoc phep nap E1 va dong P23-A/L11 tai A5.
M-72b MISS -> mo hinh rang cua sai ngay trong CLEAN; khong retune/do them.
Khong mo Tang 3, khong lam min luoi rho, khong them mode thu ba.
```

## 6. Thu tu 30 run da khoa

```text
01 prod_rho0.700_rep3   02 prod_rho0.850_rep2
03 clean_rho0.850_rep1 04 prod_rho0.960_rep3
05 clean_rho0.900_rep2 06 prod_rho0.850_rep3
07 prod_rho0.900_rep2  08 prod_rho0.925_rep1
09 clean_rho0.960_rep2 10 clean_rho0.925_rep1
11 prod_rho0.700_rep1  12 clean_rho0.925_rep3
13 clean_rho0.700_rep3 14 prod_rho0.925_rep3
15 prod_rho0.850_rep1  16 clean_rho0.850_rep3
17 clean_rho0.850_rep2 18 prod_rho0.700_rep2
19 clean_rho0.900_rep1 20 clean_rho0.960_rep3
21 prod_rho0.900_rep1  22 prod_rho0.900_rep3
23 clean_rho0.700_rep1 24 prod_rho0.925_rep2
25 prod_rho0.960_rep2  26 clean_rho0.700_rep2
27 prod_rho0.960_rep1  28 clean_rho0.900_rep3
29 clean_rho0.925_rep2 30 clean_rho0.960_rep1
```

## 7. Output khoa

```text
results/phase-23/aoi_v7_campaign/*
results/phase-23/aoi_v7_estimates.json
results/phase-23/fig8_aoi_v7.png
docs/phase-23/20-aoi-on-topology-v7.md
```
