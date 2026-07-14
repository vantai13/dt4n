# Noise Results

Noise tra loi cau hoi: trong dieu kien mang khoe, moi chieu state dao dong nen
bao nhieu? Ket qua dung de lap nguong phan biet dao dong vo hai voi su co that.

## File Quan Trong

- `noise_a2.json`: phep do moi cho state A2 9 chieu.
- `noise_std.json`, `rate_noise_final.json`, `sweep_sync_quick.csv`: artifact
  Phase 5/45D cu, giu de doi chieu.

## Key Can Doc

- `state_dims.<dim>.median`: tam nhieu nen cua mot chieu.
- `state_dims.<dim>.sigma_robust`: do dao dong ben vung, tinh tu MAD.
- `state_dims.<dim>.three_sigma`: nguong 3-sigma.
- `degenerate_dimensions`: chieu khong dao dong trong dieu kien do.
- `condition`: dieu kien luc do; khong doc so neu dieu kien sai.

## Lenh Sinh A2

```bash
sudo -E env PYTHONPATH="$PWD" DT4N_FAST_PUSH=1 "$CONDA_PY" rl/a2/measure_noise_a2.py \
  --samples 300 \
  --warmup 3 \
  --interval 1.0 \
  --condition a2_healthy_stable_demand \
  --out results/noise/noise_a2.json
```
