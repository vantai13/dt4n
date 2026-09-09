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

### Canary span = 0: môi trường không trôi suốt chiến dịch

Đo trên `results/PENDING/phase-T2/sweep_r2/run_log.jsonl`, sinh bởi
`tools/20r2_1_canary_span.py`, kết quả ở `results/PENDING/phase-20R2/canary_span.json`.

| Phép đo | Kết quả |
|---|---:|
| Số run canary (`is_canary=True`) | 6 |
| `run_index` của chúng | 0, 31, 62, 93, 124, 155 |
| Số sha256 **khác nhau** giữa 6 canary | 1 |
| **canary span** (= n_distinct − 1) | **0** |
| Trải dài thời gian giữa canary đầu và cuối | 1.711 s (28,5 phút) |
| Tham số của cả 6 | τ=3,0; seed=999; a=0,9; branch=fixed |
| Lệnh chuẩn hoá (bỏ `--out`), số bản khác nhau | 1 |

Canary là phép đo **lặp lại không nhằm lấy kết quả mới**, mà để phát hiện môi
trường trôi (*environmental drift*). Sáu lệnh y hệt nhau, rải đều suốt chiến
dịch, cho ra **byte giống hệt nhau** (`9fb07f1adc87…`). Nghĩa là thư viện, RNG,
thứ tự phép tính, luồng và cache **không trôi** trong 28,5 phút đó. Mọi khác
biệt giữa 160 run còn lại là do **tham số**, không do máy.

**Đối chứng âm — vì sao span = 0 ở đây không tầm thường.** Nếu tham số bị bỏ
qua thì *mọi* run đều ra một sha, và span = 0 vì lý do vô nghĩa. Nên công cụ đo
luôn cả nhóm không phải canary: **160/160 run cho 160 sha khác nhau**. Tham số
thật sự sinh ra byte khác nhau, nên 6 canary trùng nhau chỉ có thể vì **lệnh
giống nhau**. Đó là điều phân biệt "canary tốt" với "một tham số bị bỏ qua";
`verdict` ghi `CANARY_SPAN_0_WITH_DISCRIMINATING_CONTROL` chứ không phải
`canary_span=0` trơ trọi.

Đây là **tiền lệ đo được** cho harness `decision_error_v2`, dùng cho gate `5-3`
của Lesson 20R2.5 ("Canary span = 0"). Số này đo lại được bất cứ lúc nào bằng
lệnh ở cuối tài liệu; nó không phải một lời khai.

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

### Đèn xanh rỗng: `realizability_grid.json` thừa kế từ T2

Sinh bởi `tools/20r2_4_realizability_audit.py` →
`results/PENDING/phase-20R2/realizability_audit.json`.

Tiêu đề artifact trông hoàn hảo: `n_cells = 96`, `n_realizable = 96`,
`n_rejected = 0`, `rejected_by_reason = {}`. Mở từng ô ra:

| Phép đo | Kết quả |
|---|---:|
| Số tiêu chí trong mỗi ô | 9 |
| Tiêu chí **không chạy ở bất kỳ ô nào** | **3** |
| Tên chúng | `censoring_ok`, `mondrian_cells_populated`, `sigma_feasible` |
| Số ô có `failed = []` | 96/96 |
| Số ô có `passed = []` | **96/96** |
| Ô gắn `REALIZABLE` mà bảng khả thi nói KHÔNG | **16** |

```text
failed = []        doc la "khong tieu chi nao TRUOT"
nhung 3 tieu chi   KHONG CHAY  =>  khong the truot  =>  khong the fail
=> verdict xanh vi KHONG AI HOI, khong phai vi DA TRA LOI
```

Tiêu chí bị bỏ qua có tên `sigma_feasible` (`need: "> 0"`, `got: null`) — đúng
là tiêu chí lẽ ra phải bắt được `cbr@0.925` và `cbr@0.960`. Đối chứng chéo với
`sla_calibration.json` đếm được **16 ô** (8 τ × 2 ô `(c_a, ρ̄)`) được gắn
`REALIZABLE` trong khi dữ liệu đã có sẵn nói chúng không khả thi.

