# Phase 20R.6 -- Design Validation

Trang thai: preregistration truoc khi chay testbed additivity/quasistatic.
Ngay ky: 2026-08-06.

## Muc Tieu

Lesson 20R.6 kiem tra ba diem con lai sau H7/H8:

- G6 additivity: chi so `cost_path` co tuong duong voi tong chi phi link hay
  co cascade end-to-end dang ke.
- Quasistatic o muc decision: composition bang tinh theo `rho(t)` co khop
  measured dynamic trace theo cua so 60 s hay khong.
- Sensitivity voi `a=0.2`: giam bien do `sigma_rho = a * sigma_max` va kiem
  tra `R = sd(cost margin) / mean(cost margin)` van xep hang `err_total`.

Hai ghi chu duoc khoa truoc khi chay:

- H8b margin gan nguong: max `|Delta R| = 0.0189`, nguong 0.02. Vi vay
  20R.6 phai bao cao CI bootstrap block cho chinh `R`; khong chi dung point
  estimate.
- Spearman pooled tau = 0.989 khong mau thuan voi tau-scaling. Luat day du la
  `err = g(R, z/tau)`. Khi gom tau tai `z = 0.55`, `z/tau` thay doi tu 0.11
  den 2.75, nen bao cao dung la `R` dominates trong mien nay, khong phai
  `R` giai thich tat ca.

## Additivity G6

Chi so test la mean cost, khong cong p95/p99. Percentile chi duoc bao cao
neu co end-to-end measurement truc tiep.

Kiem dinh dung `TandemTopo`: ba link do noi tiep, moi link cai qdisc bang dung
`setup_measure_qdisc` va `setup_return_qdisc` cua Phase L. Khong dung
`RoutingTopo8` vi topology, controller va qdisc khac Phase L.

Bon nhanh:

- A: truth table da co, `SplitQdiscTopo`, mot link.
- A': `TandemTopo`, chi link i co tai, probe chi qua link i. Day la phep
  chuyen topology.
- B: `TandemTopo`, ca ba link co tai, probe chi qua link i. Day la CPU
  contention/probe artifact.
- C: `TandemTopo`, ca ba link co tai, probe xuyen ca ba link. Day la
  cascade/G6.

Doi chieu:

```text
A' - A       = topology transfer
B  - A'      = CPU contention
C  - sum(B)  = cascade/G6 thuan
C  - sum(A)  = transfer + contention + cascade
```

Thiet ke live da cat giam:

```text
modes       = poisson,h2
seeds       = 101,102,103,104,105
A table     = 2 mode x 2 rho_bar x 3 link = 12 table cells
A' live     = 2 mode x 1 rho_bar(0.925) x 3 link x 5 seed = 30 run
B live      = 2 mode x 1 rho_bar(0.925) x 3 link x 5 seed = 30 run
C live      = 2 mode x 2 rho_bar(0.85,0.925) x 5 seed = 20 run
Delta       = 0.44 ms (= 20% cost gap)
TOST        = CI90 phai nam trong [-0.44,+0.44]
power check = 1.645 * se < 0.44
probe gate  = probe intrusion <= 2%
schedule    = paired; `trajectory_digest` phai khop theo mode/rho_bar/seed
```

Du doan da khoa truoc live run:

```text
A' - A       ~ 0
B  - A'      ~ 0
C  - sum(B)  < 0, neu co cascade thi huong chinh la queue smoothing
```

So thoi gian:

```text
smoke topology : ~ 1 phut
A'             : 30 run, ~ 40 phut tren runner hien tai
B              : 30 run, ~ 40 phut
C              : 20 run, ~ 28 phut
Tong additivity: ~ 1.8 gio, du tru 2.1 gio ca cleanup/overhead
```

Dieu kien dung som: sau A' phai chay `--compare-a-vs-truthtable`. Neu
`A' - A` vuot `0.44 ms`, dung, khong chay B/C; khi do truth table mot-link
khong chuyen duoc sang topology ba-link.

Lenh khoa plan:

```bash
python3 -m measurements.additivity_check --plan-only
python3 -m measurements.additivity_check \
  --write-plan results/phase-20R/additivity_plan.json
```

Sau khi co state live A'/B/C:

```bash
python3 -m measurements.additivity_check --compare-a-vs-truthtable
python3 -m measurements.additivity_check --analyze
```

## Quasistatic Decision

Thiet ke:

```text
mode       = poisson
rho_bar    = 0.925
duration   = 600 s
window     = 60 s
seeds      = 101,102,103,104,105
threshold  = max |measured_cost - table_cost(rho(t))| <= 0.44 ms
```

So run du kien: `600 s x 5 seed = 50 min`, du tru 60 phut ca startup/cleanup.

Cat giam truoc live run: dung `seeds = 101,102,103`, `600 s x 3 seed = 30 min`,
du tru 40 phut. Ly do: day la xac nhan o muc decision, khong phai uoc luong
link-level moi; nguong bat cap can phat hien la `0.44 ms`.

