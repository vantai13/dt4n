# G-A020 — rút ω khỏi lưới quét hiện tại, báo cáo proxy sigma_eff

Ngày: 2026-09-07 UTC. Trạng thái: `DECISION_NOT_MEASUREMENT`.
Mốc Git: tag `phase-G2-g-a020-decision` trên commit chứa tài liệu này và
các artifact được trích. Đây là dấu đóng băng cục bộ, không là chữ ký mật mã.

Quyết định dựa trên G5c đã phân xử hợp lệ, không đổi gate hay phán quyết cũ.
Amendment này sửa những diễn giải trong hướng dẫn đính kèm không được code
và artifact hỗ trợ; các đính chính được nêu rõ ở §3, §4 và §8.

## 1. Quyết định

1. Rút ω khỏi chiều quét độc lập của chiến dịch 20R2/21R2/22R/23R **khi
   estimand và cấu trúc claim nằm trong phạm vi §4**. Lưới dự kiến còn
   `(rho_bar, sigma, tau, c_a)`. Mỗi phase phải kiểm điều kiện trước khi áp dụng.
2. Giữ ω trong mô hình và metadata; báo cáo `sigma_eff_proxy = sigma*c(ω)`
   với c tính từ covariance, không fit. Không tự thay sigma của bộ sinh
   bằng sigma_eff rồi coi hai phân phối là bằng nhau. Khi bỏ chiều ω,
   prereg của chiến dịch phải ghi mức ω cố định và quy tắc ánh xạ proxy.
3. Báo cáo toàn bộ bằng chứng ω trong Method/Evaluation/Sensitivity, kể cả
   gate cũ VOID, phần dư và độ lệch của proxy. Giữ artifact lịch sử.
4. Áp điều khoản tái xét G-L113; giữ nguyên `kappa_time=5` và các gate vật lý
   đã ký. Việc rút kappa_time cần amendment riêng.

Đây là quyết định phân bổ ngân sách có điều kiện, không phải định lý rằng
không gian vật lý giảm chính xác một chiều. MASTER_PLAN_v10 và các cấu hình
chiến dịch tương ứng không có trong checkout; §5 là amendment kế hoạch
có hiệu lực cho phạm vi trên, không tuyên bố đã sửa file ngoài repo.

## 2. Bằng chứng dùng để quyết định

| Mã | Bằng chứng | Nguồn và số |
|---|---|---|
| E1 | Coverage thay đổi nhỏ ở estimand hiện tại | G5b amplitude 0.00102250; G5c 0.00152500, ngưỡng 0.005; ba seed G5/G5b/G5c là tái lập mô phỏng |
| E2 | Coverage link không chuyển thành hiệu ứng lớn trên khe | G5 maxscore amplitude 0.00071417 vs 0.020; doc 70/70a giữ TRANSFER_FAILS |
| E3 | Cấu trúc coupling trong tập quan trọng, không thể chỉ quy cho K | Doc 70a: K=2, coupling sum≈0.707 → 0.027215; K=4, sum=0 → 0.000551 |
| E4 | Phần dư nhỏ so với hiệu ứng và ngưỡng phân loại | G5c L_total=0.10195333, L_scale=0.10621000, R=+0.00425667; abs(R)<0.03 |
| E5 | Retest có dấu đúng và seed mới | G5c 6/6 gate PASS, POWER_AXIS_HOLDS + REDUCIBLE_TO_EFFECTIVE_SIGMA |
| E6 | Proxy không fit gần hệ số khe đo được | c_analytic(1)=1.30653541; G5b 1.31552310 (+0.6879%); G5c 1.31226265 (+0.4384%) |
| E7 | Null topo không có hiệu ứng acceptance | G5b/G5c NC-2 amplitude=0 chính xác |

SHA256 của từng artifact nằm trong §9. “Coverage nhỏ” là đo trong mô hình,
không là bảo đảm tuyệt đối hay bằng chứng vật lý mới.

## 3. Công thức thay thế và phạm vi chính xác

