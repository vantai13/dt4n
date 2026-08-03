# AMENDMENT 18 -- Phase T / T.6e paired-by-seed error bars

Ngay viet: 2026-08-03
Trang thai: T.6 confirmatory, T.6b baseline, T.6c noise-floor, va T.6d
cell-level restatement da xong.

## Boi Canh

T.6d cho thay 8/8 o khong phai cbr co `mean_dyn` am:

```text
sign test p = 0.0078125
Wilcoxon W+ = 0, p = 0.0078125
mean khong trong so = -0.0327 ms
KTC 95% thuc nghiem = [-0.0513, -0.0141] ms
```

Nhung thanh sai so bao thu trong T.6d van co mau thuan:

```text
sqrt(mean(SE_tot^2)) / sd(mean_dyn giua 8 o) = 4.522
```

Chan doan: `SE_tot = sqrt(SE_stat^2 + SE_C^2)` gia dinh hai ve doc lap, trong
khi khoi C va khoi chinh dung cung bo seed `{11,12,13,14,15}`. Thanh phan
ngau nhien cua lich la chung theo seed va can duoc triet tieu bang thiet ke
ghep cap, giong bai hoc Amendment 11.

## Trang Thai Phan Tich

A18 la **EXPLORATORY**. Cac ket qua T.6/T.6b/T.6c/T.6d van phai duoc bao cao
nguyen ven. A18 chi sua thanh sai so theo dung thiet ke ghep cap; khong duoc
thay doi gia tri `mean_dyn`.

## Phep Tinh Khoa Truoc Khi Chay

Voi moi o `o = (mode, rho_bar)` va seed `s`:

```text
d(o,s) = mean_{a,tau} err_qs_corrected_main(o,s,a,tau)
         - err_qs_corrected_C(o,s)

mean_dyn_paired(o) = mean_s d(o,s)
SE_paired(o)       = sd_s(d(o,s)) / sqrt(5)
```

Kiem bat bien bat buoc:

```text
abs(mean_dyn_paired(o) - mean_dyn_T6d(o)) < 1e-9
```

Neu bat bien fail, dung lai. A18 chi duoc doi thanh sai so, khong duoc doi
uoc luong.

## Du Doan Truoc Khi Chay

```text
R1  SE_paired trung binh tren 8 o khong phai cbr : 0.015--0.030 ms
R2  ti_so mau thuan sau khi ghep cap             : 0.7--1.5 va < 2
R3  So o co |t_paired| > 2                       : 6--8 / 8
R4  mean gop sau ghep cap                        : -0.033 +/- 0.008 ms
R5  cbr@0.98 van la o manh nhat                  : co
```

## Bao Cao Bat Buoc

T.6e phai bao cao:

```text
mode, rho, n_seed, mean_dyn, sd_paired, se_paired, t_paired, ci95
```

Va summary:

```text
mean SE_paired tren 8 o khong phai cbr
so o |t_paired| > 2
mean gop 8 o
ti_so mau thuan moi
cbr@0.98 tach rieng
```

## Nguyen Tac Moi

NT-L20. Neu thiet ke thuc nghiem co ghep cap theo seed, thanh sai so phai dung
hieu ghep cap truoc khi tinh `sd`; khong dung two-sample SE doc lap.

NT-L21. Moi thay doi thanh sai so sau unblind phai co test bat bien chung minh
uoc luong trung tam khong doi.

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-08-03
