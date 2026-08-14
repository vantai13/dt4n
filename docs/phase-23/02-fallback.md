# LESSON 23.1 -- fallback semantics

Ngay: 2026-08-14

Trang thai: da chay sau tag `phase-23-start` va sau amendments 23-1..23-5.
Report chinh:

```text
results/phase-23/fallback_poisson_0.925_k0.5.json
```

Lenh:

```bash
/tmp/dt4n-venv/bin/python -m cert.fallback \
  --calib results/phase-22/calib_set_v3.parquet \
  --cell-label poisson@0.925 \
  --config C3 \
  --kappa 0.5 \
  --out results/phase-23/fallback_poisson_0.925_k0.5.json
```

Provenance trong artifact:

```text
git_hash  = d541cda7f0fdf8ef4d00153881eee96faca1cc00
git_dirty = false
rowset    = test rows
```

## 1. Controls first

Chay doi chung am truoc khi doc ket qua:

```text
/tmp/dt4n-venv/bin/python -m pytest \
  test/test_phase23_fallback.py::test_NC23_5_fallback_equals_twin_reproduces_anchor \
  test/test_phase23_fallback.py::test_NC23_1_accept_all_uses_no_fallback -q

2 passed
```

Sau do chay cong Lesson 23.1:

```text
/tmp/dt4n-venv/bin/python -m pytest test/test_phase23_fallback.py -q
10 passed
```

Va cum hoi quy lien quan:

```text
/tmp/dt4n-venv/bin/python -m pytest \
  test/test_phase23_prereg.py test/test_phase23_fallback.py test/test_phase22_matrix.py -q

26 passed in 101.01s
```

## 2. Setup

| Dai luong | Gia tri |
|---|---:|
| config | C3 |
| kappa | 0.5 |
| n_test_rows | 499,967 |
| accept | 0.491126 |
| reject | 0.508874 |
| anchor err | 0.222399 |
| anchor regret | 1.767461 ms |
| anchor sla_rate | 0.153950 |
| break-even `err|reject` | 0.359001 |

Break-even duoc tinh tu:

```text
err_system = P(acc)*err|acc + P(rej)*err|fallback
```

## 3. Ket qua chinh

| Policy | err_system | regret_system (ms) | sla_system | err_reject | regret_reject (ms) |
|---|---:|---:|---:|---:|---:|
| anchor B0 | 0.222399 | 1.767461 | 0.153950 | n/a | n/a |
| F2 STATIC | 0.238686 | 2.004680 | 0.156298 | 0.391007 | 3.468606 |
| F1 STICKY | 0.236890 | 1.961192 | 0.156740 | 0.387477 | 3.383148 |
| F3 WAIT-idl | 0.166635 | 0.988530 | 0.125008 | 0.249418 | 1.471745 |
| F3 WAIT-exp | 0.183222 | 1.212313 | 0.132434 | n/a | n/a |

Ket luan:

```text
STATIC va STICKY lam he thong TE HON anchor tren ca err va regret.
WAIT tot hon anchor tren ca ba thang, ngay ca khi tinh exposure window.
```

## 4. Con so doi cuc dien

Du doan co che o Amendment 23-1/23-2 noi:

```text
err_F2_reject co kha nang vuot break-even vi reject set la tap kho.
```

Do duoc:

```text
err_F2_reject = 0.391007 > 0.359001
```

Nghia la P1 tinh dung 65.6% tren bien nhung khong du tren tap bi reject.
Tập reject dung la tap kho: static routing tu tot "vua du" thanh lam he thong
te hon B0.

## 5. Vi sao STICKY gan STATIC

Diagnostics:

| Dai luong | Gia tri |
|---|---:|
| sticky_age_ms_mean | 466.702 ms |
| reject_run_len_mean | 115.751 hang |
| initial_state_share | 0.078260 |

`reject_run_len_mean` tuong duong khoang 579 ms voi `dt = 5 ms`. Sticky dang
giu mot quyet dinh kha cu, gan nua `tau = 1 s`, nen no chi cai thien nhe so
voi STATIC:

```text
err:    0.238686 -> 0.236890
regret: 2.004680 -> 1.961192 ms
```

`initial_state_share = 7.83%` lon hon nguong chan doan 5%, nen L15 quan trong:
reset dau block lam F1 te hon router that co the, va F1 nen duoc doc nhu can
tren cua risk sticky.

## 6. F3 delay gate

| Dai luong | Gia tri |
|---|---:|
| mean delay, all rows | 103.948 ms |
| mean delay given reject | 204.271 ms |
| max delay | 500.000 ms |
| retry_accept_rate | 0.633376 |
| no_refresh_in_block | 21,909 / 254,420 reject |

G23-5 moi PASS:

```text
0 < E[w|reject] = 204.271 ms < 252.5 ms
max(w) <= 505 ms
w = (0.550 - z_s) + 0.005 tren cac hang co wait
```

## 7. Doi chieu du doan F0..F6

| ID | Du doan | Do duoc | KQ |
|---|---|---:|---|
| F0 | `P(a*=P1)` 0.64-0.68, mo ta | 0.656141 all / 0.659724 test | N/A |
| F1 | `err_system(F2 STATIC)` 0.21-0.27 | 0.238686 | HIT |
| F2 | `err_system(F1 STICKY)` 0.17-0.24 | 0.236890 | HIT |
| F3 | `err_system(F3 WAIT)` 0.10-0.18 | 0.166635 idl / 0.183222 exp | HIT idl |
| F4 | thu tu `F2 > F1 > F3` | 0.238686 > 0.236890 > 0.166635 | HIT |
| F5 | delay F3 100-250 ms | 204.271 ms given reject | HIT |
| F6 | best fallback beats anchor err 0.2224 | WAIT-exp err 0.183222 | HIT |

Ghi chu: F3 prediction ban dau doc theo F3-idl. Amendment 23-3 bat buoc bao
cao F3-exp; ket luan van giu voi F3-exp vi 0.183222 < 0.222399.

## 8. Gates

| Gate | Ket qua |
|---|---|
| G23-1 every policy has one action per row | PASS |
| G23-4 total probability identity | PASS |
| G23-5 decision delay profile | PASS |

G23-4 residual lon nhat trong report nho hon `1e-9`.

## 9. Ket luan Lesson 23.1

Phase 22 accept branch khong du de ket luan gia tri he thong. Khi reject thanh
hanh dong that:

```text
F2 STATIC va F1 STICKY xoa sach loi ich cua trust gate.
F3 WAIT, du tinh exposure window, moi lam risk_system tot hon anchor.
```

Dong gop cua 23.1 la mot thong diep he thong ro rang: selective prediction chi
co nghia trong control loop khi fallback semantics duoc dinh nghia va do cung
voi nhanh accept.
