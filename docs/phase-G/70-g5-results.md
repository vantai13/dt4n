# G′.5 — Kết quả phép chuyển estimand

**Phán quyết: `TRANSFER_FAILS`.** Đề xuất doc 47 (ω là trục coverage) **không được adopt**.
`kappa_time = 5` của [doc 42](42-amendment-G-A014-certificate-renewal.md) §"PC", ký từ [G-A010](30-amendment-G-A010.md) **giữ nguyên hiệu lực**.
Nghiên cứu tổng hợp, không chạy mạng. Prereg: [doc 69](69-prereg-g5-estimand-transfer.md), tag `phase-G2-g5-prereg`, commit `6702d310`.
Ngưỡng, lưới ω, số lượt, seed và bốn thủ tục đều cố định trước khi chạy; không đổi sau khi thấy kết quả.

Mã chấm điểm Phase 22 (`cert/simultaneous_score.py`, `cert/margin_score.py`, 23 golden test) **không bị sửa một dòng**.
Công cụ tự kiểm tra bằng `git show phase-G2-g5-prereg:<path>` trước và sau khi chạy; chỉ đầu vào `y_true`/`y_hat` là mới.

## 1. Bảng gate

| Gate | Đại lượng | Ngưỡng đã ký | Đo được | Kết quả |
|---|---|---|---:|---|
| `T-1` | biên độ coverage đồng thời trên khe xếp hạng | >= 0.020 | 0.004441 | **FAIL** |
| `T-2` | biên độ / SD một vệt | >= 3.0 | 0.144917 | **FAIL** |
| `T-3` | bước liền kề xấu nhất | >= -0.002 | -0.002897 | **FAIL** |
| `NC-1` | trôi coverage biên | <= 0.005 | 0.003073 | PASS |
| `NC-2` | biên độ trên tập chỉ `{uA, uB}` | <= 0.005 | 0.000000 | PASS |
| `NC-3` | neo phụ thuộc tại ω=0 | báo cáo | +0.041859 | báo cáo |

`NC-1`/`NC-2` PASS nên bộ sinh **không** bị nghi ngờ: ω đúng là chỉ ghép được các link có đường chung.
Trên tập `{uA, uB}` (`K_TOPO = 0`) biên độ bằng **đúng 0** ở cả bốn thủ tục — khối hiệp phương sai bất biến theo ω nên cùng innovation cho cùng kết quả bit-đối-bit.
`T-1` FAIL với biên độ nhỏ hơn ngưỡng **4.5 lần**, và `T-3` FAIL vì chuỗi không đơn điệu — nó là nhiễu quanh một đường phẳng.

## 2. Bốn thủ tục, đều báo cáo như đã ký

`qhat_per_slot(alpha_each=.10)` mà nhận xét đề nghị là **đối chứng không hiệu chỉnh** của Phase 22 (`PC22-2`), không phải chứng nhận đang dùng.
Prereg §1 đã cố định trước: gate chính chạy trên đối chứng đó, còn adoption **thêm** điều kiện max-score phải đạt cùng `T-1 = .020`.

| Thủ tục | coverage ω=0 | ω=1 | biên độ | SNR | trôi biên | `NC-3` | cận trên 95% biên độ |
|---|---:|---:|---:|---:|---:|---:|---:|
| uncorrected (đối chứng) | 0.770213 | 0.771757 | 0.004441 | 0.1449 | 0.003073 | +0.041859 | 0.009621 |
| Bonferroni | 0.914360 | 0.914027 | 0.000524 | 0.0281 | 0.000506 | +0.012795 | 0.004611 |
| Šidák | 0.911594 | 0.911288 | 0.000455 | 0.0240 | 0.000522 | +0.013299 | 0.004659 |
| **max-score (chứng nhận 22R)** | 0.898317 | 0.898162 | **0.000714** | 0.0348 | 0.002360 | +0.015914 | **0.005493** |

Chứng nhận thật sự đang dùng là max-score, và ở đó hiệu ứng **nhỏ hơn 28 lần** so với ngưỡng.
Không có thủ tục nào đạt `T-1`; không có cửa nào để adopt qua đường khác.

## 3. Vì sao phép chuyển thất bại: đây là hiệu ứng theo `K`, không phải do trung bình hoá

Phần tính lại doc 47 đã lưu **cả `K = 2` lẫn `K = 8`** như prereg §4 yêu cầu. Đó là mấu chốt giải thích:

| Không gian | Số phát biểu đồng thời | Biên độ theo ω |
|---|---:|---:|
| link, doc 47, nugget chứng nhận, dt=0.1 | K = 8 | **0.135766** |
| link, cùng dữ liệu, cùng lượt | K = 2 | **0.001062** |
| khe xếp hạng 22R, max-score | 3 khe | **0.000714** |

Cùng một bộ sinh, cùng ω, cùng nugget: hiệu ứng ω lên coverage đồng thời **lớn dần theo số phát biểu phải đúng cùng lúc**.
Ở `K = 2` nó đã gần như biến mất, và 22R chỉ phát biểu **ba** khe. Con số 0.000714 của khe xếp hạng nằm đúng thang với 0.001062 của `K = 2`.

