# Phase T / Lesson T.5 -- Campaign va tmux

Muc tieu T.5 la chay do song theo thu tu da preregister, co checkpoint/resume,
co sentinel, va giu phan tich chinh o trang thai niem phong cho den T.6.

Script:

```text
measurements/t5_step.py
measurements/t5_campaign.py
```

## Luoi Do Va Thoi Gian

| giai doan | diem | uoc luong |
|---|---:|---:|
| G0 smoke | 6 | 12-15 phut |
| G2 doi chung am | 45 | 1.4-1.6 gio |
| G2b C' cung-seed | 45 | ~1.0 gio wall, 52.5 phut traffic |
| G3 main | 270 + 9 sentinel | 8.4-9.1 gio |
| G1b step response v2 | 13 | 1.6-1.8 gio |
| tong con lai sau smoke | 382 | 12.4-13.5 gio |

Dung luong raw du kien khoang vai tram MB. Van nen de san it nhat 5 GB.

State mac dinh:

```text
results/phase-T/smoke_state.json
results/phase-T/step_v2_state.json
results/phase-T/control_state.json
results/phase-T/control_sameseed_state.json
results/phase-T/campaign_state.json
results/phase-T/sealed/{pid}.json
```

Log nen ghi:

```text
logs/t5_00_smoke.log
logs/t5_01_step_v2.log
logs/t5_02_controls.log
logs/t5_02_controls_A11_audit.log
logs/t5_02b_controls_sameseed_A11.log
logs/t5_03_main_s1.log
logs/t5_03_main_s2.log
logs/t5_03_main_s3.log
results/phase-T/RUNLOG.md
results/phase-T/UNBLINDING_LOG.txt
```

Sau Amendment 7, state public khong chua response metric (`q_mean_ms`,
percentiles, `probe_mean_ms`, `delta_pasta_ms`, SE). Cac truong nay nam trong
`results/phase-T/sealed/` va khong mo cho den T.6.

## Kiem Tra Truoc Khi Chay

Chay ngoai tmux cung duoc:

```bash
cd /home/ubuntu/dt4n
export PYTHONPATH="$PWD"
mkdir -p logs results/phase-T/raw
sudo -v
sudo -n touch results/phase-T/RUNLOG.md results/phase-T/UNBLINDING_LOG.txt
df -h .
test -f results/phase-L/link_model_v2_fit.json
pytest test/test_phase_t_gate_specs.py test/test_phase_t_validate.py test/test_phase_t_t5.py -q
pytest -q
```

Neu `test -f ...` khong co output va exit code la 0 thi file model da co.
Neu lenh do fail, dung T.5 va quay lai Phase L.7 fit.

Kiem plan:

```bash
python3 -m measurements.t5_campaign --stage smoke --plan-only
python3 -m measurements.t5_step --plan-only
python3 -m measurements.t5_campaign --stage controls --plan-only
python3 -m measurements.t5_campaign --stage controls-samesed --state results/phase-T/control_sameseed_state.json --plan-only
python3 -m measurements.t5_campaign --stage main --plan-only
```

Ky vong:

```text
smoke:    6 diem
step v2: 13 diem, ~1.7 gio
controls:45 diem, ~1.5 gio
controls-samesed:45 diem, ~1.0 gio wall
main:    279 diem, ~9.1 gio
```

Neu da chay `results/phase-T/step_state.json` truoc Amendment 8, khong dung
file do de fit truc hoanh. Giu raw cu de doi chieu D-T9, nhung step live moi
dung `results/phase-T/step_v2_state.json`.

Neu G2 da dung truoc Amendment 9 tai `V-T4a_ca_operational`, co the resume
cung `results/phase-T/control_state.json`. Khi idx do pass, runner se xoa
`failed_rows` cu cua idx.

Sau Amendment 11, G2 phai duoc audit bang cung interpreter voi live runner:

```bash
sudo -n env PYTHONPATH="$PWD" python3 -m measurements.t5_controls_audit \
  --state results/phase-T/control_state.json \
  --sealed-dir results/phase-T/sealed
```

V-T5b 105s chi la aggregate z diagnostic. Neu aggregate `V-T5b_q_phase_l`
fail, dung. Neu pass nhung `h2@0.70` con dang nghi, chay khoi C' cung-seed
truoc G3.
Khong dung `python3` conda/user-shell de ket luan V-T5a bit-exact digest; live
runner chay bang `sudo python3`.

Neu da tung chay smoke truoc Amendment 7, archive state cu truoc khi chay lai:

```bash
stamp=$(date +%Y%m%d_%H%M%S)
test ! -f results/phase-T/smoke_state.json || \
  mv results/phase-T/smoke_state.json results/phase-T/smoke_state.preA7.$stamp.json
test ! -d results/phase-T/sealed || \
  mv results/phase-T/sealed results/phase-T/sealed.preA7.$stamp
mkdir -p results/phase-T/sealed
```

## Tao Tmux

```bash
tmux new -s t5
```

Ben trong tmux:

