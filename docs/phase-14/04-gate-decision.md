# PHASE 14 - QUYET DINH GATE

Ngay: 2026-07-24
Base Git: 64b92ac

## Ket Qua: Gate FAIL

Dieu kien (5) `headroom >= 0.10`: FAIL.

Cau hinh tot nhat da do:

```text
routing3, cliffband, CVaR alpha=0.1
gap_marginalized = 0.0123
lower CI95       = 0.0101
threshold        = 0.10
```

Thieu khoang 8 lan so voi gate da pre-register.

Da thu:

- 5 vong lap Phase 14
- 8 cau hinh chinh
- 2 objective: `mean`, `cvar`
- 3 band profile: `cliffband`, `narrow`, `wide`
- 6 muc `CRASH_BIAS_TEMP`
- 4 muc `EVENT_RATE`

Plan goc noi: sau 3 vong FAIL thi dung lai va mang so lieu gap GVHD. Da di
qua 5 vong; day la diem dung chinh thuc.

## Ba Con So Giai Thich Phase 11 Am

| Dai luong | Gia tri | Nghia |
|---|---:|---|
| `gap_marginalized` tot nhat | 0.0123 | headroom ly thuyet toi da da do |
| `noise_floor` moi truong | 0.0095 | dao dong cua Bayes oracle/evaluation |
| `std_agent` Phase 9 | 0.045 | dao dong giua cac lan train agent |

Ty le:

```text
gap / noise_floor = 1.3
gap / std_agent   = 0.27
```

Doc ket qua:

- Hieu ung CVaR la that: `gap` lon hon san nhieu moi truong khoang 1.3 lan.
- Hieu ung qua nho de song sot qua training variance: `gap` nho hon
  `std_agent` khoang 3.7 lan.
- Bon lan am cua Phase 11 khong can giai thich bang agent kem,
  hyperparameter sai, hay seed xui. Giai thich dinh luong don gian hon:
  hieu ung nho hon nhieu huan luyen.

## Power Analysis

Cong thuc xap xi cho so sanh hai nhanh, power 80%, alpha 0.05:

```text
n ~= 16 x (sigma / delta)^2
```

Voi `sigma = std_agent = 0.045`:

| So seed moi nhanh | Gap phat hien duoc |
|---:|---:|
| 5 | 0.0805 |
| 10 | 0.0569 |
| 20 | 0.0402 |
| 50 | 0.0255 |
| 100 | 0.0180 |
| 214 | 0.0123 |

So seed can cho cac gap da do:

| Cau hinh | gap | seed moi nhanh can |
|---|---:|---:|
| mean v4 | 0.0004 | 202500 |
| mean v3 | 0.0079 | 519 |
| CVaR alpha=0.1 | 0.0123 | 214 |
| nguong 0.10 | 0.1000 | 3 |

Phase 11 chay 10 seed moi nhanh. De phat hien gap tot nhat hien tai
`0.0123`, can khoang 214 seed moi nhanh, tong 428 lan train. Khong kha thi
trong pham vi hien tai.

## Sau Dong Gop Phuong Phap

1. Thuoc do moi:

```text
gap_marginalized = Bayes(o + z) - Bayes(o, marginalize z)
```

Negative control: thang cu bao GO sai, thang moi bao NO-GO dung tren topology
2-duong.

2. Phan ra:

```text
gap = disagree_rate x decision_regret
```

Phan ra nay khop qua cac cau hinh va giup biet FAIL do action it doi hay do
chon sai khong ton kem.

3. Dinh luat danh doi headroom:

```text
q_margin tang  ->  disagree_rate giam
```

Khi action cach xa nhau, z kho lat duoc argmax. Khi z lat duoc argmax, cac
action dang o vung bien nen regret bi chan nho.

4. Dieu kien (3) do bang bien lien tuc:

```text
CRASH_BIAS_TEMP: 0.0 -> 6.0
gap:             0.0079 -> 0.0001
```

Rui ro cang du doan duoc tu obs thi AoI cang du thua.

5. Dieu kien moi: risk-sensitivity.

Bayes-optimal voi `E[R]` khong hedge; no chi chon ky vong cao nhat. Thong tin
ve do tin cay cua observation nam o phuong sai/duoi xau, ma ky vong thu gon
phan bo ve mot so.

Bang chung:

```text
mean v4 cliffband: gap=0.0004
CVaR alpha=0.1:   gap=0.0123
```

CVaR lam gap tang 30 lan va negative control 2path van FAIL.

6. Power analysis noi ket gap voi so seed can thiet.

Day bien ket luan tu "khong tim thay hieu ung" thanh "hieu ung, neu co, nho
hon nguong phat hien cua thiet ke train kha thi".

## Noise-Floor Check

Da ghi cam ket truoc khi do trong `00-design.md`: chi dung nguong moi neu cong
cu noise-floor qua duoc anchor.

Ket qua anchor:

```text
python3 -m measurements.noise_floor --topology routing_2path \
  --objective mean --seeds 10 --cases 200 --mc-samples 100

noise_floor = 0.0095
threshold_2x = 0.0191
reference Phase 9 std_agent = 0.045
```

Cong cu khong tai tao duoc anchor Phase 9. Nguyen nhan hop ly: no do
evaluation variance cua Bayes oracle, khong do training variance cua learner.

Theo cam ket pre-registered, khong dung `noise_floor.py` de ha nguong gate.
Nguong 0.10 giu nguyen cho quyet dinh Phase 14.

## Ba Duong Di Can Y Kien GVHD

### A. Viet chuong RQ0 va ket thuc Phase 14

Thoi gian: khoang 1 tuan. Rui ro thap. Gia tri khoa hoc cao.

Ket luan chinh:

> Trong bai toan routing voi objective risk-neutral, thong tin AoI khong co
> headroom du lon de vuot nhieu huan luyen kha thi. Phase 14 xac dinh cac dieu
> kien can va ba che do that bai rieng biet.

### B. Chuyen sang risk-sensitive RL

Thoi gian: 3-4 tuan. Rui ro cao.

Can distributional RL nhu QR-DQN/C51 hoac mot bien the CVaR RL. DQN chuan toi
da hoa `E[R]`, nen khong du de train hanh vi hedge CVaR.

Ngay ca voi CVaR, gap tot nhat hien tai van can khoang 214 seed moi nhanh de
phat hien bang train. Khong nen lam neu khong co dong y mo rong pham vi.

### C. Doi bai toan, giu nguyen phuong phap

Thoi gian: 2-3 tuan. Rui ro trung binh. Gia tri cao nhat neu thanh cong.

Phan ra `gap = disagree x regret` chi ra bai toan co kha nang gap lon can:

- hau qua roi rac;
- quyet dinh kho rut lai;
- do lon cua sai lam khong phu thuoc viec hai action gan nhau ve Q.

Ung vien:

- admission control;
- scaling / VNF placement;
- failover trigger;
- A2 allocation trong `rl/a2/`.

Da doc nhanh `rl/a2/`: A2 co decision roi rac va staleness wrapper san co,
nhung env hien tai gan Mininet/EnvRunner. De dung voi `pilot_marginalized`, can
viet mot `SamplerA2` rieng va audit objective/dynamics truoc. Khong nen biet
ket qua A2 bang mot surrogate chua duoc ky.

## Quyet Dinh De Xuat

Dung Phase 14 routing tai day. Mang bao cao nay gap GVHD voi ba lua chon A/B/C.

Neu can tiep tuc ma van giu thoi gian do an, uu tien C: thu A2/admission-control
bang cung thang `gap_marginalized`, vi cong cu Phase 14 co the tai su dung va
chi can them sampler dung.
