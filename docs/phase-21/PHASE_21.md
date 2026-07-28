# PHASE 21 - PRE-REGISTRATION: CONFORMAL TRUST GATE

Ngay: 2026-07-27
Trang thai: superseded. Ban chot de ky la
`docs/phase-21/00-preregistration.md` ngay 2026-07-28.
Phu thuoc: `phase-20-complete`
Executor: DT4N owner + Codex

Ghi chu: file nay la ban nhap nen ly thuyet/ke hoach ban dau. Cac quyet dinh
P1-P8, score tren hieu, Mondrian 2 chieu `(z,u)`, va ho tieu chi theo `eps`
duoc chot trong `00-preregistration.md`.

Phase 20 da chung minh tin hieu quyet dinh ton tai. Phase 21 chot luat cho
bo du doan bat dinh va tap hieu chuan, truoc khi Phase 22 do coverage va
Phase 23 bien khoang tin cay thanh trust gate.

## 1. Vi Sao Phase Nay Ton Tai

Phase 20 tra loi RQ-A:

```text
err  = 0.18233, CI95(t,df=4) [0.16838, 0.19628]
d_sla = 0.07939, CI95(t,df=4) [0.06952, 0.08926]
P(error | crossed) / P(error | not crossed) = 8.94 tren trace0
```

Twin khong sai nhe ve prediction roi vo hai; no sai o muc co the doi quyet
dinh routing. Nhung Phase 20 chi do nguy co. Phase 21-23 doi bai toan sang:

```text
Khi nao controller duoc phep tin twin, va khi nao phai tu choi hanh dong?
```

Neu trust gate khong giam duoc `d_sla` so voi baseline coverage 1.0, no vo
gia tri ngay ca khi coverage interval co ve dung ve mat thong ke.

## 2. Cau Hoi Nghien Cuu

RQ-B1. Co the xay khoang conformal cho loi twin sao cho:

```text
coverage gan 1 - alpha tren du lieu Mininet doc lap
coverage khong vo o cac bin tuoi twin quan trong
khoang du hep de tao trust gate co gia tri quyet dinh
```

Mac dinh:

```text
alpha = 0.10
coverage muc tieu = 90%
don vi danh gia chinh = block dai 5*tau_core, khong phai sample 10 ms
```

## 3. Nen Ly Thuyet Chot Truoc

### 3.1 Split Conformal

Voi calibration scores `s_1, ..., s_n`, chon:

```text
k = ceil((n + 1) * (1 - alpha))
q_hat = k-th smallest score
```

Khoang du doan:

```text
C(x) = [y_hat(x) - q_hat, y_hat(x) + q_hat]
```

Neu `k > n`, dat `q_hat = +inf` va ghi ro bin khong du mau.

### 3.2 Nonconformity Score

Score chinh:

```text
s_abs = |cost_true - cost_twin|
```

Ly do: trust gate can so sanh khoang cost giua action, nen don vi ms/cost
truc tiep de dien giai.

Score phu de chuan doan:

```text
s_norm = |cost_true - cost_twin| / max(epsilon, cost_true)
```

`s_norm` khong thay `s_abs` trong gate chinh tru khi co amendment rieng.

### 3.3 Bao Phu Bien Va Bao Phu Theo Nhom

Conformal chuan chi hua bao phu bien:

```text
P(y in C(x)) >= 1 - alpha
```

DT4N khong duoc chi bao cao bao phu bien neu loi tap trung o tuoi cao. Bao cao
bat buoc co:

```text
coverage marginal
coverage theo bin tuoi z
width theo bin tuoi z
```

### 3.4 Mondrian Theo Tuoi

Dung phan vi rieng cho moi bin tuoi:

```text
q_hat_g = conformal_quantile({s_i: z_i in bin g})
C_g(x) = y_hat(x) +/- q_hat_g
```

Ly do chon `z`:

```text
z quan sat duoc tai thoi diem quyet dinh
Phase 20 da thay err(z) tang don dieu
z gan truc tiep voi co che AoI cua twin
```

Bin mac dinh ban dau:

```text
[0.00, 0.10)
[0.10, 0.20)
[0.20, 0.35)
[0.35, 0.75)
[0.75, +inf)
```

Neu bin co it hon 50 block calibration thi gop voi bin lan can gan nhat. Neu
sau khi gop van it hon 50 block, bin do chi duoc bao cao exploratory.

### 3.5 Exchangeability Theo Block

