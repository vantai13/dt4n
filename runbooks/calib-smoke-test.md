# Lesson 9.0 Calibration Smoke Test

Muc tieu cua smoke test nay: tra loi mot cau duy nhat truoc khi chay sweep dai:
`tc -s qdisc` co doc duoc backlog that khong, va backlog co tang khi bom tai
khong?

Neu cau tra loi la "khong", dung lai. Chay sweep 7 gio luc do chi tao du lieu
rac.

## 1. Kiem moi truong

Ban dang kiem tra may co du cong cu Mininet va iperf v2 de tao traffic that.

```bash
cd ~/dt4n
sudo mn --version
which mnexec tc iperf
sudo mn -c
```

Ket qua tren may nay:

- Mininet: `2.3.0`
- Co `mnexec`, `tc`, `iperf`
- `sudo mn -c` chay duoc

## 2. Nhin qdisc bang mat

Ban dang dung mot link co shaping de xem kernel tao may tang qdisc. Dung tin
regex truoc khi nhin output that.

```bash
sudo -E env PYTHONPATH="$PWD" python3 - <<'PY'
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.node import OVSBridge
import subprocess

class T(Topo):
    def build(self):
        self.addHost('h1', ip='10.0.0.1/8')
        self.addHost('h2', ip='10.0.0.2/8')
        self.addSwitch('s1')
        self.addSwitch('s2')
        self.addLink('h1', 's1', bw=1000)
        self.addLink('h2', 's2', bw=1000)
        self.addLink('s1', 's2', bw=4, delay='2ms',
                     max_queue_size=20, use_htb=True)

net = Mininet(topo=T(), link=TCLink, switch=OVSBridge, controller=None)
try:
    net.start()
    s1 = net.get('s1')
    intf = None
    for i in s1.intfList():
        if i.link:
            other = i.link.intf2 if i.link.intf1 == i else i.link.intf1
            if other.node.name == 's2':
                intf = i.name
    print('INTERFACE:', intf)
    print(subprocess.run(['tc', '-s', 'qdisc', 'show', 'dev', intf],
                         capture_output=True, text=True).stdout)
finally:
    net.stop()
PY
```

Pass tren may nay:

- Co 2 block qdisc: `htb` va `netem`
- Luc rong backlog la `0b`
- Interface do duoc la `s1-eth2`

## 3. Kiem backlog co tang khi bom tai

Ban dang tao UDP offered load tu 0.5M den 5.2M tren link 4Mbps. Neu backlog
khong tang gan saturation, phep do queueing delay khong co nen.

Luu y: dung `pkill -x iperf`, khong dung `pkill -f iperf` trong inline script.
`pkill -f` co the kill nham tien trinh Python cha vi source text co chu iperf.

```bash
sudo -E env PYTHONPATH="$PWD" python3 -u - <<'PY'
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.node import OVSBridge
import subprocess, time, re

class T(Topo):
    def build(self):
        self.addHost('h1', ip='10.0.0.1/8')
        self.addHost('h2', ip='10.0.0.2/8')
        self.addSwitch('s1')
        self.addSwitch('s2')
        self.addLink('h1', 's1', bw=1000)
        self.addLink('h2', 's2', bw=1000)
        self.addLink('s1', 's2', bw=4, delay='2ms',
                     max_queue_size=20, use_htb=True)

def sh(pid, cmd):
    return subprocess.run(['mnexec', '-a', str(pid), 'sh', '-lc', cmd],
                          capture_output=True, text=True).stdout

net = Mininet(topo=T(), link=TCLink, switch=OVSBridge, controller=None)
try:
    net.start()
    h1, h2, s1 = net.get('h1'), net.get('h2'), net.get('s1')
    intf = [i.name for i in s1.intfList()
            if i.link and (i.link.intf2 if i.link.intf1 == i
                           else i.link.intf1).node.name == 's2'][0]

    net.pingAll()
    sh(h2.pid, 'iperf -s -u -p 5001 >/tmp/dt4n_smoke_s.log 2>&1 &')
    time.sleep(1)

    print('INTERFACE:', intf)
    print('%-12s %-22s %s' % ('offered', 'backlog(raw)', 'tc line'))
    print('-' * 90)
    for off in [0.5, 2.0, 3.8, 5.2]:
        sh(h1.pid, 'pkill -x iperf 2>/dev/null')
        time.sleep(0.3)
        sh(h1.pid, 'iperf -c 10.0.0.2 -u -b %gM -p 5001 -t 12 -l 1470 '
                   '>/tmp/dt4n_smoke_c.log 2>&1 &' % off)
        time.sleep(3)
        out = subprocess.run(['tc', '-s', 'qdisc', 'show', 'dev', intf],
                             capture_output=True, text=True).stdout
        bl = re.findall(r'backlog\s+(\S+)', out)
        lines = ' | '.join(l.strip() for l in out.splitlines()
                           if 'backlog' in l)
        print('%-12s %-22s %s' % ('%gM' % off, str(bl), lines))
finally:
    sh(h1.pid, 'pkill -x iperf 2>/dev/null')
    sh(h2.pid, 'pkill -x iperf 2>/dev/null')
    net.stop()
PY
```

Pass tren may nay:

```text
0.5M  -> backlog 0b
2M    -> backlog 0b
3.8M  -> backlog 30240b 20p
5.2M  -> backlog 30240b 20p
```

Ket luan: backlog doc duoc va tang/dai dien saturation dung nhu ky vong.

## 4. Chay smoke cua script calibration

Ban dang kiem tra script chinh co ghi CSV dung schema khong, truoc khi chay
repeats lon.

```bash
sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache \
  python3 -m measurements.calib_link_sweep \
  --bw 4 --delay 2 --queue 20 --repeats 1 --duration 0.5 --settle 0.2 \
  --out /tmp/dt4n_calib_smoke.csv

head -3 /tmp/dt4n_calib_smoke.csv
tail -3 /tmp/dt4n_calib_smoke.csv
sudo mn -c
```

Pass tren may nay:

- Script ghi 14 dong.
- `qdisc_kind=htb`.
- `qdisc_layers` co ca `htb` va `netem`.
- Qua 4Mbps thi `loss_rate` bat dau tang.

## 5. Neu smoke pass thi chay sweep that

Ban dang thu thap raw data de fit link model. Day la du lieu, chua phai ket
luan.

```bash
sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache \
  python3 -m measurements.calib_link_sweep \
  --bw 4 --delay 2 --repeats 10 --duration 10 --settle 2 \
  --out results/calib/raw_sweep_2node.csv
```

Lap lai cho cac cau hinh:

```bash
sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache \
  python3 -m measurements.calib_link_sweep --bw 6 --delay 3 \
  --repeats 10 --duration 10 --settle 2 \
  --out results/calib/raw_sweep_2node.csv

sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache \
  python3 -m measurements.calib_link_sweep --bw 8 --delay 1.5 \
  --repeats 10 --duration 10 --settle 2 \
  --out results/calib/raw_sweep_2node.csv
```

Mac dinh moi lenh se quet queue targets `5,15,40` ms.

## 6. Fit sau khi co raw CSV

Ban dang de du lieu phan xu M/M/1, M/D/1, va free-form.

```bash
python3 -m rl.routing.link_model_fit \
  --csv results/calib/raw_sweep_2node.csv \
  --out-json results/calib/link_profiles.json \
  --out-report results/calib/fit_report.md
```

Kiem:

```bash
sed -n '1,120p' results/calib/fit_report.md
python3 -m json.tool results/calib/link_profiles.json | sed -n '1,80p'
```
