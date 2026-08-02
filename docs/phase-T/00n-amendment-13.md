# AMENDMENT 13 -- Phase T

Ngay: 2026-08-02

## Phat Hien

Khoi C' cung-seed da chay du 45/45 diem, `failed_rows = 0`.

```text
V-T5a_delegation       seen=40 pass=40 fail=0
V-T5a_phase_l_digest   seen=40 pass=40 fail=0
V-T4a_ca_operational   seen=45 pass=45 fail=0
V-T6b_rho_bias         seen=45 pass=45 fail=0
V-T5b_same_seed        n=40 mean_r=+0.0033 sd_r=0.0039 mean_gate=OK sd_gate=OK
```

V-T5b' pass theo nguong da dang ky:

```text
|mean(r_i)| = 0.00331 < 0.005
sd(r_i)    = 0.00400 < 0.010
```

Nhung dau cua lech la co he thong:

```text
n = 40
mean(r_i) = +0.0033087
SE(mean) = 0.0006321
t = +5.234
so diem duong/am = 36/4
```

Lech nay la cong tinh, khong phai nhan. Doi bien `Delta_i = r_i * q_L,i` lam
dai luong phang hon nhieu so voi `r_i`:

```text
rel theo rho:
  rho=0.700   +0.65321%
  rho=0.850   +0.41474%
  rho=0.925   +0.14889%
  rho=0.980   +0.10664%

Delta theo rho:
  rho=0.700   +0.01301 ms
  rho=0.850   +0.02270 ms
  rho=0.925   +0.01428 ms
  rho=0.980   +0.01312 ms

rel theo mode:
  h2          +0.19173%
  poisson     +0.47001%

Delta theo mode:
  h2          +0.01880 ms
  poisson     +0.01276 ms
```

Uoc luong preregistered tu C' truoc G3:

```text
Delta_hat = +0.01578 ms
SE        =  0.00230 ms
n         = 40
t         = +6.859
q_L range = 1.261 .. 13.227 ms
```

Dien giai: Phase T do tre cao hon Phase L mot offset thiet bi cong tinh khoang
16 us moi goi. Nguyen nhan hop ly la vong lap gui Phase T lam them viec so voi
Phase L: tra cuu `rho(t)`, chi so lich, metadata, va/hoac them mot lan goi dong
ho.

## Anh Huong

Oracle quasi-static dung model fit tu Phase L:

```text
MODEL_PATH = results/phase-L/link_model_v2_fit.json
```

Do do:

```text
err_qs = q_do_boi_Phase_T - f_Phase_L(rho)
```

se thua huong offset `+Delta_hat`. Offset nay cung bac voi san "bo qua duoc"
da dung o T.0, nen phai dang ky truoc khi chay G3.

## Xu Ly Preregistered Truoc G3

A13.1. Bao cao `err_qs` theo hai dang; dang mac dinh cho dien giai la dang da
hieu chinh:

```text
err_qs_raw_ms       = q_T - f_L(rho)
err_qs_corrected_ms = q_T - f_L(rho) - Delta_hat
```

A13.2. `Delta_hat = 0.01578 ms` chi duoc uoc luong tu khoi C' `a = 0`. Khong
duoc uoc luong lai tu G3.

A13.3. `SE(Delta_hat) = 0.00230 ms` duoc cong vao thanh phan he thong cua thanh
sai so `err_qs`.

A13.4. Neu ket luan dat/khong dat cua bat ky o nao doi dau giua
`err_qs_raw_ms` va `err_qs_corrected_ms`, bao cao ca hai va noi ro o nao bi
doi dau. Khong chon dang co loi hon.

A13.5. Gia dinh dang kiem: offset la hang so per-packet, do o `a = 0`, va giu
nguyen khi `rho(t)` bien thien. Day la threat to validity. Kiem duoc mot phan
bang G2 controls `a > 0` va sentinel trong G3.

## Provenance Truoc G3

30 hang C' moi co `env` va deu ghi `git_dirty = true`, vi worktree co state/raw
ket qua chua commit khi chay. Co che provenance hoat dong dung: no da phat hien
commit hash khong mo ta day du trang thai sinh du lieu.

15 hang dau C' chay truoc A12 nen chua co `env`. Chung duoc chap nhan vi
`V-T5a_phase_l_digest` pass bit-exact, dieu chi kha thi tren interpreter live
tuong thich CPython <= 3.11.

Truoc G3:

```text
git status --porcelain phai TRONG
git tag phase-T-G3-start tai commit bat dau G3
```

Runner `stage=main` tu choi chay neu fingerprint dau phien co
`git_dirty=True`.

## Phat Hien Phu

Mo hinh nhieu duoc xac nhan tren 45 diem C':

```text
ca_operational_z  n=40 mean=+0.945 sd=0.952 max|z|=2.421
rho_bias_z        n=45 mean=+0.121 sd=0.971 max|z|=1.999
vt5b_z            n=45 mean=+0.121 sd=0.962 max|z|=2.536
```

`sd(z) ~= 1` cho ca ba cong, dung voi ky vong cua cac mo hinh SE da dang ky.

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-08-02
