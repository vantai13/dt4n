# KIEM TOAN KE THUA -- Phase 22

Ngay: 2026-08-13

## 1. Phan loai L1-L10 cua 21R

| ID | Gioi han | Phase 22 lam gi |
|---|---|---|
| L1 | Ground truth la bang tra do day, khong phai chan ly vat ly | Ghi pham vi -> P23-C |
| L2 | 48.1% phuong sai e_model la nhieu do | Ghi pham vi va dung trong mo hinh tien doan L22.6 |
| L3 | Bao dam cho AR(1) tong hop, tau = 1.0 | Da dong mot phan o 22.6: AR(1) giu tren tau in [0.5, 5.0], gom tau=2.87; tai that de Phase 23 |
| L4 | Bao dam chinh xac thuoc Variant A; B la xap xi headline | Ghi pham vi, bao cao A/B song song |
| L5 | Bao phu khong giu sau chon loc (0.0913 -> 0.1214) | Giai quyet o 22.4 |
| L6 | Chung nhan la cap, khong dong thoi tren K=4 | Giai quyet o 22.1 va 22.3 |
| L7 | Duong co dinh chi co 1 ho tai ngoai poisson | De Phase 23 |
| L8 | Ti so tuoi 2.17 la quan sat, chua la dinh luat | Da dong o 22.6: la gioi han bao hoa R_inf khi A/rms_em lon; cbr xac nhan cho vo |
| L9 | Cac o van hanh chia trajectory theo seed -> p-value lac quan | Ghi pham vi (R22-6) |
| L10 | Xep hang tuyet doi ke thua gia dinh residual-bound cua 20R | De Phase 23 |

## 2. Gioi han phat hien moi -- khong co trong so 21R

Hai muc duoi day duoc phat hien khi soan Phase 22, sau khi 21R da dong.
Chung khong duoc them nguoc vao `docs/phase-21R/99-gate-decision.md` theo
luat ve sinh so 4. Chung duoc dang ky tai day.

### L11 -- Nguon goc AoI khac topology

```text
Ngay phat hien : 2026-08-13
Noi dung : AoI (d_sync = 51 ms, T = 500 ms) do tren cau Ditto (host srv1,
           sC-eth3) o giai doan topo 3 duong (9 canh). No duoc dung cho
           topology_v7 (8 link).
Bien ho  : AoI la tinh chat cua kenh quan sat (Ditto <-> collector), khong
           phai cua data plane. Chuyen la hop le.
Dinh luong: chenh 11% so link => q_hat lech ~4.6% bang do nhay muc 3.
Phase 22 : Khong do lai. Chi ghi pham vi + bang do nhay.
Phase 23 : P23-A do lai truc tiep tren topology_v7, kem CI.
```

### L12 -- AoI gia dinh dong nhat tren 8 link

```text
Ngay phat hien : 2026-08-13
Noi dung : y_hat = c_fresh[old] dich ca vector rho 8 chieu di cung mot luong.
           Vong poll that cho AoI trai theo link.
Huong    : rms_es(z) lom => Jensen => E_l[rms_es(z_l)] <= rms_es(z_bar)
           => gia dinh dong nhat la bao thu, khong phai lac quan.
Phase 22 : Da dong o 22.7. U1/U2 khong tao hieu ung >2% tren o chinh;
           PC4 bat duoc cho vo va dinh luong dieu kien sd(d) << tau.
```

### L13 -- Dinh luat ti so tuoi can AoI dong nhat

```text
Ngay phat hien : 2026-08-13
Noi dung : R_inf(tau) cua Lesson 22.6 duoc dan voi mot tuoi chung z cho ca
           vector rho 8 link. Khi AoI trai qua link rat rong, ti so B3/B0
           khong con theo luat nay.
Do duoc  : poisson@0.925
             U0/U1/U2 (sd(d) <= 14.79 ms): ratio B3/B0 = 2.0736 - 2.1099
             PC4      (sd(d) = 165.36 ms): ratio B3/B0 = 3.4604
Dieu kien: sd(d) << tau. Voi U1, sd(d)/tau = 0.0148; voi PC4 = 0.165.
Phase 23 : Neu lich poll that co sd(d) lon, mo rong dinh luat ratio sang
           trong-so-theo-link / phi tuyen cost quanh cliff.
```

## 3. Ba nhan cho moi so ke thua

| So | Gia tri | THANG | MUC | TAP HANG | Nguon |
|---|---:|---|---|---|---|
| q_hat(B0) | 11.5878 | cost ms | margin (cap) | test block, sigma=0.0096, poisson@0.925 | conformal_poisson_0.925.json |
| q_hat(B1) | 15.6348 | cost ms | margin | nhu tren | nhu tren |
| q_hat(B2) | 19.6461 | cost ms | margin | nhu tren | nhu tren |
| q_hat(B3) | 24.3222 | cost ms | margin | nhu tren | nhu tren |
| ti so B3/B0 | 2.0990 | khong thu nguyen | margin | nhu tren | tinh tu tren |
| ti so 8 o van hanh | 2.1766 | khong thu nguyen | margin | duong van hanh, sigma theo o | 99-gate-decision.md |
| rms_em | 2.1418 | cost ms | margin | cua so 800..n, 3 seed | decomposition_*.json |
| rms_es(0.550) | 16.8149 | cost ms | margin | nhu tren | nhu tren |
| cov_e(0.550) | -14.7942 | cost ms^2 | margin | nhu tren | nhu tren |
| A (bien do AR1) | 25.8855 | cost ms | margin | khop tren 13 diem z | tinh moi, muc 4 |
| c = 1+2cov/es^2 | 0.89345 | khong thu nguyen | margin | nhu tren | tinh moi, muc 4 |
| pair_ok | 0.98757 | -- | margin | toan tap poisson@0.925 | calib_set parquet |
| viol marginal | 0.09132 | -- | margin | TEST | usefulness_*.json |
| viol given accept | 0.12144 | -- | margin | TEST, kappa=1 | nhu tren |
| corr(s_margin, m_hat) | 0.1122 | -- | margin | TEST | nhu tren |
| P(m_true<0 given accept) | 0.03074 | -- | decision | TEST, kappa=1 | nhu tren |
| P(accept, kappa=1) | 0.28354 | -- | decision | TEST | nhu tren |
| neo err | 0.220835 | -- | decision | sawtooth, khai bao | anchor.json |
| neo err tren test | 0.222399 | -- | decision | sawtooth, TEST | usefulness_*.json |

