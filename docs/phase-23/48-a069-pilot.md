# 48 -- Lesson 23.22c PILOT: audit lan INVALID va ket qua S-B

Ngay chay : 2026-08-26

Prereg    : `A069-amendment-69.md`, commit `307b250`

Disclosure: `A069b-amendment-69b.md`, commit `6a24333`

Artifact invalid: `results/SMOKE/phase-23/a069-invalid-selfcal/`

## 0. Lan dau INVALID -- KHONG co phan quyet

Lan dau dung calibration sidecar `self_calibrated`, khong dung hop dong S-B.
`test_no_stale_axes` bat 9 FAIL, gom `sla_axis=UNREGISTERED`. `wrong` va
`err_neo` phu thuoc `w_loss`, nen sau con so duoi day KHONG duoc cham stop-rule.

`G23-270` giu NOT_RUN. Xem `A069c-amendment-69c.md`.

## 1. So do duoc -- chi allowlist da ky

| cell | err_neo | song? | calib/test block | kappa_A | build giay |
|---|---:|:--:|---:|---:|---:|
| poisson@0.740 | 0.001421 | KHONG | 500/500 | 2.275604 | 9.00 |
| poisson@0.780 | 0.075077 | CO | 500/500 | 0.999023 | 8.69 |
| poisson@0.820 | 0.189571 | CO | 500/500 | 0.605957 | 8.77 |
| h2@0.740 | 0.074819 | CO | 500/500 | 0.999756 | 8.75 |
| h2@0.780 | 0.036774 | KHONG | 500/500 | 1.164185 | 9.76 |
| h2@0.820 | 0.014741 | KHONG | 500/500 | 1.366272 | 8.62 |

```text
common_alive_rho          []
stop_no_common_alive_rho  true
stop_low_calib_blocks     []
stop_slow_cells           []
may_proceed_to_prereg     false
```

## 2. Vi sao khong duoc dien giai cau truc

Duoi truc self-calibrated INVALID, hai day so la:

```text
poisson: 0.001421 -> 0.075077 -> 0.189571   (cat 0.05 giua .740 va .780)
h2     : 0.074819 -> 0.036774 -> 0.014741   (cat 0.05 giua .740 va .780)
```

Khong duoc suy diem cat, overlap hay stop tu bang nay. Lan S-B hop le giu
nguyen dung luoi/nguong va se duoc ghi tach o muc 6.

## 3. Capacity va chi phi cua lan INVALID

Ca 6 cell co 500 calib + 500 test block. Build parquet mat 8.62--9.76 giay,
tong 53.59 giay. Day la so chi phi tham khao; phan quyet capacity/cost chinh
lay tu lan S-B hop le.

## 4. Disclosure A069b

Lan chay thu nhat cua `poisson@0.740` da in validation report day du ra stdout
truoc khi bi dung. Artifact do duoc giu tai
`results/SMOKE/phase-23/a069-invalid-selfcal/stdout-leak/`; lan chay sau build
lai tu dau voi stdout builder bi chan. Cell nay mang nhan
`PARTIALLY_UNBLINDED_INPUT_DIAGNOSTICS`. Pilot chi dung bon truong da cho phep;
M-210..M-214 khong chay.

## 5. File va cach tai tao

```text
runner       tools/a069_pilot_new_cells.py
invalid      results/SMOKE/phase-23/a069-invalid-selfcal/
```

SHA-256 summary:

```text
3804a2f7133bc5e8c47e8efb32c469193bfff1c9e52939d850cf8ac36306917d
```

Lenh:

```bash
.venv/bin/python -m tools.a069_pilot_new_cells
```

## 6. Lan S-B hop le

Cho dien sau khi manifest 20 cell da dang ky va pilot chay lai. Den luc do
`G23-270` van NOT_RUN, khong co phan quyet ve `L92`.
