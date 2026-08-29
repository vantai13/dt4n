# LESSON 23.25c -- KIEM TOAN NHAN DANG VA DUNG CU

Tien dang ky : `A079-amendment-79.md`

Artifact     : `results/LIVE/phase-23/link_corr_matrix.json::T8_identifiability`

Probe        : `results/LIVE/phase-23/host_confound_probe.json`

Ma           : `measurements/link_corr_matrix.py`,
               `measurements/host_confound_probe.py`

Ngay do      : 2026-08-27; 15 run CLEAN, 599 mau/run; KHONG do Mininet moi

## 0. Ket qua mot dong

```text
G23-315  PASS         k x shared-host cong tuyen hoan hao trong 12 cap k>0
G23-316  PASS/MISS    in du 28 n_eff; ca hai dai M-258/M-259 deu MISS cao
G23-317  PASS         PC thu hoi omega=0.5 -> 0.5208; NC identity -> 0
G23-318  ADJUDICATED  M1 chi2/dof=46.48; M3=9.41, ca hai thieu bien
G23-319  ADJUDICATED  shortfall xac nhan endpoint contention, nhung K3 vi M3 MISS
G23-320  PASS         T0..T7 canonical SHA256 giong nhau, diff=0
G23-321  PASS         scale-S cho moi WLS; M1/M3 scaled CI deu chua 0
G23-322  PASS         M3 == M1-bo-2; bac thang 28/26/24 cap da in
G23-323  FAIL         nugget/tau/CI hop le 4/8 link; 4 core fit invalid
G23-324  ADJUDICATED  DEFAULT_MIXED_OR_INVALID
G23-325  ADJUDICATED  SNR corrected UNDECIDED; D3 measured dang treo
G23-326  PASS         K3 default invalid tu to cao trong artifact
```

Phan quyet A079: **K3_DEFAULT_USE_M1**. A080 nang cap may kiem va tu to cao
**K3_DEFAULT_INADMISSIBLE_DISCLOSED**: point estimate `omega=-0.1022` nam
ngoai khong gian tham so. Sau scale-S, CI chua 0 nhung point estimate van
khong admissible. Lesson 23.25 chi la **doi chung am / hieu chuan san nhieu**.
Quyet dinh D3 do duoc duoc GIU LICH SU nhung dang TREO vi SNR khử nugget
khong tinh hop le duoc (`G23-325`).

## 1. Ba loi va bang chung

### E1 -- khong nhan dang duoc `omega` theo duong

| lop `k` | so cap | chung host | ti le |
|---:|---:|---:|---:|
| 0 | 16 | 6 | 0.375 |
| 0.5 | 4 | 0 | 0.000 |
| 0.7071 | 8 | 8 | 1.000 |

Trong tap co cau truc, lop `k=0.7071` va shared-host trung khit 8/8, con lop
`k=0.5` la 0/4. Them run cua cung thiet ke khong pha duoc cong tuyen. He thong
sinh tai mot-hop cung ap dat `omega` that bang 0: byte nap `uA` khong chay tiep
qua `ac`.

### E2 -- `n_eff` cu khong phai phep do

`T7.neff_pair` dung `max(tau_pred)`, suy ra 32.5--44.9. T8 thay bang tong
Bartlett tu ACF cua chinh CSV, cua so tam giac 1/4 run, khong gia dinh AR(1).
Ket qua thuc nghiem cao hon du doan rat nhieu:

| ho cap | n | min | mean | max | dai A079 | phan quyet |
|---|---:|---:|---:|---:|---:|---|
| fast-fast | 6 | 660.3 | 764.4 | 871.0 | [khong cham] | mo ta |
| slow-fast | 16 | 786.7 | 1253.7 | 1784.5 | 150--500 | MISS cao |
| slow-slow | 6 | 832.6 | 1179.8 | 1537.7 | 40--150 | MISS cao |

Ten "slow" o day den tu `tau_pred_s`, con ACF do tren `rho_measured` giam
nhanh hon du doan. Vi vay ca 393 cua bootstrap lan 32.5--44.9 cua max-tau deu
khong duoc dung lam `n_eff` thay the. Tuy nhien `n_eff` lon cung lam lo ro
model misspecification qua `chi2/dof`, khong tu dong tao ra mot CI vat ly hop le.

### E3 -- fit hai giai doan khong truyen sai so nen

T8 fit mot lan tren 28 cap:

```text
Fisher-z(r_lm) = b + omega*k_lm (+ covariate) + error_lm
weight         = n_eff_lm - 3
```

No thay cho phep tru `b_hat` roi LS qua goc. He so khuếch dai an cua cach cu
la `sum(k)/sum(k^2) = 1.531`.

## 2. WLS chung M1/M2/M3

| model | `omega` | `sd_formal` | `S` | `sd_scaled` | `chi2/dof` |
|---|---:|---:|---:|---:|---:|
| M1 `b+omega` | -0.1022 | 0.0173 | 6.817 | **0.1180** | 46.478 |
| M2 `+shared_host` | -0.2475 | 0.0197 | 6.233 | **0.1229** | 38.846 |
| M3 `+host_x_slow` | +0.0391 | 0.0179 | 3.067 | **0.0549** | 9.407 |

