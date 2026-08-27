# AMENDMENT 23-81 -- DONG LESSON 23.25 NHU DOI CHUNG AM

Ngay ky : 2026-08-27

Moc     : sau A080/23.25d, TRUOC khi chay T5b/T9/T10/T11

Loai    : TIEN DANG KY phep dong lesson; chi them artifact, khong sua T0..T8

## 1. Phat bieu ket qua khoa truoc

Tren generator mot-hop campaign 23.8, he so ghep theo duong `omega` KHONG
NHAN DANG DUOC vi `k` va shared-host cong tuyen trong tap co cau truc. Contrast
duy nhat co `k>0` ma khong chung host la bon cap `k=0.5`; so voi cac cap NULL
khong chung host, contrast mo ta du kien cho `omega` gan 0. Contrast nay van
co the confound theo loai link/thang thoi gian, nen KHONG duoc goi la uoc
luong causal sach neu khong co thiet ke path-level.

Nhan lesson khoa vinh vien sau A081:

```text
DOI CHUNG AM + HIEU CHUAN SAN NHIEU + XAC DINH DIEU KIEN TIEN QUYET 23.26.
KHONG phai phep do path-coupling.
```

## 2. Du doan bang so

| ID | Dai luong | Dai khoa |
|---|---|---:|
| M-270 | T5b target-cov ratio measured/independent, ca 6 margin | 0.85 .. 1.00 |
| M-271 | T5b target-cov ratio omega=1, cap KE | 1.388 .. 1.390 |
| M-272 | T9 so cap vuot tran independent-residual | >= 2 |
| M-273a | T10 Spearman(log pair-process dose, r), 6 cap shared-host | >= +0.80 |
| M-273b | T10 Spearman(log total-endpoint dose, r) | bao cao; khong cham |
| M-274 | T11 median sd(measured)/sd(offered), core tai clean@0.960 | <= 0.60 |

M-270/271 den tu review ben ngoai da tinh sau khi xem artifact/meta, nen mang
nhan **[POST-HOC CONFIRMATION]**. M-272/273/274 chua duoc chay trong workspace
tai thoi diem ky file nay.

## 3. Dinh nghia khoa

### T5b -- covariance theo sigma target

Doc `sigma_target` median tu meta. `Sigma = D R D`; moc independent la
`D^2`. T5 cu dung R giu nguyen. T5b la phan tich theo THIET KE TARGET; khong
duoc goi la covariance empirical neu measured SD khong bang target.

### T9 -- tran attenuation

Voi fit nugget hop le dung `s=signal_fraction`; fit invalid co intercept>1
project ve `s=1` de tao tran cao nhat. Neu `|r|>sqrt(s_a*s_b)`, ket luan
model-free dung la **thanh phan residual lag-0 khong doc lap/cross-correlated**.
Chi goi no la measurement noise khi co them bang chung host shortfall.

### T10 -- hai dose, khong chon sau khi xem

```text
pair_process_dose = n_concurrent[a] + n_concurrent[b]
total_endpoint_dose(host) = tong n_concurrent cua MOI channel co host la endpoint
```

M-273a cham pair-process dose theo review; M-273b bat buoc in de to cao neu
quan he bien mat khi tinh toan bo workload that cua host.

### T11 -- censoring/saturation

So offered 10 ms da aggregate dung ve 200 ms voi measured. In theo moi
run/link: mean, sd, sd_ratio, p(measured>0.99), p(measured>=p99 offered).
M-274 chi cham `clean@0.960` va 4 core link; cac cell khac van in day du.

## 4. Nhánh phu kin

```text
M-272 MISS -> nugget fit khong du de ket luan residual correlated;
              split-half + tx_packets bat buoc o 23.26.
M-273a MISS -> co che pair-process dose bi bac; chi giu host shortfall nhu
               instrument artifact, khong goi dose-response.
M-273a HIT nhung M-273b yeu/nguoc -> dose-response phu thuoc cach dinh nghia;
               bao cao ca hai, khong phat bieu nhan qua tong host load.
M-274 HIT -> nghi saturation/censoring; R7 bat buoc.
M-274 MISS -> khong co bang chung censoring theo gate nay; R7 van la monitor,
              khong la dieu kien hạ rho.
```

## 5. Quy tac D3 -- khong gia dinh dieu can chung minh

Chi duoc goi `SNR_measured` la can duoi vo dieu kien neu T9 KHONG vi pham
independent-residual ceiling va T11 KHONG co saturation. Neu T9 co vi pham,
residual tuong quan co the vao covariance margin theo ca hai dau; neu T11 fire,
TX counter con bi nen. Trong hai truong hop do, D1/D2/D3 corrected van
`UNDECIDED`; D3 measured duoc giu lam pilot budget, khong goi la dinh ly.

## 6. Gate

```text
G23-327  contrast 2x2 k x shared-host + omega descriptive
G23-328  T5b target-covariance 6 margin
G23-329  T9 attenuation ceiling
G23-330  T10 hai dose-response
G23-331  T11 censoring/saturation
G23-332  phan xu D3 va khoa R1--R7
G23-333  NC: T0..T8 canonical khong doi khi them T9..T11 artifact rieng
```

## 7. Rang buoc 23.26 du kien

R1 path-level 3 hop; R2 map/process count co dinh qua omega; R3 chay lai
T8/T9/T10 moi omega; R4 logger 0.1 s + `tx_packets_delta`, tao chuoi 0.2 s va
split-half; R5 shortfall moi omega; R6 giam pair-process dose hsrc/hdst <=200
va gate `r(uA,uB)<0.15` tai omega=0; R7 monitor `p(rho_measured>0.99)<0.05`.
