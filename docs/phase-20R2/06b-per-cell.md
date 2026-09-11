# 20R2.6b — Phụ lục: số gộp che một quần thể phân hoá

⚠️ **THĂM DÒ.** Mọi số ở đây sinh **SAU** khi mở hộp. Nó **không đổi** phán quyết
20R2.6 (8 ô, đã ký, **5/8**). Nó chỉ tách lớp gộp ra.

**Đối chứng cho chính phụ lục này:** cột `pooled_8_signed` dưới đây tái lập
`06-adjudication.json` với sai lệch < 1e-9; nếu không, tool tự dừng.

---

## 1. Tỉ số theo TỪNG ô (a = 0.9, z = 0.366, trung bình 5 seed)

`m` và số đường "sống" tính từ **bảng chi phí sự thật**, KHÔNG từ `err` — nếu suy
`m` từ `err` thì quan hệ "Rice giải thích err" đúng theo định nghĩa và không kiểm
được gì.

```text
o               t=0,5   t=3    t=28  | stale: 0,5    3     28  |    m    rice  song
poisson@0.850      1.414  1.523  1.655 |  1.410  1.518  1.625 |  0.04  0.999    3
h2@0.700           1.277  1.347  1.557 |  1.264  1.326  1.457 |  0.22  0.976    3
poisson@0.925      1.230  1.300  1.457 |  1.239  1.301  1.388 |  0.15  0.989    3
h2@0.850           1.088  1.199  1.300 |  1.060  1.166  1.182 |  0.49  0.887    3
poisson@0.700      0.945  1.047  1.385 |  0.887  0.964  1.008 |  0.34  0.944    3
poisson@0.960  R7  0.876  0.886  1.004 |  0.883  0.890  0.963 |  0.51  0.879    2
h2@0.925           0.334  0.375  0.406 |  0.309  0.345  0.324 |  1.35  0.404    2
h2@0.960       R7  0.006  0.009  0.027 |  0.004  0.005  0.008 |  3.11  0.008    1
```

`R7` = ô đánh dấu `EXTRAPOLATION_CONTAMINATED`, T2 đã cấm dùng làm headline (§18.2).

**Biên độ phân hoá: 0,006 → 1,655.** Hai ô cùng "quần thể gate" chênh nhau
**gần 300 lần**.

---

## 2. Ba cách tổng hợp, ba bức tranh

```text
tau                           0.5       1       2       3       5      10      20      28
gop 8 o (DA KY)             0.896   0.923   0.938   0.961   1.002   1.022   1.030   1.099
trung vi 8 o                1.017   1.052   1.082   1.123   1.177   1.197   1.257   1.342
gop 7 (bo h2@0.960)         1.023   1.054   1.071   1.097   1.143   1.167   1.177   1.252
gop 6 (bo 2 o R7)           1.048   1.082   1.103   1.132   1.187   1.205   1.213   1.293
```

**Chỉ cần bỏ MỘT ô — h2@0.960 — là cả 3 MISS biến mất** (τ=0,5 thành 1,023).
Ô "điển hình" (trung vị) nằm **trên** Sheppard ở **mọi** τ.

⚠️ Đây **không phải** phán quyết mới. Xem §18.2 về vì sao quần thể **không** được
đổi sau khi mở hộp.

---

## 3. Cơ chế: số đường cạnh tranh, không phải mức tải

### 3.1 Ô có 1–2 đường sống — Rice dự đoán khá sát

```text
o                m    rice e^(-m^2/2)   stale/Sheppard do duoc
poisson@0.960   0.51          0.879   0.883 - 0.963
h2@0.925        1.35          0.404   0.301 - 0.345
h2@0.960        3.11          0.008   0.002 - 0.008
```

Đây là nơi giả định "2 hành động" của Sheppard gần đúng, và hệ số Rice
`e^(−m²/2)` bám khá sát giá trị quan sát.

### 3.2 Ô có 3 đường sống — Rice ≈ 1 nhưng lỗi CAO HƠN Sheppard

```text
o                m    rice     stale/Sheppard do duoc
poisson@0.850   0.04   0.999     1.410 - 1.625
h2@0.700        0.22   0.976     1.264 - 1.457
poisson@0.925   0.15   0.989     1.239 - 1.388
h2@0.850        0.49   0.887     1.060 - 1.187
poisson@0.700   0.34   0.944     0.887 - 1.008
```

Hệ số Rice ≈ 1, nhưng 4 trên 5 ô cho tỉ số **1,06–1,63**. Nhiều ranh giới quyết
định thì có nhiều cơ hội lật hơn trường hợp 2 hành động. Đây chính là vi phạm
**"4 đường thay vì 2"** trong bảng đã ký, và nó đẩy lỗi **LÊN**.

### 3.3 ★ SỬA cách kể chuyện của 06.md

```text
06.md viet   : H-B dung o CA 8 tau -> 'hai co che giai thich CHINH XAC'
SU THAT      : H-B dung o muc GOP. Xet TUNG O:
               4/8 o co err_stale > Sheppard o MOI tau
               3/8 o co err_stale < Sheppard o MOI tau
```

Rice **không** phải câu chuyện của cả quần thể. Nó giải thích các ô **ít đường
cạnh tranh**. MISS ở τ nhỏ là kết quả của một **HỖN HỢP**: vài ô bị Rice nén rất
mạnh (đặc biệt ô gần như khoá cứng), cộng với nhiều ô bị **giãn** vì có nhiều
hành động. Câu "giải thích chính xác" trong 06.md đã được sửa.

---

## 4. "Khó về tải" ≠ "khó về quyết định"

```text
prereg dong 802 (AGGREGATION_FALLACY_GUARD) viet:
  "o che do kho that (h2@0.960) co the la 20%"

THUC DO err_total cua h2@0.960:  0.194% (t=0,5)  0.135% (t=3)  0.137% (t=28)
=> lech HAI BAC DO LON so voi con so trong prereg.

Ly do: tai cang nang thi MOT duong cang ap dao.
  h2@0.960: duong tot nhat la argmin 100.0% thoi gian, m = 3.11
  -> quyet dinh gan nhu KHONG BAO GIO lat, twin cu van dung.
```

Với digital twin, đây là hiểu biết có giá trị (vẫn là **thăm dò**): **độ nhạy của
quyết định do CẤU TRÚC CẠNH TRANH giữa các đường quyết định, không do mức tải.**
Twin cũ nguy hiểm nhất ở vùng **tải vừa**, nơi 3–4 đường gần hoà nhau — không
phải ở vùng tải cao nhất.

---

## 5. Muốn biến thăm dò thành khẳng định

Phải theo đúng thứ tự tách mẫu (khám phá trên seed 101–105 → khẳng định trên
seed **mới**):

```text
1. KY TRUOC hai du doan, voi m va so duong song LAY TU 06b (da co san):
   P1  o co <= 2 duong song: err_stale/Sheppard trong mot DUNG SAI quanh
       e^(-m^2/2). Dung sai phai CHON va KY TRUOC khi chay.
   P2  o co >= 3 duong song: ti so > 1.
2. Chay seed MOI 301-305, a = 0.9, tau in {0,5; 3; 28}, nhanh chinh (~15 lenh).
3. Dung lai DUNG khuon plan / guard / hygiene / bo cham dong bang.
```

Chưa ký thì mục 3 của phụ lục này **vẫn chỉ là thăm dò**, dù nó khớp đẹp.

