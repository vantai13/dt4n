#!/usr/bin/env bash
# Phase 11.2 - train 2 branches x 5 paired seeds = 10 runs.
set -euo pipefail

cd "$(dirname "$0")/.."

LINK_SHA="$(
  python3 - <<'PY'
import hashlib
print(hashlib.sha256(open('rl/routing/link_model.py', 'rb').read()).hexdigest())
PY
)"
LINK_VERSION="$(cat frozen_policies/v1/link_model_version.txt)"
GIT="$(git rev-parse --short HEAD 2>/dev/null || echo nogit)"

echo "git = ${GIT}"
echo "link_model_version = ${LINK_VERSION}"
echo "link_model_sha256 = ${LINK_SHA}"

for BRANCH in aoi mask; do
  CFG="rl/routing/configs/train_r_ablation_${BRANCH}.yaml"
  OUT="results/ablation/${BRANCH}"
  for SEED in 0 1 2 3 4; do
    echo "=== TRAIN branch=${BRANCH} seed=${SEED} ==="
    python3 -m rl.routing.train_r \
      --config "${CFG}" \
      --seed "${SEED}" \
      --out-root "${OUT}" \
      --print-every 200

    RUN_DIR="$(ls -dt "${OUT}"/r_seed"${SEED}"_* | head -1)"
    python3 - "${RUN_DIR}" "${LINK_SHA}" "${LINK_VERSION}" "${BRANCH}" <<'PY'
import json
import os
import sys

run_dir, link_sha, link_version, branch = sys.argv[1:5]
path = os.path.join(run_dir, "train.json")
with open(path) as handle:
    payload = json.load(handle)

payload["ablation_branch"] = branch
payload["link_model_sha256"] = link_sha
payload["link_model_version"] = link_version

with open(path, "w") as handle:
    json.dump(payload, handle, indent=2)

print(f"  manifest updated: {path}")
PY
  done
done

echo "DONE 10 runs."
