# 66 — State of Lesson 23.25 tại Phase D′

Trang này phân loại con số của Lesson 23.25 theo bằng chứng mới nhất ở commit
`481cace`. Các trang closeout 61–65 vẫn là nguồn chi tiết; bảng dưới là chỉ
mục trạng thái ngắn.

| Đại lượng | Giá trị | Trạng thái | Cách được phép dùng |
|---|---:|---|---|
| `sum(k^2)` trên 12 cặp không thứ tự có cấu trúc | 5.0000 | SỐNG | wiring đại số topology |
| T17 target-cov sensitivity | median +2.09%, worst +17.06% | SỐNG CÓ ĐIỀU KIỆN | bound trên pilot SNR; không xác nhận magnitude SNR |
| `r(uA,uB)` measured | +0.5986 | SỐNG CÓ ĐIỀU KIỆN | shared-endpoint confound; không phải path coupling |
| `r(vC,vD)` measured | +0.6376 | SỐNG CÓ ĐIỀU KIỆN | shared-endpoint confound; không phải path coupling |
| `r(ac,ad)`, `r(bc,bd)` measured | +0.0358, +0.0314 | SỐNG | đối chứng endpoint lõi gần 0 |
| `omega_hat=+0.0852` và các bản corrected/deattenuated cũ | — | CHẾT | không nhận dạng được; cấm trích magnitude |
| `Var(m)=0.54–0.71` T5 cũ | — | CHẾT | sai tầng đơn vị; dùng T5b 0.88–0.96 |
| `err=0.0519` từ `tau_system=27.67 s` | — | CHẾT | thay bằng ACF margin đo trực tiếp, 0.1566–0.1758 |
| “~900 socket/namespace” | — | CHẾT | code không có cơ chế này; 817–875 là luồng ảo warm-start |
| mọi điểm dùng `sigma,tau` như hai trục độc lập của flow generator cũ | — | ĐIỀU KIỆN | regression control, không chứng minh realizability hai trục |

## Bằng chứng cơ chế socket/luồng ảo

`mininet/flow_engine.py` có một sender socket trong mỗi `FlowEngine` process
và một receiver socket trong `udp_sink`; sender gộp tất cả luồng ảo trong
`heapq` thành `rate_sum_bps`. Không có một socket cho mỗi virtual flow.

## Bằng chứng sampling mới nhất

Không dùng `tau_pred_s` để thay ACF của đại lượng đang phân tích. T8 Bartlett
trên chính `rho_measured` cho `n_eff` theo cặp từ khoảng 660 đến 1785 và làm
lộ model misspecification qua `chi2/dof`, thay vì xác nhận diễn giải thiếu mẫu
từ time scale dự đoán. Xem `59-identifiability-audit.md` và artifact
`results/LIVE/phase-23/link_corr_matrix.json::T8_identifiability`.
