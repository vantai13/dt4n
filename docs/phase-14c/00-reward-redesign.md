# Phase 14C.0 - Reward redesign preregistration

Ngay tao: 2026-07-24
Base Git truoc Phase 14C: `4cf5846` (`phase14a-final`)
Trang thai: preregistration cho reward redesign. Khong sua de
`rl/routing3/reward3.py`; r_v2 phai tiep tuc tai lap duoc.

## 1. Why this phase exists

Phase 14A voi `r_v2` ket luan FAIL va da duoc giu nguyen. Phase 14B.0 cho thay
gross break-even cua sync tren cau hinh tot nhat r_v2 chi la:

```text
c* = 0.023188
```

Khong duoc sua reward chi vi muon ket qua duong. Reward chi duoc sua neu co loi
ky thuat co the chung minh doc lap voi ket qua 14D/sync. Ba loi duoi day la ly
do cho Phase 14C.

## 2. Three technical failures in r_v2

### Failure A - delay clipping erases overload delay signal

`rl/routing3/reward3.py` dung:

```text
delay_term = max(-1.0, -delay_ms / 20.0)
```

Tren bottleneck link cua topology3, vung overload quan trong cho AoI la khoang
`rho=0.93 -> 1.30`. Trong vung nay delay term cua r_v2 bi clip tai `-1.0`, nen
delay/tail-latency component khong phan biet "vua qua cliff" voi "qua tai nang".

Expected diagnostic command:

```bash
python3 -m measurements.diagnose_reward3_v3
```

Gate co hoc cho Failure A:

```text
v2_delay_overload_span == 0
v3_delay_overload_span > 0
```

### Failure B - terminal arrival constant contaminates cross-action economics

`R_ARRIVED = 5.0` la hang so chung giua cac hanh dong route, nen no khong doi
argmax trong Phase 14A. Nhung Phase 14D se them hanh dong `REQUEST_SYNC`, tuc la
action space co hai loai hanh dong. Khi do hang so route-terminal khong con la
hang so chung nua.

Do do Phase 14C reward moi phai loai terminal arrival constant ra khoi reward
cham diem hanh dong route. Neu can shaping cho training, phai them rieng va ghi
ro la shaping, khong dung lam measurement metric.

### Failure C - linear reward is risk-neutral

Reward r_v2 tuyen tinh theo delay va loss. Voi objective ky vong, no chi cho
AoI gia tri khi thong tin moi doi duoc argmax. No khong cho kenh "giam bat dinh"
co gia tri rieng.

Phase 14C se them phi tuyen bang expected retransmission cost va SLA penalty:

```text
loss_penalty = 1/(1-loss) - 1
loss_term    = -W_LOSS * loss_penalty
sla_term  = -W_SLA * max(0, delay_ms - SLA_DELAY_MS) / DELAY_NORM_MS
```

Revision note: ban dau de xuat `loss^2`, nhung deterministic diagnostic cho
thay no di sai huong vi `loss in [0,1]` nen binh phuong lam giam dai dong loss
3.4 lan so voi tuyen tinh. Doi sang `1/(1-loss)-1` vi no la chi phi truyen lai
ky vong: khi loss nho thi gan tuyen tinh, khi loss tien gan 1 thi phat rat nang.
`sla_term` dua tail-latency / SLA violation vao metric.

## 3. New reward file

Create:

```text
rl/routing3/reward3_v3.py
```

Do not modify:

```text
rl/routing3/reward3.py
```

Initial constants:

| constant | value | reason |
|---|---:|---|
| `REWARD_VERSION` | `r_v3` | separate provenance |
| `DELAY_CLIP_EVAL` | `None` | truthful eval metric |
| `DELAY_CLIP_TRAIN` | `-1.0` | optional train stabilization only |
| `R_ARRIVED` | `0.0` | remove route-only filler |
| `LOSS_SATURATION` | `0.99` | cap retransmission blow-up |
| `SLA_DELAY_MS` | `10.0` | signed per-hop cliff threshold |
| `W_SLA` | `2.0` | balance SLA and delay channels |
| `CRITICALITY_DEFAULT` | `1.0` | backward-compatible call sites |

## 4. Literature basis

Agheli, Pappas, Popovski, and Kountouris, "Effective Communication: When to
Pull Updates?", arXiv:2311.06432 / ICC 2024, study pull-based update control
from the receiver side. Their GoE formulation couples freshness with usefulness
and optimizes query decisions under communication cost. This supports Phase
14C's later `criticality` variable and Phase 14D's `REQUEST_SYNC` action.

Ng, Harada, and Russell, "Policy Invariance Under Reward Transformations:
Theory and Application to Reward Shaping", ICML 1999, is the guardrail for
separating task reward from optional training shaping.

## 5. Guardrails

1. Keep all r_v2 Phase 14A/14B.0 artifacts.
2. Do not run a Phase 14C pilot/gate on r_v3 before this file exists.
3. Run deterministic reward diagnostic first.
4. Run negative control again before making any positive claim.
5. Report both r_v2 and r_v3 results in the thesis.

## 6. Immediate deterministic diagnostic

Command da chay sau khi file prereg nay va `reward3_v3.py` duoc tao:

```bash
python3 -m measurements.diagnose_reward3_v3 \
  --json-out results/phase-14c/reward3_v3_diagnostic.json
```

Ket qua:

| rho | delay_ms | loss | v2_delay | v2_total | v3_loss | v3_total | v3_total_v0.2 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.300 | 3.971 | 0.0000 | -0.1986 | -0.2186 | -0.0000 | -0.2186 | -0.0597 |
| 0.700 | 5.266 | 0.0000 | -0.2633 | -0.2833 | -0.0000 | -0.2833 | -0.0727 |
| 0.900 | 5.913 | 0.0000 | -0.2957 | -0.3157 | -0.0000 | -0.3157 | -0.0791 |
| 0.925 | 5.994 | 0.0000 | -0.2997 | -0.3197 | -0.0000 | -0.3197 | -0.0799 |
| 0.930 | 21.608 | 0.0035 | -1.0000 | -1.0269 | -0.0069 | -2.2681 | -0.4696 |
| 1.000 | 29.208 | 0.0732 | -1.0000 | -1.1664 | -0.1580 | -3.5592 | -0.7278 |
| 1.100 | 29.208 | 0.1575 | -1.0000 | -1.3349 | -0.3738 | -3.7750 | -0.7710 |
| 1.300 | 29.208 | 0.2871 | -1.0000 | -1.5942 | -0.8054 | -4.2066 | -0.8573 |

Summary:

| quantity | value |
|---|---:|
| v2 delay span below cliff `0.30 -> 0.925` | 0.101156 |
| v2 delay span overload `0.93 -> 1.30` | 0.000000 |
| v2 total span overload `0.93 -> 1.30` | 0.567262 |
| v3 delay span overload `0.93 -> 1.30` | 0.380016 |
| v3 loss-term span overload `0.93 -> 1.30` | 0.798460 |
| v3 total span overload `0.93 -> 1.30` | 1.938508 |
| v3/v2 total overload span ratio | 3.417 |

Interpretation: the exact delay component in r_v2 is fully clipped in the
overload interval. r_v2 still has a loss signal, so this is not a claim that
all r_v2 signal is zero. The claim is narrower and technical: r_v2 erases the
delay/tail-latency signal exactly where AoI should matter most, while r_v3
restores that channel and adds an SLA tail penalty.

No `pilot_marginalized` result on r_v3 belongs in this file. Full Phase 14C
gates must go in later docs.
