# AMENDMENT 23-84 -- LESSON 23.25 CLOSEOUT: BON PHEP KIEM CUOI, ROI DONG

Ngay ky : 2026-08-28
Moc     : sau `lesson-23-25-closeout-start`, truoc khi chay closeout lan dau
Loai    : TIEN DANG KY T14--T17 + QUY TAC DUNG + DINH CHINH DINH NGHIA
Parent  : `9982b1d`

## 1. Ngan sach gate

Lesson 23.25-closeout co DUNG 4 gate `G23-340..343`. Khong mo gate thu nam;
nhu cau moi la debt cua Phase 24/23.26, khong la mot vong 23.25 khac.

## 2. Dinh chinh `omega`

Ban plan ngoai workspace tung viet pha tron BIEN DO `rho=w*path+(1-w)*link`.
A077 muc 3 khoa pha tron PHUONG SAI:

```text
rho_l = mu_l + sigma*[sqrt(w)*(sum_p M[l,p] f_p)/sqrt(d_l)
                      + sqrt(1-w)*g_l]
```

Ban chinh thuc la A077: `Var(rho_l)=1` va `r_lm=w*k_lm`. Uoc luong
`sum(r*k)/sum(k^2)` chi dung voi ban nay. `PHASE_23_v3.md`/`MASTER_PLAN_v8.md`
khong co tren dia tai luc ky; correction repo-native va L163 la nguon ap dung
cho den khi file plan duoc dua vao workspace.

## 3. Bon phep kiem va dai khoa

T14/T16/T17 tinh tu artifact da ton tai, va ban review da cung cap con so
truoc khi module closeout chay. Vi vay M-283..285 va M-287..291 mang nhan
**[POST-HOC CONFIRMATION]**; chi T15/M-286 chua biet tai luc ky.

### G23-340 -- T14 jackknife theo link

```text
M-283 omega_full            [-0.05,+0.05]  [POST-HOC CONFIRMATION]
M-284 loo_range             [0.15,0.40]    [POST-HOC CONFIRMATION]
M-285 sign_flips_under_loo  TRUE           [POST-HOC CONFIRMATION]
```

Uoc luong chi dung k=0.5 khong chung host so voi k=0 khong chung host.
`sd_jackknife_descriptive` KHONG la SE; chi trich range/noise floor.

### G23-341 -- T15 tinh dung theo thoi gian

Chia tung run thanh 3 lat, dung median 16 cap null.

```text
M-286 b_hat_first_minus_later  [-0.05,+0.05]
WARMUP_DELTA_WARN              0.10
du doan verdict                STATIONARY_NO_TRIM_NEEDED
```

Dung HIEU, khong ti so. Nhanh W-A false: khong trim. Nhanh W-B true: chi
duoc tao MOT artifact trimmed rieng, skip 1/3 run; khong ghi de ban goc.
`abs(delta omega)<0.05` giu headline cu, nguoc lai trimmed la headline.

### G23-342 -- T16 paired null

```text
M-287 n_survives_strict_null   [0,6]/12       [POST-HOC CONFIRMATION]
M-288 mean_excess/k no-host    [-0.10,+0.10] [POST-HOC CONFIRMATION]
du doan verdict                NULLS_CANCEL_STRUCTURE
```

Dung TAT CA null partner khong chung host; khong chon mot cap sau khi xem.

### G23-343 -- T17 sensitivity `err(omega)`

```text
M-289 median relative effect       [+1%,+8%]   [POST-HOC CONFIRMATION]
M-290 worst relative effect        [+15%,+35%] [POST-HOC CONFIRMATION]
M-291 abs ratio delta khi sua r     [0,0.01]    [POST-HOC CONFIRMATION]
```

T17 la sensitivity CO DIEU KIEN tren pilot SNR measured T6, do lon SNR van
UNDECIDED theo A083. Moi cap duong dung `r_margin_at_requested_z` rieng.
NC-84-1 bat buoc: sua r phai lam muc err doi >3x nhung ratio doi <0.01.

## 4. Doi chung bat buoc

```text
PC-84-1 structured_matrix(w) -> omega_contrast=w, w={0,.25,.5,1}
PC-84-2 bom +0.6 vao moi cap chung host -> omega_contrast khong doi
PC-84-3 bom common ramp -> T15 fire
NC-84-2 stationary -> T15 khong fire
NC-84-3 structured_matrix(.5) -> T16 12/12 survive
NC-84-4 identity -> omega_contrast=0
NC-84-5 link_corr_matrix.json bit-for-bit khong doi
```

## 5. Quy tac dung NT50 -- khong dao logic

Truoc audit, ghi worst-case effect len KET LUAN. Neu <10%, khong mo audit.
Neu >=10%, audit CO THE duoc bien minh, khong phai bat buoc. T17 du kien
worst-case 15--35%, nen KHONG duoc dung NT50 de noi moi debt "duoi 10%".
Closeout dong PHAM VI negative-control; debt con can cho thiet ke moi duoc
CHUYEN sang 23.26/Phase 24, khong bi tuyen la da bien mat.

## 6. Phan loai NT51 va dau ra NT52

Lesson 23.25 la **[NEGATIVE CONTROL]**: generator mot-hop co path-coupling
true bang 0 theo cau tao. Cau hoi hop le la may do co bia signal hay khong.

Con so di vao paper: `omega_contrast`, LOO range, confound endpoint, va
conditional sensitivity bound T17. Moi so corrected/WLS khac bi cam.

## 7. Quy tac dong debt

Sau G23-340..343, L139..L162 dong TRONG PHAM VI Lesson 23.25. Muc nao la
rang buoc cho generator/path-level moi duoc chuyen sang 23.26/Phase 24 voi
provenance cu; khong mo lai nhu 23.25h. L163 khoa tham so hoa omega.

## 8. Bat bien append-only

Module closeout ghi artifact rieng. `link_corr_matrix.json` phai giu nguyen
whole-file SHA256 truoc/sau. Neu doi, dung commit va dieu tra.
