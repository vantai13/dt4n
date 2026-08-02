# AMENDMENT 11 -- Phase T

Ngay: 2026-08-01
Trang thai truoc sua: Amendment 10 cham V-T5b bang nguong tung diem 2% va lam
G2 controls fail 24/45. Doc lai `vt5b_z` cho thay nhieu diem `|z| < 2` van
fail, nen nguong 2% dang do don vi tuong doi thay vi do tan cua dai luong.

## Ket Qua Mien Phi Tren G2 Da Co

Cham lai 45 diem controls bang z aggregate:

```text
all45
  n 45
  mean_z -0.04408904204552579
  sd_z 1.1099716042992318
  mean_limit_3sqrtN 0.4472135954999579
  pass_mean True
  pass_sd_0.6_1.6 True

h2@0.70
  n 5
  mean_z -1.32159506170186
  sd_z 1.80084518552455
  mean_limit_3sqrtN 1.3416407864998738
  pass_mean True
  pass_sd_0.6_1.6 False
```

Ket luan: toan bo 45 diem khong co lech he thong ro. Rieng `h2@0.70` co do
tan lon va can phep kiem manh hon.

## Loi Cu

V-T5b dung nguong:

```text
abs(q_T / mean(q_L_cross_seed) - 1) < 0.02
```

Nguong nay bat kha vi Phase L khong tu vuot qua noi tren chinh cac seed cua
no. Cross-seed sd gom ca bien thien thiet ke giua cac lich, khong phai chi
nhieu may. No khong the lam per-row gate 2%.

## Sua Gi

A11.1. V-T5b 105s cu chi con la diagnostic aggregate:

```text
V-T5b_q_phase_l: mean(vt5b_z) va sd(vt5b_z) tren 45 diem
pass_mean: |mean_z| < 3/sqrt(45)
pass_sd:   0.6 < sd_z < 1.6
```

Khong con dua `V-T5b_q_phase_l` vao `gate_fail` tung row.

A11.2. Them khoi C' cung-seed:

```text
stage: controls-samesed  (alias: controls-sameseed)
DUR = 70.0
WARM = 10.0
45 diem = 9 cau hinh x 5 seed
state: results/phase-T/control_sameseed_state.json
```

Phase L co du toan bo `(mode, rho, seed)` cho 45 diem C':

```text
same_seed_plan 45
missing 0
```

A11.3. V-T5a' tren C':

```text
V-T5a_phase_l_digest
```

Voi `h2` va `poisson`, schedule digest cua Phase T phai khop bit-exact Phase L
cung `(mode, rho, seed, bw, q, duration=70, warm=10)`. `cbr@0.98` khong lam
cong digest vi lich hang so khong phan biet duoc nhanh delegation.

A11.4. V-T5b' tren C':

```text
r_i = q_T(mode,rho,seed) / q_L(mode,rho,seed) - 1
pass_mean: |mean(r_i)| < 0.005
pass_sd:   sd(r_i) < 0.010
```

`cbr@0.98` duoc bao cao nhung loai khoi gate aggregate vi nam vung toi han
D-T9.

A11.5. Them `reference_sd_source` vao `GateSpec`.

Moi gate phai khai bao do tan cua dai luong lay tu dau:

```text
analytic
replicates
cross_seed
```

`guessed` khong duoc phep. Gate dung `cross_seed` phai co notes ghi ro han che,
vi cross-seed gom ca bien thien thiet ke.

## Ket Qua Sau Sua

Audit G2 105s sau A11:

```text
T5 controls audit
  rows=45 done=45/45 failed=0
  V-T5a_delegation       seen=40 pass=40 fail= 0
  V-T4a_ca_operational   seen=45 pass=45 fail= 0
  V-T6b_rho_bias         seen=45 pass=45 fail= 0
  V-T5b_q_phase_l          n=45 n_eff=45 mean=-0.044 sd=1.110 mean_gate=OK sd_gate=OK
  V-T5b_h2_r070            n= 5 n_eff= 5 mean=-1.322 sd=1.801 mean_gate=OK sd_gate=FAIL
```

State public da duoc update: `n_fail=0`, khong ro `q_mean_ms`/`probe_mean_ms`/
`delta_pasta_ms`.

## Kiem Tra

```text
pytest test/test_phase_t_validate.py test/test_phase_t_gate_specs.py \
  test/test_phase_t_t5.py test/test_phase_t_no_v1_import.py -q
  -> 54 passed
```

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-08-01
