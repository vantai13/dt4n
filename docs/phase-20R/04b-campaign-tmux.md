# Phase 20R.4 -- Tmux Runbook

Muc tieu: chay smoke, continuity, roi full campaign Mininet co resume.

## 0. Preflight

```bash
cd /home/ubuntu/dt4n
export PYTHONPATH="$PWD"
mkdir -p logs results/phase-20R/raw

python3 -m measurements.l6_campaign_fine --stage smoke --plan-only
python3 -m measurements.l6_campaign_fine --stage continuity --plan-only
python3 -m measurements.l6_campaign_fine --stage full --dry-run | head -40

python3 -m pytest test/test_phase20r_campaign_grid.py test/test_phase20r_truth_table.py -q
```

Neu `git status --short` co file code/doc chua commit, dung va commit truoc
khi full campaign. Cac raw files trong `results/phase-20R/raw/` duoc ignore.

## 1. Tao Tmux

```bash
tmux new -s p20r4
```

Ben trong tmux:

```bash
cd /home/ubuntu/dt4n
export PYTHONPATH="$PWD"
set -o pipefail
mkdir -p logs results/phase-20R/raw
sudo -v
sudo -n mn -c
```

Detach:

```text
Ctrl-b  d
```

Attach lai:

```bash
tmux attach -t p20r4
```

Xem log tu terminal khac:

```bash
tail -f logs/20r4_00_smoke.log
```

## 2. Smoke -- 10 Diem

```bash
printf "%s BAT DAU 20R.4 smoke\n" "$(date -Is)" | tee -a results/phase-20R/RUNLOG.md
sudo -n mn -c
sudo -n env PYTHONPATH="$PWD" /usr/bin/python3 -u -m measurements.l6_campaign_fine \
  --stage smoke \
  --state results/phase-20R/smoke_state.json \
  2>&1 | tee -a logs/20r4_00_smoke.log
printf "%s XONG 20R.4 smoke\n" "$(date -Is)" | tee -a results/phase-20R/RUNLOG.md
```

Kiem tra:

```bash
python3 -m measurements.l6_campaign_fine \
  --stage smoke \
  --state results/phase-20R/smoke_state.json \
  --summary
```

Chi di tiep neu `n_fail = 0`, `n_socket_drop_rows = 0`, va `n_foreign_rows = 0`.

## 3. Continuity -- 8 Diem Trung Phase L

```bash
printf "%s BAT DAU 20R.4 continuity\n" "$(date -Is)" | tee -a results/phase-20R/RUNLOG.md
sudo -n mn -c
sudo -n env PYTHONPATH="$PWD" /usr/bin/python3 -u -m measurements.l6_campaign_fine \
  --stage continuity \
  --state results/phase-20R/continuity_state.json \
  2>&1 | tee -a logs/20r4_01_continuity.log
printf "%s XONG 20R.4 continuity\n" "$(date -Is)" | tee -a results/phase-20R/RUNLOG.md
```

Sinh check:

```bash
python3 -m measurements.build_truth_table \
  --skip-truth \
  --skip-sentinel \
  --continuity-state results/phase-20R/continuity_state.json \
  --continuity-out results/phase-20R/continuity_check.json

cat results/phase-20R/continuity_check.json
```

Chi di tiep neu `all_pass = true`. Neu fail, dung full campaign.

## 4. Pre-Full Dirty Check

Sau commit/tag freeze, chay dung 1 diem de dam bao provenance sach:

```bash
sudo -n mn -c
sudo -n env PYTHONPATH="$PWD" /usr/bin/python3 -u -m measurements.l6_campaign_fine \
  --stage smoke \
  --limit 1 \
  --state /tmp/20r4_dirty_check.json \
  2>&1 | tee -a logs/20r4_dirty_check.log

python3 - <<'PY'
import json
r = json.load(open("/tmp/20r4_dirty_check.json"))["rows"][0]
assert r["env"]["git_dirty"] is False, r["env"].get("git_status_relevant")
print("OK git_dirty =", r["env"]["git_dirty"], "commit =", r["git_hash"][:8])
PY
```

## 5. Full Campaign -- 609 Diem

Preflight ngay truoc khi bam chay:

```bash
git log -1 --oneline --decorate
git tag --list phase-20R-campaign-grid
git tag --list phase-20R-campaign-start
python3 -m measurements.l6_campaign_fine --stage full --dry-run | head -40
```

Chay mot mach trong tmux:

```bash
printf "%s BAT DAU 20R.4 full\n" "$(date -Is)" | tee -a results/phase-20R/RUNLOG.md
sudo -n mn -c
sudo -n env PYTHONPATH="$PWD" /usr/bin/python3 -u -m measurements.l6_campaign_fine \
  --stage full \
  --state results/phase-20R/campaign_state.json \
  2>&1 | tee -a logs/20r4_02_full.log
printf "%s XONG 20R.4 full\n" "$(date -Is)" | tee -a results/phase-20R/RUNLOG.md
```

Hoac chay bang `nohup` neu lo mat SSH:

```bash
sudo -n mn -c
nohup sudo -n env PYTHONPATH="$PWD" /usr/bin/python3 -u \
  -m measurements.l6_campaign_fine \
  --stage full \
  --state results/phase-20R/campaign_state.json \
  > logs/20r4_02_full.log 2>&1 &
echo $! > /tmp/20r4_campaign.pid
tail -f logs/20r4_02_full.log
```

Resume neu bi dut:

```bash
tmux attach -t p20r4
cd /home/ubuntu/dt4n
export PYTHONPATH="$PWD"
sudo -n mn -c
sudo -n env PYTHONPATH="$PWD" /usr/bin/python3 -u -m measurements.l6_campaign_fine \
  --stage full \
  --state results/phase-20R/campaign_state.json \
  --resume \
  2>&1 | tee -a logs/20r4_02_full.log
```

Tom tat:

```bash
python3 -m measurements.l6_campaign_fine \
  --stage full \
  --state results/phase-20R/campaign_state.json \
  --summary
```

## 6. Build Artifacts Sau Full

```bash
python3 -m measurements.build_truth_table \
  --phase-l-state results/phase-L/campaign_state.json \
  --phase-20r-state results/phase-20R/campaign_state.json \
  --continuity-state results/phase-20R/continuity_state.json \
  --out results/phase-20R/truth_table.parquet \
  --csv-out results/phase-20R/truth_table.csv \
  --continuity-out results/phase-20R/continuity_check.json \
  --sentinel-out results/phase-20R/sentinel_control.json
```

Commit ket qua sau khi validate:

```bash
git add results/phase-20R/campaign_state.json \
        results/phase-20R/smoke_state.json \
        results/phase-20R/continuity_state.json \
        results/phase-20R/continuity_check.json \
        results/phase-20R/sentinel_control.json \
        results/phase-20R/truth_table.parquet \
        results/phase-20R/truth_table.csv \
        results/phase-20R/RUNLOG.md
git commit -m "Phase 20R: collect measured truth table"
```
