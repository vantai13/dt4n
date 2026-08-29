# PRE-REGISTRATION — Phase D′ Lesson D.2, cell C

```text
Ngày soạn                 2026-08-29
Trạng thái                DRAFT_LOCKED_FOR_SIGNATURE
Người ký                  CHƯA KÝ
Commit chứa prereg        CHƯA CÓ
Tag bắt buộc              phase-D-cellC-start (CHƯA TẠO)
Cho phép chạy Mininet?    KHÔNG, cho tới khi commit + tag hoàn tất
```

Mọi thay đổi nội dung sau khi tag phải đi qua amendment mới; không sửa âm thầm
file này. Artifact factorial là hậu kiểm trên dữ liệu cũ. Cell C là phép đo
xác nhận tương lai.

## 1. Bằng chứng đã xem trước khi ký

Nguồn: `results/SMOKE/phase-D/factorial_endpoint_x_load.json`, đọc đủ 28 cặp
từ `results/LIVE/phase-23/link_corr_matrix.json`.

| Số link low-σ | Chung host | n | mean r | Vai trò |
|---:|:---:|---:|---:|---|
| 2 | có | 2 | +0.6181 | ô phát hiện |
| 2 | không | 4 | +0.0364 | đối chứng âm H2/H3 |
| 1 | có | 8 | +0.0625 | mixed-load descriptive |
| 1 | không | 8 | +0.0527 | mixed-load descriptive |
| 0 | có | 4 | +0.0171 | đối chứng âm H1 thuần |
| 0 | không | 2 | +0.0145 | noise-floor descriptive |

Các con số này **không** được dùng như xác nhận H4 vì giả thuyết được rút ra
sau khi nhìn ma trận.

## 2. Giả thuyết được khóa trước cell C

### H1 — endpoint-only

Chỉ cần hai kênh chia sẻ endpoint host là đủ sinh `r≈+0.6`; hạ `N_bar` của
edge nhưng giữ `hsrc`/`hdst` không làm tương quan sụp.

### H2 — link-dynamics-only

Bundle `sigma/tau/lifetime` tự sinh tương quan, không cần host chung. Bốn cặp
low-σ không chung host đã chống H2 ở mức hậu kiểm; cell C không phải test độc
lập hoàn hảo cho H2 vì nó đổi chính bundle này.

### H3 — sampling/shared-transient

`r≈+0.6` là artifact của duration/burn-in. Bốn cặp low-σ không chung host đã
chống H3 ở mức hậu kiểm, nhưng run 120 s cũ vẫn không có hậu burn-in theo
`5*tau_pred` của link chậm nhất. Cell C dùng budget đủ dài để loại thiếu mẫu
khỏi chính outcome mới.

### H4 — endpoint × low-σ/high-`N_bar` bundle interaction

Tương quan cao chỉ xuất hiện khi đồng thời có endpoint chung và cả hai channel
nằm trong bundle low-σ/high-`N_bar`. Đây là phát biểu tương tác. Nó không khóa
cơ chế “số heap operation tăng 11×”: code không có tính chất đó. Các cơ chế
runtime cụ thể vẫn là ứng viên và cần instrumentation riêng.

## 3. Thiết kế cell C

Chỉ thay một CLI factor so với cấu hình A:

```text
rho_bar          0.925
core_sigma       0.10   (giữ nguyên)
edge_sigma       0.10   (đổi từ 0.03)
kappa            2.5
size_min_kb      20
duration_s       240
log_dt_s         0.010
measured_window  0.200
measurement_mode clean
rep/seed          1/11, 2/12, 3/13
```

`meta_clean_rho0.925_rep3.json` cũ cho dự đoán:

| Link edge | `N_bar` cũ | `N_bar` cell C | `tau_pred` cũ | `tau_pred` cell C |
|---|---:|---:|---:|---:|
| uA | 817.0 | 73.5 | 20.63 s | 1.86 s |
| uB | 855.6 | 77.0 | 28.15 s | 2.53 s |
| vC | 817.0 | 73.5 | 20.63 s | 1.86 s |
| vD | 875.2 | 78.8 | 28.47 s | 2.56 s |

Core không đổi; `ad` có `tau_pred=4.2769 s`, là max bảo thủ. Duration được
suy trước khi chạy:

```text
burn = 5*tau_max = 21.38 s
analysis_time = 240 - burn = 218.62 s
n_eff conservative = analysis_time/(2*tau_max) = 25.56 >= 25
```

## 4. Estimator khóa

1. Với từng rep và từng link, lấy `rho_measured` sau khi bỏ missing samples.
2. Tính ACF bằng FFT; integral time scale cắt tại lag dương cuối trước lần
   đầu `ACF<=0`.