```text
Sigma_path(ω) = Bᵀ [Sigma_link(ω) + diag(v)] B
sd_j(ω)^2     = Sigma_path[r,r] + Sigma_path[j,j] − 2 Sigma_path[r,j]
c_proxy(ω)    = mean_j(sd_j(ω)/sd_j(0)), j != r
sigma_eff_proxy = sigma_ref * c_proxy(ω)
```

B là INCIDENCE, v lấy từ nugget_variance(CAP_BPS, dt), reference r=0
là **đường cố định đầu tiên** theo topology. Công thức covariance/SD là
chính xác cho các contrast có danh tính đường cố định. API cho phép đổi
reference và hàm contrast_sd nhận incidence bất kỳ để kiểm lại cấu trúc.

| ω | c giải tích | sigma_eff proxy | Spread SD ratio |
|---:|---:|---:|---:|
| 0.00 | 1.00000000 | 0.02800000 | 0.0000% |
| 0.25 | 1.08485027 | 0.03037581 | 1.8572% |
| 0.50 | 1.16347783 | 0.03257738 | 3.2236% |
| 0.75 | 1.23708693 | 0.03463843 | 4.2712% |
| 1.00 | 1.30653541 | 0.03658299 | 5.1002% |

Cài đặt: [g6_sigma_eff.py](../../tools/g6_sigma_eff.py), 13 test,
bao gồm covariance tính tay, triệt tiêu link chung, đổi reference,
scale covariance, xác nhận r_lm=ω*k_lm và phản ví dụ cho thang đồng nhất.
JSON G6 chỉ ghi phép tính xác định và đối chiếu artifact sẵn có, không tạo
một lượt đo mới và không phân xử gate mới.

**Vì sao đây chưa là định luật qhat:** Trong `pair_scores`, a1 là hành động
đứng đầu theo twin **của từng hàng**, không phải đường cố định r=0. Lấy
trung bình SD của các contrast cố định không suy ra phân vị của hỗn hợp
contrast sau chọn/xếp hạng. Ba ratio ở ω=1 là
`[1.28907697, 1.28194684, 1.34858240]`, không đồng nhất. Covariance cũng
không xác định toàn bộ phân phối score khi có nugget uniform MA(1).

Scale-equivariance bảo đảm qhat(c*S)=c*qhat(S) nếu **toàn bộ ma trận score**
được nhân cùng c. Nó không chứng minh việc đổi ω tạo ra ma trận c*S.
Sai lệch 0.4384% là so với trung bình qhat khe; so với qhat **maxscore**
đo 1.32029042, sai lệch là **1.0528%** (mẫu số c giải tích).
Spread giải tích 5.1002% khác spread qhat khe đo 2.0815%; hai đại lượng
khác nhau nên không khẳng định khớp. Không quy toàn bộ chênh lệch cho
xếp hạng hay “phân vị làm mịn” khi chưa có nhận dạng cơ chế.

## 4. G-L113 — điều khoản bảo vệ và kích hoạt lại

Phân loại quy giản thực nghiệm được thiết lập trên **4 hành động / 3 khe
xếp hạng**, topology hiện tại, alpha=0.10, dt=0.1 s, tau=3 s,
sigma_ref=0.028 tại uA, 5 ω và mô hình twin/nugget tổng hợp hiện tại.

Nếu phase sau có **hơn 3 claim**, đổi tập hành động, đổi liên thuộc/link
chung, quy tắc xếp hạng hoặc estimand, G-A020 tự động hết hiệu lực cho
phase đó. K giữ nguyên không đủ để chuyển kết luận: doc 70a đã bác bỏ
cách đọc đơn thuần theo K. Các chế độ sigma/dt/tau, alpha hoặc nugget
khác cũng cần kiểm chuyển giao trước khi tuyên bố quy giản.

Bước rẻ: tính lại covariance/contrast SD bằng công thức trong vài giây.
Bước này chỉ sàng lọc, **không tái chứng nhận** rank-slot coverage/power.
Nếu kết luận cần cho estimand mới thì tiền đăng ký kiểm định chuyển giao,
chạy mô phỏng phù hợp với mô hình/claim mới; chỉ đo mạng khi câu hỏi
đòi bằng chứng vật lý. Không ký trước một chi phí vài giây cho toàn bộ
việc tái chứng nhận khi chưa biết estimand và độ chính xác cần thiết.

