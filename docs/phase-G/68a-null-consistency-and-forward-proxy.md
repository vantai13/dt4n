# G4 — phụ lục null và proxy cho thiết kế tương lai

Giữ nguyên certificate v2 và mọi kết quả đã ký. Bản v2.1 bổ sung kiểm tra null hậu nghiệm, không đổi hệ số nugget hoặc phạm vi vật lý.

| Ô | n gộp | SD dưới null | max quan sát | max/SD | E[max] tham khảo, 28 chuẩn độc lập |
|---|---:|---:|---:|---:|---:|
| t2_s0.028 | 8200 | 0.013525 | 0.032004 | 2.366 | 0.031065 |
| t2_s0.045 | 8200 | 0.013525 | 0.022590 | 1.670 | 0.031065 |
| t5_s0.028 | 20500 | 0.008554 | 0.025599 | 2.993 | 0.019647 |
| t5_s0.045 | 20500 | 0.008554 | 0.016769 | 1.960 | 0.019647 |
| t30_s0.036 | 61500 | 0.004939 | 0.012642 | 2.560 | 0.011343 |
| g2_run3 | 16400 | 0.009564 | 0.022681 | 2.372 | 0.021966 |

364 phép so sánh từng lượt: max|z|=3.31525, cận Bonferroni .05=3.81287, min p hiệu chỉnh=0.33328; NO_EVIDENCE_AGAINST_NULL_AT_FWER_0.05.
168 phép so sánh gộp: min p hiệu chỉnh=0.46458; NO_EVIDENCE_AGAINST_NULL_AT_FWER_0.05.
Var(r)≈(1+2*.5²)/n là xấp xỉ Bartlett cho hai MA1 độc lập. Bonferroni không cần độc lập giữa các cặp, nhưng p-value vẫn dựa trên xấp xỉ chuẩn.

**Sửa nhận xét được cung cấp:** E[max] không phải ngưỡng kiểm định; một số ô vượt E[max] và điều đó có thể hoàn toàn bình thường. max/SD cũng tăng theo số phép thử. Các lượt có n khác nhau phải chuẩn hóa riêng, không chia tất cả cho SD tại n=4100.
Không bác bỏ null không chứng minh rho_eps=0. NC-3 trong G5 cũng không tách riêng một nguyên nhân phụ thuộc.

## Kappa và giới hạn G-L108

Kappa G3b=2.004501; G2=2.021731. IQR trên các link/ô không phải SE trên các lượt độc lập. Chưa khẳng định chênh lệch là hệ thống ở mức 4.9 SE từ phép tính trong nhận xét.
G-L108: mô hình gần κ_nugget=2, lệch mô tả khoảng 1% theo bộ dữ liệu. Thay hệ số bằng trung vị thực nghiệm làm sf đổi tối đa 0.0008102 ở các ô kiểm; không hiệu chỉnh mô hình. Vi phân đúng là d(sf)=-sf*(1-sf)*dκ/κ, không bỏ thừa số sf.

## Proxy Q-1 cho thiết kế tương lai

Hệ số mới sqrt(2*.8264/(1-.8264))=3.085569206; giữ sai số claim C=.10. Đây là thay thế proxy sf=.95 bằng sf=.8264 đã dùng, không hồi tố và không chứng nhận vận hành sigma thấp chưa đo.
| dt | sigma_ref min cũ | sigma_ref min mô hình mới |
|---:|---:|---:|
| 0.1 | 0.0256671 | 0.0181646 |
| 0.15 | 0.0171114 | 0.0121097 |
| 0.2 | 0.0128335 | 0.0090823 |
| 0.25 | 0.0102668 | 0.0072658 |

Vẫn phải xét clipping, T/tau, dt/tau, hiệu quả mẫu, timing, burst và hạ tầng. Việc raw max=.05867<.10 chỉ làm proxy pair-bias dùng raw max không binding; không chứng minh mọi bias omega hoặc mọi cấu hình đều đạt.
G4 chỉ kiểm omega=0 trong cả hai bộ dữ liệu. Sai số phục hồi omega .0271 của G3a không phải giới hạn thay đổi coverage.

[Certificate v2.1](../../results/LIVE/phase-G2/measurement_path_cert_v2_1.json) — SHA256 `57732bc3d5eb742d35eda1eb104c2627fc1f32b6de61adb89d3aa90d1ef2341c`
[JSON đầy đủ](../../results/SMOKE/phase-G2/g5_rho_eps_null.json) — SHA256 `11337d8f8f3d12e7af17f8551a8ab682362874e0f2ebaf5a334056b01d928778`
