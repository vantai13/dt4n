# AMENDMENT 2 -- Phase 21R

Ngay ky: 2026-08-12
Nguoi ky: Codex theo yeu cau owner repo DT4N
Boi canh: sau khi chay `cert/build_calib_set_v2.py` va tinh diem neo P9b.
CHUA tinh `q_hat`, CHUA tinh bat ky ti le accept nao.

## B1. Ghi nhan du doan truot, khong sua du doan

```text
tien dang ky : err_anchor in [0.27, 0.31]
do duoc      : err_anchor = 0.220835
CI95 block   : [0.213463, 0.227895]
ket qua      : TRUOT -- thap hon can duoi 18%
```

Chan doan: du doan neo vao `err(z=0.55) = 0.290467`, tuc tuoi toi da. AoI
rang cua lai phan bo deu tren `[0.055, 0.550]`, nen diem neo dung la ky vong
theo phan phoi tuoi:

```text
E_z[err(z)] uoc luong tu 20R = 0.216273
err(z = tuoi trung binh)     = 0.226360
err(z = 0.55)                = 0.290467
do duoc                      = 0.220835
```

`err(z)` la ham lom va tang theo `z`, nen `E[err(z)] < err(E[z]) < err(z_max)`.
Lesson 21R.7 khi noi "twin phai tuoi hon z*" phai noi ro do la rang buoc tren
AoI toi da hay AoI ky vong.

## B2. Danh sach o -- ap quy tac da ky

P4 da ky quy tac loai moi o co `err < 0.01` vi bai toan rong. Ap dung quy tac
da co truoc vao diem neo moi:

```text
poisson@0.700  err_neo = 0.000000  -> suy bien, doi chung duong
h2@0.850       err_neo = 0.004847  -> loai
h2@0.925       err_neo = 0.001175  -> loai
```

`poisson@0.700` la bat ngo co ich. Duoi sigma van hanh `0.04622`, 20R sawtooth
co `err = 0.145858`; duoi sigma co dinh `0.0096`, anchor moi co `err = 0`.
Do kho cua bai toan quyet dinh bi bien do dao dong tai chi phoi, khong chi boi
muc tai trung binh.

Danh sach o sau Amendment 2:

```text
CHINH  : poisson@0.925                err_neo 0.220835
PHU    : poisson@0.850, h2@0.700      err_neo 0.219062 / 0.127259
PC     : cbr@0.700, poisson@0.700     err_neo 0.000000 / 0.000000
LOAI   : h2@0.850, h2@0.925, h2@0.960
N/A    : cbr@0.925, cbr@0.960
```

## B3. He qua cho 21R-G10

Chi con 3 o khong suy bien, va 2/3 cung ho `poisson`. Chung khong doc lap hoan
toan, dung rui ro R5 da ghi. O doc lap that su duy nhat la `h2@0.700`.

Phat bieu bat buoc:

```text
Tinh ben vung duoc kiem tren dung mot ho luu luong thu hai.
```

Bo sung tien dang ky: chay them duong van hanh (`sigma = sigma_max` theo o, da
giao cho Lesson 21R.8) lam kiem chung ben vung phu. Duoi sigma van hanh, cac o
sau khong suy bien:

```text
poisson@0.700  err 0.145858
h2@0.700       err 0.296182
h2@0.850       err 0.255145
```

Ket qua headline van dung sigma co dinh de so duoc voi 20R.

## B4. So da chot

Nguon tong hop: `results/phase-21R/anchor.json`.

| Cell | Role | err | d_sla | CI95(err) | pair_ok | clip |
|---|---|---:|---:|---:|---:|---:|
| poisson@0.925 | CHINH | 0.220835 | 0.060125 | [0.213463, 0.227895] | 0.9876 | 0.000000 |
| poisson@0.850 | PHU | 0.219062 | 0.059699 | [0.211749, 0.226113] | 0.9826 | 0.000000 |
| h2@0.700 | PHU | 0.127259 | 0.001023 | [0.120588, 0.134359] | 0.9995 | 0.000000 |
| cbr@0.700 | PC | 0.000000 | 0.000000 | [0.000000, 0.000000] | 1.0000 | 0.000000 |
| poisson@0.700 | PC | 0.000000 | 0.000000 | [0.000000, 0.000000] | 1.0000 | 0.000000 |
| h2@0.850 | LOAI | 0.004847 | 0.000118 | [0.003607, 0.006278] | 1.0000 | 0.000000 |
| h2@0.925 | LOAI | 0.001175 | 0.000094 | [0.000544, 0.001935] | 1.0000 | 0.000000 |

```text
eps_regret = 0.10 * T_delay:
poisson@0.925 3.2222 ms
poisson@0.850 2.4244 ms
h2@0.700      2.8614 ms

n_block = 1000 tong, 1000 tren moi bin (ca luoi chinh lan phu)
sau chia 50/50 = 500 block/bin; nguong 9; du 55 lan

clip_fraction = 0.000000 o moi o
NC1 z=0: e_stale_margin_max_abs = 0.0
V5: tai tao 20R fixed-z voi max_abs_diff = 0.0
```
