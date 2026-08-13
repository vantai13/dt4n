# AMENDMENT 1 -- Phase 22

Ngay: 2026-08-13

Trang thai: sau Lesson 22.3, da cham du lieu Phase 22 v3 that. Khong sua cac
thu tuc confirmatory da prereg trong `00-preregistration.md`.

## A1. P3c -- bridge half-normal cho s_sim

Quan sat Lesson 22.3:

```text
qhat_maxscore / (1.645 * rms(s_sim)) = [0.9100, 0.9124, 0.9060, 0.9079]
```

Dieu nay khong phai bang chung rang `1.645*rms` la du doan absolute dung cho
tat ca score. No chi noi: voi cung mot score `s_sim`, ratio theo z-bin kha on
dinh. Tu day, P3c duoc them vao prereg:

```text
1.645*rms la bridge phu thuoc score. Voi s_sim, chi bao cao ratio diagnostic;
khong dung no de thay qhat conformal, khong dung de sua gate confirmatory.
```

## A2. Thu tuc exploratory: studentized max

Ly do them: Lesson 22.3 cho thay maxscore bi chi phoi boi slot 1 trong accept,
nhung qhat chung lai phai bao phu slot 3. Co che la slot heterogeneity: ranking
va error cung den tu rho, nen rank xa hon co score lon hon.

Thu tuc de xuat, danh dau EXPLORATORY:

```text
Chia calib theo block, seed 7001, thanh fold1/fold2.
Uoc luong sigma_j tren fold1 cho tung slot j.
s_std = max_j |e(a_j)-e(a1)| / sigma_j
Lay c = qhat_alpha(s_std) tren fold2.
Final qhat_j = c * sigma_j.
Evaluate tren test nhu cac thu tuc khac.
```

Quy tac khoa:

```text
Khong dung studentized max lam confirmatory cho Phase 22.3.
Neu chay o lesson sau, phai bao cao la exploratory / post-data.
Khong thay ranking claim cua bonferroni, sidak, maxscore da prereg.
```

Du doan truoc khi chay studentized max:

| Dai luong | Du doan |
|---|---|
| c | 1.15 - 1.30 |
| qhat_j(B0) slot1 / qhat_21R(B0) | 1.20 - 1.30 |
| acceptance tai kappa=1 | 0.175 - 0.205 |
| simultaneous coverage | 0.895 - 0.910 |
| expected acceptance ranking | studentized > sidak > bonferroni > maxscore |

## A3. Khong thay doi ket luan confirmatory

Sau amendment, ket luan confirmatory cua Lesson 22.3 van la:

```text
bonferroni, sidak, maxscore: simultaneous coverage pass
uncorrected: negative control collapses
slot1: reproduces 21R exactly
```

