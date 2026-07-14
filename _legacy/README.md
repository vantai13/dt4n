# Legacy Archive

Thu muc nay chua code cu da duoc dua ra khoi duong chay chinh sau chang B+C.
Muc tieu la lam sach repo cho A2 allocation-centric, nhung van giu lai code cu
de doi chieu lich su, doc lai thiet ke, hoac khoi phuc neu can.

## Noi Dung

- `rl/`: TwinEnv cu, state 45 chieu network-centric, reward/action/train/eval
  cu, cac script verify/diagnostic gan voi he do.
- `measurements/`: cac phep do cu cho state/link/twin Phase 4.5-5, khong phai
  bo do A2 9 chieu moi.
- `test/`: test di kem cac module cu da archive.

## Dang Duoc Thay The Boi

- A2 env/state/reward/demand: `rl/a2/`
- A2 measurement scripts:
  - `rl/a2/measure_delta_a2.py`
  - `rl/a2/measure_noise_a2.py`
  - `rl/a2/measure_aoi_a2.py`
  - `rl/a2/measure_fidelity_a2.py`
- Ha tang chung van giu ngoai legacy:
  - `mininet/`
  - `bridge/`
  - `rl/injection.py`
  - `rl/scenarios.py`
  - `rl/oracle_policy.py`
  - `rl/flow_ack.py`
  - `rl/agent/`

## Nguyen Tac Dung

Code trong `_legacy/` khong nam tren duong chay chinh. Neu can dung lai, hay
doc import path truoc vi mot so module cu van import theo ten goc `rl.*` hoac
`measurements.*`. Khong sua code trong nay de phuc vu A2, tru khi ban dang lam
viec khoi phuc/doi chieu lich su.

## Khi Nao Xoa Han

Co the xoa han khi:

1. A2 da co measurement va training pipeline on dinh.
2. Khong con doc/bao cao nao can reproduce ket qua Phase 4.5-5 bang code cu.
3. Da tag/commit mot moc truoc khi xoa de co the tra lai neu can.