Lenh khoa plan:

```bash
python3 -m measurements.quasistatic_check --plan-only
python3 -m measurements.quasistatic_check \
  --write-plan results/phase-20R/quasistatic_plan.json
```

Chay live tren `TandemTopo`, 3 seed x 10 cua so:

```bash
sudo -n env PYTHONPATH="$PWD" python3 -m measurements.quasistatic_check \
  --live --duration 600 --tau 1.0 --rho-bar 0.925 --mode poisson \
  --seeds 101,102,103 \
  --state results/phase-20R/quasistatic_state.json
```

Sau khi co state live:

```bash
python3 -m measurements.quasistatic_check --analyze
```

## Sensitivity a=0.2 va CI R

Khong chay Mininet; dung `truth_table.parquet`, AR(1) generator da ky, va
bang calibration hien co.

```bash
python3 -m measurements.decision_error_v2 --run-fixed \
  --a-override 0.2 \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --out results/phase-20R/sensitivity_a02.parquet

python3 -m measurements.decision_error_v2 --compute-margin-cv \
  --a-override 0.2 \
  --n 200000 \
  --seeds 101,102,103 \
  --out results/phase-20R/margin_cv_a02.parquet

python3 -m measurements.decision_error_v2 --compute-margin-cv-ci \
  --sigma-override 0.0096 \
  --tau 0.2,1.0,5.0 \
  --n 200000 \
  --seeds 101,102,103 \
  --n-boot 2000 \
  --out results/phase-20R/margin_cv_ci.json

python3 -m measurements.plot_decision_error_v2
```

Criterion sensitivity: tai `z=0.55`, `Spearman(R, err_total) > 0.9` tren
`poisson,h2`. Neu fail, bao cao huong fail va tac dong len gate H8.

## Ket Qua Khong-Mininet Sau Prereg

Prereg/code duoc commit truoc khi sinh so tai commit `986a8a3`.

Artifacts da sinh:

```text
results/phase-20R/additivity_plan.json
results/phase-20R/quasistatic_plan.json
results/phase-20R/sensitivity_a02.parquet
results/phase-20R/margin_cv_a02.parquet
results/phase-20R/margin_cv_ci.json
results/phase-20R/margin_cv_ci_n800k.json
docs/phase-20R/figures/decision_error_a02_margin_cv_vs_err.png
```

Sensitivity `a=0.2` tai `z=0.55`:

```text
mode     rho_bar  R         err_total
h2       0.700    0.667557  0.180545
h2       0.850    0.392885  0.012725
h2       0.925    0.145859  0.000000
h2       0.960    0.064526  0.000000
poisson  0.700    0.177920  0.000000
poisson  0.850    0.747392  0.297133
poisson  0.925    0.733750  0.228484
poisson  0.960    0.438822  0.016551
```

`Spearman(R, err_total) = 0.975900`, `n = 8`, PASS > 0.9.

CI `R` da duoc tinh bang block bootstrap, dung estimator mean theo seed nhu
H8b. Max point delta vs tau=1:

```text
tau=0.2: max |Delta R| = 0.003991
tau=5.0: max |Delta R| = 0.018882
```

H8b van o sat nguong 0.02. Sau formal H9 review, khoang CI bao thu cho worst
H8b:

```text
tau=5, poisson rho_bar=0.85
point |Delta R| = 0.018882
CI bao thu signed delta = [-0.025670, +0.062551]
```

Vi CI bao thu cu cham/vuot `0.02`, H8b o artifact `n=200000` la `KHONG KET
LUAN DUOC`. Phep va no-testbed da duoc chay voi `n=800000`, 5 seed,
`n_boot=2000`:

```text
max |Delta R| = 0.006670
conservative signed CI envelope = [-0.016592, +0.015376]
```

Envelope moi nam tron trong `+-0.02`, nen H8b PASS sau artifact n800k.

H9 formal:

```text
pooled n = 30
Spearman(R, err_total) = 0.994651
c * Phi(-k/R): k = 1.159900, c = 4.760398
H9a PASS: sd(k) = 0.020053 tren ba tap tau=1; 0.015017 tren tau sweep
H9b PASS: Spearman(z/tau, c) = 1.000000 tren tau=1; 0.971625 tren tau sweep
H9c FAIL: nguong sac R<0.30 => err=0 bi bac bo
can mem thay the: R<0.30 => err_total<0.002, n=5/5
```

Artifacts H9:

```text
results/phase-20R/h9_separability.json
docs/phase-20R/figures/decision_error_h9_separability.png
```

`results/phase-20R/additivity_check.json` va
`results/phase-20R/quasistatic_check.json` hien chi la placeholder
`not evaluated`, vi chua chay live Branch A'/B/C va dynamic trace.

## Loi Khong Duoc Lam

- Khong dung ordinary t-test thay cho TOST equivalence.
- Khong dung unpaired schedule neu so sanh B/C.
- Khong chay tat ca probe cung luc.
- Khong bo Branch B khi ket luan G6.
- Khong cong p95/p99.
- Khong chon `Delta` sau khi nhin ket qua.
- Khong sua nguoc `truth_table.parquet` de lam dep G6.

