# Delta Results

Delta tra loi cau hoi: sau khi action lam doi bandwidth/topology, can cho bao
lau truoc khi observation phan anh he qua that?

## File Quan Trong

- `delta_a2.json`: phep do moi cho A2. Doc `delta_s_recommended` de cap nhat
  `--delta-s` hoac cfg cua `TwinEnvA2`.
- `delta_final.json`, `delta_final_gate.json`, `delta_*.json/csv`: artifact
  Phase 5 cu cho he network-centric, giu de doi chieu.
- `delta_variant_summary.*`: so sanh cac bien the delta cu.

## Key Can Doc

- `delta_mean_s`: thoi gian on dinh trung binh.
- `delta_p95_s`: 95% lan do on dinh trong muc nay.
- `margin_s`: bien an toan cong them.
- `delta_s_recommended`: so nen dung cho wait/step.
- `failed_repeats`: neu lon hon 0, xem mau loi truoc khi tin p95.

## Lenh Sinh A2

```bash
sudo -E env PYTHONPATH="$PWD" DT4N_FAST_PUSH=1 "$CONDA_PY" rl/a2/measure_delta_a2.py \
  --repeats 20 \
  --out results/delta/delta_a2.json
```
