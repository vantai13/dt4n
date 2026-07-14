# Gate 1 — Ổn định hệ thống trước khi train

## Triệu chứng ban đầu
Train log có 18 episode liên tiếp return = -16.5 (throughput=0, loss=1).
Reward forensics: -1.10/step × 15 = -16.5 → mạng "chết" theo quan sát.

## Quá trình chẩn đoán (đo trước khi sửa)
1. Nghi hard_reset → diag_hard_reset.py (10 lần) → 10/10 ổn định → LOẠI.
2. Nghi _link_up toggle leak → diag_soft_reset_leak.py (A/B) →
   base_thr KHÔNG tụt dần (bimodal, không xu hướng) → RACE, không phải leak.
3. Nghi net_lock → bench_sync_cycle.py → adapt/diff <1ms → LOẠI.
4. Đo collect → bimodal 54ms vs 1460ms → ping timeout trên đường bão hòa.

## Nguyên nhân gốc
collect_latency dùng `ping -c 3 -W 1` trên path h1→srv1 đang bão hòa TCP.
Gói ping timeout → mỗi ping ~1460ms → sync cycle quá tải → pipeline quan sát
chập chờn → steady-state timeout → base_thr=0 → (18 ep chết / 2 health-retry).

## Sửa
- ping: `-c 3 -W 1` → `-c 1 -W 0.3` (cycle chậm 1460ms → 357ms, vẫn < period).
- ping_every: 5 → 20 (path latency đổi chậm, không cần ping dày).
- Thêm health gate trước inject (fail-fast) + _link_up reset (bug phụ).

## Bằng chứng đóng gate
| | collect p95 | health-retry / 30 ep | base_thr |
|---|---|---|---|
| Trước | 1464ms | 2 | thỉnh thoảng 0.000 |
| Sau | 130ms | 0 | ổn định ~1.08 |

## Giới hạn ghi nhận (future work)
Ping chủ động trong vòng nóng là điểm yếu kiến trúc — nguồn staleness không
kiểm soát. Tương lai: tách ping sang thread riêng, hoặc suy latency gián tiếp.