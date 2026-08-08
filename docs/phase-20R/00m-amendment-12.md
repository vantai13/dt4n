# AMENDMENT 12 -- Sua thuoc do cua 20R.6, khong sua gia thuyet

Ngay: 2026-08-07
Trang thai: ky truoc khi chay lai phan tich offline bang estimator bg.

## 1. Su Kien Kich Hoat

Chay B2, branch A', 30 run, 0 gate fail. Quy tac dung som cua Amendment 11
kich hoat: `topology_transfer_pass = false`. Da dung dung theo quy tac, chua
chay branch B/C.

Doc lai artifact cho thay fail khong phai do he thong/topology hong, ma do
thuoc do A' khong cung ho voi branch A:

```text
Branch A  = truth table do tren luong TAI/background
Branch A' = state live cu tinh loss/cost tren luong PROBE rieng
```

## 2. Nguyen Nhan Goc

RC1 -- estimator mismatch:

`l6_campaign.py` va truth table dung `bg = analyze(*_bg.bin, *_bgtx.bin)`.
`additivity_live.py` ban dau tinh loss/cost cua A' tu luong probe rieng. Voi
tai `h2`, PASTA khong ap dung; packet-average cua luong tai va time-average
cua probe la hai dai luong khac nhau.

RC2 -- khong du power:

Probe 5 pps x 70 s chi con khoang 300 goi sau warmup. Sai so nhi thuc cua
loss, sau khi nhan voi `w_loss = 3222..4516 ms`, lon hon margin `0.44 ms`
hang chuc den hang tram lan. Tang probe rate de sua power lai vi pham
`probe_intrusion <= 2%`.

RC3 -- stale constant:

`delta = 0.44 ms` la hang so phai sinh tu phase cu. Dinh nghia goc la `20%`
khe cost quyet dinh. Trong 20R, `w_loss` da duoc hieu chuan lai nen khe cost
phai tinh tai runtime theo `(mode, rho_bar)`.

## 3. Sua Gi

S1. A'/B link-level duoc rescore bang luong tai bg, khong chay lai Mininet.
File raw `*_bg.bin` va `*_bgtx.bin` da co tren dia. Script:

```text
measurements/additivity_rescore.py
```

S2. Analyzer tinh equivalence margin tai runtime:

```text
delta_path = 0.20 * measured_cost_gap_ms(mode, rho_bar)
delta_link = delta_path / 3
```

`A' - A` va `B - A'` dung `delta_link`; `C - sum(B)` dung `delta_path`.

S3. Bao cao ba contrast rieng:

```text
cost  : don vi ms, delta theo cost gap
delay : don vi ms, delta theo cost gap
loss  : don vi fraction, delta = 0.005
```

## 4. Khong Sua Gi

- Khong doi gia thuyet G6.
- Khong doi `rho_bar`, mode, seed, topology, qdisc.
- Khong bo diem nao.
- So do bang probe duoc giu lai trong state moi thanh `probe_loss`,
  `probe_cost_ms`, `probe_delay_ms` de lam doi chung PASTA.

## 5. Du Doan Truoc Rescore

```text
delta_pasta = delay_bg - delay_probe: duong voi h2, gan 0 voi poisson.
A' - A (bg) cua h2: trong +-20.53 ms path, tuc +-6.84 ms/link.
A' - A (bg) cua poisson: co the van vuot +-0.50 ms/link tren L2/L3.
```

Neu poisson van lech, dieu tra theo thu tu: `rho_actual`, noi suy truth table,
CPU/timing. Khong noi nguong hau nghiem.

## 7. Bo Sung Sau Chan Doan RC4

Trang thai: ky truoc khi chay lai live bang load budget da sua.

### 7.1 RC1 Da Duoc Xac Nhan Doc Lap

Rescore A'/B tu luong tai bg da sua estimator mismatch giua A va A'. Bang
chung doc lap trong `results/phase-20R/campaign_state.json`:

```text
cbr     mean(delta_pasta_ms) = +0.020, n = 40
h2      mean(delta_pasta_ms) = +1.296, n = 294
poisson mean(delta_pasta_ms) = -0.029, n = 275
```

