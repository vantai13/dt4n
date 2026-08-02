# AMENDMENT 10 -- Phase T

Ngay: 2026-08-01
Trang thai truoc sua: G2 controls da chay xong 45/45 theo cac gate A9, nhung
chua cham V-T5 -- cong doi chung am noi Phase T voi Phase L.

Ghi chu sau Amendment 11: phan V-T5b tung diem 2% trong amendment nay bi thay
bang z aggregate va khoi C' cung-seed. Ket luan "V-T5b fail 24/45" la fail gia
do nguong 2% bat kha.

## Loi Cu

Khoi C ton tai de kiem `sigma_rho = 0` co tai tao Phase L hay khong, nhung
`control_state.json` khong co gate V-T5. Nhu vay G2 da chay ma chua kiem dung
thu no duoc tao ra de kiem.

## Sua Gi

A10.1. Them V-T5a:

```text
V-T5a_delegation
```

Voi `h2` va `poisson`, row `sigma_rho = 0` phai co schedule digest khop voi
lich Phase L constant-load duoc xay tu cung `(mode, rho_bar, bw, seed,
duration_s)`. `cbr` bi skip vi lich hang so khong phan biet duoc nhanh
delegation.

A10.2. Them V-T5b:

```text
V-T5b_q_phase_l
```

`q_mean_ms` cua khoi C duoc doc tu sealed row de so voi Phase L reference
nhom theo `(mode, rho)` tai `bw=6, q=13, probe_pps=20`. Public state chi ghi:

```text
vt5b_z
vt5b_ref_n
```

Khong ghi `q_mean_ms`, `probe_mean_ms`, hay `delta_pasta_ms` ra public state.

A10.3. Them audit CLI:

```bash
sudo -n env PYTHONPATH="$PWD" python3 -m measurements.t5_controls_audit \
  --state results/phase-T/control_state.json \
  --sealed-dir results/phase-T/sealed \
  --update-state
```

Lenh nay cham lai 45 diem da co, ghi V-T5 vao public state, nhung khong mo niem
phong response metrics.

A10.4. Sua cong tap hop z:

```text
n_eff = so nhom neu sd_giua_nhom > 1.5 * sd_trong_nhom
```

Moi GateSpec khai bao them:

```text
corr_group: "seed" | "rho_bar" | None
```

Voi `ca_operational_z`, cac diem cung seed tuong quan manh; n hieu dung la so
seed, khong phai so row.

A10.5. Them `--force-idx` cho `measurements.t5_campaign` de rerun mot diem da
done va thay row cu trong state. Dung cho idx 0 cua G2, vi diem nay chay truoc
A9 nen public row cu thieu cac truong `ca_operational_*`.

## Ket Qua Tren G2 Da Co

Cham bang dung interpreter live (`sudo -n env PYTHONPATH="$PWD" python3`):

```text
T5 controls audit
  rows=45 done=45/45 failed=24
  V-T5a_delegation       seen=40 pass=40 fail= 0
  V-T5b_q_phase_l        seen=45 pass=21 fail=24
  V-T4a_ca_operational   seen=45 pass=45 fail= 0
  V-T6b_rho_bias         seen=45 pass=45 fail= 0
  rho_bias_z               n=45 n_eff=45 mean=+0.241 sd=0.897 mean_gate=OK sd_gate=OK
  ca_operational_z_h2      n=20 n_eff= 5 mean=+0.818 sd=0.660 mean_gate=OK sd_gate=OK
  ca_operational_z_poisson n=20 n_eff= 5 mean=+0.742 sd=0.797 mean_gate=OK sd_gate=OK
```

Ket luan: V-T5a sach, nhung V-T5b fail 24/45 theo nguong 2% da dang ky. Theo
luat T.5, dung truoc G3 va di nhanh T8(b) de dieu tra Phase T co tai tao Phase
L ve delay hay khong.

Ghi chu interpreter: live campaign chay bang `sudo python3` (system Python).
Audit digest V-T5a phai chay bang cung interpreter nay; khong dung `python3`
conda cua user shell de ket luan bit-exact provenance.

## Kiem Tra

```text
pytest test/test_phase_t_validate.py test/test_phase_t_gate_specs.py \
  test/test_phase_t_t5.py test/test_phase_t_no_v1_import.py -q
  -> 48 passed

pytest -q
  -> 337 passed, 4 skipped
```

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-08-01
