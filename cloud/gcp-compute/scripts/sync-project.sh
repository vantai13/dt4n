#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/sync-project.sh ubuntu@GCE_IP [./dt4n-gcp.pem] [/home/ubuntu/dt4n]

Dong bo source DT4N local len GCE VM bang rsync.
Mac dinh script KHONG copy secret (.env, *.pem, private key) va KHONG copy thu muc nang.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ] || [ $# -lt 1 ]; then
  usage
  exit 0
fi

REMOTE="$1"
SSH_KEY="${2:-}"
REMOTE_DIR="${3:-/home/ubuntu/dt4n}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

SSH_CMD=(ssh -o StrictHostKeyChecking=accept-new)
if [ -n "$SSH_KEY" ]; then
  SSH_CMD+=(-i "$SSH_KEY")
fi

"${SSH_CMD[@]}" "$REMOTE" "mkdir -p '$REMOTE_DIR'"

RSYNC_EXCLUDES=(
  --exclude ".git/"
  --exclude ".terraform/"
  --exclude "terraform.tfstate"
  --exclude "terraform.tfstate.*"
  --exclude "terraform.tfvars"
  --exclude "node_modules/"
  --exclude "__pycache__/"
  --exclude ".pytest_cache/"
  --exclude ".mypy_cache/"
  --exclude ".ruff_cache/"
  --exclude ".venv/"
  --exclude "venv/"
  --exclude "*.pem"
  --exclude "*.key"
  --exclude ".env"
  --exclude ".env.*"
)

# Mac dinh bo qua runs/ vi co the rat nang. Neu muon copy ca ket qua train:
#   INCLUDE_RUNS=1 ./scripts/sync-project.sh ubuntu@IP ./dt4n-gcp.pem
if [ "${INCLUDE_RUNS:-0}" != "1" ]; then
  RSYNC_EXCLUDES+=(--exclude "runs/")
fi

rsync -az --delete --info=progress2 \
  -e "${SSH_CMD[*]}" \
  "${RSYNC_EXCLUDES[@]}" \
  "$ROOT_DIR/" \
  "$REMOTE:$REMOTE_DIR/"

"${SSH_CMD[@]}" "$REMOTE" "cd '$REMOTE_DIR' && if [ -f dashboard/package-lock.json ]; then npm ci --prefix dashboard; fi"

cat <<EOF
Sync xong: $REMOTE:$REMOTE_DIR

Goi y kiem tra:
  ssh ${SSH_KEY:+-i "$SSH_KEY" }$REMOTE
  cd $REMOTE_DIR
  source ~/miniforge3/etc/profile.d/conda.sh
  conda activate sdn_rl
  PYTHONPATH=\$PWD python -m pytest test -q
EOF
