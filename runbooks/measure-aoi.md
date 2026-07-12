# Runbook đo AoI và kiểm pipeline freshness

Mục tiêu: đo `Age of Information` của một Thing trong Ditto và đối chiếu với
công thức lý thuyết:

```text
AoI_mean ~= d + T/2
```

Trong đó:

- `T`: chu kỳ polling của collector, ví dụ `1.0s`.
- `d`: delay cố định của pipeline, ước bằng `AoI min`.
- `AoI`: `time.time() - features.meta.properties.tSource`.

## Điều kiện trước khi đo

`measure_aoi.py` chỉ đọc Ditto. Nó không tự bật Mininet, không tự bật collector,
không tự đẩy `tSource`.

Vì vậy phải có testbed sống:

- Ditto đang chạy.
- Ryu/controller đang chạy nếu topology cần.
- Mininet + sync agent đang chạy bằng `mininet.run_sync`.

Nếu không có testbed sống, bạn sẽ thấy `tSource` đứng yên và AoI tăng lên rất
lớn, ví dụ vài nghìn giây. Đó là dữ liệu cũ trong Ditto, không phải đo hợp lệ.

## Terminal 1: bật Mininet + sync agent

Chạy và giữ terminal này sống, không gõ `exit` trong Mininet CLI:

```bash
PYBIN=/home/vantai/miniconda3/envs/sdn_rl/bin/python
sudo env PYTHONPATH="$PWD" "$PYBIN" -m mininet.run_sync \
  --period 1.0 --server-bg-rate 2.0
```

Đợi tới khi thấy CLI Mininet sẵn sàng.

## Terminal 2: Bước 0 - kiểm `tSource` có lên Ditto không

```bash
PYBIN=/home/vantai/miniconda3/envs/sdn_rl/bin/python
sudo env PYTHONPATH="$PWD" "$PYBIN" measurements/measure_aoi.py \
  --thing org.dt4n:link-s2-s3 --samples 10 --interval 0.5 --polling-period 1.0 \
  --out docs/phase-5/artifacts/aoi_step0_link_s2_s3.json
```

Đúng khi:

- Có cột `AoI_s` với số dương nhỏ, thường khoảng `0.1s` đến `2.5s`.
- `tSource` thay đổi theo chu kỳ khoảng `1s`.
- Không có dòng `missing meta.tSource`.
- AoI không âm.

Sai khi:

- `tSource` đứng yên qua nhiều dòng.
- `AoI_s` tăng đều theo `--interval`.
- AoI rất lớn, ví dụ hàng trăm hoặc hàng nghìn giây.

Nếu sai kiểu này, nghĩa là đang đọc dữ liệu cũ trong Ditto hoặc sync agent không
đang đẩy trạng thái mới.

## Terminal 2: Bước 1 - đo đủ mẫu và đối chiếu `d + T/2`

```bash
sudo env PYTHONPATH="$PWD" "$PYBIN" measurements/measure_aoi.py \
  --thing org.dt4n:link-s2-s3 --samples 100 --interval 0.3 --polling-period 1.0 \
  --out docs/phase-5/artifacts/aoi_link_s2_s3.json
```

Output cuối sẽ có khối:

```text
== DOI CHIEU d + T/2 ==
  T (polling)      = 1.00 s
  d (uoc = AoI min)= ...
  AoI mean (do)    = ...
  AoI p95 (do)     = ...
  Ky vong d + T/2  = ...
  Ty le do/ky vong = ...
```

Đọc kết quả:

- `Ty le do/ky vong` khoảng `0.8` đến `1.5`: pipeline lành.
- `Ty le do/ky vong > 1.5`: pipeline tụt hậu, AoI đang phình lên.
- `d (uoc = AoI min)`: delay thấp nhất quan sát được, gần delay cố định của pipeline.
- `AoI p95`: đuôi trễ; nếu p95 cao hơn mean nhiều thì pipeline có jitter hoặc nghẽn.

Kết quả JSON sẽ nằm ở:

```text
docs/phase-5/artifacts/aoi_link_s2_s3.json
```

File này chứa:

- `summary`: mean, p95, min, max, số mẫu hợp lệ.
- `theory_check`: `T`, `d_est`, `expected_mean`, tỉ lệ đo/kỳ vọng, verdict.
- `records`: từng mẫu raw gồm `t_source`, `aoi_s`, lỗi nếu có.

## Ghi chú nhanh

Nếu `polling-period` của `mininet.run_sync` không phải `1.0`, phải truyền đúng
giá trị đó vào `--polling-period`. Ví dụ chạy `--period 0.5` thì đo bằng:

```bash
sudo env PYTHONPATH="$PWD" "$PYBIN" measurements/measure_aoi.py \
  --thing org.dt4n:link-s2-s3 --samples 100 --interval 0.3 --polling-period 0.5 \
  --out docs/phase-5/artifacts/aoi_link_s2_s3.json
```
