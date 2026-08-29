# 07 — Phán quyết PC-C3: `+0.6` không sống sót khi chỉ bundle telemetry đổi

```text
Prereg      docs/phase-D/00c-prereg-pc-c3.md
Tag         phase-D-pc-c3-start  tại commit 7f486a28
Ký lúc      TRƯỚC khi bất kỳ hệ số tương quan nào được tính trên cellA_long
Artifact    results/SMOKE/phase-D/pc_c3_cellA_long.json
Mininet     0 giây
```

## 1. Kết quả

```text
pair        r         n_eff    CI95(Fisher)         band da ky
uA-uB    +0.1755      40.81   [-0.1404, +0.4590]    H6
vC-vD    -0.0166      40.90   [-0.3230, +0.2929]    H0
ac-ad    -0.0489     108.88   [-0.2349, +0.1406]    NC-C1 dat
bc-bd    -0.0009     204.76   [-0.1380, +0.1362]    NC-C1 dat
uA-vC    -0.0360      40.90   [-0.3402, +0.2751]    NC-C2 dat
```

Mốc cùng `sigma`, cùng `N_bar = 817`, cùng endpoint, **chỉ khác bundle
telemetry**:

```text
phase-23 (bundle BAT)   uA-uB = +0.5986      vC-vD = +0.6376
cellA_long (bundle TAT) uA-uB = +0.1755      vC-vD = -0.0166
```

Ô then chốt của giai thừa 2×2 — ô đã sinh ra toàn bộ cuộc điều tra này:

```text
phase-23   o (2 low-sigma, chung host) = +0.6181 ; o cao ke tiep +0.0625 ; ti so 9.893x
cellA_long o (2 low-sigma, chung host) = +0.0795 ; o cao ke tiep +0.0183 ; ti so 4.341x
```

Cấu trúc `9.893×` đã sụp. Giá trị tuyệt đối của ô then chốt giảm **7.8×**.

## 2. Kiểm dự đoán điểm bằng đúng máy Fisher đã ký

`SE = 1/sqrt(n_eff - 3)`, áp vào ba dự đoán điểm đã ký ở prereg §3:

| | vs H4 (`r=0.60`) | vs H6 (`r=0.13`) | vs H0 (`r=0`) |
|---|---:|---:|---:|
| `uA-uB` | **−3.17σ BÁC** | +0.29σ | +1.09σ |
| `vC-vD` | **−4.37σ BÁC** | −0.91σ | −0.10σ |
| gộp Fisher z (`r=+0.0802`) | **−5.33σ BÁC** | −0.44σ | +0.70σ |

```text
H4 (endpoint x N_bar) BI BAC o ca hai ban nhan doc lap va o muc gop 5.33 sigma.
H6 va H0 KHONG bi bac boi bat ky ban nhan nao.
```

Đây đúng là kết cục mà phân tích công suất ký trước đã báo: thiết kế có công
suất tách H4, **không** có công suất tách H6 khỏi H0 (D-L29).

## 3. Nhãn tự động và cách đọc nó cho đúng

```text
uA-uB -> band H6 ;  vC-vD -> band H0
=> PHAN QUYET PC-C3 = PRIMARY_REPLICATES_DISAGREE
```

Đây là nhãn đã ký và **không được sửa**. Nhưng phải đọc nó đúng bản chất:

- Hai band `H6` và `H0` **chồng lấn** trên `[0.00,+0.10]`, và prereg §3 đã ghi
  trước điều đó. Hai primary rơi vào hai nhãn khác nhau vì `+0.1755` và
  `−0.0166` nằm hai bên vạch, **không** vì chúng mâu thuẫn nhau.
- Kiểm trực tiếp: `dz = +0.1940`, `SE_diff = 0.2298` ⟹ **+0.84σ**. Hai bản
  nhân **nhất quán với nhau** về mặt thống kê.
- Cả hai nhãn `H6` và `H0` đều nằm trong tập **bác H4**. Nhãn tự động
  `PRIMARY_REPLICATES_DISAGREE` không mang thông tin đó vì partition ký trước
  không lường trước tình huống “hai bản nhân bất đồng nhưng cùng bác H4”. Đây
  là một lỗ hổng đặc tả của chính prereg PC-C3, ghi thành `D-L30`, **không**
  phải lý do để sửa nhãn sau khi nhìn số.

Phát biểu được phép rút ra, ở đúng hạng bằng chứng:

> **H4 (endpoint × N_bar) bị bác ở mức confirmatory.** `N_bar = 817` và
> endpoint `hsrc` chung được giữ **nguyên vẹn**; nếu cơ chế của H4 tồn tại thì
> `r` phải còn ở `+0.45…+0.75`. Nó không còn.
>
> Việc phân xử giữa H6 và H0 **không** thuộc thẩm quyền của PC-C3.

## 4. Validity gate

| Gate | Kết quả |
|---|---|
| prereg + tool commit/tag trước khi tính `r` | PASS, `7f486a28`, audit ở prereg §0 |
| `n_eff >= 25` cho cặp được kết luận | PASS, cả 5 cặp (primary 40.8/40.9) |
| burn-in thực tế `>= 5*tau_pair` | PASS, 87.0 s / 86.8 s |
| NC-C1 `ac-ad`, `bc-bd` ∈ `[-0.10,+0.15]` | PASS |
| NC-C2 `uA-vC` ∈ `[-0.10,+0.15]` | PASS |
| NC-C3 offered mọi cặp `\|r\| <= 0.15` | PASS (lớn nhất `uA-uB = +0.0964`) |
| infra 4 cờ false | PASS |
| thiếu link / NaN / counter reset | PASS, 0 dòng rơi |

`controls.all_pass = true`. Đây là **lần đầu tiên trong Phase D′** một phép đo
correlation đi qua trọn vẹn validity gate.

## 5. Vì sao Cell C `INVALID_RUN` không còn là mất mát

```text
Cell C doi sigma 0.03 -> 0.10, ma sigma dieu khien DONG THOI
     N_bar = rho^2/sigma^2 : 817 -> 74     <- bien cua H4
     nugget                : 0.63 -> 0.13  <- bien cua H6
⟹ confound cau truc: Cell C KHONG BAO GIO tach duoc H4 khoi H6.
   Cell C' (sigma=0.05) cung vay, chi doi it hon.
```

`cellA_long` giữ `sigma = 0.03` nên **giữ nguyên mọi biến của H4** và chỉ đổi
biến của H6. Nó là thí nghiệm phân biệt mà Cell C không thể là. Cell C hỏng
vì nó là **thí nghiệm sai**, không phải vì dữ liệu tệ — và nó được thay bằng
một thí nghiệm đúng, thu được như một đối chứng cho `tau`.

Phán quyết Cell C **không đổi**: `INVALID_RUN` dưới A001/A002, outcome đóng
băng vẫn chưa từng được đọc.

## 6. Ý nghĩa — phát biểu ở đúng hạng

`+0.6` đã đi qua nhiều tài liệu của dự án như một hiện tượng cần giải thích.
PC-C3 cho thấy nó **không sống sót** khi giữ nguyên mọi biến mạng và chỉ tắt
bundle quan trắc của chính Digital Twin.

Với một luận văn về Digital Twin, đây không phải kết quả âm: nó là bằng chứng
rằng **tầng quan trắc dùng để theo dõi hệ đã làm nhiễu chính phép đo đó**, và
nhiễu ấy đủ mạnh để tạo ra một “hiện tượng” giả ở chế độ tải mượt (`sigma`
nhỏ, `nugget` chiếm 63% phương sai). Nối thẳng vào AoI: probe đo độ tươi thông
tin tự nó là một tải, và tải đó làm hỏng đại lượng nó đang đo.

Giới hạn bắt buộc đi kèm phát biểu này:

- `D-L27` — `n_runs = 1` (seed 41). Không có phương sai liên-run.
- `D-L28` — bundle đổi **bốn** yếu tố cùng lúc (`ditto`, `aoi_probe`,
  `cycle_trace`, `reconcile_every 1→30`). PC-C3 tách `{bundle}` khỏi
  `{sigma}`; nó **không** tách được bốn yếu tố với nhau.
- `D-L29` — không có công suất tách H6 khỏi H0.
- Cơ chế vật lý chưa được nhận dạng. “Observer effect ở tầng hệ thống” là
  **mô tả**, chưa phải cơ chế đã đo.

## 7. Việc cho Phase G

```text
luoi 2x2  {ditto on/off} x {sigma_edge 0.03/0.10},  >= 3 seed moi o
muc tieu  (a) tach bon yeu to cua bundle;
          (b) do sf o bon o -> khop hai tham so v_on, v_off (xem D-L25);
          (c) do truc tiep counter_read_dt / common-mode de tach H6 khoi H0.
```
