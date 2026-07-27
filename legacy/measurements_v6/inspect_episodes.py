#!/usr/bin/env python3
"""Phase 10.1 — soi per-episode: nhìn cancellation của voi_headroom.

In mỗi episode: scenario, đường của blind/ospf/clairvoyant, return, ai thắng.
Rồi tổng hợp 3 mức headroom (max-of-mean / mean-of-max / per-scenario).
"""
import numpy as np
from rl.routing_2path.metrics_r import run_episode
from rl.routing_2path.oracles import blind_dijkstra, clairvoyant_dijkstra, posthoc_dijkstra
from rl.routing_2path.baselines import ospf_calibrated
from rl.routing_2path.route_env import RouteEnv
from rl.routing_2path.staleness_r import StalenessWrapper
from rl.routing_2path.topology_r import TOPO, LOAD_CFG_SWEEP

Z = 12
N = 40
DEBUG_SEEDS = [7, 39, 13, 9, 1, 36, 2]

LC = LOAD_CFG_SWEEP


def _fmt(value, digits=3):
    if value is None:
        return "?"
    return f"{float(value):.{digits}f}"


def _valid_action(env, info, action):
    valid = np.flatnonzero(info['valid_mask'])
    if len(valid) == 0:
        return 0
    action = int(action)
    return action if action in set(valid.tolist()) else int(valid[0])


def action_to_hop(env, info, action):
    node = info['current_node']
    neighbors = env.adj[node]
    action = int(action)
    if 0 <= action < len(neighbors):
        return neighbors[action]
    return f"invalid:{action}"


def path_text(row):
    return "-".join(row.get('path', []))


def run_one(policy_fn, seed, z):
    base = RouteEnv(TOPO, load_cfg=LC, max_steps=15, seed=seed)
    env = StalenessWrapper(base, z_steps_choices=(z,))
    stats = run_episode(env, policy_fn, seed=seed, target_fn=posthoc_dijkstra)
    row = stats.as_dict()
    row['return'] = row['total_reward']
    row['scenario_name'] = base._load_scenario
    return row


def independent_rollouts(seed, z):
    rows = {
        'Blind': run_one(blind_dijkstra, seed, z),
        'OSPF': run_one(ospf_calibrated, seed, z),
        'Clair': run_one(clairvoyant_dijkstra, seed, z),
    }
    print("Independent rollouts (same seed, separate envs):")
    for name in ('Blind', 'OSPF', 'Clair'):
        row = rows[name]
        print(
            f"  {name:<5} return={row['return']:>7.3f} "
            f"steps={row['steps']:>2} path={path_text(row)}"
        )
    return rows


def print_link_metrics(env, info):
    node = info['current_node']
    neighbors = env.adj[node]
    true_off = info.get('rho_offered_snapshot', {})
    stale_off = info.get('rho_offered_snapshot_observed', {})
    true_rho = info.get('rho_snapshot', {})
    stale_rho = info.get('rho_snapshot_observed', {})
    true_loss = info.get('loss_snapshot', {})
    stale_loss = info.get('loss_snapshot_observed', {})

    print("  candidate links:")
    for idx, nb in enumerate(neighbors):
        link = (node, nb)
        valid = "*" if info['valid_mask'][idx] > 0.5 else " "
        print(
            f"    {valid} {node}->{nb:<3} "
            f"off_true={_fmt(true_off.get(link))} "
            f"off_stale={_fmt(stale_off.get(link))} "
            f"rho_true={_fmt(true_rho.get(link))} "
            f"rho_stale={_fmt(stale_rho.get(link))} "
            f"loss_true={_fmt(true_loss.get(link))} "
            f"loss_stale={_fmt(stale_loss.get(link))}"
        )


def debug_blind_same_state(seed, z):
    base = RouteEnv(TOPO, load_cfg=LC, max_steps=15, seed=seed)
    env = StalenessWrapper(base, z_steps_choices=(z,))
    _obs, info = env.reset(seed=seed)
    total = 0.0
    path = [info['current_node']]

    print("\nSame-state action probe on Blind trajectory:")
    print("  At each state: ask Clair/Blind/OSPF, then execute Blind.")

    for step_idx in range(env.max_steps + 1):
        actions = {
            'Clair': clairvoyant_dijkstra(env, info),
            'Blind': blind_dijkstra(env, info),
            'OSPF': ospf_calibrated(env, info),
        }
        hops = {
            name: action_to_hop(env, info, action)
            for name, action in actions.items()
        }
        exec_action = _valid_action(env, info, actions['Blind'])
        exec_hop = action_to_hop(env, info, exec_action)
        diverged = len(set(hops.values())) > 1
        diverge_mark = "  <-- policies differ" if diverged else ""

        print(
            f"\n  step={step_idx} node={info['current_node']} "
            f"scenario={info.get('load_scenario')} "
            f"aoi={_fmt(info.get('aoi_measured_s'), 1)}s "
            f"stale={info.get('util_is_stale')}{diverge_mark}"
        )
        print_link_metrics(env, info)
        for name in ('Clair', 'Blind', 'OSPF'):
            print(
                f"  {name:<5} -> {hops[name]:<3} "
                f"(action={int(actions[name])})"
            )

        _obs, reward, terminated, truncated, info = env.step(exec_action)
        total += float(reward)
        path.append(info['current_node'])
        print(
            f"  EXEC Blind -> {exec_hop:<3} reward={float(reward):>+.4f} "
            f"next={info['current_node']} "
            f"arrived={info.get('arrived')} truncated={truncated}"
        )
        if terminated or truncated:
            break

    print("\nBlind trajectory from same-state probe:")
    print(f"  path={path_text({'path': path})}")
    print(f"  return={total:.3f}")


