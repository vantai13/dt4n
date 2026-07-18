"""Xem tay 10 path cua agent + do E_usage_rate theo tai.

Cong cu chan doan Lesson 9.3/9.4. KHONG train gi. Chi load model da co,
cho no chay o 3 muc tai (normal/borderline/bottleneck_E), in path that,
va dem ti le di qua node E.

Chay:
    conda activate sdn_rl
    python scripts/inspect_paths.py <duong_dan_model.pt>
"""
from pathlib import Path
import sys, yaml

from rl.routing.topology_r import TOPO_V2, LOAD_PRESETS
from rl.routing.route_env import RouteEnv
from rl.agent.dqn_agent import DQNAgent
from rl.routing.state_r import R_STATE_DIM, MAX_NEIGHBORS


def load_agent(model_path, cfg_path):
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)
    agent = DQNAgent(R_STATE_DIM, MAX_NEIGHBORS, cfg)
    agent.load(model_path)
    agent.main_net.eval()
    return agent


def run_episode(agent, env):
    """Chay 1 episode voi epsilon=0 (thuan khai thac). Tra path + co qua E."""
    obs, info = env.reset()
    done = False
    while not done:
        mask = env.valid_mask()                                  # (1) mask luc chon
        a = agent.select_action(obs, epsilon=0.0, valid_mask=mask)  # eps=0: eval
        obs, r, term, trunc, info = env.step(a)
        done = term or trunc
    path = info['path']
    return path, ('E' in path)


def measure_preset(agent, load_cfg, n_ep=30, seed0=500):
    used_E, paths = 0, []
    for i in range(n_ep):
        env = RouteEnv(TOPO_V2, load_cfg=load_cfg, max_steps=15, seed=seed0 + i)
        path, e = run_episode(agent, env)
        paths.append(path)
        used_E += int(e)
    uniq = len(set(tuple(p) for p in paths))
    return used_E / n_ep, uniq, paths


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python scripts/inspect_paths.py <duong_dan_model.pt>", file=sys.stderr)
        print(
            "\nVi du:\n"
            "  python scripts/inspect_paths.py "
            "results/train_calib/rev5_ep5000/r_seed0_bdeb2b9-dirty_cf4b675/model.pt",
            file=sys.stderr,
        )
        sys.exit(2)

    model = sys.argv[1]
    if not Path(model).is_file():
        print(f"Khong tim thay model: {model}", file=sys.stderr)
        sys.exit(2)

    cfg = 'rl/routing/configs/train_r_v1.yaml'
    agent = load_agent(model, cfg)
    print(f"Model: {model}\n")
    print(f"{'preset':<14}{'E_usage_rate':>14}{'path_unique':>13}")
    print("-" * 41)
    rates = {}
    for name, lc in LOAD_PRESETS.items():
        e_rate, uniq, paths = measure_preset(agent, lc, n_ep=30)
        rates[name] = e_rate
        print(f"{name:<14}{e_rate:>14.3f}{uniq:>13}")
        if name == 'bottleneck_E':
            print("\n  10 path o bottleneck_E:")
            for p in paths[:10]:
                mark = "  <-- qua E" if 'E' in p else ""
                print("   ", " -> ".join(p) + mark)

    delta = rates['normal'] - rates['bottleneck_E']
    print("\n" + "=" * 50)
    print(f"E_usage(normal)       = {rates['normal']:.3f}")
    print(f"E_usage(bottleneck_E) = {rates['bottleneck_E']:.3f}")
    print(f"delta                 = {delta:.3f}")
    print()
    if abs(delta) < 0.15:
        print(">> E_usage KHONG DOI theo tai => POLICY TINH (khong doc util)")
    else:
        print(">> E_usage doi theo tai => agent CO doc util. Tot.")
