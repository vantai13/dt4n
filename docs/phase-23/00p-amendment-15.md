# AMENDMENT 23-15 -- Break-even argmin gate and effective K

Ngay: 2026-08-15

Ly do: audit Lesson 23.3 cho thay ket luan cu "tin hieu khong nam o tuoi" la
sai. B3/AoI co tin hieu ve do tin cay argmin, nhung tin hieu nay chua vuot
nguong hoa von cua fallback P1. Can them mot gate dong nhat thuc va mot threat
to validity moi.

## G23-21 -- break-even argmin identity

Pham vi: F2 STATIC, thang `err`.

Voi moi selector va coverage `c`:

```text
delta_vs_anchor = err_system(selector, c) - err_anchor
delta_vs_anchor = P(reject) * [P(a_twin=a*|reject) - P(a*=P1|reject)]
```

Gate PASS neu identity khop trong `1e-9`.

Ket qua tai coverage 0.78 tren `poisson@0.925`, C3 static:

| Selector | delta_vs_anchor | reconstructed | abs error |
|---|---:|---:|---:|
| B1_random | +0.026395742 | +0.026395742 | 1.4e-17 |
| B3_aoi | +0.012560829 | +0.012560829 | 1.6e-17 |
| B2_constant_gap | -0.012984857 | -0.012984857 | 1.2e-17 |
| C3_conformal | -0.012868849 | -0.012868849 | 3.5e-18 |

Ket qua: `G23-21 PASS`.

## G23-21b -- gamma closure mechanism

Pham vi: C3(gamma), F2 STATIC, coverage 0.78.

Muc tieu: adjudicate gia thuyet "C3(gamma) noi B2 tai `gamma=0` voi B3 khi
`gamma -> infinity`".

Ket qua:

```text
qhat slots = 3
keys       = z_bin,m_hat_bin
qhat monotone theo z trong moi m_hat_bin = True
qhat monotone row-level theo z_s         = False

b2_to_b3_interpolation_supported           = False
gamma_max_within_0.002_of_B3               = False
no_gamma_gt2_beats_gamma1                  = True
paired_gamma0.5_minus_gamma1_CI_contains_0 = True
```

Bang chinh:

| gamma | err_system | gap vs B3 | overlap B3 |
|---:|---:|---:|---:|
| 0.0 | 0.209413821 | -0.025545686 | 0.780129 |
| 0.5 | 0.208991793 | -0.025967714 | 0.786193 |
| 1.0 | 0.209529829 | -0.025429678 | 0.791863 |
| 2.0 | 0.209549830 | -0.025409677 | 0.801941 |
| 3.0 | 0.211097932 | -0.023861575 | 0.810031 |
| 5.0 | 0.214762174 | -0.020197333 | 0.822329 |
| 20.0 | 0.243768089 | +0.008808581 | 0.839433 |
| 100.0 | 0.248062372 | +0.013102865 | 0.839494 |

Dien giai: gia thuyet noi B2-B3 bi bac cho implementation C3 hien tai, vi C3
condition theo `z_bin x m_hat_bin`; khi gamma lon, ranking bi cau truc cell/slot
cua `q_hat` chi phoi, khong phai tuoi thuan B3.

## G23-20 -- chance agreement la moc bat buoc

Moi phat bieu dang "argmin mat thong tin" hoac "X dong thuan voi chan ly" phai
bao cao kem moc chance agreement tren cung tap con:

```text
agreement_independent = sum_j P(a_twin=j) * P(a_star=j)
kappa = (agreement - agreement_independent) / (1 - agreement_independent)
```

Cam dung hang so bia nhu "dong xu 0.5" hoac "deu 1/K" lam moc. Ly do: tai
Lesson 23.3, con so `0.4989` gan 0.5 la trung hop theo phan phoi bien, khong
phai ket qua cua K=4.

## Co che thay the

Ket luan cu bi rut lai:

```text
SAI: tin hieu khai thac duoc nam chu yeu o m_hat, khong nam o tuoi.
```

Ket luan moi:

```text
Tuoi co tin hieu that ve do tin cay argmin:
  kappa separation(B3) = 0.166247
  kappa separation(C3) = 0.524540

Nhung B3 chua vuot nguong hoa von:
  P(a_twin=a*|rej) = 0.716509
  P(a*=P1|rej)     = 0.659415
```

Vay B3 lam reject co hai, khong phai vi vo tin hieu, ma vi fallback P1 tao mot
nguong cung. Selector yeu khong nhan "mot phan loi ich"; no co the nhan loi ich
am neu chua day `P(a_twin=a*|rej)` xuong duoi nguong P1.

## L21 -- action space hieu dung

Phan phoi bien tai Lesson 23.3:

```text
a_twin_distribution = [0.619176866, 0.000000000, 0.369222369, 0.011600766]
a_star_distribution = [0.659723542, 0.000014001, 0.333091984, 0.007170473]
```

Threat moi:

```text
L21  Khong gian hanh dong hieu dung la 3 trong khi thiet ke danh nghia co
     K=4 action, tuc K-1=3 score slots. Neu action chet co the loai hop le,
     so so sanh hieu dung co the la 2 thay vi 3. Chi phi cua slot/action chet
     chua duoc luong hoa.
```

Amendment nay khong doi ket qua cu; no doi cach doc co che va them gate bao ve
artifact Lesson 23.3.
