# AMENDMENT 23-74b -- SUA `A074` TRUOC KHI CHAY

Ngay ky : 2026-08-27

Moc     : sau `A074` (commit `c65fe78`), TRUOC dong code cham diem dau tien
          cua Lesson 23.24. KHONG mot phep do nao da chay.

Loai    : SUA TIEN DANG KY (`A074` khong duoc sua tai cho -- da ky va da
          commit; `L114` / `A071` R1)

Ngan sach: KHONG doi. Van 4 gate `G23-297..300`.

## 0. Vi sao amendment nay ton tai

`A074` muc 1 cap `Code: cert/action_pruning.py` va muc 5 viet "tai dung
`cert/baselines_lit.py`". Khi doc ma nguon de viet module do, ba su that
ky thuat lo ra, va ca ba deu lam `A074` KHONG THI HANH DUOC nhu da viet.

Khong su that nao trong so do doi mot DAI da ky. Chung doi CACH DO. Vi vay
amendment nay ky TRUOC khi chay, dung ban le ma `A071` R1 doi hoi.

## 1. Su that 1 -- "cat mot hanh dong" khong phai "xoa mot cot"

`cert/simultaneous_score.py:82` (`pair_scores`) ghi nguyen van:

```text
"Column `j` is the comparison `a1` versus the twin's `(j+2)`-th best action.
 The column index is a rank slot, never a path identity, so the slot is
 exchangeable across rows."
```

Cot `s_pair_1..3` la HANG (rank slot), khong phai DUONG. Duong nao o hang
nao thay doi TUNG HANG. Do do:

```text
Cat mot duong  =  cat cot cua ma tran (n, K)  ->  XEP HANG LAI  ->  s moi
                  KHONG phai "xoa cot s_pair_j"
```

He qua then chot, tu `a_1 = argmin y_hat` (`top_k_by_twin`, argsort tang):

```text
Neu duong bi cat KHONG BAO GIO la `a_1` -> mo neo giu nguyen -> moi `e(a)`
  cua duong song sot giu nguyen -> tap `s` con lai la TAP CON cua tap cu.
Neu duong bi cat CO KHI la `a_1`        -> mo neo nhay -> ca bai toan doi.

Do duoc tren TEST o 23.7:  P(a_twin = P2) = 0.000000
                           P(a_twin = P3) = 0.369222
```

## 2. Su that 2 -- parquet KHONG luu `y_hat` / `y_true`

`cert/build_calib_set_v3.py` ghi ra `a1`, `a2`, `s_pair_1..3`, `m_hat_1..3`,
... nhung KHONG ghi ma tran `(n, 4)` theo TUNG DUONG. Tu parquet ta biet
duong nao o hang 1 va hang 2, KHONG biet hang 3 hay hang 4.

=> Tu parquet mot minh, KHONG xep hang lai duoc. Mot module doc parquet roi
   "xoa mot cot" van CHAY va van RA SO -- va so do SAI, khong test cau truc
   nao bat duoc. Day la dang loi nguy hiem nhat: sai im lang.

**SUA `A074` muc 1 va muc 5:** `cert/action_pruning.py` xay tren
`cert/cell_matrices.py` (tang day: dung lai ma tran day du tu truth table +
AoI), **KHONG** tren `cert/baselines_lit.py` / parquet. Cau "tai dung
`cert/baselines_lit.py`" o `A074` muc 5 `G23-298` bi HUY.

`cell_matrices.acceptance_for` da lam dung bon dong can thiet (cat cot ->
`pair_margins_hat` -> `pair_scores` -> `fit_and_accept`). Dung lai, khong
viet lai.

## 3. Su that 3 -- `cell_matrices.prepare()` o tren TRUC CU (phat hien moi)

Day la phat hien cua chinh dot nay, khong co trong ban thao.

`cell_matrices.prepare()` (dong 233) goi cung:

```python
"z_bin": assign_bin(base["z_s"], Z_EDGES_PRIMARY)
```

`Z_EDGES_PRIMARY = (0.055, 0.1, 0.2, 0.3, 0.5501)` la truc LEGACY
(`legacy_sawtooth_51ms`). Cau hinh SONG cua 23.23 la truc DO
(`measured_v7`), `Z_EDGES_V7 = (0.1, 0.241, 0.366, 0.491, 0.641)` --
xem `results/LIVE/phase-23/baselines_lit.json` muc `validity.z_edges`.

Do duoc trong dot nay (1 seed, `axis = AXIS_MEASURED`, 199899 hang):

```text
z_s tren truc DO      : [0.1150, 0.6150]
mien bin cua PRIMARY  : [0.055,  0.5501]
assign_bin(z_s, Z_EDGES_PRIMARY) -> ValueError: z ngoai mien bin da tien
                                    dang ky [0.055, 0.5501]: min=0.115 max=0.615
assign_bin(z_s, Z_EDGES_V7)      -> 4 bin, dem 50591 / 49950 / 49950 / 49408
```

Nghia la `prepare()` KHONG CHAY duoc tren truc do -- no chi chay tren truc
legacy. Neu Lesson 23.24 goi `prepare()`, no se AM THAM chay tren truc cu,
va moi so se khong so sanh duoc voi 23.23. Do dung la hinh dang cua `S12`
va `L41`.

