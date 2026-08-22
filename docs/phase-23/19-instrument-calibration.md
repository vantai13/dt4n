# Lesson 23.8[A0] -- kiem chuan nhac cu AoI

Ngay: 2026-08-22
Trang thai: **INSTRUMENT_CALIBRATION -- khong dong P23-A.**

## Ket luan

Nhac cu per-Thing timestamp, push trace va cycle trace da duoc cai dat va qua
cac control da sua theo Amendment 23-42c. Delta sync that su pha vo rang cua:
voi trang thai dung yen va `reconcile_every=30`, AoI tang den 15.0069 s truoc
khi ha xuong.

Hai prediction goc khong hop le ve dai luong van duoc bao cao la MISS:

```text
M-68 goc                MISS (max 1.011122 s > 1.010 s)
NC-do-2 CV 0.44..0.52   MISS (CV 0.556914)
```

Khong doi hai MISS nay thanh HIT. Amendment 23-42c thay chung bang control
tach timestamp quantisation khoi PATCH latency va control shape co tinh den
`d` thuc cua lan calibration.

## 1. Thay doi vat ly A0

- `collector.collect_all` dat `t_source` rieng ngay truoc moi `collect_*`, va
  ghi `t_cycle_start`, `t_cycle_end`, `cycle_scan_ms`.
- Adapter tang do chinh xac `tSource` tu millisecond len microsecond.
- Pusher ghi `t_source`, `t_send`, `t_ack`, `push_ms`, `ok` khi trace bat.
- Sync agent co `clean`/`prod`, ghi `n_pushed`, `cycle_scan_ms`,
  `lock_wait_ms`, overrun va cac dem thanh cong/that bai.
- Mac dinh production `period=1.0` khong bi thay doi.

## 2. Hoi quy M-66

| Lan | Ket qua |
|---|---|
| baseline truoc A0 | 1047 passed, 5 skipped, 8 deselected |
| sau A0 | 1050 passed, 5 skipped, 8 deselected |

Ba test moi bao ve A0 lam tong pass tang 3. Khong test cu nao doi trang thai:
`M-66 = 0`, nam trong dai khoa 0..6.

Trong lan test muc tieu dau tien, `test_phase2_5` co hai internal check fail
vi con doi gia tri cu `1000.123` va `1001.568`. Hai expected duoc cap nhat
thanh `1000.1234` va `1001.5678`, dung hop dong microsecond da tien dang ky;
khong co check rate nao bi sua de lam xanh.

## 3. M-67 rate smoke

Smoke dinh truoc gom 8 link, delta byte bang nhau, scan span thay doi tu 70 ms
sang 84 ms giua hai snapshot. Sai lech `rxRate` tuong doi lon nhat:

```text
max relative gap = 0.031008 <= 0.05  -> HIT
```

## 4. NC-do-1 va timestamp residual

Voi 20 lan dat `tSource=now-1.000s`:

| Dai luong | Gia tri |
|---|---:|
| AoI request-start mean | 1.009495 s |
| min / max | 1.009026 / 1.011122 s |
| PATCH contribution mean | 9.495 ms |
| reader contribution mean | 6.283 ms |
| max timestamp residual | 0.000477 ms |

M-68 goc MISS do mot mau vuot 10 ms. M-68b HIT vi residual luong tu nho hon
0.001 ms, chung minh `tSource -> Ditto -> read-back` khong co offset he thong.

## 5. NC-do-2 MODE-CLEAN

Mot Thing dung yen, period 0.5 s, full push moi cycle:

| Dai luong | Gia tri |
|---|---:|
| n cycle / n sample | 31 / 255 |
| n_pushed == n_things | 31/31 PASS |
| AoI min / p50 / max | 0.011102 / 0.258302 / 0.507215 s |
| p95 - p05 | 0.448080 s |
| CV observed | 0.556914 |
| CV expected tu d_hat | 0.556343 |
| absolute CV gap | 0.000572 |
| overrun ratio | 0.0 |

NC-do-2a va 2b HIT. Shape phu hop `Uniform[d,d+0.5]`; CV goc MISS vi CV
phu thuoc `d`, khong phai vi shape rang cua sai.

## 6. NC-do-3 MODE-PROD

Mot Thing dung yen, period 0.5 s, delta sync va reconciliation moi 30 cycle:

| Dai luong | Gia tri |
|---|---:|
| n cycle / n sample | 121 / 1050 |
| push records | 5 |
| AoI p50 / p95 / max | 7.578459 / 14.269211 / 15.006900 s |
| CV | 0.569183 |
| overrun ratio | 0.0 |

`M-69 = HIT`: max lon hon 5 s. Suy luan VD-2 khong bi rut lai; production
delta sync khong tao rang cua chu ky 0.5 s cho mot Thing khong doi.

## 7. Artifact

```text
results/phase-23/a0_baseline_tests.txt
results/phase-23/a0_post_tests.txt
results/phase-23/a0_instrument_calibration_attempt1.json
results/phase-23/a0_instrument_calibration_attempt2.json
results/phase-23/a0_instrument_calibration.json
```

Artifact cuoi mang `status="INSTRUMENT_CALIBRATION"`,
`closes_P23A=false`. Hai attempt fail duoc giu de khong che giau qua trinh
kiem chuan.
