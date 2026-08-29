# 03 — Gate decision Phase D′ (Lesson D.2/D.3)

Ngày phán quyết: 2026-08-29. Bảng dự đoán được khóa trước dữ liệu Cell C tại
tag `phase-D-cellC-start` (commit `adfb7223`).

## Kết quả theo bảng dự đoán đã ký

| Phép đo | H4 dự đoán | H6 dự đoán | Quan sát | Phán xử |
|---|---:|---:|---:|---|
| Cell C `r(uA,uB)` | −.10…+.15 | −.10…+.15 | không diễn giải | `INVALID_RUN` |
| Cell C `r(vC,vD)` | −.10…+.15 | −.10…+.15 | không diễn giải | `INVALID_RUN` |
| Cell C′ `r(uA,uB)` | ≤.08 hoặc ≥.45 | +.18…+.28 | không chạy | dừng đúng PC-C2 |
| Cell C′ `r(vC,vD)` | ≤.08 hoặc ≥.45 | +.18…+.28 | không chạy | dừng đúng PC-C2 |
| Offered, ô then chốt | cao | ≈0 | **+0.0048** | ủng hộ H6 hậu kiểm |

Không điền r của Cell C vào cột quan sát khoa học vì validity gate đã fail
trước bước diễn giải. Các số chẩn đoán vẫn nằm trong artifact để tái kiểm.

## Validity gate Cell C

| Gate | Kết quả |
|---|---|
| prereg commit + tag trước raw run | PASS |
| PC-C1 warm-start/N thực | PASS, edge 74–79 |
| PC-C3 metadata σ/duration/seed | PASS |
| NC-C1 `ac-ad`, `bc-bd` | PASS |
| NC-C2 `uA-vC` | PASS |
| infra 4 cờ false cả 3 rep | PASS |
| counter/completeness | PASS |
| burn thực tế ≥5τ | PASS |
| mọi pair/rep `n_eff>=25` | **FAIL**, 3 pair-rep fail |
| PC-C2 ACF-tau giảm ≥5× | **FAIL**, median chỉ khoảng 1.1× |

Phán quyết Cell C: `INVALID_RUN`. Đây không phải bằng chứng cho H0 và cũng
không được dùng để chọn H4 hay H6.

## Phán quyết giả thuyết

- H1: bị bác ở mức hậu kiểm bởi các cặp core cùng host có r gần 0.
- H2: bị bác ở mức hậu kiểm bởi các cặp low-σ khác host có r gần 0.
- H3: bị chống ở mức hậu kiểm, nhưng duration debt chưa đóng xác nhận.
- H4: **BỊ BÁC ở mức confirmatory bởi PC-C3** (−5.33σ gộp trên `cellA_long`,
  nơi `N_bar=817` và endpoint chung được giữ nguyên vẹn). Phán xử này KHÔNG
  đến từ Cell C — Cell C vẫn invalid và C′ không chạy.
- H6: ứng viên sống sót cùng H0; PC-C3 không có công suất tách hai cái
  (D-L29). Vẫn chưa confirmatory với tư cách một cơ chế.
- H0: không được giữ/loại bằng Cell C invalid.

Lesson D.2 đóng theo ngân sách một vòng với nhãn
`CLOSED_UNRESOLVED_INVALID_VALIDITY`; mở giới hạn D-L18, không ép kết luận.

### Amendment D-A001 — kiểm toán lại chính control PC-C2

Giữ nguyên phán quyết trên. Amendment/tag mới khóa PC-C2′ trước tái phân tích
dữ liệu cũ, chuyển tau control sang `rho_offered` và dùng `nlag=n//4`.

```text
PC-C2′ offered ratio từng edge  4.942 / 7.145 / 4.048 / 2.878
median ratio                    4.495 < 5.0                  FAIL
PC-C2′b Cell A signal fraction  0.3682 (A080 reference 0.3696)
PC-C2′b Cell C                  1/4 edge fit hợp lệ          FAIL
nhãn                            GENERATOR_CONTROL_FAIL_CELL_C_REMAINS_INVALID
```

Do đó Cell C **không** được tái phân xử thành VALID và A001 không cho phép đọc
r đóng băng như outcome confirmatory. Audit vẫn chứng minh PC-C2 measured cũ
sai loại đại lượng; control mới MISS magnitude đã ký, có thể do finite trace
120 s/censoring ACF nhưng không được sửa hậu nghiệm. Xem
`05-pc-c2-prime-readjudication.md`, D-L18 và D-L19.

### Amendment D-A002 — nhánh baseline đủ dài, control generator ĐẠT

Giữ nguyên hai phán quyết trên. A002 chẩn đoán PC-C2′ MISS là bias estimator
chứ không phải generator, rồi ký PC-C2″ tại tag `phase-D-pc-c2-second-start`
(commit `124c99f6`) trước khi thu `cellA_long` — 1 run 1505 s, seed 41,
`core 0.10 / edge 0.03`, `T/tau = 68.6`.

