# 20R2.7 — `d_sla`: cái giá của một quyết định sai

Cách đọc khoá tại prereg **§20**, đóng băng bởi tag `phase-20R2-dsla-frozen`.

⚠️ **`d_sla` KHÔNG phải ms.** Sổ đăng ký trước đây khai `UNIT = ms`,
`SCALE = cost_ms`; mã nói khác (dòng 388 + 567). Thực chất là **hiệu hai tỉ lệ vi
phạm**, **không thứ nguyên**, trong `[−1, 1]`. Đã đính chính ở §20.1 **trước** khi
mở cột.

---

## 1. Kết quả chính có được TRƯỚC khi mở một cột nào

Trên trục exogenous, **13/16 tổ hợp gate có `d_sla` = 0 THEO CẤU TRÚC** — bất kể
twin sai nhiều hay ít. Điều này đo được chỉ từ **môi trường** (07a), 0 phút CPU.

```text
TRUC EXOGENOUS (T_d = 50 ms, T_l = 1%)     12 DEGENERATE . 1 WEAK . 3 INFORMATIVE
  poisson@0.700  a=0,9/0,5   spread 0,005 / 0,000   KHONG duong nao vi pham
  poisson@0.850  a=0,9/0,5   spread 0,886 / 0,919   VUNG BIEN      <- INFORMATIVE
  h2@0.700       a=0,9       spread 0,123           VUNG BIEN      <- INFORMATIVE
  h2@0.700       a=0,5       spread 0,012           WEAK
  poisson@0.925 . poisson@0.960 . h2@0.850 . h2@0.925 . h2@0.960
                             spread 0,000           MOI duong vi pham ~100%

TRUC SELF_CALIBRATED (DEPRECATED)          16/16 INFORMATIVE (spread 0,79-0,97)
```

**ĐO ĐƯỢC ≠ MANG THÔNG TIN.** Hai nguyên nhân **khác nhau** cho cùng một số 0:
SLA **không bao giờ bị chạm** (poisson@0.700), và SLA **không thể đạt được** (từ
h2@0.850 trở lên, *mọi* đường vượt 50 ms gần như mọi lúc).

**Đây là S14 hiện hình trên `d_sla`.** Trục exogenous **trung thực** nhưng **mù ở
hầu hết các ô**; trục self_calibrated **nhìn thấy mọi ô** nhưng chỉ vì ngưỡng được
dựng từ **chính phân phối của từng ô**, tức **vòng tròn**. §20.6 vì thế **không**
chạy nhánh self_calibrated (~35–40 phút): H3 đã đạt ở mức **cấu trúc**.

---

## 2. Phán quyết

```text
S0 DUNG CU   |d_sla| <= err_total moi hang PASS   0/10400 hang vi pham severity CAO
S1 DEGENERATE |d_sla| < 0,01               PASS   96/96 dat          severity THAP
S2 INFORMATIVE d_sla > 0                   PASS   24/24 dat          severity VUA
```

⚠️ **S1 có severity THẤP và điều đó đã được khai trước** (§20.4): `spread` **là**
cận trên của `|d_sla|` và nó ≈ 0, nên S1 gần như chắc chắn đạt. Nó là một phép
kiểm **nhất quán**, không phải một phát hiện.

**S0 là phép kiểm dụng cụ thật:** `|d_sla| ≤ err_total` là **hệ quả đại số** của
định nghĩa (§20.2), nên vi phạm chỉ có thể do **mã**, không do "khoa học". Đã quét
**mọi hàng, mọi z** (10 400 hàng), 0 vi phạm.

---

## 3. `Δ_cond` — giá của MỘT lần sai

Đồng nhất thức (§20.2): `d_sla = err_total · Δ_cond`. `Δ_cond` là thông tin **mới**
mà `d_sla` mang lại, ngoài những gì `err` đã cho biết.

