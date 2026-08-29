# Amendment D-A002 — chẩn đoán PC-C2′ FAIL (KHÔNG đảo phán quyết A001)

```text
Ngày ký                  2026-08-29
Trạng thái               SIGNED_DIAGNOSIS_ONLY
Tag khóa                 phase-D-pc-c2-second-start
Dữ liệu                  0 giây Mininet cho amendment này
Giữ nguyên               GENERATOR_CONTROL_FAIL_CELL_C_REMAINS_INVALID
```

## 0. Điều amendment này KHÔNG làm

- Không hạ threshold `5.0` của PC-C2′/PC-C2″.
- Không bỏ link `vD`, không thay median bốn ratio bằng ratio của median gộp.
- Không project `intercept > 1` về 1 dưới rule fit đã ký ở A001.
- Không đọc outcome đóng băng của Cell C. `may_read_frozen_outcomes_under_A001`
  vẫn `false`; các `r` trong `cellC_analysis.json` không được trích dẫn hay
  diễn giải ở bất kỳ mục nào bên dưới.
- Không đảo `INVALID_RUN` của Cell C trong `03-gate-decision.md`.

Amendment này chỉ chẩn đoán **vì sao** PC-C2′ MISS, rồi ký một
preregistration mới (`00b-prereg-pc-c2-second.md`) đòi **dữ liệu mới**.

## 1. Nhánh 1 — tỉ số tau = 4.495 so với ngưỡng ≥ 5.0

Lý thuyết S19 dự đoán `(0.10/0.03)^2 = 11.11×`. Quan sát 4.495×, hụt 2.5×.

Câu hỏi đúng không phải “generator có hỏng không” mà là “`tau_hat` ở nhánh
nào bị lệch”. Cả hai nguồn lệch dưới đây **chỉ tác động lên nhánh Cell A**.

### 1.1 Nguồn (a) — cắt đuôi ACF (truncation)

```text
tau_hat = tau * (1 - exp(-L/tau))

Cell A: L = 30 s, tau_true ~ 29.3 s  ->  he so 0.641   (hut 36%)
Cell C: L = 60 s, tau_true ~  2.64 s ->  he so 1.000   (khong hut)
```

### 1.2 ★ Đính chính cơ chế: L = 30 s của Cell A đến từ `NLAG_CAP`, không từ `n//4`

Chẩn đoán ban đầu gán trần 30 s cho `nlag = n//4`. Đọc lại artifact
`results/SMOKE/phase-D/pc_c2_prime.json` cho thấy **không phải vậy**:

```text
offered dt = 0.01 s (khong phai 0.2 s)
Cell A: n = 12 000  -> n//4 =  3 000 ; NLAG_CAP = 3 000 -> nlag = 3 000 -> L = 30 s
Cell C: n = 24 000  -> n//4 =  6 000 ; NLAG_CAP = 3 000 -> nlag = 3 000 -> L = 30 s
```

Ở Cell A hai giới hạn trùng nhau tại 3000 nên nhìn bề ngoài giống nhau. Ở Cell
C thì `NLAG_CAP` mới là ràng buộc thật (6000 -> 3000).

Bằng chứng trần bị **chạm**, tức censoring xảy ra thật chứ không phải nguy cơ
lý thuyết — `cut_lag == nlag == 3000`:

```text
Cell A: uA rep1, uB rep3, vC rep3   -> 3/12 uoc luong bi cat tai dung tran
Cell C: vD rep2                     -> 1/12
```

Hệ quả then chốt cho thiết kế tiếp theo: **kéo dài run KHÔNG tự động sửa
truncation.** Với `NLAG_CAP = 3000` cố định, một run 1505 s vẫn chỉ nhìn 30 s.
Muốn đạt `L = n//4 * dt = 376 s`, PC-C2″ **phải** nâng cap, và phải nâng
**đối xứng cho cả hai nhánh** (Cell C: 3000 -> 6000, tức 30 s -> 60 s). Việc
này được ký trước trong `00b-prereg-pc-c2-second.md`, không phải sửa sau khi
nhìn số. [D-L21]

### 1.3 Nguồn (b) — trừ trung bình mẫu (mean-removal)

ACF trừ `x_bar` chứ không trừ `mu`. Với chuỗi nhớ dài, `x_bar` hấp thụ đúng
thành phần tần số thấp cần đo:

```text
tau_hat / tau_true ~ 1 - 2*tau/T

Cell A: 1 - 2(29.3)/120  = 0.512     (mat gan mot nua)
Cell C: 1 - 2(2.64)/240  = 0.978     (gan nhu khong mat)
```

### 1.4 Gộp hai nguồn

```text
tau_hat_A ~ 29.3 * 0.641 * 0.512 = 9.6 s     (thay vi 29.3)
tau_hat_C ~  2.64 * 1.000 * 0.978 = 2.58 s
ti so uoc luong ~ 9.6/2.58 = 3.7x
quan sat median = 4.495x                      -> cung bac, cung huong
```

