# AMENDMENT 23-42 -- Lesson 23.8[A]: do do nhay cua ket luan theo d_sync

Ngay: 2026-08-21
Trang thai: **SAU micro-pilot range-setting; TRUOC khi sua cac builder
certificate, TRUOC khi build bat ky calib set sensitivity nao, va TRUOC khi
tinh bat ky err_neo / lift / swing / Delta nao tai d_sync khac 0.051.**

## 0. Boi canh va pham vi

P23-A (dong L11, L13) ghi rang AoI dung trong Phase 20R--23 duoc do tren mot
topology khac `topology_v7`. Truy nguon trong repo:

```text
d_sync = 0.051 s      docs/phase-20/00c-amendment-2.md
artifact              results/aoi/aoi_a2_host_srv1_gcp_20260816.json
thing                  org.dt4n:host-srv1 (muc HOST)
topology artifact      ditto/topology_spec.json (tam giac Phase 1)
he duoc chung nhan     twin/topology_v7.py (2x2 butterfly, 8 link, K=4)
```

`mininet/run_sync_v7.py` khong bootstrap Things, khong chay `sync_agent`, va
khong co `tSource`; AoI chua duoc do tren `topology_v7`. Lesson nay khong xay
vong dong bo day du. No chi do value-of-information: ket luan bracket Poisson
co nhay voi `d_sync` hay khong.

Lesson 23.8[A] **KHONG dong P23-A**. Moi output bat buoc co
`status = "SENSITIVITY_ONLY"` va `closes_P23A = false`.

## 1. Estimand

Voi moi cell va moi `d` trong dai khoa `D`:

```text
LS(cell,d)    = lift(cell,d) - swing(cell,d)
Delta(cell,d) = reject_share * (swing(cell,d) - lift(cell,d))

S(cell) = 1  <=> sign(LS(cell,d)) khong doi voi moi d trong D
A(cell)      = max_d |Delta(cell,d) - Delta(cell,0.051)|
```

Estimand chinh la do ben cua **dau**, vi ket luan cong bo la bracket doi dau
`(0.900, 0.925)`, khong phai mot gia tri Delta cu the.

## 2. Micro-pilot range-setting va dai d_sync khoa

Micro-pilot chi doc/ghi 20 Thing gia; khong doc certificate outcome. Mot cycle
bao gom snapshot giong collector, 20 PATCH tuan tu qua pusher, Ditto HTTP
acknowledgement, va 20 GET truc tiep qua reader. Moi GET phai thay dung token
cua cycle. Script va artifact:

```text
measurements/dsync_bridge_micro_pilot.py
results/phase-23/dsync_bridge_micro_pilot.json
```

Ket qua range-setting da do truoc outcome:

```text
n_thing / warmup / n_cycle : 20 / 20 / 200
cycle p05 / p50 / p95      : 0.173449 / 0.201793 / 0.260590 s
cycle min / mean / max     : 0.168093 / 0.207728 / 0.331235 s
push p50 / read p50        : 0.117335 / 0.083287 s
HTTP success               : 100%
read-back token verified   : 100%
```

Dai de xuat ban dau `{0.030, 0.040, 0.051, 0.070, 0.090}` khong bao phu
pilot, nen bi thay **truoc outcome**. Lay p05/p95 lam bien, noi suy 1/3 va 2/3,
roi luong tu ve luoi 5 ms; them bat buoc negative control ke thua 51 ms:

```text
D = { 0.051, 0.175, 0.205, 0.230, 0.260 } giay
```

`0.051` nam ngoai dai pilot nhung bat buoc giu de doi chieu bit-exact voi
artifact da commit. Khong duoc doi `D` sau tag `lesson-23.8a-pre`.

`T = 0.5 s` khong sweep: T la lua chon thiet ke; `d_sync` la thuoc tinh do
duoc cua he.

## 3. Quy tac canh bin giu cau truc theo buoc luong tu

`z` song tren luoi `dt = 0.005 s`. Canh bin duoc dinh nghia bang do lech buoc
so voi `k_min`, khong bang gia tri giay:

```text
Z_STEP_OFFSETS_PRIMARY   = (0, 9, 29, 49)
Z_STEP_OFFSETS_SECONDARY = (0, 20, 40, 60, 80)

k_min, k_max = min/max(sawtooth_age_steps(n, dt, T, d_sync))
edges = [(k_min + offset) * dt for offset in offsets] + [k_max * dt + 1e-4]
```

`k_min` va `k_max` phai dung dung `n` cua lan build. Tai `d=0.051`, `n=200000`:

```text
PRIMARY   = (0.055, 0.100, 0.200, 0.300, 0.5501)
SECONDARY = (0.055, 0.155, 0.255, 0.355, 0.455, 0.5501)
```

Hai bo tren phai bang chinh xac hang so da commit. Quy tac nay giu bin share
PRIMARY xap xi `0.090 / 0.200 / 0.200 / 0.510`; no chi doi tuoi tuyet doi,
khong doi khoi luong thong ke cua bin.

