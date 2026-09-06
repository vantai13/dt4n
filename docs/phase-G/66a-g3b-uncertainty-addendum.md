# G3b — phụ lục bất định và G-L107

Phân tích hậu nghiệm; doc 66 và toàn bộ phán quyết đã ký giữ nguyên.
64 ước lượng ở lưới 2×2 được tính lại từ NPZ bởi g4_nugget_model; đối chiếu JSON ở rtol=atol=1e-12.

## Hồi quy có hiệu ứng cố định theo link

log(tau_hat/tau) = intercept + beta_sigma*log(sigma_ref/.028) + beta_tau*log(tau/2) + 7 dummy link.
beta_sigma = -0.0160297; n=64, rank=10.

| Phương pháp CI95 | Cận dưới | Cận trên | Cận độ trôi log | Cận thay đổi exp(bound)−1 |
|---|---:|---:|---:|---:|
| ols | -0.157537 | 0.125478 | 7.474% | 7.761% |
| hc3 | -0.170084 | 0.138024 | 8.070% | 8.404% |
| cluster_link | -0.285216 | 0.253157 | 13.532% | 14.491% |
| cluster_run | -0.184490 | 0.152431 | 8.753% | 9.148% |

OLS giả định sai số độc lập, đồng phương sai; HC3 cho phép phương sai khác nhau. CR1 theo link hoặc lượt là kiểm tra độ nhạy với phụ thuộc trong nhóm, dùng t(7). Chỉ có 8 nhóm nên các CI này là xấp xỉ; fixed effects không tự loại bỏ phụ thuộc. Không chọn CI hẹp nhất làm kết luận chắc chắn.
Các cận độ trôi là cho hiệu ứng trung bình trong mô hình log tuyến tính trên dải đã quét, không chặn mọi link hoặc mọi đường cong phi tuyến.

Tham khảo công thức CR1 và hiệu chỉnh mẫu nhỏ: [statsmodels](https://www.statsmodels.org/v0.13.5/generated/statsmodels.stats.sandwich_covariance.cov_cluster.html); lượng vị t: [SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html).

## Bootstrap đúng thống kê đã ký

20000 lần, seed 20260906, resample 8 link cùng danh tính qua bốn ô; giữ cả hai lượt mỗi link. Đây là bootstrap theo link, có điều kiện trên các lượt đã có, không chứng minh độc lập giữa các link qua kernel dùng chung.
| Thống kê | CI95 percentile | SD | P(pass khi slope=0), xấp xỉ chuẩn |
|---|---|---:|---:|
| RT-O1 | [-0.24129, 0.18402] | 0.10257 | 0.670 |
| RT-O2 | [-0.01567, 0.03761] | 0.01364 | 1.000 |

**G-L107:** PASS của ước lượng điểm không thiết lập tương đương trong biên đã ký. Gate độ dốc cần kèm CI và tính trước xác suất PASS dưới mô hình đúng. Độ trôi trên dải đo liên hệ với ngân sách claim, nhưng chuyển sang đại lượng đó sau khi xem dữ liệu là phân tích bổ sung, không phải gate tiền đăng ký mới.

## Các điểm cần sửa trong nhận xét được cung cấp

- Code G3b lấy trung vị gộp 16 giá trị link/lượt, không phải trung vị-của-trung-vị. Phụ lục bootstrap đúng code đã ký.
- Nếu SD=.11, P(|N(0,.11)|<=.1)=0.6367; với slope thật .20, xác suất là 0.1785, không phải ~50%.
- 4.8e-5 là khoảng 48 ppm, không phải 5 ppm.
- Khoảng [0.948,0.993] không chứa tỉ số 1; việc hai CI chồng nhau không phải kiểm định hiệu giữa hai ô. Không thể kết luận bác bỏ clipping chỉ từ thứ hạng vài link.
- Cận 0.0732 trên thang log tương ứng exp(0.0732)-1 khoảng 7.59%, không phải cận chính xác 7.32%.

Outlier giữ nguyên: tau=5, sigma=.045, rep=0, vC: sf=0.999791144, v gián tiếp=4.43745088e-07. Hệ số chặn gần 1 là dấu hiệu bất ổn ngoại suy; riêng con số này chưa chứng minh cơ chế bão hòa vật lý hay clipping của code.
Sai số tau từng link/lượt quan sát được: [-22.99%, +31.16%]. Gate trung vị không bảo đảm từng link đáp ứng claim B.

## Bằng chứng

- [JSON phân tích](../../results/SMOKE/phase-G2/g3b_orthogonality_audit.json)
- SHA256 JSON: `0947ecd886ac62c488a71c52bda22434761dc6ea562c0d359eb4fd52d0e667ca`
- SHA256 model nguồn: `e5285b4319afe4b51a55b876630c009b16f5bb720a5dd58564d6d747477c9a9e`