Phase 20 co:

```text
tau_core = 2.87 s
dt = 0.010 s
block_len = round(5 * tau_core / dt) = 1435 samples = 14.35 s
```

Mau lien tiep 10 ms khong exchangeable vi tuong quan thoi gian. Split du lieu
phai theo block nguyen:

```text
khong cat giua block
khong chia calibration/test theo sample
khong dung mau trong cung block cho ca calib va test
```

Positive control se co y chia sai theo sample de kiem tra pipeline co nhay voi
ro ri thoi gian hay khong.

### 3.6 Don Vi Bao Dam

Moi ket luan coverage cua Phase 22 phai phat bieu:

```text
coverage is evaluated on held-out Mininet blocks of length 5*tau_core
```

Khong duoc viet nhu bao dam pointwise cho tung sample doc lap.

## 4. Tai San Dong Bang Tu Phase 20

Dung lai cac hang so:

```text
topology = topology_v7 butterfly 2x2
traffic = v7 flow-level Poisson/Pareto
sync_period = 0.5 s
d_sync = 0.051 s
tau_core = 2.87 s
warmup_frac = 0.20
z_list = 0,0.05,0.10,0.20,0.298,0.50,1.0,2.0,4.0
calibration trace for SLA = trace0 frozen from Phase 20
replicate seeds = 0,1,2,3,4
```

Ket qua tham chieu:

```text
offered err mean = 0.18233
offered d_sla mean = 0.07939
measured_fixed err mean = 0.16768
measured_fixed d_sla mean = 0.07100
```

Diagnostic L7 moi:

```text
trace-level corr(rho_core_mean, err) inconclusive with n=5
block-level corr(crossing_rate, err) = 0.460, CI95 [0.388, 0.526], r2 = 0.211
block-level corr(crossing_rate, d_sla) = 0.434, CI95 [0.360, 0.503], r2 = 0.189
block-level corr(rho_core_mean, err) = 0.286, CI95 [0.203, 0.365], r2 = 0.082
mechanism risk ratio is unchanged on measured_fixed: 10.03 vs 9.77, p ~= 0.65
```

## 5. Lessons Phase 21

### 21.0 Chot Luat Truoc Khi Do

Khong viet code measurement. Chot:

```text
alpha
score chinh/phu
bin tuoi
block split
gates H1-H7
fail branches
```

### 21.1 Build Calibration Set

Script du kien:

```text
measurements/build_conformal_calib_set.py
```

Input:

```text
results/phase-20/rho_offered_long*.csv
results/phase-20/decision_error_offered.json
```

Output schema toi thieu:

```text
trace_id
block_id
t
z
age_bin
action
cost_twin[action]
cost_true[action]
score_abs[action]
score_norm[action]
optimal_action_true
optimal_action_twin
wrong_operational
crossed_operational
```

Mot row co the la action-level neu gate can khoang cho tung action. Neu dung
decision-level score, phai ghi amendment vi no doi doi tuong bao phu.

### 21.2 Error Versus Age

Script du kien:

```text
measurements/error_vs_age.py
```

Phai tra loi:

```text
Q1: score_abs co tang theo z khong?
Q2: q_hat(z) co tang theo z khong?
Q3: crossing_rate co giai thich err/d_sla theo block khong?
Q4: measured telemetry co lam alias tuoi nhu L8 khong?
```

### 21.3 Conformal Age Bins

Script du kien:

```text
measurements/conformal_age.py
```

Chay hai che do:

```text
marginal split conformal
Mondrian conformal theo age_bin
```

Split mac dinh:

```text
calib traces = seed 0,1,2
test traces = seed 3,4
```

Sensitivity bat buoc:

```text
leave-one-trace-out: moi lan 4 trace calib, 1 trace test
```

### 21.4 Usefulness Cho Trust Gate

Script du kien:

```text
measurements/conformal_usefulness.py
```

Trust gate prototype:

```text
ACCEPT action a* neu upper_bound(cost(a*)) < lower_bound(cost(a2))
REJECT neu khoang chong lan
```

Bao cao:

```text
coverage
risk = d_sla tren accepted decisions
coverage_decision = accepted / total
risk_coverage_curve
```

Baseline Phase 20:

```text
coverage_decision = 1.00
risk = d_sla = 0.07939
```

## 6. Gates H1-H7

H1. Calibration set integrity PASS neu:

