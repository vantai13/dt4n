#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/prepare-local.sh GCP_PROJECT_ID

Tao/cap nhat terraform.tfvars local cho GCP:
  - copy terraform.tfvars.example neu chua co
  - tao dt4n-gcp.pem neu chua co
  - dien gcp_project_id
  - khoa ssh_allowed_cidrs/app_allowed_cidrs ve IP public hien tai
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ] || [ $# -lt 1 ]; then
  usage
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ID="$1"
TFVARS="$ROOT_DIR/terraform.tfvars"

cd "$ROOT_DIR"

if [ ! -f "$TFVARS" ]; then
  cp terraform.tfvars.example "$TFVARS"
fi

if [ ! -f dt4n-gcp.pem ]; then
  ssh-keygen -t ed25519 -f dt4n-gcp.pem -C dt4n-gcp -N ""
fi
chmod 600 dt4n-gcp.pem

PUBLIC_IP="$(curl -fsS https://checkip.amazonaws.com | tr -d '[:space:]')"

perl -0pi -e "s/gcp_project_id\\s*=\\s*\"[^\"]*\"/gcp_project_id = \"$PROJECT_ID\"/" "$TFVARS"
perl -0pi -e "s/ssh_allowed_cidrs\\s*=\\s*\\[[^\\]]*\\]/ssh_allowed_cidrs = [\"$PUBLIC_IP\\/32\"]/" "$TFVARS"
perl -0pi -e "s/app_allowed_cidrs\\s*=\\s*\\[[^\\]]*\\]/app_allowed_cidrs = [\"$PUBLIC_IP\\/32\"]/" "$TFVARS"

cat <<EOF
Da chuan bi:
  $TFVARS
  $ROOT_DIR/dt4n-gcp.pem
  $ROOT_DIR/dt4n-gcp.pem.pub

Project: $PROJECT_ID
Allowed CIDR: $PUBLIC_IP/32
EOF