G-L113 được đăng ký trong `docs/phase-23/LIMITS.md`.

## 5. Hạng mục kế hoạch bị hủy hoặc thu nhỏ trong phạm vi §4

| Hạng mục MASTER_PLAN_v10 được nêu trong hướng dẫn | Quyết định | Lý do / ước tính từ kế hoạch |
|---|---|---|
| G0.4 tối ưu k_phys và omega_max | Hủy nhiệm vụ tối ưu riêng | Với sigma_l=a0*sqrt(d_l)/C_l, correlation off-diagonal=ω*k_topo và covariance PSD đến ω=1; 3 ngày dự kiến |
| G.P / mininet/traffic_path_v10.py | Hủy nhánh phát triển chỉ nhằm mở trục ω riêng | Không dành chiến dịch riêng cho chiều đã rút trong phạm vi này; 4–5 ngày dự kiến |
| measurements/k_phys.py | Hủy nhiệm vụ phát triển | Không còn cần fit/đo k_phys riêng cho mô hình cố định này; 1 ngày dự kiến |
| G-9, so k_phys đo/dự đoán ±20% | Rút khỏi gate chiến dịch trong phạm vi này | Nhiệm vụ trục ω tương ứng đã rút; không xóa gate/vật chứng lịch sử |
| T2.1 ar1_matrix_omega | Thu nhỏ | Giữ bộ sinh/covariance và sensitivity; bỏ sweep ω lặp tại mọi ô đủ điều kiện; 2 ngày dự kiến |
| T2.3 omega<=omega_max trong realizability_gate | Bỏ tối ưu/ràng buộc riêng trùng lặp | Miền đầu vào 0<=ω<=1 vẫn giữ, cùng headroom/tau/censoring; 0.5 ngày dự kiến |
| Lưới 5 chiều → 4 chiều | Bỏ chiều ω độc lập khi đủ điều kiện | 5 mức ω sẽ cho N_new=N_old/5 (giảm 80% số ô), các chiều khác giữ như cũ |

Các tên file/nhiệm vụ trên không hiện diện như implementation tương ứng
trong checkout. Không xóa tool v7/v9, dữ liệu mạng, kiểm tra đầu vào hoặc
nguồn lịch sử. Không có lưới 20R2 đã đóng băng trong repo để sửa trực tiếp.

“1.5–2 tuần” là **ước tính ngân sách trong hướng dẫn**, không phải số đo
thời gian tiết kiệm. Không cộng tự động các ngày phát triển với tuần chạy
vì có thể chồng lấp. Dành ngân sách dự kiến cho Phase 24; lịch thực tế
cần kế hoạch số ô và phụ thuộc công việc. Giảm số ô 5 lần chỉ đúng khi
chiều ω có 5 mức và tất cả các ô đều đủ điều kiện G-L113.

## 6. Những điều amendment không quyết định

- Giữ `kappa_time=5`, T=200*max(tau_p,tau_g), PC của doc 42 và gate alignment.
- Không đảo phán quyết G′.2/G′.3a/G′.3b/G′.4/G′.5/G′.5b.
- Không nói ω vô nghĩa vật lý; giữ bằng chứng G3a về cơ chế ghép được thiết kế.
- Không gọi kiểm tra covariance là chứng minh bảo toàn byte trên đường vật lý.
- Không tự áp proxy vào code chứng nhận Phase22 hay chiến dịch chưa có trong repo.

## 7. Nội dung có thể dùng trong paper (đã sửa diễn giải)

**Method.** The generator defines off-diagonal link correlations as
r_lm=ω*k_lm, with invariant link variances. We project its covariance,
including the certified nugget variance, onto fixed path contrasts to
compute a non-fitted effective-scale proxy.

**Evaluation.** The previously measured G3a round trip recovered five
coupling levels with worst mean recovery error 0.0271 against a 0.20 budget
(doc 64, including its explicit P-7 readjudication). This concerns the
designed coupling mechanism. The present G5c study is synthetic and adds
no new network measurement.

