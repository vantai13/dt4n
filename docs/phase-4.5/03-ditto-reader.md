# Phase 4.5.3 - Ditto Reader

This step adds the Python read path for future RL agents:

- `bridge.ditto_reader.fetch_snapshot(session, thing_ids, cache=None)`
- `bridge.ditto_reader.compute_aoi(things, t_read)`
- `bridge.ditto_reader.SnapshotCache`
- `measurements/bench_reader.py`

## Design Choice

The reader intentionally does not use an SSE/WebSocket cache.

An SSE cache would make `fetch_ms` close to zero, but it would also add a new
uncontrolled source of staleness: event buffering, reconnect gaps, dropped
events, and Python thread backpressure. D5 is the staleness axis of the research
plan. Optimizing the measurement path in a way that touches the measured
quantity would create a confounder, not a clean optimization.

Default reader mode is therefore direct `GET /things/{id}` per Thing. The
`/search/things` mode exists only for benchmarking until its `tSource` skew is
measured.

## Semantics

`t_read` is recorded when the response is received. AoI is therefore a
conservative upper bound with error no larger than one request RTT.

`compute_aoi(things, t_read)` is pure:

- it does not call `time.time()`
- missing `tSource` is omitted, not treated as zero
- negative AoI is returned and logged, not clipped

`SnapshotCache` forward-fills on transient read failures:

- partial failure: keep old values for missing Things and set `data_fresh = 0.0`
- three consecutive full failures: set `aborted = True`
- never return NaN

The future env must discard aborted episodes before adding transitions to a
replay buffer.

## Local Checks

```bash
cd ~/dt4n
python3 test/test_ditto_reader.py
python3 -m py_compile bridge/ditto_reader.py measurements/bench_reader.py
```

If `pytest` is installed:

```bash
pytest test/test_ditto_reader.py -q
```

## Runtime Benchmark

Start Ryu static and `run_sync` first:

```bash
cd ~/dt4n
PYTHONPATH=$PWD ryu-manager mininet.controller_static --ofp-tcp-listen-port 6653
```

In another terminal:

```bash
cd ~/dt4n
sudo mn -c
sudo PYTHONPATH=$PWD /usr/bin/python3 -m mininet.run_sync --period 1.0
```

Then benchmark the reader:

```bash
cd ~/dt4n
/usr/bin/python3 measurements/bench_reader.py --samples 100 --skew-samples 30
```

Record:

- A direct GET p50/p95/max `fetch_ms`
- B search p50/p95/max `fetch_ms`
- `tSource` skew `B - A`

If search has median skew below `-0.100s`, prefer direct GET even if search is
faster. That means the search index is returning older data than the Thing
store, which would inflate AoI.

## Expected Thing Count

For the current topology, the agent reader expects 17 Things:

- 5 hosts
- 3 switches
- 8 physical links
- 1 directed path probe: `org.dt4n:path-h1-srv1`

The controller inbox Thing is intentionally omitted because it is a command
sink, not an observation source.
