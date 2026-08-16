#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/sync-ditto-deployment.sh ubuntu@GCE_IP [./dt4n-gcp.pem] [/home/ubuntu/tools/ditto]

Dong bo checkout Eclipse Ditto hien tai len GCE VM. Mac dinh lay tu:
  LOCAL_DITTO_DIR=$HOME/tools/ditto

Script sync ca source Ditto can cho deployment/docker, bo qua .git va thu muc build nang,
roi so sanh SHA-256 cua toan bo deployment/docker/* giua local va remote.

Bien huu ich:
  LOCAL_DITTO_DIR=/path/to/ditto  chon checkout Ditto local khac
  START_DITTO=1                  chay docker compose up -d sau khi sync
  CLEAN_DITTO=1                  down/up sach de tranh Pekko cluster giu node cu
  COMPOSE_PROJECT=dt4n-aoi-smoke dung project name dang chay tren GCP
  DITTO_VERSION=3.9.1            pin image tag khi can giu benchmark co dinh
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ] || [ $# -lt 1 ]; then
  usage
  exit 0
fi

REMOTE="$1"
SSH_KEY="${2:-}"
REMOTE_DIR="${3:-/home/ubuntu/tools/ditto}"
LOCAL_DITTO_DIR="${LOCAL_DITTO_DIR:-$HOME/tools/ditto}"
START_DITTO="${START_DITTO:-0}"
CLEAN_DITTO="${CLEAN_DITTO:-0}"
COMPOSE_PROJECT="${COMPOSE_PROJECT:-ditto}"
DITTO_VERSION="${DITTO_VERSION:-}"

if [ ! -f "$LOCAL_DITTO_DIR/deployment/docker/docker-compose.yml" ]; then
  echo "ERROR: Khong thay Ditto docker-compose.yml trong $LOCAL_DITTO_DIR/deployment/docker" >&2
  echo "Dat LOCAL_DITTO_DIR=/path/to/eclipse-ditto neu checkout nam cho khac." >&2
  exit 1
fi

SSH_CMD=(ssh -o StrictHostKeyChecking=accept-new)
if [ -n "$SSH_KEY" ]; then
  SSH_CMD+=(-i "$SSH_KEY")
fi

RSYNC_EXCLUDES=(
  --exclude ".git/"
  --exclude ".idea/"
  --exclude ".gradle/"
  --exclude "**/target/"
  --exclude "**/node_modules/"
  --exclude "**/.pytest_cache/"
  --exclude "**/__pycache__/"
)

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

hash_deployment() {
  local dir="$1"
  (
    cd "$dir"
    find deployment/docker -maxdepth 1 -type f -print0 \
      | sort -z \
      | xargs -0 sha256sum
  )
}

hash_deployment "$LOCAL_DITTO_DIR" >"$tmp_dir/local.sha256"

"${SSH_CMD[@]}" "$REMOTE" "mkdir -p '$(dirname "$REMOTE_DIR")'"

rsync -az --delete --info=stats2 \
  -e "${SSH_CMD[*]}" \
  "${RSYNC_EXCLUDES[@]}" \
  "$LOCAL_DITTO_DIR/" \
  "$REMOTE:$REMOTE_DIR/"

"${SSH_CMD[@]}" "$REMOTE" "cd '$REMOTE_DIR' && find deployment/docker -maxdepth 1 -type f -print0 | sort -z | xargs -0 sha256sum" \
  >"$tmp_dir/remote.sha256"

if ! diff -u "$tmp_dir/local.sha256" "$tmp_dir/remote.sha256"; then
  echo "ERROR: Ditto deployment hash tren remote khong khop local." >&2
  exit 1
fi

local_git_rev="$(git -C "$LOCAL_DITTO_DIR" rev-parse --short HEAD 2>/dev/null || true)"
local_git_status="$(git -C "$LOCAL_DITTO_DIR" status --short deployment/docker/docker-compose.yml deployment/docker/nginx.conf 2>/dev/null || true)"

"${SSH_CMD[@]}" "$REMOTE" "cat >~/DITTO_GCP_SYNC_READY.txt" <<EOF
Ditto deployment synced at $(date -Is)

Remote dir:  $REMOTE_DIR
Local dir:   $LOCAL_DITTO_DIR
Local rev:   ${local_git_rev:-unknown}

Tracked local deployment edits at sync time:
${local_git_status:-clean}

Verified SHA-256 for deployment/docker/*.

Start/update Ditto with:
  cd $REMOTE_DIR/deployment/docker
  docker compose -p $COMPOSE_PROJECT up -d --remove-orphans

If you need the exact existing smoke-stack image tag:
  DITTO_VERSION=3.9.1 docker compose -p dt4n-aoi-smoke down --remove-orphans
  DITTO_VERSION=3.9.1 docker compose -p dt4n-aoi-smoke up -d
EOF

if [ "$START_DITTO" = "1" ]; then
  remote_env=()
  if [ -n "$DITTO_VERSION" ]; then
    remote_env+=(DITTO_VERSION="$DITTO_VERSION")
  fi

  if [ "$CLEAN_DITTO" = "1" ]; then
    "${SSH_CMD[@]}" "$REMOTE" "cd '$REMOTE_DIR/deployment/docker' && ${remote_env[*]} docker compose -p '$COMPOSE_PROJECT' down --remove-orphans"
  fi
  "${SSH_CMD[@]}" "$REMOTE" "cd '$REMOTE_DIR/deployment/docker' && ${remote_env[*]} docker compose -p '$COMPOSE_PROJECT' up -d --remove-orphans"
  "${SSH_CMD[@]}" "$REMOTE" "cd '$REMOTE_DIR/deployment/docker' && ${remote_env[*]} docker compose -p '$COMPOSE_PROJECT' ps"
fi

cat <<EOF
Ditto sync OK: $REMOTE:$REMOTE_DIR
Verified deployment/docker SHA-256 matches local $LOCAL_DITTO_DIR.

Remote note:
  ssh ${SSH_KEY:+-i "$SSH_KEY" }$REMOTE 'cat ~/DITTO_GCP_SYNC_READY.txt'
EOF
