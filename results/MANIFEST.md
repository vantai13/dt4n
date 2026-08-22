# MANIFEST -- kho artifact DT4N

Sinh tu dong boi `tools/build_manifest.py` tai commit `85ffde5`. Cot **Dung cho** do NGUOI dien, luu trong `results/_intent.json` de khong bi ghi de.

Bon tang (Lesson 23.17, amendment 23-44):

```text
  RAW           5849 file
  LIVE            11 file
  SUPERSEDED     373 file
  SMOKE           34 file
```

`RAW/` khong liet ke tung file o day: do la du lieu do tho, Hang 1 (khong tai tao duoc), chi doc, khong bao gio ghi de. Xem `results/RAW/README.md`.


## LIVE  (11 artifact json/parquet)

| Artifact | Sinh boi | git | Ngay | Truc AoI | Truc SLA | Dung cho |
|---|---|---|---|---|---|---|
| `phase-20R/sla_calibration.json` | `measurements.sla_calib_v2` | `?` | 2026-08-04 | - | - | Nguong SLA + w_loss theo cell. Doc boi build_calib_set_v2/v3, cell_matrices, decomposition, eight_cell_sweep, gate_report, live_region_sweep, decision_error_v2. CANH BAO S14 (self-calibrated), thay o Lesson 23.21 |
| `phase-23/a0_instrument_calibration.json` | `?` | `?` | ? | - | - | Hieu chuan nhac cu do A0 (M-66..M-69, NC-do-1..3). Doc boi instrument_calibration.py |
| `phase-23/aoi_decomposition.json` | `measurements/aoi_decompose.py` | `e39d7ab` | 2026-08-22 | - | - | Phan ra AoI = d_transport + phase (Lesson 23.18 T3-T7). Chot d = 115.50 ms (moment, khong phu thuoc bias); co che vong PATCH do bang Var~E va vi tri that; corr(AoI,rho) trong link = +0.026; phat hien L30 (rho uA/uB sai chieu) |
| `phase-23/aoi_model_selfcheck.json` | `?` | `?` | ? | - | - | Selfcheck + doi chung cho aoi_model_v7 (Lesson 23.19 Task B/C/D/E). Dai CHUAN HOA THEO MEAN (d triet tieu; mean la tautology nen bi loai). M-110 = 1/3: p50 4.10 sigma, p95 4.03 sigma NGOAI -> L35, co che chua biet. M-111/M-112/M-113 HIT: selfcheck co suc phan biet. Z_EDGES_V7 khoa o amendment 23-48 |
| `phase-23/aoi_sampling_diagnostic.json` | `?` | `?` | ? | - | - | Chan doan lay mau probe (Lesson 23.19 Task A). Phan xu H7_BIASED_MUST_CORRECT: probe khoa tuong uoc gan 5:1 voi vong sync (jitter chi 0.079 ms) -> phan bo AoI do duoc la mot LUOC 5 rang, KHONG phai phan bo trung binh theo thoi gian ma pipeline can. Dinh luong sai so lay mau len d: +/-6.5 ms (95%) |
| `phase-23/aoi_stall_anatomy.json` | `measurements/aoi_stall_anatomy.py` | `3ae6390` | 2026-08-22 | - | - | Giai phau chu ky stall (Lesson 23.18 T1/T2 + vong ra soat 45b). Phan xu H1 vs H2 vs H3; sau khi cat 20 chu ky warm-up AoI la RANG CUA SACH (sd lech 0.23%, CV lech 0.000893 so voi null DUNG). Muc tieu selfcheck cho aoi_model_v7 o Lesson 23.19 |
| `phase-23/aoi_v7_estimates.json` | `?` | `71cd524` | 2026-08-22 | - | - | So do AoI tren topology_v7, 30 run x 120 s, 287.760 quan sat (Lesson 23.8). Co so SO cua amendment 23-44 va cua aoi_model_v7 se dung o Lesson 23.19/23.20 |
| `phase-23/dsync_sensitivity.json` | `cert/dsync_sensitivity.py` | `d899a4f` | 2026-08-21 | - | - | Quet d_sync tren {51, 175, 205, 230, 260} ms. Cong cu do do nhay -- chinh no la thu do truc, nen khong the bi truc lam sai |
| `phase-L/link_model_v2_fit.json` | `results/phase-L/campaign_state.json` | `?` | ? | - | - | Fit mo hinh link v2 tren do Phase L. Dau vao cua twin/cost_v2 (FIT_PATH); doc boi l7_fit, sla_calib_v2, t5_campaign, qs_loss_residual; **can xac nhan hinh/bang** |
| `phase-20R/decision_error_by_age_by_regime.parquet` | `?` | `?` | ? | - | - | Duong cong sai so quyet dinh tren LUOI z CO DINH [0, .05, .1, .2, .3, .55, 1, 2, 4] s. Doc boi decision_error_v2, h9_separability, plot_decision_error_v2; **can xac nhan hinh/bang** |
| `phase-20R/truth_table.parquet` | `?` | `?` | ? | - | - | Bang tra chi phi do duoc cua Phase 20R. Doc boi decision_error_v2, cell_matrices, gate_report, build_truth_table, l6_campaign_fine, quasistatic_check; **can xac nhan hinh/bang** |

