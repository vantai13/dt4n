#!/usr/bin/env python3
"""Freeze trained routing policies with provenance and behavioral gates.

Examples:
    python scripts/freeze_policies.py --runs results/train_scenario --version v1
    python scripts/freeze_policies.py --runs results/train_scenario --version v1 --force
"""

import argparse
import glob
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone

sys.path.insert(0, '.')

from rl.agent.dqn_agent import DQNAgent  # noqa: E402
from rl.routing.route_env import RouteEnv  # noqa: E402
from rl.routing.state_r import MAX_NEIGHBORS, R_STATE_DIM  # noqa: E402
from rl.routing.topology_r import SCENARIOS_TRAIN, TOPO_V2  # noqa: E402


REQUIRED_SEEDS = (0, 1, 2, 3, 4)
COPY_FILES = ('train.json', 'eval.csv', 'episodes.csv')


def read_json(path):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def write_json(path, payload):
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write('\n')


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def infer_seed(meta, run_dir):
    if 'agent_seed' in meta:
        return int(meta['agent_seed'])
    name = os.path.basename(os.path.normpath(run_dir))
    if name.startswith('r_seed'):
        return int(name.split('_', 1)[0].replace('r_seed', ''))
    raise ValueError('cannot infer agent seed from %s' % run_dir)


def latest_run_dirs(runs_root, required_seeds=REQUIRED_SEEDS):
    """Return the latest complete run for each required agent seed."""
    by_seed = {}
    pattern = os.path.join(runs_root, 'r_seed*')
    for run_dir in sorted(glob.glob(pattern)):
        if not os.path.isdir(run_dir):
            continue
        train_json = os.path.join(run_dir, 'train.json')
        model_path = os.path.join(run_dir, 'model.pt')
        if not os.path.exists(train_json) or not os.path.exists(model_path):
            continue
        meta = read_json(train_json)
        seed = infer_seed(meta, run_dir)
        by_seed.setdefault(seed, []).append((run_dir, meta))

    selected = []
    missing = []
    for seed in required_seeds:
        candidates = by_seed.get(seed, [])
        if not candidates:
            missing.append(seed)
            continue
        candidates.sort(
            key=lambda item: os.path.getmtime(os.path.join(item[0], 'train.json')),
            reverse=True,
        )
        selected.append(candidates[0])
    if missing:
        raise SystemExit(
            'missing complete run(s) for seed(s): %s under %s'
            % (', '.join(str(seed) for seed in missing), runs_root)
        )
    return selected


def load_agent(model_path, cfg):
    agent = DQNAgent(R_STATE_DIM, MAX_NEIGHBORS, cfg)
    agent.load(model_path)
    agent.main_net.eval()
    agent.target_net.eval()
    return agent


def e_usage(agent, scenario_cfg, max_steps, n_episodes=20, seed0=700):
    used_e = 0
    returns = []
    for offset in range(int(n_episodes)):
        seed = int(seed0) + offset
        env = RouteEnv(
            TOPO_V2,
            load_cfg=scenario_cfg,
            max_steps=max_steps,
            seed=seed,
        )
        obs, info = env.reset(seed=seed)
        done = False
        total = 0.0
        while not done:
            action = agent.select_action(
                obs,
                epsilon=0.0,
                valid_mask=env.valid_mask(),
            )
            obs, reward, terminated, truncated, info = env.step(action)
            total += float(reward)
            done = bool(terminated or truncated)
        used_e += int('E' in info['path'])
        returns.append(total)
    return used_e / max(int(n_episodes), 1), float(sum(returns) / len(returns))


def audit_model(model_path, cfg, n_episodes):
    agent = load_agent(model_path, cfg)
    max_steps = int(cfg['env']['max_steps'])
    rows = {}
    for name, scenario_cfg in SCENARIOS_TRAIN.items():
        usage, mean_return = e_usage(
            agent,
            scenario_cfg,
            max_steps=max_steps,
            n_episodes=n_episodes,
        )
        rows[name] = {
            'E_usage': round(float(usage), 6),
            'return': round(float(mean_return), 6),
        }
    delta = rows['S1_viaE_better']['E_usage'] - rows['S2_direct_better']['E_usage']
    return rows, round(float(delta), 6)


