# Phase L / Lesson L.3 -- Golden tests va regression tests

Ngay: 2026-07-29

## 1. Muc tieu

Ha tang do khong duoc phep "muc ruong am tham". L.3 tach phan thuan ra khoi
phan song, dong bang golden result L.2, va them unit/golden tests de bat thay
doi kernel/Mininet/hang so/logic phan tich.

## 2. File moi

```text
mininet/tc_spec.py
test/test_phase_l_tc_spec.py
test/test_phase_l_probe.py
test/test_phase_l_analyze.py
test/test_phase_l_golden_measured.py
tools/freeze_l2_golden.py
tools/raw_manifest.py
results/phase-L/golden/l2_staircase_golden.json
results/phase-L/raw/MANIFEST.sha256.json
```

`mininet/tc_spec.py` khong import `mininet.topo`, `mininet.net`, hay bat ky
phan live nao. No chi chua ham thuan: doi don vi, sinh chuoi tc, parse output
tc, ly thuyet bac thang token bucket, va fit nguoc C/burst.

## 3. Golden source

Golden file duoc sinh tu:

```text
results/phase-L/l2_probe_0729_0803.json
```

Lenh:

```bash
python3 tools/freeze_l2_golden.py results/phase-L/l2_probe_0729_0803.json
```

Ket qua regression tren golden:

| bw | C do duoc (Mbps) | burst do duoc (B) | R2 |
|---:|---:|---:|---:|
| 8 | 8.0164 | 1648.8 | 0.99939 |
| 6 | 5.9968 | 1680.5 | 0.99966 |
| 4 | 3.9907 | 1634.7 | 0.99993 |

Nguong golden:

```text
|dC|/C < 1%
|dB|/B < 10%
R2 > 0.999
```

## 4. Raw manifest

Raw `.bin` khong vao git. Manifest vao git:

```text
results/phase-L/raw/MANIFEST.sha256.json
```

Lenh:

```bash
python3 tools/raw_manifest.py results/phase-L/raw
```

Manifest hien tai:

```text
90 file, 0.8 MB
archive_doi = TBD -- dien sau khi upload Zenodo
```

## 5. Invariant coverage

| Invariant | Noi dung | Test phu trach |
|---|---|---|
| I1 | queue ceiling ti le thuan q, nghich bw | test_phase_l_tc_spec |
| I2 | bfifo limit theo byte, khong phai packet | test_phase_l_tc_spec |
| I3 | chieu DO khong co netem | test_phase_l_tc_spec |
| I4 | burst >= 1 MTU | test_phase_l_tc_spec |
| I5 | unpack(pack(x)) == x | test_phase_l_probe |
| I6 | sai MAGIC/version bi tu choi | test_phase_l_probe |
| I7 | HDR=32, REC_RX=24, REC_TX=16 | test_phase_l_probe |
| I8 | count/loss khong vi pham bien | test_phase_l_analyze |
| I9 | loss_rate trong [0,1] voi fixture | test_phase_l_analyze |
| I10 | percentile nearest-rank don dieu | test_phase_l_analyze |
| I11 | cat cua so theo t_send, khong t_recv | test_phase_l_analyze |
| I12 | OWD am lo ra, khong bi loc | test_phase_l_analyze |
| I13 | C trich tu bac thang khop trong 1% | test_phase_l_golden_measured |
| I14 | burst trich tu bac thang khop trong 10% | test_phase_l_golden_measured |
| I15 | R2 bac thang > 0.999 | test_phase_l_golden_measured |
| I16 | OWD tai 0 khong phu thuoc bw | test_phase_l_golden_measured |

## 6. Negative fixtures

Bo test co cac fixture co chu dich sai de chung minh test bat duoc loi:

```text
TCLINK_QDISC co netem tren chieu DO -> bi bat V-L1b
NO_LEAF_QDISC thieu bfifo leaf -> bi bat V-L1c
PFIFO_QDISC gioi han theo packet -> bi bat V-L1c
burst 15000b -> bi bat V-L1d
synthetic slow packet cat theo t_send -> bat thien lech t_recv
raw file kich thuoc khong chia het record -> bi bat HONG
```

Day la mutation testing nhe bang fixture, khong can sua file nguon roi revert.

## 7. Validation da chay

```bash
pytest test/test_phase_l_*.py -q
pytest test/ -q
```

Ket qua:

```text
45 passed in 0.04s
127 passed, 4 skipped, 2 warnings in 13.16s
```

Canh bao hien tai khong thuoc Phase L:

```text
bridge/command_agent.py: datetime.datetime.utcnow() deprecated
```

## 8. Live tests

Chua tron live Mininet/root vao unit tests. Neu sau nay them integration live:

```bash
DT4N_LIVE_MININET_TESTS=1 sudo -E pytest -m live
```

CI chi chay:

```bash
pytest test/ -q -m "not live"
```
