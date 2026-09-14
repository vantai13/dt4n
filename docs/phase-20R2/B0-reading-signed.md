# 20R2.9-B — cách đọc cố định trước lần chạy tái lập

Ngày 2026-09-14, baseline `1de19e1c`. Tag `phase-20R2-B-reading-signed` phải được commit và push trước lần chạy S1/S2/S3 của đợt này. Người dùng đã cung cấp kết quả mẫu; đây là tái lập/thăm dò có luật đọc cố định, không phải đăng ký mù trước khi bất kỳ ai thấy kết quả. Mọi thay đổi sau lần chạy cần amendment có tên. Bước đóng-v2 chưa thuộc phạm vi.

## S1 — độ nhạy ω theo ô và τ

Giữ `omega_ref=0.10`, `sensitive_ratio=1.25` (quy ước tăng trên 25%), `z=0.365` từ prediction đã ký, `omega_grid=(0,.05,.10,.25,.50,1)`. Các ngưỡng này được người dùng ấn định và không đổi theo kết quả. Tỷ số 1.25 không bảo đảm một kết luận có hướng sẽ đảo hay không đảo.

Đính chính lý do ω: `link_corr_matrix.json/T4_block_bootstrap` có CI [-.03137,.04747] nhưng tự ghi `ci_is_lower_bound_on_width=true`; T7 nói bootstrap lệch vị trí và rộng thiếu, T11/closeout phân biệt noise-floor với tương quan mạng thực. Vì vậy .10 chỉ là kịch bản cố định (xấp xỉ hai lần đầu trên CI cũ), **không gọi là cận bảo thủ được CI hợp lệ bảo đảm**. .25/.50/1 là các kịch bản bổ sung; ω=1 là cực trị mô hình.

Suy cặp đường thắng nhiều nhất/thứ hai từ bảng chi phí thật trên từng ô, τ=3, n=200000, a=.9, seeds101–103; ghi cặp từng seed, thị phần và độ ổn định. Không gọi đây là cặp hạng nhất/thứ hai tại mọi thời điểm. Lấy V(1) theo đúng cặp trong T5_var_margin. SNR0 dùng margin_structure/m_mean của 06b-per-cell và kiểm lại bằng cùng phép tính; không suy từ err.

Mô hình: r=exp(-z/τ); s(ω)=|SNR0|/sqrt(1+ω(V1−1)); err=1−Φ₂(−s,−s;r)−Φ₂(s,s;r). Tính bằng tích phân tất định tương đương để tránh nhiễu số của CDF. Đây là **ước lượng độ nhạy có điều kiện theo mô hình hai đường Gaussian**, chưa được chứng minh là cận trên/dưới cho pipeline bốn đường. Bỏ qua thay đổi hình dạng margin, r và cặp đường khi ω đổi; kế thừa SNR ở τ=3 không chứng minh SNR bất biến trên mọi τ.

R-S1-1: 64 hàng = 8 ô × 8 τ, không gộp err/tỷ số trên tám ô. R-S1-2: nhãn theo (ô,τ), báo n_sensitive/n_tau từng ô. R-S1-3: chấp nhận không ô nhạy; không hạ ngưỡng. R-S1-4: mọi trích dẫn giữ giới hạn mô hình nói trên. R-S1-5: giải SNR* sao cho ratio=1.25 cho từng τ và cặp V1; báo khoảng cách tương đối. Nếu |SNR/SNR*−1|≤.10 thì UNREADABLE. Cặp không ổn định/thiếu hai đường hoặc SNR không hữu hạn cũng UNREADABLE, không lặng lẽ bỏ hàng. T2-R7 áp dụng cho cả hai ô rho=.960.

## S2 — bản đồ SLA theo ngưỡng

Estimand mới `SLA_VIOL_BY_AGE_BY_THRESHOLD`, LEVEL all_action, UNIT dimensionless [-1,1], BRANCH z_fixed. Quần thể: 8 ô gate ×8 τ ×5 seed101–105 ×13 z của nhánh main ×108 ngưỡng, **a=.9**, n của từng τ lấy nguyên kế hoạch chiến dịch đã ký. Giữ nguyên w_loss=5000 và quyết định đường, chỉ đổi cách chấm vi phạm.

T_delay_ms=(14,18,22,26,30,35,40,45,50).
T_loss=(.00002,.00005,.0001,.0005,.002,.005,.01,.02,.05,.10,.15,.20).

Lưới chung cố định trải nhiều thang độ lớn; không phải lưới đều log chính xác. Miền phủ được chọn từ pilot đã có trong hướng dẫn, nên công khai có thông tin dữ liệu; không hiệu chỉnh theo phân vị từng ô và không thay ngưỡng vận hành (50ms,1%).

