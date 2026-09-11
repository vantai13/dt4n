# PHASE 20R2 — PRE-REGISTRATION

Trạng thái: **CHƯA KÝ** | Ký tại commit: `<điền sau>` | Tag: `phase-20R2-prereg-signed`
Nguồn số: `results/PENDING/phase-20R2/axis_audit.json`, sinh bởi
`tools/20r2_0_axis_audit.py` (gate 0-1: bảng SINH BỞI CÔNG CỤ, không viết tay).

---

## 0. Cảnh báo phạm vi — đọc trước

Bản prereg này được dựng **chỉ từ những gì có trong checkout**. Hai tài liệu mà
lesson 20R2.0 trích dẫn **không tồn tại trong repo và không có trong lịch sử git**:

```text
PHASE_20R2.md        khong co trong checkout; `git log -S"20R2"` = 0 commit
MASTER_PLAN_v10.md   khong co trong checkout
```

Điều này **được chính repo xác nhận**, không phải suy đoán —
`docs/phase-G/76-amendment-G-A020-omega-reduction.md` §1 và §5 viết:

> *"MASTER_PLAN_v10 và các cấu hình chiến dịch tương ứng không có trong checkout"*
> *"Không có lưới 20R2 đã đóng băng trong repo để sửa trực tiếp."*

**Hệ quả cho việc ký:**

| Mục | Trạng thái |
|---|---|
| A1–A4, A6, A7 (kiểm toán trục, CPU) | ✅ đo được, số trong artifact |
| Danh sách 5 RQ (a–e) | ⚠️ đã điền, **nguồn NGOÀI REPO** — mục 1 |
| Lưới ~~960 ô~~ → **800 ô** | ✅ **suy ra từ bảng khả thi** — mục 0.1 |
| Định nghĩa "một ô" | ✅ **đã xác định từ artifact** — mục 0.1 |

Dòng ⚠️ còn lại **đã được điền** (mục 1) nhưng từ một nguồn **không nằm trong
repo**, nên nó được **gắn nhãn nguồn yếu** thay vì được coi là đã kiểm. Đó là
mức trung thực cao nhất đạt được mà không đưa `PHASE_20R2.md` vào git — và đưa
nó vào git là cách đóng hẳn dòng này.

### 0.1 ★ Định nghĩa "một ô" và kích thước lưới — GIẢI ĐƯỢC TỪ CHECKOUT

Hai dòng trên **không cần** `PHASE_20R2.md` nữa. Chúng suy được từ chính các
artifact đang có trong repo, đúng nguyên tắc "chỉ từ những gì có trong checkout".
Sinh bởi `tools/20r2_0_axis_audit.py`, số nằm ở `axis_audit.json` khoá
`A7_cpu_budget.grid` và `A7_cpu_budget.cells_per_command`.

**(a) Một ô = `(ρ̄, c_a, τ, σ, seed)` — `seed` là MỘT CHIỀU, không phải lần lặp.**

Đo từ `results/PENDING/phase-T2/sweep_r2/run_log.jsonl` (160 lệnh không phải
canary): các trục có mặt là τ (8 giá trị: 0,5 · 1 · 2 · 3 · 5 · 10 · 20 · 28),
`a` (2: 0,5 và 0,9), `seed` (5: 101–105), `branch` (2). Số tổ hợp
(τ, a, seed, branch) đếm được = **160 = 8×2×5×2**, mỗi tổ hợp **đúng một lần**
→ thiết kế đầy đủ giai thừa, không có lần lặp nào.

Trục τ còn được **kiểm chéo độc lập** từ 9 lưới z trong `parquet_recovery.json`:
8 lưới 4 điểm đều thoả `z = τ · {0,1; 0,3; 0,55; 1,0}`, cho đúng tập
τ = {0,5; 1; 2; 3; 5; 10; 20; 28}. Hai nguồn khác nhau, cùng một tập τ.

**(b) MỘT LỆNH `decision_error_v2` phủ 10 ô, không phải 1 ô.**

Cả 166 `*_report.json` đều liệt kê **cùng một danh sách 10 ô** `(c_a, ρ̄)` và
`n_rows` = 10 × (số điểm z). Lệnh lặp qua toàn bộ `feasible_cells()` trong một
tiến trình. Đây là giả định sai nặng nhất của mục 5.2 cũ.

**(c) Lưới là 800 ô, không phải 960 — `cbr@0.925` và `cbr@0.960` KHÔNG khả thi.**

Đọc `results/LIVE/phase-20R/sla_calibration.json`:

| `c_a` | ρ̄=0,700 | ρ̄=0,850 | ρ̄=0,925 | ρ̄=0,960 |
|---|---|---|---|---|
| `cbr` | ✅ | ✅ | ❌ `sigma_max = 0` | ❌ `sigma_max = 0` |
| `poisson` | ✅ | ✅ | ✅ | ✅ |
| `h2` | ✅ | ✅ | ✅ | ✅ |

`summary.n_feasible = 10` trên `n_design_cells = 12`, khớp đúng danh sách 10 ô
mà 166 report đã dùng — **lưới đo thật xưa nay vẫn là 10, không phải 12.**

Hai ô đó còn mang sẵn `role = "pc1_excluded_by_q8"` và `reason =
"sigma_max_regime = 0 (het headroom den tran do tin cay)"` — nghĩa là **chính
artifact hiệu chuẩn đã ghi rõ chúng bị loại**, không cần ai suy diễn.

> ⚠️ Tên trường thật là **`sigma_max`** (và `sigma_rho`), cả hai bằng `0.0`.
> Chuỗi `sigma_max_regime` **chỉ xuất hiện trong văn bản `reason`**, không phải
> tên khoá. Đọc theo câu chữ sẽ tra nhầm khoá và nhận `None`.

Vì `σ = a · sigma_max`, khi `sigma_max = 0` thì σ = 0 với **mọi**
`a`: trục σ **sụp xuống một điểm**, ô mất một chiều nên không còn là ô của thí
nghiệm này. Đây là lý do **loại ô**, không phải "một ô có σ nhỏ".

```text
LUOI DUNG = 10 (c_a x rho kha thi) x 8 tau x 2 sigma x 5 seed = 800 o
960 = 12 x 8 x 2 x 5  -- nhan bon so ma KHONG tra bang kha thi
```

Tên phase là *"Decision error trên chế độ **KHẢ THI**"*; chạy 160 ô không khả
thi mâu thuẫn với chính tên phase.

---

## 1. RQ và estimand

| Mã | Câu hỏi | Đo bằng gì |
|---|---|---|
| `RQ-20R2a` | Twin sai quyết định bao nhiêu theo tuổi `z`? | `err(z \| chế độ)` |
| `RQ-20R2b` | Sai đó **giá** bao nhiêu? | `d_sla(z)` — vi phạm SLA |
| `RQ-20R2c` | `err` biến thiên thế nào theo `τ` trên miền khả thi? | trục chính của v10 |
| `RQ-20R2d` | Twin có khớp Sheppard không? | `err = arccos(exp(−z/τ))/π` |
| `RQ-20R2e` | ★ Kết quả điều kiện theo **trục nào**? | ⟵ `20R2.0` trả lời |

**Nguồn 5 RQ: `PHASE_20R2.md` MỤC 1**, chép qua phiên hướng dẫn 2026-09-09.

> ⚠️ Tài liệu này **không có trong checkout** và **chưa từng được thêm vào git**.
> Đo lại 2026-09-09, chính xác đến từng lệnh:
>
> ```text
> git log --all --diff-filter=A -- '**/PHASE_20R2.md'     -> 0 commit
> git log --all --diff-filter=A -- '**/MASTER_PLAN_v10.md' -> 0 commit
> git log -S"RQ-20R2" -- .                                 -> 1 commit (665bebe9)
> git grep -l "RQ-20R2" HEAD  -> docs/phase-20R2/00-preregistration.md  (CHỈ MỘT)
> ```
>
> Lệnh thứ ba **không** phản chứng hai lệnh đầu — nó chỉ tìm thấy **chính tài
> liệu này**, tức bản đã chép. Nói cách khác danh sách 5 RQ trong repo là
> **tự quy chiếu**: nguồn duy nhất của nó là bản chép của chính nó. Đó đúng là
> định nghĩa của "không tự kiểm được".
>
> Cách duy nhất để ai đó kiểm là đưa `PHASE_20R2.md` vào git. Ghi nhãn nguồn
> yếu là đủ để dùng — giấu nó thì không.
>
> `RQ-20R2e` là mục **được thêm**, không có trong `MASTER_PLAN_v10`: T2 đã chứng
> minh nó quyết định mọi câu còn lại (T2-L5, T2-L8).

### 1.1 ★ CÂU HỎI MỞ — `cbr` là một MỨC hay một ĐỐI CHỨNG? (phải trả lời ở 20R2.2)

`PHASE_20R2.md` §0.1 coi `c_a ∈ {cbr, poisson, h2}` là **một trục ba mức**, tức
ba mức **cùng loại**. Nhưng `sla_calibration.json` nói khác — `role` đo được:

| `c_a` | ρ̄=0,700 | ρ̄=0,850 | ρ̄=0,925 | ρ̄=0,960 |
|---|---|---|---|---|
| `cbr` | `pc1` | `pc1` | `pc1_excluded_by_q8` | `pc1_excluded_by_q8` |
| `poisson` | `gate` | `gate` | `gate` | `gate` |
| `h2` | `gate` | `gate` | `gate` | `gate` |

Và `summary` của chính artifact đã **phân hoạch sẵn**: `n_gate_cells = 8`,
`n_pc1_cells = 4`. `pc1` = *positive control 1* — **nhánh đối chứng**, không
phải một mức điều trị.

```text
NEU cbr CUNG population voi poisson/h2
    -> c_a la truc 3 muc; luoi KET QUA = 800 o
NEU KHONG
    -> luoi KET QUA  = 2 (poisson,h2) x 4 rho x 8 tau x 2 sigma x 5 seed = 640
       luoi DOI CHUNG= 2 (cbr kha thi)         x 8 tau x 2 sigma x 5 seed = 160
       va 160 o cbr duoc bao cao RIENG nhu doi chung duong
                                                        640 + 160 = 800
```

⚠️ **Ngân sách KHÔNG đổi trong cả hai trường hợp** (vẫn 800 ô, 29,4 phút hai
nhánh) — cái đổi là **POPULATION của estimand**, tức được phép kết luận về ai.
Nên câu hỏi này **không chặn việc ký**, nhưng **chặn việc khai estimand**:
`POPULATION` là một trong 7 trường bắt buộc của `estimand_id` (H4), nên phải
trả lời **trước** khi đo, không phải sau.

**Chưa quyết ở đây.** Ghi làm câu hỏi mở của Lesson 20R2.2.

`estimand_id` khai ở Lesson 20R2.2. **⛔ KHÔNG tái dùng `RMS_ALLACTION_DELAY`**
cho claim về margin: khác LEVEL (`all_action` vs `margin`) và khác SCALE
(`delay_ms` vs `cost_ms`). Đây là va chạm đã trả giá một lần:

```text
RMS_MARGIN_COST      LEVEL=margin      SCALE=cost_ms    moc 2.1400 ms
RMS_ALLACTION_DELAY  LEVEL=all_action  SCALE=delay_ms   moc 0.3405 ms
                                                        ti le 6.285x
```

Nguồn: `docs/GLOSSARY.md:145-192`, `cert/tau_sweep.py:35`,
`measurements/decision_error_v2.py:48`. [A-T2-3]

---

## 2. Kết quả kiểm toán trục (Lesson 20R2.0)

### A1 — Đã khắc phục mặc định `_valid_rows` (20R2.1)

`axis` là keyword-only bắt buộc; gọi thiếu hoặc truyền theo vị trí sẽ lỗi
trước khi sinh dữ liệu. Audit mới ghi **0 caller thiếu axis** trong các
harness, kể cả `cert/aoi_profiles.py` và `cert/cell_matrices.py`.
`tau_sweep` nhận `--axis` bắt buộc qua `sweep` → `build_at_tau` → `_valid_rows`.
Harness Phase 22 chỉ nhận legacy vì z-bin/z-rep/ratio bands đã khóa theo
trục ấy; measured bị từ chối tường minh, cần prereg mới.
Các API builder cấp cao còn giữ mặc định tương thích Phase 22;
không diễn giải gate này là đã xóa mọi mặc định axis trong toàn repo.

Audit bổ sung caller trực tiếp bộ sinh, hàm chứa và điều kiện `axis` bao
quanh. Đây là bằng chứng phục vụ rà soát, không phải chứng minh luồng điều
khiển tổng quát. Metadata `build_one_v3` đã chọn đúng bộ sinh theo axis.
Test: `test/test_axis_label_agreement.py`; số đo trước/sau:
`results/SMOKE/phase-20R2/remediation_smoke.json`.

### A2 — Trục SLA

| Nhãn | Trạng thái | Nội dung |
|---|---|---|
| `self_calibrated` | **DEPRECATED** (S14) | ngưỡng suy từ chính dữ liệu được đánh giá |
| `exogenous_g114_S-B` | **ACTIVE**, approved_for_live | `T_delay=50 ms` (ITU-T G.114), `T_loss=1%`, `w_loss=5000` |

`w_loss` của `self_calibrated` **biến thiên theo ô** — đo được:
`1245.6 … 4722.7` (`docs/phase-21R/99-gate-decision.md:79-88`).
`exogenous` cho **5000 cố định mọi ô**.

⟹ đổi trục SLA **không phải đổi một số**, mà đổi **9 số khác nhau thành 1**.
Ô có `w_loss` thấp nhất (1245.6, `cbr@0.700`) chịu thay đổi mạnh nhất
(hệ số 4.01×). Ghi vào Threats to Validity **trước**, không để thành bất ngờ.

### A3 — Độ lệch hai trục AoI, **MIỀN MÔ HÌNH** (dt = 0.005 s, n = 20 000)

```text
truc        n      p05     median   mean     p95     min     max     CV
legacy    19989  0.0770   0.3000   0.3024  0.5250  0.055   0.550   0.4771
measured  19899  0.1400   0.3650   0.3659  0.5900  0.115   0.615   0.3945
                                   ti le trung vi = 1.2167  (lech 21.7%)
```

Tham số nguồn: `measurements/decision_error.py:37-38` (`d=0.051`, `T=0.5`);
`measurements/aoi_model_v7.py:38-40` (`d=0.1159 ± 0.0065`, `T=0.5002922`).

### A3b ★ — Trục measured **THỰC NGHIỆM** khác trục measured **MÔ HÌNH**

Đây là mục **không có trong lesson**, và nó đổi kết luận của mục 4.

Registry ghi cho `measured_v7_uniform`: *"Đo lại trên v7 cho p05=143.072 ms,
mean=368.924 ms, CV=0.419529."* Đó là số **đo trên mạng**
(`docs/phase-23/20-aoi-on-topology-v7.md:71`, 15 run, CI95, amendment 44).
Nhưng bộ sinh mà pipeline **thực sự gọi** (`base_age_steps`, U0) cho:

| | E1/p05 | p50 | mean | p95 | p99 | max | CV |
|---|---:|---:|---:|---:|---:|---:|---:|
| MÔ HÌNH (`base_age_steps`, U0) | 0.1400 | 0.3650 | 0.3659 | 0.5900 | — | **0.6150** | **0.394506** |
| THỰC NGHIỆM (CLEAN, đo) | 0.1431 | 0.3583 | 0.3689 | 0.5879 | 0.6275 | **1.5689** | **0.419529** |

Hai chỗ lệch, **cả hai đều đã được ghi là MISS từ Lesson 23.20**:

```text
M-72   CV CLEAN = 0.419529 ngoai bang du doan [0.32, 0.41]        MISS
M-72b  CV sawtooth ky vong = 0.367286; gap = 0.052243 > 0.05      MISS
```

⟹ mô hình uniform-phase **hẹp hơn thực nghiệm ở cả hai đầu**: CV thấp hơn
5.96%, và đuôi phải kết thúc ở 0.615 s — **dưới cả p99 đo được (0.6275 s)**,
còn max thực nghiệm là **1.5689 s, gấp 2.55 lần** max mô hình.

**Đây không phải lý do bỏ mô hình** — pipeline gọi nó, nên miền mô hình là
miền mà `err(z)` thực sự được đánh giá. Đây là lý do phải **ghi rõ mọi kết
luận là điều kiện theo MIỀN MÔ HÌNH**, và ghi đuôi phải chưa đo vào
Threats to Validity.

### A3′ ★ — Lưới z cố định chính là trục legacy hoá trang

```text
Z_GRID (decision_error_v2.py:57)      = (0.0, 0.05, 0.10, 0.20, 0.30, 0.55)
Z_EDGES_PRIMARY (build_calib_set_v2:50) = (0.055, 0.10, 0.20, 0.30, 0.5501)
                                           ↑ legacy d          ↑ legacy d+T
```

Lưới z "tiền đăng ký" phủ **khít miền legacy [0.055, 0.550]**. Trên trục
measured [0.115, 0.615], kết quả kiểm miền (A6, sinh bởi công cụ):

```text
Z_GRID hien tai vs MO HINH measured:
    NGOAI SUY tai z = [0.0, 0.05, 0.10]     <- BA diem, khong phai mot
    p95: KHONG cham    max: KHONG cham
```

> **Đính chính lesson.** Lesson 20R2.0 chỉ nêu `z = 0.05` nằm ngoài miền.
> **`z = 0.10` cũng nằm ngoài** (0.10 < 0.1159). Tính cả `z = 0` (đối chứng)
> thì **3 trong 6 điểm** của lưới hiện tại là ngoại suy trên trục measured,
> không phải 1. [NT 63 — kỷ luật phạm vi]

---

## 3. ★ A5 — QUYẾT ĐỊNH TRỤC (ký ở đây)

Chọn: **lối (iii) TÁCH ĐÔI**, đổi **một yếu tố một lúc**.

```text
NHANH CHINH      aoi = measured_v7_uniform     sla = exogenous_g114_S-B
                 -> moi claim khoa hoc cua 20R2
                 -> results/LIVE/phase-20R2/       (chi sau khi A5 duoc KY)

DOI CHUNG AM     aoi = assumed_sawtooth_51ms   sla = exogenous_g114_S-B
                 -> CHI de do "doi truc AoI lam err doi bao nhieu"
                 -> results/SUPERSEDED/phase-20R2/
```

⚠️ **Trục SLA GIỮ NGUYÊN giữa hai nhánh.** Đổi cả hai cùng lúc thì chênh lệch
quan sát được là hiệu ứng **gộp** của hai thay đổi và không quy trách nhiệm
được (one-factor-at-a-time).

Lý do chọn:

- `z` **là trục chính** của phase; chạy nó trên nhãn DEPRECATED là lặp lại S12
- chênh lệch hai trục **là kết quả**: lượng hoá cái giá của lỗi cấu trúc S12,
  trả lời trực tiếp RQ-20R2e
