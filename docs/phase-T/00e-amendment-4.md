# AMENDMENT 4 -- Phase T

Ngay: 2026-07-31
Trang thai truoc sua: Phase T chua chay do song; T.3 moi chi la code/test
ham thuan.
Tai lieu kem: `docs/phase-T/03-two-scale-coupling.md`.

## Da Thay Cong Nao Truoc Khi Sua

Preregistration cu ghi:

```text
V-T4a. c_a trong cua so 100 ms doc lap voi sigma_rho, tau_rho.
V-T6.  rho_thuc_te(t) do tu _bgtx.bin khop rho(t): RMSE < 0.01.
```

Khi cai T.3, hai y nay lo ra la dang so uoc luong noisy voi gia tri thiet ke.
V-T4a trong real time phai bi lam phat khi `lambda(t)` bien thien; V-T6 tren
cua so 100 ms phai co nhieu dem lon voi poisson/h2.

## Bang Chung

Voi cua so 100 ms, ket qua pure schedule cho:

```text
mode      a     RMSE      bias
cbr     0.90   0.00801  -0.00001
poisson 0.90   0.12929  +0.00059
h2      0.90   0.25449  +0.00055
```

`bias` gan 0, nhung RMSE cua poisson/h2 lon hon nguong 0.01 tu 13 den 25 lan.
Ly do la nhieu dem:

```text
sd(rho_hat) = (FRAME_BG/cap) * sqrt(IDC * lambda / W)
```

Cong thuc khop RMSE do duoc trong 1-4% cho poisson/h2 tai `W=0.1` va
`W=0.5`. De h2 dat RMSE < 0.01 can cua so khoang 68 s, gan bang toan bo cua
so do 90 s.

Day khong phai bug schedule. Day la estimator noisy.

## Sua Gi

A4.1. V-T4a duoc dinh nghia lai trong thoi gian van hanh:

```text
u_i = Lambda(T_i)
|CV(u_i - u_{i-1}) - c_design| < 0.02
```

Trong thoi gian van hanh, thang luong bien mat va chi con thang goi. Day la
phep kiem dung cho time-rescaling.

A4.2. Them V-T4b lam doi chung duong cho `c_a` thoi gian that:

```text
c_a_pooled = sqrt((1+c_design^2) * E[lambda] * E[1/lambda] - 1)
```

No xac nhan rescaling va phan biet voi thinning.

A4.3. Thay V-T6 cu bang hai muc:

```text
V-T6a (cong):
  mean(gap_u) = 1.000 trong 0.5%
  CV(gap_u)   = c_design voi sai so tuyet doi < 0.02

V-T6b (mo ta):
  rho_hat window co bias < 0.002
  RMSE khop cong thuc nhieu dem trong 20%
```

Ghi chu sau Amendment 7: nguong `bias < 0.002` bi thay bang
`abs(rho_bias_z) < 3`, voi `rho_bias_z` chuan hoa theo dao dong renewal tai
bien warm-up.

A4.4. Them code/test:

```text
mininet/rho_schedule.py
test/test_phase_t_rho_schedule.py
```

## Khong Sua

```text
rho_spec.py giu nguyen
load_spec.py giu nguyen
probe van Poisson hang 20 pps, seed + 500000
duong sigma_rho=0 van phai khop digest Phase L
grid mode/rho/a/tau/seed giu nhu Amendment 2/3
```

## Ghi Chu Ve Mau Loi

Day la lan thu tu mot cong ban dau fail vi so uoc luong noisy voi gia tri
thiet ke:

```text
V-T1: sigma_hat trong 90 s co finite-window bias
V-T2: tau_hat trong 90 s noisy hon nua
V-T4: c_a real-time pooled bi lam phat dung ly thuyet
V-T6: rho_hat window co shot noise
```

Quy tac tu Amendment 4 tro di: moi gate phai so uoc luong voi ky vong cua
chinh uoc luong do, hoac doi sang mot dai luong gan nhu khong noisy.

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-07-31
