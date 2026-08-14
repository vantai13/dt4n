# AMENDMENT 23-7 -- One-time kappa grid refinement

Ngay: 2026-08-14

Ly do: thiet ke luoi, khong phai gia tri ket qua.

Quan sat sau Lesson 23.1: argmin cua risk he thong tren luoi kappa tien dang ky
P8 roi vao `kappa = 0.25`, diem khong-suy-bien dau tien cua luoi. Diem
`kappa = 0` chap nhan 100% hang va khong dung fallback, nen no la diem suy
bien. Mot argmin o bien mien kha dung khong phan giai cuc tri.

## Luoi bo sung

Chi duoc lam min MOT LAN:

```text
kappa in {0.05, 0.10, 0.15, 0.20, 0.30, 0.35, 0.40}
```

## Quy tac bao cao

```text
(a) Gate G23-14 van cham tren luoi goc P8. Con so tien dang ky vao abstract
    la diem P8 tot nhat, hien tai la F2 STATIC tai kappa=0.25.

(b) Luoi min bao cao rieng voi nhan [KHAM PHA]. Khong dung luoi min de cham
    gate tien dang ky.

(c) Neu argmin tren luoi min roi vao bien kappa=0.05, ghi ro rang cuc tri
    van chua duoc phan giai va KHONG lam min them lan nua.

(d) Ket luan tu luoi min can duoc kiem chung tren split seed doc lap V23-3
    truoc khi dung lam khang dinh chinh.
```
