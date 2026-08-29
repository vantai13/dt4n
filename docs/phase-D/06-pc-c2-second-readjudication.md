# 06 — Tái phân xử PC-C2″ theo Amendment D-A002

```text
Prereg          docs/phase-D/00b-prereg-pc-c2-second.md
Tag             phase-D-pc-c2-second-start  tại commit 124c99f6
Ký lúc          2026-08-29 03:3x UTC, TRƯỚC byte raw đầu tiên của cellA_long
Dữ liệu mới     1 run Mininet, 1505 s, seed 41 (03:37:57 → 04:03:11 UTC)
Artifact        results/SMOKE/phase-D/pc_c2_second.json
```

Phán quyết `INVALID_RUN` của Cell C trong `03-gate-decision.md` và nhãn A001
không bị xóa hay sửa ngược.

## 1. Run mới — validity đầu vào

| Kiểm tra | Kết quả |
|---|---|
| prereg + tool commit và tag trước raw | PASS, `124c99f6` lúc 03:3x, raw đầu tiên 03:38 |
| runner exit code | PASS, `rc=0` |
| PC-C3 metadata (`σ`, duration, seed) | PASS: `core 0.10 / edge 0.03 / 1505.0 s / seed 41` |
| PC-C1 warm-start `= round(ρ²/σ²)` | PASS 4/4: `817 / 856 / 817 / 875` khớp chính xác |
| infra 4 cờ CPU/swap/drop/clock | PASS, cả bốn `false` (cpu p95 14.2%, swap 0, drop 0, jump 1.96 ms) |
| completeness | PASS: offered 1 204 000 dòng, measured 7 524 mẫu |

Infra summary: `results/SMOKE/phase-D/infra_cellA_long_summary.json`.

## 2. PC-C2″a — tau trên `rho_offered` — **PASS**

`nlag = min(n//4, 50000)`; nhánh A `L = 376.2 s`, nhánh C `L = 60.0 s`.

| Edge | tau A_long (s) | median tau C (s) | A/C |
|---|---:|---:|---:|
| uA | 15.8215 | 1.8923 | 8.3610 |
| uB | 21.9372 | 1.9567 | 11.2111 |
| vC | 18.9321 | 2.6999 | 7.0121 |
| vD | 17.8521 | 2.6238 | 6.8037 |

```text
median bon ratio = 7.6865   >=  nguong da ky 5.0        PC-C2''a = PASS
T/tau nhanh A    = 68.6     >=  san 50                  budget OK
T/tau nhanh C    = 88.9     >=  san 50                  budget OK
```

Cả **bốn** edge đều vượt ngưỡng riêng lẻ (thấp nhất `vD = 6.80`), không phải
chỉ median. So với A001 thì mọi ratio đều tăng: `4.942→8.361`, `7.145→11.211`,
`4.048→7.012`, `2.878→6.804`.

Chẩn đoán A002 được xác nhận: **`4.495` của PC-C2′ là artifact đo, không phải
generator hỏng.** S19 (`tau ~ 1/sigma^2`) **không** bị bác; dự đoán lý thuyết
`11.11×` nằm trong dải bốn ratio quan sát.

Ba đường độc lập cùng chỉ một hướng:

```text
du doan dai so A002 (1.4)                     ~10.9x
mo phong generator HOAN HAO (A002 1.7)         10.006x
quan sat PC-C2''a                               7.687x   (min edge 6.80)
```

Quan sát thấp hơn mô phỏng ~24%: phần dư là do ACF offered thật có đuôi không
đúng hàm mũ AR(1), nên `tau_hat_A` vẫn hụt nhẹ. Hướng của phần dư là **chống
lại** PASS, tức PASS đạt được bất chấp phần bias còn lại.

## 3. PC-C2″b — signal fraction — **FAIL**

```text
nguong da ky:  sf_A <= 0.50  VA  sf_C >= 0.75  VA  ca 8 edge fit hop le
quan sat:      sf_A  = 1.000 (cham tran)      -> VI PHAM nguong sf_A
               sf_C  = 0.9468                 -> dat nguong sf_C
               cell C: 2/4 edge hop le (uA, uB co intercept/se = 4.89, 5.59)
PC-C2''b = FAIL
```

Rule miền giá trị mới có tác dụng đúng như thiết kế: `vD` Cell C từ INVALID
dưới A001 (`raw = 1.0040`) thành **valid, `at_ceiling = true`, `sf = 1.000`**
— đúng là `sf = 1.000 ± noise` như A002 §2.2 dự đoán. Số edge Cell C hợp lệ
tăng từ 1/4 lên 2/4. [D-L23 đóng một phần]

### 3.1 Vì sao FAIL — và đây là lỗi của chính prereg này

Ngưỡng `sf_A <= 0.50` và dự đoán `sf_A ~ 0.37` được thừa kế từ reference A080
đo trên campaign phase-23. Nhưng mục 1.1 của chính prereg này đã **cố ý đổi
cấu hình nhánh A**: `cellA_long` chạy `ditto=False`, không AoI probe, không
cycle trace, `reconcile_every=30` — sao chép runner của Cell C để contrast
`A ↔ C` chỉ còn một biến `σ`.

Việc đó đúng cho PC-C2″a và là lý do PC-C2″a PASS. Nhưng nó **cũng đổi luôn
đại lượng mà PC-C2″b đo trên nhánh A**, và ngưỡng `sf_A <= 0.50` đã không
được ký lại theo cấu hình mới. Đây là **cùng một lớp lỗi với D-L22**, lần này
do chính prereg PC-C2″ gây ra: ký ngưỡng trên một nhánh sau khi đã đổi cấu
hình nhánh đó, mà không kiểm lại dự đoán còn áp dụng không. [D-L26]

