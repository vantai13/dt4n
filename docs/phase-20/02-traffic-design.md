# Phase 20 Traffic Design

Muc tieu cua Lesson 20.1b la bien traffic Q8 thanh he sinh flow that tren
Mininet, roi do lai `rho_mean`, `sigma`, `tau` tu counter kernel.

## Chuoi Nhan Qua

```text
traffic model -> rho(t) -> rho_mean, sigma, tau -> err(z), Delta_sla -> gate
```

Phase 20 khong dieu khien `err` truc tiep. Ta dieu khien tham so flow, sau do
do lai cac dai luong trung gian.

## Mo Hinh Flow

```text
flow arrivals: Poisson(lambda)
flow sizes:    Pareto(kappa, size_min)
flow rate:     r_f co dinh
duration:      D = S / r_f
```

Ba cong thuc M/G/inf dung trong code:

```text
rho_mean  = lambda * E[S] / C
sigma_rho = sqrt(rho_mean * r_f / C)
ACF(s)    = integral_s^inf P(D > u) du / E[D]
```

`mininet.traffic_v7.TrafficConfig` suy nguoc:

```text
r_f    = C * sigma_target^2 / rho_target
lambda = rho_target * C / E[S]
```

Nen pre-registration noi bang dai luong co nghia (`rho_target`,
`sigma_target`, `kappa`, `size_min`) thay vi chinh tay `lambda` va `r_f`.

## Diem Chot Q8

```text
rho_target:    twin/topology_v7.LOAD_MEAN
sigma_target: 0.20
kappa:        2.5
size_min:     20 KB
```

`sigma=0.010` khong chay duoc tren Mininet vi can khoang 8460 flow dong thoi
tren moi link 6 Mbps. Sau Amendment 3, generator dung sigma theo vai tro:
`core_sigma=0.10` cho link loi va `edge_sigma=0.03` cho link bien de link bien
khong tro thanh noi ra quyet dinh.

## Do Va Phan Tich

Runner:

```text
mininet/run_sync_v7.py
```

Nhiem vu:

```text
1. dung topology butterfly v7 bang OVS static flows;
2. start 8 generator Poisson/Pareto doc lap;
3. log `rho_offered(t)` thang tu FlowEngine;
4. log `rho_measured(t)` tu counter kernel voi cua so 200 ms;
5. ghi `results/phase-20/rho_offered*.csv`, `rho_measured*.csv`, va metadata.
```

Analyzer:

```text
measurements/measure_tau.py
```

Nhiem vu:

```text
1. bo warm-up;
2. kiem drift tinh dung;
3. tinh ACF va tau tai ACF=1/e;
4. so decay exp voi power-law;
5. so sigma/tau do that voi du doan TrafficConfig.
```

So sanh telemetry:

```text
measurements/compare_estimators.py
```

Tieu chi prereg:

```text
sigma relative error < 30%
tau relative error < 100%  (trong 2x)
```

Neu khong dat, dung so do that va ghi threats to validity; khong tune lai Q8
chi de khop model.
