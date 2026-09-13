# 20R2-E1 — Đính chính (ERRATUM)

Ngày: 2026-09-13 UTC. Tag đóng đính chính: `phase-20R2-erratum-1`.
Loại: **ERRATUM**. Văn bản gốc `99-gate-decision.md`, tag
`phase-20R2-closed`, commit `042c58f4`, vẫn có hiệu lực và giữ nguyên bytes.

## 0. Phán quyết giữ nguyên và bằng chứng kiểm tra

| Nội dung | Phán quyết đã đóng, giữ nguyên |
|---|---|
| PRIMARY — RQ-20R2d | 5/8 HIT ba mức; 4/8 nếu đọc nguyên văn; mẫu số 8 |
| SHAPE — RQ-20R2c | 6 DECREASING, 1 UNREADABLE; mẫu số 7 |
| d_sla — RQ-20R2b | S0/S1/S2 PASS |
| G4 holdout | 7/8; tương ứng 5/6 ô có rủi ro thật |

Hai điều kiện mở lại ở `99-gate-decision.md` §7 được kiểm tra như sau:

- **Lệch hash sổ cái:** tính lại SHA256 của 167 parquet và 167 sidecar theo
  `04-campaign-log.jsonl`: **334/334 khớp, `bad = []`**. Đây là kiểm lại trên
  đĩa, không chỉ chép kết quả H3 cũ.
- **Lỗi bộ chấm:** nội dung `tools/20r2_6_adjudicate.py` trùng tag
  `phase-20R2-adjudicator-frozen` (`f294a43c`). Chạy lại các test bộ chấm có
  đối chứng nhân tạo, cùng test d_sla và hợp đồng estimand. Chi tiết kết quả
  trong `E1-validation/regression.log`. Việc mã trùng tag tự nó không chứng
  minh mã không lỗi; kết luận giới hạn ở **chưa phát hiện lỗi qua các kiểm tra này**.

Đối chiếu 525 file có sẵn ở mốc đóng (tài liệu 20R2, dữ liệu LIVE 20R2,
measurements/twin/cert và tools): **không file nào đổi**.
Bằng chứng: `E1-validation/custody.json` và `E1-validation/summary.json`.
Không có căn cứ mới trong các kiểm tra trên để mở lại phán quyết.
Đổi quần thể sau khi thấy số vẫn là đổi estimand sau khi thấy dữ liệu.

## 1. Năm đính chính

### E1-a — Sổ đăng ký khai sai đơn vị của `SLA_VIOL_BY_AGE`

Trước đính chính, `docs/GLOSSARY.md` khai `SCALE = cost_ms`, `UNIT = ms`.
Trong `measurements/decision_error_v2.py`, `_viol` trả boolean và `d_sla`
là hiệu hai trung bình boolean: **không thứ nguyên, trong [-1, 1]**.
Đính chính `20R2.7-B1` ngày 2026-09-11 đã tới mã và `07-dsla.md` nhưng chưa
được chép về sổ đăng ký.

Đã sửa cả khối SCALE/UNIT và dòng tóm tắt ánh xạ trường ở GLOSSARY.
`err_total` và `d_sla` cùng không thứ nguyên, khác sự kiện được đếm: hàng chọn
sai so với chênh lệch tỷ lệ vi phạm SLA. Không dùng chung ngưỡng chấp nhận.
Hai estimand vẫn dùng cùng quần thể ô/hàng đã ký. `d_sla` vẫn nhạy với ngưỡng
SLA và với `w_loss` thông qua lựa chọn `argmin`.

Chặn cơ học: `test/test_estimand_registry_matches_code.py`, **9 phép kiểm**,
neo văn bản và mã vào cùng hợp đồng; kiểm cả bảy trường, LEVEL, ánh xạ trường
và nguồn đính chính.

```text
TRƯỚC khi vá: 2 failed, 7 passed in 0.98s
  test_registry_declares_the_unit_the_contract_requires[SLA_VIOL_BY_AGE]
  test_erratum_exists_and_is_referenced_from_the_registry
SAU khi vá:   9 passed in 0.37s
```

