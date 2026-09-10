# 20R2.6 — Phán quyết (Adjudication)

Artifact: `06-adjudication.json`. Cách đọc **đã khoá trước khi mở** tại prereg §17,
đóng băng bởi tag `phase-20R2-adjudicator-frozen`.

---

## 1. Validity trước — gate VALIDITY đã xong trước gate OUTCOME [NT 56]

```text
ve sinh 20R2.5      8/8 kiem VALIDITY PASS  +  H9 [BUDGET] PASS (70,08/74,53 phut)
H4                  doi chung twin-hoan-hao OM TRON chien dich (PRE rc=0, POST rc=0)
H2                  mot commit, mot moi truong, signed_tag_commit == git_commit
chien dich          167/167 lenh rc=0, 0 file thieu
bo cham             dong bang TRUOC khi mo: tag phase-20R2-adjudicator-frozen
                    -> commit f294a43c2a4e
bo cham tu kiem     bang Sheppard da ky TAI LAP tu cong thuc; band == K_MC*se
                    sha tung parquet doi chieu lai voi so cai (khong thua ke niem tin)
```

Nhánh `PRIMARY_directional.if_violated` mục **(b) "estimator có bug — chạy đối
chứng TRƯỚC khi diễn giải"** đã được thoả bởi H4 **trước** khi mở. Vì vậy các
MISS dưới đây **không** kéo theo lần chạy lại nào.

---

## 2. PRIMARY — dự đoán có hướng `err_đo ≥ err_Sheppard`

```text
tau      err_do   Sheppard      rel      band   muc
0.5      0.3046     0.3399   -10.38%    2.73%   BELOW_BEYOND_BAND
1        0.2362     0.2558    -7.66%    3.86%   BELOW_BEYOND_BAND
2        0.1750     0.1865    -6.16%    5.45%   BELOW_BEYOND_BAND
3        0.1478     0.1539    -3.93%    6.68%   BELOW_WITHIN_BAND
5        0.1203     0.1202    +0.16%    8.62%   AT_OR_ABOVE
10       0.0873     0.0855    +2.15%    8.62%   AT_OR_ABOVE
20       0.0625     0.0606    +3.03%    8.62%   AT_OR_ABOVE
28       0.0564     0.0513    +9.88%    8.62%   AT_OR_ABOVE

HIT (§17-G2, ba muc, 3-sigma co huong) : 5/8
HIT (doc NGUYEN VAN, uoc luong diem)   : 4/8
phan bo muc: {'AT_OR_ABOVE': 4, 'BELOW_BEYOND_BAND': 3, 'BELOW_WITHIN_BAND': 1}
```

⚠️ **Hai con số HIT đều được báo cáo, đúng §17-G2.** Chúng khác nhau vì cách đọc
nguyên văn tính MISS cả những τ chỉ thấp hơn **trong phạm vi nhiễu**.

**Mẫu số là 8 và cố định.** Không MISS nào bị loại khỏi báo cáo.

**Kiểm độ vững z (§17-G3):** bảng ký tại `z = 0,365`, lưới chạy tại `z = 0,366`.
Có phán quyết nào **lật** giữa hai giá trị không? **KHÔNG**.

---

## 3. SHAPE — đơn điệu giảm theo τ

```text
cap             hieu      sigma   trang thai
[0.5, 1.0]     +0.06846    16.66   DECREASING
[1.0, 2.0]     +0.06115    13.91   DECREASING
[2.0, 3.0]     +0.02721     5.95   DECREASING
[3.0, 5.0]     +0.02746     5.75   DECREASING
[5.0, 10.0]    +0.03303     7.73   DECREASING
[10.0, 20.0]   +0.02485     8.06   DECREASING
[20.0, 28.0]   +0.00611     2.53   UNREADABLE

verdict: PASS   {'DECREASING': 6, 'INCREASING': 0, 'UNREADABLE': 1}   mau so = 7 (CO DINH)
```

`UNREADABLE` **không** được tính là đơn điệu và **không** rời khỏi mẫu số (§17-G4).