def validate_runs(selected, delta_min, audit_episodes):
    config_hashes = set()
    git_hashes = set()
    audited = []
    all_ok = True

    for run_dir, meta in selected:
        seed = infer_seed(meta, run_dir)
        run_id = meta.get('run_id', os.path.basename(run_dir))
        model_path = os.path.join(run_dir, 'model.pt')
        cfg = meta.get('config')
        if not cfg:
            raise SystemExit('run %s has no config in train.json' % run_dir)

        dirty = 'dirty' in run_id or 'dirty' in str(meta.get('git_hash', ''))
        e_usage_rows, delta = audit_model(model_path, cfg, audit_episodes)
        audit_pass = (not dirty) and delta >= float(delta_min)
        all_ok = all_ok and audit_pass

        config_hashes.add(meta.get('config_hash'))
        git_hashes.add(meta.get('git_hash'))

        row = {
            'seed': seed,
            'run_dir': run_dir,
            'run_id': run_id,
            'git_hash': meta.get('git_hash'),
            'config_hash': meta.get('config_hash'),
            'model_sha256': sha256_file(model_path),
            'train_json_sha256': sha256_file(os.path.join(run_dir, 'train.json')),
            'state_dim': int(meta.get('state_dim', R_STATE_DIM)),
            'action_dim': int(meta.get('action_dim', MAX_NEIGHBORS)),
            'audit_episodes': int(audit_episodes),
            'audit_seed0': 700,
            'E_usage': e_usage_rows,
            'delta_S1_S2': delta,
            'dirty': dirty,
            'audit_pass': audit_pass,
        }
        audited.append((run_dir, meta, row))

        status = 'PASS' if audit_pass else 'FAIL'
        dirty_text = ' DIRTY' if dirty else ''
        print(
            'seed %d: delta=%.2f %s%s run=%s'
            % (seed, delta, status, dirty_text, run_id),
            flush=True,
        )

    if len(config_hashes) != 1:
        all_ok = False
        print('ERROR: config hashes differ: %s' % sorted(config_hashes))
    if len(git_hashes) != 1:
        all_ok = False
        print('ERROR: git hashes differ: %s' % sorted(git_hashes))

    return audited, all_ok


def ensure_output_dir(out_dir, force):
    if os.path.exists(out_dir):
        if not force:
            raise SystemExit(
                '%s already exists; pass --force to replace it' % out_dir
            )
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)


def copy_run_artifacts(run_dir, seed_dir):
    os.makedirs(seed_dir)
    shutil.copy2(os.path.join(run_dir, 'model.pt'), os.path.join(seed_dir, 'model.pt'))
    for name in COPY_FILES:
        src = os.path.join(run_dir, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(seed_dir, name))


def write_readme(out_dir, manifest):
    text = """# Frozen Routing Policies {version}

This directory contains the official Phase 9 frozen routing policies.

- Source runs: `{source_runs}`
- Git hash: `{git_hash}`
- Config hash: `{config_hash}`
- Seeds: `{seeds}`
- Behavioral gate: `delta(S1-S2) >= {delta_min}`

Re-evaluate without training:

```bash
python scripts/evaluate_frozen.py --version {version}
```
""".format(
        version=manifest['version'],
        source_runs=manifest['source_runs'],
        git_hash=manifest['git_hash'],
        config_hash=manifest['config_hash'],
        seeds=', '.join(str(row['seed']) for row in manifest['seeds']),
        delta_min=manifest['delta_min'],
    )
    with open(os.path.join(out_dir, 'README.md'), 'w', encoding='utf-8') as fh:
        fh.write(text)


def freeze(selected, audited, out_dir, version, runs_root, delta_min, audit_episodes):
    first_meta = audited[0][1]
    manifest = {
        'version': version,
        'created_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'source_runs': runs_root,
        'git_hash': first_meta.get('git_hash'),
        'config_hash': first_meta.get('config_hash'),
        'delta_min': float(delta_min),
        'audit_episodes': int(audit_episodes),
        'audit_seed0': 700,
        'state_dim': R_STATE_DIM,
        'action_dim': MAX_NEIGHBORS,
        'seeds': [row for _run_dir, _meta, row in audited],
        'all_pass': True,
    }

    write_json(os.path.join(out_dir, 'manifest.json'), manifest)
    write_json(os.path.join(out_dir, 'config.json'), first_meta['config'])
    write_readme(out_dir, manifest)

    for run_dir, _meta, row in audited:
        copy_run_artifacts(run_dir, os.path.join(out_dir, 'seed%d' % row['seed']))

    # Re-write manifest last so a reader sees it only after seed dirs exist.
    write_json(os.path.join(out_dir, 'manifest.json'), manifest)


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--runs', default='results/train_scenario')
    parser.add_argument('--version', default='v1')
    parser.add_argument('--out', default='frozen_policies')
    parser.add_argument('--delta-min', type=float, default=0.5)
    parser.add_argument('--audit-episodes', type=int, default=20)
    parser.add_argument('--force', action='store_true')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    selected = latest_run_dirs(args.runs)
    audited, all_ok = validate_runs(
        selected,
        delta_min=args.delta_min,
        audit_episodes=args.audit_episodes,
    )
    if not all_ok:
        print('\nfreeze blocked: at least one gate failed')
        return 1

    out_dir = os.path.join(args.out, args.version)
    ensure_output_dir(out_dir, force=bool(args.force))
    freeze(
        selected,
        audited,
        out_dir=out_dir,
        version=args.version,
        runs_root=args.runs,
        delta_min=args.delta_min,
        audit_episodes=args.audit_episodes,
    )
    print('\nfrozen: %s' % out_dir)
    print('manifest: %s' % os.path.join(out_dir, 'manifest.json'))
    print('all_pass = True')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