### Dinh chinh ke thua

```text
PHASE_22.md (du thao) muc 1.2 ghi corr(s_margin, m_hat) = 0.1165.
Artifact ghi 0.1122 (poisson@0.925, TEST). Khong o nao cho 0.1165.
Con so 0.1122 duoc dung. Day la vi du dau tien cho thay quy tac ba nhan
la can thiet, khong phai hinh thuc.

PHASE_22.md muc 1.1 ghi bao phu khong hieu chinh = 0.9^4 = 0.656.
Dung phai la 0.9^3 = 0.729 (K-1 = 3 so sanh, moi khang dinh la hieu voi a1).
Da sua o GS-12 va PC22-2.
```

## 4. Mo hinh tien doan tai khop tu artifact 21R

```text
Ly thuyet AR(1): Var(rho(t) - rho(t-z)) = 2*sigma^2*(1 - exp(-z/tau))
                 => rms_es(z) = A * sqrt(1 - exp(-z/tau))

Khop tren 13 diem z cua decomposition_poisson_0.925.json (tau = 1.0):
    A                   = 25.8855 ms
    A tren 13 diem      = min 25.850, max 25.928 (bien thien 0.30%)
    cov_e / rms_es^2    = -0.05327 (bien thien 0.15%)
    c = 1 + 2*cov/es^2  = 0.89345
    rms_em              = 2.1418 ms (phang theo z: bien thien 0.15%)

Mo hinh day du:
    rms_tot(z; tau)^2 = rms_em^2 + c * A^2 * (1 - exp(-z/tau))
Sai so toi da so voi rms_total do duoc tren 13 diem: 0.21%

Gia thuyet cua Lesson 22.6:
    A, c, rms_em doc lap voi tau.
    Day la thu duoc kiem, khong duoc coi la su that truoc khi chay.
```

## 5. Ket luan audit

Phase 22 ke thua nen Phase 21R nhung khong viet lai lich su 21R. L11 va L12
duoc dang ky moi tai day. Hai sua nghi trong nhat truoc khi ky la:

1. Thu tuc sau chon loc phai la diem bat dong, khong phai cong thuc mot buoc.
2. Mo hinh Lesson 22.6 phai dung cov_e va du doan R(tau) hinh chuong.

## 6. Cap nhat sau Lesson 22.6

`cert/tau_sweep.py` da chay tren du lieu that cho tau
`{0.5, 1.0, 2.0, 2.87, 5.0}` voi block_s = 5*tau.

```text
poisson@0.925:
  A      = 25.976 -> 26.175, span 0.762%
  c      = 0.88837 -> 0.89770, span 1.046%
  rms_em = 2.1339 -> 2.1482, span 0.664%
  R      = 1.9779 -> 2.0990 -> 2.1432 -> 2.0834 -> 2.0076
  R_inf(1.0) = 2.1614
```

Ket luan:

```text
L3: dong mot phan. Bao dam AR(1) khong con chi tau=1.0; no giu tren
    [0.5, 5.0], gom tau=2.87 cua tai loi that. Van chua dong cho tai
    khong-AR(1).

L8: dong. Ratio ~2.17 la gia tri bao hoa cua
    sqrt((1-exp(-z3/tau))/(1-exp(-z0/tau))) khi A/rms_em lon.
    PC22-1 cbr@0.700 cho A/rms_em ~0.02 va ratio ~1.0, dung la cho
    ly thuyet tien doan se vo.
```

## 7. Cap nhat sau Lesson 22.7

`cert/aoi_profiles.py` da so sanh U0/U1/U2/PC4 tai cung tuoi trung binh bang
cach can giua offset tung link.

```text
poisson@0.925:
  U1/U0 qhat ratio = 0.9962, 0.9989, 1.0042, 1.0013
  U2/U0 qhat ratio = 1.0139, 0.9998, 0.9998, 1.0016
  PC4/U0           = 0.5649, 0.7875, 0.8715, 0.9311
  coverage         = 0.9053 - 0.9087
```

Ket luan:

```text
L12: dong. Voi lich poll thuc te sd(d) <= 15 ms va tau=1 s, Jensen gap
     du kien ~0.07%, nho hon san nhieu qhat. Khong co hieu ung thuc te nao
     lon hon 2% tren o chinh.

L13: mo. Dinh luat ti so tuoi cua Lesson 22.6 giu cho U0/U1/U2 nhung vo o
     PC4, nen dieu kien ap dung phai ghi la sd(d) << tau / AoI gan dong nhat.
```