Do do PASTA chi gan dung cho poisson/cbr; voi h2, probe va bg la hai estimator
khac nhau. Moi contrast phai dung estimator noi bo nhat quan:

```text
A' - A       : dung bg stream, vi A truth table la bg/load stream.
B - A'       : dung cung estimator hai ve; bg cho cost/loss co power hon.
C - sum(B)   : probe co the dung cho delay, nhung loss/cost bang probe o rho=0.925 khong du power.
```

### 7.2 RC4 -- Probe Da Lam Sai Load Budget

Runner cu goi `load_gen --probe-pps 0` voi background bang nguyen rho muc tieu,
sau do lai them mot probe rieng. Vi the tong tai tren link bi cong them probe.
Chan doan tu artifact cu:

```text
L3 poisson seed 101: rho_bg = 0.987466, probe = 0.015120, total = 1.002586, truth target = 0.9875
L3 h2      seed 101: rho_bg = 0.987466, probe = 0.015120, total = 1.002586, truth target = 0.9875
```

Kiem CV khong ung ho gia thuyet CPU smoothing:

```text
h2      CV_schedule = 1.9473, CV_actual = 1.9475, degradation = -0.01%
poisson CV_schedule = 0.9903, CV_actual = 0.9903, degradation = -0.00%
```

Sua pre-registered cho runner moi:

```text
rho_bg_command = rho_target_total - rho_probe_share_on_link
DEFAULT_PROBE_RATE_PPS = 20.0
DEFAULT_PROBE_SIZE_BYTES = 64
PROBE_INTRUSION_MAX = 0.005
```

Voi rho_bar = 0.925, budget moi la:

```text
L1: probe_share = 0.002120, rho_target_total = 0.857500, rho_bg_command = 0.855380
L2: probe_share = 0.002827, rho_target_total = 0.977500, rho_bg_command = 0.974673
L3: probe_share = 0.004240, rho_target_total = 0.987500, rho_bg_command = 0.983260
```

### 7.3 RC5 -- TOST Chua Truyen SE Cua Truth Table

Analyzer hien xem truth table nhu gia tri exact. Day la mot thieu sot thong ke
doc lap voi RC1/RC4. Neu can ket luan publication-grade cho A' - A, thay TOST
mot mau bang two-sample/Welch TOST, truyen `se_mean_ms` va SE loss tu truth
table vao contrast. Khong sua nguong hau nghiem.

### 7.4 Tach G6 Thanh Hai Nhanh

G6 cost/loss bang probe tai rho = 0.925 khong du power voi ngan sach hien tai.
Ghi lai de khong dien giai sai gate:

```text
G6a: delay additivity bang probe, co the test trong runner hien tai.
G6b: loss/cost additivity bang bg path flow, can thiet ke runner rieng.
```

Script one-button moi ghi additivity state/report voi hau to `budgetfix` de
khong resume nham cac state cu da bi RC4. Final gate cua script dung `G6a`
delay; cost/loss probe cu van duoc bao cao trong JSON nhung khong duoc xem la
ket luan G6b.

## 8. Sua Ha Tang Do (2026-08-07) -- Khong Cham Vao Gia Thuyet

### 8.1 Trieu Chung

`V-L1g` fail khi dung topology: `direct_packets_stat = 1` tren mot interface
do. Loi xuat hien khong on dinh: 2026-08-06 tren `s1-eth6`, 2026-08-07 tren
`s2-eth6`. Chien dich `budgetfix` dung tai `rows = 0`, chua sinh diem do.

### 8.2 Nguyen Nhan Goc

`measure_cmds()` cai measured qdisc bang ba lenh `tc` roi nhau. Giua lenh add
HTB root `default 10` va lenh add class `1:10`, class mac dinh chua ton tai,
nen HTB co the gui mot goi direct va bo qua shaping.

Goi lot vao cua so nay khop voi IPv6 DAD Neighbor Solicitation 86 B va MLD
report 90 B do kernel sinh khi veth Mininet bat len. Cua so race bi noi rong
boi helper cu dung `sh -lc`, vi login shell doc profile scripts moi lan goi.

