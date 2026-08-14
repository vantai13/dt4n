# LESSON 23.1 -- fallback semantics

Ngay: 2026-08-14

Trang thai: da chay lai sau Amendment 23-6. Ket qua F3-a cu bi rut lai vi
look-ahead accounting; artifact hien hanh dung row-level installed-path
accounting.

Artifact chinh:

```text
results/phase-23/fallback_poisson_0.925_k0.5.json
results/phase-23/fallback_grid_poisson_0.925_C3.json
results/phase-23/fallback_grid_poisson_0.925_C3.csv
results/phase-23/fallback_grid_err_reject_poisson_0.925_C3.png
```

## 1. Controls first

Audit F3 va gates fallback:

```text
/tmp/dt4n-venv/bin/python -m pytest \
  test/test_phase23_fallback_audit.py test/test_phase23_fallback.py -q -s

ti le hang reject co the dung thong tin TUONG LAI: 0.8584
horizon trung binh: +168.5 ms
horizon lon nhat  : +445.0 ms
P(a*(t) == a*(t')) tren hang reject co the cho: 0.7753
14 passed in 7.22s
```

Full regression sau cung:

```text
/tmp/dt4n-venv/bin/python -m pytest -q
755 passed, 1 skipped, 2 warnings in 298.37s (0:04:58)
```

Report `kappa=0.5`:

```text
/tmp/dt4n-venv/bin/python -m cert.fallback \
  --calib results/phase-22/calib_set_v3.parquet \
  --cell-label poisson@0.925 \
  --config C3 \
  --kappa 0.5 \
  --out results/phase-23/fallback_poisson_0.925_k0.5.json
```

Provenance trong artifact `kappa=0.5`:

```text
git_hash  = 914effa7290d984708a5b46ff5485c65ed8d87e3
git_dirty = false
rowset    = test rows
```

## 2. Dong nhat thuc hoa von

Voi mot phan hoach accept/reject co dinh:

```text
R_neo = P(acc) * err|acc(twin) + P(rej) * err|reject(twin)
R_sys = P(acc) * err|acc(twin) + P(rej) * err|reject(fallback)
```

Hoa von `R_sys = R_neo` khi va chi khi:

```text
err|reject(fallback) == err|reject(twin)
```

Day la dong nhat thuc, khong phai quan sat. Khi kappa thay doi, tap reject
thay doi, nen ca hai ve cung di chuyen.

Gate moi:

```text
G23-4b  break_even_err_reject == err_reject(twin)  (tol 1e-12)
```

Trong report:

```text
break_even_err_reject = 0.35900086471189374
anchor.err_reject     = 0.35900086471189374
identity_residual     = 0.0
G23-4b                = PASS
```

## 3. Ket qua tai kappa = 0.5

Setup:

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

Bang chinh:

| Policy tren reject | err\|reject | err_system | vs anchor err | regret_system (ms) | vs anchor regret | sla_system | vs anchor sla |
|---|---:|---:|---:|---:|---:|---:|---:|
| twin / B0 | 0.359001 | 0.222399 | 0.00% | 1.767461 | 0.00% | 0.153950 | 0.00% |
| F1 STICKY | 0.387477 | 0.236890 | +6.52% | 1.961192 | +10.96% | 0.156740 | +1.81% |
| F2 STATIC | 0.391007 | 0.238686 | +7.32% | 2.004680 | +13.42% | 0.156298 | +1.53% |
| F3-a WAIT | 0.387477 | 0.236890 | +6.52% | 1.961192 | +10.96% | 0.156740 | +1.81% |

Ket luan tai diem prereg `kappa=0.5`:

```text
F1 STICKY va F2 STATIC deu te hon B0 tren ca err, regret, va sla_rate.
F3-a WAIT khong phai fallback thu ba: action row-level cua no bang F1.
```

## 4. Vi sao F3 cu bi rut lai

Ban cu cua `fallback_wait` da cham diem:

```text
a_chosen[t] = a_twin[t']    voi t' la refresh ke tiep
loss         = loss(a_chosen[t], state[t])
```

Do do, voi 85.84% hang reject co the cho, action duoc tao tu anh chup tuong lai
so voi hang dang duoc cham diem. Con so cu:

```text
err_system(F3-idl) = 0.166635
err_system(F3-exp) = 0.183222
```

bi rut lai. Sau Amendment 23-6:

```text
F3-a WAIT == F1 STICKY theo installed-path accounting.
err_system_exposed(F3-a) = err_system(F1) = 0.236890
```

Delay van la diagnostic hop le:

| Dai luong | Gia tri |
|---|---:|
| mean delay, all rows | 103.948 ms |
| mean delay given reject | 204.271 ms |
| max delay | 500.000 ms |
| retry_accept_rate | 0.633376 |
| no_refresh_in_block | 21,909 / 254,420 reject |

## 5. Vi sao F1 gan F2

Diagnostics moi:

| Dai luong | Gia tri |
|---|---:|
| `p_sticky_equals_static_given_reject` | 0.605727 |
| `p_twin_equals_static_marginal` | 0.619177 |
| `p_twin_equals_static_given_accept` | 0.707404 |
| `sticky_age_ms_mean` | 466.702 ms |
| `reject_run_len_mean` | 115.751 hang |
| `initial_state_share` | 0.078260 |

