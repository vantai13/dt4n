# PHASE 20 - GATE DECISION: PASS

Ngay: 2026-07-27
Tag: `phase-20-complete`
Nguoi quyet dinh: DT4N owner
Executor: Codex

Tai lieu nay dong bang Gate 20. Sai sot phat hien sau tai lieu nay phai ghi vao
`docs/phase-20/99b-erratum.md`, khong sua nguoc file nay.

## 1. Cau Hoi

RQ-A: Co ton tai mot che do van hanh that trong do loi cua twin gay sai quyet
dinh du thuong xuyen va du dat de mot co che chung nhan trust gate co gia tri?

Phase 20 khong de xuat chinh sach moi. No la phep do mo ta, duoc thiet ke de
co the giet nhanh huong RQ-A neu tin hieu khong ton tai.

## 2. Dieu Da Hua Truoc Khi Do

Pre-registration: `docs/phase-20/00-preregistration.md`

Amendments:

```text
00b-amendment-1.md
00c-amendment-2.md
00d-amendment-3.md
00e-amendment-4.md
00f-amendment-5.md
00g-amendment-6.md
00h-amendment-7.md
```

San khau dong bang tai tag `phase-20-stage-frozen`. Sau tag do chi do, khong
sua san khau.

## 3. San Khau

Topology: butterfly 2x2, `K=4`, 6 nut, 8 link, moi link duoc dung boi dung
2/4 duong. Link nam tren moi duong khong the doi argmin, nen san khau buoc
phai co chia se theo tap con.

Luu luong: flow-level, Poisson arrival, Pareto `kappa=2.5`, sinh boi
FlowEngine thuong tru.

Mo hinh duoc xac nhan tren ba tham so doc lap, khong fit lai tu du lieu
decision-error:

```text
sigma = sqrt(rho_mean * r_f / C): 8/8 link, |log2| <= 0.20
tau ~= 1.06 * S_min / r_f: 8/8 link, |log2| <= 0.28 tren dai 2.4-32 s
kappa_hat tu ACF hop le: 2.22-2.56 vs cau hinh 2.50
```

Bat bien phan giai: `tau(dt=10ms)` vs `tau(dt=2ms)` lech 0.003-0.037% tren
4 link loi. Ket luan: phep do dang do he thong, khong do san cua thuoc.

## 4. Diem Van Hanh

Chu ky sync `0.5 s`, `d_sync = 0.051 s`, tao AoI rang cua. Tuoi trung binh
thuc te la `0.305 s`, khong phai `0.298 s`, vi thoi diem quyet dinh nam tren
luoi 10 ms va tuoi nhan 50 gia tri roi rac `{0.06, ..., 0.55}`.

Hieu chuan SLA tu hoi tu sau 2 vong:

```text
w_loss = T_delay / T_loss = 1451.3766
T_delay = 14.5138 ms
T_loss = 0.010
optimal_violation = 15.000%
tie_rate = 0.0000%
```

Hieu chuan nay duoc dong bang tu trace0 va dung lai cho trace1-4.

## 5. Ket Qua Chinh

Nam trace Mininet doc lap theo seed sinh tai `0/1/2/3/4`, cung dung hieu chuan
dong bang:

```text
metric   trace0   trace1   trace2   trace3   trace4 | mean     SD_giua  SE_trong  SE_mean  CI95_mean_t(df=4)
err      0.17286  0.19047  0.18522  0.18609  0.17702| 0.18233  0.00719  0.00863   0.00502 [0.16838, 0.19628]
d_sla    0.07287  0.08552  0.08439  0.08222  0.07194| 0.07939  0.00650  0.00458   0.00355 [0.06952, 0.08926]
```

`SD_giua / SE_trong = 0.83` cho `err` va `1.42` cho `d_sla`. Neu chi bao
cao CI bootstrap trong-trace thi van hep gia ro ret. Day la bang chung thuc
nghiem cho nguyen tac: bootstrap tai lay mau du lieu, khong tai lay mau thi
nghiem.

Co che tren trace0:

```text
risk_ratio = 8.94
P(error | crossed) = 36.1%
P(error | not crossed) = 4.0%
share_errors_crossed = 86.3%
regret_on_error = 33.67 ms
twin_violation = 22.09%
optimal_violation = 14.80%
```

So voi Phase 14A, SNR tang tu `0.38` len `16.5`.

## 6. Gate

```text
G1 err CI subset [0.05, 0.40]          PASS  [0.16838, 0.19628]
G2 d_sla lower >= 0.03                 PASS  lower = 0.06952 = 2.32x threshold
G3 err(z) tang don dieu                PASS  8/8 adjacent deltas CI99.4 > 0
G4 NC1-NC4                             PASS
G5 P3' risk ratio >= 3.0               PASS  8.94
G6 sim vs real                         PASS  4/4 qualitative criteria
```

Ket luan: **GATE 20 PASS**. Huong RQ-A kha thi.

Nghia nghien cuu: ton tai mot che do van hanh that, do tren testbed Mininet
that, trong do twin co do chinh xac muc gia tri cao nhung van gay sai quyet
dinh o muc `18.2%` va tang vi pham SLA them `7.9` diem phan tram.

## 7. Kiem Chung Noi Tai

Bon kiem chung noi tai cho thay thuoc do khong dem lech:

```text
IC1 gap = err * regret_on_error khop 0.0000% tren nhieu diem doc lap.
IC2 NC4 = 0.7494 / 0.7503 / 0.7501 vs ly thuyet 1 - 1/K = 0.750000.
IC3 NC3 = 0.611 / 0.643 / 0.613 vs ly thuyet 1 - sum(p_a^2) = 0.62348.
IC4 audit tai lap: chay lai tu 5 trace dong bang cho err_delta = d_sla_delta = 0
    tren ca 5 replicate.
```

Ket luan: bo dem `err`, bo tinh `regret`, va bo loc tie/regret nhat quan.

## 8. Gioi Han

L1. Da dong sau khi tang `n=3 -> n=5`. Diem uoc luong
`SD_giua(d_sla)=0.00650`. CI95 cua chinh SD theo chi-square, df=4, co can tren
`0.01866`, thap hon nguong gay G2 `0.03951` khoang 2.1x. Voi n=3, can tren
cu la `0.04401`, vuot nguong gay cu `0.0215`; khi tang len n=5, can tren SD
giam va nguong gay tang, nen gioi han nay khong con chan gate.

```text
[x] da chay them seed 3/4 de len n=5
[x] L1 dong
```

L2. Hieu chuan lay tu trace0, nen trace0 la in-sample. O n=5, trace0 xep hang
1/5 ve `err` va 2/5 ve `d_sla`; vi tri nay nhat quan voi ngau nhien
(`p=0.2/0.4`). Khong co bang chung thien lech in-sample phat hien duoc. Lan
sau van nen tach mot trace hieu chuan rieng va khong dung no trong bao cao.

L3. G6 la AR(1) model validation so voi trace Mininet, khong phai kiem chung
cheo giua hai testbed doc lap.

L4. Phep do chinh dung `rho_offered` cho ca twin va oracle de co lap mot bien:
do cu cua twin. Nhieu telemetry duoc tach rieng va chi dung lam cross-check.

L5. `kappa=2.5` co phuong sai huu han, thap burstiness hon mot so luu luong
Internet thuc. Huong anh huong chua duoc danh gia.

L6. Topology B la manh leaf-spine 2x2, khong phai topology co ten. Phase 24
nen nang len topology lon hon nhu Abilene. Cau truc topology da la du lieu
`LINKS/PATHS`, nen `decision_error.py` khong can doi khi nang cap dung cach.

L7. `err` va `d_sla` tuong quan cao giua cac trace (`r=0.944`), cho thay co
mot yeu to chung day hai dai luong cung chieu. Gia thuyet dau tien la
`rho_mean` cua bon link loi, nhung chi co `n=5` diem trace nen khong du suc
ket luan:

```text
corr(rho_core_mean, err)   = 0.396, CI95 Fisher [-0.747, 0.947]
corr(rho_core_mean, d_sla) = 0.183, CI95 Fisher [-0.834, 0.917]
```

