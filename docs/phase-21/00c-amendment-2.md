# AMENDMENT 2 - Phase 21

Ngay: 2026-07-28
Trang thai truoc sua: `00b-amendment-1.md`, commit `43b3863`

## Da Thay So Nao Truoc Khi Sua

Nguon: report measured sinh tu `cert/build_calib_set.py` truoc khi sua measured.

```text
dt measured = 0.2 s
z chi co 3 muc: {0, 0.2, 0.4} tren trace 0-3 va {0.2, 0.4, 0.6} tren trace 4
n_blocks = 20 vi B_BLOCK hard-code 1435 mau thay vi 14.35 giay
u_max ~= 3.6e14 do chia cho sigma_z ~= 0 khi z=0
q_hat(z_bin 0) = 0.0 vi z=0 bi clip vao bin tuoi dau
```

## Sua Gi

M1. Doi block va common-window tu don vi mau sang don vi vat ly:

```text
B_BLOCK_S = 14.35 s
T0_S      = 4.0 s
block_len_samples = round(B_BLOCK_S / dt_s)
t0_steps          = round(T0_S / dt_s)
```

M2. Loai hoan toan hang `z = 0` khoi tap calibration. Ly do: `z=0` nghia la
`rho_hat = rho`, score bang 0 tat dinh. Day la NC1 cua Phase 20, khong phai mau
hieu chuan.

M3. Dung age bins rieng cho measured:

```text
M-B1 [0.10, 0.30)  -> z = 0.2
M-B2 [0.30, 0.70)  -> z = 0.4 va 0.6
```

M4. Giu nguyen `U_EDGES = [0,1), [1,2), [2,3), [3,inf)`.

M5. Neu measured van co `n_g < 39` thi khong bao cao Bonferroni `alpha/K`; chi
bao cao `alpha` va ghi ro do rang buoc `n >= ceil(1/alpha)-1`.

## Phat Bieu Trong Paper

```text
The measured-telemetry branch is a robustness check at reduced age resolution
(200 ms sampling admits only two usable age levels); it is not used to calibrate
the reported certificates.
```

## Khong Sua

```text
alpha = 0.10
U_EDGES
w_loss / T_delay / T_loss
offered AGE_EDGES
offered source remains primary
```

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-07-28
