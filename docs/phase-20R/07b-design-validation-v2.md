# Phase 20R.6 Design Validation v2

Trang thai: final sau cascade seed 101-108 va band/scan `n=120000`.

## 1. Estimand

Co hai dai luong khac nhau:

- **G6-TRANSFER**: bang tra mot-link do tren SplitQdiscTopo co chuyen giao duoc
  sang TandemTopo khong? Cong thuc: `A' - A`.
- **G6-CASCADE**: chi phi do end-to-end tren duong 3-link co bang tong chi phi
  tung link do rieng trong cung topology/session/seed/background khong? Cong
  thuc: `C - sum(B_i)`.

Luat dung som cua Amd 11 ap dung cho dinh nghia cu co `A`; no khong ap dung
cho `C - sum(B_i)` vi `A` khong xuat hien trong estimand cascade.

## 2. Estimator Loss

Cascade loss dung `probe_loss`, khong dung `bg_loss`.

Ly do:

- Nhanh C khong co background loss end-to-end; background la link-local.
- Phase L truth table loss cung duoc do bang probe, nen estimator nhat quan.
- Tren link probe di qua, lich nen khop giua B/Li va C; link khong di qua duoc
  phep lech do carve-out va khong anh huong phep do probe.

Pham vi: voi `h2`, probe Poisson muot va nen h2 bursty co the co ti le loss
khac nhau trong cung FIFO. Ket qua cascade loss la cascade ma dong tham chieu
probe trai qua, khong phai loss cua chinh nen h2.

## 3. False Alarms

Hai bao dong gia da duoc tach khoi ket luan khoa hoc:

- Rho gate preflight 120s: nguong cu `0.003` chi tuong duong 1.80 sigma cua
  nhieu dem goi, nen xac suat bao dong gia tren 6 diem B khoang 36%. Fix:
  Poisson fixed-count va gate duration-aware.
- Pairing digest guard: `trajectory_digest` cua ca ba link khong the khop giua
  B/Li va C do carve-out dung thiet ke. Guard dung la digest cua link probe di
  qua: `load_schedule_digests[link_dich]`.

## 4. Band-First Rule

Ket luan duoc bao cao theo band cua residual:

```text
K1 err in [0.05, 0.40]
K2 d_sla_lower >= 0.03
K3 Spearman(err, z) > 0
K4 path ranking preserved
K5 family order preserved
```

`safety_published` la min qua bien the duoc support, dung conservative lower
bracket. Voi `joint`, scan dung QT-3: truc quet la lambda khong thu nguyen, moi
mode bi bom theo endpoint CI90 cua chinh no.

## 5. Transfer Result

Artifact final:

- `results/phase-20R/band_v2_transfer.json`
- `results/phase-20R/breakdown_scan_transfer_qt3_n120k.json`

Headline transfer band `n=120k` van giu:

```text
|Delta err| <= 0.004020
d_sla >= 0.0898 vs floor 0.03
path ranking P1 < P3 < P4 < P2 preserved
```

Transfer scan QT-3:

```text
safety_published = 3.713969993755349
binding          = poisson / loss / common_mode
first_broken     = K4_path_ranking_preserved
first_broken_cell= poisson@0.925
```

## 6. Deterministic K4

`K4_path_ranking_preserved` khong doc seed va khong doc `n`; no tinh ranking
tu bang tra tai mot vector `rho` co dinh. Artifact scan van ghi K4 trong ket
qua tong, nhung metadata tach:

```text
scan_split_policy.K4_path_ranking_preserved =
  deterministic_path_ranking_no_seed_no_n
k4_deterministic.n_dependence = none
```

K1/K2/K3/K5 van la ket luan Monte Carlo va phai dung `n` preregistered.

## 7. Power And Stability

Pilot 3 seed da duoc tinh lai sau khi sua guard link-dich:

```text
poisson/loss      sd=0.00144245   sd95_hi=0.00636901   n_seed@0.005=5
poisson/delay_ms  sd=0.0885187    sd95_hi=0.390845     n_seed@0.44=3
h2/loss           sd=0.000758182  sd95_hi=0.00334767   n_seed@0.005=2
h2/delay_ms       sd=0.0761877    sd95_hi=0.336399     n_seed@0.44=2
```

Full run seed 104-108 se dua tong seed len 8. Sau khi run xong, phai chay:

```bash
python3 tools/check_phase20r6_structure.py
python3 tools/check_sd_stability.py --out results/phase-20R/sd_stability_s101_108.json
```

`check_sd_stability.py` chi in `sd`, khong in residual mean.

## 8. Cascade Result

Artifact final:

- `results/phase-20R/residual_cascade.json`
- `results/phase-20R/band_v2_cascade.json`
- `results/phase-20R/breakdown_scan_cascade.json`
- `results/phase-20R/tmux_logs/p20r6_scan_cascade.log`

Lenh da chay:

```bash
python3 -m measurements.cascade_residual \
  --branch-b results/phase-20R/branch_b_fixed_pilot3.json,results/phase-20R/branch_b_fixed_s104_108.json \
  --branch-c results/phase-20R/branch_c_fixed_pilot3.json,results/phase-20R/branch_c_fixed_s104_108.json \
  --rho-bar 0.925 --out results/phase-20R/residual_cascade.json

python3 -m measurements.band_v2 --residual results/phase-20R/residual_cascade.json \
  --mode band --rho-bar 0.925 --seeds 101,102,103,104,105 --n 120000 \
  --out results/phase-20R/band_v2_cascade.json

python3 -m measurements.band_v2 --residual results/phase-20R/residual_cascade.json \
  --mode scan --rho-bar 0.925 --seeds 101,102,103,104,105 --n 120000 \
  --variants common_mode \
  --out results/phase-20R/breakdown_scan_cascade.json
```

Cascade residual la muc duong (`per_path`), nen scan cong bo chi dung
`common_mode`. `differential`, `full`, va `joint` khong xac dinh.

Residual `C - sum(B_i)` deu am, khop du doan pay-bursts-only-once:

```text
mode     channel    r_path       se          CI90
poisson  loss       -0.009522    0.000373    [-0.010135, -0.008908]
poisson  delay_ms   -0.746400    0.059438    [-0.844166, -0.648633]
h2       loss       -0.009351    0.000432    [-0.010062, -0.008641]
h2       delay_ms   -0.449241    0.030064    [-0.498692, -0.399791]
```

Moi hang co `n_pairs = 8`; khong CI90 nao chua 0. DC-C3 chi gate `poisson` va
dat: `max |z| applicable = 2.084 <= 3.0`. `h2` DC-C3 khong gate, dung §38.

Band cascade `n=120000`:

```text
poisson/loss/common_mode: d_err=[+0.024084,+0.029663],
  d_sla shift=[-0.079342,-0.067121], clip_ratio=43.20%,
  band_is_lower_bound=true, worst_endpoint_resolvable=true
poisson/delay/common_mode: d_err=[0,0], d_sla shift=[+0.001388,+0.001448]
h2/loss/common_mode: d_err approx 0, d_sla shift=[-0.006391,-0.005804]
h2/delay/common_mode: d_err=[0,0], d_sla shift=[+0.003377,+0.003525]
```

`band_v2_cascade.json` co 16 rows: `common_mode` supported cho 4 hang;
`differential`, `full`, va `joint` supported=false cho 12 hang con lai.

Scan cascade `n=120000`, `--variants common_mode`:

```text
safety_published = 0.868750
binding          = poisson / loss / common_mode
r*               = [0.008805, 0.008868]
first_broken     = K4_path_ranking_preserved
first_broken_cell= poisson@0.925
K4 detail        = P1,P3,P4,P2 -> P3,P1,P4,P2

poisson/delay safety = [4.533203, 4.533301], first_broken=K2
h2/loss safety       > 10.00, no broken conclusion in scan range
h2/delay safety      > 10.03, no broken conclusion in scan range
```

Kiem co che K4 tai `rho_bar=0.925`:

```text
poisson path cost:
  P1 = 112.9658
  P3 = 120.5115
  |P1-P3| = 7.5457  # khe nho nhat trong 6 cap

h2 path cost:
  khe nho nhat la |P2-P4| = 19.6496
```

Viec cascade scan lam `poisson@0.925` doi ranking `P1,P3,P4,P2` thanh
`P3,P1,P4,P2` xay ra dung o cap co khe quyet dinh nho nhat cua o binding. Day
la co che mong doi: nhieu dong he thong lat cap gan nhau nhat truoc.

Ket luan: twin cong tinh la bao thu theo dau am da ky, nhung do bao thu cascade
du lon de lam lat K4 tai o `poisson@0.925` theo kenh `loss/common_mode`.
Phat bieu transfer van co safety rieng `3.71397`; phat bieu cascade phai ghi
pham vi hieu luc nay thay vi danh PASS gate-first.

Caveat can di kem ket qua: voi `poisson/loss`, `clip_ratio=43.20%`, nen bien
am la can duoi cua tac dong that trong mo hinh nhieu cong bi chan tai 0. Ngoai
ra residual cascade do o muc duong; quy ve bang tra bang chia deu cho 3 link la
xap xi tuyen tinh, kem chinh xac hon khi loss per-link len toi cap `0.075`.
Tat ca artifact phan tich van co `git_dirty=true` vi repo dang chua commit code
va artifact ket qua.

Ghi chu provenance sau commit: cac artifact cascade final ghi
`git_commit = c4fb70d75605e2539b357841c39be8cd547c6307` voi
`git_dirty = true` tai thoi diem sinh so. Toan bo code, docs, compact JSON, va
manifest raw sha256 da duoc commit tai `2570585`. Cac input chinh
(`truth_table`, `calibration`, `residual`, va raw manifest) co sha256 trong
artifact/manifest, nen so lieu co the tai lap tu checkpoint da commit ma khong
can chay lai Mininet.

## 9. Threats And Scope

- Cascade loss la loss cua dong tham chieu probe trong nen, khong phai loss cua
  nen h2 bursty.
- `c_a_aggregate_with_probe_by_link` da duoc ghi de mo ta diem van hanh cua
  carve-out. Viec bom residual cascade len bang tra gia dinh residual on dinh
  theo `c_a`; day la pham vi hieu luc, khong phai gate da chung minh.
- DC-C3b van nen chay sau khi Mininet ranh: h2 probe sinh tu h2, 2 seed, de
  xac nhan chenh lech probe/background la do qua trinh den.
