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
- H4: chưa phân xử xác nhận; Cell C invalid và C′ không chạy.
- H6: được ủng hộ mạnh bởi offered key cell `+0.0048` so với measured
  `+0.6181`, nhưng nhãn vẫn là hậu kiểm, không confirmatory.
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
D.2 confirmatory validity       FAIL (Cell C INVALID_RUN; n_eff debt cũ;
                                A002 PC-C2''b MISS -- nhung generator
                                control PC-C2''a nay PASS 7.687)
D.3 family sensitivity          PARTIAL (band đóng; selection có điều kiện,
                                dùng được trên {poisson,h2} theo theory prior)
D-9 trust-gate latency          PASS
OVERALL PHASE D′                FAIL
```

So với bản trước A002, `D.2` vẫn FAIL nhưng **lý do đã đổi**: không còn nghi
ngờ generator không nhận `sigma`; phần còn nợ là outcome validity của Cell C
và một lỗi đặc tả ngưỡng của chính PC-C2″.

Năm mục ngoài máy là **BLOCKED, không phải SKIPPED**; xem
`04-execution-report.md`. Không được tuyên bố Gate D′ PASS trước khi Version
DOI tồn tại và các debt validity trên được xử lý.
