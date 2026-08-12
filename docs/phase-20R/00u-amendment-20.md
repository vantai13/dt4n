# AMENDMENT 20 -- Lesson 20R.8: QS-LOSS by Phase T reanalysis

Ngay ky: 2026-08-12
Trang thai: KY sau khi chay `measurements/qs_loss_residual.py`.

## 1. Van de

`quasistatic_band.py` da chan kenh delay, nhung kenh loss moi la kenh quyet
dinh chinh gan cac gate mong manh. Khong duoc suy ra QS-LOSS tu QS-DELAY.

## 2. Estimand

Dung tai phan tich Phase T, khong chay Mininet moi. Voi moi row dong va control
ghep theo `(mode, rho_bar, seed)`:

```text
r_loss = (loss_do_dong - loss_QS_packet_weighted_dong)
       - (loss_do_control - loss_QS_packet_weighted_control)
```

`loss_QS_packet_weighted` dung trajectory thiet ke va arrival intensity, khong
dung trung binh theo thoi gian. Diem nay quan trong: time-weighted loss de
Jensen leak vao estimand.

## 3. Artifact

Artifact: `results/phase-20R/qs_loss_residual.json`

Decision CI trong artifact la seed-cluster, packet-weighted, normal CI95; row
level CI cung duoc bao cao nhu doi chieu.

```text
mode      a   point       CI95 decision              verdict
h2      0.2  -0.000109   [-0.000171, -0.000046]     PASS
h2      0.9  -0.000526   [-0.001037, -0.000015]     KHONG KET LUAN DUOC
poisson 0.2  +0.000003   [-0.000073, +0.000079]     KHONG KET LUAN DUOC
poisson 0.9  -0.000305   [-0.000555, -0.000055]     PASS
```

Nguong sup do da dong bang truoc:

```text
loss_negative = -0.001
loss_positive = +0.00005
```

## 4. Quyet dinh

O GO cua Phase 20R la `poisson`, nen QS-LOSS DAT cho ket luan headline:
CI nam trong `[-0.001, +0.00005]` tai `poisson, a=0.9`.

`h2, a=0.9` KHONG DUOC GOI LA PASS vi can duoi CI cham/vuot `-0.001`. Ket qua
nay chi noi h2 chua ket luan duoc trong bien loss hien tai.

## 5. Dien giai co che

`a=0.2` gan 0 hon ro so voi `a=0.9`, dac biet tren poisson:

```text
|poisson a=0.9| / |poisson a=0.2| > 100
```

Day ung ho ky vong vat ly: sai so tua-tinh o kenh loss tang theo bien do dao
dong tai, khong phai offset thiet bi phang.
