# AMENDMENT 23-4 -- Replace the brittle decision-delay gate

Ngay: 2026-08-14

Ly do: G23-5 cu `E[delay] <= T/2 = 250 ms` sat mep do cau truc sawtooth.
Bien binh quan cua sawtooth la 252.5 ms, nen gate cu do mot tai nan so hoc
hon la tinh chat he thong.

## G23-5 moi

Ba menh de duoi day deu phai dung:

```text
(a) 0 < E[w | reject] < E[w | marginal] = 252.5 ms
    Xac nhan reject set lech ve tuoi gia, nen cho ngan hon bien.

(b) max(w) <= T_SYNC + dt = 505 ms
    Chan cung cua F3-a.

(c) w tinh tat dinh tu z_s:
    |w - ((0.550 - z_s) + 0.005)| < 1e-9
    Doi chung thiet bi do.
```

`252.5 ms` suy ra truoc tu `z_s` co 100 gia tri deu:

```text
E[w] = 0.555 - E[z] = 0.555 - 0.3025 = 0.2525 s
```

Khong dung nguong 250 ms cu trong gate Lesson 23.1.