- nhánh legacy đúng vai trò **NEGATIVE CONTROL** mà chính docstring
  `cert/build_calib_set_v3.py:281` đã gán cho nó
- chi phí: xem mục 5 — hai nhánh vẫn dưới ngưỡng, **nếu** đơn vị ô được xác định

Ký bởi: `<tên>`   Ngày: `<ngày>`   Commit: `<sha>`

---

## 4. Lưới z

**NHÁNH CHÍNH** — neo vào `Z_EDGES_V7` (`measurements/aoi_model_v7.py:68`,
đã khoá ở amendment 23-48):

```python
Z_GRID_20R2_MEASURED = (
    0.115,   # d_base -- SAN THAT cua truc mo hinh
    0.170, 0.241, 0.305, 0.366, 0.430, 0.491, 0.555,
    0.615,   # max cua truc MO HINH
)
Z_CONTROL = (0.0,)           # DOI CHUNG: err(0) = err_model = SAN mo hinh.
                             # KHONG phai diem van hanh -- tren truc measured
                             # tuoi khong bao gio bang 0 (san d = 115.9 ms).
Z_EXTRAP  = (1.0, 2.0, 4.0)  # gan co extrapolated=True
```

Kết quả kiểm miền (A6): lưới này **nằm trọn trong miền mô hình measured**,
chạm p95 và max mô hình. ✅

**Nhưng — hai điều phải ghi kèm, không được bỏ:**

1. **Không chạm p99 thực nghiệm (0.6275 s) và không chạm max (1.5689 s).**
   Đuôi phải của tuổi thật **không được đo** bởi lưới này.
2. `z = 1.0` nằm dưới max thực nghiệm 1.5689 s; `z = 2.0` và `4.0`
   nằm ngoài cả miền mô hình lẫn miền thực nghiệm đã đo.
   Gắn cờ `extrapolated=True` phải nói rõ **ngoại suy so với miền nào**.

> Cả hai cờ đã có sẵn trong code: `measurements/decision_error_v2.py:489`
> (`"extrapolated": bool(float(z_s) in Z_EXTRAP)`) và `err_model` được tính
> riêng ở dòng 463 (`err_model_const`). Dùng lại, đừng viết mới.

**ĐỐI CHỨNG ÂM**: giữ nguyên `Z_GRID` legacy để so được với T2.

---

## 5. Ngân sách CPU (ĐÍNH CHÍNH RT20-4 — và đính chính chính lesson)

### 5.1 Tỉ lệ `n_for_tau`: 1.4×, không phải 56×

`n_for_tau` **có sàn** `n_floor = DEFAULT_N = 200_000`
(`measurements/sla_calib_v2.py:65`). Đo thật tại `dt = 0.005`:

```text
tau <= 20  -> n = 200 000   (SAN chi phoi)
tau = 28   -> n = 280 000   (cong thuc chi phoi)
ti le tau=28 / tau=0.5 = 1.400        RT20-4 ghi 56  -> SAI
diem giao o dung tau = 20
```

### 5.2 ⚠️ Nhưng tỉ lệ `n` **KHÔNG PHẢI** ngân sách

Đây là chỗ lesson 20R2.0 kết luận vội. Ngân sách phải đo bằng **giây trên
lệnh thật**, và hai harness trong repo lệch nhau **3.6 lần**:

| run_log | lệnh | n | giây/lệnh (min–max, mean) | ~~960 ô~~ (ĐÃ BỎ) |
|---|---|---:|---|---:|
| `sweep_r2` | `decision_error_v2 --run-fixed`, **1 τ × 1 seed** | 166 | 9.25 – 15.30, **mean 11.05** | ~~2.95 h~~ |
| `sweep_r3` | `cert.tau_sweep --taus 0.5..28`, **8 τ × 5 seed** | 18 | 37.77 – 41.73, **mean 39.87** | ~~10.63 h~~ |

> ⛔ **Cột cuối đã bị bác bỏ** — nó nhân `mean` với 960 và giả định 1 lệnh = 1 ô.
> Cả hai giả định đều sai (mục 0.1). Giữ lại để đối chiếu, **không dùng để ký**.
> Nhãn "1 τ × 1 seed" của `sweep_r2` cũng thiếu: mỗi lệnh còn quét **10 ô**
> `(c_a, ρ̄)` bên trong.

> **Đính chính lesson.** Lesson ghi *"11.6–15.0 s/lệnh"*. Khoảng thật của
> `sweep_r2` là **9.25–15.30 s** (mean 11.05); `11.62` là **bản ghi đầu tiên**
> của file, không phải cận dưới. Kết luận ~3.5 h/nhánh vẫn **an toàn vì bảo
> thủ** (thật là 2.95 h), nhưng con số trích dẫn thì sai. [W4 — hằng số phán
> quyết: một nguồn, IMPORT, không chép]

**★ ĐÃ KẾT LUẬN ĐƯỢC (2026-09-09).** Điều kiện chặn ở mục 0 nay đã giải xong,
nên phần dưới đây thay cho lập luận "nếu/thì" cũ.

Uớc tính cũ **2,95 h/nhánh sai 12 lần**, do **hai** sai số cùng chiều nhân lên:

```text
sai so (1)  coi 1 LENH = 1 O                he so 10.0
            thuc te 1 lenh decision_error_v2 phu 10 o (muc 0.1b)
sai so (2)  coi luoi = 960 O                he so  1.2
            thuc te 800 o (muc 0.1c)
                                   tich  =  12.0x
```

Ngân sách thật, đo từ `sweep_r2/run_log.jsonl`, 160 lệnh không phải canary
(sinh bởi `tools/20r2_0_axis_audit.py`, khoá `A7_cpu_budget.harness_seconds.*.corrected`):

| Đại lượng | Giá trị |
|---|---:|
| Tổng thời gian 160 lệnh không canary | 1.764,4 s |
| Điểm lưới đã phủ (160 lệnh × 10 ô) | 1.600 |
| **Chi phí một ô** | **1,1028 s** |
| Lưới 20R2 = 800 ô → một nhánh | 882 s = **14,7 phút** |
| Hai nhánh | 1.764 s = **29,4 phút** |
| Hai nhánh + 30% dự phòng | **38,2 phút** |

Chú ý một điều làm con số này **mạnh hơn một phép ngoại suy**: 160 lệnh × 10 ô
= 1.600 = **đúng 800 ô × 2 nhánh**. Chiến dịch đã chạy có **cùng kích thước**
với lưới 20R2, nên 1.764 s là một **phép đo của chính khối lượng đó**, không
phải suy rộng từ mẫu nhỏ. Dự phòng 30% dành cho lưới z 20R2 dày hơn (mục 4)
chứ không phải cho bất trắc về kích thước lưới.

⟹ **KẾT LUẬN CÓ NGUỒN: không cần fractional design (E4).** 38 phút so với trần
8 h — dư hai bậc độ lớn. Kết luận này neo vào `axis_audit.json`, đo lại được
bằng lệnh ở mục 10; nó không phải một lời khai.

⚠️ Cảnh báo khi ký gate `20R2-5` ("CPU khớp ước tính ±30%"): ước tính được ký
phải là **29,4 phút hai nhánh**, không phải 5,89 h. Ký con số cũ là tự đặt bẫy —
một lần chạy 40 phút sẽ "vượt ước tính" theo hướng ngược lại.

Ghi chú: `sweep_r3` amortize tốt hơn (39.87 s / 40 tổ hợp ≈ **1.0 s** mỗi
(τ, seed), so với 11.05 s của `sweep_r2` cho 1 tổ hợp) — chi phí khởi động
chi phối. Nếu 20R2 gom τ theo lô như r3 thì ngân sách **rẻ hơn nhiều** so với
cả hai ước tính trên. Đây là một lựa chọn thiết kế, phải ký, không mặc định.

---

## 6. Dự đoán Sheppard — TÍNH LẠI, KHÔNG CHÉP

```text
err(z, tau) = arccos(exp(-z/tau)) / pi          (Sheppard 1898)
```

| τ | z=0.3650 (CHÍNH, measured mô hình) | z=0.3000 (ĐỐI CHỨNG, legacy) | z=0.3583 (thực nghiệm p50) |
|---:|---:|---:|---:|
| 0.5 | 0.3399 | 0.3151 | 0.3375 |
| 1.0 | 0.2558 | 0.2344 | 0.2536 |
| 2.0 | 0.1865 | 0.1700 | 0.1848 |
| 3.0 | 0.1539 | 0.1400 | 0.1525 |
| 5.0 | 0.1202 | 0.1092 | 0.1191 |
| 10.0 | 0.0855 | 0.0776 | 0.0847 |
| 20.0 | 0.0606 | 0.0550 | 0.0600 |
| 28.0 | 0.0513 | 0.0465 | 0.0508 |

⛔ **Bảng của MASTER_PLAN (z = 0.369) KHÔNG dùng**: lệch −0.5% so với
measured, **−9.3% so với legacy**. Nếu băng chấp nhận là ±10% thì chọn sai
trục **ăn gần hết băng** — mọi gate thành không đọc được. Chép mù = **W4**.

`Z_MEDIAN_S = 0.369` (`measurements/link_corr_matrix.py:62`) chú thích là
*"trung vị AoI đo được"*: nó thuộc họ **measured**, gần trung vị mô hình
(0.3650) trong 1.1%, và gần trung vị **thực nghiệm** (0.3583) trong 3.0%.
Không sai, nhưng không phải số nên chép.

**Sheppard là ĐƯỜNG THAM CHIẾU, không phải sự thật.** Giả định bị vi phạm ở
4 chỗ đã biết:

```text
Sheppard gia dinh          He cua ban
margin chuan 2 chieu       margin = hieu chi phi PHI TUYEN theo rho
ky vong 0                  err_model != 0 -> co bias
chi 2 hanh dong            4 duong, argmin trong 4, khong phai doi dau
tuong quan thuan AR(1)     co nugget MA(1) + clip o RELIABLE_CEILING
```

**LỆCH LÀ KẾT QUẢ, không phải thất bại.** [NT 21 — kết quả âm có kiểm soát
là dữ liệu]

---

## 7. A4 — Điều kiện G-A020 §4: **FAIL**

Kiểm bằng công cụ trên `docs/phase-G/76-amendment-G-A020-omega-reduction.md`:

| Chiều | G-A020 §4 thiết lập trên | 20R2 thực tế | |
|---|---|---|---|
| `dt` | 0.1 s | **0.005 s** (20× mịn hơn) | ❌ |
| `tau` | cố định 3 s | **trục quét** {0.5 … 28} | ❌ |
| estimand | rank-slot coverage/acceptance | **err(z), d_sla** | ❌ |
| quy tắc xếp hạng | 4 hành động / **3 khe xếp hạng** | 4 đường, **argmin top-1** | ❌ |
| số claim | ≤ 3 claim | **5 RQ (a–e)** | ❌ |
| `alpha` | 0.10 | 0.10 | ✅ |

§4 nói rõ: *"Nếu phase sau có hơn 3 claim, đổi tập hành động, đổi liên
thuộc/link chung, quy tắc xếp hạng hoặc estimand, G-A020 **tự động hết hiệu
lực** cho phase đó."* Và §1: *"Mỗi phase phải kiểm điều kiện trước khi áp dụng."*

⟹ **G-A020 KHÔNG chuyển giao sang 20R2. Ghi FAIL.**

Điều này **không** buộc quét ω trở lại. Nó buộc **đổi lý do**:

```text
❌ CACH VIET SAI (thua huong lang le):
   "omega duoc rut khoi luoi theo G-A020 §1.1."
   -> §4 khong cho phep. Day la mot quyen KHONG TON TAI.

✅ CACH VIET DUNG (quyet dinh cua chinh minh, co trach nhiem):
   "Dieu kien G-A020 §4 duoc kiem cho estimand err(z|che do): FAIL tren
    dt, tau, estimand, quy tac xep hang va so claim. G-A020 do do KHONG
    chuyen giao duoc sang 20R2.

    20R2 van co dinh omega = omega_0 nhu mot QUYET DINH NGAN SACH cua
    RIENG PHASE NAY, KHONG phai nhu mot ket luan thua ke. He qua:
      · gate 20R2-3 VOID vi omega khong phai truc -- KHONG vi G-A020
      · moi ket luan cua 20R2 dieu kien theo omega = omega_0, PHAI ghi vay
      · sigma_eff_proxy = sigma * c(omega_0) bao cao cho moi o
        (§3 G-A020 VAN dung duoc: cong thuc covariance la CHINH XAC,
         chi phan SUY GIAM THUC NGHIEM moi het hieu luc)
      · buoc sang re (§4): tinh lai covariance/contrast SD o dt = 0.005 va
        tau trong luoi 20R2 -> ghi vao prereg. Vai giay CPU.
        ⚠️ §4 noi ro: buoc nay CHI SANG LOC, KHONG tai chung nhan."
```

Khác biệt giữa hai cách viết không phải chữ nghĩa: cách thứ nhất **giấu** rằng
đang có một quyết định; cách thứ hai **nhận trách nhiệm**. Cùng một lưới, hai
mức độ tin cậy hoàn toàn khác nhau.

---

## 8. Sổ giới hạn thừa kế

```text
T2-L5   T2 chay tren truc SLA self_calibrated (DEPRECATED, S14)

T2-L8 ★ DINH CHINH co che: T2 KHONG chay qua sawtooth_age_steps trong
        `run_cell`. `decision_error_v2.run_cell` dung do TRE TAT DINH
        k = round(z/dt) (dong 465), khong goi bo sinh AoI nao.
        `sawtooth_age_steps` chi duoc goi o dong 680, trong
        `_sawtooth_metric_series` -- mot duong KHAC.
        T2-L8 DUNG ve tinh than (ket qua neo vao mien legacy), SAI ve co
        che (khong phai qua bo sinh, ma qua LUOI z trung khit mien legacy).

20R2-L1 ★ MOI: moi ket luan dieu kien theo MIEN MO HINH cua truc AoI.
        Duoi phai thuc nghiem (p99 = 0.6275 s, max = 1.5689 s) KHONG duoc
        do boi luoi z nao dang de xuat. CV mo hinh thap hon thuc nghiem
        5.96% (MISS M-72 / M-72b da ghi tu Lesson 23.20).

20R2-L2 [DA GIAI -- 2026-09-09] don vi "mot o" chua duoc dinh nghia.
        GO BO vi da xac dinh duoc TU CHECKOUT, khong can PHASE_20R2.md:
        mot o = (rho_bar, c_a, tau, sigma, seed); 1 lenh = 10 o; luoi = 800
        (muc 0.1). Ngan sach = 29,4 phut hai nhanh -> KHONG can fractional
        design (muc 5.2). Ly do go: dieu kien chan da duoc do, khong phai
        duoc mien.
        CON HIEU LUC: QD-33 -- KHONG tru 166 lenh khoi ngan sach moi
        (reuse = 0) du da bao ton du 166/166 parquet, vi truc SLA khac.
        Gate CPU +/-30% van CHUA xac nhan (chua chay luoi that).

20R2-L4 ★ MOI: `results/PENDING/phase-T2/realizability_grid.json` bao
        96/96 REALIZABLE, n_rejected = 0, rejected_by_reason = {}.
        DEN XANH RONG. Do duoc 2026-09-09 boi
        tools/20r2_4_realizability_audit.py:
          - 3/9 tieu chi KHONG CHAY o BAT KY o nao trong 96 o:
            censoring_ok, mondrian_cells_populated, sigma_feasible
          - `failed = []` o ca 96 o, nhung `passed` cung RONG o ca 96 o
          - verdict xanh vi KHONG AI HOI, khong phai vi DA TRA LOI
          - doi chung cheo: 16 o duoc gan REALIZABLE trong khi
            sla_calibration.json da noi cbr@0.925 va cbr@0.960 KHONG kha thi
            (sigma_max = 0, sigma_rho = 0, role = pc1_excluded_by_q8)
            -- dung tieu chi `sigma_feasible` bi bo qua
        ⟹ KHONG ke thua ket luan kha thi cua T2. Lesson 20R2.4 phai CHAY LAI
          gate voi DU tham so (sigma, clip_fraction, min_cell_blocks) va
          assert not_evaluated == [].
        Song song voi T2-L6 (tieu chi headroom khong hoat dong cho toi
        T2.4-fix): cung mot co che, khac tieu chi.
        [W5, RT20-7, gate 20R2-4 muc 4-2]
        Nguyen tac rut ra: mot verdict PASS chi co nghia khi biet BAO NHIEU
        tieu chi da thuc su chay. Phu luc B ghi "mot co che phong thu DO
        THUONG TRUC thi da chet"; day la mat kia cua dong xu -- XANH THUONG
        TRUC cung da chet, va nguy hiem hon vi khong ai di kiem den xanh.

20R2-L5 ★ MOI: nhan truc BIA DAT qua duoc test_no_stale_axes mot cach RONG.
        Do duoc 2026-09-09: gan `MIXED_OR_MISSING` vao
        parquet_recovery.json -> `pytest -k parquet_recovery` VAN XANH
        (1 passed), vi test PENDING chi hoi "nhan KHONG nam trong
        approved_for_live" -- ma mot chuoi bia thi dung la khong nam trong.
        Da bit bang test/test_axis_label_vocabulary.py (nhan phai thuoc TU
        VUNG suy tu axis_registry.json). `null` van hop le: do la cach noi
        "khong ap dung" bang co che DA CO, khac han voi mot tu moi.
        [cung lop loi voi `vacuous pass` o test_no_stale_axes.py]

20R2-L6 ★ MOI: phan loai `axis_role` THIEU O cho hai truong hop that.
        Do duoc 2026-09-09. Nhanh LIVE cua test_no_stale_axes.py:201 doi
        `assert "z_grid_s" in aoi_axis` cho MOI artifact khai aoi_axis_free.
        Ba artifact 20R2 deu KHONG thoa, vi HAI ly do KHAC NHAU:

          (1) LUOI SO NHIEU -- artifact chay tren NHIEU luoi z co dinh:
              parquet_recovery.json, canary_span.json  -> co `z_grids_s`
              (so nhieu), khong co `z_grid_s`. Dinh nghia AXIS_FREE trong
              measurements/validity.py viet "luoi z CO DINH" o so it, nen
              khong mo ta duoc artifact tong hop nhieu run.
          (2) KHONG CO LUOI NAO -- artifact KIEM TOAN SO SACH:
              realizability_audit.json khong dung truc z, ke ca co dinh.
              No khong phai consumes (khong dung z), khong phai measures
              (khong do z), khong phai axis_free (khong co luoi nao de ghim).
              Ba vai tro hien co khong vai tro nao mo ta dung no.

        Hien ca ba o PENDING/ nen nhanh LIVE khong cham toi -> XANH. Chung se
        DO khi promote, va luc do cam do la gan mot `z_grid_s` GIA cho qua --
        DUNG MOT TOI voi `MIXED_OR_MISSING` (20R2-L5): bia mot gia tri de mua
        mot den xanh, thay vi khai dung rang phan loai chua co o cho minh.

        ⟹ KHONG gan z_grid_s gia. Hai loi thoat hop le:
           (a) them vai tro `bookkeeping_audit` va cho phep `z_grids_s`
               QUA MOT AMENDMENT, hoac
           (b) giu ba artifact o PENDING/ vinh vien va ghi ly do tai day.
        Chua chon; phai chon TRUOC khi promote bat ky cai nao.
        [lien quan: 20R2-L5, test_no_stale_axes.py:201]

20R2-L7 ★ MOI: artifact chua DUONG DAN TUYET DOI cua may sinh ra no.
        Do duoc 2026-09-09: hai cong cu 20R2 moi (`20r2_1_canary_span.py`,
        `20r2_4_realizability_audit.py`) ghi 3 truong dang
        "/home/ubuntu/dt4n/..." vao artifact. Chay lai tren may khac cho DUNG
        MOI CON SO nhung KHAC BYTE.
        Ba ly do phai sua, khong phai mot:
          (1) TAI LAP  -- 20R2.3 doi golden BIT-EXACT. Artifact khong tai lap
              lien may khong lam golden duoc; no se do moi lan CI chay.
          (2) RO       -- ten nguoi dung + bo cuc may di theo thu se cong bo.
          (3) NHAT QUAN-- `20r2_0_axis_audit.py` DA lam dung tu dau
              (os.path.relpath(..., REPO)). Mot phase co hai quy uoc la mot
              phase chua co quy uoc nao.
        DA SUA ca ba truong; da them test/test_no_absolute_paths_in_artifacts.py.

        ★ Va no lo ra mot NO LON HON: quet ca cay results/ thay 39 artifact
        thua ke cung mac loi nay -- 15 SMOKE/phase-20R, 7 PENDING/phase-23,
        7 LIVE/phase-23, 5 SMOKE/phase-G2, 5 PENDING/phase-T2. Bay trong so do
        o LIVE/ (sha duoc trich dan noi khac) nen phai qua amendment.
        Xu ly HAI TANG, co chu dich:
          TANG 1 CHAN     phase-20R2 -- do tuyet doi neu vi pham.
          TANG 2 BANH COC 39 tep ghim thanh danh sach; danh sach CHI DUOC NGAN
                          DI. Them tep moi -> do; sua duoc mot tep -> cung do,
                          kem loi nhac xoa khoi danh sach.
        Vi sao khong bat ca 39 do ngay: 39 dong do thuong truc se lam ca bo
        test bi lo di -- dung loi "DO THUONG TRUC thi da chet" (Phu luc B), va
        la mat kia cua 20R2-L4 (XANH THUONG TRUC).

20R2-L3 Hai he ten truc cung ton tai: measured_v7 -> measured_v7_uniform;
        legacy_sawtooth_51ms -> assumed_sawtooth_51ms. Anh xa 1-1 khoa boi
        test/test_axis_label_agreement.py, doi chieu validity suy tu SHA.
20R2-L8 ★ MOI (20R2.4): `results/PENDING/phase-T2/realizability_grid.json`
        duoc sinh boi GATE_VERSION 1, khong phai 2.
        Do duoc 2026-09-10: derived.gate_version = None (truong chua ton tai
        o v1), tieu chi ten `sigma_feasible` (ten cu), khong co
        derived.sigma_max_regime, 96/96 REALIZABLE voi 3/9 not_evaluated o
        MOI hang.
        Luoi thua ke VO HIEU vi BA ly do DOC LAP:
          (1) SAI PHIEN BAN   v1, E1 doi v2.
          (2) 3/9 TIEU CHI KHONG CHAY  -- va `verdict` chi nhin `failed`, nen
              tieu chi khong chay khong bao gio doi duoc phan quyet:
              DEN XANH RONG (cert/realizability_gate.py:195).
          (3) TIEU CHI DA CHAY LA TIEU CHI MA. v1 chi kiem `sigma > 0`, ma
              tau_sweep luon truyen sigma thiet ke duong => KHONG BAO GIO fail
              duoc. `from twin import cost_v2 as C` la DEAD IMPORT: do tren
              commit 54a05ddc, `grep -c "C\."` = 0, trong khi thong diep `why`
              van nhac `sigma_max_regime`. Nguoi doc thong diep se tin rang
              tran DA duoc kiem.
        => E1 sinh lai TOAN BO bang v2. Da lam: grid_prescreen.json, 160/160.
        Bang chung: CUNG o cbr@0.925, goi THIEU sigma -> REALIZABLE; goi DU
        sigma -> REJECTED (sigma_max_regime = 0.0).
```

