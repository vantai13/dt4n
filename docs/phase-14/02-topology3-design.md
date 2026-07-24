# Thiet ke topology3 - 3 duong + su kien ngau nhien vo huong

Ngay: 2026-07-24

## Chuoi suy luan tu that bai den thiet ke

| Lan | Chet vi | Do duoc | Rang buoc rut ra |
|:---:|---|---|---|
| 1,2 | The gioi tinh | E\|rho(t)-rho(t-z)\| ~ 0 | Phai co su kien |
| 3 | Duong troi | max_a P(a*|fresh)=0.665 | Khong co path prior tinh |
| 4 | z ro vao obs | trend co huong | Su kien vo huong |
| 14.1 | q_margin tang theo z | 0.41 -> 1.41 | Drift khuech tan |

## Che do dinh tuyen

Phase 8-11 (`routing_2path`) la hop-by-hop: agent quyet dinh o moi node va co
the sua sai o hop sau neu topology cho phep.

Phase 14+ (`routing3`) la path-selection: agent cam ket mot lan tai `SRC` vao
mot trong ba duong. Day la mo hinh hop le cho MPLS-TE, segment routing, SD-WAN
path selection.

Ly do chon path-selection cho RQ0: kha nang khac phuc quyet dinh sai lam giam
gia tri cua AoI. Path-selection la che do thuan loi nhat de AoI co gia tri; neu
AoI van khong co headroom o day thi do la ket luan manh.

## Primary/backup ngau nhien

Topology co 3 duong song song, cau truc doi xung:

    SRC -> A1 -> B1 -> DST
    SRC -> A2 -> B2 -> DST
    SRC -> A3 -> B3 -> DST

Moi duong co cung 3 hop, delay, bandwidth, queue size. Cau truc primary/backup
duoc mo hinh hoa bang load state, khong bang hard-code path identity:

| role | load band |
|---|---|
| primary | `(0.35, 0.50)` |
| backup1 | `(0.60, 0.72)` |
| backup2 | `(0.70, 0.82)` |

Moi observation boc ngau nhien path nao giu role nao. Vi vay:

- tai mot thoi diem cu the van co duong tot nhat;
- tinh trung binh qua episode, `P(P1 best) ~= P(P2 best) ~= P(P3 best) ~= 1/3`;
- agent khong hoc duoc prior tinh "mac dinh P1".

Do dieu kien (2), `P(a* | fresh)` voi 2000 mau:

```text
P(a* | fresh): {'P2': 0.326, 'P1': 0.333, 'P3': 0.341}
max = 0.341  (< 0.45)
```

## Dong hoc v2

Ba loi ky thuat cua vong dau da sua:

1. `apply_event()` tung resample muc tai moi lan goi.
   Bay gio event outcome duoc dong bang trong event object:
   `crash_level`, `free_level`, hoac `reset_levels`.
   `apply_event(levels, event)` khong con tham so `rng`, nen deterministic.
2. Noise cong o cuoi duoc doi ten thanh `JITTER_SIGMA` va tach ra
   `observe_levels()`. Jitter la instantaneous load jitter, khong phai state
   dynamics tich luy.
3. Sampler3 khong giu hidden schedule cho counterfactual z.
   `roll_forward(obs, z)` bat dau tu public `obs['rho']`, roi sample mot future
   event history moi moi lan goi. Day moi la uoc luong `E[R | o, z]`, khong phai
   `E[R | o, z, latent schedule]`.

Event process:

```text
Moi buoc co xac suat EVENT_RATE xay ra event.
P(co it nhat 1 event trong z buoc) = 1 - (1 - EVENT_RATE)^z
```

`EVENT_RATE` co the override bang env var `ROUTING3_EVENT_RATE`. Default hien
tai la `0.12`, rate tot nhat trong sweep ben duoi, nhung van FAIL gate.

## Guardrails da chay

| Kiem tra | Ket qua |
|---|:---:|
| 3 duong cung delay/bw/queue | PASS |
| initial sampler doi xung marginal theo path identity | PASS |
| crash_path marginal gan 1/3 moi duong | PASS |
| role load bands duoi cliff, `CRASH_LOAD` vuot cliff | PASS |
| frozen events deterministic | PASS |
| `P(a* | fresh).max < 0.45` | PASS |
| `roll_forward(obs, z=0)` tra dung `obs['rho']` | PASS |
| `reward_of(action, true_world)` khong nhan obs/z | PASS |
| `rl/routing3/link_model.py` giong `rl/routing_2path/link_model.py` | PASS |
| `rl/routing3/reward3.py` giong `rl/routing_2path/reward_r.py` | PASS |