## SUPERSEDED  (320 artifact json/parquet)

| Artifact | Sinh boi | git | Ngay | Truc AoI | Truc SLA | Dung cho |
|---|---|---|---|---|---|---|
| `aoi/aoi_a2_host_srv1_gcp_20260816.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `calib/link_profiles.json` | `results/calib/raw_sweep_2node.csv` | `?` | ? | - | - | _(dien tay)_ |
| `phase-14b/sync_headroom_corrected_200x150_s0.json` | `?` | `76a9cd2` | ? | - | - | _(dien tay)_ |
| `phase-14b/sync_headroom_z5_200x150_s0.json` | `?` | `76a9cd2` | ? | - | - | _(dien tay)_ |
| `phase-14c/factorial_300x200_s0-2.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-14c/factorial_honest_200x200_s0.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-14c/factorial_honest_300x200_s0-2.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-14c/factorial_honest_300x200_s0-2_byz.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-14c/factorial_honest_with_C1.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-14c/negctrl_2path.json` | `?` | `5b6bb5c` | ? | - | - | _(dien tay)_ |
| `phase-14c/negctrl_2path_byz.json` | `?` | `989dc2f` | ? | - | - | _(dien tay)_ |
| `phase-14c/placebo_honest.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/between_trace_summary.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/between_trace_summary_n5.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/block_crossing_diagnostic_n5.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/core_load_diagnostic_n5.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_measured_fixed_replicates_summary.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_measured_fixed_trace_s0.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_measured_fixed_trace_s1.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_measured_fixed_trace_s2.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_measured_fixed_trace_s3.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_measured_fixed_trace_s4.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_measured_long.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_measured_replicates_summary.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_measured_trace_s0.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_measured_trace_s1.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_measured_trace_s2.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_measured_trace_s3.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_measured_trace_s4.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_offered.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_offered_nc.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_replicates_summary.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_trace_s0.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_trace_s1.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_trace_s2.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_trace_s3.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/decision_error_trace_s4.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/estimator_compare_10ms.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/estimator_compare_long.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/measured_crosscheck_diagnostic_n5.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/measured_fixed_crosscheck_diagnostic_n5.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/tau_summary_10ms.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/tau_summary_2ms.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20/tau_summary_long.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/additivity_band_sawtooth.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/additivity_branch_a_state.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/additivity_branch_a_state_budgetfix.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/additivity_branch_a_state_inband.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/additivity_check.json` | `measurements.additivity_check` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/additivity_check_probe_runtime.json` | `measurements.additivity_check` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/additivity_plan.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/band_v2_cascade.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/band_v2_transfer.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/branch_b_fixed_s104_108.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/branch_c_fixed_s104_108.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/breakdown_scan_cascade.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/breakdown_scan_cascade_pilot_n30k.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/breakdown_scan_transfer_n30k_bracket.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/breakdown_scan_transfer_qt3_n120k.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/campaign_state.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/continuity_check.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/continuity_state.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/controls.json` | `measurements.decision_error_v2` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/decision_error_sawtooth.json` | `measurements.decision_error_v2` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/diag_ca_late.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/diag_ca_late_inband.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/diag_interp_bias.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/g6_differential.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/g6_differential_inband.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/h9_separability.json` | `measurements.h9_separability` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/locked_argmin_check.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/margin_cv_ci.json` | `measurements.decision_error_v2` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/margin_cv_ci_n800k.json` | `measurements.decision_error_v2` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/margin_radius.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/mechanism_k4_closed_form.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/mechanism_maps.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/mechanism_predictions.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/pilot_power_fixed_s101_108.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/prediction_pre_campaign.json` | `measurements.predict_err_quick` | `?` | 2026-08-04 | - | - | _(dien tay)_ |
| `phase-20R/qs_loss_residual.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/quasistatic_band.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/quasistatic_check.json` | `measurements.quasistatic_check` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/quasistatic_plan.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/residual_cascade.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/residual_transfer.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/sd_stability_s101_108.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/sentinel_control.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/sentinel_loss_recheck.json` | `?` | `ae655ee` | ? | - | - | _(dien tay)_ |
| `phase-21/calib_set_measured_report.json` | `cert/build_calib_set.py` | `2c356de` | 2026-07-28 | - | - | _(dien tay)_ |
| `phase-21/calib_set_offered_report.json` | `cert/build_calib_set.py` | `2c356de` | 2026-07-28 | - | - | _(dien tay)_ |
| `phase-21/conformal_measured_z.json` | `cert/conformal_age.py` | `0b05064` | 2026-07-28 | - | - | _(dien tay)_ |
| `phase-21/conformal_offered_z.json` | `cert/conformal_age.py` | `0b05064` | 2026-07-28 | - | - | _(dien tay)_ |
| `phase-21/conformal_offered_zu.json` | `cert/conformal_age.py` | `0b05064` | 2026-07-28 | - | - | _(dien tay)_ |
| `phase-21/error_vs_age_measured_svsa1.json` | `cert/error_vs_age.py` | `2c356de` | 2026-07-28 | - | - | _(dien tay)_ |
| `phase-21/error_vs_age_offered_s_maxabs.json` | `cert/error_vs_age.py` | `2c356de` | 2026-07-28 | - | - | _(dien tay)_ |
| `phase-21/error_vs_age_offered_s_range.json` | `cert/error_vs_age.py` | `2c356de` | 2026-07-28 | - | - | _(dien tay)_ |
| `phase-21/error_vs_age_offered_svsa1.json` | `cert/error_vs_age.py` | `2c356de` | 2026-07-28 | - | - | _(dien tay)_ |
| `phase-21/risk_coverage_oos.json` | `inline risk_coverage_oos from cert.conformal_age split` | `0b05064` | 2026-07-28 | - | - | _(dien tay)_ |
| `phase-21/sens_payload_calib.json` | `cert/build_calib_set.py` | `fab9080` | 2026-07-28 | - | - | _(dien tay)_ |
| `phase-21/sens_payload_conformal.json` | `cert/conformal_age.py` | `fab9080` | 2026-07-28 | - | - | _(dien tay)_ |
| `phase-21/sens_payload_usefulness.json` | `cert/usefulness.py` | `fab9080` | 2026-07-28 | - | - | _(dien tay)_ |
| `phase-21/usefulness_measured.json` | `cert/usefulness.py` | `6e1fa91` | 2026-07-28 | - | - | _(dien tay)_ |
| `phase-21/usefulness_offered.json` | `cert/usefulness.py` | `7fc60a6` | 2026-07-28 | - | - | _(dien tay)_ |
| `phase-21R/anchor.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-21R/calib_set_cbr_0.700.json` | `cert/build_calib_set_v2.py` | `cdc4a56` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/calib_set_h2_0.700.json` | `cert/build_calib_set_v2.py` | `cdc4a56` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/calib_set_h2_0.850.json` | `cert/build_calib_set_v2.py` | `cdc4a56` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/calib_set_h2_0.925.json` | `cert/build_calib_set_v2.py` | `cdc4a56` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/calib_set_poisson_0.700.json` | `cert/build_calib_set_v2.py` | `cdc4a56` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/calib_set_poisson_0.850.json` | `cert/build_calib_set_v2.py` | `cdc4a56` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/calib_set_poisson_0.925.json` | `cert/build_calib_set_v2.py` | `cdc4a56` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/calib_set_poisson_0.925_V3.json` | `cert/build_calib_set_v2.py` | `cdc4a56` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/conformal_cbr_0.700.json` | `cert/conformal_v2.py` | `46c7245` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/conformal_h2_0.700.json` | `cert/conformal_v2.py` | `46c7245` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/conformal_poisson_0.850.json` | `cert/conformal_v2.py` | `46c7245` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/conformal_poisson_0.925.json` | `cert/conformal_v2.py` | `46c7245` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/decomposition_cbr_0.700.json` | `cert/decomposition.py` | `2c3b782` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/decomposition_h2_0.700.json` | `cert/decomposition.py` | `2c3b782` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/decomposition_poisson_0.850.json` | `cert/decomposition.py` | `2c3b782` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/decomposition_poisson_0.925.json` | `cert/decomposition.py` | `2c3b782` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/error_vs_age_cbr_0.700.json` | `cert/error_vs_age_v2.py` | `a72ff5f` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/error_vs_age_h2_0.700.json` | `cert/error_vs_age_v2.py` | `a72ff5f` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/error_vs_age_poisson_0.850.json` | `cert/error_vs_age_v2.py` | `a72ff5f` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/error_vs_age_poisson_0.925.json` | `cert/error_vs_age_v2.py` | `a72ff5f` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/freshness_h2_0.700.json` | `cert/freshness_requirement.py` | `1387f01` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/freshness_poisson_0.850.json` | `cert/freshness_requirement.py` | `1387f01` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/freshness_poisson_0.925.json` | `cert/freshness_requirement.py` | `1387f01` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/gate_report_h2_0.700.json` | `cert/gate_report.py` | `8d8ee8b` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/gate_report_poisson_0.850.json` | `cert/gate_report.py` | `8d8ee8b` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/gate_report_poisson_0.925.json` | `cert/gate_report.py` | `8d8ee8b` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/operational_sigma.json` | `cert/operational_sigma.py` | `30674c9` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/prediction_scorecard.json` | `cert/gate_report.py` | `8d8ee8b` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/usefulness_cbr_0.700.json` | `cert/usefulness_v2.py` | `63afa37` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/usefulness_h2_0.700.json` | `cert/usefulness_v2.py` | `63afa37` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/usefulness_poisson_0.850.json` | `cert/usefulness_v2.py` | `63afa37` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-21R/usefulness_poisson_0.925.json` | `cert/usefulness_v2.py` | `63afa37` | 2026-08-12 | - | - | _(dien tay)_ |
| `phase-22/aoi_profiles_h2_0.700.json` | `cert/aoi_profiles.py` | `7ee5142` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/aoi_profiles_poisson_0.850.json` | `cert/aoi_profiles.py` | `7ee5142` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/aoi_profiles_poisson_0.925.json` | `cert/aoi_profiles.py` | `7ee5142` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_cbr_0.700.json` | `cert/build_calib_set_v3.py` | `f95c6be` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_h2_0.650_report.json` | `cert/build_calib_set_v3.py` | `57974cf` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_h2_0.700.json` | `cert/build_calib_set_v3.py` | `c0e884c` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_h2_0.850_report.json` | `cert/build_calib_set_v3.py` | `b453703` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_h2_0.925_report.json` | `cert/build_calib_set_v3.py` | `b453703` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_h2_0.960_report.json` | `cert/build_calib_set_v3.py` | `b453703` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_poisson_0.700.json` | `cert/build_calib_set_v3.py` | `f95c6be` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_poisson_0.700_report.json` | `cert/build_calib_set_v3.py` | `b453703` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_poisson_0.850.json` | `cert/build_calib_set_v3.py` | `15d8a04` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_poisson_0.875_report.json` | `cert/build_calib_set_v3.py` | `57974cf` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_poisson_0.900_report.json` | `cert/build_calib_set_v3.py` | `57974cf` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_poisson_0.925.json` | `cert/build_calib_set_v3.py` | `f95c6be` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_poisson_0.925_V3.json` | `cert/build_calib_set_v3.py` | `f95c6be` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_poisson_0.960_report.json` | `cert/build_calib_set_v3.py` | `b453703` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_report.json` | `cert/build_calib_set_v3.py` | `945ce38` | 2026-08-14 | - | - | _(dien tay)_ |
| `phase-22/config_matrix_cbr_0.700.json` | `cert/config_matrix.py` | `660d823` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/config_matrix_h2_0.700.json` | `cert/config_matrix.py` | `660d823` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/config_matrix_poisson_0.700.json` | `cert/config_matrix.py` | `660d823` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/config_matrix_poisson_0.850.json` | `cert/config_matrix.py` | `660d823` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/config_matrix_poisson_0.925.json` | `cert/config_matrix.py` | `660d823` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/config_matrix_poisson_0.925_V3.json` | `cert/config_matrix.py` | `660d823` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/conformal_sim_cbr_0.700.json` | `cert/conformal_simultaneous.py` | `63df2f0` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/conformal_sim_h2_0.700.json` | `cert/conformal_simultaneous.py` | `63df2f0` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/conformal_sim_poisson_0.700.json` | `cert/conformal_simultaneous.py` | `63df2f0` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/conformal_sim_poisson_0.850.json` | `cert/conformal_simultaneous.py` | `63df2f0` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/conformal_sim_poisson_0.925.json` | `cert/conformal_simultaneous.py` | `63df2f0` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/conformal_sim_poisson_0.925_V3.json` | `cert/conformal_simultaneous.py` | `63df2f0` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/gate_report_cbr_0.700.json` | `cert/gate_report_22.py` | `660d823` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/gate_report_h2_0.700.json` | `cert/gate_report_22.py` | `660d823` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/gate_report_poisson_0.850.json` | `cert/gate_report_22.py` | `660d823` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/gate_report_poisson_0.925.json` | `cert/gate_report_22.py` | `660d823` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/selective_cbr_0.700.json` | `cert/selective_conformal.py` | `62475ef` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/selective_h2_0.700.json` | `cert/selective_conformal.py` | `62475ef` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/selective_poisson_0.700.json` | `cert/selective_conformal.py` | `62475ef` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/selective_poisson_0.850.json` | `cert/selective_conformal.py` | `62475ef` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/selective_poisson_0.925.json` | `cert/selective_conformal.py` | `62475ef` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/selective_poisson_0.925_V3.json` | `cert/selective_conformal.py` | `62475ef` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/tau_sweep_cbr_0.700.json` | `cert/tau_sweep.py` | `bf98eb5` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/tau_sweep_h2_0.700.json` | `cert/tau_sweep.py` | `bf98eb5` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/tau_sweep_poisson_0.850.json` | `cert/tau_sweep.py` | `bf98eb5` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-22/tau_sweep_poisson_0.925.json` | `cert/tau_sweep.py` | `bf98eb5` | 2026-08-13 | - | - | _(dien tay)_ |
| `phase-23/abstain_cost_h2_0.700.json` | `cert/abstain_cost.py` | `e634aea` | ? | - | - | _(dien tay)_ |
| `phase-23/abstain_cost_poisson_0.850.json` | `cert/abstain_cost.py` | `e634aea` | ? | - | - | _(dien tay)_ |
| `phase-23/abstain_cost_poisson_0.925.json` | `cert/abstain_cost.py` | `e634aea` | ? | - | - | _(dien tay)_ |
| `phase-23/aurc_go1_cbr_0.700.json` | `cert/aurc_go1.py` | `61e360d` | 2026-08-17 | - | - | _(dien tay)_ |
| `phase-23/aurc_go1_h2_0.700.json` | `cert/aurc_go1.py` | `61e360d` | 2026-08-17 | - | - | _(dien tay)_ |
| `phase-23/aurc_go1_poisson_0.700.json` | `cert/aurc_go1.py` | `61e360d` | 2026-08-17 | - | - | _(dien tay)_ |
| `phase-23/aurc_go1_poisson_0.850.json` | `cert/aurc_go1.py` | `61e360d` | 2026-08-17 | - | - | _(dien tay)_ |
| `phase-23/aurc_go1_poisson_0.925.json` | `cert/aurc_go1.py` | `61e360d` | 2026-08-17 | - | - | _(dien tay)_ |
| `phase-23/baseline_c3_b2_audit_h2_0.700_C3_static.json` | `?` | `84c940d` | ? | - | - | _(dien tay)_ |
| `phase-23/baseline_c3_b2_audit_poisson_0.850_C3_static.json` | `?` | `78bf78e` | ? | - | - | _(dien tay)_ |
| `phase-23/baseline_c3_b2_audit_poisson_0.925_C3_static.json` | `?` | `61b09f6` | ? | - | - | _(dien tay)_ |
| `phase-23/baseline_rankings_h2_0.700_C3_static.json` | `?` | `d180804` | ? | - | - | _(dien tay)_ |
| `phase-23/baseline_rankings_poisson_0.850_C3_static.json` | `?` | `d180804` | ? | - | - | _(dien tay)_ |
| `phase-23/baseline_rankings_poisson_0.925_C3_static.json` | `?` | `6c52fc9` | ? | - | - | _(dien tay)_ |
| `phase-23/conditioning_audit_h2_0.700.json` | `cert/conditioning_audit.py` | `f252426` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-23/conditioning_audit_poisson_0.850.json` | `cert/conditioning_audit.py` | `f252426` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-23/conditioning_audit_poisson_0.925.json` | `cert/conditioning_audit.py` | `f252426` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-23/conditioning_audit_summary.json` | `cert/conditioning_audit.py --summarize` | `f252426` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-23/cross_cell_summary.json` | `cert/phase23_cross_cell.py` | `e36b8c3` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/dsync_bridge_micro_pilot.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-23/eight_cell_sweep.json` | `cert/eight_cell_sweep.py` | `7df8d48` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-23/fallback_fine_grid_poisson_0.925_C3_exploratory.json` | `cert/fallback.py run_report via inline fine-grid writer` | `2b043d8` | 2026-08-14 | - | - | _(dien tay)_ |
| `phase-23/fallback_grid_poisson_0.925_C3.json` | `cert/fallback.py via grid extraction` | `4242192` | 2026-08-14 | - | - | _(dien tay)_ |
| `phase-23/fallback_h2_0.700_C3_k0.15.json` | `cert/fallback.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/fallback_h2_0.700_C3_k0.20.json` | `cert/fallback.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/fallback_h2_0.700_C3_k0.25.json` | `cert/fallback.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/fallback_h2_0.700_C3_k0.30.json` | `cert/fallback.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/fallback_h2_0.700_C3_k0.35.json` | `cert/fallback.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/fallback_h2_0.700_C3_k0.40.json` | `cert/fallback.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/fallback_h2_0.700_C3_k0.50.json` | `cert/fallback.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/fallback_inference_poisson_0.925_C3_k0.25.json` | `cert/fallback.py inference helpers via inline artifact writer` | `2b043d8` | 2026-08-14 | - | - | _(dien tay)_ |
| `phase-23/fallback_mechanism_diagnostics_poisson_0.925_C3.json` | `cert/fallback.py helpers via mechanism diagnostic writer` | `b75cf0d` | 2026-08-14 | - | - | _(dien tay)_ |
| `phase-23/fallback_poisson_0.850_C3_k0.15.json` | `cert/fallback.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/fallback_poisson_0.850_C3_k0.20.json` | `cert/fallback.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/fallback_poisson_0.850_C3_k0.25.json` | `cert/fallback.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/fallback_poisson_0.850_C3_k0.30.json` | `cert/fallback.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/fallback_poisson_0.850_C3_k0.35.json` | `cert/fallback.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/fallback_poisson_0.850_C3_k0.40.json` | `cert/fallback.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/fallback_poisson_0.850_C3_k0.50.json` | `cert/fallback.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/fallback_poisson_0.925_k0.5.json` | `cert/fallback.py` | `914effa` | 2026-08-14 | - | - | _(dien tay)_ |
| `phase-23/fallback_sweep.json` | `cert/fallback_sweep.py` | `637a3b1` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-23/fallback_v23_3_seed_split_poisson_0.925_C3_k0.25.json` | `cert/fallback.py inference helpers via inline V23-3 writer` | `2b043d8` | 2026-08-14 | - | - | _(dien tay)_ |
| `phase-23/g23_17a_cell_margins.json` | `?` | `20ee60d` | ? | - | - | _(dien tay)_ |
| `phase-23/g23_17b_code_sanity.json` | `?` | `ac3cf85` | ? | - | - | _(dien tay)_ |
| `phase-23/g23_17c_scale_and_sla.json` | `?` | `ab2ffb2` | ? | - | - | _(dien tay)_ |
| `phase-23/g23_23_lift_law.json` | `cert/phase23_cross_cell.py` | `c17b8bb` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/go2_fwer_restatement.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-23/go2_simultaneous_h2_0.700.json` | `cert/go2_simultaneous.py` | `bbac749` | 2026-08-18 | - | - | _(dien tay)_ |
| `phase-23/go2_simultaneous_poisson_0.850.json` | `cert/go2_simultaneous.py` | `bbac749` | 2026-08-18 | - | - | _(dien tay)_ |
| `phase-23/go2_simultaneous_poisson_0.925.json` | `cert/go2_simultaneous.py` | `bbac749` | 2026-08-18 | - | - | _(dien tay)_ |
| `phase-23/lesson23_7_calibration_2b.json` | `cert/lesson23_7_calibration_2b.py` | `75dc6e9` | 2026-08-20 | - | - | _(dien tay)_ |
| `phase-23/lesson23_7_feasibility.json` | `cert/lesson23_7_feasibility.py` | `75dc6e9` | 2026-08-20 | - | - | _(dien tay)_ |
| `phase-23/lesson23_7_range_calibration.json` | `cert/lesson23_7_range_calibration.py` | `75dc6e9` | 2026-08-20 | - | - | _(dien tay)_ |
| `phase-23/lift_decomposition_by_cell.json` | `tools/lift_decomposition_by_cell.py` | `744fda1` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-23/live_region_sweep.json` | `cert/live_region_sweep.py::run_sweep` | `9964a0b` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-23/objective_misspecification_sweep.json` | `cert/objective_misspecification.py` | `1de8558` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-23/relative_conclusions_h2_0.700.json` | `cert/conditioning_audit.py --relative` | `860915a` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-23/relative_conclusions_poisson_0.850.json` | `cert/conditioning_audit.py --relative` | `860915a` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-23/relative_conclusions_poisson_0.925.json` | `cert/conditioning_audit.py --relative` | `860915a` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-23/residual_level_audit_h2_0.700.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-23/residual_level_audit_poisson_0.850.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-23/residual_level_audit_poisson_0.925.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-23/residual_relative_audit_h2_0.700.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-23/residual_relative_audit_poisson_0.850.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-23/residual_relative_audit_poisson_0.925.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-23/sla_calibration_lesson23_16.json` | `cert/live_region_sweep.py::prepare_sla` | `76d2756` | 2026-08-21 | - | - | _(dien tay)_ |
| `phase-23/studentized_h2_0.700.json` | `cert/studentized_score.py` | `ea2aa04` | 2026-08-17 | - | - | _(dien tay)_ |
| `phase-23/studentized_poisson_0.850.json` | `cert/studentized_score.py` | `ea2aa04` | 2026-08-17 | - | - | _(dien tay)_ |
| `phase-23/studentized_poisson_0.925.json` | `cert/studentized_score.py` | `ea2aa04` | 2026-08-17 | - | - | _(dien tay)_ |
| `phase-23/threshold_families_h2_0.700_C3_static.json` | `cert/threshold_families.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/threshold_families_poisson_0.850_C3_static.json` | `cert/threshold_families.py` | `d180804` | 2026-08-15 | - | - | _(dien tay)_ |
| `phase-23/threshold_families_poisson_0.925_C3_static.json` | `cert/threshold_families.py` | `2c2daf0` | 2026-08-14 | - | - | _(dien tay)_ |
| `phase-L/campaign_state.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-L/l1_infra_0729_0716.json` | `?` | `?` | 2026-07-29 | - | - | _(dien tay)_ |
| `phase-L/l1_infra_0729_0728.json` | `?` | `?` | 2026-07-29 | - | - | _(dien tay)_ |
| `phase-L/l1_infra_0729_0746.json` | `?` | `?` | 2026-07-29 | - | - | _(dien tay)_ |
| `phase-L/l1_infra_0729_0803.json` | `?` | `?` | 2026-07-29 | - | - | _(dien tay)_ |
| `phase-L/l1_infra_0729_0900.json` | `?` | `?` | 2026-07-29 | - | - | _(dien tay)_ |
| `phase-L/l2_probe_0729_0748.json` | `?` | `?` | 2026-07-29 | - | - | _(dien tay)_ |
| `phase-L/l2_probe_0729_0752.json` | `?` | `?` | 2026-07-29 | - | - | _(dien tay)_ |
| `phase-L/l2_probe_0729_0803.json` | `?` | `?` | 2026-07-29 | - | - | _(dien tay)_ |
| `phase-L/l2_probe_0729_0900.json` | `?` | `?` | 2026-07-29 | - | - | _(dien tay)_ |
| `phase-L/l2_vl0_floor_stats_0729_0752.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-L/l2_vl2_bw6_stats_0729_0752.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-L/l2_vl2b_bw6_r0_stats_0729_0752.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-L/l4_loadgen_0729_0941.json` | `?` | `?` | 2026-07-29 | - | - | _(dien tay)_ |
| `phase-L/l4_loadgen_0729_0955.json` | `?` | `?` | 2026-07-29 | - | - | _(dien tay)_ |
| `phase-L/l4_loadgen_0729_1007.json` | `?` | `?` | 2026-07-29 | - | - | _(dien tay)_ |
| `phase-L/l4_loadgen_0729_1020.json` | `?` | `?` | 2026-07-29 | - | - | _(dien tay)_ |
| `phase-L/l5_pilot_0729_1336.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-L/l7_reich_workload.json` | `results/phase-L/raw` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/campaign_state.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/control_sameseed_state.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/control_state.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/step_state.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/t6_results.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/t6b_results.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/t6d_cell_level.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/t6e_paired.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/t6f_split_dynamics.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/t6g_jensen_check.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/t6h_kappa_map.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/t6h_kappa_map.rerun.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/t7_gate_table.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/decision_error_by_age_summary.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/decision_error_constant_sigma.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/decision_error_delay_only.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/decision_error_tau0.2.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/decision_error_tau1.0.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/decision_error_tau5.0.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/decision_error_unimodal.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/decision_error_w2500.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/margin_cv_a02.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/margin_cv_by_tau.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/margin_cv_by_tau_operational.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/margin_cv_operational.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/margin_cv_unimodal.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/sensitivity_a02.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-21R/calib_set_cbr_0.700.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-21R/calib_set_h2_0.700.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-21R/calib_set_h2_0.850.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-21R/calib_set_h2_0.925.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-21R/calib_set_poisson_0.700.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-21R/calib_set_poisson_0.850.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-21R/calib_set_poisson_0.925.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-21R/calib_set_poisson_0.925_V3.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_cbr_0.700.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_h2_0.650.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_h2_0.700.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_h2_0.850.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_h2_0.925.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_h2_0.960.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_poisson_0.700.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_poisson_0.850.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_poisson_0.875.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_poisson_0.900.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_poisson_0.925.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_poisson_0.925_V3.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-22/calib_set_v3_poisson_0.960.parquet` | `?` | `?` | ? | - | - | _(dien tay)_ |

## SMOKE  (32 artifact json/parquet)

| Artifact | Sinh boi | git | Ngay | Truc AoI | Truc SLA | Dung cho |
|---|---|---|---|---|---|---|
| `gcp-smoke/aoi_a2_host_srv1_gcp_smoke_20260816.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/additivity_branch_a_state_bg.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/additivity_branch_a_state_budgetfix_bg.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/additivity_branch_a_state_inband_FAILED_race.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/additivity_branch_a_state_inband_bg.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/additivity_check_bg.json` | `measurements.additivity_check` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/additivity_check_budgetfix_bg.json` | `measurements.additivity_check` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/additivity_check_inband_bg.json` | `measurements.additivity_check` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/band_v2_transfer_smoke.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/branch_b_fixed_pilot3.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/branch_b_fixed_preflight120.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/branch_b_tmux_preflight.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/branch_b_tmux_preflight120.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/branch_b_v2_smoke.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/branch_c_fixed_pilot3.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/branch_c_fixed_preflight120.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/branch_c_tmux_preflight.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/branch_c_tmux_preflight120.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/branch_c_v2_smoke.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/breakdown_scan_cascade_smoke.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/breakdown_scan_transfer_qt3_smoke.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/breakdown_scan_transfer_qt3_smoke_n2k.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/breakdown_scan_transfer_smoke.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/pilot_power_fixed_pilot3.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-20R/smoke_state.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-23/a0_instrument_calibration_attempt1.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-23/a0_instrument_calibration_attempt2.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-23/a2_smoke_estimate.json` | `?` | `?` | 2026-08-22 | - | - | _(dien tay)_ |
| `phase-L/campaign_smoke_state.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/campaign_state.preA14.20260803_002319.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/smoke_state.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
| `phase-T/smoke_state.preA7.20260731_052633.json` | `?` | `?` | ? | - | - | _(dien tay)_ |