Log gốc: `E1-validation/red.log`, `E1-validation/green.log`.
Nguyên tắc rút ra: một đính chính chỉ hoàn tất khi tới nguồn chân lý,
không chỉ tới nơi vừa phát hiện lỗi.

### E1-b — Truy nguyên quần thể tám ô gate

Nguồn phân hoạch là `results/LIVE/phase-20R/sla_calibration.json`, trục
`self_calibrated` đã DEPRECATED. Manifest exogenous bỏ `in_band` và
`opt_viol_rate` nhưng giữ `role` đã suy từ chúng.

Công cụ `tools/20r2_9_partition_invariance.py` dùng bảng sự thật, seed 100,
50.000 mẫu, dt = 0,005 s, tau = 1 s; không đọc kết quả chiến dịch.

```text
P1  role được chép nguyên sang exogenous        CARRIED
P2  role == gate <=> mode != cbr                 12/12 KHỚP
P3  tính lại in_band trên exogenous             8/10 ô khả thi LẬT
```

| Ô | viol self | viol exogenous | in_band đổi? |
|---|---:|---:|---|
| cbr@0.700 | 0.0000 | 0.0000 | Không |
| cbr@0.850 | 0.0000 | 0.0000 | Không |
| cbr@0.925, cbr@0.960 | — | — | Không khả thi |
| poisson@0.700 | 0.1500 | 0.0000 | Có |
| poisson@0.850 | 0.1500 | 0.0358 | Có |
| poisson@0.925 | 0.1500 | 0.9924 | Có |
| poisson@0.960 | 0.1500 | 1.0000 | Có |
| h2@0.700 | 0.1500 | 0.8485 | Có |
| h2@0.850 | 0.1500 | 1.0000 | Có |
| h2@0.925 | 0.1500 | 1.0000 | Có |
| h2@0.960 | 0.1500 | 1.0000 | Có |

Tám ô gate cũ đều đạt đúng mục tiêu hiệu chuẩn 0,15, nên việc nằm trong
[0,10; 0,25] không phải bằng chứng độc lập về môi trường trên lưới này.
**Tiêu chí không bất biến; phân hoạch được giữ nguyên và trùng một vị từ
không dùng trục SLA trên đúng 12 ô đã kiểm.** Không suy rộng kết quả này sang
mọi topology hay mọi cách tái chọn quần thể theo SLA mới.

Đã bổ sung nguồn, P2/P3 và hạn chế **T2-R7** vào POPULATION trong GLOSSARY.
Không đổi role hay mẫu số. Chi tiết từng ô:
`E1b-partition-invariance.json`; stdout: `E1-validation/partition.log`.

### E1-c — Cơ chế cbr bằng bất đẳng thức, có đối chứng dương

Câu đọc cơ chế trong `06-adjudication.json` giữ nguyên. Bổ sung từ bảng tra:

```text
cbr: khe hở hai đường tốt nhất tại điểm tham chiếu = 1.49435 ms
     cận biến thiên của hiệu hai đường            = 0.07909 ms
     khe hở / cận biến thiên                       = 18.8947 lần
     loss trên các đường cong                     = 0
     argmin của bảng sự thật                      bất biến
h2:  chỉ số khe hở / biên độ delay                 = 0.021745
     có nhân chứng chọn P1, P2, P3, P4 tại các tải khác nhau
```

Biên độ delay bao phủ toàn miền bảng tra; với cbr có loss bằng 0, nó cũng
chặn được biến thiên chi phí đầy đủ. Khe hở lớn hơn cận biến thiên nên đường
thắng không đổi trong phép nội suy/kẹp miền hiện hành.

Hai giới hạn diễn giải cần giữ:

- Đường cong cbr **gần phẳng**, không hằng tuyệt đối. Chứng minh này khóa
  `argmin` của **bảng sự thật**; muốn suy ra `err_total = 0` còn cần chứng minh
  mô hình twin chọn cùng đường. Không suy ra điều đó chỉ từ bất đẳng thức.