`4.495` **không** phải bằng chứng generator sai. Nó là hệ quả của việc nhánh
Cell A bị lệch xuống ~3×.

### 1.5 Nguyên nhân gốc — thiếu dữ liệu, không thiếu estimator

```text
Cell A: T = 120 s, tau_edge ~ 29 s  ->  T/tau = 4.1
San cua chinh du an (D-L15, budget 55*tau):  T/tau >= 50
=> THIEU 12x
```

Đây là lần thứ ba cùng một lớp lỗi, ba estimator khác nhau:

| Lần | Estimator | Triệu chứng | Gốc |
|---|---|---|---|
| 1 | `tau` integral trên `rho_measured` | ratio 1.119× | nugget triệt tiêu độ nhạy `sigma` (D-L18) |
| 2 | ACF `nlag = n//10` | trần `tau_hat` = 12 s | không thể đo `tau` = 29 s (D-L19) |
| 3 | ACF `nlag = min(n//4, 3000)` | ratio 4.495× | truncation + mean-removal khi `T/tau = 4.1` |

Không estimator nào sửa được `T/tau = 4.1`. [D-L21]

### 1.6 Ngưỡng ≥ 5.0 không thể đạt được ngay từ lúc ký

Ngưỡng `5.0` lấy từ dự đoán lý thuyết `11.1×` rồi chừa biên an toàn. Nó **không
ký kèm độ lệch của estimator ở từng nhánh**. Với nhánh A lệch ~3× và nhánh C
không lệch, một thí nghiệm hoàn hảo cũng chỉ cho ~4.5. Ngưỡng đã vô hiệu từ
lúc ký, không phải vì dữ liệu.

Bài học phương pháp: khi ký ngưỡng trên một **đại lượng ước lượng**, phải ký
kèm **bias của estimator ở từng nhánh**. Phép kiểm rẻ đã bị bỏ qua: “nhánh
baseline có `T >= 50*tau` không?”. Nếu không thì ngưỡng vô nghĩa. [D-L22]

### 1.7 Kiểm chứng chẩn đoán bằng một generator HOÀN HẢO tổng hợp

Đại số ở 1.1–1.4 là xấp xỉ. Phép kiểm trực tiếp: cho **chính** estimator đã ký
ăn một quá trình AR(1) có `tau` biết trước, đúng độ dài và đúng trần lag của
từng nhánh, với tỉ số thật đúng bằng `11.098` theo lý thuyết. Câu hỏi không
phải “generator có tuân `tau ~ 1/sigma^2` không” mà là **“nếu nó tuân tuyệt
đối thì estimator trả về bao nhiêu”**.

`tools/phase_d_estimator_bias_sim.py`, 64 replicate, seed khóa, không đọc một
byte dữ liệu thực nào:

```text
branch                        tau_true   tau_hat_median   bias   cut-at-ceiling
PC-C2'  cell A   T=120 s  cap 3000       29.300    8.700   0.297      31%
PC-C2'  cell C   T=240 s  cap 3000        2.640    2.394   0.907       2%
PC-C2'' cellA_long T=1505 s cap 50000    29.300   24.203   0.826       2%
PC-C2'' cell C   T=240 s  cap 50000       2.640    2.419   0.916       0%

ti so THAT                                        11.098
ti so mot generator HOAN HAO tra ve duoi PC-C2'    3.635   nguong 5.0 -> KHONG DAT NOI
ti so mot generator HOAN HAO tra ve duoi PC-C2''  10.006   nguong 5.0 -> DAT
```

Kết luận định lượng, không còn là suy luận:

- Ngưỡng `>= 5.0` dưới estimator PC-C2′ là **bất khả thi về mặt xây dựng**.
  Một generator hoàn hảo chỉ cho 3.635.
- Quan sát thực `4.495` **cao hơn** 3.635, tức dữ liệu thực **không** kém hơn
  một generator hoàn hảo dưới cùng estimator. `4.495 < 5.0` do đó không phải
  bằng chứng chống generator.
- Dưới estimator PC-C2″ (`T = 1505 s`, cap 50000), cùng generator hoàn hảo cho
  `10.006`, vượt ngưỡng thoải mái. Dự đoán ký trước `10.9` từ đại số nằm cùng
  vùng; sai lệch còn lại là phần AR(1) không mô tả hết đuôi ACF thật.
- Đây chính là phép kiểm rẻ đã bị bỏ qua trước khi ký ngưỡng `5.0`. [D-L22]

