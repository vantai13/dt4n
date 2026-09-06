# G'.3b -- sigma/tau round-trip and orthogonality -- PREREGISTRATION

Date: 2026-09-06T03:50:00.305564+00:00. STATUS: PREREGISTRATION. Signed before any network data. Synthetic feasibility and analysis checks precede signing.

## 1. Câu hỏi

Trên mạng thật, với cơ chế shaper đã được G'.2 và G'.3a chứng nhận:
(a) sigma đặt có lấy lại được trong 10% không?          -> claim C
(b) tau đặt có lấy lại được trong 20% không?            -> claim B
(c) hai trục có TRỰC GIAO không?                        -> tiền đề Phase G

Câu (c) chưa từng được kiểm. Nó là điều kiện tiên quyết để
err(z; sigma, tau, omega) có nghĩa như một hàm nhiều biến.

## 2. Estimator đã ký

  tau, sigma, sf : log-linear ACF slope, lags [lag_lo .. n_lags]
                   lag_lo = 2                (G-A019 / G-L103)
                   n_lags = round(0.4*tau/dt)  ★ MỚI, xem gate T-5
  sigma_hat      = sqrt(Var(rho_meas) * sf)
  v              = Var(rho_meas) * (1 - sf)

⚠️ n_lags scale theo tau LÀ MỘT THAY ĐỔI ESTIMATOR.
   NT 53 buộc chạy bias-sim TRƯỚC khi ký. Kết quả: results/SMOKE/phase-G2/g3b_bias_sim.json

## 3. Bảng ngân sách sai số

| gate  | đại lượng            | ngưỡng   | suy từ                                        | đo bằng            |
|-------|----------------------|----------|-----------------------------------------------|--------------------|
| RT-C1 | \|sigma_hat/sigma-1\|| <= 0.10  | claim C trực tiếp                             | sd + sf, mỗi link  |
| RT-B1 | \|tau_hat/tau - 1\|  | <= 0.20  | claim B trực tiếp                             | ACF slope lags 2.. |
| RT-O1 | \|d log tau_hat / d log sigma\| | <= 0.10 | TRỰC GIAO. Nếu tau_hat trôi theo sigma thì hai trục không tách. Ngưỡng = nửa ngân sách claim B chia log-range 1.6x | lưới 2x2 tại tau in {2,5} |
| RT-O2 | \|d log sigma_hat / d log tau\| | <= 0.05 | TRỰC GIAO. Nửa ngân sách claim C.       | cùng lưới 2x2      |
| T-5   | n_lags*dt / tau      | >= 0.3   | claim B. ACF phải suy giảm đáng kể trong cửa sổ fit; mô phỏng cho +157% khi tỉ số = 0.08 | tham số chạy   |
| Q-1   | sigma_l/sigma_qfloor | >= 4.36  | kế thừa doc 55/56                             | tính từ dt         |
| C-1   | clip_fraction        | <= 0.01  | claim C, cắt đuôi làm co sigma_hat            | đếm trực tiếp      |
| B-1a  | sf min-over-links    | >= 0.8264| claim C: sigma_hat/sigma = 1/sqrt(sf) <= 1.10  | intercept lags 2.. |
| S-1   | \|r_sink/r_set - 1\| | <= 0.02  | kế thừa doc 55, 1/5 ngân sách sigma           | byte counter sink  |
| K-2   | shaper underrun      | <= 0.001 | kế thừa G'.2                                  | tc -s qdisc        |

## 4. Quy tắc dừng

RT-B1 hoặc RT-C1 FAIL tại tau in {2,5}  -> STOP. Cơ chế không truyền được
                                            sigma/tau. Không amendment.
RT-B1 FAIL CHỈ tại tau = 30              -> LIMIT: cắt trần lưới tau xuống 10,
                                            ghi limit, đi tiếp. KHÔNG nới ngưỡng.
RT-O1 hoặc RT-O2 FAIL                    -> STOP. Hai trục không trực giao.
                                            Phase G phải thiết kế lại.

★ NGÂN SÁCH LẶP: 1 vòng chẩn đoán. Hết là ghi limit, không amendment thứ hai.

## 5. Dự đoán ký trước từ bias-sim đã thực thi

These are Monte Carlo medians, not confidence intervals. No empirical bias
correction is applied to measured tau: the G3b estimand is the raw lag-2+
slope median, following the supplied G3b code. Historical b(tau) for 8 lags
is not reused for the 20- and 120-lag windows.

| tau (s) | sigma_ref | n_lags | tau_hat median | tau error | sigma_hat/sigma |
|---:|---:|---:|---:|---:|---:|
| 2 | 0.028 | 8 | 1.934246 | -0.032877 | 0.995788 |
| 2 | 0.045 | 8 | 1.922975 | -0.038513 | 0.988691 |
| 5 | 0.028 | 20 | 5.073921 | +0.014784 | 0.986606 |
| 5 | 0.045 | 20 | 4.889578 | -0.022084 | 0.988633 |
| 30 | 0.036 | 120 | 29.182493 | -0.027250 | 0.993416 |

All five signed cells pass B/C in the bias simulation. The diagnostic
`legacy_estimator_worse_everywhere` is false; independent Monte Carlo samples
and longer fit windows do not guarantee a larger absolute legacy error in
every cell. This diagnostic is not an acceptance gate and is not hidden.

## 6. Frozen execution and aggregation

- dt = 0.1 s, omega = 0, rho_bar = 0.857, seed = 20260906.
- Grid, in order: (2, .028, 2), (2, .045, 2), (5, .028, 2),
  (5, .045, 2), (30, .036, 1); tuples are (tau_s, sigma_ref, runs).
- T_run = 205*tau: 410, 1025, 6150 seconds per run. Total planned
  measurement time = 11890 s, excluding setup and analysis.