⚠️ Cặp `[20, 28]` không đọc được (σ = 2,53 < 3). Đây **đúng là cặp** mà
`power_note` đã ký cảnh báo trước chiến dịch: khoảng cách nhỏ nhất, ít chu kỳ
nhất. `n` tại τ = 20 và 28 đã được nâng ×4 **trước** chiến dịch vì lý do đó, và
vẫn không đủ. Đó là **dữ liệu**, không phải lỗi — và nó được báo cáo nguyên trạng.

⚠️ **σ là ước lượng THẤP (bảo thủ).** CRN qua τ làm các ước lượng ở τ gần nhau
tương quan dương, trong khi `se_diff = √(se_i² + se_j²)` giả định độc lập. Hướng
sai số này an toàn: nó khiến ta **khó** tuyên bố "đọc được" hơn thực tế.

---

## 4. Công khai — pilot đã cho xem trước (§17.0)

`02-se-pilot.json` (seed 201–205) đã cho xem trước hình dạng kết quả **trước khi**
§17 được viết. Theo pilot, §17-G2 cho **2 MISS**, đọc nguyên văn cho **6 MISS**.

**Chiến dịch KHÔNG lặp lại pilot.** Kết quả thật cho **3 MISS** (§17-G2) và
**4 HIT** nguyên văn — τ = 2 đã **vượt qua** băng, điều pilot không cho thấy:

```text
tau          0,5      1        2        3        5       10       20       28
pilot      -9,9%   -6,9%   -4,5%   -3,8%   -2,9%   -0,1%   +4,2%   +6,2%
chien dich -10,4%   -7,7%   -6,2%   -3,9%   +0,2%   +2,2%   +3,0%   +9,9%
```

Đây là bằng chứng trực tiếp rằng pilot (seed 201–205) và chiến dịch (seed 101–105)
là hai mẫu **độc lập**: bản xem trước **không** quyết định kết quả.

---

## 5. Từng MISS — cùng độ chi tiết như HIT

Ba MISS: **τ = 0,5 · 1 · 2**. Cả ba đều là `BELOW_BEYOND_BAND`, tức err đo **thấp
hơn** Sheppard quá 3σ.

```text
tau=0.5   err=0.3046  Sheppard=0.3399  rel=-10.38%  band=2.73%  thieu 11.43 sigma
tau=1     err=0.2362  Sheppard=0.2558  rel=-7.66%  band=3.86%  thieu 5.96 sigma
tau=2     err=0.1750  Sheppard=0.1865  rel=-6.16%  band=5.45%  thieu 3.39 sigma
```

Hướng của cả ba MISS **giống nhau**: err đo **THẤP hơn** dự đoán. Một dự đoán có
hướng sai theo **một** hướng nhất quán thì cho biết cái gì sai — đúng như
`PRIMARY_directional.why` đã ký kỳ vọng.

### 5.1 Cơ chế đã ĐĂNG KÝ TRƯỚC (§17-H) — trình bày như THĂM DÒ

⚠️ Hai giả thuyết dưới đây được **đăng ký trước khi mở**, nên hợp lệ để kiểm trên
mẫu khẳng định. Nhưng chúng **KHÔNG vào gate** và **KHÔNG phải lời giải thích đã
được chứng minh** — chúng là thăm dò nhất quán với dữ liệu.

```text
tau     H-B: err_stale/Sheppard    H-A: err_total/Sheppard   san mo hinh
0.5          0.8819  < 1 DUNG         0.8962             6.8%
1            0.9076  < 1 DUNG         0.9234             8.7%
2            0.9203  < 1 DUNG         0.9384            11.6%
3            0.9394  < 1 DUNG         0.9607            13.8%
5            0.9703  < 1 DUNG         1.0016            17.4%
10           0.9745  < 1 DUNG         1.0215            24.0%
20           0.9527  < 1 DUNG         1.0303            32.9%
28           0.9943  < 1 DUNG         1.0988            38.3%
```

