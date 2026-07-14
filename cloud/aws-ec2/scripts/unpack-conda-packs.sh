#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/unpack-conda-packs.sh [env ...]

Chay tren EC2 sau khi sync project. Script giai nen cac pack trong cloud/aws-ec2/conda-packs
vao Miniforge/Miniconda, roi chay conda-unpack.

Bien huu ich:
  REPLACE_EXISTING=1  xoa env cu roi giai nen lai
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PACK_DIR="${PACK_DIR:-$ROOT_DIR/cloud/aws-ec2/conda-packs}"

if [ -f "$HOME/miniforge3/etc/profile.d/conda.sh" ]; then
  # shellcheck disable=SC1091
  source "$HOME/miniforge3/etc/profile.d/conda.sh"
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
  # shellcheck disable=SC1091
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
else
  echo "ERROR: Khong thay conda.sh. Kiem tra Miniforge/Miniconda tren EC2." >&2
  exit 1
fi

CONDA_BASE="$(conda info --base)"
ENVS_DIR="$CONDA_BASE/envs"

ENVS=("$@")
if [ "${#ENVS[@]}" -eq 0 ]; then
  mapfile -t ENVS < <(find "$PACK_DIR" -maxdepth 1 -name '*.tar.gz' -printf '%f\n' | sed 's/\.tar\.gz$//' | sort)
fi

if [ "${#ENVS[@]}" -eq 0 ]; then
  echo "ERROR: Khong thay pack trong $PACK_DIR" >&2
  exit 1
fi

mkdir -p "$ENVS_DIR"

for env_name in "${ENVS[@]}"; do
  pack_file="$PACK_DIR/$env_name.tar.gz"
  target_dir="$ENVS_DIR/$env_name"

  if [ ! -f "$pack_file" ]; then
    echo "ERROR: Thieu $pack_file" >&2
    exit 1
  fi

  if [ -d "$target_dir" ]; then
    if [ "${REPLACE_EXISTING:-0}" = "1" ]; then
      rm -rf "$target_dir"
    else
      echo "== Skip $env_name: $target_dir da ton tai. Dung REPLACE_EXISTING=1 de thay the. =="
      continue
    fi
  fi

  echo "== Unpack $env_name =="
  mkdir -p "$target_dir"
  tar -xzf "$pack_file" -C "$target_dir"
  "$target_dir/bin/conda-unpack" || true
done

conda env list