```bash
cd /home/ubuntu/dt4n
export PYTHONPATH="$PWD"
set -o pipefail
mkdir -p logs results/phase-T/raw
sudo -v
sudo -n touch results/phase-T/RUNLOG.md results/phase-T/UNBLINDING_LOG.txt
sudo -n mn -c
```

Detach ma tien trinh van chay:

```text
Ctrl-b  d
```

Quay lai:

```bash
tmux attach -t t5
```

Xem log tu shell khac:

```bash
tail -f logs/t5_00_smoke.log
```

## G0 Smoke

```bash
printf "%s BAT DAU G0 smoke\n" "$(date -Is)" | sudo -n tee -a results/phase-T/RUNLOG.md >/dev/null
sudo -n mn -c
sudo -n env PYTHONPATH="$PWD" python3 -u -m measurements.t5_campaign \
  --stage smoke \
  --state results/phase-T/smoke_state.json \
  2>&1 | tee -a logs/t5_00_smoke.log
printf "%s XONG G0 smoke\n" "$(date -Is)" | sudo -n tee -a results/phase-T/RUNLOG.md >/dev/null
```

Sau khi xong, xem tom tat:

```bash
python3 - <<'PY'
import json
from measurements.t5_campaign import build_smoke_plan, campaign_summary
state = json.load(open("results/phase-T/smoke_state.json"))
print(json.dumps(campaign_summary(state, build_smoke_plan()), indent=2, sort_keys=True))
PY
```

Ky vong sau Amendment 7: 6/6 PASS, khong retry `V-T6b_rho_bias`. Neu runner
dung vi deterministic gate fail, khong chay tiep.

## G1 Step Response v1 Bi Loai

Neu da chay G1 v1 va thay S-1 fail, dung dung ket qua do cho fit truc hoanh.
Sau Amendment 8, G2/G3 khong bi chan boi step response vi campaign runner
khong dung `ensemble_average`. Step v2 se chay lai sau G3, truoc khi mo niem
phong T.6.

## G2 Doi Chung Am

```bash
printf "%s BAT DAU G2 controls\n" "$(date -Is)" | sudo -n tee -a results/phase-T/RUNLOG.md >/dev/null
sudo -n mn -c
sudo -n env PYTHONPATH="$PWD" python3 -u -m measurements.t5_campaign \
  --stage controls \
  --state results/phase-T/control_state.json \
  2>&1 | tee -a logs/t5_02_controls.log
printf "%s XONG G2 controls\n" "$(date -Is)" | sudo -n tee -a results/phase-T/RUNLOG.md >/dev/null
```

Tom tat:

```bash
sudo -n env PYTHONPATH="$PWD" python3 -m measurements.t5_controls_audit \
  --state results/phase-T/control_state.json \
  --sealed-dir results/phase-T/sealed \
  --update-state \
  2>&1 | tee -a logs/t5_02_controls_A11_audit.log
```

Trang thai 2026-08-01 sau Amendment 11: G2 105s co row gates sach va
`V-T5b_q_phase_l` aggregate pass; `h2@0.70` co sd_z lon nen can C' cung-seed
truoc G3.

Neu can lam dong nhat provenance cho idx 0 da chay truoc Amendment 9, rerun
mot diem duy nhat bang `--force-idx`. Runner se thay row cu, khong tao duplicate:

```bash
sudo -n mn -c
sudo -n env PYTHONPATH="$PWD" python3 -u -m measurements.t5_campaign \
  --stage controls \
  --state results/phase-T/control_state.json \
  --force-idx 0 \
  2>&1 | tee -a logs/t5_02_controls_idx0_rerun_A10.log
sudo -n env PYTHONPATH="$PWD" python3 -m measurements.t5_controls_audit \
  --state results/phase-T/control_state.json \
  --sealed-dir results/phase-T/sealed \
  --update-state
```

## G2b C' Cung-Seed

Chay truoc G3. Muc tieu la so Phase T voi Phase L cung seed, cung
duration/warm-up `70/10`, nen lich co the khop bit-exact va do nhay cao hon
phep so cross-seed.

```bash
printf "%s BAT DAU G2b controls-samesed A11\n" "$(date -Is)" | sudo -n tee -a results/phase-T/RUNLOG.md >/dev/null
sudo -n mn -c
sudo -n env PYTHONPATH="$PWD" python3 -u -m measurements.t5_campaign \
  --stage controls-samesed \
  --state results/phase-T/control_sameseed_state.json \
  2>&1 | tee -a logs/t5_02b_controls_sameseed_A11.log
printf "%s XONG G2b controls-samesed A11\n" "$(date -Is)" | sudo -n tee -a results/phase-T/RUNLOG.md >/dev/null
```

Audit C':

```bash
sudo -n env PYTHONPATH="$PWD" python3 -m measurements.t5_controls_audit \
  --stage controls-samesed \
  --state results/phase-T/control_sameseed_state.json \
  --sealed-dir results/phase-T/sealed \
  --update-state \
  2>&1 | tee -a logs/t5_02b_controls_sameseed_A11_audit.log
```

