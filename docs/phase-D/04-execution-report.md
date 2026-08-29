# Phase D′ — báo cáo thực thi 2026-08-28/29

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

### 2b. Gói custody chờ upload

Chạy `tools/prepare_d0_archive.sh /tmp/dt4n-archive`; script kiểm lại đủ tám
SHA256 trước khi đóng gói và tạo checksum dùng tên file tương đối:

```text
dt4n-phase21R-parquet.tar.gz  239 MiB  sha256 138913388ba5d7d156496be84ec85a850c0ba4ced063ae001507154975710eee
dt4n-raw-measurements.tar.gz  105 MiB  sha256 0c3ccd202b434134f74306fde22e238916bb374d341a258680d013cbbadee930
SHA256SUMS                    /tmp/dt4n-archive/SHA256SUMS
```

Đây mới là staging cục bộ, chưa phải archive bất biến. Không ghi DOI giả và
không untrack parquet trước khi người dùng publish Zenodo Version DOI.

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

Rerun đóng sổ D.0/D.1 ngày 2026-08-29:

```text
D.0/D.1 + Phase-D targeted   79 passed, 1 skipped
Full suite (loại L121 cũ)    1797 passed, 46 skipped, 14 deselected, 1 failed
failure ngoài D.0/D.1        test_no_doc_claims_a_missing_tag
nguyên nhân                  prereg D.2 nhắc tag tương lai phase-D-cellC-start
phán quyết                   không tạo tag trước khi prereg D.2 được ký
```

### 7. Audit factorial 28 cặp (bổ sung 2026-08-29)

```text
ô (2 low-sigma, shared)       n=2  mean r=+0.6181
ô (2 low-sigma, no-shared)    n=4  mean r=+0.0364
ô (1 low-sigma, shared)       n=8  mean r=+0.0625
ô (1 low-sigma, no-shared)    n=8  mean r=+0.0527
ô (0 low-sigma, shared)       n=4  mean r=+0.0171
ô (0 low-sigma, no-shared)    n=2  mean r=+0.0145
ratio ô phát hiện / ô kế      9.893x
nhãn                          POST_HOC_REANALYSIS_NOT_CONFIRMATORY
```

H1/H2/H3 bị bác ở mức mô tả hậu kiểm; H4 endpoint × configuration bundle là
ứng viên. Cell C đã được soạn prereg nhưng chưa ký/chạy. Duration được sửa từ
120 s thành 240 s vì `tau_pred(ad)=4.2769 s` và gate tính sau burn-in cần
`T >= 55*tau_max = 235.2 s`.

## Artifact đầu ra

| Nội dung | File |
|---|---|
| benchmark trust gate | `results/SMOKE/phase-D/trust_gate_benchmark.json` |
| infra JSONL | `results/SMOKE/phase-D/infra_trust_gate_benchmark.jsonl` |
| infra summary | `results/SMOKE/phase-D/infra_trust_gate_benchmark_summary.json` |
| correlation rerun | `results/SMOKE/phase-D/link_pair_stability_rerun.json` |
| host confound rerun | `results/SMOKE/phase-D/host_confound_probe_rerun.json` |
| scaling audit | `results/SMOKE/phase-D/scaling_test_existing_120s.json` |
| factorial audit 28 cặp | `results/SMOKE/phase-D/factorial_endpoint_x_load.json` |
| 8 SHA256 parquet | `docs/phase-D/parquet-sha256-before-delete.txt` |
| script chuẩn bị gói Zenodo | `tools/prepare_d0_archive.sh` |
| checker D.0/D.1 | `tools/check_d0_d1.sh` |

## Gate chưa thể PASS trong phiên này

- Version DOI/Zenodo: cần tài khoản và hành động publish bên ngoài; manifest
  hiện vẫn có `doi: null`.
- Tag `v9-pre-cleanup` không dùng vì sai ngữ nghĩa. Tag thay thế
  `phase-D-cleanup-start` đã tạo cục bộ tại `fbde6a4`. Kiểm lại 2026-08-29:
  tag này đã có trên origin; chỉ tag prereg mới còn chờ credential.
