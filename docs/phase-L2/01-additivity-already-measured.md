# L2.1 — Cộng tính theo đường ĐÃ ĐƯỢC ĐO Ở PHASE 20R.6

Ngày: 2026-09-07 UTC.
Trạng thái: **`AUDIT_NO_MEASUREMENT`**. Không chạy root/netns/tc/Mininet.
Mọi số đọc lại từ artifact đã tồn tại, tái lập bằng
`tools/l2_1_additivity_recheck.py`, khoá bởi `test/test_l2_1_additivity.py`.

---

## 0. Phát hiện

Kế hoạch L2 (`PHASE_L2.md` §S36) phát biểu:

> "`twin/link_model_v2.py` dòng 5: *additive across path links*.
> Chưa ai kiểm delay của một đường 3 chặng có bằng tổng ba delay link không."

**Mệnh đề đó SAI.** Đại lượng này đã được đo ở Phase 20R.6, dưới tên
`G6-CASCADE`, ký trong `docs/phase-20R/00o-amendment-14.md §42`
(2026-08-09), với artifact `results/*/phase-20R/residual_cascade.json`.

Nguyên nhân bỏ sót: **một đại lượng, ba tên gọi.**

| Tên | Xuất hiện ở |
|---|---|
| `additive across path links` | `twin/link_model_v2.py:6` (docstring) |
| `G6-CASCADE` | prereg + bảng gate Phase 20R |
| `cascade residual` / `r_path` | `measurements/cascade_residual.py`, artifact |

⟹ **`NT 64`** (mới): trước khi xây một phép đo, grep repo bằng ÍT NHẤT
ba cách gọi: tên khái niệm · tên gate · công thức.

## 1. Estimand

```text
r_path  =  C  −  Σ_i B_i
```

- `C`   — nhánh C: MỘT probe đi hết đường 3 chặng
- `B_i` — nhánh B: probe đi qua link i, **cả ba link đều đang tải**
- Ghép cặp theo `(mode, seed)`: cùng topology, cùng session, cùng background

Ký hiệu của `PHASE_L2.md` ngược dấu:

```text
e_add  =  Σ_i delay_link_ĐO  −  delay_đường_ĐO  =  ΣB − C  =  − r_path
```

## 2. Kết quả (tái lập, khớp Amd 14 §42 tới 5e-7 ms)

`n_pairs = 8` seed · `ρ̄ = 0.925` · TandemTopo `L1=(8,18) L2=(6,13) L3=(4,10)`

| mode | ΣB | C | **e_add** | CI90 | |e_add|/C |
|---|---:|---:|---:|---|---:|
| poisson | 26.4262 | 25.6798 | **+0.7464** | [+0.625, +0.868] | **2.91 %** |
| h2 | 31.5026 | 31.0533 | **+0.4492** | [+0.388, +0.511] | **1.45 %** |

**Dấu DƯƠNG 4/4 residual, không CI90 nào chứa 0.**

## 3. Đối chiếu bảng dự đoán ký trước (`PHASE_L2.md` PART IV)

| Dự đoán | Đo được | |
|---|---|---|
| `L2.4` dấu `e_add` **DƯƠNG** (Σ link ≥ đường) | **DƯƠNG**, 4/4, mọi seed | ✅ **TRÚNG** |
| `L2.4-2` dấu khớp Burke ở ≥3/4 mức | 4/4 | ✅ |
| `L2.4-5` `|e_total|/delay > 15%` ⟹ mở nhánh `η` | poisson 1.0 % | ✅ **không cần η** |

Cơ chế (Amd 14 §42): *"đo trên đường end-to-end nhỏ hơn tổng ba phép đo
link riêng vì burst đã được trả / làm phẳng ở node trước"* — đây chính là
lập luận làm-mịn kiểu Burke của `PHASE_L2.md` §L2.4, phát biểu chặt hơn
cho hàng đợi hữu hạn và dịch vụ gần tất định.

## 4. Giới hạn

```text
L2-L2  MỘT ĐIỂM ρ DUY NHẤT
  Toàn bộ cascade residual đo ở ρ̄ = 0.925, hai họ (poisson, h2).
  KHÔNG có lưới ρ ∈ {0.60, 0.75, 0.85, 0.92}.
  ⟹ KHÔNG được viết "e_add là hàm của ρ".
  ⟹ ĐƯỢC viết "tại điểm vận hành poisson@0.925, |e_add|/delay = 2.9 %".
  Biện minh: 0.925 chính là điểm vận hành đã bàn giao cho 21R
  (docs/phase-20R/99-gate-decision.md §8).

L2-L3  KÊNH LOSS KHÔNG CỘNG TÍNH
  r_path(loss) = −0.00952 (poisson) trên nền 0.0598  ⟹  −15.9 %.
  Đây KHÔNG bất ngờ: loss đường = 1 − Π(1−l_i), vốn dưới-cộng-tính.
  Thêm: clip_ratio = 43.2 % ⟹ biên âm là CẬN DƯỚI, không phải điểm ước lượng.
  Và: path p95/p99 KHÔNG cộng tính (99-gate-decision.md §7, đã ghi).

L2-L4  NHÃN ARTIFACT
  residual_cascade.json nằm ở tầng SUPERSEDED do đợt tổ chức lại 4 tầng
  (Lesson 23.17 / amendment 23-44), KHÔNG phải vì kết quả bị bác bỏ:
  99-gate-decision.md §8 vẫn bàn giao r_path ≈ 0.00886 cho 21R.
  Amd 14 §42 ghi `git_dirty = true` trên các artifact phân tích.
  ⟹ Trước khi trích vào bản nộp: dọn provenance, tạo commit sạch.

L2-L5  ĐỐI CHỨNG DƯƠNG n_hop = 1 KHÔNG TỒN TẠI Ở DẠNG NÀY
  Gate L2.4-1 đòi |e_add| ≈ 0 tại n_hop = 1.
  Thay thế: Amd 14 §1.3 lập luận thiết kế paired (C và B cùng
  topology/session/seed/background) triệt tiêu common-mode trong hiệu.
  QUYẾT ĐỊNH: chấp nhận lập luận đó, KHÔNG chạy lại. Ghi thành giới hạn.
```

## 5. Nợ KHÔNG đóng được

```text
D1  Coupling do bảo toàn byte xuyên multi-hop
    Thiết kế 20R.6 đặt ρ CỐ ĐỊNH mỗi link (0.8575 / 0.9775 / 0.9875),
    không có chuỗi thời gian ⟹ không có tương quan để đo.
    ⟹ Gate L2.4-6 KHÔNG áp dụng được. D1 chuyển tiếp nguyên trạng.
```
