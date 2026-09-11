# 20R2 — Phán quyết đóng phase

Ngày: 2026-09-11 UTC. Tag: `phase-20R2-closed`.
Trạng thái: **`CONFIRMED_WITH_A_HETEROGENEOUS_POPULATION`**.

20R2 đo được đường cong `err(z, τ)` trên một trục AoI **đã ký trước**, với một
chiến dịch 167 lệnh có sổ cái, vệ sinh 9/9, và một bộ chấm đóng băng trước khi mở
hộp. Dự đoán có hướng **đạt 5/8**.

Nhưng **kết quả có giá trị nhất không phải con số 5/8.** Đó là: **quần thể 8 ô
"gate" — vốn được ký như một quần thể đồng nhất — thực ra phân hoá gần 300 lần**,
và **toàn bộ 3 MISS phụ thuộc MỘT ô** mà T2 đã cấm dùng làm headline từ trước.
Số gộp che điều đó, và không có cơ chế nào trong quy trình bắt được nó cho tới khi
mở hộp.

---

## 1. Câu hỏi nghiên cứu và phán quyết

| RQ | Câu hỏi | Phán quyết | Bằng chứng |
|---|---|---|---|
| RQ-20R2a | Twin sai quyết định bao nhiêu theo tuổi `z`? | **ĐO ĐƯỢC**, 8 τ × 13 z × 8 ô × 2 a × 5 seed. Đơn điệu giảm theo τ, 6/7 cặp đọc được | `06-adjudication.json`; hygiene 9/9 |
| RQ-20R2b | Sai đó **giá** bao nhiêu? | **CHỈ ĐO ĐƯỢC Ở 3/16 TỔ HỢP.** 13/16 có `d_sla` = 0 **theo cấu trúc** trên trục exogenous | `07a-dsla-structure.json`; `07-dsla.json` |
| RQ-20R2c | `err` biến thiên thế nào theo `τ`? | **ĐƠN ĐIỆU GIẢM**, 6/7 cặp `DECREASING`, 1 cặp `UNREADABLE` (τ 20→28, σ = 2,53) | `06-adjudication.json` SHAPE |
| RQ-20R2d | Twin có khớp Sheppard? | **5/8 HIT** (ba mức) / **4/8** (đọc nguyên văn). 3 MISS ở τ ≤ 2, đều THẤP hơn Sheppard | `06-adjudication.json` PRIMARY |
| RQ-20R2e | Kết quả điều kiện theo **trục nào**? | **TRỐNG THEO CẤU TẠO** — không phải "gần như trống" | `06-adjudication.md` §7 |

---

## 2. Kết quả chính — viết thẳng

```text
PRIMARY (RQ-20R2d)  5/8 HIT ba muc . 4/8 doc nguyen van . mau so 8 CO DINH
  AT_OR_ABOVE 4 . BELOW_WITHIN_BAND 1 . BELOW_BEYOND_BAND 3
  3 MISS: tau = 0,5 (-10,38%) . 1 (-7,66%) . 2 (-6,16%) -- deu THAP hon Sheppard

SHAPE (RQ-20R2c)    PASS. 6 DECREASING . 0 INCREASING . 1 UNREADABLE . mau so 7

d_sla (RQ-20R2b)    S0 PASS (0/10400 hang vi pham) . S1 PASS 96/96 . S2 PASS 24/24

G4 holdout          PASS 7/8 -- nhung THAT la 5/6 o rui ro that (san tuyet doi)
```

**Mẫu số khai trước khi đọc** (§12.2 `DENOMINATOR`, §17-G4); không đổi mẫu số,
không đổi ngưỡng sau khi thấy số. Cả 3 MISS được giữ nguyên trong báo cáo.

### 2.1 ★ Phát hiện quan trọng hơn cả 5/8

```text
ti so err_total/Sheppard theo TUNG o, tai z = 0,366:
  poisson@0.850  1,414 -> 1,655        h2@0.925   0,334 -> 0,406
  h2@0.700       1,277 -> 1,557        h2@0.960   0,006 -> 0,027
  ...
  bien do phan hoa: 0,006 ... 1,655  -- chenh GAN 300 LAN

ba cach tong hop, ba buc tranh:
  gop 8 o (DA KY)          0,896 ... 1,099   -> 3 MISS
  trung vi 8 o             1,017 ... 1,342   -> 0 MISS
  gop 7 (chi bo h2@0.960)  1,023 ... 1,252   -> 0 MISS
```

**Toàn bộ 3 MISS phụ thuộc MỘT ô: `h2@0.960`** — nơi quyết định gần như khoá cứng
(một đường là `argmin` **100%** thời gian, `m` = 3,11, Rice `e^(−m²/2)` = 0,008).
Và ô đó thuộc diện **T2-R7 đã cấm dùng làm headline** từ 2026-09-08.

