# PHASE D′ — custody, identifiability và instrumentation trước Phase 23.26

Trạng thái tại `50f80cf`: **đang ở Lesson D.2**. Phase này không được coi là
đóng cho tới khi `docs/phase-D/03-gate-decision.md` tồn tại và phân xử từng
validity gate. Outcome của một giả thuyết không phải validity gate.

## D.0 — custody dữ liệu

- Backup cục bộ 6.5 GiB và SHA256: đã có; bản sao khác thiết bị còn thiếu.
- Positive control tái tạo parquet: FAIL có kiểm soát; tám parquet không được
  xoá/untrack trước khi có archive ngoài repo và Version DOI.
- `results/DATA_MANIFEST.json::doi`: còn `null`.
- Hook chặn file mới trên 5 MiB: đã cài và đã fire trên file thử 6 MiB.
- Tag bất biến trước custody action: chưa tạo. Tên dự kiến
  `phase-D-cleanup-start`, không dùng tên `v9-pre-cleanup` sai ngữ nghĩa.

## D.1 — state, limits và đính chính

- State of 23.25: `docs/phase-23/66-state-of-23-25.md`.
- Limits: `docs/phase-D/02-limits-addendum.md`.
- `LOAD_SIGMA_TARGET`/`LOAD_TAU_TARGET_STEPS` được giữ như provenance và đã
  deprecate cho run mới.
- Cơ chế “một virtual flow = một socket” bị rút. `FlowEngine` dùng một sender
  socket cho tải gộp; 817–875 là số virtual flow warm-start.

## D.2 — thí nghiệm phân biệt endpoint × load

### D.2.1 Bằng chứng hậu kiểm hiện có

Tool chính thức:

```bash
.venv/bin/python -m tools.phase_d_factorial_audit
```

Artifact: `results/SMOKE/phase-D/factorial_endpoint_x_load.json`. Tool đọc đủ
28 cặp không thứ tự trong ma trận 8×8 đã có; không chạy Mininet.

| Số link low-σ (`σ=0.03`) | Chung endpoint host | n cặp | mean r | Fisher pooled r |
|---:|:---:|---:|---:|---:|
| 2 | có | 2 | **+0.6181** | +0.6185 |
| 2 | không | 4 | +0.0364 | +0.0365 |
| 1 | có | 8 | +0.0625 | +0.0635 |
| 1 | không | 8 | +0.0527 | +0.0535 |
| 0 | có | 4 | +0.0171 | +0.0172 |
| 0 | không | 2 | +0.0145 | +0.0145 |

Ô `(2 low-σ, chung host)` lớn gấp **9.893×** ô mean cao kế tiếp. Đây là
`POST_HOC_REANALYSIS_NOT_CONFIRMATORY`: nó sinh giả thuyết, không xác nhận
giả thuyết.

### D.2.2 Phán quyết mô tả H1–H4

| Giả thuyết | Đối chứng hậu kiểm | Kết quả mô tả |
|---|---|---|
| H1 endpoint-only | 4 cặp chung host nhưng cả hai `N_bar` nhỏ | mean r=+0.0171; không đủ giải thích +0.6 |
| H2 link-dynamics-only | 4 cặp cả hai low-σ nhưng không chung host | mean r=+0.0364; không đủ giải thích +0.6 |
| H3 sampling/shared-transient | cùng 4 cặp trên, cùng lớp σ/τ và duration | mean r=+0.0364; không đủ giải thích +0.6 |
| H4 endpoint × low-σ/high-`N_bar` bundle | chỉ ô đồng thời có cả hai yếu tố | ứng viên sống: mean r=+0.6181 |

H4 là giả thuyết về **tương tác của bundle cấu hình**, chưa phải cơ chế heap
được chứng minh. Trong `flow_engine.py`, số arrival/retirement event không
tăng theo `N_bar`; heap lớn hơn chỉ làm đổi kích thước state và chi phí mỗi
operation. Cell C cũng đổi đồng thời `sigma`, lifetime, `tau` và `N_bar`, nên
không được diễn giải riêng là “`N_bar` gây ra r”.

### D.2.3 Cell C — test xác nhận đã soạn nhưng chưa được ký

Nguồn duy nhất của thiết kế là `docs/phase-D/00-preregistration.md`. Không
được chạy cell C trước khi file đó, tool factorial và artifact được commit,
sau đó tag `phase-D-cellC-start` trỏ đúng commit đã ký.

Cell C giữ `core_sigma=0.10`, đổi duy nhất `edge_sigma: 0.03 -> 0.10` tại
`rho_bar=0.925`. Dự đoán từ meta đã có:

```text
edge N_bar: 817–875 -> 73.5–78.8  (giảm 11.111×)
edge tau_pred: 20.6–28.5 s -> 1.86–2.56 s
core max tau_pred: ad = 4.2769 s  (trở thành time scale bảo thủ lớn nhất)
```

Vì phải giữ cả NC core và burn-in `5*tau`, duration 120 s trong bản nháp là
không đủ cho gate bảo thủ `n_eff>=25`:

```text
T_min = 5*tau_max + 2*25*tau_max = 55*4.2769 = 235.2 s
```

Khóa `duration=240 s`, 3 rep, seed 11/12/13. Tổng thời gian đo khoảng 12 phút,
chưa kể setup. Outcome chính là Fisher-pooled within-run `r(uA,uB)` sau burn.

## D.3 — instrumentation và độ nhạy

- Infra monitor + 4 cờ: đã chạy.
- Trust gate: p99 0.222126 ms, PASS ngưỡng 10 ms.
- Scaling audit offered 120 s: đã chạy; không thay thế measured trace dài.
- Độ nhạy `c_a`/L141: chưa chạy; cần NC poisson bit-exact và PC
  `cbr < poisson < h2` trước khi đóng phase.

## Điều kiện tạo `03-gate-decision.md`

1. Cell C được ký trước, chạy đủ 3 rep và mọi validity control được in.
2. Mỗi kết luận correlation ghi estimator, burn-in, `tau`, `n_eff` và CI/giới
   hạn của CI.
3. Archive/DOI và tag custody được phân xử rõ PASS hoặc BLOCKED, không để trống.
4. L141 được đóng bằng sensitivity hoặc giữ OPEN với lý do định lượng.
5. Phán quyết ghi cả kết quả âm; không đặt “H4 phải thắng” thành gate.
