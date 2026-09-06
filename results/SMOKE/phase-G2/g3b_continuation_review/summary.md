# Tổng kết kiểm tra tiếp nối G′.3b

**Kết quả: GO — xác nhận lại từ dữ liệu đo đã có.**

Bạn đã hoàn tất vá estimator, bias-sim, ký prereg, dry-run, đo mạng đủ 5 ô/9 lượt và teardown. Báo cáo doc 66, CSV và biểu đồ đã có trước lượt kiểm tra này.
Đợt đo: 2026-09-06T03:51:09.883762+00:00 đến 2026-09-06T07:09:25.180901+00:00 (UTC); thời lượng đo danh định 11890 giây (~3 giờ 18 phút).

Phần thực hiện tiếp trong lượt này:

- Kiểm tra 46/46 SHA256 khớp manifest cũ; code đã ký còn nguyên và commit prereg có trước lượt đo.
- Tính lại 72 ước lượng link/lượt từ chuỗi NPZ: τ̂, σ̂, sf và trung vị khớp JSON (rtol=atol=1e-12).
- Đối chiếu 9 cặp chuỗi measured/target ở checkpoint: bằng nhau chính xác với NPZ tổng.
- Tính lại gate và trực giao: khớp GO đã lưu; toàn bộ 11 gate số học PASS.
- Chạy lại kiểm thử estimator/harness: 7 passed in 1.91s.
- Log mạng ghi exit code 0, teardown hoàn tất. Lượt này không chạy lại mạng, không đổi ngưỡng hoặc code.

| τ đặt (s) | σ_ref | τ̂ (s) | Sai số τ | σ̂/σ | Sai số σ |
|---:|---:|---:|---:|---:|---:|
| 2 | 0.028 | 1.984606 | -0.770% | 1.003095 | +0.310% |
| 2 | 0.045 | 1.901177 | -4.941% | 0.961815 | -3.819% |
| 5 | 0.028 | 4.958147 | -0.837% | 1.004533 | +0.453% |
| 5 | 0.045 | 4.944392 | -1.112% | 0.984901 | -1.510% |
| 30 | 0.036 | 28.972070 | -3.426% | 1.023714 | +2.371% |

RT-O1 = 0.048187 ≤ 0.10; RT-O2 = 0.013724 ≤ 0.05.

Các file kết quả:

- [Kiểm tra tiếp nối JSON](verification.json)
- [Báo cáo đầy đủ](../../../../docs/phase-G/66-g3b-results.md)
- [Số liệu đo và gate JSON](../g3b_sigma_tau.json)
- [Bảng round-trip CSV](../g3b_roundtrip.csv)
- [Từng link/lượt CSV](../g3b_per_link.csv)
- [Chuỗi thô NPZ](../g3b_sigma_tau_series.npz)
- [Log chạy mạng](../g3b_logs/network_run.log)
- [Log hạ tầng JSONL](../g3b_infra.jsonl)

![Sai số τ và σ](../g3b_roundtrip.png)

GO áp dụng cho protocol G3b đã ký, các ô đã đo và đường kernel veth/HTB trên host này. Kết quả chưa chứng nhận NIC vật lý/Internet, toàn miền σ/τ hoặc protocol trung vị 3 replicate sau hiệu chỉnh của doc 55. Trực giao được đánh giá bằng thống kê trung bình đã ký ở lưới 2×2; τ=30 chỉ có một mức σ.

G′.3b đã hoàn tất. Bước kế tiếp trong lộ trình là G′.4 (thu nhỏ); tài liệu được cung cấp chưa có protocol triển khai G′.4.
