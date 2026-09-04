#!/usr/bin/env bash
# Prepare a quiet host for G-A016. Dry-run by default; pass --execute explicitly.
set -euo pipefail

execute=false
if [[ "${1:-}" == "--execute" ]]; then
  execute=true
elif [[ $# -ne 0 ]]; then
  echo "usage: $0 [--execute]" >&2
  exit 2
fi

echo "=== BEFORE ==="
uptime
ps -eo pcpu,rss,comm --sort=-pcpu | head -12

if [[ "$execute" == true ]]; then
  docker compose -f ditto/docker-compose.yml stop 2>/dev/null || \
    pkill -f 'org.eclipse.ditto' || true
  sudo systemctl stop docker.socket docker 2>/dev/null || true
  sudo pkill -f mongod || true
  pkill -f '.vscode-server' || true
  pkill -f 'anthropic.claude-code' || true
  pkill -f 'openai.chatgpt' || true
  sudo systemctl stop unattended-upgrades snapd.service 2>/dev/null || true
  sudo cpupower frequency-set -g performance 2>/dev/null || \
    echo "cpupower unavailable (normal on a VM)"
  sleep 30
else
  echo "DRY RUN: no process or service was stopped; use --execute from tmux/SSH."
fi

echo "=== AFTER / CURRENT ==="
uptime
ps -eo pcpu,rss,comm --sort=-pcpu | head -12
cat /proc/pressure/cpu 2>/dev/null || true
grep -c . /proc/interrupts 2>/dev/null || true
awk '/^cpu / {print "steal_ticks_since_boot = " $9}' /proc/stat

load1=$(cut -d' ' -f1 /proc/loadavg)
echo "load1 = $load1"
awk -v l="$load1" 'BEGIN {
  if (l > 0.10) {
    print "REFUSED: load > 0.10"
    exit 1
  }
  print "host is quiet enough"
}'