---

## 9. Đính chính thuật ngữ — NT bị trích sai trong lesson 20R2.0

`docs/NT_REGISTRY.md:123-142` có một mục riêng về **va chạm ID/nội dung**, và
nó nêu đích danh hai trích dẫn mà lesson 20R2.0 dùng:

| Lesson trích | Nội dung thật | Registry |
|---|---|---|
| **NT 49** = "suy ràng buộc từ định luật" | cấm RÚT kết quả, chỉ được đổi nhãn | ghi thẳng: trích như vậy là **SAI** |
| **NT 50** = "câu chuyện nhân quả phải có bằng chứng máy móc" | đổi một giá trị NGUỒN phải xử lý mọi thứ PHÁI SINH; xoá theo NGHĨA không theo TÊN | va chạm nội dung |

Hai nội dung được trích ở trên **không có ID**. Theo registry: *"Viết chúng
trần, hoặc cấp số mới qua amendment."* Prereg này viết trần.

Trích **đúng**: `NT 21` (kết quả âm có kiểm soát là dữ liệu, dùng ở mục 6),
`NT 63` (kỷ luật phạm vi, dùng ở mục 2/A3′), `W4`
(`docs/phase-T2/07-handoff-21R2.md:225` — hằng số phán quyết: một nguồn,
IMPORT, không chép; dùng ở mục 5.2 và 6).

> Registry đóng mục này bằng một câu nên đọc kỹ:
> *"Bài học: một bản kiểm toán trích dẫn cũng phải được kiểm bằng grep.
> Chính nó cũng có thể sai theo CẢ HAI chiều."*
> Lesson 20R2.0 là một bản kiểm toán. Nó cũng phải chịu luật đó — và
> mục 9 này là kết quả của việc áp luật đó lên chính nó.


## 10. Trạng thái sau khắc phục 20R2.1 (2026-09-09)

Gate 0-5 PASS trong phạm vi `_valid_rows` và đường gọi đã kiểm.

**Cập nhật 2026-09-09.** Hai trong ba mục chặn ở §0 **đã giải xong bằng số đo
từ chính checkout**, không cần `PHASE_20R2.md`:

| Mục chặn §0 | Trước | Nay | Nguồn |
|---|---|---|---|
| Định nghĩa "một ô" | ❌ | ✅ `(ρ̄, c_a, τ, σ, seed)` | §0.1a, `axis_audit.json` |
| Kích thước lưới | ⚠️ 960 | ✅ **800** | §0.1c, `sla_calibration.json` |
| Ngân sách CPU | ⚠️ 2,95 h/nhánh | ✅ **14,7 phút/nhánh** | §5.2, `axis_audit.json` |
| Danh sách 5 RQ (a–e) | ⚠️ | ⚠️ **vẫn chưa kiểm được** | cần `PHASE_20R2.md` |

Gate 0-3 **VẪN CHƯA ĐẠT**, nhưng nay chỉ còn **hai** lý do, không phải bốn:

1. Danh sách 5 RQ (a–e) vẫn chỉ chép từ lesson, chưa có nguồn kiểm được.
2. **Người ký chưa được xác định.** Prereg là một cam kết của *người*; không ai
   khác ký thay được. Ô chữ ký ở §11 để trống chờ điền.

Không tạo tag `phase-20R2-prereg-signed` khi chưa đáp ứng §0. Không chạy lưới
kết quả 20R2. QD-33 và báo cáo `01-recovery-and-remediation.md` ghi công việc
đã hoàn tất.

### Lệnh sinh lại mọi số trong bản này

```bash
PYTHON=/home/ubuntu/miniforge3/envs/sdn_rl/bin/python
$PYTHON -m tools.20r2_0_axis_audit          --out results/PENDING/phase-20R2/axis_audit.json
$PYTHON -m tools.20r2_1_parquet_recovery    --out results/PENDING/phase-20R2/parquet_recovery.json
$PYTHON -m tools.20r2_1_canary_span         --out results/PENDING/phase-20R2/canary_span.json
$PYTHON -m tools.20r2_4_realizability_audit --out results/PENDING/phase-20R2/realizability_audit.json
```

---

## 11. Chữ ký (gate 0-3)

Điền tay. Không công cụ nào điền hộ mục này — đó chính là điểm của việc ký.

```text
Nguoi ky        : doan van tai
Ngay            : 2026-09-10
Commit sha      : = DICH cua tag `phase-20R2-prereg-signed`  -- KHONG dien tay
                  kiem: git rev-parse phase-20R2-prereg-signed^{commit}
                  ^ O nay TRUOC DAY doi "sha CUA BAN prereg duoc ky". O do
                    KHONG THE dien dung: sha cua commit phu thuoc noi dung
                    prereg, ma prereg lai chua sha do -- vong TU QUY CHIEU,
                    nhu mot file khong the chua sha256 cua chinh no. TAG moi
                    la thu gan chu ky voi commit. [20R2.5-C1]
Xac nhan        : [x] toi da doc §0 va chap nhan muc ⚠️ con lai (danh sach 5 RQ)
                  [x] toi ky ngan sach 74,53 phut hai nhanh (+30% = 96,89)
                      -- DO DUOC o cpu_pilot.json. Con so 29,4 phut o ban truoc
                         la A7 KE THUA, da bi 20R2.4 thay. Xem §16.1.
                  [x] toi ky luoi 800 o (KHONG phai 960)
                  [x] toi KHONG ke thua ket luan kha thi cua T2 (20R2-L4)
                  [x] toi da doc §16 va ky BANG DA SUA: C_upper = 0,406418
                      tren truc exogenous (ban cu 0,409554 do tren truc SAI)
                  [x] toi ky KE HOACH docs/phase-20R2/03-run-plan.json
                      sha256 a984020e104bb13b4743be5aca2d5e0eabf0d49558f53cc5f0d70c6ce4fdf662
                      (sinh lai bat cu luc nao de doi chieu: tool TAT DINH)

Sau khi dien:
    git add docs/phase-20R2/00-preregistration.md
    git commit -m "20R2 prereg: ky gate 0-3 + §16"
    git tag -a phase-20R2-prereg-signed -m "20R2 prereg signed"
    git push origin main && git push origin phase-20R2-prereg-signed
    git ls-remote --tags origin | grep prereg-signed   # BANG CHUNG

Roi moi duoc chay:
    python -m tools.20r2_5_run          # guard doi tag CO tren remote
    python -m tools.20r2_5_hygiene --out docs/phase-20R2/05-hygiene.json
    git add -A && git commit -m "20R2.5: chien dich + ve sinh"   # NHAN CHUNG
    #  ^ chi SAU commit nay moi duoc mo 20R2.6  [F5, NT 56]
```

---

## 12. Dự đoán ký trước — gate 20R2.2 (2026-09-10)

### 12.1 Artifact đã ký và hash ghim

```text
docs/phase-20R2/01-prediction-signed.json
sha256 = 6ec81b2584779f128d33bc20e3cd55bf57f7ebc5b545fcc8de8795d303897291
  ^ CAP NHAT lan 2 boi amendment §20.1 (20R2.7-B1): dinh chinh
    UNIT/SCALE cua SLA_VIOL_BY_AGE. Hash truoc do: d9eef23b75c26881f5df2ad7c44a12017593aad2eb92323f7297b42d4462beac
  ^ CAP NHAT boi amendment §16.3 (20R2.5-P3): bang do lai tren truc SLA
    exogenous. Hash truoc do: 8eff683ff4fe115a322b8639bd17d2dd71c58829fefcbf4b2df3670d83bf1d9c
sinh bởi: tools/20r2_2_predictions.py     (gate 0-1: SINH BỞI CÔNG CỤ)
test canh: test/test_20r2_2_prediction.py
```

Bảng Sheppard **không được gõ tay**. Số dòng của `ARTIFACT_FIELD` cũng
không: công cụ **quét nguồn** để lấy chúng, vì GLOSSARY đã ghi rằng số dòng
`:402` của T2 từng trôi. Một số dòng gõ tay là một sự thật có hạn sử dụng,
và nó hết hạn **im lặng**.

### 12.2 ★ POPULATION — quyết định khoa học, ký ở đây

**LỐI B**: quần thể kết quả là **8 ô `gate`**; `cbr` là **đối chứng dương**.

```text
QUẦN THỂ KẾT QUẢ   8 ô gate  (poisson × 4 rho_bar, h2 × 4 rho_bar)
                   → lưới kết quả = 8 × 8τ × 2σ × 5 seed = 640 ô
ĐỐI CHỨNG DƯƠNG    2 ô cbr khả thi (rho_bar 0.700, 0.850) = 160 ô
                   → báo cáo RIÊNG, KHÔNG gộp vào bất kỳ trung bình nào
LOẠI BỞI q8        2 ô cbr (rho_bar 0.925, 0.960), sigma_max_regime = 0
```

Nguồn phân hoạch là **artifact, không phải suy diễn**:
`results/LIVE/phase-20R/sla_calibration.json` → `summary`:
`n_design_cells = 12`, `n_feasible = 10`, `n_gate_cells = 8`,
`n_pc1_cells = 4`. Artifact đã phân hoạch sẵn; không cần suy từ `role`.

**Vì sao không gộp**: `cbr` là chế độ dễ nhất (lưu lượng đều, không ngẫu
nhiên). Gộp nó vào trung bình sẽ **kéo `err` xuống** và cho ra một câu như
"twin sai 12%" trong khi ở chế độ khó thật (`h2@0.960`) có thể là 20%. Hợp
pháp về số học, sai lệch về khoa học — **ngụy biện gộp**.

**Chi phí của lối B = 0.** Ngân sách vẫn 800 ô (29,4 phút ước tính kế thừa; **đo được 74.5 phút (đã nâng n)** — §14.7). Cái đổi là
**phạm vi kết luận**, không phải chi phí tính toán. Hai trục độc lập.

Kỳ vọng đối chứng: **ĐÃ RÚT — xem §13.5.**

Bản ký đầu tiên của §12 có dòng này:

```text
err(cbr) < err(poisson) < err(h2)   tại cùng (z, τ)      ⛔ KHÔNG CÒN KÝ
```

Dữ kiện đo ở **20R2.4 (E2)** cho thấy `cbr` **suy biến trên trục biên**, nên
không thể biết trước chiều của `err(cbr)`. Một bất đẳng thức một chiều ở đây
là **đoán**, không phải đối chứng. Chi tiết và cơ chế: §13.5.

### 12.3 ★ ĐÍNH CHÍNH — băng chấp nhận KHÔNG lấy sàn từ 10,3%

Con số "độ nhạy trục AoI = 10,3% ở τ=28" **là tương phản measured ↔ legacy**,
không phải độ bất định của kết quả chính. §6 của chính prereg này đã ghi đúng:
`−9,3% so với legacy`. Mà **legacy là ĐỐI CHỨNG ÂM có chủ đích** (§3, §4),
không phải một lựa chọn trục đang mở.

Đo lại, tách hai thứ thường bị gộp:

```text
ĐỘ BẤT ĐỊNH CÒN LẠI trong họ measured, SAU KHI trục đã ký
    z ∈ {0.3650, 0.35827, 0.36594, 0.36728, 0.369}
    biên độ / err(z đã ký):   1,11% (τ=0,5) … 1,47% (τ=28)     ← XẤU NHẤT 1,47%

TƯƠNG PHẢN với trục legacy (ĐỐI CHỨNG ÂM, chủ đích)
    z = 0.30237 →  −7,02% (τ=0,5) … −8,95% (τ=28)
```

Lấy ~9–10% làm sàn cho băng là **nhầm đối chứng với độ bất định**: nó cho một
băng **rộng gấp ~6 lần** mức cần. Và một băng quá rộng không phải là "an
toàn" — nó làm gate **mất lực phân giải**: cái gì cũng PASS, nên gate không
còn nói lên điều gì.

> Phân biệt cần giữ: băng **quá hẹp** → gate dễ trượt vì nhiễu.
> Băng **quá rộng** → gate **không đọc được**, vì PASS không mang thông tin.
> Cả hai đều hỏng, nhưng hỏng theo hai kiểu khác nhau.

### 12.4 Băng chấp nhận — CÔNG THỨC ký trước, không phải con số chọn sau

```text
band_rel = max(AXIS_FLOOR, K_MC × se_pilot_rel)

AXIS_FLOOR   = 0.0147   (1,47% — độ bất định trục CÒN LẠI, τ xấu nhất)
K_MC         = 3.0      (ký TRƯỚC pilot)
se_pilot_rel = <điền từ pilot 3 ô của 20R2.4>
```

Chỉ **giá trị cắm vào** đến từ pilot; **không bậc tự do nào** còn mở sau khi
nhìn số. Đây là điểm khác giữa "pre-register công thức" và "chọn băng sau".

### 12.5 Chính sách đọc — ký trước

```text
CHÍNH (có định hướng)   err_đo ≥ err_Sheppard tại MỌI τ
    cơ sở: 3/4 vi phạm giả định Sheppard đẩy err LÊN
    nếu vỡ: (a) một vi phạm chưa nghĩ tới đẩy xuống — phải NÊU TÊN nó
            (b) estimator có bug — chạy đối chứng TRƯỚC khi diễn giải

PHỤ (hình dạng)         err đơn điệu GIẢM theo τ
    ≥ 7/8 điểm đơn điệu        → 20R2-2 PASS
    vỡ ở ĐÚNG MỘT τ            → báo cáo là DỮ LIỆU, KHÔNG sửa lưới
    vỡ ở ≥ 2 τ                 → nghi estimator, chạy đối chứng trước

MẪU SỐ                  8/8 τ đều được chấm, GIỮ nguyên mọi miss
                        (T2 chấm 21/32 = 65,6% và giữ cả 10 miss; làm y hệt)
```

### 12.6 Hai estimand — đăng ký đủ 7 trường

Đăng ký trong `docs/GLOSSARY.md` mục **SO DANG KY ESTIMAND**:
`DECISION_ERR_BY_AGE` (tỉ lệ, không thứ nguyên, `per_z[].err_total`) và
`SLA_VIOL_BY_AGE` (`cost_ms`, `per_z[].d_sla`).

