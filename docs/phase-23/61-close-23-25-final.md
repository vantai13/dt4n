# LESSON 23.25 -- KET LUAN CUOI

Amendment : `A081-amendment-81.md`

Artifact  : `results/LIVE/phase-23/lesson_23_25_final_audit.json`

Trang nay THAY THE ket luan cua `56-link-corr-matrix.md` va cac lop doi nhan
58--60. Cac file cu giu nguyen lam lich su audit, khong con la headline.

## Mot cau

Tren generator mot-hop, omega khong nhan dang duoc; contrast it confound nhat
gan 0, va ba lop host contention, nugget/residual, saturation da duoc bien
thanh rang buoc thiet ke bat buoc cho 23.26. Lesson nay la DOI CHUNG AM, khong
phai phep do path-coupling.

## Ba con so duoc phep dua vao paper

```text
omega contrast khong chung host = -0.0173
  (4 cap k=0.5 mean +0.0364 vs 10 cap k=0 mean +0.0451)

r(uA,uB) = +0.5986 > sqrt(s_uA*s_uB)=0.4338 -> vuot 1.380x
r(vC,vD) = +0.6376 > sqrt(s_vC*s_vD)=0.3308 -> vuot 1.927x

Spearman(log pair-process dose,r)=+0.6571; total-endpoint=+0.6000, n=6
  -> M-273 MISS; KHONG duoc noi dose-response nhan qua
```

T5b target-covariance bo sung: measured/identity=0.8803--0.9577; tai
omega=1 la 1.389233 cho cap ke va 1.719092 cho cap cheo. M-270/271 HIT.

## Ba thu KHONG duoc trich tu lesson nay

1. `omega_hat=+0.0852` va moi ban corrected/deattenuated: khong nhan dang.
2. `Var(m)=0.54--0.71` cua T5 cu: sai tang don vi; dung T5b 0.88--0.96.
3. `err=0.0519` tu `tau_system=27.67 s`: dung ACF margin do duoc,
   `err=0.1566--0.1758` tai 0.369 s.

## T11 va D3

M-274 MISS: median `sd(measured)/sd(offered)` cua core tai clean@0.960 la
0.6992, khong dat <=0.60. Tuy nhien monitor tran cung da khai bao FIRE:
`p(rho_measured>0.99)=0.4741--0.5042`, va p99 measured dong tai ~1.0094
trong khi offered p99=1.1838--1.2062. Day la bang chung saturation/censoring,
nhung khong duoc doi ten thanh M-274 HIT.

T9 bac gia thuyet residual doc lap; T11 cho thay TX service bi nen. Vi vay
lap luan "SNR measured luon la can duoi" khong hop le. D3 measured=0.3752
chi giu lam pilot budget; **D1/D2/D3 corrected van UNDECIDED**. Day la phan
xu cuoi, khong phai cho phep doi nhan tiep.

## Rang buoc bat buoc truoc 23.26

- R1 path-level 3 hop; R2 process map co dinh qua omega; R3 lap T8/T9/T10.
- R4 logger 0.1 s + `tx_packets_delta`, aggregate 0.2 s va split-half.
- R5 shortfall theo moi omega.
- R6 pair-process dose hsrc/hdst <=200 va `r(uA,uB)<0.15` tai omega=0.
- R7 `p(rho_measured>0.99)<0.05` tren moi link/moi omega; neu fail thi ha
  core target hoac do demand bang backlog+drop.

## Gia tri dong gop

Lesson khong do duoc omega. No chung minh thiet ke hien tai khong the tach
path coupling khoi shared-host contention, chi ra residual cross-correlated
va TX saturation, va khoa chinh xac cac sua doi can co cho phep do ke tiep.
Do la gia tri cua mot doi chung am duoc thuc hien nghiem tuc.

## Tai tao va output man hinh

```bash
PYTHONPATH=. .venv/bin/python -m measurements.lesson_23_25_final_audit \
  --campaign results/RAW/phase-23/aoi_v7_campaign \
  --corr-artifact results/LIVE/phase-23/link_corr_matrix.json \
  --nugget-artifact results/LIVE/phase-23/acf_nugget.json \
  --out results/LIVE/phase-23/lesson_23_25_final_audit.json
```

```text
[final] omega contrast no-shared-host=-0.0173
[final:T5b] measured ratio 0.8803..0.9577 adjacent omega1=1.3892
[final:T9] violations=['uA-uB', 'vC-vD'] verdict=LAG0_RESIDUAL_IS_CROSS_CORRELATED_PROVEN
[final:T10] Spearman pair-dose=+0.6571 total-dose=+0.6000 n=6
[final:T11] core@0.960 median sd_ratio=0.6992 M274_hit=False hard_ceiling=True saturation_evidence=True
```

NC append-only: SHA256 canonical T0..T8 truoc/sau deu la
`188472781e66848a33cc7e55d040b397362a77f521308e2f3e8c642f28298a49`.
