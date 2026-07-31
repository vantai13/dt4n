# PHASE T -- T.2 RHO SPEC

Ngay: 2026-07-31
Deliverable: `mininet/rho_spec.py` va `test/test_phase_t_rho_spec.py`.

T.2 la buoc code dau tien cua Phase T. No chi sinh quyen dao tai `rho(t)`;
chua sinh goi, chua mo socket, chua dung Mininet. Day la ham thuan theo mau
Phase L `load_spec.py`.

--------------------------------------------------------------------
## Muc Tieu

```text
(rho_bar, sigma_rho, tau_rho, seed) -> RhoTrajectory
```

Hop dong:

```text
khong I/O, khong dong ho, khong socket
cung input -> cung rho va cung digest
rho nam trong mien link_model_v2 [0.50,1.05]
ghi n_clamped va clamp_ratio lam provenance
```

--------------------------------------------------------------------
## Quyet Dinh Thiet Ke

1. Normal dung Box-Muller tu `rng.random()`, khong dung `random.gauss`.

Ly do: `random.gauss()` co cache noi bo tren doi tuong `Random`, nen so uniform
tieu thu phu thuoc lich su goi. Box-Muller trong module nay tieu thu dung
2 uniform cho 1 normal.

2. Tach dong RNG bang nhan:

```text
sub_seed(master_seed, label) = sha256(seed|label)[:8]
```

Ly do: khong dung offset cong tay khi Phase T co nhieu dong ngau nhien
(`rho_ou`, `rho_mminf`, ve sau la `bg`, `probe`, ...). Phase L `load_spec.py`
giu nguyen de digest cu khop.

3. OU khoi tao o phan phoi dung:

```text
x0 = rho_bar + sigma_rho*z0
```

Ly do: khoi tao tai `rho_bar` lam 3*tau dau co phuong sai thap gia, tao
burn-in cua chinh rho(t). Warm-up thuc nghiem van giu cho hang doi, khong phai
cho bo sinh rho.

4. Clamp dung mien measured:

```text
RHO_MIN=0.50, RHO_MAX=1.05
```

Ly do: `link_model_v2.predict_delay(strict=True)` khong xac dinh ngoai mien.
Moi tich phan `f(rho(t))` phai dung chinh quyen dao da clamp.

5. `sigma_max` la rang buoc hai phia:

```text
sigma_max = min(rho_bar-0.50, 1.05-rho_bar) / 2.58
sigma_rho = a*sigma_max, a in {0.20,0.90}
```

Day la dinh chinh T.2. Ban T.1 chi nhin bien tren, lam `rho_bar=0.70` co the
clamp 5.28% tai `a=0.90`, vuot V-T3. Code bien rang buoc nay thanh ham
`sigma_max_feasible()` va co test bao ve.

6. `dt` tach theo muc dich:

```text
experiment dt = 0.005 s
unit-test dt  = tau/2
```

AR(1) la roi rac hoa chinh xac voi moi `dt`. `dt=0.005` la yeu cau vat ly de
hang doi thay tai tron; `dt=tau/2` trong unit test de co nhieu mau doc lap hon
voi cung so buoc.

7. Tra ve `RhoTrajectory`, khong tra list tran.

`RhoTrajectory` gom `rho`, `dt`, `n_clamped`, `kind`, `design`, `digest()` va
`as_dict()`. `n_clamped` la bang chung V-T3, khong phai metadata phu.

8. Doi chung M/M/infinity dung chuyen tiep chinh xac:

```text
n(t+dt) = Binom(n(t), exp(-dt/tau)) + Poisson(E[n]*(1-exp(-dt/tau)))
```

Khong dung `Poisson(lambda_f*dt)`.

--------------------------------------------------------------------
## Bug M/M/infinity Bi Test Bat

Ban dau dong nap moi duoc viet theo truc giac:

```text
n_act += Poisson(lambda_f*dt)
```

