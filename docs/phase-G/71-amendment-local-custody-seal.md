# Amendment — cổng custody chuyển sang niêm phong backup đã xác minh hash

Ngày: 2026-09-06 UTC. Ký **trước** khi `G′.7` sinh ra bất kỳ dữ liệu nào, nên không thể là quyết định chạy theo kết quả.
Thay thế cơ sở của cổng, **không** thay thế DOI. `results/DATA_MANIFEST.json::doi` vẫn là `null`.

## 1. Vì sao thay

Cổng Phase G mở từ 2026-08-30 trên [waiver lời khai](../phase-D/05-offsite-backup-custody-waiver.md):
`offsite_backup.status = USER_ATTESTED_PRESENT`, và quan trọng là `checksum_verified_in_workspace = false`.
Tức cơ sở của cổng là một **lời khai chưa kiểm được**: nếu một file bằng chứng bị sửa im lặng, waiver đó không phát hiện ra.

Điều cổng thật sự muốn bảo vệ là **bằng chứng không đổi im lặng sau khi đã trích dẫn**. Cái đó kiểm được cục bộ.
Cái không kiểm được cục bộ là **tính công khai, trích dẫn được, do bên thứ ba giữ** — và đó đúng là phần DOI vẫn còn nợ.

Amendment này tách hai thứ đang bị gộp làm một, rồi đáp ứng phần kiểm được.

## 2. Niêm phong đã tạo

```
/home/ubuntu/backups/dt4n/20260906T100621Z/
    SEAL.json          2028 B     sha256 93084fcbcc728d3ce8816f28d1b40be6b53f2e860f5d1ed5ace878324021e1ad
    repo.bundle        1.68 GB    git bundle --all, git bundle verify = PASS
    results.tar.zst    6.38 GB    toàn bộ cây results/, đọc lại full listing OK
```

Cả ba đặt quyền `0444`. `latest` là symlink trỏ tới bản niêm phong mới nhất.

**Bước có ý nghĩa nhất không phải là bản sao, mà là phép kiểm trước khi sao:**
`tools/local_custody_backup.py --create` đọc lại **từng file** trong `DATA_MANIFEST.json` và `g4_data_manifest.json`, tính lại SHA256, đối chiếu với giá trị đã ghi, và **từ chối niêm phong** nếu có một sai lệch hoặc một file thiếu.

```
n_files_verified      134
bytes_verified        6952580229
n_mismatched          0
n_missing             0
```

134/134 file tái tạo đúng hash đã ghi. Đây là lần đầu điều đó được kiểm trong workspace, không phải khai báo.

## 3. Cổng mới

`tools/check_phase_g_custody.py` giờ có ba cơ sở, mạnh trước:

| Cơ sở | Chạy Phase G cục bộ | Chạy chiến dịch `G′.7`/`G′.8` | Tuyên bố lưu trữ công khai | Dọn dữ liệu lịch sử |
|---|---|---|---|---|
| `PUBLIC_VERSION_DOI` | CHO | CHO | **CHO** | CHO |
| `VERIFIED_LOCAL_BACKUP_SEAL` ← đang dùng | CHO | **CHO** | CẤM | CẤM |
| `USER_ATTESTED_OFFSITE_BACKUP_WAIVER` | CHO | CẤM | CẤM | CẤM |

Cổng **kiểm lại niêm phong tại chỗ**, không tin manifest: file `SEAL.json` phải còn, phải hash đúng giá trị manifest đã ghi, phải khai `doi = null` và `public_archival_gate_pass = false`, phải báo đã tái tạo mọi hash, và cả hai artifact được niêm phong phải còn nguyên hash.
Một niêm phong bị sửa sẽ **rơi xuống** cơ sở waiver và `campaign_execution_allowed` trở lại `false` — có test khoá đúng đường đó (`test_seal_is_reverified_not_trusted_from_the_manifest`).

```
$ python3 -m tools.check_phase_g_custody
{"pass": true, "basis": "VERIFIED_LOCAL_BACKUP_SEAL", "doi": null,
 "phase_g_local_work_allowed": true, "campaign_execution_allowed": true,
 "public_archival_claim_allowed": false, "historical_cleanup_allowed": false,
 "seal_detail": "ok"}
```

## 4. Cái này KHÔNG phải là gì

Ghi rõ để không ai, kể cả tác giả sau sáu tháng, đọc nhầm:

- **Không phải DOI, không tương đương DOI.** Không có DOI nào được sinh, dự trữ hay bịa ra. `doi` vẫn `null`, `published_doi` vẫn `null`, `is_doi_equivalent = false`.
- **Không mở cổng công bố.** Luận văn, bài báo, hay bất kỳ văn bản nào trích dẫn bộ dữ liệu **vẫn cần một Version DOI thật**. `G′.8` được phép **chạy**, không được phép **phát hành ra ngoài** trên cơ sở này.
- **Bản sao cùng máy.** Nó không sống sót nếu mất chính host này. Nó bổ sung cho bản offsite đã khai, không thay thế.
- **Không do bên thứ ba giữ, không bất biến trước chính tài khoản này.** Quyền `0444` chống nhầm tay, không chống chủ ý.
- **Niêm phong theo thời điểm.** Nó chứng nhận cây bằng chứng tại `2026-09-06T10:06:21Z`. Dữ liệu `G′.7` sinh ra sau đó cần một niêm phong mới; chạy `--create` lần nữa sau chiến dịch.

## 5. Việc còn nợ

DOI thật vẫn là điều kiện của công bố. Khi có `ZENODO_ACCESS_TOKEN`, `tools/zenodo_reserve_doi.py --reserve` dựng bản nháp và ghi biên nhận; DOI dự trữ vẫn **không** tự nó qua được cổng lưu trữ công khai — chỉ bản ghi đã xuất bản mới qua.
Khi điều đó xảy ra, đặt `DATA_MANIFEST.json::doi` và cơ sở cổng tự động nâng lên `PUBLIC_VERSION_DOI`; niêm phong cục bộ ở lại như lớp custody thứ hai, không cần gỡ.

Mã: `tools/local_custody_backup.py` (`--create`, `--verify`), `tools/check_phase_g_custody.py`, `test/test_phase_g_custody.py`.
