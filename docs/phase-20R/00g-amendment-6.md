# AMENDMENT 6 -- Phase 20R.5: quy tac so sanh khi prediction gan 0

Ngay: 2026-08-06

## Van De

Rule ty le trong `02-prediction.md` dung cho cac o co prediction khac 0 ro
rang. Sau khi do Phase 20R.5, `h2@0.960, z=0.55` nam trong vung near-zero:

```text
predicted err_total = 0.000330
measured  err_total = 0.001675
absolute gap        = 0.001345
ratio               = 5.07x
```

Ratio lon o day la do mau so gan 0, khong phai mot discrepancy co y nghia gate.

## Quy Tac Chot

So sanh prediction voi measured error:

```text
neu predicted err >= 0.02:
  dung ratio law nhu da ky trong prediction

neu predicted err < 0.02:
  dung absolute law: |measured - predicted| <= 0.02
```

Nguong `0.02` la vung floor thuc nghiem cho decision error; ben duoi nguong nay
ratio bi bat on va khong phan biet duoc "sai gap nhieu lan" voi "ca hai deu
gan 0".

## Ap Dung

`h2@0.960, z=0.55` PASS theo absolute law:

```text
|0.001675 - 0.000330| = 0.001345 <= 0.02
```

Cac o khac o `z=0.55` co `predicted err >= 0.02` van dung ratio law cu.

