# Delta Claim Check

## t_change sample index
| case | traffic | period | sample_indices | first-sample hits | min progress frac | below t50 trials | max rate seen |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| delta_tcp_p1 | tcp | 1.0 | [2, 2, 2, 2, 2] | 0 | 0.67 | 0 | 14.74 |
| delta_tcp_p05 | tcp | 0.5 | [2, 2, 2, 2, 2] | 0 | 0.59 | 0 | 15.55 |
| delta_udp_p1 | udp | 1.0 | [2, 2, 2, 2, 2] | 0 | 0.68 | 0 | 15.53 |
| delta_udp_p05 | udp | 0.5 | [2, 2, 2, 2, 2] | 0 | 0.43 | 1 | 16.04 |

Verdict: t_change is not hitting the first collector sample in these artifacts; it hits sample 2 in every trial. For TCP, every t_change sample already passes 50% progress. UDP p05 has one 43% trial, but UDP is not the recommended mode.

## rate noise
| probe | period | median Mbps | sigma robust Mbps | 3sigma Mbps | min | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| rate_noise_tcp_p0_5 | 0.50 | 4.905 | 0.0625 | 0.1875 | 4.455 | 4.977 |
| rate_noise_tcp_p1_0 | 1.00 | 4.895 | 0.0350 | 0.1051 | 4.705 | 4.981 |

Verdict: 3sigma is about 0.105 Mbps at period 1.0 and 0.187 Mbps at period 0.5, far below the expected 5->15 Mbps swing. Noise increases at 0.5s but not enough to invalidate t50.

## whitelist / HTTP ack
| case | HTTP | audit result | reason |
| --- | ---: | --- | --- |
| valid_bw_15 | 202 | ok | None |
| invalid_bw_negative | 202 | rejected | bw out of range (0, 100], got -999.0 |
| invalid_bw_string | 202 | rejected | bw must be a number, got 'abc' |
| invalid_unknown_subject | 202 | rejected | unknown command: notACommand |
| invalid_bad_target | 202 | rejected | target not found: org.dt4n:link-no-such-link |

Verdict: HTTP 202 is only message acceptance. Invalid commands are still rejected by Command Agent and recorded in audit log.

## snapshot span
- A (direct)     p50= 119.1ms  p95= 144.0ms  max= 185.1ms  n_things=17
- B (search)     p50=  22.3ms  p95=  41.7ms  max= 664.9ms  n_things=19
- n=510  p50=+0.000s  p05=+0.000s  min=+0.000s  max=+0.000s

Use direct GET p95 ~= 0.144s as measured snapshot_span for the conservative Delta formula.

## proposed TCP Delta
| case | formula result |
| --- | ---: |
| delta_tcp_p1 | 2.498s |
| delta_tcp_p05 | 1.577s |

Verdict: the note's recommendation of period=0.5, TCP, Delta about 1.6s is consistent with these checks, but should be rerun with 20 trials before freezing.
