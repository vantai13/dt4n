# Phase 10 - Ket qua chinh (CHOT, ky sau confirmatory sweep)

**Ngay ky:** 2026-07-19
**Nguoi ky:** vantai13
**Frozen:** `frozen_policies/v1/` (freeze tag `2ef208e`, link_model `3a3c7e5`)
**Commit code tai thoi diem chot/run:** `dec1d33` (`change into wrong_excess`)
**Doi chieu:** ket qua nay khop mo hinh va nguong da khoa o
`docs/phase-10/00-preregistration.md` (pre-reg dung truoc sweep, khong HARKing).

---

## 1. Cau hinh da chay (khop pre-registration muc 3)

- Truc chinh: `wrong_excess = blind_wrong_rate - clair_wrong_rate`
- Truc he qua: `cost_of_blindness = clair_return - blind_return`
- Dai z: `[0,1,2,3,5,8,12,20]` -> AoI `[0..10]s`; `STEP_DURATION_S=0.5`
- Load: `LOAD_CFG_SWEEP` (`drift_sigma=0.15`, da fix bug drift-override)
- Seeds: 500 (confirmatory; pilot dung 300)

## 2. Doi chieu pre-registration

| Hang muc | Da khoa (pre-reg) | Ket qua (confirmatory) | Khop? |
|---|---|---|---|
| Dang ham | `A*(1-exp(-AoI/tau))` | dung dung | yes |
| Breaking point | `tau` (knee 63%) | dung dung | yes |
| Nguong fit | `R2 >= 0.95` | `R2 = 0.989` | yes |
| `std_agent` | `0.0450` | `0.0450` | yes |
| Gate | `SNR >= 3` -> GO | `SNR = 7.29` -> GO | yes |

## 3. Ket qua sweep chinh (500 seed)

| z | AoI(s) | wrong_excess | cost_of_blindness | blind_wrong | clair_wrong |
|--:|-------:|-------------:|------------------:|------------:|------------:|
| 0 | 0.00 | 0.0000 | 0.0000 | 0.2133 | 0.2133 |
| 1 | 0.50 | 0.0620 | 0.1002 | 0.2753 | 0.2133 |
| 2 | 1.00 | 0.0960 | 0.1364 | 0.3093 | 0.2133 |
| 3 | 1.50 | 0.1093 | 0.2035 | 0.3227 | 0.2133 |
| 5 | 2.50 | 0.1500 | 0.2366 | 0.3633 | 0.2133 |
| 8 | 4.00 | 0.1827 | 0.2789 | 0.3960 | 0.2133 |
| 12 | 6.00 | 0.2060 | 0.3171 | 0.4193 | 0.2133 |
| 20 | 10.00 | 0.2233 | 0.3283 | 0.4367 | 0.2133 |

**Fit (dai da dang ky, z <= 20):** `A = 0.2181`, `tau = 1.997 s`,
`R2 = 0.989`, `knee90 = 4.60 s`.

## 4. Sanity checks (bang chung so dung)

- `z=0` -> `wrong_excess = 0.000000` (blind = clair khi anh khong cu).
- `clair_wrong_rate = 0.2133` co dinh moi z (noise floor duoc co lap).
- `clair_return spread = 0.000000` (clairvoyant khong bi AoI anh huong).
- `wrong_excess` va `cost_of_blindness` don dieu tang tren dai da dang ky.

## 5. Breaking point va dien giai Ditto that

- **Breaking point:** `tau = 1.997 s` (fit day du tren dai da dang ky).
- **Khoang bat dinh:** robustness qua cac bo seed doc lap cho `tau` trong khoang
  xap xi `[1.4, 2.5] s` (`1tau mean = 1.97s`, `sd = 0.53s`). Bo diem `z=20`:
  `tau = 1.81 s`. Vi vay bao cao breaking point la **khoang 1.8-2.5 s**,
  khong phai mot hang so chinh xac.
- **Ditto that (AoI 0.05-0.55s):** `wrong_excess@0.55s = 0.0525`
  (`24.1%` tran `A`).
- **Ket luan:** twin that (`0.55s`) nam vung truoc breaking point
  (`0.55 << 1.8`). Twin du tuoi cho bai toan nay; loi ton du nho
  (khoang `5%`). Day la phat hien thuc tien, khong phai that bai.

## 5b. Co che (Lesson 10.4): chon sai -> mat diem

Khong chi bao cao hien tuong return giam, Phase 10.4 do them kenh co che.

**Bang chung dinh luong (500 seed, `LOAD_CFG_SWEEP`):**

- `Pearson(wrong_excess, cost_of_blindness | AoI>0) = 0.985`
  -> truc sai-lam va truc mat-diem di cung nhip theo AoI.
- Chuoi nhan-qua: AoI cao -> anh twin cu -> blind chon next-hop sai
  -> luong vao link da nghen -> return giam.

**Bang chung dinh tinh:** episode seed `2` (xem `07-handtrace-seed2.md`).
Tai node `D`, E/F dao ngoi trong `1.5s`:
`D->E: 0.698 -> 1.300`; `D->F: 0.871 -> 0.280`. Blind tin anh cu, re vao
`E` dang nghen, mat `1.18` reward so voi clairvoyant.

**Ghi chu metric phu (`safe_path_freq`):** do duoc nhung non-monotone theo AoI,
nen khong phai kenh co che sach. Khong dung lam bang chung chinh; `wrong_excess`
voi Pearson `0.985` la kenh co che dang tin. Chi tiet o `06-exploratory-two-phase.md`.

## 6. Gate GO/NO-GO Phase 11

- `cost_of_blindness_max = 0.3283` (tai `z=20`)
- `std_agent = 0.0450`
- `SNR = 0.3283 / 0.0450 = 7.29`
- Cay quyet dinh pre-reg: `SNR >= 3` -> **GO**
- **Quyet dinh: GO Phase 11.** Tin hieu vuot nhieu thuoc do 7.3 lan; ablation
  se do duoc, khong roi vao inconclusive.

## 7. Ban giao Phase 11

- Co tin hieu de hoc: Dijkstra hoan hao van bi AoI hai, nen bai toan co noi dung.
- Neu Phase 11 ra hue: uu tien nghi loi o agent/training, khong o bai toan.
- Vung thuc te Ditto `0.55s` co headroom nho (`wrong_excess ~5%`), nen Phase 11
  nen train/eval them o regime du manh qua cliff de tin hieu ablation khong bi nuot.

**San pham kem:** `measurements/out/sweep_10_2.csv`,
`measurements/out/main_figure_10_3.csv`, `measurements/out/sweep_10_2_mechanism.md`,
`measurements/out/main_figure_10_3_cost_ci.md`,
`measurements/out/mechanism_10_4.csv`, `measurements/out/mechanism_10_4.txt`,
`measurements/out/mechanism_10_4.png`.

**Chu ky:** vantai13 - 2026-07-19
