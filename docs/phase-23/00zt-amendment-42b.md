# AMENDMENT 23-42b -- Lesson 23.8[A0]: sua nhac cu do la THAY DOI VAT LY

Ngay: 2026-08-21
Trang thai: **SAU Lesson 23.8[A]; TRUOC khi sua bat ky file nao trong bridge/.**

## 1. Vi sao day khong phai refactor

`bridge/collector.py::collect_all` hien dong dau mot `now_ts` cho moi Thing.
`now_ts` duoc truyen vao `collect_host` / `collect_link` va dung lam mau so
`dt` trong `compute_rate`. Doi sang dau thoi gian rieng cho tung Thing se doi
`rxRate`, `txRate`, `lossPct`: day la doi gia tri quan sat, khong chi doi cach
ghi.

`bridge/adapter.py` lam tron `tSource` ve 3 chu so thap phan (1 ms). Estimand
E3 do offset giua link cung o bac ms, nen luong tu nay la sai so he thong khong
chap nhan duoc.

A0 vi vay duoc khai bao la **THAY DOI VAT LY**.

## 2. Pham vi thay doi

```text
bridge/collector.py  t_source rieng tung Thing; them t_cycle_start/end va
                     cycle_scan_ms
bridge/adapter.py    tSource round 3 -> round 6
bridge/pusher.py     ghi t_send/t_ack moi patch khi trace duoc bat
bridge/sync_agent.py them measurement_mode va cycle trace; period mac dinh
                     van la 1.0, moi call site A2 phai truyen 0.5 tuong minh
```

Khong doi cong thuc utilization, `UTIL_DIRECTION`, `compute_health_state`,
`diff_features`, `DEFAULT_TOL`, thu tu Thing, hoac quy uoc `make_thing_id_*`.

## 3. Kiem soat hoi quy bat buoc

Truoc khi sua, chay va luu:

```bash
pytest -q > results/phase-23/a0_baseline_tests.txt
```

Sau khi sua, chay lai cung tap test. Moi test doi trang thai phai duoc liet ke
trong doc 19. Neu test do vi `rxRate` doi, ghi ro gia tri cu/moi; khong sua test
chi de lam xanh.

## 4. Du doan khoa M-66 .. M-69

| ID | Dai luong | Nhan | Dai khoa |
|---|---|---|---|
| M-66 | so test doi trang thai sau A0 | [NGOAI SUY] | 0 .. 6 |
| M-67 | max `abs(rxRate_moi-rxRate_cu)/rxRate_cu` tren snapshot smoke | [CO CHE] | `<= 0.05` |
| M-68 | NC-do-1, tSource thu cong = now-1.000 s | [CO CHE] | `0.995 .. 1.010 s` |
| M-69 | NC-do-3 MODE-PROD, rho dung yen, AoI max trong 60 s | [CO CHE] | `>= 5.0 s` |

M-67: `dt` chi doi bang do dai vong quet so voi chu ky 500 ms; sai lech rate
du kien nho. M-69 co the sai va la severe test cua suy luan delta-sync pha vo
rang cua. Neu M-69 MISS, VD-2 phai duoc rut lai.

## 5. Output khoa

```text
results/phase-23/a0_baseline_tests.txt
results/phase-23/a0_instrument_calibration.json
docs/phase-23/19-instrument-calibration.md
```

Artifact A0 mang `status="INSTRUMENT_CALIBRATION"` va `closes_P23A=false`.
