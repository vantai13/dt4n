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
| D-L25 | Nugget của `rho_measured` KHÔNG do trace ngắn và KHÔNG do generator. Cùng `sigma_edge=0.03` và cùng estimator A080: phase-23 (ditto bật, `reconcile_every=1`, AoI probe, cycle trace) cho `sf=0.3682`; `cellA_long` (ditto tắt) cho `sf=0.8638`. Đối chứng quyết định: cắt chính `cellA_long` thành cửa sổ 120/240/400/750 s cho `sf=0.938..0.943`, gần như không phụ thuộc T — nên `0.3682` không đến từ `T=120 s`. Bốn yếu tố instrumentation đổi đồng thời nên chưa tách được yếu tố nào | mở; ủng hộ H6 và định vị nguồn nhiễu ở đường đo/đồng bộ. **Đính chính phát biểu:** dạng `sf=sigma^2/(sigma^2+v)` KHÔNG bị bác mà là **underdetermined** ở `ditto=off` — hiệu chuẩn `v_off` từ điểm `sigma=0.03` cho `v_off=1.42e-4` và dự đoán `sf(0.10)=0.986`, không mâu thuẫn với quan sát `≈1` chạm trần; ở `ditto=off` cả hai `sigma` đều sát trần nên dữ liệu không đủ độ phân giải để kiểm dạng hàm. Cái thật sự bị bác là `v` như **hằng số vật lý**: `v_on=1.54e-3` vs `v_off=1.42e-4`, tỉ số **10.9×** ⟹ `sf(sigma, config) = sigma^2/(sigma^2 + v(config))`. Phase G chạy 2×2 `{ditto on/off}×{sigma 0.03/0.10}` để khớp hai tham số `v_on`, `v_off` |
| D-L26 | Prereg PC-C2″ đổi cấu hình nhánh A (`ditto` bật→tắt, bỏ probe/cycle trace) để contrast `A↔C` chỉ còn một biến `sigma`, nhưng vẫn giữ ngưỡng `sf_A <= 0.50` thừa kế từ reference A080 đo ở cấu hình cũ. Đổi cấu hình một nhánh mà không ký lại dự đoán của nhánh đó là **cùng lớp lỗi với D-L22**, lần này do chính PC-C2″ gây ra; PC-C2″b FAIL vì `sf_A = 1.000` | ghi nhận, không hạ ngưỡng hậu nghiệm. Quy tắc bổ sung: mỗi lần đổi cấu hình một nhánh phải kiểm lại MỌI ngưỡng đang gắn vào nhánh đó, không chỉ ngưỡng của control đang sửa |
| D-L27 | `cellA_long` chỉ có `n_runs = 1` (seed 41). `n_eff` trong-run 40.8/40.9 cho CI Fisher hợp lệ nhưng KHÔNG thay thế replicate độc lập; không có phương sai liên-run | mở; Phase G cần ≥3 seed mỗi ô |
| D-L28 | Bundle telemetry đổi BỐN yếu tố cùng lúc (`ditto`, `aoi_probe`, `cycle_trace`, `reconcile_every 1→30`). PC-C3 tách `{bundle}` khỏi `{sigma}` và bác H4, nhưng KHÔNG tách được bốn yếu tố với nhau | mở có chủ đích; cần lưới 2×2 `{ditto on/off}×{sigma}` ở Phase G |
| D-L29 | PC-C3 có công suất tách H4 (`\|dz\|=0.562` vs nửa-CI `0.319`) nhưng KHÔNG có công suất tách H6 khỏi H0 (`\|dz\|=0.131`). Ghi trước khi ký, không phát hiện sau | đóng về mặt ghi nhận; phân xử H6/H0 cần đo trực tiếp `counter_read_dt`/common-mode ở Phase G |
| D-L30 | Partition ký trước của PC-C3 không lường tình huống “hai bản nhân bất đồng NHƯNG cùng bác H4”: `uA-uB→H6`, `vC-vD→H0` cho nhãn `PRIMARY_REPLICATES_DISAGREE`, che mất việc cả hai đều bác H4 ở 3.17σ/4.37σ. Hai bản nhân thực ra nhất quán với nhau (0.84σ); bất đồng chỉ là artifact vạch band | lỗ hổng đặc tả của chính PC-C3; KHÔNG sửa nhãn hậu nghiệm. Quy tắc: partition trên nhãn phải kèm partition trên **tập giả thuyết bị bác** |

## Nguyên tắc phương pháp mở bởi Phase D′

**NT 53 — positive control cho chính ESTIMATOR, tách khỏi positive control cho hệ thống.**
(Được đề xuất trong chỉ thị đầu vào là “NT 58”; đánh lại số theo slot trống kế
tiếp — NT cao nhất đang tồn tại trong repo là `NT 52`.)

> Mọi ngưỡng ký trước trên một **đại lượng ước lượng** phải được kiểm bằng
> cách cho một **ground truth tổng hợp** đi qua **đúng estimator đó**, ở
> **đúng cấu hình của từng nhánh**, TRƯỚC KHI ký.

Cơ sở thực nghiệm trong chính Phase D′: `tools/phase_d_estimator_bias_sim.py`
cho một generator hoàn hảo (tỉ số thật `11.098`) đi qua estimator PC-C2′ và
nhận về `3.635` — ngưỡng `5.0` **bất khả thi về mặt xây dựng**; qua estimator
PC-C2″ nhận về `10.006`. Chi phí của phép kiểm: một script AR(1) ~30 dòng.
Cái nó chặn: một FAIL không thể tránh (`D-L22`), một stop-rule kích hoạt sai,
và một vòng amendment.

Hệ quả bắt buộc kèm theo, từ `D-L26`: khi đổi cấu hình **một nhánh**, phải
kiểm lại **mọi** ngưỡng đang gắn vào nhánh đó, không chỉ ngưỡng của control
đang sửa.

**NT 56 — power của đối chứng phải được chứng minh trước khi đọc phép so.**

> Trước khi so một ước lượng với đối chứng, phải chứng minh độ bất định của
> **thống kê so sánh** nhỏ hơn ngưỡng phán quyết. Một đối chứng hoặc phép so
> nhiễu hơn ngưỡng là `INSUFFICIENT_POWER` và không được đọc theo cả hai chiều.

**NT 57 — gate phải đặt trên chính thống kê mà phán quyết đọc.**

> Trước khi ký, viết công thức của thống kê phán quyết và kiểm gate ràng buộc
> đúng công thức đó, không dùng một proxy chỉ nghe có vẻ tương đương. Với phép
> kiểm ghép cặp G-A004, thống kê là
> `abs(r_true_hat-r_offered)` trên cùng hiện thực, không phải độ chính xác biên
> duyên của riêng `r_offered`.

Định danh NT54--NT55 thuộc master plan ngoài workspace và không được tái dựng
từ trí nhớ tại đây. NT56 được chép lại từ chỉ dẫn Phase G trước; NT57 được ký
bởi `docs/phase-G/13-amendment-G-A004.md`.

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
