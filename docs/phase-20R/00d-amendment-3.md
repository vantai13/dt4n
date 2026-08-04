# AMENDMENT 3 -- Phase 20R: bo sung H6 va khai bao tau/a

Ngay: 2026-08-04
Commit truoc thay doi: f282a07f0c6bce4eeb702078a097eaa8129afe53

## Toi Da Thay Gi

Khi chay du doan truoc chien dich, hai bac tu do `tau_rho` va `a` co anh
huong lon hon du kien. Tren nhieu o, doi `tau_rho` tu 1.0 sang 0.2 hoac 5.0
lam `err(0.55)` doi nhieu lan; doi `a` tu 0.2 sang 0.9 co the doi `err` tu
gan 0 sang muc co y nghia.

Dong thoi, tren `poisson@0.925`, cac duong theo `tau in {0.2,1.0,5.0}` gop
lai khi ve theo bien khong thu nguyen `z/tau_rho`; max spread tien chien dich
= 0.0156.

## Toi Doi Gi

Bo sung gia thuyet H6:

```text
H6  err(z | che do) chi phu thuoc z qua ti so khong thu nguyen z/tau_rho.
    Kiem: chay tau in {0.2, 1.0, 5.0} tren mot o,
          gop duong cong theo z/tau.
    PASS neu do tan giua ba duong < 0.05 tuyet doi tren toan luoi z/tau.
    Neu bi bac bo, bao cao ket qua am.
```

Khai bao `tau_rho = 1.0` va `a = 0.9` la hai bac tu do thiet ke da chot.
Lesson 20R.6 se chay doi chung do nhay voi `a = 0.2` va
`tau_rho in {0.2, 5.0}`.

## Toi Khong Doi Gi

Q1-Q8, Q2', Q5', gate G1-G7, va ngan sach lap giu nguyen. `z = 0.55 s`
van la diem doc gate; `z in {1,2,4}` van la ngoai suy.
