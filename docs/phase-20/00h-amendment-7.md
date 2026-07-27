# AMENDMENT 7 - Phase 20 Acceptance And Remaining Blocker

Ngay: 2026-07-27
Commit do chinh: `a5ce833`
Tag do chinh: `phase-20-measured`

Trang thai: G1-G6 pass tren trace offered da dong bang, nhung gate chua dong
chinh thuc vi bat dinh giua-trace chua duoc do.

## A7.1 Ket Qua Chinh

Hieu chuan tu hoi tu:

```text
w_loss: 2500 -> 1451.38 -> 1451.38
T_delay = 14.5138 ms
T_loss = 0.010
optimal_violation = 15.000%
tie_rate = 0.0000%
```

Diem van hanh dung rang cua AoI that:

```text
mean_age = 0.305 s
err      = 0.17286, CI95 [0.1557, 0.1885]
d_sla    = 0.07287, CI95 [0.0650, 0.0818]
regret_on_error = 33.67 ms
twin_violation = 22.09% vs optimal_violation = 14.80%
```

Co che P3':

```text
P(error | crossed)     = 36.1%
P(error | not crossed) = 4.0%
risk_ratio             = 8.94
share_errors_crossed   = 86.3%
```

G1, G2, G4, G5 pass. G6 pass voi pham vi ro rang: day la kiem chung mo hinh
AR(1) so voi trace Mininet, khong phai kiem chung cheo hai testbed doc lap.

## A7.2 Kiem Chung Noi Tai

Ba kiem chung noi tai cho thay thuoc do khong dem lech:

```text
IC1 gap = err * regret_on_error khop 0.0000% tren nhieu diem.
IC2 NC4 = 0.7494 / 0.7503 / 0.7501 vs ly thuyet 0.750000.
IC3 NC3 = 0.611 / 0.643 / 0.613 vs ly thuyet 1 - sum(p_a^2) = 0.62348.
```

So voi Phase 14A, SNR tang tu `0.38` len `17.1`, tuc khoang `45x`. Nguyen
nhan khong phai may man: dai luong do, san khau, va thang AoI deu da duoc chot
truoc khi do.

## A7.3 G3 Duoc Sua

Khong dung `p_one_sided` cua Spearman nua. Ly do: 9 gia tri `err(z)` duoc tinh
tren cung mot trace, phu thuoc manh voi nhau; p-value Spearman gia dinh quan
sat doc lap.

G3 moi:

```text
G3 PASS iff ca 8 hieu lien tiep err(z_i+1) - err(z_i)
co CI Bonferroni 95% family-wise nam hoan toan tren 0.
```

`decision_error.py` bao cao truong:

```text
gate.G3_pairwise_err_delta_bonferroni_positive
gate.G3_pairwise
```

Spearman chi con la thong tin mo ta:

```text
gate.spearman_descriptive_only
```

## A7.4 Jensen Duoc Sua

Khoang cach Jensen phai so:

```text
f(E[age_that]) - E[f(age_that)]
```

khong phai so `f(z*=0.298)` voi operational. Tren luoi 10 ms, rang cua thuc te
co tuoi roi rac `{0.06, ..., 0.55}` nen `E[age] = 0.305 s`.

`decision_error.py` dung noi suy tu cac diem fixed-z de bao cao:

```text
summary.jensen_reference_age_s
summary.jensen_reference_err
summary.jensen_reference_d_sla
summary.jensen_gap_err
summary.jensen_gap_d_sla
```

Truong `nominal_z_star_gap_*` duoc giu rieng de truy vet sai khac voi so cu.

## A7.5 Van De Chan: Bat Dinh Giua-Trace

Ba seed `100,101,102` trong `decision_error.py` chi doi bootstrap va negative
controls. Uoc luong diem giong nhau den chu so cuoi vi cung dung mot trace.

Bootstrap do bat dinh trong-trace. No khong the do bat dinh giua lan chay
Mininet, gom hien thuc luu luong moi, jitter OS/CPU, va sai so mau cua
`rho_mean`, `sigma`, `tau` tren tung trace.

Rui ro gate:

```text
G1 an toan: can SD_giua_trace ~ 0.063-0.116 moi lat ket luan.
G2 can do: fail neu SD_giua_trace > 0.0215.
```

Viec can chay:

```text
2 trace Mininet moi voi --seed 1 va --seed 2, duration 1800 s.
Sau do chay decision_error tren seed 0/1/2 voi --freeze-calibration.
Bao cao SE_total = sqrt(SE_bootstrap^2 + SD_giua_trace^2).
```

Lenh chi tiet nam trong `runbooks/phase-20-traffic-v7-tmux.md`.

## A7.6 Tooling Added

`measurements/decision_error.py` them:

```text
--freeze-calibration
G3 pairwise Bonferroni CIs
Jensen gap at mean operational age
G6 scope wording
```

`measurements/summarize_decision_error_replicates.py` doc ba file JSON
decision-error va bao cao:

```text
err.between_trace_sd
err.se_total
d_sla.between_trace_sd
d_sla.se_total
d_sla.ci95_total
gates.G2_d_sla_total_lower_ge_003
```
