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
| G3 main | 270 + 9 sentinel | 8.4-9.1 gio |
| G1b step response v2 | 13 | 1.6-1.8 gio |
| tong con lai sau smoke | 337 | 11.4-12.5 gio |

Dung luong raw du kien khoang vai tram MB. Van nen de san it nhat 5 GB.

State mac dinh:

```text
results/phase-T/smoke_state.json
results/phase-T/step_v2_state.json
results/phase-T/control_state.json
results/phase-T/campaign_state.json
results/phase-T/sealed/{pid}.json
```

Log nen ghi:

```text
logs/t5_00_smoke.log
logs/t5_01_step_v2.log
logs/t5_02_controls.log
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
touch results/phase-T/RUNLOG.md results/phase-T/UNBLINDING_LOG.txt
df -h .
test -f results/phase-L/link_model_v2_fit.json
pytest test/test_phase_t_validate.py test/test_phase_t_t5.py -q
pytest -q
```

Neu `test -f ...` khong co output va exit code la 0 thi file model da co.
Neu lenh do fail, dung T.5 va quay lai Phase L.7 fit.

Kiem plan:

```bash
python3 -m measurements.t5_campaign --stage smoke --plan-only
python3 -m measurements.t5_step --plan-only
python3 -m measurements.t5_campaign --stage controls --plan-only
python3 -m measurements.t5_campaign --stage main --plan-only
```

Ky vong:

```text
smoke:    6 diem
step v2: 13 diem, ~1.7 gio
controls:45 diem, ~1.5 gio
main:    279 diem, ~9.1 gio
```

Neu da chay `results/phase-T/step_state.json` truoc Amendment 8, khong dung
file do de fit truc hoanh. Giu raw cu de doi chieu D-T9, nhung step live moi
dung `results/phase-T/step_v2_state.json`.

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
touch results/phase-T/RUNLOG.md results/phase-T/UNBLINDING_LOG.txt
sudo -v
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
printf "%s BAT DAU G0 smoke\n" "$(date -Is)" | tee -a results/phase-T/RUNLOG.md
sudo -n mn -c
sudo -n env PYTHONPATH="$PWD" python3 -u -m measurements.t5_campaign \
  --stage smoke \
  --state results/phase-T/smoke_state.json \
  2>&1 | tee -a logs/t5_00_smoke.log
printf "%s XONG G0 smoke\n" "$(date -Is)" | tee -a results/phase-T/RUNLOG.md
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
printf "%s BAT DAU G2 controls\n" "$(date -Is)" | tee -a results/phase-T/RUNLOG.md
sudo -n mn -c
sudo -n env PYTHONPATH="$PWD" python3 -u -m measurements.t5_campaign \
  --stage controls \
  --state results/phase-T/control_state.json \
  2>&1 | tee -a logs/t5_02_controls.log
printf "%s XONG G2 controls\n" "$(date -Is)" | tee -a results/phase-T/RUNLOG.md
```

Tom tat:

```bash
python3 - <<'PY'
import json
from measurements.t5_campaign import build_controls_plan, campaign_summary
state = json.load(open("results/phase-T/control_state.json"))
print(json.dumps(campaign_summary(state, build_controls_plan()), indent=2, sort_keys=True))
PY
```

Neu doi chung am khong tai tao Phase L theo gate, dung lai. Khong chay main.

## G3 Main

Chay 3 phien lien tiep trong cung tmux. Tong main khoang 8.4-9.1 gio; moi
phien khoang 2.8-3.1 gio.

```bash
printf "%s BAT DAU G3 main\n" "$(date -Is)" | tee -a results/phase-T/RUNLOG.md
for S in 1 2 3; do
  printf "%s BAT DAU main session %s\n" "$(date -Is)" "$S" | tee -a results/phase-T/RUNLOG.md
  sudo -n mn -c
  sudo -n env PYTHONPATH="$PWD" python3 -u -m measurements.t5_campaign \
    --stage main \
    --session "$S" \
    --n-sessions 3 \
    --state results/phase-T/campaign_state.json \
    2>&1 | tee -a "logs/t5_03_main_s${S}.log"
  printf "%s XONG main session %s\n" "$(date -Is)" "$S" | tee -a results/phase-T/RUNLOG.md
done
printf "%s XONG G3 main\n" "$(date -Is)" | tee -a results/phase-T/RUNLOG.md
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
printf "%s BAT DAU G1b step_v2\n" "$(date -Is)" | tee -a results/phase-T/RUNLOG.md
sudo -n mn -c
sudo -n env PYTHONPATH="$PWD" python3 -u -m measurements.t5_step \
  --state results/phase-T/step_v2_state.json \
  2>&1 | tee -a logs/t5_01_step_v2.log
printf "%s XONG G1b step_v2\n" "$(date -Is)" | tee -a results/phase-T/RUNLOG.md
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
