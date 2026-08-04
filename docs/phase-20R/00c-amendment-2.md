# AMENDMENT 2 -- Phase 20R: sua Q2 (hieu chuan SLA) va z_max cua gate

Ngay: 2026-08-04
Commit truoc thay doi: 5506e3e975dbad33e5ca240779a5a31bf4d072dd

## Toi Da Thay Gi

1. Hang so `0.01` cua Phase 20 dong hai vai khac nhau: nguong SLA cua loss
   va ti gia quy doi loss sang ms trong `w_loss`. Gop lam mot lam `h2` de roi
   vao trang thai vi pham 100% va `d_sla = 0` co hoc.
2. Lay ca `T_delay` va `T_loss` o p85 khong dam bao opt-viol 15%, vi vi pham
   la hop `(delay > T_delay) OR (loss > T_loss)`. Giai nguoc cho `p` nam
   quanh 88..92 va khac nhau tung o.
3. `cbr` khong hieu chuan duoc trong vung tin cay: delay gan hang so, loss
   bang 0, nen opt-viol bang 0%.
4. `z_max = 4.0 s` khong ton tai trong he thong. AoI that Phase 9 sawtooth
   nam trong `[0.051, 0.548] s`, nen gate doc tai 4 s la ngoai suy.

## Toi Doi Gi

```text
Q2' HIEU CHUAN SLA
    LOSS_EXCHANGE = 0.01  CO DINH moi che do
    TARGET_VIOL   = 0.15  CHOT
    w_loss        = T_delay / LOSS_EXCHANGE
    T_delay,T_loss = phan vi p cua delay/loss duong TOI UU,
                     voi p giai nguoc bang bisection sao cho
                     P((delay>T_delay) OR (loss>T_loss) | toi uu) = 0.15
    RANG BUOC: opt_viol_rate in [0.10,0.25], ngoai band -> LOAI o

Q5' z_max cua gate = 0.55 s (p95 AoI that, Phase 9)
    z in {1,2,4} van do va bao cao, nhung danh dau NGOAI SUY.
```

## Hau Qua Len Luoi Che Do

12 o thiet ke -> 10 o kha thi (Amendment 1, Q8) -> 8 o vao gate.
4 o `cbr` chuyen vai tro thanh doi chung duong PC1; khi can PC1 se dung
nguong muon tu o `poisson` cung `rho_bar`, ky vong `err = 0` tuyet doi.

## Toi Khong Doi Gi

Q1, Q3, Q4, Q6, Q7, Q8 giu nguyen. Nguong gate G1 `[0.05,0.40]`,
G2 `>= 0.03`, G3 Spearman `> 0` giu nguyen. Ngan sach lap giu nguyen.
