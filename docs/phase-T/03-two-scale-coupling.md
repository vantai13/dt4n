# PHASE T -- T.3 TWO-SCALE COUPLING

Ngay: 2026-07-31
Deliverable: `mininet/rho_schedule.py` va
`test/test_phase_t_rho_schedule.py`.

T.3 ghep hai dai luong o hai thang thoi gian:

```text
thang luong: rho(t), sigma_rho, tau_rho    tu mininet/rho_spec.py
thang goi : mode, c_a                     tu mininet/load_spec.py
```

Muc tieu la sinh mot lich goi nen sao cho cuong do tuc thoi bam `rho(t)`,
nhung `c_a` cua base process van giu dung thiet ke khi do trong thoi gian
van hanh.

--------------------------------------------------------------------
## Quyet Dinh Chinh

Dung time-rescaling.

Dat `lambda(t)` la toc do goi nen can de:

```text
rho(t) = (bg_pps(t)*1512 + probe_pps*106) / (bw*1e6/8)
```

Dung lai `mininet.load_spec.background_pps()` de dinh nghia rho khong lech
giua Phase L va Phase T.

Tinh:

```text
Lambda(t) = integral_0^t lambda(s) ds
```

Sinh base gaps trong thoi gian van hanh:

```text
G_i, E[G_i] = 1, CV(G_i) = c_design
U_i = sum_j<=i G_j
T_i = Lambda^{-1}(U_i)
```

Khi do so diem trong `[0,t]` bang so diem base trong `[0,Lambda(t)]`, nen
ky vong so goi la `Lambda(t)` va cuong do tuc thoi la `lambda(t)`.

--------------------------------------------------------------------
## Vi Sao Khong Dung Thinning

Thinning sinh o toc do cuc dai roi giu moi goi voi xac suat `p`. Voi process
khac Poisson, no doi burstiness:

```text
c_moi^2 = p*c_cu^2 + (1-p)
```

He qua voi `p ~= 0.81`:

```text
cbr:     0.00 -> 0.43    bi pha hoan toan
poisson: 1.00 -> 1.00    chi Poisson moi bat bien
h2:      2.00 -> 1.86    giam 5-10%, co the lot qua cong cu ma van sai
```

Rate-modulated renewal cung bi loai vi chi gan dung, co tre bang mot gap khi
`lambda(t)` doi nhanh, va khong co cong thuc dong cho sai so.

--------------------------------------------------------------------
## Hai Cach Do `c_a`

Trong thoi gian van hanh:

```text
u_i = Lambda(T_i)
CV(u_i - u_{i-1}) = c_design
```

Day la cong V-T4a/V-T6a. No dung toan bo lich goi, khong can chon cua so, va
khong bi nhieu dem.

Trong thoi gian that, `c_a` gop phai tang khi `lambda(t)` bien thien. Cong
thuc doi chung duong:

```text
c_a_pooled = sqrt((1+c_design^2) * E[lambda] * E[1/lambda] - 1)
```

`E[.]` o day la trung binh theo thoi gian tren quy dao da sinh. Do
Cauchy-Schwarz, tich `E[lambda]E[1/lambda] >= 1`; dau bang chi khi
`lambda(t)` hang.

--------------------------------------------------------------------
## Bon Cam Bay Cai Dat

1. Khong lam tron `Lambda^{-1}` ve bien luoi.

`rho_spec` giu `lambda` hang trong moi buoc `dt=0.005`, nen `Lambda` tuyen
tinh tung khuc va nghich dao dung la noi suy tuyen tinh. Lam tron ve `k*dt`
lam cbr `c_a` nhay tu khoang `0.08` len `1.05` va tao gan 20k goi trung thoi
diem trong 90 s.

2. Chuan hoa base process truoc khi rescale.

`build_schedule(mode, n_base, 1.0, seed)` chuan hoa mean gap bang 1 trong
thoi gian van hanh. Mutation testing T.4 cho thay chuan hoa them sau khi
rescale gan nhu vo hai trong he hien tai: he so do duoc khoang `1.000016`,
tuc anh huong `0.0016%`, vi `lambda(rho)` tuyen tinh nen `E[lambda] =
lambda(E[rho])`.

Van giu thu tu "chuan hoa trong operational time roi moi rescale" vi no lam
rate phu thuoc thiet ke thay vi realization, va se la thu tu dung neu sau nay
anh xa `rho -> lambda` tro nen phi tuyen.

