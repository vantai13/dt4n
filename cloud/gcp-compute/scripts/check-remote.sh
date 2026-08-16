#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/check-remote.sh ubuntu@GCE_IP [./dt4n-gcp.pem]

Kiem tra nhanh cac thanh phan DT4N tren GCE VM: Docker, OVS, Mininet, Conda env, Node.

Bien huu ich:
  RL_ENV=sdn_rl RYU_ENV=sdn_net ./scripts/check-remote.sh ubuntu@GCE_IP ./dt4n-gcp.pem
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
if conda env list | awk \"{print \\\$1}\" | grep -qx \"\$RL_ENV\"; then
  conda run -n \"\$RL_ENV\" python -c \"import numpy, requests, yaml, gymnasium, torch; print(\\\"numpy\\\", numpy.__version__); print(\\\"torch\\\", torch.__version__); print(\\\"gymnasium\\\", gymnasium.__version__)\"
else
  echo \"SKIP: Conda env \$RL_ENV chua ton tai. Chay ./cloud/gcp-compute/scripts/restore-conda-envs.sh sau khi sync project.\"
fi
echo
echo == Ryu ==
if conda env list | awk \"{print \\\$1}\" | grep -qx \"\$RYU_ENV\"; then
  conda run -n \"\$RYU_ENV\" ryu-manager --version || true
else
  echo \"SKIP: Conda env \$RYU_ENV chua ton tai. Chay ./cloud/gcp-compute/scripts/restore-conda-envs.sh sau khi sync project.\"
fi
echo
echo == Ditto deployment files ==
if [ -f ~/tools/ditto/deployment/docker/docker-compose.yml ]; then
  cd ~/tools/ditto
  sha256sum deployment/docker/docker-compose.yml deployment/docker/nginx.conf
  grep -n \"FIRE_AND_FORGET_ENFORCEMENT_TIMEOUT\" deployment/docker/docker-compose.yml || true
  grep -n \"Swagger UI is disabled\" deployment/docker/nginx.conf || true
else
  echo \"SKIP: ~/tools/ditto chua co. Chay ./cloud/gcp-compute/scripts/sync-ditto-deployment.sh tu local.\"
fi
echo
echo == Running Ditto gateway ==
gateway=\$(docker ps --format \"{{.Names}}\" | grep -E \"gateway\" | head -1 || true)
if [ -n \"\$gateway\" ]; then
  echo \"gateway=\$gateway\"
  docker inspect \"\$gateway\" --format \"{{range .Config.Env}}{{println .}}{{end}}\" | grep -E \"ENABLE_PRE_AUTHENTICATION|FIRE_AND_FORGET_ENFORCEMENT_TIMEOUT|DITTO_HOME|JAVA_VERSION\" || true
else
  echo \"SKIP: khong thay Ditto gateway container dang chay.\"
fi
'"
