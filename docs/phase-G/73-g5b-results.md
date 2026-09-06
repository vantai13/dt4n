# G′.5b — Kết quả trục công suất

**Phán quyết vận hành: `ADOPT_WEAK`. Không viết amendment, `kappa_time = 5` vẫn giữ.**
Lý do là **một lỗi đặc tả trong prereg của chính tôi**, không phải dữ liệu. Đọc §2 trước khi đọc bất cứ gì khác.

Prereg: [doc 72](72-prereg-g5b-power-axis.md), tag `phase-G2-g5b-prereg`, commit `19b1b70c`. Seed mới `20260908`, một thang thời gian, không có `kappa_time`.
Mã Phase 22 không bị sửa; tool tự kiểm bằng `git show phase-G2-g5b-prereg:<path>` trước và sau khi chạy.

## 1. Bảng gate

| Gate | Đại lượng | Ngưỡng đã ký | Đo được | Kết quả |
|---|---|---|---:|---|
| `P-1` | biên độ tỉ lệ chấp nhận qua ω, max-score | >= 0.050 | 0.101771 | PASS |
| `P-2` | biên độ / SD một vệt | >= 5.0 | 7.360852 | PASS |
| `P-3` | "bước liền kề xấu nhất, phải không tăng" | >= -0.005 | -0.030782 | **VOID — xem §2** |
| `NC-1` | biên độ coverage max-score | <= 0.005 | 0.001022 | PASS |
| `NC-2` | biên độ công suất trên `{uA, uB}` | <= 0.010 | 0.000000 | PASS |
| `P-4` | `\|A(1) − A_scale(1)\|` | báo cáo | 0.005292 | báo cáo |
| `P-5` | tỉ lệ dòng bị xếp lại | báo cáo | 0.457400 | báo cáo |
| `NC-3` | không đồng nhất hệ số thang | báo cáo | 2.28% | báo cáo |
| `S-1` | q̂ phình so với dự đoán kênh thang | báo cáo | +32.20% | báo cáo |

## 2. ⚠️ `P-3` ký sai dấu — và tôi lấy phán quyết bảo thủ

Prereg §4 ghi `P-3` là:

> *"worst adjacent step in acceptance, **must be non-increasing** | `>= -0.005`"*

Hai vế đó **mâu thuẫn nhau**. Văn xuôi đòi dãy **không tăng**; công thức lại phạt mọi bước **giảm** quá 0.005.
Mà tỉ lệ chấp nhận của một trục công suất **phải giảm** khi ghép cặp tăng — đó chính là hiệu ứng đang tìm. Tôi bê nguyên quy ước dấu của `T-3` (doc 69), nơi đại lượng được đo là coverage **tăng** theo ω, mà không lật dấu cho một đại lượng giảm.

Dữ liệu đọc theo cả hai cách:

```
acceptance:  0.53977  0.50899  0.48303  0.45946  0.43800
bước      :   -0.03078  -0.02596  -0.02357  -0.02146
              ↑ cả bốn bước ĐỀU ÂM, đơn điệu giảm tuyệt đối

Đọc theo CÔNG THỨC  (bước ≥ −0.005)        →  FAIL  (−0.0308)
Đọc theo VĂN XUÔI   (không tăng: bước ≤ 0) →  PASS  (bước tăng lớn nhất = −0.0215)
```

Một gate tự mâu thuẫn thì **không đo được gì**. Tôi ghi nó là **VOID**, không phải PASS và không phải FAIL.

**Và tôi lấy phán quyết bảo thủ: `ADOPT_WEAK`, tức không rút `kappa_time`.**

Lý do phải bảo thủ, dù cách đọc kia cho kết quả đẹp hơn: nếu tôi chọn cách đọc sau khi đã thấy `0.101771` và biết nó cho `POWER_AXIS_HOLDS`, thì tôi đang **chọn ngưỡng theo kết quả**. Đó đúng là thứ toàn bộ kỷ luật prereg tồn tại để chặn, và nó không được phép ngay cả khi cách đọc kia rõ ràng là ý định ban đầu.