**H-B đúng ở CẢ 8 τ.** `err_stale` — đại lượng thuần độ cũ, đúng loại hiện tượng
Sheppard mô tả — nằm **dưới** Sheppard ở mọi τ (0,88 → 0,99). Cơ chế đã đăng ký:
biên chi phí có **kỳ vọng khác 0**, nên theo **Rice (1944)** tần suất đổi dấu bị
nén bởi `exp(−μ²/2s²)`. Nói cách khác: trong topology này **thường có một đường
tốt nhất rõ rệt**, nên twin dùng dữ liệu cũ vẫn chọn đúng thường xuyên hơn mô
hình đối xứng của Sheppard giả định.

**H-A cũng đúng.** `err_total/Sheppard` tăng **đơn điệu** theo τ (0,896 → 1,099) và
**cắt qua 1** giữa τ = 3 và τ = 5. Sàn mô hình `err_model/err_total` tăng đơn điệu
**6,8% → 38,3%**.

Hai cơ chế **ngược chiều nhau**, đúng như §17-H đã đăng ký: H-B kéo xuống ở mọi τ;
H-A đẩy lên ở τ lớn. Chỗ giao nhau giải thích vì sao MISS **chỉ** xuất hiện ở τ nhỏ
— nơi sàn mô hình còn bé (6,8%) nên `err_total ≈ err_stale`, tức nằm dưới Sheppard.

⚠️ **Đính chính đã ghi ở §17-S:** bảng lý do của dự đoán đã ký nói *"3/4 vi phạm
đẩy cùng MỘT hướng"*. Điều đó **không đứng vững**: (a) "kỳ vọng khác 0" thực ra
gộp **hai** hiệu ứng **ngược dấu**, và phần đẩy **xuống** đã bị bỏ sót; (b)
*"nugget MA(1)"* **không tồn tại** trong harness này — `ar1_matrix` sinh AR(1)
thuần. Dự đoán đã ký **không được sửa**, nhưng cơ sở của nó yếu hơn bản ký tuyên bố.

---

## 6. cbr — CHẨN ĐOÁN, báo cáo RIÊNG

```text
16 to hop (8 tau x 2 o cbr): {'BELOW_ALL_GATE': 16}
err_total = {0.0}   err_model = {0.0}   -> SUY BIEN HOAN TOAN
```

**CƠ CHẾ 1 thắng tuyệt đối** (§17-G6): `err(cbr)` nằm dưới **toàn bộ** dải 8 ô gate
ở cả 16 tổ hợp. Và nó không chỉ thấp — nó **đúng bằng 0**.

cbr đều theo thời gian, nên ρ tất định: twin dùng dữ liệu cũ **vẫn chọn đúng**.
Điều này giải thích vì sao claim đối chứng dương của cbr **đã bị rút vì suy biến** —
một ô luôn cho 0 không phân biệt được "dụng cụ đúng" với "dụng cụ chết".

cbr **không bao giờ** vào trung bình của 8 ô gate (`AGGREGATION_FALLACY_GUARD`).

---

## 7. RQ-20R2e — tương phản trục AoI: MÔ TẢ, không phán quyết

```text
z legacy: luoi 0.3 (da ky 0.30237 -- KHAI theo §17-G5)

tau     legacy/main do duoc   Sheppard du kien tu RIENG z
0.5                -6.50%                  -7.02%
1                  -7.76%                  -8.01%
2                  -8.36%                  -8.50%
3                  -8.52%                  -8.66%
5                  -8.44%                  -8.79%
10                 -8.46%                  -8.89%
20                 -8.10%                  -8.94%
28                 -7.80%                  -8.95%
```

Nhánh legacy thấp hơn nhánh chính **6,5–8,5%**. Nhưng cột phải cho thấy **gần như
toàn bộ** chênh lệch đó được giải thích **chỉ bằng việc z khác nhau**
(`z = 0,30` so với `0,366` — độ trễ nhỏ hơn thì lỗi nhỏ hơn). Phần dư nhỏ và đổi
dấu theo τ.

