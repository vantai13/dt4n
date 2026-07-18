#!/usr/bin/env bash
# Train five routing DQN seeds on the independent-congestion scenario config.
set -euo pipefail

CONFIG="${1:-rl/routing/configs/train_r_scenario.yaml}"
EPISODES="${2:-2000}"
OUT_ROOT="${3:-results/train_scenario}"
PRINT_EVERY="${4:-10}"
LOG_DIR="${LOG_DIR:-docs/phase-9/artifacts/logs}"

mkdir -p "$LOG_DIR"

if ! git diff-index --quiet HEAD -- || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    echo "ERROR: working tree is dirty; train_r.py would mark runs as dirty." >&2
    echo "Commit the scenario/dashboard changes first, then rerun this script." >&2
    exit 1
fi

if ! git check-ignore -q "$OUT_ROOT/.probe"; then
    echo "ERROR: OUT_ROOT is not ignored by git: $OUT_ROOT" >&2
    echo "Generated files from seed 0 would make seed 1 look dirty." >&2
    echo "Use the default OUT_ROOT or add your custom OUT_ROOT to .gitignore." >&2
    exit 1
fi

echo "[5seed] git=$(git rev-parse --short HEAD)"
echo "[5seed] config=$CONFIG episodes=$EPISODES out_root=$OUT_ROOT print_every=$PRINT_EVERY"

for seed in 0 1 2 3 4; do
    echo ""
    echo "==================== TRAIN SEED $seed ===================="
    python -m rl.routing.train_r \
        --config "$CONFIG" \
        --seed "$seed" \
        --episodes "$EPISODES" \
        --out-root "$OUT_ROOT" \
        --print-every "$PRINT_EVERY" \
        2>&1 | tee "$LOG_DIR/train_scenario_seed${seed}.log"

    run_dir="$(find "$OUT_ROOT" -maxdepth 1 -type d -name "r_seed${seed}_*" -printf '%T@ %p\n' \
        | sort -nr \
        | head -n 1 \
        | cut -d' ' -f2-)"
    if [ -z "$run_dir" ]; then
        echo "ERROR: could not find run directory for seed $seed in $OUT_ROOT" >&2
        exit 1
    fi

    echo ""
    echo "==================== DASHBOARD SEED $seed ===================="
    python scripts/plot_training.py "$run_dir" \
        2>&1 | tee "$LOG_DIR/dashboard_scenario_seed${seed}.log"
done

echo ""
echo "==================== FIVE-SEED DASHBOARD ===================="
python scripts/plot_training.py \
    --runs-glob "$OUT_ROOT/r_seed*" \
    --out "$OUT_ROOT/dashboard_5seed.png" \
    2>&1 | tee "$LOG_DIR/dashboard_scenario_5seed.log"

echo ""
echo "[5seed] complete"
echo "[5seed] per-seed dashboards: $OUT_ROOT/r_seed*/dashboard.png"
echo "[5seed] aggregate dashboard: $OUT_ROOT/dashboard_5seed.png"
echo "[5seed] logs: $LOG_DIR/train_scenario_seed*.log"