`verdict` của audit: **`VACUOUS_GREEN`**. Gate `20R2-4` mục 4-2
(`assert not_evaluated == []`) **trượt trên artifact thừa kế**.

⟹ **Không kế thừa kết luận khả thi của T2.** Ghi vào sổ giới hạn là `20R2-L4`.

> Một verdict PASS chỉ có nghĩa khi biết **bao nhiêu tiêu chí đã thực sự chạy**.
> Phụ lục B ghi *"một cơ chế phòng thủ ĐỎ THƯỜNG TRỰC thì đã chết"*; đây là mặt
> kia của đồng xu — **XANH THƯỜNG TRỰC cũng đã chết**, và nguy hiểm hơn, vì
> không ai đi kiểm một đèn xanh.

### Nhãn bịa đặt qua được test — đo bằng thí nghiệm ngược

`parquet_recovery.json` trước đây ghi `aoi_axis.label = "MIXED_OR_MISSING"` và
`sla_axis.label = "MIXED_OR_MISSING"`. Hai lỗi, lỗi thứ hai nặng hơn:

1. Nó **được gõ tay**, vi phạm nguyên tắc của chính `measurements/validity.py`:
   *"nhãn được SUY RA, không được KHAI BÁO"*.
2. Nó **sai sự thật**. Chính `source_axes` của artifact đó có **9/9 mục đồng
   nhất**: `sla_axis.label = "self_calibrated"` (cùng một `source_sha256`
   `0387d300…`, đã kiểm lại khớp với tệp thật) và `aoi_axis.label =
   "aoi_axis_free"`. Không "mixed", không "missing" — chỉ khác nhau ở **lưới z**,
   9 lưới, mà 8 trong số đó thoả đúng `z = τ · {0,1; 0,3; 0,55; 1,0}`.

**Vì sao nó lọt.** Thí nghiệm ngược, đo 2026-09-09: gắn lại nhãn cũ rồi chạy

```text
pytest test/test_no_stale_axes.py -k parquet_recovery   ->  1 passed   ✅ VAN XANH
pytest test/test_axis_label_vocabulary.py                ->  1 failed   ❌ (test moi)
```

Test cũ hỏi *"nhãn có nằm ngoài `approved_for_live` không?"* — và một chuỗi bịa
thì đúng là nằm ngoài. Nên nó **PASS RỖNG** (*vacuous pass*). Qua test ở đây là
bằng chứng **test còn hở**, không phải bằng chứng nhãn đúng.

**Đã sửa tận gốc**, không sửa tay tệp JSON: `tools/20r2_1_parquet_recovery.py`
gộp nhãn **theo từng trường** (`_reduce_field` / `_reduce_aoi_axis`) và **báo
lỗi** nếu các nguồn bất đồng, thay vì bịa nhãn. Chạy lại công cụ cho ra
`self_calibrated` + `aoi_axis_free` thật. Đối chiếu trước/sau: `summary`,
`rows`, `source_axes` **giống hệt**; chỉ `validity` và `generated_utc` đổi.

**Đã bịt lỗ hổng**: `test/test_axis_label_vocabulary.py` bắt nhãn phải thuộc
**từ vựng suy từ** `docs/phase-23/axis_registry.json`. `null` vẫn hợp lệ — đó
là cách nói "không áp dụng" bằng cơ chế **đã có**, khác hẳn một từ mới.

## Kiểm thử toàn repo và đối chiếu mã gốc

`pytest -q`: **25 failed, 3287 passed, 197 skipped, 13 deselected**,
679,96 giây (11 phút 20 giây). Không báo toàn repo xanh.

Số `passed` tăng 2842 → 3287 so với lần đo trước là do **test mới thêm trong
đợt này** (từ vựng nhãn trục, bất biến z trên artifact đông lạnh, lưới và ngân
sách), không phải do lỗi cũ tự khỏi: **danh sách 25 tên bên dưới khớp từng
dòng** với danh sách trước.

