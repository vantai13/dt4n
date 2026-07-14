#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/restore-conda-envs.sh [env ...]

Chay tren EC2 sau khi sync project. Script tao lai Conda env tu cloud/aws-ec2/conda-envs.

Bien huu ich:
  UPDATE_EXISTING=1  cap nhat env da ton tai thay vi bo qua
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
EXPORT_DIR="${EXPORT_DIR:-$ROOT_DIR/cloud/aws-ec2/conda-envs}"

sanitize_pip_requirements() {
  local input_file="$1"
  local output_file="$2"

  awk '
    /^[[:space:]]*$/ { next }
    /^[[:space:]]*#/ { next }
    /[[:space:]]@ file:\/\// { next }
    /^-e[[:space:]]/ { next }
    /^mininet([[:space:]@=<>!]|$)/ { next }
    /^ryu==/ { next }
    /^torch==.*\+cu/ { next }
    /^torchaudio==.*\+cu/ { next }
    /^torchvision==.*\+cu/ { next }
    /^torch_scatter==.*\+/ { next }
    /^torch_sparse==.*\+/ { next }
    { print }
  ' "$input_file" >"$output_file"
}

install_ryu_workaround() {
  local env_name="$1"

  echo "== Ryu workaround $env_name =="
  conda run -n "$env_name" python -m pip install --upgrade \
    pip==23.3.2 setuptools==57.5.0 wheel
  conda run -n "$env_name" python -m pip install --no-build-isolation ryu==4.34
  conda run -n "$env_name" python -m pip install \
    eventlet==0.30.2 dnspython==1.16.0 greenlet==2.0.2
}

install_cpu_torch_if_needed() {
  local env_name="$1"
  local pip_file="$2"

  if grep -Eq '^(torch|torchaudio|torchvision)==.*\+cu' "$pip_file"; then
    echo "== Install CPU PyTorch for $env_name =="
    conda run -n "$env_name" python -m pip install torch \
      --index-url https://download.pytorch.org/whl/cpu
  fi
}

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

ENVS=("$@")
if [ "${#ENVS[@]}" -eq 0 ]; then
  mapfile -t ENVS < <(find "$EXPORT_DIR" -maxdepth 1 -name '*-full.yml' -printf '%f\n' | sed 's/-full\.yml$//' | sort)
fi

if [ "${#ENVS[@]}" -eq 0 ]; then
  echo "ERROR: Khong thay file export trong $EXPORT_DIR" >&2
  exit 1
fi

for env_name in "${ENVS[@]}"; do
  full_file="$EXPORT_DIR/$env_name-full.yml"
  minimal_file="$EXPORT_DIR/$env_name-minimal.yml"
  pip_file="$EXPORT_DIR/$env_name-pip.txt"

  if [ ! -f "$full_file" ]; then
    echo "ERROR: Thieu $full_file" >&2
    exit 1
  fi

  if conda env list | awk '{print $1}' | grep -qx "$env_name"; then
    if [ "${UPDATE_EXISTING:-0}" = "1" ]; then
      echo "== Update existing env $env_name =="
      conda env update -n "$env_name" -f "$full_file" --prune
    else
      echo "== Skip $env_name: env da ton tai. Dung UPDATE_EXISTING=1 de update. =="
      continue
    fi
  else
    echo "== Restore $env_name tu full export =="
    if ! conda env create -f "$full_file"; then
      echo "WARN: full export loi; thu minimal + pip cho $env_name"
      conda env remove -n "$env_name" -y || true
      if [ ! -f "$minimal_file" ]; then
        echo "ERROR: Thieu $minimal_file" >&2
        exit 1
      fi
      conda env create -f "$minimal_file"
    fi
  fi

  if [ -s "$pip_file" ]; then
    clean_pip_file="$(mktemp)"
    sanitize_pip_requirements "$pip_file" "$clean_pip_file"

    if grep -Eq '^ryu==' "$pip_file"; then
      install_ryu_workaround "$env_name"
    fi

    if [ -s "$clean_pip_file" ]; then
      echo "== Pip sync $env_name =="
      conda run -n "$env_name" python -m pip install -r "$clean_pip_file"
    fi

    install_cpu_torch_if_needed "$env_name" "$pip_file"
    rm -f "$clean_pip_file"
  fi
done

conda env list