- Xoá/untrack/rewrite lịch sử: bị chặn đúng quy trình vì NC tái tạo FAIL.
- Cell C generator một-hop: chưa chạy trong phiên 2026-08-28. Audit factorial
  ngày 2026-08-29 đã làm sống lại cell này cho câu hỏi cơ chế endpoint ×
  configuration bundle (không phải câu hỏi path-omega). Prereg nằm ở
  `docs/phase-D/00-preregistration.md`; chỉ được chạy sau commit + tag ký.

## Bổ sung D.2/D.3 ngày 2026-08-29

### D2-1 — factorial trên `rho_offered`

Chạy `tools/phase_d_factorial_offered.py` trên đủ 15 CLEAN trace, bỏ
`5*tau_max` riêng từng run. Ô `(2 low-σ, chung host)` trên offered là
`r=+0.0048`, so với measured reference `+0.6181`. Theo partition đã cho
(`|r|<0.15`), H6 shared measurement noise được ủng hộ ở mức hậu kiểm.

### D2-2/D2-3 — khóa preregistration

Prereg Cell C/C′, tool offered và artifact offered được commit tại
`adfb7223`; annotated tag `phase-D-cellC-start` có tag-object SHA
`785555793d76d050494bcddfd8dfb909364915b0` và trỏ tới commit
`adfb722367ba80947d947b50168d8b15a1d8a0a7`. Push bị chặn vì môi trường
không có GitHub credential.

### D2-4 — Cell C

Chạy đủ ba rep 240 s, seed 11/12/13 với infra monitor 100 ms. PC-C1 và PC-C3
đạt; ba negative control đạt; counter/metadata/infra sạch. Cả ba infra summary
có bốn cờ false, CPU p95 lần lượt 14.379%, 19.804%, 13.642%.

Validity gate trả `INVALID_RUN` trước khi diễn giải outcome:

```text
PC-C2 median ACF-tau reduction edge   khoảng 1.1×, yêu cầu >=5×  FAIL
n_eff failures                         uA-uB rep1 20.383
                                       bc-bd rep2 23.894
                                       ac-ad rep3 10.536
```

Vì chỉ dẫn yêu cầu dừng khi PC-C2 fail, không chạy Cell C′, không chạy run
dài trong vòng này và không dùng pooled r Cell C để phán H4/H6. Trace thô
được giữ dưới `results/RAW/phase-D/cellC/`; artifact validity là
`results/SMOKE/phase-D/cellC_analysis.json`.

Ba infra summary chẩn đoán được xếp đúng tầng SMOKE tại
`results/SMOKE/phase-D/infra_cellC_s{11,12,13}_summary.json`; JSONL lấy mẫu
đầy đủ vẫn ở local dưới `results/PENDING/phase-D/` và đã được hấp thụ vào
artifact validity.

### D3 — sensitivity theo traffic family

Khẳng định chịu lực thật là `T6_snr_and_decision`, không dùng hai placeholder
trong hướng dẫn. NC poisson tái tạo bit-exact đủ 30 giá trị + median + quyết
định; PC tại rho=0.90 đạt:

```text
cbr 0.138878 ms < poisson 5.724837 ms < h2 11.041078 ms
```

Quyết định D3 giữ nguyên trên cả ba mode, nhưng cell được chọn đổi:

```text
cbr       SNR median 0.259234   highest cell clean@0.700
poisson   SNR median 0.375163   highest cell clean@0.960
h2        SNR median 0.792666   highest cell clean@0.960
```

Do đó L141 **VẪN MỞ** cho khẳng định “highest-SNR cell”; kết luận budget band
D3 thì robust. On/off chỉ spot-check được tại key `onoff|6|13`, delay rho=0.90
là 6.630987 ms; không được mở rộng thành mọi traffic family.

### D-9 — hệ quả định lượng cho Phase 24

Trust-gate p99 là 0.222126 ms. Chu kỳ sync/control hiện hành là 500 ms, nên
gate chiếm `0.222126/500 = 0.0444%` ngân sách, thấp hơn ngưỡng an toàn 5%.
Nếu gate nằm trên critical path, đóng góp trực tiếp tối đa quan sát vào AoI z
là 0.222126 ms mỗi quyết định. Trạng thái D-9: PASS; chưa cần nhánh tối ưu.
Giới hạn D-L17: đây là một lần đo local, CPU p95 15.5%, chưa đo dưới tải.