Nghĩa là biên độ 0.108 của doc 47 **không** phải một tính chất của ω truyền được sang estimand khác; nó là tính chất của **estimand 8-link**.
Trong ba kiểu chết mà nhận xét dự đoán, dữ liệu chỉ ra kiểu thứ nhất theo một nghĩa cụ thể hơn: không phải "trung bình hoá qua 3 link mỗi đường", mà là **22R chỉ cần 3 phát biểu đúng cùng lúc thay vì 8**.
`NC-3` bác bỏ "chết kiểu 2": phụ thuộc do `e(a1)` dùng chung tại ω=0 chỉ là +0.0159 ở max-score, tức còn thừa chỗ cho ω nếu ω có gì để đóng góp.

## 4. ω vẫn có tác dụng đo được — nhưng lên **công suất**, không lên coverage

Đây là quan sát mô tả từ cùng file kết quả đã đóng băng, **không phải gate**, và không có trong bảng gate đã ký.

| Thủ tục | q̂ trung bình ω=0 → ω=1 | tỉ lệ chấp nhận ω=0 → ω=1 | tỉ lệ quyết định sai trong tập chấp nhận |
|---|---|---|---|
| uncorrected | 11.676 → 15.333 (+31.3%) | 0.6238 → 0.5400 (−13.4%) | 0.008644 → 0.012919 (+49.5%) |
| Bonferroni | 15.281 → 20.218 (+32.3%) | 0.5310 → 0.4314 (−18.8%) | 0.002939 → 0.004840 (+64.7%) |
| Šidák | 15.175 → 20.075 (+32.3%) | 0.5335 → 0.4343 (−18.6%) | 0.003021 → 0.004971 (+64.5%) |
| max-score | 14.698 → 19.427 (+32.2%) | 0.5403 → 0.4382 (−18.9%) | 0.003306 → 0.005179 (+56.7%) |

Cơ chế nhất quán: ω làm sai số đường phình ra, q̂ hiệu chuẩn nở theo, coverage được **giữ nguyên đúng như thiết kế conformal**, và cái phải trả là **số cửa sổ được chứng nhận**.
Chứng nhận không hỏng khi ω tăng; nó **đắt hơn**. Với max-score, gần 19% cửa sổ chấp nhận được ở ω=0 không còn chấp nhận được ở ω=1.

Vì vậy ω vẫn phải nằm trong nhãn chế độ của chiến dịch, nhưng với vai trò **trục công suất/chi phí**, không phải trục coverage. Đây là input cho `G′.6`/`G′.7` về ngân sách cửa sổ, không phải một tuyên bố chứng nhận mới.

## 5. `R-1`, `R-2` — suy lại doc 47 dưới nugget đã chứng nhận

Doc 47 §8 tự ghi limit 3: *"the nugget is white"*. `G′.4` chứng nhận nugget là MA(1) với `ACF(1) = −0.5`. Limit đó đến hạn và đã được kiểm.
Phần chạy lại tái tạo được đúng bảng doc 47 gốc ở `rtol = atol = 1e-12` trước khi thêm ô mới.

| dt | biên độ | trắng | Gauss MA(1) | dư uniform MA(1) |
|---:|---|---:|---:|---:|
| 0.2 | sf=0.85 (doc 47) | 0.106602 | 0.107420 | 0.108440 |
| 0.2 | công thức chứng nhận | 0.149645 | 0.150100 | 0.149927 |
| 0.1 | sf=0.85 | 0.108637 | 0.108102 | 0.108886 |
| 0.1 | công thức chứng nhận | 0.136128 | 0.135337 | **0.135766** |

`R-1`: giữ nguyên phương sai biên của nugget, **màu của nugget gần như không đổi biên độ** — chênh lệch giữa trắng và MA(1) là ≤ 0.0009, nhỏ hơn hai bậc so với chính biên độ.
Giả định nugget trắng của doc 47 **không chịu tải**; kết luận số học của doc 47 vẫn đứng sau khi thay bằng nugget đã chứng nhận.

`R-2`: ở sf của certificate v2, biên độ **tăng** lên 0.1358 (dt=0.1) và 0.1499 (dt=0.2), so với 0.1086/0.1084 khi giả định sf=0.85. Dự đoán 0.13–0.15 của nhận xét trúng.
Chỉ hàng dt=0.1 là `SYNTHETIC_AT_CERTIFIED_DT`; hàng dt=0.2 là **ngoại suy**, `G′.4` không đo ở dt đó.

Kết luận của mục này: doc 47 **đúng về vật lý link** và **mạnh hơn** nó tự báo cáo. Nó chỉ không chuyển được sang estimand mà luận văn thực sự tuyên bố.

## 6. Dự đoán trước khi chạy so với kết quả

| Đại lượng | Dự đoán đã ký | Đo được | |
|---|---|---:|---|
| biên độ khe xếp hạng | 0.02 – 0.09 | 0.004441 | **trượt** |
| `NC-1` | < 0.002 | 0.003073 | trượt nhẹ, vẫn dưới gate 0.005 |
| `NC-2` | < 0.002 | 0.000000 | trúng |
| `NC-3` | 0.02 – 0.10 | 0.041859 | trúng |
| biên độ link tại sf chứng nhận | 0.13 – 0.15 | 0.135766 | trúng |

