# Mutual satisfiability of the G-A017 gate set

Date: 2026-09-05 UTC. Status: `DESK_CHECK_NO_DATA`.

This note is the `G-L90` countermeasure applied to the G'.1 error budget. It
takes no data, changes no published verdict, and authorises no run. It answers
one question about a gate SET before that set is signed: does a configuration
exist that satisfies all of it at once.

Artifact: `results/SMOKE/phase-G2/g1_mutual_sat.json`, produced by
`tools/g1_mutual_satisfiability.py`.

## 1. Why the check exists, and proof that it works

`G-L90` and `G-L96` record that `EMIT-1` and `EMIT-4` were both signed and
could not both be met. The checker reproduces that case as a regression:

| Gate | p per trial | N trials | P(pass) | Signable |
|---|---:|---:|---:|---|
| `EMIT-4` `alignment_exact` (historical) | 0.001 | 76,800 | `4.261e-34` | no |

This matches the `4.26e-34` recorded in doc 45 to three significant figures.
The accident was one line of arithmetic away from being caught before the
64-minute run. It is now that one line.

**No gate in the G-A017 budget is a tolerance-free boolean.** Every gate is a
threshold with a stated tolerance, so this failure mode cannot recur by
construction.

## 2. The pair that actually binds: B-1 against the G.0 tail headroom

`B-1` requires a signal fraction `sf >= 0.95`, which is a LOWER bound on
`sigma`: the nugget `v` has a hard floor set by packet quantisation, and
`sf >= s` forces `sigma >= sqrt(v_floor * s/(1-s))`.

The G.0 headroom constraint is an UPPER bound on the same variable:
`rho_bar + 2.58*sigma <= rho_max` gives `sigma <= 0.0535`
(`docs/phase-G/00-prereg-g0.md:28`).

The two bound `sigma` from opposite sides, so the intersection must be
computed rather than assumed.

| tau | dt | sigma quant. floor | sigma lower (sf=0.95) | sigma upper | headroom | empty |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 0.05 | 0.00808 | 0.0352 | 0.0535 | **1.52x** | no |
| 3 | 0.15 | 0.00269 | 0.0117 | 0.0535 | 4.55x | no |
| 5 | 0.20 | 0.00202 | 0.0088 | 0.0535 | 6.07x | no |
| 10 | 0.20 | 0.00202 | 0.0088 | 0.0535 | 6.07x | no |
| 20 | 0.20 | 0.00202 | 0.0088 | 0.0535 | 6.07x | no |
| 30 | 0.20 | 0.00202 | 0.0088 | 0.0535 | 6.07x | no |

**No intersection is empty. The gate set is satisfiable.** But the margin is
not uniform, and the `tau = 1 s` cell is the one to watch.

### 2.1 The quantisation step is one PACKET, not one byte

This is where the check earns its cost. A window carries
`C*dt*rho_bar/8` bytes, but the emitter delivers whole 1400-byte payloads, so
the load can only move in steps of `8*L/(C*dt)` in `rho` units:

    sigma_floor = 8*L/(C*dt*sqrt(12))
    dt = 0.20 s  ->  0.00202
    dt = 0.05 s  ->  0.00808

Computing the same floor with a one-byte step gives `5.8e-6` at `dt = 0.05`,
about 1400x smaller, and would have made every margin above look enormous and
the check look pointless. The packet-level figure is the correct one, and the
repository already has direct evidence for it: `G-L43` records that the v2
static smoke returned 45 of 48 cells `QUANT_LIMITED`.

### 2.2 The `tau = 1 s` cell is tight, and the cause is gate T-2

`T-2` requires `dt <= tau/20`, so `tau = 1 s` must sample at `dt = 0.05 s`.
A four-times finer window carries a quarter of the packets, and the
quantisation floor rises by the same factor of four. That drives the `sigma`
lower bound from 0.0088 up to 0.0352 while the upper bound stays at 0.0535.

The window `[0.0352, 0.0535]` is real but is a factor of 1.52. `T-2` and
`B-1` therefore pull against each other at small `tau`, and this is a
property of the design rather than of the host.

Recorded consequence: the `tau = 1 s` cell is admitted with `sigma` fixed in
the upper half of its window, and if any additional white measurement noise
appears beyond quantisation, this is the first cell to become infeasible.
It is the designated canary, not a cell to quietly drop when it fails.

## 3. Run length against the wall clock

`T-1` sets `T_run = 205*tau` with 3 replicates.

| tau | T_run | x3 replicates |
|---:|---:|---:|
| 1 s | 205 s | 0.17 h |
| 3 s | 615 s | 0.51 h |
| 5 s | 1,025 s | 0.85 h |
| 10 s | 2,050 s | 1.71 h |
| 20 s | 4,100 s | 3.42 h |
| 30 s | 6,150 s | 5.12 h |

Every individual cell fits a 6-hour budget. The CAMPAIGN total does not:
the full six-point grid is 11.78 h, while `{1, 3, 5, 10, 20}` is 6.66 h.

`tau = 30 s` is dropped from the signed grid on cost. It is the one cell that
is fully feasible at `T/tau = 100` at every `sf` level tested, so it can be
restored later for 2.63 h rather than 5.12 h if it is wanted. That option is
recorded here so the choice is a decision rather than a rediscovery.

## 4. Verdict

| Check | Result |
|---|---|
| Pairs checked | 12 |
| Pairs with empty intersection | 0 |
| Tolerance-free booleans in this budget | 0 |
| Cells over the per-cell wall-clock budget | 0 |
| Campaign total within budget | only after dropping `tau = 30 s` |

The G-A017 gate set is mutually satisfiable on the signed grid
`tau in {1, 3, 5, 10, 20}`.
