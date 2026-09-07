# G′.5c — P-3b: gate đơn điệu ký lại với dấu ĐÚNG. Tiền đăng ký

Trạng thái: `PREREGISTRATION`. Nghiên cứu tổng hợp, không chạy mạng.
Ký trước khi thực thi `tools/g5c_monotone.py`. Tag `phase-G2-g5c-prereg`.

## 1. Vì sao tồn tại

`docs/phase-G/73-g5b-results.md` §2 ghi `G-L111`: gate `P-3` của doc 72 tự
mâu thuẫn. Văn xuôi đòi dãy KHÔNG TĂNG; công thức phạt mọi bước GIẢM quá
0.005. Đại lượng đo — tỉ lệ chấp nhận trên trục công suất — GIẢM theo thiết
kế, nên công thức phạt đúng hiệu ứng đang tìm. Gate ghi VOID và phán quyết
lấy nhánh bảo thủ `ADOPT_WEAK`.

Đây là sửa DẤU của một gate, không phải nới NGƯỠNG sau khi thấy dữ liệu.
Ngưỡng được kiểm lại bằng ngân sách từ seed cũ ở §3 và trùng giá trị cũ; sự trùng đó là kết quả
của phép tính, không phải điều kiện của nó.

## 2. Cái gì đổi, cái gì KHÔNG

ĐỔI — đúng ba thứ:
  · `P-3`  min(diff(acceptance)) >= -0.005   →  VOID, rút
  · `P-3b` max(diff(acceptance)) <= +0.005   →  ký mới
  · seed 20260908 → 20260909 (seed thứ ba)

KHÔNG ĐỔI:
  · bộ sinh, mô hình sai số, surrogate thang, lưới ω, số replicate,
    dt, tau, sigma_ref, alpha, kappa_accept, kappa_nugget
  · ngưỡng `P-1`, `P-2`, `NC-1`, `NC-2`
  · cây phán quyết doc 72 §4
  · `tools/g5b_power_axis.py` KHÔNG bị sửa một dòng; `SEED` được rebind
    lúc import, theo đúng khuôn mẫu `tools/g2_kill_test.py:66`
  · nguồn được bảo vệ `cert/simultaneous_score.py`, `cert/margin_score.py`,
    `test/test_phase22_simscore.py` — kiểm bằng `verify_protected()`
    trước VÀ sau khi chạy

## 3. Ngân sách sai số của ngưỡng +0.005

Từ `acceptance_mc_se` của artifact G′.5b (SHA256 trong §8):
    mc_se = [0.000969, 0.000919, 0.000989, 0.000992, 0.001017]
    SE_independent(step) = √(se_i² + se_{i+1}²) <= 0.001421096

Đây chỉ là cận trên NẾU covariance giữa các điểm liền kề không âm. CRN
không tự bảo đảm điều đó, nhất là khi bộ sinh dùng eigenfactor thay đổi theo ω.
Các xác suất dưới đây là xấp xỉ chuẩn, có điều kiện trên giả định covariance
không âm và SE ước lượng từ seed cũ; không phải bảo đảm báo động giả hữu hạn mẫu.
Không biết dấu covariance thì cận SD là se_i + se_j <= 0.002009574,
cho union bound xấp xỉ chuẩn khoảng 0.0257 tại dung sai 0.005.
Giữ dung sai 0.005 theo ngân sách làm việc có điều kiện này, không tuyên bố
báo động giả <0.1% vô điều kiện. Báo cáo thêm paired-step SE và covariance
trên seed mới; không dùng chẩn đoán này đổi gate hay chạy lại.

| dung sai | z | P(bắn nhầm, 1 bước) | P(bắn nhầm, 4 bước) |
|---:|---:|---:|---:|
| +0.003 | 2.11 | 1.7e-02 | 6.9e-02  ← quá cao |
| **+0.005** | **3.52** | **2.2e-04** | **8.6e-04** ✓ |
| +0.010 | 7.04 | 9.5e-13 | 3.8e-12  ← quá lỏng |

Độ nhạy tại +0.005: bắt được tăng thật +0.010 với xác suất 0.9998.
Ngưỡng vừa ĐẠT ĐƯỢC vừa CÓ THÔNG TIN — thoả `G-L90`.

## 4. Gate đóng băng

