# AMENDMENT 23-9 -- F1 low-kappa mechanism diagnostic

Ngay: 2026-08-14

Ly do: doi chung quyet dinh cho co che shrinkage ve prior cua Lesson 23.1.

Luu y trang thai thong tin: luoi min [KHAM PHA] da duoc sinh truoc amendment
nay va co chua cac point estimate cua F1/F2/F3-a. Amendment nay KHONG duoc
cham nhu mot du doan blind tren point estimate. No khoa truoc khi chay phan
kiem dinh rieng cua F1 gom paired block bootstrap CI, sticky diagnostics, va
so sanh truc tiep voi nguong hoa von tai `kappa=0.20`.

## Gia thuyet can phan biet

```text
H_shrinkage:
  F2 thang vi P1 la prior cau truc khong nhieu.
  F1 khong thang ro vi no giu mot quan sat twin cu, van la nhieu.

H_tam_thuong:
  Bat ky fallback nao cung thang o kappa thap vi reject set nho.
```

## Prediction diagnostic

```text
F6a  [CO CHE / DIAGNOSTIC]
     Delta err_system(F1 STICKY) tai kappa=0.20 nam trong [-0.003, +0.003],
     va CI95 ghep cap chua 0.

F6b  [CO CHE / DIAGNOSTIC]
     sticky_age_ms_mean tai kappa=0.20 < 20 ms.

F6c  [CO CHE / DIAGNOSTIC]
     err|reject(F1) tai kappa=0.20 nam trong +/-0.02 cua err|reject(twin).
```

Nhanh fail viet truoc: neu F1 cung thang ro tai kappa=0.20 voi CI95 am khong
chua 0, co che "F2 thang rieng vi prior khong nhieu" bi bac hoac can viet lai.
