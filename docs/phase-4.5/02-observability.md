# Phase 4.5.2 - Observability

This step adds two observability primitives without breaking delta sync:

- `features.meta.properties.tSource`: source timestamp, float epoch seconds
- `features.traffic.properties.rxRate/txRate` on physical link Things
- directed path Thing `org.dt4n:path-h1-srv1`

## tSource

`tSource` is stamped where data is born, not where it is pushed to Ditto.

- Host, switch, and physical link Things use the collector cycle timestamp.
- Path Things use the midpoint of the ping measurement window.
- Path timestamp has a systematic uncertainty of roughly half the ping duration.

`meta.tSource` is deliberately ignored as a delta trigger. It only rides along
with real feature changes. This preserves delta sync: a quiet Thing remains
quiet until it changes or until periodic reconciliation sends a full patch.

That behavior is intentional. In delta sync, silence means "no new information
was sent", not "the old value is freshly confirmed". The AoI of stable Things
therefore grows until the next reconciliation. `reconcile_every * period` is the
practical AoI cap.

## Link Traffic

For a canonical link `link-A-B`, where `A < B` alphabetically:

- `rxRate` is RX bytes/sec on A's interface
- `txRate` is TX bytes/sec on A's interface
- utilization is `max(rxRate, txRate) * 8 / 1e6 / bwMbps`

Use `max`, not average or sum, because Mininet bandwidth is per direction. A
single saturated direction is enough for that direction to be congested.

If reading an interface counter fails, the collector omits `traffic` instead of
inventing zero. Zero is a meaningful value. Silence lets `tSource` age, which is
the honest signal that the twin has stale knowledge.

## Path Thing

`path-h1-srv1` is a directed path measurement, not a physical link. It must not
be sorted like link IDs:

```text
org.dt4n:path-h1-srv1 != org.dt4n:path-srv1-h1
```

The dashboard translates only `attributes.type === "link"` into edges, so a
path Thing should not create a fake visual edge.

## Local Checks

```bash
cd ~/dt4n
python3 test/test_logic.py
python3 test/test_phase2_5.py
python3 -m py_compile bridge/collector.py bridge/adapter.py bridge/differ.py \
  bridge/ditto_common.py bridge/bootstrap.py bridge/health.py \
  measurements/measure_aoi.py
```

If `pytest` is installed:

```bash
pytest test/ -v
```

## Runtime Checks

Terminal 1:

```bash
cd ~/dt4n
PYTHONPATH=$PWD ryu-manager mininet.controller_static --ofp-tcp-listen-port 6653
```

Terminal 2:

```bash
cd ~/dt4n
sudo mn -c
sudo PYTHONPATH=$PWD /usr/bin/python3 -m mininet.run_sync --period 1.0
```

Check link traffic and source time:

```bash
curl -u ditto:ditto \
  http://localhost:8080/api/2/things/org.dt4n:link-s2-s3 | jq '.features'
```

Expected:

- `.traffic.properties.rxRate` or `.traffic.properties.txRate` is present
- `.meta.properties.tSource` is a recent float epoch timestamp
- with the 4.5.1 server background traffic, `s2-s3` utilization is non-zero

Check path:

```bash
curl -u ditto:ditto \
  http://localhost:8080/api/2/things/org.dt4n:path-h1-srv1 | jq
```

Expected:

- `attributes.type == "path"`
- `features.quality.properties.latency_ms` appears after a ping probe cycle
- `features.meta.properties.tSource` differs from host/link timestamps in the
  same collector cycle because ping is measured after the fast snapshot section

Measure AoI:

```bash
/usr/bin/python3 measurements/measure_aoi.py --thing org.dt4n:link-s2-s3 --samples 50
/usr/bin/python3 measurements/measure_aoi.py --thing org.dt4n:path-h1-srv1 --samples 50
```

For actively changing Things, AoI should look like a sawtooth. With
`period=1.0`, mean should be near `d + T/2`, roughly `0.7s` for fast metrics.
Path metrics update every `ping_every * period`, so their AoI is expected to be
larger.

## Delta-Sync Guard

On a quiet network, watch `logs/run_sync.log`:

```bash
tail -f logs/run_sync.log
```

Healthy behavior:

- delta cycles usually show `0/0 patch`
- reconciliation cycles send full patches every `reconcile_every` cycles
- adding `meta.tSource` must not make every Thing patch every cycle

This is the main safety check for observer effect.