## Năm mục BLOCKED, không phải SKIPPED

1. Bản backup trên thiết bị/đám mây thứ hai: cần người dùng cấp đích/tài khoản.
2. Upload hai gói archive lên Zenodo và publish Version DOI: cần tài khoản.
3. Ghi Version DOI/`ARCHIVE_DOI` vào manifest/constants: phụ thuộc mục 2.
4. Push branch `main`: thiếu GitHub credential.
5. Push annotated tag prereg `phase-D-cellC-start`: thiếu GitHub credential.

Các mục trên là **BLOCKED, không phải SKIPPED**. Gate D′ vẫn FAIL cho tới khi
có DOI và các validity debt được phân xử.

## Kiểm thử cuối

```text
Targeted D/ledger                 82 passed, 1 skipped
Full suite lần đầu               1798 passed, 48 skipped, 13 deselected,
                                  5 failed
Sau khi chuyển 3 infra summary
PENDING -> SMOKE                  99 passed, 6 skipped, 2 failed
Hai failure còn lại              L121 KNOWN_DANGLING parquet tồn tại sẵn;
                                  g23-17c historical-number drift tồn tại sẵn
```

Ba failure do artifact D mới đã được sửa hết; rerun chỉ còn hai debt ngoài
phạm vi D.2/D.3. Không sửa/xóa parquet hoặc historical report để làm test xanh
giả vì hai hành động đó cần adjudication riêng.

Audit cuối sau commit và cài hook:

```text
tools/check_d0_d1.sh              PASS 20 / FAIL 1 / BLOCKED 4
FAIL                              D0-1a: backup tarball không hiện diện trong
                                  filesystem của workspace hiện tại
BLOCKED                           backup ngoài máy, DOI, whitelist, 8 parquet
git push origin main              FAIL: thiếu GitHub credential
git push phase-D-cellC-start      FAIL: thiếu GitHub credential
```

Tag custody `phase-D-cleanup-start` đã xác nhận có trên origin; branch mới và
tag prereg vẫn chỉ tồn tại local trong phiên này.

## Bổ sung Amendment D-A001 — 2026-08-29

Người dùng xác nhận sau phiên trước rằng push đã thành công và remote ở
`c766af2`. Trước tái phân tích, amendment PC-C2′ được commit/tag riêng:

```text
commit prereg A001               19351dfe
annotated tag                    phase-D-pc-c2-prime-start
tag object                       d648f4871a8a7dd48f724b391fb4cc3095d06d56
commit thật tag trỏ tới          19351dfec13106666a01ec8f00a4b8c88c5c34ca
Mininet mới                      0 giây
```

PC-C2′ chạy trên ba offered trace Cell A rho=0.925 và ba trace Cell C:

```text
edge             uA       uB       vC       vD       median
tau A/C ratio    4.942    7.145    4.048    2.878    4.495
gate             median >=5.0                           FAIL
```

PC-C2′b tái dùng estimator nugget A080. Cell A rho=0.925 cho median signal
fraction 0.3682, khớp reference 15-run 0.3696. Cell C chỉ vC fit hợp lệ
(`sf=0.9729`); uA/uB/vD có raw intercept 1.187/1.180/1.004 >1 nên rule signed
không cho project về biên.

Phán quyết tự động:

```text
GENERATOR_CONTROL_FAIL_CELL_C_REMAINS_INVALID
may_read_frozen_outcomes_under_A001 = false
```

Kết quả nằm ở `results/SMOKE/phase-D/pc_c2_prime.json`; diễn giải đầy đủ tại
`docs/phase-D/05-pc-c2-prime-readjudication.md`. Không hạ threshold 5×, không
bỏ vD và không đảo phán quyết cũ.

Sau A3, `git push origin main` và push tag
`phase-D-pc-c2-prime-start` được thử lại nhưng checkout hiện tại vẫn không có
GitHub credential (`could not read Username`). Remote được xác nhận dừng ở
`c766af2`; ba commit A001 và tag mới đang chờ người dùng push từ môi trường có
credential.