**Sensitivity.** On an independent preregistered seed, all six power-axis
gates passed. Acceptance fell from 0.53887 to 0.43691 while simultaneous
coverage amplitude was 0.001525. A score-scale surrogate predicted a
loss of 0.10621 versus the observed 0.10195, leaving a positive acceptance
residual of 0.00426. The covariance-derived fixed-contrast scale proxy,
1.30654, was within 0.44% of the measured mean per-slot quantile ratio
1.31226, and within 1.06% of the max-score quantile ratio. We therefore
omit an independent coupling sweep for the present estimand, subject to
revalidation when claim structure or the operating model changes. This
is an empirical reduction and a budget decision, not an exact identity
between changing coupling and multiplying every ranked score by one scale.

## 8. Rủi ro và đính chính so với hướng dẫn đầu vào

| Điểm cần sửa / rủi ro | Bằng chứng hoặc cách phát hiện | Xử lý |
|---|---|---|
| c được gọi là định luật qhat chính xác | Contrast cố định khác rank-slot; ratios không đều | Giữ công thức chính xác cho SD, gọi c là proxy cho qhat; §3 |
| E3 chỉ dựa trên K | Doc 70a đã có đối chứng ngược | Dùng cấu trúc coupling trong tập; mở rộng G-L113 |
| 94.8% chi phí do scale | Artifact G5b cho L_scale=L_total+R | Đính chính dấu tại doc 75 §4; không sửa artifact cũ |
| CRN bị coi là bảo đảm covariance dương | Eigenfactor đổi theo ω; không có định lý dấu | Prereg ghi xác suất có điều kiện; G5c báo paired covariance, không đổi gate |
| Tái xét được gọi là vài giây | Chỉ covariance là phép tính vài giây | Tách sàng lọc giải tích và kiểm chuyển giao mô phỏng |
| Reviewer yêu cầu bảo toàn byte vật lý | Không suy ra từ G5c hoặc công thức covariance | Báo giới hạn G3a; nghiên cứu vật lý riêng nếu cần |
| Hiệu ứng thay đổi ở sigma/tau khác | G5c chỉ chạy một cấu hình | Tính lại proxy và kiểm estimand theo §4; không mặc định rủi ro thấp |

Không gán xác suất số cho các rủi ro khi chưa có mô hình/bằng chứng.

## 9. Chuỗi bằng chứng và SHA256

| Artifact | SHA256 |
|---|---|
| [g5_estimand_transfer.json](../../results/SMOKE/phase-G2/g5_estimand_transfer.json) | `8d6b5ec7820c8deff1ac4151831a3627013972a2814b2c4dda27f83960add9b7` |
| [g5a_mechanism_audit.json](../../results/SMOKE/phase-G2/g5a_mechanism_audit.json) | `1c699b185b363bb95ecd1775a76a11d66aee04b98c8174a39801e56ae990d4e1` |
| [g5b_power_axis.json](../../results/SMOKE/phase-G2/g5b_power_axis.json) | `62239b1f5cef6e276e82854cc691e0ce2e0cfd5eb38f4adab68001b7dbb38600` |
| [g5c_monotone.json](../../results/SMOKE/phase-G2/g5c_monotone.json) | `10e44f07dd57f5bdbaad5ce7f83b878334dc1b47ea18cc30b51773cf24d75d3c` |
| [g6_sigma_eff.json](../../results/SMOKE/phase-G2/g6_sigma_eff.json) | `3ad56f7ac9351ffc3dcec6fa1b5e8af03a451d94839e9812d4f1e76a9c957977` |
| [g3a_omega_sweep.json](../../results/SMOKE/phase-G2/g3a_omega_sweep.json) | `947a987f33889201034d86407c4efe78a8a9f05fe4ba5e42298ce4237b3ebe0e` |
| [g3a_readjudicated.json](../../results/SMOKE/phase-G2/g3a_readjudicated.json) | `351049ee17185cd2ac6909767316821b8efa9713a572716122655b1767b59757` |

G5c source/prereg/protected hashes nằm trong artifact G5c. G6 ghi hash
của công thức và topology cùng hashes G5b/G5c. Doc 75 ghi hashes CSV/PNG/log.
Không sửa prereg sau tag để chèn commit tự tham chiếu.
