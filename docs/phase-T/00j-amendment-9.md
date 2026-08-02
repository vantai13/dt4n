# AMENDMENT 9 -- Phase T

Ngay: 2026-07-31
Trang thai truoc sua: G2 controls dung o idx 1 vi
`V-T4a_ca_operational` fail. Runner dung la dung: day la gate deterministic.

## Loi Cu

V-T4a dung nguong tuyet doi:

```text
abs(c_a_operational - c_a_design) < 0.02
```

Nhung `c_a_operational` la CV uoc luong tren mau huu han. Voi `h2`, duoi nang
lam sai so CV lon:

```text
h2:      SE(c_a_hat) ~= 0.020-0.021 voi n ~= 44k gap
poisson: SE(c_a_hat) ~= 0.0048
cbr:     SE(c_a_hat) = 0
```

Nguong cu bang khoang 1 SE cua `h2`, nen tao fail gia khoang 30%. Khoi C co
20 diem h2, ky vong 6 fail gia; runner quan sat dung mau do.

## Sua Gi

A9.1. Them noise model delta-method cho CV:

```text
Var(c_hat) ~= (c^2/n) * [ (gamma2 + 2)/4 + c^2 - c*gamma1 ]
```

`gamma1` va `gamma2` lay tu mot mau tham chieu lon cua chinh generator
`build_schedule(mode, 400000, 1.0, seed=7)`.

A9.2. V-T4a doi sang nguong dong:

```text
threshold = max(4 * ca_operational_se(mode, n_gaps), 0.005)
```

Voi 45 diem controls:

```text
h2 ca_op min/max = 2.0020 / 2.0469
h2 threshold     = 0.0821
h2 max |z|       = 2.15
```

Voi `cbr`, nguong moi la `0.005`, chat hon nguong cu `0.02` bon lan.

A9.3. `gate_row()` ghi them vao public state:

```text
ca_operational
ca_operational_se
ca_operational_thr
ca_operational_z
```

A9.4. Them `measurements/gate_specs.py`.

Moi gate khai bao:

```text
kind: transient | deterministic
threshold_fn
noise_fn hoac None neu nhi phan
must_catch
max_false_fail
```

Runner T.5 lay `GATES_TRANSIENT`/`GATES_DETERMINISTIC` tu bang nay, khong copy
tay.

A9.5. Khi rerun mot idx da fail va lan moi pass, `record_row()` xoa failed row
cu cua idx do. Nhu vay state G2 dang co failed_rows pre-A9 co the resume truc
tiep; khi idx 1 pass, failed_rows cu duoc don sach.

## Kiem Tra

Meta-test moi:

```text
test_static_scan_315_preregistered_points_has_no_vt4a_or_vt6b_false_fail
test_gate_specs_noise_gates_false_fail_under_one_percent_200_seed
test_moi_cong_bat_duoc_cac_mutant_da_khai_bao
```

Ket qua quet tinh:

```text
n_points 315
fail_V-T4a 0
fail_V-T6b 0
h2_controls_ca_min 2.0020129098501998
h2_controls_ca_max 2.046851941170963
h2_controls_thr 0.08207322939766841
h2_controls_max_abs_z 2.149036512729069
```

Kiem tra tai thoi diem amendment:

```text
pytest test/test_phase_t_gate_specs.py -q  -> 11 passed
pytest test/test_phase_t_validate.py test/test_phase_t_t5.py test/test_phase_t_no_v1_import.py -q
  -> 29 passed
```

## Ghi Chu Ve Mau Loi

Day la lan thu sau cung mau: mot gate so uoc luong noisy voi gia tri thiet ke
bang nguong tuyet doi khong co noise model. Tu Amendment 9 tro di, them gate
Phase T phai them GateSpec va meta-test false-fail/mutant.

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-07-31
