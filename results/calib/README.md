# Lesson 9.0 Calibration Results

This directory is the handoff between real Mininet measurements and the routing
simulator.

Generated files:

* `raw_sweep_2node.csv` comes from `sudo -E env PYTHONPATH="$PWD" python3 -m measurements.calib_link_sweep --bw 4 --delay 2`.
  By default this sweeps queue targets `5,15,40` ms and derives `max_queue_size`
  per link from the selected bandwidth.
* `raw_topo_validate.csv` comes from `sudo python3 -m measurements.calib_topo_validate`.
* `link_profiles.json` and `fit_report.md` come from `python3 -m rl.routing.link_model_fit`.

Keep raw CSV files immutable after collection. If a sweep was wrong, write a new
CSV or append a new run with clear timestamps instead of editing old rows.

For the 8-node routing topology, generate artifacts with:

```bash
python3 - <<'PY'
from mininet.topology_routing import write_routing_artifacts
write_routing_artifacts()
PY
```

Run the controller against those artifacts:

```bash
DT4N_TOPOLOGY_SPEC=ditto/topology_routing_spec.json \
DT4N_ROUTING_TABLE=ditto/routing_table_routing.json \
DT4N_PORT_MAP=ditto/port_map_routing.json \
ryu-manager mininet.controller_static --ofp-tcp-listen-port 6653
```
