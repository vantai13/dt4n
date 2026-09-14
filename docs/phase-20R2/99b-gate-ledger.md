# 20R2 — Sổ chấm bảy gate cấp phase, bổ sung 20R2.9-A

Ngày 2026-09-14. Giữ nguyên `99-gate-decision.md` và các artifact đã đóng.
Nguồn định nghĩa: khai **theo từng gate** trong [99c-gate-definition-sources.json](99c-gate-definition-sources.json) — 4/8 dòng trích được một câu chữ trong kho (file:dòng, có test kiểm), 2/8 chỉ viện dẫn, 2/8 không có nguồn trong kho. `PHASE_20R2.md` và `MASTER_PLAN_v10.md` được hướng dẫn viện dẫn nhưng không có trong checkout/lịch sử tìm được (20R2.9-C/C-1, `BLOCKED_INPUT_SOURCE`); chưa đối chiếu trực tiếp hai tài liệu đó và **không** tái dựng chúng. `test_a_missing_specification_cannot_arrive_unnoticed` sẽ đỏ ngay khi byte gốc xuất hiện, buộc nâng cấp sổ nguồn. Bảng có tám dòng vì lưu cả gate 3 đã rút và gate 3′ thay thế.

Nhãn: PASS = thoả; FAIL = không thoả (VALIDITY phải sửa, không gọi là kết quả khoa học); VOID = tiền đề đã rút; DEFERRED = có phase nhận, amendment và điều kiện đóng; SUBSTITUTED = thay phép kiểm, phải công khai phần mất độ phủ.

| Gate | Loại | Nhãn | Bằng chứng và giới hạn | Nợ |
|---|---|---|---|---|
| 20R2-1 | VALIDITY | **SUBSTITUTED** | Neo T2 A1/A2 đạt theo bằng chứng lịch sử; không xác nhận tái tạo literal v8. Xem dưới. | E1-L11 |
| 20R2-2 | OUTCOME | **PASS** | `06-adjudication.json`, secondary_shape: 6 DECREASING, 0 INCREASING, 1 UNREADABLE; mẫu số 7. | — |
| 20R2-3 | — | **VOID** | G-A020 §1.1 rút ω khỏi chiều quét, thay bằng 3′. | — |
| 20R2-3′ | VALIDITY | **PASS (tầm thường)** | ω₀=0 theo cấu tạo, c(0)=1, sigma_eff_proxy=sigma. Prereg §7/§17-W ghi điều kiện G-A020 §4 FAIL; không suy thành kiểm định tương quan. | G1 |
| 20R2-4 | VALIDITY | **PASS** | H8 chạy lại qua helper sản xuất: 320/320 đủ tiêu chí và REALIZABLE strict; mutation thiếu sigma/clip/blocks bị bắt. | A2 đóng |
| 20R2-5 | BUDGET | **PASS** | H9 đã lưu: 70.0836502473 / 74.5285461744 = 0.9403598198, dung sai 0.30. Đây là số chiến dịch lịch sử, không phải thời gian pytest lần này. | — |
| 20R2-6 | VALIDITY | **FAIL(a), PASS(b)** | (a) chỉ sửa một phần truy nguyên; (b) đã ép lựa chọn tường minh trong phạm vi AST A4. | D11 mở; D12 đóng trong phạm vi kiểm |
| 20R2-7 | VALIDITY | **DEFERRED → 21R2** | [AMENDMENT-20R2-A2](AMENDMENT-20R2-A2.md); N3/N4 phần 20R2 chưa đo. | D4 |

## 20R2-1: bốn phần của SUBSTITUTED

(a) Đã ký theo hướng dẫn: “tái tạo BIT-EXACT kết quả v8”. Không tìm được v8 trong tên artifact results, thông điệp git log --all, hoặc tài liệu T2/MAP đã quét; không có đối tượng để thực hiện phép kiểm literal đó.

(b) Thay thế: neo A1 digest bộ sinh và A2 166 parquet T2 legacy, kết quả lịch sử 166/166 BIT-EXACT. Xem prereg §15 và `results/PENDING/phase-20R2/bit_exact_regression.json`. Lần A này không chạy lại toàn bộ chiến dịch 166 lệnh; suite có kiểm hồi quy giới hạn và artifact đã lưu.