- Với h2/poisson, biên độ delay riêng không phải cận đầy đủ của cost có loss.
  Việc cận đủ không đạt không chứng minh tồn tại lật. Công cụ vì vậy tính thêm
  nhân chứng chi phí thật tại điểm tham chiếu và 256 góc miền tải, lưu
  `flip_witnesses` với rho từng link, bốn chi phí và đường thắng.

Nguồn: `E1-mechanics.json :: C_cbr_mechanism`, gồm bảng từng link và đối chứng.

### E1-d — 20R2-L9: giả định tựa-tĩnh của bảng tra

`truth_table.parquet` mô tả trạng thái dừng. Dùng bảng đó ở rho(t) biến thiên
ngầm giả định hàng đợi kịp cân bằng. E1 tính sàng lọc từ thời gian phục vụ
s = MTU*8/bw, lấy MIN của s/(1-rho)^2 và q*s/|1-rho|, rồi so với tau/5.

| rho_bar | Thời gian đặc trưng lớn nhất (s) | Link | Tau bị gắn cờ (s) |
|---:|---:|---|---|
| 0.700 | 0.054 | ad | Không |
| 0.850 | 0.346 | ad | 0.5, 1 |
| 0.925 | 2.419 | ad | 0.5, 1, 2, 3, 5, 10 |
| 0.960 | 3.494 | bc | 0.5, 1, 2, 3, 5, 10 |

**Giới hạn của phép sàng lọc:** hai biểu thức là ước lượng thời gian đặc trưng
và thời gian trôi của buffer; MIN của chúng chưa được chứng minh là cận chặt
cho thời gian cân bằng ngẫu nhiên của các traffic family. Ngưỡng tau/5 là
**quy ước**, lấy cảm hứng từ `BLOCKS_PER_TAU = 5.0`, không suy từ định luật.
Do đó “vi phạm” trong tên trường JSON nghĩa là **không đạt quy tắc sàng lọc**,
không phải đã đo được hệ động lực học mất tựa-tĩnh.

Ba MISS ở tau = 0.5, 1, 2 nằm trong vùng bị gắn cờ tại rho cao. Giả thuyết
này chưa được loại trừ, cũng chưa được chứng minh là nguyên nhân. Cần thí
nghiệm động lực học riêng để kết luận. Nguồn:
`E1-mechanics.json :: D_quasi_static`, 8 link × 4 rho_bar × 8 tau.

### E1-e — 20R2-L10: thành phần chi phí mất gói lớn

Manifest S-B khai `w_loss = 5000 = 50/0.01`, quy tắc equal_budget.
Đo trên 8 ô gate × a ∈ {0.5, 0.9}, tau = 3 s, seed 101, n = 50.000:

```text
loss_share = mean(w_loss * loss) / [mean(delay_ms) + mean(w_loss * loss)]
miền đo được: 11.6% (poisson@0.700, a=0.5) ... 95.8% (h2@0.960)
14/16 tổ hợp có loss_share >= 50%
```

Trung bình lấy trên **mọi thời điểm và cả bốn đường**, không chỉ đường được
chọn. Nhãn delay của một số hạng không mô tả thành phần của tổng chi phí.
Tuy nhiên, **tỷ trọng trung bình không chứng minh loss quyết định argmin**:
xếp hạng phụ thuộc chênh lệch giữa các đường. E1 không khẳng định margin
m = 3.11 hay sai khác với dự báo prereg là do w_loss. Muốn quy nguyên nhân
cần thí nghiệm độ nhạy hoặc phân tích chênh lệch chi phí riêng.

Nguồn: `E1-mechanics.json :: E_cost_composition.rows` (16 hàng) và `summary`.

## 2. Phạm vi bất biến