⛔ **KHÔNG tái dùng `RMS_ALLACTION_DELAY`**: đúng LEVEL (`all_action`) nhưng
sai SCALE (`delay_ms` vs tỉ lệ) và sai ARTIFACT_FIELD (`rms_e_model` vs
`err_total`). Hai trường sai là đủ.

### 12.7 ★ PHÁT HIỆN — `estimand_id` đóng dấu ở MỨC ARTIFACT, không ở MỨC TRƯỜNG

```text
measurements/decision_error_v2.py:48    ESTIMAND_ID = "RMS_ALLACTION_DELAY"
                              :472      "estimand_id": ESTIMAND_ID   → vào artifact
                              :1047     "estimand_id": ESTIMAND_ID   → vào validity
```

Nghĩa là **một** artifact của `run_cell` mang **một** nhãn, trong khi
`per_z[]` của nó chứa **ba** đại lượng khác THANG và khác ĐƠN VỊ:

```text
rms_e_model / rms_e_stale / cov_e  →  RMS_ALLACTION_DELAY   (delay_ms)
err_total / err_model / err_stale  →  DECISION_ERR_BY_AGE   (tỉ lệ)
d_sla                              →  SLA_VIOL_BY_AGE       (cost_ms)
```

Dùng nhãn mức-artifact để phán quyết một dự đoán 20R2 là **lặp lại đúng lỗi
A-T2-3**, chỉ ở độ phân giải thấp hơn — và như A-T2-3, nó **sẽ không báo lỗi**.

Khắc phục: thêm `ESTIMAND_BY_FIELD` vào `measurements/decision_error_v2.py`
— khai theo **trường**. `ESTIMAND_ID` giữ nguyên (tương thích ngược).

### 12.8 Tự chấm gate 20R2.2

```text
✅ 2-1  Mọi dự đoán ký trước, sha256 ghim trong prereg      §12.1
✅ 2-2  Bảng Sheppard tính tại z_median CỦA TRỤC ĐÃ CHỌN    z = 0,3650 (KHÔNG 0,369)
✅ 2-3  estimand_id đủ 7 trường, qua test registry           §12.6 + GLOSSARY
✅ 2-4  MẪU SỐ khai TRƯỚC                                    §12.5
✅ 2-5  POPULATION được KÝ: cbr = ĐỐI CHỨNG DƯƠNG            §12.2
```

### 12.9 Nợ có tên mở từ 20R2.2

```text
20R2-D1  se_pilot_rel chưa điền — chờ pilot 3 ô của 20R2.4. Băng CHƯA đóng
         hoàn toàn; CÔNG THỨC đã đóng.
20R2-D2  GIA TRI MOC của cả hai estimand chưa điền — cùng lý do.
```


---

## 13. Lưới, realizability, ngân sách CPU — gate 20R2.4 (2026-09-10)

### 13.1 ★ ĐÈN XANH RỖNG — căn nguyên nằm ở MỘT dòng

`cert/realizability_gate.py:195` tính phán quyết bằng:

```python
"verdict": "REALIZABLE" if not failed else "REJECTED"
```

Nó **chỉ nhìn `failed`**, bỏ qua `not_evaluated` hoàn toàn. Một tiêu chí không
chạy có `pass = None`, nên **không bao giờ vào `failed`**, nên **không bao giờ
đổi được phán quyết**.

Chứng minh bằng thí nghiệm — **cùng ô, cùng mã, cùng máy**, chỉ khác cách gọi:

```text
cbr@0.925, tau=3, dt=0.005, n=200000        sigma_max_regime(cbr, 0.925) = 0.0

A. gọi THIẾU sigma  -> REALIZABLE   failed=[]
                       not_evaluated=[censoring_ok, mondrian_cells_populated,
                                      sigma_within_headroom]
B. gọi ĐỦ  sigma    -> REJECTED     failed=[sigma_within_headroom]
                       not_evaluated=[]
C. poisson@0.925 đủ -> REALIZABLE   failed=[]  not_evaluated=[]   (gate lành)
```

**Logic ba giá trị** (Kleene): PASS / FAIL / **CHƯA KIỂM**. Giá trị thứ ba là
*thiếu thông tin*, và thiếu thông tin **không được cư xử như thông tin tốt** —
đúng như `NULL` trong SQL. Gate đã làm đúng phần khó (dùng `None`, ghi
`not_evaluated` ra artifact) và hỏng ở phần dễ: dòng tổng hợp làm phẳng ba giá
trị thành hai.

⟹ E1 **không đọc `verdict` một mình**. Nó khẳng định riêng cả **phạm vi**:
`not_evaluated` phải **đúng bằng** hai tiêu chí hậu-kiểm.

### 13.2 Gate chạy HAI LẦN — và gate 4-2 chỉ nói về lần hai

```text
LẦN 1  TIỀN SÀNG   "tôi ĐƯỢC PHÉP chạy ô nào?"     7 tiêu chí
       not_evaluated = 2 là ĐÚNG và ĐƯỢC PHÉP.
LẦN 2  HẬU KIỂM    "ô đã chạy có ĐỌC ĐƯỢC không?"  9 tiêu chí
       not_evaluated PHẢI = [].    <- gate 4-2
```

Nếu áp `assert not_evaluated == []` cho lần 1 thì nó **không bao giờ thoả**, và
người viết sẽ bị cám dỗ nới assert — tức mở lại đúng cái lỗ vừa bịt.

**Kết quả lần 1** (`results/PENDING/phase-20R2/grid_prescreen.json`):

```text
10 ô khả thi × 8 τ × 2 a = 160 tổ hợp   × 5 seed = 800 ô
REALIZABLE 160   REJECTED 0   lý do trượt: (không có)
not_evaluated: censoring_ok + mondrian_cells_populated, ×160   ĐÚNG NHƯ MONG ĐỢI
```

⟹ **Lưới 800 có bằng chứng, không còn là suy luận.**

### 13.3 20R2-L8 — lưới thừa kế là GATE_VERSION 1

```text
results/PENDING/phase-T2/realizability_grid.json   (đo 2026-09-10)
  derived.gate_version      = None            <- trường chưa tồn tại ở v1
  derived.sigma_max_regime  = KHÔNG CÓ
  tên tiêu chí sigma        = 'sigma_feasible' (tên cũ)
  96/96 REALIZABLE với 3/9 not_evaluated ở MỌI hàng
```

Vô hiệu vì **ba lý do độc lập**: sai phiên bản gate · 3/9 tiêu chí không chạy ·
tiêu chí đã chạy là **tiêu chí ma**. Lý do thứ ba nặng nhất: v1 chỉ kiểm
`sigma > 0`, mà `tau_sweep` luôn truyền sigma thiết kế dương ⟹ **không bao giờ
fail được**. Và `from twin import cost_v2 as C` là **dead import** — kiểm trên
commit `54a05ddc`: `grep -c "C\."` = **0**, trong khi thông điệp `why` vẫn nhắc
`sigma_max_regime`. Người đọc thông điệp sẽ tin rằng trần đã được kiểm.

### 13.4 ★ Ngân sách CPU — ĐO, không kế thừa (E3/E4)

Lưới z của 20R2 là **13 điểm**; lưới trong mã là **9**. Pilot đo **cả hai** để
tách chi phí *của lưới* khỏi chi phí *của máy*:

```text
tau     z20R2(s)   legacy(s)   tỉ số
  0.5     13.76      12.60   1.092
  1.0     13.16      11.76   1.119
  2.0     13.05      11.64   1.121
  3.0     13.03      11.63   1.121
  5.0     12.16      10.89   1.117
 10.0     11.97      10.80   1.108
 20.0     11.86      10.64   1.115
 28.0     16.90      15.20   1.112
```

```text
ô/lệnh 10 · 800 ô · MỘT nhánh 17.65 phút · HAI nhánh 35.30 phút (+30%: 45.89)
s/ô đo được 1.3237   vs kế thừa 1.1028   = +20.0%   [PASS, ngưỡng ±30%]
```

Gate 4-3 **PASS**, nhưng con số ký phải đổi: **29,4 phút → 35.3 phút**.
Chênh đến từ hai nguồn tách được: lưới 13 điểm tốn ~+12% (dưới tuyến tính — sinh
trace mới là phần đắt, không phải vòng z), phần còn lại là máy khác với máy đã
sinh `run_log` của `sweep_r2`.

> ⚠️ **Các chữ số trên là MỘT lần đo, không phải hằng số.** Chạy lại trên cùng
> máy này lệch ~1% (đo được: +21,4% rồi +20,0%). Thứ được **ký** là **ngưỡng
> ±30%** và **công thức**, không phải chữ số thứ tư. Nguồn luôn đúng là
> `results/PENDING/phase-20R2/cpu_pilot.json`; văn bản này chỉ trích nó.

**E4 — thiết kế phân đoạn: KHÔNG CẦN**, và lý do được ghi thay vì để trống:
35.3 phút ≈ 7.4% của ngưỡng 8 giờ.

### 13.5 ★★ RÚT ĐỐI CHỨNG DƯƠNG `cbr` — dữ kiện từ E2

Bảng `em/A` (`results/PENDING/phase-20R2/em_over_a.json`, **20 dòng = 10 ô × 2 a**):

```text
cbr@0.700  a=0.9   A_bar = 3.502e-04   em/A = 17.69   span/pure = 0.0067  SUY BIẾN
cbr@0.700  a=0.5   A_bar = 2.245e-04   em/A = 27.68   span/pure = 0.0047  SUY BIẾN
cbr@0.850  a=0.5   —                                                      CHƯA BIẾT
cbr@0.850  a=0.9   —                                                      CHƯA BIẾT

ô không-cbr: A_bar ∈ [1.13, 179]  ⟹ cbr nhỏ hơn ô nhỏ nhất khác ~3213 lần
```

`span/pure ≈ 0.005` nghĩa là **đường cong theo tuổi của `cbr` gần như phẳng**.

**Vì sao điều đó rút đối chứng dương.** Một đối chứng dương chỉ có giá trị khi
ta **biết trước** kết quả phải ra sao. Với biên ≈ 0, **hai cơ chế kéo `err` về
hai hướng ngược nhau**:

```text
(1) cbr đều theo thời gian   -> twin cũ VẪN đúng          -> err THẤP
(2) biên giữa 4 đường ≈ 0    -> argmin gần như tuỳ ý,
                                lật vì một nhiễu rất nhỏ  -> err CAO
```

Không có cơ sở tiên nghiệm chọn giữa hai. Bản ký đầu chỉ nghĩ tới (1). Ký một
bất đẳng thức một chiều trong tình huống đó là **đoán**, không phải đối chứng.

```text
QUYẾT: cbr  ->  CHẨN ĐOÁN có điều kiện, báo cáo RIÊNG,
                KHÔNG dùng phán quyết bất kỳ RQ nào.
        Ghi CẢ HAI cơ chế TRƯỚC, rồi báo cáo cơ chế nào thắng.
        Đó là một quan sát — không phải một phép kiểm dụng cụ.
```

**Phép kiểm dụng cụ thật** của 20R2 là **đối chứng twin-hoàn-hảo** (`--control`),
vốn **phải cho đúng 0** (`measurements/decision_error_v2.py:6`). Đó là ràng buộc
**tất định**, không phụ thuộc chế độ lưu lượng, nên suy biến không làm hỏng được.

> POPULATION (§12.2) **không đổi**: 8 ô `gate` vẫn là quần thể kết quả, `cbr` vẫn
> báo cáo riêng. Cái đổi là **tư cách** của `cbr`: từ *đối chứng dương* thành
> *chẩn đoán*. Lưới và ngân sách không đổi một ô nào.

### 13.6 E5 — N3/N4: mốc đã ghim, phần 20R2 CHƯA đo

```text
N3  ar1_rms_total_fit_within_2pct     18 arm chính: 14 PASS / 4 FAIL
    ĐÍNH CHÍNH PHẠM VI: handoff viết "chủ yếu ở poisson@0.850"; đo lại thì
    4 FAIL trải trên BA ô: poisson@0.850 (×2), poisson@0.700, h2@0.850.
N4  "A, c, em độc lập với τ"          18 mục: 7 PASS / 11 FAIL
    FAIL theo tham số: em 6 · c 3 · A 2
```

⛔ **Không được chép sang 20R2.** Một giả định vỡ 11/18 ở điều kiện A có thể vỡ
3/18 hoặc 17/18 ở điều kiện B. Phần 20R2 cần `cert/tau_sweep.py` chạy trên lưới
20R2 — một chiến dịch thứ hai (~53 phút) — **chạy sau 20R2.5**.

### 13.7 ⛔ NỢ CHẶN — lưới z của 20R2 CHƯA CÓ TRONG MÃ

```text
prereg §4      Z_GRID_20R2_MEASURED  9 điểm + 1 đối chứng + 3 ngoại suy = 13
mã hiện tại    decision_error_v2.py:76
               Z_GRID = (0.0, 0.05, 0.10, 0.20, 0.30, 0.55)  + 3 = 9  LEGACY
```

Chạy chiến dịch hôm nay sẽ **lặng lẽ dùng lưới legacy** — đúng cái lỗi §A3′ đã
chỉ ra (*"lưới z tiền đăng ký phủ KHÍT miền legacy [0.055, 0.550]"*). Và **nó
không báo lỗi**: cả hai lưới đều chạy được, chỉ trả lời câu hỏi khác nhau.

```text
20R2-D3 ⛔ CHẶN 20R2.5: nối Z_GRID_20R2_MEASURED vào decision_error_v2.
           Test canh: test/test_20r2_4_grid_and_gate.py
                      ::test_the_20r2_z_grid_is_still_missing_from_the_harness
           Test đó ĐỎ khi ai đó sửa mã — đó là ý muốn. Khi ĐỎ: đổi assert,
           sinh lại cpu_pilot.json, gỡ mục này.
```

### 13.8 Tự chấm gate 20R2.4

```text
✅ 4-1  Mọi ô realizable; ô false RAISE            160/160, tool tự RAISE
✅ 4-2  not_evaluated == [] cho kết quả CHÍNH      → LẦN 2, sau chiến dịch
✅ 4-3  CPU ký trước, lệch ≤ 30%                   +20.0%  PASS
✅ 4-4  Bảng em/A mọi ô, sinh TRƯỚC chiến dịch     20 dòng
◐  4-5  N3/N4 kiểm lại                             mốc ghim; 20R2 sau 20R2.5
✅ 4-6  gate_version = 2 mọi artifact + test canh
```

### 13.9 Nợ có tên mở từ 20R2.4

```text
20R2-D3 ⛔ lưới z 20R2 chưa có trong mã — CHẶN 20R2.5   (§13.7)
20R2-D4    N3/N4 phần 20R2 chưa đo — cần chiến dịch thứ hai (§13.6)
20R2-D5    cbr@0.850 chưa có em/A — T2 không đo ô này    (§13.5)
```

---

## 14. Băng theo τ, sàn chu kỳ, và lưới z vào mã — G1–G4 (2026-09-10)

### 14.1 ★ Lực thống kê biến thiên 40 lần trong khi chi phí gần như phẳng

`n_for_tau` giữ **chi phí** phẳng (~1,32 s/ô) nhưng **không** giữ **lực**. Cỡ mẫu
hiệu dụng là **số chu kỳ độc lập** `T_sim/τ`, không phải `n`:

```text
tau     n_for_tau   T_sim     chu ky
0.5        200000    1000     2000.0
20         200000    1000       50.0
28         280000    1400       50.0    <- n co gian x1.4 de giu DUNG san 50
                              ────────
                              bien thien 40 lan
```

⚠️ Con số "35,7 chu kỳ ở τ=28" **không tồn tại**: nó giả định `n = 200.000`, mà
ở τ=28 `n_for_tau` trả **280.000**. Ở `n = 200.000` ô đó **trượt**
`run_covers_tau` (35,7 < 50) nên không bao giờ vào lưới.

### 14.2 ★★ Đo được: `se` từ 5 seed KHÔNG dùng làm sàn băng được

Pilot 8 τ × 5 seed (**seed 201–205**, không phải 101–105 của chiến dịch — dùng
chung seed sẽ chọn băng từ chính dữ liệu sẽ được chấm):

```text
se_rel di tu 0.639% (tau=0.5) den 5.836% (tau=20)  -- bien thien ~9 lan
```

Rồi tôi chạy **đối chứng**: nâng `n` gấp 4 thì `se` **phải giảm 2 lần**.

```text
tau=20   se 0.003381 -> 0.001699   GIAM 1.99x   dung huong
tau=28   se 0.000908 -> 0.001569   TANG 1.73x   NGUOC huong
```

Một đại lượng mà phép đo **không theo kịp hướng đã biết** thì không dùng làm
tham số của băng. Nguyên nhân: `se` ước từ 5 seed có ~35% bất định danh nghĩa,
và thực tế còn tệ hơn (`F(4,4)` cho `p ≈ 0,02`).

⟹ **Dùng LUẬT GỘP thay vì 8 ước lượng rời rạc:**

```text
se_rel = C / sqrt(so chu ky doc lap)

so mu do duoc  -0.532     (ly thuyet -0.5)      10 diem, R2 = 0.69
C trung binh    0.2922    sd 0.1173
C dung          0.4096    (= trung binh + 1sd, bao thu vua phai)
C do duoc trai  0.1278 .. 0.4708  (3.7 lan)  <- chinh la nhieu 5-seed
```

Gộp 10 phép đo để ước **một** tham số ổn định hơn hẳn 10 ước lượng độc lập.

### 14.3 ★ SÀN CHU KỲ = 200, và bảng nhân `n` — KÝ TRƯỚC

Đo σ từng cặp liền kề (thống kê đúng cho câu hỏi đơn điệu):

```text
cap        sigma dat duoc
0.5->1        26.15        3->5      13.75
1->2          24.76        5->10      8.18
2->3          13.73        10->20     4.82
                           20->28     2.20   <- DUOI 3 sigma
```

Mắt xích yếu **xác nhận bằng số đo**: khoảng cách nhỏ nhất gặp ít chu kỳ nhất.
Nhưng ràng buộc là `se(20)`, **không phải** `se(28)` — τ=28 đã được `n_for_tau`
nâng 1,4× nên nó không phải chỗ yếu.

**Quy tắc ký: mọi ô phải đạt ≥ 200 chu kỳ độc lập.** 200 là mức τ=5 *đã* có, nên
nó không nâng bất kỳ τ ≤ 5 nào.

```text
tau <= 5   x1        tau = 10   x2        tau = 20, 28   x4
```

Kiểm lại sau khi nâng (đo thật, không ngoại suy): cặp `20→28` đạt **5,87 σ**.

