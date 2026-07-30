# Phase L / Lesson L.6 -- Campaign va tmux

Muc tieu L.6 la chay chien dich dai co checkpoint/resume, diem canh, va gate
tung diem. Script:

```
measurements/l6_campaign.py
```

## Luoi do

| khoi | diem |
|---|---:|
| A: 3 mode x 12 rho x 3 cau hinh x 5 seed | 540 |
| B: onoff x 12 rho x (6,13) x 5 seed | 60 |
| C: them seed 16..20 cho rho 0.98/1.00/1.02 tai (6,13) | 45 |
| D: probe_pps=0 controls tai 4 rho x 3 mode x 5 seed | 60 |
| E: sentinel moi 30 diem thuong | 23 |
| tong | 728 |

State mac dinh:

```
results/phase-L/campaign_state.json
```

## Kiem tra truoc khi chay

```bash
cd /home/ubuntu/dt4n
df -h .
python3 -m measurements.l6_campaign --plan-only --max-points 12
pytest test/test_phase_l_l6_campaign.py -q
```

## Tmux: cach treo may

Tao session:

```bash
tmux new -s l6
```

Ben trong tmux:

```bash
cd /home/ubuntu/dt4n
sudo -n mn -c
python3 -m measurements.l6_campaign --plan-only --max-points 5
```

Chay smoke 20 diem de kiem checkpoint:

```bash
sudo -n env PYTHONPATH="$PWD" python3 -u -m measurements.l6_campaign \
  --state results/phase-L/campaign_smoke_state.json --max-points 20 \
  2>&1 | tee -a /tmp/l6_smoke.out
```

De tach khoi tmux ma tien trinh van chay:

```text
Ctrl-b  d
```

Quay lai:

```bash
tmux attach -t l6
```

Xem log khi da detach:

```bash
tail -f /tmp/l6_smoke.out
```

## Test resume

Trong smoke, ban co the bam `Ctrl-C` giua chung. Sau do chay lai lenh y het:

```bash
sudo -n env PYTHONPATH="$PWD" python3 -u -m measurements.l6_campaign \
  --state results/phase-L/campaign_smoke_state.json --max-points 20 \
  2>&1 | tee -a /tmp/l6_smoke_resume.out
```

Script se doc file state ban truyen qua `--state` va bo qua cac `idx` da xong.

Smoke dung state rieng `campaign_smoke_state.json`, nen campaign that van bat dau
tu `campaign_state.json` sach. Neu muon dung smoke lam du lieu that, doi
`--state` ve `results/phase-L/campaign_state.json`.

## Chay bon phien that

Van trong tmux:

```bash
cd /home/ubuntu/dt4n
for S in 1 2 3 4; do
  sudo -n mn -c
  sudo -n env PYTHONPATH="$PWD" python3 -u -m measurements.l6_campaign --session "$S" \
    2>&1 | tee -a "/tmp/l6_session${S}.out"
done
```

Muon detach:

```text
Ctrl-b  d
```

Muon xem tien do tu shell ngoai tmux:

```bash
tail -f /tmp/l6_session4.out
```

Muon quay lai cua so dang chay:

```bash
tmux attach -t l6
```

## Dung/pause an toan

Neu can dung, bam `Ctrl-C`. Diem dang chay co the mat, nhung moi diem da hoan
tat truoc do da checkpoint. Chay lai cung lenh se tiep tuc.

Khong xoa `campaign_state.json`. Neu can chay lai tu dau, doi ten no:

```bash
mv results/phase-L/campaign_state.json results/phase-L/campaign_state.old.$(date +%Y%m%d_%H%M%S).json
```

## Kiem ket qua

```bash
python3 - <<'PY'
import json
from measurements.l6_campaign import build_plan, campaign_summary
state = json.load(open("results/phase-L/campaign_state.json"))
summary = campaign_summary(state, build_plan())
print(json.dumps(summary, indent=2, sort_keys=True))
PY
```

Sau khi xong:

```bash
python3 tools/raw_manifest.py results/phase-L/raw
du -sh results/phase-L/raw
```

Gates L.6:

| gate | dieu kien |
|---|---|
| G1 | coverage >= 98%, fail sau rerun <= 15 |
| G2 | sentinel 0 diem ngoai 3-sigma va khong co trend |
| G3 | q(rho) khong giam trong tung mode/config |
| G4 | cbr < poisson < h2 voi rho >= 0.7 |
| G5 | cung rho thi q scale gan 1/bw sau khi tru san |
| G6 | socket_drops/n_foreign bang 0 va digest khong bi trung bat thuong |

## Ket Qua Da Chay

Artifact:

```text
results/phase-L/campaign_state.json
```

Ket qua:

| muc | gia tri |
|---|---:|
| diem hoan tat | 728/728 |
| gate fail sau rerun | 0 |
| socket_drops | 0 moi diem |
| n_foreign | 0 moi diem |
| max `abs(rate_ratio - 1)` | 8.15e-05 |
| sentinel | 23 diem |

Sentinel `h2, rho=0.90, bw=6, q=13, seed=999`:

| tap | mean ms | sd ms | CV |
|---|---:|---:|---:|
| tat ca 23 diem | 10.8749 | 0.0122 | 0.112% |
| bo diem dau | 10.8733 | 0.0096 | 0.088% |

Diem canh dau tien nam ngoai 3-sigma so voi 22 diem sau, nen duoc ghi la hieu
ung khoi dong may. Ket luan va phan ra phuong sai nam trong
`docs/phase-L/00h-amendment-7.md`. Fit model tu campaign nam trong
`docs/phase-L/07-fit.md`.
