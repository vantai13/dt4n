# axis_audit

```text
=== A1: harness x truc AoI ===
(UNREGISTERED tren mot harness KHONG phai loi: chi module BO SINH moi nam trong registry)
measurements/decision_error_v2.py      - (chi goi, khong dinh nghia truc)
cert/build_calib_set_v3.py             - (chi goi, khong dinh nghia truc)
cert/tau_sweep.py                      - (chi goi, khong dinh nghia truc)
cert/aoi_profiles.py                   - (chi goi, khong dinh nghia truc)
cert/cell_matrices.py                  - (chi goi, khong dinh nghia truc)
cert/realizability_gate.py             - (chi goi, khong dinh nghia truc)
measurements/aoi_model_v7.py           measured_v7_uniform
measurements/decision_error.py         assumed_sawtooth_51ms

=== A3: do lech hai truc, MIEN MO HINH (dt=0.005) ===
legacy    p05=0.0770 med=0.3000 mean=0.3024 p95=0.5250  [0.055, 0.550]  CV=0.4771
measured  p05=0.1400 med=0.3650 mean=0.3659 p95=0.5900  [0.115, 0.615]  CV=0.3945
ti le trung vi measured/legacy = 1.2167

=== A3b: truc measured, MIEN THUC NGHIEM (CLEAN) ===
E1/p05=0.1431 p50=0.3583 p95=0.5879 p99=0.6275 max=1.5689 CV=0.419529
CV mo hinh 0.394506 vs thuc nghiem 0.419529  (lech -5.96%)
max mo hinh 0.6150 s  vs  p99 thuc nghiem 0.6275 s / max 1.5689 s

=== A6: luoi z co nam trong mien cua truc khong ===
  Z_GRID_hien_tai (decision_error_v2.Z_GRID)
    grid = [0.0, 0.05, 0.1, 0.2, 0.3, 0.55]
    vs MO HINH legacy    [0.055,0.550]  NGOAI SUY tai z=[0.0, 0.05]  p95:cham max:cham
    vs MO HINH measured  [0.115,0.615]  NGOAI SUY tai z=[0.0, 0.05, 0.1] p95:KHONG max:KHONG
    vs THUC NGHIEM CLEAN  p95:KHONG p99:KHONG max:KHONG
  Z_GRID_20R2_MEASURED (de xuat)
    grid = [0.115, 0.17, 0.241, 0.305, 0.366, 0.43, 0.491, 0.555, 0.615]
    vs MO HINH legacy    [0.055,0.550]  NGOAI SUY tai z=[0.555, 0.615] p95:cham max:cham
    vs MO HINH measured  [0.115,0.615]  trong mien                   p95:cham max:cham
    vs THUC NGHIEM CLEAN  p95:cham p99:KHONG max:KHONG
  Z_EDGES_V7 (da khoa)
    grid = [0.1, 0.241, 0.366, 0.491, 0.641]
    vs MO HINH legacy    [0.055,0.550]  NGOAI SUY tai z=[0.641]      p95:cham max:cham
    vs MO HINH measured  [0.115,0.615]  NGOAI SUY tai z=[0.1, 0.641] p95:cham max:cham
    vs THUC NGHIEM CLEAN  p95:cham p99:cham max:KHONG

=== A4: G-A020 §4 chuyen giao -> FAIL -- G-A020 KHONG chuyen giao sang 20R2 ===
  dt                 ga020=0.1 s                        20R2=0.005 s                            KHAC
  tau                ga020=co dinh 3 s                  20R2=TRUC QUET [0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 28.0] KHAC
  estimand           ga020=rank-slot coverage/acceptance 20R2=RMS_ALLACTION_DELAY (err(z), d_sla) KHAC
  quy tac xep hang   ga020=4 hanh dong / 3 khe xep hang 20R2=4 duong, argmin top-1, khong xep hang khe KHAC
  so claim           ga020=<= 3 claim                   20R2=5 RQ (a-e)                         KHAC
  alpha              ga020=0.10                         20R2=0.10                               OK

=== A7: ngan sach CPU (960 o) ===
n_for_tau ti le tau=28/tau=0.5 = 1.400  (RT20-4 ghi 56)
  sweep_r2 (decision_error_v2 --run-fixed, 1 tau x 1 seed) n=166  9.25-15.30 s  mean=11.05  -> 2.95 h/nhanh
  sweep_r3 (cert.tau_sweep, 8 tau x 5 seed)            n= 18  37.77-41.73 s  mean=39.87  -> 10.63 h/nhanh

-> results/PENDING/phase-20R2/axis_audit.json

```
