# 20R2.5 — Sự cố lần chạy 1: PermissionError (bản ghi sự cố)

**Vì sao file này tồn tại.** Log gốc nằm ở `logs/`, bị `.gitignore:31` (`logs/*`)
loại. Sổ cái `04-campaign-log.jsonl` **cũng không có dòng nào** về lần chết này —
đó là một lỗ thiết kế trong runner, xem mục "Đã vá" bên dưới. Sổ cái vì thế đúng
về **trạng thái** nhưng thiếu về **lịch sử**. File này vá phần lịch sử.

Một bàn giao chỉ có thật khi nằm trong git.

## Điều đã xảy ra

Lần chạy đầu (2026-09-10, ~13:05 UTC) chết ở **lệnh thứ 2** — lệnh
`control_legacy` đầu tiên, tức lệnh đầu tiên ghi vào tầng SUPERSEDED.

```text
PermissionError: [Errno 13] Permission denied:
    '/home/ubuntu/dt4n/results/SUPERSEDED/phase-20R2'
```

Nguyên nhân: `results/SUPERSEDED` có mode `dr-xr-xr-x` (555) — khoá ghi **cố ý**
từ 2026-08-23 để bảo vệ bằng chứng đã bị thay thế. Nhưng prereg §3 ký nhánh đối
chứng âm ghi vào chính tầng đó. Hai quyết định đều đúng, va nhau.

Phân loại theo runbook §2: **HẠ TẦNG** — không chạm mã, không chạm khoa học.
Kế hoạch, dụng cụ và đích ghi đều đúng như đã ký.

## Đã sửa thế nào

Tối thiểu, giữ nguyên ý đồ bảo vệ:

```bash
chmod u+w results/SUPERSEDED
mkdir -p results/SUPERSEDED/phase-20R2/campaign
chmod u-w results/SUPERSEDED          # TRA LAI khoa cho tang
```

Đã kiểm sau khi sửa: `touch results/SUPERSEDED/phase-23/.x` **vẫn bị từ chối**.
Chỉ thư mục mới của phase-20R2 ghi được.

⚠️ **Mode 555 là trạng thái filesystem CỤC BỘ. Git không lưu quyền của thư mục**
(chỉ lưu bit thực thi của file). Một clone của người khác **sẽ không có khoá này**,
và cũng sẽ không gặp lỗi này. Ai tái lập trên máy khác cần biết điều đó.

## Sổ cái không bị ảnh hưởng

Lệnh 0 (điểm canh) đã hoàn tất và có dòng sổ hợp lệ. Trước khi resume đã đối chiếu
sha trên đĩa với sổ cái: **KHỚP**. Không có file mồ côi. Resume bỏ qua lệnh 0 và
chạy tiếp từ lệnh 1. Chiến dịch cuối cùng: 167/167 `rc=0`, vệ sinh PASS 9/9.

## Đã vá (để chiến dịch N3/N4 không lặp lại)

Trong `tools/20r2_5_run.py`, phần chuẩn bị trước `subprocess` (`unlink` file mồ côi
và `mkdir` thư mục đích) chạy **trước** `append_log`. Nên một ngoại lệ ở đó văng ra
mà **không để lại dấu vết nào trong sổ cái**.

Đã bọc bằng `try/except`, ghi `{"kind": "run", "returncode": -1, "error": ...}` rồi
mới ném lại. Từ nay mọi lần chết đều có dòng sổ.

## Bằng chứng — log gốc

```text
Traceback (most recent call last):
  File "/home/ubuntu/miniforge3/envs/sdn_rl/lib/python3.12/pathlib.py", line 1311, in mkdir
    os.mkdir(self, mode)
FileNotFoundError: [Errno 2] No such file or directory: '/home/ubuntu/dt4n/results/SUPERSEDED/phase-20R2/campaign'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/ubuntu/dt4n/tools/20r2_5_run.py", line 220, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/home/ubuntu/dt4n/tools/20r2_5_run.py", line 189, in main
    target.parent.mkdir(parents=True, exist_ok=True)
  File "/home/ubuntu/miniforge3/envs/sdn_rl/lib/python3.12/pathlib.py", line 1315, in mkdir
    self.parent.mkdir(parents=True, exist_ok=True)
  File "/home/ubuntu/miniforge3/envs/sdn_rl/lib/python3.12/pathlib.py", line 1311, in mkdir
    os.mkdir(self, mode)
PermissionError: [Errno 13] Permission denied: '/home/ubuntu/dt4n/results/SUPERSEDED/phase-20R2'
twin-hoan-hao (pre): PASS
[  1/167] CANARY         tau=3    a=0.9 seed=999     13.4 s  ok
=== EXIT rc=0  ===
```
