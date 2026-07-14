#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/pack-conda-envs.sh [env ...]

Dong goi nguyen Conda env thanh tar.gz bang conda-pack.
Can nhieu dung luong local hon export YAML, nen chi dung khi ban muon copy gan nhu y nguyen env.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUT_DIR="${OUT_DIR:-$ROOT_DIR/cloud/aws-ec2/conda-packs}"
ENVS=("$@")
if [ "${#ENVS[@]}" -eq 0 ]; then
  ENVS=(sdn_net sdn_rl)
fi

if ! command -v conda-pack >/dev/null 2>&1; then
  echo "== Cai conda-pack vao base =="
  conda install -y -n base -c conda-forge conda-pack
fi

mkdir -p "$OUT_DIR"

for env_name in "${ENVS[@]}"; do
  if ! conda env list | awk '{print $1}' | grep -qx "$env_name"; then
    echo "ERROR: Khong thay Conda env: $env_name" >&2
    exit 1
  fi

  echo "== Pack $env_name =="
  conda-pack -n "$env_name" -o "$OUT_DIR/$env_name.tar.gz" --force
done

echo "Pack xong: $OUT_DIR"