Artifact phai ghi `z_edges_nominal`, `z_edges_realised`, `k_min`, `k_max`,
`bin_shares`, va `n_valid_rows`.

## 4. Cell, hai tang, va stop rule

```text
TANG 1  poisson@0.900, poisson@0.925             2 cell x 5 d = 10 build
TANG 2  poisson@0.850, poisson@0.960, h2@0.700   3 cell x 5 d = 15 build
        chi chay neu Tang 1 co MISS tai M-62 hoac M-63.

Tang 1 HIT het  -> DUNG; khong chay Tang 2.
Tang 1 co MISS  -> chay Tang 2, sau do DUNG bat ke ket qua.
Khong mo Tang 3, khong them cell, khong lam min D, khong retune.
```

## 5. Du doan khoa M-58..M-65

Pilot lam bien tren tang tu 90 ms len 260 ms. Do do prediction M-61 va M-64
duoc noi rong **truoc outcome** so voi de xuat ban dau.

| ID | Dai luong | Nhan | Dai khoa |
|---|---|---|---|
| M-58 | NC `d=0.051` tai lap Delta/lift/swing/err_neo da commit, 2 cell | [TAI TINH] | max abs gap `<= 1e-12` |
| M-59 | bin_share lech so voi `d=0.051`, moi d, moi bin | [TAI TINH] | `<= 1e-4` |
| M-60 | `w_loss` tren 5 lan chay cua cung cell | [CO CHE] | identical bitwise |
| M-61 | `err_neo` don dieu tang theo d; bien do toan D moi cell | [CO CHE] | don dieu CO; bien do `<= 0.060` |
| M-62 | sign(LS) khong doi tren D, ca 2 cell Tang 1 | [NGOAI SUY] | CO: am @0.900, duong @0.925 |
| M-63 | sign(Delta_F2) khong doi tren D, ca 2 cell Tang 1 | [NGOAI SUY] | CO: duong @0.900, am @0.925 |
| M-64 | `A(poisson@0.925)` | [NGOAI SUY] | `0.000 .. 0.018` |
| M-65 | q_hat o `(z_bin=0,m_hat_bin=0)` don dieu tang theo d | [CO CHE] | don dieu CO |

Co che M-61: voi AR(1), `corr = exp(-z_bar/tau)`, `tau=1.0 s`. Tai NC,
`z_bar=0.3025` va corr xap xi 0.739. Tai `d=0.260`, `z_bar=0.5075` va corr
xap xi 0.602. Tuong quan giam khoang 18.5%, lon hon de xuat ban dau 5.8%, nen
bien do err khoa duoc noi tu 0.020 len 0.060 va M-64 tu 0.006 len 0.018.

M-65 la negative control tu than: neu q_hat khong doi theo d_sync thi truc
tuoi trong certificate khong chiu tai. MISS duoc bao cao, khong retune.

## 6. Controls bat buoc

```text
NC-L  w_loss giong bitwise tren moi d cua cung cell; neu lech thi DUNG.
NC-M  d=0.051 tai lap outcome da commit den 1e-12; neu truot thi DUNG.
NC-N  bin_shares lech toi da 1e-4.
NC-O  Delta = reject_share * (swing - lift) den 1e-12.
NC-P  row/seed disjoint, C3, alpha, Bonferroni, GAMMA_OP, fallback families
      va tie-break khong doi.
NC-Q  ghi n_valid_rows chinh xac cho moi d.
```

## 7. He thong dong bang

Khong doi `SIGMA=0.0096`, `SEEDS=(101..105)`, `N=200000`, `DT=0.005`,
`TAU=1.0`, `ALPHA`, `C3`, 16 o Mondrian, `GAMMA_OP`, fallback families,
bootstrap, `sla_calibration.json`, hoac `w_loss`.

Khong chay lai SLA fixed-point calibration. `path_tables` dung rho tuoi, khong
dung age, nen `w_loss` doc lap voi d_sync; NC-L bien menh de nay thanh control
chay duoc.

## 8. Output khoa

```text
cert/dsync_sensitivity.py
test/test_phase23_dsync_sensitivity.py
results/phase-23/dsync_sensitivity.json
results/phase-23/fig7_dsync_sensitivity.png
docs/phase-23/18-dsync-sensitivity.md
```

Test phai fail neu mat `status="SENSITIVITY_ONLY"` hoac neu
`closes_P23A` khac `false`.

## 9. Nhanh ket luan viet truoc

```text
NHANH 1  M-62 HIT  -> bracket ben tren D; P23-A ha thanh limitation co bang
                      chung, nhung khong dong.

NHANH 2  M-62 MISS -> P23-A la rui ro chi mang co bang chung; xay vong sync DT
                      topology_v7 tro thanh bat buoc. Cac ket luan cu phai ghi
                      "conditional on d_sync = 51 ms" cho den khi do lai.
```

Ca hai nhanh deu la ket qua dung duoc. Khong mo them nhanh sau khi xem outcome.
