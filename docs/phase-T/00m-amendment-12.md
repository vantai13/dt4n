# AMENDMENT 12 -- Phase T

Ngay: 2026-08-02

## Van De

V-T5a' tren C' bao digest lech khi audit bang conda Python 3.13, nhung live
campaign chay bang `/usr/bin/python3` 3.10. Day la mismatch interpreter, khong
phai loi trong `load_spec.py` hay Phase L.

CPython >= 3.12 doi float `sum()` sang compensated summation. `normalize_rate()`
dung `sum(gaps) / len(gaps)`, nen he so chuan hoa co the lech ULP va lam digest
lich khac nhau giua interpreter.

## Sua Gi

Them `_mean_stable()` trong `mininet/load_spec.py` voi phep cong tuan tu ro
rang, va doi duy nhat `normalize_rate()` sang dung ham nay. Muc tieu la khoa
hanh vi so hoc da sinh Phase L, khong doi ket qua live.

Them frozen digest test tu Phase L:

```text
test/test_load_spec_frozen_digests.py
```

Them provenance tang moi truong:

```text
measurements/provenance.py
row["env"] = env_fingerprint()
```

Them `GateSpec.relax_policy` de tach ba truc:

```text
kind                 = retry policy
reference_sd_source  = nguon do tan
relax_policy         = co duoc noi long gate hay khong
```

Ba cong bit-exact duoc danh dau `relax_policy="never"` va
`reference_sd_source="exact"`:

```text
V-T0_digest_khop
V-T5a_delegation
V-T5a_phase_l_digest
```

## Kiem Tra

Truoc sua:

```text
live  /usr/bin/python3 frozen digests -> 7/7 pass
conda 3.13             frozen digests -> 4 failed, 3 passed
```

Trong 6 mau vang, 3 mau co rang:

```text
poisson rho=1.05 seed=15 n=36360 -> +55 ULP
h2      rho=0.50 seed=15 n=17262 -> +29 ULP
h2      rho=0.60 seed=14 n=20735 ->  -9 ULP
```

Ba mau con lai khoa nhanh code nhung khong phan biet duoc hai interpreter:

```text
poisson rho=0.60 seed=12 n=20735 -> 0 ULP
onoff   rho=0.60 seed=15 n=20735 -> 0 ULP
cbr     rho=0.95 seed=11 n=32887 -> n/a, khong goi normalize_rate
```

Sau sua:

```text
live  /usr/bin/python3 frozen digests -> 7/7 pass
conda 3.13             frozen digests -> 7/7 pass
conda full suite                      -> 350 passed, 4 skipped
```

Do lech quan sat duoc:

```text
live  3.10.12  sum_minus_naive = 0.0
conda 3.13.13  sum_minus_naive = -5.36e-10
```

Ket luan: 15 diem C' da chay van hop le. Toan bo Phase L van hop le. Khong
chay lai.

## Luat Sau Amendment 12

Moi ket luan ve gate/digest/provenance phai chay bang live interpreter:

```bash
sudo -n env PYTHONPATH="$PWD" /usr/bin/python3 -m pytest
```

Conda Python chi dung de phat trien nhanh, khong dung de ket luan bit-exact.

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-08-02
