# PHASE 21.5 - Payload Sensitivity Rule

Ngay: 2026-07-28
Trang thai: quy tac quyet dinh duoc ghi truoc khi chay sensitivity payload.

Muc tieu: kiem tra xem sai khac payload giua calibration 1470 B va thi nghiem
1400 B co lam doi ket luan Gate 21 hay khong.

## Quy Tac Quyet Dinh

Chay lai toan bo duong ong Phase 21 tren nhanh rieng voi hang so sua:

```text
OVERHEAD_FACTOR = 1.0829
MTU_BYTES = 1442
CLIFF_RHO_OFFERED = 0.92341
```

Giu nguyen ket qua goc lam chinh, bao cao ban sua lam do nhay, neu ca ba dieu
kien sau deu dat:

```text
(a) H_C moi van PASS ca ba dieu kien
(b) CI95 cua hieu ablation tai eps=0 van loai tru 0
(c) coverage marginal van trong 0.90 +/- 0.02
```

Neu bat ky dieu kien nao that bai:

```text
ban SUA tro thanh CHINH
su khac biet duoc bao cao noi bat trong gate-decision
```

Cam ket nay duoc ghi truoc khi chay. Khong sua sau khi thay ket qua.

## Lenh Chay Khi Thuc Hien Sensitivity

```bash
cd ~/dt4n
git checkout -b sensitivity/payload-1400

# Sua 3 hang so trong twin/link_model.py:
#   OVERHEAD_FACTOR = 1.0829
#   MTU_BYTES = 1442
#   CLIFF_RHO_OFFERED = 0.92341

python -m cert.build_calib_set \
  --traces results/phase-20/rho_offered_long.csv \
           results/phase-20/rho_offered_long_s1.csv \
           results/phase-20/rho_offered_long_s2.csv \
           results/phase-20/rho_offered_long_s3.csv \
           results/phase-20/rho_offered_long_s4.csv \
  --out /tmp/calib_sens.parquet \
  --report-json results/phase-21/sens_payload_calib.json

python -m cert.conformal_age \
  --calib /tmp/calib_sens.parquet \
  --score s_vs_a1 \
  --cells z_bin \
  --out-json results/phase-21/sens_payload_conformal.json

python -m cert.usefulness \
  --calib /tmp/calib_sens.parquet \
  --score s_vs_a1 \
  --out-json results/phase-21/sens_payload_usefulness.json

git checkout main
```

Ghi chu: khong merge nhanh sensitivity. Chi commit cac JSON sensitivity vao main
sau khi da doc ket qua theo quy tac tren.
