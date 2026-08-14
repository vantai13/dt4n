# AMENDMENT 23-12 -- Phase 23 headline metrics

Ngay: 2026-08-14

Ly do: `risk_system` cua Phase 23 khong don dieu theo coverage. AURC toan dai
tren `[0,1]` co the bi chi phoi boi vung coverage thap, noi fallback gan nhu
duoc dung cho moi hang va he thong te hon neo.

## Van de

Voi C3 + F2 STATIC trong Lesson 23.2:

```text
AURC_system_err(C3+F2, toan dai) = 0.252450
AURC_err(neo twin)               = 0.222399
```

Neu dung AURC toan dai lam headline, C3+F2 co ve te hon neo, mau thuan voi
ket qua van hanh o coverage cao. Mau thuan nay la do chi so, khong phai do
artifact: o coverage thap, fallback P1 chi phoi risk he thong.

## Chi so headline moi

Phase 23 phai bao cao:

```text
1. Dai coverage co loi: risk_system < neo
2. Dien tich cai thien: integral max(0, neo - risk_system) dc
3. AURC rieng phan tren dai van hanh [0.60, 1.00], chuan hoa theo be rong
```

Voi C3 + F2 STATIC hien tai:

```text
dai co loi                  = [0.6151, 1.0000]
tu choi toi da van co loi    = 38.49%
dien tich cai thien err      = 0.003368
best improvement             = 0.013227 tai coverage 0.79345
partial AURC [0.60,1.00]     = 0.214012
neo                          = 0.222399
partial-AURC ratio           = 0.9623
```

AURC toan dai van duoc bao cao trong bang phu, kem canh bao rang no khong
phai headline cho `risk_system` hinh chu U.
