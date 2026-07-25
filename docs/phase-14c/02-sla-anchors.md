# Phase 14C.2 - Natural SLA anchors

Ngay tao: 2026-07-24
Status: anchor measurement only. No routing3 positive pilot has been run.

## Purpose

Before choosing `SLA_DELAY_MS` and `W_SLA`, record natural delay anchors from
the calibrated `link_model`. This prevents tuning `SLA_DELAY_MS` after seeing a
positive/negative routing3 pilot result.

## Command

```bash
python3 - <<'PY'
from rl.routing3 import link_model as LM
from rl.routing3 import topology3 as T3
cfg=T3.link_cfg()
print('DIEM NEO TU NHIEN trong link_model (de chon SLA_DELAY_MS):')
print()
for name,lk in [('access',T3.ACCESS_LINKS['P1']),
                ('bottleneck',T3.BOTTLENECK_LINKS['P1']),
                ('egress',T3.EGRESS_LINKS['P1'])]:
    m=cfg[lk]
    ceil=LM.queue_ceiling_ms(m['base_bw'],m['queue_pkts'])
    d_lo=LM.total_delay_ms(m['base_delay'],0.90,bw_mbps=m['base_bw'],queue_pkts=m['queue_pkts'])
    d_hi=LM.total_delay_ms(m['base_delay'],1.00,bw_mbps=m['base_bw'],queue_pkts=m['queue_pkts'])
    print(f'{name:<12s} base={m["base_delay"]:.1f}ms  ceiling={ceil:.2f}ms  '
          f'delay@0.90={d_lo:.2f}  delay@1.00={d_hi:.2f}')
print()
print('Tong delay MOT DUONG (3 hop):')
for r in [0.5,0.9,0.925,0.93,1.0]:
    tot=sum(LM.total_delay_ms(cfg[lk]['base_delay'],r,bw_mbps=cfg[lk]['base_bw'],
            queue_pkts=cfg[lk]['queue_pkts']) for lk in T3.PATH_LINKS['P1'])
    print(f'  rho={r:.3f} -> {tot:7.2f} ms')
PY
```

## Output

```text
DIEM NEO TU NHIEN trong link_model (de chon SLA_DELAY_MS):

access       base=2.0ms  ceiling=19.66ms  delay@0.90=3.94  delay@1.00=21.66
bottleneck   base=3.0ms  ceiling=26.21ms  delay@0.90=5.91  delay@1.00=29.21
egress       base=2.0ms  ceiling=19.66ms  delay@0.90=3.94  delay@1.00=21.66

Tong delay MOT DUONG (3 hop):
  rho=0.500 ->   10.78 ms
  rho=0.900 ->   13.80 ms
  rho=0.925 ->   13.99 ms
  rho=0.930 ->   53.52 ms
  rho=1.000 ->   72.52 ms
```

## Anchors

| anchor | value |
|---|---:|
| per-link access/egress delay at rho=0.90 | 3.94 ms |
| per-link bottleneck delay at rho=0.90 | 5.91 ms |
| per-link access/egress delay at rho=1.00 | 21.66 ms |
| per-link bottleneck delay at rho=1.00 | 29.21 ms |
| one-path total delay at rho=0.925 | 13.99 ms |
| one-path total delay at rho=0.930 | 53.52 ms |
| one-path total delay at rho=1.000 | 72.52 ms |

## Interpretation

The SLA threshold is per-hop because `step_reward()` is called once per hop.
The natural per-hop gap is between the healthy bottleneck delay at `rho=0.925`
(`5.99 ms`) and the just-over-cliff access/egress delay at `rho=0.930`
(`15.96 ms`).

## Candidate comparison

Command:

```bash
python3 - <<'PY'
from rl.routing3 import link_model as LM
from rl.routing3 import topology3 as T3
cfg=T3.link_cfg(); W_SLA=2.0; DNORM=20.0
def pd(r):
    return [LM.total_delay_ms(cfg[lk]['base_delay'],r,bw_mbps=cfg[lk]['base_bw'],
            queue_pkts=cfg[lk]['queue_pkts']) for lk in T3.PATH_LINKS['P1']]
print(f'{"rho":>7s} ' + ' '.join(f'SLA={s:<5.1f}' for s in [8.0,10.0,12.0,15.0]))
for r in [0.5,0.9,0.925,0.93,0.95,1.0,1.2]:
    ds=pd(r); row=f'{r:7.3f} '
    for sla in [8.0,10.0,12.0,15.0]:
        row+=f'{sum(-W_SLA*max(0.0,d-sla)/DNORM for d in ds):9.3f} '
    print(row)
print('SO HOP bi phat tai rho=0.930:')
for sla in [8.0,10.0,12.0,15.0]:
    print(f'  SLA={sla:5.1f} -> {sum(1 for d in pd(0.93) if d>sla)}/3 hop')
PY
```

Output:

```text
    rho SLA=8.0   SLA=10.0  SLA=12.0  SLA=15.0
  0.500     0.000     0.000     0.000     0.000
  0.900     0.000     0.000     0.000     0.000
  0.925     0.000     0.000     0.000     0.000
  0.930    -2.952    -2.352    -1.752    -0.852
  0.950    -4.852    -4.252    -3.652    -2.752
  1.000    -4.852    -4.252    -3.652    -2.752
  1.200    -4.852    -4.252    -3.652    -2.752

SO HOP bi phat tai rho=0.930:
  SLA=  8.0 -> 3/3 hop
  SLA= 10.0 -> 3/3 hop
  SLA= 12.0 -> 3/3 hop
  SLA= 15.0 -> 3/3 hop
```

All four candidates keep zero penalty below the cliff and activate at the
cliff. `SLA=15.0` is still brittle: the access/egress hops at `rho=0.930` only
clear it by about `0.96 ms`. `SLA=8.0` is too close to the healthy bottleneck
anchor (`5.99 ms`). `SLA=10.0` gives a balanced margin: `4.01 ms` above the
healthy anchor and `5.96 ms` below the first cliff delay.

## Signed Decision

Ngay ky: 2026-07-24
Git hash at signing: `4cf5846`

```text
SLA_DELAY_MS = 10.0
W_SLA        = 2.0
```

Rationale:

- `SLA_DELAY_MS = 10.0` is per-hop, catches all three hops at `rho=0.930`, and
  has balanced lower/upper margins around the empty interval `5.99 -> 15.96 ms`.
- `W_SLA = 2.0` matches `W_LOSS = 2.0`, keeping the nonlinear SLA and loss
  channels comparable while leaving the unclipped delay channel active.
- These values are signed before any positive `routing3` pilot with r_v3.
