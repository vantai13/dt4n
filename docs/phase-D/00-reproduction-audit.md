# Phase D′ — kiểm toán tái tạo trước khi dọn dữ liệu

Ngày kiểm toán: 2026-08-28. HEAD trước thay đổi: `481cace`.

## Backup

Đã tạo bản sao đầy đủ có cả `.git` tại:

```text
/home/vantai/dt4n-FULL-BACKUP-20260828.tar.gz  6.5 GiB
SHA256 83162ca25f6eb9041b1b2bf2c03d02b99a3fff99d4cc88ba047a9216c8495ff5
```

Đây là backup cục bộ trên cùng máy, chưa thay thế bản sao ngoài máy của quy
tắc 3-2-1.

## Đối chứng tái tạo parquet

Lệnh thật của code hiện tại dùng `--rho-bar`, không dùng `--rho`:

```bash
.venv/bin/python -m cert.build_calib_set_v2 \
  --mode poisson --rho-bar 0.850 \
  --out /tmp/dt4n-phase-d-repro/calib_set_poisson_0.850.parquet \
  --report /tmp/dt4n-phase-d-repro/calib_set_poisson_0.850.report.json
```

Kết quả:

```text
old SHA256  8c75cbf884b44147786eb36ef0f2c043aedf63e4ff121bb94dba91e747965651
new SHA256  1cf19e3e26848b6160a4e8b552d4358137fc9d774053517d4cb5cb5d8902d2a9
old shape   (999945, 24)
new shape   (999945, 24)
pandas.equals(old,new) = False
```

Report gốc ghi `git_dirty=true` tại commit `cdc4a561...`; lịch sử cho thấy
`cert/build_calib_set_v2.py` chưa tồn tại trong tree của chính commit đó. Vì
vậy provenance hiện tại không đủ để khôi phục bit-exact code đã sinh file.

## Phán quyết lưu trữ

NC tái tạo **FAIL**. Tám parquet gốc, tổng `280,794,510` byte, chưa được phép
xếp hạng DERIVED có thể xoá. Chúng được giữ nguyên, vẫn tracked, và cần được
xử lý như dữ liệu cần custody cho đến khi tái tạo tương đương được giải thích.
Không chạy `git rm --cached`, không rewrite lịch sử.

SHA256 của cả tám file nằm ở `parquet-sha256-before-delete.txt`.
