# AMENDMENT 3 -- Phase T

Ngay: 2026-07-31
Trang thai truoc sua: `00c-amendment-2.md`, Phase T chua chay do song.
Tai lieu kem: `docs/phase-T/02-rho-spec.md`.

## Da Thay So Nao Truoc Khi Sua

Trong T.1/Amendment 2, cong thuc rang buoc bien do tai duoc ghi:

```text
sigma_max = (1.05-rho_bar)/2.58
```

Cong thuc nay chi xet khoang cach toi bien tren. Khi viet va test
`mininet/rho_spec.py`, loi nay lo ra o `rho_bar=0.70`, noi bien duoi 0.50 moi
la bien gan hon:

```text
rho_bar  sig_max sai  sig_max dung  clamp tai a=0.90 neu dung so sai
0.700       0.1357       0.0775       5.28%
0.850       0.0775       0.0775       0.21%
0.925       0.0484       0.0484       0.21%
0.980       0.0271       0.0271       0.21%
```

Chi `rho_bar=0.70` bi anh huong, nhung no vuot V-T3 `n_clamped/n_steps < 1%`
hon 5 lan neu dung cong thuc sai.

## Sua Gi

A3.1. Dinh chinh `sigma_max` thanh rang buoc hai phia:

```text
sigma_max = min(rho_bar-0.50, 1.05-rho_bar) / 2.58
sigma_rho = a * sigma_max
a in {0.20,0.90}
```

A3.2. Bien rang buoc nay thanh code chay duoc:

```text
mininet/rho_spec.py::sigma_max_feasible()
mininet/rho_spec.py::sigma_from_a()
```

A3.3. Them test bao ve quyet dinh:

```text
test/test_phase_t_rho_spec.py::test_sigma_max_lay_min_cua_hai_phia_khong_phai_mot_phia
test/test_phase_t_rho_spec.py::test_vt3_moi_o_luoi_co_ti_le_kep_duoi_1_phan_tram
```

Ket qua kiem tay voi cong thuc moi:

```text
rho=0.700 a=0.90 sigma=0.069767 clamp=0.0325%
rho=0.850 a=0.90 sigma=0.069767 clamp=0.0455%
rho=0.925 a=0.90 sigma=0.043605 clamp=0.0455%
rho=0.980 a=0.90 sigma=0.024419 clamp=0.0455%
```

Tat ca thoa V-T3.

## Khong Sua

```text
truc a giu {0.20,0.90}
rho_bar grid giu {0.70,0.85,0.925,0.98} cho h2/poisson
cbr van chi rho_bar=0.98
tau_rho van {0.2,1.0,5.0}
dt van 0.005 s
```

## Ghi Chu

Day la loi go cong thuc trong T.1/Amendment 2, khong phai HARKing. T.2 chua
chay do song nao; test pure da bat loi truoc khi campaign bat dau.

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-07-31
