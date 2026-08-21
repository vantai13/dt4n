# AMENDMENT 23-34 -- Lesson 23.7-ter: do residual vi sai P1-P3

Ngay: 2026-08-21
Trang thai: **TRUOC KHI SUA RUNNER, TRUOC KHI CHAY MININET, VA TRUOC KHI
NHIN KET QUA MOI.**

Lesson 23.7-bis da tach common-mode khoi artifact clipping, nhung L10 van mo
vi artifact cascade chi co mot residual pooled tren mot duong dai dien. Phep do
nay do truc tiep hai duong quyet dinh `P1` va `P3` cua `topology_v7`.

Khong dung cac ID `G23-43..G23-48`: dinh nghia cua chung khong co trong repo.
Ket qua nay la bo sung cho 23.7 va khong tu y dong Lesson 23.8.

## 1. Estimand khoa truoc

Voi `p in {P1, P3}`, cung cell va seed:

```text
r_loss,p  = loss_C,p  - (1 - product_i(1 - loss_B,p,i))
r_delay,p = delay_C,p - sum_i delay_B,p,i
r_cost,p  = r_delay,p + w_loss(cell) * r_loss,p

d_loss = r_loss,P1 - r_loss,P3
d_delay = r_delay,P1 - r_delay,P3
d_cost = r_cost,P1 - r_cost,P3
```

`C` la probe end-to-end qua ba link. `B` la ba probe tung link tren cung
`TandemTopo`, ghep cap bang `mode/rho_bar/seed/path` va bat buoc digest lich
tai cua tung link B/C trung nhau.

Dai luong quyet dinh chinh la `abs(d_cost)`. Bao cao them thanh phan khoa truoc
`w_loss * abs(d_loss)` de noi truc tiep voi erratum 23.7-bis, nhung khong bo
qua `d_delay` khi phan quyet.

## 2. Duong, cell va ngan sach do

Duong dung dung thu tu trong `twin.topology_v7.PATHS`:

```text
P1 = (uA, ac, vC) = ((8,18), (6,13), (8,18))
P3 = (uB, bc, vC) = ((6,13), (6,13), (8,18))
```

Ba cell khoa theo audit 23.7-bis:

```text
poisson@0.925
poisson@0.850
h2@0.700
```

Moi `path x cell` chay 5 seed `201..205`; moi seed co 3 diem B va 1 diem C.
Tong cong `2 x 3 x 5 x 4 = 120` diem live. Thoi luong moi diem 30 s, warmup
5 s, payload probe 1470 B, carve-out 0.25, timeout 120 s. Thu lai toi da mot
lan chi cho gate co the thu lai cua runner cu; validity gate `V-L1g-run` khong
duoc thu lai de lam mat dau vet.

## 3. Bat bien validity

Mot row chi hop le khi tat ca dieu kien runner 20R.6 giu:

```text
socket_drops = 0; n_foreign = 0
max_abs_rate_error <= 1e-4
max_abs_rho_error <= max(0.003, 4*sigma_counting)
n_late_ratio <= 0.001; max_late_ms <= 50
probe_intrusion_ratio <= 0.02
direct_packets_delta = 0 tren moi measured qdisc
q_mean huu han; probe khong rong
```

Ngoai ra analyzer phai dung neu:

```text
- thieu bat ky B link hoac C path nao trong mot cap;
- B/C schedule digest khong trung tren tung link;
- path spec trong artifact khong trung `topology_v7`;
- `w_loss` khac nhau giua P1/P3 trong cung cell.
```

## 4. Uoc luong va phan quyet

Moi residual duoc tinh tung seed. CI90 cua trung binh va cua `d_*` dung paired
bootstrap seed, 10,000 lan, RNG seed `20260821`. Bao cao point, SE, percentile
CI90, tat ca gia tri per-seed va provenance.

Khe doi chieu khoa truoc:

```text
gap_P1_P3 = abs(cost_truth(P1) - cost_truth(P3))
```

tai tam `rho_vector(rho_bar)`, dung `truth_table.parquet` va `w_loss` cua
chinh cell. Phan quyet theo CI90 cua `abs(d_cost)` qua can bao thu:

```text
SAFE_AT_POINT : max(abs(ci90_lo), abs(ci90_hi)) < gap_P1_P3
UNSAFE_AT_POINT: min(abs(ci90_lo), abs(ci90_hi)) > gap_P1_P3
INCONCLUSIVE  : cac truong hop con lai
```

Neu CI cat 0, can duoi cho `abs(d_cost)` la 0. `SAFE_AT_POINT` chi co nghia tai
ba tam cell da do; khong duoc mo rong thanh an toan tren moi row, moi rho hay
toan bo L10. `h2` dung Poisson fixed-count probe tren nen H2 nhu residual
cascade goc; vi vay phai ghi ro estimand la probe-level, khong danh dong voi
loss cua chinh luong H2.

## 5. Negative controls va output

Analyzer phai co NC voi `P1` so voi chinh no: `d_loss=d_delay=d_cost=0` chinh
xac tung seed. File chinh:

```text
results/phase-23/differential_residual_p1_p3.json
```

State live va raw dat rieng duoi:

```text
results/phase-23/differential_live/
results/phase-23/raw_differential/
```

Bao cao cuoi phai liet ke row fail, path spec, plan digest, git commit/dirty,
interpreter/kernel, state files va SHA256 cua moi input.
