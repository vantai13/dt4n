# AMENDMENT 1 -- Phase T

Ngay: 2026-07-30
Trang thai truoc sua: Phase T chua chay do; audit T.0 yeu cau sua provenance
Hurst cua traffic flow-level.

## Da Thay So Nao Truoc Khi Sua

`mininet/traffic_v7.py` tinh:

```text
H = (3 - kappa) / 2
```

Voi default `kappa = 2.5`, code ghi `H = 0.25`.

Gia tri nay vo nghia cho muc tieu provenance LRD: quan he
`H = (3-kappa)/2` chi ap dung khi `1 < kappa < 2`, noi thoi luong luong
Pareto co phuong sai vo han. Voi `kappa >= 2`, phuong sai huu han nen mo hinh
khong tao long-range dependence; gia tri trung lap dung de ghi la `H = 0.5`.

## Sua Gi

`TrafficConfig.hurst` doi thanh:

```text
1 < kappa < 2  ->  H = (3-kappa)/2
kappa >= 2     ->  H = 0.5
kappa <= 1     ->  raise ValueError
```

Them regression test:

```text
test/test_traffic_v7_hurst.py
```

Test nay khoa hai hanh vi:

```text
kappa = 1.5 -> H = 0.75
kappa >= 2 -> H = 0.5
```

## Khong Sua

Khong doi cac tham so traffic v7 khac:

```text
rho_target
sigma_target
size_min_kb
lam
rate_bps
mean_duration_s
tau_pred_s
payload cua ResidentLoadGenerator
```

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-07-30
