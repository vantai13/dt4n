#!/usr/bin/env python3
"""Phase 10.4 mechanism diagnostic.

Products:
  1. A two-panel mechanism figure:
       - normalized wrong_excess and cost_of_blindness
       - blind vs clair safe_path_freq
  2. A CSV table with the mechanism metrics by AoI.
  3. A hand-traced episode where blind_dijkstra diverges from clairvoyance.

This script is diagnostic/reporting code only. It does not modify the frozen
policies or rl.routing.metrics_r.
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

import numpy as np

from rl.routing.metrics_r import (
    SAFE_HOP,
    _valid_action,
    evaluate_z,
    make_env,
    run_episode,
)
from rl.routing.oracles import blind_dijkstra, clairvoyant_dijkstra, posthoc_dijkstra
from rl.routing.topology_r import LOAD_CFG_SWEEP, LOAD_PRESETS


Z_VALUES = (0, 1, 2, 3, 5, 8, 12, 20)
N_SEEDS_CONFIRMATORY = 500
N_SEEDS_QUICK = 60
OUT_DIR = Path("measurements/out")

_LINES: list[str] = []


def log(message: str = "") -> None:
    """Print a line immediately and keep it for the text report."""
    print(message, flush=True)
    _LINES.append(str(message))


def parse_z_values(text: str) -> tuple[int, ...]:
    """Parse a comma-separated z list."""
    return tuple(int(part.strip()) for part in text.split(",") if part.strip())


def safe_norm(values: np.ndarray) -> np.ndarray:
    """Normalize an array by max absolute value while handling all-zero input."""
    values = np.asarray(values, dtype=float)
    denom = float(np.max(np.abs(values))) if values.size else 0.0
    if denom <= 1e-12:
        return np.zeros_like(values)
    return values / denom


def pearson_nonzero_aoi(rows: list[dict]) -> float:
    """Compute Pearson correlation excluding the trivial AoI=0 point."""
    aoi = np.array([row["aoi_mean_s"] for row in rows], dtype=float)
    wrong = np.array([row["wrong_excess"] for row in rows], dtype=float)
    cost = np.array([row["cost_of_blindness"] for row in rows], dtype=float)
    mask = aoi > 0.0
    if int(mask.sum()) < 2:
        return float("nan")
    return float(np.corrcoef(wrong[mask], cost[mask])[0, 1])


def collect_mechanism_rows(z_values: tuple[int, ...], n_seeds: int) -> list[dict]:
    """Run evaluate_z over the registered grid and keep mechanism fields."""
    log("=" * 72)
    log("PART 1 - mechanism curve: wrong_excess <-> cost_of_blindness")
    log("=" * 72)
    log(f"[SWEEP] z={z_values} seeds={n_seeds} load_cfg=LOAD_CFG_SWEEP")

    rows: list[dict] = []
    for z in z_values:
        result = evaluate_z(z, seeds=range(int(n_seeds)), load_cfg=LOAD_CFG_SWEEP)
        row = {
            "z_steps": int(z),
            "aoi_mean_s": float(result["aoi_mean_s"]),
            "wrong_excess": float(result["wrong_excess"]),
            "cost_of_blindness": float(result["cost_of_blindness"]),
            "blind_wrong_rate": float(result["blind_wrong_rate"]),
            "clair_wrong_rate": float(result["clair_wrong_rate"]),
            "blind_safe_path_freq": float(result["blind_safe_path_freq"]),
            "clair_safe_path_freq": float(result["clair_safe_path_freq"]),
            "safe_path_gap_blind_minus_clair": (
                float(result["blind_safe_path_freq"])
                - float(result["clair_safe_path_freq"])
            ),
            "blind_return": float(result["blind_return"]),
            "clair_return": float(result["clair_return"]),
        }
        rows.append(row)
        log(
            f"  z={row['z_steps']:2d} AoI={row['aoi_mean_s']:5.2f}s "
            f"wrong_excess={row['wrong_excess']:.4f} "
            f"CoB={row['cost_of_blindness']:.4f} "
            f"safe(blind)={row['blind_safe_path_freq']:.3f} "
            f"safe(clair)={row['clair_safe_path_freq']:.3f}"
        )

    pearson = pearson_nonzero_aoi(rows)
    log("")
    log(f"Pearson(wrong_excess, cost_of_blindness | AoI>0) = {pearson:.4f}")
    if pearson > 0.9:
        log("Read: the decision-error axis and reward-loss axis move together.")
    else:
        log("Read: the two axes do not move together cleanly; inspect the table.")
    log("")
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    """Write a list of dictionaries to CSV."""
    fieldnames = list(rows[0].keys()) if rows else []
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    log(f"[CSV] wrote {path}")


def make_figure(rows: list[dict], pearson: float, path: Path) -> None:
    """Make the Phase 10.4 mechanism figure."""
    path.parent.mkdir(parents=True, exist_ok=True)
    mpl_config = path.parent / "mplconfig"
    mpl_config.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_config))

    try:
        import matplotlib
    except ModuleNotFoundError:
        log(
            "[FIG] skipped: matplotlib is not installed in this Python env. "
            "Run inside sdn_rl or install matplotlib to create the PNG."
        )
        return

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    aoi = np.array([row["aoi_mean_s"] for row in rows], dtype=float)
    wrong = np.array([row["wrong_excess"] for row in rows], dtype=float)
    cost = np.array([row["cost_of_blindness"] for row in rows], dtype=float)
    blind_safe = np.array(
        [row["blind_safe_path_freq"] for row in rows],
        dtype=float,
    )
    clair_safe = np.array(
        [row["clair_safe_path_freq"] for row in rows],
        dtype=float,
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.2))

    ax1.plot(
        aoi,
        safe_norm(wrong),
        "o-",
        color="crimson",
        label="wrong_excess (normalized)",
    )
    ax1.plot(
        aoi,
        safe_norm(cost),
        "s--",
        color="darkorange",
        label="cost_of_blindness (normalized)",
    )
    ax1.set_xlabel("AoI (s)")
    ax1.set_ylabel("normalized value [0,1]")
    ax1.set_title(
        "Decision errors track reward loss\n"
        f"Pearson(AoI>0) = {pearson:.3f}"
    )
    ax1.grid(alpha=0.3)
    ax1.legend(fontsize=9)

    ax2.plot(
        aoi,
        blind_safe,
        "o-",
        color="crimson",
        label="blind_dijkstra",
    )
    ax2.plot(
        aoi,
        clair_safe,
        "s--",
        color="seagreen",
        label="clairvoyant_dijkstra",
    )
    ax2.set_xlabel("AoI (s)")
    ax2.set_ylabel("safe_path_freq")
    ax2.set_title("Safe-path behavior vs AoI\nPhase 11 anchor metric")
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=9)

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    log(f"[FIG] wrote {path}")


def format_link(link) -> str:
    """Format a tuple link key as SRC->DST."""
    try:
        return f"{link[0]}->{link[1]}"
    except Exception:
        return str(link)


def link_snapshot_rows(info: dict, node: str) -> list[dict]:
    """Compare observed and true offered load for outgoing links at a node."""
    true = info.get("rho_offered_snapshot")
    observed = info.get("rho_offered_snapshot_observed")
    loss_true = info.get("loss_snapshot", {})
    loss_observed = info.get("loss_snapshot_observed", {})
    if not (isinstance(true, dict) and isinstance(observed, dict)):
        return []

    rows = []
    for link, true_value in true.items():
        if not isinstance(link, tuple) or len(link) != 2 or link[0] != node:
            continue
        obs_value = float(observed.get(link, true_value))
        true_value = float(true_value)
        rows.append(
            {
                "link": link,
                "observed_offered": obs_value,
                "true_offered": true_value,
                "delta_true_minus_observed": true_value - obs_value,
                "observed_loss": float(loss_observed.get(link, np.nan)),
                "true_loss": float(loss_true.get(link, np.nan)),
            }
        )
    rows.sort(key=lambda row: abs(row["delta_true_minus_observed"]), reverse=True)
    return rows


def top_global_snapshot_diffs(info: dict, limit: int = 4) -> list[dict]:
    """Return the largest global observed-vs-true offered-load differences."""
    true = info.get("rho_offered_snapshot")
    observed = info.get("rho_offered_snapshot_observed")
    if not (isinstance(true, dict) and isinstance(observed, dict)):
        return []

    rows = []
    for link, true_value in true.items():
        obs_value = float(observed.get(link, true_value))
        true_value = float(true_value)
        rows.append(
            {
                "link": link,
                "observed_offered": obs_value,
                "true_offered": true_value,
                "delta_true_minus_observed": true_value - obs_value,
            }
        )
    rows.sort(key=lambda row: abs(row["delta_true_minus_observed"]), reverse=True)
    return rows[: int(limit)]


def run_policy_summary(policy_fn, z: int, seed: int, load_cfg: dict) -> dict:
    """Run one policy and return the compact stats needed for the trace."""
    env = make_env(z, seed=seed, load_cfg=load_cfg)
    stats = run_episode(
        env,
        policy_fn,
        seed=seed,
        target_fn=posthoc_dijkstra,
    ).as_dict()
    return {
        "total_reward": float(stats["total_reward"]),
        "wrong_rate": float(stats["wrong_rate"]),
        "safe_path_freq": float(stats["safe_path_freq"]),
        "path": list(stats["path"]),
        "arrived": bool(stats["arrived"]),
        "steps": int(stats["steps"]),
    }


def trace_one_episode(
    z: int,
    seed: int,
    load_cfg: dict,
    max_steps: int,
) -> tuple[list[dict], dict, dict]:
    """Trace one blind rollout and record all blind-vs-clair divergences."""
    env = make_env(z, seed=seed, load_cfg=load_cfg, max_steps=max_steps)
    _obs, info = env.reset(seed=seed)
    divergences: list[dict] = []

    for _step in range(max_steps + 1):
        node = info["current_node"]
        valid = np.flatnonzero(info["valid_mask"])
        if len(valid) > 1:
            clair_action = _valid_action(env, info, clairvoyant_dijkstra(env, info))
            blind_action = _valid_action(env, info, blind_dijkstra(env, info))
            if clair_action != blind_action:
                divergences.append(
                    {
                        "step": int(info.get("step", _step)),
                        "node": node,
                        "has_safe_opportunity": SAFE_HOP in env.adj[node],
                        "aoi_s": float(info.get("aoi_measured_s", 0.0)),
                        "clair_hop": env.adj[node][clair_action],
                        "blind_hop": env.adj[node][blind_action],
                        "outgoing": link_snapshot_rows(info, node),
                        "global_diffs": top_global_snapshot_diffs(info),
                    }
                )

        blind_action = _valid_action(env, info, blind_dijkstra(env, info))
        _obs, _reward, terminated, truncated, info = env.step(blind_action)
        if terminated or truncated:
            break

    blind_summary = run_policy_summary(blind_dijkstra, z, seed, load_cfg)
    clair_summary = run_policy_summary(clairvoyant_dijkstra, z, seed, load_cfg)
    return divergences, blind_summary, clair_summary


def handtrace_load_cfg(drift_sigma: float) -> dict:
    """Return the drift-enabled bottleneck_E regime used for hand tracing."""
    cfg = dict(LOAD_PRESETS["bottleneck_E"])
    cfg["drift_sigma"] = float(drift_sigma)
    return cfg


def part2_handtrace(args: argparse.Namespace) -> int | None:
    """Find and log one seed where blind and clair diverge."""
    log("")
    log("=" * 72)
    log("PART 2 - hand-traced episode: blind != clair")
    log("=" * 72)

    cfg = handtrace_load_cfg(args.trace_drift)
    log(
        "Regime: LOAD_PRESETS['bottleneck_E'] with "
        f"drift_sigma={args.trace_drift:.3f}"
    )
    log(
        f"Search: z={args.trace_z} (nominal AoI~{0.5 * args.trace_z:.2f}s), "
        f"seeds=0..{args.max_trace_seed - 1}"
    )

    fallback = None
    for seed in range(int(args.max_trace_seed)):
        divergences, blind, clair = trace_one_episode(
            z=args.trace_z,
            seed=seed,
            load_cfg=cfg,
            max_steps=args.max_steps,
        )
        if not divergences:
            continue

        preferred = [
            row for row in divergences
            if row.get("has_safe_opportunity", False)
        ]
        if not preferred:
            if fallback is None:
                fallback = (seed, divergences, blind, clair)
            continue

        first = preferred[0]
        return _log_trace_hit(seed, args.trace_z, first, divergences, blind, clair)

    if fallback is not None:
        seed, divergences, blind, clair = fallback
        log("")
        log(
            "No divergence at a SAFE_HOP opportunity was found; "
            "falling back to the first blind-vs-clair divergence."
        )
        first = divergences[0]
        return _log_trace_hit(seed, args.trace_z, first, divergences, blind, clair)

    log("")
    log("No blind-vs-clair divergence found. Check whether drift is enabled.")
    return None


def _log_trace_hit(
    seed: int,
    z: int,
    first: dict,
    divergences: list[dict],
    blind: dict,
    clair: dict,
) -> int:
    """Log a selected divergence episode and return its seed."""
    log("")
    log(f">>> EPISODE seed={seed}, z={z} <<<")
    log(
        f"At step={first['step']} node={first['node']} "
        f"AoI={first['aoi_s']:.3f}s:"
    )
    log(f"  clairvoyant next hop: {first['clair_hop']}")
    log(f"  blind next hop:       {first['blind_hop']}")
    log("")
    log("Outgoing offered-load view at the decision node:")
    for row in first["outgoing"]:
        log(
            f"  {format_link(row['link'])}: "
            f"blind_saw={row['observed_offered']:.3f} "
            f"true={row['true_offered']:.3f} "
            f"delta={row['delta_true_minus_observed']:+.3f} "
            f"loss_seen={row['observed_loss']:.3f} "
            f"loss_true={row['true_loss']:.3f}"
        )

    if first["global_diffs"]:
        log("")
        log("Largest global stale-snapshot differences:")
        for row in first["global_diffs"]:
            log(
                f"  {format_link(row['link'])}: "
                f"blind_saw={row['observed_offered']:.3f} "
                f"true={row['true_offered']:.3f} "
                f"delta={row['delta_true_minus_observed']:+.3f}"
            )

    log("")
    log("Episode outcome under the same seed/regime:")
    log(
        f"  blind: reward={blind['total_reward']:.4f} "
        f"wrong_rate={blind['wrong_rate']:.3f} "
        f"safe_path_freq={blind['safe_path_freq']:.3f} "
        f"arrived={blind['arrived']} path={'->'.join(blind['path'])}"
    )
    log(
        f"  clair: reward={clair['total_reward']:.4f} "
        f"wrong_rate={clair['wrong_rate']:.3f} "
        f"safe_path_freq={clair['safe_path_freq']:.3f} "
        f"arrived={clair['arrived']} path={'->'.join(clair['path'])}"
    )
    log(
        f"  reward_gap_clair_minus_blind="
        f"{clair['total_reward'] - blind['total_reward']:.4f}"
    )
    log(f"  total divergence steps in blind rollout: {len(divergences)}")
    return seed


def write_summary(path: Path) -> None:
    """Write the captured log to the text report."""
    with open(path, "w") as handle:
        handle.write("\n".join(_LINES) + "\n")
    log(f"[TXT] wrote {path}")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--quick",
        action="store_true",
        help="use fewer seeds for a smoke test",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=N_SEEDS_CONFIRMATORY,
        help="number of seeds for the mechanism curve",
    )
    parser.add_argument(
        "--z-values",
        default=",".join(str(z) for z in Z_VALUES),
        help="comma-separated z values for Part 1",
    )
    parser.add_argument("--trace-z", type=int, default=3)
    parser.add_argument("--trace-drift", type=float, default=0.30)
    parser.add_argument("--max-trace-seed", type=int, default=500)
    parser.add_argument("--max-steps", type=int, default=15)
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.quick:
        args.seeds = min(args.seeds, N_SEEDS_QUICK)
        args.max_trace_seed = min(args.max_trace_seed, 100)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    z_values = parse_z_values(args.z_values)

    log("### PHASE 10.4 - MECHANISM + HAND TRACE ###")
    log(f"[MODE] {'quick' if args.quick else 'confirmatory'}")
    log("")

    rows = collect_mechanism_rows(z_values, args.seeds)
    pearson = pearson_nonzero_aoi(rows)

    write_csv(rows, out_dir / "mechanism_10_4.csv")
    make_figure(rows, pearson, out_dir / "mechanism_10_4.png")

    seed = part2_handtrace(args)
    log("")
    log(f"[SUMMARY] Pearson={pearson:.4f}; handtrace_seed={seed}")
    write_summary(out_dir / "mechanism_10_4.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