Không sửa prereg, prediction, plan, log chiến dịch, hygiene, 06*, 07*,
08-handoff, 99-gate-decision, parquet chiến dịch hoặc dụng cụ đã đóng băng.
Không đổi phán quyết, mẫu số, ngưỡng, quần thể hay băng chấp nhận.
Không đóng D2, D4, D5, D6, D9, D10, N7; chúng thuộc công việc 20R2.9 tiếp theo.

Các file đang sống được sửa: GLOSSARY, inherited_restrictions và test canh.
Hai tool mới, hai artifact mới và erratum bổ sung dấu vết; không ghi đè kết
quả lịch sử. Mốc đóng cũ được kiểm bằng `git rev-parse phase-20R2-closed^{}`
vì tag annotated có object hash riêng, khác commit đích.

## 3. Tiếp nhận và bàn giao cho 21R2

20R2-R3: ACCEPT — Ghi loss_share cùng diễn giải err_total; không suy nguyên nhân argmin từ tỷ trọng trung bình.
20R2-R4: ACCEPT — Khai 20R2-L9 ở các ô bị gắn cờ; không coi sàng lọc là phép đo động lực học.

Hai hạn chế ACTIVE trong `docs/inherited_restrictions.json` chỉ đưa
`docs/phase-21R2` vào `phases_in_scope`. Phase 21R2 chưa có prereg.
`acknowledged_in` trỏ tới chính erratum này, cùng file với `source`.

Test trước đây bắt buộc mọi hạn chế có ít nhất một phase đang tồn tại trong
scope, nên bản hướng dẫn nguyên văn gây **1 failed, 4 passed**. Đã thêm cơ
chế xác nhận tại erratum của phase hiện hữu: cần file nguồn tồn tại, phase
cha có prereg, và dòng đúng ID `ACCEPT`. Không bỏ test, không đưa 20R2 vào
scope mới, không viết lại prereg cũ. **13/13 test đạt**, gồm đối chứng thiếu
file/thiếu ACCEPT/sai ID/sai nguồn và kiểm phase tương lai vẫn phải trả lời.

Công cụ tái sử dụng: P1/P2/P3 của partition; chứng nhận và nhân chứng lật của
mechanics; test estimand neo hai chiều. Không nâng NT đề xuất thành quy tắc
đã ký trong NT_REGISTRY ở bước này.

## 4. Tái lập và dấu vết thực thi

Môi trường: `/home/ubuntu/miniforge3/envs/sdn_rl/bin/python` theo
`requirements-test.txt`. Python mặc định của shell không có pytest.

```bash
export PATH=/home/ubuntu/miniforge3/envs/sdn_rl/bin:$PATH
python -m tools.20r2_9_partition_invariance --deterministic
python -m tools.20r2_9_e1_mechanics --deterministic
python -m pytest test/test_estimand_registry_matches_code.py -q -p no:randomly
python -m pytest test/test_inherited_restrictions.py -q -p no:randomly
```

Hai artifact đã lưu được sinh bằng `--deterministic`: bỏ generated_utc và
git_commit, giữ SHA256 đầu vào và mã nguồn. Kiểm tái lập chạy ra đường dẫn
tạm rồi so **bytes/SHA256**, không ghi đè artifact đã đóng.

Baseline đo trước: **17 failed, 715 passed, 42 skipped** cho no_stale_axes;
khác số passed trong tài liệu hướng dẫn nhưng vẫn có đúng 17 lỗi cũ.
Kết quả sau và tập ID lỗi so sánh nằm trong `E1-validation/summary.json`.
Log và lệnh đầy đủ: thư mục `E1-validation/`. Báo cáo đọc nhanh:
`E1-validation/REPORT.md`. Tự chấm E1-1…E1-4 nằm trong báo cáo đó.

Chuỗi commit riêng: E1-0 → E1-a → E1-b → E1-cde → E1-f → E1-g → E1-h.
Tag `phase-20R2-closed` giữ commit đích `042c58f4`; tag erratum chỉ tạo sau
khi kiểm tra xong. Trạng thái publish được xác nhận bằng Git remote sau push.