3. Duong `sigma_rho=0` phai uy quyen cho Phase L.

Neu tu cai lai duong hang so bang cong thuc rescale, gap co the lech mot ULP
vi `(g/m)*mean_gap` khac `g*(mean_gap/m)` trong dau phay dong. SHA-256 thay
doi hoan toan. Vi vay `traj.kind == "const"` goi thang
`load_spec.build_schedule()`.

4. Chon `n_base = int(Lambda_total)` va dung het.

Neu sinh du thua roi cat theo `U_i > Lambda_total`, mean cua phan duoc dung
co sai so ngau nhien. Voi h2 va khoang 38k goi, sai so mean co the gan 1%,
lon hon cong `|rate_ratio-1| < 0.001`. Cach hien tai cho rate ratio khoang
`0.99998`.

--------------------------------------------------------------------
## Probe

Probe khong duoc rescale. No giu Poisson hang `20 pps` voi seed
`seed + 500000`, dung mau Phase L.

Ly do la PASTA: probe Poisson toc do hang thay trung binh theo thoi gian. Neu
rescale probe theo `rho(t)`, no se lay mau co trong so tai va mat vai tro
doi chung time-average.

--------------------------------------------------------------------
## V-T6 Duoc Sua

Ban prereg cu co:

```text
V-T6. rho_thuc_te(t) do tu _bgtx.bin khop rho(t): RMSE < 0.01
```

Cong nay fail bang cau tao. Voi cua so 100 ms:

```text
mode      a     RMSE      bias
cbr     0.90   0.00801  -0.00001
poisson 0.90   0.12929  +0.00059
h2      0.90   0.25449  +0.00055
```

Bias gan 0, nhung RMSE lon vi nhieu dem. Ly thuyet:

```text
Var(N) = IDC * lambda * W
sd(rho_hat) = (FRAME_BG/cap) * sqrt(IDC * lambda / W)
```

Poisson va h2 khop cong thuc trong khoang 1-4%. Muon h2 co RMSE duoi 0.01
can cua so khoang 68 s, gan bang ca cua so do 90 s, nen khong co y nghia.

Sua thanh:

```text
V-T6a (cong):
  mean(gap_u) = 1.000 trong 0.5%
  CV(gap_u)   = c_design voi sai so tuyet doi < 0.02

V-T6b (mo ta):
  rho_hat window co bias < 0.002
  RMSE khop cong thuc nhieu dem trong 20%
```

Ghi chu sau Amendment 7: nguong `bias < 0.002` bi thay bang
`abs(rho_bias_z) < 3`, voi sd du doan tu dao dong renewal tai bien warm-up.

Day la cung khuon mau voi V-T1, V-T2 va V-T4: khong so truc tiep mot uoc
luong noisy voi gia tri thiet ke; phai so voi ky vong cua uoc luong do, hoac
doi sang dai luong khong noisy.

--------------------------------------------------------------------
## Lenh Kiem Tra Lai

Chay rieng T.3:

```bash
pytest test/test_phase_t_rho_schedule.py -q
```

Chay nhom Phase T hien co:

```bash
pytest test/test_phase_t_no_v1_import.py test/test_traffic_v7_hurst.py test/test_phase_t_rho_spec.py test/test_phase_t_rho_schedule.py -q
```

Chay full suite:

```bash
pytest -q
```

Ket qua tai thoi diem them T.3:

```text
pytest test/test_phase_t_rho_schedule.py -q
53 passed

pytest test/test_phase_t_no_v1_import.py test/test_traffic_v7_hurst.py test/test_phase_t_rho_spec.py test/test_phase_t_rho_schedule.py -q
108 passed

pytest -q
282 passed, 4 skipped, 2 warnings
```

Kiem tay mot schedule:

```bash
python3 - <<'PY'
from mininet.rho_spec import ou_trajectory, sigma_from_a
from mininet.rho_schedule import build_varying_schedule
import json

tr = ou_trajectory(0.85, sigma_from_a(0.85,0.90), 1.0, 18000, 11)
s = build_varying_schedule("h2", tr, 6.0, 11)
print(json.dumps(s.as_dict(), indent=2, sort_keys=True))
PY
```

Ky vong:

```text
c_a_operational ~= 2.00
c_a_pooled      ~= 2.02
rate_ratio      ~= 0.99998
path            = rescale
```
