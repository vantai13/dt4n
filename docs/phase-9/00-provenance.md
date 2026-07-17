# Nguon goc cac hang so simulator

## Phat hien

`rl/routing/link_model.py` va `rl/routing/topology_r.py` thua ke truc tiep tu
dong `routing-sdn`:

- `LOSS_THRESHOLD = 0.85`: khong co nguon do.
- `LOSS_FULL = 1.20`: khong co nguon do.
- M/M/1 voi `base_delay` lam service time: lua chon mo hinh, chua kiem chung.
- `MAX_QUEUING_FACTOR = 8.0`: co trong simulator cu, khong co nguon do.
- `base_traffic = bw * 0.30`: co trong simulator cu, khong co nguon do.
- Nhieu Pareto: lua chon phan bo tuy tien trong simulator cu.

Docstring cu cua `topology_r.py` tung noi topology da duoc calibrated voi real
Mininet testbed. Phat bieu do khong dung voi hien trang: Mininet that cua dt4n
ban dau la topology tam giac 3-switch, khong phai topology routing 8-node.

## Ve moc "+34.8% den +61.1%" cua routing-sdn

Moc nay den tu training tren `network/simulator.py`, tuc la tren simulator tu
viet, khong phai Mininet. `mn_env/` la code demo/eval, khong phai noi tao du
lieu training chinh.

Khong dung moc nay lam baseline trade-off cho Lesson 9.6. Neu nhac den, dat no
trong limitations voi nguon goc ro rang.

## Hanh dong

Lesson 9.0 thay cac hang so khong nguon bang so do Mininet that:

- `measurements/calib_link_sweep.py` do raw `rho_offered`, `rho_measured`,
  queueing delay, loss, va qdisc layer.
- `rl/routing/link_model_fit.py` fit M/M/1, M/D/1, va free-form theo tung
  `(bw, delay, queue)`.
- `mininet/topology_routing.py` coi queue size la bien thi nghiem, khong phai
  hang so: queue packets duoc suy ra tu full-queue delay target.

Moi hang so simulator con sot ma chua co nguon do phai duoc danh dau
`UNCALIBRATED` cho den khi co `results/calib/link_profiles.json`.

## Utilization contract

Train va deploy dung chung dinh nghia trong `rl/routing/util_spec.py`.
State contract duoc ghi o `docs/phase-9/state_spec.json`:

- Dung `txRate`, khong tu y chuyen sang `rxRate`.
- `txRate` la bytes/s, `bwMbps` la megabits/s, nen phai nhan `8`.
- Utilization deployable bi clamp vao `[0, 1]`; thong tin qua tai phai di qua
  kenh loss, khong phai qua `rho > 1`.
