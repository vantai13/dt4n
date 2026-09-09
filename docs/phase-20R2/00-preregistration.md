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
Nguoi ky        : ______________________________
Ngay            : ______________________________
Commit sha      : ______________________________   (sha CUA BAN prereg duoc ky)
Xac nhan        : [ ] toi da doc §0 va chap nhan muc ⚠️ con lai (danh sach 5 RQ)
                  [ ] toi ky ngan sach 29,4 phut hai nhanh (KHONG phai 5,89 h)
                  [ ] toi ky luoi 800 o (KHONG phai 960)
                  [ ] toi KHONG ke thua ket luan kha thi cua T2 (20R2-L4)

Sau khi dien:
    git add docs/phase-20R2/00-preregistration.md
    git commit -m "20R2 prereg: ky gate 0-3"
    git tag -a phase-20R2-prereg-signed -m "20R2 prereg signed"
    git push origin main && git push origin phase-20R2-prereg-signed
    git ls-remote --tags origin | grep prereg-signed   # BANG CHUNG
```