⚠️ **Phán quyết GIỮ NGUYÊN 5/8.** Đổi quần thể bây giờ — kể cả sang một luật có
sẵn từ trước — vẫn là đổi estimand **sau khi thấy dữ liệu**. Độ nhạy theo R7 đứng
**cạnh** phán quyết, không thay thế nó.

### 2.2 Cơ chế: cấu trúc cạnh tranh, không phải mức tải

Đã chuyển từ **thăm dò** sang **khẳng định** qua một holdout ở **điều kiện mới**
(a = 0.5), không phải seed mới:

```text
G4 (Gauss 4 hanh dong, KHONG tham so khop) du doan err_stale/Sheppard
  h2@0.850: a=0,9 do duoc 1,146  ->  G4 du doan a=0,5 = 0,635  ->  THUC DO 0,623
  Mot dao chieu 45% du doan dung trong 1,8%, o dieu kien mo hinh CHUA TUNG THAY.
```

Và ngược với trực giác: **`err_total` của `h2@0.960` chỉ 0,14–0,19%**, trong khi
prereg dòng 802 viết *"ở chế độ khó thật (h2@0.960) có thể là 20%"* — **lệch hai
bậc độ lớn**. Tải càng nặng thì **một** đường càng áp đảo, nên quyết định càng ít
lật. ⇒ **Twin cũ nguy hiểm nhất ở tải VỪA**, nơi 3–4 đường gần hoà nhau.

### 2.3 `Δ_cond` — giá của một lần sai, và nó giảm theo τ

```text
poisson@0.850, a = 0,9, tu tau = 0,5 den tau = 28:
  ti le sai        err_total   0,4806 -> 0,0849    giam  5,66x
  gia moi lan sai  Delta_cond  0,385  -> 0,064     giam  6,02x
  tac hai SLA      d_sla       0,1849 -> 0,0054    giam 34,10x  = 5,66 x 6,02
```

Hai yếu tố **nhân với nhau** ⇒ tác hại SLA của độ cũ **tập trung siêu tuyến tính**
ở τ ngắn. Đọc `err` một mình sẽ **đánh giá thấp** mức tập trung đó.

---

## 3. Đóng góp về PHƯƠNG PHÁP (giá trị lâu hơn các con số)

```text
1. HAN CHE KE THUA ROI IM LANG -- doi ngau cua "mac dinh im lang"
   mac dinh im lang   = mot GIA TRI ke thua ma khong ai khai   (da bat 5 lan)
   han che roi im lang = mot RANG BUOC DA KY bi MAT khi sang phase moi
   Loai thu hai CHUA TUNG co cong cu nao bat. T2-R7 roi im lang qua ranh gioi
   phase, va no quyet dinh toan bo 3 MISS.
   => docs/inherited_restrictions.json + test_inherited_restrictions.py:
      prereg phase moi PHAI tra loi TUNG han che (ACCEPT / OVERRIDE + ly do).

2. DOI CHUNG DUNG CU phai chay QUA duong ong that
   NC1b cu so c_true.argmin voi CHINH no -- MENH DE LUON DUNG, va khong goi
   run_cell. Test canh no chi kiem MOT CAU VAN co trong docstring.
   Kill test: doi chung moi bat loi lech-mot (0,0263), NC1b mu (0,0).
   => perfect_twin_control + DOI CHUNG CUA DOI CHUNG (phai ton tai z>0 co err>0).

3. SEVERITY -- phep thu phai CO KHA NANG truot
   Hai dung sai de xuat ban dau: mot cai KHONG THE truot, mot cai DA TRUOT san
   tren du lieu kham pha. Ca hai bi loai TRUOC khi chay.
   Holdout o DIEU KIEN MOI (a=0.5) manh hon seed moi, vi m va so duong song la
   tinh chat cua O chu khong cua SEED.

4. DO DUOC != MANG THONG TIN
   13/16 to hop gate co d_sla = 0 THEO CAU TRUC. Biet duoc dieu do TRUOC khi mo
   mot cot nao, chi tu moi truong, 0 phut CPU.

5. BA GIA TRI, khong hai
   AT_OR_ABOVE / BELOW_WITHIN_BAND / BELOW_BEYOND_BAND; DECREASING / INCREASING /
   UNREADABLE; DEGENERATE / WEAK / INFORMATIVE. Lam phang logic ba gia tri thanh
   hai la cho su that bi giau.

6. SO CAI la nguon su that (write-ahead log)
   parquet khong co dong so = MO COI -> xoa, chay lai. Runner T2 bo qua moi file
   "> 0 byte", ma mot parquet cat cut do mat dien cung > 0 byte.
```

---

## 4. Sổ giới hạn — đọc trước khi trích bất kỳ số nào