```text
o              a    tau     d_sla      err   Delta_cond
h2@0.700       0.9    0.5   +0.0311   0.4340      +0.072
h2@0.700       0.9      1   +0.0163   0.3374      +0.048
h2@0.700       0.9      2   +0.0080   0.2470      +0.032
h2@0.700       0.9      3   +0.0054   0.2073      +0.026
h2@0.700       0.9      5   +0.0031   0.1744      +0.018
h2@0.700       0.9     10   +0.0018   0.1247      +0.014
h2@0.700       0.9     20   +0.0011   0.0865      +0.012
h2@0.700       0.9     28   +0.0006   0.0799      +0.007
poisson@0.850  0.9    0.5   +0.1849   0.4806      +0.385
poisson@0.850  0.9      1   +0.1136   0.3731      +0.304
poisson@0.850  0.9      2   +0.0625   0.2779      +0.225
poisson@0.850  0.9      3   +0.0427   0.2343      +0.182
poisson@0.850  0.9      5   +0.0270   0.1895      +0.143
poisson@0.850  0.9     10   +0.0143   0.1389      +0.103
poisson@0.850  0.9     20   +0.0068   0.0958      +0.071
poisson@0.850  0.9     28   +0.0054   0.0849      +0.064
poisson@0.850  0.5    0.5   +0.1077   0.4336      +0.249
poisson@0.850  0.5      1   +0.0613   0.3332      +0.184
poisson@0.850  0.5      2   +0.0317   0.2463      +0.129
poisson@0.850  0.5      3   +0.0214   0.2065      +0.104
poisson@0.850  0.5      5   +0.0132   0.1682      +0.079
poisson@0.850  0.5     10   +0.0068   0.1218      +0.056
poisson@0.850  0.5     20   +0.0032   0.0846      +0.038
poisson@0.850  0.5     28   +0.0024   0.0726      +0.033
```

### 3.1 ★ Phát hiện: `Δ_cond` GIẢM theo τ, nên `d_sla` giảm nhanh hơn `err`

```text
poisson@0.850, a = 0,9, tu tau = 0,5 den tau = 28:
  ti le sai        err_total   0,4806 -> 0,0849    giam  5,66x
  gia moi lan sai  Delta_cond  0,385  -> 0,064     giam  6,02x
  tac hai SLA      d_sla       0,1849 -> 0,0054    giam 34,10x   = 5,66 x 6,02
```

Hai yếu tố **cùng giảm và nhân với nhau**. Cách đọc (THĂM DÒ): ở τ nhỏ, khi twin
sai thì nó sai về một tải **đang biến động nhanh**, nên đường nó chọn thực sự tệ.
Ở τ lớn, tải đổi chậm, nên một lựa chọn "sai" vẫn gần như tốt bằng lựa chọn đúng.

⇒ **Tác hại SLA của độ cũ tập trung SIÊU TUYẾN TÍNH ở vùng thời gian tương quan
ngắn.** Đọc `err` một mình sẽ **đánh giá thấp** mức độ tập trung đó.

### 3.2 Số gộp 8 ô — CHỈ MÔ TẢ

```text
gop 8 o (a=0,9): [0.02706, 0.01624, 0.00881, 0.00602, 0.00377, 0.00201, 0.00098, 0.00075]

tai tau = 0,5:  gop = 0.0271  nhung poisson@0.850 MOT MINH = 0.1849
=> so gop ~ 1/7 gia tri cua o INFORMATIVE, vi 6/8 o gop vao cac so 0 CAU TRUC.
```

⚠️ Số gộp này **bị chi phối bởi các số 0 theo cấu trúc**. Nó **không** phải "giá
của sai". Đây là bài học §18.1 áp dụng ngay: từ 20R2.7, **bảng theo từng ô là bắt
buộc**, đứng cạnh số gộp.

---

## 4. Hàm ý cho digital twin (THĂM DÒ)

"Giá của sai" chỉ tồn tại ở **vùng biên** — nơi SLA *đạt được nhưng không được bảo
đảm* (poisson@0.850, h2@0.700 ở a=0,9). Ở **cả hai phía** của vùng đó, độ cũ của
twin **không ảnh hưởng gì** đến SLA: dưới biên thì không gì vi phạm, trên biên thì
mọi đường đều vi phạm.

Kết hợp với 06c: **cấu trúc cạnh tranh** quyết định *tỉ lệ* sai, còn **vị trí so
với ngưỡng SLA** quyết định *giá* của sai. Hai câu hỏi khác nhau, hai vùng nguy
hiểm khác nhau.

---

## 5. Threats to Validity

```text
gate 7-3     CHI do tren truc exogenous. H3 dat o muc CAU TRUC (07a) voi 0 phut
             CPU; nhanh self_calibrated KHONG chay vi moi so tren do dieu kien
             theo mot truc VONG TRON (nguong dung tu chinh phan phoi tung o).
§20.1        So dang ky tung khai SAI don vi (ms / cost_ms). Da sua o NGUON SINH
             truoc khi mo. Moi tai lieu cu trich "d_sla (ms)" deu SAI.
S1 severity  THAP theo cau tao -- da khai TRUOC (§20.4), khong doc nhu phat hien.
13/16 = 0    Ket luan ve "gia cua sai" chi dua tren 3 to hop INFORMATIVE. Mot luoi
             SLA khac (vi du T_delay = 150 ms cua G.114 goc) se cho phan hoach
             KHAC HAN, va cac ket luan nay KHONG chuyen sang do duoc.
link doc lap Nhu 20R2.6: omega_0 = 0 theo cau tao.
```

