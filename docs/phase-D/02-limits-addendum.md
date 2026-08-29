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
`+0.9612` cho hai cặp biên. Vì vậy hiện tượng được giữ là bằng chứng shared
endpoint contention của generator một-hop; nó không được diễn giải thành
path coupling vật lý.
