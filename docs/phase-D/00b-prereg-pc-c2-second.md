# PRE-REGISTRATION — PC-C2″ (Phase D′, sau Amendment D-A002)

```text
Ngày ký                  2026-08-29
Trạng thái               SIGNED_BEFORE_DATA_COLLECTION
Người ký                 Claude Code execution agent, theo chỉ thị của người dùng
Tag khóa                 phase-D-pc-c2-second-start
Dữ liệu mới              đúng MỘT run Mininet (cellA_long), ~25 phút
Ngân sách                hết sau vòng này; không có vòng 3
```

File này được commit và tag **trước** khi tồn tại bất kỳ byte raw nào của
`results/RAW/phase-D/cellA_long/`. Cơ sở chẩn đoán là
`A002-amendment-pc-c2-prime.md`. A001 và phán quyết `INVALID_RUN` của Cell C
trong `03-gate-decision.md` **không** bị sửa bởi file này.

## 1. Dữ liệu mới cần thu — đúng một run

```text
ten cell   cellA_long
duration   1505 s   (= 55 * 27.35 s, tau_uB tu tau_by_link_from_meta)
seed       41
core sigma 0.10
edge sigma 0.03
rho_bar    0.925    kappa 2.5    size_min_kb 20
log_dt     0.010 s  measured_window 0.200 s   measurement_mode clean
rep        1  (POSITIVE CONTROL, khong phai uoc luong can CI)
```

Lý do: Cell A hiện tại có `T/tau = 120/29.3 = 4.1`, trong khi sàn của chính dự
án là `T/tau >= 50` (D-L15). Không estimator nào cứu được thiếu hụt 12×.
[D-L21]

### 1.1 Ký trước một sai lệch có chủ đích so với “y hệt Cell A”

Chỉ thị gốc là “y hệt cell A, đổi đúng một thứ: độ dài run”. Trace Cell A hiện
có (`phase-23/aoi_v7_campaign`) chạy với `ditto=True`, `reconcile_every=1`,
`aoi_probe` và `cycle_trace` bật; Cell C chạy với `ditto=False`,
`reconcile_every=30`, không probe. PC-C2″a so **A với C**, nên nếu sao chép
Cell A thì confound ditto/probe vẫn còn nguyên trong tỉ số.

Quyết định đã ký: `cellA_long` sao chép **cấu hình runner của Cell C**, và đổi
đúng hai thứ so với Cell C — `edge_sigma 0.10 -> 0.03` (biến độc lập đang
kiểm) và `duration 240 -> 1505 s` (điều kiện để đo được `tau` nhánh A). So với
Cell C thì contrast là **một biến σ**; so với Cell A cũ thì bỏ được confound
ditto/probe. Ghi rõ ở đây trước khi chạy, không phải chọn sau khi nhìn số.

Lệnh chính xác nằm ở mục 6.

### 1.2 Điều kiện tiên quyết infra

`tools/infra_monitor` chạy song song suốt run. Bốn cờ CPU/swap/drop/clock phải
`false`. Nếu bất kỳ cờ nào `true` thì run bị loại và PC-C2″ trả
`REANALYSIS_INVALID_OR_INCOMPLETE`; không chạy lại (hết ngân sách).

## 2. PC-C2″a — tỉ số tau trên `rho_offered`

```text
estimator      integral ACF, bien, chuan hoa lag-0, tinh bang FFT
cut            lag dau tien co ACF <= 0
nlag           min(n//4, NLAG_CAP)
NLAG_CAP       50 000                       <-- NANG tu 3 000 cua A001
nhanh A        cellA_long, 1 rep            n = 150 500 -> nlag = 37 625 -> L = 376.25 s
nhanh C        cellC rep1/2/3 da co         n =  24 000 -> nlag =  6 000 -> L =  60.00 s
gop            tau_C[link] = median 3 rep ; tau_A[link] = gia tri run duy nhat
ratio[link]    tau_A[link] / tau_C[link]   tren uA,uB,vC,vD
NGUONG         median(ratio) >= 5.0         <-- GIU NGUYEN, KHONG HA
```

