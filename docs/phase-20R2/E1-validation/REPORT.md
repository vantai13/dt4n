# Kết quả thi công 20R2-E1

Ngày đo: 2026-09-13 UTC. Phán quyết gốc **5/8 giữ nguyên**.

Đã sửa đơn vị d_sla và POPULATION trong GLOSSARY; thêm hai công cụ, hai
artifact số đo, erratum, R3/R4 trong sổ hạn chế và các test cơ học.
Không sửa nội dung tài liệu, mã dụng cụ hay dữ liệu đã đóng.

## Kết quả chạy

| Kiểm tra | Kết quả thực chạy | Log |
|---|---|---|
| Đối chứng trước khi vá | 2 failed, 7 passed | [red.log](red.log) |
| Sổ estimand sau khi vá | 9 passed | [green.log](green.log) |
| E1 cuối: sổ + kế thừa + bằng chứng | 31 passed | [e1-tests.log](e1-tests.log) |
| Riêng kế thừa (đã tính trong 31) | 13 passed | [restrictions-green.log](restrictions-green.log) |
| Công cụ mới và tái lập | 5 passed, 27 deselected | [tool-reproduction-tests.log](tool-reproduction-tests.log) |
| Hồi quy bộ chấm/d_sla/estimand | 66 passed | [regression.log](regression.log) |
| no_stale_axes trước | 17 failed, 715 passed, 42 skipped | [stale-before.log](stale-before.log) |
| no_stale_axes sau | 17 failed, 715 passed, 42 skipped | [stale-after.log](stale-after.log) |

**Tập ID của 17 lỗi cũ trùng hoàn toàn; không phát sinh lỗi mới trong bộ kiểm
tra này.** Chưa chạy toàn bộ suite của repo; không tuyên bố cả repo xanh.
Baseline số passed khác tài liệu hướng dẫn, nhưng môi trường đã được ghi
đủ trong [environment.json](environment.json), khớp requirements-test.txt.

## Kết quả đo

| Phép đo | Kết quả | Artifact |
|---|---|---|
| P1 — role kế thừa | CARRIED | [Partition](../E1b-partition-invariance.json) |
| P2 — phân hoạch khớp vị từ mode != cbr | 12/12 | [Partition](../E1b-partition-invariance.json) |
| P3 — in_band đổi trên trục exogenous | 8/10 ô khả thi | [Partition](../E1b-partition-invariance.json) |
| C — khe hở / biên độ cbr | 1.49435 / 0.07909 ms = 18.8947× | [Mechanics, khối C](../E1-mechanics.json) |
| C — đối chứng h2 | Nhân chứng chọn P1, P2, P3, P4 | [Mechanics, flip_witnesses](../E1-mechanics.json) |
| E — tỷ trọng chi phí mất gói | 11.6–95.8%; 14/16 tổ hợp ≥ 50% | [Mechanics, khối E](../E1-mechanics.json) |

| rho_bar | Thời gian đặc trưng lớn nhất (s) | Tau bị gắn cờ sàng lọc (s) |
|---:|---:|---|
| 0.700 | 0.054 | Không |
| 0.850 | 0.346 | 0.5, 1 |
| 0.925 | 2.419 | 0.5, 1, 2, 3, 5, 10 |
| 0.960 | 3.494 | 0.5, 1, 2, 3, 5, 10 |

Số đầy đủ ở khối D của Mechanics. Sàng lọc tựa-tĩnh dựa trên giả định MIN
hai thời gian đặc trưng và ngưỡng tau/5; chưa phải phép đo động lực học.
Tỷ trọng chi phí trung bình không chứng minh số hạng nào quyết định argmin.
Bất đẳng thức C khóa argmin bảng sự thật; không tự chứng minh err_total = 0
cho mọi mô hình twin. [Erratum](../E1-erratum.md) nêu rõ các giới hạn này.

## Tự chấm và tái lập

- E1-1: **PASS** — 525 file đóng băng giữ nguyên; 167 parquet + 167 sidecar
  khớp sổ cái. [custody.json](custody.json).
- E1-2: **PASS** — kiểm tra cơ học và đối chứng như bảng trên; hai artifact
  chạy lại trùng bytes và SHA256. [reproduction.json](reproduction.json).
- E1-3: **PASS** — erratum ghi rõ 5/8 giữ nguyên và bằng chứng kiểm hai điều
  kiện mở lại, không đánh đồng mã trùng tag với chứng minh mã không lỗi.
- E1-4: tạo tag `phase-20R2-erratum-1` sau commit tự chấm; kiểm remote sau push.
  Bằng chứng publish thực tế ghi sau commit tại `/home/ubuntu/20r2-e1-publish.log`.
  Tag cũ có commit đích `042c58f4dd20dc6f7b78cdfe7f3473a6e3745ffb`.

SHA256 artifact đã tái lập:

- `20r2_9_partition_invariance`: `2d6bbf1d5a1265cca56c3b68cbc9162330df88c2a465b1b2d4ca004e79b15849`
- `20r2_9_e1_mechanics`: `3ca4119bb7df0bfc27d18422964a41011a7fb5162aff438f2e027365e91c5a32`

Các điều chỉnh cần thiết so với hướng dẫn: dùng đúng env sdn_rl; sửa mã
T2-R7 và định dạng nguồn `::`; tiếp nhận hạn chế mới tại erratum mà không
sửa prereg cũ; đăng ký hai tool vào bộ test tái lập; lưu deterministic; thêm
nhân chứng lật thật và giới hạn diễn giải khoa học. Không triển khai 20R2.9-A.

Lệnh chạy lại: [commands.md](commands.md). Dữ liệu tổng hợp máy đọc:
[summary.json](summary.json). Không dùng số dự kiến trong hướng dẫn thay số thực đo.