```text
PC-C2''a offered ratio tung edge  8.361 / 11.211 / 7.012 / 6.804
median ratio                      7.687 >= 5.0                    PASS
                                  (ca 4 edge deu vuot, min 6.80)
PC-C2''b sf_A                     1.000 (cham tran)  nguong <=0.50 FAIL
PC-C2''b sf_C                     0.9468             nguong >=0.75 dat
PC-C2''b fit hop le cell C        2/4 edge (A001: 1/4)             FAIL
nhan                              REANALYSIS_INVALID_OR_INCOMPLETE
```

Hai hệ quả tách bạch:

1. **Control generator ĐẠT.** `4.495` của A001 là artifact đo. Mô phỏng một
   generator hoàn hảo dưới chính estimator PC-C2′ chỉ trả `3.635`, tức ngưỡng
   `5.0` là bất khả thi về mặt xây dựng ở A001; dưới PC-C2″ nó trả `10.006`.
   S19 (`tau ~ 1/sigma^2`) **không** bị bác. Đóng D-L18/D-L19/D-L21, và đóng
   duration debt D-L10/D-L15 cho cấu hình A.
2. **Cell C vẫn `INVALID_RUN`.** PC-C2″b FAIL, nên `may_read_frozen_outcomes`
   vẫn `false` và `r` đóng băng của Cell C chưa từng được đọc. Nguyên nhân
   FAIL là lỗi đặc tả của chính PC-C2″ (D-L26), không phải dữ liệu. Ngân sách
   hết; không có vòng 3.

Phát hiện hậu kiểm quan trọng nhất của vòng này: nugget `0.3696` của phase-23
**không** do trace ngắn và **không** do generator — cắt chính `cellA_long`
thành cửa sổ 120 s vẫn cho `sf = 0.9405` trong khi phase-23 cùng `T = 120 s`
cho `0.3682`. Nugget đi kèm bundle instrumentation `ditto + AoI probe + cycle
trace + reconcile_every=1`. Điều này ủng hộ H6 mạnh hơn và định vị nguồn nhiễu
ở đường đo, nhưng bác dạng định lượng `sf = sigma^2/(sigma^2+v)`. Xem D-L25 và
`06-pc-c2-second-readjudication.md` mục 6. H6 vẫn là **hậu kiểm**.

### PC-C3 — thí nghiệm phân biệt thật sự, và H4 bị bác

> **Trùng tên, phải phân biệt:** `PC-C3` trong bảng validity Cell C ở trên là
> đối chứng *metadata* (`σ`/duration/seed) của prereg `00-preregistration.md`.
> `PC-C3` dưới đây là phép phân tích thứ cấp của `00c-prereg-pc-c3.md`. Trong
> tài liệu mới, đối chứng metadata được gọi là `PC-C3m`.

`cellA_long` giữ `sigma_edge=0.03` nên `N_bar=817` và endpoint `hsrc` chung
**nguyên vẹn** so với campaign phase-23; chỉ bundle telemetry đổi. Đó là thí
nghiệm đổi đúng một biến mà Cell C không bao giờ là được — vì `sigma` của Cell
C điều khiển đồng thời `N_bar` (biến H4) và nugget (biến H6).

Ký tại tag `phase-D-pc-c3-start` (commit `7f486a28`), trước khi bất kỳ hệ số
tương quan nào được tính trên `cellA_long`; khẳng định đó được kiểm bằng audit
code/artifact, ghi ở `00c-prereg-pc-c3.md` mục 0.

```text
                 phase-23 (bundle BAT)   cellA_long (bundle TAT)
uA-uB                 +0.5986                  +0.1755    n_eff 40.81
vC-vD                 +0.6376                  -0.0166    n_eff 40.90
o then chot 2x2       +0.6181                  +0.0795
ti so o then chot/ke tiep  9.893x                4.341x

vs du doan diem H4 (r=0.60):  uA-uB -3.17s   vC-vD -4.37s   gop -5.33s   BAC
vs H6 (0.13) va H0 (0):       khong ban nhan nao bac
nhan tu dong:                 PRIMARY_REPLICATES_DISAGREE  (band H6 / band H0)
```

Cả 8 mục validity gate PASS — **lần đầu tiên trong Phase D′** một phép đo
correlation đi trọn vẹn qua gate: `n_eff` 40.8/40.9 ≥ 25, burn-in 87 s ≥ 5τ,
NC-C1/NC-C2/NC-C3 đạt, infra 4 cờ false, 0 dòng rơi.

Phán quyết giả thuyết được cập nhật:

- **H4 (endpoint × N_bar): BỊ BÁC ở mức confirmatory**, −5.33σ gộp. Đây là
  phán xử confirmatory đầu tiên của Lesson D.2.