`NLAG_CAP` phải nâng vì ở A001 nó là ràng buộc **thật sự bị chạm**
(`cut_lag == nlag == 3000` ở 3/12 ước lượng Cell A và 1/12 Cell C), và vì với
cap 3000 thì một run 1505 s vẫn chỉ nhìn 30 s — tức kéo dài run sẽ không sửa
được truncation. Cap mới áp **đối xứng cho cả hai nhánh**; nhánh C do đó cũng
đổi từ `L = 30 s` sang `L = 60 s`. [D-L21]

`T/tau` sau khi nâng: nhánh A `1505/29.3 = 51` (đạt sàn 50), nhánh C
`240/2.64 = 91` (đạt sàn).

### Dự đoán ký trước — tính trước, kiểm được

```text
mean-removal bias A = 1 - 2(29.3)/1505 = 0.961      (thay vi 0.512)
truncation A, L = 376 s >> tau         = 1.000      (thay vi 0.641)
=> tau_hat_A ~ 29.3 * 0.961 = 28.2 s               (thay vi 9.6 s)
=> tau_hat_C ~  2.58 s
=> ti so ~ 28.2 / 2.58 = 10.9x   =>  PASS >= 5.0 rat thoai mai
```

Nếu tỉ số **vẫn < 5** với `T = 1505 s` và `L = 376 s`, thì khi đó mới thật sự
là vấn đề generator, và S19 (`tau ~ 1/sigma^2`) bị bác. Đó sẽ là một kết quả
LỚN, không phải một lỗi. Ghi lại và dừng.

## 3. PC-C2″b — signal fraction, estimator có miền bị chặn

Sửa **đặc tả** rule (miền giá trị + fit lag), không hạ ngưỡng.

### 3.1 Miền giá trị

```text
raw   = exp(intercept)          tu fit log-tuyen tinh log(ACF) ~ intercept + slope*t
sf    = min(1.0, raw)
at_ceiling = bool(raw > 1.0)
```

Tiêu chí hợp lệ ký trước (KHÔNG dùng hằng số chọn sau khi nhìn số):

```text
valid  <=>  slope < 0
        AND raw > 0
        AND intercept <= 3 * se(intercept)
```

Điều kiện thứ ba nói: intercept **không lệch có ý nghĩa** lên trên
`log(1) = 0`, với `se(intercept)` lấy từ ma trận hiệp phương sai của chính
phép bình phương tối thiểu. Đây là phát biểu thống kê về “chạm trần”, không
phải một biên độ chọn tay. Với `raw <= 1` thì điều kiện tự thỏa mãn. [D-L23]

### 3.2 Fit lag chuẩn hóa theo `tau` của chính cell

`FIT_LAGS = (1..20)` cố định phủ `0.007*tau .. 0.14*tau` ở nhánh A nhưng
`0.08*tau .. 1.5*tau` ở nhánh C — cùng estimator ở hai chế độ khác nhau.
[D-L24] Fit lag mới phủ xấp xỉ `0.2*tau .. 2*tau`, log-spaced, khóa cứng
thành tuple:

```text
dt_measured = 0.2 s
nhanh A  tau_pred edge 20.6 .. 28.5 s  ->  muc tieu  ~5.9 .. ~58.6 s
         A_FIT_LAGS = (30, 40, 50, 65, 80, 100, 125, 155, 190, 240, 300)
                       = 6.0 s .. 60.0 s
nhanh C  tau_pred edge  1.86 .. 2.56 s ->  muc tieu  ~0.5 ..  ~5.1 s
         C_FIT_LAGS = (3, 4, 5, 6, 8, 10, 13, 16, 21, 26)
                       = 0.6 s .. 5.2 s
```

Giữ nguyên `ACF_FIT_MIN = 0.02` của A080. Mean ACF lấy trung bình qua các rep
của cell rồi fit riêng từng edge; không dùng core fit.

### 3.3 Nguồn dữ liệu

```text
nhanh A   results/RAW/phase-D/cellA_long/rho_measured_rep1.csv   (1 rep, ~7 524 mau)
nhanh C   results/RAW/phase-D/cellC/rho_measured_rep{1,2,3}.csv  (3 rep, 1 199 mau/rep)
```

