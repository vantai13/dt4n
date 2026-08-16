#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/apply-and-check.sh

Chay end-to-end sau khi da co terraform.tfvars hop le va Google Cloud credential:
  1. terraform init/validate/apply
  2. lay public IP output
  3. doi SSH vao VM
  4. doi startup script tao ~/DT4N_GCP_READY.txt
  5. chay scripts/check-remote.sh

Bien huu ich:
  AUTO_APPROVE=0        xem apply plan va tu nhap yes
  SKIP_REMOTE_CHECK=1   chi tao VM va in lenh SSH
  SSH_WAIT_SECONDS=1800 doi SSH/bootstrap toi da 30 phut
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

AUTO_APPROVE="${AUTO_APPROVE:-1}"
SKIP_REMOTE_CHECK="${SKIP_REMOTE_CHECK:-0}"
SSH_WAIT_SECONDS="${SSH_WAIT_SECONDS:-1800}"

if [ ! -f terraform.tfvars ]; then
  echo "ERROR: Chua co terraform.tfvars. Chay: ./scripts/prepare-local.sh YOUR_GCP_PROJECT_ID" >&2
  exit 1
fi

PROJECT_ID="$(awk -F\" '/^[[:space:]]*gcp_project_id[[:space:]]*=/{print $2; exit}' terraform.tfvars)"
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "YOUR_GCP_PROJECT_ID" ]; then
  echo "ERROR: gcp_project_id trong terraform.tfvars chua hop le." >&2
  echo "Sua file hoac chay: ./scripts/prepare-local.sh YOUR_GCP_PROJECT_ID" >&2
  exit 1
fi

if [ ! -f dt4n-gcp.pem ]; then
  ssh-keygen -t ed25519 -f dt4n-gcp.pem -C dt4n-gcp -N ""
fi
chmod 600 dt4n-gcp.pem

if [ ! -f dt4n-gcp.pem.pub ]; then
  ssh-keygen -y -f dt4n-gcp.pem >dt4n-gcp.pem.pub
fi

if gcloud auth list --filter=status:ACTIVE --format='value(account)' | grep -q .; then
  gcloud services enable compute.googleapis.com --project "$PROJECT_ID"
else
  echo "WARN: gcloud chua co active account. Terraform van co the chay neu ADC/service account da hop le."
  echo "      Neu apply loi auth, chay: gcloud auth login && gcloud auth application-default login"
fi

terraform init
terraform validate

if [ "$AUTO_APPROVE" = "1" ]; then
  terraform apply -auto-approve
else
  terraform apply
fi

PUBLIC_IP="$(terraform output -json public_ips | jq -r '.[0] // empty')"
SSH_COMMAND="$(terraform output -json ssh_commands | jq -r '.[0] // empty')"
if [ -z "$PUBLIC_IP" ] || [ -z "$SSH_COMMAND" ]; then
  echo "ERROR: Khong lay duoc public_ips/ssh_commands tu Terraform output." >&2
  exit 1
fi

REMOTE="ubuntu@$PUBLIC_IP"
SSH_KEY="./dt4n-gcp.pem"
SSH_OPTS=(-i "$SSH_KEY" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)

echo "VM public IP: $PUBLIC_IP"
echo "SSH: $SSH_COMMAND"
echo "Doi SSH san sang..."

deadline=$((SECONDS + SSH_WAIT_SECONDS))
until ssh "${SSH_OPTS[@]}" "$REMOTE" "true" >/dev/null 2>&1; do
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo "ERROR: Het thoi gian doi SSH vao $REMOTE" >&2
    exit 1
  fi
  sleep 15
done

echo "SSH da san sang. Doi startup script hoan tat..."
until ssh "${SSH_OPTS[@]}" "$REMOTE" "test -f ~/DT4N_GCP_READY.txt" >/dev/null 2>&1; do
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo "ERROR: Het thoi gian doi startup script. Log gan nhat:" >&2
    ssh "${SSH_OPTS[@]}" "$REMOTE" "sudo tail -n 120 /var/log/dt4n-bootstrap.log" || true
    exit 1
  fi
  ssh "${SSH_OPTS[@]}" "$REMOTE" "sudo tail -n 20 /var/log/dt4n-bootstrap.log" || true
  sleep 30
done

ssh "${SSH_OPTS[@]}" "$REMOTE" "cat ~/DT4N_GCP_READY.txt"

if [ "$SKIP_REMOTE_CHECK" != "1" ]; then
  ./scripts/check-remote.sh "$REMOTE" "$SSH_KEY"
fi