Chi vao G3 neu:

```text
V-T5a_phase_l_digest fail = 0
V-T5b_same_seed mean_gate=OK va sd_gate=OK
```

## G3 Main

Chay 3 phien lien tiep trong cung tmux. Tong main khoang 8.4-9.1 gio; moi
phien khoang 2.8-3.1 gio.

```bash
printf "%s BAT DAU G3 main\n" "$(date -Is)" | sudo -n tee -a results/phase-T/RUNLOG.md >/dev/null
for S in 1 2 3; do
  printf "%s BAT DAU main session %s\n" "$(date -Is)" "$S" | sudo -n tee -a results/phase-T/RUNLOG.md >/dev/null
  sudo -n mn -c
  sudo -n env PYTHONPATH="$PWD" python3 -u -m measurements.t5_campaign \
    --stage main \
    --session "$S" \
    --n-sessions 3 \
    --state results/phase-T/campaign_state.json \
    2>&1 | tee -a "logs/t5_03_main_s${S}.log"
  printf "%s XONG main session %s\n" "$(date -Is)" "$S" | sudo -n tee -a results/phase-T/RUNLOG.md >/dev/null
done
printf "%s XONG G3 main\n" "$(date -Is)" | sudo -n tee -a results/phase-T/RUNLOG.md >/dev/null
```

Tom tat:

```bash
python3 - <<'PY'
import json
from measurements.t5_campaign import build_main_plan, campaign_summary
state = json.load(open("results/phase-T/campaign_state.json"))
print(json.dumps(campaign_summary(state, build_main_plan()), indent=2, sort_keys=True))
PY
```

Gate tap hop duoc phep xem vi chi dung `rho_bias_z`:

```bash
python3 - <<'PY'
import json
from measurements.t4_validate import gate_rho_bias_aggregate
state = json.load(open("results/phase-T/campaign_state.json"))
print(json.dumps(gate_rho_bias_aggregate(state.get("rows", [])), indent=2, sort_keys=True))
PY
```

## G1b Step Response v2

Chay sau G3, truoc khi mo niem phong T.6:

```bash
printf "%s BAT DAU G1b step_v2\n" "$(date -Is)" | sudo -n tee -a results/phase-T/RUNLOG.md >/dev/null
sudo -n mn -c
sudo -n env PYTHONPATH="$PWD" python3 -u -m measurements.t5_step \
  --state results/phase-T/step_v2_state.json \
  2>&1 | tee -a logs/t5_01_step_v2.log
printf "%s XONG G1b step_v2\n" "$(date -Is)" | sudo -n tee -a results/phase-T/RUNLOG.md >/dev/null
```

Tom tat nhanh:

```bash
python3 - <<'PY'
import json
state = json.load(open("results/phase-T/step_v2_state.json"))
rows = state.get("rows", [])
print("rows", len(rows))
for r in rows:
    print(r["idx"], r["mode"], r["rho_a"], "->", r["rho_b"],
          "T_mean_s=", r.get("T_mean_s"),
          "amp_z=", r.get("amp_z"),
          "amp_ok=", r.get("amp_significant"),
          "drops=", r.get("socket_drops"),
          "foreign=", r.get("n_foreign"))
PY
```

## Pause Va Resume

Neu can dung, bam `Ctrl-C`. Diem dang chay co the mat, nhung cac diem da xong
da nam trong state. Chay lai dung lenh cu se bo qua `idx` da xong.

Kiem tien do state:

```bash
python3 - <<'PY'
import json
for path in [
    "results/phase-T/smoke_state.json",
    "results/phase-T/step_v2_state.json",
    "results/phase-T/control_state.json",
    "results/phase-T/campaign_state.json",
]:
    try:
        s = json.load(open(path))
    except FileNotFoundError:
        print(path, "missing")
        continue
    print(path, "done", len(set(s.get("done_idx", []))), "rows", len(s.get("rows", [])))
PY
```

Khong xoa state that. Neu can chay lai tu dau, doi ten file state:

```bash
mv results/phase-T/campaign_state.json \
  results/phase-T/campaign_state.old.$(date +%Y%m%d_%H%M%S).json
```

## Niem Phong Va Unblind

Trong T.5, khong tinh cac metric chinh sau khi main dang chay:

```text
err_qs
err_jensen
d_sampling
err_total
err_mol
gain_mol
```

Sau khi G3 va G1b xong, ghi checksum va ly do mo niem phong:

```bash
sha256sum results/phase-T/*_state.json logs/t5_*.log results/phase-T/sealed/*.json \
  | tee -a results/phase-T/UNBLINDING_LOG.txt
printf "%s READY_TO_UNBLIND after G0-G3 and G1b complete\n" "$(date -Is)" \
  | tee -a results/phase-T/UNBLINDING_LOG.txt
```

Repo hien tai chua them `measurements/t6_analyze.py`; dung tai day va sang
lesson T.6 de mo niem phong.
