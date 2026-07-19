# Phase 10.1 — Pre-registration (chốt TRƯỚC sweep 10.2)

**Ngày ký:** 2026-07-19
**Người ký:** <tên bạn>
**Frozen:** frozen_policies/v1/ (freeze tag 2ef208e, link_model 3a3c7e5)
**Bằng chứng không HARK:** commit này đứng TRƯỚC mọi commit sweep 10.2.

## 1. Trục đo (cấu trúc 2 tầng)

- TRỤC CHÍNH (nguyên nhân, vô đơn vị): `wrong_excess`
    = blind_wrong_rate − clair_wrong_rate
    "AoI làm tăng tỷ lệ quyết định sai bao nhiêu"
- TRỤC HỆ QUẢ (tác động, có đơn vị): `cost_of_blindness`
    = clair_return − blind_return
- BỎ voi_headroom khỏi trục chính (phụ thuộc OSPF cứng nhắc, bị cancellation;
  giữ như quan sát phụ: "routing bền bất ngờ so với OSPF").

## 2. Mô hình & breaking point (TIÊN NGHIỆM)

Giả thuyết: wrong_excess(AoI) = A·(1 − e^(−AoI/τ))   [bão hòa mũ]
Breaking point ≡ τ (knee tại 63% trần) — định nghĩa GIẢI TÍCH từ fit,
KHÔNG dùng ngưỡng tùy ý.
Điều kiện chấp nhận fit: R² ≥ 0.95 (nếu < 0.95 → đổi dạng hàm, ghi lại).

## 3. Dải z & quy đổi

STEP_DURATION_S=0.5 → aoi_s = z·0.5
Dải z: [0,1,2,3,5,8,12,20]  → aoi [0..10]s
Load sweep: LOAD_CFG_SWEEP (drift_sigma=0.15, fix bug drift-override)
VÙNG ĐO: [0,10]s (định vị τ)
VÙNG DIỄN GIẢI: [0.05,0.55]s (Ditto thật) — kết luận về twin thực tế

## 4. Gate GO/NO-GO Phase 11

std_agent = 0.0450  (5 seed frozen v1, z=0, LOAD_CFG_SWEEP)
SNR = cost_of_blindness_max / std_agent
Cây quyết định: SNR≥3 GO / 2-3 GO+tăng seed / <2 NO-GO.

## 5. Kết quả pilot (điền từ fit_knee.py, TRƯỚC sweep đầy đủ)

R² = 0.9977   A = 0.2105   τ = 1.823 s
breaking_point = τ = 1.82 s   (knee 90% = 4.20 s)
cost_of_blindness_max = 0.336 → SNR = 0.336/0.045 = 7.5 → GO ✅
wrong_excess @ 0.55s (trần Ditto) = 0.0548 = 26% trần
→ Twin thật NẰM TRƯỚC điểm gãy (an toàn tương đối, lỗi tồn dư 5.5%)