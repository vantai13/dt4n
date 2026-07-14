# AoI Results

AoI, Age of Information, tra loi cau hoi: du lieu trong Ditto/twin cu bao nhieu
giay so voi thoi diem nguon phat sinh?

## File Quan Trong

- `aoi_a2_host_srv1.json`: baseline AoI moi cho Thing A2 `host-srv1`.

## Key Can Doc

- `summary.aoi_mean_s`: tuoi thong tin trung binh.
- `summary.aoi_p95_s`: tuoi thong tin phan vi 95.
- `summary.aoi_min_s`: uoc luong delay nen `d`.
- `summary.expected_d_plus_T_half_s`: ky vong ly thuyet `d + T/2`.
- `summary.ratio_measured_over_expected`: gan 1 la lanh; qua lon thi can dieu tra.
- `summary.thing_is_quiet`: neu true, Thing it doi; do lai khi co traffic.
- `summary.diagnosis`: ket luan nhanh cua script.

## Lenh Sinh A2

```bash
sudo -E env PYTHONPATH="$PWD" DT4N_FAST_PUSH=1 "$CONDA_PY" rl/a2/measure_aoi_a2.py \
  --start-runner \
  --host srv1 \
  --samples 100 \
  --out results/aoi/aoi_a2_host_srv1.json
```