- Eight links per run. sigma target on link l = a0*sqrt(degree_l)/C_l.
  Divide by this target BEFORE pooling; tau median and sigma-ratio median
  pool all run/link estimates in a cell (16 values, or 8 at tau=30).
  This is not the original doc 55 median-of-three-runs claim B protocol.
  Per-link and per-run estimates are retained for audit.
- RT-O1 is the signed mean of the two log-log tau slopes across sigma;
  RT-O2 is the signed mean of the two log-log sigma-ratio slopes across tau.
  Absolute value is taken AFTER the signed mean, as in the supplied code.
  Passing these aggregate statistics does not bound each individual slope.
- RT-C1 reads the pooled sigma ratio at every acquired cell, including tau=30.
  RT-B1_small_tau reads cells with tau <= 5; tau30 is a separate gate.
- B-1a uses the minimum over links of the median sf over runs. S-1 uses
  maximum absolute sink-rate error. C-1 uses maximum run-level global target
  clipping fraction. K-2 uses maximum backlog underrun fraction.
- RT-O1 = .10 and RT-O2 = .05 are the supplied design tolerances. The
  shorthand 'half the error budget divided by log-range' in the supplied
  table is a rationale, not an exact numerical derivation of .10/.05.
  Numerical limits are preserved without tuning to measured results.
- T-5 refers to nominal maximum lag. All fits retain the historical ACF
  noise-floor filter; n_lags_used and fit status are retained per link.
- Missing/nonfinite estimates cannot pass; incomplete grids cannot receive GO.
- Check stop rules after each completed cell. Stop on small-tau B/C failure,
  invalid estimates, or orthogonality failure once the 2x2 grid is present.
  Keep all acquired data, mark remaining cells unmeasured, do not pay for
  tau=30 after a signed STOP. A tau30-only B failure yields LIMIT_TAU_CEILING;
  tau=10 remains UNMEASURED, not automatically certified by interpolation.
- Otherwise GO requires all gates. GO_STAR is the supplied code's label for
  ancillary-gate failure; it is conditional and does not establish full validity.
- One diagnostic round maximum; no post-data threshold amendment.

## 7. Corrections to supplied code, made before network data

1. Doc 61 defines v = Var(eps) = 6.5e-5. For eps = w[k]-w[k-1],
   Var(w) must be v/2. The supplied sqrt(v) doubles the calibrated nugget.
   Simulation and dry-run use sqrt(v/2); white control uses sqrt(v).
   The requested estimator positive-control test retains its original,
   stronger 2v noise level and passes. No historical artifacts are edited.
2. The lag_lo regression compares 200 series to a frozen copy of the original
   function, not only default versus explicit calls of the same new function.
3. The generator dt guard probes the actual AR(1) recurrence with an impulse
   and zero subsequent innovations; a factor-two dt error is rejected without
   finite-sample ACF uncertainty. The historical generator is unchanged.
4. Q-1 is evaluated explicitly; the supplied adjudicator omitted this signed gate.
5. CLI requires an explicit mutually exclusive action. The run checks prereg
   ancestry, clean tracked code, simulation feasibility and output existence
   before traffic. JSON and NPZ refuse overwrite; raw per-run checkpoints and
   console progress survive a later failure.
6. Infrastructure monitor requires --duration, omitted in the supplied command.
   It produces JSONL; use g3b_infra.jsonl with 1 s interval and requested
   duration 12500 s. Monitor runs only alongside the network campaign. CPU,
   load, memory, network counters and clock skew are recorded. The existing
   monitor does not expose CPU steal separately.
7. No host quiescing or concurrent experiment workload. Existing services
   continue normally. Setup/teardown uses the existing isolated g2 veth/netns
   harness, after confirming no experiment occupies those names.

## 8. Limits fixed before measurement

Independent latent processes at omega=0 do not prove statistically independent
observations through a shared kernel; eight links are not automatically an
8x power guarantee. Orthogonality is assessed only at the sampled 2x2 grid.
Neither monotonic error in tau nor recovery at unsampled tau values is assumed.
At fixed dt, the quantisation lower bound is constant; the widening feasible
sigma region described for dt=tau/20 belongs to that alternative design.
Finite-run target variance itself fluctuates, so report generator-only fits
from saved targets as diagnostics rather than silently replacing nominal targets.
The sf >= .8264 gate is retained from the guide as a path-quality proxy;
the corrected sigma estimator is evaluated directly by RT-C1.

## 9. Pre-network validation and artifacts

- test/test_estimator_lag_lo.py: legacy numerical identity and MA(1) control.
- test/test_g3b_sigma_tau_grid.py: dt mismatch, axis slope signs, missing data,
  stopping/ceiling verdicts and refusal to overwrite raw evidence.
- results/SMOKE/phase-G2/g3b_bias_sim.json: synthetic feasibility (40 trials/case).
- results/SMOKE/phase-G2/g3b_dry_run.json: synthetic analysis rehearsal.
- Signed post-tag rehearsal: results/SMOKE/phase-G2/g3b_signed_dry/g3b_dry_run.json.
- Measured JSON: results/SMOKE/phase-G2/g3b_sigma_tau.json.
- Raw arrays: results/SMOKE/phase-G2/g3b_sigma_tau_series.npz.
- Per-run checkpoints: results/SMOKE/phase-G2/g3b_sigma_tau_checkpoints/.
- Infrastructure: results/SMOKE/phase-G2/g3b_infra.jsonl.
- Console and test logs: results/SMOKE/phase-G2/g3b_logs/.
- Result report: docs/phase-G/66-g3b-results.md; hashes recorded after acquisition.

Tag phase-G2-g3b-prereg must be created before setup/run. Predictions, grid,
aggregation and numerical thresholds above are frozen by that tag.
