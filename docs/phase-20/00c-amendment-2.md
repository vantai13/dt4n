# AMENDMENT 2 - Phase 20 Pre-Registration

Ngay: 2026-07-26
Trang thai: TRUOC phep do chinh
Ly do: Lesson 20.1b bien `sigma` va `tau` tu so pilot thanh dai luong do
duoc tu he that.

Khong sua `00-preregistration.md` hay `00b-amendment-1.md`. Amendment nay bo
rang buoc proxy `A/tau`, chot diem van hanh moi, va ghi ro traffic Q8 co the
chay duoc tren Mininet.

## A2.1 Bo Rang Buoc So Hoc A/tau

Bo Q9 cu trong prereg va ban sua o Amendment 1.

Ly do phuong phap: `A/tau` la dai luong muc gia tri, trong khi Phase 20 do
thang dai luong muc quyet dinh `err(z)`. Rang buoc thiet ke bang proxy khi da
do duoc muc tieu la sai phuong phap, va day cung la luan diem trung tam cua
paper: bao dam muc gia tri khong suy ra bao dam muc quyet dinh.

Ly do ky thuat: voi kich thuoc flow Pareto `kappa < 2`, `rho(t)` co phu thuoc
tam xa. ACF phan ra luy thua, khong phai mu, nen khong ton tai mot thang thoi
gian `tau` duy nhat de dua vao rang buoc `A/tau`.

Bang chung tu M/G/inf:

```text
ACF(s) = integral_s^inf P(D > u) du / E[D]

kappa=3.0 -> tau/E[D]=0.63
kappa=2.0 -> tau/E[D]=0.68
kappa=1.5 -> tau/E[D]=1.09
kappa=1.2 -> tau/E[D]=9.94
```

`tau` van phai do va bao cao nhu mot dac trung traffic, nhung khong duoc dung
lam rang buoc thiet ke.

## A2.2 Diem Van Hanh Co Neo Vat Ly

Chot:

```text
z* = 1 buoc env
```

Bien minh: trong vong dieu khien dong that, controller hanh dong tren snapshot
twin moi nhat. Vi vay twin tre dung mot chu ky sync. `z*=1` la diem van hanh
tu nhien cua testbed Phase 0-4, khong phai mot lua chon tuning sau pilot.

`z > 1` mo ta twin bi suy giam: sync cham, mat goi sync, hoac twin qua tai.
Do la truc dieu kien-theo-tuoi cua Phase 22. Quet `z` la exploratory; kiem
dinh Phase 20 dung `z*=1`.

Chu ky sync chot:

```text
T = 0.5 s
```

Ly do: day la gia tri testbed da chay va da do AoI. Phep do cu khop ly thuyet
rang cua trong vong 2%:

```text
A = d_sync + T/2 = 0.051 + 0.250 = 0.301 s ly thuyet
Do duoc: Uniform[0.051, 0.548], mean 0.298 s, CV 0.487
Ly thuyet: mean 0.2995 s, CV 0.479
```

## A2.3 Sua Sigma Muc Tieu

Chot:

```text
sigma_target = 0.20
```

Thay cho `sigma = 0.010` trong pilot Lesson 20.0b.

Ly do tu M/G/inf:

```text
sigma_rho = sqrt(rho * r_f / C)
```

Voi `rho = 0.92`, `sigma = 0.010` doi hoi:

```text
r_f/C = 1.09e-4
N_mean ~= 8460 flow dong thoi moi link
```

Tren 8 link la khoang 67,000 flow dong thoi, bat kha thi tren Mininet. Voi
`sigma = 0.20`, link 6 Mbps co `r_f ~= 261 kbps` va `N_mean ~= 21 flow/link`,
nam trong vung chay duoc.

Ghi nhan: `sigma=0.010` trong Lesson 20.0b la so pilot khong co tinh kha thi.
Day la loi pilot da duoc phat hien truoc confirmatory run.

## A2.4 Kiem Chung Lai Thiet Ke O Sigma Thuc Te

Pilot bo sung:

```text
sigma=0.20: err(z=1)=0.302  Delta_sla=+0.094
            err(z=2)=0.396  Delta_sla=+0.149
            err(z=4)=0.502

sigma=0.35: err(z=1)=0.307  Delta_sla=+0.074
```

Ket luan: `z*=4` khong con dung voi sigma thuc te; `z*=1` la diem van hanh
chot. `K_eff` tang tu 2.59 len khoang 3.90/4 khi sigma tang, nen san khau
giau hon. Dich `mu_core` ra xa nguong gan nhu khong tac dong khi sigma lon;
do khong phai can gat chinh.

## A2.5 Q8 Chot

Traffic sinh o muc flow, khong sinh `rho` bang bang so:

```text
rho_target:
  edge links: theo twin/topology_v7.LOAD_MEAN, khoang 0.80-0.83
  core links: theo twin/topology_v7.LOAD_MEAN, quanh cliff

sigma_target = 0.20
kappa = 2.5
size_min = 20 KB
```

Chon `kappa = 2.5` co chu dich:

```text
(a) kappa > 2 => phuong sai huu han, ACF gan mu hon, tau co nghia hon.
(b) kappa = 1.2 lam tau cuc nhay va rat kho dieu khien tren testbed.
(c) van la duoi nang, nen van co mice/elephant, chi bot cuc doan.
```

Threat to validity da ghi nhan: `kappa=2.5` it cuc doan hon Internet that
(`1.05-1.5`). San khau co burstiness thap hon thuc te; tac dong len do kho cua
bai toan phai thao luan trong paper.

`lambda` va `r_f` duoc suy ra tu `(rho_target, sigma_target, kappa, size_min)`
bang `mininet.traffic_v7.TrafficConfig`, khong chinh tay.

## A2.6 Kiem Chung Du Doan Vs Do That

Truoc Lesson 20.2, bat buoc chay:

```text
sudo "$(command -v python3)" -m mininet.run_sync_v7 --traffic v7 --log-rho 0.010 --duration 300
python -m measurements.measure_tau --input results/phase-20/rho_trace.csv --dt 0.010
```

`TrafficConfig` in ra du doan:

```text
lambda, r_f, N_mean, E[D], tau_pred, H
```

`measure_tau.py` do that:

```text
rho_mean, sigma, tau, dang phan ra ACF, kappa_hat/H neu power-law
```

Tieu chi chot truoc:

```text
|sigma_do - sigma_du_doan| / sigma_du_doan < 0.30
|tau_do - tau_du_doan| / tau_du_doan < 1.0
```

Neu khong dat: ghi vao threats to validity, dung so do that, va di tiep.
Khong duoc chinh Q8 cho khop. Mo hinh sai la mot ket qua, khong phai loi.

## A2.7 Files Dong Bang

```text
docs/phase-20/00c-amendment-2.md
docs/phase-20/02-traffic-design.md
mininet/traffic_v7.py
mininet/run_sync_v7.py
measurements/measure_tau.py
runbooks/phase-20-traffic-v7-tmux.md
```
