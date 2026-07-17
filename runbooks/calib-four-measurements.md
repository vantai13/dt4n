# Lesson 9.0 - Four Calibration Measurements

This runbook measures the four model claims in order:

- A: one-link delay/loss model
- B: path composition/additivity
- C: routing AoI and observation error through Ditto
- D: TCP-vs-UDP instrument effect

Do not delete earlier CSV files unless you intentionally want a clean run.
Most commands append or write named output files under `results/calib/`.

## 0. Preflight

You are checking tools, not measuring yet.

```bash
cd ~/dt4n
which mn mnexec tc iperf
conda run -n sdn_net ryu-manager --version
python3 -c "import numpy; import mininet; import requests; print('python imports ok')"
sudo mn -c
```

## A. One-Link Model

Question: does one shaped link follow M/M/1, and does that depend on queue
depth or bandwidth?

Short smoke:

```bash
sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache \
  python3 -m measurements.calib_link_sweep \
  --bw 4 --delay 2 --queue 20 --repeats 1 --duration 0.5 --settle 0.2 \
  --out /tmp/dt4n_link_sweep_smoke.csv
```

Real sweep, fair queue-depth test for M/M/1:

```bash
sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache \
  python3 -m measurements.calib_link_sweep \
  --bw 4 --delay 2 --repeats 10 --duration 10 --settle 2 \
  --queue-targets 60,150 \
  --out results/calib/raw_sweep_2node.csv
```

Generalization to the other routing-link bandwidths:

```bash
sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache \
  python3 -m measurements.calib_link_sweep \
  --bw 6 --delay 3 --repeats 10 --duration 10 --settle 2 \
  --queue-targets 60,150 \
  --out results/calib/raw_sweep_2node.csv

sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache \
  python3 -m measurements.calib_link_sweep \
  --bw 8 --delay 1.5 --repeats 10 --duration 10 --settle 2 \
  --queue-targets 60,150 \
  --out results/calib/raw_sweep_2node.csv
```

Fit/report:

```bash
python3 -m rl.routing.link_model_fit \
  --csv results/calib/raw_sweep_2node.csv \
  --out-json results/calib/link_profiles.json \
  --out-report results/calib/fit_report.md
```

## B. Path Composition

Question: does path delay track the sum of per-link delays?

Needs a running Ryu static controller. Terminal 1:

```bash
cd ~/dt4n
python3 -m mininet.topology_routing --write-artifacts --artifacts-only
```

Then start controller in terminal 1:

```bash
cd ~/dt4n
conda activate sdn_net
export DT4N_TOPOLOGY_SPEC=ditto/topology_routing_spec.json
export DT4N_ROUTING_TABLE=ditto/routing_table_routing.json
export DT4N_PORT_MAP=ditto/port_map_routing.json
PYTHONPATH="$PWD" ryu-manager mininet.controller_static --ofp-tcp-listen-port 6653
```

Terminal 2, run a few rates and append:

```bash
cd ~/dt4n
sudo mn -c

sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache \
  DT4N_TOPOLOGY_SPEC=ditto/topology_routing_spec.json \
  DT4N_ROUTING_TABLE=ditto/routing_table_routing.json \
  DT4N_PORT_MAP=ditto/port_map_routing.json \
  python3 -m measurements.calib_topo_validate \
  --rate-mbps 1.5 --duration 5 \
  --out results/calib/raw_topo_validate.csv

sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache \
  DT4N_TOPOLOGY_SPEC=ditto/topology_routing_spec.json \
  DT4N_ROUTING_TABLE=ditto/routing_table_routing.json \
  DT4N_PORT_MAP=ditto/port_map_routing.json \
  python3 -m measurements.calib_topo_validate \
  --rate-mbps 3.2 --duration 5 --append \
  --out results/calib/raw_topo_validate.csv

sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache \
  DT4N_TOPOLOGY_SPEC=ditto/topology_routing_spec.json \
  DT4N_ROUTING_TABLE=ditto/routing_table_routing.json \
  DT4N_PORT_MAP=ditto/port_map_routing.json \
  python3 -m measurements.calib_topo_validate \
  --rate-mbps 4.4 --duration 5 --append \
  --out results/calib/raw_topo_validate.csv
```

Analyze:

```bash
python3 measurements/analyze_topo_validate.py \
  --csv results/calib/raw_topo_validate.csv
```

## C. Routing AoI And Observation Error

Question: how old and how wrong is the routing state seen through Ditto?

Needs Ditto, Ryu, routing Mininet, bootstrap, and sync_agent.

Terminal 1: controller, same as measurement B.

Terminal 2: routing topology plus Ditto sync:

```bash
cd ~/dt4n
sudo mn -c
sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache \
  DT4N_TOPOLOGY_SPEC=ditto/topology_routing_spec.json \
  DT4N_ROUTING_TABLE=ditto/routing_table_routing.json \
  DT4N_PORT_MAP=ditto/port_map_routing.json \
  python3 -m mininet.run_sync_routing \
  --write-artifacts --period 1.0
```

In the Mininet CLI from terminal 2:

```text
mininet> py hload_e.pid
mininet> py hsink_e.pid
```

Terminal 3, replace the PID placeholders:

```bash
cd ~/dt4n
sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache \
  python3 measurements/calib_aoi_routing.py \
  --node-a sC --node-b sE --ifname sC-eth3 --bw 4 \
  --load-pid <PID_HLOAD_E> --sink-pid <PID_HSINK_E> \
  --sink-ip 10.0.0.12 \
  --mode all --duration 60 \
  --out results/calib/raw_aoi_routing.csv
```

Analyze:

```bash
python3 measurements/analyze_aoi.py \
  --csv results/calib/raw_aoi_routing.csv
```

## D. TCP Instrument Effect

Question: how different is TCP from the UDP probe used for link calibration?

This is isolated like A; it does not need Ditto or Ryu.
It uses explicit queues `4,13` to match the queue depths already interpreted in
measurement A.

Short smoke:

```bash
sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache \
  python3 measurements/tcp_probe.py \
  --queues 4 --duration 5 --settle 1 \
  --out /tmp/dt4n_tcp_probe_smoke.csv
```

Real probe:

```bash
sudo mn -c
sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache \
  python3 measurements/tcp_probe.py \
  --out results/calib/raw_tcp_probe.csv
```

Analyze:

```bash
python3 measurements/analyze_tcp_probe.py \
  --csv results/calib/raw_tcp_probe.csv
```

## Completion Checklist

After all four are done, these files should exist:

```text
results/calib/raw_sweep_2node.csv
results/calib/link_profiles.json
results/calib/fit_report.md
results/calib/raw_topo_validate.csv
results/calib/raw_aoi_routing.csv
results/calib/raw_tcp_probe.csv
```