print(f"{'seed':>4} {'scenario':<18} {'blind':>7} {'ospf':>7} {'clair':>7} "
      f"{'o-b':>7} {'winner':>7} {'path_blind':<22} {'path_ospf':<22}")
print("-" * 118)

blind_rs, ospf_rs, clair_rs = [], [], []
per_scen = {}
episode_rows = []

for seed in range(N):
    rb = run_one(blind_dijkstra, seed, Z)
    ro = run_one(ospf_calibrated, seed, Z)
    rc = run_one(clairvoyant_dijkstra, seed, Z)
    b, o, c = rb['return'], ro['return'], rc['return']
    sc = rb.get('scenario_name', '?')
    pb = path_text(rb)[:22]
    po = path_text(ro)[:22]
    winner = 'OSPF' if o > b else 'blind'
    flag = '  <<<' if o > b else ''      # đánh dấu episode OSPF thắng blind
    print(f"{seed:>4} {sc:<18} {b:>7.3f} {o:>7.3f} {c:>7.3f} "
          f"{o-b:>+7.3f} {winner:>7} {pb:<22} {po:<22}{flag}")
    blind_rs.append(b); ospf_rs.append(o); clair_rs.append(c)
    per_scen.setdefault(sc, []).append((b, o, c))
    episode_rows.append((seed, sc, b, o, c, rb, ro, rc))

blind_rs = np.array(blind_rs); ospf_rs = np.array(ospf_rs); clair_rs = np.array(clair_rs)

print("\n" + "=" * 60)
print("BA MỨC HEADROOM (điều bạn phát hiện):")
h_maxmean = max(blind_rs.mean(), ospf_rs.mean()) - blind_rs.mean()
h_meanmax = np.mean(np.maximum(blind_rs, ospf_rs) - blind_rs)
print(f"  (1) max(mean)  [HIỆN TẠI, bảo thủ]  = {h_maxmean:.4f}")
print(f"  (2) mean(max)  [per-episode, TRẦN]  = {h_meanmax:.4f}")
print(f"  cost_of_blindness = clair - blind    = {clair_rs.mean()-blind_rs.mean():.4f}")
print(f"  P(Blind > Clair-fresh-Dijkstra)       = {np.mean(blind_rs > clair_rs):.3f}")
print(f"  P(OSPF  > Clair-fresh-Dijkstra)       = {np.mean(ospf_rs > clair_rs):.3f}")

print("\nPER-SCENARIO (nơi tín hiệu sống):")
for sc, rows in sorted(per_scen.items()):
    arr = np.array(rows)
    b_m, o_m = arr[:, 0].mean(), arr[:, 1].mean()
    h = max(b_m, o_m) - b_m
    h_meanmax_sc = np.mean(np.maximum(arr[:, 0], arr[:, 1]) - arr[:, 0])
    n_ospf_wins = int((arr[:, 1] > arr[:, 0]).sum())
    n_blind_gt_clair = int((arr[:, 0] > arr[:, 2]).sum())
    n_ospf_gt_clair = int((arr[:, 1] > arr[:, 2]).sum())
    print(f"  {sc:<18} n={len(rows):>2}  blind={b_m:.3f} ospf={o_m:.3f} "
          f"max(mean)={h:.4f} mean(max)={h_meanmax_sc:.4f} "
          f"OSPF thắng {n_ospf_wins}/{len(rows)} ep "
          f"Blind>Clair {n_blind_gt_clair}/{len(rows)} "
          f"OSPF>Clair {n_ospf_gt_clair}/{len(rows)}")

print("\n" + "=" * 60)
print(f"DETAILED DEBUG SEEDS at z={Z}: {DEBUG_SEEDS}")
print("Nhóm này gồm OSPF thắng mạnh, Blind thắng mạnh, và gần hòa.")
for seed in DEBUG_SEEDS:
    row = next((item for item in episode_rows if item[0] == seed), None)
    if row is None:
        print(f"\nSeed {seed}: ngoài N={N}, bỏ qua")
        continue
    _seed, sc, b, o, c, _rb, _ro, _rc = row
    print("\n" + "-" * 118)
    print(
        f"SEED {seed} | {sc} | z={Z} | "
        f"Blind={b:.3f} OSPF={o:.3f} Clair={c:.3f} "
        f"OSPF-Blind={o-b:+.3f}"
    )
    independent_rollouts(seed, Z)
    debug_blind_same_state(seed, Z)
