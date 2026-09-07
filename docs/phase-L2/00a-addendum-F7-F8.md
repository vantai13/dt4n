# L2.0a — Phụ lục cho doc 00: F7, F8, và hai đính chính

Ngày: 2026-09-07 UTC.
Trạng thái: **`AUDIT_NO_MEASUREMENT`**. Không đo, không root, không chạy mạng.

Phụ lục cho [00-mechanism-gap-audit.md](00-mechanism-gap-audit.md), đã ký dưới
tag `phase-L2-audit-signed`, commit `fecba2f4`. **Doc 00 không bị sửa** — nó là
ghi chép lịch sử. Phụ lục này rút lại §3.2/§6.5 của nó và ghi lý do.

Tái lập: [tools/l2_0a_pacing_check.py](../../tools/l2_0a_pacing_check.py),
khoá bởi [test/test_l2_0a_pacing.py](../../test/test_l2_0a_pacing.py) (8 test).
Artifact: [l2_0a_pacing_check.json](../../results/SMOKE/phase-L2/l2_0a_pacing_check.json).

---

## 0. Phán quyết

| # | Mệnh đề | Phán quyết |
|---|---|---|
| **F7** | Nguồn backlogged qua token bucket phát ra dòng **rải đều**, với mọi burst | ✅ **XÁC NHẬN** — chặt hơn: `CV = 0` chính xác, không phải 0.0016 |
| **F7′** | Độ hạt watchdog có thể cứu ON-OFF | ❌ **BÁC BỎ** — cần `g ≥ 2136 µs`; kernel có hrtimer 1 ns |
| **F8** | Nguồn sau bộ giới hạn `ρC` không sinh được hàng đợi | ⚠️ **ĐÚNG CÓ ĐIỀU KIỆN** — chỉ khi `ρ(t) < 1` **từng điểm** |
| **F9** | ★ MỚI: số hạng `ρ·s/2` **không tồn tại** trên testbed này | Dự đoán `BL-2` (0.7–1.1 ms) **sai**; giá trị thật ≈ sàn |
| **F10** | ★ MỚI: `②a` **không chết** — nó sống nếu cho `ρ(t)` vượt 1 | Không gian thiết kế **không** thu về một |

---

## 1. F7 — XÁC NHẬN, và chặt hơn bạn nêu

Mô phỏng viết lại từ thuật toán HTB (token tích ở `r`, trần `B`, lớp backlogged
nhả khi `tokens ≥ L`, thiếu thì đặt watchdog), bucket khởi tạo **đầy** — trường
hợp thuận lợi nhất cho burst:

```text
burst   rho     CV(gap)   mean gap ms   ly thuyet s/rho   transient (khung)
    1  0.90    0.000000       2.13630           2.13630                  1
    4  0.90    0.000000       2.13630           2.13630                  4
   12  0.90    0.000000       2.13630           2.13630                 12
   50  0.90    0.000000       2.13630           2.13630                 50
```

`CV = 0` **chính xác**, không phải `0.0016`. Khoảng cách trung bình bằng `s/ρ`
tới 9 chữ số, **không phụ thuộc burst**. Cơ chế đúng như bạn nói: token bị tiêu
ngay khi sinh ra, bucket không bao giờ tích luỹ dưới backlog.

### 1.1. Burst **có** tồn tại — nhưng là transient một lần

Bucket khởi tạo đầy thì đúng `burst` khung ra ở `t = 0`. Sau đó không bao giờ nữa.

| burst | khung ra tại t=0 | % của run 60 s |
|---:|---:|---:|
| 1 | 1 | 0.0036% |
| 12 | 12 | 0.0427% |
| 50 | 50 | 0.1780% |

⟹ Mô hình ON-OFF của doc 00 mô tả **0.04%** đầu của một run, rồi ngoại suy nó
ra toàn bộ. Đó là lỗi.

### 1.2. F7′ — watchdog không cứu được

Để HTB nhả trọn một khung mỗi lần thức, cần `g ≥ L/r = 2136 µs` tại ρ=0.90.

```text
kernel 6.8.0-1066-gcp · CONFIG_HZ=1000 · CONFIG_HIGH_RES_TIMERS=y
/proc/net/psched: clock_res = 0x3b9aca00 = 1e9  ⟹ hrtimer, đơn vị ns

  g (µs)   khung/lần thức    CV(gap)
      10           0.0047   0.002260
      50           0.0234   0.010440
     100           0.0468   0.022509
    1000           0.4681   0.160614      ← timer 1 ms vẫn chưa đủ 1 khung
    4000           1.8724   0.934015      ← cần timer thô gấp ~2000× hrtimer
```

⟹ Lối thoát duy nhất của mô hình ON-OFF đã bị đóng bằng số học. **F7 đứng vững.**

---

## 2. ★ F9 — nhưng giá trị thay thế của bạn cũng sai

Bạn viết giá trị thật là `ρ·s/2 ≈ 0.86 ms` — "thời gian phục vụ dở dang của gói
đang truyền". **Số hạng đó không tồn tại ở đây.**

### 2.1. Cơ chế

