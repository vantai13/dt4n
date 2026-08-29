# 05 — Tái phân xử PC-C2′ theo Amendment D-A001

Amendment được khóa tại tag `phase-D-pc-c2-prime-start`, commit `19351dfe`,
trước khi chạy `tools/phase_d_pc_c2_prime.py`. Không chạy Mininet mới.

## 1. Dấu vết lịch sử được giữ nguyên

Phán quyết trong `03-gate-decision.md` rằng Cell C là `INVALID_RUN` không bị
xóa hoặc sửa ngược. A001 tạo một lớp tái phân tích mới để kiểm giả thuyết
“control cũ hỏng”, không biến dữ liệu đã xem thành dữ liệu confirmatory mới.

## 2. PC-C2′ — tau trên offered

Estimator đã ký dùng đúng ba rep rho=0.925 của Cell A và ba rep Cell C,
`nlag=min(n//4,3000)`, integral ACF cắt ở lần đầu `ACF<=0`.

| Edge | median tau A (s) | median tau C (s) | A/C |
|---|---:|---:|---:|
| uA | 9.3512 | 1.8923 | 4.9417 |
| uB | 13.9803 | 1.9567 | 7.1447 |
| vC | 10.9288 | 2.6999 | 4.0478 |
| vD | 7.5518 | 2.6239 | 2.8781 |

Median bốn ratio là **4.4948**, thấp hơn threshold đã ký `5.0`:

```text
PC-C2′ = FAIL
```

Không làm tròn 4.4948 thành 5, không bỏ vD và không thay median bằng ratio của
median gộp sau khi nhìn số.

## 3. PC-C2′b — signal fraction

Cell A rho=0.925 cho median edge signal fraction `0.3682`, nhất quán với
reference 15-run A080 `0.36957`.

Cell C có ACF lag dương lớn như dự đoán, nhưng fit A080 trả:

| Edge | raw intercept/signal fraction | Fit hợp lệ |
|---|---:|:---:|
| uA | 1.1871 | không |
| uB | 1.1804 | không |
| vC | 0.9729 | có |
| vD | 1.0040 | không |

Ba intercept vượt 1 làm `all_edge_fits_valid=false`; không được project về 1
sau khi đã ký rule fit. Vì vậy:

```text
PC-C2′b = FAIL
```

## 4. Phán quyết A001

Partition ký trước quy định PC-C2′ FAIL có ưu tiên bất kể PC-C2′b:

```text
GENERATOR_CONTROL_FAIL_CELL_C_REMAINS_INVALID
may_read_frozen_outcomes_under_A001 = false
```

Cell C không được tái phân xử thành VALID và r đóng băng không được dùng làm
outcome confirmatory dưới A001.

## 5. Điều học được mà không đảo phán quyết

- Audit xác nhận PC-C2 measured cũ là control sai loại: Cell A measured tau
  2–3 s bị nugget và trần lag làm co mạnh so với metadata/offered.
- Dự đoán hướng của control mới đúng: ba trong bốn median tau giảm, Cell C
  signal ACF gần lag 0 tăng mạnh. Nhưng magnitude signed MISS.
- Cell A chỉ dài 120 s và nhiều offered ACF chạm/trườn gần trần 30 s; tau
  median 7.55–13.98 s thấp hơn trace Phase-20 240 s 12.58–21.86 s. Đây là
  giới hạn D-L19, không phải giấy phép đổi estimator trong A001.
- H6 vẫn là mô hình hậu kiểm dẫn đầu nhờ offered key cell `+0.0048`, A080
  nugget và raw measured correlation; A001 không nâng H6 thành confirmatory.

## 6. L141 — phán quyết hai lớp

Kết quả family sensitivity được đọc theo hai claim độc lập:

```text
D3 decision band       cbr/poisson/h2 đều D3             ROBUST, đóng
highest-SNR cell       poisson=h2: clean@0.960
                       cbr: clean@0.700                   FRAGILE toàn-grid
```

Theory prior Palm–Khintchine đã ghi trước sweep: với nhiều flow độc lập chồng
chập, Poisson là họ có cơ sở vật lý; h2 là stress family gần hơn cbr cho burst.
Vì poisson và h2 đồng ý, `clean@0.960` robust trên tập prior-supported
`{poisson,h2}`. Tuy nhiên không tuyên bố cbr “xác suất bằng 0” hay chỉ tồn tại
khi N=1; các điều kiện định lý và independence chưa được đo trực tiếp.

L141 vì vậy **đóng một phần**:

- đóng claim decision band;
- cell selection dùng được có điều kiện trên `{poisson,h2}`;
- vẫn mở cho claim không thể loại cbr bằng lý lẽ độc lập và cho onoff toàn
  lưới, vì onoff chỉ có key `6|13`.

## 7. Artifact

Kết quả máy đọc nằm tại `results/SMOKE/phase-D/pc_c2_prime.json`. Artifact giữ
SHA256 của 12 raw input cùng A080 và Cell C analysis, tag/commit, estimator,
threshold và nhãn tự động.