Cách hợp lệ duy nhất để lấy `P-3` là **ký lại `P-3b` với dấu đúng và chạy lại trên seed thứ ba**. Chi phí ~20 giây máy. Không có lý do nào để đi tắt.

> 🔑 Ghi lại vì đây là bài học nghề, không phải sự cố: một gate đúng phải nói rõ **chiều kỳ vọng** của đại lượng, không chỉ độ lớn. `T-3` và `P-3` đo hai đại lượng đi ngược chiều nhau; sao chép ngưỡng giữa chúng là sao chép một giả định ẩn về dấu.

## 3. Kết quả thực chất: `ω` gần như **thuần thang**

Đây là phát hiện chính, và nó độc lập với `P-3`.

| ω | chấp nhận thực đo `A(ω)` | surrogate thang `A_scale(ω)` | chênh lệch |
|---:|---:|---:|---:|
| 0.00 | 0.53977 | — | — |
| 0.25 | 0.50899 | 0.50738 | +0.00161 |
| 0.50 | 0.48303 | 0.48017 | +0.00286 |
| 0.75 | 0.45946 | 0.45549 | +0.00397 |
| 1.00 | 0.43800 | 0.43271 | **+0.00529** |

Surrogate **nhân ma trận score** với `c` đo được và **giữ nguyên margin twin ở ω=0** — tức nó chỉ cho phép một cơ chế duy nhất: q̂ phình lên. Không chạm sai số twin, đúng cách [doc 70a §4](70a-g5-mechanism-addendum.md) đã chỉ ra là bắt buộc.

```
Toàn bộ hiệu ứng công suất của ω:      0.101771
Phần surrogate thang giải thích được:   0.096479   (94.8%)
Phần KHÔNG quy giản được:               0.005292   ( 5.2%)
```

**94.8% chi phí công suất của `ω` chỉ là q̂ phình.** Phần dư 5.2% là kênh xếp hạng — và nó đúng bằng thang mà `P-5` đo: 45.7% số dòng bị xếp lại ở ω=1, nhưng việc xếp lại đó gần như không đổi tỉ lệ chấp nhận.

**Hệ quả nếu kết quả này đứng vững sau khi `P-3b` chạy lại:** `ω` **quy giản được về một `σ` hiệu dụng**. Không phải "trục thứ năm xứng đáng", mà là "một cách phức tạp để tăng `σ`". Theo cây phán quyết của prereg, đó là `REDUCIBLE_TO_EFFECTIVE_SIGMA` — kết cục **rẻ nhất**, vì nó cắt `ω` khỏi lưới quét chứ không chỉ cắt `kappa_time`.

Tôi **không** tuyên bố điều đó hôm nay. `classification` trong artifact để `null` vì `verdict != POWER_AXIS_HOLDS`.

## 4. Tính đúng không nhúc nhích — `G′.5` được tái xác nhận trên seed mới

```
biên độ coverage đồng thời max-score qua ω:  0.001022     (NC-1, ngưỡng 0.005)
biên độ công suất trên cặp null {uA, uB}:    0.000000     (NC-2, ngưỡng 0.010)
```

Đây là seed độc lập, và nó cho lại đúng kết luận của `G′.5`: `ω` **không** đổi tính đúng của chứng nhận. Cộng với `G-A010`, giờ có **ba** chứng cứ độc lập cho cùng một bất biến.

Cặp null cho **đúng 0.000000** ở mọi ω — khối hiệp phương sai bất biến theo ω nên cùng innovation cho cùng kết quả bit-đối-bit.

## 5. Cơ chế: dự đoán của doc 70a khớp trên seed mới

