# Kết quả thực hiện hướng dẫn 20R2.0 / 20R2.1

Ngày 2026-09-09, checkout `/home/ubuntu/dt4n`, mã ban đầu `665bebe9`.
Python dùng để chạy: `/home/ubuntu/miniforge3/envs/sdn_rl/bin/python`.
Python mặc định ở môi trường base không có pytest.

## Công việc đã làm

- `_valid_rows` bắt buộc `axis=...` dạng keyword-only; cập nhật tất cả caller
  sản xuất, caller kiểm thử và các công cụ lịch sử liên quan.
- `tau_sweep`: `--axis` bắt buộc, truyền qua CLI → sweep → build_at_tau →
  `_valid_rows`, ghi trục vào kết quả và provenance. Planner T2 cũng truyền
  trục legacy tường minh. Chỉ hỗ trợ legacy vì z-bin/z-rep/ratio bands của
  harness này đã khóa theo Phase 22; measured bị từ chối trước khi sinh số.
- `build_one_v3`: metadata tuổi dùng đúng bộ sinh theo trục và hồ sơ.
  Chẩn đoán staleness trong report cũng nhận trục đang chọn.
- Test ánh xạ hai hệ tên trục kiểm với validity suy từ SHA nguồn thật.
  Giữ tên cũ để tương thích artifact lịch sử.
- Audit AST mở rộng sang aoi_profiles/cell_matrices và ghi lời gọi trực tiếp
  bộ sinh, hàm chứa, điều kiện axis bao quanh. Sau sửa: 0 caller thiếu axis.
- Thêm công cụ kiểm toàn vẹn parquet: đủ đúng 166 report/đường dẫn duy nhất,
  SHA từng tệp, giải mã parquet và đối chiếu số hàng. Test cả thiếu, lệch SHA,
  sai số hàng và tập 165/166/167 tệp; không dùng điều kiện tự khớp tập con.
- Mở `.gitignore` đúng thư mục sweep_r2, bảo tồn 166 parquet nguyên bản.
  Cập nhật QD-33, OWNERSHIP, hợp đồng bàn giao, T2-L8, 20R2-L2/L3.
- Đính chính thêm prereg §4: z=2 s vượt max thực nghiệm 1,5689 s;
  chỉ z=1 s nằm trong miền thực nghiệm đã đo.

## Số đo thật

| Phép kiểm | Kết quả |
|---|---:|
| Report đã đối chiếu | 166 |
| Parquet tồn tại, khớp SHA và đọc được | 166/166 |
| Thiếu / lệch SHA | 0 / 0 |
| Số hàng báo cáo = đọc được | 10.940 = 10.940 |
| Dung lượng parquet | 3.097.390 byte = 3,097390 MB |
| Caller `_valid_rows` thiếu axis trong các harness đã audit | 0 |

Đây là đo trên máy hiện tại, không phải clone sạch. 166 file còn trên máy
nhưng trước thay đổi bị gitignore chặn. Không chạy lại 166 lệnh.
Bảo tồn không cho phép tái dùng trên A5: SLA self_calibrated khác exogenous
ở cả nhánh chính lẫn đối chứng. Không trừ lệnh nào khỏi ngân sách lưới mới.

### Đo bản sửa metadata, dt=0,005 s; n=20.000; seed=101; poisson@0.925

| Trục / hồ sơ | k trước | k sau | z thực tế sau (s) | Dữ liệu trước/sau |
|---|---|---|---|---|
| legacy / U0 | 11–110 | 11–110 | 0,055–0,550 | bit-exact |
| measured / U0 | 11–110 | 23–123 | 0,115–0,615 | bit-exact |
| measured / U1 | 11–110 | 19–119 | 0,1175–0,6175 | bit-exact |
| measured / U3 | 11–110 | 22–122 | 0,118125–0,618125 | bit-exact |

`k` là tuổi cơ sở; `z = k*dt + z_shift_ms/1000`. Với U1/U3 phải cộng
phần dịch trung bình của các link. So DataFrame bằng
`pandas.testing.assert_frame_equal(check_exact=True)` với mã từ commit gốc.
Smoke tau legacy, τ=1 s, n=20.000: 19.989 hàng, DataFrame bit-exact.
Đây là hồi quy trên SLA lịch sử, không phải kết quả lưới A5.

CLI thật cũng đã chạy với `--axis legacy_sawtooth_51ms`, τ=1, seed=101,
sigma=0,0096, n=20.000: ratio_measured=2,423539910533333; 10 block calibration
ở bin ít nhất. Smoke nhỏ không dùng phán quyết gate khoa học Phase 22/20R2.

### Ví dụ dữ liệu lịch sử đọc từ parquet đã khôi phục

poisson@0.925, seed=101, τ=0,5 s, sigma=0,021802…,
SLA=self_calibrated, w_loss=3222,244682…; giữ đúng một file/cấu hình:

| z (s) | err_total | d_sla |
|---:|---:|---:|
| 0,00 | 0,023569 | 0,005648 |
| 0,05 | 0,186682 | 0,041396 |
| 0,10 | 0,251913 | 0,071406 |
| 0,20 | 0,334739 | 0,118389 |
| 0,30 | 0,390944 | 0,153715 |
| 0,55 | 0,480537 | 0,213544 |

Đây là **số cũ được đọc lại**, không phải số mới đo trên measured/exogenous.
CSV lưu đầy đủ độ chính xác, nguồn parquet, các cờ ngoại suy và nhãn trục.

## Gate và phần chưa hoàn tất

