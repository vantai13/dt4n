# AMENDMENT 21 -- Phase T / T.6h kappa map

Ngay viet: 2026-08-03
Trang thai: T.6g Jensen mechanism check da xong; viet truoc khi chay T.6h
kappa map.

## Boi Canh

T.6g cho thay:

```text
primary corr(err_dyn, err_jensen) = -0.425
primary slope                    = -0.148
negative_err_jensen slope         = +0.148
```

Script T.6g tra `primary_regression_not_confirmed` vi nguong prereg G1/G2
khong phu hop voi y nghia vat ly cua he so goc.

## Dien Giai Moi

Voi:

```text
err_qs     = q_do      - E[f(rho)]
err_jensen = E[f(rho)] - f(rho_bar)
```

Hai oracle bien:

```text
he theo kip hoan hao : q = E[f(rho)]   -> err_qs = 0              -> kappa = 0
he dong bang hoan toan: q = f(rho_bar) -> err_qs = -err_jensen    -> kappa = 1
```

Dinh nghia:

```text
kappa = slope cua err_dyn ~ (-err_jensen)
```

`kappa` la ti le dong bang, bi chan y nghia trong `[0, 1]`. Gia tri T.6g
`kappa ~= 0.148` nghia la he thong theo kip khoang 85% quang duong tu frozen
den quasi-static.

## Vi Sao G1/G2 Cu La Nguong Sai

A21.1. G2 `slope in [0.5, 1.5]` ngam gia dinh he gan frozen hoan toan. Truot
G2 khong phai chong lai ket qua; no la bang chung rang quasi-static hoat dong
tot va `kappa` nho.

A21.2. G1 `|corr| >= 0.7` duoc dat khi chua dua san nhieu vao. Nhieu nam trong
bien phu thuoc `err_dyn` lam suy giam tuong quan nhung khong lam lech he so goc
OLS khi `err_jensen` gan nhu khong nhieu. Do do `corr` chi la chan doan, con
`slope` moi la uoc luong chinh.

A21.3. T.6h phai bao cao hoi quy nguoc `(-err_jensen) ~ err_dyn`. Neu quan he
bi attenuation do nhieu trong `err_dyn`, slope nguoc se nho hon nhieu so voi
`1/kappa`.

## T.6h -- Kappa Map

T.6h dung cac diem da tru baseline C:

```text
x = -err_jensen_ms
y = err_dyn_ms
kappa = OLS slope cua y ~ x, co intercept
```

Base level de giam nhieu seed:

```text
group point = mean theo (mode, rho_bar, a, tau_rho)
```

Bao cao:

```text
global stable non-cbr
by lambda_bin: Lambda<3, 3<=Lambda<10, Lambda>=10
by mode
by rho_bar
by mode_rho_bar cell
by a
by tau_rho
cbr@0.98 tach rieng
```

Moi group bao cao `n`, `kappa`, bootstrap CI95 voi 2000 lan lap, `corr`,
`intercept`, va slope hoi quy nguoc.

## Du Doan Truoc Khi Chay T.6h

```text
K1. Global stable kappa se nam quanh 0.148.
K2. Kappa theo lambda_bin se phang trong do phan giai bootstrap.
K3. Kappa theo a se lon hon tai a=0.9, vi T.6f da thay scaling theo bien do.
K4. cbr@0.98 se lon hon 8 o on dinh hoac bootstrap CI rat rong.
K5. Hoi quy nguoc se co slope nho hon nhieu so voi 1/kappa, xac nhan attenuation.
```

## Nguyen Tac Moi

NT-L25. Khi da co hai oracle bien, bao cao tham so noi suy khong thu nguyen
giua hai oracle truoc khi bao cao sai so tuyet doi theo ms.

NT-L26. Tuong quan bi gioi han boi nhieu trong bien phu thuoc; voi co che
tuyen tinh, slope la dai luong chinh, corr la dai luong chan doan.

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-08-03
