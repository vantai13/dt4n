#!/usr/bin/env python3
"""Phase 14B - RQ0' / RQ0'': trajectory-level sync policy comparison.

WHY THIS FILE EXISTS
--------------------
Every earlier measurement was an UPPER BOUND over a pooled set of (obs, z)
pairs. Those bounds are not trajectory-consistent: you cannot freely choose to
stand at a large z, because z is a consequence of your own earlier sync
decisions (z is ENDOGENOUS). This file simulates full episodes and compares
real policies under an equal sync budget.

WHAT IS MEASURED
----------------
    G_AoI = V(adaptive) - V(best periodic)      <- gate RQ0'
    G_RL  = V(adaptive) - V(best simple rule)   <- gate RQ0''

If G_AoI is large but G_RL ~ 0, a one-parameter rule already captures the
value and reinforcement learning has no contribution. That is a legitimate
result and must be reported, not hidden.

DESIGN DECISIONS (deliberate, and each one attackable)
------------------------------------------------------
1. COMMON RANDOM NUMBERS. The true world does NOT depend on sync decisions
   (syncing observes the world, it does not change it). Worlds are therefore
   pre-generated per episode and every policy is scored on exactly the same
   worlds. Comparisons are PAIRED, which removes most of the variance from
   the differences.

2. SPLIT-SAMPLE POLICY SELECTION. Thresholds (T, h, tau) are chosen on
   CALIBRATION episodes and scored on DISJOINT evaluation episodes. Choosing
   and scoring on the same data is the winner's curse that inflated the
   Phase 14A CVaR result; the same trap applies to policy selection.

3. EQUAL BUDGET. Every policy may sync at most B times per episode. Because
   the budget is equal, the term c_sync * B is identical across policies and
   CANCELS inside G_AoI and G_RL. c_sync only matters when choosing B, which
   is why B is swept rather than fixed.

4. NO TERMINAL CONSTANT by default. R_ARRIVED = 5.0 was harmless in 14A
   because every routing action received it. Keeping it here would add a
   constant horizon * R_ARRIVED to every episode and shrink relative
   differences. See docs/phase-14b/00-upper-bound.md section 4.

5. STEP-LEVEL RISK by default. CVaR over pooled per-packet rewards matches
   the operational SLA story (tail latency per packet). CVaR over episode
   returns is also available via --risk-unit episode, but episode sums are
   much closer to Gaussian and hide the tail the objective is about.

POLICIES
--------
    P0 never      : never sync                       (naive reference only)
    P1 periodic   : sync every T steps               (the REAL opponent)
    P2 z-threshold: sync when z >= h                 (simple rule on AGE)
    P3 margin     : sync when q_margin <= tau        (simple rule on STATE)
    P4 voi        : sync when g_hat(obs,z) >= tau    (adaptive: age + state)

P4 is NOT an oracle. g_hat is the expected gain from a perfect sync computed
from (obs, z) alone, which a real controller can compute at run time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone

import numpy as np

from measurements.samplers3 import Sampler3Path
from rl.routing3 import link_model as LM
from rl.routing3 import reward3
from rl.routing3 import topology3 as T3


_LINK_CFG = T3.link_cfg()


# --------------------------------------------------------------------------
# reward on the TRUE world
# --------------------------------------------------------------------------

def path_reward(action, levels, include_terminal):
    """Reward of routing one packet down `action` given true latent levels."""
    rho = T3.levels_to_rho(levels)
    total = 0.0
    links = T3.PATH_LINKS[action]
    last = len(links) - 1
    for idx, link in enumerate(links):
        meta = _LINK_CFG[link]
        r = float(rho[link])
        delay = LM.total_delay_ms(
            meta["base_delay"], r,
            bw_mbps=meta["base_bw"], queue_pkts=meta["queue_pkts"],
        )
        arrived = include_terminal and (idx == last)
        total += reward3.step_reward(delay, LM.loss_rate(r), arrived=arrived).total
    return float(total)


def aggregate(values, objective, cvar_alpha):
    """Mean, or CVaR of the worst alpha fraction."""
    arr = np.sort(np.asarray(values, dtype=np.float64))
    if objective == "cvar":
        k = max(1, int(cvar_alpha * arr.size))
        return float(arr[:k].mean())
    return float(arr.mean())


# --------------------------------------------------------------------------
# belief statistics from a snapshot of age z
# --------------------------------------------------------------------------

def belief_stats(sampler, snap_levels, z, n_mc, rng, objective, cvar_alpha,
                 include_terminal):
    """One Monte Carlo pass -> Q, decision margin, and myopic sync value.

    q       : {action: Q(a | obs, z)}
    a_stale : argmax_a Q      (the action taken if we do NOT sync)
    margin  : Q(best) - Q(second)   -> small means "unsure which path"
    g_hat   : value of a PERFECT sync right now, estimated from (obs, z):
                  agg[max_a R(a, w)] - agg[R(a_stale, w)]
              All three come from the SAME rollouts (common random worlds),
              which is what makes the across-action comparison low-variance.
    """
    actions = T3.PATH_NAMES
    obs = {"rho": T3.levels_to_rho(snap_levels)}
    per_action = {a: np.empty(n_mc, dtype=np.float64) for a in actions}
    best_per_world = np.empty(n_mc, dtype=np.float64)

    for i in range(n_mc):
        world = sampler.roll_forward(obs, z, rng)
        lv = T3.rho_to_levels(world["rho"])
        best = -np.inf
        for a in actions:
            r = path_reward(a, lv, include_terminal)
            per_action[a][i] = r
            if r > best:
                best = r
        best_per_world[i] = best

    q = {a: aggregate(per_action[a], objective, cvar_alpha) for a in actions}
    order = sorted(q, key=lambda a: q[a], reverse=True)
    a_stale = order[0]
    return {
        "q": q,
        "a_stale": a_stale,
        "margin": float(q[order[0]] - q[order[1]]),
        "g_hat": float(
            aggregate(best_per_world, objective, cvar_alpha)
            - aggregate(per_action[a_stale], objective, cvar_alpha)
        ),
    }


# --------------------------------------------------------------------------
# world pre-generation (exogenous: identical for every policy)
# --------------------------------------------------------------------------

def make_world(base_seed, ep, horizon):
    """Latent level trajectory for one episode. Depends only on (seed, ep)."""
    rng = np.random.default_rng([base_seed, 1_000_003, ep])
    levels = T3.sample_initial_levels(rng)
    traj = [dict(levels)]
    for _ in range(horizon - 1):
        levels = T3.advance_levels(levels, 1, rng)
        traj.append(dict(levels))
    return traj


def snapshot_at(base_seed, ep, t, world):
    """Jittered measurement of the true state at time t.

    Keyed on (seed, ep, t) so two policies that sync at the same instant get
    the IDENTICAL snapshot. This is what makes the comparison paired.
    """
    rng = np.random.default_rng([base_seed, 2_000_003, ep, t])
    return T3.observe_levels(world[t], rng)


# --------------------------------------------------------------------------
# belief cache
# --------------------------------------------------------------------------

class StatsCache:
    """Cache belief_stats keyed by (ep, t_sync, z).

    (ep, t_sync) fixes the snapshot and z fixes its age, so the key determines
    the belief exactly. Policies that synced at the same instant share entries,
    which is where nearly all of the speed comes from.
    """

    def __init__(self, sampler, base_seed, n_mc, objective, cvar_alpha,
                 include_terminal):
        self.sampler = sampler
        self.base_seed = base_seed
        self.n_mc = n_mc
        self.objective = objective
        self.cvar_alpha = cvar_alpha
        self.include_terminal = include_terminal
        self._d = {}
        self.hits = 0
        self.misses = 0

    def get(self, ep, t_sync, z, snap_levels):
        key = (ep, t_sync, z)
        cached = self._d.get(key)
        if cached is not None:
            self.hits += 1
            return cached
        self.misses += 1
        rng = np.random.default_rng([self.base_seed, 3_000_003, ep, t_sync, z])
        out = belief_stats(
            self.sampler, snap_levels, z, self.n_mc, rng,
            self.objective, self.cvar_alpha, self.include_terminal,
        )
        self._d[key] = out
        return out


# --------------------------------------------------------------------------
# episode rollout
# --------------------------------------------------------------------------

def run_episode(policy, ep, world, cache, base_seed, budget,
                include_terminal, collect=None):
    """Simulate one episode -> (per-step rewards, syncs used, sync ages).

    Timeline of step t, following the optimal-stopping framing in
    docs/PHASE_14B.md: EITHER act now with the information you already have,
    OR pay to refresh it and THEN act.

        1. form the belief from the snapshot currently held (age z)
        2. decide whether to spend one sync; a sync observes the world at
           time t, so the belief is re-formed at age 0
        3. act, and realise the reward on the TRUE world at time t
        4. the world advances to t+1 and the age grows by 1
    """
    horizon = len(world)
    t_sync = 0
    snap = snapshot_at(base_seed, ep, 0, world)      # free initial snapshot
    z = 0
    left = budget
    rewards = np.empty(horizon, dtype=np.float64)
    sync_ages = []

    for t in range(horizon):
        st = cache.get(ep, t_sync, z, snap)           # belief BEFORE syncing

        if collect is not None:
            collect.append({"z": z, "margin": st["margin"], "g_hat": st["g_hat"]})

        if left > 0 and policy.wants_sync(t, z, st, left, horizon, budget):
            sync_ages.append(z)
            t_sync = t
            snap = snapshot_at(base_seed, ep, t, world)
            z = 0
            left -= 1
            st = cache.get(ep, t_sync, 0, snap)       # belief AFTER syncing

        rewards[t] = path_reward(st["a_stale"], world[t], include_terminal)
        z += 1

    return rewards, budget - left, sync_ages


# --------------------------------------------------------------------------
# policies
# --------------------------------------------------------------------------

class Never:
    name = "P0_never"

    def wants_sync(self, t, z, st, left, horizon, budget):
        return False


class Periodic:
    def __init__(self, period):
        self.period = max(1, int(period))
        self.name = f"P1_periodic_T{self.period}"

    def wants_sync(self, t, z, st, left, horizon, budget):
        return z >= self.period


class ZThreshold:
    def __init__(self, h):
        self.h = max(1, int(h))
        self.name = f"P2_zthresh_h{self.h}"

    def wants_sync(self, t, z, st, left, horizon, budget):
        return z >= self.h


class MarginRule:
    """Sync when the routing decision is UNCERTAIN (small margin)."""

    def __init__(self, tau):
        self.tau = float(tau)
        self.name = f"P3_margin_tau{self.tau:.5f}"

    def wants_sync(self, t, z, st, left, horizon, budget):
        return st["margin"] <= self.tau


class VoiRule:
    """Sync when the expected gain from a fresh snapshot is LARGE."""

    def __init__(self, tau):
        self.tau = float(tau)
        self.name = f"P4_voi_tau{self.tau:.5f}"

    def wants_sync(self, t, z, st, left, horizon, budget):
        return st["g_hat"] >= self.tau


# --------------------------------------------------------------------------
# evaluation helpers
# --------------------------------------------------------------------------

def evaluate(policy, episodes, worlds, cache, base_seed, budget,
             include_terminal):
    """Run one policy over a set of episodes -> per-episode step-reward arrays."""
    per_ep, used, ages = [], [], []
    for ep in episodes:
        r, u, ag = run_episode(policy, ep, worlds[ep], cache, base_seed,
                               budget, include_terminal)
        per_ep.append(r)
        used.append(u)
        ages.extend(ag)
    return per_ep, float(np.mean(used)), ages


def value_of(per_ep, objective, cvar_alpha, risk_unit):
    """risk_unit='step'    -> risk over pooled per-packet rewards (SLA view)
       risk_unit='episode' -> risk over episode returns (campaign view)"""
    if risk_unit == "episode":
        return aggregate([r.sum() for r in per_ep], objective, cvar_alpha)
    return aggregate(np.concatenate(per_ep), objective, cvar_alpha)


def paired_bootstrap(a_per_ep, b_per_ep, objective, cvar_alpha, risk_unit,
                     n_boot, seed):
    """CI95 for V(a) - V(b), resampling EPISODES (the independent unit).

    Paired, because both policies ran on the same worlds. Bootstrap rather
    than a t-test because CVaR is not a mean and has no closed-form SE.
    """
    rng = np.random.default_rng(seed)
    n = len(a_per_ep)
    diffs = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        da = [a_per_ep[j] for j in idx]
        db = [b_per_ep[j] for j in idx]
        diffs[i] = (value_of(da, objective, cvar_alpha, risk_unit)
                    - value_of(db, objective, cvar_alpha, risk_unit))
    point = (value_of(a_per_ep, objective, cvar_alpha, risk_unit)
             - value_of(b_per_ep, objective, cvar_alpha, risk_unit))
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return float(point), float(lo), float(hi)


def calibrate_tau(stats, key, target_rate, high_is_sync):
    """Threshold whose firing rate on the calibration set matches the budget.

    high_is_sync=True  -> fire when value >= tau  (VoI rule)
    high_is_sync=False -> fire when value <= tau  (margin rule)
    """
    vals = np.asarray([s[key] for s in stats], dtype=np.float64)
    if vals.size == 0:
        return 0.0
    rate = float(min(0.95, max(0.01, target_rate)))
    q = (1.0 - rate) * 100.0 if high_is_sync else rate * 100.0
    return float(np.percentile(vals, q))


# --------------------------------------------------------------------------
# provenance
# --------------------------------------------------------------------------

def _sha12(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()[:12]
    except OSError:
        return "unavailable"


def _git_hash():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unavailable"


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Phase 14B RQ0'/RQ0'' trajectory sync pilot")
    p.add_argument("--episodes", type=int, default=300,
                   help="evaluation episodes (disjoint from calibration)")
    p.add_argument("--calib-episodes", type=int, default=150,
                   help="episodes used ONLY to pick thresholds")
    p.add_argument("--horizon", type=int, default=T3.EPISODE_LEN)
    p.add_argument("--mc-samples", type=int, default=80,
                   help="Monte Carlo rollouts per belief evaluation")
    p.add_argument("--budget-frac", type=float, nargs="+",
                   default=[0.1, 0.2, 0.3],
                   help="sync budget as a fraction of the horizon")
    p.add_argument("--objective", choices=("mean", "cvar"), default="cvar")
    p.add_argument("--cvar-alpha", type=float, default=0.1)
    p.add_argument("--risk-unit", choices=("step", "episode"), default="step")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--include-terminal", action="store_true",
                   help="keep R_ARRIVED; OFF by default, see docs 14b/00 s.4")
    p.add_argument("--n-boot", type=int, default=2000)
    p.add_argument("--out", default=None)
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    inc_term = bool(args.include_terminal)
    obj, alpha, unit = args.objective, float(args.cvar_alpha), args.risk_unit
    H = int(args.horizon)
    n_calib, n_eval = int(args.calib_episodes), int(args.episodes)

    if obj == "cvar":
        n_tail_unit = n_eval * (H if unit == "step" else 1)
        k = int(alpha * n_tail_unit)
        if k < 20:
            print(f"WARNING: CVaR tail has only {k} samples "
                  f"(risk-unit={unit}); estimate will be very noisy. "
                  f"Increase --episodes or use --risk-unit step.",
                  file=sys.stderr)

    sampler = Sampler3Path()
    calib_eps = list(range(n_calib))
    eval_eps = list(range(n_calib, n_calib + n_eval))

    print(f"pre-generating {n_calib + n_eval} worlds (horizon={H}) ...",
          flush=True)
    worlds = {ep: make_world(args.seed, ep, H) for ep in calib_eps + eval_eps}
    cache = StatsCache(sampler, args.seed, int(args.mc_samples),
                       obj, alpha, inc_term)

    payload = {
        "phase": "14B",
        "question": "RQ0' adaptive-vs-periodic ; RQ0'' adaptive-vs-simple-rule",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_hash": _git_hash(),
        "topology": "routing3",
        "load_cfg": (f"EVENT_3PATH_RATE_{T3.EVENT_RATE}_PROFILE_"
                     f"{os.environ.get('ROUTING3_BAND_PROFILE', 'cliffband')}"),
        "dynamics_source_path": "rl/routing3/topology3.py",
        "dynamics_source_sha": _sha12("rl/routing3/topology3.py"),
        "reward_model_path": "rl/routing3/reward3.py",
        "reward_model_sha": _sha12("rl/routing3/reward3.py"),
        "link_model_path": "rl/routing3/link_model.py",
        "link_model_sha": _sha12("rl/routing3/link_model.py"),
        "estimator": "paired_CRN + split_sample_policy_selection",
        "objective": obj, "cvar_alpha": alpha, "risk_unit": unit,
        "include_terminal": inc_term, "horizon": H,
        "mc_samples": int(args.mc_samples),
        "calib_episodes": n_calib, "eval_episodes": n_eval,
        "seed": int(args.seed),
        "budgets": [],
    }

    for bf in args.budget_frac:
        B = max(1, int(round(bf * H)))
        base_T = max(1, int(round(H / B)))
        print(f"\n=== budget {bf:.2f} -> B = {B} syncs / {H} steps "
              f"(periodic T ~ {base_T}) ===", flush=True)

        # ---- calibration pass: collect the statistic distribution ----
        stats = []
        for ep in calib_eps:
            run_episode(Periodic(base_T), ep, worlds[ep], cache, args.seed,
                        B, inc_term, collect=stats)

        # ---- candidate policies ----
        cands = {"P0_never": Never()}
        for T in sorted({max(1, base_T - 1), base_T, base_T + 1}):
            cands[f"P1_periodic_T{T}"] = Periodic(T)
        for h in sorted({max(1, base_T - 1), base_T, base_T + 1, base_T + 2}):
            cands[f"P2_zthresh_h{h}"] = ZThreshold(h)
        for scale in (0.75, 1.0, 1.5):
            cands[f"P3_margin_s{scale}"] = MarginRule(
                calibrate_tau(stats, "margin", bf * scale, False))
            cands[f"P4_voi_s{scale}"] = VoiRule(
                calibrate_tau(stats, "g_hat", bf * scale, True))

        # ---- pick the best variant of each family ON CALIBRATION ----
        calib_scores = {}
        for key, pol in cands.items():
            per_ep, used, _ = evaluate(pol, calib_eps, worlds, cache,
                                       args.seed, B, inc_term)
            calib_scores[key] = {
                "V": value_of(per_ep, obj, alpha, unit),
                "sync_used": used,
            }

        def best_of(prefix):
            sel = [k for k in calib_scores if k.startswith(prefix)]
            return max(sel, key=lambda k: calib_scores[k]["V"])

        chosen = {
            "never": "P0_never",
            "periodic": best_of("P1_"),
            "zthresh": best_of("P2_"),
            "margin": best_of("P3_"),
            "voi": best_of("P4_"),
        }
        print("  chosen on CALIBRATION:", chosen, flush=True)

        # ---- evaluate on DISJOINT episodes ----
        rets, meta = {}, {}
        for role, key in chosen.items():
            per_ep, used, ages = evaluate(cands[key], eval_eps, worlds, cache,
                                          args.seed, B, inc_term)
            rets[role] = per_ep
            meta[role] = {
                "policy": key,
                "V": value_of(per_ep, obj, alpha, unit),
                "V_mean_step": float(np.concatenate(per_ep).mean()),
                "sync_used_mean": used,
                "sync_age_hist": dict(Counter(ages)),
                "sync_age_mean": float(np.mean(ages)) if ages else 0.0,
            }
            print(f"  {role:<9} {key:<24} V = {meta[role]['V']:+.4f}"
                  f"   syncs = {used:.2f}"
                  f"   mean sync age = {meta[role]['sync_age_mean']:.2f}",
                  flush=True)

        simple_best = max(("periodic", "zthresh", "margin"),
                          key=lambda r: meta[r]["V"])

        g_aoi = paired_bootstrap(rets["voi"], rets["periodic"], obj, alpha,
                                 unit, args.n_boot, args.seed)
        g_rl = paired_bootstrap(rets["voi"], rets[simple_best], obj, alpha,
                                unit, args.n_boot, args.seed)
        g_ref = paired_bootstrap(rets["periodic"], rets["never"], obj, alpha,
                                 unit, args.n_boot, args.seed)

        print(f"  G_AoI (voi - periodic)    = {g_aoi[0]:+.4f}  "
              f"CI95 [{g_aoi[1]:+.4f}, {g_aoi[2]:+.4f}]")
        print(f"  G_RL  (voi - best simple) = {g_rl[0]:+.4f}  "
              f"CI95 [{g_rl[1]:+.4f}, {g_rl[2]:+.4f}]  "
              f"(best simple = {simple_best})")
        print(f"  [ref] (periodic - never)  = {g_ref[0]:+.4f}  "
              f"CI95 [{g_ref[1]:+.4f}, {g_ref[2]:+.4f}]")

        payload["budgets"].append({
            "budget_frac": bf, "B": B, "periodic_T_base": base_T,
            "policies": meta, "best_simple": simple_best,
            "G_AoI": {"point": g_aoi[0], "lo": g_aoi[1], "hi": g_aoi[2]},
            "G_RL": {"point": g_rl[0], "lo": g_rl[1], "hi": g_rl[2],
                     "vs": simple_best},
            "ref_periodic_minus_never": {"point": g_ref[0], "lo": g_ref[1],
                                         "hi": g_ref[2]},
            "calibration_scores": calib_scores,
        })

    payload["cache_hits"] = cache.hits
    payload["cache_misses"] = cache.misses
    print(f"\ncache: {cache.hits} hits / {cache.misses} misses")

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
        print(f"-> wrote {args.out}")
    return payload


if __name__ == "__main__":
    main()