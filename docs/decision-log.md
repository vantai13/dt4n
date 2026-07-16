# Decision Log

## 2026-07-16 - Lesson 8.2: minimal RouteEnv

### QD-1: Separate link model, cap rho instead of queueing delay

The old routing simulator capped queueing delay directly, which freezes the
consequence of high utilization. `rl/routing/link_model.py` caps utilization
at `RHO_CAP = 0.97` and keeps the M/M/1 delay curve monotone.

### QD-2: State is 7D, not 12D

The locked topology has at most two outgoing neighbors per node, so padding for
four neighbors would create dead dimensions. `dest_node` is also omitted
because the destination is always `DST` in this locked stage.

### QD-3: Staleness stays outside RouteEnv

`RouteEnv` exposes true per-neighbor utilization through `true_utils()` and
`info['neighbor_utils_true']`. A later staleness wrapper must rebuild state
from these raw values. `RouteEnv` itself contains no staleness buffers, so the
clean `z=0` case is provable by inspecting the file.

## 2026-07-16 - Lesson 8.3: snapshot-buffer staleness

### QD-4: Buffer full rho snapshots, not positional neighbor utils

A2 stales demand, which is a global pair. Routing stales local neighbor
utilities: at C the pair means `(rho_CE, rho_CF)`, while at A it means
`(rho_AC, rho_AD)`. Buffering positional utils by step would mix unrelated
links.

The wrapper stores full per-link rho snapshots keyed by `(src, dst)`. This
matches the real twin pipeline better: Sync Agent publishes a whole network
snapshot with one source timestamp, and the twin ages as a single image.

### QD-5: z=0 is exactly invisible

For `z_steps == 0`, the wrapper reports `aoi_s = 0.0` and rebuilds the same
observation as bare `RouteEnv`. This keeps the zero-divergence gate exact
instead of letting tiny wall-clock differences leak into `aoi_norm`.

## 2026-07-16 - Lesson 8.3b: simulator/testbed alignment

### Correction: the previous fidelity check was invalid

The simulator topology used in Lesson 8.2 had an 8-node 50-100 Mbps link budget.
The real Mininet testbed described in the lesson notes uses a much smaller
4-8 Mbps budget. Comparing those directly was not a valid fidelity check.

### QD-6: Keep simulator training, do not train routing on Mininet

Routing v4 is a measurement problem, not just a learning problem. Mininet is
too slow and noisy for the main AoI curve: A2 measured about 16.86 s/episode,
while this simulator runs in sub-millisecond episodes. The main experiments
therefore stay in the controlled simulator; Phase 12 is where the frozen policy
is compared with the real pipeline.

### QD-7: Use TOPO V2 with a 4-8 Mbps link budget

`rl/routing/topology_r.py` now keeps the compact 8-node structure but changes
bandwidth values to 4, 6, and 8 Mbps. This matches the low-bandwidth Mininet
budget better while preserving the E/F decision flip and the 2-neighbor action
space.

### QD-8: Use continuous e_load for measurement

The main AoI curve should sweep one continuous congestion axis instead of
crossing many named scenarios. Named presets remain as slices of that axis:
`normal`, `borderline`, and `bottleneck_E`. They are for demo/storytelling, not
for multiplying the main experimental grid.

## 2026-07-16 - Lesson 8.4: Dijkstra instruments and hard gates

### QD-9: Separate instruments from baselines

`rl/routing/oracles.py` contains the measuring instruments:
`clairvoyant_dijkstra` uses true rho, while `blind_dijkstra` uses the observed
possibly stale rho. They are the same algorithm and differ only in data.

`rl/routing/baselines.py` contains opponents such as OSPF-like static shortest
path. OSPF is the twin-free anchor: the AoI where blind Dijkstra falls below
OSPF is the point where trusting the stale twin is worse than ignoring it.

### QD-10: Dijkstra cost is in reward units

The oracle cost mirrors the reward: `delay / DELAY_NORM_MS + W_LOSS * loss`
plus `W_HOP` per edge. This prevents the instrument from optimizing a different
objective than the one used to score episodes.

### QD-11: Reward r_v2 for TOPO V2

`DELAY_NORM_MS=100` and `W_HOP=0.10` were inherited from the old topology. On
TOPO V2, the fixed hop penalty dominated delay/loss and made Dijkstra choose by
hop count. `reward_r.py` now uses `REWARD_VERSION='r_v2'`,
`DELAY_NORM_MS=20.0`, and `W_HOP=0.02`.

