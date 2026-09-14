# 20R2.9-B — bổ sung sổ giới hạn

Ngày 2026-09-14. Đọc cùng [B0 đã ký](B0-reading-signed.md). Phụ lục này bổ sung [sổ G1–G8](99-gate-decision.md); giữ nguyên byte và phán quyết đã đóng. Bước đóng-v2 chưa thực hiện.

## G1 — lượng hóa độ nhạy có điều kiện; tải chung thực vẫn chưa đo

[S1](B1-omega-sensitivity.json) có 64 hàng theo ô × τ tại z=.365 và ω=.10. Cặp đường thắng nhiều nhất/thứ hai được đo riêng mỗi ô trên ba seed: P1–P3 ổn định 3/3; V(1)=1.7071067811865475 lấy theo đúng cặp.

| Ô | Ratio min–max qua 8 τ | Số τ nhạy / 8 |
|---|---:|---:|
| h2@0.700 | 1.001586–1.001752 | 0/8 |
| h2@0.850 | 1.008001–1.008834 | 0/8 |
| h2@0.925 | 1.061817–1.067967 | 0/8 |
| h2@0.960 | 1.376625–1.406127 | 8/8 |
| poisson@0.700 | 1.003788–1.004184 | 0/8 |
| poisson@0.850 | 1.000050–1.000055 | 0/8 |
| poisson@0.925 | 1.000759–1.000838 | 0/8 |
| poisson@0.960 | 1.008541–1.009430 | 0/8 |

SNR*=2.575323556 tại τ=3; từng τ có ngưỡng và khoảng cách riêng. Không hàng nào trong vùng biên ±10%. Đây là độ nhạy của mô hình Gaussian hai đường, giữ r/cặp đường/hình dạng margin và kế thừa SNR ở τ=3. Chưa chứng minh là cận cho pipeline bốn đường hoặc SNR bất biến theo τ.

ω=.10 là kịch bản đã cố định. CI cũ của Lesson 23.25 tự ghi độ rộng bị đánh giá thiếu; closeout phân biệt noise floor với tương quan thực. Không dùng CI đó để chứng nhận .10 là cận bảo thủ. G1 được lượng hóa một phần, **không đóng nợ đo tải chung 21R2**.

## G2/G3/G4 — giữ phạm vi, bổ sung bản đồ

T2-R7 vẫn áp dụng cho **cả h2@0.960 và poisson@0.960**. Không gọi bảy ô còn lại “vững qua bốn phép kiểm độc lập”; tính độc lập chưa được chứng minh, các giới hạn tựa-tĩnh/ước lượng còn phạm vi riêng. Phán quyết 5/8 có mẫu số τ, không phải tám ô. Không gộp err hoặc tỷ số tám ô làm headline.

[S2](B2-sla-threshold-map.json) và [PDF](B2-sla-threshold-maps.pdf) mô tả 108 ngưỡng, a=.9, giữ w_loss=5000 và quyết định đường. Phân biệt truth=0, truth=1 và nội miền/hỗn hợp seed; giữ min/max hiệu ứng qua seed. Nonzero quan sát chưa phải ý nghĩa thống kê. Không đổi điểm vận hành (50ms,1%) theo bản đồ.

## RQ-20R2e — kỳ vọng theo tuổi cơ sở

[S3](B3-axis-marginal.json) dùng chính hai generator tuổi vô hướng, một triệu bước tại dt=.005. Trung bình tuổi legacy=.3025s, measured=.3660396s; không phải tái mô phỏng AoI nhiều link. 1.280 hàng shared-z được kiểm trước gộp seed, max|diff|=0. Mọi mass_outside=0.

Sai số đồng nhất mean_shift×shape tối đa 2.22e-16 ở các hàng mean seed, 4.44e-16 ở seed có mẫu số dương. Đây là đại số, không xác định nhân quả hình dạng độc lập khỏi dịch tuổi; không nhân các trung vị riêng để khẳng định đồng nhất.

Một số Jensen gap ở h2@0.960 **dương**. Dấu gap không chứng minh lồi/lõm toàn miền. Tại h2@0.960, τ=20, seed103, err(E_Z)=0 nên tỷ số Jensen/phân rã seed không xác định; giữ null và seed đó. Kỳ vọng tuyệt đối vẫn đọc được. Max tuyệt đối của trung bình tỷ số Jensen qua năm seed, trong các hàng xác định, trục measured là 3.3021% tại h2@0.925, τ=.5; không dùng cực đại này làm đại diện tám ô.

## INV-01 — Q1′, Q2′, Q3′, vẫn mở

[Truy vết](B-validation/INV01-floating-point-trace.json) ghi n=499967 ở mỗi ô. Trên input hiện tại poisson@0.925, np.mean cho regret=1.7674606558720711; math.fsum/n và cộng tuần tự cho 1.767460655872071, khớp số công bố. [Đổi riêng phép cộng](B-validation/INV01-reduction-propagation.json), rồi chạy tiếp công thức gốc, tái lập **8/8 trường lệch**. Đây là lời giải thích số học đủ khả năng gây drift, chưa xác định cách cộng lịch sử.

Sai lệch penalty=1.7763568394002505e-15 là **2 ULP tại ~7.947**; regret lệch 1 ULP. Với u=eps/2, gamma_k=k*u/(1−k*u), cận mean có điều kiện là (gamma_k+u*(1+gamma_k))*Σ|x|/n. k=n−1 cho cộng tuần tự; ceil(log2 n) cho cây cân bằng. Tại regret poisson@0.925: 9.81073e-11 và 3.92455e-15. Artifact còn truyền cận riêng nhánh regret qua penalty/normpen khi giữ err/median cố định. sqrt(n)*eps không phải cận pairwise tất định tổng quát.

Chưa thiết lập cây giảm của NumPy lịch sử; hash raw poisson@0.925 khác lịch sử theo L85. Chưa đủ cơ sở chọn dung sai toàn test hoặc đóng điều tra input. Giữ nguyên test/số công bố. RNG/action identity trong môi trường ghim, S2 default/điểm ngưỡng đồng nhất, S3 shared-z và digest đóng băng vẫn giữ sai số 0. Bảy parquet thiếu digest lịch sử còn mở, không thêm miễn trừ.

## Năm câu tự kiểm

1. Với bảng này, đổi riêng ngưỡng sang 1.10 vẫn chỉ h2@0.960 có hàng nhạy, 8/8 τ. Ngưỡng chính vẫn 1.25 đã ký, không chọn lại theo kết quả.
2. Var(X−Y)=Var(X)+Var(Y)−2Cov(X,Y): phần cùng biến thiên bị triệt khi lấy hiệu. Tra V(1) theo đúng cặp và mô hình covariance; không suy mọi trường hợp chỉ từ số link chia sẻ.
3. Gap dương nghĩa E[err(Z)]>err(E[Z]) với phân phối này. Kiểm khóa seed/z, nội suy và mẫu số; một gap không chứng minh độ cong toàn cục.
4. Lưới phân vị từng ô đổi thước đo bằng phân phối đang đánh giá, tái tạo cơ chế tự hiệu chuẩn S14. Lưới chung đã ký chấp nhận miền bão hòa.
5. n=1120000, bốn đường: một mảng bool 4480000 byte (~4.27 MiB); 108 mảng 483840000 byte (~461.43 MiB). Vòng ngưỡng ngoài giữ một mảng vi phạm, ngoài bộ nhớ chuỗi thật/twin khác. RSS toàn worker được đo riêng.
