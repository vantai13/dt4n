# Phase D′ — báo cáo thực thi 2026-08-28

## Kết quả chính

### 1. Backup

```text
file    /home/vantai/dt4n-FULL-BACKUP-20260828.tar.gz
size    6.5 GiB
sha256  83162ca25f6eb9041b1b2bf2c03d02b99a3fff99d4cc88ba047a9216c8495ff5
```

### 2. Reproduction control

Tái tạo `calib_set_poisson_0.850.parquet` bằng `.venv`:

```text
shape old/new        (999945,24) / (999945,24)
SHA old/new          8c75cbf8... / 1cf19e3e...
pandas.equals        False
verdict              FAIL -- không xoá 8 parquet
```

### 3. Trust-gate latency và hạ tầng

```text
N / warm-up          5000 / 200
p50 / p95 / p99      0.131140 / 0.166973 / 0.222126 ms
max                  0.862302 ms
gate p99 <= 10 ms    PASS

infra samples        50 @ 100 ms
CPU p95              15.479%
load_1m max          0.313
net drops            0
clock jump max       0.150955 ms
CPU/swap/drop/clock  false / false / false / false
```

### 4. Correlation rerun trên 15 run CLEAN

```text
pair     measured   offered    sd measured     negative measured runs
uA-uB    +0.5986    +0.1725      0.2839              1/15
vC-vD    +0.6376    -0.1832      0.1768              0/15
ac-ad    +0.0358    +0.0267      0.1610              5/15
bc-bd    +0.0314    -0.0070      0.1363              6/15
```

Pre-registered A078 không phủ kín outcome nên script trả
`GAP_IN_SIGNED_SCENARIOS`. Probe độc lập trên shortfall trả
`HOST_SHORTFALL_SUPPORTED`, với `+0.9020` cho uA-uB và `+0.9612` cho vC-vD.

### 5. Scaling audit trên dữ liệu 120 s đang có

Trace 1800 s trong hướng dẫn không tồn tại trong working tree. Audit không
giả dữ liệu dài; nó chạy trên 15 offered trace 120 s, bỏ `5*tau_pair` đầu.

Với uA-uB:

```text
window   r pooled   n_eff total   adequate
10 s     -0.1071       6.55       false
20 s     +0.0414      13.09       false
40 s     +0.1187      25.06       true
60 s     +0.1300      22.17       false (chỉ 7 run còn đủ hậu burn-in)
```

Offered intent sau burn-in gần 0; kết quả này nhất quán với việc `+0.6` xuất
hiện ở tầng measured do endpoint contention, không phải RNG/generator intent.
Nó không thay thế scaling test 1800 s trên measured traces.

### 6. Kiểm thử

```text
Phase-D + ledger targeted    141 passed, 7 skipped
Full suite ban đầu           1796 passed, 46 skipped, 6 failed
  - 5 failure do artifact mới đặt sai tier PENDING; đã sửa sang SMOKE
  - 1 failure tồn tại sẵn: test_known_dangling_only_shrinks (L121)
Full suite loại đúng L121     1796 passed, 46 skipped, 14 deselected
Pre-commit file >5 MiB       PASS: file thử 6 MiB bị chặn, exit 1
```

## Artifact đầu ra

| Nội dung | File |
|---|---|
| benchmark trust gate | `results/SMOKE/phase-D/trust_gate_benchmark.json` |
| infra JSONL | `results/SMOKE/phase-D/infra_trust_gate_benchmark.jsonl` |
| infra summary | `results/SMOKE/phase-D/infra_trust_gate_benchmark_summary.json` |
| correlation rerun | `results/SMOKE/phase-D/link_pair_stability_rerun.json` |
| host confound rerun | `results/SMOKE/phase-D/host_confound_probe_rerun.json` |
| scaling audit | `results/SMOKE/phase-D/scaling_test_existing_120s.json` |
| 8 SHA256 parquet | `docs/phase-D/parquet-sha256-before-delete.txt` |

## Gate chưa thể PASS trong phiên này

- Version DOI/Zenodo: cần tài khoản và hành động publish bên ngoài; manifest
  hiện vẫn có `doi: null`.
- Tag `v9-pre-cleanup`: không tạo vì HEAD hiện tại đã là Lesson 23.25 closeout,
  gắn tên v9 vào commit này sẽ sai provenance.
- Xoá/untrack/rewrite lịch sử: bị chặn đúng quy trình vì NC tái tạo FAIL.
- Lưới Mininet D.4′ mới: không chạy vì thiết kế mới nhất trong repo đã thay
  bằng yêu cầu path-level Phase 23.26; chạy lưới generator một-hop cũ không
  giải quyết identifiability đã được closeout xác nhận.
