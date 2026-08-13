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

## 2026-07-17 - Lesson 9.3: pilot load balance

### QD-21: Separate LOAD_CFG_TRAIN from LOAD_CFG_V1

Before running the DQN pilot, `scripts/diag_decision_balance.py` checks whether
the optimal E/F decision is alive. `LOAD_CFG_V1` is intentionally strong for the
Dijkstra AoI sweep, but it makes E almost never optimal at C/D. A DQN could then
learn the correct static rule "always choose F", stop reading utilization, and
become insensitive to AoI.

This is not reward hacking: it is optimal behavior in a world whose training
distribution is wrong for RQ3. The fix is to change the training world, not to
punish the agent.

`LOAD_CFG_V1` remains locked for the Phase 8/10 Dijkstra sweep:
`e_load=(0.80, 0.97), drift_sigma=0.15`.

`LOAD_CFG_TRAIN` is added for DQN training:
`e_load=(0.60, 0.97), drift_sigma=0.15`.
It covers both balanced and bottleneck regimes, keeping the optimal decision
variable while avoiding a train/eval distribution gap on the bottleneck side.

Measured by `scripts/pilot_load_cfg.py --seeds 300`:

- V1 current: `frac_E_better=0.000`, `cost_bl max=0.5869`, verdict `FAIL`.
- V2d covering / selected train config: `frac_E_better=0.330`,
  `cost_bl max=0.4612`, verdict `PASS`.
- V2e covering also passed and was monotone, but had less balance headroom
  (`frac_E_better=0.223`). Training chooses the better decision-balance margin.

### QD-22: Gate policy responsiveness before 5-seed training

`scripts/pilot_train_r.py` runs a one-seed pilot and checks the behavior before
committing to 5 seeds:

- manual path inspection over 10 eval seeds,
- mean Q-spread on two-action states,
- `safe_path_freq(bottleneck_E) - safe_path_freq(normal) > 0.20`,
- arrival rate and revisit rate.

The safe-path gate uses a difference, not an absolute level. A policy that has
the same safe-path frequency under every load is static even if its absolute
frequency looks reasonable.

Pilot result for `scripts/pilot_train_r.py --seed 0 --episodes 400`:

- unique paths: `4/10`,
- Q-spread: `0.1790`,
- safe-path delta: `0.5700`,
- arrived rate: `1.0000`,
- revisit rate: `0.0000`,
- verdict: `GO`.

## 2026-07-17 - Lesson 9.4: 5-seed SNR gate

### QD-23: Do not fix the SRC first-hop quirk before Phase 11

The pilot revealed a known imperfection: the learned policy often starts with
`SRC -> B`, although `SRC -> A` has lower base delay. The state exposes
neighbor utilization but not neighbor base delay, so the agent has to infer
base-delay offsets from the node identity. At SRC the performance difference is
small, about 0.9% of total return.

This does not threaten the AoI measurement because AoI matters where stale
utilization flips a decision. The large, flipping decision is C/D `E` vs `F`,
not SRC `A` vs `B`. Adding base-delay features would expand state 7D to 9D and
weaken the AoI ablation from 28.6% to 22.2% for a tiny return gain.

Decision: record the quirk and leave the state unchanged.

### QD-24: Fix the 5-seed SNR gate before seeing 5-seed results

The decisive Phase 9 question is whether agent variance can swallow the Phase
11 effect. The SNR gate is fixed before the real 5-seed train:

- `headroom_sweep = 0.5869`,
- `std_agent <= 0.1956` means `SNR >= 3` and PASS,
- `0.1956 < std_agent <= 0.2934` means WARN and run 10 seeds,
- `std_agent > 0.2934` means FAIL and the stage needs investigation.

`scripts/train_5seed.sh` runs seeds 0..4 sequentially and refuses to run on a
dirty working tree. `scripts/analyze_5seed.py` computes the behavior gates,
`std_agent`, SNR, and the `safe_path_freq(AoI=0)` anchor for Phase 11.

## 2026-07-18 - Lesson 9.0 rev5: density resolves link model meaning

### QD-25: Use offered load for calibrated physical delay

The calibrated delay model now takes offered load, not measured utilization.
This is necessary because measured utilization clips near `1.0`, while the
fine density sweep distinguishes:

- `rho_offered=0.925`: BDP occupancy only.
- `rho_offered=0.930`: metastable queue, about `0.71 * ceiling`.
- `rho_offered>=0.935`: near-full finite queue.

The subthreshold formula is still:
`qdisc_delay_ms = base_delay_ms * rho_measured`.

Its interpretation changed. It is not a new queueing law and not M/M/1. The
density probes show that low-load mean qdisc backlog matches BDP/netem
occupancy:

- `bw=4, base=2.0`: mean packets `0.61`, BDP `0.64`.
- `bw=6, base=3.0`: mean packets `1.52`, BDP `1.44`.
- `bw=8, base=1.5`: mean packets `0.96`, BDP `0.96`.

