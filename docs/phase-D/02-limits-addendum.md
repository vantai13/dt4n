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
| D-L18 | PC-C2 cũ sai loại đại lượng: control phía generator `tau~sigma^-2` bị đánh giá trên `rho_measured` có median edge signal fraction 0.3696, nên nugget làm co integral ACF và triệt độ nhạy sigma. Amendment A001 giữ dấu vết cũ rồi kiểm lại trên offered; PC-C2′ vẫn MISS theo ngưỡng ký trước: ratio từng edge 4.942/7.145/4.048/2.878, median 4.495 <5 | Cell C vẫn `INVALID_RUN` dưới A001, nay vì generator control signed MISS chứ không còn vì ratio measured 1.1×; không được hạ threshold hậu nghiệm |
| D-L19 | Estimator ACF cũ dùng `nlag=n//10`; với T=120 s, dt=0.2 s chỉ nhìn tối đa 12 s trong khi tau edge metadata 20–28 s. A001 tăng lên `min(n//4,3000)`, nhưng ba baseline offered 120 s vẫn bị finite-trace/censoring: một số run chạm đúng trần lag 30 s | Tau offered Cell A ước lượng 7.55–13.98 s theo median link, thấp hơn 12.58–21.86 s của trace Phase-20 dài 240 s; cần run dài hoặc estimator fit được ký mới, không được đổi sau A001 |
| D-L20 | Mọi r trên `rho_measured` có thể bị common-mode nugget chi phối. Classical disattenuation độc lập cho uA-uB dùng signal fraction khoảng 0.370 cho `0.5986/0.370=1.62>1`, nên mô hình independent-error đơn giản không admissible; shared measurement component là ứng viên mạnh. Cell C measured r sụp và offered r≈0 là hậu kiểm hỗ trợ nhưng A001 không qua control | Không dùng raw measured r làm coupling vật lý; Phase G phải đo `counter_read_dt`/common-mode và signal fraction, hoặc dùng offered. H6 là leading post-hoc model, chưa được nâng thành confirmatory bởi A001 |
| D-L21 | Nhánh baseline Cell A có `T/tau = 120/29.3 = 4.1`, trong khi sàn của chính dự án là `T/tau >= 50` (D-L15). `tau_hat` nhánh A bị lệch xuống bởi hai nguồn cộng dồn — truncation `1-exp(-L/tau)=0.641` và mean-removal `1-2*tau/T=0.512` — cho `tau_hat_A ~ 9.6 s` thay vì 29.3 s, `tau_hat_C ~ 2.58 s`, tỉ số ước lượng ~3.7× so với quan sát 4.495×. Thêm nữa `L = 30 s` của A001 đến từ `NLAG_CAP=3000` chứ không từ `n//4`, và trần đó **bị chạm thật** (`cut_lag==nlag==3000` ở 3/12 ước lượng Cell A, 1/12 Cell C), nên kéo dài run mà không nâng cap sẽ không sửa được truncation | A002 chẩn đoán; PC-C2″ thu `cellA_long` 1505 s và nâng `NLAG_CAP` đối xứng 3000→50000 (A: L=376 s, C: L=60 s) |
| D-L22 | Ngưỡng `>=5.0` của PC-C2/PC-C2′ được ký từ dự đoán lý thuyết 11.11× mà **không ký kèm bias của estimator ở từng nhánh**. Với nhánh A lệch ~3× và nhánh C không lệch, một thí nghiệm hoàn hảo cũng chỉ cho ~4.5: ngưỡng đã không thể đạt được ngay từ lúc ký | quy tắc phương pháp: ký ngưỡng trên đại lượng ước lượng phải kèm phép kiểm `T >= 50*tau` cho MỌI nhánh; áp dụng từ PC-C2″ trở đi |
| D-L23 | `signal_fraction` là ACF ngoại suy về lag `0+`, miền vật lý `[0,1]`; `sf=1` nghĩa là hết nugget. Rule A080 coi `exp(intercept) > 1` là fit invalid nên **không thể kiểm định** một estimator chạm trần: `vD=1.0040` chính là `sf=1.000 ± noise`. Đây là lỗi đặc tả rule, không phải lỗi dữ liệu | không override A001; PC-C2″b ký rule mới `sf=min(1,exp(intercept))` + `at_ceiling`, invalid chỉ khi `intercept > 3*se(intercept)` |
| D-L24 | `FIT_LAGS=(1..20)` cố định phủ `0.007*tau..0.14*tau` ở Cell A nhưng `0.08*tau..1.5*tau` ở Cell C — cùng một estimator chạy ở hai chế độ khác nhau trên hai nhánh của cùng một control | PC-C2″b chuẩn hóa fit lag theo `tau` của chính cell (~`0.2*tau..2*tau`), tuple khóa cứng trước khi chạy |

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
