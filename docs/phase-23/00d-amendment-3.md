# AMENDMENT 23-3 -- F3 wait semantics and exposure window

Ngay: 2026-08-14

Ly do: lo hong thiet ke phat hien khi dinh nghia API Lesson 23.1, truoc khi
chay bat ky ket qua fallback nao.

## F3 variant

Chot F3-a:

```text
Cho dung mot lan den refresh ke tiep trong cung block.
Neu lan thu hai accept, dung a_twin cua refresh do.
Neu lan thu hai van reject, dung F1 STICKY tai hang goc.
Neu khong con refresh trong block, dung F1 STICKY tai hang goc.
```

F3-a khong phai fallback doc lap; no la `F1 + mot lan thu lai bang thong tin
tuong lai`.

## Hai muc risk cua F3

Tat ca bang F3 phai bao cao ca hai:

```text
F3-idl  : risk cua quyet dinh sau khi cho; cua so cho coi nhu khong ton tai.
F3-exp  : risk co phoi nhiem trong luc cho:
          risk = w_wait * risk(F1) + (1 - w_wait) * risk(F3-idl)
          w_wait = delay_wait / (delay_wait + T_SYNC)
```

Neu ket luan chi giu o F3-idl ma khong giu o F3-exp, phai ghi ro trong abstract
va caption: ket qua chi la can duoi ly tuong.

## Gioi han moi

L17: ngu nghia "cho" gia dinh controller co the tri hoan quyet dinh. Trong
data plane that, luu luong van chay tren duong da cai. F3-exp chi la mo hinh
gan dung bang trong so thoi gian; no khong thay the closed-loop Phase 24.
