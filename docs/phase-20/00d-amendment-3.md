# AMENDMENT 3 - Phase 20 Pre-Registration

Ngay: 2026-07-26
Trang thai: sau lan do 20.1b thu 1, TRUOC phep do chinh

Ket luan lan do 1: KHONG HOP LE. Khong dung `rho_trace.csv`,
`tau_summary.json`, hay bat cu so nao tu lan do nay cho `decision_error.py`.
Lan do do chu yeu do thang do va gioi han implementation, khong do dung he
thong.

## A3.1 Loi Cua Thuoc

L1. Tieu chi "trong 2x" viet bang sai so tuong doi:

```text
|m - p| / p < 1.0
```

Tieu chi nay bao hoa o 1.0 khi `m -> 0`, nen co the che mat sai lech hang
chuc hoac hang tram lan. Sua thanh thang log:

```text
|log2(m / p)| <= 1
```

L2. Lan do cu khong co kiem tra san phan giai. Voi nhieu trang, noi suy tu
ACF(0)=1 sang ACF(1)=0 luon cho:

```text
tau = (1 - 1/e) * dt = 0.632 * dt
```

Lan do cu co `tau/dt` quanh gia tri nay cho ca 8 link. `measure_tau.py` tu nay
gan co `RESOLUTION_FLOOR`, `UNRESOLVED`, `MARGINAL`, hoac `OK`; khong phan loai
decay khi tau chua duoc phan giai.

L3. Test tinh dung cu dung nguong drift co dinh, ngam gia dinh mau doc lap.
Sua: bao cao SE theo `n^(H-1)` khi uoc luong duoc H; neu khong thi ghi ro dang
gia dinh `H=0.5`.

L4. `decay_shape()` cu co the fit tren qua it lag. Sua: can toi thieu 20 diem
trong vung ACF fit.

## A3.2 Nguyen Nhan Goc 1 - Dem Byte Cua So 10 ms

Link 6 Mbps voi cua so 10 ms chi co khoang 5 goi MTU. Nhieu dem goi co the ap
dao sigma va keo tau xuong san phan giai. Sua: ghi thang:

```text
rho_offered(t) = sum(rate active flows) / C
```

tu bo sinh tai. Day la dai luong dung vi `twin.link_model` nhan
`rho_offered`, khong phai `rho_measured`.

Van ghi song song `rho_measured` tu counter kernel voi cua so 200 ms de do
nhieu telemetry:

```text
rho_offered.csv
rho_measured.csv
measurements/compare_estimators.py
```

## A3.3 Nguyen Nhan Goc 2 - Spawn Mot iperf Moi Flow

Lan do cu spawn khoang 160 process iperf moi giay. Mininet khong theo kip,
flow chong lan, tai vuot thiet ke, lam san khau dao nguoc: link loi bi ghim
tren plateau, link bien thanh noi quyet dinh.

Sua: `mininet/flow_engine.py` la mot process thuong tru moi kenh. Moi process
quan ly flow ao bang hang doi su kien va gui UDP theo tong toc do active flow.
Chi co 8 process sinh tai thay vi fork/exec theo tung flow.

## A3.4 Dieu Kien Chap Nhan Lan Do 2

C1. Ca 8 link:

```text
|log2(rho_mean_do / rho_target)| <= log2(1.05)
```

C2. Bon link loi `ac, ad, bc, bd` that su vat qua cliff:

```text
P(rho < 0.9250) >= 0.15
P(rho > 0.9325) >= 0.15
```

C3. Bon link bien `uA, uB, vC, vD` that su nhan roi:

```text
P(rho > 0.9250) <= 0.05
```

C4. Tau da duoc phan giai:

```text
tau / dt >= 10
```

C5. Tau do va tau du doan trong 2 lan tren thang log:

```text
|log2(tau_do / tau_du_doan)| <= 1
```

C6. Sigma do va sigma du doan trong 2 lan tren thang log:

```text
|log2(sigma_do / sigma_du_doan)| <= 1
```

C7. Dang phan ra phan loai duoc voi it nhat 20 lag trong vung fit; bao cao H
neu power-law.

Khong dat C1-C3: sua bo sinh tai, khong sua topology. Khong dat C4: giam dt va
do lai, khong ket luan tau. Khong dat C5-C6: ghi threats to validity, dung so
do duoc, khong tune Q8 cho khop.

## A3.5 Q8 Cho Lan Do 2

De giu link bien that su nhan roi trong khi link loi van co sigma du de vat
qua cliff, lan do 2 dung sigma theo vai tro:

```text
core_sigma = 0.10  cho ac, ad, bc, bd
edge_sigma = 0.03  cho uA, uB, vC, vD
kappa = 2.5
size_min = 20 KB
```

`core_sigma` la dai luong dung cho bang chon `z*` sau khi co sigma_flow that.
`edge_sigma` chi nham giu tai nen bien khong thanh noi quyet dinh.

Ghi nhan: quick-check 60s voi `core_sigma=0.20, edge_sigma=0.05` khong dat
C1/C3 (`bd` va `vD` bi lech). Theo A3.4, day la loi bo sinh tai nen da sua
tham so generator, khong sua topology.

Bang chon `z*` chot truoc khi thay `err`:

```text
sigma_flow <= 0.07         -> z* = 4
0.07 < sigma_flow <= 0.15  -> z* = 2
sigma_flow > 0.15          -> z* = 1
```

## A3.6 Cach Chay Lai

```text
tools/phase20_smoke.sh
runbooks/phase-20-traffic-v7-tmux.md
```

Bat buoc do hai do phan giai `dt = 10 ms` va `dt = 2 ms` de kiem tra
resolution invariance. Neu tau bam theo dt, van dang do thang do.