Không hạ ngưỡng, không sửa hậu nghiệm. FAIL đứng nguyên.

## 4. Phán quyết A002

Partition ký trước cho hàng “dữ liệu/infra/fit invalid” ưu tiên trước hàng
“PASS/FAIL”, và tool đã khóa thứ tự đó trước khi có dữ liệu:

```text
GENERATOR_CONTROL:              PASS  (PC-C2''a = 7.687 >= 5.0)
SIGNAL_FRACTION_CONTROL:        FAIL  (sf_A cham tran; 2/4 edge C hop le)
nhan tu dong:                   REANALYSIS_INVALID_OR_INCOMPLETE
cell_C_readjudicated_valid:     false
may_read_frozen_outcomes_under_A002: false
S19_refuted:                    false
```

**Cell C vẫn `INVALID_RUN`.** `r` đóng băng của Cell C không được đọc, không
được trích dẫn, không được dùng làm outcome. Không có vòng 3 — ngân sách đã
ghi “hết sau vòng này”.

Ghi nhận một nhập nhằng của bảng partition: khi PC-C2″b FAIL **vì** fit
invalid thì cả hàng 3 (`NUGGET_MODEL_MISS...`) và hàng 4
(`REANALYSIS_INVALID_OR_INCOMPLETE`) đều khớp. Tool đã khóa ưu tiên hàng 4
trước khi chạy, cùng thứ tự với A001. Hệ quả thực tế của hai nhãn là **giống
hệt nhau**: Cell C không được tái phân xử.

## 5. Điều PC-C2″ **đóng được**

- `D-L18`/`D-L21` chuyển từ mở sang **đóng về mặt chẩn đoán**: control phía
  generator đạt khi nhánh baseline đủ dài. `4.495` là bias estimator.
- `D-L19` đóng: `nlag` không còn là ràng buộc; `cut_at_ceiling` không xảy ra ở
  bất kỳ edge nào trong PC-C2″a.
- `D-L15`/`D-L10` (duration debt của cấu hình A) **đóng**: đã tồn tại một run
  1505 s ở `core 0.10 / edge 0.03` với `T/tau = 68.6`.
- `D-L4` (“không có trace dài trong working tree”) đóng một phần: nay có một
  trace 1505 s, tuy chưa phải 1800 s của scaling test.

## 6. Phát hiện ngoài dự kiến — nguồn gốc của nugget

Đây là **hậu kiểm**, không phải control đã ký. Artifact:
`results/SMOKE/phase-D/nugget_origin.json`.

Cùng `sigma_edge = 0.03`, cùng estimator A080 (`FIT_LAGS 1..20`):

| Trace | σ_edge | T | ditto/probe | ACF(0.2 s) | sf (A080) |
|---|---:|---:|:---:|---:|---:|
| phase-23 cell A | 0.03 | 120 s | **BẬT**, `reconcile_every=1` | 0.418 | **0.3682** |
| cellA_long | 0.03 | 1505 s | tắt | 0.858 | **0.8638** |
| cell C | 0.10 | 240 s | tắt | 0.901 | 1.0922 |

Nugget biên sụp từ `λ = 0.632` xuống `λ = 0.136` khi tắt instrumentation
bundle. Giả thuyết “do trace ngắn” bị **bác trực tiếp** bằng đối chứng không
cần dữ liệu mới — cắt chính `cellA_long` thành cửa sổ ngắn:

```text
cua so 120 s  x12   sf = 0.9405        (phase-23 cung T=120 s cho 0.3682)
cua so 240 s  x6    sf = 0.9434
cua so 400 s  x3    sf = 0.9377
cua so 750 s  x2    sf = 0.9394
```

`sf` gần như **không phụ thuộc độ dài cửa sổ**. Vậy `0.3682` của phase-23
không đến từ `T = 120 s`.

Hệ quả — phải phát biểu thận trọng:

- Nugget lớn của phase-23 **không** do generator và **không** do trace ngắn.
  Nó đi kèm **bundle instrumentation** `ditto + AoI probe + cycle trace +
  reconcile_every=1`. Bốn thứ đó đổi đồng thời nên **không tách được** cái
  nào gây ra; đây là confound có chủ đích của thiết kế này. [D-L25]
- Điều này **ủng hộ** H6 (shared measurement noise) ở mức mạnh hơn trước, và
  còn định vị nguồn: nhiễu đến từ đường đo/đồng bộ, không từ traffic.
- Nhưng nó **bác** dạng định lượng `sf(sigma) = sigma^2/(sigma^2+v)` đã hiệu
  chuẩn ở A002 §2.4. Với ditto tắt, `sf` đi từ `0.864` (σ=0.03) tới `1.092`
  (σ=0.10) — phụ thuộc σ yếu, không phải `0.37 → 1.0`. Tham số `v = 0.0015457`
  chỉ mô tả chế độ **ditto bật**. Không được dùng nó như hằng số vật lý.
- `D-L20` được **làm sắc** chứ không đóng: `r` trên `rho_measured` của
  phase-23 bị common-mode chi phối, và biên độ common-mode do cấu hình đo
  quyết định. Con số `+0.5986` gắn với cấu hình phase-23, không phải với
  topology.

**Không** dùng mục này để tái phân xử Cell C hay để nâng H6 lên confirmatory.
Nó là thiết kế cho Phase G: chạy 2×2 `{ditto on/off} × {σ_edge 0.03/0.10}` và
tách bundle thành từng trục.

## 7. Ngân sách

Hết. Không vòng 3 dưới A002. H6 chuyển sang Phase G như giả thuyết hậu kiểm
dẫn đầu, kèm thiết kế ở mục 6.