## OFAT - Vong 1

Vong 1 dung topology 3 duong doi xung voi event process ban dau. Ket qua:

| Vong | Sua gi | q_margin(0) | q_margin(12) | disagree | regret | gap | lower CI95 | verdict |
|:---:|---|---:|---:|---:|---:|---:|---:|:---:|
| 1 | Tang `CRASH_LOAD` | 0.0641 | 0.0477 | 0.4375 | 0.0354 | 0.0155 | 0.0129 | FAIL |

Chan doan: `disagree_rate` dat muc tieu, nhung `decision_regret` qua thap.

## OFAT - Vong 2: sua sampler/event semantics + primary/backup + sweep EVENT_RATE

Vong 2 gom cac sua loi bat buoc (#13/#14/#15) va them primary/backup ngau
nhien. Sau do chi sweep mot tham so: `EVENT_RATE`.

Command mau:

```bash
ROUTING3_EVENT_RATE=0.08 python3 -m measurements.pilot_marginalized \
  --topology routing3 \
  --cases 400 --mc-samples 200 --seed 0 \
  --out results/phase-14/pilot_routing3_rate008_seed0.json
```

| EVENT_RATE | q_margin(0) | q_margin(12) | disagree | regret | gap | lower CI95 | verdict |
|---:|---:|---:|---:|---:|---:|---:|:---:|
| 0.03 | 0.0366 | 0.0305 | 0.0725 | 0.0121 | 0.0009 | 0.0004 | FAIL |
| 0.05 | 0.0364 | 0.0283 | 0.1175 | 0.0196 | 0.0023 | 0.0015 | FAIL |
| 0.08 | 0.0373 | 0.0294 | 0.2175 | 0.0246 | 0.0054 | 0.0039 | FAIL |
| 0.12 | 0.0375 | 0.0320 | 0.2350 | 0.0297 | 0.0070 | 0.0053 | FAIL |

## Chan doan vong 2

Primary/backup ngau nhien giu duoc dieu kien (2), va `EVENT_RATE` dieu khien
`disagree_rate` dung huong: rate tang thi disagree tang.

Nhung `decision_regret` van rat thap, toi da 0.0297 tai rate 0.12. Dieu nay
noi rang expected-Q giua cac action van qua sat nhau. Event random theo path
identity lam cac duong doi xung hoa qua manh trong ky vong; biet z co doi
action nhieu hon, nhung sai/ dung van khong dat.

Ket luan: khong duoc sang train/Gym env. Vong tiep theo phai tang regret bang
mot thay doi dong hoc co ly do, khong sua reward/link model.

Ung vien cho vong tiep theo: event state phai gan voi role/rank hien tai thay
vi crash/free path identity hoan toan ngau nhien. Vi du: primary/current-best co
rui ro degrade theo thoi gian, trong khi backup co the tro thanh safe path.
Path identity van phai doi xung; chi role/rank moi anh huong risk.

## Audit sau chan doan reward

Kiem tra ngay 2026-07-24 cho thay `Sampler3Path.reward_of()` da dung reward
that cua Phase 11/route model:

```text
delay_ms = link_model.total_delay_ms(rho_offered)
loss     = link_model.loss_rate(rho_offered)
reward   = reward3.step_reward(delay_ms, loss, arrived=last_hop).total
```

Vi vay ket qua FAIL hien tai khong phai do reward gia kieu
`-util - 3*loss - hop_cost`. Nguyen nhan chinh la load band cua primary/backup
dang nam trong vung duoi cliff, noi delay/reward con kha phang.

Bang link model:

| rho | util measured | loss |
|---:|---:|---:|
| 0.4200 | 0.4532 | 0.0000 |
| 0.6600 | 0.7121 | 0.0000 |
| 0.7600 | 0.8200 | 0.0000 |
| 0.9000 | 0.9711 | 0.0000 |
| 0.9275 | 1.0000 | 0.0008 |
| 1.0500 | 1.0000 | 0.1173 |
| 1.2000 | 1.0000 | 0.2277 |

Path reward 3-hop tuong ung:

| rho moi bottleneck | path reward |
|---:|---:|
| 0.4200 | 4.4681 |
| 0.6600 | 4.4292 |
| 0.7600 | 4.4130 |
| 0.9275 | 3.6845 |
| 1.0500 | 3.4514 |
| 1.2000 | 3.2307 |

Chenh giua primary/backup trong vung 0.42-0.76 chi khoang 0.055 reward/path,
trong khi reward roi manh khi cham/vuot cliff. Do do can day risk future gan
hon voi cliff hoac tao event risk phu thuoc role/rank.

Rerun mac dinh sau audit:

| Topology | gap | lower CI95 | disagree | regret | verdict |
|---|---:|---:|---:|---:|:---:|
| routing_2path | 0.0056 | 0.0032 | 0.0525 | 0.1063 | FAIL |
| routing3, EVENT_RATE=0.12 | 0.0070 | 0.0053 | 0.2350 | 0.0297 | FAIL |

Spread diagnostic cua routing3:

| z | bottleneck spread obs | bottleneck spread after z |
|---:|---:|---:|
| 0 | 0.3332 | 0.3332 |
| 1 | 0.3392 | 0.3928 |
| 3 | 0.3323 | 0.4701 |
| 5 | 0.3309 | 0.5298 |
| 8 | 0.3353 | 0.5749 |
| 12 | 0.3346 | 0.6467 |

Ket luan cua audit: hidden future context da tao them dispersion khi z tang,
nhung expected-Q margin van nho. Vong tiep theo nen la OFAT tren
role/state-dependent crash risk, vi du `CRASH_BIAS_TEMP`, thay vi sua reward.

## OFAT - Vong 3: `CRASH_BIAS_TEMP`

Them `ROUTING3_CRASH_BIAS_TEMP` vao event sampler:

```text
CRASH_BIAS_TEMP = 0.0  -> crash path uniform nhu baseline
CRASH_BIAS_TEMP > 0.0  -> path co load hien tai cao hon de crash hon
```

Risk phu thuoc state hien tai, khong phu thuoc ten path. Event sampler phai ap
tuan tu vi event sau dung state sau event truoc.

Sweep voi `EVENT_RATE=0.12`, `cases=400`, `mc=200`, `seed=0`:

| CRASH_BIAS_TEMP | gap | lower CI95 | disagree | regret | q_margin | verdict |
|---:|---:|---:|---:|---:|---:|:---:|
| 0.0 | 0.0079 | 0.0063 | 0.2825 | 0.0280 | 0.0312 | FAIL |
| 0.5 | 0.0044 | 0.0032 | 0.2000 | 0.0222 | 0.0342 | FAIL |
| 1.0 | 0.0023 | 0.0015 | 0.1200 | 0.0195 | 0.0397 | FAIL |
| 2.0 | 0.0005 | 0.0001 | 0.0300 | 0.0156 | 0.0547 | FAIL |
| 4.0 | 0.0001 | -0.0000 | 0.0125 | 0.0094 | 0.0761 | FAIL |
| 6.0 | 0.0001 | -0.0000 | 0.0075 | 0.0080 | 0.0861 | FAIL |

Guardrail fresh optimal voi moi temp deu `max_fresh=0.335`, counts xap xi
`P1=669, P2=661, P3=670`, nen khong co prior tinh theo ten path.

Chan doan: bias duong theo high-load lam policy on dinh hon tu public obs.
`q_margin` tang, nhung `disagree_rate` giam manh, nen AoI headroom giam. Day
la ket qua FAIL co ich: role/state-dependent crash risk theo huong "duong tai
cao de crash" khong tao them gia tri cho AoI trong san khau nay.

## OFAT - Vong 4: dich role bands vao vung cliff

Vong 3 chi ra nguyen nhan goc: role bands cu nam trong vung `loss = 0`, nen
reward chi con delay va `decision_regret` bi nen xuong khoang 0.03. Vong 4
dich role bands vao vung doc quanh cliff va khoa `CRASH_BIAS_TEMP=0.0`.

Bang loss quanh cliff:

| rho | util | loss | d(loss) |
|---:|---:|---:|---:|
| 0.8500 | 0.9171 | 0.0000 | +0.0000 |
| 0.8800 | 0.9495 | 0.0000 | +0.0000 |
| 0.9000 | 0.9711 | 0.0000 | +0.0000 |
| 0.9275 | 1.0000 | 0.0008 | +0.0008 |
| 0.9400 | 1.0000 | 0.0141 | +0.0133 |
| 0.9600 | 1.0000 | 0.0346 | +0.0205 |
| 0.9800 | 1.0000 | 0.0543 | +0.0197 |
| 1.0000 | 1.0000 | 0.0732 | +0.0189 |
| 1.0200 | 1.0000 | 0.0914 | +0.0182 |
| 1.0500 | 1.0000 | 0.1173 | +0.0260 |
| 1.1000 | 1.0000 | 0.1575 | +0.0401 |
| 1.1500 | 1.0000 | 0.1941 | +0.0366 |
| 1.2000 | 1.0000 | 0.2277 | +0.0336 |
| 1.3000 | 1.0000 | 0.2871 | +0.0594 |

Path reward voi access/egress giu background `0.25`, chi bottleneck thay doi:

| bottleneck rho | path reward |
|---:|---:|
| 0.8000 | 4.4066 |
| 0.8800 | 4.3936 |
| 0.9200 | 4.3871 |
| 0.9275 | 3.6845 |
| 0.9600 | 3.6169 |
| 1.0200 | 3.5033 |
| 1.1000 | 3.3711 |
| 1.2500 | 3.1689 |

Them `ROUTING3_BAND_PROFILE` de sweep do rong band:

| profile | primary | backup1 | backup2 | crash | free |
|---|---|---|---|---|---|
| cliffband | 0.80-0.88 | 0.92-0.96 | 0.99-1.04 | 1.10-1.25 | 0.55-0.70 |
| narrow | 0.84-0.86 | 0.93-0.94 | 1.01-1.02 | 1.10-1.25 | 0.55-0.70 |
| wide | 0.75-0.90 | 0.90-0.98 | 0.98-1.08 | 1.10-1.25 | 0.55-0.70 |

Dieu kien (2) van dat voi ca ba profile:

| profile | max P(a* fresh) |
|---|---:|
| cliffband | 0.3405 |
| narrow | 0.3405 |
| wide | 0.3395 |

Ket qua meter, `EVENT_RATE=0.12`, `CRASH_BIAS_TEMP=0.0`, `cases=400`,
`mc=200`, `seed=0`:

| profile | gap | lower CI95 | disagree | regret | q_margin | verdict |
|---|---:|---:|---:|---:|---:|:---:|
| cliffband | 0.0004 | 0.0001 | 0.0225 | 0.0178 | 0.3577 | FAIL |
| narrow | 0.0004 | 0.0000 | 0.0225 | 0.0164 | 0.3352 | FAIL |
| wide | 0.0008 | 0.0003 | 0.0400 | 0.0195 | 0.3378 | FAIL |

Chan doan: vong 4 da lam `q_margin` tang tu khoang 0.03 len khoang
0.34-0.36, dung muc tieu tang bien do Q. Nhung no cung lam bai toan qua de
tu public obs: `a*(z)` va `a*_marg` giong nhau 96-98% so case.

Trade-off hien tai:

```text
role cu duoi cliff:      disagree cao hon, regret qua nho -> gap thap
role quanh/tren cliff:   regret/q_margin cao, disagree qua nho -> gap thap
```

Ket luan: FAIL cua routing3 khong con la loi code cuc bo. No den tu viec hai
dieu kien can kho dong thoi: AoI phai lam doi action thuong xuyen, va quyet
dinh sai phai ton reward lon. Cac cau hinh hien tai chi dat mot trong hai dieu
kien moi lan.

## Phat hien chinh: dinh luat danh doi headroom

Quan sat qua bon vong va sweep:

| cau hinh | disagree | regret | q_margin | gap |
|---|---:|---:|---:|---:|
| 2path hop-by-hop | 0.053 | 0.106 | ~1.0 | 0.0056 |
| 3path v3 duoi cliff | 0.283 | 0.028 | 0.031 | 0.0079 |
| 3path v4 quanh cliff | 0.023 | 0.018 | 0.358 | 0.0004 |
| 3path bias=6 | 0.008 | 0.008 | 0.086 | 0.0001 |

Sweep `CRASH_BIAS_TEMP`:

```text
temp:  0.0    0.5    1.0    2.0    4.0    6.0
gap:   .0079  .0044  .0023  .0005  .0001  .0001
```

Ba can thiep khac nhau, gom bias theo tai, dich vung tai len cliff, va doi do
rong band, deu cho cung hanh vi:

```text
q_margin tang  ->  disagree giam
```

Phat bieu:

```text
gap = disagree_rate x decision_regret

disagree_rate  ~ P(|anh huong cua z| > q_margin)
decision_regret <= q_margin tai vung bien
```

Ly do regret bi chan: disagreement chi xay ra khi hai action gan nhau ve Q.
Neu chung cach xa, z khong lat duoc argmax. Nen thiet hai khi lat bi chi phoi
boi do rong vung bien, khong phai khoang cach toan cuc giua cac duong.

Bang chung: regret nam trong 0.016-0.030 qua cac vong, du `q_margin` thay doi
tu 0.031 den 0.358. Hai thua so keo nguoc nhau, nen gap bi ep nho tu ca hai
phia.

Gia thuyet cuoi: ham muc tieu hien tai la risk-neutral. Phase 14 dang tim hanh
vi hedge, nhung Bayes-optimal voi `E[R]` chi chon ky vong cao nhat. Hedge chi
noi len khi objective phat phuong sai hoac duoi xau. Vi vay them thang do
exploratory `CVaR_alpha` vao meter, khong sua `reward3.py`, de kiem tra risk
sensitive objective truoc khi quyet dinh doi huong de tai.

## Exploratory: CVaR objective trong meter

Them `--objective {mean,cvar}` va `--cvar-alpha` vao
`measurements/pilot_marginalized.py`. Default van la `mean`, nen thang do da
pre-register khong doi. `cvar` chi gom cac reward sample bang trung binh cua
`alpha` phan ket qua te nhat, va khong sua `reward3.py`.

Ket qua voi routing3 v4 `cliffband`, `EVENT_RATE=0.12`,
`CRASH_BIAS_TEMP=0.0`, `cases=400`, `mc=200`, `seed=0`:

| run | objective | alpha | gap | lower CI95 | disagree | regret | q_margin | verdict |
|---|---|---:|---:|---:|---:|---:|---:|:---:|
| routing3 | cvar | 0.1 | 0.0123 | 0.0101 | 0.4250 | 0.0289 | 0.1716 | FAIL |
| routing3 | cvar | 0.2 | 0.0121 | 0.0096 | 0.2800 | 0.0433 | 0.2589 | FAIL |
| routing3 | cvar | 0.3 | 0.0057 | 0.0039 | 0.1550 | 0.0365 | 0.3316 | FAIL |
| 2path negative control | cvar | 0.2 | 0.0056 | 0.0032 | 0.0525 | 0.1063 | 1.1612 | FAIL |

Doc ket qua:

```text
mean v4 cliffband: gap=0.0004
CVaR alpha=0.1:   gap=0.0123
CVaR alpha=0.2:   gap=0.0121
```

CVaR lam routing3 tang headroom ro so voi mean v4, va negative control 2path
van FAIL, nen no khong tu tao gap gia tren moi topology. Nhung `gap` van thap
hon threshold 0.10 khoang 8 lan. Ket luan: risk-sensitive objective la gia
thuyet co tin hieu, nhung chua du manh de doi de tai hoac sang train. Neu muon
theo huong nay, can ghi ro day la exploratory sau khi thay so, va phai hieu
chuan lai threshold/objective trong design rieng.

## Noise-floor calibration attempt

Sau khi ghi cam ket truoc vao `00-design.md`, them
`measurements/noise_floor.py` de do seed-to-seed noise cua
Bayes-marginalized policy ma khong train.

Kiem dinh cong cu tren anchor `routing_2path` / `mean`, `seeds=10`,
`cases=200`, `mc=100`:

```text
performance mean  : 4.4770
noise_floor       : 0.0095
threshold = 2x    : 0.0191
reference         : Phase 9 std_agent=0.045, old threshold=0.10
```

Ket qua nay lech xa anchor Phase 9 `std_agent=0.045`. Theo cam ket trong
`00-design.md`, khong duoc dung cong cu nay de hieu chuan lai threshold cho
routing3.

Chan doan: cong cu dang do seed-to-seed variance cua Bayes oracle/evaluation
sampling, khong do training-seed variance cua agent trong Phase 9. Oracle loai
bo training instability, nen noise floor thap hon la hop ly, nhung no khong
cung dai luong voi `std_agent` da neo threshold cu.

Ket luan: khong doi gate dua tren `noise_floor.py`. Neu can hieu chuan threshold
that su cho routing3/CVaR, phai do bang agent training seeds tren objective moi,
hoac ghi ro day la mot proxy khac va xin phe duyet truoc.
