# Phase 11 - Pre-registration (chot TRUOC khi train 2x5 seed)

**Ngay ky:** 2026-07-20
**Nguoi ky:** vantai13
**Frozen:** `frozen_policies/v1/` (freeze tag `2ef208e`, link_model `3a3c7e5`)
**Phase 10 baseline:** commit `dbe3ce1` (`Phase 10.4: co che Pearson va handtrace seed2`)
**Bang chung khong HARK:** commit chua file nay dung TRUOC moi commit train Phase 11.

---

## 1. Ba gia thuyet H1/H2/H3

H1: `VoI(AoI=0) ~= 0` - hai nhanh hue khi du lieu tuoi
(`paired t-test p > 0.05`).

H2: `VoI(AoI cao) > 0` - agent-AoI thang o vung mu
(`paired t-test p < 0.05`).

H3: hanh vi phong ve tach - agent-AoI phong ve nhieu hon o AoI cao; do bang
`wrong_excess` per-nhanh la kenh uu tien, `safe_path_freq` la kenh phu vi
Phase 10.4 da thay non-monotone.

Neu H1 + H2 + H3 cung dung, nhan-qua duoc xac lap: loi the den tu thong tin AoI,
khong phai confounder.

## 2. Hinh dang duong cong VoI (pre-register mem)

Duong cong VoI it nhat co suon len:

`VoI(0) ~= 0 < VoI(AoI cao)`.

O AoI rat cao, ca hai kha nang deu duoc chap nhan la ket qua hop le:

- (a) giam ve 0 (dang chuong), neu mu den muc vo phuong cuu.
- (b) phang o muc cao (bao hoa), neu biet minh mu va rut ve hanh vi an toan van
  con huu ich.

Ly do sua so voi plan goc: Phase 10 cho `wrong_excess` bao hoa
(`A=0.2181`, `tau=1.997s`, `R2=0.989`) va khong giam ve 0 trong dai do. Vi vay
khong khoa cung "chuong"; pre-register dang mem: bat buoc co suon len, con tail
duoc doc theo du lieu.

## 3. SNR-gate (cong vao, khong dung voi_headroom)

So that tu repo:

- `cost_of_blindness_max = 0.3283` (Phase 10, `z=20`, sweep 500 seed)
- `std_agent = 0.0450` (frozen_policies/v1, z=0, `LOAD_CFG_SWEEP`)
- `SNR = 0.3283 / 0.0450 = 7.29`

Cay quyet dinh:

- `SNR >= 3` -> GO voi 5 seed moi nhanh.
- `2 <= SNR < 3` -> GO nhung tang len 10 seed moi nhanh.
- `SNR < 2` -> NO-GO, khong train, quay lai sua san khau.

**Quyet dinh:** GO Phase 11, train 5 seed moi nhanh.

Khong dung `voi_headroom` lam gate vi Phase 10 da thay metric nay phu thuoc OSPF
va bi cancellation. Gate dung `cost_of_blindness_max / std_agent` vi no do
tin hieu staleness tren nhieu nen agent.

**Ghi chu nhat quan load:** `SNR=7.29` dung cap so do tren `LOAD_CFG_SWEEP`:
tin hieu `cost_of_blindness_max=0.3283` va nhieu `std_agent=0.0450` cung den tu
load sweep co drift. Phase 11 train tren `LOAD_CFG_ABLATION`, la mix rong hon
gom S1-S4 tinh va S5-S6 dong. Gate van duoc giu theo cap `LOAD_CFG_SWEEP` vi no
la phep go/no-go, khong phai uoc luong hieu ung cuoi cung; bien an toan lon
(`7.29 >> 3`). Khong ghep `0.3283` voi `std_agent=0.0312` cua load tinh vi do
la ghep tin hieu va nhieu khac dieu kien.

## 4. Ky luat Muc 3

- Ca 10 run (`2 nhanh x 5 seed`) khoa cung
  `link_model_version = 3a3c7e5995a766fbf83f5227a7f4b900e6547f19`.
- Ghi them `sha256(rl/routing/link_model.py)` vao manifest moi run:
  `fd9f9f1de49af502665b8541d3ab0b414ba7a7ccc4b3ac9dde9dbc6da11bce03`.
- Paired seed: seed `k` cua nhanh AoI va seed `k` cua nhanh noAoI dung cung
  `train_seed`, cung scenario schedule, khac dung mot bien: co/khong co thong
  tin AoI trong observation.
- Confounder can tranh: dynamics-shift. De tai do observation-shift; dynamics
  phai duoc khoa bang link_model version va sha256.

## 4b. Training load Phase 11 (amendment truoc train)

Phase 11 train tren `LOAD_CFG_ABLATION`, gom ca 6 scenario:

- S1-S4 tu `SCENARIOS_TRAIN`: tinh trong episode (`drift_sigma=0.0`)
- S5-S6 tu `SCENARIOS_DYNAMIC`: dong trong episode (rising side `0.88-0.93`,
  safe side `0.20-0.40`, trend co huong duoc sample moi episode trong
  `0.12-0.35`, `drift_sigma=0.02`, per-scenario `offered_load_max=1.60`,
  offered-load floor `0.15`)

Ly do them S5-S6: ablation AoI can co episode ma anh cu khac su that trong luc
train. S1-S4 tinh van giu branch-choice calibration; S5-S6 dong tao observation
shift de chieu AoI co thong tin de hoc.

`LOAD_CFG_ABLATION` khong dat `drift_sigma` o cap cha; moi scenario tu giu
trend/drift rieng de tranh lam mo ranh gioi tinh/dong.

## 5. Ngan sach

Frozen config that ghi `train.episodes = 2000`. Phase 11 tam lay cung muc nay
cho moi run.

Cong thuc ngan sach:

`total_time ~= 2000 episodes x T_giay/episode x 10 run`.

Pilot pipeline 200 episode cho thay toc do co bac do `~14-20 ms/episode`
(khac nhau tuy lay timer noi bo hay shell `time`). Ngan sach uoc tinh:

- optimistic: `0.014 x 2000 x 10 ~= 280s` (<5 phut)
- conservative: `0.020 x 2000 x 10 ~= 400s` (~7 phut)

Neu lan pilot moi cua may cho toc do khac, dung so moi do de cap nhat ngan sach
truoc khi bam 10 run. Khong dung uoc luong 500 episode trong plan cu.

## 6. Validation gate truoc khi train

- H1/H2/H3 da ghi va commit truoc moi train Phase 11.
- Hinh dang VoI pre-register mem: suon-len bat buoc, tail chuong/bao hoa mo.
- SNR tinh tu so that trong repo: `7.29 >= 3` -> GO 5 seed.
- `link_model_version` va `link_model_sha256` duoc khoa de chong dynamics-shift.
- Manifest Phase 11 phai ghi du nhanh, seed, git commit, `link_model_version`,
  `link_model_sha256`, mask/no-mask, episodes, va train_seed.
