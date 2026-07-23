# Chan doan 4 lan chay am cua Phase 11

Ngay viet: 2026-07-23

## Bang 1 — Bon lan chay

| Lan | Cau hinh | Ket qua | Nguyen nhan do duoc |
|:---:|---|---|---|
| 1 | LOAD_CFG_TRAIN (S1-S4 static, drift_sigma=0) | AM | The gioi TINH: stale == fresh, khong co gi de biet |
| 2 | + drift_sigma parent | AM | Drift qua nho, |rho(t)-rho(t-z)| ~ 0 |
| 3 | LOAD_CFG_ASYM (weights lech) | AM | Duong TROI: max_a P(a*|fresh) = 0.665 |
| 4 | LOAD_CFG_DYNAMIC (S5/S6 trend, weight 3.0) | AM | z KHONG doc lap voi obs (dieu kien 3) |

## Bang 2 — Ba phat hien phuong phap

1. **Thuoc sai.** `fresh - stale` do "stale lua duoc Dijkstra bao nhieu",
   KHONG do "biet z thang duoc mot learner da hedge bao nhieu".
   Bang chung: blindWrong=0.386 vs maskWrong=0.045-0.159 (sai it hon 3-8 lan).
   Nhanh mask KHONG mu — no hoc prior va hedge.

2. **Thuoc dung = gap_marginalized = Bayes(obs+z) - Bayes(obs, marginalize z).**
   Do dung headroom cua LEARNER, khong phai cua ORACLE tin anh.

3. **Dieu kien (3) chua bao gio duoc dam bao.** Trend co huong trong
   SCENARIOS_DYNAMIC lam noi dung obs tiet lo z:
   thay e_load > cliff => suy ra dang o S5_E_rising => suy ra "thuc te te hon"
   => KHONG can doc chieu AoI.
   Nang hon: scenario_weights cho S5/S6 = 3.0 moi cai, 4 scenario static = 0.5
   => 6/8 = 75% episode co ro ri nay. Khong phai truong hop hiem — la DA SO.

## Bang 3 — Bay gia thuyet da loai tru

| # | Gia thuyet | Cach kiem | Ket luan |
|:-:|---|---|---|
| 1 | DQN hyperparam sai | sweep lr, buffer, eps | Loai — Phase 9 hoc duoc tot |
| 2 | Train qua ngan | keo dai steps | Loai — curve da phang |
| 3 | Reward ro theo z | test invariance | Loai — reward giong het qua z |
| 4 | Mask sai chieu | assert len(mask_aoi(v))==9 | Loai — dung 2 chieu (7,8) |
| 5 | Seed xui | 10 run x 4 lan | Loai — nhat quan am |
| 6 | AoI khong doc duoc tu env | do aoi_measured ~ z*0.5s | Loai — do dung |
| 7 | Duong troi | max_a P(a*|fresh) | XAC NHAN o lan 3 (0.665), da sua |

## Ket luan va quyet dinh

Ngay 2026-07-23: chuyen sang topology 3-duong voi co che su kien dao chieu
ngau nhien VO HUONG. Ly do: (a) 2-duong suy bien nhi phan, prior du de giai
=> AoI du thua by construction; (b) trend co huong ro z vao obs.
Sang Phase 14 voi gate 5 dieu kien, thuoc gap_marginalized.
