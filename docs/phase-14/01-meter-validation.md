# Kiem dinh thuoc do gap_marginalized - Negative Control

Ngay: 2026-07-23
Git hash khi chay: 8854763

## Muc dich

Truoc khi tin thuoc do moi tren topology 3 duong, kiem dinh no tren mau da
biet dap an am: topology 2 duong `rl/routing_2path/`.

Day la negative control. Neu thuoc moi bao PASS tren topology cu, thuoc moi
khong duoc dung cho cac gate tiep theo.

## Cac sua doi bao ve thuoc do

- Reward dung cung objective voi Phase 11: `step_reward()` + calibrated
  `total_delay_ms()`/`loss_rate()`. Terminal reward la hang so chung giua cac
  route den dich, nen khong lam doi thu tu action.
- Public observation chi chua `rho`. Scenario va cfg khong nam trong obs.
- Q cua cac action tai cung `(obs, z)` duoc uoc luong bang common random
  worlds de giam variance cua hieu action.
- Drift adapter duoc test doi chieu truc tiep voi
  `RouteEnv._drift_offered_snapshot()`.
- Gate FAIL mac dinh tra exit code 0 vi day la ket qua khoa hoc hop le, khong
  phai crash. Pipeline co the dung `--strict` de bien gate FAIL thanh exit
  code 1 va chan train.
- JSON ghi provenance: `load_cfg`, `link_model_sha`, `reward_model_sha`, va
  `dynamics_source_sha`.

## Provenance

| truong | gia tri |
|---|---|
| load_cfg | `LOAD_CFG_DYNAMIC` |
| link_model_path | `rl/routing_2path/link_model.py` |
| link_model_sha | `fd9f9f1de49a` |
| reward_model_sha | `5164640c6c72` |
| dynamics_source_sha | `3e33b80b08bb` |

## Ket qua

| seed | cases | mc | gap_mean | ci95 | can duoi | verdict | agree_rate | n_disagree | decision_regret |
|:---:|:---:|:---:|---:|---:|---:|:---:|---:|---:|---:|
| 0 | 400 | 200 | 0.0056 | 0.0024 | 0.0032 | FAIL | 0.9475 | 21 | 0.1063 |
| 1 | 400 | 200 | 0.0054 | 0.0024 | 0.0030 | FAIL | 0.9525 | 19 | 0.1143 |
| 2 | 400 | 200 | 0.0056 | 0.0024 | 0.0032 | FAIL | 0.9475 | 21 | 0.1066 |

Nguong tien nghiem: `mean - ci95 >= 0.10`.

## Chan doan

Gap trung binh gan 0 va ca 3 seed deu FAIL. `agree_rate` khoang 95%, nghia la
trong da so case, action toi uu khi biet z va action toi uu khi marginalize z
la mot.

`decision_regret` khoang 0.106 chi tren cac case disagree, nhung disagree hiem
khi xay ra. Vi vay headroom trung binh van gan 0. Day la dung ky vong negative
control cho topology 2 duong.

Phan ra dung voi seed 0:

    gap = disagree_rate x decision_regret
        = 0.0525 x 0.1063
        = 0.0056

`decision_regret` tinh tren 21/400 case disagree, nen chi doc nhu cap do
khoang 0.1, khong phai mot hang so chinh xac.

## Phat hien bat ngo tu negative control (exploratory)

`gap_by_z` cho thay gan nhu toan bo gap tap trung o z=0:

| z | n | gap | disagree_rate | q_margin |
|:-:|---:|---:|---:|---:|
| 0 | 70 | 0.0319 | 0.300 | 0.4137 |
| 1 | 50 | 0.0000 | 0.000 | 0.9368 |
| 3 | 57 | 0.0000 | 0.000 | 1.3684 |
| 5 | 75 | 0.0000 | 0.000 | 1.3725 |
| 8 | 59 | 0.0000 | 0.000 | 1.4132 |
| 12 | 89 | 0.0000 | 0.000 | 1.3276 |

`q_margin` tang manh tu z=0 den z=8 va van cao o z=12. Nghia la tren
topology 2 duong voi trend co huong, do tre lam quyet dinh ro rang hon, khong
phai kho hon. Trend don dieu khuech dai khoang cach giua cac duong: z cang lon
thi duong dang tang tai cang vuot xa cliff, cang hien nhien phai tranh.

He qua: gia tri cua AoI suy sup ve truong hop z=0, noi no cho phep agent bo
hedge thay vi tiep tuc hedge.

Verify rieng tai z=8 voi 50 observation cho ket qua `disagree=0/50`. Action
khong bi suy bien thanh mot hang so: `a*(z=8)` co count `E=26, F=24`, va
`a*_marg` cung `E=26, F=24`. Vay `gap=0.0` tai z=8 la do hai policy dong y
theo tung observation, khong phai bug always-F.

### Rang buoc thiet ke rut ra cho topology3

Drift phai la khuech tan (su kien ngau nhien vo huong), khong duoc don dieu.
Chan doan ho tro: `q_margin` nen giam theo z, khong duoc tang.

### Muc tieu dinh luong cho topology3

    gap = disagree_rate x decision_regret

Tren 2-path: 0.0525 x 0.106 = 0.0056.

Muc tieu 3-path: `disagree_rate >= 0.33` va `decision_regret >= 0.30`, de
`gap` dat xap xi `0.10`.

## Ket luan

Thuoc `gap_marginalized` da reject topology cu. Duoc phep dung thuoc nay lam
gate cho thiet ke topology moi, voi dieu kien topology moi tiep tuc phai qua
du 5 gate tien nghiem trong Phase 14. Chan doan `q_margin` la phat hien
exploratory tu negative control, khong thay the gate chinh.
