#!/usr/bin/env python3
"""Phase 10.1 — Fit hàm bão hòa wrong_excess(AoI), kiểm R², tìm knee.

Trục chính: wrong_excess (vô đơn vị). Fit A*(1-exp(-AoI/tau)).
knee = tau (điểm gãy, 63% trần). Báo cáo cả 2.3*tau (90% trần).
"""
import numpy as np
from scipy.optimize import curve_fit
from rl.routing_2path.metrics_r import evaluate_z
from rl.routing_2path.topology_r import LOAD_CFG_SWEEP


def saturating(aoi, A, tau):
    """Hàm bão hòa mũ: A*(1 - e^(-AoI/tau))."""
    return A * (1.0 - np.exp(-aoi / tau))


# --- 1. Thu thập điểm dữ liệu (dày hơn để fit tốt) ---
Z_VALUES = [0, 1, 2, 3, 5, 8, 12, 20]
SEEDS = range(300)               # nhiều seed → điểm ít nhiễu → fit sạch

aoi, we, cb = [], [], []
for z in Z_VALUES:
    r = evaluate_z(z, seeds=SEEDS, load_cfg=LOAD_CFG_SWEEP)
    aoi.append(r['aoi_mean_s'])
    we.append(r['wrong_excess'])
    cb.append(r['cost_of_blindness'])
aoi = np.array(aoi); we = np.array(we); cb = np.array(cb)

print("Điểm dữ liệu:")
for a, w in zip(aoi, we):
    print(f"  AoI={a:5.2f}s  wrong_excess={w:.4f}")

# --- 2. Fit hàm bão hòa ---
# p0 = phỏng đoán ban đầu: A~trần quan sát, tau~1s
popt, _ = curve_fit(saturating, aoi, we, p0=[0.21, 1.0], maxfev=10000)
A_fit, tau_fit = popt

# --- 3. Đo R² (độ khớp) ---
we_pred = saturating(aoi, *popt)
ss_res = np.sum((we - we_pred) ** 2)          # sai số còn lại
ss_tot = np.sum((we - we.mean()) ** 2)        # tổng biến thiên
r2 = 1 - ss_res / ss_tot

print(f"\n=== KẾT QUẢ FIT ===")
print(f"A   (trần bão hòa)      = {A_fit:.4f}")
print(f"tau (thời gian đặc trưng)= {tau_fit:.4f} s")
print(f"R²  (độ khớp)           = {r2:.4f}")

# --- 4. Đánh giá fit ---
if r2 >= 0.95:
    print("✅ R²≥0.95 → hàm bão hòa khớp TỐT, dùng knee=tau được")
elif r2 >= 0.90:
    print("⚠️  R²∈[0.90,0.95] → khớp tạm, cân nhắc dạng hàm khác")
else:
    print("❌ R²<0.90 → dạng bão hòa mũ SAI, đừng dùng, báo tôi")

# --- 5. Knee ---
knee_63 = tau_fit                 # 63% trần = điểm gãy
knee_90 = tau_fit * np.log(10)    # 90% trần
print(f"\n=== BREAKING POINT (knee) ===")
print(f"knee (63% trần) = tau      = {knee_63:.3f} s  ← BREAKING POINT chính")
print(f"knee (90% trần) = 2.30*tau = {knee_90:.3f} s  (gần bão hòa hoàn toàn)")

# --- 6. Đối chiếu vùng Ditto thật ---
print(f"\n=== ĐỐI CHIẾU DITTO (0.05–0.55s) ===")
we_at_055 = saturating(0.55, *popt)
print(f"wrong_excess tại AoI=0.55s (trần Ditto) = {we_at_055:.4f}")
print(f"= {100*we_at_055/A_fit:.0f}% của trần bão hòa")
if knee_63 > 0.55:
    print(f"→ Breaking point ({knee_63:.2f}s) NGOÀI vùng Ditto (0.55s):")
    print(f"  twin thật của bạn nằm TRƯỚC điểm gãy → vùng an toàn tương đối")
else:
    print(f"→ Breaking point ({knee_63:.2f}s) TRONG vùng Ditto → twin thật đã qua điểm gãy!")