Nhánh A **phải** lấy từ `cellA_long`: trace Cell A cũ chỉ có 599 mẫu, không
đỡ nổi fit lag tới 300. Reference A080 15-run `0.36957` được in kèm như đối
chứng ngoài, không phải điều kiện PASS.

### 3.4 Ngưỡng

```text
NGUONG: sf_A <= 0.50   VA   sf_C >= 0.75
        va ca bon edge cua CA HAI nhanh phai co fit valid theo 3.1
```

### Dự đoán ký trước

```text
sf_A ~ 0.37   (khop reference 23.25d 0.36957 va PC-C2'b 0.3682)
sf_C ~ 0.87 .. 1.00   (mo hinh mot tham so v = 0.0015457 du doan 0.866)
=> PASS ca hai ve
```

## 4. Partition kết quả — không có khe hở

| PC-C2″a | PC-C2″b | Nhãn |
|---|---|---|
| PASS | PASS | `CONTROL_REDESIGN_SUPPORTED_CELL_C_REANALYSIS_VALID` |
| FAIL | bất kỳ | `GENERATOR_CONTROL_FAIL_CELL_C_REMAINS_INVALID` |
| PASS | FAIL | `NUGGET_MODEL_MISS_CELL_C_REMAINS_INVALID_FOR_THIS_AMENDMENT` |
| dữ liệu/infra/fit invalid | bất kỳ | `REANALYSIS_INVALID_OR_INCOMPLETE` |

Chỉ hàng đầu cho phép Cell C được **tái phân xử thành VALID**; khi và chỉ khi
đó mới được đọc outcome đóng băng của Cell C, và phải lấy bit-exact từ
artifact cũ, không chạy estimator khác để chọn số.

Mọi hàng khác: giữ Cell C `INVALID_RUN`, ghi limit, chuyển H6 sang Phase G như
giả thuyết hậu kiểm dẫn đầu. Không sửa threshold sau khi chạy. Không vòng 3.

## 5. Điều PC-C2″ vẫn KHÔNG làm được

- Không tách H4 khỏi H6; chỉ Cell C′ làm được việc đó và Cell C′ không chạy.
- Không nâng H6 lên confirmatory; `v = 0.0015457` hiệu chuẩn từ một điểm.
- Không đóng D-L11 (Cell C đổi đồng thời σ, lifetime, τ, `N_bar`).
- `cellA_long` chỉ 1 seed nên không cho CI của `tau`; nó là positive control.

## 6. Lệnh chạy đã ký

```bash
cd ~/dt4n
PY=/home/ubuntu/miniforge3/envs/sdn_rl/bin/python
mkdir -p results/RAW/phase-D/cellA_long results/PENDING/phase-D logs

$PY -m tools.infra_monitor \
    --out results/PENDING/phase-D/infra_cellA_long.jsonl \
    --duration 1520 --interval 0.1 --tag cellA_long_s41 &
MON=$!

sudo mn -c
sudo "$PY" -m mininet.run_sync_v7 \
    --traffic v7 --duration 1505 \
    --log-dt 0.010 --measured-window 0.200 --measurement-mode clean \
    --core-sigma 0.10 --edge-sigma 0.03 \
    --rho-bar 0.925 --kappa 2.5 --size-min-kb 20 \
    --seed 41 --python-bin "$PY" \
    --offered-out  results/RAW/phase-D/cellA_long/rho_offered_rep1.csv \
    --measured-out results/RAW/phase-D/cellA_long/rho_measured_rep1.csv \
    --meta-out     results/RAW/phase-D/cellA_long/meta_rep1.json \
    --flow-log-dir results/RAW/phase-D/cellA_long/flows_rep1 \
    2>&1 | tee logs/phase_d_cellA_long_s41.log
sudo mn -c

wait $MON
$PY tools/summarize_infra.py results/PENDING/phase-D/infra_cellA_long.jsonl
$PY -m tools.phase_d_pc_c2_second
```

Artifact máy đọc: `results/SMOKE/phase-D/pc_c2_second.json`.