R-S2-1: run_cell(sla_grid=None) phải trùng mọi trường/giá trị với source trước vá; truyền grid chỉ thêm sla_grid. Giữ thứ tự RNG và cửa sổ chấm. R-S2-2: tại (50,.01), mọi z/ô/τ/seed phải bằng d_sla cũ với sai số 0; trượt thì dừng. So thêm mọi per_z với parquet chiến dịch gốc bằng cùng khóa. R-S2-3: mỗi hàng có viol_rate_truth và viol_rate_twin. R-S2-4: bản đồ theo ô và τ, không một số pooled-eight; trung bình 5 seed có ghi n_seed. Vùng truth=0, truth=1, truth trong(0,1) phân biệt; d_sla=0 trong vùng không suy biến không tự có nghĩa không có hiệu ứng. Ghi zero/nonzero quan sát được và min/max qua seed; không gọi nonzero là có ý nghĩa thống kê. R-S2-5: không thay chuẩn vận hành theo bản đồ.

108×13=1404 hàng/call; 320 call =449280 hàng. Tính từng ngưỡng để không giữ 108 mảng bool(n,4). Chạy tuần tự và đo thời gian/RSS; kế hoạch bổ sung thuần hàm, tag `phase-20R2-B2-plan-signed` push trước chiến dịch. Tái dùng runner 20r2_5_run cho fsync, fingerprint và nguyên tắc log là nguồn sự thật; ghi start/completion, kiểm hash khi resume, cách ly file mồ côi, từ chối nguồn/kế hoạch/môi trường đổi. Giữ 108 ngưỡng; khoảng 68 phút trong hướng dẫn chỉ là ước tính, báo thời gian thật.

## S3 — DECISION_ERR_BY_AXIS

E_{Z~axis}[err_total(Z)], UNIT dimensionless, BRANCH axis_marginal; 8 ô×8τ, a=.9. Sinh tuổi bằng chính sawtooth_age_steps và AoIModelV7.base_age_steps tại dt=.005, N_AGE=1000000; không thay bằng uniform liên tục. Phạm vi là phân phối tuổi cơ sở vô hướng, không mô phỏng lại toàn bộ AoI nhiều link.

Gộp mẫu err(z) main/control_legacy theo khóa ô,τ,a,seed,z. **Kiểm từng seed trước khi lấy trung bình**: tại z chung đòi float lưu trong parquet trùng tuyệt đối; báo max|diff| và số hàng. Không gọi giá trị 5.55e-17 sau gộp là bit-exact. Nếu số lưu khác nhau thì dừng để điều tra, không tự tăng dung sai. Nội suy tuyến tính theo z danh định đã lưu (độ lượng tử nằm trong nguồn); gộp trùng z một lần.

R-S3-1: báo cả E_err, err_at_E_Z, Jensen gap tuyệt đối/tương đối cho từng trục, ô,τ (cùng dữ liệu từng seed). Gap âm/dương chỉ là quan hệ Jensen cho phân phối này, **không chứng minh lồi/lõm toàn miền**; E[Z] là trung bình, không phải trung vị. R-S3-2: đếm khối lượng ngoài [min z,max z], không ngoại suy. Nếu >1% hoặc E[Z] ngoài miền: UNREADABLE. Nếu phần ngoài>0 nhưng≤1%, ghi tích phân phần trong và cận [partial,partial+mass_out] vì err∈[0,1]; không trình bày kỳ vọng đầy đủ như đã biết. R-S3-3: khi mass_out=0 và mẫu số>0, phân rã mean_shift=err(EZmea)/err(EZleg) và shape=(Eerr/err(EZ))mea/(...)leg; kiểm tích bằng tổng với atol=1e-12. Đây là phân rã đại số, không phải chứng minh nhân quả hình dạng độc lập khỏi dịch trung bình; không nhân các trung vị riêng rồi gọi là đồng nhất. R-S3-4: không đổi phán quyết 5/8. Kết quả chính theo từng ô/τ, không dùng số gộp làm headline.

## Nguồn và kiểm thử

Cả ba kết quả có validity tại nguồn, inputs_sha256, hash mã nguồn và mốc ký. Nguồn đóng băng trước B giữ nguyên. B0 là tài liệu khai cách đọc nên không có trục kết quả. Kết quả B ở docs/phase-20R2/B*.json và bảng/receipt dưới B-validation; raw S2 ở results/PENDING/phase-20R2-B/S2 có validity đúng vai trò, không gắn nhãn SLA vận hành được duyệt cho cả 108 ngưỡng.

INV-01 tiếp tục MỞ, thêm Q1′ chuỗi phép tính, Q2′ cận sai số có cơ sở, Q3′ phép kiểm cần zero tolerance. 1.776e-15=8eps tại 1 không đồng nghĩa “8 ULP tại mọi giá trị” và không đủ loại trừ thay đổi input. Cận cộng tuần tự gamma_(n−1)Σ|x|, cận pairwise gamma_ceil(log2 n)Σ|x| khi đúng thuật toán; sqrt(n)eps không phải cận pairwise tổng quát. Chưa đổi tolerance test chỉ từ sai số quan sát.

Không diễn giải 5/8 như 5/8 ô: phán quyết có mẫu số τ. Không tuyên bố “7 ô vững theo bốn kiểm tra độc lập” chỉ từ hội tụ các chẩn đoán; tựa-tĩnh và T2-R7 còn hạn chế ở ô khác. Cập nhật G1 bằng phụ lục bổ sung, không sửa gate decision đã đóng.
