# Delta Variant Summary

Screening run: 5 trials per variant. Delta_stable = p95(t_stable) + 0.3s margin; Delta_change = p95(t_change) + 0.3s margin.

| variant | traffic | period_s | post_p95_ms | t_change_p95_s | delta_change_s | t_stable_p95_s | delta_stable_s | metric_settle_after_exec_p95_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tcp_p1 | tcp | 1.0 | 33.035 | 1.053967 | 1.353967 | 4.178358 | 4.478358 | 3858.0 |
| tcp_p05 | tcp | 0.5 | 34.875 | 0.632619 | 0.932619 | 2.930721 | 3.230721 | 2796.0 |
| udp_p1 | udp | 1.0 | 35.868 | 1.060029 | 1.360029 | 4.000295 | 4.300295 | 3795.0 |
| udp_p05 | udp | 0.5 | 34.348 | 0.644979 | 0.944979 | 3.554209 | 3.854209 | 3271.0 |

Interpretation: t_change is the first direction-correct rate change; t_stable waits for 3 stable collector samples, so it is the safer training Delta.
