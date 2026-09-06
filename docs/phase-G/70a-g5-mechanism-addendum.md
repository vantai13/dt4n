# Addendum doc 70 — §3 giải thích sai, cơ chế thật là hai kênh

Append-only, đúng cách [doc 66a](66a-g3b-uncertainty-addendum.md) đã làm. **Không sửa doc 70, không đổi một phán quyết nào.**
`TRANSFER_FAILS` vẫn đứng, cả năm gate vẫn nguyên kết quả, `kappa_time = 5` vẫn giữ.
Cái được sửa là **câu giải thích ở §3**, và cái được thêm là cơ chế đã kiểm được.

Toàn bộ số dưới đây tái lập bằng `python3 -m tools.g5a_mechanism_audit`.

## 1. Lỗi: `K = 2` trong §3 là cặp null topo, không phải "K nhỏ"

§3 lập luận biên độ ω lớn dần theo **số phát biểu đồng thời**, dựa trên `K=8 → 0.1358` so với `K=2 → 0.0011`.

Lập luận đó hỏng ở chính định nghĩa `K`. `tools/g3_omega_coverage_dryrun.coverage` lấy

```python
out[k] = float(inside[:k].all(axis=0).mean())
```

tức **k link đầu theo thứ tự `LINKS`**. Mà `LINKS[0:2] = ('uA', 'uB')`, và

```
K_TOPO[uA, uB] = 0.0
```

Đây đúng là **cặp null topo** mà doc 47 §4 đã tự nêu — hai link không chung đường nào, nên ω **không thể** ghép chúng và biên độ **buộc phải** bằng 0 ở đó. Chính `NC-2` của `G′.5` dùng đúng cặp này và cho `0.000000`.

Nên hàng `K = 2` không đo "ít phát biểu". Nó đo "cặp này không ghép được". Hai chuyện khác nhau bị gộp làm một, và tôi đã đọc nó thành cái thứ nhất.

## 2. Biến điều khiển là `Σk`, không phải `K`

Định nghĩa `Σk` = tổng các phần tử ngoài đường chéo của `K_TOPO` **bên trong tập** — tức ngân sách ghép cặp mà ω có thể tác động.
Cùng bộ sinh, cùng lưới ω, 200 lượt, nugget đã chứng nhận, dt=0.1:

| tập link | `K` | `Σk` | biên độ |
|---|---:|---:|---:|
| `uA, uB` | 2 | 0.000 | 0.001498 |
| `ac, ad, bc, bd` | **4** | **0.000** | **0.000551** |
| `uA, vC` | 2 | 0.500 | 0.014089 |
| `ac, vC` | 2 | 0.707 | 0.026478 |
| `uA, ac` | **2** | **0.707** | **0.027215** |
| `uA, uB, ac, ad` | 4 | 1.414 | 0.043527 |
| `uA, uB, ac, ad, bc, bd` | 6 | 2.828 | 0.072733 |
| cả 8 link | 8 | 7.657 | 0.133441 |

```
Spearman(biên độ, Σk) = 0.952
Spearman(biên độ, K)  = 0.667
```

Hai hàng in đậm giết lập luận cũ:

```
K = 2, Σk = 0.707  →  0.027215   ← LỚN HƠN ngưỡng T-1 = 0.020
K = 4, Σk = 0.000  →  0.000551   ← nhỏ hơn 49 lần, dù K GẤP ĐÔI
```

Tăng `K` mà giữ `Σk = 0` làm biên độ **giảm**. `K` không phải biến điều khiển.

## 3. Cơ chế thật: ω đi qua **hai** kênh, và cả hai đều bị hấp thụ

Đây là phần thay cho §3. Nó khác lời giải thích được đề xuất trong nhận xét ngoài, ở một điểm tôi phải nêu rõ.

### Kênh 1 — thang. Hấp thụ **chính xác**.

ω làm score phình lên gần đồng nhất trên ba khe. Đọc thẳng từ `q̂` của bản chạy đã đóng băng:

| khe | q̂ tại ω=0 | q̂ tại ω=1 | hệ số thang |
|---|---:|---:|---:|
| 1 | 11.5287 | 14.9832 | 1.29963 |
| 2 | 11.6374 | 15.2572 | 1.31105 |
| 3 | 11.8613 | 15.7589 | 1.32860 |

```
c trung bình = 1.31309     độ không đồng nhất = 2.21% của trung bình
```

Conformal split **đồng biến thang chính xác**, và tôi kiểm chứ không giả định — nhân thẳng ma trận score với `c`:

| `c` | q̂/q̂₀ | coverage | trùng bit với gốc |
|---:|---:|---:|---|
| 1.3131 | 1.313100000000000 | 0.847333333333333 | **có** |
| 2.0 | 2.000000000000000 | 0.847333333333333 | **có** |
| 7.5 | 7.500000000000000 | 0.847333333333333 | **có** |

`q̂` nhân đúng `c` tới 15 chữ số, coverage **trùng bit** ở mọi `c`. Phân vị mẫu đồng biến thang, nên điều kiện `s ≤ q̂` không đổi với **từng dòng dữ liệu**.

### Kênh 2 — xếp hạng. **Không** phải thang, và hấp thụ vì lý do khác.

Nhận xét ngoài dừng ở kênh 1. Nhưng ω không chỉ đổi thang — nó đổi **thứ hạng**:

| ω | tỉ lệ dòng có thứ tự twin khác ω=0 |
|---:|---:|
| 0.25 | 0.4448 |
| 0.50 | 0.4465 |
| 0.75 | 0.4587 |
| 1.00 | 0.4733 |

