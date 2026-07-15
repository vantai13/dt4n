# Fidelity Results

Fidelity tra loi cau hoi: gia tri twin/Ditto lech voi gia tri that bao nhieu,
va lech do chu yeu den tu stale data hay bug dong bo?

## File Quan Trong

- `fidelity_a2_srv1.json`: file se duoc tao boi script A2 moi.
- `fidelity_s2-s3.json`, `equivalence.json`, `scenario_visibility.json`,
  `fetch_time.json`, `smoke_test.json`, `phase_vs_ramp_analysis.json`: artifact
  Phase 5 cu, giu de doi chieu va viet bao cao.

## Key Can Doc Trong A2

- `analysis.abs_error_mean_mbps`: sai so tuyet doi trung binh.
- `analysis.abs_error_p95_mbps`: sai so p95.
- `analysis.fidelity_error_intercept_mbps`: sai-vi-loi khi AoI ve 0.
- `analysis.staleness_error_slope_mbps_per_s`: sai-vi-cu tren moi giay AoI.
- `analysis.r2_aoi_explains_abs_error`: AoI giai thich duoc bao nhieu error.
- `analysis.dominant_source`: `twin_good`, `staleness`, `fidelity_bug`,
  hoac `mixed`.

## Lenh Sinh A2

```bash
sudo -E env PYTHONPATH="$PWD" DT4N_FAST_PUSH=1 "$CONDA_PY" rl/a2/measure_fidelity_a2.py \
  --host srv1 \
  --samples 200 \
  --out results/fidelity/fidelity_a2_srv1.json
```
