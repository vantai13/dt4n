# AMENDMENT 23-80 -- LESSON 23.25d: NUGGET, OVERDISPERSION, ADMISSIBILITY

Ngay ky : 2026-08-27

Moc     : sau artifact 23.25c/A079, TRUOC khi chay `acf_nugget.py`

Loai    : TIEN DANG KY phep phan xu N/T + SUA CACH BAO CAO uncertainty

Du lieu : tai su dung 15 run CLEAN; KHONG do Mininet moi

## 1. Khai bao nhung gi DA BIET truoc khi ky

Da biet tu artifact A079:

```text
M1 omega=-0.1022, sd_formal=0.0173, chi2/dof=46.478
M3 omega=+0.0391, sd_formal=0.0179, chi2/dof=9.407
host_x_slow=+0.6895; shortfall uA-uB/vC-vD=+0.902/+0.961
margin ACF tai lag lam tron 0.4 s = 0.839--0.873
```

Review ben ngoai DA tinh sau khi xem artifact: scale-S, M3 tuong duong bo hai
cap, bac thang bo 2/4 cap, va cac model M4--M6 dung `r_shortfall`. Vi vay moi
so M-266..M-269 ben duoi mang nhan **[DIAGNOSTIC -- POST-HOC]**, khong duoc
doi thanh headline.

Trong mot diagnostic truoc amendment, workspace da in ACF tai vai lag cho
mot so link (vi du lag-1 uA~0.464, uB~0.522, vC~0.389, vD~0.440). Chua fit
nugget/tau va chua co artifact/CI, nhung phep do N/T KHONG con blind hoan
toan. Moi dai nugget phai ghi ro tiet lo nay (`L144`).

## 2. Quy tac uncertainty khoa truoc

Voi moi WLS trong T8:

```text
S = sqrt(max(1, chi2/dof))
sd_scaled = sd_formal * S
CI95_scaled = beta +/- 1.96*sd_scaled
```

Day la **quasi-WLS overdispersion diagnostic**, khong sua model misspecification
va khong bien point estimate omega am thanh admissible. Headline cua nhanh K3
la M1 voi CI scaled, kem co `point_estimate_in_parameter_space`.

## 3. M3 va bac thang do nhay

Bat buoc in canh nhau:

```text
M3 tren 28 cap voi dummy host_x_slow
M1 tren 26 cap bo {uA-uB, vC-vD}
```

Neu `b`/`omega` lech > 1e-10 thi equivalence FAIL. `host_x_slow` chi sang tren
hai diem, nen he so/t cua no KHONG la bang chung co che. Bang chung co che chi
lay tu host probe.

Bac thang diagnostic khoa danh sach truoc:

```text
L0  28 cap
L1  bo uA-uB, vC-vD
L2  bo them bd-vC, bd-vD
```

In moi bac, khong chon bậc co chi2 dep lam headline.

## 4. Diagnostic lien tuc M4--M6 -- da xem so

| ID | Dai luong | Dai sau-khi-xem | Nhan |
|---|---|---:|---|
| M-266 | he so `r_shortfall` cua M4 | +0.40 .. +0.95 | POST-HOC |
| M-267 | chi2/dof M4 | 1.0 .. 8.0 | POST-HOC |
| M-268 | omega M4 | -0.12 .. +0.12 | POST-HOC |
| M-269 | he so offered M6, `abs(t_scaled)` | < 2 | POST-HOC |

M4 = `b + omega*k + beta_s*r_shortfall`; M5 = `b + beta_s*r_shortfall`;
M6 = `b + beta_s*r_shortfall + beta_o*r_offered`. Chung la huong dong no,
khong thay K3/A079.

## 5. Phep do nugget khoa truoc

```text
DT = 0.2 s
FIT_LAGS = [1,2,3,4,5,6,8,10,15,20]
Chi fit diem ACF > 0.02; can >=3 diem; slope phai am.
log ACF(k) = log(1-lambda) - k*DT/tau
Bootstrap 2000 lan, resample 15 run, seed 23880; percentile CI95.
```

Hinh bat buoc in ACF lag 0..20 cho 8 link va duong fit lag>=1.

Ba nhanh phu kin:

```text
N_NUGGET
  tat ca fit hop le VA median(1-lambda) cua 4 link bien <= 0.50.
  -> bao cao raw + deattenuated omega; sua L140 thanh can DUOI co dieu kien;
     tinh SNR corrected tu nugget margin; 23.26 them cua so 1.0 s.

T_TAU_PRED_WRONG
  tat ca fit hop le VA min(1-lambda) qua 8 link >= 0.85.
  -> khong nugget; tau_measured thay tau_pred cho dien giai moi.

DEFAULT_MIXED_OR_INVALID
  moi truong hop con lai, gom fit khong hop le, signal fraction (0.5,0.85),
  hoac cac link bat dong.
  -> raw la headline; deattenuated chi la can tren diagnostic; D3 treo neu
     corrected SNR cham/vuot 1.0.
```

## 6. Khử làm loãng va SNR

Neu N hoac DEFAULT:

```text
r_deatt(a,b) = r_measured(a,b) / sqrt((1-lambda_a)(1-lambda_b))
```

In ma tran truoc/sau va co neu tri tuyet doi vuot 1. Omega deattenuated la
diagnostic vi shortfall confound van ton tai.

SNR corrected dung nugget cua CHINH cost-margin: fit ACF margin voi cung lag,
roi `SNR_corrected = SNR_measured / sqrt(1-lambda_margin)` theo tung cap duong.
Quyet dinh lay median qua cung 30 `cell x pair`, nguong D1/D2 giu 0.25/1.00.

Margin `r(z=0.369)` noi suy log giua lag 1 va 2, KHONG lam tron 0.4 s.

## 7. Admissibility -- L145 nang cap

Nhanh mac dinh phai in:

```text
point_estimate_in_parameter_space = 0 <= omega <= 1
scaled_ci_contains_zero
default_branch_admissible
```

Neu point estimate ngoai [0,1], nhanh phai tu to cao
`DEFAULT_BRANCH_INADMISSIBLE_DISCLOSED`; khong duoc im lang gan nhan hop le.

## 8. Gate

```text
G23-321  S, sd_scaled, ci95_scaled cho moi WLS T8
G23-322  M3 == M1 bo 2 cap + bac thang 28/26/24 cap
G23-323  lambda/tau/CI tung link + hinh ACF
G23-324  phan xu N/T/DEFAULT
G23-325  SNR corrected va D3/D2
G23-326  default branch tu kiem admissibility
```

Rang buoc 23.26: giu R1--R3; neu N them R4 (rho 0.2 s va 1.0 s), moi nhanh
them R5 (shortfall tai moi omega). Duration 120 s giu nguyen.
