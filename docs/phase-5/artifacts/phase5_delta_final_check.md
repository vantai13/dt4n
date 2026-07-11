# Phase 5 Delta Final Check

## 1. period=0.5 cycle gate
- cycle_elapsed: n=387, p50=0.058s, p95=0.127s, max=0.340s
- duty: p50=11.6%, p95=25.4%, max=68.0%
- delta patch cycles: 58/374 nonzero
- reconcile patch cycles: 13/13 nonzero
- verdict: PASS, period=0.5 is not overloaded on this run.

## 2. direct vs search entity set
- direct n=17
- search n=19
- search THUA : ['org.dt4n:controller', 'org.dt4n:link-h1-srv1']
- search THIEU: []
- verdict: keep direct GET for observation contract; search returns extra Things.

## 3. rate noise final
- n=120, median=4.9065 Mbps, sigma_robust=0.0694 Mbps, 3sigma=0.2083 Mbps
- min=1.7297 Mbps, p95=5.0318 Mbps, max=8.0583 Mbps
- note: robust MAD is used because raw samples include outliers.

## 4. delta final 20 trials
- t50: p50=0.632s, p95=0.845s, max=1.046s
- settling t_s: p50=2.083s, p95=2.091s, max=2.095s
- t2/t1 p95=3.30, t_change=None=0/20, t50 max/p95=1.24
- sample index counts at t50: {'2': 12, '3': 8}
- min progress fraction: 0.506

## 5. Delta decision
- Direct GET formula: t50_p95 + period + snapshot_direct_p95 + margin
- Delta = 0.845 + 0.500 + 0.144 + 0.300 = 1.789s
- Search formula would be 1.687s, but search is rejected for tail/entity-set reasons.
- Recommended freeze candidate: period=0.5s, traffic=tcp, Delta=1.80s.

## 6. Scenario mix
- ('LinkDegrade', 's2-s3')                      37
- ('LinkDegrade', 's1-s3')                      27
- ('LinkDegrade', 's1-s2')                      25
- ('TrafficFlood', 'h3', 'srv1')                24
- ('TrafficFlood', 'h3', 'srv2')                19
- ('TrafficFlood', 'h2', 'srv1')                19
- ('TrafficFlood', 'h2', 'srv2')                18
- ('TrafficFlood', 'h1', 'srv2')                18
- ('TrafficFlood', 'h1', 'srv1')                13
