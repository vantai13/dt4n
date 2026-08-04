# AMENDMENT 1 -- Phase 20R: bo sung Q8 (bien do dao dong sigma_rho)

Ngay: 2026-08-04
Commit truoc thay doi: df44a85c85975b1f5e6f273694db6452674876cf

## Toi Da Thay Gi

Khi viet golden test cho `twin/cost_v2.py`, ba quan sat xuat hien truoc khi
chay bat ky phep do Phase 20R nao:

1. Quet `rho_bar` tu 0.60 den 0.96 voi offset Q7 co dinh lam xep hang duong
   luon la `P1 < P3 < P4 < P2`. `err` khong den tu muc tai trung binh, ma den
   tu dao dong quanh muc tai. Test khoa:
   `test_gc8b_mean_ranking_is_locked_by_design`.
2. `mininet/rho_spec.sigma_max_feasible()` tinh tren `rho_bar`, nhung Q7 cong
   offset theo link, nen bat bien "hiem cham bien" bi pha vo. Tai
   `rho_bar = 0.98`, ham cu cho phep sigma 0.0271, trong khi link `ad` chi
   con headroom 0.0029 neu giu xac suat 99%.
3. Tran rang buoc khong phai chi la `RHO_MAX = 1.05`, ma la tran do tin cay
   cua tung traffic family. `cbr` chi tin cay den `rho = 0.95` theo
   `link_model_v2.is_reliable()`.

## Toi Doi Gi

Bo sung Q8 vao pre-registration:

```text
Q8  BIEN DO DAO DONG
    sigma_max(mode, rho_bar) = min over link of
        min(ceil(mode) - (rho_bar + offset_link),
            (rho_bar + offset_link) - 0.50) / 2.58

    ceil = {cbr: 0.95, poisson: 1.05, h2: 1.05}
    sigma_rho(o) = a * sigma_max(mode, rho_bar), a = 0.9 CHOT

    Neu sigma_max = 0 -> o do VO NGHIEM, LOAI, khong duoc thu nho tay.
```

`a = 0.9` lay tu truc thiet ke Phase T `a in {0.2, 0.9}`. Chon gia tri lon
de bai toan quyet dinh khong rong. `a = 0.2` se duoc chay nhu doi chung do
nhay o Lesson 20R.6.

## Hau Qua Len Luoi Che Do

12 o -> 10 o kha thi. Hai o bi loai:

```text
(cbr, rho_bar = 0.925)   sigma_max = 0
(cbr, rho_bar = 0.960)   sigma_max = 0
```

Day la he qua cua quy tac da ky va duoc phat hien truoc phep do, khong phai
lua chon sau khi thay ket qua.

## Hau Qua Len Gia Thuyet

H4 cu phai phat bieu lai:

```text
H4' err(cbr) < err(poisson) tai rho_bar in {0.70, 0.85},
    la hai o cbr con lai.
```

## Toi Khong Doi Gi

Q1-Q7 giu nguyen. Gate 20R-G1..G7 giu nguyen. Ngan sach lap giu nguyen.
