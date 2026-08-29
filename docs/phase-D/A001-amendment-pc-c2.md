# Amendment D-A001 — PC-C2 sai thiết kế và preregistration PC-C2′

```text
Ngày ký                  2026-08-29
Trạng thái               SIGNED_BEFORE_REANALYSIS
Tag khóa                 phase-D-pc-c2-prime-start
Dữ liệu                  tái sử dụng Cell A và Cell C; 0 giây Mininet
Giữ nguyên               phán quyết Cell C INVALID_RUN trong 03-gate-decision.md
```

Amendment này không sửa hoặc ghi đè preregistration/tag
`phase-D-cellC-start`. Nó tạo một lớp phân tích lại độc lập sau khi kiểm toán
chính control PC-C2.

## 1. Điều đã biết trước khi ký

PC-C2 cũ đòi tau edge giảm ít nhất 5× khi `sigma_edge: 0.03 -> 0.10`, nhưng
đã lấy cả tử và mẫu từ integral ACF của `rho_measured` ở cửa sổ 0.2 s.
Artifact Cell C đã được xem và trả:

```text
reduction ratio uA/uB/vC/vD = 1.119 / 1.546 / 0.922 / 1.077
PC-C2 = FAIL; Cell C = INVALID_RUN
```

Các số đã có độc lập cho Cell A (`sigma_edge=0.03`) không đồng nhất:

| Nguồn | uA | uB | vC | vD |
|---|---:|---:|---:|---:|
| `tau_by_link_from_meta` | 20.03 | 27.35 | 20.03 | 27.67 |
| offered 10 ms, 240 s | 15.09 | 21.86 | 19.81 | 12.58 |
| baseline PC-C2 cũ, measured 0.2 s | 2.07 | 3.01 | 2.44 | 2.55 |

`acf_nugget.json` đã tồn tại trước Cell C và đo:

```text
median edge signal fraction = 0.3695699846
min all signal fraction      = 0.3056253651
all fits valid               = false (core fits invalid)
branch                       = DEFAULT_MIXED_OR_INVALID
```

Bốn edge fit riêng đều hợp lệ, signal fraction `0.306–0.494`. PC-C1 của Cell
C lại khớp trực tiếp 4/4 edge:
`warm_start_active = round(rho_target^2/sigma_target^2)`.

## 2. Vì sao PC-C2 cũ sai loại đại lượng

Với `rho_measured = rho_true + epsilon`, epsilon trắng theo thời gian và có
phương sai nugget, ở lag dương:

```text
ACF_measured(k) = signal_fraction * ACF_true(k)
signal_fraction(sigma) = sigma^2 / (sigma^2 + v_nugget)
tau_true(sigma) = k / sigma^2
```

Vì vậy estimator integral không tách intercept nugget có xấp xỉ:

```text
tau_hat_measured ~= signal_fraction * tau_true
                 = k / (sigma^2 + v_nugget)
```

Khi nugget chi phối, sigma² bị triệt tiêu khỏi độ nhạy của estimator. Do đó
ratio khoảng 1.1× không chứng minh sigma không vào engine; nó cho thấy control
phía generator đã bị đánh giá trên đại lượng phía counter.

Lỗi thứ hai: analyzer cũ giới hạn ACF tại `n//10`. Với T=120 s, dt=0.2 s,
trần tìm kiếm chỉ 12 s, ngắn hơn tau edge 20–28 s. Tái phân tích khóa
`nlag=min(n//4,3000)`.

## 3. PC-C2′ và PC-C2′b khóa trước

### PC-C2′ — control phía generator

- Cell A: đúng ba trace CLEAN `rho=0.925`, rep 1/2/3,
  `rho_offered_clean_rho0.925_rep*.csv`.
- Cell C: đúng ba trace `rho_offered_rep1/2/3.csv` đã đo.
- Dùng edge `uA,uB,vC,vD`, dt lấy từ timestamp/sample metadata và kiểm gần
  0.01 s.
- Với từng run/link, integral ACF cắt tại lag đầu `ACF<=0`,
  `nlag=min(n//4,3000)`.
- Gộp bằng median qua ba rep theo từng link; ratio = tau_A/tau_C.

PC-C2′ PASS khi median của bốn ratio edge `>=5.0` và mọi trace đầy đủ/hữu hạn.

### PC-C2′b — dự đoán trực tiếp của mô hình nugget

- Dùng `rho_measured` Cell A rho=0.925 và Cell C, ba rep mỗi cell.
- Dùng chính estimator đã khóa ở A080: dt=0.2 s,
  `FIT_LAGS=[1,2,3,4,5,6,8,10,15,20]`, chỉ ACF>0.02, log-linear fit.
- Tính mean ACF qua ba rep rồi fit riêng bốn edge; không dùng core fit.

PC-C2′b PASS khi cả bốn edge Cell C fit hợp lệ và median signal fraction Cell
C `>=0.75`. Cell A được in như negative/reference control, không bắt buộc
khớp bit-exact `0.36957` vì A080 gộp 15 run qua năm rho, còn phép này chỉ dùng
rho=0.925.

## 4. Partition kết quả — không có khe hở

| PC-C2′ offered | PC-C2′b signal | Nhãn tái phân tích |
|---|---|---|
| PASS | PASS | `CONTROL_REDESIGN_SUPPORTED_CELL_C_REANALYSIS_VALID` |
| FAIL | bất kỳ | `GENERATOR_CONTROL_FAIL_CELL_C_REMAINS_INVALID` |
| PASS | FAIL | `NUGGET_MODEL_MISS_CELL_C_REMAINS_INVALID_FOR_THIS_AMENDMENT` |
| dữ liệu/fit invalid | bất kỳ | `REANALYSIS_INVALID_OR_INCOMPLETE` |

Chỉ hàng đầu cho phép đọc outcome Cell C đã đóng băng. Khi đó:

- `r(uA,uB)` và `r(vC,vD)` được lấy bit-exact từ artifact Cell C cũ, không
  chạy estimator khác để chọn số.
- H1 bị loại nếu cả hai outcome ngoài vùng H1 `+0.45…+0.75`.
- Cell C một mình vẫn không tách H4/H6; phân xử H6 phải ghi riêng ba đường
  bằng chứng và nhãn hậu kiểm/định lượng phù hợp.

Mọi hàng khác giữ Cell C invalid. Không chỉnh threshold sau khi chạy.

## 5. Dự đoán khóa trước

Theo S19, đổi sigma 0.03→0.10 dự đoán tau offered giảm 11.11×; threshold 5×
để chịu finite-trace estimator. Theo mô hình nugget, signal fraction phải tăng
khi sigma tăng; dự đoán Cell C median `>=0.75`.

Đây là preregistration của phép **tái phân tích** sau khi đã biết r Cell C,
không phải confirmatory preregistration của dữ liệu mới. Giá trị của nó là
khóa control/threshold trước khi tính PC-C2′ trên raw offered và nugget Cell C.