Tầng 2 là HTB `rate C`, `burst B₂ = 1600 B`, trên **veth**. Veth không có tốc độ
đường truyền — HTB tạo trễ bằng cách **hoãn dequeue**, không bằng cách nối tiếp
bit. Dưới đầu vào rải đều ở `ρC`:

```text
token tích ở C, tiêu ở ρC  ⟹  net +(1−ρ)C  ⟹  bucket BÃO HOÀ ở B₂ = 1600 B
B₂ = 1600 B > L = 1442 B   ⟹  mọi khung tới đều có đủ token  ⟹  đi ngay
⟹ backlog tầng 2 ≡ 0 với MỌI ρ < 1
```

### 2.2. Phán quyết bằng dữ liệu đã đo

`cbr` của Phase L **chính là** chế độ F7: `c_a = 0.004`, tức rải đều. Nếu `ρ·s/2`
có thật, nó phải hiện ra ở đó.

| ρ | `cbr` đo được | dôi trên sàn | `ρ·s/2` đòi hỏi |
|---:|---:|---:|---:|
| 0.60 | 0.1382 | **−0.0025** | +0.6048 |
| 0.80 | 0.1403 | **−0.0004** | +0.8064 |
| 0.90 | 0.1330 | **−0.0077** | +0.9072 |
| 0.95 | 0.1385 | **−0.0022** | +0.9576 |

`R` đo được = **1.0021**. `R` nếu `ρ·s/2` đúng = 1.5833.

⟹ Sai lệch **hai bậc độ lớn**. Số hạng `ρ·s/2` bị bác bỏ bằng thực nghiệm.

Bằng chứng cơ chế độc lập, `02-probe-validation.md:36-38` — OWD tại tải 0:

```text
bw=8: 0.1624 ms   (nếu serialize: s = 1.512 ms)
bw=6: 0.1407 ms   (nếu serialize: s = 2.016 ms)
bw=4: 0.1273 ms   (nếu serialize: s = 3.024 ms)
⟹ OWD KHÔNG tỉ lệ nghịch với bw; nó còn TĂNG theo bw.
⟹ khớp 99-gate-decision.md:50-51: serialization không được tính.
```

### 2.3. Hậu quả với gate của bạn

| gate bạn đề xuất | ngưỡng bạn ký | giá trị thật | phán quyết |
|---|---|---|---|
| `BL-1` burst=1 vs 12 lệch < 0.15 ms | — | cả hai ≈ sàn | ✅ PASS, nhưng **tầm thường** |
| `BL-2` delay(ρ=0.90) = **0.7–1.1 ms** | ký trước | **≈ 0.14 ms** (sàn) | ⛔ **sẽ FAIL và bị đọc nhầm** |
| `R` nhánh `BL` = 1.583 | "sống sót" | **không xác định** (0/0) | ⛔ rút |

★ `BL-2` phải sửa thành: **`delay(ρ) − sàn ≤ 0.15 ms` với mọi ρ, và `R_BL` không
đọc được.** Nếu ký ngưỡng 0.7–1.1 ms rồi đo ra 0.14 ms, bạn sẽ kết luận "đường
ống hỏng" trong khi nó chạy đúng — đúng kiểu thất bại `INVALID_INSTRUMENT` giả.

---

## 3. ★ F10 — F8 chỉ đúng TỪNG ĐIỂM, nên `②a` chưa chết

F8 phát biểu: nguồn sau bộ giới hạn `ρC` (`ρ < 1`) không sinh được hàng đợi.
Đúng — **nhưng chỉ khi `ρ(t) < 1` tại mọi thời điểm.** Nếu `ρ(t)` được phép vượt
1 tạm thời trong khi `ρ̄ < 1`, hàng đợi hình thành ngay:

```text
sigma_fast   %ρ(t)>1   d(0.60)   d(0.90)   d(0.95)        R
      0.00      0.0%    0.0000    0.0000    0.0000    không xác định
      0.05     16.0%    0.0000    0.0043    0.0648    không xác định
      0.10     31.5%    0.0000    0.1297    0.5453
      0.20     40.5%    0.0173    1.0906    2.9321    169.5
      0.30     43.7%    0.1650    2.9393    6.3539     38.5

tham chiếu Phase L đo được: poisson d(0.90) = 5.725 ms, R = 11.84
```

Tại `σ_fast = 0.30`, `d(0.90) = 2.94 ms` — cùng bậc với 5.725 ms của Phase L, và
**cả hai tầng vẫn là HTB trong kernel**, tức không mở lại `G-L98`.

| lựa chọn | phán quyết của bạn | phán quyết sau F10 |
|---|---|---|
| ① `cbr` | CHẾT | **CHẾT** (không đổi) |
| ②a điều biến rate nhanh | ⛔ CHẾT | ⚠️ **SỐNG có điều kiện** — cần `ρ(t)` vượt 1 |
| ②b/②c burst kernel-side | ⛔ CHẾT | **CHẾT** (F7 đúng) |
| ③ nguồn không bị giới hạn | ✅ duy nhất sống | ✅ sống |
| ②d HYBRID (`φ`) | ★ đề xuất | ✅ vẫn hợp lệ, nhưng **không còn là lối duy nhất** |

