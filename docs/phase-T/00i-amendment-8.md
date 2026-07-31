# AMENDMENT 8 -- Phase T

Ngay: 2026-07-31
Trang thai truoc sua: G1 step response v1 da chay 21 diem. Doi chung bat buoc
S-1 fail va ket qua `T_ab/T_ba` bat doi xung bat thuong.

## Phan Xu

G1 step response v1 khong duoc dung de fit truc hoanh. Tuy nhien,
`measurements.t5_campaign` khong dung `ensemble_average`, nen G2/G3 khong bi
anh huong. Sau smoke A7 sach, duoc chay G2 controls va G3 main ngay, roi chay
step v2 truoc khi mo niem phong T.6.

## Bug 1: Hoan Doi Nhan A/B

`step_trajectory()` dung chu ky:

```text
[rho_a]*hold + [rho_b]*hold
```

Vay A->B nam o nua sau cua chu ky, con B->A nam o nua dau. Ban T.5 dat:

```text
off = 0.0 neu phase == "ab"
```

la nguoc. Hau qua: `q_a` bam `f(rho_b)`, `q_b` bam `f(rho_a)`, dau bien do
bi lat va cua so tu dong cua `T_area_v2` co the khong kich hoat.

Sua:

```text
off = hold_s neu phase == "ab", nguoc lai 0.0
```

Test oracle moi kiem tail cua `ab` khop `f(rho_b)` va tail cua `ba` khop
`f(rho_a)`.

## Bug 2: Thieu SNR Trong Step v1

V1 dung cac buoc rho ke nhau. O tai cao, bien do delay chi khoang 1-2 ms trong
khi nhieu bin theo chu ky doc lap lon. Doi chung S-1 co amp do duoc 3.3 SE va
da tao `T` rac; `cbr 0.95->0.98` co amp khoang 0.013 ms va cung vo nghia.

Them chot:

```text
SE(amp) = q_sd * sqrt(2 / (n_cycles * n_tail_bins))
amp_significant = abs(q_a - q_b) > 5 * SE(amp)
```

Neu amp khong co y nghia, `T_ab_s` va `T_ba_s` tra `NaN`.

## Step v2

Default state moi:

```text
results/phase-T/step_v2_state.json
```

Default PID moi:

```text
t5s2_*
```

Plan live v2:

```text
S-1      h2      0.80 -> 0.80  hold=0.6  N=262  binw=0.020  1 seed
h2       0.60 -> 0.80  hold=0.6  N=262  binw=0.020  3 seed
h2       0.80 -> 0.98  hold=0.6  N=398  binw=0.020  3 seed
poisson  0.80 -> 0.98  hold=0.6  N=150  binw=0.020  3 seed
poisson  0.60 -> 0.80  hold=0.6  N=766  binw=0.020  3 seed
```

Tong 13 diem, raw duration 5988 s ~= 1.66 gio; co overhead ~= 1.7 gio.

Khong chay lai `cbr 0.95->0.98`. Raw cu cua `cbr 0.98->1.00` duoc giu lam
bang chung D-T9; khi re-analyze voi nhan da sua, mot chieu cho `T ~= 28.46 s`
va amp lon 28.96 SE.

## Thien Lech Da Biet

Synthetic budget cho estimator v2 con thien lech khoang -7% den -12% moi run.
Ghi nhan sai so he thong -10% trong tai lieu; khong dung no de dieu chinh sau
khi nhin `err_qs`.

## Hieu Chuan Truc Hoanh

Step response do trung binh tren khoang `[A, B]`. Phan tich T.6 phai fit mot
he so `k` rieng cho tung mode:

```text
T_relax(rho) = k * T_RBM(rho, c_a, B)
```

Fit `k` truoc khi mo niem phong `err_qs`; `k` khong phai bac tu do cua phan
tich chinh.

## Test Them

```text
test_ensemble_average_giu_dung_nhan_binh_on
test_step_estimator_tra_nan_khi_bien_do_khong_y_nghia
test_amplitude_significant_can_5se
```

Kiem tra tai thoi diem amendment:

```text
pytest test/test_phase_t_t5.py -q  -> 12 passed
```

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-07-31