| đại lượng | doc 70a (seed cũ) | `G′.5b` (seed mới) |
|---|---:|---:|
| hệ số thang trung bình `c` | 1.31309 | 1.31552 |
| không đồng nhất giữa các khe | 2.21% | 2.28% |
| q̂ phình, max-score | +32.17% | +32.20% |
| dòng bị xếp lại tại ω=1 | 47.33% | 45.74% |

Cơ chế hai kênh của doc 70a tái lập trên dữ liệu chưa từng dùng để phát hiện ra nó. Đây là kiểm chứng out-of-sample thật, không phải mô tả lại.

## 6. Dự đoán ký trước so với kết quả

| đại lượng | dự đoán đã ký | đo được | |
|---|---|---:|---|
| `P-1` biên độ chấp nhận | 0.07 – 0.13 | 0.101771 | trúng |
| `P-2` SNR | > 10 | 7.360852 | **trượt** (vẫn qua gate 5.0) |
| `P-4` phần dư | 0.00 – 0.03 | 0.005292 | trúng |
| `P-5` dòng xếp lại | 0.44 – 0.48 | 0.457400 | trúng |
| `NC-1` | < 0.003 | 0.001022 | trúng |
| `NC-2` | < 0.005 | 0.000000 | trúng |
| `NC-3` | 1.5% – 3.5% | 2.28% | trúng |
| `S-1` q̂ phình | 30% – 34% | +32.20% | trúng |

7/8 trúng. `P-2` trượt vì tôi ngoại suy SNR từ biên độ mà quên rằng SD giữa các lượt cũng lớn hơn ở kênh công suất so với kênh coverage.

## 7. Giới hạn

```
G-L111: P-3 của doc 72 tự mâu thuẫn — văn xuôi đòi dãy không tăng, công thức
        phạt bước giảm. Đại lượng được đo GIẢM theo thiết kế, nên công thức
        phạt đúng hiệu ứng đang tìm. Gate ghi VOID, không PASS không FAIL, và
        phán quyết lấy nhánh bảo thủ. Mọi gate về sau phải ghi rõ CHIỀU kỳ
        vọng của đại lượng, không chỉ độ lớn ngưỡng.

G-L112: 94.8% chi phí công suất của ω được giải thích bằng q̂ phình đơn thuần
        (surrogate nhân ma trận score). Phần dư 0.005292 là kênh xếp hạng.
        Nếu tái lập sau P-3b, ω quy giản được về σ hiệu dụng và KHÔNG xứng
        đáng một trục riêng. Chưa tuyên bố; cần một lượt chạy hợp lệ.
```

- Toàn bộ là mô hình tổng hợp sai số twin, không phải chạy gói thật.
- Kết luận chỉ áp cho 4 hành động / 3 khe, `dt=0.1`, `τ=3 s`, `σ_ref=0.028` tại `uA`, lưới ω 5 điểm, `alpha=0.10`.
- `A_scale` giữ margin twin ở ω=0 theo thiết kế; nó cô lập kênh q̂, **không** phải một mô hình đầy đủ của ω.
- Chưa có bằng chứng vật lý cho ω≠0: `G′.4` chỉ đo ω=0.

## 8. Việc tiếp theo

1. **`P-3b`**: ký lại một gate đơn điệu với dấu đúng (`max(diff) <= +0.005`), seed thứ ba, chạy lại. ~20 giây máy.
2. Chỉ sau đó mới xét amendment rút `kappa_time`, và amendment đó còn phải nói rõ chế độ PC của doc 42 đang mua cái gì mà giờ không mua nữa.
3. Nếu `P-4` tái lập ở mức ~0.005, cân nhắc rút luôn `ω` khỏi lưới quét, thay bằng `σ_eff = σ·c(ω)`.

[g5b_power_axis.json](../../results/SMOKE/phase-G2/g5b_power_axis.json) — SHA256 `62239b1f5cef6e276e82854cc691e0ce2e0cfd5eb38f4adab68001b7dbb38600`
