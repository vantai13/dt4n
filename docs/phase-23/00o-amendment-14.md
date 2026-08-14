# AMENDMENT 23-14 -- B6-sys is the system oracle

Ngay: 2026-08-14

Ly do: B6 xep theo `m_true` la oracle cho bai toan du doan, nhung Phase 23 do
rui ro he thong sau khi gan fallback. Oracle dung cho bai toan he thong phai
xep hang theo loi ich doi tu twin sang fallback.

## Dinh nghia

```text
B6      : score = m_true_1
B6-sys  : score = loss(a_fallback) - loss(a_twin)
```

Voi thang `err` va fallback F2 STATIC:

```text
s* = 1[P1 != a*] - 1[a_twin != a*] in {-1, 0, +1}
```

Ba xac suat da do:

```text
P(twin sai)   = 0.222399
P(P1 sai)     = 0.340276
P(ca hai sai) = 0.093956
```

Suy ra duong B6-sys co dang dong ba doan:

```text
mass_pos  = 0.246320  twin dung, P1 sai, phai chap nhan
mass_zero = 0.625237  hai ben nhu nhau, tho o
mass_neg  = 0.128443  twin sai, P1 dung, phai tu choi

knee 1 coverage = 0.246320, err = 0.093956
knee 2 coverage = 0.871557, err = 0.093956
endpoint coverage = 1.0, err = 0.222399
AURC_err(B6-sys) = 0.132542
```

## Gates

```text
G23-12a  B6 nam duoi cac duong khac tren err|accept.
G23-12b  B6-sys nam duoi cac duong khac tren err_system.
G23-12c  B6-sys do duoc khop cong thuc ba doan trong 1e-9.
```

Du doan co che:

```text
O2  err_system(B6) - err_system(B6-sys) tai coverage 0.50 nam trong [0.02,0.08].
```

Neu B6 nam duoi B6-sys tren `err_system`, mot trong hai oracle bi cai sai; dung
G23-12c de xac dinh loi.