### QD-12: AoI uses simulated time and warm-up history

The simulator does not sleep, so wall-clock AoI would be microseconds and the
AoI dimensions would be nearly dead. `RouteEnv.STEP_DURATION_S=0.5` provides a
nominal simulated time scale.

The staleness wrapper also pre-fills history for the selected z. This prevents
large z from being silently clipped by short episodes and models the real twin,
which has history before a flow starts. Warm-up uses a local RNG and local rho
copy only, so it does not advance `RouteEnv`'s RNG or corrupt zero-divergence.

## 2026-07-16 - Lesson 8.5: hard gates

### QD-13: Gates are pre-sweep hard stops

`scripts/gate_route_stage.py` now formalizes four hard gates:
zero-divergence, staleness-alive, reward-invariance, and clairvoyant-flat. Any
red gate means stop: no sweep, no training, no plot, because the harness is
emitting uninterpretable numbers.

### QD-14: Wrong-rate uses a post-hoc target

Comparing `clairvoyant_dijkstra` with itself made `clair_wrong=0` by tautology.
`posthoc_dijkstra` now uses `rho_snapshot_next`, obtained by `RouteEnv.peek_next_rho()`,
to measure the drift noise floor. `peek_next_rho()` clones RNG state, so
peeking cannot perturb the episode.

### QD-15: Warm-up history ordering and OFAT

Warm-up timestamps must be oldest-first because `_observed_snapshot()` indexes
the deque positionally as `len(hist)-1-z`. The wrapper also seeds warm-up past
from the episode seed, never from z. Seeding by z changed both how far back the
agent looked and what history existed there, an OFAT violation that could make
a bad but pretty curve.

## 2026-07-16 - Lesson 8.6: GO/NO-GO

### QD-16: Loop handling is a tripwire

`topology_r.py` is a DAG: there are no back edges, so loops are physically
impossible unless the topology changes. The loop/timeout branch in `RouteEnv`
is retained as a guard, not as live experiment complexity.

### QD-17: OSPF calibrated replaces the strawman for breaking points

`ospf_reactive` assumes every link is empty and therefore always walks into the
short-delay E bottleneck. It is retained as a strawman reference only.

`ospf_calibrated` uses expected load from `load_cfg` and still does not read the
twin. This is the fair twin-free anchor for the breaking point.

### QD-18: GO configuration

The chosen GO configuration is:
`LOAD_CFG_V1 = {'base_load': (0.25, 0.40), 'e_load': (0.80, 0.97),
'drift_sigma': 0.15}`.

It is intentionally not the largest drift setting. `drift_sigma=0.30` can make
effects larger, but it pushes the experiment into a noisy tail where CoB is
less interpretable. The selected setting is on the rising side of the curve.

## 2026-07-16 - Lesson 8.7: correction from real Ditto AoI

### Correction: do not report the legacy BP in seconds

The previous Lesson 8.6 statement "BP is around 0.5-1.0 s" is suspended. In
the legacy z harness, seconds came from `RouteEnv.STEP_DURATION_S=0.5`. Changing
that constant changes the reported seconds axis while leaving returns
unchanged. Therefore the invariant result is only "BP occurs between z=1 and
z=2" in that legacy harness, not a defensible physical time.

### QD-19: Use physical packet time for routing

Routing decisions happen per hop, not after an A2-style stabilization delay.
`RouteEnv` now exposes `sim_time_s`, reset to zero at episode start and advanced
by `link_delay_ms / 1000.0` on each valid hop. This is the physical time axis
for routing AoI.

### QD-20: Sweep Ditto sync period, not z, for operational claims

The real Ditto measurement in `results/aoi/aoi_a2_host_srv1.json` shows:
AoI mean about 0.298 s, std about 0.145 s, range about [0.051, 0.548] s, and
sync period 0.500 s. The histogram is a sawtooth: sync refreshes the snapshot,
then AoI grows until the next sync.

`rl/routing/ditto_staleness_r.py` adds `DittoStalenessWrapper`, which samples a
flow phase inside the sync cycle and refreshes the observed rho snapshot at
physical sync boundaries. The new sweep variable is `sync_period_s`, the knob
an operator can actually tune.

### Known risk

A routing episode is often tens of milliseconds, while the measured Ditto sync
period is 500 ms. The twin may not refresh inside one flow at all. If the
sync-period curve stays flat near 0.5 s, that is a finding: AoI is acting across
flow arrivals more than inside a single per-packet route episode.
