> **SUPERSEDED cho con so `err_dyn` (2026-08-08).**
>
> Bang duoi day dong bang o commit `f91b4ad`. Artifact hien hanh
> `results/phase-T/t6e_paired.json` (script `t6_analyze_v4_t6e_paired`) cho:
>
> ```text
> h2       mean -0.0342  se 0.0172  n=120   CI95 [-0.0679, -0.0004]
> poisson  mean -0.0313  se 0.0184  n=120   CI95 [-0.0674, +0.0048]
> cbr      mean -0.6166  se 0.2108  n= 30   CI95 [-1.0298, -0.2034]
> ```
>
> Con so `-0.0200 +/- 0.0046` KHONG tai lap duoc tu artifact hien hanh. Da thu
> cac tap con sau, khong tap nao khop:
>
> ```text
> bo cbr                                n=249  mean -0.0335  se 0.0121
> class=khong_phan_biet_duoc_o_phan_giai n=152  mean -0.0276  se 0.0078
> class=quasi_static_khong_dung          n= 78  mean -0.0429  se 0.0335
> class=cong_vao_band_21R                n= 19  mean -0.0425  se 0.0530
> block=A                                n=240  mean -0.0327  se 0.0126
> ```
>
> Ket luan: day la chenh lech GIUA HAI LAN CHAY (commit khac nhau), khong phai
> hai estimand khac nhau. Moi trich dan MOI phai dung artifact, khong dung bang
> duoi day. `measurements/quasistatic_band.py` doc truc tiep tu artifact va co
> test canh (`test_phase_t_err_dyn_is_read_from_the_artifact_not_hardcoded`).

# PHU LUC -- Xap xi quasi-static (khong thuoc Gate T)

**Trang thai: EXPLORATORY. Dong bang theo so lieu o commit `f91b4ad`.
Khong phan tich them cho den Phase 21R.**

## Vi sao co phu luc nay

Phu luc nay sinh ra trong qua trinh chay chien dich Phase T. No khong phuc vu
gate nao cua Phase T. No duoc giu lai vi do truc tiep thanh phan dong cua
`e_model`, la dau vao cho Phase 21R khi tach sai so model/staleness.

## Ket qua dong bang

Phan tach:

`err_dyn = kappa(Lambda) x err_jensen(sigma_rho^2)`

- `kappa = 0`: theo kip hoan hao.
- `kappa = 1`: dong bang hoan toan.
- Hai thua so bien thien nguoc chieu theo `tau`, nen co the triet tieu trong
  phep do sai so tuyet doi. Day la ly do D-T3 trong gan phang.

| Dai luong | Gia tri |
|---|---|
| `kappa` toan cuc | 0.148, CI95 [0.002, 0.317], corr 0.425 |
| `kappa(Lambda < 3)` | 0.345, CI95 [0.024, 0.413], corr 0.927 |
| `kappa(3 <= L < 10)` | 0.094, CI95 [-0.783, 0.468], corr 0.361 |
| `kappa(Lambda >= 10)` | 0.013, CI95 [-0.323, 0.386], corr 0.034 |
| `err_dyn` tuyet doi | -0.0200 +/- 0.0046 ms; CI95 [-0.0290, -0.0110] |
| Scaling theo bien do | `sigma^2` (z=-0.018); thiet bi bi bac bo (z=+3.413, p=6.4e-4) |
| `cbr @ rho=0.98` | -0.617 +/- 0.166 ms; CI95 [-1.077, -0.156] |
| `kappa(cbr @ rho=0.98)` | 0.293, CI95 [-0.164, 2.022], corr 0.459 |
| `T_relax(cbr, rho->1)` | 28.5 s (do truc tiep T.1); bat doi xung len/xuong lon |

## Canh bao khi dung lai o 21R

1. Cac KTC cua `kappa` theo bin chong nhau. Chua bootstrap hieu
   `kappa(L<3) - kappa(L>=10)`, nen chua duoc tuyen bo `kappa` phu thuoc
   `Lambda` co y nghia.
2. `by_lambda` va `by_tau` khong doc lap: `Lambda = tau/T_relax` va `tau` chi
   co 3 gia tri, nen chia theo `Lambda` thuc chat gan voi chia theo `tau`.
3. `kappa(a=0.2) = -0.516` la phi vat ly, do bien doc lap gan nhu khong bien
   thien khi `sigma_rho` nho. Khong dung no nhu mot ket qua.
4. `kappa(cbr@0.98)` co `n=6` va CI rat rong. Ket luan ve `cbr` phai dung
   tren `err_dyn` tuyet doi va `T_relax`, khong dua tren `kappa`.
5. `corr = 0.425` nam gan tran suy giam do nhieu. Khong dung `corr` de danh
   gia co che; dung he so goc, vi nhieu o bien phu thuoc lam giam `r` nhung
   khong lam lech he so goc.

## Viec con lai neu quay lai o 21R

- Bootstrap hieu `kappa(L<3) - kappa(L>=10)`, khong so hai KTC rieng.
- Mo hinh tuong tac tren toan bo diem on dinh:
  `err_dyn ~ (-err_jensen) * (b0 + b1*log10(Lambda))`, kiem `b1 < 0`.
