#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/check-remote.sh ubuntu@EC2_IP [./dt4n-aws.pem]

Kiem tra nhanh cac thanh phan DT4N tren EC2: Docker, OVS, Mininet, Conda env, Node.

Bien huu ich:
  RL_ENV=sdn_rl RYU_ENV=sdn_net ./scripts/check-remote.sh ubuntu@EC2_IP ./dt4n-aws.pem
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ] || [ $# -lt 1 ]; then
  usage
  exit 0
fi

REMOTE="$1"
SSH_KEY="${2:-}"
RL_ENV="${RL_ENV:-sdn_rl}"
RYU_ENV="${RYU_ENV:-sdn_net}"

SSH_CMD=(ssh -o StrictHostKeyChecking=accept-new)
if [ -n "$SSH_KEY" ]; then
  SSH_CMD+=(-i "$SSH_KEY")
fi

"${SSH_CMD[@]}" "$REMOTE" "RL_ENV='$RL_ENV' RYU_ENV='$RYU_ENV' bash -lc '
set -e
echo == OS ==
lsb_release -a 2>/dev/null || cat /etc/os-release
echo
echo == Docker ==
docker --version
docker compose version
echo
echo == OVS ==
systemctl is-active openvswitch-switch
ovs-vsctl --version | head -1
echo
echo == Mininet ==
mn --version || true
echo
echo == Node ==
node --version
npm --version
echo
echo == Conda ==
source ~/miniforge3/etc/profile.d/conda.sh
conda env list
echo
echo == Python imports in \$RL_ENV ==
conda run -n \"\$RL_ENV\" python - <<PY
import numpy, requests, yaml, gymnasium, torch
print(\"numpy\", numpy.__version__)
print(\"torch\", torch.__version__)
PY
echo
echo == Ryu ==
conda run -n \"\$RYU_ENV\" ryu-manager --version || true
'"
