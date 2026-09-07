# L2 — Phán quyết đóng phase

Ngày: 2026-09-07 UTC. Trạng thái: **`AUDIT_NO_MEASUREMENT`** toàn phase.
L2 không sinh một phép đo mạng nào. Nó phát hiện một bất khả thi cơ chế,
và phát hiện rằng lesson trung tâm của nó đã được đo ở một phase trước.

## 1. Ba câu hỏi nghiên cứu

| RQ | Câu hỏi | Phán quyết | Bằng chứng |
|---|---|---|---|
| RQ-L2a | Mô hình delay Phase L có chuyển giao được không? | **CÓ cho delay** ở poisson mọi kênh và h2 kênh delay; **KHÔNG** cho h2 kênh loss | `A′−A`, 48 điểm 8 seed, Amd 14 §2 |
| RQ-L2b | Delay đường có bằng tổng delay link? | **GẦN BẰNG.** `e_add` = +0.75 ms / 25.68 ms = 2.9 % (poisson), dấu DƯƠNG 4/4 | `01-additivity-already-measured.md` §2 |
| RQ-L2c | `c_a` nên sống ở tầng nào? | **KHÔNG tầng nào.** `c_a` không đủ để xác định delay | `00-*.md` §1.2 + `L2-L1` |

## 2. Phân rã ba phần (điểm vận hành ρ̄ = 0.925)

| | poisson | h2 |
|---|---:|---:|
| `e_add`  (cộng tính) | +0.7464 ms · **2.91 %** | +0.4492 ms · **1.45 %** |
| `e_model` (mô hình)  | −1.0071 ms · **3.92 %** | +5.1386 ms · **16.55 %** |
| `e_total` (twin sai) | −0.2607 ms · **1.02 %** ✅ | +5.5878 ms · **17.99 %** ⛔ |

★ **Cộng tính KHÔNG phải nguồn sai số chính. Mô hình mới là, và chỉ với `h2`.**
⟹ KHÔNG mở nhánh hiệu chỉnh `η(n_hop, ρ)`. Cascade đã đủ tốt.
⟹ Gate `L2.4-5` FIRE cho `h2` ⟹ giới hạn `L2-L6`, không phải hiệu chỉnh cascade.

⚠️ **Phần dư tương tác ≡ 0 do ĐẠI SỐ, không do vật lý.** Với `e_model` định nghĩa
trên chính nhánh B, `ΣB` triệt tiêu. Gate `L2.4-4` như viết là tautology.
Phiên bản có nghĩa: định nghĩa `e_model` trên nhánh `A′`. Chuyển thành nợ.

## 3. Đóng góp của L2

```text
① S37   — cưỡng chế tốc độ và phương sai đến loại trừ nhau trên một đường
② L2-L1 — nguồn backlogged sau bộ giới hạn tốc độ phát ra CV(gap) = 0 chính xác,
          với MỌI burst; chỉ hai lối thoát (nguồn có nhàn rỗi, hoặc ρ(t) > 1)
③ L2-L1b— CV(gap) > 0 KHÔNG đủ: gói kích thước ngẫu nhiên cho CV = 0.913 mà
          delay = 0, vì gap tỉ lệ thuận với thời gian phục vụ.
          ⟹ giải thích CƠ CHẾ cho phản ví dụ Amendment 7 của Phase L
④ e_add — cận sai số cộng tính đã đo, có dấu, tại điểm vận hành
⑤ NT 63/64/65 — kỷ luật phạm vi và đặt tên estimand
```

## 4. Sổ giới hạn

`L2-L1` · `L2-L1b` · `L2-L2` (một điểm ρ) · `L2-L3` (loss không cộng tính)
· `L2-L4` (nhãn artifact) · `L2-L5` (thiếu đối chứng n_hop=1)
· `L2-L6` (twin dự đoán thừa `h2` 16.6 %)

## 5. Nợ chuyển ra

```text
D1  coupling bảo toàn byte — KHÔNG đóng được: ρ cố định mỗi run, không có
    chuỗi thời gian. Chuyển tiếp nguyên trạng.
D9  MỚI: phần dư tương tác có nghĩa cần e_model tính trên nhánh A′.
D10 MỚI: pipeline triển khai = Phase L (Mininet + flow_engine).
    Phase G′ hạ xuống nghiên cứu đo độc lập về giới hạn pacing userspace.
    Câu Threats-to-Validity: xem §6.
```

## 6. Câu Threats-to-Validity viết sẵn

> The load-controllability study and the delay-model study were run on two
> testbeds with different pacing mechanisms. We do not claim joint
> certification: the former bounds userspace pacing fidelity, while all
> delay-model and closed-loop results are calibrated and deployed on the same
> flow-level pipeline, satisfying calibration–deployment matching.

## 7. Điều kiện mở lại

```text
· Nếu Phase 24 cần một CLAIM đa họ lưu lượng closed-loop ⟹ mở lại L2.2
· Nếu headline chuyển khỏi poisson@0.925 ⟹ e_total phải đo lại ở điểm mới
· Nếu twin bắt đầu dùng h2 cho quyết định ⟹ L2-L6 thành chặn, không phải giới hạn
```
