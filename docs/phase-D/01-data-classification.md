# Phase D′ — phân loại dữ liệu và quyết định custody

Snapshot 2026-08-28:

| Khu vực | Byte cục bộ | Phân loại hiện tại | Quyết định |
|---|---:|---|---|
| `results/RAW` | 544,296,325 | RAW | không xoá; cần archive ngoài repo và Version DOI |
| `results/LIVE` | 2,887,137,232 | CITED + derived cache hỗn hợp | giữ; phân loại từng artifact trước khi dọn |
| `results/PENDING` | 1,510,501,124 | PENDING | không dùng làm headline; chưa xoá tự động |
| `results/SMOKE` | 478,983,745 | diagnostic | giữ tạm; không phải RAW khoa học |
| `results/SUPERSEDED` | 2,217,457,625 | history + derived hỗn hợp | không xoá hàng loạt |

`results/DATA_MANIFEST.json` đã ghi SHA256 cho 122 artifact nhị phân, nhưng
`doi` hiện là `null` và manifest không bao phủ toàn bộ RAW CSV/JSONL. Vì chưa
có tài khoản/Version DOI trong phiên chạy này, D-1 và D-13 chưa PASS đầy đủ.

Tám parquet gốc Phase 21R không được xoá: positive-control tái tạo thất bại
về cả SHA256 lẫn nội dung. Xem `00-reproduction-audit.md`.