> Vì sao ×4 chứ không ×2 ở τ=20/28: ×2 chỉ cho 3,11 σ — mà `se` chỉ biết đến
> ~35%, nên 3,11 có thể thực sự dưới 3. ×4 sống sót qua chính độ bất định đó.

### 14.4 Băng chấp nhận THEO TỪNG τ

```text
band_rel(tau) = max( AXIS_FLOOR(tau), K_MC x se_rel(tau) )     K_MC = 3.0

tau   nhan  chu ky    san truc   se(luat)     BANG
  0.5   x1    2000.0     1.109%     0.916%     2.747%
  1.0   x1    1000.0     1.291%     1.295%     3.885%
  2.0   x1     500.0     1.383%     1.832%     5.495%
  3.0   x1     333.3     1.413%     2.243%     6.730%
  5.0   x1     200.0     1.437%     2.896%     8.688%
 10.0   x2     200.0     1.455%     2.896%     8.688%
 20.0   x4     200.0     1.464%     2.896%     8.688%
 28.0   x4     200.0     1.466%     2.896%     8.688%
```

Băng rộng nhất **8,69%** — vẫn hẹp hơn tương phản legacy (8,95%), nên gate
**giữ được lực phân giải**. Băng bị ràng buộc bởi nhiễu MC ở **mọi** τ; sàn trục
không bao giờ là ràng buộc.

Bản vô hướng cũ giữ trong `acceptance_band.superseded_scalar_band` — không xoá
dấu vết.

### 14.5 Đính chính: đơn điệu đếm theo **CẶP**, không theo **ĐIỂM**

```text
ban ky dau:  "don dieu o >= 7/8 DIEM"    sai ca don vi lan mau so
sua:         "don dieu o >= 6/7 CAP"     8 tau -> 7 cap lien ke
```

Đơn điệu là tính chất của một **cặp**. Và nó dùng thống kê **khác** với băng:

```text
band_rel(tau)                     "co khop Sheppard tai tau nay khong?"
sigma = |e_i - e_j| / se_diff     "hai tau co phan biet duoc khong?"
```

Hai câu hỏi khác nhau thì không dùng chung một con số.

### 14.6 20R2-D3 ĐÃ GỠ — lưới z vào mã

```python
Z_GRIDS = {"legacy": Z_ALL, "20r2_measured": Z_ALL_20R2}

ap.add_argument("--z-grid", choices=sorted(Z_GRIDS), required=True, ...)
```

`required=True` — cùng thuốc đã dùng cho `axis` ở gate 0-5. Một mặc định im lặng
ở lưới z nguy hiểm y hệt ở trục AoI vì **cả hai lưới đều chạy được và không báo
lỗi**.

```text
max(legacy) == max(20r2_measured) == 4.0   CO CHU DICH
  scoring_window_start lay max cua luoi => hai luoi cham diem tren CUNG dai
  hang, nen so duoc voi nhau. Doi max mot ben la pha tinh chat do.
```

`tools/t2_6_plan.py` và `tools/t2_6_run.py` giờ khai `--z-grid legacy` **tường
minh**. Giá trị không đổi; chỉ lời khai đổi — và đó là điểm: lựa chọn lưới z
giờ nằm trong chính dòng lệnh.

### 14.7 Ngân sách sau khi nâng `n` — ĐO, không ngoại suy

```text
nen (chua nang)          35.83 phut / hai nhanh
he so nang n             {'0.5': 1, '1.0': 1, '10.0': 2, '2.0': 1, '20.0': 4, '28.0': 4, '3.0': 1, '5.0': 1}
chi phi DO DUOC cua ban da nang:
  tau=10    x2   24.86s   ti so do duoc 2.06  (tuyen tinh: 2)
  tau=20    x4   52.20s   ti so do duoc 4.35  (tuyen tinh: 4)
  tau=28    x4   80.22s   ti so do duoc 4.67  (tuyen tinh: 4)
TONG (da nang)           74.53 phut hai nhanh  (+30%: 96.89)  =  15.5% nguong 8 gio
```

⚠️ **Chi phí KHÔNG tỉ lệ tuyến tính với `n`.** Đo được `2,06×` (τ=10), `4,35×`
(τ=20), `4,67×` (τ=28) cho các hệ số `2/4/4`. Ngoại suy tuyến tính cho **68.62
phút**, tức **thấp hơn 7.9%** — và một ước tính **thấp** chính là thứ làm
gate 4-3 trượt khi chạy thật.

> ⛔ **NT 50, và lần này là của tôi.** Bản đầu của §14.7 ghi con số **gõ tay**
> trong khi `cpu_pilot.json` vẫn ghi ngân sách **nền** (chưa nâng `n`) và
> **không có trường nào biết về `n_multiplier`**. Gate 4-3 đối chiếu **artifact**
> (gate 0-1: sinh bởi công cụ), nên nó sẽ đọc 35,08 phút, so với thời gian chạy
> thật ~74.53 phút, thấy lệch ~110% và **TRƯỢT OAN** — một FAIL do sổ sách,
> không do khoa học.
>
> Sửa: công cụ đọc `n_multiplier` từ artifact dự đoán đã ký và **tự đo** bản đã
> nâng. Số trong văn bản này **trích** từ `cpu_pilot.json`, có test khoá hai
> nguồn lại với nhau.

E4 vẫn **KHÔNG CẦN** thiết kế phân đoạn.

### 14.8 G3 — test tái lập phủ hết tool

`TOOLS` giờ có đủ 4 tool tất định mới. `20r2_4_cpu_pilot` **cố ý** nằm ở bảng
`NON_DETERMINISTIC` (nó đo thời gian; đòi bit-exact sẽ đỏ thường trực) và được
kiểm bằng **mã thoát + lược đồ + bất biến phán quyết**. Thêm một test đỏ khi có
tool `20r2_*` mới chưa đăng ký ở **một trong hai** bảng.

`SyntaxWarning: invalid escape sequence` — nguyên nhân là `/!\` ở dòng 23 (không
phải chuỗi `grep -c "C\."`, vốn đã escape đúng). Sửa bằng docstring raw.

**Và test đó bắt ngay một lỗi thật của chính công cụ.** Bản `--quick` đo 3 τ rồi
nhân 8/3, nhưng `QUICK_TAUS = [0.5, 3, 28]` **chứa τ đắt nhất**, nên ngoại suy
**thiên lệch lên**: nó trả `FAIL` trong khi bản đầy đủ trả `PASS`.

```text
Mot uoc tinh THIEN LECH khong duoc phep phan quyet mot gate.
=> ban --quick TU KHAI `verdict = NOT_AUTHORITATIVE`, `authoritative = False`,
   thay vi im lang tra mot verdict sai.
=> test doi artifact DA COMMIT phai la ban DAY DU (authoritative = True).
```

Đây là cùng hình dạng với đèn xanh rỗng, nhưng **ngược dấu**: một cơ chế phán
quyết trả lời `NO` khi nó không có tư cách trả lời gì cả. Cách chữa giống nhau —
bắt nó **khai phạm vi thẩm quyền** thay vì phát ra một phán quyết.

### 14.9 Nợ sau G1–G4

```text
20R2-D3  ĐÃ GỠ (§14.6)
20R2-D4     N3/N4 phần 20R2 chưa đo — cần chiến dịch thứ hai
20R2-D5     cbr@0.850 chưa có em/A
20R2-D6  MỚI: se pilot đo tại MỘT điểm z (0.366) và MỘT giá trị a (0.9).
            Luật C/sqrt(N) giả định C không đổi theo z và a. CHƯA kiểm.
            Nếu C phụ thuộc z thì băng ở z khác phải tính lại.
20R2-D7  MỚI: parquet thô của se pilot KHÔNG nằm trong git (.gitignore:64 chỉ
            cho qua json/md/csv/png/sha256 trong results/). Trên clone sạch
            `tools/20r2_2_se_pilot.py` phải chạy lại phép đo (~20 phút).
            Cùng tính chất với baseline_failures.txt. Tool BÁO TO khi thiếu,
            và nằm ở bảng REQUIRES_LOCAL_RAW chứ không phải TOOLS.
```

### 14.10 ⚠️ Một lỗi của chính tôi, ghi lại vì nó suýt lọt

`02-se-pilot.json` ban đầu được sinh bởi **một script tạm trong scratchpad**, không
phải công cụ đã commit — **vi phạm gate 0-1** mà chính phase này đặt ra. Đã sửa:
`tools/20r2_2_se_pilot.py`.

Và khi sửa thì lộ tiếp một tầng nữa: tôi định commit parquet thô làm dữ liệu
nguồn, nhưng `.gitignore:64` loại parquet **có chủ đích**. Nếu không kiểm, test
tái lập sẽ **xanh trên máy tôi và đỏ trên clone sạch** — một lỗi chỉ xuất hiện ở
nơi khác, đúng loại khó tìm nhất.

---

## 15. Đối chứng hồi quy bit-exact — gate 20R2.3 (2026-09-10)

### 15.1 ⚠️ ĐÂY LÀ ĐỐI CHỨNG HỒI QUY, KHÔNG PHẢI KẾT QUẢ KHOA HỌC  [gate 3-3, S26]

Nó trả lời **đúng một** câu:

```text
"Ma hom nay co con lam DUNG NHUNG GI no lam hom qua khong?"
```

Nó **không** trả lời *"hôm qua làm có đúng không"*. Một golden **chép lại cả
lỗi**: nếu hôm qua sai, hôm nay sai y hệt ⟹ PASS.

Một dòng "bit-exact PASS" trong luận văn **không kèm nhãn này** sẽ được đọc
thành "kết quả đã được xác nhận". Hai chuyện khác hẳn nhau.

### 15.2 Hai neo, khác cấp — khai CẢ HAI kèm độ phủ  [D1]

```text
A1  results/RAW/phase-T2/golden/ar1_tau1.0_poisson_0.925_s101.json
    NEO       bo sinh dau vao `sla_calib_v2.ar1_matrix`
    PHU       bo sinh AR(1); KHONG cham truc AoI hay SLA  -> TRUC-DOC-LAP
    do duoc   sha256 dbe26ba7...cba8   BIT-EXACT ✅