Ket luan dung: khong ket luan duoc voi `n=5`; khong thay bang chung khong co
nghia la co bang chung phu dinh. Diagnostic co suc manh hon phai dung muc
block va dung bien dung co che: crossing-rate. Tren 500 block dai `5*tau`:

```text
corr(crossing_rate_block, err_block)   = 0.460, CI95 [0.388, 0.526], r2 = 0.211
corr(crossing_rate_block, d_sla_block) = 0.434, CI95 [0.360, 0.503], r2 = 0.189
```

Doc dung: quan he co that va CI loai tru 0, nhung `r2 ~= 21%` nen day khong
phai la bang chung co che manh nhat. Co che chinh van la P3' risk ratio:
`P(error|crossed) / P(error|not crossed)`. O muc block, so sanh cung don vi
voi trung binh tai loi cho thay crossing-rate giai thich tot hon proxy
`rho_core_mean`, nhung ca hai chi la diagnostic phu:

```text
corr(rho_core_mean_block, err_block)   = 0.286, CI95 [0.203, 0.365], r2 = 0.082
corr(rho_core_mean_block, d_sla_block) = 0.148, CI95 [0.061, 0.232], r2 = 0.022
```

Ghi chu CI: cac CI tren coi 500 block la doc lap. Vi block trong cung trace
chia se hieu ung cap-trace, `n_eff` that nho hon 500 va CI bao thu hon se rong
hon. Diem can dung trong paper: crossing-rate co lien he block-level voi loi,
nhung luan diem co che dung risk ratio chu khong dung moi `r=0.46`.

L8. Kiem chung cheo tren telemetry co nhieu ban dau bi hong do aliasing tuoi:
trace measured co `dt_s ~= 0.200 s`, trong khi z-list mac dinh duoc thiet ke
cho trace offered 10 ms. Nhieu z khac nhau bi lam tron ve cung mot `z_steps`,
nen cac hieu G3 bang 0 mot cach tat dinh. Ket qua sawtooth measured cu
`err=0.14220`, `d_sla=0.06111` khong duoc trich dan nhu evidence.

Ban fixed khong chay lai Mininet. No doc `dt_s` tu file, chi dung z bieu dien
duoc tren luoi measured `0,0.2,0.4,0.6,1.0,2.0,4.0`, va thay operational
sawtooth bang noi suy bracket tai tuoi Phase 20 tham chieu `0.305 s`:

```text
err_measured_fixed   = 0.16768, CI95(t,df=4) [0.15233, 0.18303]
d_sla_measured_fixed = 0.07100, CI95(t,df=4) [0.06122, 0.08078]
```

So cap theo seed sau khi sua:

```text
offered - measured_fixed err   = [0.0158, 0.0078, 0.0182, 0.0191, 0.0123], t=7.05
offered - measured_fixed d_sla = [0.0087, 0.0033, 0.0133, 0.0121, 0.0046], t=4.28
two-sided sign-test p cho 5/5 cung dau = 0.0625
```

Tat ca 5 trace fixed co `pass_without_G6=True`, G3 pass, P3' pass. Trace s4
khong con la ngoai le: `err_fixed=0.16474`, cung bac voi s0-s3. Kiem tra dt
tu file cho thay ca 5 trace deu co `dt_s ~= 0.200 s`; `mean_age=0.360` trong
ban sawtooth cu la hien vat pha/luoi 200 ms sau `z_max`, khong phai trace ngan
hay median dt lech thanh 0.24 s. Ket qua measured fixed van la cross-check phu,
khong thay the offered-load gate chinh.

Dien giai co che measured fixed: risk ratio khong cao hon offered mot cach co
y nghia; no giu nguyen do manh trong telemetry 200 ms:

```text
risk ratio offered        = [8.94, 9.48, 11.59, 10.23, 8.59], mean 9.77, SD 1.19
risk ratio measured_fixed = [8.19, 9.57, 13.88,  9.92, 8.57], mean 10.03, SD 2.27
paired measured-offered   = [-0.75, +0.09, +2.28, -0.31, -0.02], t=0.49, p ~= 0.65
P(error | not crossed): offered 0.0392, measured_fixed 0.0405
```

