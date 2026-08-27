# AMENDMENT 23-79 -- LESSON 23.25c: KIEM TOAN NHAN DANG VA `n_eff`

Ngay ky : 2026-08-27

Moc     : sau tag `lesson-23-25b-complete`, TRUOC khi chay phep do moi cua
          Lesson 23.25c

Loai    : SUA PHAM VI ket luan + TIEN DANG KY kiem toan dung cu offline

Du lieu : 15 run CLEAN da co trong `results/RAW/phase-23/aoi_v7_campaign`;
          KHONG do Mininet moi

## 1. Vi sao mo

Ra soat nguoc Lesson 23.25/23.25b phat hien ba loi cau truc:

```text
E1  Trong 12 cap co `k > 0`, chi bao "chung host" trung khit voi lop
    `k = 0.7071` (8/8 chung host) va `k = 0.5` (0/4 chung host). Hai nguyen
    nhan cong tuyen hoan hao trong tap co cau truc, nen `omega_hat` khong
    nhan dang duoc nhu "tuong quan theo duong".

E2  `neff_pair` cua 23.25b dung `max(tau)`. Phuong sai tuong quan cheo theo
    Bartlett phu thuoc tong tich `rho_X(k) * rho_Y(k)`, nen phai DO ACF cua
    chinh hai chuoi thay vi chon `tau` cham nhat.

E3  Uoc luong hai giai doan tru `b_hat` roi LS qua goc khuếch dai sai so cua
    `b_hat` voi he so `sum(k)/sum(k^2) = 1.531`, nhung thanh sai so cu khong
    truyen phuong sai nay. Phai fit chung `z = b + omega*k` tren 28 cap.
```

Lesson nay doi nhan 23.25 thanh **doi chung am / hieu chuan san nhieu** tren
mot he co `omega` that bang 0 theo kien truc sinh tai mot-hop. Khong xoa hay
sua cac ket qua T0..T7 da dong.

## 2. Du doan bang so -- khoa truoc khi chay

| ID | Dai luong | Dai khoa |
|---|---|---:|
| M-258 | `n_eff` Bartlett DO DUOC, cap cham-nhanh | 150 .. 500 |
| M-259 | `n_eff` Bartlett DO DUOC, cap cham-cham | 40 .. 150 |
| M-260 | `omega_hat` tu WLS chung M3 | -0.05 .. +0.15 |
| M-261 | `sd(omega_hat)` tu WLS chung M3 | 0.02 .. 0.06 |
| M-262 | he so `host_x_slow` | +0.45 .. +0.85 |
| M-263 | `chi2/dof` M1 (`b + omega`) | 2.0 .. 20.0; PHAI lon |
| M-264 | `chi2/dof` M3 (them `host_x_slow`) | 0.4 .. 2.5; PHAI gan 1 |
| M-265 | `r_shortfall(uA,uB)` | +0.30 .. +0.85 |

Khai bao: cac dai tren den tu ban kiem toan ben ngoai do nguoi dung cung cap;
chung chua duoc chay lai tren workspace nay tai thoi diem ky file.

## 3. Doi chung bat buoc

```text
NC-25c-1  T0..T7 cua artifact moi GIU NGUYEN bit-for-bit theo JSON canonical
          so voi artifact 23.25b. Ket qua moi chi nam trong T8.

PC-25c-1  WLS chung tren ma tran gia `omega = 0.5` -> thu hoi omega trong
          [0.45, 0.55].

NC-25c-2  WLS chung tren ma tran don vi -> omega gan 0. `sd` phai khop dung
          nghiem giai tich cua ma tran normal co intercept `(X'WX)^-1`.
          Luu y: cong thuc `1/sqrt(sum(w*k^2))` chi dung cho fit QUA GOC;
          ap no cho fit chung co intercept la sai dai so, nen khong dung lam
          gate gia.
```

## 4. Ba kich ban phu kin khong gian ket qua

```text
K1  M-265 HIT VA M-264 HIT
    -> xac nhan co che nghen tien trinh sinh tai tren hsrc/hdst; doi nhan
       Lesson 23.25 thanh doi chung am; bao cao omega tu M3.

K2  M-265 MISS (`r_shortfall < 0.30`) nhung `r_measured(uA,uB)` van >= 0.40
    -> co che o switch/OVS hoac instrument, khong du bang chung quy cho host;
       covariate doi ten `shared_endpoint_artifact`, mo no truy nguyen.

K3  MOI truong hop con lai, ke ca M-263 MISS hoac M-264 MISS
    -> nhanh mac dinh: khong them covariate vao ket luan chinh; chi thay
       `n_eff` bang Bartlett do duoc va thay uoc luong hai giai doan bang WLS
       chung M1.
```

Quyet dinh duration 23.26 cung khoa truoc:

```text
min n_eff cham-cham >= 60  -> 120 s du cho truc omega
20 <= min n_eff < 60      -> 240 s
min n_eff < 20            -> giu rang buoc 415 s
```

## 5. Gate Lesson 23.25c

```text
G23-315  bang cong tuyen `k x chung host`, in du 28 cap
G23-316  `n_eff` Bartlett do duoc, in du 28 cap
G23-317  PC-25c-1 thu hoi `omega = 0.5`
G23-318  WLS chung: he so, sd, CI95, chi2/dof cua M1/M2/M3
G23-319  phan xu K1/K2/K3 tu host confound probe + M3
G23-320  NC-25c-1: T0..T7 canonical diff = 0
```

## 6. Dieu khong doi

- Quyet dinh D3: mo 23.26 rut gon tren `clean@0.960`.
- Moi so va moi truong trong T0..T7.
- Ket luan dinh tinh: testbed hien tai phu hop `omega` gan 0.
- `L143`: khong bao cao percentile bootstrap khi `block/tau < 3`.

## 7. Rang buoc moi cho Lesson 23.26

```text
R1  Generator path-level phai gui hsrc -> hdst qua tron mot duong 3 hop de
    pha confound giua chia se host va chia se duong.
R2  Ban do host va so tien trinh tren moi host giu co dinh qua moi omega.
R3  Chay lai T8 o moi omega: `host_x_slow` gan bat bien, he so omega tang
    tuyen tinh theo omega dat vao.
```