### 8.3 Sua

L1. Tat IPv6 cho interface moi bang
`net.ipv6.conf.default.disable_ipv6 = 1` truoc khi Mininet tao veth, roi khoi
phuc trong `finally`. Khong dung khoa `all`, nen khong dung vao `eth0`/SSH.

L2. Doi helper shell tu `sh -lc` sang `sh -c`, va chay ba lenh add measured
qdisc bang `tc -batch` trong mot process. Khong dung `tc -force`.

L3. Tach `V-L1g` thanh hai y nghia:

```text
V-L1g-setup: snapshot sau khi cai dat. Neu fail thi cai lai toi da 3 lan.
V-L1g-run  : delta direct_packets_stat truoc/sau moi diem do. Neu delta > 0
             thi diem do fail validity gate, khong retry im lang.
```

Gate moi chat hon gate cu: gate cu bat nham goi vo hai truoc phep do va khong
bat duoc goi nguy hiem trong phep do; gate moi do dung counter delta bao quanh
khoang can bao ve.

L4. Moi lan reinstall qdisc setup duoc ghi vao provenance voi event
`qdisc_reinstall`.

### 8.4 Xac Nhan

Smoke topology phai chay 5 lan lien tiep truoc khi mo lai chien dich full.
Ket qua sau patch:

```text
smoke 1: pass=True, vl1g_run_pass=True, direct_delta={'L1': 0, 'L2': 0, 'L3': 0}, reinstall=0
smoke 2: pass=True, vl1g_run_pass=True, direct_delta={'L1': 0, 'L2': 0, 'L3': 0}, reinstall=0
smoke 3: pass=True, vl1g_run_pass=True, direct_delta={'L1': 0, 'L2': 0, 'L3': 0}, reinstall=0
smoke 4: pass=True, vl1g_run_pass=True, direct_delta={'L1': 0, 'L2': 0, 'L3': 0}, reinstall=0
smoke 5: pass=True, vl1g_run_pass=True, direct_delta={'L1': 0, 'L2': 0, 'L3': 0}, reinstall=0
```

### 8.5 Anh Huong Den Du Lieu

Khong co diem do nao cua chien dich `budgetfix` duoc sinh truoc sua nay.
Truth table va ket qua 20R.0-20R.5 khong bi cham toi.

### 8.6 RC6 -- Thien Lech Theo KICH THUOC GOI Trong bfifo

`bfifo` gioi han hang doi theo BYTE. Goi probe 106 B tren day co cua so chap
nhan rong hon goi bg 1512 B dung mot goi bg:

```text
limit 15120 B
goi bg    1512 B : nhan khi backlog <= 13608 B
goi probe  106 B : nhan khi backlog <= 15014 B
```

Do do `loss(probe) < loss(bg)` mot cach CO HE THONG, ke ca voi tai poisson.

Do trong cung run `budgetfix`, ca hai ve deu lay tu state da rescore (warmup
10 s, unique packets) nen cung mot dinh nghia thoi gian:

```text
mode     lnk   loss_probe   loss_bg    ti so probe/bg
poisson  L1    0.000166    0.000554      0.30
poisson  L2    0.012268    0.025320      0.48
poisson  L3    0.020409    0.036560      0.56
h2       L1    0.009759    0.028243      0.35
h2       L2    0.044420    0.098111      0.45
h2       L3    0.053703    0.124504      0.43
```

Poisson cung lech -> loai tru PASTA lam nguyen nhan. `delta_pasta_ms` Phase L
cho poisson = -0.029 ms (~0), tuc PASTA VAN dung cho delay. Day la mot hieu ung
khac: *packet-size bias in byte-based AQM* (tinh than RFC 2680: loss do duoc
khong so sanh duoc giua cac kich thuoc goi khac nhau).

He qua:

