# MAP - Ban do repo DT4N

Cap nhat: 2026-07-28 | Nhanh lam viec: `main`

## Di dau truoc

| Viec | Duong dan |
|---|---|
| Xem loi digital twin hien tai | `twin/link_model.py` |
| Lam Phase 20 kill-test | `docs/phase-20/00-preregistration.md`, `docs/phase-20/00b-amendment-1.md`, `docs/phase-20/00c-amendment-2.md`, `docs/phase-20/00d-amendment-3.md`, `docs/phase-20/00e-amendment-4.md`, `docs/phase-20/00f-amendment-5.md`, `docs/phase-20/00g-amendment-6.md`, `docs/phase-20/00h-amendment-7.md`, `docs/phase-20/99-gate-decision.md` |
| Chay lai Gate 20 day du n=5 | `tools/phase20_full5_rerun.sh`, `runbooks/phase-20-full5-rerun.md` |
| Chay phu luc/audit Phase 20 mot lan | `tools/phase20_appendix_once.sh`, `runbooks/phase-20-appendix-once.md` |
| Nen Phase 21 conformal | `docs/phase-21/00-conformal-foundation.md`, `docs/phase-21/PHASE_21.md` |
| Lam Phase 21 conformal | `docs/phase-21/00-preregistration.md`, `docs/phase-21/00-conformal-foundation.md`, `cert/` |
| Xay tap calib Phase 21 | `cert/build_calib_set.py`, `docs/phase-21/00b-amendment-1.md`, `results/phase-21/` |
| Phan tich error-vs-age Phase 21 | `cert/error_vs_age.py`, `docs/phase-21/02-error-vs-age.md`, `results/phase-21/error_vs_age_*.json` |
| Kiem coverage conformal Phase 21 | `cert/conformal_age.py`, `docs/phase-21/00d-amendment-3.md`, `results/phase-21/conformal_*.json` |
| Dong Phase 21 usefulness/gate | `cert/usefulness.py`, `cert/plot_usefulness.py`, `docs/phase-21/04-usefulness.md`, `docs/phase-21/99-gate-decision.md` |
| Xem san khau Q7=B | `twin/topology_v7.py` |
| Do tau/sigma va decision error Phase 20 | `tools/phase20_smoke.sh`, `mininet/run_sync_v7.py`, `measurements/measure_tau.py`, `measurements/compare_estimators.py`, `measurements/decision_error.py`, `measurements/summarize_decision_error_replicates.py`, `measurements/phase20_core_load_diagnostic.py`, `measurements/phase20_block_crossing_diagnostic.py`, `measurements/phase20_measured_crosscheck_diagnostic.py`, `runbooks/phase-20-traffic-v7-tmux.md` |
| Fit lai profile calibration | `twin/link_model_fit.py` |
| Do lai link Mininet | `measurements/calib_link_sweep.py` |
| Do lai AoI that | `measurements/aoi_probe.py` |
| Chay Mininet + Ditto sync | `mininet/run_sync.py` |
| Quan ly lifecycle Mininet/Ditto | `mininet/env_runner.py` |
| Doc snapshot tu Ditto | `bridge/ditto_reader.py` |
| Dong bo len Ditto | `bridge/sync_agent.py`, `bridge/collector.py` |
| Lenh chieu xuong | `bridge/command_agent.py` |
| Scenario/injection song | `rl/scenarios.py`, `rl/injection.py`, `rl/oracle_policy.py` |
| Ket qua phase cu | `docs/phase-*/`, `results/phase-14*/` |
| RL va script cu | `legacy/README.md` |

## Kien truc hien tai

| Lop | Thu muc | Vai tro |
|---|---|---|
| He that | `mininet/` | Topology, traffic, runner, static routes |
| Cau noi | `bridge/` | Collector, sync agent, command agent, Ditto adapter |
| Thing spec | `ditto/` | Policy, topology spec, routing table |
| Twin core | `twin/` | Delay/loss model, util contract, topology tam |
| Measurement song | `measurements/` | Script do Mininet/Ditto that |
| Test song | `test/` | Pytest cho infra/twin dang con dung |
| Evidence cu | `legacy/` | RL Phase 5-14 va artifact da dong |
| Chung nhan | `cert/` | Phase 21: q_hat(z); Phase 22-23: trust gate |

## Ba con so calibration can bao ve

| So | Gia tri | Source hien tai |
|---|---:|---|
| Cliff offered load | `0.9275` | `twin/link_model.py` |
| Overhead factor | `1.0790` | `twin/link_model.py` |
| Critical ceiling fraction | `0.71` | `twin/link_model.py` |

`results/calib/` da duoc khoi phuc tu git history:
commit `7bcce0d^`, truoc khi `chore(results): remove stale experiment artifacts`
xoa nham thu muc nay vao 2026-07-19.

Neu do lai calibration, commit bang:

```bash
git add results/calib/
git commit -m "provenance: add calibration source data"
```

## Scripts Phase 21 trong `cert/`

| Script | Vai tro |
|---|---|
| `cert/build_calib_set.py` | Tao calibration table offered/measured tu evidence Phase 20 |
| `cert/error_vs_age.py` | Do q_hat(z), eta2, monotonicity, error-vs-age |
| `cert/conformal_age.py` | Chon bien the q_hat va kiem coverage/V3/V3c/risk-coverage |
| `cert/usefulness.py` | Ablation adaptive q_hat(z) vs constant threshold + baselines |
| `cert/plot_usefulness.py` | Helper ve Figure 3 tu JSON usefulness |

## Luat ve sinh

1. Ket qua paper ghi vao `results/<phase>/`, ten file co ngay, seed, config.
2. JSON ket qua nen co `provenance`: `git_hash`, `timestamp_utc`, `seed`,
   `config`, `script`, va `git_dirty`.
3. Khong copy them `link_model.py`; `twin/link_model.py` la single source.
4. Khong sua evidence da dong trong `docs/phase-*/`; neu sai, viet file moi.
5. Truoc phase moi, tao tag `phase-NN-start`.
6. `pytest test/` phai xanh truoc commit. Test command live chi chay khi set
   `DT4N_LIVE_COMMAND_TESTS=1`.
