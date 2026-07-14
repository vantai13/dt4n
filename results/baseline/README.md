# Baseline Results

Thu muc nay chua diagnostic va baseline khong phai training chinh. Chuc nang
chinh la lam moc doi chieu: reset co sach khong, oracle co thuc thi duoc khong,
rule-based co hanh vi hop ly khong.

## File Hien Co

- `diag_hard_reset.json`: chan doan hard reset.
- `diag_soft_leak.json`: chan doan leak khi soft reset.
- `oracle_executability.json`: oracle/action co thuc thi duoc trong env khong.
- `rulebased_diag.json`: chan doan policy rule-based.

## Cach Doc

- Tim cac field `ok`, `dirty`, `leaked`, `error`, `passed`, `summary` neu co.
- Neu baseline do reset bi dirty/leak, dung pipeline train/eval lai truoc khi
  tin ket qua agent.
- Baseline cu co the dung de viet phan "system sanity" trong bao cao, nhung
  khong thay the measurement A2 moi trong `results/delta`, `noise`, `aoi`,
  va `fidelity`.