| Gate | Trạng thái / phạm vi |
|---|---|
| 0-1 | PASS: audit sinh bằng công cụ, đã chạy lại sau sửa |
| 0-2 | PASS về kiểm tra: G-A020 transfer vẫn FAIL 5/6 chiều |
| 0-3 | CHƯA ĐẠT: prereg chưa đủ điều kiện ký |
| 0-4 | N/A cho lối (iii); đã ghi T2-L5/L8 |
| 0-5 | PASS cho `_valid_rows` và đường truyền axis đã kiểm |
| 1-1 | PASS: QD-33 nêu không tái dùng vì khác trục SLA |
| 1-2 | PASS kiểm khôi phục: 166/166; không cấp quyền tái dùng A5 |
| 1-3 | PASS: OWNERSHIP giữ nguyên nội dung lịch sử, thêm banner |
| 1-4 | Đã sửa reuse=0; CHƯA xác nhận ngân sách ±30% vì chưa định nghĩa ô |

Không tạo `phase-20R2-prereg-signed`, không ký thay người dùng, không chạy
lưới kết quả 20R2. Còn thiếu định nghĩa một ô/các chiều tạo 960 ô trong
PHASE_20R2.md và tên người ký. Prereg §0 yêu cầu giải quyết trước khi ký.
Tag `phase-T2-closed-v2` dùng để đánh dấu commit có T2-L8 và bản bảo tồn.

Giới hạn kiểm thử: baseline validity là 17 failed / 627 passed / 42 skipped,
khác 609 passed trong hướng dẫn. Sau sửa: 17 failed / 628 passed / 42 skipped;
so danh tính 17 lỗi để kiểm không tăng, không chỉ đếm lỗi.
61 kiểm thử liên quan đều đạt. Kiểm lại 14 test mới sau lần sửa cuối đều đạt.
Test mở rộng từng thử legacy U1/U3 gặp lỗi chỉ số âm có sẵn; smoke bit-exact
trong báo cáo chỉ bao phủ legacy U0 và measured U0/U1/U3.
Các API builder cấp cao vẫn có mặc định tương thích; không tuyên bố đã xóa
mọi mặc định axis trên toàn repo. 20R2.3 vẫn phải kiểm neo v8 và môi trường.

## Kiểm thử toàn repo và đối chiếu mã gốc

`pytest -q`: **25 failed, 2842 passed, 138 skipped, 13 deselected**,
688,02 giây (11 phút 28 giây). Không báo toàn repo xanh.

Đã tái hiện **đủ 25 danh tính lỗi** trên mã gốc `665bebe9` với cùng dữ liệu:
17 lỗi validity T2; 3 cờ CLI chưa nối trong công cụ G2/G3; 1 danh sách
KNOWN_DANGLING đã lỗi thời; 1 so số công bố g23-17c; 3 lỗi G3 phụ thuộc
thứ tự import. Nhóm G3 chạy riêng thì đạt, nhưng thu thập chung với
`test_g3b_sigma_tau_grid.py` khiến `g3_dryrun.DT_S` bị đổi 0,2 → 0,1;
đã tái hiện đúng 3 lỗi đó trên mã gốc. Không sửa các lỗi ngoài phạm vi này.

Phương pháp đối chứng: tách mã tracked ở HEAD gốc sang thư mục độc lập,
dùng lại cây results hiện có, chạy lại các nhóm lỗi; **không** chạy toàn
suite lần thứ hai trên baseline. `verification.json` ghi danh tính từng
lỗi và tập lỗi mới rỗng. Các cập nhật cuối về xuất báo cáo được kiểm riêng:
14 test mới đạt, 2 test recovery đạt, 3 kiểm cờ CLI công cụ 20R2 đạt.

## Tệp kết quả và cách chạy lại

- `results/PENDING/phase-20R2/parquet_recovery.json`: 166 dòng SHA, số hàng, byte.
- `results/PENDING/phase-20R2/recovered_sample.csv`: mẫu số đo lịch sử đầy đủ.
- `results/PENDING/phase-T2/sweep_r2/*.parquet`: dữ liệu gốc được bảo tồn.
- `results/PENDING/phase-20R2/axis_audit.json`: audit trục và ngân sách.
- `results/SMOKE/phase-20R2/remediation_smoke.json`: số trước/sau và bit-exact.
- `results/SMOKE/phase-20R2/tau_sweep_cli.json`: kết quả CLI smoke thực tế.
- `results/SMOKE/phase-20R2/verification.json`: tổng hợp kết quả kiểm thử.
- `results/SMOKE/phase-20R2/test_*.md`: log kiểm thử đầy đủ.

```bash
PYTHON=/home/ubuntu/miniforge3/envs/sdn_rl/bin/python
$PYTHON -m tools.20r2_0_axis_audit --out results/PENDING/phase-20R2/axis_audit.json
$PYTHON -m tools.20r2_1_parquet_recovery --out results/PENDING/phase-20R2/parquet_recovery.json --sample-out results/PENDING/phase-20R2/recovered_sample.csv
$PYTHON -m tools.20r2_remediation_smoke --out results/SMOKE/phase-20R2/remediation_smoke.json
$PYTHON -m pytest test/test_axis_label_agreement.py test/test_20r2_parquet_recovery.py test/test_phase22_calibv3.py test/test_phase23_dsync_sensitivity.py test/test_phase23_axis_integration.py test/test_phase22_tau.py -q
$PYTHON -m pytest test/test_no_stale_axes.py -q
```