> ⚠️ **Điều kiện đọc con số này.** Nó chỉ so sánh được giữa hai lần chạy
> **cùng môi trường**: env `sdn_rl`, Python 3.12.13, các phiên bản ghim ở
> `requirements-test.txt`, **và** có sẵn cây `results/` đầy đủ. Một clone sạch
> **không** cho cùng con số, và điều đó không có nghĩa repo hỏng — xem mục
> "Vì sao clone sạch ra số khác" bên dưới.

### Danh tính 25 lỗi — theo TÊN, không theo số đếm

**Nhóm N7 — 17 lỗi, cùng một test, cùng một nguyên nhân**
`test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for`
trên 17 artifact ở `results/PENDING/phase-T2/` chưa có khối `validity`:

```text
adjudication_r2.json            hygiene_checks.json
calib_p0925_tau10_report.json   hygiene_checks_r2.json
calib_p0925_tau10_v3_report.json preservation_r2.json
clip_direction_r2.json          realizability_grid.json      <- xem 20R2-L4
conformal_u_cond.json           rms_reference_check_r2.json
conformal_u_cond_load.json      traces/rho_p0925_tau10_s101.meta.json
conformal_u_main.json           traces/rho_p0925_tau10_s102.meta.json
                                traces/rho_p0925_tau10_s103.meta.json
                                traces/rho_p0925_tau10_s104.meta.json
                                traces/rho_p0925_tau10_s105.meta.json
```

**8 lỗi còn lại — liệt kê ĐỦ TÊN, từng cái một**

| # | Test node ID | Nguyên nhân |
|---|---|---|
| 1 | `test_cli_flags_are_wired.py::test_every_declared_flag_is_read_somewhere[tools/g2_kill_test.py]` | cờ CLI khai mà không đọc |
| 2 | `test_cli_flags_are_wired.py::test_every_declared_flag_is_read_somewhere[tools/g3a_omega_sweep.py]` | như trên |
| 3 | `test_cli_flags_are_wired.py::test_every_declared_flag_is_read_somewhere[tools/g3b_sigma_tau_grid.py]` | như trên |
| 4 | `test_no_dangling_parquet_refs.py::test_known_dangling_only_shrinks` | `KNOWN_DANGLING` đã lỗi thời |
| 5 | `test_phase23_cell_margins.py::test_G23_225_canonical_input_preserves_published_numbers[g23-17c]` | lệch số đã công bố g23-17c |
| 6 | `test_g3_dryrun.py::test_quantize_target_is_independent_per_window_rounding` | phụ thuộc thứ tự import |
| 7 | `test_g3_dryrun.py::test_quantization_step_is_smaller_in_dangerous_persistent_cell` | như trên |
| 8 | `test_g3_dryrun.py::test_mixture_acf_has_the_signed_endpoints` | như trên |

Ba lỗi 6–8 **đạt khi chạy riêng**; thu thập chung với
`test_g3b_sigma_tau_grid.py` làm `g3_dryrun.DT_S` bị đổi 0,2 → 0,1. Đây là lỗi
rò trạng thái giữa module, không phải lỗi nội dung.

Cho đến khi có bảng này, câu "không có lỗi mới" vẫn là **lời khai**: một tập
25 phần tử không so được với một tập 25 phần tử khác nếu chỉ biết lực lượng.
Danh sách tên là bằng chứng; số đếm thì không. Đối chiếu bằng **danh sách**.

### Vì sao một clone sạch ra số khác — và vì sao đó không phải repo hỏng

Đã đo và truy nguyên ba nguồn chênh lệch:

1. **Thiếu `results/`.** Nhiều test đọc parquet/JSON ngoài git. Clone sạch
   không có → lỗi hàng loạt, không liên quan chất lượng mã.
2. **Thiếu tag.** `test_closure_tags_exist.py` cần tag đầy đủ; `git clone
   --depth N` cắt mất tag → lỗi giả. Clone **đủ sâu, đủ tag** thì hết.
3. **Thiếu Mininet hệ thống — và đây là cái dễ chẩn sai nhất.**