⚠️ **Cái giá chưa đo của ②a:** khi `ρ(t) > 1`, tầng 2 kẹp tốc độ ở `C`, nên
`ρ̄` **thực hiện được** nhỏ hơn `ρ̄` **ra lệnh**. Đó là một thiên lệch trên chính
estimand mà Phase G vừa mua. Phải đo, không được giả định.

> 📌 Vậy không gian thiết kế **không** thu về một. Nó còn `②a`, `②d`, `③` —
> và cả ba đều tham số hoá bởi *"bao nhiêu phương sai, và phương sai đó đến từ
> đâu"*. Đó là câu hỏi của L2.0b′, không phải "có hàng đợi không".

---

## 4. Rút lại từ doc 00

| mục doc 00 | trạng thái |
|---|---|
| §3.2 mô hình ON-OFF, `delay_q = ρ·max(0,(n−1)s−β)²/(2ns)` | ⛔ **RÚT** — mô tả transient 0.04%, không phải trạng thái dừng |
| §3.2 bảng dự đoán MAIN (n × ρ) | ⛔ **RÚT** — giá trị thật ≈ sàn ở mọi ô |
| §6.5 `Q-1`, `Q-3`, lưới `B ∈ {1,4,8,12}` | ⛔ **RÚT** — `Q-3` ≡ 0 theo cấu trúc |
| §3.3 `R` tất định = 1.583 | ⛔ **RÚT** cho nhánh `BL` — `R` không xác định |
| §1.1 **F1** `q_mean_ms` là OWD thô | ✅ **GIỮ** |
| §1.2 **F2** `cbr` phẳng, R = 1.002 | ✅ **GIỮ** — và giờ là bằng chứng chính của F9 |
| §3.4 **F5** `h2` R = 3.716, gate `LOSS-1` | ✅ **GIỮ** |
| §6.2 **F6** probe phải chèn ở `l2mid` | ✅ **GIỮ** |
| §4 `T_c = B/(ρC)` bộ lọc thông thấp | ⚠️ **SỬA** — đúng cho nguồn **có lúc nhàn rỗi**, không đúng cho nguồn backlogged (bucket không bao giờ tích) |

`β = 2.13333 ms` vẫn đúng và vẫn cần cho nhánh `PC`/`OVF`, nơi nguồn **không**
backlogged. Nó chỉ vô nghĩa ở nhánh `BL`.

---

## 5. Giới hạn L2-L1

```text
L2-L1  NGUỒN BACKLOGGED SAU MỘT BỘ GIỚI HẠN TỐC ĐỘ KHÔNG SINH ĐƯỢC PHƯƠNG SAI

  Một nguồn backlogged đi qua token bucket (rate r = ρC, burst B) phát ra dòng
  RẢI ĐỀU chu kỳ L/r, với MỌI B. Token bị tiêu ngay khi sinh, nên bucket không
  bao giờ tích luỹ; `burst` chỉ có hiệu lực sau một khoảng NHÀN RỖI, mà nguồn
  backlogged không có. Phương sai đến bằng 0 theo cấu trúc.

  ⟹ Hàng đợi ở link tốc độ C chỉ hình thành khi tốc độ đến TỨC THỜI vượt C.
     Điều đó đòi hỏi MỘT trong hai:
       (a) một nguồn KHÔNG bị giới hạn dưới C  → lựa chọn ③ / ②d
       (b) cho phép ρ(t) VƯỢT 1 từng lúc      → lựa chọn ②a
     Không có cách thứ ba.

  ⚠️ Kiểm bằng: CV(gap) = 0 với B ∈ {1,4,12,50} (F7); độ hạt watchdog cần
     ≥ 2136 µs mới đảo được kết luận, kernel thực tế có hrtimer 1 ns (F7′);
     và `cbr` của Phase L — chính chế độ này — đo được dôi trên sàn ≈ 0 (F9).
```

## 6. Nợ chuyển tiếp cho L2.0b′

1. **`BL-2` phải sửa ngưỡng** trước khi ký (§2.3). Ngưỡng 0.7–1.1 ms sẽ tạo một
   `INVALID_INSTRUMENT` giả.
2. **`②a` phải vào lại bộ lựa chọn** với một nhánh đo riêng: `σ_fast` nào cho
   `d(0.90)` khớp Phase L, và thiên lệch `ρ̄` thực hiện so với ra lệnh là bao nhiêu.
3. **Đường cong `φ`** của bạn vẫn là kết quả chính đáng đo, nhưng `RHO-2` giờ
   phải đo cho **cả** `②a` lẫn `②d` — chúng đánh đổi trên hai trục khác nhau
   (`φ` mua phương sai bằng tải userspace; `σ_fast` mua phương sai bằng thiên
   lệch `ρ̄`).
4. Mô hình fluid của F10 chỉ đúng cho **trung bình**, không cho phân vị. Trước
   khi ký `②a` phải có mô phỏng mức gói.
