#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST_ALIAS="${HOST_ALIAS:-dt4n-gcp}"

cd "$ROOT_DIR"

if ! command -v powershell.exe >/dev/null 2>&1; then
  echo "ERROR: Khong thay powershell.exe. Script nay can chay trong WSL tren Windows." >&2
  exit 1
fi

public_ip="${1:-}"
if [ -z "$public_ip" ]; then
  public_ip="$(terraform output -json public_ips 2>/dev/null | jq -r '.[0] // empty')"
fi

if [ -z "$public_ip" ]; then
  echo "ERROR: Chua co GCE public IP. Hay chay terraform apply truoc, hoac truyen IP vao script:" >&2
  echo "  ./scripts/setup-vscode-ssh-from-terraform.sh GCE_PUBLIC_IP" >&2
  exit 1
fi

powershell.exe -NoProfile -ExecutionPolicy Bypass \
  -File "$(wslpath -w "$ROOT_DIR/scripts/setup-windows-vscode-ssh.ps1")" \
  -HostName "$public_ip" \
  -HostAlias "$HOST_ALIAS" \
  -SourceKey "$(wslpath -w "$ROOT_DIR/dt4n-gcp.pem")"

echo
echo "Kiem tra tu PowerShell hoac Windows Terminal:"
echo "  ssh $HOST_ALIAS"
echo
echo "Trong VS Code:"
echo "  Ctrl+Shift+P -> Remote-SSH: Connect to Host... -> $HOST_ALIAS"
