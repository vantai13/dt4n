# Phase D′ — phân loại dữ liệu và quyết định custody

Snapshot 2026-08-28:

Hai cột byte trả lời hai câu hỏi khác nhau: `local` là custody trên máy đo;
`tracked` là khối lượng đi vào clone Git. Snapshot tracked được tính bằng
`git ls-files` tại `50f80cf`.

| Khu vực | Byte local | Byte tracked | Phân loại hiện tại | Quyết định |
|---|---:|---:|---|---|
| `results/RAW` | 544,296,325 | 4,101,323 | RAW | không xoá; cần archive ngoài repo và Version DOI |
| `results/LIVE` | 2,887,137,232 | 6,773,168 | CITED + derived cache hỗn hợp | giữ; phân loại từng artifact trước khi dọn |
| `results/PENDING` | 1,510,501,124 | 197,114 | PENDING | không dùng làm headline; chưa xoá tự động |
| `results/SMOKE` | 479,053,094 | 2,337,860 | diagnostic | giữ tạm; không phải RAW khoa học |
| `results/SUPERSEDED` | 2,217,457,625 | 310,508,285 | history + non-reproducible hỗn hợp | không xoá hàng loạt |

`results/DATA_MANIFEST.json` đã ghi SHA256 cho 122 artifact nhị phân, nhưng
`doi` hiện là `null` và manifest không bao phủ toàn bộ RAW CSV/JSONL. Vì chưa
có tài khoản/Version DOI trong phiên chạy này, D-1 và D-13 chưa PASS đầy đủ.

Tám parquet gốc Phase 21R (280,794,510 byte local/tracked) không còn đủ bằng
chứng để gọi là DERIVED tái tạo được: positive-control thất bại về cả SHA256
lẫn nội dung. Chúng chuyển sang hạng **R/non-reproducible custody**: phải đưa
lên archive có Version DOI trước, sau đó mới được `git rm --cached`. Xem
`00-reproduction-audit.md`.
