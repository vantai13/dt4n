#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/export-conda-envs.sh [env ...]

Mac dinh export 2 env local cua DT4N: sdn_net va sdn_rl.
Ket qua nam trong cloud/aws-ec2/conda-envs:
  ENV-full.yml      - full Conda spec, khong co build string
  ENV-minimal.yml   - chi cac package ban cai truc tiep
  ENV-pip.txt       - pip freeze trong env
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUT_DIR="${OUT_DIR:-$ROOT_DIR/cloud/aws-ec2/conda-envs}"
ENVS=("$@")
if [ "${#ENVS[@]}" -eq 0 ]; then
  ENVS=(sdn_net sdn_rl)
fi

mkdir -p "$OUT_DIR"

for env_name in "${ENVS[@]}"; do
  if ! conda env list | awk '{print $1}' | grep -qx "$env_name"; then
    echo "ERROR: Khong thay Conda env: $env_name" >&2
    exit 1
  fi

  echo "== Export $env_name =="
  conda env export -n "$env_name" --no-builds | grep -v '^prefix:' >"$OUT_DIR/$env_name-full.yml"
  conda env export -n "$env_name" --from-history | grep -v '^prefix:' >"$OUT_DIR/$env_name-minimal.yml"
  conda run -n "$env_name" python -m pip freeze >"$OUT_DIR/$env_name-pip.txt" || true
done

echo "Export xong: $OUT_DIR"