```text
- Moi contrast noi bo van hop le (cung estimator ca hai ve):
    A' - A      : ca hai ve dung loss cua luong tai 1512 B  -> khong anh huong
    B  - A'     : cung estimator hai ve                     -> triet tieu
    C  - sum(B) : ca hai ve dung probe 64 B                 -> triet tieu
- NHUNG loss do bang probe 64 B KHONG dai dien cho loss ma twin mo hinh hoa.
- => G6b (cong tinh cua loss) BAT BUOC do bang luong bg xuyen path.
- Bao cao phai ghi ro kich thuoc goi probe.
```

Doi lap voi lua chon truoc do: probe 1470 B khong co size bias nhung intrusion
1.5% (qua tai, chinh la RC4); probe 64 B co intrusion 0.42% nhung mang size
bias. Khong co lua chon nao mien phi; vi vay G6a (delay) dung probe, G6b (loss)
dung bg.

### 8.7 RC5 Da Duoc Cai Dat -- Truyen SE Cua Truth Table

`measurements.additivity_check` truoc day coi branch A nhu hang so exact. Da
sua: `TruthDelaySE` doc lai `se_mean_ms`/`n_seed` tu truth table, noi suy theo
`rho`, va `tost_equivalence(..., ref_se=, ref_df=)` cong phuong sai hai ve roi
lay df theo Welch-Satterthwaite. Path SE = root-sum-square SE cua ba link
(cac o truth table doc lap).

**Cap nhat 2026-08-07: da dong not phan loss.** Truth table khong co cot SE cho
`loss`, nhung `campaign_state.json` con giu `loss` theo tung seed. `TruthLossSE`
tinh lai SE tu chinh cac row da dung de dung bang (gate-clean, >= 5 replicate moi
o), noi suy theo `rho`:

```text
h2 bw=8 q=18 @0.8575   se_loss = 0.000493
h2 bw=6 q=13 @0.9775   se_loss = 0.000904
h2 bw=4 q=10 @0.9875   se_loss = 0.001628
```

Vi `cost = delay + w_loss * loss` voi `w_loss ~ 4516` (h2), phan loss CHI PHOI
sai so cua phia A: `se_cost` cua h2 L3 di tu 0.136 ms (chi delay) len 7.354 ms.

O muc path, `path_loss = 1 - prod(1 - l_i)` la PHI TUYEN, nen SE khong duoc
cong binh phuong thang tu SE cua cost tung link; phai qua dao ham rieng:

```text
d(path_loss)/d(l_i) = prod_{j != i} (1 - l_j)
se_path_loss  = sqrt( sum_i ( prod_{j!=i}(1-l_j) * se_i )^2 )
se_path_cost  = sqrt( sum_i se_delay_i^2 + (w_loss * se_path_loss)^2 )
```

Cac dao ham rieng < 1 nen ket qua NHO HON RSS ngay tho -- lam dung se khong
"an gian" theo huong noi long.

`estimand.reference_se_covers_loss_term` gio = `true`.

Mot quan sat phu quan trong: o sentinel `rho = 0.90` co `sd(loss) = 1.28e-4`
voi n = 19 nhung LAP LAI CUNG SEED 999; cac o luoi n = 5 dung 5 SEED KHAC NHAU
co `sd(loss) ~ 1.5e-3 ... 3.5e-3`, tuc lon hon 10-25 lan. Phuong sai cua truth
table bi chi phoi boi seed-to-seed, khong phai run-to-run. Hai ve cua `A' - A`
dung hai tap seed khac nhau nen phuong sai nay vao DOC LAP o ca hai ve. Do la
ly do ky thuat khien thiet ke GHEP CAP (cung seed) co the cuu power cho poisson,
trong khi tang so seed thi khong.

### 8.8 Doi Estimand Chinh: Per-Link -> Path-Level

Gate G6 goc phat bieu tren cost cua DUONG DI: `|cost_path - sum(link)| <= 0.20
x khe cost`. Nguong per-link `delta_path / 3` la mot phat minh sau nay trong
`additivity_check.py`, khong co trong preregistration.

Voi `delta_link = 0.503 ms` (poisson), so seed can de CI lot vao nguong:

```text
mode     lnk   sd_cost_ms   n_seed can
poisson  L1        1.07          13
poisson  L2        2.64          75
poisson  L3        5.99         384     <- khong kha thi
```

Do do estimand chinh chuyen ve dung muc path da pre-register:

```text
G6-transfer-path : sum(3 link A') - sum(3 link A), delta = delta_path -> CHINH
G6-transfer-link : tung link, delta = delta_path/3                    -> CHAN DOAN
```

Day KHONG phai noi nguong: `delta_path = 0.20 x khe cost` giu nguyen y nguyen
van; chi doi dai luong duoc kiem ve dung cai da ky. Ket qua per-link van duoc
tinh va luu day du trong report voi `role = "diagnostic"`.

### 8.9 Ba Muc Ket Luan: PASS / FAIL / INCONCLUSIVE

`tost_equivalence` nay tra ve `verdict` va `bias_detected`:

```text
PASS         : CI nam trong +-delta            -> tuong duong da duoc chung minh
FAIL         : CI nam hoan toan ngoai +-delta  -> KHONG tuong duong, bias da xac lap
INCONCLUSIVE : con lai (thuong CI rong hon delta) -> van de POWER, khong phai bias
```

Ranh gioi nay bat buoc vi hai chan doan can hai cach chua khac han. Mot o
INCONCLUSIVE khong duoc ghi la FAIL, va cung khong duoc noi delta de thanh
PASS. Runbook `tools/phase20r6_full_once.sh` chi STOP khi verdict = FAIL hoac
khi validity gate (paired schedule, probe intrusion) fail; INCONCLUSIVE duoc in
ra kem CI va chay tiep.

## 9. Ket Qua A' Sau Budgetfix + Rescore (2026-08-07)

Nguon: `results/phase-20R/additivity_branch_a_state_budgetfix_bg.json`,
`results/phase-20R/additivity_check_budgetfix_bg.json`. Rescore warmup 10 s,
unique packets, bg load stream -- cung estimator voi truth table.

Validity cua 30/30 diem do: `n_fail = 0`, `max_direct_packets_delta = 0`,
`max_probe_intrusion_ratio = 0.004357 < 0.005`, `max_abs_rate_error = 2.85e-05`.

### 9.1 Du Doan Da Ky Truoc Khi Rescore -- Va Ket Qua

Du doan: ca sau `Delta_loss` se dich LEN (bot am) sau khi cat warmup 10 s, vi
hang doi dang day dan tu trang thai rong nen loss trong warmup thap hon steady
state.

Ket qua thuc te: chi 2/6 o dich len.

```text
mode lnk | Dloss tho   Dloss rescore | dich chuyen
h2   L1  |  -0.002194     -0.002567  |  -0.000373
h2   L2  |  -0.001651     -0.002712  |  -0.001062
h2   L3  |  -0.007164     -0.008231  |  -0.001067
pois L1  |  +0.000004     +0.000018  |  +0.000013
pois L2  |  -0.000081     +0.000358  |  +0.000439
pois L3  |  -0.001623     -0.001785  |  -0.000162
```

Gia thuyet "phan du am chi la artifact do khong cat warmup" BI BAC cho h2: cat
warmup lam h2 lech THEM. Ghi lai day du theo dung nguyen tac khong xoa negative
result.

### 9.2 Path-Level (Estimand Chinh)

Tat ca so duoi day da truyen SE hai ve day du (RC5 dong, ke ca loss).

```text
mode     n  mean_ms  se_sample  se_ref  se_ms   df    CI90                delta    verdict
h2       5  -61.525    8.320     7.475  11.184  7.91  [-82.714, -40.335]  20.532   FAIL
poisson  5   -4.793    2.373     4.257   4.874  6.27  [-14.263,  +4.678]   1.509   INCONCLUSIVE
```

Tach theo thanh phan:

```text
contrast     mode     mean      se_ms     CI90                  delta     verdict
path delay   h2      -0.510 ms  0.191     [-0.873, -0.148]      20.532    PASS
path delay   poisson -0.251 ms  0.328     [-0.873, +0.371]       1.509    PASS
path loss    h2      -0.01150   0.00226   [-0.01578, -0.00722]   0.005    FAIL
path loss    poisson -0.00138   0.00152   [-0.00432, +0.00157]   0.005    PASS
```