⚠️ **Không có luật phán quyết nào được ký cho RQ-20R2e**, nên đây **chỉ là mô tả**.
Ghép cặp theo seed (CRN) để tương phản chính xác hơn.

---

## 8. a = 0.5 — MÔ TẢ (nợ 20R2-D6)

```text
tau        rel      band     (band CHUA duoc kiem o a=0.5)
0.5       -35.12%    2.73%
1         -33.34%    3.86%
2         -31.48%    5.45%
3         -29.96%    6.68%
5         -27.65%    8.62%
10        -24.58%    8.62%
20        -22.95%    8.62%
28        -16.74%    8.62%
```

Ở `a = 0.5` mọi τ đều thấp hơn Sheppard rất nhiều (**−35% → −17%**). Điều này
**nhất quán** với H-B và làm nó mạnh hơn: giảm `a` làm `σ_ρ` nhỏ đi, nên tỉ số
`μ/s` của biên **lớn hơn**, và theo Rice hiệu ứng nén đổi dấu **mạnh hơn**.

⚠️ Đây **KHÔNG phải phán quyết**: băng chưa được kiểm ở `a = 0.5` (nợ 20R2-D6).
Băng in ở cột phải chỉ để tham chiếu.

---

## 9. Threats to Validity

```text
LINK DOC LAP     omega_0 = 0 THEO CAU TAO. ar1_matrix sinh 8 AR(1) DOC LAP; do
                 duoc max |r| cheo = 0,023 (n = 200 000, seed 7). Gate 20R2-3'
                 vi the thoa MOT CACH TAM THUONG -- KHONG phai tin tot. Moi ket
                 luan cua 20R2 chi dung CO DIEU KIEN theo gia dinh link doc lap.
                 Tai CHUNG giua cac link (Q7 canh bao) CHUA HE duoc do.
MIEN MO HINH     20R2-L1: ket luan dieu kien theo mien cua bang tra do duoc.
D6               band CHUA kiem o a = 0.5 -> muc 8 chi mo ta.
D2 QUA HAN       GIA TRI MOC cua hai estimand van null, trong khi han la "dien
                 SAU pilot, TRUOC chien dich". KHAI la qua han (§17-D2), khong
                 lang le dien roi coi nhu dung han.
z LECH           bang ky tai z = 0,365, luoi chay 0,366. Khong phan quyet nao lat.
z LEGACY         dung 0,30 (diem luoi) thay 0,30237 (da ky) -- §17-G5.
sigma BAO THU    CRN qua tau -> se_diff that nho hon; sigma la uoc luong THAP.
PILOT XEM TRUOC  §17.0: §17 duoc viet khi pilot da cho xem truoc hinh dang.
                 Chien dich cho ket qua KHAC pilot (3 MISS thay vi 2), nen ban
                 xem truoc khong quyet dinh ket qua.
cbr SUY BIEN     err = 0 tuyet doi -> khong dung lam doi chung duong duoc.
```

---

## 10. Tóm tắt

```text
PRIMARY  5/8 HIT (§17-G2 ba muc)  .  4/8 HIT (doc nguyen van)
         3 MISS: tau = 0,5 . 1 . 2   -- deu THAP hon Sheppard, cung mot huong
SHAPE    PASS  6 DECREASING . 0 INCREASING . 1 UNREADABLE (cap 20-28)  mau so 7
cbr      CO CHE 1 thang tuyet doi (err = 0 o ca 16 to hop) -- SUY BIEN
RQ-20R2e MO TA: legacy thap hon 6,5-8,5%, gan nhu toan bo do z khac nhau
§17-H    H-B dung o CA 8 tau . H-A dung (ti so tang don dieu, cat qua 1 tai ~tau 5)
```

**Việc còn lại trước khi đóng phase:** 20R2.7 (`d_sla`); chiến dịch N3/N4 bằng
`tau_sweep` (nợ D4, ~53 phút) dùng lại khuôn plan/guard/hygiene; đo lại em/A trên
dữ liệu 20R2 để bàn giao 21R2.