```text
SUA DA KY: `action_pruning` KHONG goi `cell_matrices.prepare()`.
No dung `cell_matrices(tt, axis = AXIS_MEASURED, aoi_profile = "U0")` va
mot ham `prepare` rieng dung `Z_EDGES_V7`.
Artifact PHAI khai `validity_block(aoi_generator = AOI_V7,
z_edges = Z_EDGES_V7, ...)` -- cung truc voi 23.23, khong phai truc legacy.
```

`A074` muc 5 viet "CUNG 4 bin `z_bin`". Cau do duoc GIU, va bay gio no co
mot dinh nghia thi hanh duoc: 4 bin cua `Z_EDGES_V7`.

Ghi vao `LIMITS.md` la `L130`: `cell_matrices.prepare()` chi dung duoc tren
truc legacy; moi nguoi goi tren truc do phai tu bin.

## 4. SUA `G23-300` / `NC-23.24-1` -- bo ve (i), them ve chan (iii)

Ly do: tu muc 1, cat `P3` doi mo neo tren ~36.9% hang, con cat `P2` khong
bao gio doi. Hai nhanh vi vay khac nhau o CA CAU TRUC bai toan, khong chi o
"duong song hay chet". Ve (i) da ky:

```text
(i)  |Delta acceptance(cat P3) - Delta acceptance(cat P2)| <= 0.02
```

do luong ca hieu ung MO NEO lan hieu ung ngan sach. No co the fail vi mo
neo nhay -- tuc fail vi mot ly do KHAC voi dieu no dinh kiem. Mot phep kiem
bi nhieu la mot phep kiem khong ket luan duoc: cung lop benh voi `L119`.

Va kenh ngan sach DA co mot phep co lap sach hon, da ky, khong ton them
gate: nhanh (ii) cua `M-235` -- CHI noi `alpha_each`, khong cat gi, nen mo
neo khong the doi.

```text
BAN SUA CUA `G23-300`:

BO   ve (i).  Ly do o tren. Kenh ngan sach do bang `M-235` nhanh (ii).

GIU  ve (ii)  `Delta err|accept (cat P3)` >= +0.02
              -> tinh CHET moi la thu mua duoc su "mien phi"

THEM ve (iii) VE CHAN, cham tren CALIB:
              `P_calib(a_twin = P2) = 0`  VA  `P_calib(a_twin = P3) > 0.05`
              Neu (iii) HONG thi (ii) KHONG dien giai duoc, vi ta khong con
              biet minh dang cat mot duong "song" hay khong.

BAO CAO them, KHONG cham diem: ti le hang bi DOI MO NEO o moi nhanh
              (`anchor_moved_rate`). Day la co CHUAN DOAN cho moi so cua
              nhanh do. Du bao: ~0.000 o nhanh P2, ~0.37 o nhanh P3.
```

`G23-300` van la MOT gate. Ngan sach khong doi.

## 5. Nhung gi KHONG doi

```text
· Ngan sach 4 gate (`A071` R1).
· Tieu chi hai tang o `A074` muc 3.2 -- nguyen van, khong mot chu nao doi.
· Dai cua `M-233` (tap CAT tren CALIB == {P2}).
· Dai cua `M-234`: ti so q_hat trong [0.88, 0.94]; Delta acceptance(S1 vs
  S0) trong [+0.01, +0.05]; bac S2 la [MO TA].
· Dai cua `M-235`: `budget_share(S1) >= 0.90`.
· Ba kich ban K1/K2/K3 o `A074` muc 6.
· N1..N6 o `A074` muc 8.
· Bonferroni, `kappa = 0.50`, `alpha_family = 0.10`, cell `poisson@0.925`.
```

## 6. Mot du bao bi BAC BO -- chi phi may

Ban thao canh bao `cell_matrices()` "ton thoi gian may (nhieu seed x N
buoc)" va de nghi cache ra `/tmp`. Do duoc trong dot nay:

```text
1 seed, truc do, 199899 hang : 0.8 s
5 seed (SEEDS = 101..105)     : ~4 s
```

=> KHONG can cache. De nghi cache bi BAC BO. Mot lop cache khong can thiet
   la mot nguon lech im lang giua hai lan chay (`L118`).

## 7. Pham vi va gioi han cua chinh amendment nay

```text
N1  Amendment nay KHONG noi rong mot dai nao, KHONG them mot gate nao, va
    KHONG doi mot hang so nao. No sua CACH DO va BO mot ve khong ket luan
    duoc. Viec bo ve (i) lam `G23-300` DE dat hon (2 ve thay vi 2 ve, nhung
    ve bi bo la ve co the fail vi ly do ngoai le). Ghi ro dieu do o day de
    nguoi doc tu tru: `G23-300` sau ban sua yeu hon truoc.

N2  Ve (iii) duoc cham tren CALIB, con ve (ii) tren TEST. Do la co y: (iii)
    la dieu kien DIEN GIAI (ta co dang cat mot duong song khong), nen no
    phai dung cung nguon su that voi `M-233`. Tron hai nguon la `L121`.

N3  Con so `P(a_twin = P3) = 0.369222` trich o tren do TREN TEST o 23.7
    (`A074` N1). No dung de DU BAO `anchor_moved_rate`, khong de cham diem.
    Ve (iii) cham tren CALIB va co the ra khac.

N4  `cell_matrices.prepare()` KHONG bi sua trong amendment nay. No la tang
    day, nhieu artifact da dong phu thuoc vao no o truc legacy. Sua no la
    mot nhanh khac. Ghi `L130`, KHONG mo o day (`A071` R2).
```
