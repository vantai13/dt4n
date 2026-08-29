# Phase D′ — giới hạn bổ sung sau kiểm toán

| ID | Giới hạn / phát hiện | Trạng thái |
|---|---|---|
| D-L1 | Generator mức luồng khóa `sigma` và time scale qua kích thước/rate/lifetime; hai trục không độc lập | đã hiểu, chờ generator mới để tách trục |
| D-L2 | `LOAD_SIGMA_TARGET` và `LOAD_TAU_TARGET_STEPS` chỉ là mục tiêu lịch sử, không phải cặp đã đạt | đã deprecate trong code |
| D-L3 | Tám parquet Phase 21R không tái tạo được bằng code hiện tại; provenance gốc ghi dirty commit | mở; không được xoá |
| D-L4 | Không có trace 1800 s được yêu cầu bởi scaling test trong working tree hiện tại | mở; audit dùng 15 run 120 s hiện có, không giả là scaling 1800 s |
| D-L5 | Suy `n_eff` chỉ từ `tau_pred_s` của generator mâu thuẫn với ACF đo trực tiếp trên `rho_measured` | đóng theo phép đo mới: ưu tiên ACF của chính đại lượng phân tích |
| D-L6 | Cơ chế “~900 socket” không tồn tại; `FlowEngine` có một UDP sender socket mỗi process, sink có một receiver socket | đóng bằng đọc code |
| D-L7 | Con số 817–875 là số luồng ảo warm-start, không phải số socket | đóng; khớp metadata và `rho^2/sigma^2` |
| D-L8 | `results/DATA_MANIFEST.json::doi` còn `null`; chưa có Version DOI | mở, cần thao tác tài khoản ngoài |
| D-L9 | Backup 6.5 GiB mới chỉ nằm trên cùng máy | mở, cần sao chép ra phương tiện/tài khoản khác |
| D-L10 | Run cũ 120 s ngắn hơn `5*tau_pred` của uB/vD (140–151 s theo max campaign); không có vùng hậu burn-in theo estimator generator dù measured-ACF T8 cho n_eff lớn | mở; không tráo hai estimator. Cell C dùng 240 s; cấu hình A muốn đóng riêng cần run dài |
| D-L11 | Cell C đổi đồng thời sigma, lifetime, tau và N_bar; dù H4 thắng cũng chỉ xác nhận endpoint × configuration bundle, không nhận dạng riêng N_bar hay heap cost | mở có chủ đích; tách trục cần generator mới hoặc intervention khác |
| D-L12 | Giả thuyết “access link host chung bị bão hòa” bị bác về tải danh định: access link là 1000 Mbps (`run_sync_v7.py:89`), trong khi tổng tải lớn nhất qua một host chỉ ≈17.0 Mbps (<1.7%) | đóng bằng code + metadata `rho_bar=0.925, rep3` |
| D-L13 | Giả thuyết “tổng tải namespace càng cao thì r càng cao” có thứ tự ngược: hA ≈16.675 Mbps với `r(ac,ad)=+0.0358`; hB ≈16.995 với `r(bc,bd)=+0.0314`; hsrc chỉ ≈12.125 với `r(uA,uB)=+0.5986` | bác ở mức mô tả; không loại mọi hiệu ứng endpoint/runtime |
| D-L14 | `lambda=rho*C/mean_size` không phụ thuộc sigma (uA ≈25.1, ac ≈21.5 arrival/s); độ sâu heap chỉ đổi chi phí operation theo `O(log N)`, với `log2(817)/log2(96)=1.47×`, không phải 9.9× | cơ chế heap chưa nhận dạng; số học bác diễn giải “11× operation rate” hoặc “9.9× do log-heap” |
| D-L15 | Theo median `tau_pred`, `5*tau_uB=136.7 s` và `5*tau_vD=138.4 s`, lớn hơn run 120 s; budget `55*tau` cho cấu hình A là khoảng 1504–1522 s (tới 1663 s nếu dùng max campaign) | mở; T8 measured-ACF n_eff lớn không thay thế gate burn-in này |
| D-L16 | `c_a` không phải thống kê đủ cho traffic family; full-grid chỉ có cbr/poisson/h2, onoff chỉ có key `6|13`. Sensitivity T6 giữ D3 band nhưng đổi highest cell dưới cbr (`clean@0.700` thay vì `clean@0.960`) | L141 vẫn mở cho cell selection; không mở rộng ba họ thành mọi họ khả dĩ |
| D-L17 | Trust-gate p99 0.222126 ms được đo một lần trên máy local, CPU p95 15.5%, chưa đo dưới tải. So với sync/control 500 ms là 0.0444%, nhưng con số này chưa phải tail bound production | D-9 PASS local; giữ phép đo under-load cho Phase 24 |
| D-L18 | Cell C đủ 3×240 s nhưng validity fail: ACF-tau edge measured chỉ giảm median khoảng 1.1× thay vì PC-C2 ≥5×; ba pair-rep có n_eff 20.383, 23.894, 10.536 <25. Điều này lộ mâu thuẫn giữa giả định `tau~sigma^-2` của generator và time scale của `rho_measured` dùng làm outcome | Cell C `INVALID_RUN`; dừng trước C′, không diễn giải pooled r; Lesson D.2 đóng unresolved theo ngân sách một vòng |

## Đính chính quan trọng so với bản hướng dẫn đầu vào

Giả thuyết H3 “`r≈+0.6` chỉ do thiếu mẫu” là một giả thuyết hợp lý ở thời
điểm chỉ có `tau_pred_s`, nhưng bằng chứng mới hơn trong repo không ủng hộ
kết luận đó. Trên 15 run CLEAN độc lập:

```text
uA-uB measured +0.5986, offered +0.1725
vC-vD measured +0.6376, offered -0.1832
ac-ad  measured +0.0358
bc-bd  measured +0.0314
```

Shortfall endpoint trong `host_confound_probe.json` là `+0.9020` và
`+0.9612` cho hai cặp biên. Factorial audit bổ sung cho thấy endpoint là điều
kiện chưa đủ: cặp chung host với hai `N_bar` nhỏ có mean r=+0.0171. Hiện tượng
được giữ như ứng viên tương tác endpoint × low-sigma/high-N bundle; nó không
được diễn giải thành path coupling vật lý trước cell C.