Vi vay phat bieu dung la "co che giu nguyen do manh tren telemetry that hon",
khong phai "telemetry lam co che manh hon".

## 9. Sua Sai Da Cong Bo

E1. P3 goc, ">=70% loi co r_jump < 0.01", la kiem dinh thieu ti le nen. Gia
tri 0.998 trong Lesson 20.0b co base rate 0.924, lift chi 1.08x. Da thay bang
P3' risk ratio.

E2. ACF cua qua trinh la tuyen tinh voi `s <= u_min`, roi luy thua voi
`s >= u_min`, khong phai "mu + duoi luy thua" nhu phat bieu som. `kappa_hat`
1.40/1.45 voi `R^2 < 0.6` khong duoc trich dan.

E3. Rang buoc `A/tau in [0.5, 2.0]` bi bo vi do la proxy muc gia tri, trong
khi Phase 20 do thang dai luong muc quyet dinh.

E4. `p_one_sided = 2.76e-06` cua Spearman khong hop le cho gate vi 9 gia tri
`err(z)` duoc tinh tren cung mot trace va phu thuoc manh. Da thay bang 8 CI
cap voi Bonferroni.

E5. Dien giai "risk ratio tren telemetry cao hon offered" la sai vi dua tren
measured sawtooth bi alias tuoi. Sau khi sua bang z-list bieu dien duoc va
`operational-mode=bracket`, risk ratio measured fixed la `10.03` so voi
offered `9.77`, khac biet cap `t=0.49`, `p ~= 0.65`. Cau dung: risk ratio
khong khac nhau phat hien duoc; co che giu nguyen do manh tren telemetry.

## 10. Chuyen Giao Sang Phase 21-23

Duong cong `err(z)` va `d_sla(z)` cua Phase 20 la duong co so ma trust gate
phai danh bai. Diem neo cho risk-coverage:

```text
coverage = 1.00
risk = d_sla = 0.07939
```

Trust gate co gia tri neu no ve duoc bien nam duoi diem neo nay: giam risk
bang cach hy sinh coverage. Neu bien risk-coverage nam ngang tai `0.07939`,
gate vo gia tri.

Artifacts da commit cho Gate 20:

```text
results/phase-20/decision_error_trace_s0.json
results/phase-20/decision_error_trace_s1.json
results/phase-20/decision_error_trace_s2.json
results/phase-20/decision_error_trace_s3.json
results/phase-20/decision_error_trace_s4.json
results/phase-20/decision_error_replicates_summary.json
results/phase-20/between_trace_summary.json
results/phase-20/between_trace_summary_n5.json
results/phase-20/core_load_diagnostic_n5.json
results/phase-20/block_crossing_diagnostic_n5.json
results/phase-20/decision_error_measured_fixed_trace_s0.json
results/phase-20/decision_error_measured_fixed_trace_s1.json
results/phase-20/decision_error_measured_fixed_trace_s2.json
results/phase-20/decision_error_measured_fixed_trace_s3.json
results/phase-20/decision_error_measured_fixed_trace_s4.json
results/phase-20/decision_error_measured_fixed_replicates_summary.json
results/phase-20/measured_fixed_crosscheck_diagnostic_n5.json
```

Raw CSV seed1-4 dang co local:

```text
results/phase-20/rho_offered_long_s1.csv
results/phase-20/rho_offered_long_s2.csv
results/phase-20/rho_offered_long_s3.csv
results/phase-20/rho_offered_long_s4.csv
results/phase-20/rho_measured_long_s1.csv
results/phase-20/rho_measured_long_s2.csv
results/phase-20/rho_measured_long_s3.csv
results/phase-20/rho_measured_long_s4.csv
```

Moi file `rho_offered_long_s*.csv` hon 100 MB, nen khong add vao commit nay.
Neu can version hoa raw trace, dung Git LFS hoac artifact archive rieng.

Phase 22 dung chinh cac JSON/trace nay de hieu chuan conformal theo block,
khong chia ngau nhien theo mau vi tuong quan thoi gian se gay ro ri.
