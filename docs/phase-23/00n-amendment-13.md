# AMENDMENT 23-13 -- B4 is B3 by monotone ranking invariance

Ngay: 2026-08-14

Ly do: trong thiet ke API Lesson 23.3, nhan ra B4 variance proxy khong tao mot
baseline doc lap neu proxy chi la ham don dieu cua tuoi.

## Dong nhat dai so

Mo hinh sigma theo tuoi co dang:

```text
sigma_hat(z)^2 = rms_em^2 + cA2 * (1 - exp(-z/tau))
```

Voi `tau > 0` va `cA2 > 0`, `sigma_hat(z)` tang don dieu theo `z`. B3 xep theo
`-z`, B4 xep theo `-sigma_hat(z)`. Hai score nay co cung thu hang, vi bang xep
hang bat bien duoi bien doi don dieu tang.

## Xu ly

1. B4 duoc giu trong bang ket qua theo quy tac khong bo baseline, nhung bao cao
   la `DEGENERATE_WITH_B3`.
2. Du doan B4p trong prereg cu bi vo hieu cho Lesson 23.3.
3. Gate moi:

```text
G23-10b  B4 va B3 cho accept mask giong bit-for-bit tai moi coverage khop.
         Neu khac, sigma_hat dang phu thuoc them bien ngoai z hoac cai dat sai.
```
