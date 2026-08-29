# 66 — State of Lesson 23.25 tại Phase D′

Trang này phân loại con số của Lesson 23.25 theo bằng chứng mới nhất ở commit
`50f80cf` cộng audit factorial D′. Các trang closeout 61–65 vẫn là nguồn chi tiết; bảng dưới là chỉ
mục trạng thái ngắn.

| Đại lượng | Giá trị | Trạng thái | `n_eff`/sampling | Cách được phép dùng |
|---|---:|---|---|---|
| `sum(k^2)` trên 12 cặp không thứ tự có cấu trúc | 5.0000 | SỐNG | — | wiring đại số topology |
| T17 target-cov sensitivity | median +2.09%, worst +17.06% | SỐNG CÓ ĐIỀU KIỆN | theo pilot artifact | bound trên pilot SNR; không xác nhận magnitude SNR |
| `r(uA,uB)` measured | +0.5986 | SỐNG CÓ ĐIỀU KIỆN | run cũ 120 s; `<5*tau_pred(uB)` nhưng T8 measured-ACF cho n_eff lớn | hiện tượng endpoint × bundle candidate; không phải path coupling |
| `r(vC,vD)` measured | +0.6376 | SỐNG CÓ ĐIỀU KIỆN | cùng giới hạn run cũ | đối xứng với uA-uB; chờ cell C |
| 4 cặp cả hai low-σ, không chung host | mean +0.0364 | SỐNG HẬU KIỂM | cùng lớp duration/σ/τ cũ | đối chứng âm mô tả cho H2/H3 |
| 4 cặp chung host, cả hai `N_bar` nhỏ | mean +0.0171 | SỐNG HẬU KIỂM | core tau_pred 2.7–4.3 s | đối chứng âm bác H1 thuần; ac-ad/bc-bd cũng chung host |
| H4 endpoint × low-σ/high-`N_bar` bundle | ratio ô = 9.893× | ỨNG VIÊN | chưa có run xác nhận | chỉ được gọi giả thuyết cho tới cell C |
| `omega_hat=+0.0852` và các bản corrected/deattenuated cũ | — | CHẾT | — | không nhận dạng được; cấm trích magnitude |
| `Var(m)=0.54–0.71` T5 cũ | — | CHẾT | — | sai tầng đơn vị; dùng T5b 0.88–0.96 |
| `err=0.0519` từ `tau_system=27.67 s` | — | CHẾT | — | thay bằng ACF margin đo trực tiếp, 0.1566–0.1758 |
| “~900 socket/namespace” | — | CHẾT | — | code không có cơ chế này; 817–875 là luồng ảo warm-start |
| mọi điểm dùng `sigma,tau` như hai trục độc lập của flow generator cũ | — | ĐIỀU KIỆN | phụ thuộc estimator | regression control, không chứng minh realizability hai trục |

## Bằng chứng cơ chế socket/luồng ảo

`mininet/flow_engine.py` có một sender socket trong mỗi `FlowEngine` process
và một receiver socket trong `udp_sink`; sender gộp tất cả luồng ảo trong
`heapq` thành `rate_sum_bps`. Không có một socket cho mỗi virtual flow.

## Bằng chứng sampling mới nhất

Không dùng `tau_pred_s` để thay ACF của đại lượng đang phân tích. T8 Bartlett
trên chính `rho_measured` cho `n_eff` theo cặp từ khoảng 660 đến 1785 và làm
lộ model misspecification qua `chi2/dof`. Tuy nhiên quy tắc burn-in theo
`tau_pred` lại cho `5*tau_pred(uB)>120 s`; hai định nghĩa time scale không
được tráo cho nhau. Factorial audit dùng các cặp cùng lớp low-σ nhưng khác
host làm discriminator hậu kiểm mạnh hơn. Xem `59-identifiability-audit.md` và artifact
`results/LIVE/phase-23/link_corr_matrix.json::T8_identifiability`.