- **H6 và H0: không phân xử được với nhau.** PC-C3 được ký với đúng phạm vi
  đó; thiếu công suất là điều đã ghi trước (D-L29), không phải phát hiện sau.
- Nhãn `PRIMARY_REPLICATES_DISAGREE` là artifact vạch band: hai bản nhân nhất
  quán với nhau ở `0.84σ`, và **cả hai** đều thuộc tập bác H4. Lỗ hổng đặc tả
  của chính PC-C3, ghi `D-L30`, không sửa nhãn hậu nghiệm.
- Cell C **không đổi**: `INVALID_RUN`, outcome đóng băng chưa từng được đọc.

Xem `07-pc-c3-adjudication.md`.

## D.3 / L141

PC `cbr < poisson < h2` đạt và NC poisson tái tạo bit-exact. Đọc theo hai lớp:
D3 budget band không đổi trên `{cbr,poisson,h2}`; highest-SNR cell đổi từ
`clean@0.960` sang `clean@0.700` chỉ dưới cbr. Vì vậy:

```text
T6 decision band D3             ROBUST — ĐÓNG
highest cell, full grid         FRAGILE
highest cell, poisson+h2        ROBUST CÓ ĐIỀU KIỆN — clean@0.960
L141                            ĐÓNG MỘT PHẦN
```

Palm–Khintchine là theory prior đã ghi trước sweep
(`results/SMOKE/phase-D/family_sensitivity.json::theory_prior`) và ưu tiên
Poisson cho nhiều flow độc lập chồng chập: chồng chập `N_bar` in `[95,875]`
luồng gần độc lập hội tụ về Poisson, còn cbr (`c_a=0`) là chế độ tất định chỉ
giữ được khi số nguồn chồng chập rất nhỏ. Đây là lý do **tiên nghiệm** để hạ
trọng số cbr, nên trên dải vật lý khả dĩ `{poisson,h2}` kết luận highest-cell
`clean@0.960` là ROBUST và dùng được. Nó **không** cho phép tuyên bố cbr bất
khả thi khi independence chưa đo trực tiếp; L141 vì vậy chỉ còn mở cho các
khẳng định cell-selection không loại được cbr bằng lý lẽ độc lập, và cho onoff
vì onoff chỉ có key `6|13`.

## D-9 và hệ quả Phase 24

Trust gate p99 `0.222126 ms < 10 ms`: PASS. Với chu kỳ hiện hành 500 ms,
overhead là 0.0444%, đạt ngưỡng an toàn `<5%`; nhánh tối ưu chưa cần mở.
Nếu chạy trên critical path, gate tự cộng khoảng 0.222126 ms vào AoI z theo
mỗi quyết định. Chưa có phép đo dưới tải (D-L17).

## Hệ quả cho Phase G/23.26

- Không được đặt edge/core σ khác nhau như một lựa chọn vô hại: offered audit
  cho thấy chênh σ có thể tạo measurement artifact common-mode.
- Nếu vẫn dùng `rho_measured`, cần thêm `counter_read_dt`/common-mode
  instrumentation hoặc estimator hiệu chỉnh trước claim coupling.
- Mỗi campaign vẫn phải budget theo `55*tau` của chính đại lượng/gate đã chọn.
- Không dùng Cell C invalid để điều tra ghép nối endpoint như cơ chế đã xác nhận.
- Traffic family phải là trục sensitivity; không thay bằng scalar `c_a`.

## Gate Phase D′

```text
D.0 custody/DOI                 FAIL/BLOCKED (DOI còn null)
D.2 confirmatory validity       PARTIAL (Cell C van INVALID_RUN va
                                A002 PC-C2''b MISS; NHUNG PC-C3 di tron
                                validity gate va BAC H4 confirmatory)
D.3 family sensitivity          PARTIAL (band đóng; selection có điều kiện,
                                dùng được trên {poisson,h2} theo theory prior)
D-9 trust-gate latency          PASS
OVERALL PHASE D′                FAIL
```

So với bản trước A002, `D.2` đổi từ FAIL sang PARTIAL: không còn nghi ngờ
generator không nhận `sigma` (PC-C2″a PASS), và Lesson D.2 nay **có** một phán
xử confirmatory — H4 bị bác bởi PC-C3, đi trọn validity gate. Phần còn nợ là
outcome validity của Cell C, lỗi đặc tả ngưỡng của PC-C2″, và việc tách H6
khỏi H0 (D-L29) cùng tách bốn yếu tố của bundle (D-L28) — cả hai thuộc Phase G.

`OVERALL PHASE D′` vẫn **FAIL** vì D.0 custody/DOI còn BLOCKED. Kết quả khoa
học không đổi được gate custody.

Năm mục ngoài máy là **BLOCKED, không phải SKIPPED**; xem
`04-execution-report.md`. Không được tuyên bố Gate D′ PASS trước khi Version
DOI tồn tại và các debt validity trên được xử lý.