`S=sqrt(max(1,chi2/dof))` la quasi-WLS overdispersion diagnostic, khong sua
model sai. M1 scaled CI95 cua omega = **[-0.333,+0.129]**; M3 =
**[-0.068,+0.147]**, ca hai chua 0. M3 giam `chi2/dof` nhung van MISS.

A080 chung minh M3 **chinh la** M1 bo `uA-uB,vC-vD`: delta `b=-6.94e-18`,
delta `omega=+3.47e-17`. Do do `host_x_slow` khong duoc trich nhu bang chung
thong ke; no la can gat loai hai diem. Bang chung co che van la shortfall probe.

Hai doi chung ma moi deu dat:

```text
PC-25c-1  structured_matrix(omega=0.5) -> omega_hat=0.520813  FIRE
NC-25c-2  identity matrix              -> omega_hat=0         PASS
            sd report = sd tu (X'WX)^-1 = 0.0173076, sai so 0
```

NC dung nghiem co intercept. Cong thuc `1/sqrt(sum(w*k^2))` chi dung cho fit
qua goc, nen khong duoc dung lam doi chung cho WLS chung.

## 3. Host confound probe -- phan xu co che `+0.6`

> **DINH CHINH PHASE D' (2026-08-29).** Shortfall probe xac nhan thanh phan
> sinh ra giua offered va measured tai endpoint, nhung **shared endpoint mot
> minh KHONG du** de giai thich `+0.6`. Audit du 28 cap cho mean r=+0.0171 o
> bon cap chung host ma ca hai channel co `N_bar` nho, va +0.0364 o bon cap
> ca hai low-sigma/high-N ma khong chung host. Gia thuyet hien tai la H4
> endpoint x configuration-bundle interaction (post-hoc); phan quyet xac nhan
> cho cell C nam o `docs/phase-D/00-preregistration.md`.

Probe doc dung cot `rho_offered` (cot 2, khong phai timestamp cot 1), gop
10 ms -> 200 ms, tinh trong tung run roi gop Fisher-z.

| cap | host | offered | measured | shortfall |
|---|---|---:|---:|---:|
| uA-uB | hsrc | +0.1736 | +0.5986 | **+0.9020** |
| vC-vD | hdst | -0.1840 | +0.6376 | **+0.9612** |
| ac-ad | hA | +0.0269 | +0.0358 | +0.0060 |
| bc-bd | hB | -0.0076 | +0.0314 | +0.1753 |

Generator/RNG khong sinh `+0.6`: offered cua hai cap bien khong cung dau va
khong gan +0.6. Phan dat duoc (`measured/offered`) cua hai tien trinh cung
endpoint lai tut cung luc rat manh. Probe xac nhan **thanh phan endpoint trong
mot tuong tac**, khong xac nhan H1 endpoint-only. `~750` virtual flow dong thoi
o link bien la marker cua configuration bundle; chua duoc goi la co che nhan
qua cho toi khi cell C duoc chay theo prereg Phase D'.

Day dong `G23-312` o muc co che. Nhung phan quyet tong cua A079 van la K3 vi
K1 doi ca M-265 HIT VA M-264 HIT; M-265 vuot cao dai (+0.902 > +0.85) va
M-264 MISS. Khong noi long gate sau khi xem so.

## 4. Do ACF cua chinh margin

`tau_system=max(tau_link)` cu cho `r(z=0.369)=0.9868`, `err=0.0519`. A080 noi
suy log giua lag 0.2/0.4 s de do DUNG tai `z=0.369 s`:

| cap duong | `r_margin(0.4s)` | `err` zero-mean |
|---|---:|---:|
| P1-P2 | 0.8768 | 0.1597 |
| P1-P3 | 0.8514 | 0.1758 |
| P1-P4 | 0.8571 | 0.1723 |
| P2-P3 | 0.8764 | 0.1599 |
| P2-P4 | 0.8814 | 0.1566 |
| P3-P4 | 0.8681 | 0.1654 |

Muc err tham chieu cu thap hon khoang 3.0--3.4 lan. Truong
`T6.err_reference_zero_mean_sheppard=0.051868` va hai `err_at_omega0=0.048336`
duoc GIU de bao toan T0..T7, nhung DA BI THAY THE ve dien giai boi
`T8.margin_acf_measured.*.err_zero_mean_sheppard=0.1566--0.1758`.

## 5. Doi pham vi 23.25/23.25b

