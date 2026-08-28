# LESSON 23.25 -- DONG VINH VIEN

> Trang nay thay ket luan 56, 58, 59, 60, 61, 62, 63. File cu giu nguyen
> lam audit trail. Cau hoi moi thuoc 23.26/Phase 24, khong la 23.25h.

Amendment : `A084-amendment-84.md`

Artifact  : `results/LIVE/phase-23/lesson_23_25_closeout.json`

Ma/Test   : `measurements/lesson_23_25_closeout.py` / 18 test

Nguon     : 15 run CLEAN, 599 mau/run, dt=0.2 s; khong do Mininet moi.

## 0. Mot cau

Lesson 23.25 la DOI CHUNG AM: clean omega contrast=-0.017, jackknife theo link
cho [-0.138,+0.143], va conditional target-cov sensitivity cua omega=0->1
lam decision error tang median 2.09%, worst 17.06% tren pilot SNR.

## 1. Bon phep kiem

```text
G23-340 T14  omega=-0.0173; LOO [-0.1381,+0.1427]
              NOT_IDENTIFIABLE_SIGN_UNDETERMINED
G23-341 T15  median-null slices +0.0432/+0.0119/-0.0085; delta +0.0414
              STATIONARY_NO_TRIM_NEEDED; nhanh W-A, khong trim
G23-342 T16  strict survives 3/12; excess/k no-host -0.0326,
              shared-host +0.0246; NULLS_CANCEL_STRUCTURE
G23-343 T17  target-cov +2.09% median, +17.06% worst
              legacy unit-variance +3.11%/+21.97% (lich su)
              NC: err level x3.383, ratio delta 0.000726 PASS
```

T15 chi loai common-null warmup lon. Omega theo lat +0.258/-0.162/-0.080,
nen khong duoc dien giai verdict nhu chung minh stationarity toan bo.

## 2. Ba con so duoc trich

1. `omega_contrast=-0.017`, LOO `[-0.138,+0.143]`: path-coupling khong
   phat hien duoc; `~0.15` la noise floor descriptive, khong la CI/SE.
2. Endpoint confound: r uA-uB/vC-vD `+0.599/+0.638`; shortfall
   `+0.902/+0.961`.
3. Conditional sensitivity target-cov: `+2.09%` median, `+17.06%` worst tai
   `clean@0.960|m(P1,P4)`. Bound dieu kien tren pilot SNR T6.

## 3. Tuyet doi khong trich

- `omega_hat=+0.0852` va corrected/deattenuated/WLS M1--M3.
- T5 unit-correlation `Var(m)=0.54--0.71` hoac V1=1.707/1.943 lam headline;
  dung T5b target-cov V1=1.389/1.719.
- `err=0.0519` tu tau_system; ACF margin do duoc cho 0.1566--0.1758.
- `sd_jackknife_descriptive` nhu SE, hay noise floor 0.143 nhu CI.
- magnitude SNR/D3 corrected; chung van UNDECIDED.

## 4. Dinh nghia va bai hoc

Omega 23.26 la variance-share voi `sqrt(omega)` va normalization
`1/sqrt(d_l)`, cho `r=omega*k`. Round-trip test bat buoc. Plan amplitude-share
ngoai workspace bi thay boi correction note/L163.

NT50: worst target-cov 17.06% >10%, nen khong duoc noi moi audit le ra bi cam.
Closeout dung vi pham vi negative-control da tra loi, khong vi effect bang 0.
NT51/NT52 khoa lesson type va paper-number-first cho vong sau.

## 5. Ban giao 23.26/Phase 24

```text
R0 variance-share omega + round-trip
R1 path 3 hop pha collinearity host/path
R2 process/host map co dinh qua omega
R3 T14/T16 moi omega
R4 rho 0.2s/1.0s + tx_packets_delta + common clock
R5 shortfall moi omega
R6 >=4 dose; r(uA,uB)<0.15 tai omega=0
R7 p(rho>K09*0.995)<0.05 moi link/omega
R8 omega>=0.3 la heuristic 2x noise floor, KHONG la power theorem
```

## 6. D3 va pham vi

G23-339 cho phep chon `clean@0.960` o muc argmax hau kiem. D1/D2/D3
corrected van UNDECIDED. Debt L139..L162 dong trong 23.25; constraint thiet
ke moi chuyen 23.26/Phase 24 voi provenance, khong mo 23.25h.

## 7. Tai tao va bat bien

```bash
PYTHONPATH=. .venv/bin/pytest -q test/test_lesson_23_25_closeout.py
PYTHONPATH=. .venv/bin/python -m measurements.lesson_23_25_closeout \
  --campaign results/RAW/phase-23/aoi_v7_campaign \
  --corr-artifact results/LIVE/phase-23/link_corr_matrix.json \
  --final-audit results/LIVE/phase-23/lesson_23_25_final_audit.json \
  --out results/LIVE/phase-23/lesson_23_25_closeout.json
```

NC-84-5 PASS: `link_corr_matrix.json` SHA256 truoc/sau cung la
`6a753c1a6e7791682b74ebd8e0eef5a4ab8f451614f5c05a02f5b55835e8e291`.