```text
G1  omega_0 = 0 THEO CAU TAO (8 AR(1) DOC LAP, max |r| cheo = 0,023). Gate 20R2-3'
    thoa MOT CACH TAM THUONG. Moi ket luan dieu kien theo gia dinh link doc lap;
    tai CHUNG giua cac link CHUA HE duoc do.  => uu tien cao nhat cho 21R2.
G2  T2-R7: 2 o rho_bar = 0.96 KHONG duoc lam headline. Toan bo 3 MISS phu thuoc
    mot trong hai o do.
G3  Quan the phan hoa ~300 lan. So GOP khong dai dien cho o nao.
G4  d_sla MU o 13/16 to hop tren truc exogenous. Mot luoi SLA khac se cho phan
    hoach KHAC HAN va cac ket luan nay KHONG chuyen sang duoc.
G5  Bang chap nhan CHUA kiem o a = 0.5 (D6). Moi so a=0.5 chi MO TA.
G6  G4 duoc CHON giua BA mo hinh tren du lieu kham pha (§19.2). Holdout lam nhe,
    KHONG xoa loi re do. Va G4 sai HE THONG o poisson@0.700 (D9).
G7  Pilot da cho XEM TRUOC hinh dang ket qua truoc khi §17 duoc viet (§17.0).
    Chien dich lap lai pilot rat sat (tau=2 lech 0,65 sigma).
G8  Bang em/A cua §13.5 la so KE THUA tu T2, o estimand KHAC (margin/cost_ms cua
    cert.tau_sweep). KHONG duoc doc nhu do tren 20R2. Xem 08-handoff muc 2.
```

---

## 5. Nợ chuyển ra

`20R2-D2` (quá hạn) · `D4` (N3/N4, cần `cert.tau_sweep`) · `D5` (cbr@0.850 em/A,
cùng estimand với D4) · `D6` (băng ở a=0.5) · **`D9`** (G4 sai hệ thống ở
`poisson@0.700`) · **`D10`** (2/8 ô của phép thử G4 gần như không thể trượt).

Chi tiết và lý do từng cái: `08-handoff-21R2.md` mục 4.

---

## 6. Câu Threats-to-Validity viết sẵn cho luận văn

> Mọi kết quả của 20R2 điều kiện theo giả định **các link độc lập**: harness sinh
> 8 chuỗi AR(1) độc lập (đo được: hệ số tương quan chéo lớn nhất 0,023), nên cổng
> `20R2-3′` được thoả một cách **tầm thường** và tải tương quan chung giữa các
> link **chưa hề được đo**. Trong phạm vi đó, dự đoán có hướng `err ≥ Sheppard`
> đạt **5/8** τ trên quần thể 8 ô đã ký; ba lần trượt đều ở τ ≤ 2 và đều theo
> **một** hướng (err thấp hơn Sheppard). Quần thể này **không đồng nhất**: tỉ số
> `err/Sheppard` theo từng ô trải từ 0,006 đến 1,655, và cả ba lần trượt phụ thuộc
> **một** ô (`h2@0.960`) vốn đã được T2 đánh dấu ngoại suy và **cấm dùng làm
> headline**. Trung vị các ô, và quần thể loại theo luật T2-R7, đều nằm **trên**
> đường Sheppard ở cả 8 τ. Một mô hình Gauss bốn hành động **không khớp tham số**
> dự đoán được tỉ số này ở một **điều kiện chưa từng thấy** (a = 0.5) với 7/8 ô
> trong dung sai đã dẫn xuất trước, cho thấy đại lượng điều khiển độ nhạy quyết
> định là **cấu trúc cạnh tranh giữa các đường**, không phải mức tải.

---

## 7. Điều kiện mở lại

```text
MO LAI phan quyet 5/8 neu:
  - phat hien loi trong bo cham DA DONG BANG (tag phase-20R2-adjudicator-frozen)
    -> amendment + tag moi + GIU CA HAI artifact
  - phat hien sha parquet lech so cai -> bang chung bi sua, DUNG toan bo
KHONG mo lai chi vi:
  - khong thich con so 5/8
  - muon doi quan the sang 6 o (do la doi estimand SAU khi thay du lieu)

VIEC PHAI LAM TRUOC khi 21R2 trich bat ky so nao:
  1. doc docs/inherited_restrictions.json va tra loi TUNG han che trong prereg moi
  2. doc 08-handoff-21R2.md muc 2 (bay estimand rms_e_model) truoc khi dung em/A
  3. bang theo TUNG O la BAT BUOC, dung canh moi so gop
```

---

## 8. Dấu vết

```text
phase-20R2-prereg-signed        a92f062d   ky gate 0-3 + §16
phase-20R2-campaign-hygiene     82be66d7   167/167 lenh, ve sinh 9/9
phase-20R2-adjudicator-frozen   f294a43c   bo cham dong bang TRUOC khi mo
phase-20R2-g4-frozen            c20850b0   du doan G4 dong bang
phase-20R2-g4-frozen-a1         84ba0af0   amendment a1 (co --score, khong doi so)
phase-20R2-dsla-frozen          79de5a01   §20 khoa TRUOC khi mo d_sla
phase-20R2-closed               (commit nay)
```
