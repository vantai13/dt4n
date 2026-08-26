# AMENDMENT 23-70a -- dong allowlist W bang stop-rule that

Ngay ky : 2026-08-26

Moc      : sau tag `lesson-23-22d-prereg`, truoc ma/chay A070

Loai     : TIEN DANG KY, sua mau thuan noi tai cua A070 muc 2.2

## 0. Disclosure

Chua viet/chay ma A070; chua sinh cell W. Khi chuyen A070 thanh hop dong may,
phat hien `n_calib_blocks` va `build_seconds` nam trong allowlist nhung
stop-rule W da viet chi doc `err_neo`. Dieu nay tu vi pham quy tac `L108`.

## 1. Hai stop-rule van hanh bo sung cho W

```text
W-I1  Moi cell phai co DUNG 500 calibration block.
      Bat ky cell nao khac 500 -> batch INVALID, DUNG W, khong cham M-215..217.

W-I2  build_seconds cua moi cell phai <= 60.0 giay.
      Bat ky cell nao vuot 60.0 -> DUNG W va ky lai budget/batch.
```

60 giay rong gan 7 lan so lon nhat A069 hop le (8.81 giay), nhung chat hon
30 lan stop-rule cu 1800 giay. No bat thay doi co che tinh toan that su ma
khong toi uu theo nhieu timing nho.

Sau sua nay, anh xa allowlist -> stop-rule la day du:

| outcome duoc mo | noi doc |
|---|---|
| `err_neo` | M-215/M-216/M-217 va stop-rule M-215 |
| `n_calib_blocks` | W-I1 |
| `build_seconds` | W-I2 |

`cell` chi la khoa thiet ke. Khong outcome nao khac duoc mo.