---

## Lesson 20R.6 -- Ket Qua Cuoi Va Tam Nhin Nguyen Nhan

Muc nay tong hop phan chan doan. Chi tiet so va pham vi hieu luc o
`00n-amendment-13.md` §15; bang bay cong o `08-gates.md`.

### Thieu hut theo TUNG LINK, kem nguon goc diem lua

Bao cao o muc path che mat tang nay, va reviewer se hoi ngay.

```text
link  rho      hai diem luoi neo cua bang tra   deficit poisson   deficit h2
L1    0.8575   ca hai tu 20R.4 (04/08)          +0.000018         -0.002567
L2    0.9775   mot 20R.4, mot Phase L           +0.000358         -0.002712
L3    0.9875   ca hai tu Phase L  (29/07)       -0.001785         -0.008231
```

Thieu hut lon nhat, o ca hai mode, roi vao link ma ca hai diem neo deu tu Phase
L. Day KHONG phai bang chung (`n = 3` link, `rho`/`bw`/`q` doi cung luc), nhung
no la mot bien gay nhieu phai ghi ra. Sentinel loss recheck (`z_welch = +1.78`,
MDE = 3.4e-4, tuc 5-24 lan nho hon deficit) da loai drift theo thoi gian nhu
mot loi giai thich.

### Do doc BAC HAI thay secant

`loss(c_a)` loi, nen do doc trung binh tren `c_a in [1, 2]` uoc luong THAP phan
ung tai `c_a = 2`. Ba duong cong cbr do duoc `loss = 0` tuyet doi, cho phep neo
parabol qua goc:

```text
loss'(2) = 1.5 * l_h2 - 2 * l_poisson      (cuc bo)
secant   =       l_h2 -     l_poisson      (trung binh)
```

Ket qua tai o FAIL (`h2 L3`): burstiness giai thich **83.3%**, khong phai 64%.

### Cochran Q -- phan du la common-mode hay differential

```text
mode      phan du gop     Cochran Q (df=2)    I2      doc
h2         -0.001884          0.06            0%      ba link DONG NHAT
poisson    -0.000262          0.62            0%      ba link DONG NHAT
```

Voi 5 seed truoc do poisson co `I2 = 67%`; phan lon "di dieu" khi ay la nhieu
do, boc ra duoc bang 8 seed. `I2` la con so bien minh dinh luong cho viec tang
seed -- khong phai cam tinh.

### CENSORING -- vi sao "phan bo delay khop" KHONG phai bang chung

```text
delay quan sat duoc = min(X, q_max)     <- bi cat cut
loss  quan sat duoc = P(X > q_max)      <- chinh la phan bi cat
```

Hai phan bo `X` khac nhau CHI o phan duoi vuot `q_max` cho phan bo delay quan
sat duoc gan nhu y het nhung loss khac ro ret. Voi h2, `p99` cham tran buffer o
CA HAI phia, nen so sanh phan vi delay mat kha nang phan biet. Phan bo delay chi
lay lai kha nang do khi `p99 << q_max`, tuc che do chua bao hoa.

(Amendment 12 §10.1 tung ket luan nguoc lai; da danh dau `!! SUA` va giu nguyen
van de theo vet.)

### Ket qua do lai in-band (RC7)

48 diem, 8 seed, validity sach. `probe_injection_differs = False` nhung deficit
h2 chi giam **11.9%** (`-0.011497 -> -0.010130`), duoi nguong `20%` da ky.
**RC7 bi bac; RC7 va RC8 la hai nguyen nhan doc lap.**

### RC1-RC8: moi nguyen nhan, kem "phep do co the noi doi nhu the nao"

```text
RC1  estimator mismatch      probe vs bg la hai dai luong khac nhau voi h2
RC2  thieu power             probe 5 pps -> sai so nhi phan x w_loss >> margin
RC3  hang so oi              delta = 0.44 ms tu he cu; DELTA_LOSS = 0.005 la ca thu hai
RC4  ngan sach probe         background nguyen rho + probe -> tai thuc > muc tieu
RC5  SE bang tra bi bo qua   coi bang tra la hang so exact -> mot FAIL gia (poisson L3)
RC6  packet-size bias        bfifo gioi han theo BYTE -> probe 106 B loss thap hon bg 1512 B
RC7  diem bom probe          in-band vs out-of-band -> arrival process tai bfifo khac
RC8  silent join failure     join tra ve rong ma khong bao loi -> ket luan NGUOC
```

### Trang thai cuoi

```text
G6-ABS   h2 FAIL (-0.010130 vs 0.005) | poisson PASS
G6-DIFF  h2 INCONCLUSIVE (tac o d_sla, ngay tai k=0) | poisson PASS
```

Branch B va C **khong mo** theo quy tac dung som cua Amendment 11. Pham vi hieu
luc: `00n-amendment-13.md` §15.8.