(c) Cơ sở: T2 là tiền thân trực tiếp; A1 độc lập trục, A2 kiểm đường ống legacy chung. Điều này hỗ trợ tính liên tục của phần mã chung.

(d) Mất đi: prereg §15.3 đã công khai nhánh z `20r2_measured`, SLA exogenous và mã mới G4 không được neo bởi đối chứng legacy. SUBSTITUTED không có nghĩa PASS nguyên văn gate v8.

## 20R2-6: không che nợ bằng chuỗi ghim

Vế (a): 9/9 JSON PENDING có validity; H7 đã kiểm 160 parquet chiến dịch và sidecar. Tuy nhiên 11/13 JSON top-level docs thiếu validity, 5/5 JSON SMOKE thiếu validity. Không sửa những artifact đã đóng để gắn nhãn hồi tố.

`tools/20r2_9_axis_chain.py` kiểm hash thật và nguồn SLA qua registry, sidecar chiến dịch, ngữ cảnh z-grid theo nhánh. Bốn tài liệu có `inputs_sha256` phân giải được; `E1b-partition-invariance` có hai trục SLA vì cố ý so đối chứng legacy với exogenous. Hai ngữ cảnh chiến dịch main/control cũng được giữ riêng. Các lá chưa khai đủ trục được ghi ra, không suy rằng mọi lá đều có validity.

Chín tài liệu chưa có ghim chuẩn tắc: 01-prediction-signed, 02-se-pilot, 05-hygiene, 06b-per-cell, 06c-g4-predictions, 06c-g4-score, 07-dsla, 07a-dsla-structure, 08-handoff-measurements. Chúng vẫn thuộc **20R2-D11**, có 9 skip mang tên nợ trong test chuỗi. Gate (a) giữ FAIL_WITH_PARTIAL_LINEAGE_REPAIR. Đóng D11 khi producer 21R2 ghi inputs_sha256 và các trục tại nguồn, mọi chuỗi kiểm được, 5 artifact SMOKE được xử lý theo phạm vi công bố, và gỡ miễn trừ hết hạn; giữ nguyên bằng chứng lịch sử.

Vế (b): A4 kiểm AST measurements/cert/twin, đổi 22 mặc định trục trên 7 file; mở rộng tới 94 mặc định trên 35 file tính cả hằng đường dẫn artifact. 128 biểu thức gọi lịch sử được truyền lựa chọn cũ tường minh. Sentinel không được dùng làm bool; các đối số chọn calibration/axis/sigma không nhận None. D12 đóng trong phạm vi bộ quét (hằng số được đặt tên và đường dẫn hằng top-level); không tuyên bố phân tích mọi cấu trúc động Python.

## Custody: prediction đổi hash, số dự đoán giữ nguyên

03-run-plan và 06-adjudication ghim d9eef23b… tại b855d49/1918b89. 79de5a0 sửa mô tả đơn vị d_sla thành 6ec81b25… như prereg §12.1. Byte lịch sử vẫn có trong git.

[Custody ledger](../CUSTODY_LEDGER.json) lưu hash trước/sau, commit, lý do và diff mọi lá. Trong 149 trường số có 5 khác biệt, tất cả là số dòng mã nguồn; thêm 5 thay đổi chuỗi/mô tả/thời điểm. **Không giá trị dự đoán số nào đổi.** Không nói “0/149 trường số đổi”. Test tính lại diff từ git, kiểm whitelist metadata và từ chối cả thay đổi số giả mạo có verdict_affected=false. Đây là kiểm tra kỹ thuật của Codex theo yêu cầu người dùng, không giả làm chữ ký khoa học của tác giả.

Kết quả máy: [axis-chain.json](A-validation/axis-chain.json), [custody-diff-unreviewed.json](A-validation/custody-diff-unreviewed.json). Kết quả toàn suite và giới hạn còn mở ghi trong báo cáo A sau khi chạy.