**47% số dòng bị xếp lại** ở ω=1. Đây là một nhiễu loạn lớn, và đồng biến thang **không** hấp thụ nó.
Đáng chú ý: nó **nhảy bậc** — 44.5% ngay tại ω=0.25 rồi gần như đứng yên — trong khi kênh thang tăng đơn điệu.

Cái hấp thụ kênh này là **thiết kế của estimand 22R**, không phải conformal. `cert/simultaneous_score.pair_scores` ghi rõ:

> *"The column index is a rank slot, never a path identity, so the slot is exchangeable across rows."*

Xếp lại làm **dòng** đổi khe, nhưng phân phối score **của mỗi khe** được giữ. Estimand được định nghĩa trên khe, không trên đường, nên hoán vị dòng giữa các khe không đổi coverage của khe.

```
kênh thang     → hấp thụ bởi tính đồng biến thang của conformal   (chính xác)
kênh xếp hạng  → hấp thụ bởi tính hoán đổi được của khe xếp hạng  (theo thiết kế 22R)
⟹ coverage bất biến; dư lượng 0.000714 tương ứng đúng 2.21% không đồng nhất của thang
```

Đây **không** phải là hai thất bại. Đây là hai tính chất cấu trúc, một của thủ tục và một của estimand, cùng chỉ về một hướng.

### Kiểm chứng định lượng của cơ chế

Cơ chế dự đoán `q̂` phải phình đúng bằng hệ số thang:

```
Dự đoán từ c trung bình:        +31.31%
Đo được, max-score:             +32.17%
```

Khớp trong **0.86 điểm phần trăm**. Và max-score **phải** vượt trung bình vì nó lấy cực đại của ba khe đã bị nhân thang lệch nhau — đúng chiều, không phải trùng hợp.

## 4. ⚠️ Hệ quả cho thiết kế `G′.5b`: "surrogate thang thuần tuý" phải nhân **score**, không nhân sai số twin

Nhận xét ngoài đề nghị một đối chứng: nhân sai số twin ở ω=0 với `c` rồi so với ω=1. **Đối chứng đó không thuần thang**, và tôi đo được nó lệch bao nhiêu:

| `c` | q̂/q̂₀ (đáng lẽ = `c`) | coverage | dòng bị xếp lại |
|---:|---:|---:|---:|
| 1.3131 | 1.316453 | 0.848167 | **0.0912** |
| 2.0 | 2.023738 | 0.846833 | 0.2790 |
| 7.5 | **8.081441** | 0.838833 | **0.7768** |

Nhân sai số twin lên thì twin **xếp lại thứ hạng**: 9.1% số dòng ngay ở `c = 1.31`, và 77.7% ở `c = 7.5`, kéo `q̂/q̂₀` lệch khỏi `c` (8.081 thay vì 7.5).
Nên đối chứng đó trộn cả hai kênh và **không** trả lời được câu "ω có cấu trúc ngoài thang không".

Muốn cô lập kênh thang, phải nhân **ma trận score** (bảng ở §3, trùng bit). Muốn đo phần không quy giản được của ω, đối chứng đúng là so ω=1 với **ω=0 đã nhân score theo `c` đo được**, và chênh lệch còn lại chính là kênh xếp hạng.
Điều này phải vào prereg của `G′.5b` **trước** khi chạy, không phải sửa sau.

## 5. Giới hạn mới

```
G-L109: biên độ coverage đồng thời theo ω tỉ lệ với TỔNG GHÉP CẶP `Σk`
        bên trong tập được phát biểu, không với cỡ tập `K`.
        Đo được: Σk=0.707 tại K=2 cho 0.027215, còn Σk=0 tại K=4 cho
        0.000551. Spearman theo Σk = 0.952, theo K = 0.667.
        Mọi so sánh "K nhỏ hơn nên hiệu ứng nhỏ hơn" đều phải kiểm Σk trước.

G-L110: ω đi vào estimand khe xếp hạng qua HAI kênh — một hệ số thang gần
        đồng nhất (c=1.31309, không đồng nhất 2.21%) và một phép xếp lại
        thứ hạng (47% số dòng tại ω=1, nhảy bậc ngay từ ω=0.25).
        Kênh một bị conformal hấp thụ CHÍNH XÁC; kênh hai bị tính hoán đổi
        được của khe hấp thụ THEO THIẾT KẾ 22R. Đây là cùng hình dạng với
        phép triệt tiêu của G-A010: một thừa số chung xuất hiện ở cả hai vế.
        Hệ quả: mọi thủ tục quyết định đồng biến thang và định nghĩa trên
        khe hoán đổi được đều bất biến với ω ở mức coverage. Chi phí của ω
        hiện ra ở CÔNG SUẤT, không ở tính đúng.
```

`G-L109` và `G-L110` là **giới hạn về diễn giải**, không hiệu chỉnh số nào. Không có gate nào đổi kết quả.

## 6. Cái không đổi

- `TRANSFER_FAILS`, doc 47 không adopt, `kappa_time = 5` giữ nguyên.
- `T-1`/`T-2`/`T-3` FAIL, `NC-1`/`NC-2` PASS, biên độ max-score 0.000714.
- Cận trên đúng để trích dẫn vẫn là **0.0055**; vẫn **không** dùng `0.0271` của `G′.3a`.
- Kết luận §5 về doc 47 dưới nugget MA(1) không phụ thuộc §3, nên không đổi.
- §4 (ω là trục công suất) vẫn là **quan sát mô tả ngoài bảng gate**, và §3 sai không làm nó mạnh hơn hay yếu đi.

[g5a_mechanism_audit.json](../../results/SMOKE/phase-G2/g5a_mechanism_audit.json) — SHA256 `1c699b185b363bb95ecd1775a76a11d66aee04b98c8174a39801e56ae990d4e1`