Ket luan h2 BEN VUNG sau khi dong RC5: SE tang tu 8.32 len 11.18 ms, CI rong
them ~24%, nhung `|mean| = 61.5` van gap 3 lan `delta = 20.5` va CI van khong
chua 0. Diem yeu thong ke da duoc tu xu ly, khong lat nguoc ket luan.

Ket luan doc duoc:

```text
DELAY chuyen topology TOT o ca hai mode. Lech <= 0.51 ms, nam sau ben trong
delta o ca hai mode. Topology-transfer KHONG phai van de cua delay.

LOSS moi la cho hong, va chi voi h2. Toan bo -61.5 ms cua h2 den tu
-0.0115 loss nhan w_loss ~ 3222. Delay chi dong gop -0.51 ms.

poisson: CI CHUA 0 (bias_detected = false) nhung CI rong hon delta
-> INCONCLUSIVE thuan tuy do POWER, dung nhu du bao. Khong co bang chung bias.

h2: power_ok = true VA CI khong chua 0 -> day la BIAS DA XAC LAP, khong phai
thieu power. Day la mot FINDING, khong phai mot measurement bug da biet.
```

### 9.3 Per-Link (Chan Doan, Khong Phai Ket Luan)

```text
contrast          mode     lnk  mean_ms   se_ms   CI90                delta    verdict
Aprime_minus_A    h2       L1   -11.803   5.422   [-22.729,  -0.878]   6.844    INCONCLUSIVE
Aprime_minus_A    h2       L2   -12.260   8.795   [-29.351,  +4.831]   6.844    INCONCLUSIVE
Aprime_minus_A    h2       L3   -37.461   9.403   [-55.276, -19.646]   6.844    FAIL
Aprime_minus_A    poisson  L1    +0.048   0.729   [ -1.332,  +1.429]   0.503    INCONCLUSIVE
Aprime_minus_A    poisson  L2    +1.134   3.220   [ -4.966,  +7.234]   0.503    INCONCLUSIVE
Aprime_minus_A    poisson  L3    -5.975   3.965   [-13.680,  +1.730]   0.503    INCONCLUSIVE
```

Delay per-link PASS o 5/6 o (o con lai poisson L3 INCONCLUSIVE, mean -0.223 ms).
Mot lan nua: van de nam o loss, khong o delay.

Luu y sua sai: TRUOC khi dong RC5, poisson L3 bi cham `FAIL` voi CI
`[-10.041, -1.909]`. Sau khi truyen SE cua cot loss trong truth table, CI thanh
`[-13.680, +1.730]` va CHUA 0 -> `INCONCLUSIVE`. Nhu vay `FAIL` cu la artifact
cua viec coi truth table nhu hang so exact. Sau khi sua, KHONG CON o poisson nao
FAIL. Bang cu duoc giu o day de nguoi doc theo duoc vet sua.

### 9.4 Viec Tiep Theo Truoc Khi Mo B/C

h2 co bias path-level da xac lap -> runbook STOP dung theo thiet ke. Truoc khi
ket luan day la tinh chat vat ly that, phai loai hai bien gay nhieu con lai,
theo thu tu:

```text
1. Do bo sung truth table TAI DUNG rho = 0.8575 / 0.9775 / 0.9875 tren
   SplitQdiscTopo (15 run x 2 mode). Hien dang noi suy tai 0.9775 giua luoi
   0.96 va 0.98 voi ham loss loi manh. Uoc luong sai so noi suy ~8e-5, nho hon
   nhieu so voi -0.0115 dang duoi, nhung do la 35 phut may de xoa vinh vien
   mot bien khoi moi tranh luan ve sau.
2. So c_a thuc te LUC DEN switch (khong phai luc gui) giua A' va Phase L. CV
   luc gui da do: degradation 0.01%. Neu CV luc den khac -> access link hoac
   OVS lam muot burst, va do la topology-transfer that.
3. Neu sau 1 va 2 h2 van lech: day la FINDING. Bao cao, va Phase 21R phai dung
   truth table do TREN TandemTopo cho h2.
```

