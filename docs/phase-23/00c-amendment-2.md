# AMENDMENT 23-2 -- Primary system-risk scale is regret

Ngay: 2026-08-14

Ly do: Lesson 23.0 do duoc `P(a* = P1) = 0.656141`. Duong tinh dung 65.6%
lam thang `err` bi nen trong dai hep; day la phep do truoc 23.1, khong phai
ket qua fallback.

## Quyết định

Thang risk CHINH cho phat bieu he thong cua Phase 23 la:

```text
regret = E[cost_true(a_chon) - cost_true(a*)]  [ms]
```

Ly do:

```text
err la bien 0/1, khong phan biet sai 0.1 ms voi sai 5 ms.
Khi mot static path dung 65.6%, err cua cac policy co the gan nhau trong khi
thiet hai van hanh rat khac nhau.
```

## Ràng buộc

`err` van phai duoc bao cao trong moi bang vi no noi tiep Phase 21R/22.
`sla_rate` va `d_sla` van phai duoc bao cao theo P18.

Khong dong prediction nao bi xoa hoac doi sau khi thay ket qua.