A2  results/PENDING/phase-T2/sweep_r2/*.parquet  (166 tep)
    NEO       TOAN duong ong tren nhanh LEGACY
    PHU       nhanh legacy DAY DU; nhanh 20r2_measured KHONG
    do duoc   166/166 KHOP, 1866.8 s   BIT-EXACT ✅
```

**Vì sao A1 lưu DIGEST chứ không lưu mảng:** mảng `200000×8 float64` = 12,8 MB,
mà `.gitignore:64` chỉ cho qua `*.json` trong `results/`. Digest 64 ký tự cho
đối chứng **bit-exact y hệt** (sha khác ⟺ bytes khác) **và** chạy được trên
clone sạch. *Một golden không nằm trong git là một đối chứng không tồn tại với
người khác.*

### 15.3 ★★ ĐỘ PHỦ — và vì sao "PASS" ở đây là một câu ĐÚNG dẫn tới kết luận SAI  [gate 3-4]

> **Đối chứng hồi quy neo chính xác những đoạn mã mà bạn KHÔNG đổi.**

```text
NEO A2 di qua      Z_ALL (9 diem legacy) · nhanh SLA cu · lag k = round(z/dt)
CHIEN DICH di qua  Z_ALL_20R2 (13 diem) · SLA exogenous · dispatch --z-grid MOI

giao cua hai  =  phan KHONG doi
=> ma MOI cua G4 KHONG duoc bat ky artifact lich su nao neo
```

Và mã mới chính là **chỗ rủi ro cao nhất** — nó vừa được viết hôm qua.

```text
doi chung hoi quy  -> bao ve QUA KHU
doi chung duong    -> bao ve HIEN TAI
du doan ky truoc   -> bao ve TUONG LAI
Ba thu KHONG thay the nhau. 20R2.3 chi mua duoc cai dau.
```

### 15.4 ★ NEO B — bất biến TẤT ĐỊNH cho mã mới  [D3]

Neo B **không dựa vào quá khứ** (không có quá khứ để dựa). Nó dựa vào ràng buộc
đúng theo suy luận. `test/test_20r2_3_anchors.py`:

```text
1. bon diem z CHUNG giua hai luoi: {0.0, 1.0, 2.0, 4.0}
   -> hai luoi PHAI cho CUNG ket qua tai do, vi lag k = round(z/dt) KHONG
      biet minh den tu luoi nao.
   -> do duoc: 7 cot so (err_total, err_model, err_stale, d_sla, rms_e_model,
      rms_e_stale, cov_e) TRUNG TUNG BIT tren ca hai luoi.
   -> KILL TEST: lam dispatch ro ri mot `a_override` -> test DO dung cho.

2. cua so cham diem TRUNG NHAU vi max(ca hai luoi) = 4.0 CO CHU DICH.

3. doi chung twin-hoan-hao PHAI cho dung 0 -- rang buoc TAT DINH, khong phu
   thuoc che do luu luong (khac `cbr`, von da bi rut vi suy bien).
```

> 💡 **Nguyên tắc:** khi thêm một nhánh mới song song nhánh cũ, tìm những điểm
> **hai nhánh phải trùng** và khoá chúng. Một nhánh mới ít khi sai ở chỗ *mới* —
> nó sai ở chỗ nó **khác** nhánh cũ trong khi lẽ ra phải giống.

### 15.5 Cờ `--z-grid` làm lệnh lịch sử không phát lại được

```text
run_log.jsonl sinh TRUOC G4 -> `cmd` KHONG co --z-grid
--z-grid gio la required=True             -> phat lai nguyen van THAT BAI
```

Công cụ **thêm `--z-grid legacy`** khi phát lại — đúng giá trị T2 vẫn chạy ngầm.
Giá trị không đổi; chỉ lời khai đổi. Ghi trong `replay.why` của artifact.

> Đây là **giá phải trả** của `required=True`, và nó đáng trả: đổi lại, không
> lệnh mới nào có thể im lặng chọn nhầm lưới.

### 15.6 Tự chấm gate 20R2.3

```text
✅ 3-1  Bit-exact PASS                      166/166 + A1 digest
✅ 3-2  Golden trong git + test canh        NC-T2-1 (digest, clone-sach-chay-duoc)
✅ 3-3  Ghi rõ ĐỐI CHỨNG HỒI QUY  [S26]     WHAT_THIS_IS trong artifact
✅ 3-4  ĐỘ PHỦ được khai  ★ THÊM            coverage.NOT_anchored + NEO B
```

### 15.7 Nợ sau 20R2.3

```text
20R2-D7  ĐÃ ĐÓNG: 10 parquet của se pilot (444 KB) đã `git add -f` vào
         results/RAW/phase-20R2/se_pilot/ — đúng tiền lệ commit 60a88784 đặt
         ra khi bảo tồn 166 parquet của T2. Lý do bảo tồn: chúng là BẰNG CHỨNG
         của luật `se_rel = C/√N`, mà luật đó là tham số của BĂNG ĐÃ KÝ.
         Một băng người khác không kiểm lại được thì không phải một băng đã ký.
20R2-D8  MỚI: NEO B kiểm điểm z chung tại τ = 3.0 (một τ). Ràng buộc "hai lưới
         trùng tại z chung" đúng với MỌI τ theo suy luận, nhưng chỉ ĐO tại một.
         Mở rộng khi rẻ; không chặn.
```

### 15.8 Ba bảng công cụ — mỗi bảng một lý do

```text
TOOLS               tất định, tái lập được trên clone sạch          9 tool
NON_DETERMINISTIC   cpu_pilot — đo thời gian; kiểm mã thoát + lược đồ + bất biến
TOO_SLOW_FOR_SUITE  bit_exact_regression — tất định nhưng 31 phút;
                    kiểm bằng lát mỏng `--limit 3`, bản đầy đủ chạy tay
REQUIRES_LOCAL_RAW  (rỗng — D7 đã đóng, giữ cấu trúc)
```

Một test không ai chạy là một test đã chết — cùng kết cục với test đỏ thường
trực. Nên `bit_exact_regression` **không** vào `TOOLS`: nó sẽ làm bộ test chậm
hơn 15 lần. Nó được kiểm bằng lát mỏng, và bản đầy đủ đã commit kèm test đòi
artifact phải là **bản đầy đủ và tươi** (`n_runs == 166`, `rows_are_fresh`).

---

## 16. Sửa trước khi ký — gate 20R2.5 (2026-09-10)

Sáu phát hiện tiền-chiến dịch. Tất cả được sửa **trước** khi ký và **trước**
khi có một con số kết quả nào — nên đây là amendment hợp lệ, không phải HARKing.
Làm đúng những việc này *sau* chiến dịch thì mới là HARKing.

### 16.1 P1 — prereg chưa ký (⛔ đã chặn)

`git tag` không có `phase-20R2-prereg-signed`, §11 còn nguyên mẫu trống. Vì
chưa ký nên prereg **còn được sửa tự do**: mọi thay đổi ở 16.2–16.6 vào thẳng
bản ký lần này, không cần amendment sau ký.

⚠️ Checklist §11 còn ghi *"ngân sách 29,4 phút"* — số đó là bản **A7 kế thừa**
đã bị 20R2.4 thay bằng **74,53 phút hai nhánh** (đo thật, `cpu_pilot.json`).
Người ký phải ký con số 74,53 (+30% = 96,89), không phải 29,4.

### 16.2 P2 — mặc định im lặng lần thứ NĂM: `--calibration` (⛔ đã sửa)

```text
TRUOC  ap.add_argument("--calibration", default=CALIBRATION)
       CALIBRATION = results/LIVE/phase-20R/sla_calibration.json
       -> axis_registry: "self_calibrated", status DEPRECATED (S14)
SAU    required=True; run_fixed_grid(calibration_path=None) -> ValueError
```

§3 ký SLA = `exogenous_g114_S-B` nhưng **không một dòng mã nào bắt buộc** điều
đó. Cùng một cơ chế với `DEFAULT_TAU`, `axis=AXIS_LEGACY`, `sigma=V3.SIGMA`,
`--z-grid`. Lỗi này **đã gây hậu quả thật** — xem 16.3.

**Phạm vi (khai đúng, không tuyên bố quá):** chỉ `main()` và `run_fixed_grid`.
`fixed_summary_with_bootstrap`, `sawtooth_summary`, `compute_margin_cv` **vẫn
còn** mặc định `CALIBRATION`. Chúng không nằm trên đường chạy của 20R2.5.

### 16.3 P3 — băng chấp nhận đã đo trên trục SLA SAI (⛔ đã đo lại)

`tools/20r2_2_se_pilot.py::_measure` gọi `run_fixed_grid(...)` **không truyền
`calibration_path`**, nên rơi về `self_calibrated`.

**Bằng chứng máy móc** (không phải suy luận): parquet đã commit
`results/RAW/phase-20R2/se_pilot/se_3.0.parquet` có cột `w_loss` mang **9 giá
trị khác nhau**, từ 1245,64 đến 4722,69. Trục exogenous có **một** giá trị
duy nhất `w_loss = 5000,0` cho mọi ô. Một bảng đo trên trục exogenous không
thể có 9 giá trị w_loss.

**Đã đo lại** trên `sla_manifest_exogenous_S-B.json`, giữ nguyên seed 201–205
(độc lập với chiến dịch dùng 101–105), cùng công thức đã ký, ghi vào thư mục
MỚI `results/RAW/phase-20R2/se_pilot_exo/` — **không ghi đè** bản cũ, vì tầng
RAW không bao giờ ghi đè và bản cũ là **bằng chứng của chính lỗi này**.

```text
                     self_calibrated      exogenous        doi
C_mean                      0.292206       0.307328     +5.18%
C_sd                        0.117348       0.099090    -15.56%
C_upper                     0.409554       0.406418     -0.77%   <- THAM SO BANG
fitted_exponent            -0.532115      -0.592585    +11.36%
do phu C_upper                  8/10           9/10     TOT HON

bang chap nhan   band_rel(tau) hep di DUNG -0.77% o CA 8 tau
                 (rang buoc van la mc_noise o moi tau)
n_multiplier     KHONG DOI  -> luoi 800 o va ngan sach CPU KHONG bi cham
K_MC, cycle_floor KHONG DOI
```

**Đọc kết quả này cho trung thực.** Từng điểm τ dịch nhiều (đo được ở τ=3:
C 0,165 → 0,220, +34%), nhưng tham số **gộp** `C_upper` chỉ dịch −0,77%. Đó
đúng là việc mà luật gộp sinh ra để làm. Điều đó **không** làm lỗi trở nên vô
hại: ta chỉ biết nó nhỏ **vì đã đo lại**. Một băng mà không ai biết nó đo ở
điều kiện nào thì không phải một băng đã ký.

Chính docstring `cpu_pilot.py` đã viết: *"Một hằng số KHÔNG được kế thừa qua
ranh giới điều kiện mà không đo lại."*

```text
sha256 ban cu (self_calibrated), de doi chieu:
  02-se-pilot.json          418ce31fe9247e2402d1746da9c9c72319ec43ec409606faa53663e343296048
  01-prediction-signed.json 8eff683ff4fe115a322b8639bd17d2dd71c58829fefcbf4b2df3670d83bf1d9c
```

**Đối chứng ×4 vẫn NGƯỢC HƯỚNG ở τ=28** trên trục mới (tỉ số 0,94 thay vì
2,00; τ=20 cho 1,88 đúng hướng). Kết luận của §12 giữ nguyên: ước lượng se từ
5 seed không dùng làm sàn băng được, nên phải gộp. Lỗi trục **không** phải
nguyên nhân của hiện tượng đó.

### 16.4 P4 — "phép kiểm dụng cụ thật" là đèn xanh rỗng (⛔ đã thay)

§13.5 gọi đối chứng twin-hoàn-hảo là *phép kiểm dụng cụ thật* của 20R2. Mã của
nó, `_control_one`:

```python
a_true = c_true.argmin(axis=1)
nc1b   = float((c_true.argmin(axis=1) != a_true).mean())   # so X voi CHINH X
```

Đây là **mệnh đề luôn đúng**: bằng 0 vì đại số, không vì dụng cụ đúng. Nó còn
**không gọi `run_cell`**, nên không chạm tới lag, cửa sổ chấm điểm, hay dispatch
lưới z. Test canh nó chỉ kiểm rằng **một câu văn** có mặt trong docstring.

**Kill test (mutation testing) — đã chạy, cấy lỗi lệch-một `lag_rows =
current - k - 1` vào `run_cell`, ô h2@0.700, τ=3, lưới 20r2_measured:**

```text
doi chung MOI (qua run_cell)   err_total(z=0) = 0.026315   BAT DUOC
NC1b CU                                         0.0        MU
```

**Hợp đồng đúng** (điểm người mới hay sai: "twin hoàn hảo" **không** nghĩa là
err = 0 ở mọi z — twin hoàn hảo về *mô hình* vẫn dùng dữ liệu *cũ*):

```text
err_model == 0 . rms_e_model == 0 . err_total(z) == err_stale(z) moi z
err_total(z = 0) == 0
+ DOI CHUNG CUA DOI CHUNG: ton tai z > 0 co err_total > 0
  (khong co thi lag khong lam gi, va hop dong thoa mot cach TAM THUONG)
```

Đã chạy trên mã hiện tại, **hai lưới × 8 τ × 10 ô**: 0 vi phạm, và nontrivial
(max err tại z > 0 lên tới 0,65). Docstring dòng 6 đã được nói rõ **đại lượng
nào** bằng 0 — chính sự mơ hồ đó cho phép một mệnh đề luôn đúng đứng tên
"đối chứng". `NC1b` được giữ lại để không phá bảng số lịch sử, nhưng đã dán
nhãn đúng bản chất trong mã.

Test canh cũng được nâng từ "một câu văn có trong mã" thành **kiểm hành vi**:
`test_perfect_twin_control_actually_runs_through_run_cell` và
`test_perfect_twin_control_is_not_a_tautology` (test thứ hai tự cấy lỗi
lệch-một và đòi đối chứng phải ĐỎ).

### 16.5 P5 — sidecar và tầng LIVE không nhìn thấy trục AoI (⚠️ đã sửa)

**(a)** §12.7 đã phát hiện nhãn mức-artifact không đủ độ phân giải và thêm
`ESTIMAND_BY_FIELD` — nhưng `write_validity_sidecar` **không bao giờ ghi nó**.
Artifact vẫn mang một nhãn `RMS_ALLACTION_DELAY` cho ba đại lượng khác thang
(đúng va chạm A-T2-3). Nay sidecar ghi cả `estimand_by_field`.

**(b)** Một sidecar sinh với lưới **legacy** qua **mọi** kiểm tầng LIVE:
`axis_role = aoi_axis_free`, có `z_grid_s`, SLA đã duyệt → `True`. Tức đúng
cái phân biệt mà A5 được ký để bảo vệ lại **vô hình** với cái chắn. Lý do:
`decision_error_v2` không gọi bộ sinh AoI nào — trục AoI chỉ đi vào **qua việc
chọn lưới z** (T2-L8).

**Sửa:** `z_grid_id_of()` **suy ra** tên lưới từ chính các điểm z đã chạy,
không nhận lời khai (validity.py, Luật 2), và sidecar ghi `z_grid_id`. Hygiene
H7 đòi giá trị suy ra phải khớp nhánh trong kế hoạch.

### 16.6 P6 — lưu trữ quyết TRƯỚC khi chạy (⚠️ đã quyết)

`.gitignore` loại parquet trong `results/`. Chiến dịch ~167 file × 20–25 KB
≈ 4 MB, cùng bậc với T2 (166 file, 4,1 MB). Mở ngoại lệ **có phạm vi** cho ba
thư mục của chiến dịch + `se_pilot_exo/`, đúng tiền lệ `60a88784`. Quyết
trước khi có dữ liệu, vì quyết sau là mở cửa cho việc chọn giữ cái nào.

### 16.7 Ghi chú đã kiểm, không chặn

```text
a=0.9 ngam        Ke hoach 20R2.5 LUON truyen --a-override tuong minh, ke ca 0.9.
ngan sach         74,53 phut do TREN self_calibrated. KHONG do lai, ly do manh
                  hon "thoi gian khong nhay voi truc": HAI truc cho DUNG 10 o
                  kha thi NHU NHAU (do duoc), cung n, cung luoi z => moi mang
                  CUNG HINH DANG. Chi hang so vo huong w_loss doi. Ngan sach la
                  ham cua HINH DANG, khong phai cua gia tri.
subprocess        cpu_pilot do in-process; chien dich chay subprocess. Chi phi
                  khoi dong ~0,43 s/lenh ~ +1,5% tren 160 lenh. Nho, CO HUONG,
                  nen khai. Dung sai 30% van phu.
realizability     Luot 2 can min_cell_blocks ma 20R2 khong co conformal. Anh xa
                  "so do nao cam vao tieu chi nao" DA KY trong 03-run-plan.json
                  (realizability_pass2_mapping), khong chon sau.
lenh lich su      Cac khoi lenh trong docs/phase-20R/ (06-decision-error.md,
                  07-design-validation.md, 00i-amendment-8.md) sinh TRUOC P2 nen
                  khong co --calibration. Chung KHONG duoc sua: do la ban ghi
                  lich su, khong phai huong dan. Muon phat lai thi them
                  `--calibration results/LIVE/phase-20R/sla_calibration.json`
                  (DUNG truc chung da chay ngam). Loi "required" bay ra khi phat
                  lai la CO ICH: no bat nguoi phat lai phai CHON truc, thay vi
                  thua ke im lang.
Sheppard          Du doan ky tai z = 0,365; luoi co 0,366. Do doi tuong doi
                  ~0,10-0,14%, khong dang ke so voi bang >= 2,73%. De 20R2.6 khai.
D8                Dong MIEN PHI o hygiene H6: CRN cho phep kiem "hai nhanh trung
                  tung bit tai 4 diem z chung" tren MOI (tau, a, seed) -- 80 cap
                  x 10 o, thay vi chi tau=3 nhu NEO B.
```

### 16.8 Băng cũ/mới đủ 8 τ, và vì sao dịch ĐỀU −0,77%

```text
tau      band_rel CU    band_rel MOI      doi    rang buoc
0,5         2,7474%        2,7263%     -0,77%   mc_noise
1,0         3,8854%        3,8556%     -0,77%   mc_noise
2,0         5,4947%        5,4527%     -0,77%   mc_noise
3,0         6,7297%        6,6781%     -0,77%   mc_noise
5,0         8,6880%        8,6214%     -0,77%   mc_noise
10,0        8,6880%        8,6214%     -0,77%   mc_noise
20,0        8,6880%        8,6214%     -0,77%   mc_noise
28,0        8,6880%        8,6214%     -0,77%   mc_noise
```

Dịch **đều** vì `band_rel = max(AXIS_FLOOR, K_MC · se)` mà số hạng `mc_noise`
**chi phối ở mọi τ** (không τ nào bị `AXIS_FLOOR` ràng buộc). Khi đó
`band_rel ∝ C_upper`, nên mọi τ thừa hưởng đúng tỉ lệ −0,77%. Nếu có τ nào bị
sàn trục ràng buộc thì τ đó sẽ **không** dịch — đó là cách đọc bảng này.

`K_MC = 3,0`, `cycle_floor = 200`, `n_multiplier` đều **KHÔNG đổi**.

**Vì sao `C_upper` gần như đứng yên dù từng điểm dịch ~34%.** `C_upper =
mean + 1·sd` trên 10 điểm. Nếu mọi điểm cùng dịch một chiều thì `C_upper` dịch
theo đúng chừng ấy. Nó chỉ dịch −0,77%, nên các dịch chuyển phải **ngược dấu
nhau và triệt tiêu**. Điều đó **ủng hộ** chẩn đoán §14.2: `C` của từng điểm bị
**nhiễu 5-seed chi phối** (sd 0,117 trên mean 0,292 ≈ 40% hệ số biến thiên).
Đổi trục SLA xáo các ước lượng đó **trong dải nhiễu của chính chúng**. Luật gộp
được thiết kế đúng để hấp thụ loại dao động này.

Đây là một **phép đo độ nhạy (sensitivity analysis) có kết quả**, không phải
một lời bào chữa:

```text
CHUNG MINH      tham so GOP ben voi doi truc SLA -- da DO, khong phai suy doan
KHONG CHUNG MINH `se` cua tung tau la dung. Nhung bang KHONG dung so tung tau,
                 no dung LUAT -- va do la thiet ke CO CHU DICH.
```

Phân biệt phải giữ cho đúng thì tự:

```text
"loi vo hai"                       = loi khai TRUOC khi do        -> KHONG duoc noi
"loi co hau qua NHO, DA DUOC DO"   = phat bieu SAU khi do         -> cai ta noi
```

**Độ phủ 9/10 — điểm còn chưa phủ là gì.**

```text
CHUA PHU:  tau = 28,  n_multiplier = x4,  200 chu ky,
           is_campaign_config = TRUE          <- CHINH la cau hinh chien dich
           C = 0,4812   se_rel do duoc = 3,402%   3sigma rieng = 10,207%
```

So với bản cũ (2 điểm chưa phủ): điểm τ=20 ×1 nay **đã được phủ** — nó vốn là
cấu hình **pilot**, không còn dùng. Điểm τ=28 ×4 **vẫn chưa phủ**, và nó **là**
cấu hình chiến dịch.

⇒ Chính sách đọc đã ký ở `C_coverage` **vẫn áp dụng nguyên vẹn cho ô τ=28**:
một trượt riêng ở ô này, trong phạm vi đã ghi, là **ứng viên của nhiều bằng**,
không phải một phát hiện. Băng tại τ=28 (8,6214%) vẫn **hẹp hơn** 3σ riêng của
ô đó (10,207%) — đúng như `why_accepted` đã ký. **20R2.6 không phải tra lại.**

### 16.9 Hai loại bằng chứng cho P3 — dùng đúng từ

```text
BANG CHUNG LOAI TRU  (exclusion)   9 gia tri w_loss (1245-4722)
                                   -> chung minh KHONG PHAI exogenous (chi co 1 gia tri)
BANG CHUNG DINH DANH (identification) 9 gia tri do KHOP DUNG file self_calibrated
                                   -> chung minh CHINH LA self_calibrated
```

Ở đây ta có **cả hai**, nên kết luận đóng kín. Nhưng hai loại này không thay
nhau: loại trừ một mình chỉ nói "không phải X", không nói "là Y". Trong văn
bản phải dùng đúng từ cho từng loại.

### 16.10 Ngân sách: lập luận CẤU TRÚC + phép đo, và giả định ngầm của nó

```text
LAP LUAN  sigma_max giong het o hai file (do bit-exact) -> dong rho(t) giong het
          10 o giong nhau . n giong nhau . luoi z giong nhau
          SLA chi doi vai hang so VO HUONG (w_loss, t_delay, t_loss)
          => moi mang CUNG HINH DANG => ngan sach la ham cua HINH DANG
```

⚠️ **Giả định ngầm phải gọi tên: KHÔNG có đường điều khiển phụ thuộc DỮ LIỆU.**
Tức không vòng lặp dừng sớm theo giá trị, không sắp xếp mà thời gian phụ thuộc
giá trị, không nhánh `if` theo giá trị. Trong `run_cell` giả định này **đúng**:
`argmin`, `np.interp` và phép so ngưỡng đều có chi phí theo **kích thước** mảng.

Nhưng nó có thể bị phá bởi một thay đổi mã hoàn toàn hợp lý — ví dụ thêm một
đường tắt "nếu mọi chi phí bằng nhau thì bỏ qua", hoặc một `while` lặp đến khi
hội tụ. Vì vậy dạng **mạnh nhất là cả hai đi cặp**:

```text
LAP LUAN giai thich VI SAO hai so phai gan nhau  (co the sai neu co duong
                                                  phu thuoc du lieu chua ai thay)
PHEP DO  xac nhan RANG chung gan nhau            (khong biet co tong quat khong)
```

Ngân sách 74,53 phút giữ nguyên, **và** H9 sẽ đo lại trên chính chiến dịch —
đó là phép đo xác nhận. H9 là hạng BUDGET nên một trượt ở đó không làm kết quả
sai.

### 16.11 Kill test các nhánh dừng của guard — ĐÃ TỰ TAY CHẠM

"Guard chặn khi chưa ký" chỉ chứng minh **một** nhánh. Mã chưa từng chạy là mã
chưa chứng minh được gì. Đã chạm **đủ 6 nhánh** trong một **clone tạm có
`origin` GIẢ** (một bare repo cục bộ) — nhờ vậy chạm được nhánh sau kiểm remote
**bằng chính mã thật**, không phải bằng cách vô hiệu hoá cái chắn:

```text
1  chua co tag (local)              -> DUNG: chua co tag ... §11 chua ky        OK
2  co tag local, CHUA co tren remote-> DUNG: tag chua co tren REMOTE            OK
3  worktree BAN ngoai chien dich    -> DUNG: worktree ban ... (?? README.md)    OK
3b BAN trong results/               -> KHONG chan (dung: resume phai chay duoc) OK
4a DUNG CU doi SAU tag              -> DUNG: ... AMENDMENT: measurements/...    OK
4b KE HOACH doi SAU tag             -> DUNG: ... AMENDMENT: 03-run-plan.json    OK
5  moi truong/commit KHAC phien truoc -> DUNG: moi truong/commit KHAC ...       OK
6  sha tren dia LECH so cai         -> DUNG: ... file tren dia KHAC so cai      OK
```

Nhánh **4** là khó chạm nhất: nó nằm **sau** nhánh 2, nên trong một clone
thường không bao giờ tới được. `origin` giả giải quyết đúng chỗ đó.

Clone tạm đã xoá; repo thật không bị chạm (0 tag, HEAD `c42f7367`, `origin` vẫn
là remote thật, không tiến trình nào còn chạy).

### 16.12 C1 — ô "Commit sha" ở §11 là VÒNG TỰ QUY CHIẾU (đã sửa)

Ô cũ ghi *"sha CỦA BẢN prereg được ký"*. Ô đó **không thể điền đúng**: sha của
commit phụ thuộc nội dung prereg, mà prereg lại chứa sha đó — như một file
không thể chứa sha256 của chính nó. **TAG** mới là thứ gắn chữ ký với commit:

```text
Commit sha : = DICH cua tag `phase-20R2-prereg-signed`
             kiem: git rev-parse phase-20R2-prereg-signed^{commit}
```

**Chuỗi ghim đã kiểm là KHÔNG CÓ VÒNG:**

```text
prereg ──ghim sha──► 01-prediction-signed.json ◄──ghim sha── 03-run-plan.json
prereg ──ghim sha──► 03-run-plan.json
01-prediction ──TRICH DAN duong dan (KHONG ghim sha)──► prereg     [an toan]
```

`01-prediction-signed.json` có trường `"authority": ".../00-preregistration.md"`
— đó là **trích dẫn đường dẫn**, không phụ thuộc **nội dung**, nên không tạo
vòng. Đã thêm test canh `test_pin_chain_has_no_cycle`: nếu ai đó thêm prereg vào
`inputs_sha256` của kế hoạch, vòng khép lại và **không file nào ký được nữa**.

### 16.13 C3 — tag có thể BỊ DỜI (đã gia cố)

`git ls-remote` chỉ chứng minh tag **tồn tại lúc kiểm**, không chứng minh nó
**bất biến**: một annotated tag có thể bị xoá rồi tạo lại (`git push -f --tags`).

**Gia cố:** `env_fingerprint()` nay ghi `signed_tag_commit` (đích của tag) vào
sổ cái, và hygiene **H2** đòi `signed_tag_commit == git_commit`. Nhờ vậy **sổ
cái TỰ chứng minh** chiến dịch chạy đúng commit đã ký — không cần ai tin rằng
tag chưa bị dời.

Đã kill test: dời tag sang commit khác ⇒ `tag_ok = False` ⇒ H2 **FAIL**.

*(Tuỳ chọn chưa làm: `git tag -s` ký GPG, thêm bằng chứng mật mã về AI đã ký.
Cần khoá GPG nên để người ký quyết.)*

### 16.14 Thứ tự thi công đã dùng

```text
1. sua P2/P4/P5 trong measurements/decision_error_v2.py
2. khai tuong minh gia tri lich su o t2_6_plan/run + bit_exact_regression
   (GIA TRI khong doi -> NEO A giu nguyen: da chay lai --limit 3, KHOP 3/3)
3. do lai se pilot tren exogenous -> 02-se-pilot.json -> 01-prediction-signed.json
4. sinh 03-run-plan.json (tat dinh: hai lan sinh cung sha256)
5. sinh lai axis_audit.json (harness doi sha -> khong sinh lai thi full suite
   bao "loi moi" gia)
6. .gitignore ngoai le co pham vi
7. ★ NGUOI KY dien §11, commit, tag, push   <- KHONG cong cu nao lam ho
8. tools.20r2_5_run  ->  tools.20r2_5_hygiene  ->  commit NHAN CHUNG
9. chi sau do moi mo 20R2.6
```

---

## 17. Cách đọc — KHOÁ trước khi mở chiến dịch (gate 20R2.6)

Chiến dịch đã chạy xong (167/167, vệ sinh PASS 9/9, tag
`phase-20R2-campaign-hygiene` → `82be66d7`). **Chưa một cột kết quả nào được
mở.** Mục này khoá cách đọc **trước** khi mở, để lúc mở chỉ còn **một** cách đọc.

### 17.0 ★ CÔNG KHAI — pilot đã cho XEM TRƯỚC

`02-se-pilot.json` (seed 201–205, trục exogenous) chứa `err_bar` theo τ. So với
bảng Sheppard đã ký, nó **đã cho xem trước** hình dạng của kết quả:

```text
tau     0,5      1       2       3       5      10      20      28
rel   -9,9%   -6,9%   -4,5%   -3,8%   -2,9%   -0,1%   +4,2%   +6,2%
band   2,73%   3,86%   5,45%   6,68%   8,62%   8,62%   8,62%   8,62%
```

⚠️ **Mọi quyết định trong §17 được viết KHI bản xem trước ĐÃ tồn tại.** Điều đó
không làm chúng vô hiệu — pilot (seed 201–205) và chiến dịch (seed 101–105) là
hai mẫu **độc lập**, đúng thiết kế **tách mẫu**: pilot là mẫu *khám phá*, chiến
dịch là mẫu *khẳng định*. Nhưng nó **phải được khai**, và người đọc tự đánh giá.

Hệ quả cụ thể, phải nói thẳng: theo pilot, cách đọc §17-G2 cho **2 MISS**, còn
cách đọc nguyên văn cho **6 MISS**. G2 là lựa chọn **có hậu quả thật**. Vì vậy
§17-G2 bắt buộc báo cáo **cả hai** con số.

**Chưa đọc một con số chiến dịch nào khi viết mục này.**

### 17-G1 Quần thể và estimator chính

```text
CHINH   a = 0.9, 8 o gate (poisson/h2 x 4 rho_bar), z = 0.366 (diem luoi)
        estimator: trung binh qua O cho TUNG seed, ROI qua seed
        -- dung estimator da dung de dung luat se, khong duoc doi
a = 0.5 MO TA. Bang CHUA duoc kiem o a = 0.5 (no 20R2-D6) -> khong phan quyet.
```

Lý do `a = 0.9` là chính: băng được dựng **tại** điều kiện đó. Một băng đo ở điều
kiện này không được kế thừa sang điều kiện khác mà không đo lại — chính nguyên
tắc đã dùng ở §16.3.

### 17-G2 ★ Ba mức, không phải hai

```text
rel >= 0            AT_OR_ABOVE         dung huong
-band <= rel < 0    BELOW_WITHIN_BAND   thap hon, nhung TRONG nhieu
rel < -band         BELOW_BEYOND_BAND   thap hon CO Y NGHIA  -> MISS
HIT = khong phai BELOW_BEYOND_BAND
```

**Vì sao ba mức, không phải đọc nguyên văn.** Đọc nguyên văn ("ước lượng điểm
≥ Sheppard") hỏng về mặt thống kê: nếu sự thật *đúng bằng* Sheppard ở mọi τ, mỗi
ước lượng vẫn có ~50% khả năng rơi xuống dưới chỉ vì nhiễu — trung bình ~4/8 MISS
**dù dự đoán hoàn toàn đúng**. Một tiêu chí mà lý thuyết đúng vẫn trượt một nửa
thì không kiểm được gì.

**Ngưỡng này KHÔNG phải phát minh mới.** Đã đo: `band_rel = 3 · se_rel` **đúng ở
cả 8 τ** (mọi τ đều ràng buộc bởi `mc_noise`, `K_MC = 3`). Nên "rel < −band"
chính là kiểm định **3σ có hướng**, và `band_rel` chính là thứ §12.4 đã ký với
tên **"băng chấp nhận"**. G2 chỉ đọc đúng cái đã ký.

⚠️ **BẮT BUỘC** báo cáo kèm `n_hit_literal_point_reading` (số τ có `rel ≥ 0`).
Gộp ba mức thành hai là chỗ sự thật bị giấu — cùng bài học với đèn xanh rỗng.

### 17-G3 z: bảng ký tại 0,365, lưới có 0,366

Bảng Sheppard đã ký tính tại `z = 0,365`; lưới chiến dịch có `0,366`. **Bảng ký
là CHÍNH.** Giá trị tại `0,366` là **kiểm độ vững**. Nếu một phán quyết **lật**
giữa hai giá trị thì phải khai rõ (`verdict_changes`). Độ dời tương đối ~0,10–0,14%,
nhỏ so với băng ≥ 2,73%, nên không kỳ vọng lật.

### 17-G4 Cặp đơn điệu: ba giá trị, mẫu số 7 CỐ ĐỊNH

```text
DECREASING / INCREASING / UNREADABLE (sigma < 3)
UNREADABLE KHONG duoc tinh la don dieu. Mau so GIU 7.
PASS = DECREASING >= 6/7.  INCREASING >= 2 cap -> HOLD_SUSPECT_ESTIMATOR.
```

`UNREADABLE` là **thiếu thông tin**, không phải bằng chứng. Cho cặp không đọc
được rời khỏi mẫu số sẽ làm mẫu số **co lại sau khi thấy dữ liệu** — đúng một
lối rẽ.

⚠️ **σ là ước lượng BẢO THỦ (phải khai).** `ar1_matrix` rút cú sốc theo thứ tự
cố định từ cùng seed; với τ ≤ 5 mọi τ có cùng `n` nên dùng **cùng dãy cú sốc**,
chỉ khác φ. Các ước lượng ở τ gần nhau vì thế **tương quan dương**, trong khi
`se_diff = √(se_i² + se_j²)` giả định độc lập. Tương quan dương làm `se_diff`
thật **nhỏ hơn**, nên σ ta tính là **ước lượng thấp**. Hướng sai số này an toàn
(khó tuyên bố "đọc được" hơn thực tế), nhưng phải khai.

### 17-G5 RQ-20R2e: MÔ TẢ, không phán quyết

Không có luật phán quyết nào được ký cho RQ-20R2e. Nên nó **chỉ mô tả**, không
vào gate. `z` legacy dùng **0,30** (điểm lưới) thay `0,30237` (đã ký) — phải khai.
Ghép cặp **theo seed** (CRN) để tương phản chính xác hơn.

### 17-G6 cbr: chẩn đoán, báo cáo RIÊNG

§13.5 ký "báo cáo cơ chế nào thắng" nhưng không định nghĩa "thắng". Khoá:

```text
err(cbr) < min(8 o gate)  -> CO CHE 1 (cbr deu theo thoi gian -> twin cu van dung)
err(cbr) > max(8 o gate)  -> CO CHE 2 (bien ~ 0 -> argmin tuy y)
nam trong dai              -> KHONG XAC DINH
```

cbr **không bao giờ** vào trung bình của 8 ô gate (`AGGREGATION_FALLACY_GUARD`).

### 17-G7 Nhánh "(b) estimator có bug" — ĐÃ THOẢ

`PRIMARY_directional.if_violated` có nhánh "(b) estimator có bug — chạy đối chứng
TRƯỚC khi diễn giải". Nhánh này **đã được thoả**: H4 đã chạy đối chứng
twin-hoàn-hảo **cả trước và sau** chiến dịch, cả hai `rc=0`. Vì vậy một MISS
**không** kéo theo những lần chạy lại tuỳ hứng.

### 17-H THĂM DÒ CÓ ĐĂNG KÝ (không vào gate)

Đăng ký **trước khi mở**, nên hợp lệ để kiểm trên mẫu khẳng định:

```text
H-B  err_stale(z) / Sheppard(z) < 1 tai MOI tau
     Co che: bien chi phi co KY VONG KHAC 0. Theo Rice (1944), tan suat mot qua
     trinh Gaussian cat muc 0 ti le voi exp(-mu^2 / 2s^2); khi mot duong THUONG
     XUYEN tot nhat, dau cua bien it doi hon truong hop Sheppard (ky vong 0).
     Gioi han o do tre lon cung giam tu 1/2 xuong 2*Phi(m)*Phi(-m).
     Doi tuong so: err_stale (thuan do CU), KHONG phai err_total.

H-A  err_total / Sheppard TANG theo tau, va err_model / err_total TANG theo tau
     Co che: SAN mo hinh. err_model > 0 khong phu thuoc z, trong khi Sheppard -> 0
     khi tau lon. Ti so vi the tang, va co the CAT QUA 1.
```

Hai cơ chế **ngược chiều nhau**: H-B kéo xuống ở mọi τ, H-A đẩy lên ở τ lớn. Đó
đúng là hình dạng pilot đã cho xem trước (âm ở τ nhỏ, dương ở τ lớn).

### 17-S Đính chính bảng vi phạm Sheppard đã ký

Dự đoán đã ký **không được sửa**. Nhưng bảng lý do của nó có hai lỗi, và nhánh
"(a) phải nêu tên vi phạm đẩy lỗi XUỐNG" được thực hiện **ở đây, trước khi mở**:

```text
1. "ky vong khac 0 => co san" gop HAI hieu ung NGUOC DAU.
   - san mo hinh (err_model) day err_total LEN  -- da ghi
   - bien co ky vong != 0 day err_stale XUONG   -- BI BO SOT (Rice, xem H-B)
2. "nugget MA(1)" KHONG TON TAI trong harness nay.
   Da doc ma: measurements/sla_calib_v2.ar1_matrix sinh AR(1) THUAN, moi link
   mot dong cu soc RIENG, khong co thanh phan MA nao. Clip co, nhung ti le
   clip < 0,09%.
```

⇒ Lập luận "3/4 vi phạm đẩy cùng MỘT hướng" **không đứng vững**. Dự đoán có
hướng vẫn là dự đoán có hướng, nhưng cơ sở của nó yếu hơn bản đã ký tuyên bố.

### 17-W ω₀ = 0 theo cấu tạo — và vì sao đó là GIỚI HẠN

§7 ký "cố định ω = ω₀" nhưng không nêu giá trị. Thực tế `ar1_matrix` sinh **8
link ĐỘC LẬP**, không có tham số tương quan chung nào. Đo được (n = 200 000,
seed 7): **max |r| chéo = 0,023**. Vậy:

```text
omega_0 = 0  .  c(0) = 1 theo dinh nghia  .  sigma_eff_proxy = sigma
```

Gate 20R2-3′ được thoả **một cách TẦM THƯỜNG**. Đây **không** phải tin tốt: nó
nghĩa là mọi kết luận của 20R2 chỉ đúng **có điều kiện theo giả định các link
độc lập**. Tải chung giữa các link (Q7 đã cảnh báo) **chưa hề được đo**. Vào
Threats to Validity.

### 17-D2 20R2-D2 QUÁ HẠN

`GIA TRI MOC` của hai estimand vẫn `null`, trong khi hạn ghi là *"điền SAU pilot,
TRƯỚC chiến dịch"*. Chiến dịch đã chạy xong. **Khai là QUÁ HẠN**, không lặng lẽ
điền rồi coi như đúng hạn. Nếu cần giá trị mốc, lấy từ pilot (vốn có trước chiến
dịch) và **dán nhãn ĐIỀN MUỘN**.

### 17-P Thứ tự bắt buộc (blind analysis)

```text
1. §17 + bo cham + test tren du lieu GIA  -> commit -> tag
   phase-20R2-adjudicator-frozen -> push        [CHUA mo mot o nao]
2. chay bo cham. Guard doi: tag co tren REMOTE; bo cham/du doan/prereg KHONG
   doi tu tag; hygiene 05 = PASS (gate VALIDITY truoc gate OUTCOME, NT 56)
3. commit artifact + bao cao. MOI MISS giu nguyen, cung do chi tiet nhu HIT.
```

⚠️ Nếu sau khi mở phát hiện bộ chấm có lỗi: **không sửa rồi chạy lại im lặng**.
Amendment + tag mới + giữ **cả hai** artifact. Cùng quy tắc với chiến dịch.

---

## 18. Hạn chế KẾ THỪA — trả lời từng cái (bổ sung SAU 20R2.6)

⚠️ **Mục này lẽ ra phải có TRƯỚC chiến dịch.** Nó được thêm sau khi phán quyết
20R2.6 phát hiện rằng một ràng buộc đã ký ở T2 **đã rơi im lặng** qua ranh giới
phase. Đây là **trả lời muộn**, và được khai đúng như vậy.

Sổ đăng ký: `docs/inherited_restrictions.json`. Cái chặn:
`test/test_inherited_restrictions.py` — prereg không nhắc một hạn chế thì test **đỏ**.

### 18.1 Đây là mặt đối ngẫu của "mặc định im lặng"

```text
mac dinh im lang     mot GIA TRI duoc ke thua ma khong ai khai
                     -> da bat duoc 5 lan (DEFAULT_TAU, axis, sigma, --z-grid,
                        --calibration). Co cong cu: axis_audit, required=True.
han che roi im lang  mot RANG BUOC DA KY bi MAT khi sang phase moi
                     -> CHUA co cong cu nao bat. Day la lan dau bi bat, va bi
                        bat MUON (sau khi da mo hop).
```

Kiểm toán tiền-chiến dịch ở 20R2.5 **chỉ săn mặc định im lặng**, không đối chiếu
quần thể §12.2 với các hạn chế còn hiệu lực từ T2. Bộ chấm 20R2.6 cũng không
bắt buộc in bảng theo từng ô. Phép chặn `AGGREGATION_FALLACY_GUARD` được viết
**chỉ cho cbr**, trong khi lẽ ra phải áp cho **cả** quần thể.

### 18.2 Trả lời từng hạn chế

**T2-R7: ACCEPT** — `ρ̄ = 0.96` (poisson và h2) đánh dấu `EXTRAPOLATION_CONTAMINATED`,
**không dùng làm headline**, **không loại khỏi lưới chạy**
(`docs/phase-T2/00-preregistration.md` A-T2-1 mục (c) và (e), ký 2026-09-08).

```text
⚠️ TRA LOI MUON. Prereg 20R2 KHONG nhac R7 mot dong nao, va quan the headline
   8 o cua §12.2 GOM CA HAI o 0.96. Phan quyet 20R2.6 da cong bo voi quan the do.

HE QUA DO DUOC (tham do, xem 06b):
   ti so err_total/Sheppard theo tung o trai tu 0,006 den 1,655
   gop 8 o (DA KY)            0,896 ... 1,099   -> 3 MISS tai tau <= 2
   trung vi 8 o               1,017 ... 1,342   -> KHONG MISS nao
   gop 6 o (bo 2 o R7)        1,048 ... 1,293   -> KHONG MISS nao
   gop 7 o (chi bo h2@0.960)  1,023 ... 1,252   -> KHONG MISS nao
   => TOAN BO 3 MISS phu thuoc MOT o: h2@0.960, noi quyet dinh gan nhu khoa cung
      (mot duong la argmin 100% thoi gian, m = 3,11, Rice e^(-m^2/2) = 0,008).

XU LY (dung thu tu, KHONG doi estimand sau khi mo):
   1. Phan quyet CHINH GIU NGUYEN 5/8 tren quan the 8 o DA KY. Doi quan the
      BAY GIO -- ke ca sang mot luat co san tu truoc -- van la doi estimand
      SAU khi thay du lieu.
   2. Do nhay theo R7 dung NGAY CANH phan quyet, KHONG thay the no. Duoc phep
      vi R7 co TRUOC 20R2 va ly do cua no DOC LAP voi ket qua.
   3. Tu 20R2.7 tro di: bang theo TUNG O la BAT BUOC, dung canh so gop.
```

**D-PENDING: ACCEPT** — artifact trong `results/PENDING` không dùng làm headline
(`docs/phase-D/01-data-classification.md`).

```text
DA KIEM: chuoi dau vao HEADLINE cua 20R2 (06-adjudication.inputs_sha256) gom
   01-prediction-signed.json . 02-se-pilot.json . 03-run-plan.json
   04-campaign-log.jsonl . 05-hygiene.json
-> TAT CA nam trong docs/, KHONG file nao trong results/PENDING. KHONG vi pham.
   (cpu_pilot.json va grid_prescreen.json trong PENDING chi dung cho THIET KE
    -- ngan sach, luoi kha thi -- khong phai ket luan khoa hoc.)
```

**20R-SMOKE-CITE: ACCEPT** — artifact có `is_smoke = true` chỉ để debug, không
được trích (`docs/phase-20R/00o-amendment-14.md` mục 16).

```text
DA KIEM: is_smoke duoc DINH NGHIA la (n < 50000). Doi chung twin-hoan-hao cua
   20R2.5 nam trong TANG results/SMOKE nhung chay n >= 200000, nen no KHONG
   phai mot is_smoke artifact. KHONG vi pham.
⚠️ TRUNG TEN phai ghi ro: TANG `results/SMOKE` (phan tang tu 2026-08-22) KHAC
   co `is_smoke` (n < 50000). Hai thu nay khong lien quan, va mot nguoi doc
   nhanh se nham -- da ghi vao so dang ky.
```

### 18.2b Hạn chế do CHÍNH 20R2 sinh ra — trả lời ngay ở đây

Hai hạn chế dưới đây được ghi vào sổ đăng ký khi đóng phase 20R2. Chúng ràng buộc
**cả 20R2 (hồi tố)** và **21R2**. Trả lời hồi tố cho 20R2:

**20R2-R1: ACCEPT** — quần thể 8 ô gate **không đồng nhất**; mọi số gộp phải đứng
**cạnh** một bảng theo từng ô.

```text
DA TUAN THU HOI TO, nhung MUON:
  06-adjudication.md  ban dau CHI co so gop -> da them con tro "bat buoc doc kem
                      06b" va hai dong Threats moi
  06b-per-cell.md     bang theo tung o, do nhay theo T2-R7
  07-dsla.json        bang theo tung o + Delta_cond, so gop DAN NHAN "bi so 0
                      CAU TRUC chi phoi"
  08-handoff           bang em 20 hang theo tung (o, a)
LY DO DOC LAP KET QUA: ti so theo tung o trai 0,006-1,655 (chenh ~300 lan). Mot
  trung binh tren quan the phan hoa co do khong dai dien cho o nao.
```

**20R2-R2: ACCEPT** — `rms_e_model` có **hai** nghĩa; không so sánh, không thay thế
nhau.

```text
decision_error_v2.rms_e_model = RMS_ALLACTION_DELAY (all_action, delay_ms)
cert/tau_sweep.rms_e_model    = margin, cost_ms     (DI QUA w_loss)

⚠️ KHI DONG PHASE TOI DA SUYT LAP LAI DUNG LOI NAY: tinh em tu du lieu chien dich,
   so voi em_bar cua T2, thay lech toi -99%, va gan nhu bao do la MOT PHAT HIEN.
   No KHONG phai phat hien -- no la LOI PHAM TRU (A-T2-3). Bang em/A cua §13.5
   lay nguon tu results/PENDING/phase-T2/sweep_r3 = cert.tau_sweep, tuc estimand
   THU HAI.
=> D4/D5 KHONG dong duoc bang du lieu chien dich. Chan co hoc:
   test/test_20r2_8_handoff.py (5 test, gom mot test doi KHONG duoc bia ra em/A
   va mot test doi D5 KHONG bi go nham thanh "da dong").
```

### 18.3 Cách tôi đi tìm, để người sau lặp lại được

```text
1. grep cac cum tu chi HAN CHE qua MOI prereg/amendment cua cac phase truoc:
     "khong dung lam headline" . "khong duoc trich" . "chi dung de chan doan"
     "DOWNGRADED" . "khong vao gate" . "CHI MO TA" . "khong duoc dung lam"
2. Voi TUNG han che tim duoc: doi chieu voi (a) QUAN THE cua phase hien tai,
   va (b) CHUOI DAU VAO HEADLINE (inputs_sha256 cua artifact phan quyet).
3. Han che nao co CO DO DUOC trong du lieu thi them mot test HANH VI kiem co
   do -- va kiem ca chieu nguoc: neu MOI o deu mang co thi co do vo nghia.
```

Bước 3 đã làm cho T2-R7: `test_T2_R7_cells_are_flagged_in_the_campaign_data`
đòi **đúng** hai ô 0,96 mang cờ, không nhiều hơn, không ít hơn.

---

## 19. G4 — mô hình cơ chế, holdout a = 0.5 (gate 20R2.6c)

Biến các phát hiện **thăm dò** của 06b thành một phép thử **khẳng định**. Khoá
trước khi mở `err_stale` của a = 0.5.

### 19.0 Hai dung sai đề xuất ban đầu ĐỀU HỎNG — đã đo

```text
UNG VIEN 1  +-0,15 TUYET DOI, o h2@0.960
            rice = 0,0080 | quan sat 0,0024-0,0076 | khoang qua duoc [0; 0,158]
            => MOI gia tri >= 0 deu qua. PHEP THU KHONG THE TRUOT -> den xanh rong.

UNG VIEN 2  +-20% TUONG DOI, o h2@0.925
            rice = 0,4040 | lech -25,5% .. -14,6%
            => vuot 20% o 3/8 tau. DA TRUOT SAN tren du lieu kham pha
               -> chay mot phep "xac nhan" ma ket cuc da biet truoc la that bai.
```

**P2 bị RÚT.** Luật đề xuất *"ô ≥ 3 đường sống ⇒ tỉ số > 1"* có **phản ví dụ nằm
sẵn** trong bảng 06b: `poisson@0.700` có 3 đường sống nhưng tỉ số 0,945–1,385,
tức ≤ 1 ở 2/8 τ.

### 19.1 Nguyên lý: phép thử phải CÓ KHẢ NĂNG trượt (severity)

Mayo (*Statistical Inference as Severe Testing*, 2018): một phép thử chỉ có giá
trị khi, **nếu giả thuyết sai**, nó có khả năng cao cho kết quả **trượt**.

```text
seed moi 301-305 tren cung 8 o  =  PHEP THU YEU
   m, so duong song va bang chi phi la tinh chat cua O, khong cua SEED.
   Seed moi chi kiem nhieu lay mau -> gan nhu chac chan "qua".

holdout a = 0.5 theo TUNG O     =  PHEP THU MANH
   - DA CHAY trong chien dich -> ton 0 phut CPU
   - CHUA AI MO theo tung o: bo cham 06 chi in so GOP cua a=0.5 (phai khai)
   - CAU TRUC bien KHAC HAN: m tang, so duong song doi. Mo hinh phai du doan
     dung o dieu kien no CHUA THAY.
   - Luu y CRN: a=0.5 dung CUNG dong cu soc voi a=0.9, chi nhan ti le. Nhieu la
     CHUNG, nhung CAU TRUC la khac -- va cau truc moi la thu ta muon kiem.
```

### 19.2 ⚠️ CÔNG KHAI: G4 được CHỌN trên dữ liệu khám phá

**Ba** mô hình đã được so trên dữ liệu khám phá (a = 0.9) rồi G4 được chọn vì
khớp tốt nhất: Rice xấp xỉ độ trễ nhỏ; Gauss **hai** chiều chính xác cho 2 đường
đầu; và G4. Đây là một **lối rẽ** (garden of forking paths). Mô hình Gauss hai
chiều thật ra khớp `poisson@0.700` tốt hơn (0,93) nhưng **trượt nặng** ở mọi ô có
3 đường sống.

Chính vì lối rẽ đó mà holdout là **bắt buộc**, và phải là **điều kiện mới**.

### 19.3 Mô hình G4 — không có tham số nào được khớp

```text
c(t) in R^4 ~ N(mu, Sigma), tu tuong quan r = exp(-z/tau) cho moi thanh phan
du doan: err_stale = P(argmin c(t) != argmin c(t-z))      -- Monte Carlo 1e6
(mu, Sigma) uoc tu seed 901-903 (NGOAI thiet ke), tu chi phi TWIN c_fresh
```

⚠️ **Đính chính so với 06b:** `err_stale` so twin với **chính nó** ở thời điểm cũ,
nên cấu trúc biên phải lấy từ `c_fresh` (chi phí **twin**), không phải `c_true`.
06b tính `m` từ `c_true` — dùng được để *mô tả*, nhưng G4 phải dùng `c_fresh`.

Các trường hợp đã biết là **trường hợp riêng**: `m = 0` và 2 hành động → đúng
Sheppard; kỳ vọng khác 0 → nén (Rice); ≥ 3 đường sống → giãn.

### 19.4 Dung sai DẪN XUẤT, không chọn tay

```text
Thong ke : trung binh qua 8 tau cua err_stale/Sheppard(0,365), tai z = 0,366,
           a = 0.5, TUNG o gate
Dat o    : |quan sat - G4| <= max(0,10 * G4 ; 0,02)
Dat P1   : >= 7/8 o

Dan xuat:
  0,10 = bien sai so lon nhat cua 7 o kham pha (7,6%) + nhieu seed (~1-2%)
  0,02 = SAN tuyet doi, vi hai du doan gan 0 (0,022 va 0,000) -- o do sai so
         TUONG DOI vo nghia
  7/8  = khop DUNG hieu nang tren kham pha (7/8, mot o di thuong)
```

### 19.5 ⚠️ GIỚI HẠN SEVERITY: chỉ 6/8 ô mang rủi ro thật

Đã đo, và phải khai:

```text
o               G4      tol   tol/G4   phep thu
poisson@0.850  1,491   0,149     10%   RUI RO THAT
h2@0.700       1,126   0,113     10%   RUI RO THAT
poisson@0.925  1,121   0,112     10%   RUI RO THAT
poisson@0.960  0,699   0,070     10%   RUI RO THAT
poisson@0.700  0,650   0,065     10%   RUI RO THAT
h2@0.850       0,635   0,063     10%   RUI RO THAT
h2@0.925       0,022   0,020     91%   YEU  <- san tuyet doi chi phoi
h2@0.960       0,000   0,020   vo cuc   YEU  <- moi gia tri trong [0; 0,02] deu qua
```

Sàn tuyệt đối 0,02 **cần thiết** (không có nó thì hai ô gần 0 không kiểm được),
nhưng nó làm hai ô đó gần như **không thể trượt** — đúng bệnh của ứng viên 1, chỉ
ở phạm vi nhỏ hơn. Hệ quả thật: ngưỡng `7/8` nghĩa là **5/6 ô rủi ro thật**.
Không được đọc "7/8" như thể tám ô đều khắt khe.

### 19.6 Dự đoán ĐÃ ĐÓNG BĂNG cho holdout a = 0.5

Sinh **trước** khi đọc một dòng `err_stale` nào của a = 0.5:

```text
poisson@0.850  1,491 (3 duong song)   poisson@0.960  0,699 (2)
h2@0.700       1,126 (2)              poisson@0.700  0,650 (2)
poisson@0.925  1,121 (2)              h2@0.850       0,635 (2)
h2@0.925       0,022 (1)              h2@0.960       0,000 (1)
```

Đây là phép thử **rủi ro thật**: `h2@0.850` ở a=0.9 có tỉ số 1,15, còn G4 dự đoán
ở a=0.5 nó **rơi xuống 0,64**. Đảo chiều như vậy không thể đúng do tình cờ.

### 19.7 Câu hỏi mở (KHÔNG phải điều kiện đạt)

`poisson@0.700` là ô **dị thường** duy nhất trên khám phá: G4 = 1,556 nhưng quan
sát 0,952 (lệch −38,8%). Chưa giải thích được. G4 dự đoán ở a=0.5 nó là 0,650.
Kết quả ở ô này cho biết dị thường **còn tồn tại hay không** — ghi thành **câu hỏi
mở**, không tính vào phán quyết.

### 19.8 Nếu FAIL thì đó vẫn là kết quả tốt

Một FAIL cho biết G4 chỉ khớp được dữ liệu mà nó **đã được chọn trên đó** — tức
lối rẽ ở §19.2 đã sinh ra một mô hình không tổng quát. Đó là thông tin thật, và
là lý do holdout tồn tại.

---

## 20. `d_sla` — KHOÁ trước khi mở (gate 20R2.7)

### 20.1 ★ Đính chính sổ đăng ký: đơn vị đang bị khai SAI

Sổ đăng ký ghi `SLA_VIOL_BY_AGE`: **UNIT = ms**, **SCALE = cost_ms**, *"đi qua hàm
chi phí `delay + w_loss·loss`"*. **Mã nói khác:**

```python
# decision_error_v2.py:388
def _viol(delay, loss, t_delay_ms, t_loss):
    return (delay > t_delay_ms) | (loss > t_loss)        # BOOLEAN
# decision_error_v2.py:567
"d_sla": viol[current, a_twin].mean() - viol[current, a_truth].mean()
```

⇒ `d_sla` là **hiệu hai TỈ LỆ vi phạm**: **không thứ nguyên**, nằm trong `[−1, 1]`,
**không phải ms**. Hàm chi phí chỉ chạm vào **gián tiếp** qua việc chọn `argmin`;
trục SLA chạm vào **trực tiếp** qua hai **ngưỡng** `T_delay`, `T_loss`.

Đây là **NT 64 lần nữa — một tên, hai đại lượng** — nhưng lần này **lời khai trong
sổ đăng ký sai so với MÃ**, chứ không phải hai chỗ trong mã lệch nhau.

**Sửa hợp lệ vì cột `d_sla` CHƯA được đọc, và mã là sự thật.** Giữ nguyên ID, sửa
`UNIT` + `SCALE`, thêm `IDENTITY`. `ARTIFACT_FIELD_LINE: 567` **đúng từ đầu**. Sửa
ở **nguồn sinh** (`tools/20r2_2_predictions.py`) rồi sinh lại — không gõ tay vào
artifact. Chú thích sai trong `ESTIMAND_BY_FIELD` cũng đã sửa. Hash cũ ghi ở §12.1.

### 20.2 Đồng nhất thức, hai cận, và dấu

**Đồng nhất thức (CHÍNH XÁC, suy ra từ định nghĩa).** Tại mọi `t` có
`a_twin = a_truth`, hiệu vi phạm **bằng 0**. Vậy tổng chỉ còn các `t` mà twin sai:

```text
d_sla = (1/T) Σ_t [viol(t, a_twin) − viol(t, a_truth)]
      = (n_sai/T) · (1/n_sai) Σ_{t: twin sai} [viol_twin − viol_truth]
      = err_total · Δ_cond ,   Δ_cond = E[viol_twin − viol_truth | twin SAI]
```

`Δ_cond` là **"giá của MỘT lần sai"**. Đây là thông tin **mới** mà `d_sla` mang
lại, ngoài những gì `err` đã cho biết.

**Hai cận (chính xác).** Vì `viol ∈ {0,1}` nên hiệu `∈ {−1,0,1}`, do đó `|Δ_cond| ≤ 1`:

```text
|d_sla| <= err_total                                  (tu dong nhat thuc)
|d_sla| <= spread = mean_t[max_p viol − min_p viol]    (can tren cau truc)
```

**Dấu.** Trục exogenous đặt `w_loss = T_d/T_l = 50 ms / 1% = 5000`, tức hàm chi
phí được **căn thẳng hàng** với SLA: 1% loss "đắt" đúng bằng 50 ms trễ. Vì vậy
`Δ_cond ≥ 0` gần như chắc chắn: twin chọn sai sẽ không "may mắn" chọn được đường
**ít** vi phạm hơn.

### 20.3 Lớp cấu trúc — ĐO TRƯỚC KHI MỞ (07a, seed 901–903)

```text
DEGENERATE  spread < 0,01     WEAK  0,01 <= spread < 0,05     INFORMATIVE  >= 0,05
```

**Kết quả trên 16 tổ hợp gate (8 ô × 2 giá trị a):**

```text
TRUC EXOGENOUS (T_d = 50 ms, T_l = 1%)      12 DEGENERATE . 1 WEAK . 3 INFORMATIVE
  poisson@0.700  a=0,9/0,5   spread 0,005 / 0,000   KHONG duong nao vi pham
  poisson@0.850  a=0,9/0,5   spread 0,886 / 0,919   VUNG BIEN   <- INFORMATIVE
  h2@0.700       a=0,9       spread 0,123           VUNG BIEN   <- INFORMATIVE
  h2@0.700       a=0,5       spread 0,012           WEAK
  poisson@0.925/0.960 . h2@0.850/0.925/0.960        MOI duong vi pham ~100%

TRUC SELF_CALIBRATED (DEPRECATED)           16/16 INFORMATIVE (spread 0,79-0,97)
```

**Ba điều phải rút ra:**

1. **ĐO ĐƯỢC ≠ MANG THÔNG TIN.** Trên trục exogenous, **13/16** tổ hợp có `d_sla`
   bằng 0 **theo cấu trúc** (12 DEGENERATE + 1 WEAK), bất kể twin sai nhiều hay ít.
   Hai nguyên nhân **khác nhau**: SLA **không bao giờ bị chạm** (poisson@0.700), và
   SLA **không thể đạt được** (từ h2@0.850 trở lên, *mọi* đường vượt 50 ms gần như
   mọi lúc). ⇒ Số gộp 8 ô gần bằng **1/8** giá trị của poisson@0.850, và **hoàn
   toàn không phải "giá của sai"**.

2. **Đây là S14 hiện hình trên `d_sla`.** Trục exogenous **trung thực** nhưng **mù
   ở hầu hết các ô**. Trục self_calibrated **nhìn thấy mọi ô** — nhưng chỉ vì
   ngưỡng của nó được dựng **từ chính phân phối của từng ô**, tức **vòng tròn**.

3. **Hàm ý cho digital twin (THĂM DÒ):** "giá của sai" chỉ tồn tại ở **vùng biên**,
   nơi SLA *đạt được nhưng không được bảo đảm*. Ở **cả hai phía** của vùng đó, độ
   cũ của twin **không ảnh hưởng gì** đến SLA.

### 20.4 Dự đoán — và severity của từng cái

```text
S0  DUNG CU, CHINH XAC   |d_sla| <= err_total o MOI hang, MOI z
    -> severity CAO: vi pham = loi dung cu, vi day la HE QUA DAI SO cua dinh nghia.
S1  o DEGENERATE         |d_sla| < 0,01 o moi tau
    -> ⚠️ severity THAP, phai khai: spread da la CAN TREN va no ~ 0, nen S1 gan
       nhu chac chan dat. No la mot phep kiem NHAT QUAN, khong phai mot phat hien.
S2  o INFORMATIVE        d_sla > 0 o moi tau
    -> severity VUA: co the truot neu Delta_cond < 0, tuc twin sai lai chon duoc
       duong IT vi pham hon. Ly do tin la dung: w_loss = T_d/T_l (§20.2).
```

### 20.5 Báo cáo

Bảng theo **từng ô** kèm `Δ_cond`, **đứng cạnh** số gộp; số gộp 8 ô **bắt buộc**
dán nhãn *"bị chi phối bởi các số 0 THEO CẤU TRÚC — không đọc như giá của sai"*.
Đây là bài học §18.1 áp dụng ngay: bảng theo từng ô là **bắt buộc** từ 20R2.7.

### 20.6 Trục: CHỈ exogenous

H3 ("đo trên cả hai trục") **đã đạt ở mức CẤU TRÚC** với **0 phút CPU** (07a).
**Không** chạy thêm nhánh self_calibrated (~35–40 phút), vì mọi con số trên đó đều
điều kiện theo một trục **vòng tròn**. Khai vào Threats (gate 7-3).

### 20.7 Nếu S0 FAIL

⇒ **lỗi dụng cụ**, **DỪNG** diễn giải. S0 là hệ quả đại số của định nghĩa; nó
không thể sai vì "khoa học", chỉ vì mã.

### 20.8 Nói thẳng: 20R2.7 có rất ít nội dung khẳng định

Kết quả **chính** của gate này là **cấu trúc** (§20.3), và nó có được **trước khi**
mở một cột nào. Phần mở cột chủ yếu để **xác nhận dụng cụ** (S0) và **mô tả**
`Δ_cond` ở ba tổ hợp INFORMATIVE.
