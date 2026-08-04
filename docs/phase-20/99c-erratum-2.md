# ERRATUM 2 - Phase 20

Ngay: 2026-08-04
Trang thai: Phase 20 dong bang tai tag `phase-20-complete`. KHONG sua nguoc.

## E10. Thay link_model la DIFFERENTIAL error, khong phai common-mode

Erratum 1 (E6) lap luan: `c_hat` va `c` cung duoc ve bang MOT `link_model`,
nen sai lech hang so payload la common-mode doi voi phep do noi bo. Lap luan
do dung cho E6, nhung khong mo rong duoc sang viec thay `link_model`.

Bang chung dinh luong, sinh lai bang `python3 tools/audit_v1_vs_v2.py --write`,
tai LOAD_MEAN, mode `poisson`:

```text
link   v2/v1
ad     0.61x      <- v2 THAP hon v1
bd     2.00x      <- v2 CAO hon v1 gap doi
```

Sai lech doi chieu nhau giua cac link, nen day la vi sai, khong dong pha.

Hau qua tren xep hang duong:

```text
v1 : P1 < P4 < P3 < P2
v2 : P1 < P3 < P4 < P2
```

Va tren nguong SLA:

```text
T_delay(Phase 20) = 14.5138 ms
min delay duong toi uu duoi v2, mode poisson, rho_bar = 0.70: 15.35 ms
=> moi duong, moi thoi diem deu vi pham delay threshold cu trong bang can duoi
```

## Ket Luan

`err = 0.187` va `d_sla = 0.081` KHONG duoc trich dan nhu ket qua khoa hoc.
Chung tro thanh phu luc: ket qua khi ground truth bi o nhiem boi chinh mo hinh.
Phep do thay the: Phase 20R, `docs/phase-20R/`.

## Khong Hanh Dong

Khong chay lai Phase 20. Khong sua `results/phase-20/`. Khong sua nguoc cac
erratum cu. Danh dau DEPRECATED trong docstring `twin/link_model.py`, nhung
khong `git rm`, de tai lap phu luc v7.
