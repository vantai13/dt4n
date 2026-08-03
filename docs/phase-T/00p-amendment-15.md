# AMENDMENT 15 -- Phase T / T.6b exploratory baseline

Ngay viet: 2026-08-03
Trang thai: viet sau khi da mo niem phong T.6 confirmatory, truoc khi chay
phan tich baseline khoi C.

## Boi Canh

T.6 confirmatory da chay dung quy trinh blinded:

```text
fake sealed: mean(err_qs_corrected) = +0.00006 ms, sd = 0.0029 ms
real sealed: mean(err_qs_corrected) = -0.116 ms,   sd = 0.458 ms
```

D-T2 fail manh, nhung D-T3 la chan doan quan trong hon:

```text
Lambda < 3       mean|err_qs_corrected| = 0.1605 ms
3 <= Lambda < 10 mean|err_qs_corrected| = 0.1875 ms
Lambda >= 10     mean|err_qs_corrected| = 0.1666 ms
```

Sai so phang theo `Lambda` khong co hinh dang cua sai so quasi-static, vi theo
dinh nghia sai so quasi-static phai tien ve 0 khi
`Lambda = tau_rho / T_relax -> infinity`. Dieu nay goi y `err_qs` dang bi chi
phoi boi lech mo hinh chung cua `f_L(mode,bw,q,rho)`.

Bang chung ho tro sau T.6:

```text
poisson mean = -0.017 ms, sd = 0.202
h2      mean = -0.098 ms, sd = 0.206
cbr     mean = -0.583 ms, sd = 1.155
```

## Trang Thai Phan Tich

Phan tich nay la **EXPLORATORY**.

Amendment 10 khai bao khoi C ton tai de kiem `sigma_rho = 0` co tai tao Phase L
hay khong. Viec dung khoi C lam baseline lech mo hinh khong nam trong T.0, nen
tat ca ket qua T.6b phai duoc gan nhan exploratory trong paper.

Ket qua confirmatory `err_qs` cua T.6 van phai duoc bao cao day du. T.6b khong
duoc thay the ket qua confirmatory.

## Phep Tach Khoa Truoc Khi Chay

Khoi C co `a = 0`, `duration_s = 105`, `warmup_s = 15`, `meas_s = 90`, va 9 o
`(mode, rho_bar)` khop 1-1 voi khoi chinh. Khi `a = 0`, `rho(t)` hang theo cau
tao, nen sai so quasi-static bang 0 theo dinh nghia.

Cho tung o `o = (mode, rho_bar)`:

```text
baseline_C(o) = mean_{5 seed} err_qs_corrected_C(o)
SE_C(o)       = sd_C(o) / sqrt(5)
err_dyn(i)    = err_qs_corrected(i) - baseline_C(mode_i, rho_bar_i)
SE_dyn(i)     = sqrt(SE_err_qs_corrected(i)^2 + SE_C(o)^2)
```

Baseline chi duoc uoc luong tu khoi C. Khong uoc luong baseline lai tu khoi
chinh, khong fit them theo `a`, `tau_rho`, hay seed.

## Du Doan T.6b

Cac du doan duoi day duoc dien truoc khi chay script T.6b tren sealed khoi C:

```text
P1. mean|err_dyn| tren h2/poisson se giam con <= 0.140 ms
    (moc hien tai: mean theo 3 bin Lambda la khoang 0.171 ms).

P2. D-T3 tren err_dyn se co xu huong don dieu:
    mean|err_dyn| tai Lambda < 3 > 3 <= Lambda < 10 > Lambda >= 10.

P3. So diem "quasi_static_khong_dung" tren toan bo 270 diem chinh se giam
    tu 132/270 xuong <= 80/270.

P4. cbr@rho_bar=0.98 van la o lech/bat on nhat sau khi tru baseline_C.
```

## Bao Cao Bat Buoc

T.6b phai xuat bang 9 o `(mode, rho_bar)`:

```text
mode, rho_bar, n_C, baseline_C, SE_C,
n_main, mean_err_qs_corrected, mean_err_dyn, sd_err_dyn
```

T.6b phai chay lai D-T2, D-T3, D-T4 tren `err_dyn`, dong thoi giu nguyen bang
T.6 confirmatory tren `err_qs_corrected`.

## Gioi Han

Sai so mo hinh la nhieu chung cua `f_L`, khong giam theo `sqrt(n_main)`. Thanh
sai so he thong cua baseline phai dung `SE_C(o)`, va chi co 5 seed moi o.

`cbr` chi co tai `rho_bar = 0.98`, nen moi ket luan ve cbr phai so voi
`h2@0.98` va `poisson@0.98`, khong so voi trung binh toan cuc cua h2/poisson.

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-08-03
