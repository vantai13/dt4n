# AMENDMENT 7 -- Phase T

Ngay: 2026-07-31
Trang thai truoc sua: G0 smoke T.5 da chay 6 diem. Hai diem fail
`V-T6b_rho_bias` sau retry, nhung cac cong ha tang khac deu xanh.

## Bang Chung Tu Smoke

Smoke co mau fail:

```text
h2      rho=0.85 a=0.20  rho_bias = -0.0028475
poisson rho=0.85 a=0.20  rho_bias = +0.0024786
cbr     rho=0.98         rho_bias gan 0
```

Fail chi xuat hien o mode co `c_a` lon. Day la dau hieu cua dao dong renewal
tai bien warm-up, khong phai drift ha tang.

## Loi Cu

V-T6b dung nguong tuyet doi:

```text
abs(rho_bias) < 0.002
```

Nguong nay khong co noise model. Lich duoc dung cho `[0, duration]`, nen tong
so goi cuoi bi ghim. Nhung phan goi truoc warm-up khong bi ghim:

```text
sd(N(u)-u) = c_a * sqrt(u), voi u = Lambda(warm_s)
```

Voi `warm_s=15`, `duration=105`, `meas_s=90`:

```text
h2      sd(rho_bias) ~= 0.00356
poisson sd(rho_bias) ~= 0.00178
cbr     sd(rho_bias) ~= 0.000022
```

Nguong cu tao fail gia khoang 57% cho `h2` va 21% cho `poisson`.

## Sua Gi

A7.1. V-T6b doi sang z-score theo mode:

```text
rho_bias_sd_pred = (FRAME_BG/cap) * sqrt(c_a^2 * Lambda(warm_s) + 1) / meas_s
rho_bias_z       = rho_bias / rho_bias_sd_pred
pass             = abs(rho_bias_z) < 3
```

So hang `+1` trong can bac hai la floor bao thu do `int()`/lam tron cua so.
Voi `cbr`, nguong moi chat hon nguong cu khoang 30 lan.

A7.2. Them cong tap hop:

```text
gate_rho_bias_aggregate(rows):
  pass_mean = abs(mean(z)) < 3/sqrt(n)
  pass_sd   = 0.6 < sd(z) < 1.6
```

Cong nay bat duoc drift nho nhung co he thong ma cong tung diem co the bo sot.

A7.3. Phan loai retry:

```text
Transient    : A5-7_socket_drops, A5-7_n_late, A5-7_n_foreign
Deterministic: V-T0, V-T3, V-T4a, V-T4b, V-T6a, V-T6b
```

Runner chi retry khi tat ca fail deu la transient. Fail deterministic thi ghi
vao `failed_rows` va dung chien dich.

A7.4. Tach state public khoi du lieu niem phong.

`results/phase-T/*_state.json` chi chua gate/provenance/diagnostic co the
nhin. Cac truong response:

```text
q_mean_ms, q_p50_ms, q_p90_ms, q_p95_ms, q_p99_ms, q_sd_ms
probe_mean_ms, delta_pasta_ms, se_batch_ms, se_naive_ms
```

duoc ghi rieng vao:

```text
results/phase-T/sealed/{pid}.json
```

Khong mo thu muc `sealed/` cho den T.6.

## Test Them

```text
test_rho_bias_sd_khop_mo_phong_200_seed_va_giam_fail_gia
test_gate_rho_bias_aggregate_bat_drift_nho
test_retry_chi_danh_cho_cong_transient
test_public_state_khong_lo_metric_niem_phong
```

Kiem tra tai thoi diem amendment:

```text
pytest test/test_phase_t_validate.py test/test_phase_t_t5.py -q  -> 23 passed
```

## Ghi Chu Ve Mau Loi

Day la cong thu nam cung mau: so uoc luong noisy bi so voi gia tri thiet ke
bang mot nguong tuyet doi khong co noise model.

```text
V-T1   sigma_hat
V-T2   tau_hat
V-T4   c_a real-time
V-T6a  rate/counting
V-T6b  rho_bias tai bien warm-up
```

Quy tac them: moi nguong gate phai co dong dan xuat noise ngay ben canh.

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-07-31