| gate | đại lượng | ngưỡng |
|---|---|---:|
| `NC-0` | vector acceptance KHÁC vector đã công bố của G′.5b | phải khác |
| `P-1`  | biên độ chấp nhận qua ω, max-score | >= 0.050 |
| `P-2`  | biên độ / SD một vệt | >= 5.0 |
| `P-3b` | **max(diff(acceptance))** | **<= +0.005** |
| `P-4`  | \|A(1) − A_scale(1)\| | BÁO CÁO |
| `P-5`  | tỉ lệ dòng bị xếp lại | BÁO CÁO |
| `NC-1` | biên độ coverage max-score | <= 0.005 |
| `NC-2` | biên độ công suất trên {uA, uB} | <= 0.010 |
| `NC-3` | không đồng nhất hệ số thang | BÁO CÁO |
| `S-1`  | q̂ phình | BÁO CÁO |

Cây phán quyết (giữ nguyên doc 72 §4, thêm NC-0 ở đầu):
  NC-0 FAIL                        → `INVALID_SEED_NOT_INDEPENDENT`
  NC-1 hoặc NC-2 FAIL              → `STOP_GENERATOR`
  P-1 FAIL                         → `POWER_TOO_WEAK`
  P-2 hoặc P-3b FAIL               → `ADOPT_WEAK`
  tất cả PASS                      → `POWER_AXIS_HOLDS`
                                     rồi P-4 phân loại:
                                       |P-4| < 0.03 → `REDUCIBLE_TO_EFFECTIVE_SIGMA`
                                       ngược lại    → `IRREDUCIBLE`

## 5. Dự đoán ký trước

```
NC-0  khác vector cũ                   dự đoán khác (seed khác; không là chứng minh độc lập)
P-1   biên độ chấp nhận       0.085 – 0.115   (G′.5b: 0.1018)
P-2   SNR                     6.0  – 9.0      ← sửa dự đoán hỏng của doc 72,
                                                doc 72 đoán >10 và trượt vì
                                                ngoại suy SNR từ biên độ mà
                                                quên SD kênh công suất lớn hơn
P-3b  bước tăng lớn nhất      −0.025 – −0.018
P-4   phần dư                 0.003 – 0.008   (G′.5b: 0.00529)
P-5   dòng xếp lại tại ω=1    0.44 – 0.48
NC-1  biên độ coverage        < 0.003
NC-2  biên độ trên {uA,uB}    = 0.000000 chính xác (khối hiệp phương sai
                                bất biến theo ω ⟹ cùng innovation ⟹ bit-đối-bit)
NC-3  không đồng nhất thang   1.5% – 3.5%
S-1   q̂ phình                 30% – 34%
```

## 6. Quy tắc dừng

- MỘT lượt chạy. Không có vòng chẩn đoán.
- `P-3b` FAIL ⟹ ghi `ADOPT_WEAK`, `kappa_time = 5` giữ nguyên, KHÔNG chạy lần
  thứ tư và KHÔNG đổi ngưỡng. Ba seed mà không có phán quyết thì phán quyết
  chính là "không có hiệu ứng đơn điệu ổn định".
- `NC-0` FAIL ⟹ run vô hiệu, sửa lỗi rebind, chạy lại vào tên file MỚI.
- Không ngưỡng nào được nới từ một quan sát mà nó trượt.

## 7. Thực thi và dấu tiền đăng ký

Ngày chuẩn bị: 2026-09-07 UTC. Seed là số định danh, không phải ngày chạy.
Dùng `/home/ubuntu/miniforge3/envs/sdn_rl/bin/python` vì workspace không có
`.venv`; NumPy 2.4.3, SciPy 1.17.1, pytest 9.0.3.
Test trước, sau đó commit ba file mới và tạo tag `phase-G2-g5c-prereg`,
rồi chạy một sweep primary và một sweep null, mỗi sweep 5 ω × 200 replicate,
600 s calibration + 600 s test mô phỏng mỗi replicate, dt=0.1 s.
Commit của tag được ghi trong artifact và doc 75, không chèn ngược vào
prereg sau khi ký (tránh làm bẩn worktree và thay hash của chính prereg).
Tag Git là mốc đóng băng cục bộ, không phải chữ ký mật mã hay timestamp bên ngoài.
`verify_protected()` thực tế đối chiếu tag `phase-G2-g5-prereg`;
kiểm trước và sau, cùng kiểm chứng evidence của measurement certificate.
NC-0 chỉ phát hiện vector trùng hoàn toàn; seed khác và provenance mới
là bằng chứng bổ sung, không suy độc lập thống kê từ vector khác nhau.

## 8. Nguồn đã xem trước khi chạy

G5b artifact: `results/SMOKE/phase-G2/g5b_power_axis.json`
SHA256 `62239b1f5cef6e276e82854cc691e0ce2e0cfd5eb38f4adab68001b7dbb38600`.
Doc 72, 73, 70a và hướng dẫn đính kèm đã được đọc trước tiền đăng ký này.
Đây là tiền đăng ký retest, không phải giả thuyết chưa từng nhìn dữ liệu.
