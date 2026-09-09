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
| Danh sách 5 RQ (a–e) | ⚠️ chép từ lesson, **không kiểm được** |
| Lưới **960 ô** | ⚠️ chép từ lesson, **không kiểm được** |
| Định nghĩa "một ô" | ❌ **chưa xác định** — xem mục 5 |

Ba dòng ⚠️/❌ phải được điền từ `PHASE_20R2.md` **trước khi ký**. Ký mà để
nguyên là lặp lại đúng lỗi mà phase này tồn tại để chống: nhận một con số
không có nguồn kiểm được.

---

## 1. RQ và estimand

```text
RQ-20R2a  err(z | che do) theo tuoi z
RQ-20R2b  d_sla(z) -- gia cua sai
RQ-20R2c  err theo tau tren mien kha thi
RQ-20R2d  err co khop Sheppard khong
RQ-20R2e  ★ ket qua dieu kien theo TRUC NAO
```

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

### A1 — Mặc định im lặng của `axis`: **2 chỗ**, đã xác nhận bằng AST

```text
cert/tau_sweep.py:159             V3._valid_rows(int(n), float(dt))
                                  -> DUONG CHAY CHINH
cert/build_calib_set_v3.py:689    _valid_rows(n, DT)
                                  -> ham chan doan staleness_path_diagnostic
```

Cả hai rơi vào mặc định `axis: str = AXIS_LEGACY`
(`cert/build_calib_set_v3.py:276`) — tức trục **DEPRECATED**.

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
2. `Z_EXTRAP = (1.0, 2.0)` **không phải ngoại suy trên trục thực nghiệm**
   (nằm dưới max đo được 1.5689 s); chỉ `4.0` là ngoại suy trên cả hai miền.
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

| run_log | lệnh | n | giây/lệnh (min–max, mean) | 960 ô |
|---|---|---:|---|---:|
| `sweep_r2` | `decision_error_v2 --run-fixed`, **1 τ × 1 seed** | 166 | 9.25 – 15.30, **mean 11.05** | **2.95 h** |
| `sweep_r3` | `cert.tau_sweep --taus 0.5..28`, **8 τ × 5 seed** | 18 | 37.77 – 41.73, **mean 39.87** | **10.63 h** |

> **Đính chính lesson.** Lesson ghi *"11.6–15.0 s/lệnh"*. Khoảng thật của
> `sweep_r2` là **9.25–15.30 s** (mean 11.05); `11.62` là **bản ghi đầu tiên**
> của file, không phải cận dưới. Kết luận ~3.5 h/nhánh vẫn **an toàn vì bảo
> thủ** (thật là 2.95 h), nhưng con số trích dẫn thì sai. [W4 — hằng số phán
> quyết: một nguồn, IMPORT, không chép]

**Điều kiện để kết luận "không cần fractional design" đứng vững:**

```text
NEU  mot "o" = MOT lenh decision_error_v2 --run-fixed (1 tau, 1 seed)
     -> 960 o = 2.95 h/nhanh; hai nhanh = 5.89 h  < 8 h    KHONG can E4  ✅

NEU  mot "o" = mot lenh cert.tau_sweep (8 tau x 5 seed)
     -> 960 o = 10.63 h/nhanh; hai nhanh = 21.3 h  > 8 h   CAN E4       ❌
```

⟹ **`PHASE_20R2.md` phải định nghĩa "một ô" trước khi ký mục này.** Không có
tài liệu đó trong repo nên **không kết luận được**. Ghi ❌ ở mục 0, không ghi
"không cần fractional design" như một sự thật.

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

20R2-L2 ★ MOI: don vi "mot o" chua duoc dinh nghia -> ngan sach CPU chua
        ket luan duoc (muc 5.2). Khong ghi "khong can fractional design"
        cho den khi PHASE_20R2.md xac dinh don vi o.
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
