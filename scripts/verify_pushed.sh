#!/usr/bin/env bash
# Canonical remote-state check for main and any evidence tags supplied as args.
set -euo pipefail

git fetch --quiet --tags origin
local_head=$(git rev-parse HEAD)
remote_head=$(git rev-parse origin/main)

if [[ "$local_head" != "$remote_head" ]]; then
    echo "BLOCKED main local=$local_head origin=$remote_head"
    exit 1
fi
echo "OK main $local_head"

for tag in "$@"; do
    if git ls-remote --exit-code --tags origin "refs/tags/$tag" >/dev/null; then
        echo "OK tag $tag"
    else
        echo "BLOCKED tag $tag missing"
        exit 1
    fi
done