Poisson INCONCLUSIVE: khong duoc chua bang cach tang seed vo han (poisson L3
can ~384 seed o muc link). O muc path can it hon nhieu nhung van chua du voi
n = 5. Bao cao INCONCLUSIVE kem CI la ket luan hop le.

## 10. Chan Doan Ngay 2026-08-07: Tach Ba Thanh Phan Cua `A' - A`

`A' - A` bac cau qua hai chien dich cach nhau nhieu thang, nen no KHONG phai
thuan tuy topology:

```text
A' - A = (chuyen topology) + (noi suy bang tra) + (drift may/kernel theo thoi gian)
```

Muc 10.1-10.3 tach ba thanh phan nay. Khong ton them phut may nao cho 10.1-10.2.

### 10.1 Phan Bo Hang Doi Trung Khit -- Co Che KHONG O Tang Arrival

So phan vi hang doi (da tru `static_ms`) giua A' va Phase L noi suy:

```text
|Delta mean| <= 0.21 ms   |Delta p90| <= 0.29 ms   |Delta p95| <= 0.23 ms
|Delta p99| <= 0.53 ms    |Delta sd|  <= 0.13 ms
```

Tren hang doi 9-30 ms, `p99` khop trong 0.07 ms o 5/6 o. Voi h2, `p99` gan sat
tran buffer o CA HAI phia (vd L2: 26.217 vs 26.178, tran 26.208).

**!! SUA (2026-08-07, xem Amendment 13 muc 2). Ket luan duoi day SAI. Giu lai
nguyen van de theo vet.**

~~Ket luan co che: neu burst bi lam muot tren duong den shaper (CPU/softirq
batching, OVS datapath cua tandem) thi `sd` va `p99` cua A' phai THAP hon ro
ret. Chung khong. Vay gia thuyet "lam muot burst" bi loai; chenh lech loss
sinh ra o TANG DROP chu khong o tang arrival.~~

Loi lap luan: bien delay bi KIEM DUYET (censored) o tran buffer, nen "phan bo
delay khop" KHONG phai bang chung loai tru. Xem Amendment 13 muc 2. Chinh doan
tren da tu ghi "p99 gan sat tran o CA HAI phia" -- do la dau hieu censoring,
khong phai dau hieu hai phan bo giong nhau.

### 10.2 Noi Suy Bang Tra: Lon Hon Uoc Luong Cu ~20 Lan

**!! SUA (2026-08-07, xem Amendment 13 muc 1). Toan bo muc nay SAI vi lay luoi
tu `campaign_state.json` (chi chien dich 20R.4) thay vi tu
`truth_table.parquet` (da tron Phase L + 20R.4). Luoi that DEU 0.02. Giu lai
nguyen van de theo vet.**

~~Luoi truth table quanh diem can dung KHONG min o vung bao hoa:~~

```text
L1 rho = 0.8575  nam giua luoi 0.840 va 0.860   (khoang 0.02)
L2 rho = 0.9775  nam giua luoi 0.960 va 1.040   (khoang 0.08)   <- SAI
L3 rho = 0.9875  nam giua luoi 0.960 va 1.040   (khoang 0.08)   <- SAI
```

`TruthTable.delay_loss` noi suy TUYEN TINH (`np.interp`). Ham loss loi manh o
vung nay, nen day cung nam TREN duong cong -> gia tri tra ve bi THIEN LECH CAO
mot cach he thong. Uoc luong do lech bang fit bac hai cuc bo (4 diem luoi gan
nhat):

```text
mode lnk | bias_interp  Dloss_quan_sat | phan giai thich duoc
pois L3  |   -0.001807      -0.001785  | ~100%
pois L2  |   -0.001857      +0.000358  | qua muc
h2   L2  |   -0.000511      -0.002712  | 19%
h2   L1  |   -0.000113      -0.002567  | 4%
h2   L3  |   -0.000191      -0.008231  | 2.3%
```