Neu phan song sot cua luong cu dung chinh xac `p = 1-exp(-dt/tau)`, ky vong
dung cua chuoi sai nay la:

```text
E[n] = n_mean * x/(1-exp(-x)), x=dt/tau
```

Voi `dt=tau/4`, sai so la:

```text
0.25/(1-exp(-0.25)) = 1.130
```

Tuc `rho_bar` lech +13%. Test `test_mminf_khop_ca_ba_tham_so_thiet_ke` chan
loi nay bang cach so voi ca ba tham so thiet ke `(rho_bar, sigma_rho, tau_rho)`.

Sua dung:

```text
n_act += Poisson(n_mean * p_leave)
```

--------------------------------------------------------------------
## Ket Qua Kiem Tra

Da chay:

```text
pytest test/test_phase_t_rho_spec.py -q
50 passed in 10.69 s

pytest -q
229 passed, 4 skipped, 2 warnings
```

Kiem tay:

```text
rho_bar=0.70, a=0.90 -> sigma=0.069767, clamp=0.0325%
rho_bar=0.85, a=0.90 -> sigma=0.069767, clamp=0.0455%
rho_bar=0.925,a=0.90 -> sigma=0.043605, clamp=0.0455%
rho_bar=0.98, a=0.90 -> sigma=0.024419, clamp=0.0455%
```

Tat ca duoi V-T3 `1%`.

Manual provenance sample:

```text
ou_trajectory(0.85, sigma_from_a(0.85,0.90), 1.0, 18000, 11)
duration_s = 90.0
clamp_ratio = 0.0
trajectory_digest = 7a5a4a9ccd3b5ed4512063a95fda07c4c1aa594cf4f573bf4f70202397f1eb79
measured.rho_bar ~= 0.84994
measured.sigma_rho ~= 0.06593
```

Gia tri design cua o nay la:

```text
sigma_rho = sigma_from_a(0.85,0.90) = 0.069767
```

Mot realization 90 s do duoc `0.065931`, tuc thap hon thiet ke khoang
`-5.5%`. Voi `tau=1.0`, cong thuc finite-window tien doan trung binh chi
lech khoang `-1.1%`, nhung do tan cua mot realization don le vao khoang
`~7%`. Vi vay `-5.5%` nam trong mot sd va la binh thuong.

`tau` va `sigma` trong mot cua so 90 s don le co the lech; V-T1'/V-T2' kiem
bo sinh bang chuoi dai, con V-T1''/V-T2'' chi mo ta mot run.

--------------------------------------------------------------------
## Lenh Kiem Tra Lai

Chay rieng T.2:

```bash
pytest test/test_phase_t_rho_spec.py -q
```

Chay nhom Phase T hien co:

```bash
pytest test/test_phase_t_no_v1_import.py test/test_traffic_v7_hurst.py test/test_phase_t_rho_spec.py -q
```

Chay full suite:

```bash
pytest -q
```

Kiem tay mot trajectory:

```bash
python3 - <<'PY'
from mininet.rho_spec import ou_trajectory, sigma_from_a
import json
t = ou_trajectory(0.85, sigma_from_a(0.85, 0.90), 1.0, 18000, 11)
print(json.dumps(t.as_dict(), indent=2, sort_keys=True))
PY
```

Kiem clamp ca luoi:

```bash
python3 - <<'PY'
from mininet.rho_spec import ou_trajectory, sigma_from_a
for rho_bar in (0.70, 0.85, 0.925, 0.98):
    for a in (0.20, 0.90):
        t = ou_trajectory(rho_bar, sigma_from_a(rho_bar, a), 1.0, 200000, 7)
        print(rho_bar, a, sigma_from_a(rho_bar, a), t.clamp_ratio)
PY
```

--------------------------------------------------------------------
## Sang T.3

T.3 se dung `RhoTrajectory` lam input de time-rescale lich goi, giu dung
`rho(t)` tuc thoi va `c_a` o thang goi.