> Thư mục `mininet/` trong repo **là gói của chính dự án** (`load_spec.py`,
> `rho_schedule.py`, `topology_tandem.py`, …) và **đã nằm trong git — 33 tệp**.
> Nó **trùng tên** với gói Mininet thật. `mininet/__init__.py` xử lý bằng cách
> nối `__path__` tới Mininet hệ thống **khi có**.
>
> Trên máy không cài Mininet, `from mininet.topo import Topo` (trong
> `mininet/topology*.py`) thất bại **lúc THU GOM (collect)**, không phải lúc
> chạy. Vì vậy marker `live` trong `pytest.ini` **không cứu được**: marker chỉ
> bỏ qua ở thời điểm CHẠY, còn lỗi import đã nổ trước đó — nên báo cáo ra
> "collect error", không phải "skip". Kết luận "repo thiếu mininet" là **sai
> chẩn đoán**; đúng là "gói trùng tên + lỗi ở tầng collect".

**Đã làm để con số kiểm được từ bên ngoài:**

- `requirements-test.txt` — ghim numpy/pandas/scipy/pyarrow/pytest đúng phiên
  bản đã đo, kèm ghi chú đầy đủ về bẫy `mininet` ở trên.
- `.github/workflows/tests.yml` — trước đây chỉ `pip install pytest`, nên bước
  chạy cả bộ **không thể** có numpy/pandas/pyarrow. Nay cài từ
  `requirements-test.txt`, và Python CI đổi 3.11 → **3.12** cho khớp môi
  trường đã đo (ghim thư viện mà không ghim Python thì vẫn là hai môi trường).

Phương pháp đối chứng: tách mã tracked ở HEAD gốc sang thư mục độc lập,
dùng lại cây results hiện có, chạy lại các nhóm lỗi; **không** chạy toàn
suite lần thứ hai trên baseline. `verification.json` ghi danh tính từng
lỗi và tập lỗi mới rỗng.

## Tệp kết quả và cách chạy lại

- `results/PENDING/phase-20R2/parquet_recovery.json`: 166 dòng SHA, số hàng, byte.
- `results/PENDING/phase-20R2/recovered_sample.csv`: mẫu số đo lịch sử đầy đủ.
- `results/PENDING/phase-T2/sweep_r2/*.parquet`: dữ liệu gốc được bảo tồn.
- `results/PENDING/phase-20R2/axis_audit.json`: audit trục và ngân sách.
- `results/PENDING/phase-20R2/canary_span.json`: canary span và đối chứng âm.
- `results/PENDING/phase-20R2/realizability_audit.json`: phát hiện đèn xanh rỗng.
- `results/SMOKE/phase-20R2/remediation_smoke.json`: số trước/sau và bit-exact.
- `results/SMOKE/phase-20R2/tau_sweep_cli.json`: kết quả CLI smoke thực tế.
- `results/SMOKE/phase-20R2/verification.json`: tổng hợp kết quả kiểm thử.
- `results/SMOKE/phase-20R2/test_*.md`: log kiểm thử đầy đủ.

```bash
PYTHON=/home/ubuntu/miniforge3/envs/sdn_rl/bin/python
$PYTHON -m tools.20r2_0_axis_audit --out results/PENDING/phase-20R2/axis_audit.json
$PYTHON -m tools.20r2_1_parquet_recovery --out results/PENDING/phase-20R2/parquet_recovery.json --sample-out results/PENDING/phase-20R2/recovered_sample.csv
$PYTHON -m tools.20r2_1_canary_span --out results/PENDING/phase-20R2/canary_span.json
$PYTHON -m tools.20r2_4_realizability_audit --out results/PENDING/phase-20R2/realizability_audit.json
$PYTHON -m tools.20r2_remediation_smoke --out results/SMOKE/phase-20R2/remediation_smoke.json
$PYTHON -m pytest test/test_axis_label_agreement.py test/test_20r2_parquet_recovery.py test/test_phase22_calibv3.py test/test_phase23_dsync_sensitivity.py test/test_phase23_axis_integration.py test/test_phase22_tau.py -q
$PYTHON -m pytest test/test_no_stale_axes.py -q
```