Ghi nhận thời điểm để giữ dấu vết: mục 1.7 và tool của nó được viết **sau**
tag `phase-D-pc-c2-second-start` và **trong lúc** `cellA_long` đang chạy. Nó
không đọc dữ liệu `cellA_long`, không đổi ngưỡng `5.0`, không đổi dự đoán ký
trước `10.9`, và không đổi bất kỳ hằng số nào trong
`00b-prereg-pc-c2-second.md`. Artifact:
`results/SMOKE/phase-D/estimator_bias_sim.json`.

## 2. Nhánh 2 — `intercept > 1` là ước lượng CHẠM TRẦN, không phải fit hỏng

### 2.1 Con số

```text
Cell A rho=0.925   sf = 0.3682   (reference A080 15-run 0.36957)   fit hop le
Cell C  vC         sf = 0.9729                                     fit hop le
Cell C  uA         raw intercept = 1.1871                          bi danh invalid
Cell C  uB         raw intercept = 1.1804                          bi danh invalid
Cell C  vD         raw intercept = 1.0040                          bi danh invalid
```

### 2.2 Vì sao phải chạm trần ở Cell C

`sf` là ACF ngoại suy về lag `0+`; miền vật lý là `[0,1]`; `sf = 1` nghĩa là
**không có nugget**. Ở Cell C:

```text
tau ~ 2.64 s, dt_measured = 0.2 s
FIT_LAGS 1..6 = 0.2..1.2 s = 0.08*tau .. 0.45*tau
ACF chi tut tu ~0.93 xuong ~0.63 trong dai do
```

Ngoại suy log-tuyến tính từ một đoạn decay ngắn có nhiễu ⟹ sai số intercept
lớn; khi giá trị thật ≈ 1.0, ước lượng vượt 1 khoảng nửa số lần. `vD = 1.0040`
đúng là `sf = 1.000 ± noise`.

### 2.3 Lỗi đặc tả rule

Một estimator có **miền giá trị bị chặn `[0,1]`** không thể kiểm định bằng
một rule coi “ước lượng chạm trần” là invalid. Đây là lỗi **đặc tả rule**,
không phải lỗi dữ liệu.

Cách xử lý đúng: **ký một rule mới**, không phải bỏ qua rule cũ. A001 vẫn giữ
nguyên; PC-C2″b ký lại miền giá trị và tiêu chí hợp lệ.

Lỗi đặc tả thứ hai, độc lập: `FIT_LAGS = (1..20)` cố định phủ
`0.007*tau .. 0.14*tau` ở Cell A nhưng `0.08*tau .. 1.5*tau` ở Cell C. Cùng
một estimator đang chạy ở **hai chế độ khác nhau** trên hai nhánh của cùng một
control. Fit lag phải chuẩn hóa theo `tau` của chính cell. [D-L24]

### 2.4 Nội dung — mô tả, KHÔNG nâng lên confirmatory

Mô hình nugget dự đoán `sf(sigma) = sigma^2 / (sigma^2 + v)`. Hiệu chuẩn `v`
từ một điểm duy nhất là Cell A:

```text
0.368 = 0.0009/(0.0009 + v)   ->  v = 0.0015457
sf(0.10) du doan = 0.01/(0.01 + 0.0015457) = 0.866
sf(0.10) quan sat ~ 0.97 .. 1.00   -> cung huong, cung bac, khong khop chinh xac
```

Cùng `v` đó cho nugget fraction Cell A `1 - 0.368 = 0.632`; nhân với phần
nugget dùng chung `~0.95` ra `0.60`, so với `r(uA,uB)` measured đã công bố
`+0.5986`. Đây là một đường mô tả nhất quán, **một tham số tự do**, không tinh
chỉnh — nhưng nó vẫn là hậu kiểm:

- `v` được hiệu chuẩn từ chính Cell A, nên khớp Cell A không phải dự đoán.
- Hệ số “phần nugget dùng chung ~0.95” chưa được đo độc lập.
- `r` đóng băng của Cell C **không** được đọc để kiểm đường này.

Do đó H6 vẫn giữ nhãn hậu kiểm dẫn đầu, đúng như A001 và `03-gate-decision.md`.

## 3. Quyết định

```text
GIU     GENERATOR_CONTROL_FAIL_CELL_C_REMAINS_INVALID
GIU     may_read_frozen_outcomes_under_A001 = false
KHONG   override A001, khong chay Cell C', khong doc frozen outcomes
KY      preregistration moi PC-C2'' (docs/phase-D/00b-prereg-pc-c2-second.md)
THU     dung MOT run moi: cellA_long, T = 1505 s, seed 41
NGAN SACH  het sau vong nay; khong co vong 3
```

Dừng vòng lặp sửa estimator. Nguyên nhân gốc là **thiếu dữ liệu**: nhánh
baseline chưa bao giờ đủ dài để đo `tau` của link biên.

## 4. Giới hạn mở bởi amendment này

`D-L21`, `D-L22`, `D-L23`, `D-L24` — xem `02-limits-addendum.md`.