F1 va F2 trung action tren 60.57% hang reject. Tren 39.43% con lai, F1 tot hon
F2 mot chut tai `kappa=0.5`, nen hai duong gan nhau:

```text
err_system:    F2 0.238686 -> F1 0.236890
regret_system: F2 2.004680 -> F1 1.961192 ms
```

Day giai thich du doan "F1 tot hon F2 ro ret" bi sai ve co che: sticky giu mot
quyet dinh kha cu va thuong van la P1.

## 6. Quet toan luoi kappa

Luoi P8:

```text
{0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 3, 4, 6, 8}
```

Hinh headline:

```text
results/phase-23/fallback_grid_err_reject_poisson_0.925_C3.png
```

Bang `err|reject`:

| kappa | accept | twin / break-even | F1 sticky | F2 static | F3-a wait |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 1.0000 | n/a | n/a | n/a | n/a |
| 0.25 | 0.7380 | 0.438556 | 0.446433 | 0.392267 | 0.446433 |
| 0.50 | 0.4911 | 0.359001 | 0.387477 | 0.391007 | 0.387477 |
| 0.75 | 0.2734 | 0.295159 | 0.331723 | 0.373988 | 0.331723 |
| 1.00 | 0.1436 | 0.258096 | 0.311387 | 0.361324 | 0.311387 |
| 1.25 | 0.0720 | 0.239512 | 0.310296 | 0.352368 | 0.310296 |
| 1.50 | 0.0348 | 0.230413 | 0.321436 | 0.346941 | 0.321436 |
| 2.00 | 0.0095 | 0.224528 | 0.331823 | 0.342545 | 0.331823 |
| 3.00 | 0.0005 | 0.222516 | 0.340205 | 0.340438 | 0.340205 |
| 4.00 | 0.0000 | 0.222403 | 0.340283 | 0.340283 | 0.340283 |
| 6.00 | 0.0000 | 0.222399 | 0.340276 | 0.340276 | 0.340276 |
| 8.00 | 0.0000 | 0.222399 | 0.340276 | 0.340276 | 0.340276 |

Best point tren toan luoi:

| Scale | Best policy | kappa | system risk | vs anchor |
|---|---|---:|---:|---:|
| err | F2 STATIC | 0.25 | 0.210270 | -5.45% |
| regret | F2 STATIC | 0.25 | 1.598988 ms | -9.53% |
| sla_rate | F2 STATIC | 0.25 | 0.145156 | -5.71% |

Ket luan sau khi quet luoi:

```text
Tai kappa=0.5: ca F1/F2/F3-a deu fail so voi anchor.
Tren toan luoi: G23-14 PASS, nhung chi nho F2 STATIC tai kappa=0.25.
F1 STICKY va F3-a WAIT khong beat anchor o bat ky kappa > 0 nao trong luoi.
```

## 7. Doi chieu du doan F0..F6

| ID | Du doan | Do duoc sau audit | KQ |
|---|---|---:|---|
| F0 | `P(a*=P1)` 0.64-0.68, mo ta | 0.656141 all / 0.659724 test | N/A |
| F1 | `err_system(F2 STATIC)` tai k=0.5: 0.21-0.27 | 0.238686 | HIT |
| F2 | `err_system(F1 STICKY)` tai k=0.5: 0.17-0.24 | 0.236890 | HIT, gan tran |
| F3 | `err_system(F3 WAIT)` tai k=0.5: 0.10-0.18 | valid F3-a = 0.236890; so cu 0.183222 bi rut lai | VOID |
| F4 | thu tu `F2 > F1 > F3` | valid: F2 > F1 = F3-a | VOID |
| F5 | delay F3 100-250 ms | 204.271 ms given reject | HIT diagnostic |
| F6 | best fallback beats anchor err 0.2224 | grid best: F2, k=0.25, err=0.210270 | HIT tren grid; FAIL tai k=0.5 |

Du doan trung nho artifact F3 cu khong duoc cham la HIT.

## 8. Gates

| Gate | Ket qua |
|---|---|
| G23-1 every policy has one action per row | PASS |
| G23-4 total probability identity | PASS |
| G23-4b break-even identity | PASS |
| G23-5 decision delay profile | PASS |
| F3 audit: production wait action equals installed path | PASS |

## 9. Ket luan Lesson 23.1

Thong diep dung sau audit khong phai "F3 wait giam loi 17.6%". Thong diep dung:

```text
1. Break-even cua fallback la err|reject(twin) tren cung tap reject.
2. F3-a suy bien thanh F1 neu cham theo duong dang cai that.
3. Tai kappa=0.5, fallback mien phi lam he thong te hon anchor.
4. Tren toan luoi, co mot diem hop le: F2 STATIC tai kappa=0.25 giam risk
   tren ca err, regret, va sla_rate.
```

Gia tri cua certificate trong Phase 23 vi vay la hai lop: bao dam formal tren
nhanh accept, va tin hieu phan bo reject-set de chon luc nao dung fallback hay
tai nguyen moi trong Phase 24.