3. `tau_pair=max(tau_a,tau_b)`; bỏ `ceil(5*tau_pair/dt)` mẫu đầu.
4. Tính Pearson `r` riêng trong từng rep, không nối ba trace.
5. Outcome gộp: `tanh(mean(atanh(clip(r_rep))))`.
6. `n_eff_rep=T_after_burn/(2*tau_pair)`; không dùng row count làm n.
7. In đầy đủ `r_rep`, pooled r, tau, burn, `n_eff_rep`, drift và infra flags.

Primary pair: `uA-uB`. Secondary confirmatory symmetry pair: `vC-vD`.
`ac-ad` và `uA-vC` là controls, không phải outcome phụ để chọn kết luận.

## 5. Outcome partition — phủ kín, không có khe hở

Phán quyết dùng pooled `r(uA,uB)` và yêu cầu ít nhất 2/3 rep rơi cùng vùng với
pooled estimate. Nếu điều kiện consistency không đạt, outcome là UNRESOLVED.

| Pooled r | Nhãn khóa trước | Diễn giải được phép |
|---:|---|---|
| `[-0.10, +0.15]` | `H4_SUPPORTED_H1_REFUTED` | nhất quán với endpoint × bundle interaction |
| `(+0.15, +0.45)` | `UNRESOLVED_INTERMEDIATE` | không phân giải H1/H4 |
| `[+0.45, +0.75]` | `H1_SUPPORTED_H4_REFUTED` | endpoint-only được ưu tiên |
| `<-0.10` hoặc `>+0.75` | `OUT_OF_RANGE_MODEL_FAILURE` | không ép vào H1/H4; mở limit mới |

Biên `+0.15` thuộc H4; biên `+0.45` thuộc H1. Nếu controls/validity fail thì
nhãn cuối là `INVALID_RUN`, bất kể pooled r.

## 6. Controls bắt buộc

### Negative controls

- NC-C1: `r(ac,ad)` pooled phải thuộc `[-0.10,+0.15]`. Hai kênh vẫn chung
  sender hA nhưng core config không đổi.
- NC-C2: `r(uA,vC)` pooled phải thuộc `[-0.10,+0.15]`. Hai kênh cùng bundle
  edge mới nhưng không chung host.

### Positive controls

- PC-C1: mỗi edge metadata có `warm_start_active`/`n_concurrent` khớp
  `round(rho_target^2/0.10^2)` trong sai số làm tròn 1 flow.
- PC-C2: median `tau_edge` cell C nhỏ hơn median cũ ít nhất 5×. Dự đoán lý
  thuyết là 11.111×; khóa 5× để chịu sai số estimator nhưng vẫn có độ nhạy.
- PC-C3: output ghi đúng `core_sigma=edge_sigma=0.10`, đúng seed và duration.

## 7. Validity gate

- Mỗi primary/secondary/control pair có `n_eff_rep>=25` ở cả 3 rep.
- Burn-in thực tế của mỗi pair ít nhất `5*tau_pair`.
- Infra monitor chạy phủ toàn bộ mỗi rep; bốn cờ CPU/swap/drop/clock đều false.
- Không thiếu link, không NaN correlation, không counter reset chưa xử lý.
- Prereg này và tool factorial đã commit; tag `phase-D-cellC-start` tồn tại
  trước timestamp của raw run đầu tiên.

Giả thuyết nào thắng **không** phải validity gate.

## 8. Lệnh dự kiến sau khi ký

Mỗi rep dùng đường dẫn riêng dưới `results/RAW/phase-D/cellC/`. Trước mỗi rep
phải chạy `sudo mn -c`; infra monitor bắt đầu trước Mininet và dừng sau Mininet.

```bash
sudo .venv/bin/python -m mininet.run_sync_v7 \
  --traffic v7 --duration 240 --log-dt 0.010 --measured-window 0.200 \
  --rho-bar 0.925 --core-sigma 0.10 --edge-sigma 0.10 \
  --kappa 2.5 --size-min-kb 20 --measurement-mode clean \
  --seed 11 \
  --offered-out results/RAW/phase-D/cellC/rho_offered_rep1.csv \
  --measured-out results/RAW/phase-D/cellC/rho_measured_rep1.csv \
  --meta-out results/RAW/phase-D/cellC/meta_rep1.json \
  --flow-log-dir results/RAW/phase-D/cellC/flows_rep1
```

Rep 2/3 chỉ đổi seed `12/13` và suffix `rep2/rep3`. Lệnh này chưa được phép
chạy khi header còn `DRAFT_LOCKED_FOR_SIGNATURE`.
