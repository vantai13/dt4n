#!/usr/bin/env bash
# [9.4] Train five routing DQN agent seeds sequentially.
set -euo pipefail

CONFIG="${1:-rl/routing/configs/train_r_v1.yaml}"
EPISODES="${2:-500}"
OUT_ROOT="${3:-results/train}"
LOG_DIR="docs/phase-9/artifacts/logs"

# *.log is ignored by .gitignore, so tee logs do not make train_r.py mark the
# run dirty after this preflight check passes.
mkdir -p "$LOG_DIR"

if ! git diff-index --quiet HEAD -- || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    echo "ERROR: working tree is dirty; train_r.py would mark runs as dirty." >&2
    echo "Commit first, then rerun this script for the real 5-seed train." >&2
    exit 1
fi

echo "working tree clean, git=$(git rev-parse --short HEAD)"
echo "config=$CONFIG episodes=$EPISODES out_root=$OUT_ROOT"

for seed in 0 1 2 3 4; do
    echo ""
    echo "==================== SEED $seed ===================="
    python3 rl/routing/train_r.py \
        --config "$CONFIG" \
        --seed "$seed" \
        --episodes "$EPISODES" \
        --out-root "$OUT_ROOT" \
        2>&1 | tee "$LOG_DIR/train_seed${seed}.log"
done

echo ""
echo "5 seeds complete. Analyze with:"
echo "  python3 scripts/analyze_5seed.py --runs-glob '${OUT_ROOT}/r_seed*'"