```text
RUT LAI  "n_eff that = 32.5--44.9" va rang buoc run >=415 s cua L142.
          ACF Bartlett do duoc cho 660--1785, min slow-slow=832.6.

RUT LAI  moi cach doc `omega_hat_corrected=-0.0828` nhu mot uoc luong co SE
          hop le. Uoc luong hai giai doan khong truyen sai so nen.

KHONG THAY bang CI M3 nhu mot headline: M3 co chi2/dof=9.41, MISS gate fit.

GIU       L143: percentile bootstrap block ngan bi lech va khong duoc bao cao.
GIU LICH SU D3 do tren rho measured; TREO quyet dinh thi hanh den khi co
          SNR khử nugget hop le (A080/G23-325).
GIU       dai so Var(m) theo omega; day la wiring/co che, khong la phep do.

THAY NHAN Lesson 23.25 = doi chung am / noise-floor calibration cua generator
          mot-hop, khong phai phep do path-coupling.
```

## 6. No va duration 23.26

```text
L139     DONG theo huong bo bootstrap khoi, khong chay lai de cuu CI do.
L142     DONG/RETRACT max-tau; bo rang buoc 415 s.
G23-312  DONG co che bang shortfall endpoint; model residual van la L148.
```

Theo quy tac A079, `min n_eff slow-slow = 832.6 >= 60`, nen duration cho truc
omega la **120 s**. Day khong co nghia 120 s du cho moi metric khac cua 23.26.

## 7. Rang buoc bat buoc cho 23.26

1. Path-level traffic phai di hsrc -> hdst qua tron mot duong 3 hop, pha cong
   tuyen giua chia se host va chia se duong.
2. So tien trinh/ban do host giu co dinh qua moi omega.
3. Chay T8 o moi omega: artifact endpoint gan bat bien, thanh phan theo duong
   tang theo omega dat vao.
4. M3 hien tai KHONG duoc mo rong bang covariate post-hoc; 23.26 la thiet ke
   moi co doi chung duong, khong phai bai tap ep phan du ve 0.
5. R4: ghi rho o ca 0.2 s va 1.0 s; R5: do shortfall tai moi omega.

## 9. A080 -- nugget va bac thang do nhay

### 9.1. Scale-S va bac thang

```text
28 cap                         omega=-0.1022 +/-0.1180  chi2/dof=46.478
bo {uA-uB,vC-vD}              omega=+0.0391 +/-0.0557  chi2/dof= 9.709
bo them {bd-vC,bd-vD}         omega=+0.0276 +/-0.0299  chi2/dof= 2.445
```

Day la sensitivity ladder [DIAGNOSTIC], khong chon bac cuoi lam headline.
Omega khong tach duoc khoi 0 o ca ba bac sau scale-S.

M4 post-hoc lien tuc cho `corr(r_measured,r_shortfall)=0.9465`, he so
shortfall `+0.6870 +/-0.0501` scaled, `omega=-0.0202 +/-0.0416`,
`chi2/dof=5.663`. M6 cho offered `t_scaled=1.373`. Tat ca mang nhan
**DIAGNOSTIC -- POST-HOC, NOT HEADLINE**.

### 9.2. Nugget N/T

| link | `1-lambda` | CI95 | `lambda` | CI95 | `tau_do` s | CI95 |
|---|---:|---:|---:|---:|---:|---:|
| uA | 0.381 | [0.300,0.483] | 0.619 | [0.517,0.700] | 11.90 | [8.46,16.67] |
| uB | 0.494 | [0.387,0.628] | 0.506 | [0.372,0.613] | 13.04 | [9.46,17.49] |
| vC | 0.358 | [0.299,0.427] | 0.642 | [0.573,0.701] | 10.09 | [7.96,12.84] |
| vD | 0.306 | [0.258,0.358] | 0.694 | [0.642,0.742] | 9.39 | [7.10,12.31] |
| ac/ad/bc/bd | INVALID | -- | -- | -- | raw 1.70--2.91 | -- |

Bon fit loi co slope am nhung ngoai suy signal fraction `1.036--1.194 > 1`.
Theo A080, phan quyet la **DEFAULT_MIXED_OR_INVALID**, khong phai N gan nhat.
Nugget bi xac nhan tren rieng bon link bien, nhung khong co correction hop le
cho toan ma tran. Diagnostic project core ve lambda=0 cho omega through-origin
`0.0852 -> 0.1662`, dong thoi clip `uA-uB,vC-vD`; khong la can tin cay.

Fit nugget cua ca 6 margin cung invalid (signal fraction raw 1.05--1.16), nen
`SNR_corrected=UNDECIDED`. D3 khong bi lat sang D2, nhung cung chua duoc xac
nhan sau attenuation. Can cua so rho 1.0 s/path-level 23.26 de dong no.

## 8. Tai tao

```bash
.venv/bin/python -m pytest test/test_link_corr_matrix.py \
  test/test_host_confound_probe.py -q

.venv/bin/python -m measurements.host_confound_probe \
  --campaign results/RAW/phase-23/aoi_v7_campaign \
  --out results/LIVE/phase-23/host_confound_probe.json

.venv/bin/python -m measurements.link_corr_matrix \
  --campaign results/RAW/phase-23/aoi_v7_campaign \
  --baseline-artifact results/LIVE/phase-23/link_corr_matrix.json \
  --host-probe results/LIVE/phase-23/host_confound_probe.json \
  --out results/LIVE/phase-23/link_corr_matrix.json
```
