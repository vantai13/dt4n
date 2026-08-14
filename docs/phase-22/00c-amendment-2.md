# AMENDMENT 2 -- Phase 22 GO debt closure

Ngay: 2026-08-14

Trang thai: viet truoc khi tag `phase-23-start`. Amendment nay khong them ket
qua confirmatory moi cho Phase 22; no dong cach phat bieu cua GO-1/GO-2/GO-3
truoc khi Phase 23 bat dau.

## GO-1 -- Duong bien khong suy giam: DONG, co pham vi

| O | anchor_err (test) | AURC(C3)/AURC(C0) | Danh gia duoc? |
|---|---:|---:|---|
| poisson@0.925 (chinh) | 0.222399 | 0.997272 | CO - PASS |
| poisson@0.850 | 0.220727 | 1.008532 | CO - PASS |
| h2@0.700 | 0.126536 | 1.008595 | CO - PASS |
| poisson@0.700 | 0.000000 | khong xac dinh | KHONG - suy bien |
| cbr@0.700 | 0.000000 | khong xac dinh | KHONG - suy bien |

Hai o suy bien co `err` neo = 0, nen ti so AURC la 0/0. Bao trang thai NONE,
khong bao PASS.

Phat bieu duoc phep:

```text
Tren ca ba o van hanh danh gia duoc, viec chuyen sang chung nhan dong thoi
K=4 hop le sau chon loc khong lam suy giam duong bien risk-coverage:
AURC(C3)/AURC(C0) <= 1.009 < 1.02.
```

Khong duoc viet:

```text
Duong bien khong doi nhu mot dinh luat pho quat.
```

Pham vi la ba o nay, tai AR(1) tong hop va ho so AoI U0.

## GO-2 -- Xep hang FWER: DONG, phat bieu lai theo slot

Bang chung:

```text
results/phase-22/conformal_sim_poisson_0.925.json
  -> paired_bootstrap_delta_qhat
cert.go2_restate
  -> results/phase-23/go2_fwer_restatement.json
```

Ket qua 200 lan block bootstrap ghep cap, baseline = max-score, variant B:

```text
chua 0: 5/24
slot 1: + 0  - 3  0 5  (n=8)
slot 2: + 8  - 0  0 0  (n=8)
slot 3: + 8  - 0  0 0  (n=8)
```

Phat bieu duoc phep:

```text
Xep hang ba thu tuc FWER phu thuoc slot, khong co thu tu toan phan.

O slot 2 va 3, max-score chat hon ca Bonferroni lan Sidak o moi z-bin:
16/16 khoang tin cay 95% cua hieu q_hat(procedure) - q_hat(max-score) nam
hoan toan phia duong.

O slot 1, max-score khong phan biet duoc voi Bonferroni trong 4/4 bin; so voi
Sidak, max-score long hon o 3 bin va khong phan biet duoc o 1 bin.
```

Co che:

```text
Max-score dung mot nguong chung cho max_j s_j. Slot co score phan tan rong
keo nguong chung len. Vi vay max-score re cho slot 2/3, nhung khong chac re
cho slot 1.
```

Khong duoc viet:

```text
Sidak > Bonferroni > max-score
```

Hay bat ky thu tu toan phan nao.

## GO-3 -- Studentized max-score: CHUYEN SANG PHASE 23 EXPLORATORY

Lua chon: B - future work co ly do cu the.

Ly do:

```text
Studentized max-score duoc de xuat sau khi da nhin artifact Phase 22. Neu dung
no de sua ket luan Phase 22 thi khong con confirmatory. GO-2 vua cho thay loi
ich, neu co, phai duoc phat bieu theo slot va can seed/test doc lap.
```

Quyet dinh:

```text
Khong dua studentized max-score vao bang ket qua chinh Phase 22.
Khong dung no de thay the ranking FWER da prereg.
Tien dang ky lai o Phase 23 voi du doan:
  - loi ich tap trung o slot 1, q_hat_stud/q_hat_max = 0.92-0.98
  - slot 2/3 gan nhu khong doi, q_hat_stud/q_hat_max = 0.98-1.02
  - neu chay, phai validate tren seed doc lap V23-3
```

## Ket luan

GO-1 va GO-2 duoc dong ve mat phat bieu. GO-3 khong bi chen vao Phase 22 sau
du lieu; no duoc ghi thanh exploratory/future-work co prereg lai trong
`docs/phase-23/00-preregistration.md`.