The apparent "forbidden zone" was an artifact twice over. In the 3-config
density matrix, the only config with BDP above one packet, `bw=6, base=3.0`,
is the only config with substantial mass at two packets. In the fine cliff
sweep, `rho_offered=0.930` has large middle-queue mass.

### QD-26: The real calibrated effect is a narrow finite-queue transition

The robust effect is not gradual queue growth. It is the transition from BDP
occupancy through a very narrow metastable band into a near-full finite queue.
The fine cliff sweep brackets the transition at:

`rho_offered in (0.925, 0.930]`.

`loss_rate()` keeps the fitted overhead factor `1.079`, giving a derived
offered-load cross-check at `1 / 1.079 = 0.927`. After saturation, measured
utilization is clipped to `1.0`, queue delay uses the finite queue ceiling, and
overload magnitude is carried by loss. The agent state remains measured
utilization plus loss; reward/oracles/gates use offered-load snapshots.

## 2026-07-18 - Lesson 9.5: gate std must be model-local

### QD-27: Remove the hardcoded Phase-8 seed std from the oracle gate

`STD_SEED_ESTIMATE = 0.0276` came from an older Phase-8/M/M/1 world. After the
link model moved to rev5, the measured 5-seed agent std is about `0.0799`.
Using the old value made G2 report:

`SNR = 0.2219 / 0.0276 = 8.04`

The current-model estimate is:

`SNR = 0.2219 / 0.0799 = 2.78`

So the rev5 gate is WARN/NO-GO for the 1500-episode agent variance, even though
G1 balance and G3 symmetry remain acceptable. `evaluate_oracle_gate()` and
`tools/tune_stage.py` now require an explicit `std_seed_estimate`; callers must
measure it from the current 5-seed run before making an SNR claim.

### QD-28: Return is not enough, but behavior presets must match the physics

The rev5 1500-episode run had stable returns but unstable `safe_delta`. The
first interpretation was that some seeds were static. A direct heldout check
showed a more precise issue: the old `normal`/`bottleneck_E` presets were
chosen for the M/M/1 world, where `e_load=0.85` looked congested. In rev5, the
measured cliff is near `rho_offered=0.9275`, so both old presets were below
the cliff and asked the agent to distinguish two mostly uncongested worlds.

This keeps the behavior gates necessary, but their scenarios must be calibrated
whenever the link model changes. `LOAD_PRESETS` now uses deterministic rev5
slices below/around/above the measured cliff and sets `drift_sigma=0.0`.

## 2026-08-12 - Phase 21R complete: age-conditional conformal certificate

### QD-29: Proceed to Phase 22 with explicit post-selection and K=4 scope

Phase 21R closes as GO. The final status is 11 PASS gates and 1 PASS_MARGINAL
gate (G2 eta2), with G5 completed by block-bootstrap CI for `Var(e_model)`,
`Var(e_stale)`, and `Cov`. The fixed-sigma headline path remains the controlled
analysis; the operational-sigma path is robustness evidence and is reported
separately.

Phase 22 must address three scoped gaps: simultaneous coverage for all K=4
actions, coverage after selection, and sensitivity of the observed q_hat
age-shape ratio to tau/AoI/real telemetry.

## 2026-08-13 - Phase 22 complete: simultaneous and post-selection-valid certificate

### QD-30: Phase 22 GO is scoped to the main fixed-sigma cell

Phase 22 closes as GO on `poisson@0.925`: 17/17 gates PASS, 0 FAIL, 0
NOT_RUN. The full C3 operating point is `kappa=0.5`, acceptance `0.4911`,
`err|accept=0.0809`, `violation|accept=0.0794 <= alpha`, and
`err|reject / err|accept=4.44`.

The phase statement is scoped: simultaneous K=4 and post-selection-valid
certification is feasible on the main cell. The observed cost is a shift along
the risk-coverage curve, not a degraded frontier: AURC C0 `0.0913` vs C3
`0.0911`.

### QD-31: Prediction hit rate is reported, never used as a gate

The honest prediction scorecard is 21/32 = 65.6%. All signed misses M1..M10
remain in the table. Dropping them would be selective reporting, which is the
failure mode Phase 22 was designed to prevent.

The hit rate correlates with the origin of the prediction: the mechanism-based
tau model in Lesson 22.6 scored 7/7, while extrapolating one multiplier across
a family in Lesson 22.5 scored 2/7.

### QD-32: GO has three recorded conditions

GO-1: before claiming frontier invariance in an abstract, confirm
AURC(C3)/AURC(C0) < 1.02 on all non-degenerate cells. Current scan: 3/3
evaluable cells pass; 2 cells are degenerate/not evaluable.

GO-2: do not rank FWER procedures without paired bootstrap deltas. The current
artifact has 200 paired bootstrap draws, and 5/24 delta intervals contain zero.

GO-3: Amendment 1, studentized max-score, was signed but not run in Phase 22.
It must be recorded as future work or run as exploratory.