~~Uoc luong cu trong muc 9.4 ("sai so noi suy ~8e-5") THAP HON thuc te khoang 20
lan o cac o poisson. Sua lai o day.~~

Bang tren la LEAVE-OUT SENSITIVITY voi khoang cach ~0.08-0.10, khong phai bias
cua estimator dang dung. Bias that (luoi 0.02) nho hon ~20 lan. So dung o
Amendment 13 muc 1.

Hai he qua:

```text
- Toan bo thieu hut cua poisson L3 co the giai thich bang noi suy. Cong voi
  muc 9.3 (poisson khong con o nao FAIL sau RC5), poisson khong con bang chung
  bat thuong nao.
- h2 L3 -- so hang chi phoi -- chi duoc giai thich 2.3%. Noi suy KHONG cuu
  duoc h2.
```

### 10.3 Drift Cua May: Loss On Dinh, Delay Co Dich Nhe

Sentinel cua Phase L chi tung bao ve `q_mean_ms`; cot `loss` chua bao gio duoc
kiem drift. `measurements/sentinel_loss_recheck.py` chay lai dung o sentinel
(`h2 | bw=6 | q=13 | rho=0.90 | seed=999`) tren `SplitQdiscTopo` hom nay, 5 lan
lap; 1 lan fail gate `late=0.0012` va bi loai dung theo quy tac cua Phase L.

```text
truong     hom nay (n=4)        Phase L (n=19)       z_mean   z_welch   ket luan
loss       0.064104 +-0.000217  0.063904 +-0.000128   +1.57    +1.78    ON DINH
q_mean_ms  10.904064 +-0.014085 10.868010 +-0.014864  +2.43    +4.61    DRIFT
```

`direct_packets_delta = 0` o ca 5 lan chay.

Sua mot loi thiet ke test trong chinh module nay: co `drift` ban dau dung
`z_mean` (chia do lech cua TRUNG BINH n mau cho sd cua MOT run). Phep do
understate muc y nghia khoang `sqrt(n)`. Da doi sang `z_welch` (two-sample,
dung SE ca hai ve). Sau khi sua, `q_mean_ms` chuyen tu "on dinh" sang DRIFT.

Doc ket qua:

```text
LOSS -- cot quan trong -- KHONG drift. Va uoc luong diem la +0.0002
(hom nay CAO hon Phase L), tuc NGUOC DAU voi thieu hut -0.0026..-0.0082 cua
A' - A. Hieu chinh drift se lam thieu hut LON HON, khong nho di.
=> Drift KHONG giai thich duoc phat hien h2.

DELAY drift +0.036 ms, that ve thong ke nhung bang 0.33% cua 10.87 ms va
cung nguoc dau voi Delta delay cua A' - A (-0.51 ms). Ket luan "delay chuyen
topology tot" vi the la KET LUAN THAN TRONG, khong phai bi drift lam dep.
```

### 10.4 Trang Thai Sau Ba Chan Doan

```text
poisson : khong bias (RC5), thieu hut giai thich duoc bang noi suy, khong drift.
          -> KHONG con bat thuong. Ket luan: INCONCLUSIVE do power, kem CI.

h2      : khong phai arrival smoothing (10.1)
          khong phai noi suy      (10.2, chi 2.3%)
          khong phai drift        (10.3, va nguoc dau)
          -> phan du -0.0115 loss van chua co loi giai thich vo hai nao.
             Day la ung vien FINDING that su, o TANG DROP.

Buoc tiep theo con thieu de ket luan: branch A0 (`SplitQdiscTopo` hom nay, tai
DUNG rho = 0.8575/0.9775/0.9875, CUNG SEED 101-105 voi A'). A0 dong thoi:
  - xoa han thanh phan noi suy (do tai dung rho),
  - xoa han thanh phan drift (cung ngay),
  - va cho phep GHEP CAP theo seed -> triet tieu phuong sai seed-to-seed,
    thu ma tang so seed khong lam duoc (xem muc 7.3 cap nhat).
`A' - A0` khi do moi la topology transfer thuan tuy.
```