```text
khong co block xuat hien trong ca calib va test
schema day du
n_block_total >= 450
moi age_bin chinh co >= 50 block calibration sau khi gop bin
```

H2. Marginal coverage PASS neu:

```text
coverage_test >= 0.88 voi alpha=0.10
```

Nguong 0.88 cho phep sai so huu han nhung khong duoc che bang binning.

H3. Mondrian age-bin coverage PASS neu:

```text
moi age_bin chinh co coverage_test >= 0.85
```

Neu bin it mau va duoc danh dau exploratory thi khong tinh vao H3, nhung phai
bao cao rieng.

H4. Width monotonicity sanity PASS neu:

```text
median q_hat(age_bin) khong giam manh khi z tang
```

"Giam manh" = bin sau thap hon bin truoc qua 20% ma khong co giai thich bang
n mau hoac crossing-rate.

H5. Positive control PASS neu:

```text
sample-random split cho ket qua khac ro block split
```

Muc tieu cua H5 khong phai lam dep ket qua; no chung minh pipeline thay duoc
ro ri tuong quan thoi gian.

H6. Trust-gate usefulness PASS neu ton tai mot diem tren risk-coverage curve:

```text
d_sla_accepted <= 0.055
coverage_decision >= 0.30
```

Neu coverage cao hon nhung risk khong giam, gate vo gia tri. Neu risk giam
nhung coverage qua thap, gate khong co tac dung van hanh.

H7. Mechanism consistency PASS neu:

```text
accepted decisions co crossing_rate thap hon rejected decisions
hoac q_hat(z/crossing) cao hon o nhom gan nguong
```

H7 noi Phase 22-23 lai voi co che L7 cua Phase 20.

## 7. Fail Branches

F1. Marginal coverage fail:

```text
kiem tra score, split block, off-by-one conformal quantile
khong doi alpha tru khi co amendment
```

F2. Marginal pass nhung age-bin fail:

```text
Mondrian la bat buoc; khong duoc chi bao cao marginal
gop bin hoac them dac trung crossing-rate neu bin tuoi qua tho
```

F3. Coverage pass nhung gate vo dung:

```text
bao cao la conformal dung nhung qua rong
Phase 23 khong duoc claim trust gate co gia tri
```

F4. Measured telemetry khac offered qua lon:

```text
giu offered la gate chinh cho co-che-AoI sach
bao cao measured_fixed la robustness/cross-check sau khi sua coarse telemetry aliasing
khong tron hai nguon thanh mot con so
```

## 8. Iteration Budget

Toi da 2 vong sua sau lan chay dau:

```text
vong 1: sua bug/format/split neu fail do loi code
vong 2: gop age_bin hoac them score phu da prereg
```

Sau 2 vong, neu H2-H6 van fail thi Phase 21-23 ket luan negative hoac can
pre-registration moi.

## 9. Rui Ro Da Biet

R1. `n=5` trace van it cho ket luan trace-level.

R2. Block `5*tau` giam tuong quan nhung khong chung minh exchangeability tuyet
doi.

R3. `z` co the khong du de dieu kien; crossing-rate co the can lam feature
trong Phase 22b.

R4. Measured telemetry 200 ms tao alias tuoi neu dung sawtooth/z-list 10 ms.
Dung `operational-mode=bracket` cho cross-check, va khong dung measured lam
nguon gate chinh neu chua nang cap telemetry.

R5. Trust gate co the dung ve coverage nhung qua bao thu, lam coverage_decision
qua thap.

## 10. Chuyen Giao Sang Phase 22

Phase 22 duoc phep viet code khi:

```text
[ ] owner ky PHASE_21.md
[ ] tag phase-21-prereg duoc tao
[ ] raw trace Phase 20 can dung con nam local hoac duoc archive rieng
```

Artifact dau ra Phase 22 du kien:

```text
results/phase-22/conformal_calib_blocks.json
results/phase-22/conformal_age_marginal.json
results/phase-22/conformal_age_mondrian.json
results/phase-22/conformal_positive_control.json
results/phase-22/trust_gate_usefulness.json
```

## 11. Checklist Ky

```text
[ ] alpha = 0.10
[ ] score chinh = s_abs
[ ] score phu = s_norm chi de chuan doan
[ ] split theo block 5*tau_core
[ ] Mondrian theo age_bin
[ ] gates H1-H7 duoc chap nhan
[ ] fail branches F1-F4 duoc chap nhan
```