3/5 trúng. Đại lượng trượt là đúng đại lượng quyết định lesson này — đó là lý do phải ký dự đoán trước khi chạy.

## 7. Quyết định append-only

1. **Không adopt doc 47.** §9 của nó tự chặn chờ phép chuyển estimand; phép chuyển đã được kiểm và không đạt ngưỡng đã ký.
2. **`kappa_time = 5` của doc 42 giữ nguyên.** Không có bằng chứng để rút. Hệ quả ngân sách `T_run × 5` vẫn còn, và `G′.6` phải xử lý nó như một ràng buộc thật.
3. **Không tuyên bố bất biến toàn cục.** `T-1` FAIL nghĩa là *thiết kế tổng hợp hữu hạn này* không phát hiện được hiệu ứng, không phải chứng minh ω không bao giờ đổi coverage.
4. **Cận trên đúng để trích dẫn là 0.0055**, cận trên 95% Bonferroni trên 10 tương phản của biên độ max-score trong lưới ω đã kiểm. **Không** dùng 0.0271 của `G′.3a` — đó là sai số phục hồi ω, không phải giới hạn thay đổi coverage; prereg §3 đã cấm việc này trước khi chạy.
5. **ω ở lại nhãn chế độ như trục công suất**, với chứng cứ ở mục 4, không phải như trục coverage.
6. `κ` đã tách tên: `kappa_nugget = 2` (`G′.4`), `kappa_time = 5` (doc 42), `kappa_accept = 1` (Phase 22). Mã mới dùng `tools/g5_parameters.py`; JSON và mã lịch sử được tham chiếu bằng hash **không** bị đổi tên.

## 8. Giới hạn

- Toàn bộ là mô hình tổng hợp sai số twin, **không phải chạy gói thật**. Không có clipping, không có nhiễu hạ tầng, `y_true` độc lập với sai số, thang 100 ms/đơn vị ρ được cố định trước.
- Coverage ở đây là coverage thực nghiệm trên dữ liệu AR(1) phụ thuộc; conformal split không có định lý trao đổi được cho chuỗi phụ thuộc, và `qhat` dùng `n_rows` mặc định.
- `NC-3` gộp cả phụ thuộc do đường vật lý dùng chung và do xếp hạng, **không** tách riêng thành phần `e(a1)`.
- Kết luận chỉ áp cho `K = 4` hành động / 3 khe, `dt = 0.1`, `τ = 3 s`, `σ_ref = 0.028` tại `uA`, ω trên lưới 5 điểm.
- `G′.4` chỉ đo ω=0; không có chứng nhận vật lý cho nugget ở ω=0.5.
- DOI Zenodo vẫn **null**: môi trường không có token/kết nối. `tools/zenodo_reserve_doi.py` chỉ dựng yêu cầu cục bộ, và một DOI dự trữ không tự nó qua được cổng lưu trữ công khai — bản nháp không phải bộ dữ liệu bất biến đã xuất bản. `G′.7`/`G′.8` vẫn bị chặn.

## 9. Artifact

| File | SHA256 |
|---|---|
| [g5_estimand_transfer.json](../../results/SMOKE/phase-G2/g5_estimand_transfer.json) | `8d6b5ec7820c8deff1ac4151831a3627013972a2814b2c4dda27f83960add9b7` |
| [g5_doc47_recomputed.json](../../results/SMOKE/phase-G2/g5_doc47_recomputed.json) | `fcc4125e9604066acc5bb24777384a67a28782dd7e9585c95f502f57f651dc98` |
| [g5_slot_coverage.csv](../../results/SMOKE/phase-G2/g5_slot_coverage.csv) | `8402451f59692b5e62ef05ce9d522f5357137c0a87a5194b6570cf142774292e` |
| [g5_link_coverage.csv](../../results/SMOKE/phase-G2/g5_link_coverage.csv) | `b4142a71a31b2f1bc9c99705ac988a520abe6e04bf3f92a8a07fbc4298001269` |
| [g5_transfer.png](../../results/SMOKE/phase-G2/g5_transfer.png) | `a198aa12df8b42b2597792ca33e0b87e38d825d0fbf78d5b1a11da44bd25da21` |
| [g5_rho_eps_null.json](../../results/SMOKE/phase-G2/g5_rho_eps_null.json) | `11337d8f8f3d12e7af17f8551a8ab682362874e0f2ebaf5a334056b01d928778` |
| [measurement_path_cert_v2_1.json](../../results/LIVE/phase-G2/measurement_path_cert_v2_1.json) | `57732bc3d5eb742d35eda1eb104c2627fc1f32b6de61adb89d3aa90d1ef2341c` |

Mã: `tools/g5_estimand_transfer.py`, `tools/g5_parameters.py`, `tools/g5_report.py`, `tools/g5_null_addendum.py`, `test/test_g5_estimand_transfer.py`.
Phụ lục null và proxy `Q-1`: [doc 68a](68a-null-consistency-and-forward-proxy.md).
