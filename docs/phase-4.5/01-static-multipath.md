# Phase 4.5.1 - Static Multipath Controller

This step removes STP from the triangle topology. The physical loop stays, but
the controller never floods frames:

- ARP requests go to the controller and receive proxy ARP replies.
- IPv4 packets match `eth_type=0x0800, ipv4_dst=<host IP>`.
- Each switch outputs to one port from the generated next-hop table.
- Link up/down events recompute routes reactively.

## Generate Routes

Run this before starting Ryu if `ditto/topology_spec.json` changes:

```bash
cd ~/dt4n
python3 -m mininet.gen_routes \
  --spec ditto/topology_spec.json \
  --out ditto/routing_table.json
```

Expected key routes:

```text
s1 10.0.0.4 -> s2
s1 10.0.0.5 -> s3
s2 10.0.0.5 -> s3
s3 10.0.0.4 -> s2
```

The last two keep `srv1 <-> srv2` traffic on bottleneck `s2-s3`.

## Run

Terminal 1:

```bash
cd ~/dt4n
ryu-manager mininet.controller_static --ofp-tcp-listen-port 6653
```

Terminal 2:

```bash
cd ~/dt4n
sudo mn -c
sudo python3 -m mininet.topology --convergence-timeout 8
```

`start_net()` writes `ditto/port_map.json` from live Mininet state. The Ryu app
waits for that file before installing IPv4 flows.

## Checks

Inside Mininet CLI:

```bash
pingall
h1 ping -c 3 10.0.0.4
h1 ping -c 3 10.0.0.5
link s1 s3 down
h1 ping -c 3 10.0.0.5
link s1 s3 up
h1 ping -c 3 10.0.0.5
```

From another terminal:

```bash
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
sudo ovs-ofctl -O OpenFlow13 dump-flows s2
sudo ovs-ofctl -O OpenFlow13 dump-flows s3
cat ditto/port_map.json
```

After `link s1 s3 down`, the `10.0.0.5` flow on `s1` should point to the port
toward `s2`, and traffic to `srv2` should still work through `s1-s2-s3`.

## Regression Measurements

Use the static controller in terminal 1, then run:

```bash
cd ~/dt4n
sudo mn -c
sudo python3 -m mininet.run_sync --measure-latency --trials 20 \
  2>&1 | tee docs/phase-4.5/sync_latency_static.txt

sudo mn -c
sudo python3 -m mininet.run_sync --measure-command --trials 20 \
  2>&1 | tee docs/phase-4.5/command_latency_static.txt
```

For a quiet measurement without `srv1 -> srv2` background traffic:

```bash
sudo python3 -m mininet.run_sync --measure-latency --trials 20 --server-bg-rate 0
```

## Local Logic Tests

```bash
python3 -m mininet.gen_routes --spec ditto/topology_spec.json --out /tmp/routes.json
python3 test/test_static_routing.py
python3 test/test_logic.py
python3 test/test_phase2_5.py
```

If `pytest` is installed:

```bash
pytest test/ -v
```
